#!/usr/bin/env python3
"""
補充「前段有分類 + 後段無分類 → category=null」的多輪訓練樣本。
涵蓋同品項與不同品項，並平衡品項分佈（優先補強朱槿普洱紅、米香玉露菁）。

用法:
  python add_category_null_multiturn.py          # 執行新增
  python add_category_null_multiturn.py --dry-run # 預覽不寫入
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# 從 train.jsonl 第一筆取得 system prompt
with open(DATA_DIR / "train.jsonl") as f:
    SYS_PROMPT = json.loads(f.readline())["messages"][0]["content"]


def order(item, category=None, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
    return {
        "item": item,
        "category": category,
        "size": size,
        "ice": ice,
        "sugar": sugar,
        "addon": addon or [],
        "qty": qty,
        "note": note,
    }


def sample(user_text, intents, orders, preferences=None, recommendations=None):
    assistant = json.dumps({
        "intents": intents,
        "orders": orders,
        "preferences": preferences or {},
        "recommendations": recommendations or [],
    }, ensure_ascii=False)
    return {
        "messages": [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant},
        ]
    }


# ====== 同品項：前段有分類，後段同品項無分類 → null ======
SAME_ITEM = [
    # 1. 桂花輕烏龍 鮮奶→null
    sample(
        "桂花輕烏龍鮮奶半糖少冰;再一杯桂花輕烏龍",
        ["order", "order"],
        [order("桂花輕烏龍", "fresh_milk_tea", ice="少冰", sugar="半糖"),
         order("桂花輕烏龍")],
    ),
    # 2. 琥珀鐵觀音 奶茶→null
    sample(
        "琥珀鐵觀音奶茶去冰;再一杯琥珀鐵觀音半糖",
        ["order", "order"],
        [order("琥珀鐵觀音", "rich_milk_tea", ice="去冰"),
         order("琥珀鐵觀音", sugar="半糖")],
    ),
    # 3. 三窨十五茉 純茶→null
    sample(
        "三窨十五茉純茶無糖;再來一杯三窨十五茉",
        ["order", "order"],
        [order("三窨十五茉", "pure_tea", sugar="無糖"),
         order("三窨十五茉")],
    ),
    # 4. 茶花紅烏龍 奶蓋→null (valid set)
    sample(
        "茶花紅烏龍奶蓋;還要一杯茶花紅烏龍",
        ["order", "order"],
        [order("茶花紅烏龍", "cloud_velvet"),
         order("茶花紅烏龍")],
    ),
    # 5. 金杯蜜香紅 鮮奶→null
    sample(
        "金杯蜜香紅鮮奶半糖去冰;加一杯金杯蜜香紅",
        ["order", "order"],
        [order("金杯蜜香紅", "fresh_milk_tea", ice="去冰", sugar="半糖"),
         order("金杯蜜香紅")],
    ),
    # 6. 朱槿普洱紅 鮮奶→null
    sample(
        "朱槿普洱紅鮮奶少冰;再一杯朱槿普洱紅無糖",
        ["order", "order"],
        [order("朱槿普洱紅", "fresh_milk_tea", ice="少冰"),
         order("朱槿普洱紅", sugar="無糖")],
    ),
    # 7. 米香玉露菁 奶茶→null
    sample(
        "米香玉露菁奶茶半糖;再來一杯米香玉露菁去冰",
        ["order", "order"],
        [order("米香玉露菁", "rich_milk_tea", sugar="半糖"),
         order("米香玉露菁", ice="去冰")],
    ),
    # 8. 朱槿普洱紅 純茶→null
    sample(
        "朱槿普洱紅純茶去冰;再一杯朱槿普洱紅",
        ["order", "order"],
        [order("朱槿普洱紅", "pure_tea", ice="去冰"),
         order("朱槿普洱紅")],
    ),
    # 9. 米香玉露菁 鮮奶→null (valid set)
    sample(
        "米香玉露菁鮮奶去冰無糖;再一杯米香玉露菁",
        ["order", "order"],
        [order("米香玉露菁", "fresh_milk_tea", ice="去冰", sugar="無糖"),
         order("米香玉露菁")],
    ),
    # 10. 桂花輕烏龍 奶蓋→null
    sample(
        "桂花輕烏龍奶蓋;再一杯桂花輕烏龍半糖",
        ["order", "order"],
        [order("桂花輕烏龍", "cloud_velvet"),
         order("桂花輕烏龍", sugar="半糖")],
    ),
]

# ====== 不同品項：前段有分類，後段不同品項無分類 → null ======
DIFF_ITEM = [
    # 11. 琥珀鐵觀音鮮奶 → 金杯蜜香紅 null
    sample(
        "琥珀鐵觀音鮮奶半糖去冰;再一杯金杯蜜香紅",
        ["order", "order"],
        [order("琥珀鐵觀音", "fresh_milk_tea", ice="去冰", sugar="半糖"),
         order("金杯蜜香紅")],
    ),
    # 12. 桂花輕烏龍奶茶 → 三窨十五茉 null
    sample(
        "桂花輕烏龍奶茶;再一杯三窨十五茉",
        ["order", "order"],
        [order("桂花輕烏龍", "rich_milk_tea"),
         order("三窨十五茉")],
    ),
    # 13. 茶花紅烏龍鮮奶 → 琥珀鐵觀音 null (valid set)
    sample(
        "茶花紅烏龍鮮奶半糖;再一杯琥珀鐵觀音",
        ["order", "order"],
        [order("茶花紅烏龍", "fresh_milk_tea", sugar="半糖"),
         order("琥珀鐵觀音")],
    ),
    # 14. 三窨十五茉純茶 → 朱槿普洱紅 null
    sample(
        "三窨十五茉純茶無糖;再一杯朱槿普洱紅",
        ["order", "order"],
        [order("三窨十五茉", "pure_tea", sugar="無糖"),
         order("朱槿普洱紅")],
    ),
    # 15. 朱槿普洱紅鮮奶 → 米香玉露菁 null
    sample(
        "朱槿普洱紅鮮奶去冰;再一杯米香玉露菁",
        ["order", "order"],
        [order("朱槿普洱紅", "fresh_milk_tea", ice="去冰"),
         order("米香玉露菁")],
    ),
    # 16. 米香玉露菁奶茶 → 三窨十五茉 null
    sample(
        "米香玉露菁奶茶半糖;再一杯三窨十五茉",
        ["order", "order"],
        [order("米香玉露菁", "rich_milk_tea", sugar="半糖"),
         order("三窨十五茉")],
    ),
    # 17. 金杯蜜香紅鮮奶 → 朱槿普洱紅 null
    sample(
        "金杯蜜香紅鮮奶去冰;再來一杯朱槿普洱紅",
        ["order", "order"],
        [order("金杯蜜香紅", "fresh_milk_tea", ice="去冰"),
         order("朱槿普洱紅")],
    ),
    # 18. 桂花輕烏龍奶蓋 → 茶花紅烏龍 null
    sample(
        "桂花輕烏龍奶蓋;再一杯茶花紅烏龍",
        ["order", "order"],
        [order("桂花輕烏龍", "cloud_velvet"),
         order("茶花紅烏龍")],
    ),
    # 19. 茶花紅烏龍奶蓋 → 米香玉露菁 null
    sample(
        "茶花紅烏龍奶蓋;再一杯米香玉露菁",
        ["order", "order"],
        [order("茶花紅烏龍", "cloud_velvet"),
         order("米香玉露菁")],
    ),
    # 20. 朱槿普洱紅純茶 → 米香玉露菁 null (valid set)
    sample(
        "朱槿普洱紅純茶無糖;再一杯米香玉露菁",
        ["order", "order"],
        [order("朱槿普洱紅", "pure_tea", sugar="無糖"),
         order("米香玉露菁")],
    ),
    # 21. 琥珀鐵觀音奶茶 → 茶花紅烏龍 null
    sample(
        "琥珀鐵觀音奶茶去冰;再一杯茶花紅烏龍",
        ["order", "order"],
        [order("琥珀鐵觀音", "rich_milk_tea", ice="去冰"),
         order("茶花紅烏龍")],
    ),
    # 22. 金杯蜜香紅奶茶 → 桂花輕烏龍 null
    sample(
        "金杯蜜香紅奶茶半糖;加一杯桂花輕烏龍",
        ["order", "order"],
        [order("金杯蜜香紅", "rich_milk_tea", sugar="半糖"),
         order("桂花輕烏龍")],
    ),
]

# ====== 三段式：前段有分類 + 中段無分類 + modify ======
THREE_SEG = [
    # 23. 三窨鮮奶 + 朱槿null + 都去冰
    sample(
        "三窨十五茉鮮奶半糖;再一杯朱槿普洱紅;都去冰",
        ["order", "order", "modify"],
        [order("三窨十五茉", "fresh_milk_tea", ice="去冰", sugar="半糖"),
         order("朱槿普洱紅", ice="去冰")],
    ),
    # 24. 琥珀鮮奶 + 米香null + 第一杯半糖去冰
    sample(
        "琥珀鐵觀音鮮奶;米香玉露菁;第一杯半糖去冰",
        ["order", "order", "modify"],
        [order("琥珀鐵觀音", "fresh_milk_tea", ice="去冰", sugar="半糖"),
         order("米香玉露菁")],
    ),
]

# ====== 分配：20 train + 4 valid ======
VALID_INDICES = {3, 8, 12, 19}  # samples 4, 9, 13, 20 (0-indexed)

ALL_SAMPLES = SAME_ITEM + DIFF_ITEM + THREE_SEG


def main():
    dry_run = "--dry-run" in sys.argv

    train_samples = []
    valid_samples = []
    for i, s in enumerate(ALL_SAMPLES):
        if i in VALID_INDICES:
            valid_samples.append(s)
        else:
            train_samples.append(s)

    print(f"新增樣本: {len(ALL_SAMPLES)} 筆 (train {len(train_samples)}, valid {len(valid_samples)})")

    # 品項統計
    item_count = {}
    null_count = 0
    for s in ALL_SAMPLES:
        output = json.loads(s["messages"][2]["content"])
        for o in output["orders"]:
            item = o["item"]
            item_count[item] = item_count.get(item, 0) + 1
            if o["category"] is None:
                null_count += 1

    print(f"\n品項分佈:")
    for item, count in sorted(item_count.items(), key=lambda x: -x[1]):
        print(f"  {item}: {count}")
    print(f"\ncategory=null 訂單數: {null_count}")

    # 分類關鍵字統計
    cat_count = {}
    for s in ALL_SAMPLES:
        output = json.loads(s["messages"][2]["content"])
        for o in output["orders"]:
            cat = o["category"] or "null"
            cat_count[cat] = cat_count.get(cat, 0) + 1
    print(f"\n分類分佈:")
    for cat, count in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    if dry_run:
        print("\n[DRY RUN] 不寫入檔案")
        print("\n=== 樣本預覽 ===")
        for i, s in enumerate(ALL_SAMPLES):
            dest = "valid" if i in VALID_INDICES else "train"
            user = s["messages"][1]["content"]
            output = json.loads(s["messages"][2]["content"])
            cats = [o.get("category") or "null" for o in output["orders"]]
            print(f"  [{dest}] {user}")
            print(f"         intents={output['intents']}  categories={cats}")
        return

    # 備份
    for fname in ["train.jsonl", "valid.jsonl"]:
        src = DATA_DIR / fname
        bak = DATA_DIR / f"{fname}.bak"
        if not bak.exists():
            import shutil
            shutil.copy2(src, bak)
            print(f"備份: {src} → {bak}")

    # 寫入
    train_path = DATA_DIR / "train.jsonl"
    valid_path = DATA_DIR / "valid.jsonl"

    with open(train_path, "a") as f:
        for s in train_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"已寫入 {len(train_samples)} 筆 → {train_path}")

    with open(valid_path, "a") as f:
        for s in valid_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"已寫入 {len(valid_samples)} 筆 → {valid_path}")

    # 驗證
    print("\n=== 驗證 ===")
    for fname in ["train.jsonl", "valid.jsonl"]:
        path = DATA_DIR / fname
        with open(path) as f:
            lines = f.readlines()
        print(f"{fname}: {len(lines)} 筆")

    # 自檢：所有新樣本的後段品項 category 必須為 null
    errors = 0
    for i, s in enumerate(ALL_SAMPLES):
        output = json.loads(s["messages"][2]["content"])
        orders = output["orders"]
        # 最後一筆 order（或第二筆）的 category 應為 null
        if len(orders) >= 2 and orders[-1]["category"] is not None:
            # 三段式 modify 不一定，但普通二段式後者必須 null
            intents = output["intents"]
            if intents[-1] != "modify":
                print(f"  ✗ 樣本 {i+1}: 後段 category={orders[-1]['category']}≠null")
                errors += 1
    if errors == 0:
        print("  ✓ 所有後段品項 category=null 檢查通過")


if __name__ == "__main__":
    main()
