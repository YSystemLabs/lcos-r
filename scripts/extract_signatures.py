#!/usr/bin/env python3
"""
从 AgiBot World Task Catalog 系统化提取五领域语义签名要素。
输出：每个领域的对象类型、谓词/技能、动作模板、约束等，
以及跨领域重叠分析。
"""

import json, os, re, sys
from collections import defaultdict, Counter
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent.parent / "data" / "agibot-world" / "task_info"

# ── 领域分类规则 ──────────────────────────────────────────────
# 关键词优先级：先匹配更具体的，再匹配宽泛的
DOMAIN_RULES = [
    # (domain, task_name patterns, scene_text patterns)
    ("restaurant", [
        r"restaurant", r"milk tea", r"serve .*(meal|food)", r"pour.*tea",
        r"hand.*menu", r"receive.*menu", r"place cutlery", r"make juice",
        r"make milk tea", r"pour the tea", r"pack takeout", r"water pouring.*restaurant",
        r"place.*feed box", r"slice.*noodle", r"knead dough", r"roll.*dough",
    ], [
        r"restaurant", r"milk tea", r"counter.*tray", r"guest.*order",
    ]),
    ("retail", [
        r"supermarket", r"restock", r"checkout", r"scan.*barcode",
        r"scan.*code.*pack", r"scan.*package", r"pack.*fruit",
        r"deliver goods", r"convey merchandise", r"place goods.*shelves",
        r"hanging basket", r"scan.*security", r"strike.*gong",
        r"wave goodbye",
    ], [
        r"supermarket", r"shelf.*shopping cart", r"snack shelf",
        r"freezer.*restock", r"checkout counter", r"cash register",
        r"barcode scanner", r"store.*entrance",
    ]),
    ("industrial", [
        r"warehouse", r"e-commerce", r"industrial logistics",
        r"permanent magnet", r"packing.*detergent", r"install.*memory module",
        r"sort.*warehouse", r"pack.*medicine", r"carry.*bottled water",
        r"lift dumbbell", r"carry books", r"move house",
        r"transport table",
    ], [
        r"warehouse", r"conveyor belt", r"logistics box", r"pico carton",
        r"sudoku grid", r"material frame.*target fra",
    ]),
    ("office", [
        r"pen.*holder", r"meeting room", r"shredder", r"whiteboard",
        r"replenish tissue", r"print document", r"felt bag",
        r"stamp.*document", r"reimbursement", r"confirm.*meeting",
        r"open.*door.*turn off", r"insert.*key.*open.*door",
        r"name tag", r"clap hands",
        r"remove bottled water.*carton",
    ], [
        r"meeting room", r"whiteboard", r"shredder", r"printer",
        r"reimbursement box",
    ]),
    # domestic 是默认 fallback，但也列出关键词以提高准确性
    ("domestic", [
        r"wardrobe", r"fridge", r"fold.*short", r"fold.*t-shirt", r"fold.*towel",
        r"fold.*sleeve", r"iron.*cloth", r"ironing", r"wash.*dish", r"toast",
        r"sweep.*floor", r"mop.*floor", r"brew.*tea", r"brew.*coffee",
        r"make.*coffee", r"bookshelf", r"vacuum", r"curtain", r"laundry",
        r"washing machine", r"microwave", r"oven", r"cook.*vegetable",
        r"prepare.*breakfast", r"make.*salad", r"make.*sandwich",
        r"oatmeal", r"lemon.*water", r"boil.*water", r"kettle",
        r"clean.*toilet", r"wipe.*toilet", r"bathroom", r"mirror cabinet",
        r"showerhead", r"hair dryer", r"sofa", r"bed", r"pillow",
        r"clothesline", r"drying rack", r"hanger", r"hang.*cloth",
        r"store.*toy", r"grab.*toy", r"hammer.*toy", r"arrange.*flower",
        r"water.*flower", r"open.*drawer", r"trash", r"discard",
        r"disinfect", r"stain", r"wipe", r"peel", r"slice",
        r"rice.*cooker", r"ice.*maker", r"fan", r"remote.*control",
        r"bottle.*cap", r"plug", r"charger", r"schoolbag",
        r"paint.*wall", r"lint roller", r"curtain.*sash", r"pen cap",
        r"insert.*straw", r"capsule.*coffee", r"season", r"condiment",
        r"flatten.*short", r"dishcloth", r"countertop", r"pot.*spatula",
        r"open.*red wine", r"pour.*water", r"arrange.*fruit",
        r"sort.*cloth", r"separate.*cloth", r"clear.*waste",
        r"place.*item.*bag", r"pack.*box.*secure",
    ], [
        r"bedroom", r"kitchen", r"bathroom", r"wardrobe", r"fridge",
        r"refrigerator", r"washing machine", r"microwave", r"oven",
        r"sink", r"sofa", r"bed\b", r"toilet", r"curtain",
        r"flower pot", r"laundry basket",
    ]),
]


def classify_task(task_name, scene_text):
    """基于关键词匹配将任务分类到五个领域之一。"""
    tn = task_name.lower()
    st = scene_text.lower()
    for domain, name_patterns, scene_patterns in DOMAIN_RULES:
        for pat in name_patterns:
            if re.search(pat, tn):
                return domain
        for pat in scene_patterns:
            if re.search(pat, st):
                return domain
    return "domestic"  # fallback


def extract_objects_from_text(text):
    """从场景描述和动作文本中提取物体名词短语。"""
    # 去掉位置描述，保留物体
    objects = set()
    # 匹配 "a/an/the <noun phrase>" 或直接名词短语
    # 简单但有效的启发式：提取场景中提到的关键名词
    patterns = [
        r'\b(?:a|an|the|some|two|three|four|five|six)\s+([\w\s\-]+?)(?:\s+(?:is|are|on|in|with|placed|next|to|from|and|,|\.))',
        r'(?:holding|contains?|including|with)\s+(?:a|an|the|some)?\s*([\w\s\-]+?)(?:\s+(?:is|are|on|in|,|\.))',
    ]
    for pat in patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            obj = m.group(1).strip()
            if len(obj) > 2 and len(obj) < 50:
                objects.add(obj.lower())
    return objects


def load_all_tasks():
    """加载所有任务并分类。"""
    tasks = []
    for f in sorted(TASK_DIR.iterdir()):
        if not f.suffix == '.json':
            continue
        tid = f.stem.replace('task_', '')
        with open(f) as fp:
            data = json.load(fp)

        ep0 = data[0]
        task_name = ep0['task_name']
        scene_text = ep0.get('init_scene_text', '')

        # 收集所有 episode 的技能和动作文本
        skills = set()
        action_texts = []
        for ep in data:
            for ac in ep.get('label_info', {}).get('action_config', []):
                s = ac.get('skill', '').strip()
                if s:
                    skills.add(s)
                at = ac.get('action_text', '').strip()
                if at:
                    action_texts.append(at)

        domain = classify_task(task_name, scene_text)
        tasks.append({
            'tid': tid,
            'task_name': task_name,
            'scene_text': scene_text,
            'domain': domain,
            'skills': sorted(skills),
            'action_texts': action_texts,
            'episode_count': len(data),
        })
    return tasks


def analyze_domain(tasks, domain_name):
    """分析单个领域的语义签名要素。"""
    domain_tasks = [t for t in tasks if t['domain'] == domain_name]

    # 1. 技能集合 → 对应 A_t (动作模板)
    skill_counter = Counter()
    for t in domain_tasks:
        for s in t['skills']:
            skill_counter[s] += 1

    # 2. 动作文本摘要 → 提取谓词模式
    action_text_counter = Counter()
    all_action_texts = []
    for t in domain_tasks:
        for at in t['action_texts']:
            all_action_texts.append(at)
            # 提取动词短语（动作文本通常以动词开头）
            verb_match = re.match(r'^(\w+(?:\s+\w+)?)', at)
            if verb_match:
                action_text_counter[verb_match.group(1).lower()] += 1

    # 3. 场景物体 → 对应 S_t (对象类型)
    all_objects = Counter()
    for t in domain_tasks:
        objs = extract_objects_from_text(t['scene_text'])
        for o in objs:
            all_objects[o] += 1
        # 也从动作文本中提取
        for at in t['action_texts'][:50]:  # 采样前50条
            objs = extract_objects_from_text(at)
            for o in objs:
                all_objects[o] += 1

    # 4. 任务名称列表
    task_names = [(t['tid'], t['task_name'], t['episode_count']) for t in domain_tasks]

    return {
        'task_count': len(domain_tasks),
        'total_episodes': sum(t['episode_count'] for t in domain_tasks),
        'tasks': task_names,
        'skills': skill_counter.most_common(),
        'top_action_verbs': action_text_counter.most_common(30),
        'top_objects': all_objects.most_common(40),
    }


def cross_domain_overlap(tasks):
    """分析跨领域技能重叠 → 对应可重用谓词。"""
    domain_skills = defaultdict(set)
    for t in tasks:
        for s in t['skills']:
            domain_skills[t['domain']].add(s)

    all_domains = sorted(domain_skills.keys())
    # 全局共享技能 (出现在 ≥3 个领域)
    skill_domain_count = Counter()
    for d, skills in domain_skills.items():
        for s in skills:
            skill_domain_count[s] += 1

    shared = {s: c for s, c in skill_domain_count.items() if c >= 3}
    # 每对领域之间的特有重叠
    pairwise = {}
    for i, d1 in enumerate(all_domains):
        for d2 in all_domains[i+1:]:
            overlap = domain_skills[d1] & domain_skills[d2]
            unique_overlap = overlap - set(shared.keys())
            pairwise[f"{d1} ∩ {d2}"] = sorted(unique_overlap)

    return {
        'domain_skills': {d: sorted(s) for d, s in domain_skills.items()},
        'shared_skills_3plus': {s: c for s, c in sorted(shared.items(), key=lambda x: -x[1])},
        'pairwise_unique_overlap': pairwise,
    }


DOMAIN_ZH = {
    'domestic': '家居 (Domestic)',
    'retail': '零售 (Retail)',
    'industrial': '工业 (Industrial)',
    'restaurant': '餐饮 (Restaurant)',
    'office': '办公 (Office)',
}

DOMAIN_ORDER = ['domestic', 'retail', 'industrial', 'restaurant', 'office']


def print_report(tasks):
    """打印完整的语义签名提取报告。"""
    print("=" * 80)
    print("AgiBot World Task Catalog — 五领域语义签名要素提取报告")
    print("=" * 80)

    # 总览
    print(f"\n总任务数: {len(tasks)}")
    print(f"总 episode 数: {sum(t['episode_count'] for t in tasks)}")
    domain_counts = Counter(t['domain'] for t in tasks)
    print("\n领域分布:")
    for d in DOMAIN_ORDER:
        eps = sum(t['episode_count'] for t in tasks if t['domain'] == d)
        print(f"  {DOMAIN_ZH[d]:20s}  任务数={domain_counts[d]:3d}  episodes={eps:>6d}")

    # 各领域详情
    for d in DOMAIN_ORDER:
        info = analyze_domain(tasks, d)
        print(f"\n{'─' * 80}")
        print(f"领域: {DOMAIN_ZH[d]}")
        print(f"任务数: {info['task_count']}  |  总 episodes: {info['total_episodes']}")

        print(f"\n  ▸ 任务列表 (tid | task_name | episodes):")
        for tid, tn, ec in info['tasks']:
            print(f"    {tid:>4s} | {tn:<65s} | {ec:>5d}")

        print(f"\n  ▸ 技能集 A_t ({len(info['skills'])} 种):")
        for s, c in info['skills']:
            print(f"    {s:<25s} (出现在 {c} 个任务中)")

        print(f"\n  ▸ 高频动作谓词 (top 20):")
        for v, c in info['top_action_verbs'][:20]:
            print(f"    {v:<30s} × {c}")

        print(f"\n  ▸ 场景物体 S_t (top 25):")
        for o, c in info['top_objects'][:25]:
            print(f"    {o:<40s} × {c}")

    # 跨领域重叠
    print(f"\n{'═' * 80}")
    print("跨领域分析")
    print("=" * 80)
    overlap = cross_domain_overlap(tasks)

    print(f"\n  ▸ 各领域技能总数:")
    for d in DOMAIN_ORDER:
        skills = overlap['domain_skills'].get(d, [])
        print(f"    {DOMAIN_ZH[d]:20s}  {len(skills)} 种: {', '.join(skills)}")

    print(f"\n  ▸ 共享技能 (≥3 个领域):")
    for s, c in overlap['shared_skills_3plus'].items():
        print(f"    {s:<20s} → {c} 个领域")

    print(f"\n  ▸ 领域对特有重叠:")
    for pair, skills in overlap['pairwise_unique_overlap'].items():
        if skills:
            print(f"    {pair}: {', '.join(skills)}")

    # 语义签名映射总结
    print(f"\n{'═' * 80}")
    print("语义签名要素映射总结 (对应 §9.1 表)")
    print("=" * 80)
    print("""
┌────────────────┬──────────────────────────────────────────────────────────┐
│ Σ_t 组件       │ Task Catalog 来源                                       │
├────────────────┼──────────────────────────────────────────────────────────┤
│ S_t (对象类型)  │ init_scene_text + action_text 中的名词短语               │
│ R_t^b (基态)    │ init_scene_text 中的空间关系与状态描述                   │
│ R_t^g (目标态)  │ task_name 隐含目标 + action_text 终态                   │
│ A_t (动作模板)  │ skill 字段 (标准技能标签)                                │
│ C_t (约束)      │ init_scene_text 中的限制条件/注意事项                   │
└────────────────┴──────────────────────────────────────────────────────────┘
""")


def save_json_report(tasks, out_path):
    """保存 JSON 格式的提取结果。"""
    result = {
        'summary': {
            'total_tasks': len(tasks),
            'total_episodes': sum(t['episode_count'] for t in tasks),
            'domain_distribution': {},
        },
        'domains': {},
        'cross_domain': cross_domain_overlap(tasks),
    }
    for d in DOMAIN_ORDER:
        info = analyze_domain(tasks, d)
        result['summary']['domain_distribution'][d] = {
            'task_count': info['task_count'],
            'total_episodes': info['total_episodes'],
        }
        result['domains'][d] = {
            'name_zh': DOMAIN_ZH[d],
            'tasks': [{'tid': t[0], 'task_name': t[1], 'episodes': t[2]} for t in info['tasks']],
            'skills': dict(info['skills']),
            'top_action_verbs': dict(info['top_action_verbs'][:30]),
            'top_objects': dict(info['top_objects'][:40]),
        }

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nJSON 报告已保存: {out_path}")


if __name__ == '__main__':
    tasks = load_all_tasks()
    print_report(tasks)
    json_out = Path(__file__).resolve().parent.parent / "data" / "agibot-world" / "signature_extraction.json"
    save_json_report(tasks, json_out)
