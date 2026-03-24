"""
Rewrite 执行引擎：按序执行 pass 列表，每个 pass 后分层验证，失败则回滚。
对应 tech-note §6.5。
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional, Tuple

from src.core import SemanticSignature
from src.core.test_suite import run_q_star, TestSuiteResult
from src.rewrite import pass1_predicate_elimination, pass2_rule_folding, pass3_object_pruning


def run_global_rewrite(
    sigma: SemanticSignature,
) -> Tuple[SemanticSignature, List[Dict]]:
    """
    执行全局 rewrite：仅 Pass 1 + Pass 2（Core-Preserving）。
    """
    start = time.time()
    log = []
    current = sigma

    sigma_p1, stats_p1 = pass1_predicate_elimination.apply(current)
    q_result = run_q_star(sigma_p1)
    if q_result.failed == 0:
        current = sigma_p1
        stats_p1["verified"] = True
    else:
        stats_p1["verified"] = False
        stats_p1["failed_tests"] = [r.name for r in q_result.results if not r.passed]
    stats_p1["q_star_pass_rate"] = q_result.pass_rate
    log.append(stats_p1)

    sigma_p2, stats_p2 = pass2_rule_folding.apply(current)
    q_result = run_q_star(sigma_p2)
    if q_result.failed == 0:
        current = sigma_p2
        stats_p2["verified"] = True
    else:
        stats_p2["verified"] = False
        stats_p2["failed_tests"] = [r.name for r in q_result.results if not r.passed]
    stats_p2["q_star_pass_rate"] = q_result.pass_rate
    log.append(stats_p2)

    total_ms = (time.time() - start) * 1000
    log.append({"total_rewrite_ms": round(total_ms, 2)})
    return current, log


def run_task_pruning(
    sigma: SemanticSignature,
    task: Dict,
) -> Tuple[SemanticSignature, Dict]:
    """
    执行 Pass 3（Task-Preserving），per-task。
    """
    sigma_p3, stats_p3 = pass3_object_pruning.apply(sigma, task)
    q_result = run_q_star(sigma_p3)
    if q_result.failed == 0:
        stats_p3["verified"] = True
        return sigma_p3, stats_p3
    else:
        stats_p3["verified"] = False
        return sigma, stats_p3  # 回滚


def run_full_rewrite(
    sigma: SemanticSignature,
    task: Optional[Dict] = None,
) -> Tuple[SemanticSignature, List[Dict]]:
    """
    执行完整的 3-pass rewrite 序列。
    每步验证 Q_star，失败则回滚到上一步。
    返回 (最终签名, rewrite 日志列表)。
    """
    current, log = run_global_rewrite(sigma)

    if task is not None:
        sigma_p3, stats_p3 = run_task_pruning(current, task)
        current = sigma_p3
        log.insert(-1, stats_p3)  # 插入到 total 前面

    return current, log
