#!/usr/bin/env python3
"""
新增「鮮奶茶」→ fresh_milk_tea 訓練樣本。
目的: 教模型區分「鮮奶茶」(fresh_milk_tea) 和「奶茶」(rich_milk_tea)。
目前「鮮奶茶」只有 26 筆，相比「鮮奶」507 筆嚴重不足。

兼顧 sugar/ice null ~40%、size null ~75%。
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


def get_system_prompt(samples):
    return next(m for m in samples[0]["messages"] if m["role"] == "system")["content"]


def make_sample(sys_prompt, user_text, intents, orders, prefs=None, recs=None):
    assistant_data = {
        "intents": intents,
        "orders": orders,
        "preferences": prefs or {},
        "recommendations": recs or [],
    }
    return {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(assistant_data, ensure_ascii=False)},
        ]
    }


def order(item, cat, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
    return {
        "item": item, "category": cat, "size": size,
        "ice": ice, "sugar": sugar,
        "addon": addon or [], "qty": qty, "note": note,
    }


def main():
    train = load_jsonl(DATA_DIR / "train.jsonl")
    valid = load_jsonl(DATA_DIR / "valid.jsonl")
    sys_prompt = get_system_prompt(train)

    print(f"修正前: train={len(train)}, valid={len(valid)}")

    # ================================================================
    # Train 新增樣本 (12 筆)
    # 三種模式:
    #   A. 單純「X鮮奶茶」→ fresh_milk_tea (覆蓋各品項)
    #   B. 對比「X鮮奶茶 + X奶茶」→ fresh vs rich
    #   C. 多杯同品項鮮奶茶、不同規格
    # ================================================================
    new_train = [
        # A1. 三窨十五茉鮮奶茶 + spec
        make_sample(sys_prompt,
            "三窨十五茉鮮奶茶半糖少冰",
            ["order"],
            [order("三窨十五茉", "fresh_milk_tea", sugar="半糖", ice="少冰")]),

        # A2. 琥珀鐵觀音鮮奶茶 + size + spec
        make_sample(sys_prompt,
            "琥珀鐵觀音鮮奶茶大杯無糖去冰",
            ["order"],
            [order("琥珀鐵觀音", "fresh_milk_tea", size="L", sugar="無糖", ice="去冰")]),

        # A3. 朱槿普洱紅鮮奶茶 + spec (null size)
        make_sample(sys_prompt,
            "朱槿普洱紅鮮奶茶微糖少冰",
            ["order"],
            [order("朱槿普洱紅", "fresh_milk_tea", sugar="微糖", ice="少冰")]),

        # A4. 米香玉露菁鮮奶茶 + size + spec
        make_sample(sys_prompt,
            "米香玉露菁鮮奶茶中杯無糖去冰",
            ["order"],
            [order("米香玉露菁", "fresh_milk_tea", size="M", sugar="無糖", ice="去冰")]),

        # A5. 茶花紅烏龍鮮奶茶 (null sugar/ice)
        make_sample(sys_prompt,
            "茶花紅烏龍鮮奶茶",
            ["order"],
            [order("茶花紅烏龍", "fresh_milk_tea")]),

        # A6. 桂花輕烏龍鮮奶茶 + partial spec (null ice)
        make_sample(sys_prompt,
            "桂花輕烏龍鮮奶茶半糖",
            ["order"],
            [order("桂花輕烏龍", "fresh_milk_tea", sugar="半糖")]),

        # B1. 對比: 桂花鮮奶茶 vs 桂花奶茶
        make_sample(sys_prompt,
            "兩杯桂花輕烏龍，一杯鮮奶茶半糖少冰，一杯奶茶微糖去冰",
            ["order"],
            [order("桂花輕烏龍", "fresh_milk_tea", sugar="半糖", ice="少冰"),
             order("桂花輕烏龍", "rich_milk_tea", sugar="微糖", ice="去冰")]),

        # B2. 對比: 三窨鮮奶茶大杯 vs 奶茶中杯 + 共用 ice
        make_sample(sys_prompt,
            "兩杯三窨十五茉，一杯鮮奶茶大杯無糖，一杯奶茶中杯半糖，都去冰",
            ["order"],
            [order("三窨十五茉", "fresh_milk_tea", size="L", sugar="無糖", ice="去冰"),
             order("三窨十五茉", "rich_milk_tea", size="M", sugar="半糖", ice="去冰")]),

        # B3. 對比: 金杯鮮奶茶 vs 金杯奶茶 (null specs)
        make_sample(sys_prompt,
            "一杯金杯蜜香紅鮮奶茶無糖，一杯金杯蜜香紅奶茶半糖",
            ["order"],
            [order("金杯蜜香紅", "fresh_milk_tea", sugar="無糖"),
             order("金杯蜜香紅", "rich_milk_tea", sugar="半糖")]),

        # C1. 兩杯同品項鮮奶茶不同規格
        make_sample(sys_prompt,
            "兩杯琥珀鐵觀音鮮奶茶，一杯半糖少冰，一杯無糖去冰",
            ["order"],
            [order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="少冰"),
             order("琥珀鐵觀音", "fresh_milk_tea", sugar="無糖", ice="去冰")]),

        # C2. 多輪: 鮮奶茶 + 改 spec
        make_sample(sys_prompt,
            "金杯蜜香紅鮮奶茶大杯半糖少冰;改無糖",
            ["order", "modify"],
            [order("金杯蜜香紅", "fresh_milk_tea", size="L", sugar="無糖", ice="少冰")]),

        # A7. 米香玉露菁鮮奶茶 (null spec, 補 null 佔比)
        make_sample(sys_prompt,
            "來杯米香玉露菁鮮奶茶",
            ["order"],
            [order("米香玉露菁", "fresh_milk_tea")]),
    ]

    # ================================================================
    # Valid 新增樣本 (3 筆)
    # ================================================================
    new_valid = [
        # V1. 金杯鮮奶茶 + size + spec
        make_sample(sys_prompt,
            "金杯蜜香紅鮮奶茶中杯微糖少冰",
            ["order"],
            [order("金杯蜜香紅", "fresh_milk_tea", size="M", sugar="微糖", ice="少冰")]),

        # V2. 對比: 琥珀鮮奶茶 vs 奶茶
        make_sample(sys_prompt,
            "兩杯琥珀鐵觀音，一杯鮮奶茶半糖少冰，一杯奶茶無糖去冰",
            ["order"],
            [order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="少冰"),
             order("琥珀鐵觀音", "rich_milk_tea", sugar="無糖", ice="去冰")]),

        # V3. 朱槿鮮奶茶 + size
        make_sample(sys_prompt,
            "朱槿普洱紅鮮奶茶大杯半糖去冰",
            ["order"],
            [order("朱槿普洱紅", "fresh_milk_tea", size="L", sugar="半糖", ice="去冰")]),
    ]

    # ================================================================
    # 合併並儲存
    # ================================================================
    train.extend(new_train)
    valid.extend(new_valid)

    save_jsonl(DATA_DIR / "train.jsonl", train)
    save_jsonl(DATA_DIR / "valid.jsonl", valid)

    print(f"新增: train +{len(new_train)}, valid +{len(new_valid)}")
    print(f"修正後: train={len(train)}, valid={len(valid)}, total={len(train)+len(valid)}")

    # ---- 影響分析 ----
    new_orders = sum(len(json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])["orders"])
                     for s in new_train + new_valid)
    new_sugar_null = sum(1 for s in new_train + new_valid
                         for o in json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])["orders"]
                         if o["sugar"] is None)
    new_ice_null = sum(1 for s in new_train + new_valid
                       for o in json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])["orders"]
                       if o["ice"] is None)
    new_size_null = sum(1 for s in new_train + new_valid
                        for o in json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])["orders"]
                        if o["size"] is None)
    new_fresh = sum(1 for s in new_train + new_valid
                    for o in json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])["orders"]
                    if o["category"] == "fresh_milk_tea")
    new_rich = sum(1 for s in new_train + new_valid
                   for o in json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])["orders"]
                   if o["category"] == "rich_milk_tea")

    print(f"\n--- 影響分析 ---")
    print(f"  新增 orders: {new_orders}")
    print(f"  fresh_milk_tea: {new_fresh}, rich_milk_tea: {new_rich}")
    print(f"  sugar null: {new_sugar_null}/{new_orders} = {new_sugar_null/new_orders*100:.0f}%")
    print(f"  ice null: {new_ice_null}/{new_orders} = {new_ice_null/new_orders*100:.0f}%")
    print(f"  size null: {new_size_null}/{new_orders} = {new_size_null/new_orders*100:.0f}%")


if __name__ == "__main__":
    main()
