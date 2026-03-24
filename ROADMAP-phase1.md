# LCOS-R 一阶段实验实施路线图

**目标**：验证核心 thesis——"开放扩展若没有 rewrite，会退化成规则堆积；有 rewrite，才会带来系统级收益"。

**当前状态**：全部 11 个步骤（0-10）已完成。✅

---

## 步骤 0 ✅ 数据获取与领域分析

> 已完成。

- **输入**：AgiBot World Task Catalog（HuggingFace 217 个 task JSON）
- **输出**：
  - `data/agibot-world/task_info/` — 217 个原始 JSON
  - `data/agibot-world/signature_extraction.json` — 结构化提取结果
  - `data/agibot-world/extraction_report.txt` — 文本报告
- **工具**：`scripts/extract_signatures.py`
- **关键产出**：
  - 五领域分类（家居 128 / 零售 30 / 工业 20 / 餐饮 22 / 办公 17）
  - 每领域的技能集、物体集、动作谓词
  - 跨领域共享技能 16 种（≥3 域）

---

## 步骤 1 ✅ 实验设计定稿

> 已完成。见 tech-note-0v1.md §9。

---

## 步骤 2 ✅ 语义签名数据结构 `Sigma_t`

**目标**：实现 §4+§5.2 中定义的语义签名及其所有分量的可序列化数据结构。

### 输入
- `data/agibot-world/signature_extraction.json`（领域分类和提取结果）
- tech-note §4（术语定义）、§5.2（系统配置定义）

### 输出
- `src/core/signature.py` — `SemanticSignature` 类

### 具体内容

```
SemanticSignature:
  S_t: Set[Type]           # 对象类型集合（cup, shelf, dough …）
  D_t: Set[Entity]         # 当前对象域实例（cup_1, shelf_A …）
  R_b: Set[BoolPredicate]  # 布尔谓词（on, in, reachable, holding …）
  R_g: Set[GradedPredicate]# 渐变谓词（fragile, hot, heavy …）
  A_t: Set[ActionTemplate]  # 动作模板（pick, place, pour …）
  C_t: Set[Constraint]     # 约束条件

ActionTemplate:
  name: str
  parameters: List[TypedParam]
  preconditions: List[Predicate]  # 前提
  effects: List[Predicate]        # 效果

Constraint:
  name: str
  body: LogicalFormula  # 例如 hot(x) → ¬allow(grasp_bare(x))
```

### 验收标准
- [ ] 能从 `signature_extraction.json` 自动生成家居领域的 `Sigma_0`
- [ ] `Sigma_t` 可序列化为 JSON 并可反序列化
- [ ] 有 `merge(Sigma_t, Delta)` 方法用于接受领域扩展
- [ ] 有 `predicate_count()`, `rule_count()`, `constraint_count()` 等统计方法

---

## 步骤 3 ✅ Task Catalog → Sigma_t 映射脚本

**目标**：将步骤 0 提取的原始数据转换为步骤 2 定义的 `SemanticSignature` 实例。

### 输入
- `data/agibot-world/signature_extraction.json`
- `src/core/signature.py`（步骤 2 的数据结构）

### 输出
- `scripts/build_signatures.py` — 映射脚本
- `data/signatures/domestic.json` — 家居领域签名
- `data/signatures/retail_delta.json` — 零售领域增量
- `data/signatures/industrial_delta.json` — 工业领域增量
- `data/signatures/restaurant_delta.json` — 餐饮领域增量
- `data/signatures/office_delta.json` — 办公领域增量

### 映射规则（对应 §9.1 表）

| 来源字段 | 目标分量 | 示例 |
|----------|----------|------|
| skill 标签 | `A_t` 动作模板 | `Pick` → `pick(obj: Graspable)` |
| init_scene_text 物体 | `S_t` + `D_t` | "cup" → 类型 `Cup ⊂ Container` |
| init_scene_text 空间关系 | `R_b` 谓词 | "on the table" → `on(x, table)` |
| init_scene_text 状态 | `R_b` / `R_g` | "closed" → `closed(x)`; "hot" → `hot(x)` |
| 任务描述中的限制 | `C_t` 约束 | 安全/顺序限制 → 约束规则 |

### 关键设计决策
- 家居领域构成完整的 `Sigma_0`（基线）
- 其余领域只输出**增量** `Delta_k`（仅包含该领域独有的新类型/新谓词/新技能/新约束）
- **故意保留跨领域同义谓词**（如 `on(x,y)` vs `on_shelf(x,y)`），留给 rewrite 来合并

### 验收标准
- [ ] 5 个签名文件生成且可被 `SemanticSignature` 反序列化
- [ ] `Sigma_0` 覆盖家居领域全部 69 种技能
- [ ] 每个 `Delta_k` 至少包含 3 种该领域独有谓词、2 种独有技能、1 条独有约束
- [ ] 存在至少 5 对跨领域同义谓词可供 rewrite 合并

---

## 步骤 4 ✅ PDDL 生成器

**目标**：将 `SemanticSignature` 翻译为 PDDL domain + problem 文件，使标准 planner 可求解。

### 输入
- `SemanticSignature` 实例（步骤 2–3）
- 具体任务的对象实例和目标状态

### 输出
- `src/core/pddl_generator.py` — 签名到 PDDL 的翻译器
- 生成的 `*.pddl` domain / problem 文件

### 具体内容

```
pddl_generator.generate_domain(sigma: SemanticSignature) -> str
  # S_t → (:types ...)
  # R_b → (:predicates ...)
  # A_t → (:action ... :parameters :precondition :effect)
  # C_t → 嵌入 action precondition 或单独 axiom

pddl_generator.generate_problem(sigma, objects, init_state, goal) -> str
  # D_t → (:objects ...)
  # init_state → (:init ...)
  # goal → (:goal ...)
```

### Planner 选择
- **推荐**：Fast Downward（开源，支持增量规划，Python 绑定）
- **备选**：ENHSP（支持 numeric planning）、pyperplan（纯 Python，调试方便）

### 验收标准
- [ ] 家居 `Sigma_0` 生成的 PDDL domain 可被 Fast Downward 解析
- [ ] 对家居领域 10 个采样任务，planner 能生成合法 plan
- [ ] PDDL 行数可度量（作为表示复杂度指标）

---

## 步骤 5 ✅ 测试集框架 `Q_star / Q_task / Q_t`

**目标**：实现 §5.1 定义的三层测试集及其执行接口。

### 输入
- `SemanticSignature` + PDDL 生成器（步骤 2–4）
- tech-note §5.1（测试定义）、§6.6（分层验证）

### 输出
- `src/core/test_suite.py` — 测试集框架

### 测试类型（按 §6.6 分层）

```
T0 廉价测试 (O(1)–O(n)):
  - type_consistency(sigma)      # 类型一致性
  - signature_match(sigma, plan) # 签名匹配
  - well_formedness(config)      # WF(c) 验证

T1 中等测试 (O(n²)–O(n³)):
  - predicate_eval(sigma, state, pred) # 谓词求值
  - affordance_check(sigma, action)     # affordance 查表
  - risk_threshold(sigma, action)       # 风险阈值

T2 昂贵测试 (NP-hard):
  - is_plannable(sigma, init, goal)     # 规划可行性
  - plan_cost(sigma, init, goal)        # 计划代价
  - conflict_count(sigma)               # 规则冲突数
```

### 三层测试集

```
Q_star ⊆ Q_task ⊆ Q_t

Q_star: 核心安全+类型测试（只增不减）
  - 类型一致性
  - 核心约束不违反
  - 安全谓词不被删除

Q_task: 当前领域任务测试
  - 当前领域采样任务的可规划性
  - 规划结果的前提/效果一致性

Q_t: 全集 = Q_star + Q_task + 诊断测试
  - 谓词覆盖率
  - 规划代价统计
```

### 验收标准
- [ ] `Q_star` 包含至少 10 条核心测试
- [ ] 家居 `Sigma_0` 上全部 T0/T1 测试通过
- [ ] 家居领域 10 个任务的 T2 测试可执行
- [ ] 测试结果可序列化，支持前后对比

---

## 步骤 6 ✅ 系统配置 `Config_t` 与 Rewrite Pass 实现

**目标**：实现 §5.2 的系统配置和 §6.5 的三个核心 rewrite pass。

### 输入
- `SemanticSignature`, PDDL 生成器, 测试集框架（步骤 2–5）
- tech-note §6（Rewrite Layer 完整定义）

### 输出
- `src/core/config.py` — `SystemConfig` 类（对应 $c_t$）
- `src/rewrite/pass1_predicate_elimination.py` — 冗余谓词消除
- `src/rewrite/pass2_rule_folding.py` — 规则折叠
- `src/rewrite/pass3_object_pruning.py` — 无关对象裁剪
- `src/rewrite/engine.py` — rewrite 执行引擎

### 系统配置

```python
class SystemConfig:
    sigma: SemanticSignature  # 语义签名
    belief: BeliefState       # 当前 belief
    projection: Projection    # Π_t
    transition: TransitionKernel  # K_t
    planner: PlannerInterface    # Plan_t
    grammar: RewriteGrammar      # G_t
```

### 三个 Rewrite Pass

**Pass 1 — 冗余谓词消除（Core-Preserving）**
```
输入: config_t, Q_star
过程:
  1. 遍历 R_b ∪ R_g 中每个谓词 P
  2. 检查 P 是否可由其他谓词在 D_t 上推导
  3. 若可推导，构造候选替换 config'
  4. 分层验证: T0 → T1 → T2 on Q_star
  5. 通过则应用替换
输出: 简化后的 config_t'
```

**Pass 2 — 规则折叠（Core-Preserving）**
```
输入: config_t, Q_star
过程:
  1. 识别规则中的同构模式（相同结构、不同实例）
  2. 构造参数化通用规则
  3. 分层验证
输出: 规则数减少后的 config_t'
```

**Pass 3 — 无关对象裁剪（Task-Preserving）**
```
输入: config_t, Q_task, current_task
过程:
  1. 分析 current_task 涉及的对象集合
  2. 标记不出现在 Q_task 任何输入中的对象
  3. 从工作状态中移除标记对象及其关联事实
  4. 在 Q_task 上验证
输出: 裁剪后的 config_t'
```

### Rewrite 引擎

```python
class RewriteEngine:
    def run_pass_sequence(config, passes, test_suite):
        """按序执行 pass 列表，每个 pass 后验证，失败则回滚"""
        for p in passes:
            config_new = p.apply(config)
            if test_suite.verify(config_new, p.required_level):
                config = config_new
                log(p.name, "applied", metrics(config))
            else:
                log(p.name, "rejected")
        return config
```

### 验收标准
- [ ] Pass 1 能在家居+零售合并签名上消除至少 1 对同义谓词
- [ ] Pass 2 能将至少 2 条同构规则折叠为 1 条参数化规则
- [ ] Pass 3 能在单领域任务中裁剪其他领域对象
- [ ] 每个 pass 的 Q_star / Q_task 回归测试全部通过
- [ ] 每个 pass 记录 wall-clock 时间

---

## 步骤 7 ✅ 四组实验系统搭建

**目标**：实现 §9.3 定义的四组对比系统。

### 输入
- 步骤 2–6 的全部组件
- 五领域签名和增量（步骤 3）

### 输出
- `src/experiment/baseline.py` — Baseline 系统
- `src/experiment/expand_only.py` — Expand-Only 系统
- `src/experiment/expand_rewrite.py` — Expand+Rewrite 系统
- `src/experiment/expand_manual.py` — Expand+ManualOpt 系统
- `data/manual_opt/` — 人工优化规则（步骤 7 中手工编写）

### 四组系统逻辑

```
                        Stage 0    Stage 1      Stage 2        Stage 3        Stage 4
                        (家居)    (+零售)      (+工业)        (+餐饮)        (+办公)

Baseline:               Σ₀         Σ₀           Σ₀             Σ₀             Σ₀
                        (不变)

Expand-Only:            Σ₀        Σ₀+Δ₁       Σ₀+Δ₁+Δ₂      …+Δ₃           …+Δ₄
                                  (直接追加)

Expand+Rewrite:         Σ₀        R(Σ₀+Δ₁)    R(…+Δ₂)       R(…+Δ₃)       R(…+Δ₄)
                                  (追加后 rewrite)

Expand+ManualOpt:       Σ₀        M(Σ₀+Δ₁)    M(…+Δ₂)       M(…+Δ₃)       M(…+Δ₄)
                                  (追加后手动优化)
```

### ManualOpt 准备工作
每个阶段的手动优化规则需要提前准备：
1. 查看 `Expand-Only` 阶段合并后的签名
2. 人工标注哪些谓词应该合并、哪些规则应该折叠、哪些对象应该裁剪
3. 将手动决策写为配置文件 `data/manual_opt/stage_k.json`

### 验收标准
- [ ] 四组系统都能在 Stage 0 上正常运行
- [ ] Expand-Only 在 Stage 1 后谓词数 > Stage 0
- [ ] Expand+Rewrite 在 Stage 1 后谓词数 < Expand-Only
- [ ] ManualOpt 可配置且可复现

---

## 步骤 8 ✅ 指标收集与实验运行

**目标**：运行 4 阶段 × 4 组实验，收集 §9.4 的五类指标。

### 输入
- 四组系统（步骤 7）
- 每领域采样任务集（≥30 个任务/领域，配对设计）

### 输出
- `src/experiment/runner.py` — 实验运行器
- `src/experiment/metrics.py` — 指标收集模块
- `results/raw/` — 原始实验数据（CSV/JSON）
- `results/pilot/` — pilot study 结果（每领域 10 任务）

### 实验流程

```
for stage in [0, 1, 2, 3, 4]:
    for system in [Baseline, ExpandOnly, ExpandRewrite, ExpandManualOpt]:
        config = system.setup(stage)
        for task in sampled_tasks[stage]:
            metrics = run_single(config, task)
            record(system, stage, task, metrics)
```

### 五类指标（对应 §9.4）

```
1. 表示复杂度:
   - active_predicates: |R_b| + |R_g|
   - active_rules: len(rules)
   - active_constraints: len(constraints)
   - pddl_lines: wc -l domain.pddl
   - fact_count: len(working_state)
   - predicate_overlap_rate: 跨领域重复谓词比例

2. 计算开销:
   - sig_construction_ms: 签名构造时间
   - planning_ms: 单次规划时间
   - rewrite_ms: rewrite pass 时间
   - verify_ms: 验证时间

3. 任务可规划性:
   - plannable_rate: 可规划率 (%)
   - conflict_count: 规则冲突数
   - regression_pass_rate: Q_task 回归通过率 (%)

4. 稳定性曲线:
   - 以上指标随 stage 0→4 的变化趋势

5. 端到端参照:
   - go1_success_rate: GO-1 已发表成功率 [8]
   - lcos_plannable_rate: LCOS-R 可规划率（同任务）
```

### 统计设计
1. **Pilot study**：每领域 10 个任务，估计方差
2. **Power analysis**：目标 power ≥ 0.8，α = 0.05，d ≥ 0.5
3. **正式实验**：根据 pilot 确定样本量（最少 30/领域）
4. **配对检验**：同一任务集在四组系统上运行，配对 t 检验 / Wilcoxon

### 验收标准
- [ ] Pilot study 完成，方差估计合理
- [ ] 正式实验每领域 ≥ 30 任务
- [ ] 五类指标全部收集到 `results/raw/`
- [ ] 原始数据可复现

---

## 步骤 9 ✅ 结果分析与可视化

**目标**：分析、可视化、验证核心 thesis。

### 输入
- `results/raw/` — 原始实验数据（步骤 8）
- §9.5 预期结果作为对照

### 输出
- `scripts/analyze_results.py` — 分析脚本
- `results/figures/` — 图表
- `results/analysis.md` — 分析报告

### 核心图表

```
图 1: 表示复杂度 vs 扩展阶段（4 条折线，x=stage, y=predicates+rules）
      预期: Expand-Only 线性/超线性上升，Expand+Rewrite 被抑制

图 2: 可规划率 vs 扩展阶段（4 条折线）
      预期: Expand-Only 下降，Expand+Rewrite 稳定

图 3: 规划时间 vs 扩展阶段（4 条折线）
      预期: 同上趋势

图 4: Rewrite 收益分解（堆叠柱状图）
      Pass 1/2/3 各自消除的谓词/规则/对象数

图 5: OOD 泛化（跨领域复合任务的可规划率对比）

图 6: 跨领域谓词重叠率（rewrite 前 vs 后）

表 1: 与 GO-1 参照对比（可规划率 vs 动作成功率）
```

### 核心统计检验

```
H0: Expand+Rewrite 的表示复杂度 = Expand-Only 的表示复杂度
H1: Expand+Rewrite 的表示复杂度 < Expand-Only 的表示复杂度
检验: 配对 t 检验 / Wilcoxon signed-rank test
```

### 验收标准
- [ ] 图 1–6 生成且趋势与 §9.5 预期一致（或记录偏差原因）
- [ ] 统计检验 p < 0.05 或记录未达显著性的原因
- [ ] 分析报告完成

---

## 步骤 10 ✅ 回写 tech-note 并校准参数

**目标**：根据实验结果更新 tech-note，校准代价函数权重和误差预算参数。

### 输入
- `results/analysis.md`（步骤 9）
- `tech-note-0v1.md`

### 输出
- `tech-note-0v2.md`（更新版本）
- 更新内容：
  - §9 补充实际实验结果数据
  - §10 更新数学自洽性判断
  - §11 更新工程可落地判断
  - §8.2 校准 $\lambda_1$–$\lambda_4$ 权重和 $\varepsilon$ 预算
  - §13 更新下一步计划

### 验收标准
- [ ] 实验数据嵌入 tech-note
- [ ] 代价函数权重有经验依据
- [ ] 下一步方向明确

---

## 依赖关系与建议时序

```
步骤 0 ✅ ──→ 步骤 1 ✅ ──→ 步骤 2 ──→ 步骤 3 ──→ 步骤 4
                                                       ↓
                                                    步骤 5
                                                       ↓
                                              步骤 6 ──→ 步骤 7 ──→ 步骤 8 ──→ 步骤 9 ──→ 步骤 10
```

可并行的步骤：
- **步骤 2 + 步骤 4** 可以同时开始（签名结构和 PDDL 生成器独立）
- **步骤 5** 可在步骤 4 完成后立刻开始
- **ManualOpt 规则编写**（步骤 7 的一部分）可在步骤 6 完成后并行准备

---

## 项目目录结构（目标）

```
lcos-r/
├── tech-note-0v1.md             # 主文档
├── ROADMAP.md                   # 本路线图
├── data/
│   ├── agibot-world/
│   │   ├── task_info/           # 217 个原始 JSON ✅
│   │   ├── signature_extraction.json  ✅
│   │   └── extraction_report.txt      ✅
│   ├── signatures/              # 步骤 3 产出
│   │   ├── domestic.json
│   │   ├── retail_delta.json
│   │   ├── industrial_delta.json
│   │   ├── restaurant_delta.json
│   │   └── office_delta.json
│   └── manual_opt/              # 步骤 7 手动优化规则
├── scripts/
│   ├── extract_signatures.py    ✅
│   ├── build_signatures.py      # 步骤 3
│   └── analyze_results.py       # 步骤 9
├── src/
│   ├── core/
│   │   ├── signature.py         # 步骤 2
│   │   ├── config.py            # 步骤 6
│   │   ├── pddl_generator.py    # 步骤 4
│   │   └── test_suite.py        # 步骤 5
│   ├── rewrite/
│   │   ├── engine.py            # 步骤 6
│   │   ├── pass1_predicate_elimination.py
│   │   ├── pass2_rule_folding.py
│   │   └── pass3_object_pruning.py
│   └── experiment/
│       ├── runner.py            # 步骤 8
│       ├── metrics.py           # 步骤 8
│       ├── baseline.py          # 步骤 7
│       ├── expand_only.py
│       ├── expand_rewrite.py
│       └── expand_manual.py
├── results/
│   ├── pilot/                   # 步骤 8 pilot
│   ├── raw/                     # 步骤 8 正式
│   ├── figures/                 # 步骤 9
│   └── analysis.md              # 步骤 9
└── tests/                       # 单元测试
    ├── test_signature.py
    ├── test_pddl_generator.py
    ├── test_rewrite_passes.py
    └── test_experiment.py
```

---

## 风险点与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Task Catalog 描述太粗，无法构造精确前提/效果 | 签名质量差 | 手动补充前 50 个高频任务的前提/效果；在 §9 中说明这是"从自然语言描述中提取的近似签名" |
| Fast Downward 对大签名规划超时 | T2 测试卡住 | 设置 planner 超时 30s；超时视为"不可规划" |
| Expand+Rewrite 和 Expand-Only 差异不显著 | thesis 不成立 | 如实报告；分析原因（可能是领域差异本身较小，或 rewrite pass 太保守） |
| ManualOpt 的人工偏见 | 对比不公平 | 由两个人独立编写 ManualOpt 规则，取交集 |
| approximate rewrite 误差累积 | 第一版暂不实现 Pass 5（affordance 摘要），只做 exact rewrite（Pass 1–3） |
