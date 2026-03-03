#!/usr/bin/env python3
"""
修改既有 fresh_milk_tea / rich_milk_tea 樣本的 size=null → M/L。
目標: size null 從 84.8% 降到 ~75%，需改 243 筆。

做法：
  1. 找出 category=fresh_milk_tea/rich_milk_tea 且 size=null 的候選 order
  2. 條件：user text 含唯一 "{item}{鮮奶/奶茶}" 且無尺寸詞
  3. 隨機選 243 筆，按 L:M ≈ 70:30 分配
  4. 在 user text 的 item+category 後方插入「大杯」或「中杯」
  5. 更新 order.size = L 或 M
"""

import json
import random
from pathlib import Path

random.seed(42)
DATA_DIR = Path(__file__).parent / "data"

TARGET_CHANGES = 243
L_RATIO = 0.70  # 70% L, 30% M

CAT_KW = {"fresh_milk_tea": "鮮奶", "rich_milk_tea": "奶茶"}
SIZE_WORDS = ["大杯", "中杯", "大的", "中的"]


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

    all_samples = [("train", i, s) for i, s in enumerate(train)] + \
                  [("valid", i, s) for i, s in enumerate(valid)]

    # ---- 1. 找候選 ----
    candidates = []
    for src, idx, s in all_samples:
        user_msg = get_user(s)
        user_text = user_msg["content"]
        data = get_data(s)

        for oi, o in enumerate(data.get("orders", [])):
            cat = o.get("category")
            if cat not in CAT_KW or o.get("size") is not None:
                continue

            item = o["item"]
            kw = CAT_KW[cat]
            pattern = f"{item}{kw}"

            if user_text.count(pattern) != 1:
                continue

            if any(sz in user_text for sz in SIZE_WORDS):
                continue

            # fresh_milk_tea: '鮮奶' 不可接 '茶'
            pos = user_text.index(pattern) + len(pattern)
            if cat == "fresh_milk_tea" and pos < len(user_text) and user_text[pos] == "茶":
                continue

            # 同 item+category 只能有 1 筆 order
            same_combo = sum(1 for o2 in data["orders"]
                            if o2["item"] == item and o2.get("category") == cat)
            if same_combo > 1:
                continue

            candidates.append((src, idx, oi, item, cat, kw))

    print(f"候選: {len(candidates)} 筆")

    # ---- 2. 隨機選取 ----
    selected = random.sample(candidates, min(TARGET_CHANGES, len(candidates)))
    print(f"選取: {len(selected)} 筆")

    # ---- 3. 分配 L/M ----
    n_L = int(len(selected) * L_RATIO)
    sizes = ["L"] * n_L + ["M"] * (len(selected) - n_L)
    random.shuffle(sizes)
    size_text = {"L": "大杯", "M": "中杯"}

    # ---- 4. 修改 ----
    train_changed = 0
    valid_changed = 0

    for (src, idx, oi, item, cat, kw), new_size in zip(selected, sizes):
        s = train[idx] if src == "train" else valid[idx]
        user_msg = get_user(s)
        data = get_data(s)

        # 修改 user text: 在 "{item}{kw}" 後插入 "大杯"/"中杯"
        pattern = f"{item}{kw}"
        insert_word = size_text[new_size]
        user_msg["content"] = user_msg["content"].replace(pattern, f"{pattern}{insert_word}", 1)

        # 修改 size
        data["orders"][oi]["size"] = new_size
        set_data(s, data)

        if src == "train":
            train_changed += 1
        else:
            valid_changed += 1

    print(f"修改: train {train_changed}, valid {valid_changed}")
    print(f"L: {sizes.count('L')}, M: {sizes.count('M')}")

    # ---- 5. 儲存 ----
    save_jsonl(DATA_DIR / "train.jsonl", train)
    save_jsonl(DATA_DIR / "valid.jsonl", valid)
    print("已儲存")

    # ---- 6. 驗證 ----
    print("\n--- 驗證 ---")
    train2 = load_jsonl(DATA_DIR / "train.jsonl")
    valid2 = load_jsonl(DATA_DIR / "valid.jsonl")
    all2 = train2 + valid2

    total_orders = 0
    size_null = 0
    size_L = 0
    size_M = 0
    for s in all2:
        data = get_data(s)
        for o in data.get("orders", []):
            total_orders += 1
            sz = o.get("size")
            if sz is None:
                size_null += 1
            elif sz == "L":
                size_L += 1
            elif sz == "M":
                size_M += 1

    print(f"  Total orders: {total_orders}")
    print(f"  size null: {size_null} ({size_null/total_orders*100:.1f}%)")
    print(f"  size L: {size_L} ({size_L/total_orders*100:.1f}%)")
    print(f"  size M: {size_M} ({size_M/total_orders*100:.1f}%)")

    # 抽樣驗證: 印出 5 筆修改結果
    print("\n--- 抽樣驗證 (前 5 筆) ---")
    for src, idx, oi, item, cat, kw in selected[:5]:
        s = train2[idx] if src == "train" else valid2[idx]
        user_text = get_user(s)["content"]
        data = get_data(s)
        o = data["orders"][oi]
        print(f"  {src}:{idx+1} [{oi}] {item} {cat} size={o['size']}")
        print(f"    User: {user_text[:80]}")


if __name__ == "__main__":
    main()
