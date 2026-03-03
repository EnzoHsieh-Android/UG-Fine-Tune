#!/usr/bin/env python3
"""
Round 19 — 全稱點單補強（精簡版）

問題：模型對「簡稱+分類詞」識別正確，但對「全稱」反而返回 not_on_menu。

策略：
- 減少數據量到 ~40 條（避免覆蓋原有能力）
- 只補充最關鍵的全稱場景
"""

import json
import random

SYSTEM_PROMPT = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。\n\n"
    "菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。\n\n"
    "純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，回傳 not_on_menu 欄位。\n\n"
    '輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}]}'
)

# 重點品項（之前測試失敗的）
KEY_ITEMS = [
    ("琥珀鐵觀音", ["fresh_milk_tea", "rich_milk_tea"]),
    ("金杯蜜香紅", ["fresh_milk_tea", "rich_milk_tea"]),
    ("三窨十五茉", ["pure_tea", "fresh_milk_tea", "rich_milk_tea"]),
    ("桂花輕烏龍", ["pure_tea", "fresh_milk_tea", "rich_milk_tea"]),
    ("茶花紅烏龍", ["pure_tea", "rich_milk_tea"]),
    ("朱槿普洱紅", ["pure_tea", "fresh_milk_tea"]),
]

SUGARS = ["正常糖", "少糖", "半糖", "微糖", "無糖"]
ICES = ["正常冰", "少冰", "微冰", "去冰", "熱飲"]

def make_sample(user_text, orders):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps({"orders": orders}, ensure_ascii=False)}
        ]
    }

def gen_order(item, category, sugar=None, ice=None, size=None, qty=1):
    if category in ["fresh_milk_tea", "rich_milk_tea", "cloud_velvet"]:
        size = size or "M"
    else:
        size = None
    return {
        "item": item,
        "category": category,
        "size": size,
        "ice": ice,
        "sugar": sugar,
        "addon": [],
        "qty": qty,
        "note": ""
    }

samples = []

# ============================================================
# 1. 每個重點品項的全稱點單（每個 2-3 條）
# ============================================================
for item, categories in KEY_ITEMS:
    cat = categories[0]  # 使用第一個分類

    # 基本全稱
    sugar = random.choice(SUGARS)
    ice = random.choice(ICES)
    samples.append(make_sample(
        f"{item}，{sugar}{ice}",
        [gen_order(item, cat, sugar=sugar, ice=ice)]
    ))

    # 帶「一杯」
    sugar = random.choice(SUGARS)
    ice = random.choice(ICES)
    samples.append(make_sample(
        f"一杯{item}，{sugar}{ice}",
        [gen_order(item, cat, sugar=sugar, ice=ice)]
    ))

# ============================================================
# 2. 全稱 + 明確分類詞（確保映射正確）
# ============================================================
explicit_samples = [
    ("琥珀鐵觀音鮮奶，半糖少冰", "琥珀鐵觀音", "fresh_milk_tea", "半糖", "少冰"),
    ("琥珀鐵觀音奶茶，無糖去冰", "琥珀鐵觀音", "rich_milk_tea", "無糖", "去冰"),
    ("金杯蜜香紅鮮奶，微糖微冰", "金杯蜜香紅", "fresh_milk_tea", "微糖", "微冰"),
    ("金杯蜜香紅奶茶，半糖少冰", "金杯蜜香紅", "rich_milk_tea", "半糖", "少冰"),
    ("三窨十五茉純茶，無糖去冰", "三窨十五茉", "pure_tea", "無糖", "去冰"),
    ("三窨十五茉鮮奶，半糖少冰", "三窨十五茉", "fresh_milk_tea", "半糖", "少冰"),
    ("桂花輕烏龍純茶，微糖去冰", "桂花輕烏龍", "pure_tea", "微糖", "去冰"),
    ("桂花輕烏龍鮮奶，無糖微冰", "桂花輕烏龍", "fresh_milk_tea", "無糖", "微冰"),
    ("茶花紅烏龍純茶，半糖去冰", "茶花紅烏龍", "pure_tea", "半糖", "去冰"),
    ("朱槿普洱紅純茶，無糖熱飲", "朱槿普洱紅", "pure_tea", "無糖", "熱飲"),
]

for user_text, item, cat, sugar, ice in explicit_samples:
    samples.append(make_sample(user_text, [gen_order(item, cat, sugar=sugar, ice=ice)]))

# ============================================================
# 3. 多杯全稱（少量）
# ============================================================
samples.append(make_sample(
    "兩杯琥珀鐵觀音，半糖少冰",
    [gen_order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="少冰", qty=2)]
))

samples.append(make_sample(
    "三杯金杯蜜香紅鮮奶，都無糖去冰",
    [gen_order("金杯蜜香紅", "fresh_milk_tea", sugar="無糖", ice="去冰", qty=3)]
))

# ============================================================
# 4. 全稱混合點單
# ============================================================
samples.append(make_sample(
    "一杯琥珀鐵觀音半糖少冰，一杯金杯蜜香紅無糖去冰",
    [
        gen_order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="少冰"),
        gen_order("金杯蜜香紅", "fresh_milk_tea", sugar="無糖", ice="去冰"),
    ]
))

samples.append(make_sample(
    "三窨十五茉鮮奶微糖微冰，還有桂花輕烏龍純茶無糖去冰",
    [
        gen_order("三窨十五茉", "fresh_milk_tea", sugar="微糖", ice="微冰"),
        gen_order("桂花輕烏龍", "pure_tea", sugar="無糖", ice="去冰"),
    ]
))

# ============================================================
# 5. 不帶甜度冰量的全稱（由店員確認）
# ============================================================
for item, categories in KEY_ITEMS[:3]:  # 只取前 3 個
    cat = categories[0]
    samples.append(make_sample(
        f"一杯{item}",
        [gen_order(item, cat, sugar=None, ice=None)]
    ))

# 輸出
random.shuffle(samples)
print(f"Generated {len(samples)} samples")

with open("data/round19.jsonl", "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print("Saved to data/round19.jsonl")
