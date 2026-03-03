#!/usr/bin/env python3
"""
從 train.jsonl 抽取 200 筆多樣性樣本，格式化為推論 prompt 格式。
輸出 calibration_data.json 供 GPTQ 校準使用。
"""

import json
import random
from pathlib import Path
from collections import Counter

TRAIN_PATH = Path(__file__).parent / "data" / "train.jsonl"
OUTPUT_PATH = Path(__file__).parent / "calibration_data.json"
SAMPLE_SIZE = 200
SEED = 42


def classify_intent(assistant_text: str) -> str:
    """從 assistant 輸出推斷主要 intent 類型。"""
    try:
        data = json.loads(assistant_text)
        intents = data.get("intents", [])
        if not intents:
            return "other"
        # 用最後一個 intent 作為分類（與後端邏輯一致）
        return intents[-1]
    except (json.JSONDecodeError, KeyError):
        return "other"


def format_prompt(messages: list[dict]) -> str:
    """
    將 messages 格式化為推論時的 prompt 字串。
    格式與後端 llm.go 送給 /v1/completions 的一致。
    """
    system_content = ""
    user_content = ""
    assistant_content = ""

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            system_content = content
        elif role == "user":
            user_content = content
        elif role == "assistant":
            assistant_content = content

    # 完整 prompt（含 assistant 輸出，供校準用）
    prompt = (
        f"<|im_start|>system\n{system_content}<|im_end|>\n"
        f"<|im_start|>user\n{user_content}<|im_end|>\n"
        f"<|im_start|>assistant\n/no_think\n{assistant_content}<|im_end|>"
    )
    return prompt


def main():
    random.seed(SEED)

    # 讀取所有訓練資料
    samples = []
    with open(TRAIN_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))

    print(f"Total training samples: {len(samples)}")

    # 按 intent 分類
    by_intent: dict[str, list] = {}
    for sample in samples:
        messages = sample["messages"]
        assistant_msg = next(
            (m["content"] for m in messages if m["role"] == "assistant"), ""
        )
        intent = classify_intent(assistant_msg)
        by_intent.setdefault(intent, []).append(sample)

    print("Intent distribution:")
    for intent, items in sorted(by_intent.items()):
        print(f"  {intent}: {len(items)}")

    # 分層抽樣：按 intent 比例抽取，確保每種至少 5 筆
    selected = []
    remaining_budget = SAMPLE_SIZE

    # 先保證每種 intent 至少 5 筆
    min_per_intent = 5
    for intent, items in by_intent.items():
        n = min(min_per_intent, len(items))
        chosen = random.sample(items, n)
        selected.extend(chosen)
        remaining_budget -= n
        # 從候選中移除已選的
        chosen_set = {id(c) for c in chosen}
        by_intent[intent] = [x for x in items if id(x) not in chosen_set]

    # 剩餘按比例分配
    total_remaining = sum(len(v) for v in by_intent.values())
    if total_remaining > 0 and remaining_budget > 0:
        for intent, items in by_intent.items():
            proportion = len(items) / total_remaining
            n = min(int(remaining_budget * proportion), len(items))
            if n > 0:
                selected.extend(random.sample(items, n))

    # 如果還不夠，隨機補齊
    selected_ids = {id(s) for s in selected}
    all_remaining = [
        s for s in samples if id(s) not in selected_ids
    ]
    if len(selected) < SAMPLE_SIZE and all_remaining:
        extra = random.sample(
            all_remaining, min(SAMPLE_SIZE - len(selected), len(all_remaining))
        )
        selected.extend(extra)

    selected = selected[:SAMPLE_SIZE]
    random.shuffle(selected)

    # 格式化為 prompt 字串
    calibration_texts = []
    for sample in selected:
        prompt = format_prompt(sample["messages"])
        calibration_texts.append(prompt)

    # 統計最終 intent 分佈
    final_intents = Counter()
    for sample in selected:
        messages = sample["messages"]
        assistant_msg = next(
            (m["content"] for m in messages if m["role"] == "assistant"), ""
        )
        final_intents[classify_intent(assistant_msg)] += 1

    print(f"\nSelected {len(calibration_texts)} samples")
    print("Final intent distribution:")
    for intent, count in final_intents.most_common():
        print(f"  {intent}: {count}")

    # 輸出
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(calibration_texts, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
