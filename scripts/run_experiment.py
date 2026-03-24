#!/usr/bin/env python3
"""
实验运行器：执行 5 阶段 × 4 组实验，收集全部指标。
对应 tech-note §9。
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core import SemanticSignature
from src.experiment.systems import (
    ALL_SYSTEMS, DOMAINS, load_sigma_0, load_deltas, generate_domain_tasks,
)
from src.experiment.metrics import (
    collect_complexity_metrics, collect_planning_metrics, collect_verification_metrics,
)
from src.rewrite.engine import run_global_rewrite, run_task_pruning
from src.rewrite.pass1_predicate_elimination import KNOWN_SYNONYMS

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def remap_task_predicates(task, sigma):
    """将任务中的谓词名映射到 sigma 中已有的谓词。"""
    known_preds = sigma.predicate_names()
    import copy
    task = copy.deepcopy(task)
    for p_list in [task["init"], task["goal"]]:
        for p in p_list:
            if p.name not in known_preds and p.name in KNOWN_SYNONYMS:
                p.name = KNOWN_SYNONYMS[p.name]
    return task


def run_experiment(n_tasks_per_domain: int = 30, is_pilot: bool = False):
    """
    运行完整实验。
    is_pilot=True 时只用 10 个任务/领域。
    """
    if is_pilot:
        n_tasks_per_domain = 10

    out_dir = RESULTS_DIR / ("pilot" if is_pilot else "raw")
    out_dir.mkdir(parents=True, exist_ok=True)

    sigma_0 = load_sigma_0()
    deltas = load_deltas()

    # 生成各领域采样任务
    all_domain_tasks = {}
    for domain in DOMAINS:
        all_domain_tasks[domain] = generate_domain_tasks(domain, n_tasks_per_domain)

    # 收集实验结果
    all_results = []
    total_start = time.time()

    for stage in range(5):  # Stage 0-4
        stage_domain = DOMAINS[stage] if stage < len(DOMAINS) else DOMAINS[-1]
        tasks = all_domain_tasks[stage_domain]

        print(f"\n{'='*60}")
        print(f"Stage {stage}: {DOMAINS[stage] if stage < len(DOMAINS) else 'all'}")
        print(f"{'='*60}")

        for system in ALL_SYSTEMS:
            # 用第一个任务作为 rewrite 的参考任务
            ref_task = tasks[0] if tasks else None

            t0 = time.time()
            sigma = system.setup(stage, sigma_0, deltas, ref_task)
            setup_ms = (time.time() - t0) * 1000

            # 收集复杂度指标
            complexity = collect_complexity_metrics(sigma)

            if system.name in ("Expand+Rewrite", "Expand+ManualOpt") and stage > 0:
                verification_tasks = [remap_task_predicates(task, sigma) for task in tasks]
            else:
                verification_tasks = tasks

            # 对每个任务收集规划指标
            plannable_count = 0
            total_plan_time = 0.0
            total_plan_length = 0
            task_results = []
            pass3_verified_count = 0

            for task, task_mapped in zip(tasks, verification_tasks):
                # Remap task predicates for systems that did predicate elimination
                # Per-task pruning for Expand+Rewrite
                if system.name == "Expand+Rewrite" and stage > 0:
                    sigma_for_task, pruning_stats = run_task_pruning(sigma, task_mapped)
                    if pruning_stats.get("verified"):
                        pass3_verified_count += 1
                else:
                    sigma_for_task = sigma
                pm = collect_planning_metrics(sigma_for_task, task_mapped)
                if pm["plannable"]:
                    plannable_count += 1
                    total_plan_length += pm["plan_length"]
                total_plan_time += pm["planning_ms"]
                task_results.append({
                    "task": task["name"],
                    "plannable": pm["plannable"],
                    "plan_length": pm["plan_length"],
                    "planning_ms": pm["planning_ms"],
                })

            plannable_rate = plannable_count / len(tasks) if tasks else 0
            avg_plan_time = total_plan_time / len(tasks) if tasks else 0

            # 验证指标
            verification = collect_verification_metrics(sigma, verification_tasks)

            # Rewrite 统计（仅 Expand+Rewrite）
            rewrite_ms = 0.0
            rewrite_log = []
            if system.name == "Expand+Rewrite" and stage > 0:
                sigma_pre = sigma_0
                for i in range(min(stage, len(deltas))):
                    sigma_pre = sigma_pre.merge(deltas[i])
                _, rewrite_log = run_global_rewrite(sigma_pre)
                for entry in rewrite_log:
                    if "elapsed_ms" in entry:
                        rewrite_ms += entry["elapsed_ms"]

            result = {
                "stage": stage,
                "domain": stage_domain,
                "system": system.name,
                "setup_ms": round(setup_ms, 2),
                **complexity,
                "plannable_rate": round(plannable_rate, 4),
                "plannable_count": plannable_count,
                "total_tasks": len(tasks),
                "avg_planning_ms": round(avg_plan_time, 2),
                "total_planning_ms": round(total_plan_time, 2),
                "avg_plan_length": round(total_plan_length / max(1, plannable_count), 2),
                "rewrite_ms": round(rewrite_ms, 2),
                "pass3_verified_count": pass3_verified_count,
                "pass3_verified_rate": round(pass3_verified_count / len(tasks), 4) if tasks else 0.0,
                **verification,
                "task_results": task_results,
                "rewrite_log": rewrite_log,
            }
            all_results.append(result)

            print(f"  {system.name:20s}: preds={complexity['active_predicates']:3d} "
                  f"rules={complexity['active_rules']:2d} "
                  f"complexity={complexity['total_complexity']:3d} "
                  f"plannable={plannable_rate:.0%} "
                  f"plan_time={avg_plan_time:.1f}ms")

    total_elapsed = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"Total experiment time: {total_elapsed:.1f}s")

    # 保存结果
    # 分离 task_results 以减小主文件大小
    summary = []
    for r in all_results:
        s = {k: v for k, v in r.items() if k not in ("task_results", "rewrite_log")}
        summary.append(s)

    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(out_dir / "full_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\nResults saved to {out_dir}/")
    return all_results


if __name__ == "__main__":
    is_pilot = "--pilot" in sys.argv
    n = 10 if is_pilot else 30
    run_experiment(n, is_pilot)
