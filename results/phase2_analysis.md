# LCOS-R 二阶段实验分析报告：跨域组合任务

## 1. 实验概况

- **实验目的**: 验证一阶段未能触及的关键预期——Expand-Only 的可规划率因同义谓词歧义在跨域任务中退化，Expand+Rewrite 保护可规划性
- **实验阶段**: 3 (S2-S4, 仅在 3+ 域合并后运行，跨域任务才有意义)
- **实验组**: 4 (Baseline, Expand-Only, Expand+Rewrite, Expand+ManualOpt)
- **跨域任务数**: 18 个模板（4 组）
- **BFS 参数配置**: 2 组（standard: depth=8/50K nodes; relaxed: depth=12/200K nodes）

### 1.1 与一阶段的关系

一阶段验证了 **复杂度抑制**（EO 125 vs ER 115, p=0.0248），但因单步模板任务太简单，所有系统可规划率均为 100%，无法区分 rewrite 对可规划性的保护作用。

二阶段通过设计跨域组合任务，专门暴露同义谓词歧义导致的规划失败。

## 2. 跨域任务设计

### 2.1 核心机制

Expand-Only 的 sigma 中保留了 7 对同义谓词：

| 特化谓词 | 基础谓词 | 来源域 |
|----------|---------|--------|
| `on_shelf` | `on` | retail |
| `on_belt` | `on` | industrial |
| `on_tray` | `on` | restaurant |
| `on_desk` | `on` | office |
| `in_cart` | `in` | retail |
| `sorted_into` | `in` | industrial |
| `in_holder` | `in` | office |

在 Expand+Rewrite 中，这些特化谓词被 Pass 1 统一合并为基础谓词（`on`/`in`）。

### 2.2 失败模式分析

**Type A（同义谓词不可达）**: 当任务 goal 包含特化谓词（如 `on_tray(food, tray)`），但 EO 中没有动作的 effect 产生该谓词时，任务逻辑上不可规划。这不是搜索超时——是因为 goal 表达式涉及的谓词根本不在任何动作的 effect 中。

关键示例：
- `place(obj, tray)` 的 effect 为 `on(obj, tray)`
- `serve(food, tray)` 的 precondition 为 `on_tray(food, tray)`
- EO 中 `on` ≠ `on_tray` → `place` 的 effect 无法满足 `serve` 的 precondition → **规划链断裂**
- ER 中 `on_tray` → `on`，两者统一 → `place` → `serve` 链条通畅

### 2.3 任务模板分组

| 组 | 目标谓词 | 任务数 | 涉及域 | 失败机制 |
|----|---------|--------|--------|----------|
| serve-chain | `served(food)` | 5 | domestic/retail + restaurant | `serve` 需要 `on_tray`，`place` 产生 `on` |
| on\_desk goal | `on_desk(item, desk)` | 5 | domestic/retail/industrial + office | 无 EO 动作产生 `on_desk` |
| on\_belt goal | `on_belt(item, belt)` | 3 | domestic/retail + industrial | 无 EO 动作产生 `on_belt` |
| on\_tray goal | `on_tray(item, tray)` | 5 | domestic/retail + restaurant | 无 EO 动作产生 `on_tray` |

共 18 个任务，覆盖所有 4 类特化 `on` 谓词和 5 个域的两两组合。

## 3. 核心结论

### 3.1 Thesis 验证

**核心 thesis**: Expand-Only（纯堆积）在跨域任务中因同义谓词歧义完全失效；Expand+Rewrite 通过消除歧义恢复规划能力。

- **Expand-Only S4 可规划率**: **0%**（18/18 任务全部失败）
- **Expand+Rewrite S4 可规划率**: **100%**（18/18 任务全部成功, BFS relaxed）
- **风险差**: Δ = 1.00（完全分离）
- **McNemar exact test**: p = 7.63 × 10⁻⁶（极显著）

### 3.2 失败不是搜索不足，是逻辑不可达

EO 在 standard（50K nodes）和 relaxed（200K nodes）两种配置下均为 0%，说明**增加搜索预算无法挽救**——问题出在谓词名不匹配导致的逻辑不可达，而非搜索空间爆炸。

### 3.3 Rewrite 与 ManualOpt 完全一致

ER 和 ManualOpt 在所有 18 个任务、两种 BFS 配置、3 个 stage 上的结果完全相同（可规划率、节点数均一致），进一步确认自动 rewrite 达到了人工优化水平。

## 4. 数据表

### 4.1 可规划率总表（BFS relaxed）

| Stage | Baseline | Expand-Only | Expand+Rewrite | Expand+ManualOpt |
|-------|----------|-------------|----------------|------------------|
| S2 (+Industrial, 3 tasks) | 0% (0/3) | **0% (0/3)** | 100% (3/3) | 100% (3/3) |
| S3 (+Restaurant, 13 tasks) | 0% (0/13) | **0% (0/13)** | 100% (13/13) | 100% (13/13) |
| S4 (+Office, 18 tasks) | 0% (0/18) | **0% (0/18)** | **100% (18/18)** | 100% (18/18) |

### 4.2 BFS 参数敏感性（Stage 4）

| 系统 | standard (8/50K) | relaxed (12/200K) | 差异原因 |
|------|-----------------|-------------------|---------|
| Baseline | 0% (0/18) | 0% (0/18) | 缺乏新域词汇 |
| Expand-Only | 0% (0/18) | 0% (0/18) | 谓词逻辑不可达 |
| Expand+Rewrite | 83% (15/18) | 100% (18/18) | 3 个 crowded 任务需更多节点 |
| Expand+ManualOpt | 83% (15/18) | 100% (18/18) | 同上 |

standard → relaxed 时 ER 从 83% 提升到 100%，说明 3 个含干扰物体的 crowded 变体在紧凑表示下仍需较大搜索空间，但在合理预算内可解。

### 4.3 表示复杂度（Stage 4）

| 系统 | 谓词数 | 规则数 | 动作数 | 类型数 | 总复杂度 | PDDL 行数 |
|------|--------|--------|--------|--------|---------|----------|
| Baseline | 25 | 4 | 26 | 45 | 59 | 170 |
| Expand-Only | 56 | 12 | 45 | 94 | 125 | 298 |
| Expand+Rewrite | 49 | 9 | 45 | 94 | 115 | 291 |
| Expand+ManualOpt | 49 | 8 | 45 | 94 | 114 | 291 |

EO 多出的 7 个谓词正是被 ER 消除的同义谓词——它们是跨域任务失败的直接原因。

### 4.4 搜索代价对比（Stage 4, BFS relaxed）

| 系统 | 中位节点数 | 平均节点数 | 最小 | 最大 |
|------|-----------|-----------|------|------|
| Expand-Only | 200,001 | 200,001 | 200,001 | 200,001 |
| Expand+Rewrite | 40,697 | 46,981 | 11,881 | 188,197 |

ER 的中位搜索节点仅为 EO 节点预算的 **20.3%**，说明紧凑表示不仅恢复可规划性，还大幅降低搜索代价。

### 4.5 分组搜索代价分析（ER, Stage 4, relaxed）

| 任务组 | 任务数 | 平均节点数 | 范围 |
|--------|--------|-----------|------|
| serve-chain | 5 | 17,389 | [11,881, 39,421] |
| on\_desk goal | 5 | 65,595 | [17,563, 188,197] |
| on\_belt goal | 3 | 53,377 | [40,681, 78,531] |
| on\_tray goal | 5 | 54,121 | [38,623, 109,891] |

serve-chain 组搜索代价最低（平均 17K nodes），因为 `serve` 是唯一一个在 precondition 中使用同义谓词的动作，ER 消除歧义后规划路径最直接。on\_desk 组有一个 crowded 变体（6 objects）导致最大节点数达到 188K。

### 4.6 逐任务结果（Stage 4, BFS relaxed）

| 任务 | 组 | EO | ER | EO 节点 | ER 节点 | ER 搜索节省 |
|------|----|----|----|---------|---------|----|
| xd\_serve\_salad | serve | ✗ | ✓ | 200,001 | 11,881 | 94.1% |
| xd\_serve\_fruit | serve | ✗ | ✓ | 200,001 | 11,881 | 94.1% |
| xd\_serve\_noodle | serve | ✗ | ✓ | 200,001 | 11,881 | 94.1% |
| xd\_serve\_dough | serve | ✗ | ✓ | 200,001 | 11,881 | 94.1% |
| xd\_pen\_to\_desk | desk | ✗ | ✓ | 200,001 | 40,697 | 79.7% |
| xd\_form\_to\_desk | desk | ✗ | ✓ | 200,001 | 40,697 | 79.7% |
| xd\_module\_to\_desk | desk | ✗ | ✓ | 200,001 | 40,825 | 79.6% |
| xd\_item\_to\_belt | belt | ✗ | ✓ | 200,001 | 40,681 | 79.7% |
| xd\_snack\_to\_belt | belt | ✗ | ✓ | 200,001 | 40,921 | 79.5% |
| xd\_cup\_to\_tray | tray | ✗ | ✓ | 200,001 | 40,697 | 79.7% |
| xd\_fruit\_to\_tray | tray | ✗ | ✓ | 200,001 | 40,697 | 79.7% |
| xd\_serve\_crowded | serve | ✗ | ✓ | 200,001 | 39,421 | 80.3% |
| xd\_desk\_crowded | desk | ✗ | ✓ | 200,001 | 188,197 | 5.9% |
| xd\_lift\_to\_desk | desk | ✗ | ✓ | 200,001 | 17,563 | 91.2% |
| xd\_belt\_crowded | belt | ✗ | ✓ | 200,001 | 78,531 | 60.7% |
| xd\_tray\_crowded | tray | ✗ | ✓ | 200,001 | 109,891 | 45.1% |
| xd\_fold\_to\_tray | tray | ✗ | ✓ | 200,001 | 38,623 | 80.7% |
| xd\_triple\_chain | tray | ✗ | ✓ | 200,001 | 40,697 | 79.7% |

所有 18 个任务均呈现 **EO 失败 + ER 成功** 的一致模式。ER 的平均搜索节省为 **76.5%**。

## 5. 统计检验

### 5.1 McNemar Exact Test（EO vs ER, Stage 4, relaxed）

配对 2×2 列联表：

|  | ER pass | ER fail |
|--|---------|---------|
| **EO pass** | 0 | 0 |
| **EO fail** | 18 | 0 |

- 不一致对 (discordant pairs): b + c = 0 + 18 = 18
- McNemar exact p = 7.63 × 10⁻⁶

**结论**: EO 和 ER 的可规划性差异极其显著。所有 18 个不一致对均为"EO 失败 + ER 成功"，没有反方向的案例。

### 5.2 效应量

- **风险差（Risk Difference）**: Δ = 1.0000
- **95% 置信区间**: [1.0000, 1.0000]
- **NNT (Number Needed to Treat)**: 1.0（每应用 1 次 rewrite 即可挽救 1 个任务）

由于 EO 0%、ER 100% 是完全分离的极端情况，Wald CI 退化为点估计。实际上，使用精确二项 CI 对单侧边界更准确——但即使最保守的估计，p 值也远低于任何常规阈值。

### 5.3 与一阶段统计结果对比

| 检验 | 一阶段（复杂度） | 二阶段（可规划率） |
|------|-----------------|-------------------|
| 检验方法 | 配对 t 检验 | McNemar exact test |
| p 值 | 0.0248 | 7.63 × 10⁻⁶ |
| 效应量 | Cohen's d = 2.42 | Δ = 1.00 |
| 方向 | ER 复杂度更低 | ER 可规划率更高 |
| 样本量 | Stage 1-4, n=4 对 | 18 个跨域任务 |

## 6. 图表

- Fig 7: [跨域可规划率](figures/fig7_xd_plannable.png) — 分阶段 × 系统组的可规划率分组柱状图
- Fig 8: [BFS 搜索节点箱线图](figures/fig8_nodes_boxplot.png) — EO vs ER 搜索代价对比
- Fig 9: [BFS 预算效应](figures/fig9_bfs_budget.png) — standard vs relaxed 配置下 ER 的可规划率变化

## 7. 结论与限制

### 7.1 支持 thesis 的证据

结合两阶段实验，核心 thesis 获得了两条独立证据线的支持：

1. **复杂度抑制**（一阶段）: EO 复杂度 125 vs ER 115, p = 0.0248, Cohen's d = 2.42
2. **可规划性保护**（二阶段）: EO 可规划率 0% vs ER 100%, p = 7.63 × 10⁻⁶, Δ = 1.00

这两条证据线互补：
- 一阶段证明 **rewrite 压缩了表示**
- 二阶段证明 **压缩的表示带来了规划能力保护**

即"rewrite 不只是减少了数字，它实质性地保护了系统在跨域扩展后的功能完整性"。

### 7.2 Expand-Only 失败的根本原因

EO 的失败**不是搜索能力不足**（增加 4 倍节点预算后仍为 0%），而是**逻辑上不可达**：

- 5 域合并后，EO 的 sigma 中同时存在 `on` 和 `on_tray`、`on_desk`、`on_belt` 等特化谓词
- 通用动作（如 `place`）只能产生基础谓词 `on`
- 特化谓词 `on_tray`/`on_desk`/`on_belt` 没有任何动作能产生它们
- 当 goal 包含特化谓词时，规划器穷举所有动作组合也找不到解

这正是"规则堆积"（纯合并不做重写）的核心危害：名义上系统"知道更多"，实际上内部表示的不一致导致能力退化。

### 7.3 局限性

1. **跨域任务为人工构造**: 任务模板基于对 EO sigma 的分析设计，目的是暴露已知的同义谓词歧义。真实场景中的跨域冲突可能更多样
2. **EO 失败是确定性的**: 0% vs 100% 的完全分离过于极端，在真实场景中更可能是梯度退化（如 70% → 40%）
3. **仅测试 Type A 失败模式**: 当前所有 18 个任务均为同义谓词不可达（Type A），未涉及约束冲突（Type B）或纯搜索空间爆炸（Type C）
4. **BFS planner 局限**: crowded 变体在 standard 配置下连 ER 也失败（3/18），说明 BFS 在有干扰物体时搜索效率有限，更高效的规划器（如 FF/LAMA）可能改善
5. **实验仍在 PDDL 层**: 未涉及物理执行和感知不确定性
6. **ER = ManualOpt 结果过于一致**: 二者在所有配置下结果完全相同，这是因为 Pass 1 的同义谓词消除是确定性的且涵盖了所有失败原因；更复杂的场景中两者可能出现差异

### 7.4 两阶段综合判断

> **Rewrite 的价值不仅在于"把 125 压到 115"，更在于"把 0% 拉回 100%"。**
> 一阶段展示了量变（复杂度抑制），二阶段展示了质变（可规划性恢复）。
> 两者共同支持核心 thesis：开放扩展不做 rewrite 就是规则堆积，做了 rewrite 才是结构升级。