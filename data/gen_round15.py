#!/usr/bin/env python3
"""
Round 15: 強化兩大弱點
A. 同品項不同規格（~15 筆）
B. 非菜單加料（~10 筆）
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
    '"ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}]}'
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
# A. 同品項不同規格（兩杯為主 + 少量三杯）
# ============================================================

# --- 不同甜度 ---

# A1
examples.append(make(
    "兩杯鐵觀音鮮奶少冰，一杯半糖一杯無糖",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# A2
examples.append(make(
    "兩杯三窨十五茉鮮奶少冰，一杯微糖一杯半糖",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "微糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A3
examples.append(make(
    "兩杯桂花輕烏龍奶茶去冰，一杯無糖一杯少糖",
    {"orders": [
        order("桂花輕烏龍", "rich_milk_tea", "M", "去冰", "無糖"),
        order("桂花輕烏龍", "rich_milk_tea", "M", "去冰", "少糖"),
    ]}
))

# --- 不同冰量 ---

# A4
examples.append(make(
    "兩杯鐵觀音鮮奶半糖，一杯少冰一杯去冰",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "半糖"),
    ]}
))

# A5
examples.append(make(
    "兩杯三窨十五茉奶茶無糖，一杯去冰一杯微冰",
    {"orders": [
        order("三窨十五茉", "rich_milk_tea", "M", "去冰", "無糖"),
        order("三窨十五茉", "rich_milk_tea", "M", "微冰", "無糖"),
    ]}
))

# --- 不同尺寸 ---

# A6
examples.append(make(
    "兩杯桂花輕烏龍鮮奶半糖少冰，一杯大杯一杯中杯",
    {"orders": [
        order("桂花輕烏龍", "fresh_milk_tea", "L", "少冰", "半糖"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A7
examples.append(make(
    "兩杯鐵觀音奶茶微糖去冰，一大一中",
    {"orders": [
        order("琥珀鐵觀音", "rich_milk_tea", "L", "去冰", "微糖"),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "去冰", "微糖"),
    ]}
))

# --- 甜度+冰量都不同 ---

# A8
examples.append(make(
    "兩杯鐵觀音鮮奶，一杯半糖少冰，一杯無糖去冰",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "無糖"),
    ]}
))

# A9
examples.append(make(
    "兩杯三窨十五茉鮮奶，一杯微糖微冰一杯半糖少冰",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "微冰", "微糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A10
examples.append(make(
    "兩杯桂花輕烏龍鮮奶，一杯半糖少冰一杯無糖去冰",
    {"orders": [
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "無糖"),
    ]}
))

# --- 尺寸+甜冰混合 ---

# A11
examples.append(make(
    "兩杯鐵觀音鮮奶，一杯大杯半糖少冰，一杯中杯無糖去冰",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "L", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "無糖"),
    ]}
))

# A12: 口語「一冰一熱」
examples.append(make(
    "兩杯三窨十五茉鮮奶半糖，一杯少冰一杯熱的",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("三窨十五茉", "fresh_milk_tea", "M", "熱飲", "半糖"),
    ]}
))

# --- 三杯變化 ---

# A13: 三杯，三種甜度
examples.append(make(
    "三杯鐵觀音鮮奶少冰，一杯半糖一杯微糖一杯無糖",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "微糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# A14: 三杯，兩杯X一杯Y（不對稱）
examples.append(make(
    "三杯桂花輕烏龍鮮奶少冰，兩杯半糖一杯無糖",
    {"orders": [
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# A15: 三杯，用「其他」指代
examples.append(make(
    "三杯鐵觀音奶茶少冰，第一杯半糖其他無糖",
    {"orders": [
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "無糖"),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "無糖"),
    ]}
))

# ============================================================
# B. 非菜單加料（品項正常，加料不在菜單）
# ============================================================

# B1: 珍珠
examples.append(make(
    "三窨十五茉鮮奶半糖少冰加珍珠",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", [],
                      "本店無珍珠，可選紅烏龍茶凍或燕麥粒")]}
))

# B2: 椰果
examples.append(make(
    "桂花輕烏龍鮮奶半糖少冰加椰果",
    {"orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖", [],
                      "本店無椰果，可選紅烏龍茶凍或燕麥粒")]}
))

# B3: 布丁
examples.append(make(
    "鐵觀音奶茶半糖少冰加布丁",
    {"orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "半糖", [],
                      "本店無布丁，可選紅烏龍茶凍或燕麥粒")]}
))

# B4: 仙草
examples.append(make(
    "大杯鐵觀音鮮奶微糖去冰加仙草",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "L", "去冰", "微糖", [],
                      "本店無仙草，可選紅烏龍茶凍或燕麥粒")]}
))

# B5: 粉圓
examples.append(make(
    "三窨十五茉奶茶無糖去冰加粉圓",
    {"orders": [order("三窨十五茉", "rich_milk_tea", "M", "去冰", "無糖", [],
                      "本店無粉圓，可選紅烏龍茶凍或燕麥粒")]}
))

# B6: 芋圓
examples.append(make(
    "桂花輕烏龍奶茶半糖少冰加芋圓",
    {"orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "少冰", "半糖", [],
                      "本店無芋圓，可選紅烏龍茶凍或燕麥粒")]}
))

# B7: 波霸（另一品項）
examples.append(make(
    "桂花輕烏龍鮮奶半糖少冰加波霸",
    {"orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖", [],
                      "本店無波霸，可選紅烏龍茶凍或燕麥粒")]}
))

# B8: 珍珠 + 多杯場景（只有一杯加了非菜單加料）
examples.append(make(
    "一杯三窨十五茉鮮奶半糖少冰加珍珠，一杯桂花輕烏龍鮮奶無糖去冰",
    {"orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", [],
              "本店無珍珠，可選紅烏龍茶凍或燕麥粒"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "無糖"),
    ]}
))

# B9: 非菜單加料 + 菜單加料同時
examples.append(make(
    "鐵觀音鮮奶半糖少冰加茶凍加珍珠",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖",
                      ["紅烏龍茶凍"],
                      "本店無珍珠，已加紅烏龍茶凍")]}
))

# B10: 對話式加非菜單加料
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：可以加珍珠嗎",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", [],
                      "本店無珍珠，可選紅烏龍茶凍或燕麥粒")]}
))

# ============================================================
# Write output
# ============================================================
output_path = "data/round15.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Generated {len(examples)} examples")
