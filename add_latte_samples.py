#!/usr/bin/env python3
"""Round 32: 新增「{品項}拿鐵 → fresh_milk_tea」樣本。

新增 10 筆 train + 2 筆 valid，教模型將「琥珀鐵觀音拿鐵」等
解析為 item=品項名, category=fresh_milk_tea。
"""

import json
import pathlib

TRAIN_PATH = pathlib.Path(__file__).parent / "data" / "train.jsonl"
VALID_PATH = pathlib.Path(__file__).parent / "data" / "valid.jsonl"


def get_system_prompt(path: str) -> str:
    """從現有 JSONL 第一行取得 system prompt。"""
    with open(path) as f:
        first = json.loads(f.readline())
    return first["messages"][0]["content"]


def make_sample(system: str, user: str, assistant: str) -> dict:
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ]
    }


def build_assistant(intents, orders, preferences=None, recommendations=None):
    return json.dumps(
        {
            "intents": intents,
            "orders": orders,
            "preferences": preferences or {},
            "recommendations": recommendations or [],
        },
        ensure_ascii=False,
    )


def order(item, category, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
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


def main():
    system = get_system_prompt(TRAIN_PATH)

    # === Train samples (10) ===
    train_samples = [
        # T1: 琥珀鐵觀音拿鐵 基本
        make_sample(
            system,
            "琥珀鐵觀音拿鐵半糖少冰",
            build_assistant(
                ["order"],
                [order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="少冰")],
            ),
        ),
        # T2: 桂花輕烏龍拿鐵 +size
        make_sample(
            system,
            "桂花輕烏龍拿鐵大杯無糖去冰",
            build_assistant(
                ["order"],
                [order("桂花輕烏龍", "fresh_milk_tea", size="L", sugar="無糖", ice="去冰")],
            ),
        ),
        # T3: 三窨十五茉拿鐵 null spec
        make_sample(
            system,
            "三窨十五茉拿鐵",
            build_assistant(
                ["order"],
                [order("三窨十五茉", "fresh_milk_tea")],
            ),
        ),
        # T4: 朱槿普洱紅拿鐵 基本
        make_sample(
            system,
            "朱槿普洱紅拿鐵微糖少冰",
            build_assistant(
                ["order"],
                [order("朱槿普洱紅", "fresh_milk_tea", sugar="微糖", ice="少冰")],
            ),
        ),
        # T5: 金杯蜜香紅拿鐵 +size
        make_sample(
            system,
            "金杯蜜香紅拿鐵中杯半糖去冰",
            build_assistant(
                ["order"],
                [order("金杯蜜香紅", "fresh_milk_tea", size="M", sugar="半糖", ice="去冰")],
            ),
        ),
        # T6: 米香玉露菁拿鐵 基本
        make_sample(
            system,
            "米香玉露菁拿鐵無糖去冰",
            build_assistant(
                ["order"],
                [order("米香玉露菁", "fresh_milk_tea", sugar="無糖", ice="去冰")],
            ),
        ),
        # T7: 茶花紅烏龍拿鐵 null spec
        make_sample(
            system,
            "茶花紅烏龍拿鐵",
            build_assistant(
                ["order"],
                [order("茶花紅烏龍", "fresh_milk_tea")],
            ),
        ),
        # T8: 對比 — 拿鐵 vs 奶茶
        make_sample(
            system,
            "一杯琥珀鐵觀音拿鐵大杯，一杯桂花輕烏龍奶茶中杯半糖",
            build_assistant(
                ["order"],
                [
                    order("琥珀鐵觀音", "fresh_milk_tea", size="L"),
                    order("桂花輕烏龍", "rich_milk_tea", size="M", sugar="半糖"),
                ],
            ),
        ),
        # T9: order+modify 多輪
        make_sample(
            system,
            "三窨十五茉拿鐵半糖少冰;改無糖",
            build_assistant(
                ["order", "modify"],
                [order("三窨十五茉", "fresh_milk_tea", sugar="無糖", ice="少冰")],
            ),
        ),
        # T10: other+order — 「拿鐵」照錄 → 追問後品項拿鐵
        make_sample(
            system,
            "一杯拿鐵;你們沒有？那金杯蜜香紅拿鐵半糖少冰",
            build_assistant(
                ["order", "order"],
                [order("金杯蜜香紅", "fresh_milk_tea", sugar="半糖", ice="少冰")],
            ),
        ),
    ]

    # === Valid samples (2) ===
    valid_samples = [
        # V1: 朱槿普洱紅拿鐵 +size
        make_sample(
            system,
            "朱槿普洱紅拿鐵大杯半糖去冰",
            build_assistant(
                ["order"],
                [order("朱槿普洱紅", "fresh_milk_tea", size="L", sugar="半糖", ice="去冰")],
            ),
        ),
        # V2: 拿鐵 vs 奶茶 對比
        make_sample(
            system,
            "兩杯米香玉露菁，一杯拿鐵半糖少冰一杯奶茶無糖去冰",
            build_assistant(
                ["order"],
                [
                    order("米香玉露菁", "fresh_milk_tea", sugar="半糖", ice="少冰"),
                    order("米香玉露菁", "rich_milk_tea", sugar="無糖", ice="去冰"),
                ],
            ),
        ),
    ]

    # Append to files
    added_train = 0
    with open(TRAIN_PATH, "a") as f:
        for s in train_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            added_train += 1

    added_valid = 0
    with open(VALID_PATH, "a") as f:
        for s in valid_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
            added_valid += 1

    print(f"Added {added_train} train + {added_valid} valid latte samples")

    # Verify counts
    train_count = sum(1 for _ in open(TRAIN_PATH))
    valid_count = sum(1 for _ in open(VALID_PATH))
    print(f"Total: {train_count} train + {valid_count} valid = {train_count + valid_count}")


if __name__ == "__main__":
    main()
