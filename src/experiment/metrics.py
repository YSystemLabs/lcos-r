"""
指标收集模块，对应 tech-note §9.4 五类指标。
"""

from __future__ import annotations
import time
from typing import Dict, List

from src.core import SemanticSignature, Predicate
from src.core.pddl_generator import generate_domain, generate_problem, solve_bfs, count_pddl_lines
from src.core.test_suite import run_q_star, run_q_task


def collect_complexity_metrics(sigma: SemanticSignature) -> Dict:
    """指标 1: 表示复杂度。"""
    domain_str = generate_domain(sigma)
    return {
        "active_predicates": sigma.predicate_count(),
        "active_rules": sigma.rule_count(),
        "active_constraints": sigma.constraint_count(),
        "active_actions": sigma.action_count(),
        "pddl_lines": count_pddl_lines(domain_str),
        "type_count": sigma.type_count(),
        "total_complexity": sigma.total_complexity(),
    }


def collect_planning_metrics(sigma: SemanticSignature, task: Dict,
                             timeout_ms: int = 10000) -> Dict:
    """指标 2+3: 计算开销 + 可规划性。"""
    t0 = time.time()
    domain_str = generate_domain(sigma)
    sig_time = (time.time() - t0) * 1000

    problem_str = generate_problem(
        sigma, task["name"], "lcos-r",
        task["objects"], task["init"], task["goal"],
    )

    plan, plan_time, success, nodes = solve_bfs(domain_str, problem_str, timeout_ms)

    return {
        "plannable": success,
        "plan_length": len(plan) if success else -1,
        "planning_ms": round(plan_time, 2),
        "sig_construction_ms": round(sig_time, 2),
        "plan": plan if success else [],
        "nodes_explored": nodes,
    }


def collect_verification_metrics(sigma: SemanticSignature, tasks: List[Dict]) -> Dict:
    """Q_star/Q_task 通过率。"""
    q_star = run_q_star(sigma)
    q_task = run_q_task(sigma, tasks)
    return {
        "q_star_pass_rate": round(q_star.pass_rate, 4),
        "q_task_pass_rate": round(q_task.pass_rate, 4),
        "q_star_total": q_star.total,
        "q_task_total": q_task.total,
    }


def collect_all_metrics(sigma: SemanticSignature, task: Dict,
                        all_tasks: List[Dict]) -> Dict:
    """收集所有指标。"""
    complexity = collect_complexity_metrics(sigma)
    planning = collect_planning_metrics(sigma, task)
    verification = collect_verification_metrics(sigma, all_tasks)
    return {**complexity, **planning, **verification}
