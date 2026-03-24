"""
Pass 3 — 无关对象裁剪（Task-Preserving）。
对于特定任务，移除不相关的领域类型和对象。
对应 tech-note §6.5 Pass 3。
"""

from __future__ import annotations
import copy
import time
from typing import Dict, List, Set, Tuple

from src.core import SemanticSignature


def _find_relevant_types(sigma: SemanticSignature, task: Dict) -> Set[str]:
    """确定任务相关的类型集合。"""
    relevant = set()
    # 任务对象直接涉及的类型
    for obj, otype in task.get("objects", {}).items():
        relevant.add(otype)
    # 追溯类型层次中的父类型
    changed = True
    while changed:
        changed = False
        for tname, parent in sigma.S_t.items():
            if tname in relevant and parent and parent not in relevant:
                relevant.add(parent)
                changed = True
    # 加入基础类型
    relevant.update(["object", "agent", "location"])
    return relevant


def _task_predicate_names(task: Dict) -> Set[str]:
    """收集任务初始状态与目标中直接出现的谓词名。"""
    names = set()
    for fact in task.get("init", []) + task.get("goal", []):
        names.add(fact.name)
    return names


def _find_relevant_predicates(
    sigma: SemanticSignature,
    relevant_types: Set[str],
    relevant_actions: Set[str],
    task: Dict,
) -> Set[str]:
    """找到与相关类型关联的谓词。"""
    relevant_preds = _task_predicate_names(task)
    for name, bp in sigma.R_b.items():
        # 如果谓词参数类型与相关类型有交集
        if any(pt in relevant_types or pt == "object" for pt in bp.param_types):
            relevant_preds.add(name)
    for name, gp in sigma.R_g.items():
        if any(pt in relevant_types or pt == "object" for pt in gp.param_types):
            relevant_preds.add(name)
    for aname in relevant_actions:
        act = sigma.A_t[aname]
        for pred in act.preconditions + act.effects:
            relevant_preds.add(pred.name)
    return relevant_preds


def _find_relevant_actions(sigma: SemanticSignature, relevant_types: Set[str]) -> Set[str]:
    """找到与相关类型关联的动作。"""
    relevant = set()
    for aname, act in sigma.A_t.items():
        # 动作参数类型有任一在 relevant_types 中（或为 object）
        if any(p.type_name in relevant_types or p.type_name == "object"
               for p in act.parameters):
            relevant.add(aname)
    return relevant


def apply(sigma: SemanticSignature, task: Dict) -> Tuple[SemanticSignature, Dict]:
    """
    执行 Pass 3：裁剪任务无关的类型和对象。
    返回 (新签名, 统计信息)。
    """
    start = time.time()
    sigma_new = copy.deepcopy(sigma)

    relevant_types = _find_relevant_types(sigma_new, task)
    relevant_actions = _find_relevant_actions(sigma_new, relevant_types)
    relevant_preds = _find_relevant_predicates(sigma_new, relevant_types, relevant_actions, task)

    # 统计裁剪前
    types_before = len(sigma_new.S_t)
    preds_before = sigma_new.predicate_count()
    actions_before = sigma_new.action_count()

    # 计算所有动作参数使用的类型
    action_types = set()
    for act in sigma_new.A_t.values():
        for p in act.parameters:
            action_types.add(p.type_name)

    # 需要保留：相关类型 + 动作使用的类型 + 它们在层次中的祖先
    keep_types = relevant_types | action_types
    # 追溯祖先
    changed = True
    while changed:
        changed = False
        for tname, parent in sigma_new.S_t.items():
            if tname in keep_types and parent and parent not in keep_types:
                keep_types.add(parent)
                changed = True
    # 追溯子类型（如果父类型保留，其子类型也保留）
    changed = True
    while changed:
        changed = False
        for tname, parent in sigma_new.S_t.items():
            if parent in keep_types and tname not in keep_types:
                keep_types.add(tname)
                changed = True

    # 裁剪类型
    types_to_remove = [t for t in sigma_new.S_t if t not in keep_types]
    for t in types_to_remove:
        del sigma_new.S_t[t]

    # 裁剪谓词
    preds_to_remove = set(sigma_new.R_b.keys()) - relevant_preds
    for p in preds_to_remove & set(sigma_new.R_b.keys()):
        del sigma_new.R_b[p]
    gpreds_to_remove = set(sigma_new.R_g.keys()) - relevant_preds
    for p in gpreds_to_remove & set(sigma_new.R_g.keys()):
        del sigma_new.R_g[p]

    # 裁剪动作
    actions_to_remove = set(sigma_new.A_t.keys()) - relevant_actions
    for a in actions_to_remove:
        del sigma_new.A_t[a]

    # 裁剪约束中引用已移除谓词的约束
    constraints_to_remove = []
    for cname, c in sigma_new.C_t.items():
        c.condition = [p for p in c.condition if p.name in relevant_preds or
                       p.name.startswith("allow_") or p.name.startswith("require_")]
        c.consequence = [p for p in c.consequence if p.name in relevant_preds or
                         p.name.startswith("allow_") or p.name.startswith("require_")]
        if not c.condition and not c.consequence:
            constraints_to_remove.append(cname)
    for cname in constraints_to_remove:
        del sigma_new.C_t[cname]

    # 裁剪规则
    sigma_new.rules = [r for r in sigma_new.rules
                       if not any(t in r.get("body", "") for t in types_to_remove)]

    elapsed = (time.time() - start) * 1000
    stats = {
        "pass": "object_pruning",
        "types_pruned": len(types_to_remove),
        "predicates_pruned": len(preds_to_remove) + len(gpreds_to_remove),
        "actions_pruned": len(actions_to_remove),
        "constraints_pruned": len(constraints_to_remove),
        "elapsed_ms": round(elapsed, 2),
        "types_before": types_before, "types_after": len(sigma_new.S_t),
        "predicates_before": preds_before, "predicates_after": sigma_new.predicate_count(),
        "actions_before": actions_before, "actions_after": sigma_new.action_count(),
    }
    return sigma_new, stats
