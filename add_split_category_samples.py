#!/usr/bin/env python3
"""
新增「N杯同品項分拆不同分類」訓練樣本。
重點: 朱槿普洱紅、米香玉露菁（underrepresented）。
兼顧 sugar/ice null ~40%、size null ~85%。
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
    # 重點: 朱槿普洱紅 x4, 米香玉露菁 x3, 金杯蜜香紅 x2, 茶花紅烏龍 x2, 桂花輕烏龍 x1
    # ================================================================
    new_train = [
        # 1. 朱槿普洱紅: "三杯...兩杯純茶一杯鮮奶" + 共用 spec
        make_sample(sys_prompt,
            "三杯朱槿普洱紅，兩杯純茶一杯鮮奶，都去冰無糖",
            ["order"],
            [order("朱槿普洱紅", "pure_tea", ice="去冰", sugar="無糖", qty=2),
             order("朱槿普洱紅", "fresh_milk_tea", ice="去冰", sugar="無糖")]),

        # 2. 米香玉露菁: "兩杯...鮮奶的/奶茶的" + 各自 spec
        make_sample(sys_prompt,
            "兩杯米香玉露菁，鮮奶的半糖少冰，奶茶的無糖去冰",
            ["order"],
            [order("米香玉露菁", "fresh_milk_tea", sugar="半糖", ice="少冰"),
             order("米香玉露菁", "rich_milk_tea", sugar="無糖", ice="去冰")]),

        # 3. 茶花紅烏龍: "三杯...純茶/鮮奶/奶蓋各一杯" + 共用
        make_sample(sys_prompt,
            "三杯茶花紅烏龍，純茶一杯、鮮奶一杯、奶蓋一杯，都無糖",
            ["order"],
            [order("茶花紅烏龍", "pure_tea", sugar="無糖"),
             order("茶花紅烏龍", "fresh_milk_tea", sugar="無糖"),
             order("茶花紅烏龍", "cloud_velvet", sugar="無糖")]),

        # 4. 金杯蜜香紅: "兩杯...鮮奶大杯/奶茶中杯" + 各自 size+spec
        make_sample(sys_prompt,
            "兩杯金杯蜜香紅，鮮奶的大杯半糖去冰，奶茶的中杯無糖少冰",
            ["order"],
            [order("金杯蜜香紅", "fresh_milk_tea", size="L", sugar="半糖", ice="去冰"),
             order("金杯蜜香紅", "rich_milk_tea", size="M", sugar="無糖", ice="少冰")]),

        # 5. 朱槿普洱紅: "兩杯...一杯加鮮奶/一杯純茶" + size
        make_sample(sys_prompt,
            "兩杯朱槿普洱紅，一杯加鮮奶中杯微糖少冰，一杯純茶去冰",
            ["order"],
            [order("朱槿普洱紅", "fresh_milk_tea", size="M", sugar="微糖", ice="少冰"),
             order("朱槿普洱紅", "pure_tea", ice="去冰")]),

        # 6. 米香玉露菁: "三杯...兩杯鮮奶一杯奶茶" + 共用 spec
        make_sample(sys_prompt,
            "三杯米香玉露菁，兩杯鮮奶茶半糖少冰、一杯奶茶無糖去冰",
            ["order"],
            [order("米香玉露菁", "fresh_milk_tea", sugar="半糖", ice="少冰", qty=2),
             order("米香玉露菁", "rich_milk_tea", sugar="無糖", ice="去冰")]),

        # 7. 茶花紅烏龍: "兩杯...奶蓋/鮮奶" + 各自 spec + size
        make_sample(sys_prompt,
            "兩杯茶花紅烏龍，一杯奶蓋微糖、一杯鮮奶大杯半糖少冰",
            ["order"],
            [order("茶花紅烏龍", "cloud_velvet", sugar="微糖"),
             order("茶花紅烏龍", "fresh_milk_tea", size="L", sugar="半糖", ice="少冰")]),

        # 8. 朱槿普洱紅: "三杯...純茶/鮮奶/奶茶" + 各自完整 spec
        make_sample(sys_prompt,
            "三杯朱槿普洱紅，一杯純茶無糖去冰、一杯鮮奶中杯半糖少冰、一杯奶茶大杯微糖",
            ["order"],
            [order("朱槿普洱紅", "pure_tea", sugar="無糖", ice="去冰"),
             order("朱槿普洱紅", "fresh_milk_tea", size="M", sugar="半糖", ice="少冰"),
             order("朱槿普洱紅", "rich_milk_tea", size="L", sugar="微糖")]),

        # 9. 米香玉露菁: "兩杯...鮮奶的/純茶的" + null spec
        make_sample(sys_prompt,
            "兩杯米香玉露菁，鮮奶的微糖微冰、純茶的無糖去冰",
            ["order"],
            [order("米香玉露菁", "fresh_milk_tea", sugar="微糖", ice="微冰"),
             order("米香玉露菁", "pure_tea", sugar="無糖", ice="去冰")]),

        # 10. 金杯蜜香紅: "三杯...一杯鮮奶大杯/兩杯奶茶" + 部分 null
        make_sample(sys_prompt,
            "三杯金杯蜜香紅，一杯鮮奶大杯半糖、兩杯奶茶少冰",
            ["order"],
            [order("金杯蜜香紅", "fresh_milk_tea", size="L", sugar="半糖"),
             order("金杯蜜香紅", "rich_milk_tea", ice="少冰", qty=2)]),

        # 11. 朱槿普洱紅: 多段 "朱槿普洱紅鮮奶;再一杯純茶的"
        make_sample(sys_prompt,
            "朱槿普洱紅鮮奶半糖少冰;再一杯純茶的無糖去冰",
            ["order", "order"],
            [order("朱槿普洱紅", "fresh_milk_tea", sugar="半糖", ice="少冰"),
             order("朱槿普洱紅", "pure_tea", sugar="無糖", ice="去冰")]),

        # 12. 桂花輕烏龍: "四杯...純茶/鮮奶/奶茶/奶蓋" + 都無糖
        make_sample(sys_prompt,
            "四杯桂花輕烏龍，純茶去冰、鮮奶中杯少冰、奶茶大杯微冰、奶蓋去冰，都無糖",
            ["order"],
            [order("桂花輕烏龍", "pure_tea", sugar="無糖", ice="去冰"),
             order("桂花輕烏龍", "fresh_milk_tea", size="M", sugar="無糖", ice="少冰"),
             order("桂花輕烏龍", "rich_milk_tea", size="L", sugar="無糖", ice="微冰"),
             order("桂花輕烏龍", "cloud_velvet", sugar="無糖", ice="去冰")]),
    ]

    # ================================================================
    # Valid 新增樣本 (3 筆)
    # ================================================================
    new_valid = [
        # V1. 朱槿普洱紅: "兩杯...一杯鮮奶一杯奶茶" + 共用 spec
        make_sample(sys_prompt,
            "兩杯朱槿普洱紅，一杯鮮奶半糖一杯奶茶無糖，都去冰",
            ["order"],
            [order("朱槿普洱紅", "fresh_milk_tea", sugar="半糖", ice="去冰"),
             order("朱槿普洱紅", "rich_milk_tea", sugar="無糖", ice="去冰")]),

        # V2. 米香玉露菁: "三杯...純茶/鮮奶/奶茶"
        make_sample(sys_prompt,
            "三杯米香玉露菁，純茶一杯去冰無糖、鮮奶一杯大杯半糖少冰、奶茶一杯中杯微糖",
            ["order"],
            [order("米香玉露菁", "pure_tea", ice="去冰", sugar="無糖"),
             order("米香玉露菁", "fresh_milk_tea", size="L", sugar="半糖", ice="少冰"),
             order("米香玉露菁", "rich_milk_tea", size="M", sugar="微糖")]),

        # V3. 茶花紅烏龍: "兩杯...純茶/奶蓋" + 共用
        make_sample(sys_prompt,
            "兩杯茶花紅烏龍，一杯純茶一杯奶蓋，都無糖去冰",
            ["order"],
            [order("茶花紅烏龍", "pure_tea", sugar="無糖", ice="去冰"),
             order("茶花紅烏龍", "cloud_velvet", sugar="無糖", ice="去冰")]),
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

    print(f"\n--- 影響分析 ---")
    print(f"  新增 orders: {new_orders}")
    print(f"  新增 sugar null: {new_sugar_null}/{new_orders} = {new_sugar_null/new_orders*100:.0f}%")
    print(f"  新增 ice null: {new_ice_null}/{new_orders} = {new_ice_null/new_orders*100:.0f}%")
    print(f"  新增 size null: {new_size_null}/{new_orders} = {new_size_null/new_orders*100:.0f}%")

    # Item count impact
    item_delta = {}
    for s in new_train + new_valid:
        data = json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])
        for o in data["orders"]:
            item = o["item"]
            qty = o.get("qty", 1)
            item_delta[item] = item_delta.get(item, 0) + qty
    print(f"  品項增量: {item_delta}")


if __name__ == "__main__":
    main()
