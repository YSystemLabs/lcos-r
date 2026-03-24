"""
四组实验系统 + 采样任务 + 手动优化配置。
对应 tech-note §9.3。
"""

from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.core import SemanticSignature, Predicate
from src.rewrite.engine import run_global_rewrite, run_task_pruning

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
SIGNATURES_DIR = DATA_DIR / "signatures"
MANUAL_OPT_DIR = DATA_DIR / "manual_opt"

DOMAINS = ["domestic", "retail", "industrial", "restaurant", "office"]
DELTA_DOMAINS = DOMAINS[1:]  # 不含 domestic（它是 base）


def load_sigma_0() -> SemanticSignature:
    return SemanticSignature.load(str(SIGNATURES_DIR / "domestic.json"))


def load_deltas() -> List[SemanticSignature]:
    return [SemanticSignature.load(str(SIGNATURES_DIR / f"{d}_delta.json"))
            for d in DELTA_DOMAINS]


# ── 手动优化配置 ──
# 每阶段人工指定的谓词合并/规则折叠/对象裁剪
MANUAL_OPT_CONFIG = {
    1: {  # +retail
        "predicate_merges": [("on_shelf", "on"), ("in_cart", "in")],
        "rule_folds": ["checkout_ready+laundry_ready"],  # 同结构折叠
    },
    2: {  # +industrial
        "predicate_merges": [("on_belt", "on"), ("sorted_into", "in")],
        "rule_folds": ["assembly_ready+checkout_ready"],
    },
    3: {  # +restaurant
        "predicate_merges": [("on_tray", "on")],
        "rule_folds": ["dish_ready+logistics_complete"],
    },
    4: {  # +office
        "predicate_merges": [("on_desk", "on"), ("in_holder", "in")],
        "rule_folds": ["doc_processed+dish_ready"],
    },
}


def apply_manual_opt(sigma: SemanticSignature, stage: int) -> SemanticSignature:
    """应用手动优化配置。"""
    sigma_new = copy.deepcopy(sigma)
    config = MANUAL_OPT_CONFIG.get(stage, {})

    for old, new in config.get("predicate_merges", []):
        sigma_new.replace_predicate(old, new)

    # 手动规则折叠：按名称标记为已折叠
    fold_names = config.get("rule_folds", [])
    for fold_spec in fold_names:
        names = fold_spec.split("+")
        if len(names) >= 2:
            indices_to_remove = []
            for i, r in enumerate(sigma_new.rules):
                if r.get("name") in names[1:]:
                    indices_to_remove.append(i)
            for i in sorted(indices_to_remove, reverse=True):
                sigma_new.rules.pop(i)

    return sigma_new


# ── 四组实验系统 ──

class ExperimentSystem:
    """实验系统基类。"""
    name: str

    def setup(self, stage: int, sigma_0: SemanticSignature,
              deltas: List[SemanticSignature], task: Optional[Dict] = None) -> SemanticSignature:
        raise NotImplementedError


class Baseline(ExperimentSystem):
    """Baseline: 始终使用初始 Sigma_0，不扩展。"""
    name = "Baseline"

    def setup(self, stage, sigma_0, deltas, task=None):
        return copy.deepcopy(sigma_0)


class ExpandOnly(ExperimentSystem):
    """Expand-Only: 逐步合并 delta，不做 rewrite。"""
    name = "Expand-Only"

    def setup(self, stage, sigma_0, deltas, task=None):
        current = copy.deepcopy(sigma_0)
        for i in range(min(stage, len(deltas))):
            current = current.merge(deltas[i])
        return current


class ExpandRewrite(ExperimentSystem):
    """Expand+Rewrite: 合并 delta 后全局 rewrite (Pass 1+2)。
    Pass 3 per-task pruning 在实验 runner 中执行。"""
    name = "Expand+Rewrite"

    def setup(self, stage, sigma_0, deltas, task=None):
        current = copy.deepcopy(sigma_0)
        for i in range(min(stage, len(deltas))):
            current = current.merge(deltas[i])
        if stage > 0:
            current, _ = run_global_rewrite(current)
        return current


class ExpandManualOpt(ExperimentSystem):
    """Expand+ManualOpt: 合并 delta 后手动优化。"""
    name = "Expand+ManualOpt"

    def setup(self, stage, sigma_0, deltas, task=None):
        current = copy.deepcopy(sigma_0)
        for i in range(min(stage, len(deltas))):
            current = current.merge(deltas[i])
            current = apply_manual_opt(current, i + 1)
        return current


ALL_SYSTEMS = [Baseline(), ExpandOnly(), ExpandRewrite(), ExpandManualOpt()]


# ── 采样任务生成 ──
# 每领域生成可规划的测试任务

def generate_domain_tasks(domain: str, n: int = 30) -> List[Dict]:
    """为指定领域生成 n 个采样任务。"""
    tasks = []

    # 任务模板库
    TASK_TEMPLATES = {
        "domestic": [
            ("pick_cup", {"cup_1": "cup", "table_1": "surface", "robot": "agent"},
             [("on", ["cup_1", "table_1"]), ("reachable", ["robot", "cup_1"]), ("clear", ["cup_1"])],
             [("holding", ["robot", "cup_1"])]),
            ("place_bowl", {"bowl_1": "bowl", "counter_1": "surface", "robot": "agent"},
             [("holding", ["robot", "bowl_1"])],
             [("on", ["bowl_1", "counter_1"])]),
            ("open_fridge", {"fridge_1": "fridge", "robot": "agent"},
             [("reachable", ["robot", "fridge_1"]), ("closed", ["fridge_1"])],
             [("open", ["fridge_1"])]),
            ("wipe_table", {"table_1": "surface", "sponge_1": "sponge", "robot": "agent"},
             [("holding", ["robot", "sponge_1"]), ("dirty", ["table_1"])],
             [("clean", ["table_1"])]),
            ("fold_shirt", {"shirt_1": "shirt", "robot": "agent"},
             [("reachable", ["robot", "shirt_1"])],
             [("folded", ["shirt_1"])]),
            ("close_drawer", {"drawer_1": "drawer", "robot": "agent"},
             [("reachable", ["robot", "drawer_1"]), ("open", ["drawer_1"])],
             [("closed", ["drawer_1"])]),
            ("hang_towel", {"towel_1": "towel", "hook_1": "object", "robot": "agent"},
             [("holding", ["robot", "towel_1"])],
             [("hung", ["towel_1"])]),
            ("sweep_floor", {"floor_1": "surface", "broom_1": "broom", "robot": "agent"},
             [("holding", ["robot", "broom_1"])],
             [("clean", ["floor_1"])]),
            ("press_microwave", {"microwave_1": "microwave", "robot": "agent"},
             [("reachable", ["robot", "microwave_1"])],
             [("powered_on", ["microwave_1"])]),
            ("pick_place_bottle", {"bottle_1": "bottle", "table_1": "surface", "counter_1": "surface", "robot": "agent"},
             [("on", ["bottle_1", "table_1"]), ("reachable", ["robot", "bottle_1"]), ("clear", ["bottle_1"])],
             [("on", ["bottle_1", "counter_1"])]),
        ],
        "retail": [
            ("scan_item", {"snack_1": "snack", "scanner_1": "barcode_scanner", "robot": "agent"},
             [("holding", ["robot", "scanner_1"])],
             [("scanned", ["snack_1"])]),
            ("bag_fruit", {"fruit_1": "fruit", "bag_1": "plastic_bag", "robot": "agent"},
             [("holding", ["robot", "fruit_1"])],
             [("bagged", ["fruit_1"])]),
            ("restock_shelf", {"snack_1": "snack", "shelf_1": "shelf", "robot": "agent"},
             [("holding", ["robot", "snack_1"])],
             [("on_shelf", ["snack_1", "shelf_1"])]),
        ],
        "industrial": [
            ("pack_box", {"module_1": "memory_module", "box_1": "target_box", "robot": "agent"},
             [("holding", ["robot", "module_1"])],
             [("packed", ["module_1"])]),
            ("lift_dumbbell", {"dumbbell_1": "dumbbell", "robot": "agent"},
             [("reachable", ["robot", "dumbbell_1"])],
             [("holding", ["robot", "dumbbell_1"])]),
        ],
        "restaurant": [
            ("chop_food", {"salad_1": "salad", "knife_1": "knife", "robot": "agent"},
             [("holding", ["robot", "knife_1"])],
             [("sliced", ["salad_1"])]),
            ("knead_dough", {"dough_1": "dough", "robot": "agent"},
             [("reachable", ["robot", "dough_1"])],
             [("kneaded", ["dough_1"])]),
            ("serve_food", {"noodle_1": "noodle", "tray_1": "tray", "robot": "agent"},
             [("on_tray", ["noodle_1", "tray_1"])],
             [("served", ["noodle_1"])]),
        ],
        "office": [
            ("stamp_form", {"form_1": "reimbursement_form", "stamp_1": "stamp", "robot": "agent"},
             [("holding", ["robot", "stamp_1"])],
             [("stamped", ["form_1"])]),
            ("shred_doc", {"form_1": "reimbursement_form", "shredder_1": "shredder", "robot": "agent"},
             [("reachable", ["robot", "shredder_1"]), ("powered_on", ["shredder_1"])],
             [("shredded", ["form_1"])]),
            ("print_doc", {"form_1": "reimbursement_form", "printer_1": "printer", "robot": "agent"},
             [("reachable", ["robot", "printer_1"]), ("powered_on", ["printer_1"])],
             [("printed", ["form_1"])]),
        ],
    }

    templates = TASK_TEMPLATES.get(domain, TASK_TEMPLATES["domestic"])

    for i in range(n):
        tmpl_idx = i % len(templates)
        name_base, objects, init_raw, goal_raw = templates[tmpl_idx]
        # 添加变体后缀
        suffix = f"_v{i // len(templates)}" if i >= len(templates) else ""
        task = {
            "name": f"{name_base}{suffix}",
            "domain": domain,
            "objects": dict(objects),
            "init": [Predicate(n, list(a)) for n, a in init_raw],
            "goal": [Predicate(n, list(a)) for n, a in goal_raw],
        }
        tasks.append(task)

    return tasks


# ── 跨域组合任务 ──
# 设计原则：利用 synonym predicate 的歧义使 Expand-Only 不可规划
#
# 关键机制：
# - EO 中 place(obj, tray) 产生 on(obj, tray)，但 serve 需要 on_tray(obj, tray) → 匹配失败
# - EO 中没有动作产生 on_desk/on_belt/on_tray/in_cart → 这些作为 goal 不可达
# - ER 中 on_tray→on, on_desk→on 等，统一为 on → place + serve 可以链接

CROSS_DOMAIN_TEMPLATES = [
    # ── Group 1: serve-chain (Type A, 3 步) ──
    # place 产生 on(food, tray), serve 在 EO 需要 on_tray → FAIL
    ("xd_serve_salad",
     {"salad_1": "salad", "counter_1": "surface", "tray_1": "tray", "robot": "agent"},
     [("on", ["salad_1", "counter_1"]), ("reachable", ["robot", "salad_1"]),
      ("clear", ["salad_1"])],
     [("served", ["salad_1"])],
     "A", ["domestic", "restaurant"]),

    ("xd_serve_fruit",
     {"fruit_1": "fruit", "shelf_1": "shelf", "tray_1": "tray", "robot": "agent"},
     [("on_shelf", ["fruit_1", "shelf_1"]), ("reachable", ["robot", "fruit_1"]),
      ("clear", ["fruit_1"])],
     [("served", ["fruit_1"])],
     "A", ["retail", "restaurant"]),

    ("xd_serve_noodle",
     {"noodle_1": "noodle", "table_1": "surface", "tray_1": "tray", "robot": "agent"},
     [("on", ["noodle_1", "table_1"]), ("reachable", ["robot", "noodle_1"]),
      ("clear", ["noodle_1"])],
     [("served", ["noodle_1"])],
     "A", ["domestic", "restaurant"]),

    ("xd_serve_dough",
     {"dough_1": "dough", "counter_1": "surface", "tray_1": "tray", "robot": "agent"},
     [("on", ["dough_1", "counter_1"]), ("reachable", ["robot", "dough_1"]),
      ("clear", ["dough_1"])],
     [("served", ["dough_1"])],
     "A", ["domestic", "restaurant"]),

    # ── Group 2: on_desk goal (Type A, 2 步) ──
    # EO 中没有动作产生 on_desk → FAIL；ER remap 为 on → place 可达
    ("xd_pen_to_desk",
     {"pen_1": "pen", "table_1": "surface", "whiteboard_1": "whiteboard", "robot": "agent"},
     [("on", ["pen_1", "table_1"]), ("reachable", ["robot", "pen_1"]),
      ("clear", ["pen_1"])],
     [("on_desk", ["pen_1", "whiteboard_1"])],
     "A", ["domestic", "office"]),

    ("xd_form_to_desk",
     {"form_1": "reimbursement_form", "shelf_1": "shelf", "whiteboard_1": "whiteboard", "robot": "agent"},
     [("on_shelf", ["form_1", "shelf_1"]), ("reachable", ["robot", "form_1"]),
      ("clear", ["form_1"])],
     [("on_desk", ["form_1", "whiteboard_1"])],
     "A", ["retail", "office"]),

    ("xd_module_to_desk",
     {"module_1": "memory_module", "belt_1": "conveyor_belt", "whiteboard_1": "whiteboard", "robot": "agent"},
     [("on_belt", ["module_1", "belt_1"]), ("reachable", ["robot", "module_1"]),
      ("clear", ["module_1"])],
     [("on_desk", ["module_1", "whiteboard_1"])],
     "A", ["industrial", "office"]),

    # ── Group 3: on_belt goal (Type A, 2 步) ──
    # EO 中没有动作产生 on_belt → FAIL
    ("xd_item_to_belt",
     {"bottle_1": "bottle", "table_1": "surface", "belt_1": "conveyor_belt", "robot": "agent"},
     [("on", ["bottle_1", "table_1"]), ("reachable", ["robot", "bottle_1"]),
      ("clear", ["bottle_1"])],
     [("on_belt", ["bottle_1", "belt_1"])],
     "A", ["domestic", "industrial"]),

    ("xd_snack_to_belt",
     {"snack_1": "snack", "shelf_1": "shelf", "belt_1": "conveyor_belt", "robot": "agent"},
     [("on_shelf", ["snack_1", "shelf_1"]), ("reachable", ["robot", "snack_1"]),
      ("clear", ["snack_1"])],
     [("on_belt", ["snack_1", "belt_1"])],
     "A", ["retail", "industrial"]),

    # ── Group 4: on_tray goal (Type A, 2 步) ──
    # EO 中没有动作产生 on_tray → FAIL
    ("xd_cup_to_tray",
     {"cup_1": "cup", "table_1": "surface", "tray_1": "tray", "robot": "agent"},
     [("on", ["cup_1", "table_1"]), ("reachable", ["robot", "cup_1"]),
      ("clear", ["cup_1"])],
     [("on_tray", ["cup_1", "tray_1"])],
     "A", ["domestic", "restaurant"]),

    ("xd_fruit_to_tray",
     {"fruit_1": "fruit", "shelf_1": "shelf", "tray_1": "tray", "robot": "agent"},
     [("on_shelf", ["fruit_1", "shelf_1"]), ("reachable", ["robot", "fruit_1"]),
      ("clear", ["fruit_1"])],
     [("on_tray", ["fruit_1", "tray_1"])],
     "A", ["retail", "restaurant"]),

    # ── Group 5: Multi-step chains (Type A+C, 4-5 步) ──

    ("xd_serve_crowded",  # 6 objects, serve-chain + extra distractors
     {"salad_1": "salad", "bowl_1": "bowl", "cup_1": "cup",
      "counter_1": "surface", "tray_1": "tray", "robot": "agent"},
     [("on", ["salad_1", "counter_1"]), ("on", ["bowl_1", "counter_1"]),
      ("reachable", ["robot", "salad_1"]), ("reachable", ["robot", "bowl_1"]),
      ("clear", ["salad_1"]), ("clear", ["bowl_1"])],
     [("served", ["salad_1"])],
     "A", ["domestic", "restaurant"]),

    ("xd_desk_crowded",  # 6 objects, on_desk + distractors
     {"pen_1": "pen", "form_1": "reimbursement_form", "stamp_1": "stamp",
      "table_1": "surface", "whiteboard_1": "whiteboard", "robot": "agent"},
     [("on", ["pen_1", "table_1"]), ("on", ["form_1", "table_1"]),
      ("reachable", ["robot", "pen_1"]), ("reachable", ["robot", "form_1"]),
      ("clear", ["pen_1"]), ("clear", ["form_1"])],
     [("on_desk", ["pen_1", "whiteboard_1"])],
     "A", ["domestic", "office"]),

    ("xd_lift_to_desk",  # industrial → office, 2 步
     {"dumbbell_1": "dumbbell", "whiteboard_1": "whiteboard", "robot": "agent"},
     [("reachable", ["robot", "dumbbell_1"]), ("clear", ["dumbbell_1"])],
     [("on_desk", ["dumbbell_1", "whiteboard_1"])],
     "A", ["industrial", "office"]),

    ("xd_belt_crowded",  # 5 objects, on_belt + distractor
     {"module_1": "memory_module", "box_1": "target_box",
      "table_1": "surface", "belt_1": "conveyor_belt", "robot": "agent"},
     [("on", ["module_1", "table_1"]), ("reachable", ["robot", "module_1"]),
      ("clear", ["module_1"])],
     [("on_belt", ["module_1", "belt_1"])],
     "A", ["domestic", "industrial"]),

    ("xd_tray_crowded",  # 5 objects, on_tray + distractor
     {"fruit_1": "fruit", "snack_1": "snack",
      "shelf_1": "shelf", "tray_1": "tray", "robot": "agent"},
     [("on_shelf", ["fruit_1", "shelf_1"]), ("on_shelf", ["snack_1", "shelf_1"]),
      ("reachable", ["robot", "fruit_1"]), ("reachable", ["robot", "snack_1"]),
      ("clear", ["fruit_1"]), ("clear", ["snack_1"])],
     [("on_tray", ["fruit_1", "tray_1"])],
     "A", ["retail", "restaurant"]),

    ("xd_fold_to_tray",  # domestic → restaurant, 3 步
     {"shirt_1": "shirt", "tray_1": "tray", "robot": "agent"},
     [("reachable", ["robot", "shirt_1"]), ("clear", ["shirt_1"])],
     [("folded", ["shirt_1"]), ("on_tray", ["shirt_1", "tray_1"])],
     "A", ["domestic", "restaurant"]),

    ("xd_triple_chain",  # industrial → domestic → restaurant, 3 步
     {"module_1": "memory_module", "counter_1": "surface",
      "tray_1": "tray", "robot": "agent"},
     [("reachable", ["robot", "module_1"]), ("clear", ["module_1"])],
     [("on_tray", ["module_1", "tray_1"])],
     "A", ["industrial", "domestic", "restaurant"]),
]


def generate_cross_domain_tasks(n: int = 30) -> List[Dict]:
    """生成 n 个跨域组合任务。"""
    tasks = []
    templates = CROSS_DOMAIN_TEMPLATES

    for i in range(n):
        tmpl_idx = i % len(templates)
        name_base, objects, init_raw, goal_raw, dtype, domains = templates[tmpl_idx]
        suffix = f"_v{i // len(templates)}" if i >= len(templates) else ""
        task = {
            "name": f"{name_base}{suffix}",
            "domain": "cross_domain",
            "objects": dict(objects),
            "init": [Predicate(nm, list(a)) for nm, a in init_raw],
            "goal": [Predicate(nm, list(a)) for nm, a in goal_raw],
            "degrade_type": dtype,
            "involved_domains": list(domains),
        }
        tasks.append(task)

    return tasks
