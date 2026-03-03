#!/usr/bin/env python3
"""
Round 12 (data round): 大量補強 cancel 和 modification with "第X杯" 指稱
目標：cancel 範例提升到 50+ 筆，modification "第X杯改" 提升到 30+ 筆
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

def make(user, assistant):
    return json.dumps({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": json.dumps(assistant, ensure_ascii=False)},
        ]
    }, ensure_ascii=False)

examples = []

# ============================================================
# CANCEL - "第X杯不要了" 模式（最關鍵）
# ============================================================

# === 2 杯取消第 2 杯（各種品項組合）===
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：第二杯不要了",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))
examples.append(make(
    "顧客：一杯紅玉紅茶鮮奶微糖去冰\n顧客：一杯桂花輕烏龍奶茶半糖少冰\n顧客：第二杯不要了",
    {"orders": [{"item": "紅玉紅茶", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))
examples.append(make(
    "顧客：一杯鐵觀音鮮奶半糖少冰\n顧客：一杯三窨十五茉純茶無糖去冰\n顧客：第二杯不要了",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖微冰\n顧客：紅玉紅茶純茶去冰無糖\n顧客：第二杯不要",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "微冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# === 2 杯取消第 1 杯 ===
examples.append(make(
    "顧客：一杯桂花輕烏龍鮮奶半糖少冰\n顧客：一杯紅玉紅茶純茶去冰無糖\n顧客：第一杯不要了",
    {"orders": [{"item": "紅玉紅茶", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 55, "note": ""}], "total": 55}
))
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：鐵觀音奶茶微糖微冰\n顧客：第一杯不要了",
    {"orders": [{"item": "鐵觀音", "category": "rich_milk_tea", "size": "M", "ice": "微冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))
examples.append(make(
    "顧客：一杯紅玉紅茶鮮奶少糖少冰\n顧客：一杯三窨十五茉鮮奶半糖微冰\n顧客：第一杯不要",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "微冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# === 3 杯取消中間 ===
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：紅玉紅茶鮮奶微糖微冰\n顧客：第二杯不要了",
    {"orders": [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""},
        {"item": "紅玉紅茶", "category": "fresh_milk_tea", "size": "M", "ice": "微冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}
    ], "total": 140}
))
examples.append(make(
    "顧客：鐵觀音鮮奶半糖少冰\n顧客：桂花輕烏龍奶茶微糖去冰\n顧客：三窨十五茉純茶無糖去冰\n顧客：第二杯不要",
    {"orders": [
        {"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""},
        {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 45, "note": ""}
    ], "total": 120}
))

# === 用「取消」 ===
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：取消第二杯",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))
examples.append(make(
    "顧客：紅玉紅茶鮮奶微糖去冰\n顧客：三窨十五茉鮮奶半糖少冰\n顧客：取消第一杯",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# === 用品名指定取消 ===
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：桂花那杯不要了",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))
examples.append(make(
    "顧客：紅玉紅茶鮮奶微糖少冰\n顧客：鐵觀音鮮奶半糖去冰\n顧客：紅玉那杯取消",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：三窨十五茉奶茶微糖微冰\n顧客：三窨那杯不用了",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# === 「不用了」「算了」 ===
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯紅玉紅茶純茶去冰無糖\n顧客：第二杯算了不用了",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))
examples.append(make(
    "顧客：鐵觀音鮮奶半糖少冰\n顧客：桂花輕烏龍鮮奶微糖微冰\n顧客：第一杯算了",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "微冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# === 全部取消 ===
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：都不要了",
    {"orders": [], "total": 0, "note": "顧客取消所有品項"}
))
examples.append(make(
    "顧客：一杯紅玉紅茶鮮奶微糖去冰\n顧客：全部取消",
    {"orders": [], "total": 0, "note": "顧客取消所有品項"}
))
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：不點了",
    {"orders": [], "total": 0, "note": "顧客取消所有品項"}
))

# === 取消最後一杯 ===
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：紅玉紅茶純茶去冰無糖\n顧客：桂花輕烏龍奶茶微糖微冰\n顧客：最後一杯不要了",
    {"orders": [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""},
        {"item": "紅玉紅茶", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 55, "note": ""}
    ], "total": 120}
))

# === 取消後再點別的 ===
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：第一杯不要了\n顧客：換桂花輕烏龍鮮奶半糖少冰",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# ============================================================
# MODIFICATION - "第X杯改..." 模式
# ============================================================

# === 第一杯改甜度 ===
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：第一杯改微糖",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))
examples.append(make(
    "顧客：一杯桂花輕烏龍鮮奶半糖少冰\n顧客：第一杯改無糖",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))
examples.append(make(
    "顧客：一杯紅玉紅茶鮮奶微糖去冰\n顧客：第一杯改半糖",
    {"orders": [{"item": "紅玉紅茶", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# === 第一杯改冰量 ===
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：第一杯改去冰",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))

# === 第二杯改 ===
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍鮮奶半糖少冰\n顧客：第二杯改微糖",
    {"orders": [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}
    ], "total": 130}
))
examples.append(make(
    "顧客：一杯紅玉紅茶鮮奶微糖少冰\n顧客：一杯鐵觀音鮮奶半糖去冰\n顧客：第二杯改無糖",
    {"orders": [
        {"item": "紅玉紅茶", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""},
        {"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}
    ], "total": 150}
))

# === 第X杯改尺寸 ===
examples.append(make(
    "顧客：一杯桂花輕烏龍鮮奶半糖少冰\n顧客：第一杯改大杯",
    {"orders": [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "L", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# === 多杯中改其中一杯（不影響其他） ===
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：紅玉紅茶鮮奶微糖微冰\n顧客：第一杯改無糖",
    {"orders": [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""},
        {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 40, "note": ""},
        {"item": "紅玉紅茶", "category": "fresh_milk_tea", "size": "M", "ice": "微冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}
    ], "total": 180}
))

# === 改加料 ===
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：第一杯加茶凍",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": ["紅烏龍茶凍"], "qty": 1, "unit_price": 80, "note": ""}], "total": 80}
))

# === 改 + 取消混合 ===
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：第一杯改微糖\n顧客：第二杯不要了",
    {"orders": [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "微糖", "addon": [], "qty": 1, "unit_price": 65, "note": ""}], "total": 65}
))
examples.append(make(
    "顧客：一杯紅玉紅茶鮮奶微糖少冰\n顧客：一杯鐵觀音鮮奶半糖去冰\n顧客：第二杯改無糖\n顧客：第一杯不要了",
    {"orders": [{"item": "鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "unit_price": 75, "note": ""}], "total": 75}
))

# ============================================================
# Output
# ============================================================
out_path = "data/round12.jsonl"
with open(out_path, "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} Round 12 (data) examples")
