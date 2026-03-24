"""
PDDL 生成器：将 SemanticSignature 翻译为 PDDL domain + problem。
使用 pyperplan 作为纯 Python planner（无需外部安装）。
"""

from __future__ import annotations
import re
import time
from typing import Dict, List, Optional, Set, Tuple

from src.core import SemanticSignature, ActionTemplate, Predicate


def _sanitize(name: str) -> str:
    """将名称转为合法 PDDL 标识符。"""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name).lower().strip('_')


def generate_domain(sigma: SemanticSignature, domain_name: str = "lcos-r") -> str:
    """从 SemanticSignature 生成 PDDL domain 字符串。"""
    lines = [f"(define (domain {_sanitize(domain_name)})"]
    lines.append("  (:requirements :strips :typing)")

    # Types —— 构建类型层次
    type_lines = []
    children_of = {}
    for t, parent in sigma.S_t.items():
        parent = parent or "object"
        if parent not in children_of:
            children_of[parent] = []
        if t != parent:
            children_of[parent].append(t)

    # 输出顶级 object 类型
    type_lines.append("    object")
    for parent, children in sorted(children_of.items()):
        if children and parent != "object":
            type_lines.append(f"    {' '.join(_sanitize(c) for c in children)} - {_sanitize(parent)}")
    # 没有显式 parent 的直接归 object
    top_children = children_of.get("object", [])
    if top_children:
        # 排除已在 sub-hierarchy 中声明的
        all_declared = set()
        for p, clist in children_of.items():
            if p != "object":
                all_declared.update(clist)
        remaining = [c for c in top_children if c not in all_declared]
        if remaining:
            type_lines.append(f"    {' '.join(_sanitize(c) for c in remaining)} - object")

    lines.append("  (:types")
    lines.extend(type_lines)
    lines.append("  )")

    # Predicates
    pred_lines = []
    for name, bp in sorted(sigma.R_b.items()):
        params = " ".join(f"?p{i} - {_sanitize(bp.param_types[i]) if i < len(bp.param_types) else 'object'}"
                          for i in range(bp.arity))
        pred_lines.append(f"    ({_sanitize(name)} {params})")
    for name, gp in sorted(sigma.R_g.items()):
        # 渐变谓词在 PDDL 中用布尔近似（阈值化后）
        params = " ".join(f"?p{i} - {_sanitize(gp.param_types[i]) if i < len(gp.param_types) else 'object'}"
                          for i in range(gp.arity))
        pred_lines.append(f"    ({_sanitize(name)} {params})")

    lines.append("  (:predicates")
    lines.extend(pred_lines)
    lines.append("  )")

    # Actions
    for aname, act in sorted(sigma.A_t.items()):
        params_str = " ".join(f"?{_sanitize(p.name)} - {_sanitize(p.type_name)}"
                              for p in act.parameters)

        pre_parts = []
        for p in act.preconditions:
            args = " ".join(f"?{_sanitize(a)}" if not a.startswith("_") else a for a in p.args)
            atom = f"({_sanitize(p.name)} {args})"
            pre_parts.append(f"(not {atom})" if p.negated else atom)

        eff_parts = []
        for p in act.effects:
            args = " ".join(f"?{_sanitize(a)}" if not a.startswith("_") else a for a in p.args)
            atom = f"({_sanitize(p.name)} {args})"
            eff_parts.append(f"(not {atom})" if p.negated else atom)

        pre_str = f"(and {' '.join(pre_parts)})" if len(pre_parts) > 1 else (pre_parts[0] if pre_parts else "()")
        eff_str = f"(and {' '.join(eff_parts)})" if len(eff_parts) > 1 else (eff_parts[0] if eff_parts else "()")

        lines.append(f"  (:action {_sanitize(aname)}")
        lines.append(f"    :parameters ({params_str})")
        lines.append(f"    :precondition {pre_str}")
        lines.append(f"    :effect {eff_str}")
        lines.append("  )")

    lines.append(")")
    return "\n".join(lines)


def generate_problem(
    sigma: SemanticSignature,
    problem_name: str,
    domain_name: str,
    objects: Dict[str, str],   # entity -> type
    init_facts: List[Predicate],
    goal_facts: List[Predicate],
) -> str:
    """生成 PDDL problem 字符串。"""
    lines = [f"(define (problem {_sanitize(problem_name)})"]
    lines.append(f"  (:domain {_sanitize(domain_name)})")

    # Objects
    type_groups = {}
    for entity, etype in objects.items():
        type_groups.setdefault(etype, []).append(entity)
    obj_parts = []
    for etype, entities in sorted(type_groups.items()):
        obj_parts.append(f"    {' '.join(_sanitize(e) for e in entities)} - {_sanitize(etype)}")
    lines.append("  (:objects")
    lines.extend(obj_parts)
    lines.append("  )")

    # Init
    init_parts = []
    for p in init_facts:
        args = " ".join(_sanitize(a) for a in p.args)
        atom = f"({_sanitize(p.name)} {args})"
        init_parts.append(f"(not {atom})" if p.negated else atom)
    lines.append("  (:init")
    for ip in init_parts:
        lines.append(f"    {ip}")
    lines.append("  )")

    # Goal
    goal_parts = []
    for p in goal_facts:
        args = " ".join(_sanitize(a) for a in p.args)
        atom = f"({_sanitize(p.name)} {args})"
        goal_parts.append(f"(not {atom})" if p.negated else atom)
    goal_str = f"(and {' '.join(goal_parts)})" if len(goal_parts) > 1 else (goal_parts[0] if goal_parts else "()")
    lines.append(f"  (:goal {goal_str})")

    lines.append(")")
    return "\n".join(lines)


def count_pddl_lines(pddl_str: str) -> int:
    return len([l for l in pddl_str.strip().split("\n") if l.strip()])


# ── 简单内置 planner（BFS） ──

def _parse_atoms(raw: str):
    """解析 PDDL 中的原子列表，返回 (positive, negative)。"""
    pos, neg = [], []
    for nm in re.finditer(r'\(not\s+\(([\w-]+)((?:\s+[\w?-]+)*)\)\)', raw):
        pred = nm.group(1)
        args = nm.group(2).strip().split() if nm.group(2).strip() else []
        neg.append((pred, tuple(a.lstrip('?') for a in args)))
    raw_no_neg = re.sub(r'\(not\s+\([^)]+\)\)', '', raw)
    for pm in re.finditer(r'\(([\w-]+)((?:\s+[\w?-]+)*)\)', raw_no_neg):
        pred = pm.group(1)
        if pred in ('and', 'not', 'define', 'domain', 'problem'):
            continue
        args = pm.group(2).strip().split() if pm.group(2).strip() else []
        pos.append((pred, tuple(a.lstrip('?') for a in args)))
    return pos, neg


def _parse_pddl_simple(domain_str: str, problem_str: str):
    """极简 PDDL 解析器，用于 STRIPS。"""
    # 提取 actions —— 用括号匹配而非简单 regex
    actions = []
    idx = 0
    while True:
        pos = domain_str.find(':action', idx)
        if pos == -1:
            break
        # 找到 :action 所在的 ( 位置
        open_pos = domain_str.rfind('(', 0, pos)
        # 从 open_pos 开始匹配括号
        depth = 0
        end_pos = open_pos
        for i in range(open_pos, len(domain_str)):
            if domain_str[i] == '(':
                depth += 1
            elif domain_str[i] == ')':
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    break
        action_block = domain_str[open_pos:end_pos]

        # 解析 action name
        name_m = re.search(r':action\s+([\w-]+)', action_block)
        if not name_m:
            idx = pos + 1
            continue
        aname = name_m.group(1)

        # 解析 parameters
        params = []
        params_m = re.search(r':parameters\s*\(([^)]*)\)', action_block)
        if params_m:
            for pm in re.finditer(r'\?([\w-]+)\s*-\s*([\w-]+)', params_m.group(1)):
                params.append((pm.group(1), pm.group(2)))

        # 解析 precondition
        pre_start = action_block.find(':precondition')
        eff_start = action_block.find(':effect')
        pre_raw = action_block[pre_start + len(':precondition'):eff_start].strip() if pre_start != -1 and eff_start != -1 else ""
        eff_raw = action_block[eff_start + len(':effect'):].strip() if eff_start != -1 else ""

        pre_pos, pre_neg = _parse_atoms(pre_raw)
        eff_pos, eff_neg = _parse_atoms(eff_raw)
        actions.append({
            'name': aname, 'params': params,
            'pre_pos': pre_pos, 'pre_neg': pre_neg,
            'eff_pos': eff_pos, 'eff_neg': eff_neg,
        })
        idx = end_pos

    # Parse objects
    objects = {}
    obj_section = re.search(r':objects\s*(.*?)\)', problem_str, re.DOTALL)
    if obj_section:
        for m in re.finditer(r'((?:[\w-]+\s+)+)-\s*([\w-]+)', obj_section.group(1)):
            etype = m.group(2)
            for name in m.group(1).strip().split():
                objects[name] = etype

    # Parse init —— 提取 :init 到 :goal 之间内容
    init_state = set()
    init_section = re.search(r':init\s*(.*?)\)\s*\(:goal', problem_str, re.DOTALL)
    if init_section:
        for m in re.finditer(r'\(([\w-]+)((?:\s+[\w-]+)*)\)', init_section.group(1)):
            pred = m.group(1)
            if pred == 'not':
                continue
            args = tuple(m.group(2).strip().split()) if m.group(2).strip() else ()
            init_state.add((pred, args))

    # Parse goal —— 找到 :goal 后提取所有内容到文件末尾
    goal_pos, goal_neg = [], []
    goal_start = problem_str.find(':goal')
    if goal_start != -1:
        goal_raw = problem_str[goal_start + len(':goal'):]
        goal_pos, goal_neg = _parse_atoms(goal_raw)

    return actions, objects, init_state, goal_pos, goal_neg


def solve_bfs(domain_str: str, problem_str: str, timeout_ms: int = 30000,
              max_depth: int = 8, nodes_limit: int = 50000):
    """简单 BFS planner。返回 (plan, planning_time_ms, success, nodes_explored)。"""
    start = time.time()
    deadline = start + timeout_ms / 1000.0

    try:
        actions, objects, init_state, goal_pos, goal_neg = _parse_pddl_simple(domain_str, problem_str)
    except Exception:
        elapsed = (time.time() - start) * 1000
        return [], elapsed, False, 0

    obj_list = list(objects.keys())

    def goal_met(state):
        for pred, args in goal_pos:
            if (pred, args) not in state:
                return False
        for pred, args in goal_neg:
            if (pred, args) in state:
                return False
        return True

    if goal_met(init_state):
        elapsed = (time.time() - start) * 1000
        return [], elapsed, True, 0

    def ground_action(action, binding):
        """把参数绑定生成 grounded atoms。"""
        def substitute(atoms):
            result = []
            for pred, args in atoms:
                new_args = tuple(binding.get(a, a) for a in args)
                result.append((pred, new_args))
            return result
        return (substitute(action['pre_pos']), substitute(action['pre_neg']),
                substitute(action['eff_pos']), substitute(action['eff_neg']))

    def get_bindings(params, objects_list):
        """生成所有可能的参数绑定。"""
        if not params:
            yield {}
            return
        first, rest = params[0], params[1:]
        for obj in objects_list:
            binding = {first[0]: obj}
            for sub_binding in get_bindings(rest, objects_list):
                merged = {**binding, **sub_binding}
                yield merged

    # BFS with limited depth
    from collections import deque
    frontier = deque()
    frontier.append((frozenset(init_state), []))
    visited = {frozenset(init_state)}
    nodes_explored = 0

    while frontier:
        if time.time() > deadline:
            elapsed = (time.time() - start) * 1000
            return [], elapsed, False, nodes_explored

        state, plan = frontier.popleft()
        if len(plan) >= max_depth:
            continue

        for action in actions:
            for binding in get_bindings(action['params'], obj_list):
                nodes_explored += 1
                if nodes_explored > nodes_limit:
                    elapsed = (time.time() - start) * 1000
                    return [], elapsed, False, nodes_explored

                pre_pos, pre_neg, eff_pos, eff_neg = ground_action(action, binding)

                # 检查前提
                ok = True
                for atom in pre_pos:
                    if atom not in state:
                        ok = False
                        break
                if ok:
                    for atom in pre_neg:
                        if atom in state:
                            ok = False
                            break
                if not ok:
                    continue

                # 应用效果
                new_state = set(state)
                for atom in eff_neg:
                    new_state.discard(atom)
                for atom in eff_pos:
                    new_state.add(atom)

                fs = frozenset(new_state)
                if fs in visited:
                    continue
                visited.add(fs)

                action_str = f"{action['name']}({', '.join(binding[p[0]] for p in action['params'])})"
                new_plan = plan + [action_str]

                if goal_met(new_state):
                    elapsed = (time.time() - start) * 1000
                    return new_plan, elapsed, True, nodes_explored

                frontier.append((fs, new_plan))

    elapsed = (time.time() - start) * 1000
    return [], elapsed, False, nodes_explored
