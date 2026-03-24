#!/usr/bin/env python3
"""
步骤 4 验证：测试 PDDL 生成器，对家居领域 10 个采样任务生成 domain+problem 并求解。
"""
import sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core import SemanticSignature, Predicate
from src.core.pddl_generator import generate_domain, generate_problem, count_pddl_lines, solve_bfs

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = DATA_DIR / "pddl_test"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 10 个家居采样任务 ──
DOMESTIC_TASKS = [
    {
        "name": "pick_cup_from_table",
        "objects": {"cup_1": "cup", "table_1": "surface", "robot": "agent"},
        "init": [Predicate("on", ["cup_1", "table_1"]),
                 Predicate("reachable", ["robot", "cup_1"]),
                 Predicate("clear", ["cup_1"])],
        "goal": [Predicate("holding", ["robot", "cup_1"])],
    },
    {
        "name": "place_bowl_on_counter",
        "objects": {"bowl_1": "bowl", "counter_1": "surface", "robot": "agent"},
        "init": [Predicate("holding", ["robot", "bowl_1"])],
        "goal": [Predicate("on", ["bowl_1", "counter_1"])],
    },
    {
        "name": "open_fridge",
        "objects": {"fridge_1": "fridge", "robot": "agent"},
        "init": [Predicate("reachable", ["robot", "fridge_1"]),
                 Predicate("closed", ["fridge_1"])],
        "goal": [Predicate("open", ["fridge_1"])],
    },
    {
        "name": "wipe_table",
        "objects": {"table_1": "surface", "sponge_1": "sponge", "robot": "agent"},
        "init": [Predicate("holding", ["robot", "sponge_1"]),
                 Predicate("dirty", ["table_1"])],
        "goal": [Predicate("clean", ["table_1"])],
    },
    {
        "name": "fold_shirt",
        "objects": {"shirt_1": "shirt", "robot": "agent"},
        "init": [Predicate("reachable", ["robot", "shirt_1"])],
        "goal": [Predicate("folded", ["shirt_1"])],
    },
    {
        "name": "close_drawer",
        "objects": {"drawer_1": "drawer", "robot": "agent"},
        "init": [Predicate("reachable", ["robot", "drawer_1"]),
                 Predicate("open", ["drawer_1"])],
        "goal": [Predicate("closed", ["drawer_1"])],
    },
    {
        "name": "hang_towel",
        "objects": {"towel_1": "towel", "hook_1": "object", "robot": "agent"},
        "init": [Predicate("holding", ["robot", "towel_1"])],
        "goal": [Predicate("hung", ["towel_1"])],
    },
    {
        "name": "sweep_floor",
        "objects": {"floor_1": "surface", "broom_1": "broom", "robot": "agent"},
        "init": [Predicate("holding", ["robot", "broom_1"])],
        "goal": [Predicate("clean", ["floor_1"])],
    },
    {
        "name": "press_microwave",
        "objects": {"microwave_1": "microwave", "robot": "agent"},
        "init": [Predicate("reachable", ["robot", "microwave_1"])],
        "goal": [Predicate("powered_on", ["microwave_1"])],
    },
    {
        "name": "pick_and_place_bottle",
        "objects": {"bottle_1": "bottle", "table_1": "surface", "counter_1": "surface", "robot": "agent"},
        "init": [Predicate("on", ["bottle_1", "table_1"]),
                 Predicate("reachable", ["robot", "bottle_1"]),
                 Predicate("clear", ["bottle_1"])],
        "goal": [Predicate("on", ["bottle_1", "counter_1"])],
    },
]


def main():
    sigma_0 = SemanticSignature.load(str(DATA_DIR / "signatures" / "domestic.json"))
    print(f"Loaded Sigma_0: {sigma_0.stats()}")

    # 生成 domain
    domain_str = generate_domain(sigma_0, "lcos-r-domestic")
    domain_lines = count_pddl_lines(domain_str)
    domain_path = OUT_DIR / "domestic_domain.pddl"
    with open(domain_path, "w") as f:
        f.write(domain_str)
    print(f"\n[Domain] PDDL lines: {domain_lines}")
    print(f"  Saved: {domain_path}")

    # 对每个任务生成 problem 并求解
    results = []
    total_plannable = 0
    total_time = 0.0

    for task in DOMESTIC_TASKS:
        problem_str = generate_problem(
            sigma_0,
            task["name"],
            "lcos-r-domestic",
            task["objects"],
            task["init"],
            task["goal"],
        )
        prob_path = OUT_DIR / f"{task['name']}_problem.pddl"
        with open(prob_path, "w") as f:
            f.write(problem_str)

        prob_lines = count_pddl_lines(problem_str)

        # BFS 求解
        plan, plan_time, success, _nodes = solve_bfs(domain_str, problem_str, timeout_ms=10000)

        total_time += plan_time
        if success:
            total_plannable += 1

        result = {
            "task": task["name"],
            "problem_lines": prob_lines,
            "plannable": success,
            "plan_length": len(plan),
            "planning_ms": round(plan_time, 2),
            "plan": plan,
        }
        results.append(result)

        status = "✓" if success else "✗"
        plan_info = f"plan_len={len(plan)}" if success else "no plan found"
        print(f"  {status} {task['name']}: {plan_info}, {plan_time:.1f}ms")

    # 汇总
    print(f"\n{'='*50}")
    print(f"Domain PDDL lines: {domain_lines}")
    print(f"Plannable: {total_plannable}/{len(DOMESTIC_TASKS)} ({100*total_plannable/len(DOMESTIC_TASKS):.0f}%)")
    print(f"Total planning time: {total_time:.1f}ms")
    print(f"Avg planning time: {total_time/len(DOMESTIC_TASKS):.1f}ms")

    # 保存结果
    summary = {
        "domain_pddl_lines": domain_lines,
        "plannable_rate": total_plannable / len(DOMESTIC_TASKS),
        "total_tasks": len(DOMESTIC_TASKS),
        "plannable_count": total_plannable,
        "total_planning_ms": round(total_time, 2),
        "avg_planning_ms": round(total_time / len(DOMESTIC_TASKS), 2),
        "tasks": results,
    }
    with open(OUT_DIR / "pddl_test_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nResults saved to {OUT_DIR / 'pddl_test_results.json'}")


if __name__ == "__main__":
    main()
