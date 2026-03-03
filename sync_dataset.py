#!/usr/bin/env python3
"""同步測試案例到 LangSmith Dataset（增量更新）。

從 eval_checkpoints_direct.py 的測試案例轉換格式後上傳。
只需在新增測試案例時跑一次。

增量策略：
- 用 input text 作為唯一鍵
- 已存在且 outputs 相同 → 跳過
- 已存在但 outputs 不同 → 更新
- 不存在 → 新增
- dataset 不存在 → 建立
"""

import os
import sys
from collections import Counter

from langsmith import Client

# Import test cases from eval script (no side effects at module level)
sys.path.insert(0, os.path.dirname(__file__))
from eval_checkpoints_direct import ALL_TESTS

DATASET_NAME = os.getenv("LANGSMITH_PROJECT", "ug-order-eval")
DATASET_DESCRIPTION = "UG 點單模型評估 — 涵蓋標準/Null策略/甜度/推薦/閒聊/泛化/跨分類/雙份加料/多輪category/數量拆分"


def convert_test_case(category: str, test: dict) -> tuple[dict, dict]:
    """將 eval 測試案例轉換為 LangSmith (inputs, outputs) 格式。"""
    inputs = {
        "input": test["input"],
        "test_category": category,
    }

    outputs = {
        "expected_intent": test["expect"],
        "expected_items": test.get("items", []),
        "expected_count": test.get("count", 0),
        "not_on_menu": test.get("not_on_menu", False),
        "check_null": test.get("check_null", {}),
        "check_value": test.get("check_value", {}),
        "check_orders": test.get("check_orders", []),
    }

    return inputs, outputs


def main():
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("錯誤：未設定 LANGSMITH_API_KEY")
        sys.exit(1)

    client = Client()

    # 取得或建立 dataset
    try:
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        print(f"找到現有 dataset: {DATASET_NAME} (id={dataset.id})")
    except Exception:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description=DATASET_DESCRIPTION,
        )
        print(f"建立新 dataset: {DATASET_NAME} (id={dataset.id})")

    # 讀取現有 examples，用 input text 建索引
    existing_examples = {}
    for example in client.list_examples(dataset_id=dataset.id):
        key = example.inputs.get("input", "")
        existing_examples[key] = example

    print(f"現有 examples: {len(existing_examples)} 筆")

    # 比對本地測試案例
    added = 0
    updated = 0
    skipped = 0
    local_keys = set()

    for category, test in ALL_TESTS:
        inputs, outputs = convert_test_case(category, test)
        key = inputs["input"]
        local_keys.add(key)

        if key in existing_examples:
            ex = existing_examples[key]
            # 比對 outputs 是否一致
            if ex.outputs == outputs and ex.inputs == inputs:
                skipped += 1
            else:
                client.update_example(
                    example_id=ex.id,
                    inputs=inputs,
                    outputs=outputs,
                )
                updated += 1
        else:
            client.create_example(
                inputs=inputs,
                outputs=outputs,
                dataset_id=dataset.id,
            )
            added += 1

    # 報告不在本地的遠端 examples（不自動刪除，僅提示）
    orphaned = set(existing_examples.keys()) - local_keys
    if orphaned:
        print(f"\n⚠ 遠端有 {len(orphaned)} 筆本地不存在的 examples（未刪除）:")
        for key in list(orphaned)[:5]:
            print(f"  - \"{key[:50]}\"")
        if len(orphaned) > 5:
            print(f"  ... 還有 {len(orphaned) - 5} 筆")

    # 摘要
    total = added + updated + skipped
    print(f"\n同步完成：{total} 筆")
    print(f"  新增: {added}")
    print(f"  更新: {updated}")
    print(f"  未變: {skipped}")

    # 分類統計
    cat_counts = Counter(cat for cat, _ in ALL_TESTS)
    print(f"\n分類統計（共 {len(ALL_TESTS)} 筆）:")
    for cat, count in cat_counts.items():
        print(f"  {cat}: {count} 筆")


if __name__ == "__main__":
    main()
