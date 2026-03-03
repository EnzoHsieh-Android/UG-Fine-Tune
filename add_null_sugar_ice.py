#!/usr/bin/env python3
"""
補充 sugar=null + ice=null 樣本，同時補強桂花/茶花 category=null 和果茶品項。
目標：sugar null 25.7%→~30%, ice null 31.1%→~34%

用法:
  python add_null_sugar_ice.py          # 執行
  python add_null_sugar_ice.py --dry-run # 預覽
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

with open(DATA_DIR / "train.jsonl") as f:
    SYS_PROMPT = json.loads(f.readline())["messages"][0]["content"]


def order(item, category=None, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
    return {"item": item, "category": category, "size": size, "ice": ice,
            "sugar": sugar, "addon": addon or [], "qty": qty, "note": note}


def rec(item, category, reason):
    return {"item": item, "category": category, "reason": reason}


def s(user_text, intents, orders, prefs=None, recs=None):
    return {"messages": [
        {"role": "system", "content": SYS_PROMPT},
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": json.dumps({
            "intents": intents, "orders": orders,
            "preferences": prefs or {}, "recommendations": recs or [],
        }, ensure_ascii=False)},
    ]}


# ================================================================
# A. 單品項 sugar=null + ice=null（純品項名或帶分類/加料/尺寸）
# ================================================================
SINGLE = [
    # --- 桂花輕烏龍 category=null 補強 (目前 17%) ---
    s("一杯桂花輕烏龍", ["order"], [order("桂花輕烏龍")]),
    s("桂花輕烏龍一杯", ["order"], [order("桂花輕烏龍")]),
    s("給我桂花輕烏龍", ["order"], [order("桂花輕烏龍")]),
    s("來杯桂花的", ["order"], [order("桂花輕烏龍")]),
    s("桂花輕烏龍加茶凍", ["order"], [order("桂花輕烏龍", addon=["紅烏龍茶凍"])]),
    s("桂花輕烏龍要加燕麥粒", ["order"], [order("桂花輕烏龍", addon=["燕麥粒"])]),

    # --- 茶花紅烏龍 category=null 補強 (目前 19%) ---
    s("來一杯茶花紅烏龍", ["order"], [order("茶花紅烏龍")]),
    s("我要茶花紅烏龍", ["order"], [order("茶花紅烏龍")]),
    s("紅烏龍一杯", ["order"], [order("茶花紅烏龍")]),
    s("茶花紅烏龍要加茶凍", ["order"], [order("茶花紅烏龍", addon=["紅烏龍茶凍"])]),

    # --- 果茶補強（低頻品項）---
    s("蜜桃紅烏龍", ["order"], [order("蜜桃紅烏龍", "fruit_tea")]),
    s("一杯蜜桃紅烏龍", ["order"], [order("蜜桃紅烏龍", "fruit_tea")]),
    s("蜜桃的那個", ["order"], [order("蜜桃紅烏龍", "fruit_tea")]),
    s("葡柚十五茉", ["order"], [order("葡柚十五茉", "fruit_tea")]),
    s("來一杯葡柚十五茉", ["order"], [order("葡柚十五茉", "fruit_tea")]),
    s("葡柚那款", ["order"], [order("葡柚十五茉", "fruit_tea")]),
    s("青檸桂蜜", ["order"], [order("青檸桂蜜", "fruit_tea")]),
    s("一杯青檸桂蜜", ["order"], [order("青檸桂蜜", "fruit_tea")]),
    s("青檸的那個", ["order"], [order("青檸桂蜜", "fruit_tea")]),

    # --- 其他品項 null sugar+ice ---
    s("給我琥珀鐵觀音", ["order"], [order("琥珀鐵觀音")]),
    s("我要鐵觀音", ["order"], [order("琥珀鐵觀音")]),
    s("金杯蜜香紅", ["order"], [order("金杯蜜香紅")]),
    s("蜜香紅一杯", ["order"], [order("金杯蜜香紅")]),
    s("朱槿普洱紅", ["order"], [order("朱槿普洱紅")]),
    s("來杯米香玉露菁", ["order"], [order("米香玉露菁")]),
    s("三窨十五茉", ["order"], [order("三窨十五茉")]),
    s("來一杯茉莉", ["order"], [order("三窨十五茉")]),

    # --- 帶分類但不帶甜度冰量（category 有值，sugar+ice=null）---
    s("琥珀鐵觀音鮮奶", ["order"], [order("琥珀鐵觀音", "fresh_milk_tea")]),
    s("金杯蜜香紅的奶茶", ["order"], [order("金杯蜜香紅", "rich_milk_tea")]),
    s("朱槿普洱紅純茶", ["order"], [order("朱槿普洱紅", "pure_tea")]),
    s("米香玉露菁鮮奶", ["order"], [order("米香玉露菁", "fresh_milk_tea")]),
    s("三窨十五茉的奶茶", ["order"], [order("三窨十五茉", "rich_milk_tea")]),

    # --- 帶尺寸但不帶甜度冰量 ---
    s("琥珀鐵觀音鮮奶大杯", ["order"], [order("琥珀鐵觀音", "fresh_milk_tea", size="L")]),
    s("金杯蜜香紅鮮奶中杯", ["order"], [order("金杯蜜香紅", "fresh_milk_tea", size="M")]),
]

# ================================================================
# B. 多品項 sugar=null + ice=null
# ================================================================
MULTI = [
    # 兩品項都 null
    s("桂花輕烏龍跟茶花紅烏龍", ["order"],
      [order("桂花輕烏龍"), order("茶花紅烏龍")]),
    s("蜜桃紅烏龍、青檸桂蜜", ["order"],
      [order("蜜桃紅烏龍", "fruit_tea"), order("青檸桂蜜", "fruit_tea")]),
    s("琥珀鐵觀音跟金杯蜜香紅", ["order"],
      [order("琥珀鐵觀音"), order("金杯蜜香紅")]),
    s("朱槿普洱紅跟米香玉露菁", ["order"],
      [order("朱槿普洱紅"), order("米香玉露菁")]),
    s("三窨十五茉、桂花輕烏龍、茶花紅烏龍", ["order"],
      [order("三窨十五茉"), order("桂花輕烏龍"), order("茶花紅烏龍")]),
    s("葡柚十五茉和蜜桃紅烏龍", ["order"],
      [order("葡柚十五茉", "fruit_tea"), order("蜜桃紅烏龍", "fruit_tea")]),
]

# ================================================================
# C. 多輪 sugar=null + ice=null
# ================================================================
MULTI_ROUND = [
    s("桂花輕烏龍;再一杯茶花紅烏龍", ["order", "order"],
      [order("桂花輕烏龍"), order("茶花紅烏龍")]),
    s("蜜桃紅烏龍;加一杯青檸桂蜜", ["order", "order"],
      [order("蜜桃紅烏龍", "fruit_tea"), order("青檸桂蜜", "fruit_tea")]),
    s("琥珀鐵觀音;再來一杯朱槿普洱紅", ["order", "order"],
      [order("琥珀鐵觀音"), order("朱槿普洱紅")]),
    s("米香玉露菁鮮奶;再一杯三窨十五茉", ["order", "order"],
      [order("米香玉露菁", "fresh_milk_tea"), order("三窨十五茉")]),
    s("金杯蜜香紅;再加一杯葡柚十五茉", ["order", "order"],
      [order("金杯蜜香紅"), order("葡柚十五茉", "fruit_tea")]),
]

# ================================================================
# D. 推薦場景（sugar+ice 不適用但增加果茶推薦覆蓋）
# ================================================================
REC = [
    s("有什麼果茶", ["recommend"], [],
      {"taste": "果香"}, [rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香與紅烏龍交織，甜蜜芬芳")]),
    s("清爽的飲料", ["recommend"], [],
      {"taste": "清爽"}, [rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑")]),
]

ALL_SAMPLES = SINGLE + MULTI + MULTI_ROUND + REC

# 分配 valid（每 5 筆取 1 筆 ≈ 20%）
VALID_INDICES = {3, 8, 13, 18, 22, 27, 32, 36, 40, 44}


def main():
    dry_run = "--dry-run" in sys.argv

    train_samples = [s for i, s in enumerate(ALL_SAMPLES) if i not in VALID_INDICES]
    valid_samples = [s for i, s in enumerate(ALL_SAMPLES) if i in VALID_INDICES]

    print(f"新增: {len(ALL_SAMPLES)} 筆 (train {len(train_samples)}, valid {len(valid_samples)})")

    # 統計
    new_orders = 0
    null_sugar = 0
    null_ice = 0
    null_cat = 0
    item_cnt = {}
    for sample in ALL_SAMPLES:
        data = json.loads(sample["messages"][2]["content"])
        for o in data.get("orders", []):
            new_orders += 1
            if o.get("sugar") is None:
                null_sugar += 1
            if o.get("ice") is None:
                null_ice += 1
            if o.get("category") is None:
                null_cat += 1
            it = o.get("item", "")
            item_cnt[it] = item_cnt.get(it, 0) + 1

    print(f"\n新增 orders: {new_orders}")
    print(f"  sugar=null: {null_sugar}/{new_orders} ({null_sugar/new_orders*100:.0f}%)")
    print(f"  ice=null: {null_ice}/{new_orders} ({null_ice/new_orders*100:.0f}%)")
    print(f"  category=null: {null_cat}/{new_orders}")

    print(f"\n品項分佈:")
    for it, cnt in sorted(item_cnt.items(), key=lambda x: -x[1]):
        print(f"  {it}: {cnt}")

    # 預估影響
    print(f"\n--- 預估影響 ---")
    old_orders = 1950
    old_sugar_null = 501
    old_ice_null = 607
    new_total = old_orders + new_orders
    new_sugar = old_sugar_null + null_sugar
    new_ice = old_ice_null + null_ice
    print(f"  sugar null: {old_sugar_null}/{old_orders} ({old_sugar_null/old_orders*100:.1f}%) → {new_sugar}/{new_total} ({new_sugar/new_total*100:.1f}%)")
    print(f"  ice null: {old_ice_null}/{old_orders} ({old_ice_null/old_orders*100:.1f}%) → {new_ice}/{new_total} ({new_ice/new_total*100:.1f}%)")

    if dry_run:
        print("\n[DRY RUN]")
        return

    # 寫入
    with open(DATA_DIR / "train.jsonl", "a") as f:
        for sample in train_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    with open(DATA_DIR / "valid.jsonl", "a") as f:
        for sample in valid_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"\n已寫入 train +{len(train_samples)}, valid +{len(valid_samples)}")

    # 驗證
    for fname in ["train.jsonl", "valid.jsonl"]:
        with open(DATA_DIR / fname) as f:
            cnt = sum(1 for _ in f)
        print(f"  {fname}: {cnt} 筆")


if __name__ == "__main__":
    main()
