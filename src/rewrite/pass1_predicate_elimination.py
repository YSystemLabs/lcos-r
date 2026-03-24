"""
Pass 1 — 冗余谓词消除（Core-Preserving）。
检测同义谓词对（如 on/on_shelf），将特化谓词统一归约为基础谓词。
对应 tech-note §6.5 Pass 1。
"""

from __future__ import annotations
import copy
import time
from typing import Dict, List, Set, Tuple

from src.core import SemanticSignature, BoolPredicate, GradedPredicate


# 已知同义谓词映射：特化 → 基础
KNOWN_SYNONYMS = {
    "on_shelf": "on",
    "on_belt": "on",
    "on_tray": "on",
    "on_desk": "on",
    "in_cart": "in",
    "sorted_into": "in",
    "in_holder": "in",
}


def detect_synonyms(sigma: SemanticSignature) -> List[Tuple[str, str]]:
    """
    检测签名中的同义谓词对。
    返回 [(特化谓词, 基础谓词), ...]。
    """
    found = []
    all_preds = set(sigma.R_b.keys()) | set(sigma.R_g.keys())
    for specialized, base in KNOWN_SYNONYMS.items():
        if specialized in all_preds and base in all_preds:
            found.append((specialized, base))
    return found


def apply(sigma: SemanticSignature) -> Tuple[SemanticSignature, Dict]:
    """
    执行 Pass 1：消除同义谓词。
    返回 (新签名, 统计信息)。
    """
    start = time.time()
    sigma_new = copy.deepcopy(sigma)

    synonyms = detect_synonyms(sigma_new)
    eliminated = []

    for specialized, base in synonyms:
        sigma_new.replace_predicate(specialized, base)
        eliminated.append({"from": specialized, "to": base})

    elapsed = (time.time() - start) * 1000
    stats = {
        "pass": "predicate_elimination",
        "synonyms_detected": len(synonyms),
        "predicates_eliminated": len(eliminated),
        "eliminations": eliminated,
        "elapsed_ms": round(elapsed, 2),
        "predicates_before": sigma.predicate_count(),
        "predicates_after": sigma_new.predicate_count(),
    }
    return sigma_new, stats
