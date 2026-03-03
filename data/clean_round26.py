#!/usr/bin/env python3
"""
Round 26 Training Data Cleaner

Fixes:
1. Update system prompt: remove not_on_menu, add default category rule
2. Remove not_on_menu field from all assistant responses (66 samples)
3. Fix 紅玉紅茶 (not on menu) → category: null (11 samples)
4. Fix INVALID_SIZE: fresh_milk_tea/rich_milk_tea without size → "M" (26 samples)
5. Fix size="null" string → null (1 sample)
6. Fix ambiguous category: apply default rule (pure_tea first, then rich_milk_tea) (48 samples)
7. Fix REC_ITEM_NOT_ON_MENU: addon items recommended as menu items (4 samples)
"""

import json
import copy
import sys

# === Menu definition (source of truth) ===
MENU = {
    "pure_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁"],
    "fresh_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "rich_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "fruit_tea": ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"],
    "cloud_velvet": ["桂花輕烏龍", "茶花紅烏龍"],
}

ALL_ITEMS = set()
for items in MENU.values():
    ALL_ITEMS.update(items)

# Default category rule: pure_tea first, then rich_milk_tea
def get_default_category(item):
    if item in MENU["pure_tea"]:
        return "pure_tea"
    if item in MENU["rich_milk_tea"]:
        return "rich_milk_tea"
    if item in MENU["fruit_tea"]:
        return "fruit_tea"
    if item in MENU["cloud_velvet"]:
        return "cloud_velvet"
    return None

# Size rules
SINGLE_SIZE_CATS = {"pure_tea", "fruit_tea", "cloud_velvet"}
ML_SIZE_CATS = {"fresh_milk_tea", "rich_milk_tea"}

# Keywords that indicate specific categories
FRESH_MILK_KEYWORDS = ["鮮奶", "鮮"]
RICH_MILK_KEYWORDS = ["奶茶"]
PURE_TEA_KEYWORDS = ["純茶"]
CLOUD_KEYWORDS = ["奶蓋"]
FRUIT_KEYWORDS = ["果茶"]

# New system prompt
OLD_PROMPT_LINE = "若品項不在菜單上，設 not_on_menu。"
NEW_PROMPT_LINES = "未指定分類時，優先歸為純茶；若該品項無純茶選項，歸為奶茶。\n若品項無法確定分類，category 設 null。"


def update_system_prompt(content):
    """Replace the not_on_menu line in system prompt."""
    return content.replace(OLD_PROMPT_LINE, NEW_PROMPT_LINES)


def fix_order(order, user_text):
    """Fix a single order entry. Returns fixed order or None to remove."""
    item = order.get("item", "")
    cat = order.get("category")

    # --- Fix 1: Remove not_on_menu field, set category to null ---
    if order.get("not_on_menu"):
        # Remove not_on_menu-specific fields
        new_order = {
            "item": item,
            "category": None,
            "size": None,
            "ice": None,
            "sugar": None,
            "addon": [],
            "qty": order.get("qty", 1),
            "note": ""
        }
        return new_order

    # --- Fix 2: 紅玉紅茶 not on menu → category null ---
    if item not in ALL_ITEMS and cat is not None:
        new_order = {
            "item": item,
            "category": None,
            "size": None,
            "ice": None,
            "sugar": None,
            "addon": [],
            "qty": order.get("qty", 1),
            "note": ""
        }
        return new_order

    # --- Fix 3: Fix size="null" string → None ---
    if order.get("size") == "null":
        order["size"] = None

    # --- Fix 4: Determine correct category based on user text and default rule ---
    if item in ALL_ITEMS and cat is not None:
        # Check if user explicitly specified a category
        user_specified_cat = None
        for kw in FRESH_MILK_KEYWORDS:
            if kw in user_text:
                user_specified_cat = "fresh_milk_tea"
                break
        if not user_specified_cat:
            for kw in RICH_MILK_KEYWORDS:
                if kw in user_text:
                    user_specified_cat = "rich_milk_tea"
                    break
        if not user_specified_cat:
            for kw in PURE_TEA_KEYWORDS:
                if kw in user_text:
                    user_specified_cat = "pure_tea"
                    break
        if not user_specified_cat:
            for kw in CLOUD_KEYWORDS:
                if kw in user_text:
                    user_specified_cat = "cloud_velvet"
                    break

        # If user specified a category, validate item belongs there
        if user_specified_cat and item in MENU.get(user_specified_cat, []):
            correct_cat = user_specified_cat
        elif user_specified_cat is None:
            # No explicit category from user → apply default rule
            correct_cat = get_default_category(item)
        else:
            # User specified but item doesn't belong → keep original if valid
            if cat in MENU and item in MENU[cat]:
                correct_cat = cat
            else:
                correct_cat = get_default_category(item)

        if correct_cat and correct_cat != cat:
            order["category"] = correct_cat

    # --- Fix 5: Fix size based on category ---
    cat = order.get("category")
    if cat in SINGLE_SIZE_CATS:
        order["size"] = None
    elif cat in ML_SIZE_CATS:
        if order.get("size") is None or order.get("size") == "":
            order["size"] = "M"

    return order


def fix_recommendation(rec):
    """Fix a single recommendation. Returns fixed rec or None to remove."""
    item = rec.get("item", "")

    # Addons are not menu items - remove these recommendations
    if item in ["紅烏龍茶凍", "燕麥粒"]:
        return None

    # Validate category
    if item in ALL_ITEMS:
        cat = rec.get("category", "")
        if cat in MENU and item not in MENU[cat]:
            # Wrong category - find correct one
            for c, items in MENU.items():
                if item in items:
                    rec["category"] = c
                    break

    return rec


def clean_sample(sample):
    """Clean a single training sample."""
    msgs = sample.get("messages", [])
    new_msgs = []

    for msg in msgs:
        new_msg = copy.deepcopy(msg)

        # Update system prompt
        if msg["role"] == "system":
            new_msg["content"] = update_system_prompt(msg["content"])

        # Fix assistant response
        elif msg["role"] == "assistant":
            try:
                parsed = json.loads(msg["content"])
            except json.JSONDecodeError:
                new_msgs.append(new_msg)
                continue

            # Get user text for context
            user_text = ""
            for m in msgs:
                if m["role"] == "user":
                    user_text = m["content"]

            # Fix orders
            if "orders" in parsed:
                fixed_orders = []
                for order in parsed["orders"]:
                    fixed = fix_order(order, user_text)
                    if fixed is not None:
                        # Ensure clean key order
                        clean_order = {
                            "item": fixed.get("item", ""),
                            "category": fixed.get("category"),
                            "size": fixed.get("size"),
                            "ice": fixed.get("ice"),
                            "sugar": fixed.get("sugar"),
                            "addon": fixed.get("addon", []),
                            "qty": fixed.get("qty", 1),
                            "note": fixed.get("note", "")
                        }
                        fixed_orders.append(clean_order)
                parsed["orders"] = fixed_orders

            # Fix recommendations
            if "recommendations" in parsed:
                fixed_recs = []
                for rec in parsed["recommendations"]:
                    fixed = fix_recommendation(rec)
                    if fixed is not None:
                        fixed_recs.append(fixed)
                parsed["recommendations"] = fixed_recs

            # Remove any top-level not_on_menu or note that's about not_on_menu
            parsed.pop("not_on_menu", None)

            new_msg["content"] = json.dumps(parsed, ensure_ascii=False)

        new_msgs.append(new_msg)

    return {"messages": new_msgs}


def main():
    for split in ["train", "valid"]:
        input_path = f"/Users/xiechengru/ug-finetune/data/{split}.jsonl"
        backup_path = f"/Users/xiechengru/ug-finetune/data/{split}.jsonl.bak.r25"
        output_path = input_path

        # Read
        with open(input_path) as f:
            samples = [json.loads(line) for line in f]

        # Backup
        with open(backup_path, "w") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"Backed up {split}.jsonl → {split}.jsonl.bak.r25 ({len(samples)} samples)")

        # Clean
        cleaned = []
        changes = {"system_prompt": 0, "not_on_menu_removed": 0, "item_not_on_menu": 0,
                    "size_fixed": 0, "category_fixed": 0, "rec_fixed": 0}

        for i, sample in enumerate(samples):
            original_json = json.dumps(sample, ensure_ascii=False)
            fixed = clean_sample(sample)
            fixed_json = json.dumps(fixed, ensure_ascii=False)

            if original_json != fixed_json:
                # Count changes
                orig_msgs = sample["messages"]
                fix_msgs = fixed["messages"]

                for om, fm in zip(orig_msgs, fix_msgs):
                    if om["role"] == "system" and om["content"] != fm["content"]:
                        changes["system_prompt"] += 1
                    if om["role"] == "assistant" and om["content"] != fm["content"]:
                        if "not_on_menu" in om["content"] and "not_on_menu" not in fm["content"]:
                            changes["not_on_menu_removed"] += 1

            cleaned.append(fixed)

        # Write
        with open(output_path, "w") as f:
            for s in cleaned:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        print(f"Cleaned {split}.jsonl: {len(cleaned)} samples")
        print(f"  Changes: {changes}")

    print("\nDone!")


if __name__ == "__main__":
    main()
