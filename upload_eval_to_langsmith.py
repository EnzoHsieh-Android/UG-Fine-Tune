#!/usr/bin/env python3
"""上傳 eval_results.json 到 LangSmith 作為 experiment，供跨 round 比較。

用法:
  LANGSMITH_API_KEY=xxx python3 upload_eval_to_langsmith.py \
      --results adapters-runpod/eval_results.json \
      --round 32 \
      --checkpoint best

會在 ug-order-eval dataset 上建立一個 experiment，名稱如 "Round 32 (checkpoint-650, 54/60)"。
"""

import argparse
import json
import os
import sys
from datetime import datetime

from langsmith import Client

sys.path.insert(0, os.path.dirname(__file__))
from eval_checkpoints_direct import ALL_TESTS

DATASET_NAME = os.getenv("LANGSMITH_PROJECT", "ug-order-eval")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, help="eval_results.json 路徑")
    parser.add_argument("--round", required=True, help="Round 編號 (如 32)")
    parser.add_argument("--checkpoint", default="best", help="要上傳的 checkpoint (如 checkpoint-650 或 best)")
    parser.add_argument("--note", default="", help="額外備注")
    args = parser.parse_args()

    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("錯誤：未設定 LANGSMITH_API_KEY")
        sys.exit(1)

    # 讀取 eval results
    with open(args.results) as f:
        data = json.load(f)

    # 選擇 checkpoint
    if args.checkpoint == "best":
        cp_name = data["best"]
    else:
        cp_name = args.checkpoint

    if cp_name not in data["results"]:
        print(f"錯誤：找不到 {cp_name}，可用: {list(data['results'].keys())}")
        sys.exit(1)

    cp_data = data["results"][cp_name]
    passed = cp_data["passed"]
    total = cp_data["total"]
    failed_list = cp_data["failed"]

    # 建立 failed lookup: input_text → reason
    failed_map = {f["input"]: f["reason"] for f in failed_list}

    print(f"Round {args.round}, {cp_name}: {passed}/{total}")
    print(f"Failed: {len(failed_list)} cases")

    # 連接 LangSmith
    client = Client()

    # 取得 dataset
    dataset = client.read_dataset(dataset_name=DATASET_NAME)
    print(f"Dataset: {DATASET_NAME} (id={dataset.id})")

    # 讀取 dataset examples，建立 input→example_id 映射
    examples = {}
    for ex in client.list_examples(dataset_id=dataset.id):
        key = ex.inputs.get("input", "")
        examples[key] = ex

    print(f"Dataset examples: {len(examples)}")

    # Experiment 名稱
    note_suffix = f" - {args.note}" if args.note else ""
    experiment_name = f"Round {args.round} ({cp_name}, {passed}/{total}){note_suffix}"

    # 建立 experiment（透過 evaluate 的方式）
    # LangSmith evaluate API: 對每個 example 執行 evaluator 並記錄結果
    results = []
    matched = 0
    unmatched = 0

    for cat, test in ALL_TESTS:
        input_text = test["input"]
        if input_text not in examples:
            print(f"  ⚠ 找不到 dataset example: {input_text[:40]}")
            unmatched += 1
            continue

        is_failed = input_text in failed_map
        reason = failed_map.get(input_text, "")

        results.append({
            "example_id": examples[input_text].id,
            "input": input_text,
            "category": cat,
            "passed": not is_failed,
            "reason": reason,
        })
        matched += 1

    print(f"Matched: {matched}, Unmatched: {unmatched}")

    # 使用 client.evaluate 建立 experiment
    def make_evaluator(result_map):
        """建立 evaluator closure。"""
        lookup = {str(r["example_id"]): r for r in result_map}

        def evaluator(run, example):
            input_text = example.inputs.get("input", "")
            # 找到對應結果
            r = None
            for res in result_map:
                if res["input"] == input_text:
                    r = res
                    break

            if r is None:
                return {"results": [{"key": "pass", "score": 0, "comment": "未找到結果"}]}

            return {
                "results": [
                    {
                        "key": "pass",
                        "score": 1 if r["passed"] else 0,
                        "comment": r["reason"] if not r["passed"] else "通過",
                    },
                    {
                        "key": "category",
                        "score": 1 if r["passed"] else 0,
                        "comment": r["category"],
                    },
                ]
            }

        return evaluator

    # 用 dummy target function（我們只有結果，沒有實際模型）
    def dummy_target(inputs):
        input_text = inputs.get("input", "")
        if input_text in failed_map:
            return {"result": f"FAILED: {failed_map[input_text]}", "passed": False}
        return {"result": "PASSED", "passed": True}

    print(f"\n建立 experiment: {experiment_name}")

    experiment_results = client.evaluate(
        dummy_target,
        data=DATASET_NAME,
        evaluators=[make_evaluator(results)],
        experiment_prefix=experiment_name,
        metadata={
            "round": args.round,
            "checkpoint": cp_name,
            "passed": passed,
            "total": total,
            "pct": cp_data["pct"],
            "timestamp": datetime.now().isoformat(),
        },
    )

    print(f"\n上傳完成！Experiment: {experiment_name}")
    print(f"  {passed}/{total} ({cp_data['pct']}%)")


if __name__ == "__main__":
    main()
