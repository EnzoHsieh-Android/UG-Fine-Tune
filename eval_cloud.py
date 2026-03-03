#!/usr/bin/env python3
"""用 Together AI 推論 API 評估雲端 fine-tuned 模型。

Usage:
  python3 eval_cloud.py --model <together_model_name>
  python3 eval_cloud.py --model <together_model_name> --quick  # 只跑核心測試
"""

import argparse
import copy
import json
import os
import sys
import time

try:
    from together import Together
except ImportError:
    print("請先安裝: pip install together")
    sys.exit(1)

sys.path.insert(0, os.path.dirname(__file__))
from eval_checkpoints_direct import (
    ALL_TESTS,
    SYSTEM_PROMPT,
    check_test,
    parse_response,
    simulate_fill_defaults,
)


def generate_response_cloud(client, model, user_input, max_retries=3):
    """透過 Together API 生成回應。"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=512,
                temperature=0,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"    API 錯誤: {e}, {wait}s 後重試...")
                time.sleep(wait)
            else:
                print(f"    API 失敗: {e}")
                return ""


def main():
    parser = argparse.ArgumentParser(description="Cloud model evaluation")
    parser.add_argument("--model", required=True, help="Together AI model name")
    parser.add_argument("--quick", action="store_true", help="只跑核心測試（標準+Null+甜度）")
    args = parser.parse_args()

    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("錯誤: 請設定 TOGETHER_API_KEY")
        sys.exit(1)

    client = Together(api_key=api_key)

    # 選擇測試範圍
    if args.quick:
        quick_cats = {"標準", "Null策略", "甜度"}
        tests = [(cat, t) for cat, t in ALL_TESTS if cat in quick_cats]
        print(f"Quick 模式: {len(tests)} 筆測試")
    else:
        tests = ALL_TESTS
        print(f"完整模式: {len(tests)} 筆測試")

    print(f"Model: {args.model}\n")

    category_results = {}
    total_passed = 0
    total_failed = 0
    failed_cases = []

    for cat, test in tests:
        if cat not in category_results:
            category_results[cat] = {"passed": 0, "total": 0}

        user_input = test["input"]
        response = generate_response_cloud(client, args.model, user_input)
        intent, orders, recommendations, data = parse_response(response)

        raw_orders = copy.deepcopy(orders)
        if orders:
            orders = simulate_fill_defaults(orders)
        passed, reason = check_test(test, intent, orders, recommendations, data, raw_orders=raw_orders)

        category_results[cat]["total"] += 1

        if passed:
            total_passed += 1
            category_results[cat]["passed"] += 1
            print(f"  ✓ [{cat}] {user_input[:35]}")
        else:
            total_failed += 1
            failed_cases.append({"cat": cat, "input": user_input, "reason": reason, "response": response[:200]})
            print(f"  ✗ [{cat}] {user_input[:35]} → {reason}")

    total = total_passed + total_failed
    print(f"\n結果: {total_passed}/{total} ({total_passed*100//total if total else 0}%)")

    print(f"\n分類結果:")
    for cat, r in category_results.items():
        status = "✓" if r["passed"] == r["total"] else "✗"
        print(f"  {status} {cat}: {r['passed']}/{r['total']}")

    if failed_cases:
        print(f"\n失敗案例:")
        for case in failed_cases[:10]:
            print(f"  [{case['cat']}] {case['input'][:40]}")
            print(f"    原因: {case['reason']}")
            print(f"    回應: {case['response'][:120]}")


if __name__ == "__main__":
    main()
