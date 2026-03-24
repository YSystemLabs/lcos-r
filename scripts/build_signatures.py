#!/usr/bin/env python3
"""
步骤 3：从 AgiBot World 提取数据构建五领域的 SemanticSignature。

家居领域 → 完整 Sigma_0（基线）
其余四领域 → 增量 Delta_k（仅独有要素）

关键设计：故意保留跨领域同义谓词，留给 rewrite pass 去合并。
"""

import json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.core import (
    SemanticSignature, BoolPredicate, GradedPredicate,
    ActionTemplate, Constraint, TypedParam, Predicate,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXTRACTION = DATA_DIR / "agibot-world" / "signature_extraction.json"
OUT_DIR = DATA_DIR / "signatures"

# ── 类型层次（手工设计，基于 AgiBot World 的物体类别） ──
TYPE_HIERARCHY = {
    "object": None,
    "container": "object",
    "surface": "object",
    "tool": "object",
    "food": "object",
    "appliance": "object",
    "clothing": "object",
    "document": "object",
    "furniture": "object",
    "location": None,
    "agent": None,
}

# ── 每个领域的特有类型 ──
DOMAIN_TYPES = {
    "domestic": {
        "cup": "container", "bowl": "container", "plate": "container",
        "bottle": "container", "pot": "container", "basket": "container",
        "drawer": "container", "fridge": "appliance", "microwave": "appliance",
        "oven": "appliance", "toaster": "appliance", "kettle": "appliance",
        "washing_machine": "appliance", "vacuum": "tool", "broom": "tool",
        "mop": "tool", "cloth": "tool", "sponge": "tool", "iron": "tool",
        "hanger": "tool", "table": "surface", "counter": "surface",
        "bed": "furniture", "sofa": "furniture", "wardrobe": "furniture",
        "bookshelf": "furniture", "curtain": "object", "pillow": "object",
        "towel": "clothing", "shorts": "clothing", "shirt": "clothing",
        "toy": "object", "flower": "object", "key": "object",
    },
    "retail": {
        "shelf": "surface", "shopping_cart": "container", "checkout_counter": "surface",
        "cash_register": "appliance", "barcode_scanner": "tool",
        "plastic_bag": "container", "cardboard_box": "container",
        "snack": "food", "fruit": "food", "frozen_item": "food",
        "price_tag": "object", "metal_detector": "tool", "gong": "tool",
    },
    "industrial": {
        "conveyor_belt": "surface", "material_frame": "container",
        "target_box": "container", "logistics_box": "container",
        "air_column_film": "tool", "permanent_magnet": "object",
        "medicine_box": "container", "memory_module": "object",
        "dumbbell": "object", "storage_box_large": "container",
    },
    "restaurant": {
        "tray": "container", "serving_plate": "container",
        "teapot": "container", "milk_tea_cup": "container",
        "menu": "document", "cutting_board": "surface",
        "dough": "food", "noodle": "food", "salad": "food",
        "straw": "tool", "knife": "tool", "ladle": "tool",
        "feed_basket": "container",
    },
    "office": {
        "pen": "tool", "pen_holder": "container", "whiteboard": "surface",
        "whiteboard_eraser": "tool", "shredder": "appliance",
        "printer": "appliance", "tissue_box": "container",
        "stamp": "tool", "nameplate": "object", "door": "object",
        "door_lock": "object", "reimbursement_form": "document",
        "felt_bag": "container",
    },
}

# ── 布尔谓词定义 ──
# 基础谓词（家居领域包含）
BASE_BOOL_PREDICATES = {
    "on": BoolPredicate("on", 2, ["object", "surface"]),
    "in": BoolPredicate("in", 2, ["object", "container"]),
    "holding": BoolPredicate("holding", 2, ["agent", "object"]),
    "reachable": BoolPredicate("reachable", 2, ["agent", "object"]),
    "clear": BoolPredicate("clear", 1, ["surface"]),
    "open": BoolPredicate("open", 1, ["container"]),
    "closed": BoolPredicate("closed", 1, ["container"]),
    "clean": BoolPredicate("clean", 1, ["object"]),
    "dirty": BoolPredicate("dirty", 1, ["object"]),
    "folded": BoolPredicate("folded", 1, ["clothing"]),
    "hung": BoolPredicate("hung", 1, ["clothing"]),
    "boiling": BoolPredicate("boiling", 1, ["container"]),
    "powered_on": BoolPredicate("powered_on", 1, ["appliance"]),
    "empty": BoolPredicate("empty", 1, ["container"]),
}

# 领域特有谓词（故意保留同义词！）
DOMAIN_BOOL_PREDICATES = {
    "domestic": {
        "ironed": BoolPredicate("ironed", 1, ["clothing"]),
        "plugged_in": BoolPredicate("plugged_in", 1, ["appliance"]),
        "curtain_open": BoolPredicate("curtain_open", 1, ["object"]),
        "arranged": BoolPredicate("arranged", 1, ["object"]),
        "stacked": BoolPredicate("stacked", 2, ["object", "object"]),
    },
    "retail": {
        "on_shelf": BoolPredicate("on_shelf", 2, ["object", "surface"]),  # 同义: on
        "scanned": BoolPredicate("scanned", 1, ["object"]),
        "bagged": BoolPredicate("bagged", 1, ["object"]),
        "restocked": BoolPredicate("restocked", 1, ["surface"]),
        "in_cart": BoolPredicate("in_cart", 2, ["object", "container"]),  # 同义: in
        "price_checked": BoolPredicate("price_checked", 1, ["object"]),
    },
    "industrial": {
        "assembled": BoolPredicate("assembled", 2, ["object", "object"]),
        "calibrated": BoolPredicate("calibrated", 1, ["object"]),
        "packed": BoolPredicate("packed", 1, ["object"]),
        "on_belt": BoolPredicate("on_belt", 2, ["object", "surface"]),  # 同义: on
        "sorted_into": BoolPredicate("sorted_into", 2, ["object", "container"]),  # 同义: in
        "inserted": BoolPredicate("inserted", 2, ["object", "object"]),
    },
    "restaurant": {
        "cooked": BoolPredicate("cooked", 1, ["food"]),
        "portioned": BoolPredicate("portioned", 1, ["food"]),
        "served": BoolPredicate("served", 1, ["food"]),
        "on_tray": BoolPredicate("on_tray", 2, ["object", "container"]),  # 同义: on
        "sliced": BoolPredicate("sliced", 1, ["food"]),
        "stirred": BoolPredicate("stirred", 1, ["food"]),
        "kneaded": BoolPredicate("kneaded", 1, ["food"]),
    },
    "office": {
        "filed": BoolPredicate("filed", 1, ["document"]),
        "stamped": BoolPredicate("stamped", 1, ["document"]),
        "shredded": BoolPredicate("shredded", 1, ["document"]),
        "printed": BoolPredicate("printed", 1, ["document"]),
        "locked": BoolPredicate("locked", 1, ["object"]),
        "on_desk": BoolPredicate("on_desk", 2, ["object", "surface"]),  # 同义: on
        "in_holder": BoolPredicate("in_holder", 2, ["tool", "container"]),  # 同义: in
    },
}

# 同义谓词对（供 rewrite pass 1 检测和合并）
SYNONYM_PAIRS = [
    ("on", "on_shelf"),
    ("on", "on_belt"),
    ("on", "on_tray"),
    ("on", "on_desk"),
    ("in", "in_cart"),
    ("in", "sorted_into"),
    ("in", "in_holder"),
]

# ── 渐变谓词 ──
BASE_GRADED_PREDICATES = {
    "hot": GradedPredicate("hot", 1, ["object"], threshold=0.7),
    "fragile": GradedPredicate("fragile", 1, ["object"], threshold=0.5),
    "full": GradedPredicate("full", 1, ["container"], threshold=0.8),
    "heavy": GradedPredicate("heavy", 1, ["object"], threshold=0.7),
}

DOMAIN_GRADED_PREDICATES = {
    "domestic": {
        "wet": GradedPredicate("wet", 1, ["object"], threshold=0.5),
        "wrinkled": GradedPredicate("wrinkled", 1, ["clothing"], threshold=0.5),
    },
    "retail": {
        "shelf_load": GradedPredicate("shelf_load", 1, ["surface"], threshold=0.9),
    },
    "industrial": {
        "aligned": GradedPredicate("aligned", 2, ["object", "object"], threshold=0.9),
    },
    "restaurant": {
        "temperature": GradedPredicate("temperature", 1, ["food"], threshold=0.5),
        "seasoned": GradedPredicate("seasoned", 1, ["food"], threshold=0.5),
    },
    "office": {
        "confidential": GradedPredicate("confidential", 1, ["document"], threshold=0.5),
    },
}

# ── 动作模板构造 ──
def _make_action(name, params, preconds, effects):
    return ActionTemplate(
        name=name,
        parameters=[TypedParam(n, t) for n, t in params],
        preconditions=[Predicate(n, a) for n, a in preconds],
        effects=[Predicate(n, a, neg) for n, a, neg in effects],
    )


# 基础动作（家居领域包含）
def _base_actions():
    return {
        "pick": _make_action("pick", [("obj", "object"), ("agent", "agent")],
            [("reachable", ["agent", "obj"]), ("clear", ["obj"])],
            [("holding", ["agent", "obj"], False), ("on", ["obj", "_src"], True)]),
        "place": _make_action("place", [("obj", "object"), ("dst", "surface"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            [("on", ["obj", "dst"], False), ("holding", ["agent", "obj"], True)]),
        "pour": _make_action("pour", [("src", "container"), ("dst", "container"), ("agent", "agent")],
            [("holding", ["agent", "src"])],
            [("empty", ["src"], False), ("full", ["dst"], True)]),
        "open": _make_action("open", [("obj", "container"), ("agent", "agent")],
            [("reachable", ["agent", "obj"]), ("closed", ["obj"])],
            [("open", ["obj"], False), ("closed", ["obj"], True)]),
        "close": _make_action("close", [("obj", "container"), ("agent", "agent")],
            [("reachable", ["agent", "obj"]), ("open", ["obj"])],
            [("closed", ["obj"], False), ("open", ["obj"], True)]),
        "wipe": _make_action("wipe", [("surface", "surface"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"]), ("dirty", ["surface"])],
            [("clean", ["surface"], False), ("dirty", ["surface"], True)]),
        "push": _make_action("push", [("obj", "object"), ("agent", "agent")],
            [("reachable", ["agent", "obj"])],
            []),
        "pull": _make_action("pull", [("obj", "object"), ("agent", "agent")],
            [("reachable", ["agent", "obj"])],
            []),
        "carry": _make_action("carry", [("obj", "object"), ("dst", "location"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            []),
        "handover": _make_action("handover", [("obj", "object"), ("src", "agent"), ("dst", "agent")],
            [("holding", ["src", "obj"])],
            [("holding", ["dst", "obj"], False), ("holding", ["src", "obj"], True)]),
        "grasp": _make_action("grasp", [("obj", "object"), ("agent", "agent")],
            [("reachable", ["agent", "obj"])],
            [("holding", ["agent", "obj"], False)]),
        "release": _make_action("release", [("obj", "object"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            [("holding", ["agent", "obj"], True)]),
        "press_button": _make_action("press_button", [("appliance", "appliance"), ("agent", "agent")],
            [("reachable", ["agent", "appliance"])],
            [("powered_on", ["appliance"], False)]),
        "insert": _make_action("insert", [("obj", "object"), ("dst", "object"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            [("holding", ["agent", "obj"], True)]),
        "fold": _make_action("fold", [("item", "clothing"), ("agent", "agent")],
            [("reachable", ["agent", "item"])],
            [("folded", ["item"], False)]),
        "hang": _make_action("hang", [("item", "object"), ("hook", "object"), ("agent", "agent")],
            [("holding", ["agent", "item"])],
            [("hung", ["item"], False), ("holding", ["agent", "item"], True)]),
        "sweep": _make_action("sweep", [("area", "surface"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"])],
            [("clean", ["area"], False)]),
        "lift": _make_action("lift", [("obj", "object"), ("agent", "agent")],
            [("reachable", ["agent", "obj"])],
            [("holding", ["agent", "obj"], False)]),
        "drop": _make_action("drop", [("obj", "object"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            [("holding", ["agent", "obj"], True)]),
        "stir": _make_action("stir", [("container", "container"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"])],
            []),
        "scoop": _make_action("scoop", [("src", "container"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"])],
            []),
    }


# 领域特有动作
DOMAIN_ACTIONS = {
    "domestic": {
        "iron": _make_action("iron", [("item", "clothing"), ("iron", "tool"), ("agent", "agent")],
            [("holding", ["agent", "iron"]), ("powered_on", ["iron"])],
            [("ironed", ["item"], False), ("wrinkled", ["item"], True)]),
        "vacuum": _make_action("vacuum", [("area", "surface"), ("vac", "tool"), ("agent", "agent")],
            [("holding", ["agent", "vac"]), ("powered_on", ["vac"])],
            [("clean", ["area"], False)]),
        "mop": _make_action("mop", [("area", "surface"), ("mop", "tool"), ("agent", "agent")],
            [("holding", ["agent", "mop"])],
            [("clean", ["area"], False)]),
        "peel": _make_action("peel", [("food", "food"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"])],
            []),
        "brush": _make_action("brush", [("obj", "object"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"])],
            [("clean", ["obj"], False)]),
    },
    "retail": {
        "scan": _make_action("scan", [("obj", "object"), ("scanner", "tool"), ("agent", "agent")],
            [("holding", ["agent", "scanner"])],
            [("scanned", ["obj"], False)]),
        "bag": _make_action("bag", [("obj", "object"), ("bag", "container"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            [("bagged", ["obj"], False), ("in_cart", ["obj", "bag"], False)]),
        "restock": _make_action("restock", [("obj", "object"), ("shelf", "surface"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            [("on_shelf", ["obj", "shelf"], False), ("restocked", ["shelf"], False)]),
    },
    "industrial": {
        "assemble": _make_action("assemble", [("part", "object"), ("base", "object"), ("agent", "agent")],
            [("holding", ["agent", "part"]), ("calibrated", ["part"])],
            [("assembled", ["part", "base"], False)]),
        "pack": _make_action("pack", [("obj", "object"), ("box", "container"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            [("packed", ["obj"], False), ("sorted_into", ["obj", "box"], False)]),
        "transport": _make_action("transport", [("obj", "object"), ("dst", "location"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            []),
        "lift_heavy": _make_action("lift_heavy", [("obj", "object"), ("agent", "agent")],
            [("reachable", ["agent", "obj"])],
            [("holding", ["agent", "obj"], False)]),
    },
    "restaurant": {
        "chop": _make_action("chop", [("food", "food"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"])],
            [("sliced", ["food"], False)]),
        "serve": _make_action("serve", [("food", "food"), ("tray", "container"), ("agent", "agent")],
            [("on_tray", ["food", "tray"])],
            [("served", ["food"], False)]),
        "knead": _make_action("knead", [("food", "food"), ("agent", "agent")],
            [("reachable", ["agent", "food"])],
            [("kneaded", ["food"], False)]),
        "roll_dough": _make_action("roll_dough", [("food", "food"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"]), ("kneaded", ["food"])],
            []),
        "hand_out": _make_action("hand_out", [("obj", "object"), ("agent", "agent")],
            [("holding", ["agent", "obj"])],
            [("holding", ["agent", "obj"], True)]),
        "cut": _make_action("cut", [("food", "food"), ("tool", "tool"), ("agent", "agent")],
            [("holding", ["agent", "tool"])],
            [("sliced", ["food"], False)]),
    },
    "office": {
        "stamp_doc": _make_action("stamp_doc", [("doc", "document"), ("stamp", "tool"), ("agent", "agent")],
            [("holding", ["agent", "stamp"])],
            [("stamped", ["doc"], False)]),
        "shred": _make_action("shred", [("doc", "document"), ("shredder", "appliance"), ("agent", "agent")],
            [("reachable", ["agent", "shredder"]), ("powered_on", ["shredder"])],
            [("shredded", ["doc"], False)]),
        "print_doc": _make_action("print_doc", [("doc", "document"), ("printer", "appliance"), ("agent", "agent")],
            [("reachable", ["agent", "printer"]), ("powered_on", ["printer"])],
            [("printed", ["doc"], False)]),
        "file": _make_action("file", [("doc", "document"), ("box", "container"), ("agent", "agent")],
            [("holding", ["agent", "doc"])],
            [("filed", ["doc"], False), ("in_holder", ["doc", "box"], False)]),
        "turn_key": _make_action("turn_key", [("key", "object"), ("lock", "object"), ("agent", "agent")],
            [("holding", ["agent", "key"])],
            [("locked", ["lock"], True)]),
        "slide": _make_action("slide", [("obj", "object"), ("agent", "agent")],
            [("reachable", ["agent", "obj"])],
            []),
    },
}

# ── 约束定义 ──
BASE_CONSTRAINTS = {
    "type_consistency": Constraint("type_consistency",
        [Predicate("holding", ["agent", "obj"])],
        [Predicate("reachable", ["agent", "obj"])]),
    "safety_hot": Constraint("safety_hot",
        [Predicate("hot", ["obj"])],
        [Predicate("allow_bare_grasp", ["obj"], negated=True)]),
    "safety_fragile": Constraint("safety_fragile",
        [Predicate("fragile", ["obj"])],
        [Predicate("allow_force_grasp", ["obj"], negated=True)]),
}

DOMAIN_CONSTRAINTS = {
    "domestic": {
        "full_no_rotate": Constraint("full_no_rotate",
            [Predicate("full", ["container"])],
            [Predicate("allow_rotate", ["container"], negated=True)]),
    },
    "retail": {
        "shelf_weight": Constraint("shelf_weight",
            [Predicate("shelf_load", ["shelf"]), Predicate("heavy", ["obj"])],
            [Predicate("allow_place_on_shelf", ["obj", "shelf"], negated=True)]),
        "scan_before_bag": Constraint("scan_before_bag",
            [Predicate("scanned", ["obj"], negated=True)],
            [Predicate("allow_bag", ["obj"], negated=True)]),
    },
    "industrial": {
        "calibrate_before_assemble": Constraint("calibrate_before_assemble",
            [Predicate("calibrated", ["part"], negated=True)],
            [Predicate("allow_assemble", ["part"], negated=True)]),
        "heavy_two_hand": Constraint("heavy_two_hand",
            [Predicate("heavy", ["obj"])],
            [Predicate("require_two_hand", ["obj"])]),
    },
    "restaurant": {
        "hot_safety": Constraint("hot_food_safety",
            [Predicate("hot", ["food"])],
            [Predicate("allow_bare_touch", ["food"], negated=True)]),
        "cook_before_serve": Constraint("cook_before_serve",
            [Predicate("cooked", ["food"], negated=True)],
            [Predicate("allow_serve", ["food"], negated=True)]),
    },
    "office": {
        "confidential_shred": Constraint("confidential_shred",
            [Predicate("confidential", ["doc"])],
            [Predicate("require_shred", ["doc"])]),
        "file_order": Constraint("file_order",
            [Predicate("stamped", ["doc"], negated=True)],
            [Predicate("allow_file", ["doc"], negated=True)]),
    },
}

# ── 规则定义（推理/派生规则） ──
BASE_RULES = [
    {"name": "graspable_derived", "type": "derivation",
     "body": "graspable(x) ≡ reachable(x) ∧ ¬blocked(x)"},
    {"name": "safe_to_touch", "type": "derivation",
     "body": "safe_to_touch(x) ≡ ¬hot(x) ∨ holding_tool(agent)"},
]

DOMAIN_RULES = {
    "domestic": [
        {"name": "laundry_ready", "type": "derivation",
         "body": "laundry_ready(x) ≡ dirty(x) ∧ clothing(x)"},
        {"name": "cookware_hot_after_use", "type": "causal",
         "body": "used_on_stove(x) → hot(x)"},
    ],
    "retail": [
        {"name": "checkout_ready", "type": "derivation",
         "body": "checkout_ready(x) ≡ scanned(x) ∧ bagged(x)"},
        {"name": "restock_needed", "type": "derivation",
         "body": "restock_needed(shelf) ≡ ¬restocked(shelf) ∧ empty(shelf)"},
    ],
    "industrial": [
        {"name": "assembly_ready", "type": "derivation",
         "body": "assembly_ready(x) ≡ calibrated(x) ∧ ¬assembled(x, _)"},
        {"name": "logistics_complete", "type": "derivation",
         "body": "logistics_complete(x) ≡ packed(x) ∧ on_belt(x, belt)"},
    ],
    "restaurant": [
        {"name": "dish_ready", "type": "derivation",
         "body": "dish_ready(x) ≡ cooked(x) ∧ portioned(x)"},
        {"name": "order_complete", "type": "derivation",
         "body": "order_complete(x) ≡ served(x)"},
    ],
    "office": [
        {"name": "doc_processed", "type": "derivation",
         "body": "doc_processed(x) ≡ stamped(x) ∧ filed(x)"},
        {"name": "room_secured", "type": "derivation",
         "body": "room_secured(room) ≡ locked(room) ∧ ¬powered_on(light)"},
    ],
}


def build_domestic_sigma() -> SemanticSignature:
    """构建家居领域完整签名 Sigma_0。"""
    sigma = SemanticSignature()

    # 类型
    sigma.S_t = {**TYPE_HIERARCHY, **DOMAIN_TYPES["domestic"]}

    # 布尔谓词
    sigma.R_b = {**BASE_BOOL_PREDICATES, **DOMAIN_BOOL_PREDICATES["domestic"]}

    # 渐变谓词
    sigma.R_g = {**BASE_GRADED_PREDICATES, **DOMAIN_GRADED_PREDICATES["domestic"]}

    # 动作模板
    sigma.A_t = {**_base_actions(), **DOMAIN_ACTIONS["domestic"]}

    # 效果词汇
    sigma.E_t = {"can-grasp", "will-spill", "collision-risk", "goal-progress",
                 "clean-result", "fold-result", "cook-result"}

    # 约束
    sigma.C_t = {**BASE_CONSTRAINTS, **DOMAIN_CONSTRAINTS["domestic"]}

    # 规则
    sigma.rules = BASE_RULES + DOMAIN_RULES["domestic"]

    return sigma


def build_domain_delta(domain: str) -> SemanticSignature:
    """构建领域增量 Delta_k（仅该领域独有要素）。"""
    delta = SemanticSignature()

    delta.S_t = DOMAIN_TYPES.get(domain, {})
    delta.R_b = DOMAIN_BOOL_PREDICATES.get(domain, {})
    delta.R_g = DOMAIN_GRADED_PREDICATES.get(domain, {})
    delta.A_t = DOMAIN_ACTIONS.get(domain, {})
    delta.C_t = DOMAIN_CONSTRAINTS.get(domain, {})
    delta.rules = DOMAIN_RULES.get(domain, [])

    return delta


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 家居 = 完整基线
    sigma_0 = build_domestic_sigma()
    sigma_0.save(str(OUT_DIR / "domestic.json"))
    print(f"Sigma_0 (domestic): {sigma_0.stats()}")

    # 四个增量
    for domain in ["retail", "industrial", "restaurant", "office"]:
        delta = build_domain_delta(domain)
        delta.save(str(OUT_DIR / f"{domain}_delta.json"))
        print(f"Delta ({domain}): predicates={delta.predicate_count()}, "
              f"actions={delta.action_count()}, constraints={delta.constraint_count()}, "
              f"rules={delta.rule_count()}")

    # 验证合并
    print("\n── 渐进合并验证 ──")
    current = sigma_0
    for i, domain in enumerate(["retail", "industrial", "restaurant", "office"], 1):
        delta = SemanticSignature.load(str(OUT_DIR / f"{domain}_delta.json"))
        current = current.merge(delta)
        print(f"Stage {i} (+{domain}): {current.stats()}")

    # 验证同义谓词存在
    print(f"\n── 同义谓词对（供 rewrite 合并） ──")
    for base, syn in SYNONYM_PAIRS:
        if base in current.R_b and syn in current.R_b:
            print(f"  ✓ {base} ↔ {syn}")
        else:
            print(f"  ✗ {base} ↔ {syn} (missing)")


if __name__ == "__main__":
    main()
