"""
Pass 2 — 规则折叠（Core-Preserving）。
识别同构规则，折叠为参数化通用规则。
对应 tech-note §6.5 Pass 2。
"""

from __future__ import annotations
import copy
import re
import time
from typing import Dict, List, Tuple

from src.core import SemanticSignature


def _normalize_rule(rule: Dict) -> str:
    """将规则 body 规范化，忽略具体变量名，只看结构。"""
    body = rule.get("body", "")
    # 替换所有具体实体名为占位符
    normalized = re.sub(r'\b[a-z_]+\(', 'P(', body)
    return normalized


def _find_foldable_groups(rules: List[Dict]) -> List[List[int]]:
    """找到可以折叠的规则组（结构相同的规则）。"""
    # 按类型分组
    type_groups = {}
    for i, rule in enumerate(rules):
        rtype = rule.get("type", "unknown")
        type_groups.setdefault(rtype, []).append(i)

    foldable = []
    for rtype, indices in type_groups.items():
        if len(indices) < 2:
            continue
        # 在同类型中找结构相似的
        struct_groups = {}
        for idx in indices:
            struct = _normalize_rule(rules[idx])
            struct_groups.setdefault(struct, []).append(idx)
        for struct, group in struct_groups.items():
            if len(group) >= 2:
                foldable.append(group)

    return foldable


def apply(sigma: SemanticSignature) -> Tuple[SemanticSignature, Dict]:
    """
    执行 Pass 2：折叠同构规则。
    返回 (新签名, 统计信息)。
    """
    start = time.time()
    sigma_new = copy.deepcopy(sigma)

    foldable_groups = _find_foldable_groups(sigma_new.rules)
    rules_before = len(sigma_new.rules)
    folded_count = 0

    # 对每组同构规则，保留第一条并标记为通用
    indices_to_remove = set()
    fold_log = []
    for group in foldable_groups:
        kept = group[0]
        removed = group[1:]
        indices_to_remove.update(removed)
        folded_count += len(removed)
        fold_log.append({
            "kept": sigma_new.rules[kept]["name"],
            "folded": [sigma_new.rules[i]["name"] for i in removed],
        })
        # 标记保留规则为参数化版本
        sigma_new.rules[kept]["parameterized"] = True
        sigma_new.rules[kept]["original_count"] = len(group)

    # 移除被折叠的规则
    sigma_new.rules = [r for i, r in enumerate(sigma_new.rules) if i not in indices_to_remove]

    elapsed = (time.time() - start) * 1000
    stats = {
        "pass": "rule_folding",
        "foldable_groups": len(foldable_groups),
        "rules_folded": folded_count,
        "fold_log": fold_log,
        "elapsed_ms": round(elapsed, 2),
        "rules_before": rules_before,
        "rules_after": len(sigma_new.rules),
    }
    return sigma_new, stats
