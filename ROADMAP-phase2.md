# LCOS-R 二阶段实验路线图

> **状态：已完成** ✅ 所有 6 个步骤均已执行。结果已写入 tech-note §9.7。

## 背景：一阶段遗留的问题

### 已验证的结论

一阶段实验（5 域渐进 × 4 组系统 × 30 任务/域）验证了：

- **复杂度抑制**：Expand+Rewrite（115）显著低于 Expand-Only（125），配对 t 检验 p=0.0248，Cohen's d=2.42
- **自动 rewrite ≈ 人工优化**：ManualOpt（114）与 Rewrite（115）无显著差异（p=0.058）
- **Baseline 失效**：Baseline 在新领域可规划率降至 0%

### 未验证的关键预期

| 预期 | 实际结果 | 原因 |
|------|---------|------|
| Expand-Only 可规划率随扩展下降 | **未观察到**，全部 100% | 任务太简单 |
| Rewrite 对可规划率有保护作用 | **无法区分**，因为都是 100% | 同上 |

### 根因分析

一阶段的 30 个任务/域全部是**模板化的 1-2 步单域任务**（如 `pick(cup)` → `place(cup, table)`）。这导致：

1. **搜索深度 ≤ 2**：BFS 在深度 1-2 就找到解，根本碰不到因冗余谓词导致的状态空间膨胀区域
2. **无跨域交互**：每个任务只涉及单一领域的谓词/动作，不会触发跨域约束冲突
3. **同义谓词歧义无影响**：单步任务的 init 和 goal 始终使用同一领域的谓词（如零售只用 `on_shelf`），不存在 init 用 `on_shelf` 而 goal 用 `on` 的歧义场景

**核心问题**：一阶段实验只验证了"rewrite 压缩表示"，没有验证"压缩表示带来规划能力保护"。

---

## 二阶段目标

设计并运行**跨域组合任务实验**，验证：

> **在多步跨域任务中，Expand-Only 的可规划率因冗余表示膨胀而退化，而 Expand+Rewrite 因表示紧凑而保持可规划。**

---

## 步骤 1：跨域组合任务设计

**目标**：设计 3-5 步的跨域组合任务模板，使其语义合理且能暴露 Expand-Only 的退化。

### 输入

- 5 域语义签名（`data/signatures/*.json`）
- 7 对同义谓词：`on_shelf→on`, `on_belt→on`, `on_tray→on`, `on_desk→on`, `in_cart→in`, `sorted_into→in`, `in_holder→in`
- 各域动作模板和约束（`scripts/build_signatures.py`）

### 设计原则

必须满足以下三类特征中的**至少一种**才能触发退化：

#### 类型 A：同义谓词歧义任务

- 任务的 init 使用某域特有谓词（如 `on_shelf(obj, shelf)`），goal 使用基础谓词（如 `on(obj, table)`）或另一域谓词（如 `on_desk(obj, desk)`）
- **在 Expand-Only 中**：`on_shelf` 和 `on` 是两个不同谓词，planner 找不到从一个到另一个的动作链
- **在 Rewrite 中**：`on_shelf` 已合并为 `on`，planner 直接识别为同一谓词

#### 类型 B：跨域约束冲突任务

- 任务涉及两个域的动作，且一个域的约束阻断另一个域的动作前置条件
- 例如：工业域约束 `heavy(obj)` →需要 `two_hand_grasp`，但零售域 `place_on_shelf` 只声明了 `holding` 前置条件
- **在 Expand-Only 中**：两套约束同时存在，planner 不知道该执行哪个分支
- **在 Rewrite 中**：折叠后的规则消除了矛盾路径

#### 类型 C：多步链式任务（深度触发）

- 任务需要 4-5 步，横跨 3+ 个域
- 例如：工业取物 → 家居清洁 → 餐饮摆盘 → 办公归档
- **在 Expand-Only 中**：125 个语义要素的搜索空间在深度 4-5 时可能超过 BFS 的 50K 节点限制
- **在 Rewrite 中**：115 个语义要素 + per-task 裁剪后搜索空间显著缩小

### 输出

- 在 `src/experiment/systems.py` 的 `generate_domain_tasks` 中新增 `cross_domain` 任务模板
- 每种类型至少 5 个模板，共 15-20 个跨域组合任务模板
- 每个模板附带注释说明其触发的退化类型（A/B/C）

### 验收标准

- 每个跨域任务在完整 Sigma（5 域合并 + Rewrite 后）上可规划
- 能明确标注任务涉及的域和使用的谓词

---

## 步骤 2：任务生成器适配

**目标**：修改实验基础设施以支持跨域组合任务。

### 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| `src/experiment/systems.py` | 新增 `generate_cross_domain_tasks(n)` 函数 |
| `scripts/run_experiment.py` | 新增阶段运行逻辑：跨域任务只在 Stage 2+ 执行（至少 3 域合并后才有意义） |

### 关键设计决策

1. **跨域任务的 objects**：需要合并多个域的对象。例如一个 industrial+retail 任务需要 `{"module_1": "memory_module", "shelf_1": "shelf", "robot": "agent"}`
2. **跨域任务的 init/goal**：init 来自源域谓词，goal 来自目标域谓词。这是制造同义歧义的关键
3. **任务变体生成**：通过对象重命名后缀（`_v0`, `_v1`）生成 n 个变体，与一阶段一致

### 输出

- 修改后的 `src/experiment/systems.py`（新增函数）
- 修改后的 `scripts/run_experiment.py`（新增跨域实验逻辑）

### 验收标准

- `generate_cross_domain_tasks(30)` 能生成 30 个有效跨域任务
- 任务结构（objects/init/goal）与现有框架兼容

---

## 步骤 3：BFS Planner 参数调整

**目标**：确保 planner 参数能区分"可规划"与"不可规划"，不因参数过松或过紧导致假结果。

### 问题分析

当前 BFS 参数：`max_depth=8, nodes_limit=50000, timeout=30s`

- **如果参数太松**（depth=20, nodes=500K）：Expand-Only 也能暴力搜到解，退化被掩盖
- **如果参数太紧**（depth=3, nodes=1000）：Rewrite 也搜不到，看不出差异

### 方案

跨域任务实验使用**两组参数**运行并对比：

| 参数组 | max_depth | nodes_limit | 说明 |
|--------|-----------|-------------|------|
| 标准 | 8 | 50,000 | 与一阶段一致，作为控制条件 |
| 宽松 | 12 | 200,000 | 给更深步骤的任务留空间 |

### 输出

- `solve_bfs()` 增加可选参数传递（或通过全局配置）
- 实验运行器支持多组参数运行

### 验收标准

- 存在部分跨域任务在标准参数下 Expand-Only 不可规划而 Rewrite 可规划
- 宽松参数下两者差距缩小（预期行为，说明差距确实来自搜索空间大小）

---

## 步骤 4：运行跨域实验

**目标**：在 Stage 2/3/4 上运行跨域组合任务实验。

### 实验设计

| 维度 | 配置 |
|------|------|
| 阶段 | S2（3 域）、S3（4 域）、S4（5 域） |
| 系统 | 4 组不变（Baseline, Expand-Only, Expand+Rewrite, Expand+ManualOpt） |
| 任务 | 每阶段 30 个跨域组合任务 |
| Planner 参数 | 标准 + 宽松 两组 |
| 指标 | 可规划率、平均规划时间、平均 plan 长度、BFS 节点数 |

### 新增指标

一阶段没有收集但二阶段需要的：

- **BFS 节点数**：直接反映搜索空间膨胀程度。需改 `solve_bfs()` 返回
- **超时率**：在 nodes_limit 内搜索失败 vs 在 timeout 内失败，区分"搜索空间爆炸"和"本质不可规划"

### 运行流程

```
对每个阶段 ∈ {S2, S3, S4}:
  对每个系统 ∈ {Baseline, EO, ER, MO}:
    sigma = system.setup(stage, sigma_0, deltas)
    对每个参数组 ∈ {standard, relaxed}:
      对每个跨域任务 t:
        task_mapped = remap_task_predicates(t, sigma)
        sigma_pruned = run_task_pruning(sigma, task_mapped)  # 仅 ER
        result = solve_bfs(sigma_pruned, task_mapped, params)
        收集: plannable, plan_length, planning_ms, nodes_explored
```

### 输出

- `results/phase2/summary.json`（主结果）
- `results/phase2/full_results.json`（逐任务结果）

### 验收标准

- Expand-Only 可规划率在跨域任务上低于 Rewrite（预期差距 ≥ 20%）
- 差距随阶段增大（S4 > S3 > S2），因为冗余越多冲突越多

---

## 步骤 5：补充可视化与统计

**目标**：生成二阶段专属图表和统计检验。

### 新增图表

| 图表 | 内容 | 预期效果 |
|------|------|---------|
| Fig 7: 跨域可规划率 | 3 阶段 × 4 系统的可规划率折线 | EO 下降，ER 保持 |
| Fig 8: BFS 节点数 | 箱线图，展示搜索空间差异 | EO 节点数远高于 ER |
| Fig 9: 一阶段 vs 二阶段对比 | 同域任务 vs 跨域任务的可规划率并排对比 | 跨域任务拉开差距 |

### 统计检验

- **McNemar 检验**：配对比较 EO vs ER 在每个任务上是否可规划（2×2 列联表）
- **Fisher 精确检验**：可规划率差异的显著性
- **效应量**：可规划率差值的 95% 置信区间

### 输出

- `scripts/analyze_phase2.py`
- `results/figures/fig7_*.png`, `fig8_*.png`, `fig9_*.png`
- 在 `results/analysis_phase2.md` 中补充统计报告

### 验收标准

- McNemar 检验 p < 0.05（EO vs ER 可规划率差异显著）
- 图表清晰展示差距

---

## 步骤 6：更新 tech-note

**目标**：将二阶段结果写入 tech-note。

### 需更新的章节

| 章节 | 更新内容 |
|------|---------|
| §9.6 | 新增"补充实验：跨域组合任务"段落，附数据表和图引用 |
| §9.6 局限性 | 将"采样任务为模板化生成"改为"已通过跨域组合任务补充验证" |
| §10 实验验证补注 | 补充可规划率保护的经验证据 |
| §13 下一步 | 将"更复杂的任务集"从待办划为已完成 |

### 验收标准

- tech-note 中同时包含复杂度抑制和可规划率保护两条证据线
- 局限性章节诚实记录二阶段仍未覆盖的部分

---

## 风险与应对

| 风险 | 可能性 | 影响 | 应对策略 |
|------|--------|------|---------|
| 跨域任务设计不当，Rewrite 也不可规划 | 中 | 高 | 先在 Rewrite 后的 sigma 上逐一验证每个模板可规划，不可规划的模板不入实验 |
| Expand-Only 也全部可规划（仍然没有差距） | 低 | 高 | 增加任务步数至 6-8 步，或降低 BFS nodes_limit 至 10K 模拟资源受限场景 |
| BFS planner 对所有系统都太弱 | 低 | 中 | 改为 A* 或 FF-style 启发式 planner，但实现成本增加 |
| `remap_task_predicates` 在跨域任务中遗漏映射 | 中 | 中 | 扩展 KNOWN_SYNONYMS 覆盖跨域任务引入的所有谓词别名 |

---

## 预期时间线

| 步骤 | 依赖 | 预估产出 |
|------|------|---------|
| 步骤 1：跨域任务设计 | 无 | 15-20 个任务模板代码 |
| 步骤 2：生成器适配 | 步骤 1 | 修改 2 个文件 |
| 步骤 3：Planner 参数调整 | 无 | 修改 1 个文件 |
| 步骤 4：运行实验 | 步骤 1-3 | JSON 结果文件 |
| 步骤 5：可视化与统计 | 步骤 4 | 3 张图 + 统计报告 |
| 步骤 6：更新 tech-note | 步骤 5 | tech-note 更新 |

> **步骤 1 和 3 可并行。步骤 4 是关键路径。**
