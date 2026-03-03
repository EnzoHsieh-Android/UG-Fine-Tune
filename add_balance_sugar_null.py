#!/usr/bin/env python3
"""
平衡品項分佈 + 補充 sugar=null 至 ~40%。
排除三窨十五茉/桂花輕烏龍，集中補強低頻品項。
"""
import json, sys, random
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent / "data"
random.seed(42)

with open(DATA_DIR / "train.jsonl") as f:
    SYS_PROMPT = json.loads(f.readline())["messages"][0]["content"]

EXISTING = set()
for fname in ["train.jsonl", "valid.jsonl"]:
    with open(DATA_DIR / fname) as f:
        for line in f:
            EXISTING.add(json.loads(line)["messages"][1]["content"])


def mk_order(item, cat=None, size=None, ice=None, addon=None, qty=1):
    return {"item": item, "category": cat, "size": size, "ice": ice,
            "sugar": None, "addon": addon or [], "qty": qty, "note": ""}


def mk_sample(text, intents, orders, prefs=None, recs=None):
    return {"messages": [
        {"role": "system", "content": SYS_PROMPT},
        {"role": "user", "content": text},
        {"role": "assistant", "content": json.dumps({
            "intents": intents, "orders": orders,
            "preferences": prefs or {}, "recommendations": recs or [],
        }, ensure_ascii=False)},
    ]}


def mk_rec(item, cat, reason):
    return {"item": item, "category": cat, "reason": reason}


# ====== 品項屬性 ======
FRUIT = {"蜜桃紅烏龍", "青檸桂蜜", "葡柚十五茉"}

NICKNAMES = {
    "蜜桃紅烏龍": ["蜜桃的", "蜜桃果茶"],
    "青檸桂蜜": ["青檸的", "青檸果茶"],
    "葡柚十五茉": ["葡柚的", "葡柚果茶"],
    "朱槿普洱紅": ["普洱紅"],
    "米香玉露菁": ["玉露菁"],
    "茶花紅烏龍": ["茶花的"],
    "金杯蜜香紅": ["蜜香紅"],
    "琥珀鐵觀音": ["鐵觀音"],
}

ITEM_CATS = {
    "蜜桃紅烏龍": ["fruit_tea"],
    "青檸桂蜜": ["fruit_tea"],
    "葡柚十五茉": ["fruit_tea"],
    "朱槿普洱紅": ["pure_tea", "fresh_milk_tea", "rich_milk_tea"],
    "米香玉露菁": ["pure_tea", "fresh_milk_tea", "rich_milk_tea"],
    "茶花紅烏龍": ["pure_tea", "fresh_milk_tea", "rich_milk_tea", "cloud_velvet"],
    "金杯蜜香紅": ["fresh_milk_tea", "rich_milk_tea"],
    "琥珀鐵觀音": ["fresh_milk_tea", "rich_milk_tea"],
}

CAT_TEXT = {
    "pure_tea": ["純茶"], "fresh_milk_tea": ["鮮奶", "鮮奶茶"],
    "rich_milk_tea": ["奶茶"], "cloud_velvet": ["奶蓋"],
}

COLD_ICES = ["去冰", "少冰", "微冰", "正常冰"]
ALL_ICES = COLD_ICES + ["熱飲"]

TARGETS = {
    "葡柚十五茉": 74, "青檸桂蜜": 73, "蜜桃紅烏龍": 55,
    "米香玉露菁": 41, "朱槿普洱紅": 41, "茶花紅烏龍": 41,
    "金杯蜜香紅": 41, "琥珀鐵觀音": 41,
}

PREFIXES = [
    "一杯", "來杯", "我要", "給我", "來一杯", "要一杯", "我想喝",
    "點", "想喝", "幫我來杯", "我想要", "請給我", "我來杯", "要",
    "幫我點", "我想點", "我要點", "再來杯", "來份", "要份",
    "我來一杯", "給我一杯", "我點",
]


def gen_candidates(item):
    """Generate (text, order_dict, ice_is_null) candidates."""
    is_fruit = item in FRUIT
    default_cat = "fruit_tea" if is_fruit else None
    ices = COLD_ICES if is_fruit else ALL_ICES
    cands = []
    seen = set()

    def add(text, ice_null, **kw):
        if text not in EXISTING and text not in seen:
            seen.add(text)
            cands.append((text, mk_order(item, **kw), ice_null))

    # 1. Bare prefix + item
    for p in PREFIXES:
        add(f"{p}{item}", True, cat=default_cat)
    add(f"{item}一杯", True, cat=default_cat)
    add(f"{item}來一杯", True, cat=default_cat)

    # 2. Nicknames
    for nick in NICKNAMES.get(item, []):
        for p in ["", "一杯", "我要", "來杯", "給我", "來一杯", "我想喝", "想喝"]:
            add(f"{p}{nick}", True, cat=default_cat)

    # 3. Addon (ice=null)
    for av, at in [("紅烏龍茶凍", "加茶凍"), ("燕麥粒", "加燕麥粒")]:
        add(f"{item}{at}", True, cat=default_cat, addon=[av])
        add(f"一杯{item}{at}", True, cat=default_cat, addon=[av])
        add(f"我要{item}{at}", True, cat=default_cat, addon=[av])
        for nick in NICKNAMES.get(item, [])[:1]:
            add(f"{nick}{at}", True, cat=default_cat, addon=[av])

    # 4. Qty
    add(f"兩杯{item}", True, cat=default_cat, qty=2)
    add(f"{item}兩杯", True, cat=default_cat, qty=2)
    add(f"三杯{item}", True, cat=default_cat, qty=3)
    add(f"我要兩杯{item}", True, cat=default_cat, qty=2)
    add(f"我要三杯{item}", True, cat=default_cat, qty=3)

    # 5. Category (multi-cat only, ice=null)
    if not is_fruit:
        for cat in ITEM_CATS[item]:
            for ct in CAT_TEXT.get(cat, []):
                add(f"{item}{ct}", True, cat=cat)
                add(f"一杯{item}{ct}", True, cat=cat)
                add(f"我要{item}{ct}", True, cat=cat)
                add(f"來杯{item}{ct}", True, cat=cat)
                add(f"給我{item}{ct}", True, cat=cat)

    # 6. Category + size
    if not is_fruit:
        for cat in ["fresh_milk_tea", "rich_milk_tea"]:
            if cat in ITEM_CATS[item]:
                ct = CAT_TEXT[cat][0]
                for sv, st in [("L", "大杯"), ("M", "中杯")]:
                    add(f"{item}{ct}{st}", True, cat=cat, size=sv)
                    add(f"一杯{item}{ct}{st}", True, cat=cat, size=sv)

    # 7. With ice (ice specified)
    for ice in ices:
        add(f"{item}{ice}", False, cat=default_cat, ice=ice)
        add(f"一杯{item}{ice}", False, cat=default_cat, ice=ice)
        add(f"我要{item}{ice}", False, cat=default_cat, ice=ice)
        add(f"來杯{item}{ice}", False, cat=default_cat, ice=ice)
    for nick in NICKNAMES.get(item, [])[:1]:
        for ice in ices[:3]:
            add(f"{nick}{ice}", False, cat=default_cat, ice=ice)
            add(f"一杯{nick}{ice}", False, cat=default_cat, ice=ice)

    # 8. Category + ice
    if not is_fruit:
        for cat in ["fresh_milk_tea", "rich_milk_tea"]:
            if cat in ITEM_CATS[item]:
                ct = CAT_TEXT[cat][0]
                for ice in ices[:3]:
                    add(f"{item}{ct}{ice}", False, cat=cat, ice=ice)
                    add(f"一杯{item}{ct}{ice}", False, cat=cat, ice=ice)

    # 9. Ice + addon combo
    for ice in ices[:2]:
        for av, at in [("紅烏龍茶凍", "加茶凍"), ("燕麥粒", "加燕麥粒")]:
            add(f"{item}{ice}{at}", False, cat=default_cat, ice=ice, addon=[av])
            add(f"{item}{at}{ice}", False, cat=default_cat, ice=ice, addon=[av])

    return cands


def gen_multi(used):
    """Multi-item candidates: (text, [orders])."""
    items = list(TARGETS.keys())
    cands = []

    def dc(it):
        return "fruit_tea" if it in FRUIT else None

    for i, it1 in enumerate(items):
        for it2 in items[i+1:]:
            for c in ["跟", "和", "、"]:
                t = f"{it1}{c}{it2}"
                if t not in EXISTING and t not in used:
                    cands.append((t, [mk_order(it1, cat=dc(it1)), mk_order(it2, cat=dc(it2))]))
                t2 = f"一杯{it1}{c}一杯{it2}"
                if t2 not in EXISTING and t2 not in used:
                    cands.append((t2, [mk_order(it1, cat=dc(it1)), mk_order(it2, cat=dc(it2))]))
    return cands


def gen_multiround(used):
    """Multi-round candidates: (text, intents, [orders])."""
    items = list(TARGETS.keys())
    cands = []

    def dc(it):
        return "fruit_tea" if it in FRUIT else None

    for it1 in items:
        for it2 in items:
            if it1 == it2:
                continue
            for lk in ["再一杯", "加一杯"]:
                t = f"{it1};{lk}{it2}"
                if t not in EXISTING and t not in used:
                    cands.append((t, ["order", "order"],
                                  [mk_order(it1, cat=dc(it1)), mk_order(it2, cat=dc(it2))]))
    return cands


REC_SAMPLES = [
    ("推薦果茶", {"taste": "果香"},
     mk_rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃與紅烏龍交織，甜蜜清香")),
    ("有什麼果香飲料", {"taste": "果香"},
     mk_rec("葡柚十五茉", "fruit_tea", "葡柚酸甜搭茉莉花香，清新消暑")),
    ("想喝酸酸甜甜的", {"taste": "酸甜"},
     mk_rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽")),
    ("推薦清爽消暑的", {"taste": "清爽"},
     mk_rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑")),
    ("有沒有水果茶", {"taste": "果香"},
     mk_rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香搭紅烏龍茶韻，甜而不膩")),
    ("想喝花香的", {"taste": "花香"},
     mk_rec("朱槿普洱紅", "pure_tea", "朱槿花香融合普洱醇厚，層次豐富")),
    ("推薦醇厚的茶", {"taste": "醇厚"},
     mk_rec("米香玉露菁", "pure_tea", "米香與玉露茶韻交融，溫潤醇厚")),
    ("有推薦的奶茶嗎", {"category": "奶茶"},
     mk_rec("金杯蜜香紅", "rich_milk_tea", "蜜香紅茶搭奶精，濃郁甜潤")),
    ("想喝濃一點的", {"taste": "濃郁"},
     mk_rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音焙火韻搭奶精，濃醇回甘")),
    ("推薦不苦的純茶", {"taste": "不苦", "category": "純茶"},
     mk_rec("米香玉露菁", "pure_tea", "玉露菁回甘清甜，完全不苦澀")),
]


def main():
    dry_run = "--dry-run" in sys.argv

    # Generate candidates
    all_cands = {item: gen_candidates(item) for item in TARGETS}

    print("候選樣本 (單品項):")
    for item in sorted(all_cands, key=lambda x: len(all_cands[x])):
        ni = sum(1 for _, _, n in all_cands[item] if n)
        si = sum(1 for _, _, n in all_cands[item] if not n)
        print(f"  {item:10s}: {ni+si:>3d} (null_ice={ni}, spec_ice={si})")

    selected = []
    used = set()
    item_orders = Counter()

    # Phase 1: Single-item (75% null-ice, 25% specified)
    for item in sorted(TARGETS, key=lambda x: -TARGETS[x]):
        target = TARGETS[item]
        nt = int(target * 0.75)
        st = target - nt

        nc = [(t, o) for t, o, n in all_cands[item] if n and t not in used]
        sc = [(t, o) for t, o, n in all_cands[item] if not n and t not in used]
        random.shuffle(nc)
        random.shuffle(sc)

        for t, o in nc[:nt]:
            used.add(t)
            selected.append(mk_sample(t, ["order"], [o]))
            item_orders[item] += 1
        for t, o in sc[:st]:
            used.add(t)
            selected.append(mk_sample(t, ["order"], [o]))
            item_orders[item] += 1

    print(f"\nPhase 1: {len(selected)} samples, {sum(item_orders.values())} orders")

    # Phase 2: Multi-item
    mc = gen_multi(used)
    random.shuffle(mc)
    for t, orders in mc:
        if t in used:
            continue
        its = [o["item"] for o in orders]
        if any(TARGETS.get(it, 0) - item_orders.get(it, 0) > 0 for it in its):
            used.add(t)
            selected.append(mk_sample(t, ["order"], orders))
            for it in its:
                item_orders[it] += 1

    print(f"Phase 2: {len(selected)} samples, {sum(item_orders.values())} orders")

    # Phase 3: Multi-round
    mrc = gen_multiround(used)
    random.shuffle(mrc)
    for t, intents, orders in mrc:
        if t in used:
            continue
        its = [o["item"] for o in orders]
        if any(TARGETS.get(it, 0) - item_orders.get(it, 0) > 0 for it in its):
            used.add(t)
            selected.append(mk_sample(t, intents, orders))
            for it in its:
                item_orders[it] += 1

    print(f"Phase 3: {len(selected)} samples, {sum(item_orders.values())} orders")

    # Phase 4: Fill remaining
    for item in sorted(TARGETS, key=lambda x: -(TARGETS[x] - item_orders.get(x, 0))):
        rem = TARGETS[item] - item_orders.get(item, 0)
        if rem <= 0:
            continue
        cands = [(t, o) for t, o, _ in all_cands[item] if t not in used]
        random.shuffle(cands)
        for t, o in cands[:rem]:
            used.add(t)
            selected.append(mk_sample(t, ["order"], [o]))
            item_orders[item] += 1

    print(f"Phase 4: {len(selected)} samples, {sum(item_orders.values())} orders")

    # Phase 5: Recommend samples
    rec_added = 0
    for user_text, prefs, rec_obj in REC_SAMPLES:
        if user_text not in EXISTING and user_text not in used:
            used.add(user_text)
            selected.append(mk_sample(user_text, ["recommend"], [], prefs, [rec_obj]))
            item_orders[rec_obj["item"]] += 1
            rec_added += 1

    print(f"Phase 5: +{rec_added} recommend samples")

    # Report
    total_orders = sum(item_orders.values())
    print(f"\n品項分佈:")
    for item in sorted(item_orders, key=lambda x: -item_orders[x]):
        t = TARGETS.get(item, 0)
        a = item_orders[item]
        flag = "✓" if a >= t * 0.9 else "⚠️"
        print(f"  {item:10s}: {a:>4d} / {t} {flag}")

    ice_null = sum(1 for s in selected
                   for o in json.loads(s["messages"][2]["content"]).get("orders", [])
                   if o.get("ice") is None)
    print(f"\n總新增: {len(selected)} 樣本, {total_orders} orders")
    print(f"ice null in orders: {ice_null}/{total_orders} ({ice_null/total_orders*100:.0f}%)")

    old_o, old_sn, old_in = 2007, 558, 664
    # sugar null = all new orders (sugar=null by design)
    sugar_null_new = sum(1 for s in selected
                         for o in json.loads(s["messages"][2]["content"]).get("orders", [])
                         if o.get("sugar") is None)
    new_o = old_o + total_orders
    new_sn = old_sn + sugar_null_new
    new_in = old_in + ice_null

    old_items = {"三窨十五茉": 441, "桂花輕烏龍": 405, "琥珀鐵觀音": 354,
                 "金杯蜜香紅": 274, "茶花紅烏龍": 266, "朱槿普洱紅": 173,
                 "米香玉露菁": 161, "蜜桃紅烏龍": 102, "青檸桂蜜": 84, "葡柚十五茉": 83}
    new_items = {k: v + item_orders.get(k, 0) for k, v in old_items.items()}
    mx, mn = max(new_items.values()), min(new_items.values())

    print(f"\n--- 預估影響 ---")
    print(f"  sugar null: {old_sn}/{old_o} ({old_sn/old_o*100:.1f}%) → {new_sn}/{new_o} ({new_sn/new_o*100:.1f}%)")
    print(f"  ice null: {old_in}/{old_o} ({old_in/old_o*100:.1f}%) → {new_in}/{new_o} ({new_in/new_o*100:.1f}%)")
    print(f"  品項比: {mx}/{mn} = {mx/mn:.1f}x (目標 <3x)")

    if dry_run:
        print("\n[DRY RUN]")
        return

    # Split & write
    random.shuffle(selected)
    vi = set(range(4, len(selected), 5))
    train = [s for i, s in enumerate(selected) if i not in vi]
    valid = [s for i, s in enumerate(selected) if i in vi]

    with open(DATA_DIR / "train.jsonl", "a") as f:
        for s in train:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    with open(DATA_DIR / "valid.jsonl", "a") as f:
        for s in valid:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"\nTrain: +{len(train)}, Valid: +{len(valid)}")
    for fname in ["train.jsonl", "valid.jsonl"]:
        with open(DATA_DIR / fname) as f:
            print(f"  {fname}: {sum(1 for _ in f)} 筆")


if __name__ == "__main__":
    main()
