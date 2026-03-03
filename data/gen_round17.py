#!/usr/bin/env python3
"""
Round 17: 專攻三杯/四杯不對稱規格分配（~14 筆）
使用 qty 欄位表示相同規格的數量
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

def order(item, cat, size, ice, sugar, qty=1, addon=None, note=""):
    return {"item": item, "category": cat, "size": size, "ice": ice, "sugar": sugar,
            "addon": addon or [], "qty": qty, "note": note}

examples = []

# ============================================================
# A. 三杯，兩杯X一杯Y（不對稱甜度）— 用 qty
# ============================================================

# A1
examples.append(make(
    "三杯三窨十五茉鮮奶少冰，兩杯半糖一杯無糖",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", qty=2),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# A2
examples.append(make(
    "三杯琥珀鐵觀音鮮奶去冰，兩杯微糖一杯半糖",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "微糖", qty=2),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "半糖"),
    ]}
))

# A3
examples.append(make(
    "三杯桂花輕烏龍奶茶少冰，一杯無糖兩杯半糖",
    {"orders": [
        order("桂花輕烏龍", "rich_milk_tea", "M", "少冰", "無糖"),
        order("桂花輕烏龍", "rich_milk_tea", "M", "少冰", "半糖", qty=2),
    ]}
))

# ============================================================
# B. 三杯，兩杯X一杯Y（不對稱冰量）
# ============================================================

# B1
examples.append(make(
    "三杯琥珀鐵觀音鮮奶半糖，兩杯少冰一杯去冰",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖", qty=2),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "半糖"),
    ]}
))

# B2
examples.append(make(
    "三杯三窨十五茉奶茶無糖，一杯微冰兩杯去冰",
    {"orders": [
        order("三窨十五茉", "rich_milk_tea", "M", "微冰", "無糖"),
        order("三窨十五茉", "rich_milk_tea", "M", "去冰", "無糖", qty=2),
    ]}
))

# ============================================================
# C. 三杯，兩杯X一杯Y（不對稱尺寸）
# ============================================================

# C1
examples.append(make(
    "三杯桂花輕烏龍鮮奶半糖少冰，兩杯中杯一杯大杯",
    {"orders": [
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖", qty=2),
        order("桂花輕烏龍", "fresh_milk_tea", "L", "少冰", "半糖"),
    ]}
))

# C2
examples.append(make(
    "三杯琥珀鐵觀音奶茶微糖去冰，一杯大杯兩杯中杯",
    {"orders": [
        order("琥珀鐵觀音", "rich_milk_tea", "L", "去冰", "微糖"),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "去冰", "微糖", qty=2),
    ]}
))

# ============================================================
# D. 三杯，用「第一杯/其他/剩下」指代
# ============================================================

# D1
examples.append(make(
    "三杯三窨十五茉鮮奶少冰，第一杯半糖其他無糖",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "無糖", qty=2),
    ]}
))

# D2
examples.append(make(
    "三杯桂花輕烏龍鮮奶去冰，第一杯微糖剩下半糖",
    {"orders": [
        order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "微糖"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "半糖", qty=2),
    ]}
))

# D3
examples.append(make(
    "三杯琥珀鐵觀音奶茶少冰，最後一杯無糖其他半糖",
    {"orders": [
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "半糖", qty=2),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# ============================================================
# E. 四杯不對稱
# ============================================================

# E1
examples.append(make(
    "四杯琥珀鐵觀音鮮奶少冰，三杯半糖一杯無糖",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖", qty=3),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# E2
examples.append(make(
    "四杯三窨十五茉奶茶去冰，兩杯半糖兩杯微糖",
    {"orders": [
        order("三窨十五茉", "rich_milk_tea", "M", "去冰", "半糖", qty=2),
        order("三窨十五茉", "rich_milk_tea", "M", "去冰", "微糖", qty=2),
    ]}
))

# ============================================================
# F. 三杯，三種不同規格（各 qty=1）
# ============================================================

# F1
examples.append(make(
    "三杯三窨十五茉鮮奶少冰，一杯半糖一杯微糖一杯無糖",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "微糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# F2
examples.append(make(
    "三杯桂花輕烏龍鮮奶半糖，一杯少冰一杯去冰一杯微冰",
    {"orders": [
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "半糖"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "微冰", "半糖"),
    ]}
))

# ============================================================
# Write output
# ============================================================
output_path = "data/round17.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Generated {len(examples)} examples")
