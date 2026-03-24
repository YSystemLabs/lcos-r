"""
系统配置 c_t，对应 tech-note §5.2。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.core import SemanticSignature, Predicate


@dataclass
class SystemConfig:
    """系统配置 c_t = (sigma, belief, active_tasks)。"""
    sigma: SemanticSignature
    # 简化的 belief state: init facts
    belief: List[Predicate] = field(default_factory=list)
    # 当前活跃任务列表
    active_tasks: List[Dict] = field(default_factory=list)
    # rewrite 历史
    rewrite_log: List[Dict] = field(default_factory=list)

    def snapshot(self) -> Dict:
        """返回当前配置的统计摘要。"""
        return {
            **self.sigma.stats(),
            "active_tasks": len(self.active_tasks),
            "rewrite_steps": len(self.rewrite_log),
        }
