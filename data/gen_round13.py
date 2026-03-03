#!/usr/bin/env python3
"""
Round 13: 強化取消品項（cancel）場景
目標：補充 30+ 個「取消特定品項」的範例，讓模型學會從 orders 中移除被取消的品項
"""
import json

SYSTEM_PROMPT = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。\n\n"
    "菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、"
    "果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。\n\n"
    "純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，回傳 not_on_menu 欄位。\n\n"
    '輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null",'
    '"ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"unit_price":0,'
    '"note":""}],"total":0}'
)

def make(user_text, assistant_json):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(assistant_json, ensure_ascii=False)},
        ]
    }

examples = []

# ============================================================
# A. 取消第 N 杯（2杯點單，取消其中1杯）
# ============================================================

# A1: 取消第二杯
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：第二杯不要了",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# A2: 取消第一杯
examples.append(make(
    "顧客：一杯桂花輕烏龍鮮奶半糖少冰\n顧客：一杯鐵觀音鮮奶去冰微糖\n顧客：第一杯不要了",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# A3: 取消第二杯（不同品項）
examples.append(make(
    "顧客：鐵觀音鮮奶半糖少冰\n顧客：大杯桂花輕烏龍奶茶正常糖正常冰\n顧客：第二杯取消",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# A4: 取消第一杯（用「不用了」）
examples.append(make(
    "顧客：桂花輕烏龍純茶去冰無糖\n顧客：三窨十五茉鮮奶半糖少冰\n顧客：第一杯不用了",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# A5: 用品名取消
examples.append(make(
    "顧客：一杯桂花輕烏龍鮮奶半糖少冰\n顧客：一杯三窨十五茉純茶去冰無糖\n顧客：桂花那杯不要了",
    {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""}], "total": 45}
))

# A6: 取消鮮奶那杯
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：三窨十五茉純茶去冰無糖\n顧客：鮮奶那杯不要了",
    {"orders": [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""}], "total": 45}
))

# ============================================================
# B. 取消第 N 杯（3杯點單，取消其中1杯）
# ============================================================

# B1: 3杯取消第三杯
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍鮮奶微糖去冰\n顧客：鐵觀音純茶去冰無糖\n顧客：第三杯不要了",
    {"orders": [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}
    ], "total": 130}
))

# B2: 3杯取消第一杯
examples.append(make(
    "顧客：桂花輕烏龍純茶去冰無糖\n顧客：鐵觀音鮮奶半糖少冰\n顧客：三窨十五茉鮮奶微糖去冰\n顧客：第一杯取消",
    {"orders": [
        {"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""},
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}
    ], "total": 140}
))

# B3: 3杯取消第二杯
examples.append(make(
    "顧客：鐵觀音鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：大杯三窨十五茉奶茶正常糖少冰\n顧客：第二杯不用了",
    {"orders": [
        {"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""},
        {"item": "三窨十五茉", "category": "rich_milk_tea", "size": "L", "ice": "少冰", "sugar": "正常糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}
    ], "total": 150}
))

# ============================================================
# C. 取消全部
# ============================================================

# C1
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：算了不要了",
    {"orders": [], "total": 0, "note": "顧客取消所有品項"}
))

# C2
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：鐵觀音純茶去冰無糖\n顧客：都不要了",
    {"orders": [], "total": 0, "note": "顧客取消所有品項"}
))

# C3
examples.append(make(
    "顧客：三窨十五茉純茶去冰無糖\n顧客：還是不要好了",
    {"orders": [], "total": 0, "note": "顧客取消所有品項"}
))

# ============================================================
# D. 更多取消第 N 杯的變化表達
# ============================================================

# D1: 「幫我把第二杯拿掉」
examples.append(make(
    "顧客：一杯鐵觀音鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶無糖去冰\n顧客：幫我把第二杯拿掉",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# D2: 「最後那杯不要」
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：三窨十五茉純茶去冰無糖\n顧客：最後那杯不要",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# D3: 「純茶那杯取消」
examples.append(make(
    "顧客：三窨十五茉鮮奶微糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：純茶那杯取消",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# D4: 「鐵觀音不要了」
examples.append(make(
    "顧客：鐵觀音鮮奶半糖少冰\n顧客：桂花輕烏龍鮮奶微糖去冰\n顧客：鐵觀音不要了",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# D5: 「第一杯改成不要」
examples.append(make(
    "顧客：大杯三窨十五茉奶茶正常糖少冰\n顧客：鐵觀音鮮奶半糖去冰\n顧客：第一杯改成不要",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# D6: 「三窨十五茉那杯拿掉」
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：鐵觀音鮮奶微糖去冰\n顧客：桂花輕烏龍純茶無糖去冰\n顧客：三窨十五茉那杯拿掉",
    {"orders": [
        {"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""},
        {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 40, "note": ""}
    ], "total": 115}
))

# ============================================================
# E. 取消後又加新品項
# ============================================================

# E1
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：那杯不要了\n顧客：改一杯鐵觀音鮮奶微糖去冰",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# E2
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：第一杯不要了\n顧客：加一杯鐵觀音鮮奶微糖少冰",
    {"orders": [
        {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 40, "note": ""},
        {"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}
    ], "total": 115}
))

# ============================================================
# F. 更多混合 not_on_menu + cancel 場景
# ============================================================

# F1: 點了不在菜單的，然後取消
examples.append(make(
    "顧客：一杯珍珠奶茶\n顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：珍珠奶茶不要了",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# F2: 混合 not_on_menu（不取消）
examples.append(make(
    "一杯珍珠奶茶，一杯鐵觀音鮮奶半糖少冰",
    {"orders": [
        {"item": "珍珠奶茶", "not_on_menu": True, "note": "本店無此品項"},
        {"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}
    ], "total": 75}
))

# F3: 多個 not_on_menu
examples.append(make(
    "一杯珍珠奶茶，一杯波霸紅茶",
    {"orders": [
        {"item": "珍珠奶茶", "not_on_menu": True, "note": "本店無此品項"},
        {"item": "波霸紅茶", "not_on_menu": True, "note": "本店無此品項"}
    ], "total": 0}
))

# F4: not_on_menu + 正常品項 + 取消正常品項
examples.append(make(
    "顧客：一杯紅茶拿鐵\n顧客：一杯桂花輕烏龍鮮奶半糖少冰\n顧客：桂花那杯不要了",
    {"orders": [
        {"item": "紅茶拿鐵", "not_on_menu": True, "note": "本店無此品項"}
    ], "total": 0}
))

# F5: mixed not_on_menu（不同表達）
examples.append(make(
    "一杯烏龍拿鐵半糖少冰，一杯三窨十五茉鮮奶微糖去冰",
    {"orders": [
        {"item": "烏龍拿鐵", "not_on_menu": True, "note": "本店無此品項"},
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}
    ], "total": 65}
))

# F6: 抹茶拿鐵 not_on_menu
examples.append(make(
    "一杯抹茶拿鐵，一杯桂花輕烏龍鮮奶半糖少冰",
    {"orders": [
        {"item": "抹茶拿鐵", "not_on_menu": True, "note": "本店無此品項"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}
    ], "total": 65}
))

# ============================================================
# G. 取消 + 修改組合
# ============================================================

# G1: 取消一杯 + 修改另一杯
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍鮮奶微糖去冰\n顧客：第一杯不要了，第二杯改半糖",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# G2: 修改 + 取消
examples.append(make(
    "顧客：鐵觀音鮮奶半糖少冰\n顧客：三窨十五茉純茶去冰無糖\n顧客：鐵觀音改微糖，純茶不要了",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# ============================================================
# Write output
# ============================================================
output_path = "data/round13.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Generated {len(examples)} examples")
