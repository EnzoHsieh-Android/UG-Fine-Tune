#!/usr/bin/env python3
"""Round 34b 追加 — 雙份+單份混合 addon 補強（14 train + 3 valid）"""

import json
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/data"
with open(f"{DATA_DIR}/train.jsonl", "r") as f:
    first_line = json.loads(f.readline())
    SYSTEM_PROMPT = first_line["messages"][0]["content"]


def make_sample(user_text, assistant_json):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(assistant_json, ensure_ascii=False)},
        ]
    }


def order_entry(item, category=None, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
    return {
        "item": item, "category": category, "size": size,
        "ice": ice, "sugar": sugar, "addon": addon or [],
        "qty": qty, "note": note,
    }


def order_response(intents, orders):
    return {"intents": intents, "orders": orders, "preferences": {}, "recommendations": []}


# 變體軸：
#   品項 × 分類 × 措辭 × addon 順序（雙份茶凍+燕麥 / 雙份燕麥+茶凍）
#   確保每筆 user text 都不同

TRAIN = [
    # --- 雙份茶凍 + 單份燕麥（各種措辭）---
    make_sample("琥珀鐵觀音奶茶半糖少冰加雙份茶凍跟燕麥", order_response(
        ["order"],
        [order_entry("琥珀鐵觀音", "rich_milk_tea", sugar="半糖", ice="少冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("金杯蜜香紅鮮奶茶大杯加兩份茶凍跟一份燕麥粒", order_response(
        ["order"],
        [order_entry("金杯蜜香紅", "fresh_milk_tea", size="L",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("三窨十五茉奶茶無糖少冰加雙份紅烏龍茶凍再加燕麥", order_response(
        ["order"],
        [order_entry("三窨十五茉", "rich_milk_tea", sugar="無糖", ice="少冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("朱槿普洱紅奶茶中杯半糖加兩份茶凍還要一份燕麥", order_response(
        ["order"],
        [order_entry("朱槿普洱紅", "rich_milk_tea", size="M", sugar="半糖",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("茶花紅烏龍鮮奶茶去冰加雙份茶凍以及燕麥粒", order_response(
        ["order"],
        [order_entry("茶花紅烏龍", "fresh_milk_tea", ice="去冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("桂花輕烏龍奶茶大杯三分糖加雙份茶凍然後加燕麥", order_response(
        ["order"],
        [order_entry("桂花輕烏龍", "rich_milk_tea", size="L", sugar="三分糖",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("米香玉露菁鮮奶茶半糖微冰加兩份茶凍和燕麥粒", order_response(
        ["order"],
        [order_entry("米香玉露菁", "fresh_milk_tea", sugar="半糖", ice="微冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),

    # --- 雙份燕麥 + 單份茶凍（反向）---
    make_sample("琥珀鐵觀音鮮奶茶大杯無糖加雙份燕麥跟茶凍", order_response(
        ["order"],
        [order_entry("琥珀鐵觀音", "fresh_milk_tea", size="L", sugar="無糖",
                     addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])]
    )),
    make_sample("三窨十五茉鮮奶茶去冰加兩份燕麥粒還有茶凍", order_response(
        ["order"],
        [order_entry("三窨十五茉", "fresh_milk_tea", ice="去冰",
                     addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])]
    )),
    make_sample("茶花紅烏龍奶茶半糖少冰加雙份燕麥再加一份茶凍", order_response(
        ["order"],
        [order_entry("茶花紅烏龍", "rich_milk_tea", sugar="半糖", ice="少冰",
                     addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])]
    )),
    make_sample("金杯蜜香紅奶茶無糖去冰加兩份燕麥和一份紅烏龍茶凍", order_response(
        ["order"],
        [order_entry("金杯蜜香紅", "rich_milk_tea", sugar="無糖", ice="去冰",
                     addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])]
    )),

    # --- 更口語化的措辭 ---
    make_sample("桂花輕烏龍鮮奶茶半糖少冰，茶凍要雙份再加燕麥", order_response(
        ["order"],
        [order_entry("桂花輕烏龍", "fresh_milk_tea", sugar="半糖", ice="少冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("朱槿普洱紅鮮奶茶大杯，燕麥粒兩份加一份茶凍", order_response(
        ["order"],
        [order_entry("朱槿普洱紅", "fresh_milk_tea", size="L",
                     addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])]
    )),
    make_sample("米香玉露菁奶茶無糖去冰，茶凍兩份燕麥一份", order_response(
        ["order"],
        [order_entry("米香玉露菁", "rich_milk_tea", sugar="無糖", ice="去冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
]

VALID = [
    make_sample("琥珀鐵觀音鮮奶茶中杯半糖加雙份茶凍和燕麥粒", order_response(
        ["order"],
        [order_entry("琥珀鐵觀音", "fresh_milk_tea", size="M", sugar="半糖",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("金杯蜜香紅鮮奶茶少冰加兩份燕麥還要茶凍", order_response(
        ["order"],
        [order_entry("金杯蜜香紅", "fresh_milk_tea", ice="少冰",
                     addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])]
    )),
    make_sample("桂花輕烏龍奶茶無糖去冰，茶凍雙份再加一份燕麥粒", order_response(
        ["order"],
        [order_entry("桂花輕烏龍", "rich_milk_tea", sugar="無糖", ice="去冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
]


def main():
    train_file = f"{DATA_DIR}/train.jsonl"
    valid_file = f"{DATA_DIR}/valid.jsonl"

    with open(train_file, "a") as f:
        for s in TRAIN:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(valid_file, "a") as f:
        for s in VALID:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    train_total = sum(1 for _ in open(train_file))
    valid_total = sum(1 for _ in open(valid_file))

    print(f"Round 34b 雙份 addon 補強完成")
    print(f"  新增: +{len(TRAIN)} train, +{len(VALID)} valid")
    print(f"  新總量: {train_total} train + {valid_total} valid = {train_total + valid_total}")

    # 統計雙份 addon 總覆蓋
    count = 0
    with open(train_file) as f:
        for line in f:
            d = json.loads(line)
            asst = json.loads(d["messages"][2]["content"])
            for o in asst.get("orders", []):
                if len(o.get("addon", [])) == 3:
                    count += 1
                    break
    print(f"  雙份混合 addon（train）: {count} 筆")


if __name__ == "__main__":
    main()
