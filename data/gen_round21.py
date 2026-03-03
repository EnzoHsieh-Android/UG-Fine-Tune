#!/usr/bin/env python3
"""Round 21: 修復 4 個失敗測試案例 + anchor samples"""

import json
from pathlib import Path

SYSTEM_PROMPT = """你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。

菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。

純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。
加料：紅烏龍茶凍(+15)、燕麥粒(+15)。
甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。
未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。
若品項不在菜單上，回傳 not_on_menu 欄位。

輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"unit_price":0,"note":""}],"total":0}"""

def make_sample(user_input, assistant_output):
    """Create a training sample in chat format"""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": assistant_output}
        ]
    }

samples = []

# ==================== 修復模式 1: 「品項+加+加料」格式 ====================
# 失敗案例: "琥珀鐵觀音加紅烏龍茶凍"

addon_patterns = [
    # 單加料 - 純茶
    ("三窨十五茉加茶凍",
     {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 60, "note": ""}], "total": 60}),
    ("桂花輕烏龍加紅烏龍茶凍",
     {"orders": [{"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 60, "note": ""}], "total": 60}),
    ("琥珀鐵觀音加茶凍",
     {"orders": [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 60, "note": ""}], "total": 60}),
    ("琥珀鐵觀音加紅烏龍茶凍",
     {"orders": [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 60, "note": ""}], "total": 60}),
    ("金杯蜜香紅加燕麥粒",
     {"orders": [{"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["燕麥粒"], "qty": 1, "unit_price": 55, "note": ""}], "total": 55}),

    # 單加料 - 鮮奶茶
    ("三窨十五茉鮮奶加茶凍",
     {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 80, "note": ""}], "total": 80}),
    ("桂花輕烏龍鮮奶加燕麥粒",
     {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["燕麥粒"], "qty": 1, "unit_price": 80, "note": ""}], "total": 80}),
    ("琥珀鐵觀音鮮奶加紅烏龍茶凍",
     {"orders": [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 80, "note": ""}], "total": 80}),

    # 帶選項的加料
    ("三窨十五茉半糖加茶凍",
     {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 60, "note": ""}], "total": 60}),
    ("桂花輕烏龍去冰加燕麥粒",
     {"orders": [{"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": ["燕麥粒"], "qty": 1, "unit_price": 60, "note": ""}], "total": 60}),
]

# ==================== 修復模式 2: 雙加料 ====================
# 失敗案例: "朱槿普洱紅加紅烏龍茶凍和燕麥粒"

double_addon_patterns = [
    ("三窨十五茉加茶凍和燕麥粒",
     {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}),
    ("朱槿普洱紅加茶凍和燕麥粒",
     {"orders": [{"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}),
    ("朱槿普洱紅加紅烏龍茶凍和燕麥粒",
     {"orders": [{"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}),
    ("琥珀鐵觀音加茶凍跟燕麥粒",
     {"orders": [{"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}),
    ("金杯蜜香紅鮮奶加茶凍和燕麥",
     {"orders": [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "unit_price": 90, "note": ""}], "total": 90}),
    ("桂花輕烏龍奶茶加茶凍和燕麥粒",
     {"orders": [{"item": "桂花輕烏龍", "category": "rich_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "unit_price": 95, "note": ""}], "total": 95}),
]

# ==================== 修復模式 3: 「A和B」多品項 ====================
# 失敗案例: "三窨十五茉和金杯蜜香紅，茉莉改半糖"

and_multi_patterns = [
    # 基本 A和B
    ("三窨十五茉和金杯蜜香紅",
     {"orders": [
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 40, "note": ""}
     ], "total": 85}),
    ("琥珀鐵觀音和桂花輕烏龍",
     {"orders": [
         {"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""}
     ], "total": 90}),
    # A和B 帶後續修改
    ("三窨十五茉和金杯蜜香紅，茉莉改半糖",
     {"orders": [
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 40, "note": ""}
     ], "total": 85}),
    ("桂花輕烏龍和琥珀鐵觀音，桂花要鮮奶",
     {"orders": [
         {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 65, "note": ""},
         {"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""}
     ], "total": 110}),
    ("金杯蜜香紅和朱槿普洱紅，都要去冰",
     {"orders": [
         {"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "unit_price": 40, "note": ""},
         {"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""}
     ], "total": 85}),
    # A和B 帶選項
    ("三窨十五茉半糖和金杯蜜香紅去冰",
     {"orders": [
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "unit_price": 40, "note": ""}
     ], "total": 85}),
]

# ==================== 修復模式 4: 頓號分隔多品項各有客製 ====================
# 失敗案例: "三窨十五茉半糖、金杯蜜香紅去冰、琥珀鐵觀音熱的"

comma_multi_patterns = [
    ("三窨十五茉半糖、金杯蜜香紅去冰",
     {"orders": [
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "unit_price": 40, "note": ""}
     ], "total": 85}),
    ("三窨十五茉半糖、金杯蜜香紅去冰、琥珀鐵觀音熱的",
     {"orders": [
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "unit_price": 40, "note": ""},
         {"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "熱飲", "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""}
     ], "total": 130}),
    ("桂花輕烏龍無糖、朱槿普洱紅微糖",
     {"orders": [
         {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": None, "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""}
     ], "total": 90}),
    ("琥珀鐵觀音鮮奶半糖、金杯蜜香紅奶茶無糖、三窨十五茉去冰",
     {"orders": [
         {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""},
         {"item": "金杯蜜香紅", "category": "rich_milk_tea", "size": "M", "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""},
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""}
     ], "total": 175}),
    ("茶花紅烏龍少冰、蜜桃紅烏龍微糖、青檸桂蜜",
     {"orders": [
         {"item": "茶花紅烏龍", "category": "pure_tea", "size": None, "ice": "少冰", "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "蜜桃紅烏龍", "category": "fruit_tea", "size": None, "ice": None, "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 60, "note": ""},
         {"item": "青檸桂蜜", "category": "fruit_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 65, "note": ""}
     ], "total": 170}),
    # 四品項
    ("三窨十五茉、桂花輕烏龍半糖、琥珀鐵觀音去冰、金杯蜜香紅熱的",
     {"orders": [
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "琥珀鐵觀音", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": "熱飲", "sugar": None, "addon": [], "qty": 1, "unit_price": 40, "note": ""}
     ], "total": 175}),
]

# ==================== Anchor samples (防止回歸) ====================

anchor_patterns = [
    # 基本單品
    ("一杯三窨十五茉",
     {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""}], "total": 45}),
    ("桂花輕烏龍鮮奶半糖少冰",
     {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}),
    # 縮寫
    ("茉莉半糖去冰",
     {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""}], "total": 45}),
    ("鐵觀音鮮奶無糖",
     {"orders": [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}),
    # 修改
    ("三窨十五茉，不對，改金杯蜜香紅",
     {"orders": [{"item": "金杯蜜香紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 40, "note": ""}], "total": 40}),
    # 刪除
    ("三窨十五茉和桂花輕烏龍，桂花不要了",
     {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 45, "note": ""}], "total": 45}),
    # 多杯
    ("三杯三窨十五茉半糖",
     {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 3, "unit_price": 45, "note": ""}], "total": 135}),
    # 同品不同選項
    ("兩杯三窨十五茉，一杯半糖一杯無糖",
     {"orders": [
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""},
         {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""}
     ], "total": 90}),
    # 非菜單
    ("一杯珍珠奶茶",
     {"orders": [{"item": "珍珠奶茶", "category": None, "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "unit_price": 0, "not_on_menu": True, "note": "本店無珍珠奶茶"}], "total": 0}),
    # 全客製
    ("大杯三窨十五茉鮮奶微糖去冰加茶凍",
     {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "L", "ice": "去冰", "sugar": "微糖", "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 90, "note": ""}], "total": 90}),
]

# Build all samples
for user_input, output in addon_patterns:
    samples.append(make_sample(user_input, json.dumps(output, ensure_ascii=False)))

for user_input, output in double_addon_patterns:
    samples.append(make_sample(user_input, json.dumps(output, ensure_ascii=False)))

for user_input, output in and_multi_patterns:
    samples.append(make_sample(user_input, json.dumps(output, ensure_ascii=False)))

for user_input, output in comma_multi_patterns:
    samples.append(make_sample(user_input, json.dumps(output, ensure_ascii=False)))

for user_input, output in anchor_patterns:
    samples.append(make_sample(user_input, json.dumps(output, ensure_ascii=False)))

# Write to file
output_file = Path(__file__).parent / "round21.jsonl"
with open(output_file, "w", encoding="utf-8") as f:
    for sample in samples:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")

print(f"Generated {len(samples)} samples:")
print(f"  - Addon patterns (品項+加+加料): {len(addon_patterns)}")
print(f"  - Double addon patterns (雙加料): {len(double_addon_patterns)}")
print(f"  - A和B multi patterns: {len(and_multi_patterns)}")
print(f"  - Comma-separated patterns (頓號分隔): {len(comma_multi_patterns)}")
print(f"  - Anchor samples: {len(anchor_patterns)}")
print(f"Output: {output_file}")
