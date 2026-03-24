# Phase 2 Analysis: Cross-Domain Tasks

## Audit Scope

- 当前实现覆盖 30 个跨域组合任务，其中 Stage 4 为 18 个 Type A、6 个 Type B、6 个 Type C。
- 任务按最小所需域逐级开放，因此 S2/S3/S4 的实际任务数分别为 3/20/30。
- 二阶段实验由 scripts/run_phase2.py 独立执行，结果写入 results/phase2/，分析报告写入 results/phase2_analysis.md。
- Type B 当前实现为动作前置条件接续失败；Type C 当前实现为高干扰单目标搜索压力任务，而不是多目标深链。

## Plannable Rate Summary

| Stage | System | BFS Config | Plannable | Rate |
|-------|--------|------------|-----------|------|
| 2 | Baseline | relaxed | 0/3 | 0% |
| 2 | Baseline | standard | 0/3 | 0% |
| 2 | Expand+ManualOpt | relaxed | 3/3 | 100% |
| 2 | Expand+ManualOpt | standard | 2/3 | 67% |
| 2 | Expand+Rewrite | relaxed | 3/3 | 100% |
| 2 | Expand+Rewrite | standard | 2/3 | 67% |
| 2 | Expand-Only | relaxed | 0/3 | 0% |
| 2 | Expand-Only | standard | 0/3 | 0% |
| 3 | Baseline | relaxed | 0/20 | 0% |
| 3 | Baseline | standard | 0/20 | 0% |
| 3 | Expand+ManualOpt | relaxed | 20/20 | 100% |
| 3 | Expand+ManualOpt | standard | 16/20 | 80% |
| 3 | Expand+Rewrite | relaxed | 20/20 | 100% |
| 3 | Expand+Rewrite | standard | 16/20 | 80% |
| 3 | Expand-Only | relaxed | 0/20 | 0% |
| 3 | Expand-Only | standard | 0/20 | 0% |
| 4 | Baseline | relaxed | 0/30 | 0% |
| 4 | Baseline | standard | 0/30 | 0% |
| 4 | Expand+ManualOpt | relaxed | 30/30 | 100% |
| 4 | Expand+ManualOpt | standard | 23/30 | 77% |
| 4 | Expand+Rewrite | relaxed | 30/30 | 100% |
| 4 | Expand+Rewrite | standard | 23/30 | 77% |
| 4 | Expand-Only | relaxed | 0/30 | 0% |
| 4 | Expand-Only | standard | 0/30 | 0% |

## Key Findings

- **EO plannable rate**: 0% (all 30 cross-domain tasks fail)
- **ER plannable rate**: 100% (alias and precondition handoff gaps eliminated by rewrite)
- **McNemar p-value**: 1.86e-09
- **Risk difference**: 1.0000 (95% CI: [1.0000, 1.0000])
- **Coverage**: Stage 4 includes A/B/C = 18/6/6.
- **BFS budget effect**: Stage 4 下 ER 从 standard 的 77% 提升到 relaxed 的 100%，EO 在两组预算下均为 0%。

## Per-Task Results (Stage 4, relaxed)

| Task | EO | ER | EO nodes | ER nodes |
|------|----|----|----------|----------|
| xd_serve_salad | ✗ | ✓ | 200,001 | 11,881 |
| xd_serve_fruit | ✗ | ✓ | 200,001 | 11,881 |
| xd_serve_noodle | ✗ | ✓ | 200,001 | 11,881 |
| xd_serve_dough | ✗ | ✓ | 200,001 | 11,881 |
| xd_pen_to_desk | ✗ | ✓ | 200,001 | 40,697 |
| xd_form_to_desk | ✗ | ✓ | 200,001 | 40,697 |
| xd_module_to_desk | ✗ | ✓ | 200,001 | 40,825 |
| xd_item_to_belt | ✗ | ✓ | 200,001 | 40,681 |
| xd_snack_to_belt | ✗ | ✓ | 200,001 | 40,921 |
| xd_cup_to_tray | ✗ | ✓ | 200,001 | 40,697 |
| xd_fruit_to_tray | ✗ | ✓ | 200,001 | 40,697 |
| xd_serve_crowded | ✗ | ✓ | 200,001 | 39,421 |
| xd_desk_crowded | ✗ | ✓ | 200,001 | 188,197 |
| xd_lift_to_desk | ✗ | ✓ | 200,001 | 17,563 |
| xd_belt_crowded | ✗ | ✓ | 200,001 | 78,531 |
| xd_tray_crowded | ✗ | ✓ | 200,001 | 109,891 |
| xd_fold_to_tray | ✗ | ✓ | 200,001 | 38,623 |
| xd_triple_chain | ✗ | ✓ | 200,001 | 40,697 |
| xd_shelf_serve_fruit | ✗ | ✓ | 200,001 | 5,179 |
| xd_shelf_serve_snack | ✗ | ✓ | 200,001 | 5,239 |
| xd_desk_serve_salad | ✗ | ✓ | 200,001 | 5,179 |
| xd_desk_serve_dough | ✗ | ✓ | 200,001 | 5,179 |
| xd_belt_serve_noodle | ✗ | ✓ | 200,001 | 5,239 |
| xd_belt_serve_fruit | ✗ | ✓ | 200,001 | 5,239 |
| xd_shelf_serve_crowded | ✗ | ✓ | 200,001 | 22,751 |
| xd_desk_serve_crowded | ✗ | ✓ | 200,001 | 12,025 |
| xd_shelf_to_desk_crowded | ✗ | ✓ | 200,001 | 80,587 |
| xd_belt_to_desk_crowded | ✗ | ✓ | 200,001 | 80,749 |
| xd_shelf_to_tray_crowded | ✗ | ✓ | 200,001 | 109,891 |
| xd_belt_to_tray_crowded | ✗ | ✓ | 200,001 | 80,749 |