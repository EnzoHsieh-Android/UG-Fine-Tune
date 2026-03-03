#!/usr/bin/env python3
"""
Round 31 自定義測試：
1. Intents 陣列品質 — 長度 = 分號數 + 1，值 ∈ {order, recommend, modify, other}
2. 多輪 category null — 同品項 & 不同品項場景
"""

import json
import requests

URL = "http://localhost:8080/v1/chat/completions"

SYSTEM_PROMPT = open("/Users/xiechengru/ug-finetune/data/train.jsonl").readline()
SYSTEM_PROMPT = json.loads(SYSTEM_PROMPT)["messages"][0]["content"]

VALID_INTENTS = {"order", "recommend", "modify", "other"}


def call_llm(text):
    """呼叫 LLM，返回 raw JSON dict"""
    resp = requests.post(URL, json={
        "model": "local",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ],
        "temperature": 0.0,
        "max_tokens": 512,
    })
    content = resp.json()["choices"][0]["message"]["content"]
    # Parse JSON from response
    if "</think>" in content:
        content = content.split("</think>")[-1].strip()
    return json.loads(content)


def test_intents_quality():
    """測試 intents 陣列品質"""
    print("=" * 60)
    print("1. Intents 陣列品質測試")
    print("=" * 60)

    cases = [
        # (text, expected_intents_count, expected_last_intent)
        ("一杯三窨十五茉", 1, "order"),
        ("你們有什麼推薦的", 1, "recommend"),
        ("你好", 1, "other"),
        ("三窨十五茉改去冰", 1, "modify"),
        ("一杯三窨十五茉;有推薦的嗎", 2, None),  # [order, recommend]
        ("一杯三窨十五茉;改去冰", 2, "modify"),
        ("一杯三窨十五茉;有推薦的嗎;改去冰", 3, "modify"),
        ("你好;一杯桂花輕烏龍", 2, "order"),
        ("有推薦的嗎;好那就桂花輕烏龍", 2, "order"),
        ("推薦苦的;算了推薦甜的", 2, "recommend"),
        ("一杯三窨十五茉;再一杯金杯蜜香紅", 2, None),  # both order
        ("一杯三窨十五茉、金杯蜜香紅、青檸桂蜜", 1, "order"),
    ]

    passed = 0
    failed = 0

    for text, expected_count, expected_last in cases:
        try:
            data = call_llm(text)
            intents = data.get("intents", [])

            errors = []

            # Check count
            semicolons = text.count(";")
            expected_by_semicolons = semicolons + 1
            if len(intents) != expected_by_semicolons:
                errors.append(f"len={len(intents)}≠{expected_by_semicolons}(分號{semicolons})")
            if expected_count and len(intents) != expected_count:
                errors.append(f"len={len(intents)}≠expected_{expected_count}")

            # Check values
            for idx, intent in enumerate(intents):
                if intent not in VALID_INTENTS:
                    errors.append(f"intents[{idx}]='{intent}' invalid")

            # Check last intent
            if expected_last and intents:
                if intents[-1] != expected_last:
                    errors.append(f"last={intents[-1]}≠{expected_last}")

            if errors:
                failed += 1
                print(f"  ✗ {text[:40]}")
                print(f"    intents: {intents}")
                print(f"    errors: {', '.join(errors)}")
            else:
                passed += 1
                print(f"  ✓ {text[:40]} → {intents}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {text[:40]} → ERROR: {e}")

    print(f"\nIntents 品質: {passed}/{passed+failed}")
    return passed, passed + failed


def test_category_null():
    """測試多輪 category null 行為"""
    print("\n" + "=" * 60)
    print("2. 多輪 Category Null 測試")
    print("=" * 60)

    passed = 0
    failed = 0

    # ---- 2a. 同品項，前輪有分類、後輪未指定分類 ----
    print("\n--- 2a. 同品項，後輪未指定分類 ---")

    cases_same_item = [
        {
            "name": "桂花輕烏龍: 鮮奶 → 未指定",
            "text": "一杯桂花輕烏龍鮮奶;再一杯桂花輕烏龍",
            "check_order_idx": 1,  # 第二杯
            "expect_category": None,  # 應為 null
        },
        {
            "name": "琥珀鐵觀音: 奶茶 → 未指定",
            "text": "琥珀鐵觀音奶茶半糖;再一杯琥珀鐵觀音",
            "check_order_idx": 1,
            "expect_category": None,
        },
        {
            "name": "三窨十五茉: 純茶 → 未指定",
            "text": "一杯三窨十五茉純茶;再一杯三窨十五茉",
            "check_order_idx": 1,
            "expect_category": None,
        },
        {
            "name": "茶花紅烏龍: 奶蓋 → 未指定",
            "text": "茶花紅烏龍奶蓋;再一杯茶花紅烏龍",
            "check_order_idx": 1,
            "expect_category": None,
        },
    ]

    for case in cases_same_item:
        try:
            data = call_llm(case["text"])
            orders = data.get("orders", [])
            idx = case["check_order_idx"]

            if idx >= len(orders):
                failed += 1
                print(f"  ✗ {case['name']} → orders count={len(orders)}, need idx={idx}")
                continue

            cat = orders[idx].get("category")
            if cat == case["expect_category"]:
                passed += 1
                print(f"  ✓ {case['name']} → category={cat}")
            else:
                failed += 1
                print(f"  ✗ {case['name']} → category={cat}≠{case['expect_category']}")
                print(f"    orders: {json.dumps(orders, ensure_ascii=False)[:200]}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {case['name']} → ERROR: {e}")

    # ---- 2b. 不同品項，前輪有分類、後輪未指定分類 ----
    print("\n--- 2b. 不同品項，後輪未指定分類 ---")

    cases_diff_item = [
        {
            "name": "琥珀鐵觀音鮮奶 → 金杯蜜香紅(未指定)",
            "text": "琥珀鐵觀音鮮奶半糖去冰;再一杯金杯蜜香紅",
            "check_order_idx": 1,
            "check_item": "金杯蜜香紅",
            "expect_category": None,
        },
        {
            "name": "桂花輕烏龍奶茶 → 三窨十五茉(未指定)",
            "text": "桂花輕烏龍奶茶大杯;再一杯三窨十五茉",
            "check_order_idx": 1,
            "check_item": "三窨十五茉",
            "expect_category": None,
        },
        {
            "name": "茶花紅烏龍鮮奶 → 琥珀鐵觀音(未指定)",
            "text": "一杯茶花紅烏龍鮮奶;再一杯琥珀鐵觀音",
            "check_order_idx": 1,
            "check_item": "琥珀鐵觀音",
            "expect_category": None,
        },
        {
            "name": "三窨十五茉奶蓋 → 桂花輕烏龍(未指定)",
            "text": "三窨十五茉奶蓋;再一杯桂花輕烏龍",
            "check_order_idx": 1,
            "check_item": "桂花輕烏龍",
            "expect_category": None,
        },
    ]

    for case in cases_diff_item:
        try:
            data = call_llm(case["text"])
            orders = data.get("orders", [])
            idx = case["check_order_idx"]

            if idx >= len(orders):
                failed += 1
                print(f"  ✗ {case['name']} → orders count={len(orders)}, need idx={idx}")
                continue

            order = orders[idx]
            item = order.get("item", "")
            cat = order.get("category")

            # 確認是正確的品項
            if case.get("check_item") and item != case["check_item"]:
                failed += 1
                print(f"  ✗ {case['name']} → item={item}≠{case['check_item']}")
                continue

            if cat == case["expect_category"]:
                passed += 1
                print(f"  ✓ {case['name']} → category={cat}")
            else:
                failed += 1
                print(f"  ✗ {case['name']} → category={cat}≠{case['expect_category']}")
                print(f"    orders: {json.dumps(orders, ensure_ascii=False)[:200]}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {case['name']} → ERROR: {e}")

    # ---- 2c. 未指定分類（單品項） ----
    print("\n--- 2c. 單品項，未指定分類 ---")

    cases_single = [
        ("桂花輕烏龍", None),
        ("琥珀鐵觀音去冰", None),
        ("三窨十五茉半糖", None),
        ("茶花紅烏龍", None),
        ("米香玉露菁", None),
    ]

    for text, expect_cat in cases_single:
        try:
            data = call_llm(text)
            orders = data.get("orders", [])
            if not orders:
                failed += 1
                print(f"  ✗ {text} → no orders")
                continue
            cat = orders[0].get("category")
            if cat == expect_cat:
                passed += 1
                print(f"  ✓ {text} → category={cat}")
            else:
                failed += 1
                print(f"  ✗ {text} → category={cat}≠{expect_cat}")
        except Exception as e:
            failed += 1
            print(f"  ✗ {text} → ERROR: {e}")

    print(f"\nCategory null: {passed}/{passed+failed}")
    return passed, passed + failed


if __name__ == "__main__":
    p1, t1 = test_intents_quality()
    p2, t2 = test_category_null()

    print("\n" + "=" * 60)
    print(f"總結: Intents {p1}/{t1}, Category {p2}/{t2}")
    print(f"合計: {p1+p2}/{t1+t2}")
    print("=" * 60)
