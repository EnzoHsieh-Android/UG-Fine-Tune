#!/usr/bin/env python3
"""
Round 14: 強化 not_on_menu 混合場景
目標：補充 ~30 個「菜單外品項 + 正常品項」混合範例
重點：珍珠奶茶、拿鐵、常見連鎖飲料店品項
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

def nom(item, note="本店無此品項"):
    """not_on_menu order"""
    return {"item": item, "not_on_menu": True, "note": note}

examples = []

# ============================================================
# A. 珍珠奶茶 混合場景（最常見的 not_on_menu 品項）
# ============================================================

# A1: 珍珠奶茶 + 鐵觀音鮮奶（完全匹配 Test 10）
examples.append(make(
    "一杯珍珠奶茶，一杯鐵觀音鮮奶半糖少冰",
    {"orders": [
        nom("珍珠奶茶"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A2: 珍珠奶茶 + 桂花鮮奶
examples.append(make(
    "一杯珍珠奶茶，一杯桂花輕烏龍鮮奶微糖去冰",
    {"orders": [
        nom("珍珠奶茶"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "微糖"),
    ]}
))

# A3: 珍珠奶茶 + 純茶
examples.append(make(
    "一杯珍珠奶茶半糖少冰，一杯三窨十五茉純茶無糖去冰",
    {"orders": [
        nom("珍珠奶茶"),
        order("三窨十五茉", "pure_tea", None, "去冰", "無糖"),
    ]}
))

# A4: 珍珠奶茶 + 奶茶
examples.append(make(
    "一杯珍珠奶茶正常冰，一杯三窨十五茉奶茶半糖少冰",
    {"orders": [
        nom("珍珠奶茶"),
        order("三窨十五茉", "rich_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A5: 珍珠奶茶 + 大杯鐵觀音
examples.append(make(
    "珍珠奶茶一杯，大杯鐵觀音鮮奶無糖去冰一杯",
    {"orders": [
        nom("珍珠奶茶"),
        order("琥珀鐵觀音", "fresh_milk_tea", "L", "去冰", "無糖"),
    ]}
))

# A6: 顧客分兩句說
examples.append(make(
    "顧客：一杯珍珠奶茶\n顧客：再一杯鐵觀音鮮奶半糖少冰",
    {"orders": [
        nom("珍珠奶茶"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# A7: 珍奶（縮寫）+ 正常品項
examples.append(make(
    "一杯珍奶，一杯桂花輕烏龍鮮奶半糖少冰",
    {"orders": [
        nom("珍珠奶茶"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# ============================================================
# B. 拿鐵 混合場景
# ============================================================

# B1: 拿鐵 + 鮮奶
examples.append(make(
    "一杯拿鐵，一杯三窨十五茉鮮奶半糖少冰",
    {"orders": [
        nom("拿鐵"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# B2: 紅茶拿鐵 + 鮮奶
examples.append(make(
    "一杯紅茶拿鐵半糖少冰，一杯桂花輕烏龍鮮奶無糖去冰",
    {"orders": [
        nom("紅茶拿鐵"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "無糖"),
    ]}
))

# B3: 烏龍拿鐵 + 奶茶
examples.append(make(
    "一杯烏龍拿鐵，一杯鐵觀音奶茶半糖少冰",
    {"orders": [
        nom("烏龍拿鐵"),
        order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# B4: 抹茶拿鐵 + 鮮奶
examples.append(make(
    "一杯抹茶拿鐵半糖少冰，一杯三窨十五茉鮮奶微糖去冰",
    {"orders": [
        nom("抹茶拿鐵"),
        order("三窨十五茉", "fresh_milk_tea", "M", "去冰", "微糖"),
    ]}
))

# ============================================================
# C. 其他常見非菜單品項 混合場景
# ============================================================

# C1: 綠茶
examples.append(make(
    "一杯綠茶，一杯桂花輕烏龍純茶無糖去冰",
    {"orders": [
        nom("綠茶"),
        order("桂花輕烏龍", "pure_tea", None, "去冰", "無糖"),
    ]}
))

# C2: 紅茶
examples.append(make(
    "一杯紅茶半糖少冰，一杯三窨十五茉鮮奶半糖少冰",
    {"orders": [
        nom("紅茶"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# C3: 多多綠
examples.append(make(
    "一杯多多綠，一杯鐵觀音鮮奶半糖少冰",
    {"orders": [
        nom("多多綠"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# C4: 冬瓜茶 + 正常品項
examples.append(make(
    "一杯冬瓜茶，一杯金杯蜜香紅鮮奶半糖少冰",
    {"orders": [
        nom("冬瓜茶"),
        order("金杯蜜香紅", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# C5: 美式咖啡 + 正常品項
examples.append(make(
    "一杯美式咖啡，一杯桂花輕烏龍鮮奶半糖少冰",
    {"orders": [
        nom("美式咖啡"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# C6: 四季春 + 正常品項
examples.append(make(
    "一杯四季春半糖少冰，一杯琥珀鐵觀音鮮奶無糖去冰",
    {"orders": [
        nom("四季春"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "無糖"),
    ]}
))

# C7: 波霸奶茶 + 正常品項
examples.append(make(
    "一杯波霸奶茶半糖少冰，一杯茶花烏龍鮮奶微糖去冰",
    {"orders": [
        nom("波霸奶茶"),
        order("茶花烏龍", "fresh_milk_tea", "M", "去冰", "微糖"),
    ]}
))

# ============================================================
# D. 多品項混合（1 not_on_menu + 2 正常）
# ============================================================

# D1: 珍珠奶茶 + 兩杯正常
examples.append(make(
    "一杯珍珠奶茶，一杯桂花輕烏龍鮮奶半糖少冰，一杯鐵觀音純茶去冰無糖",
    {"orders": [
        nom("珍珠奶茶"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "pure_tea", None, "去冰", "無糖"),
    ]}
))

# D2: 拿鐵 + 兩杯正常
examples.append(make(
    "一杯拿鐵，一杯三窨十五茉鮮奶半糖少冰，一杯桂花輕烏龍奶茶微糖去冰",
    {"orders": [
        nom("拿鐵"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("桂花輕烏龍", "rich_milk_tea", "M", "去冰", "微糖"),
    ]}
))

# ============================================================
# E. 多個 not_on_menu + 正常品項
# ============================================================

# E1: 2 not_on_menu + 1 正常
examples.append(make(
    "一杯珍珠奶茶，一杯紅茶拿鐵，一杯三窨十五茉鮮奶半糖少冰",
    {"orders": [
        nom("珍珠奶茶"),
        nom("紅茶拿鐵"),
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
    ]}
))

# E2: 2 not_on_menu
examples.append(make(
    "一杯珍珠奶茶半糖少冰，一杯拿鐵去冰無糖",
    {"orders": [
        nom("珍珠奶茶"),
        nom("拿鐵"),
    ]}
))

# ============================================================
# F. 純 not_on_menu 單品（補充）
# ============================================================

# F1: 珍珠奶茶帶甜冰規格
examples.append(make(
    "珍珠奶茶半糖少冰",
    {"orders": [nom("珍珠奶茶")]}
))

# F2: 拿鐵帶規格
examples.append(make(
    "拿鐵無糖去冰",
    {"orders": [nom("拿鐵")]}
))

# F3: 阿薩姆奶茶
examples.append(make(
    "一杯阿薩姆奶茶半糖少冰",
    {"orders": [nom("阿薩姆奶茶")]}
))

# ============================================================
# G. not_on_menu 後顧客改點菜單上的品項
# ============================================================

# G1: 珍珠奶茶沒有→改鐵觀音
examples.append(make(
    "顧客：珍珠奶茶半糖少冰\n顧客：沒有喔？那給我鐵觀音鮮奶半糖少冰",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖")]}
))

# G2: 拿鐵沒有→改三窨十五茉
examples.append(make(
    "顧客：一杯拿鐵\n顧客：你們沒拿鐵？那三窨十五茉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖")]}
))

# ============================================================
# Write output
# ============================================================
output_path = "data/round14.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Generated {len(examples)} examples")
