"""
LCOS-R 语义签名核心数据结构。
对应 tech-note §4.2 和 §5.2。
"""

from __future__ import annotations
import json
import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class TypedParam:
    name: str
    type_name: str


@dataclass
class Predicate:
    """谓词原子：name(args)，可取反。"""
    name: str
    args: List[str] = field(default_factory=list)
    negated: bool = False

    def __hash__(self):
        return hash((self.name, tuple(self.args), self.negated))

    def __eq__(self, other):
        return (self.name, tuple(self.args), self.negated) == (other.name, tuple(other.args), other.negated)

    def to_dict(self):
        d = {"name": self.name}
        if self.args:
            d["args"] = self.args
        if self.negated:
            d["negated"] = True
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Predicate:
        return cls(name=d["name"], args=d.get("args", []), negated=d.get("negated", False))

    def __repr__(self):
        neg = "¬" if self.negated else ""
        args_str = ", ".join(self.args) if self.args else ""
        return f"{neg}{self.name}({args_str})"


@dataclass
class ActionTemplate:
    """动作模板：对应 A_t 中的一个动作。"""
    name: str
    parameters: List[TypedParam] = field(default_factory=list)
    preconditions: List[Predicate] = field(default_factory=list)
    effects: List[Predicate] = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "parameters": [{"name": p.name, "type_name": p.type_name} for p in self.parameters],
            "preconditions": [p.to_dict() for p in self.preconditions],
            "effects": [p.to_dict() for p in self.effects],
        }

    @classmethod
    def from_dict(cls, d: dict) -> ActionTemplate:
        return cls(
            name=d["name"],
            parameters=[TypedParam(**p) for p in d.get("parameters", [])],
            preconditions=[Predicate.from_dict(p) for p in d.get("preconditions", [])],
            effects=[Predicate.from_dict(p) for p in d.get("effects", [])],
        )


@dataclass
class Constraint:
    """约束条件：对应 C_t / C_star。"""
    name: str
    condition: List[Predicate] = field(default_factory=list)  # 前件
    consequence: List[Predicate] = field(default_factory=list)  # 后件（通常是禁止某动作）

    def to_dict(self):
        return {
            "name": self.name,
            "condition": [p.to_dict() for p in self.condition],
            "consequence": [p.to_dict() for p in self.consequence],
        }

    @classmethod
    def from_dict(cls, d: dict) -> Constraint:
        return cls(
            name=d["name"],
            condition=[Predicate.from_dict(p) for p in d.get("condition", [])],
            consequence=[Predicate.from_dict(p) for p in d.get("consequence", [])],
        )


@dataclass
class BoolPredicate:
    """布尔谓词声明（R_b 中的一个元素）。"""
    name: str
    arity: int
    param_types: List[str] = field(default_factory=list)

    def to_dict(self):
        return {"name": self.name, "arity": self.arity, "param_types": self.param_types}

    @classmethod
    def from_dict(cls, d: dict) -> BoolPredicate:
        return cls(name=d["name"], arity=d["arity"], param_types=d.get("param_types", []))


@dataclass
class GradedPredicate:
    """渐变谓词声明（R_g 中的一个元素），取值 [0,1]。"""
    name: str
    arity: int
    param_types: List[str] = field(default_factory=list)
    threshold: float = 0.5  # 决策阈值

    def to_dict(self):
        return {"name": self.name, "arity": self.arity, "param_types": self.param_types, "threshold": self.threshold}

    @classmethod
    def from_dict(cls, d: dict) -> GradedPredicate:
        return cls(name=d["name"], arity=d["arity"], param_types=d.get("param_types", []), threshold=d.get("threshold", 0.5))


@dataclass
class SemanticSignature:
    """
    语义签名 Sigma_t = (S_t, R_b, R_g, A_t, E_t, C_star)
    对应 tech-note §4.2。
    """
    # 类型集合
    S_t: Dict[str, Optional[str]] = field(default_factory=dict)  # type_name -> parent_type
    # 对象域实例
    D_t: Dict[str, str] = field(default_factory=dict)  # entity_name -> type_name
    # 布尔谓词
    R_b: Dict[str, BoolPredicate] = field(default_factory=dict)
    # 渐变谓词
    R_g: Dict[str, GradedPredicate] = field(default_factory=dict)
    # 动作模板
    A_t: Dict[str, ActionTemplate] = field(default_factory=dict)
    # 效果词汇表
    E_t: Set[str] = field(default_factory=set)
    # 核心约束
    C_t: Dict[str, Constraint] = field(default_factory=dict)
    # 规则（从领域扩展中产生的推理规则）
    rules: List[Dict] = field(default_factory=list)

    # ── 统计方法 ──
    def predicate_count(self) -> int:
        return len(self.R_b) + len(self.R_g)

    def action_count(self) -> int:
        return len(self.A_t)

    def rule_count(self) -> int:
        return len(self.rules)

    def constraint_count(self) -> int:
        return len(self.C_t)

    def type_count(self) -> int:
        return len(self.S_t)

    def entity_count(self) -> int:
        return len(self.D_t)

    def total_complexity(self) -> int:
        return self.predicate_count() + self.rule_count() + self.constraint_count() + self.action_count()

    def stats(self) -> Dict:
        return {
            "types": self.type_count(),
            "entities": self.entity_count(),
            "bool_predicates": len(self.R_b),
            "graded_predicates": len(self.R_g),
            "predicates_total": self.predicate_count(),
            "actions": self.action_count(),
            "rules": self.rule_count(),
            "constraints": self.constraint_count(),
            "effects": len(self.E_t),
            "total_complexity": self.total_complexity(),
        }

    # ── 合并（用于领域扩展） ──
    def merge(self, delta: SemanticSignature) -> SemanticSignature:
        """合并增量签名 delta 到当前签名（返回新对象，不修改原签名）。"""
        merged = copy.deepcopy(self)
        merged.S_t.update(delta.S_t)
        merged.D_t.update(delta.D_t)
        merged.R_b.update(delta.R_b)
        merged.R_g.update(delta.R_g)
        merged.A_t.update(delta.A_t)
        merged.E_t.update(delta.E_t)
        merged.C_t.update(delta.C_t)
        merged.rules.extend(delta.rules)
        return merged

    # ── 序列化 ──
    def to_dict(self) -> dict:
        return {
            "S_t": self.S_t,
            "D_t": self.D_t,
            "R_b": {k: v.to_dict() for k, v in self.R_b.items()},
            "R_g": {k: v.to_dict() for k, v in self.R_g.items()},
            "A_t": {k: v.to_dict() for k, v in self.A_t.items()},
            "E_t": sorted(self.E_t),
            "C_t": {k: v.to_dict() for k, v in self.C_t.items()},
            "rules": self.rules,
        }

    def to_json(self, indent=2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, d: dict) -> SemanticSignature:
        return cls(
            S_t=d.get("S_t", {}),
            D_t=d.get("D_t", {}),
            R_b={k: BoolPredicate.from_dict(v) for k, v in d.get("R_b", {}).items()},
            R_g={k: GradedPredicate.from_dict(v) for k, v in d.get("R_g", {}).items()},
            A_t={k: ActionTemplate.from_dict(v) for k, v in d.get("A_t", {}).items()},
            E_t=set(d.get("E_t", [])),
            C_t={k: Constraint.from_dict(v) for k, v in d.get("C_t", {}).items()},
            rules=d.get("rules", []),
        )

    @classmethod
    def load(cls, path: str) -> SemanticSignature:
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def predicate_names(self) -> Set[str]:
        return set(self.R_b.keys()) | set(self.R_g.keys())

    def remove_predicate(self, name: str):
        """移除一个谓词及其在规则/约束/动作中的所有引用。"""
        self.R_b.pop(name, None)
        self.R_g.pop(name, None)
        # 从动作前后件中移除
        for act in self.A_t.values():
            act.preconditions = [p for p in act.preconditions if p.name != name]
            act.effects = [p for p in act.effects if p.name != name]
        # 从约束中移除
        to_remove = []
        for cname, c in self.C_t.items():
            c.condition = [p for p in c.condition if p.name != name]
            c.consequence = [p for p in c.consequence if p.name != name]
            if not c.condition and not c.consequence:
                to_remove.append(cname)
        for cname in to_remove:
            del self.C_t[cname]
        # 从规则中移除
        self.rules = [r for r in self.rules if name not in str(r)]

    def remove_entity(self, entity: str):
        """移除一个对象实例及其相关事实。"""
        self.D_t.pop(entity, None)

    def replace_predicate(self, old_name: str, new_name: str):
        """将谓词 old_name 重命名为 new_name（用于同义谓词合并）。"""
        if old_name in self.R_b:
            pred = self.R_b.pop(old_name)
            pred.name = new_name
            if new_name not in self.R_b:
                self.R_b[new_name] = pred
        if old_name in self.R_g:
            pred = self.R_g.pop(old_name)
            pred.name = new_name
            if new_name not in self.R_g:
                self.R_g[new_name] = pred
        for act in self.A_t.values():
            for p in act.preconditions + act.effects:
                if p.name == old_name:
                    p.name = new_name
        for c in self.C_t.values():
            for p in c.condition + c.consequence:
                if p.name == old_name:
                    p.name = new_name
