#!/usr/bin/env python3
"""Fix ALL audit issues before training:
1. Fix 48 menu item/category errors
2. Remove cross-set duplicates (keep in train, remove from valid)
3. Remove valid internal duplicates
4. Verify everything is clean
"""

import json
import copy
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent

# ── Menu structure (ground truth) ──
MENU = {
    "pure_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁"],
    "fresh_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "rich_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "fruit_tea": ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"],
    "cloud_velvet": ["桂花輕烏龍", "茶花紅烏龍"],
}

ITEM_CATEGORIES = {}
for cat, items in MENU.items():
    for item in items:
        if item not in ITEM_CATEGORIES:
            ITEM_CATEGORIES[item] = []
        ITEM_CATEGORIES[item].append(cat)

# ── Category fix rules ──
# When item+category is wrong, determine the correct category from context
def fix_category(item, wrong_cat, user_msg):
    """Fix wrong category based on context clues in user message."""
    valid_cats = ITEM_CATEGORIES.get(item, [])
    if not valid_cats:
        return wrong_cat  # Unknown item, leave as-is

    if wrong_cat in valid_cats:
        return wrong_cat  # Already valid

    # Context clues for category
    has_milk_clue = any(w in user_msg for w in ["鮮奶", "鮮奶茶"])
    has_rich_clue = any(w in user_msg for w in ["奶茶"])
    has_pure_clue = any(w in user_msg for w in ["純茶", "不加奶", "不要奶"])
    has_velvet_clue = any(w in user_msg for w in ["奶蓋"])

    # Priority: explicit clue > default
    if has_velvet_clue and "cloud_velvet" in valid_cats:
        return "cloud_velvet"
    if has_milk_clue and "fresh_milk_tea" in valid_cats:
        return "fresh_milk_tea"
    if has_rich_clue and "rich_milk_tea" in valid_cats:
        return "rich_milk_tea"
    if has_pure_clue and "pure_tea" in valid_cats:
        return "pure_tea"

    # No explicit clue: default to most common category
    # For items that exist in both fresh and rich, default to fresh_milk_tea
    if "fresh_milk_tea" in valid_cats:
        return "fresh_milk_tea"
    return valid_cats[0]


def fix_item_name(item, category):
    """Fix item name to match the correct name for the category."""
    # 茶花烏龍 vs 茶花紅烏龍 naming inconsistency
    if item == "茶花烏龍" and category in ["rich_milk_tea", "pure_tea", "cloud_velvet"]:
        return "茶花紅烏龍"
    if item == "茶花紅烏龍" and category == "fresh_milk_tea":
        return "茶花烏龍"
    return item


def fix_sample(sample):
    """Fix menu item/category issues in a single sample."""
    user_msg = ""
    for msg in sample["messages"]:
        if msg["role"] == "user":
            user_msg = msg["content"]

    fixes = 0
    for msg in sample["messages"]:
        if msg["role"] == "assistant":
            try:
                resp = json.loads(msg["content"])
                # Fix orders
                for order in resp.get("orders", []):
                    if order.get("not_on_menu"):
                        continue
                    item = order.get("item", "")
                    cat = order.get("category")
                    if cat and item in ITEM_CATEGORIES and cat not in ITEM_CATEGORIES[item]:
                        new_cat = fix_category(item, cat, user_msg)
                        new_item = fix_item_name(item, new_cat)
                        if new_cat != cat or new_item != item:
                            order["category"] = new_cat
                            order["item"] = new_item
                            fixes += 1
                    elif item in ITEM_CATEGORIES:
                        # Fix item name even if category is correct
                        new_item = fix_item_name(item, cat)
                        if new_item != item:
                            order["item"] = new_item
                            fixes += 1

                # Fix recommendations
                for rec in resp.get("recommendations", []):
                    item = rec.get("item", "")
                    cat = rec.get("category", "")
                    if cat and item in ITEM_CATEGORIES and cat not in ITEM_CATEGORIES[item]:
                        new_cat = fix_category(item, cat, user_msg)
                        new_item = fix_item_name(item, new_cat)
                        if new_cat != cat or new_item != item:
                            rec["category"] = new_cat
                            rec["item"] = new_item
                            fixes += 1

                if fixes > 0:
                    msg["content"] = json.dumps(resp, ensure_ascii=False)
            except json.JSONDecodeError:
                pass

    return sample, fixes


def process():
    total_fixes = 0

    # ── Fix train.jsonl ──
    print("=== Fixing train.jsonl ===")
    train_samples = []
    with open(DATA_DIR / "train.jsonl") as f:
        for line in f:
            if line.strip():
                train_samples.append(json.loads(line))

    train_fixes = 0
    for s in train_samples:
        _, fixes = fix_sample(s)
        train_fixes += fixes
    print(f"  Category fixes: {train_fixes}")
    total_fixes += train_fixes

    # ── Fix valid.jsonl ──
    print("\n=== Fixing valid.jsonl ===")
    valid_samples = []
    with open(DATA_DIR / "valid.jsonl") as f:
        for line in f:
            if line.strip():
                valid_samples.append(json.loads(line))

    valid_fixes = 0
    for s in valid_samples:
        _, fixes = fix_sample(s)
        valid_fixes += fixes
    print(f"  Category fixes: {valid_fixes}")
    total_fixes += valid_fixes

    # ── Remove cross-set duplicates from valid ──
    print("\n=== Removing cross-set duplicates ===")
    train_users = set()
    for s in train_samples:
        for msg in s["messages"]:
            if msg["role"] == "user":
                train_users.add(msg["content"])

    valid_deduped = []
    cross_removed = 0
    for s in valid_samples:
        user_msg = ""
        for msg in s["messages"]:
            if msg["role"] == "user":
                user_msg = msg["content"]
        if user_msg in train_users:
            cross_removed += 1
        else:
            valid_deduped.append(s)
    print(f"  Removed from valid (in train): {cross_removed}")

    # ── Remove valid internal duplicates ──
    seen = set()
    valid_final = []
    internal_removed = 0
    for s in valid_deduped:
        user_msg = ""
        for msg in s["messages"]:
            if msg["role"] == "user":
                user_msg = msg["content"]
        if user_msg in seen:
            internal_removed += 1
        else:
            seen.add(user_msg)
            valid_final.append(s)
    print(f"  Removed valid internal dupes: {internal_removed}")

    # ── Write fixed files ──
    with open(DATA_DIR / "train.jsonl", "w") as f:
        for s in train_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(DATA_DIR / "valid.jsonl", "w") as f:
        for s in valid_final:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"\n=== Summary ===")
    print(f"Total category fixes: {total_fixes}")
    print(f"Cross-set dupes removed: {cross_removed}")
    print(f"Internal dupes removed: {internal_removed}")
    print(f"Train: {len(train_samples)} samples")
    print(f"Valid: {len(valid_final)} samples (was {len(valid_samples)})")

    # ── Verify ──
    print("\n=== Verification ===")
    errors = 0
    for fname in ["train.jsonl", "valid.jsonl"]:
        with open(DATA_DIR / fname) as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                d = json.loads(line)
                for msg in d["messages"]:
                    if msg["role"] == "assistant":
                        try:
                            r = json.loads(msg["content"])
                            for order in r.get("orders", []):
                                if order.get("not_on_menu"):
                                    continue
                                item = order.get("item", "")
                                cat = order.get("category")
                                if cat and item in ITEM_CATEGORIES and cat not in ITEM_CATEGORIES[item]:
                                    print(f"  ❌ {fname}:{i+1} {item} as {cat}")
                                    errors += 1
                            for rec in r.get("recommendations", []):
                                item = rec.get("item", "")
                                cat = rec.get("category", "")
                                if cat and item in ITEM_CATEGORIES and cat not in ITEM_CATEGORIES[item]:
                                    print(f"  ❌ {fname}:{i+1} rec {item} as {cat}")
                                    errors += 1
                        except:
                            pass

    if errors == 0:
        print("  ✅ All menu item/category combinations are valid!")
    else:
        print(f"  ❌ {errors} remaining errors")

    # Check cross-set dupes
    train_u = set()
    valid_u = set()
    with open(DATA_DIR / "train.jsonl") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                for msg in d["messages"]:
                    if msg["role"] == "user":
                        train_u.add(msg["content"])
    with open(DATA_DIR / "valid.jsonl") as f:
        for line in f:
            if line.strip():
                d = json.loads(line)
                for msg in d["messages"]:
                    if msg["role"] == "user":
                        valid_u.add(msg["content"])
    remaining_cross = train_u & valid_u
    if remaining_cross:
        print(f"  ❌ {len(remaining_cross)} cross-set dupes remain")
    else:
        print("  ✅ No cross-set duplicates!")

    # Final distribution
    print("\n=== Final Distribution ===")
    for fname in ["train.jsonl", "valid.jsonl"]:
        intents = Counter()
        total = 0
        with open(DATA_DIR / fname) as f:
            for line in f:
                if line.strip():
                    total += 1
                    d = json.loads(line)
                    for msg in d["messages"]:
                        if msg["role"] == "assistant":
                            try:
                                r = json.loads(msg["content"])
                                intents[r.get("intent", "unknown")] += 1
                            except:
                                pass
        print(f"{fname}: {total} (order {intents['order']}, recommend {intents['recommend']}, "
              f"rec%={intents['recommend']*100/total:.1f}%)")


if __name__ == "__main__":
    process()
