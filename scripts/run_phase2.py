#!/usr/bin/env python3
"""
二阶段实验：跨域组合任务。
验证 Expand-Only 的可规划率因同义谓词歧义退化，Rewrite 保护可规划性。
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core import SemanticSignature
from src.experiment.systems import (
    ALL_SYSTEMS, CROSS_DOMAIN_TEMPLATES, DOMAINS, load_sigma_0, load_deltas,
    generate_cross_domain_tasks,
)
from src.experiment.metrics import collect_complexity_metrics
from src.core.pddl_generator import generate_domain, generate_problem, solve_bfs
from src.rewrite.engine import run_global_rewrite, run_task_pruning
from src.rewrite.pass1_predicate_elimination import KNOWN_SYNONYMS

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "phase2"

# 域名 → 最小 stage（需要已合并该域）
DOMAIN_STAGE = {d: i for i, d in enumerate(DOMAINS)}


def min_stage_for_task(task):
    """返回任务所需的最小 stage（所有涉及域都已合并）。"""
    return max(DOMAIN_STAGE.get(d, 0) for d in task.get("involved_domains", []))


def remap_task_predicates(task, sigma):
    """将任务中的谓词名映射到 sigma 中已有的谓词。"""
    import copy
    known_preds = sigma.predicate_names()
    task = copy.deepcopy(task)
    for p_list in [task["init"], task["goal"]]:
        for p in p_list:
            if p.name not in known_preds and p.name in KNOWN_SYNONYMS:
                p.name = KNOWN_SYNONYMS[p.name]
    return task


def plan_task(sigma, task, max_depth=8, nodes_limit=50000, timeout_ms=10000):
    """对单个任务运行 BFS 规划。"""
    domain_str = generate_domain(sigma)
    problem_str = generate_problem(
        sigma, task["name"], "lcos-r",
        task["objects"], task["init"], task["goal"],
    )
    plan, plan_time, success, nodes = solve_bfs(
        domain_str, problem_str, timeout_ms,
        max_depth=max_depth, nodes_limit=nodes_limit,
    )
    return {
        "plannable": success,
        "plan_length": len(plan) if success else -1,
        "planning_ms": round(plan_time, 2),
        "nodes_explored": nodes,
        "plan": [str(a) for a in plan] if success else [],
    }


# BFS 参数配置
BFS_CONFIGS = {
    "standard": {"max_depth": 8, "nodes_limit": 50000},
    "relaxed":  {"max_depth": 12, "nodes_limit": 200000},
}


def run_phase2(n_tasks=None):
    """运行二阶段跨域实验。"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    sigma_0 = load_sigma_0()
    deltas = load_deltas()
    tasks = generate_cross_domain_tasks(n_tasks)

    print(f"Generated {len(tasks)} cross-domain tasks")
    print(f"Systems: {[s.name for s in ALL_SYSTEMS]}")
    print(f"BFS configs: {list(BFS_CONFIGS.keys())}")

    all_results = []
    total_start = time.time()

    for stage in range(5):
        # 筛选本 stage 可运行的任务
        stage_tasks = [t for t in tasks if min_stage_for_task(t) <= stage]
        if not stage_tasks:
            print(f"\nStage {stage}: no eligible cross-domain tasks, skipping")
            continue

        print(f"\n{'='*60}")
        print(f"Stage {stage}: {'+'.join(DOMAINS[:stage+1])} "
              f"({len(stage_tasks)} tasks)")
        print(f"{'='*60}")

        for system in ALL_SYSTEMS:
            sigma = system.setup(stage, sigma_0, deltas)
            complexity = collect_complexity_metrics(sigma)

            for bfs_name, bfs_cfg in BFS_CONFIGS.items():
                plannable_count = 0
                total_nodes = 0
                task_details = []

                for task in stage_tasks:
                    # 对 ER/ManualOpt 进行谓词重映射
                    if system.name in ("Expand+Rewrite", "Expand+ManualOpt") and stage > 0:
                        task_m = remap_task_predicates(task, sigma)
                    else:
                        task_m = task

                    # Per-task pruning for ER
                    if system.name == "Expand+Rewrite" and stage > 0:
                        sigma_t, _ = run_task_pruning(sigma, task_m)
                    else:
                        sigma_t = sigma

                    pm = plan_task(sigma_t, task_m, **bfs_cfg)

                    if pm["plannable"]:
                        plannable_count += 1
                    total_nodes += pm["nodes_explored"]

                    task_details.append({
                        "task": task["name"],
                        "degrade_type": task.get("degrade_type", ""),
                        "involved_domains": task.get("involved_domains", []),
                        **pm,
                    })

                plannable_rate = plannable_count / len(stage_tasks)

                result = {
                    "stage": stage,
                    "system": system.name,
                    "bfs_config": bfs_name,
                    **complexity,
                    "plannable_rate": round(plannable_rate, 4),
                    "plannable_count": plannable_count,
                    "total_tasks": len(stage_tasks),
                    "avg_nodes": round(total_nodes / len(stage_tasks)),
                    "task_results": task_details,
                }
                all_results.append(result)

                print(f"  {system.name:20s} [{bfs_name:8s}]: "
                      f"plannable={plannable_rate:.0%} "
                      f"({plannable_count}/{len(stage_tasks)}) "
                      f"avg_nodes={result['avg_nodes']}")

    total_elapsed = time.time() - total_start
    print(f"\nTotal time: {total_elapsed:.1f}s")

    # 保存结果
    summary = []
    for r in all_results:
        s = {k: v for k, v in r.items() if k != "task_results"}
        summary.append(s)

    with open(RESULTS_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(RESULTS_DIR / "full_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"Results saved to {RESULTS_DIR}/")
    return all_results


if __name__ == "__main__":
    n = len(CROSS_DOMAIN_TEMPLATES) * 2 if "--full" in sys.argv else None
    run_phase2(n)
