# Phase 2 Analysis: Cross-Domain Tasks

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
| 3 | Baseline | relaxed | 0/13 | 0% |
| 3 | Baseline | standard | 0/13 | 0% |
| 3 | Expand+ManualOpt | relaxed | 13/13 | 100% |
| 3 | Expand+ManualOpt | standard | 11/13 | 85% |
| 3 | Expand+Rewrite | relaxed | 13/13 | 100% |
| 3 | Expand+Rewrite | standard | 11/13 | 85% |
| 3 | Expand-Only | relaxed | 0/13 | 0% |
| 3 | Expand-Only | standard | 0/13 | 0% |
| 4 | Baseline | relaxed | 0/18 | 0% |
| 4 | Baseline | standard | 0/18 | 0% |
| 4 | Expand+ManualOpt | relaxed | 18/18 | 100% |
| 4 | Expand+ManualOpt | standard | 15/18 | 83% |
| 4 | Expand+Rewrite | relaxed | 18/18 | 100% |
| 4 | Expand+Rewrite | standard | 15/18 | 83% |
| 4 | Expand-Only | relaxed | 0/18 | 0% |
| 4 | Expand-Only | standard | 0/18 | 0% |

## Key Findings

- **EO plannable rate**: 0% (all 18 cross-domain tasks fail)
- **ER plannable rate**: 100% (synonym gap eliminated by rewrite)
- **McNemar p-value**: 8.00e-06
- **Risk difference**: 1.0000 (95% CI: [1.0000, 1.0000])

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