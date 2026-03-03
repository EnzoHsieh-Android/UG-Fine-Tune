#!/usr/bin/env python3
"""Comprehensive training data quality audit for tea shop order LLM."""

import json
import sys
import re
from collections import Counter, defaultdict

# === Valid values ===
VALID_ITEMS = {
    "三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅",
    "朱槿普洱紅", "米香玉露菁", "青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"
}

VALID_CATEGORIES = {"pure_tea", "fresh_milk_tea", "rich_milk_tea", "fruit_tea", "cloud_velvet", None}

# Item-category valid combinations
ITEM_CATEGORIES = {
    "三窨十五茉": {"pure_tea", "fresh_milk_tea", "rich_milk_tea", None},
    "桂花輕烏龍": {"pure_tea", "fresh_milk_tea", "rich_milk_tea", "cloud_velvet", None},
    "茶花紅烏龍": {"pure_tea", "fresh_milk_tea", "rich_milk_tea", "cloud_velvet", None},
    "琥珀鐵觀音": {"fresh_milk_tea", "rich_milk_tea", None},
    "金杯蜜香紅": {"fresh_milk_tea", "rich_milk_tea", None},
    "朱槿普洱紅": {"pure_tea", "fresh_milk_tea", "rich_milk_tea", None},
    "米香玉露菁": {"pure_tea", "fresh_milk_tea", "rich_milk_tea", None},
    "青檸桂蜜": {"fruit_tea", None},
    "蜜桃紅烏龍": {"fruit_tea", None},
    "葡柚十五茉": {"fruit_tea", None},
}

# Categories that should NOT have size (single-size)
NO_SIZE_CATEGORIES = {"pure_tea", "fruit_tea", "cloud_velvet"}

# Fruit tea items (cold only)
FRUIT_TEA_ITEMS = {"青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"}

VALID_SUGARS = {"全糖", "五分糖", "三分糖", "一分糖", "無糖", "正常糖", "半糖", "少糖", "微糖", None}
VALID_ICE = {"正常冰", "少冰", "微冰", "去冰", "熱飲", None}
VALID_SIZES = {"M", "L", None}
VALID_ADDONS = {"紅烏龍茶凍", "燕麥粒"}
VALID_INTENTS = {"order", "recommend", "modify", "other"}

# Sugar keywords mapping for user text matching
SUGAR_KEYWORDS = {
    "全糖": "全糖", "五分糖": "五分糖", "三分糖": "三分糖", "一分糖": "一分糖",
    "無糖": "無糖", "正常糖": "正常糖", "半糖": "半糖", "少糖": "少糖", "微糖": "微糖",
    "不要糖": "無糖",
}

ICE_KEYWORDS = {
    "正常冰": "正常冰", "少冰": "少冰", "微冰": "微冰", "去冰": "去冰",
    "熱飲": "熱飲", "熱的": "熱飲", "溫的": "熱飲", "做熱的": "熱飲",
    "要熱": "熱飲", "不要冰": "去冰",
}


def audit_file(filepath, filename):
    issues = []
    user_texts = []  # for duplicate checking
    user_text_to_lines = defaultdict(list)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        # === Check 1: JSON format ===
        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            issues.append(f"[{filename}:{line_num}] JSONL 格式錯誤 — {e}")
            continue

        if "messages" not in data:
            issues.append(f"[{filename}:{line_num}] 缺少 messages 欄位")
            continue

        messages = data["messages"]

        # Find user and assistant messages
        user_msg = None
        assistant_msg = None
        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
            elif msg["role"] == "assistant":
                assistant_msg = msg["content"]

        if user_msg is None:
            issues.append(f"[{filename}:{line_num}] 缺少 user message")
            continue
        if assistant_msg is None:
            issues.append(f"[{filename}:{line_num}] 缺少 assistant message")
            continue

        # Track user texts for duplicate check
        user_texts.append((line_num, user_msg))
        user_text_to_lines[user_msg].append(line_num)

        # Parse assistant content as JSON
        try:
            output = json.loads(assistant_msg)
        except json.JSONDecodeError as e:
            issues.append(f"[{filename}:{line_num}] assistant content JSON 格式錯誤 — {e}")
            continue

        # Check required fields
        required_fields = {"intents", "orders", "preferences", "recommendations"}
        missing = required_fields - set(output.keys())
        if missing:
            issues.append(f"[{filename}:{line_num}] assistant JSON 缺少欄位: {missing}")

        intents = output.get("intents", [])
        orders = output.get("orders", [])
        preferences = output.get("preferences", {})
        recommendations = output.get("recommendations", [])

        # === Check 2: Intents consistency ===
        # 2a: Check intents values
        for i, intent in enumerate(intents):
            if intent not in VALID_INTENTS:
                issues.append(f"[{filename}:{line_num}] intents[{i}] 值不合法: '{intent}'")

        # 2b: Multi-turn check (semicolons)
        segments = user_msg.split(";")
        # Also check Chinese semicolons
        if "；" in user_msg:
            # If there are Chinese semicolons but no ASCII semicolons
            if ";" not in user_msg:
                issues.append(f"[{filename}:{line_num}] user text 使用中文分號「；」而非英文分號「;」 — '{user_msg}'")
            segments_cn = user_msg.split("；")
            if len(segments_cn) > len(segments):
                segments = segments_cn

        expected_intent_count = len(segments)
        if len(intents) != expected_intent_count:
            issues.append(f"[{filename}:{line_num}] intents 長度 ({len(intents)}) != segment 數量 ({expected_intent_count}) — user: '{user_msg}'")

        # 2c: Intent-content semantic match
        has_orders = len(orders) > 0
        has_recommendations = len(recommendations) > 0
        has_order_intent = "order" in intents
        has_recommend_intent = "recommend" in intents
        has_modify_intent = "modify" in intents

        # If there are orders but no order/modify intent
        if has_orders and not has_order_intent and not has_modify_intent:
            issues.append(f"[{filename}:{line_num}] 有 orders 但 intents 不含 order 或 modify — intents={intents}, orders={[o.get('item') for o in orders]}")

        # If there's a recommend intent but recommendations is empty
        if has_recommend_intent and not has_recommendations:
            issues.append(f"[{filename}:{line_num}] intents 含 recommend 但 recommendations 為空 — intents={intents}")

        # If there are recommendations but no recommend intent
        if has_recommendations and not has_recommend_intent:
            issues.append(f"[{filename}:{line_num}] 有 recommendations 但 intents 不含 recommend — intents={intents}")

        # === Check 3: Orders field validation ===
        for oi, order in enumerate(orders):
            item = order.get("item")
            category = order.get("category")
            size = order.get("size")
            ice = order.get("ice")
            sugar = order.get("sugar")
            addon = order.get("addon", [])
            qty = order.get("qty")
            note = order.get("note")

            # 3a: Check item name
            if item not in VALID_ITEMS:
                issues.append(f"[{filename}:{line_num}] orders[{oi}].item 不合法: '{item}'")

            # 3b: Check category
            if category not in VALID_CATEGORIES:
                issues.append(f"[{filename}:{line_num}] orders[{oi}].category 不合法: '{category}'")

            # 3c: Check item-category combination
            if item in ITEM_CATEGORIES and category is not None:
                if category not in ITEM_CATEGORIES[item]:
                    issues.append(f"[{filename}:{line_num}] orders[{oi}] item+category 組合不合法: '{item}' + '{category}'")

            # 3d: Check sugar
            if sugar not in VALID_SUGARS:
                issues.append(f"[{filename}:{line_num}] orders[{oi}].sugar 不合法: '{sugar}'")

            # 3e: Check ice
            if ice not in VALID_ICE:
                issues.append(f"[{filename}:{line_num}] orders[{oi}].ice 不合法: '{ice}'")

            # 3f: Check size
            if size not in VALID_SIZES:
                issues.append(f"[{filename}:{line_num}] orders[{oi}].size 不合法: '{size}'")

            # 3g: Fruit tea should NOT have ice="熱飲"
            if item in FRUIT_TEA_ITEMS and ice == "熱飲":
                issues.append(f"[{filename}:{line_num}] orders[{oi}] 果茶品項 '{item}' 不應有 ice='熱飲'（僅冷飲）")

            # 3h: pure_tea/fruit_tea/cloud_velvet should NOT have size
            if category in NO_SIZE_CATEGORIES and size is not None:
                issues.append(f"[{filename}:{line_num}] orders[{oi}] {category} 品項 '{item}' 不應有 size='{size}'（單一尺寸）")

            # Also check by item if category is null but item is fruit_tea
            if category is None and item in FRUIT_TEA_ITEMS and size is not None:
                issues.append(f"[{filename}:{line_num}] orders[{oi}] 果茶品項 '{item}' 不應有 size='{size}'（單一尺寸）")

            # 3i: Check addon values
            if addon:
                for a in addon:
                    if a not in VALID_ADDONS:
                        issues.append(f"[{filename}:{line_num}] orders[{oi}].addon 不合法: '{a}'")

            # 3j: Check qty is positive integer
            if qty is not None and (not isinstance(qty, int) or qty < 1):
                issues.append(f"[{filename}:{line_num}] orders[{oi}].qty 不合法: {qty}")

            # Check required order fields
            order_required = {"item", "category", "size", "ice", "sugar", "addon", "qty", "note"}
            order_missing = order_required - set(order.keys())
            if order_missing:
                issues.append(f"[{filename}:{line_num}] orders[{oi}] 缺少欄位: {order_missing}")

        # === Check 4: User text vs assistant output consistency ===
        # Check each segment
        for seg_i, segment in enumerate(segments):
            segment = segment.strip()

            # 4a: Check sugar mismatch
            user_sugars = []
            for kw, val in SUGAR_KEYWORDS.items():
                if kw in segment:
                    user_sugars.append(val)

            # 4b: Check ice mismatch
            user_ices = []
            for kw, val in ICE_KEYWORDS.items():
                if kw in segment:
                    user_ices.append(val)

        # Check for specific item names in user text that don't match orders
        # Use a simpler approach: check user mentions specific items
        user_item_mentions = []
        for item_name in VALID_ITEMS:
            if item_name in user_msg:
                user_item_mentions.append(item_name)

        # Also check common aliases
        item_aliases = {
            "鐵觀音": "琥珀鐵觀音",
            "蜜香紅": "金杯蜜香紅",
            "普洱": "朱槿普洱紅",
            "玉露": "米香玉露菁",
            "十五茉": "三窨十五茉",
            "茉莉": "三窨十五茉",
            "桂花": "桂花輕烏龍",
            "紅烏龍": "茶花紅烏龍",
            "蜜桃": "蜜桃紅烏龍",
            "葡柚": "葡柚十五茉",
            "青檸": "青檸桂蜜",
            "桂蜜": "青檸桂蜜",
        }

        order_items = [o.get("item") for o in orders]
        rec_items = [r.get("item") for r in recommendations]
        all_output_items = set(order_items + rec_items)

        # === Check 5: Duplicate detection is done after all lines ===

        # === Check 6: Recommendations ===
        for ri, rec in enumerate(recommendations):
            rec_item = rec.get("item")
            rec_cat = rec.get("category")
            rec_reason = rec.get("reason")

            if rec_item not in VALID_ITEMS:
                issues.append(f"[{filename}:{line_num}] recommendations[{ri}].item 不合法: '{rec_item}'")
            if rec_cat not in VALID_CATEGORIES:
                issues.append(f"[{filename}:{line_num}] recommendations[{ri}].category 不合法: '{rec_cat}'")
            if rec_item in ITEM_CATEGORIES and rec_cat is not None:
                if rec_cat not in ITEM_CATEGORIES[rec_item]:
                    issues.append(f"[{filename}:{line_num}] recommendations[{ri}] item+category 組合不合法: '{rec_item}' + '{rec_cat}'")
            if not rec_reason:
                issues.append(f"[{filename}:{line_num}] recommendations[{ri}].reason 為空")

            # Check rec required fields
            rec_required = {"item", "category", "reason"}
            rec_missing = rec_required - set(rec.keys())
            if rec_missing:
                issues.append(f"[{filename}:{line_num}] recommendations[{ri}] 缺少欄位: {rec_missing}")

        # More than 1 recommendation
        if len(recommendations) > 1:
            issues.append(f"[{filename}:{line_num}] recommendations 超過 1 項（有 {len(recommendations)} 項）— 規則限 1 項")

    # === Check 5: Exact duplicates ===
    for text, line_nums in user_text_to_lines.items():
        if len(line_nums) > 1:
            issues.append(f"[{filename}:行 {','.join(map(str, line_nums))}] 完全重複的 user text — '{text[:80]}...' ({len(line_nums)} 次)")

    # === Check 5b: Near-duplicates (differ by 1-2 chars) ===
    # Only check for short texts to avoid O(n^2) on long texts
    texts_with_lines = [(t, ls[0]) for t, ls in user_text_to_lines.items() if len(ls) == 1]
    near_dupes_found = set()
    for i in range(len(texts_with_lines)):
        t1, l1 = texts_with_lines[i]
        if len(t1) > 100:  # skip long texts
            continue
        for j in range(i + 1, len(texts_with_lines)):
            t2, l2 = texts_with_lines[j]
            if len(t2) > 100:
                continue
            if abs(len(t1) - len(t2)) > 2:
                continue
            # Simple edit distance check for 1-2 char difference
            diff = sum(1 for a, b in zip(t1, t2) if a != b) + abs(len(t1) - len(t2))
            if 0 < diff <= 2:
                key = (min(l1, l2), max(l1, l2))
                if key not in near_dupes_found:
                    near_dupes_found.add(key)
                    issues.append(f"[{filename}:行 {l1},{l2}] 近似重複 user text（差 {diff} 字）— '{t1}' vs '{t2}'")

    return issues


def detailed_consistency_check(filepath, filename):
    """More detailed user-text vs output consistency checks."""
    issues = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
        except:
            continue

        messages = data.get("messages", [])
        user_msg = None
        assistant_msg = None
        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
            elif msg["role"] == "assistant":
                assistant_msg = msg["content"]

        if not user_msg or not assistant_msg:
            continue

        try:
            output = json.loads(assistant_msg)
        except:
            continue

        orders = output.get("orders", [])
        intents = output.get("intents", [])

        # Check: user says 大杯/L but order has M or null
        if "大杯" in user_msg or "大的" in user_msg:
            for oi, order in enumerate(orders):
                # Only check if the order has size field and category supports size
                cat = order.get("category")
                if cat in ("fresh_milk_tea", "rich_milk_tea") or cat is None:
                    if order.get("size") != "L":
                        # But need to check which segment mentions 大杯
                        # Simple check: if single order and user says 大杯
                        if len(orders) == 1:
                            issues.append(f"[{filename}:{line_num}] 用戶說「大杯/大的」但 orders[{oi}].size='{order.get('size')}' — user: '{user_msg}'")

        # Check: user says 中杯/M but order has L or null
        if ("中杯" in user_msg or "小杯" in user_msg) and len(orders) == 1:
            for oi, order in enumerate(orders):
                cat = order.get("category")
                if cat in ("fresh_milk_tea", "rich_milk_tea") or cat is None:
                    if order.get("size") != "M":
                        issues.append(f"[{filename}:{line_num}] 用戶說「中杯」但 orders[{oi}].size='{order.get('size')}' — user: '{user_msg}'")

        # Check: user says 兩杯/兩份 but qty=1
        qty_patterns = {
            "兩杯": 2, "2杯": 2, "兩份": 2, "三杯": 3, "3杯": 3,
            "兩瓶": 2, "二杯": 2,
        }
        for pattern, expected_qty in qty_patterns.items():
            if pattern in user_msg and len(orders) == 1:
                if orders[0].get("qty") != expected_qty:
                    # Check if it's in same segment context
                    issues.append(f"[{filename}:{line_num}] 用戶說「{pattern}」但 orders[0].qty={orders[0].get('qty')} — user: '{user_msg}'")

        # Check: user explicitly says a sugar level but order has different sugar
        # Only for single-order cases to reduce false positives
        if len(orders) == 1 and ";" not in user_msg:
            order = orders[0]
            for kw in ["全糖", "五分糖", "三分糖", "一分糖", "無糖", "正常糖", "半糖", "少糖", "微糖"]:
                if kw in user_msg:
                    if order.get("sugar") != kw:
                        # Check if it's modify context (changing sugar)
                        if "modify" not in intents:
                            issues.append(f"[{filename}:{line_num}] 用戶說「{kw}」但 orders[0].sugar='{order.get('sugar')}' — user: '{user_msg}'")
                    break  # Only check first sugar mention

        # Check: user explicitly says ice level but order has different ice
        if len(orders) == 1 and ";" not in user_msg:
            order = orders[0]
            for kw in ["正常冰", "少冰", "微冰", "去冰"]:
                if kw in user_msg:
                    if order.get("ice") != kw:
                        if "modify" not in intents:
                            issues.append(f"[{filename}:{line_num}] 用戶說「{kw}」但 orders[0].ice='{order.get('ice')}' — user: '{user_msg}'")
                    break

        # Check: user says 熱的/熱飲/做熱 but ice is not 熱飲
        if len(orders) == 1 and ";" not in user_msg:
            order = orders[0]
            if any(kw in user_msg for kw in ["熱的", "熱飲", "做熱", "要熱"]):
                if order.get("ice") != "熱飲":
                    if "modify" not in intents:
                        # Exclude fruit tea items
                        if order.get("item") not in FRUIT_TEA_ITEMS:
                            issues.append(f"[{filename}:{line_num}] 用戶說「熱」但 orders[0].ice='{order.get('ice')}' — user: '{user_msg}'")

        # Check: size should be null for pure_tea and fruit_tea items that are explicitly categorized
        # Already covered in main audit

    return issues


def check_size_for_uncategorized_single_size_items(filepath, filename):
    """Check items that should be single-size but category is null."""
    issues = []

    # Items that ONLY appear in single-size categories
    PURE_TEA_ONLY_ITEMS = set()  # All pure_tea items also appear in milk tea
    # Actually no items are pure_tea only - all appear in milk tea too
    # But we should check: if user explicitly says 純茶, the size should be null

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except:
            continue

        messages = data.get("messages", [])
        user_msg = None
        assistant_msg = None
        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
            elif msg["role"] == "assistant":
                assistant_msg = msg["content"]

        if not user_msg or not assistant_msg:
            continue
        try:
            output = json.loads(assistant_msg)
        except:
            continue

        orders = output.get("orders", [])

        # Check: user says 純茶 but size is not null
        if "純茶" in user_msg:
            for oi, order in enumerate(orders):
                if order.get("category") == "pure_tea" and order.get("size") is not None:
                    issues.append(f"[{filename}:{line_num}] 純茶品項但 size 不為 null: orders[{oi}] size='{order.get('size')}' — user: '{user_msg}'")

        # Check: user says 奶蓋 but size is not null
        if "奶蓋" in user_msg:
            for oi, order in enumerate(orders):
                if order.get("category") == "cloud_velvet" and order.get("size") is not None:
                    issues.append(f"[{filename}:{line_num}] 奶蓋品項但 size 不為 null: orders[{oi}] size='{order.get('size')}' — user: '{user_msg}'")

    return issues


def check_valid_m_default(filepath, filename):
    """Check valid.jsonl line 5: size=M for 金杯蜜香紅鮮奶 where user didn't specify size."""
    issues = []

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except:
            continue

        messages = data.get("messages", [])
        user_msg = None
        assistant_msg = None
        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
            elif msg["role"] == "assistant":
                assistant_msg = msg["content"]

        if not user_msg or not assistant_msg:
            continue
        try:
            output = json.loads(assistant_msg)
        except:
            continue

        orders = output.get("orders", [])

        # Check: user didn't mention size but output has non-null size (for milk tea)
        # Only flag when user clearly didn't mention size
        size_keywords = ["大杯", "大的", "中杯", "小杯", "M", "L"]
        user_mentioned_size = any(kw in user_msg for kw in size_keywords)

        if not user_mentioned_size:
            for oi, order in enumerate(orders):
                cat = order.get("category")
                if cat in ("fresh_milk_tea", "rich_milk_tea") and order.get("size") is not None:
                    issues.append(f"[{filename}:{line_num}] 用戶未指定尺寸但 orders[{oi}].size='{order.get('size')}'（應為 null）— user: '{user_msg}'")

    return issues


def main():
    files = [
        ("/Users/xiechengru/ug-finetune/data/train.jsonl", "train.jsonl"),
        ("/Users/xiechengru/ug-finetune/data/valid.jsonl", "valid.jsonl"),
    ]

    all_issues = []

    for filepath, filename in files:
        print(f"\n{'='*60}")
        print(f"Auditing {filename}...")
        print(f"{'='*60}")

        issues1 = audit_file(filepath, filename)
        issues2 = detailed_consistency_check(filepath, filename)
        issues3 = check_size_for_uncategorized_single_size_items(filepath, filename)
        issues4 = check_valid_m_default(filepath, filename)

        file_issues = issues1 + issues2 + issues3 + issues4
        # Deduplicate
        file_issues = sorted(set(file_issues))

        all_issues.extend(file_issues)

        if file_issues:
            print(f"\n發現 {len(file_issues)} 個問題：\n")
            for issue in file_issues:
                print(issue)
        else:
            print("\n未發現問題。")

    # Cross-file duplicate check
    print(f"\n{'='*60}")
    print("跨檔案重複檢查...")
    print(f"{'='*60}")

    train_texts = {}
    valid_texts = {}

    for filepath, filename, store in [
        ("/Users/xiechengru/ug-finetune/data/train.jsonl", "train.jsonl", train_texts),
        ("/Users/xiechengru/ug-finetune/data/valid.jsonl", "valid.jsonl", valid_texts),
    ]:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    for msg in data["messages"]:
                        if msg["role"] == "user":
                            store[msg["content"]] = line_num
                except:
                    pass

    cross_dupes = set(train_texts.keys()) & set(valid_texts.keys())
    if cross_dupes:
        print(f"\n發現 {len(cross_dupes)} 個跨檔案重複：\n")
        for text in sorted(cross_dupes):
            issue = f"[train.jsonl:{train_texts[text]}, valid.jsonl:{valid_texts[text]}] 跨檔案重複 user text — '{text[:80]}'"
            print(issue)
            all_issues.append(issue)
    else:
        print("\n未發現跨檔案重複。")

    print(f"\n{'='*60}")
    print(f"總計發現 {len(all_issues)} 個問題")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
