#!/usr/bin/env python3
"""Round 32: 新增「雙份 addon」樣本。

新增 6 筆 train + 2 筆 valid，教模型將「雙份茶凍」「兩份燕麥」
解析為重複陣列元素，如 ["紅烏龍茶凍", "紅烏龍茶凍"]。
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

    # === Train samples (6) ===
    train_samples = [
        # T1: 雙份茶凍
        make_sample(
            system,
            "琥珀鐵觀音鮮奶茶大杯半糖少冰加雙份茶凍",
            build_assistant(
                ["order"],
                [order("琥珀鐵觀音", "fresh_milk_tea", size="L", sugar="半糖", ice="少冰",
                       addon=["紅烏龍茶凍", "紅烏龍茶凍"])],
            ),
        ),
        # T2: 兩份燕麥粒
        make_sample(
            system,
            "三窨十五茉奶茶加兩份燕麥粒",
            build_assistant(
                ["order"],
                [order("三窨十五茉", "rich_milk_tea",
                       addon=["燕麥粒", "燕麥粒"])],
            ),
        ),
        # T3: 雙份+單份混合
        make_sample(
            system,
            "桂花輕烏龍鮮奶茶中杯無糖去冰加雙份茶凍和燕麥",
            build_assistant(
                ["order"],
                [order("桂花輕烏龍", "fresh_milk_tea", size="M", sugar="無糖", ice="去冰",
                       addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])],
            ),
        ),
        # T4: 都雙份
        make_sample(
            system,
            "金杯蜜香紅鮮奶茶半糖少冰加兩份茶凍兩份燕麥",
            build_assistant(
                ["order"],
                [order("金杯蜜香紅", "fresh_milk_tea", sugar="半糖", ice="少冰",
                       addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒", "燕麥粒"])],
            ),
        ),
        # T5: cloud_velvet + 雙份茶凍
        make_sample(
            system,
            "茶花紅烏龍奶蓋加雙份茶凍",
            build_assistant(
                ["order"],
                [order("茶花紅烏龍", "cloud_velvet",
                       addon=["紅烏龍茶凍", "紅烏龍茶凍"])],
            ),
        ),
        # T6: 雙份燕麥粒
        make_sample(
            system,
            "朱槿普洱紅鮮奶茶大杯微糖少冰加雙份燕麥粒",
            build_assistant(
                ["order"],
                [order("朱槿普洱紅", "fresh_milk_tea", size="L", sugar="微糖", ice="少冰",
                       addon=["燕麥粒", "燕麥粒"])],
            ),
        ),
    ]

    # === Valid samples (2) ===
    valid_samples = [
        # V1: 雙份茶凍
        make_sample(
            system,
            "米香玉露菁鮮奶茶半糖少冰加雙份茶凍",
            build_assistant(
                ["order"],
                [order("米香玉露菁", "fresh_milk_tea", sugar="半糖", ice="少冰",
                       addon=["紅烏龍茶凍", "紅烏龍茶凍"])],
            ),
        ),
        # V2: 兩份燕麥
        make_sample(
            system,
            "琥珀鐵觀音奶茶大杯無糖去冰加兩份燕麥",
            build_assistant(
                ["order"],
                [order("琥珀鐵觀音", "rich_milk_tea", size="L", sugar="無糖", ice="去冰",
                       addon=["燕麥粒", "燕麥粒"])],
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

    print(f"Added {added_train} train + {added_valid} valid double-addon samples")

    # Verify counts
    train_count = sum(1 for _ in open(TRAIN_PATH))
    valid_count = sum(1 for _ in open(VALID_PATH))
    print(f"Total: {train_count} train + {valid_count} valid = {train_count + valid_count}")


if __name__ == "__main__":
    main()
