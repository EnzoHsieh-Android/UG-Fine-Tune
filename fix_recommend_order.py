#!/usr/bin/env python3
"""
移除「recommend → order」多輪樣本中不現實的 order 段。
真實流程: 推薦後前端彈 dialog，用戶不會再打字下單。
做法: 截斷到 recommend 為止，移除後續的 order/modify segments。
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def save_jsonl(path, samples):
    with open(path, "w") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def get_user(s):
    return next(m for m in s["messages"] if m["role"] == "user")


def get_data(s):
    return json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])


def set_data(s, data):
    next(m for m in s["messages"] if m["role"] == "assistant")["content"] = json.dumps(data, ensure_ascii=False)


def main():
    train = load_jsonl(DATA_DIR / "train.jsonl")
    valid = load_jsonl(DATA_DIR / "valid.jsonl")
    print(f"載入: train={len(train)}, valid={len(valid)}")

    all_texts = set()
    for s in train + valid:
        all_texts.add(get_user(s)["content"])

    changed = 0
    skipped_dup = 0

    for src, samples in [("train", train), ("valid", valid)]:
        for idx, s in enumerate(samples):
            user_msg = get_user(s)
            user_text = user_msg["content"]
            data = get_data(s)
            intents = data.get("intents", [])
            segs = user_text.split(";")

            if len(intents) != len(segs) or len(intents) < 2:
                continue

            # Find first recommend→order transition
            cut_at = None
            for i in range(len(intents) - 1):
                if intents[i] == "recommend" and intents[i + 1] == "order":
                    cut_at = i + 1  # keep up to index i (inclusive)
                    break

            if cut_at is None:
                continue

            # Truncate
            new_segs = segs[:cut_at]
            new_intents = intents[:cut_at]
            new_user_text = ";".join(new_segs)

            # Check for duplicate
            if new_user_text in all_texts and new_user_text != user_text:
                skipped_dup += 1
                continue

            # Count how many orders come from the KEPT segments
            # Orders from 'order' intents before cut_at
            order_count_to_keep = 0
            for i in range(cut_at):
                if new_intents[i] == "order":
                    # Count orders from this segment
                    # Heuristic: count items mentioned in this segment
                    # Simpler: just count order intents
                    order_count_to_keep += 1

            # But one segment can produce multiple orders
            # Better approach: keep orders matching items in kept segments
            kept_text = new_user_text
            orders = data.get("orders", [])
            new_orders = []
            for o in orders:
                item = o.get("item", "")
                # Check if item appears in kept text
                if item in kept_text or item[:2] in kept_text:
                    new_orders.append(o)

            # Update
            all_texts.discard(user_text)
            all_texts.add(new_user_text)

            user_msg["content"] = new_user_text
            data["intents"] = new_intents
            data["orders"] = new_orders
            # Keep recommendations (they belong to the recommend intent)
            set_data(s, data)

            changed += 1

    print(f"已截斷: {changed} 筆")
    print(f"跳過（重複）: {skipped_dup}")

    # Save
    save_jsonl(DATA_DIR / "train.jsonl", train)
    save_jsonl(DATA_DIR / "valid.jsonl", valid)
    print("已儲存")

    # Verify: no more recommend→order pattern
    print("\n--- 驗證 ---")
    remaining = 0
    for s in train + valid:
        data = get_data(s)
        intents = data.get("intents", [])
        for i in range(len(intents) - 1):
            if intents[i] == "recommend" and intents[i + 1] == "order":
                remaining += 1
                user = get_user(s)["content"]
                print(f"  殘留: {user[:60]}")
                break
    print(f"  recommend→order 殘留: {remaining}")

    # Sample output
    print("\n--- 抽樣 (前 5 筆) ---")
    count = 0
    for s in train + valid:
        data = get_data(s)
        intents = data.get("intents", [])
        if "recommend" in intents and len(intents) >= 1:
            user = get_user(s)["content"]
            orders = [(o["item"], o.get("category")) for o in data.get("orders", [])]
            recs = [(r["item"], r.get("category")) for r in data.get("recommendations", [])]
            if count < 5:
                print(f"  User: {user[:70]}")
                print(f"  Intents: {intents}, Orders: {orders}")
                print(f"  Recs: {recs}")
                print()
            count += 1


if __name__ == "__main__":
    main()
