#!/usr/bin/env python3
"""Comprehensive uniformity audit for training data."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────
MULTI_CAT_ITEMS = ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"]
FRUIT_TEA_ITEMS = ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"]
CLOUD_VELVET_ITEMS = ["桂花輕烏龍", "茶花紅烏龍"]
ALL_ITEMS = MULTI_CAT_ITEMS + FRUIT_TEA_ITEMS  # fruit_tea only items (non-multi-cat)
# Actually all unique items:
ALL_MENU_ITEMS = list(set(MULTI_CAT_ITEMS + FRUIT_TEA_ITEMS))

VALID_CATEGORIES = {
    "三窨十五茉": ["pure_tea", "fresh_milk_tea", "rich_milk_tea"],
    "桂花輕烏龍": ["pure_tea", "fresh_milk_tea", "rich_milk_tea", "cloud_velvet"],
    "茶花紅烏龍": ["pure_tea", "fresh_milk_tea", "rich_milk_tea", "cloud_velvet"],
    "琥珀鐵觀音": ["fresh_milk_tea", "rich_milk_tea"],  # no pure_tea for 琥珀鐵觀音
    "金杯蜜香紅": ["pure_tea", "fresh_milk_tea", "rich_milk_tea"],
    "朱槿普洱紅": ["pure_tea", "fresh_milk_tea", "rich_milk_tea"],
    "米香玉露菁": ["pure_tea", "fresh_milk_tea", "rich_milk_tea"],
    "青檸桂蜜": ["fruit_tea"],
    "蜜桃紅烏龍": ["fruit_tea"],
    "葡柚十五茉": ["fruit_tea"],
}

# Wait - 琥珀鐵觀音 IS in pure_tea menu? Let me re-check the system prompt...
# The pure_tea section lists: 三窨十五茉, 桂花輕烏龍, 茶花紅烏龍, 朱槿普洱紅, 米香玉露菁
# 琥珀鐵觀音 is NOT in pure_tea. Correct.

VALID_ICE = [None, "正常冰", "少冰", "微冰", "去冰", "熱飲", "熱", "熱的"]
VALID_SUGAR = [None, "全糖", "五分糖", "三分糖", "一分糖", "無糖", "正常糖", "半糖", "少糖", "微糖"]
VALID_SIZE = [None, "M", "L"]
VALID_ADDONS = ["紅烏龍茶凍", "燕麥粒"]
VALID_INTENTS = ["order", "modify", "recommend", "other"]

DATA_DIR = Path("/Users/xiechengru/ug-finetune/data")
issues = []  # (priority, issue, file, current, target, action)

def load_jsonl(path):
    samples = []
    with open(path, "r") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                msgs = obj["messages"]
                user_msg = next(m["content"] for m in msgs if m["role"] == "user")
                asst_msg = next(m["content"] for m in msgs if m["role"] == "assistant")
                asst_json = json.loads(asst_msg)
                samples.append({
                    "line": i,
                    "user": user_msg,
                    "assistant": asst_json,
                    "raw_assistant": asst_msg,
                })
            except Exception as e:
                print(f"  [WARN] Line {i} parse error: {e}")
    return samples

def sep():
    print("=" * 100)

def subsep():
    print("-" * 80)

# ── Load data ──────────────────────────────────────────────────────────
print("Loading data...")
train = load_jsonl(DATA_DIR / "train.jsonl")
valid = load_jsonl(DATA_DIR / "valid.jsonl")
print(f"  train: {len(train)} samples")
print(f"  valid: {len(valid)} samples")
print()

# ════════════════════════════════════════════════════════════════════════
# 1. RECOMMENDATION UNIFORMITY
# ════════════════════════════════════════════════════════════════════════
sep()
print("## 1. RECOMMENDATION UNIFORMITY (CRITICAL)")
sep()

for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    print(f"\n### {fname}")
    rec_items = Counter()
    rec_categories = Counter()
    total_recs = 0
    for s in data:
        recs = s["assistant"].get("recommendations", [])
        for r in recs:
            rec_items[r.get("item", "UNKNOWN")] += 1
            rec_categories[r.get("category", "UNKNOWN")] += 1
            total_recs += 1

    print(f"  Total recommendations: {total_recs}")
    if total_recs == 0:
        print("  [WARN] No recommendations found!")
        if fname == "valid.jsonl":
            issues.append(("P1", "valid.jsonl has 0 recommendations", fname, "0", ">0", "Add recommendation samples to valid"))
        continue

    print(f"\n  Per-item recommendation count:")
    mean_count = total_recs / len(rec_items) if rec_items else 0
    sorted_recs = sorted(rec_items.items(), key=lambda x: -x[1])
    max_rec = sorted_recs[0][1] if sorted_recs else 0
    min_rec = sorted_recs[-1][1] if sorted_recs else 0

    for item, cnt in sorted_recs:
        pct_dev = abs(cnt - mean_count) / mean_count * 100 if mean_count > 0 else 0
        flag = " *** >50% deviation!" if pct_dev > 50 else ""
        print(f"    {item}: {cnt} ({pct_dev:.0f}% from mean){flag}")
        if pct_dev > 50:
            issues.append(("P1", f"Recommendation imbalance: {item} has {cnt} recs ({pct_dev:.0f}% from mean)", fname, str(cnt), f"~{mean_count:.0f}", "Rebalance"))

    ratio = max_rec / min_rec if min_rec > 0 else float("inf")
    print(f"\n  Max:Min ratio = {max_rec}:{min_rec} = {ratio:.1f}:1")
    if ratio > 3:
        issues.append(("P1", f"Recommendation max:min ratio too high", fname, f"{ratio:.1f}:1", "<=3:1", "Rebalance recommendations"))

    # Check which items have 0 recommendations
    all_possible = set(ALL_MENU_ITEMS)
    items_with_recs = set(rec_items.keys())
    missing = all_possible - items_with_recs
    if missing and fname == "valid.jsonl":
        for m in missing:
            print(f"  [FLAG] {m}: 0 recommendations in {fname}")

    print(f"\n  Per-category recommendation count:")
    for cat, cnt in sorted(rec_categories.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {cnt}")

# ════════════════════════════════════════════════════════════════════════
# 2. CATEGORY NULL% UNIFORMITY (CRITICAL)
# ════════════════════════════════════════════════════════════════════════
sep()
print("\n## 2. CATEGORY NULL% UNIFORMITY (CRITICAL)")
sep()

for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    print(f"\n### {fname}")
    # item -> {null: count, total: count, cats: Counter}
    item_cat = defaultdict(lambda: {"null": 0, "total": 0, "cats": Counter()})

    for s in data:
        for order in s["assistant"].get("orders", []):
            item = order.get("item")
            if item not in MULTI_CAT_ITEMS:
                continue
            cat = order.get("category")
            item_cat[item]["total"] += 1
            if cat is None:
                item_cat[item]["null"] += 1
            else:
                item_cat[item]["cats"][cat] += 1

    print(f"  {'Item':<14} {'Null':>5} {'Total':>6} {'Null%':>6}  {'fresh:rich':>12}  Status")
    subsep()
    for item in MULTI_CAT_ITEMS:
        d = item_cat[item]
        total = d["total"]
        null_count = d["null"]
        null_pct = null_count / total * 100 if total > 0 else 0
        fresh = d["cats"].get("fresh_milk_tea", 0)
        rich = d["cats"].get("rich_milk_tea", 0)
        fr_ratio = f"{fresh}:{rich}" if rich > 0 else f"{fresh}:0"
        fr_val = fresh / rich if rich > 0 else float("inf")

        flags = []
        if total > 0 and (null_pct < 15 or null_pct > 35):
            flags.append(f"null% outside 15-35%")
            issues.append(("P1", f"{item} category null%={null_pct:.0f}% outside 15-35%", fname, f"{null_pct:.0f}%", "15-35%", f"Adjust null samples"))
        if rich > 0 and fr_val > 2.0:
            flags.append(f"fresh:rich={fr_val:.1f}:1 > 2:1")
            if fname == "train.jsonl":
                issues.append(("P1", f"{item} fresh:rich={fr_val:.1f}:1 exceeds 2:1", fname, f"{fr_val:.1f}:1", "1:1~2:1", f"Add rich_milk_tea samples"))
        if rich > 0 and fr_val < 1.0:
            flags.append(f"fresh:rich={fr_val:.1f}:1 < 1:1")

        flag_str = " | ".join(flags) if flags else "OK"
        print(f"  {item:<14} {null_count:>5} {total:>6} {null_pct:>5.1f}%  {fr_ratio:>12}  {flag_str}")

# ════════════════════════════════════════════════════════════════════════
# 3. PER-ITEM CATEGORY BREAKDOWN (CRITICAL) - train only
# ════════════════════════════════════════════════════════════════════════
sep()
print("\n## 3. PER-ITEM CATEGORY BREAKDOWN (CRITICAL) — train.jsonl only")
sep()

# Include orders AND recommendations
item_full_cat = defaultdict(Counter)
for s in train:
    for order in s["assistant"].get("orders", []):
        item = order.get("item")
        if item in MULTI_CAT_ITEMS:
            cat = order.get("category") or "null"
            item_full_cat[item][cat] += 1
    for rec in s["assistant"].get("recommendations", []):
        item = rec.get("item")
        if item in MULTI_CAT_ITEMS:
            cat = rec.get("category") or "null"
            item_full_cat[item][cat] += 1

ALL_CATS = ["pure_tea", "fresh_milk_tea", "rich_milk_tea", "cloud_velvet", "fruit_tea", "null"]

for item in MULTI_CAT_ITEMS:
    counts = item_full_cat[item]
    total = sum(counts.values())
    if total == 0:
        print(f"\n  {item}: NO DATA")
        continue

    print(f"\n  {item} (total={total}):")
    for cat in ALL_CATS:
        cnt = counts.get(cat, 0)
        if cnt == 0:
            continue
        pct = cnt / total * 100
        flag = " *** >50%!" if pct > 50 else ""
        print(f"    {cat:<20} {cnt:>4}  ({pct:>5.1f}%){flag}")
        if pct > 50 and cat != "null":
            issues.append(("P0", f"{item} category '{cat}' at {pct:.0f}% > 50% — model will over-predict", "train.jsonl", f"{pct:.0f}%", "<50%", f"Reduce {cat} or add other categories"))

    fresh = counts.get("fresh_milk_tea", 0)
    rich = counts.get("rich_milk_tea", 0)
    if rich > 0:
        ratio = fresh / rich
        flag = " *** >2.5:1!" if ratio > 2.5 else ""
        print(f"    → fresh:rich = {fresh}:{rich} = {ratio:.2f}:1{flag}")
        if ratio > 2.5:
            issues.append(("P1", f"{item} fresh:rich ratio {ratio:.1f}:1 > 2.5:1", "train.jsonl", f"{ratio:.1f}:1", "<=2.5:1", f"Add {int(fresh/2.5 - rich + 1)} rich_milk_tea samples"))
    elif fresh > 0:
        print(f"    → fresh:rich = {fresh}:0 (no rich!)")
        issues.append(("P0", f"{item} has 0 rich_milk_tea samples", "train.jsonl", "0", ">0", "Add rich_milk_tea samples"))

# ════════════════════════════════════════════════════════════════════════
# 4. INTENT COMBINATION UNIFORMITY — train only
# ════════════════════════════════════════════════════════════════════════
sep()
print("\n## 4. INTENT COMBINATION UNIFORMITY — train.jsonl")
sep()

intent_combos = Counter()
for s in train:
    intents = s["assistant"].get("intents", [])
    # Deduplicate but preserve order
    seen = set()
    unique_intents = []
    for i in intents:
        if i not in seen:
            seen.add(i)
            unique_intents.append(i)
    combo = "+".join(sorted(unique_intents))
    if not combo:
        combo = "(empty)"
    intent_combos[combo] += 1

print(f"\n  {'Intent combo':<40} {'Count':>6}")
subsep()
for combo, cnt in sorted(intent_combos.items(), key=lambda x: -x[1]):
    print(f"  {combo:<40} {cnt:>6}")

# Check thresholds
rec_mod = 0
rec_ord = 0
oth_ord = 0
any_rec_combos = {}
for combo, cnt in intent_combos.items():
    parts = set(combo.split("+"))
    if "recommend" in parts and "modify" in parts:
        rec_mod += cnt
    if "recommend" in parts and "order" in parts:
        rec_ord += cnt
    if "other" in parts and "order" in parts:
        oth_ord += cnt
    if "recommend" in parts:
        any_rec_combos[combo] = cnt

print(f"\n  Threshold checks:")
print(f"    recommend+modify: {rec_mod} (need >=15)", end="")
if rec_mod < 15:
    print(" *** BELOW THRESHOLD!")
    issues.append(("P1", f"recommend+modify combo only {rec_mod} samples", "train.jsonl", str(rec_mod), ">=15", f"Add {15-rec_mod} samples"))
else:
    print(" OK")

print(f"    recommend+order: {rec_ord} (need >=30)", end="")
if rec_ord < 30:
    print(" *** BELOW THRESHOLD!")
    issues.append(("P1", f"recommend+order combo only {rec_ord} samples", "train.jsonl", str(rec_ord), ">=30", f"Add {30-rec_ord} samples"))
else:
    print(" OK")

print(f"    other+order: {oth_ord} (need >=20)", end="")
if oth_ord < 20:
    print(" *** BELOW THRESHOLD!")
    issues.append(("P1", f"other+order combo only {oth_ord} samples", "train.jsonl", str(oth_ord), ">=20", f"Add {20-oth_ord} samples"))
else:
    print(" OK")

for combo, cnt in any_rec_combos.items():
    if cnt < 5:
        print(f"    [FLAG] '{combo}' has only {cnt} samples (recommend combo < 5)")
        issues.append(("P2", f"Recommend combo '{combo}' has {cnt} samples", "train.jsonl", str(cnt), ">=5", f"Add {5-cnt} samples"))

# ════════════════════════════════════════════════════════════════════════
# 5. SEGMENT COUNT DISTRIBUTION
# ════════════════════════════════════════════════════════════════════════
sep()
print("\n## 5. SEGMENT COUNT DISTRIBUTION")
sep()

for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    print(f"\n### {fname}")
    seg_counts = Counter()
    for s in data:
        user = s["user"]
        # Split by ; or ；
        segs = re.split(r'[;；]', user)
        segs = [seg.strip() for seg in segs if seg.strip()]
        seg_counts[len(segs)] += 1

    total = sum(seg_counts.values())
    print(f"  {'Segments':>10} {'Count':>6} {'%':>6}")
    for k in sorted(seg_counts.keys()):
        pct = seg_counts[k] / total * 100
        print(f"  {k:>10} {seg_counts[k]:>6} {pct:>5.1f}%")

    single_pct = seg_counts.get(1, 0) / total * 100 if total > 0 else 0
    multi_pct = 100 - single_pct
    print(f"\n  Single-segment: {single_pct:.1f}%, Multi-segment: {multi_pct:.1f}%")
    if single_pct > 75:
        print(f"  *** Single-segment > 75%! Model may struggle with multi-turn.")
        issues.append(("P1", f"Single-segment ratio too high ({single_pct:.0f}%)", fname, f"{single_pct:.0f}%", "<=75%", f"Add multi-segment samples"))

# ════════════════════════════════════════════════════════════════════════
# 6. ITEM ORDER COUNT UNIFORMITY
# ════════════════════════════════════════════════════════════════════════
sep()
print("\n## 6. ITEM ORDER COUNT UNIFORMITY")
sep()

for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    print(f"\n### {fname}")
    order_counts = Counter()
    for s in data:
        for order in s["assistant"].get("orders", []):
            item = order.get("item")
            if item:
                order_counts[item] += 1

    print(f"  {'Item':<16} {'Orders':>7}")
    subsep()
    sorted_items = sorted(order_counts.items(), key=lambda x: -x[1])
    for item, cnt in sorted_items:
        print(f"  {item:<16} {cnt:>7}")

    # Multi-cat items ratio
    multi_cat_counts = {item: order_counts.get(item, 0) for item in MULTI_CAT_ITEMS}
    mc_vals = [v for v in multi_cat_counts.values() if v > 0]
    if mc_vals:
        mc_max = max(mc_vals)
        mc_min = min(mc_vals)
        mc_ratio = mc_max / mc_min if mc_min > 0 else float("inf")
        print(f"\n  Multi-cat items max:min = {mc_max}:{mc_min} = {mc_ratio:.1f}:1")
        if mc_ratio > 5:
            issues.append(("P1", f"Multi-cat item order count max:min > 5:1", fname, f"{mc_ratio:.1f}:1", "<=5:1", "Rebalance"))

    # Fruit tea check
    for item in FRUIT_TEA_ITEMS:
        cnt = order_counts.get(item, 0)
        if cnt < 15 and fname == "train.jsonl":
            print(f"  [FLAG] {item} only {cnt} orders in train (< 15)")
            issues.append(("P1", f"Fruit tea '{item}' only {cnt} orders", fname, str(cnt), ">=15", f"Add {15-cnt} samples"))

# ════════════════════════════════════════════════════════════════════════
# 7. CUSTOMIZATION UNIFORMITY (train only)
# ════════════════════════════════════════════════════════════════════════
sep()
print("\n## 7. CUSTOMIZATION UNIFORMITY — train.jsonl")
sep()

ice_counts = Counter()
sugar_counts = Counter()
size_counts = Counter()
addon_counts = Counter()
qty_counts = Counter()

for s in train:
    for order in s["assistant"].get("orders", []):
        ice = order.get("ice")
        sugar = order.get("sugar")
        size = order.get("size")
        addons = order.get("addon", [])
        qty = order.get("qty", 1)

        ice_counts[ice if ice is not None else "null"] += 1
        sugar_counts[sugar if sugar is not None else "null"] += 1
        size_counts[size if size is not None else "null"] += 1
        qty_counts[qty] += 1
        if addons:
            for a in addons:
                addon_counts[a] += 1
        else:
            addon_counts["(none)"] += 1

total_orders = sum(ice_counts.values())

print(f"\n  Total orders in train: {total_orders}")

print(f"\n  ### Ice distribution:")
for val, cnt in sorted(ice_counts.items(), key=lambda x: -x[1]):
    pct = cnt / total_orders * 100
    flag = " *** < 2%!" if pct < 2 and val != "null" else ""
    print(f"    {str(val):<12} {cnt:>5} ({pct:>5.1f}%){flag}")
    if pct < 2 and val != "null":
        issues.append(("P2", f"Ice '{val}' only {pct:.1f}% of orders", "train.jsonl", f"{pct:.1f}%", ">=2%", f"Add samples with ice='{val}'"))

print(f"\n  ### Sugar distribution:")
for val, cnt in sorted(sugar_counts.items(), key=lambda x: -x[1]):
    pct = cnt / total_orders * 100
    flag = " *** < 1%!" if pct < 1 and val != "null" else ""
    print(f"    {str(val):<12} {cnt:>5} ({pct:>5.1f}%){flag}")
    if pct < 1 and val != "null":
        issues.append(("P2", f"Sugar '{val}' only {pct:.1f}% of orders", "train.jsonl", f"{pct:.1f}%", ">=1%", f"Add samples with sugar='{val}'"))

print(f"\n  ### Size distribution:")
for val, cnt in sorted(size_counts.items(), key=lambda x: -x[1]):
    pct = cnt / total_orders * 100
    print(f"    {str(val):<12} {cnt:>5} ({pct:>5.1f}%)")

l_cnt = size_counts.get("L", 0)
m_cnt = size_counts.get("M", 0)
null_sz = size_counts.get("null", 0)
if m_cnt > 0:
    lm_ratio = l_cnt / m_cnt
    print(f"    L:M ratio = {l_cnt}:{m_cnt} = {lm_ratio:.2f}:1")
else:
    print(f"    L:M ratio = {l_cnt}:0")

print(f"\n  ### Addon distribution:")
for val, cnt in sorted(addon_counts.items(), key=lambda x: -x[1]):
    print(f"    {val:<16} {cnt:>5}")

cha_dong = addon_counts.get("紅烏龍茶凍", 0)
yan_mai = addon_counts.get("燕麥粒", 0)
if yan_mai > 0:
    addon_ratio = cha_dong / yan_mai
    print(f"    茶凍:燕麥粒 ratio = {cha_dong}:{yan_mai} = {addon_ratio:.2f}:1")
else:
    print(f"    茶凍:燕麥粒 ratio = {cha_dong}:0")

print(f"\n  ### Qty distribution:")
for val, cnt in sorted(qty_counts.items(), key=lambda x: -x[1]):
    pct = cnt / total_orders * 100
    print(f"    qty={val:<6} {cnt:>5} ({pct:>5.1f}%)")

# ════════════════════════════════════════════════════════════════════════
# 8. CROSS-VALIDATION
# ════════════════════════════════════════════════════════════════════════
sep()
print("\n## 8. CROSS-VALIDATION")
sep()

# 8a. Duplicate user texts
print("\n  ### 8a. Duplicate user texts")
train_texts = [s["user"] for s in train]
valid_texts = [s["user"] for s in valid]

train_dups = {t: cnt for t, cnt in Counter(train_texts).items() if cnt > 1}
valid_dups = {t: cnt for t, cnt in Counter(valid_texts).items() if cnt > 1}
cross_dups = set(train_texts) & set(valid_texts)

print(f"    Duplicate texts within train: {len(train_dups)}")
if train_dups:
    for t, cnt in sorted(train_dups.items(), key=lambda x: -x[1])[:10]:
        print(f"      [{cnt}x] \"{t[:60]}...\"" if len(t) > 60 else f"      [{cnt}x] \"{t}\"")
    if len(train_dups) > 10:
        print(f"      ... and {len(train_dups) - 10} more")
    issues.append(("P1", f"{len(train_dups)} duplicate user texts in train", "train.jsonl", str(len(train_dups)), "0", "Remove duplicates"))

print(f"    Duplicate texts within valid: {len(valid_dups)}")
if valid_dups:
    for t, cnt in sorted(valid_dups.items(), key=lambda x: -x[1])[:10]:
        print(f"      [{cnt}x] \"{t[:60]}...\"" if len(t) > 60 else f"      [{cnt}x] \"{t}\"")
    if len(valid_dups) > 10:
        print(f"      ... and {len(valid_dups) - 10} more")
    issues.append(("P1", f"{len(valid_dups)} duplicate user texts in valid", "valid.jsonl", str(len(valid_dups)), "0", "Remove duplicates"))

print(f"    Cross-file duplicate texts: {len(cross_dups)}")
if cross_dups:
    for t in sorted(cross_dups)[:10]:
        print(f"      \"{t[:60]}...\"" if len(t) > 60 else f"      \"{t}\"")
    if len(cross_dups) > 10:
        print(f"      ... and {len(cross_dups) - 10} more")
    issues.append(("P0", f"{len(cross_dups)} cross-file duplicate texts (data leakage!)", "both", str(len(cross_dups)), "0", "Remove from valid or train"))

# 8b. recommend intent with empty recommendations
print("\n  ### 8b. recommend intent with empty recommendations")
for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    bad = []
    for s in data:
        intents = s["assistant"].get("intents", [])
        recs = s["assistant"].get("recommendations", [])
        if "recommend" in intents and len(recs) == 0:
            bad.append(s)
    print(f"    {fname}: {len(bad)} samples with intent=recommend but empty recommendations")
    if bad:
        for b in bad[:5]:
            print(f"      Line {b['line']}: \"{b['user'][:60]}\"")
        issues.append(("P0", f"{len(bad)} samples have intent=recommend but empty recommendations", fname, str(len(bad)), "0", "Fix: add recommendations or remove recommend intent"))

# 8c. orders not a list
print("\n  ### 8c. orders field not a list")
for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    bad = []
    for s in data:
        orders = s["assistant"].get("orders")
        if not isinstance(orders, list):
            bad.append(s)
    print(f"    {fname}: {len(bad)} samples where orders is not a list")
    if bad:
        issues.append(("P0", f"orders is not a list in {len(bad)} samples", fname, str(len(bad)), "0", "Fix data format"))

# 8d. Invalid category for item
print("\n  ### 8d. Invalid category for item")
for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    bad = []
    for s in data:
        for order in s["assistant"].get("orders", []):
            item = order.get("item")
            cat = order.get("category")
            if item and cat and item in VALID_CATEGORIES:
                if cat not in VALID_CATEGORIES[item] and cat is not None:
                    bad.append((s["line"], item, cat))
        for rec in s["assistant"].get("recommendations", []):
            item = rec.get("item")
            cat = rec.get("category")
            if item and cat and item in VALID_CATEGORIES:
                if cat not in VALID_CATEGORIES[item] and cat is not None:
                    bad.append((s["line"], item, cat))
    print(f"    {fname}: {len(bad)} invalid item-category pairs")
    if bad:
        for line, item, cat in bad[:10]:
            print(f"      Line {line}: {item} -> {cat}")
        issues.append(("P0", f"{len(bad)} invalid category assignments", fname, str(len(bad)), "0", "Fix category assignments"))

# 8e. Invalid ice/sugar/size values
print("\n  ### 8e. Invalid ice/sugar/size values")
for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    bad_ice = []
    bad_sugar = []
    bad_size = []
    bad_addon = []
    for s in data:
        for order in s["assistant"].get("orders", []):
            ice = order.get("ice")
            sugar = order.get("sugar")
            size = order.get("size")
            addons = order.get("addon", [])

            if ice is not None and ice not in VALID_ICE:
                bad_ice.append((s["line"], ice))
            if sugar is not None and sugar not in VALID_SUGAR:
                bad_sugar.append((s["line"], sugar))
            if size is not None and size not in VALID_SIZE:
                bad_size.append((s["line"], size))
            for a in addons:
                if a not in VALID_ADDONS:
                    bad_addon.append((s["line"], a))

    if bad_ice:
        print(f"    {fname}: {len(bad_ice)} invalid ice values")
        for line, val in bad_ice[:5]:
            print(f"      Line {line}: ice=\"{val}\"")
        issues.append(("P0", f"{len(bad_ice)} invalid ice values", fname, str(len(bad_ice)), "0", "Fix ice values"))
    if bad_sugar:
        print(f"    {fname}: {len(bad_sugar)} invalid sugar values")
        for line, val in bad_sugar[:5]:
            print(f"      Line {line}: sugar=\"{val}\"")
        issues.append(("P0", f"{len(bad_sugar)} invalid sugar values", fname, str(len(bad_sugar)), "0", "Fix sugar values"))
    if bad_size:
        print(f"    {fname}: {len(bad_size)} invalid size values")
        for line, val in bad_size[:5]:
            print(f"      Line {line}: size=\"{val}\"")
        issues.append(("P0", f"{len(bad_size)} invalid size values", fname, str(len(bad_size)), "0", "Fix size values"))
    if bad_addon:
        print(f"    {fname}: {len(bad_addon)} invalid addon values")
        for line, val in bad_addon[:5]:
            print(f"      Line {line}: addon=\"{val}\"")
        issues.append(("P0", f"{len(bad_addon)} invalid addon values", fname, str(len(bad_addon)), "0", "Fix addon values"))
    if not bad_ice and not bad_sugar and not bad_size and not bad_addon:
        print(f"    {fname}: All values valid")

# 8f. Invalid intents
print("\n  ### 8f. Invalid intent values")
for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    bad = []
    for s in data:
        for intent in s["assistant"].get("intents", []):
            if intent not in VALID_INTENTS:
                bad.append((s["line"], intent))
    print(f"    {fname}: {len(bad)} invalid intents")
    if bad:
        for line, val in bad[:5]:
            print(f"      Line {line}: intent=\"{val}\"")
        issues.append(("P0", f"{len(bad)} invalid intent values", fname, str(len(bad)), "0", "Fix intent values"))

# 8g. fruit_tea items with category != null and != fruit_tea
print("\n  ### 8g. fruit_tea items with wrong category")
for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    bad = []
    for s in data:
        for order in s["assistant"].get("orders", []):
            item = order.get("item")
            cat = order.get("category")
            if item in FRUIT_TEA_ITEMS:
                # fruit_tea items should be fruit_tea or null
                if cat is not None and cat != "fruit_tea":
                    bad.append((s["line"], item, cat))
    if bad:
        print(f"    {fname}: {len(bad)} fruit_tea items with wrong category")
        for line, item, cat in bad:
            print(f"      Line {line}: {item} -> {cat}")
        issues.append(("P0", f"fruit_tea items with wrong category", fname, str(len(bad)), "0", "Fix to fruit_tea or null"))
    else:
        print(f"    {fname}: OK")

# 8h. Check for fruit_tea category null%
print("\n  ### 8h. fruit_tea category null% check")
for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    for item in FRUIT_TEA_ITEMS:
        null_count = 0
        total = 0
        for s in data:
            for order in s["assistant"].get("orders", []):
                if order.get("item") == item:
                    total += 1
                    if order.get("category") is None:
                        null_count += 1
        if total > 0:
            null_pct = null_count / total * 100
            print(f"    {fname} - {item}: {null_count}/{total} = {null_pct:.1f}% null")

# 8i. Items in data that are not on menu
print("\n  ### 8i. Unknown items (not on menu)")
known_items = set(MULTI_CAT_ITEMS + FRUIT_TEA_ITEMS)
for fname, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
    unknown = Counter()
    for s in data:
        for order in s["assistant"].get("orders", []):
            item = order.get("item")
            if item and item not in known_items:
                unknown[item] += 1
        for rec in s["assistant"].get("recommendations", []):
            item = rec.get("item")
            if item and item not in known_items:
                unknown[item] += 1
    if unknown:
        print(f"    {fname}: {sum(unknown.values())} references to unknown items")
        for item, cnt in sorted(unknown.items(), key=lambda x: -x[1]):
            print(f"      {item}: {cnt}")
        issues.append(("P0", f"Unknown items found in data", fname, str(sum(unknown.values())), "0", "Fix item names"))
    else:
        print(f"    {fname}: All items are on menu")

# ════════════════════════════════════════════════════════════════════════
# 9. SUMMARY: ISSUES TO FIX
# ════════════════════════════════════════════════════════════════════════
sep()
print("\n## 9. ISSUES TO FIX — SUMMARY TABLE")
sep()

# Deduplicate
seen_issues = set()
unique_issues = []
for issue in issues:
    key = (issue[0], issue[1], issue[2])
    if key not in seen_issues:
        seen_issues.add(key)
        unique_issues.append(issue)

# Sort by priority
unique_issues.sort(key=lambda x: x[0])

p0_count = sum(1 for i in unique_issues if i[0] == "P0")
p1_count = sum(1 for i in unique_issues if i[0] == "P1")
p2_count = sum(1 for i in unique_issues if i[0] == "P2")

print(f"\n  Total: {len(unique_issues)} issues (P0={p0_count}, P1={p1_count}, P2={p2_count})")
print()

print(f"  {'Pri':<4} {'Issue':<60} {'File':<12} {'Current':<14} {'Target':<14} {'Action'}")
print(f"  {'─'*4} {'─'*60} {'─'*12} {'─'*14} {'─'*14} {'─'*30}")
for pri, issue, file, current, target, action in unique_issues:
    print(f"  {pri:<4} {issue:<60} {file:<12} {current:<14} {target:<14} {action}")

print(f"\n  Legend:")
print(f"    P0 = Will cause model to learn wrong patterns (fix immediately)")
print(f"    P1 = Significant imbalance that could affect model performance")
print(f"    P2 = Minor, acceptable but worth noting")
print()
