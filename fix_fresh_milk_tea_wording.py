#!/usr/bin/env python3
"""
將部分既有「{品項}鮮奶」user text 改為「{品項}鮮奶茶」。
目的: 讓模型學會「鮮奶茶」= fresh_milk_tea，符合口語用法。
目前「鮮奶」507 筆 vs「鮮奶茶」41 筆，目標平衡至各 ~270 筆。
"""

import json
import random
from pathlib import Path

random.seed(42)
DATA_DIR = Path(__file__).parent / "data"

TARGET_CONVERT = 9999  # 全部轉換

ALL_ITEMS = [
    "三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅",
    "米香玉露菁", "琥珀鐵觀音", "金杯蜜香紅",
]


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def save_jsonl(path, samples):
    with open(path, "w") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def main():
    train = load_jsonl(DATA_DIR / "train.jsonl")
    valid = load_jsonl(DATA_DIR / "valid.jsonl")
    print(f"載入: train={len(train)}, valid={len(valid)}")

    all_samples = [("train", i, s) for i, s in enumerate(train)] + \
                  [("valid", i, s) for i, s in enumerate(valid)]

    # ---- 1. 找候選 ----
    candidates = []
    for src, idx, s in all_samples:
        user_msg = next(m for m in s["messages"] if m["role"] == "user")
        user_text = user_msg["content"]
        data = json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])

        for item in ALL_ITEMS:
            pattern = f"{item}鮮奶"
            # 含 "{item}鮮奶" 但不含 "{item}鮮奶茶"
            if pattern not in user_text or f"{pattern}茶" in user_text:
                continue

            # 對應 order 必須是 fresh_milk_tea
            has_fresh = any(
                o["item"] == item and o.get("category") == "fresh_milk_tea"
                for o in data.get("orders", [])
            )
            if not has_fresh:
                continue

            # 確保只出現一次（避免歧義）
            if user_text.count(pattern) != 1:
                continue

            # 確認替換後 "{item}鮮奶茶" 不會和 "奶茶" 子串混淆
            # (前面已經確認沒有 "{item}鮮奶茶" 存在)
            candidates.append((src, idx, item))

    print(f"候選: {len(candidates)} 筆")

    # ---- 2. 隨機選取 ----
    selected = random.sample(candidates, min(TARGET_CONVERT, len(candidates)))
    print(f"選取: {len(selected)} 筆")

    # ---- 3. 收集所有 user text 用於重複檢測 ----
    all_texts = {}
    for src, idx, s in all_samples:
        user_text = next(m for m in s["messages"] if m["role"] == "user")["content"]
        all_texts[(src, idx)] = user_text

    # Build set of all texts (excluding selected ones)
    text_set = set(all_texts.values())

    # ---- 4. 執行替換 ----
    train_changed = 0
    valid_changed = 0
    skipped = 0

    for src, idx, item in selected:
        s = train[idx] if src == "train" else valid[idx]
        user_msg = next(m for m in s["messages"] if m["role"] == "user")
        old_text = user_msg["content"]

        # 替換 "{item}鮮奶" → "{item}鮮奶茶"
        new_text = old_text.replace(f"{item}鮮奶", f"{item}鮮奶茶", 1)

        # 檢查是否產生重複
        if new_text in text_set and new_text != old_text:
            skipped += 1
            continue

        # 更新
        text_set.discard(old_text)
        text_set.add(new_text)
        user_msg["content"] = new_text

        if src == "train":
            train_changed += 1
        else:
            valid_changed += 1

    print(f"已轉換: train {train_changed}, valid {valid_changed}")
    print(f"跳過（重複）: {skipped}")

    # ---- 5. 儲存 ----
    save_jsonl(DATA_DIR / "train.jsonl", train)
    save_jsonl(DATA_DIR / "valid.jsonl", valid)
    print("已儲存")

    # ---- 6. 驗證 ----
    print("\n--- 驗證 ---")
    train2 = load_jsonl(DATA_DIR / "train.jsonl")
    valid2 = load_jsonl(DATA_DIR / "valid.jsonl")

    fresh_nai = 0  # "{item}鮮奶" (非鮮奶茶)
    fresh_naicha = 0  # "{item}鮮奶茶"

    for s in train2 + valid2:
        user = next(m for m in s["messages"] if m["role"] == "user")["content"]
        for item in ALL_ITEMS:
            if f"{item}鮮奶茶" in user:
                fresh_naicha += 1
            elif f"{item}鮮奶" in user:
                fresh_nai += 1

    print(f"  「{'{item}'}鮮奶」: {fresh_nai}")
    print(f"  「{'{item}'}鮮奶茶」: {fresh_naicha}")
    print(f"  比例 鮮奶:鮮奶茶 = {fresh_nai}:{fresh_naicha}")


if __name__ == "__main__":
    main()
