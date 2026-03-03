#!/usr/bin/env python3
"""
Round 16: 補強三大弱項
A. 取消場景（~12 筆）
B. 三杯不對稱規格（~5 筆）
C. 非點餐查詢（提到菜單品項但不是點單）（~8 筆）
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
    '輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}]}'
)

def make(user_text, assistant_json):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(assistant_json, ensure_ascii=False)},
        ]
    }

def order(item, cat, size, ice, sugar, addon=None, note=""):
    return {"item": item, "category": cat, "size": size, "ice": ice, "sugar": sugar,
            "addon": addon or [], "qty": 1, "note": note}

examples = []

# ============================================================
# A. 取消場景
# ============================================================

# A1: 取消第二杯（用序號）
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：第二杯不要了",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A2: 取消第一杯（用序號）
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：琥珀鐵觀音奶茶微糖去冰\n顧客：第一杯不要了",
    {"orders": [
        order("琥珀鐵觀音", "rich_milk_tea", "M", "去冰", "微糖"),
    ]}
))

# A3: 用品名取消
examples.append(make(
    "顧客：琥珀鐵觀音鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：鐵觀音不要了",
    {"orders": [
        order("桂花輕烏龍", "pure_tea", None, "去冰", "無糖"),
    ]}
))

# A4: 全部取消
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：算了都不要了",
    {"orders": [], "note": "顧客取消全部訂單"}
))

# A5: 取消後加新的
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：那杯不要了\n顧客：改一杯琥珀鐵觀音鮮奶微糖去冰",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "微糖"),
    ]}
))

# A6: 取消第二杯（三杯中取消一杯）
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍鮮奶無糖去冰\n顧客：一杯琥珀鐵觀音奶茶微糖少冰\n顧客：第二杯取消",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "微糖"),
    ]}
))

# A7: 用「最後那杯」取消
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：最後那杯不要了",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A8: 用「前面那杯」取消
examples.append(make(
    "顧客：琥珀鐵觀音鮮奶半糖少冰\n顧客：三窨十五茉鮮奶無糖去冰\n顧客：前面那杯不要",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "去冰", "無糖"),
    ]}
))

# A9: 「不要了」（只有一杯時取消）
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：不要了",
    {"orders": [], "note": "顧客取消全部訂單"}
))

# A10: 取消後重新點
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍純茶無糖去冰\n顧客：都不要了\n顧客：來一杯琥珀鐵觀音奶茶微糖少冰",
    {"orders": [
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "微糖"),
    ]}
))

# A11: 口語「那個純茶不要」
examples.append(make(
    "顧客：桂花輕烏龍純茶去冰無糖\n顧客：三窨十五茉鮮奶半糖少冰\n顧客：那個純茶不要",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A12: 口語「鮮奶那杯取消」
examples.append(make(
    "顧客：琥珀鐵觀音純茶去冰無糖\n顧客：三窨十五茉鮮奶半糖少冰\n顧客：鮮奶那杯取消",
    {"orders": [
        order("琥珀鐵觀音", "pure_tea", None, "去冰", "無糖"),
    ]}
))

# ============================================================
# B. 三杯不對稱規格
# ============================================================

# B1: 三杯，兩杯半糖一杯無糖
examples.append(make(
    "三杯三窨十五茉鮮奶少冰，兩杯半糖一杯無糖",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# B2: 三杯，兩杯少冰一杯去冰
examples.append(make(
    "三杯琥珀鐵觀音鮮奶半糖，兩杯少冰一杯去冰",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "半糖"),
    ]}
))

# B3: 三杯，一杯大杯兩杯中杯
examples.append(make(
    "三杯桂花輕烏龍奶茶半糖少冰，一杯大杯兩杯中杯",
    {"orders": [
        order("桂花輕烏龍", "rich_milk_tea", "L", "少冰", "半糖"),
        order("桂花輕烏龍", "rich_milk_tea", "M", "少冰", "半糖"),
        order("桂花輕烏龍", "rich_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# B4: 三杯，用「第一杯X其他Y」
examples.append(make(
    "三杯三窨十五茉鮮奶少冰，第一杯無糖其他半糖",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "無糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# B5: 三杯，三種不同甜度
examples.append(make(
    "三杯琥珀鐵觀音奶茶少冰，一杯半糖一杯微糖一杯無糖",
    {"orders": [
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "微糖"),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# ============================================================
# C. 非點餐查詢（提到品項但不是點單）
# ============================================================

# C1: 問價格
examples.append(make(
    "鐵觀音鮮奶多少錢？",
    {"orders": [], "note": "顧客詢問價格，非點餐"}
))

# C2: 問價格（另一品項）
examples.append(make(
    "三窨十五茉鮮奶大杯多少？",
    {"orders": [], "note": "顧客詢問價格，非點餐"}
))

# C3: 問推薦
examples.append(make(
    "你們什麼最好喝？",
    {"orders": [], "note": "顧客詢問推薦，非點餐"}
))

# C4: 問有沒有某品項
examples.append(make(
    "你們有桂花輕烏龍嗎？",
    {"orders": [], "note": "顧客詢問品項，非點餐"}
))

# C5: 問營業時間
examples.append(make(
    "你們幾點關門？",
    {"orders": [], "note": "顧客詢問營業時間，非點餐"}
))

# C6: 問廁所
examples.append(make(
    "廁所在哪裡？",
    {"orders": [], "note": "顧客詢問廁所位置，非點餐"}
))

# C7: 問付款
examples.append(make(
    "可以用LINE Pay嗎？",
    {"orders": [], "note": "顧客詢問付款方式，非點餐"}
))

# C8: 問差異（提到品名但不是點單）
examples.append(make(
    "鐵觀音鮮奶跟鐵觀音奶茶有什麼不一樣？",
    {"orders": [], "note": "顧客詢問品項差異，非點餐"}
))

# ============================================================
# Write output
# ============================================================
output_path = "data/round16.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Generated {len(examples)} examples")
print(f"  A. 取消場景: 12")
print(f"  B. 三杯不對稱: 5")
print(f"  C. 非點餐查詢: 8")
