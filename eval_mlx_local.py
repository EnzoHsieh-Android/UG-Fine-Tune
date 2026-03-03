#!/usr/bin/env python3
"""本地 MLX 量化模型評估 — 驗證 fuse+quantize 後模型仍通過所有 eval cases。

用途：在 PEFT merge → MLX quantize 後、部署前執行，捕捉量化降級問題。
使用：python eval_mlx_local.py [model_path]
預設：model/Qwen3-8B-UG-order-v11-8bit
"""

import sys
import json
import copy

# 直接從 eval_checkpoints_direct 匯入共用元件
from eval_checkpoints_direct import (
    SYSTEM_PROMPT,
    ALL_TESTS,
    STANDARD_TESTS,
    NULL_TESTS,
    SUGAR_TESTS,
    RECOMMEND_TESTS,
    OTHER_TESTS,
    GENERALIZED_TESTS,
    CROSS_CATEGORY_TESTS,
    DOUBLE_ADDON_TESTS,
    MULTI_TURN_CATEGORY_TESTS,
    QUANTITY_SPLIT_TESTS,
    simulate_fill_defaults,
    check_test,
    parse_response,
)


def load_fused_model(model_path):
    """載入 fused MLX 模型（無 adapter）。"""
    from mlx_lm import load
    print(f"載入模型: {model_path}")
    model, tokenizer = load(model_path)
    print("模型載入完成")
    return model, tokenizer


def generate_response(model, tokenizer, user_input):
    """生成回應，與 llm_server_mlx.py 行為一致。"""
    from mlx_lm import generate
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    prompt += "/no_think\n"
    response = generate(model, tokenizer, prompt=prompt, max_tokens=512, verbose=False)
    # 剝掉 <think>...</think>
    if "</think>" in response:
        response = response.split("</think>")[-1].strip()
    return response.strip()


def run_eval(model_path):
    model, tokenizer = load_fused_model(model_path)

    category_results = {}
    total_passed = 0
    total_failed = 0
    failed_cases = []

    current_cat = ""
    for cat, test in ALL_TESTS:
        if cat != current_cat:
            current_cat = cat
            if cat not in category_results:
                category_results[cat] = {"passed": 0, "total": 0}

        user_input = test["input"]
        response = generate_response(model, tokenizer, user_input)
        intent, orders, recommendations, data = parse_response(response)

        raw_orders = copy.deepcopy(orders)
        if orders:
            orders = simulate_fill_defaults(orders)
        passed, reason = check_test(
            test, intent, orders, recommendations, data, raw_orders=raw_orders
        )

        category_results[cat]["total"] += 1

        if passed:
            total_passed += 1
            category_results[cat]["passed"] += 1
            print(f"  ✓ [{cat}] {user_input[:40]}")
        else:
            total_failed += 1
            failed_cases.append({
                "cat": cat,
                "input": user_input,
                "reason": reason,
                "response": response[:200],
            })
            print(f"  ✗ [{cat}] {user_input[:40]} → {reason}")

    total = total_passed + total_failed
    pct = total_passed * 100 // total if total else 0
    print(f"\n{'='*60}")
    print(f"MLX 量化模型評估結果: {total_passed}/{total} ({pct}%)")
    print(f"{'='*60}")

    print(f"\n分類結果:")
    for cat, r in category_results.items():
        status = "✓" if r["passed"] == r["total"] else "✗"
        print(f"  {status} {cat}: {r['passed']}/{r['total']}")

    if failed_cases:
        print(f"\n失敗案例:")
        for case in failed_cases:
            print(f"  [{case['cat']}] {case['input']}")
            print(f"    原因: {case['reason']}")
            print(f"    回應: {case['response'][:150]}")

    # 判定
    if total_passed == total:
        print(f"\n✅ 量化模型通過全部 {total} 個測試，可安全部署")
    else:
        print(f"\n⚠️  量化降級：{total_failed} 個案例失敗，建議：")
        print(f"   1. 檢查失敗案例是否為量化敏感 pattern")
        print(f"   2. 增加相關訓練資料強化 pattern")
        print(f"   3. 或嘗試不同量化精度（如 q6 替代 q8）")

    return total_passed, total, failed_cases


if __name__ == "__main__":
    default_model = "/Users/xiechengru/ug-finetune/model/Qwen3-8B-UG-order-v11-8bit"
    model_path = sys.argv[1] if len(sys.argv) > 1 else default_model
    run_eval(model_path)
