#!/usr/bin/env python3
"""
補充多輪推薦樣本（plan Step 8），覆蓋 6 種場景。
目標 25 筆，不影響既有指標佔比。
"""
import json, sys
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
# A. [order, recommend, modify] — recommend 在中間 (5)
# ================================================================
A = [
    s("朱槿普洱紅純茶;有推薦清爽的嗎;改去冰",
      ["order", "recommend", "modify"],
      [order("朱槿普洱紅", "pure_tea", ice="去冰")],
      {"taste": "清爽"},
      [rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑")]),

    s("琥珀鐵觀音鮮奶;推薦花香的;改半糖",
      ["order", "recommend", "modify"],
      [order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖")],
      {"taste": "花香"},
      [rec("茶花紅烏龍", "cloud_velvet", "茶花香氣典雅，搭奶蓋綿密順口")]),

    s("蜜桃紅烏龍;有什麼好喝的;加茶凍",
      ["order", "recommend", "modify"],
      [order("蜜桃紅烏龍", "fruit_tea", addon=["紅烏龍茶凍"])],
      {},
      [rec("米香玉露菁", "fresh_milk_tea", "米香與玉露茶韻交融，溫潤醇厚")]),

    s("金杯蜜香紅奶茶;推薦果茶;少冰",
      ["order", "recommend", "modify"],
      [order("金杯蜜香紅", "rich_milk_tea", ice="少冰")],
      {"category": "果茶"},
      [rec("葡柚十五茉", "fruit_tea", "葡柚酸甜搭茉莉花香，清新消暑")]),

    s("米香玉露菁鮮奶;有推薦的嗎;改無糖",
      ["order", "recommend", "modify"],
      [order("米香玉露菁", "fresh_milk_tea", sugar="無糖")],
      {},
      [rec("朱槿普洱紅", "pure_tea", "朱槿花香融合普洱醇厚，層次豐富")]),
]

# ================================================================
# B. [order, modify, recommend] — recommend 在最後 (5)
# ================================================================
B = [
    s("朱槿普洱紅;改半糖;有推薦的嗎",
      ["order", "modify", "recommend"],
      [order("朱槿普洱紅", sugar="半糖")],
      {},
      [rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑")]),

    s("琥珀鐵觀音;去冰;推薦果茶",
      ["order", "modify", "recommend"],
      [order("琥珀鐵觀音", ice="去冰")],
      {"category": "果茶"},
      [rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香與紅烏龍交織，甜蜜芬芳")]),

    s("金杯蜜香紅鮮奶;加燕麥粒;有什麼推薦",
      ["order", "modify", "recommend"],
      [order("金杯蜜香紅", "fresh_milk_tea", addon=["燕麥粒"])],
      {},
      [rec("葡柚十五茉", "fruit_tea", "葡柚酸甜搭茉莉花香，清新消暑")]),

    s("米香玉露菁奶茶;改少冰;推薦甜一點的",
      ["order", "modify", "recommend"],
      [order("米香玉露菁", "rich_milk_tea", ice="少冰")],
      {"taste": "甜"},
      [rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香天然甜潤，清新不膩")]),

    s("茶花紅烏龍純茶;改去冰;有推薦奶茶嗎",
      ["order", "modify", "recommend"],
      [order("茶花紅烏龍", "pure_tea", ice="去冰")],
      {"category": "奶茶"},
      [rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音焙火韻搭奶精，濃醇回甘")]),
]

# ================================================================
# C. [recommend, recommend] — 多次 recommend (5)
# ================================================================
C = [
    s("推薦苦的;算了推薦甜的",
      ["recommend", "recommend"], [],
      {"taste": "甜"},
      [rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香天然甜潤，完全不苦")]),

    s("有什麼花香的;還是推薦果香的好了",
      ["recommend", "recommend"], [],
      {"taste": "果香"},
      [rec("葡柚十五茉", "fruit_tea", "葡柚酸甜搭茉莉花香，清新消暑")]),

    s("推薦純茶;不要了推薦奶茶",
      ["recommend", "recommend"], [],
      {"category": "奶茶"},
      [rec("金杯蜜香紅", "rich_milk_tea", "蜜香紅茶搭奶精，濃郁甘甜")]),

    s("推薦清爽的;還是推薦濃郁的",
      ["recommend", "recommend"], [],
      {"taste": "濃郁"},
      [rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音焙火濃醇，回甘持久")]),

    s("有推薦的嗎;改推薦不苦的",
      ["recommend", "recommend"], [],
      {"taste": "不苦"},
      [rec("米香玉露菁", "pure_tea", "玉露菁回甘清甜，完全不苦澀")]),
]

# ================================================================
# D. [recommend, order] — 推薦後點餐 (4)
# ================================================================
D = [
    s("有推薦的嗎;好那就朱槿普洱紅純茶",
      ["recommend", "order"],
      [order("朱槿普洱紅", "pure_tea")],
      {},
      [rec("朱槿普洱紅", "pure_tea", "朱槿花香融合普洱醇厚，層次豐富")]),

    s("推薦果茶;那來杯蜜桃紅烏龍",
      ["recommend", "order"],
      [order("蜜桃紅烏龍", "fruit_tea")],
      {"category": "果茶"},
      [rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香與紅烏龍交織，甜蜜芬芳")]),

    s("有什麼推薦;我要葡柚十五茉",
      ["recommend", "order"],
      [order("葡柚十五茉", "fruit_tea")],
      {},
      [rec("葡柚十五茉", "fruit_tea", "葡柚酸甜搭茉莉花香，清新消暑")]),

    s("推薦清爽的;那青檸桂蜜好了",
      ["recommend", "order"],
      [order("青檸桂蜜", "fruit_tea")],
      {"taste": "清爽"},
      [rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑")]),
]

# ================================================================
# E. [other, recommend] — 閒聊後推薦 (3)
# ================================================================
E = [
    s("你好;有什麼推薦",
      ["other", "recommend"], [],
      {},
      [rec("米香玉露菁", "fresh_milk_tea", "米香搭鮮奶溫潤順口，很受歡迎")]),

    s("請問;有推薦的飲料嗎",
      ["other", "recommend"], [],
      {},
      [rec("茶花紅烏龍", "fresh_milk_tea", "茶花香氣搭鮮奶，清甜順口")]),

    s("嗨;推薦好喝的",
      ["other", "recommend"], [],
      {},
      [rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑")]),
]

# ================================================================
# F. 複雜多輪 4 segments (3)
# ================================================================
F = [
    s("朱槿普洱紅鮮奶;有推薦的嗎;改去冰;推薦清爽的",
      ["order", "recommend", "modify", "recommend"],
      [order("朱槿普洱紅", "fresh_milk_tea", ice="去冰")],
      {"taste": "清爽"},
      [rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑")]),

    s("琥珀鐵觀音奶茶;推薦純茶;改半糖;推薦花香的",
      ["order", "recommend", "modify", "recommend"],
      [order("琥珀鐵觀音", "rich_milk_tea", sugar="半糖")],
      {"taste": "花香"},
      [rec("茶花紅烏龍", "pure_tea", "茶花香氣典雅，純茶韻味深厚")]),

    s("推薦苦的;一杯米香玉露菁純茶;推薦甜的;改半糖",
      ["recommend", "order", "recommend", "modify"],
      [order("米香玉露菁", "pure_tea", sugar="半糖")],
      {"taste": "甜"},
      [rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香天然甜潤，清新不膩")]),
]

ALL_SAMPLES = A + B + C + D + E + F
VALID_INDICES = {4, 9, 14, 19, 24}


def main():
    dry_run = "--dry-run" in sys.argv

    train = [s for i, s in enumerate(ALL_SAMPLES) if i not in VALID_INDICES]
    valid = [s for i, s in enumerate(ALL_SAMPLES) if i in VALID_INDICES]

    print(f"新增: {len(ALL_SAMPLES)} 筆 (train {len(train)}, valid {len(valid)})")
    print(f"場景: A={len(A)}, B={len(B)}, C={len(C)}, D={len(D)}, E={len(E)}, F={len(F)}")

    # Check duplicates
    existing = set()
    for fname in ["train.jsonl", "valid.jsonl"]:
        with open(DATA_DIR / fname) as f:
            for line in f:
                existing.add(json.loads(line)["messages"][1]["content"])

    dupes = [(i, sample["messages"][1]["content"])
             for i, sample in enumerate(ALL_SAMPLES)
             if sample["messages"][1]["content"] in existing]
    if dupes:
        print(f"\n⚠️ {len(dupes)} 筆重複:")
        for idx, text in dupes:
            print(f"  [{idx}] {text}")
        print("中止寫入")
        return

    # Stats
    new_orders = 0
    null_sugar = null_ice = 0
    item_cnt = {}
    for sample in ALL_SAMPLES:
        data = json.loads(sample["messages"][2]["content"])
        for o in data.get("orders", []):
            new_orders += 1
            if o.get("sugar") is None: null_sugar += 1
            if o.get("ice") is None: null_ice += 1
            it = o.get("item", "")
            item_cnt[it] = item_cnt.get(it, 0) + 1
        for r in data.get("recommendations", []):
            it = r.get("item", "")
            item_cnt[it] = item_cnt.get(it, 0) + 1

    print(f"\n新增 orders: {new_orders}")
    if new_orders:
        print(f"  sugar=null: {null_sugar}/{new_orders}")
        print(f"  ice=null: {null_ice}/{new_orders}")
    print(f"\n品項出現 (orders+recs):")
    for it, cnt in sorted(item_cnt.items(), key=lambda x: -x[1]):
        print(f"  {it}: {cnt}")

    if dry_run:
        print("\n[DRY RUN]")
        return

    with open(DATA_DIR / "train.jsonl", "a") as f:
        for sample in train:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    with open(DATA_DIR / "valid.jsonl", "a") as f:
        for sample in valid:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"\n已寫入 train +{len(train)}, valid +{len(valid)}")
    for fname in ["train.jsonl", "valid.jsonl"]:
        with open(DATA_DIR / fname) as f:
            print(f"  {fname}: {sum(1 for _ in f)} 筆")


if __name__ == "__main__":
    main()
