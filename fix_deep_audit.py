#!/usr/bin/env python3
"""
深度審計修正腳本。修正：
  1. 27 筆 category 錯標（用戶明確說了分類但 label 不符）
  2. 3 筆熱飲推薦果茶
  3. 2 筆 size=M 幻覺
  4. 8 筆「不加X」規格指定誤標為 modify

用法：
  python3 fix_deep_audit.py
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ====== Category 修正清單 ======
# (src, line_1based, order_index, wrong_cat, correct_cat)
CAT_FIXES = [
    # fresh_milk_tea → pure_tea (用戶說純茶)
    ("train", 47, 2, "fresh_milk_tea", "pure_tea"),
    ("train", 183, 1, "fresh_milk_tea", "pure_tea"),
    ("train", 413, 2, "fresh_milk_tea", "pure_tea"),
    ("train", 448, 1, "fresh_milk_tea", "pure_tea"),
    ("train", 484, 0, "fresh_milk_tea", "pure_tea"),
    ("train", 649, 1, "fresh_milk_tea", "pure_tea"),
    ("train", 749, 1, "fresh_milk_tea", "pure_tea"),
    ("valid", 128, 1, "fresh_milk_tea", "pure_tea"),
    # rich_milk_tea → pure_tea (用戶說純茶)
    ("train", 561, 1, "rich_milk_tea", "pure_tea"),
    ("valid", 148, 1, "rich_milk_tea", "pure_tea"),
    # fresh_milk_tea → rich_milk_tea (用戶說奶茶)
    ("train", 108, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 206, 0, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 234, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 240, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 276, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 292, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 332, 0, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 365, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 373, 0, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 378, 0, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 414, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 517, 2, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 564, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 566, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 606, 0, "fresh_milk_tea", "rich_milk_tea"),
    ("train", 715, 1, "fresh_milk_tea", "rich_milk_tea"),
    ("valid", 181, 1, "fresh_milk_tea", "rich_milk_tea"),
]

# ====== 熱飲推薦果茶修正 ======
# (src, line_1based, new_rec_item, new_rec_cat, new_rec_reason)
HOT_FRUIT_FIXES = [
    ("train", 245, "朱槿普洱紅", "pure_tea", "洛神微酸暖胃，不喝冰的好選擇"),
    ("train", 504, "桂花輕烏龍", "pure_tea", "桂花蜜韻輕柔，熱飲香氣更濃"),
    ("train", 569, "茶花紅烏龍", "pure_tea", "焙火熟果韻，涼爽天氣暖手暖心"),
]

# ====== Size 幻覺修正 ======
# (src, line_1based, order_index, item_name)
SIZE_FIXES = [
    ("train", 11, 0, "琥珀鐵觀音"),   # size=M → null
    ("valid", 96, 0, "三窨十五茉"),    # size=M → null
]

# ====== 不加X 誤標 modify → order ======
# (src, line_1based) — 整筆的 intents=['modify'] → ['order']
MODIFY_TO_ORDER = [
    ("train", 89),    # 金杯蜜香紅鮮奶大杯不加糖不加冰
    ("train", 360),   # 琥珀鐵觀音鮮奶半糖不加冰
    ("train", 472),   # 桂花輕烏龍純茶不加糖去冰
    ("train", 1166),  # 米香玉露菁不加奶無糖去冰，再一杯...
    ("train", 1171),  # 茶花紅烏龍茶就好不加奶無糖...
    ("train", 1222),  # 茶花紅烏龍茶就好不加奶
    ("train", 1277),  # 米香玉露菁不加奶無糖去冰
    ("valid", 168),   # 兩杯三窨十五茉鮮奶...一杯加茶凍一杯不加
]


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def save_jsonl(path, samples):
    with open(path, "w") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def get_data(s):
    return json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])


def set_data(s, data):
    next(m for m in s["messages"] if m["role"] == "assistant")["content"] = json.dumps(data, ensure_ascii=False)


def get_user(s):
    return next(m for m in s["messages"] if m["role"] == "user")["content"]


def main():
    print("=" * 60)
    print("深度審計修正")
    print("=" * 60)

    train = load_jsonl(DATA_DIR / "train.jsonl")
    valid = load_jsonl(DATA_DIR / "valid.jsonl")
    print(f"載入: train={len(train)}, valid={len(valid)}")

    def get_sample(src, ln):
        return train[ln - 1] if src == "train" else valid[ln - 1]

    # ---- 1. Category 修正 ----
    print(f"\n--- 1. Category 修正: {len(CAT_FIXES)} 筆 ---")
    for src, ln, oi, wrong, correct in CAT_FIXES:
        s = get_sample(src, ln)
        d = get_data(s)
        order = d["orders"][oi]
        assert order["category"] == wrong, \
            f"{src}:{ln}[{oi}] expected cat={wrong}, got {order['category']}: {get_user(s)[:50]}"
        order["category"] = correct
        set_data(s, d)
    print(f"  ✓ {len(CAT_FIXES)} 筆 category 修正完成")

    # ---- 2. 熱飲推薦果茶 ----
    print(f"\n--- 2. 熱飲推薦果茶修正: {len(HOT_FRUIT_FIXES)} 筆 ---")
    FRUIT_TEA = {"青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"}
    for src, ln, new_item, new_cat, new_reason in HOT_FRUIT_FIXES:
        s = get_sample(src, ln)
        d = get_data(s)
        for r in d["recommendations"]:
            if r["item"] in FRUIT_TEA:
                old = r["item"]
                r["item"] = new_item
                r["category"] = new_cat
                r["reason"] = new_reason
                print(f"  {src}:{ln} — {old} → {new_item}")
                break
        set_data(s, d)

    # ---- 3. Size 幻覺 ----
    print(f"\n--- 3. Size 幻覺修正: {len(SIZE_FIXES)} 筆 ---")
    for src, ln, oi, item_name in SIZE_FIXES:
        s = get_sample(src, ln)
        d = get_data(s)
        order = d["orders"][oi]
        assert order["item"] == item_name, \
            f"{src}:{ln}[{oi}] expected item={item_name}, got {order['item']}"
        assert order["size"] == "M", \
            f"{src}:{ln}[{oi}] expected size=M, got {order['size']}"
        order["size"] = None
        set_data(s, d)
        print(f"  {src}:{ln} — {item_name} size=M → null")

    # ---- 4. modify → order ----
    print(f"\n--- 4. 不加X modify→order 修正: {len(MODIFY_TO_ORDER)} 筆 ---")
    for src, ln in MODIFY_TO_ORDER:
        s = get_sample(src, ln)
        d = get_data(s)
        old_intents = d["intents"]
        assert old_intents == ["modify"], \
            f"{src}:{ln} expected intents=['modify'], got {old_intents}: {get_user(s)[:50]}"
        d["intents"] = ["order"]
        set_data(s, d)
        print(f"  {src}:{ln} — ['modify'] → ['order']")

    # ---- 儲存 ----
    print(f"\n--- 儲存 ---")
    save_jsonl(DATA_DIR / "train.jsonl", train)
    save_jsonl(DATA_DIR / "valid.jsonl", valid)
    print(f"儲存: train={len(train)}, valid={len(valid)}")

    # ---- 驗證 ----
    print(f"\n--- 驗證 ---")
    train2 = load_jsonl(DATA_DIR / "train.jsonl")
    valid2 = load_jsonl(DATA_DIR / "valid.jsonl")

    # Category fixes
    cat_ok = True
    for src, ln, oi, wrong, correct in CAT_FIXES:
        s = train2[ln-1] if src == "train" else valid2[ln-1]
        d = get_data(s)
        if d["orders"][oi]["category"] != correct:
            print(f"  ✗ {src}:{ln}[{oi}] still {d['orders'][oi]['category']}")
            cat_ok = False
    print(f"  Category 修正: {'✓' if cat_ok else '✗'}")

    # Hot fruit fixes
    hot_ok = True
    for src, ln, new_item, new_cat, _ in HOT_FRUIT_FIXES:
        s = train2[ln-1] if src == "train" else valid2[ln-1]
        d = get_data(s)
        for r in d["recommendations"]:
            if r["item"] in FRUIT_TEA:
                print(f"  ✗ {src}:{ln} still has fruit tea rec: {r['item']}")
                hot_ok = False
    print(f"  熱飲推薦: {'✓' if hot_ok else '✗'}")

    # Size fixes
    size_ok = True
    for src, ln, oi, item_name in SIZE_FIXES:
        s = train2[ln-1] if src == "train" else valid2[ln-1]
        d = get_data(s)
        if d["orders"][oi]["size"] is not None:
            print(f"  ✗ {src}:{ln}[{oi}] size={d['orders'][oi]['size']}")
            size_ok = False
    print(f"  Size 修正: {'✓' if size_ok else '✗'}")

    # Modify fixes
    mod_ok = True
    for src, ln in MODIFY_TO_ORDER:
        s = train2[ln-1] if src == "train" else valid2[ln-1]
        d = get_data(s)
        if d["intents"] != ["order"]:
            print(f"  ✗ {src}:{ln} intents={d['intents']}")
            mod_ok = False
    print(f"  Modify→Order: {'✓' if mod_ok else '✗'}")

    print(f"\n{'='*60}")
    total = len(CAT_FIXES) + len(HOT_FRUIT_FIXES) + len(SIZE_FIXES) + len(MODIFY_TO_ORDER)
    print(f"修正完成！共 {total} 筆")
    print("=" * 60)


if __name__ == "__main__":
    main()
