#!/usr/bin/env python3
"""Round 22: 修復加料模式 - 避免「紅烏龍茶凍」混入品名"""

import json

SYSTEM_PROMPT = """你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。

菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。

純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。
加料：紅烏龍茶凍(+15)、燕麥粒(+15)。
甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。
未指定甜度或冰量時設為 正常糖/正常冰。未指定尺寸的鮮奶茶/奶茶預設 M。
若品項不在菜單上，回傳 not_on_menu 欄位。

輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}]}"""

# 菜單品項
MENU_ITEMS = [
    ("三窨十五茉", "pure_tea"),
    ("桂花輕烏龍", "pure_tea"),
    ("琥珀鐵觀音", "pure_tea"),  # 重點品項
    ("金杯蜜香紅", "pure_tea"),
    ("朱槿普洱紅", "pure_tea"),
    ("米香玉露菁", "pure_tea"),
    ("茶花紅烏龍", "pure_tea"),
]

def make_sample(user_input, orders):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": json.dumps({"orders": orders}, ensure_ascii=False)}
        ]
    }

samples = []

# === 1. 各品項 + 加紅烏龍茶凍 (重點：品名不應包含「紅烏龍」) ===
addon_patterns = [
    # 琥珀鐵觀音 (最容易出錯)
    ("琥珀鐵觀音加紅烏龍茶凍", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("琥珀鐵觀音加茶凍", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("鐵觀音加紅烏龍茶凍", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("鐵觀音加茶凍", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("琥珀鐵觀音加茶凍半糖", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "半糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("琥珀鐵觀音加紅烏龍茶凍去冰", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),

    # 其他品項 + 茶凍
    ("三窨十五茉加紅烏龍茶凍", [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("茉莉加茶凍", [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("桂花輕烏龍加紅烏龍茶凍", [{"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("桂花加茶凍", [{"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("金杯蜜香紅加紅烏龍茶凍", [{"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("金杯加茶凍", [{"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("朱槿普洱紅加紅烏龍茶凍", [{"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("普洱加茶凍", [{"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),

    # 茶花紅烏龍 (品名本身含「紅烏龍」，更需要區分)
    ("茶花紅烏龍加紅烏龍茶凍", [{"item": "茶花紅烏龍", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("茶花紅烏龍加茶凍", [{"item": "茶花紅烏龍", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
]

for user_input, orders in addon_patterns:
    samples.append(make_sample(user_input, orders))

# === 2. 鮮奶茶/奶茶類別 + 茶凍 ===
milk_tea_addon = [
    ("琥珀鐵觀音鮮奶加茶凍", [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("琥珀鐵觀音奶茶加紅烏龍茶凍", [{"item": "琥珀鐵觀音", "category": "rich_milk_tea", "size": "M", "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("金杯蜜香紅鮮奶加茶凍", [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
    ("桂花輕烏龍奶茶加茶凍", [{"item": "桂花輕烏龍", "category": "rich_milk_tea", "size": "M", "ice": "正常冰", "sugar": "正常糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]),
]

for user_input, orders in milk_tea_addon:
    samples.append(make_sample(user_input, orders))

# === 3. Anchor 樣本 (防止回歸) ===
anchors = [
    # 基本單品
    ("一杯三窨十五茉", [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": [], "qty": 1, "note": ""}]),
    ("琥珀鐵觀音", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": [], "qty": 1, "note": ""}]),
    ("茶花紅烏龍", [{"item": "茶花紅烏龍", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": [], "qty": 1, "note": ""}]),
    # 縮寫
    ("鐵觀音半糖", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""}]),
    # 多品項
    ("琥珀鐵觀音和金杯蜜香紅", [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": [], "qty": 1, "note": ""}, {"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": [], "qty": 1, "note": ""}]),
]

for user_input, orders in anchors:
    samples.append(make_sample(user_input, orders))

# 輸出
print(f"生成 {len(samples)} 筆 Round 22 訓練資料")
with open("/Users/xiechengru/ug-finetune/data/round22.jsonl", "w", encoding="utf-8") as f:
    for s in samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print("已儲存至 round22.jsonl")
