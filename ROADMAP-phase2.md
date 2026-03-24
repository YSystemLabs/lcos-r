# LCOS-R 二阶段实验路线图

> **状态：已完成** ✅ 所有 6 个步骤均已执行。结果已写入 tech-note §9.7。

## 背景：一阶段遗留的问题

### 当前已确认的事实

当前一阶段的稳妥结论不是“已经证明跨域可规划性保护”，而是：

- **复杂度抑制**：Expand+Rewrite（115）显著低于 Expand-Only（125），配对 t 检验 p=0.0248，Cohen's d=2.42
- **自动 rewrite ≈ 人工优化**：ManualOpt（114）与 Rewrite（115）无显著差异（p=0.0577）
- **Baseline 失效**：Baseline 在新领域可规划率降至 0%
- **Pass 3 已按任务级验证**：S1-S4 的 Expand+Rewrite 逐任务验证率为 100%
- **一阶段职责边界明确**：Phase 1 主要验证“表示是否膨胀、rewrite 是否抑制膨胀”，不单独承担“跨域可规划性保护”的证明任务

### 当前仍未回答的问题

| 预期 | 实际结果 | 原因 |
|------|---------|------|
| Expand-Only 可规划率随扩展下降 | **未观察到**，全部 100% | 任务太简单 |
| Rewrite 对可规划率有保护作用 | **无法区分**，因为都是 100% | 同上 |
| 自动 rewrite 是否已一般性保护跨域规划 | **未验证** | 一阶段任务分布不包含专门构造的跨域失败模式 |

### 当前问题为什么会留下来

一阶段的问题不在于“实验完全没做对”，而在于它的任务分布只足以回答复杂度问题，不足以回答跨域可规划性问题。一阶段的 30 个任务/域全部是**模板化的 1-2 步单域任务**（如 `pick(cup)` → `place(cup, table)`）。这导致：

1. **搜索深度 ≤ 2**：BFS 在深度 1-2 就找到解，根本碰不到因冗余谓词导致的状态空间膨胀区域
2. **无跨域交互**：每个任务只涉及单一领域的谓词/动作，不会触发跨域约束冲突
3. **同义谓词歧义无影响**：单步任务的 init 和 goal 始终使用同一领域的谓词（如零售只用 `on_shelf`），不存在 init 用 `on_shelf` 而 goal 用 `on` 的歧义场景
4. **一期高可规划率的解释边界有限**：Expand-Only / Rewrite / ManualOpt 的 100% 主要说明“当前单域采样任务可以被当前签名和 planner 正常求解”，不能推出“Expand-Only 在跨域任务上不会退化”

**当前遗留问题**：一阶段已经提供了 rewrite 抑制复杂度增长的必要证据，但还没有提供“rewrite 对跨域可规划性保护”的直接证据；这正是二阶段需要补上的部分。

---

## 二阶段目标

本阶段通过**跨域组合任务实验**，验证：

> **在当前实现的跨域任务上，Expand-Only 会因别名裂解与接续失败而失去可规划性，而 Expand+Rewrite 能恢复这些任务的可规划性。**

---

## 步骤 1：跨域组合任务设计

**本步目标**：设计能暴露 Expand-Only 退化的跨域组合任务模板，并保证这些模板在当前 planner 下可复现。

### 输入

- 5 域语义签名（`data/signatures/*.json`）
- 7 对同义谓词：`on_shelf→on`, `on_belt→on`, `on_tray→on`, `on_desk→on`, `in_cart→in`, `sorted_into→in`, `in_holder→in`
- 各域动作模板和约束（`scripts/build_signatures.py`）

### 实施原则

本阶段当前落地为三类任务：

#### 类型 A：同义谓词歧义任务

- 任务的 init 使用某域特有谓词（如 `on_shelf(obj, shelf)`），goal 使用基础谓词（如 `on(obj, table)`）或另一域谓词（如 `on_desk(obj, desk)`）
- **在 Expand-Only 中**：`on_shelf` 和 `on` 是两个不同谓词，planner 找不到从一个到另一个的动作链
- **在 Rewrite 中**：`on_shelf` 已合并为 `on`，planner 直接识别为同一谓词

#### 类型 B：动作前置条件接续失败任务

- 任务的 init 使用某域位置谓词（如 `on_shelf`、`on_desk`、`on_belt`），而关键动作前置条件使用另一域位置谓词（如 `on_tray`）
- **在 Expand-Only 中**：动作前置条件无法从 init 事实直接接续，planner 因谓词名不匹配而失败
- **在 Rewrite 中**：这些位置谓词被统一为 `on`，动作前置条件可直接接续
- **说明**：原路线图设想的“显式约束冲突型 Type B”没有落地，因为当前 planner 不消费 `C_t`

#### 类型 C：高干扰单目标任务（搜索压力触发）

- 任务仍然以单一主目标为中心，但加入额外对象与可选绑定，提升 grounding 分支数
- **在 Expand-Only 中**：别名裂解仍然阻断主路径，且额外对象会增加搜索压力
- **在 Rewrite 中**：别名裂解被消除，relaxed 预算下可恢复全部任务
- **说明**：原路线图设想的“多目标深链 Type C”在当前 planner 下不稳定，因此本轮实现先收敛为高干扰单目标版本

### 当前实现

- 在 `src/experiment/systems.py` 中扩展 `generate_cross_domain_tasks()`
- 当前 Stage 4 共 30 个模板：Type A 18 个，Type B 6 个，Type C 6 个
- 每个模板附带注释说明其触发的退化类型（A/B/C）

### 验收口径

- 当前 30 个模板在 Stage 4 的 Expand+Rewrite / Expand+ManualOpt relaxed 条件下全部可规划
- 模板能明确标注任务涉及的域与退化类型

---

## 步骤 2：任务生成器适配

**本步目标**：修改实验基础设施以支持跨域组合任务。

### 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| `src/experiment/systems.py` | 新增 `generate_cross_domain_tasks(n)` 函数 |
| `scripts/run_phase2.py` | 独立执行二阶段实验；跨域任务按最小所需域在 Stage 2+ 逐步开放 |

### 实施要点

1. **跨域任务的 objects**：需要合并多个域的对象。例如一个 industrial+retail 任务需要 `{"module_1": "memory_module", "shelf_1": "shelf", "robot": "agent"}`
2. **跨域任务的 init/goal**：init 来自源域谓词，goal 来自目标域谓词。这是制造同义歧义的关键
3. **任务变体生成**：通过对象重命名后缀（`_v0`, `_v1`）生成 n 个变体，与一阶段一致

### 当前实现

- 修改后的 `src/experiment/systems.py`（扩展跨域任务模板）
- 修改后的 `scripts/run_phase2.py`（默认运行当前全部跨域模板）

### 验收口径

- `generate_cross_domain_tasks()` 默认生成当前全部模板；Stage 4 为 30 个任务
- 任务结构（objects/init/goal/degrade_type/involved_domains）与现有框架兼容

---

## 步骤 3：BFS Planner 参数调整

**本步目标**：确保 planner 参数能区分“可规划”与“不可规划”，不因参数过松或过紧导致假结果。

### 当前约束

当前 BFS 参数：`max_depth=8, nodes_limit=50000, timeout=30s`

- **如果参数太松**（depth=20, nodes=500K）：Expand-Only 也能暴力搜到解，退化被掩盖
- **如果参数太紧**（depth=3, nodes=1000）：Rewrite 也搜不到，看不出差异

### 当前实现

跨域任务实验使用**两组参数**运行并对比：

| 参数组 | max_depth | nodes_limit | 说明 |
|--------|-----------|-------------|------|
| 标准 | 8 | 50,000 | 与一阶段一致，作为控制条件 |
| 宽松 | 12 | 200,000 | 给更深步骤的任务留空间 |

### 当前实现结果

- `solve_bfs()` 增加可选参数传递（或通过全局配置）
- 实验运行器支持多组参数运行

### 验收口径

- 存在部分跨域任务在标准参数下 Expand-Only 不可规划而 Rewrite 可规划
- 当前实现结果为：Stage 4 下 ER 从 standard 的 23/30 提升到 relaxed 的 30/30，EO 在两组参数下都为 0/30
- 这说明 relaxed 预算主要补足了 Type C 高干扰任务，而 EO 的主导失败机制仍是表示断裂

---

## 步骤 4：运行跨域实验

**本步目标**：在 Stage 2/3/4 上运行跨域组合任务实验。

### 实验配置

| 维度 | 配置 |
|------|------|
| 阶段 | S2（3 域）、S3（4 域）、S4（5 域） |
| 系统 | 4 组不变（Baseline, Expand-Only, Expand+Rewrite, Expand+ManualOpt） |
| 任务 | 按阶段逐步开放：S2=3，S3=20，S4=30 |
| Planner 参数 | 标准 + 宽松 两组 |
| 指标 | 可规划率、plan 长度、规划时间、BFS 节点数 |

### 观测指标

一阶段没有收集但二阶段需要的：

- **BFS 节点数**：直接反映搜索空间膨胀程度。需改 `solve_bfs()` 返回
- **超时率**：在 nodes_limit 内搜索失败 vs 在 timeout 内失败，区分"搜索空间爆炸"和"本质不可规划"

### 执行流程

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

### 当前实现

- `results/phase2/summary.json`（主结果）
- `results/phase2/full_results.json`（逐任务结果）

### 当前结果

| Stage | BFS | Baseline | EO | ER | ManualOpt |
|------|-----|----------|----|----|-----------|
| S2 | standard | 0/3 | 0/3 | 2/3 | 2/3 |
| S2 | relaxed | 0/3 | 0/3 | 3/3 | 3/3 |
| S3 | standard | 0/20 | 0/20 | 16/20 | 16/20 |
| S3 | relaxed | 0/20 | 0/20 | 20/20 | 20/20 |
| S4 | standard | 0/30 | 0/30 | 23/30 | 23/30 |
| S4 | relaxed | 0/30 | 0/30 | 30/30 | 30/30 |

### 验收口径

- Expand-Only 可规划率在跨域任务上显著低于 Rewrite
- 当前实现下，Stage 4 relaxed 已达到 EO 0/30 vs ER 30/30
- Stage 4 standard 与 relaxed 的差异主要体现在 ER 对 Type C 压力任务的恢复，而不是 EO 的恢复

---

## 步骤 5：补充可视化与统计

**本步目标**：生成二阶段专属图表和统计检验。

### 图表配置

| 图表 | 内容 | 预期效果 |
|------|------|---------|
| Fig 7: 跨域可规划率 | 3 阶段 × 4 系统的可规划率折线 | EO 下降，ER 保持 |
| Fig 8: BFS 节点数 | 箱线图，展示搜索空间差异 | EO 节点数远高于 ER |
| Fig 9: BFS 预算效应 | ER 在 standard / relaxed 下的可规划率对比 | relaxed 补足高压力任务 |

### 统计方法

- **McNemar 检验**：配对比较 EO vs ER 在每个任务上是否可规划（2×2 列联表）
- **Fisher 精确检验**：可规划率差异的显著性
- **效应量**：可规划率差值的 95% 置信区间

### 当前实现

- `scripts/analyze_phase2.py`
- `results/figures/fig7_*.png`, `fig8_*.png`, `fig9_*.png`
- 在 `results/phase2_analysis.md` 中补充统计报告

### 当前统计结果

- Stage 4 relaxed：EO 0/30，ER 30/30
- McNemar exact test：`p = 1.86e-09`
- 风险差：`1.0000`
- 95% CI：`[1.0000, 1.0000]`

### 验收口径

- McNemar 检验 p < 0.05（EO vs ER 可规划率差异显著）
- 图表清晰展示差距

---

## 步骤 6：更新 tech-note

**本步目标**：将二阶段结果写入 tech-note。

### 更新范围

| 章节 | 更新内容 |
|------|---------|
| §9.7 | 写入二阶段跨域组合任务结果，附数据表和统计值 |
| §9.7 局限性 | 写明当前 Type B / Type C 的实现边界 |
| §10 实验验证补注 | 补充可规划率保护的经验证据 |
| §13 下一步 | 将"更复杂的任务集"从待办划为已完成 |

### 验收口径

- tech-note 中同时包含复杂度抑制和可规划率保护两条证据线
- 第 9.7 节已更新为当前 30 个 A/B/C 任务版本
- 局限性章节诚实记录当前 Type B / Type C 仍未完全达到原始理想设计

---

## 风险与应对

| 风险 | 可能性 | 影响 | 应对策略 |
|------|--------|------|---------|
| 跨域任务设计不当，Rewrite 也不可规划 | 中 | 高 | 先在 Rewrite 后的 sigma 上逐一验证每个模板可规划，不可规划的模板不入实验 |
| Expand-Only 也全部可规划（仍然没有差距） | 低 | 高 | 增加任务步数至 6-8 步，或降低 BFS nodes_limit 至 10K 模拟资源受限场景 |
| BFS planner 对所有系统都太弱 | 低 | 中 | 改为 A* 或 FF-style 启发式 planner，但实现成本增加 |
| `remap_task_predicates` 在跨域任务中遗漏映射 | 中 | 中 | 扩展 KNOWN_SYNONYMS 覆盖跨域任务引入的所有谓词别名 |
| 当前 planner 不消费 `C_t` 约束 | 高 | 中 | 将 Type B 暂时实现为动作前置条件接续失败，而不是显式约束冲突 |
| 多目标深链在当前 BFS 下不稳定 | 中 | 中 | 将 Type C 暂时收敛为高干扰单目标搜索压力任务 |

---

## 当前实施节奏

| 步骤 | 依赖 | 预估产出 |
|------|------|---------|
| 步骤 1：跨域任务设计 | 无 | 30 个任务模板（A=18, B=6, C=6） |
| 步骤 2：生成器适配 | 步骤 1 | 修改 2 个文件 |
| 步骤 3：Planner 参数调整 | 无 | 修改 1 个文件 |
| 步骤 4：运行实验 | 步骤 1-3 | JSON 结果文件 |
| 步骤 5：可视化与统计 | 步骤 4 | 3 张图 + 统计报告 |
| 步骤 6：更新 tech-note | 步骤 5 | tech-note 更新 |

> **步骤 1 和 3 可并行。步骤 4 是关键路径。**
