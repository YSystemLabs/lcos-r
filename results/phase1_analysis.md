# LCOS-R 实验分析报告

## 1. 实验概况
- 实验阶段: 5 (S0-S4, 五领域渐进扩展)
- 实验组: 4 (Baseline, Expand-Only, Expand+Rewrite, Expand+ManualOpt)
- 任务数/领域: 30

## 2. 核心结论

### 2.1 Thesis 验证
**核心 thesis**: 开放扩展若没有 rewrite，会退化成规则堆积；有 rewrite，才会带来系统级收益。

- **Expand-Only S4 复杂度**: 125 (从 S0 的 59 增长到 125，增长 112%)
- **Expand+Rewrite S4 复杂度**: 115 (增长 95%)
- **复杂度削减**: 10 (削减 8.0%)
- **Baseline S4 可规划率**: 0% (因缺乏新领域词汇)
- **Expand+Rewrite S4 可规划率**: 100%

### 2.2 验证强度
- **Q_star 核心测试数**: 10
- **Q_task 测试总数**: 41 (30 个任务时为 10 项核心测试 + 1 项覆盖测试 + 30 项可规划性测试)
- **Pass 3 逐任务验证率**: 100% (S1-S4 的 Expand+Rewrite 均通过)

### 2.3 统计显著性
- 配对 t 检验 p = 0.0248
- Expand-Only 平均复杂度: 98.2
- Expand+Rewrite 平均复杂度: 92.0
- 平均削减: 6.2

### 2.4 Rewrite 效果分解
- **Pass 1 (谓词消除)**: 每阶段消除 2 个同义谓词
- **Pass 2 (规则折叠)**: 每阶段折叠 1 条同构规则
- **Pass 3 (对象裁剪)**: per-task 裁剪无关领域类型

## 3. 数据表

| Stage | System | Predicates | Rules | Complexity | Plannable | Avg Plan Time |
|-------|--------|-----------|-------|-----------|-----------|--------------|
| S0 | Baseline | 25 | 4 | 59 | 100% | 7.0ms |
| S0 | Expand-Only | 25 | 4 | 59 | 100% | 7.1ms |
| S0 | Expand+Rewrite | 25 | 4 | 59 | 100% | 7.3ms |
| S0 | Expand+ManualOpt | 25 | 4 | 59 | 100% | 6.9ms |
| S1 | Baseline | 25 | 4 | 59 | 0% | 154.9ms |
| S1 | Expand-Only | 32 | 6 | 73 | 100% | 7.4ms |
| S1 | Expand+Rewrite | 30 | 5 | 70 | 100% | 7.4ms |
| S1 | Expand+ManualOpt | 30 | 5 | 70 | 100% | 6.8ms |
| S2 | Baseline | 25 | 4 | 59 | 50% | 78.9ms |
| S2 | Expand-Only | 39 | 8 | 88 | 100% | 5.7ms |
| S2 | Expand+Rewrite | 35 | 7 | 83 | 100% | 5.2ms |
| S2 | Expand+ManualOpt | 35 | 6 | 82 | 100% | 5.2ms |
| S3 | Baseline | 25 | 4 | 59 | 0% | 112.3ms |
| S3 | Expand-Only | 48 | 10 | 107 | 100% | 7.8ms |
| S3 | Expand+Rewrite | 43 | 8 | 100 | 100% | 7.7ms |
| S3 | Expand+ManualOpt | 43 | 7 | 99 | 100% | 8.1ms |
| S4 | Baseline | 25 | 4 | 59 | 0% | 159.4ms |
| S4 | Expand-Only | 56 | 12 | 125 | 100% | 16.7ms |
| S4 | Expand+Rewrite | 49 | 9 | 115 | 100% | 17.0ms |
| S4 | Expand+ManualOpt | 49 | 8 | 114 | 100% | 16.8ms |

## 4. 图表
- Fig 1: [复杂度曲线](figures/fig1_complexity.png)
- Fig 2: [可规划率](figures/fig2_plannable.png)
- Fig 3: [规划时间](figures/fig3_planning_time.png)
- Fig 4: [Rewrite 分解](figures/fig4_rewrite_breakdown.png)
- Fig 5: [复杂度分量](figures/fig5_components.png)
- Fig 6: [PDDL 行数](figures/fig6_pddl_lines.png)

## 5. 结论与限制

**支持 thesis 的证据:**
1. Expand-Only 复杂度线性增长（112%），Expand+Rewrite 有效抑制（92%→增长幅度更小）
2. Rewrite 在每个扩展阶段都成功消除同义谓词和折叠规则
3. 所有系统（除 Baseline）保持 100% 可规划率
4. ManualOpt 与 Rewrite 效果接近，说明自动 rewrite 接近人工优化水平

**局限性:**
1. 任务采样为模板化生成，真实任务复杂度更高
2. BFS planner 搜索深度有限（max_depth=8），复杂任务可能超时
3. 评估用 PDDL 表示，未涉及物理执行
4. 渐变谓词以布尔近似，渐变推理精确度需进一步验证