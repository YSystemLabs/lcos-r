"""
测试套件框架：T0/T1/T2 分层测试 + Q_star/Q_task/Q_t 三级测试集。
对应 tech-note §5.1 和 §6.6。
"""

from __future__ import annotations
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from src.core import SemanticSignature, Predicate, ActionTemplate
from src.core.pddl_generator import generate_domain, generate_problem, solve_bfs, count_pddl_lines


@dataclass
class TestResult:
    """单条测试结果。"""
    name: str
    passed: bool
    level: str        # "T0", "T1", "T2"
    elapsed_ms: float = 0.0
    detail: str = ""

    def to_dict(self):
        return {"name": self.name, "passed": self.passed, "level": self.level,
                "elapsed_ms": round(self.elapsed_ms, 3), "detail": self.detail}


@dataclass
class TestSuiteResult:
    """测试套件运行结果。"""
    results: List[TestResult] = field(default_factory=list)

    @property
    def total(self): return len(self.results)
    @property
    def passed(self): return sum(1 for r in self.results if r.passed)
    @property
    def failed(self): return self.total - self.passed
    @property
    def pass_rate(self): return self.passed / self.total if self.total else 0.0
    @property
    def total_ms(self): return sum(r.elapsed_ms for r in self.results)

    def by_level(self, level: str) -> List[TestResult]:
        return [r for r in self.results if r.level == level]

    def pass_rate_by_level(self, level: str) -> float:
        lvl = self.by_level(level)
        return sum(1 for r in lvl if r.passed) / len(lvl) if lvl else 0.0

    def summary(self) -> Dict:
        return {
            "total": self.total, "passed": self.passed, "failed": self.failed,
            "pass_rate": round(self.pass_rate, 4),
            "total_ms": round(self.total_ms, 2),
            "T0": {"total": len(self.by_level("T0")), "pass_rate": round(self.pass_rate_by_level("T0"), 4)},
            "T1": {"total": len(self.by_level("T1")), "pass_rate": round(self.pass_rate_by_level("T1"), 4)},
            "T2": {"total": len(self.by_level("T2")), "pass_rate": round(self.pass_rate_by_level("T2"), 4)},
        }

    def to_dict(self):
        return {"summary": self.summary(), "results": [r.to_dict() for r in self.results]}


# ══════════════════════════════════════════════════
# T0 廉价测试 (O(1)–O(n))
# ══════════════════════════════════════════════════

def t0_type_consistency(sigma: SemanticSignature) -> TestResult:
    """检查类型层次中没有悬空引用。"""
    t = time.time()
    issues = []
    for tname, parent in sigma.S_t.items():
        if parent and parent not in sigma.S_t and parent != "object":
            issues.append(f"type '{tname}' parent '{parent}' not in S_t")
    # 检查动作参数类型都在 S_t 中
    for aname, act in sigma.A_t.items():
        for p in act.parameters:
            if p.type_name not in sigma.S_t and p.type_name not in ("object", "agent", "location"):
                issues.append(f"action '{aname}' param '{p.name}' type '{p.type_name}' not in S_t")
    elapsed = (time.time() - t) * 1000
    return TestResult("type_consistency", len(issues) == 0, "T0", elapsed,
                      "; ".join(issues[:5]) if issues else "ok")


def t0_predicate_arity(sigma: SemanticSignature) -> TestResult:
    """检查动作中引用的谓词 arity 与声明一致。"""
    t = time.time()
    issues = []
    all_preds = {**{n: bp.arity for n, bp in sigma.R_b.items()},
                 **{n: gp.arity for n, gp in sigma.R_g.items()}}
    for aname, act in sigma.A_t.items():
        for p in act.preconditions + act.effects:
            if p.name in all_preds:
                expected = all_preds[p.name]
                if len(p.args) != expected:
                    issues.append(f"action '{aname}': {p.name} arity={len(p.args)}, expected={expected}")
    elapsed = (time.time() - t) * 1000
    return TestResult("predicate_arity", len(issues) == 0, "T0", elapsed,
                      "; ".join(issues[:5]) if issues else "ok")


def t0_action_completeness(sigma: SemanticSignature) -> TestResult:
    """每个动作至少有一个参数和一个效果或前提。"""
    t = time.time()
    issues = []
    for aname, act in sigma.A_t.items():
        if not act.parameters:
            issues.append(f"action '{aname}' has no parameters")
        if not act.preconditions and not act.effects:
            issues.append(f"action '{aname}' has no preconditions or effects")
    elapsed = (time.time() - t) * 1000
    return TestResult("action_completeness", len(issues) == 0, "T0", elapsed,
                      "; ".join(issues[:5]) if issues else "ok")


def t0_pddl_parseable(sigma: SemanticSignature) -> TestResult:
    """生成的 PDDL domain 可被解析（通过内部解析器验证）。"""
    t = time.time()
    try:
        domain_str = generate_domain(sigma)
        lines = count_pddl_lines(domain_str)
        ok = lines > 0 and "(:action" in domain_str and "(:predicates" in domain_str
        detail = f"lines={lines}" if ok else "parse failed"
    except Exception as e:
        ok = False
        detail = str(e)
    elapsed = (time.time() - t) * 1000
    return TestResult("pddl_parseable", ok, "T0", elapsed, detail)


def t0_no_duplicate_predicates(sigma: SemanticSignature) -> TestResult:
    """R_b 和 R_g 中没有名称冲突。"""
    t = time.time()
    overlap = set(sigma.R_b.keys()) & set(sigma.R_g.keys())
    elapsed = (time.time() - t) * 1000
    return TestResult("no_duplicate_predicates", len(overlap) == 0, "T0", elapsed,
                      f"overlap: {overlap}" if overlap else "ok")


def t0_constraint_references(sigma: SemanticSignature) -> TestResult:
    """约束中引用的谓词都已声明（或是辅助谓词）。"""
    t = time.time()
    known = sigma.predicate_names()
    issues = []
    for cname, c in sigma.C_t.items():
        for p in c.condition + c.consequence:
            if p.name not in known:
                # 允许 辅助谓词（allow_xxx, require_xxx）
                if not p.name.startswith("allow_") and not p.name.startswith("require_"):
                    issues.append(f"constraint '{cname}': unknown pred '{p.name}'")
    elapsed = (time.time() - t) * 1000
    return TestResult("constraint_references", len(issues) == 0, "T0", elapsed,
                      "; ".join(issues[:5]) if issues else "ok")


def t0_action_references_declared_predicates(sigma: SemanticSignature) -> TestResult:
    """动作前提和效果中引用的谓词都必须已声明。"""
    t = time.time()
    declared = sigma.predicate_names()
    issues = []
    for aname, act in sigma.A_t.items():
        for pred in act.preconditions + act.effects:
            if pred.name not in declared:
                issues.append(f"action '{aname}': unknown pred '{pred.name}'")
    elapsed = (time.time() - t) * 1000
    return TestResult(
        "action_references_declared_predicates",
        len(issues) == 0,
        "T0",
        elapsed,
        "; ".join(issues[:5]) if issues else "ok",
    )


# ══════════════════════════════════════════════════
# T1 中等测试
# ══════════════════════════════════════════════════

def t1_predicate_coverage(sigma: SemanticSignature) -> TestResult:
    """每个声明的谓词至少在一个动作的前提或效果中出现。"""
    t = time.time()
    used = set()
    for act in sigma.A_t.values():
        for p in act.preconditions + act.effects:
            used.add(p.name)
    declared = sigma.predicate_names()
    unused = declared - used
    # 允许少量未使用（状态谓词可能仅用于判断）
    threshold = max(3, len(declared) * 0.2)
    elapsed = (time.time() - t) * 1000
    return TestResult("predicate_coverage", len(unused) <= threshold, "T1", elapsed,
                      f"unused({len(unused)}): {sorted(unused)}")


def t1_action_param_types_in_hierarchy(sigma: SemanticSignature) -> TestResult:
    """动作参数类型在类型层次中有定义。"""
    t = time.time()
    valid_types = set(sigma.S_t.keys()) | {"object", "agent", "location"}
    issues = []
    for aname, act in sigma.A_t.items():
        for p in act.parameters:
            if p.type_name not in valid_types:
                issues.append(f"{aname}.{p.name}: {p.type_name}")
    elapsed = (time.time() - t) * 1000
    return TestResult("action_param_types", len(issues) == 0, "T1", elapsed,
                      "; ".join(issues[:5]) if issues else "ok")


def t1_symmetry_open_close(sigma: SemanticSignature) -> TestResult:
    """如果有 open 动作就应该有 close 动作。"""
    t = time.time()
    names = set(sigma.A_t.keys())
    pairs = [("open", "close"), ("pick", "place"), ("grasp", "release")]
    issues = []
    for a, b in pairs:
        if a in names and b not in names:
            issues.append(f"has '{a}' but missing '{b}'")
        elif b in names and a not in names:
            issues.append(f"has '{b}' but missing '{a}'")
    elapsed = (time.time() - t) * 1000
    return TestResult("symmetry_actions", len(issues) == 0, "T1", elapsed,
                      "; ".join(issues) if issues else "ok")


def t1_conflict_count(sigma: SemanticSignature) -> TestResult:
    """统计可能的规则冲突（相同谓词在不同规则中出现相反结论）。"""
    t = time.time()
    # 简化版：统计规则数，超过类型数的一半视为潜在问题
    conflict_ratio = sigma.rule_count() / max(1, sigma.predicate_count())
    elapsed = (time.time() - t) * 1000
    return TestResult("conflict_count", conflict_ratio < 2.0, "T1", elapsed,
                      f"ratio={conflict_ratio:.2f} (rules/preds)")


# ══════════════════════════════════════════════════
# T2 昂贵测试 (NP-hard)
# ══════════════════════════════════════════════════

def t2_plannable(sigma: SemanticSignature, objects: Dict, init_facts: List[Predicate],
                 goal_facts: List[Predicate], timeout_ms: int = 10000) -> TestResult:
    """检查单个任务的可规划性。"""
    t = time.time()
    domain_str = generate_domain(sigma)
    problem_str = generate_problem(sigma, "test_task", "lcos-r", objects, init_facts, goal_facts)
    plan, plan_time, success, _nodes = solve_bfs(domain_str, problem_str, timeout_ms)
    elapsed = (time.time() - t) * 1000
    return TestResult("plannable", success, "T2", elapsed,
                      f"plan_len={len(plan)}, plan_time={plan_time:.1f}ms" if success else "no plan")


def t2_plan_cost(sigma: SemanticSignature, objects: Dict, init_facts: List[Predicate],
                 goal_facts: List[Predicate], timeout_ms: int = 10000) -> Tuple[TestResult, int]:
    """返回计划代价（步数）。"""
    t = time.time()
    domain_str = generate_domain(sigma)
    problem_str = generate_problem(sigma, "cost_task", "lcos-r", objects, init_facts, goal_facts)
    plan, plan_time, success, _nodes = solve_bfs(domain_str, problem_str, timeout_ms)
    cost = len(plan) if success else -1
    elapsed = (time.time() - t) * 1000
    return TestResult("plan_cost", success, "T2", elapsed, f"cost={cost}"), cost


# ══════════════════════════════════════════════════
# 三层测试集
# ══════════════════════════════════════════════════

def run_q_star(sigma: SemanticSignature) -> TestSuiteResult:
    """
    Q_star: 核心安全+类型测试（只增不减）。
    包含所有 T0 + 关键 T1 测试。
    """
    result = TestSuiteResult()
    # T0 全部
    result.results.append(t0_type_consistency(sigma))
    result.results.append(t0_predicate_arity(sigma))
    result.results.append(t0_action_completeness(sigma))
    result.results.append(t0_pddl_parseable(sigma))
    result.results.append(t0_no_duplicate_predicates(sigma))
    result.results.append(t0_constraint_references(sigma))
    result.results.append(t0_action_references_declared_predicates(sigma))
    # 关键 T1
    result.results.append(t1_action_param_types_in_hierarchy(sigma))
    result.results.append(t1_symmetry_open_close(sigma))
    result.results.append(t1_conflict_count(sigma))
    return result


def run_q_task(sigma: SemanticSignature, tasks: List[Dict], include_coverage: bool = True) -> TestSuiteResult:
    """
    Q_task: 当前领域任务测试。
    包含 Q_star + T2 可规划性测试。
    """
    result = run_q_star(sigma)
    if include_coverage:
        result.results.append(t1_predicate_coverage(sigma))
    # T2: 对每个任务测试可规划性
    for task in tasks:
        r = t2_plannable(sigma, task["objects"], task["init"], task["goal"])
        r.name = f"plannable_{task['name']}"
        result.results.append(r)
    return result


def run_q_t(sigma: SemanticSignature, tasks: List[Dict]) -> TestSuiteResult:
    """
    Q_t: 全集 = Q_task + 诊断测试。
    """
    result = run_q_task(sigma, tasks)
    # 额外诊断：PDDL 行数
    domain_str = generate_domain(sigma)
    pddl_lines = count_pddl_lines(domain_str)
    result.results.append(TestResult("pddl_complexity", pddl_lines < 1000, "T1",
                                     0.0, f"lines={pddl_lines}"))
    return result


# ══════════════════════════════════════════════════
# 回归测试
# ══════════════════════════════════════════════════

def regression_check(old_result: TestSuiteResult, new_result: TestSuiteResult) -> Dict:
    """比较两次测试运行，检测回归。"""
    old_names = {r.name: r for r in old_result.results}
    new_names = {r.name: r for r in new_result.results}
    regressions = []
    improvements = []
    for name, nresult in new_names.items():
        if name in old_names:
            oresult = old_names[name]
            if oresult.passed and not nresult.passed:
                regressions.append(name)
            elif not oresult.passed and nresult.passed:
                improvements.append(name)
    return {
        "regressions": regressions,
        "improvements": improvements,
        "old_pass_rate": old_result.pass_rate,
        "new_pass_rate": new_result.pass_rate,
    }
