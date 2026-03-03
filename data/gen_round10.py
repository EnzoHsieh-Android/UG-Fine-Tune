#!/usr/bin/env python3
"""Round 10: 中優先度 — 取消品項、果茶熱飲衝突、同品項不同規格、加料簡稱加強、混合not_on_menu補強"""
import json

SYSTEM = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。\n\n"
    "菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。\n\n"
    "純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，回傳 not_on_menu 欄位。\n\n"
    "輸出格式：{\"orders\":[{\"item\":\"品名\",\"category\":\"分類\",\"size\":\"M/L/null\",\"ice\":\"冰量/null\",\"sugar\":\"甜度/null\",\"addon\":[],\"qty\":1,\"unit_price\":0,\"note\":\"\"}],\"total\":0}"
)

def make(user, assistant):
    return json.dumps({"messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
        {"role": "assistant", "content": json.dumps(assistant, ensure_ascii=False)},
    ]}, ensure_ascii=False)

def order(item, cat, size, ice, sugar, addon, qty, unit_price, note=""):
    return {"item": item, "category": cat, "size": size, "ice": ice, "sugar": sugar,
            "addon": addon, "qty": qty, "unit_price": unit_price, "note": note}

def not_on_menu_order(item, note=""):
    return {"item": item, "category": None, "size": None, "ice": None, "sugar": None,
            "addon": [], "qty": 1, "unit_price": 0, "not_on_menu": True, "note": note}

examples = []

# ============================================================
# A. 取消/刪除品項
# ============================================================

# A1: 第二杯不要了
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：第二杯不要了",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

# A2: 桂花那杯取消
examples.append(make(
    "顧客：桂花鮮奶半糖少冰\n顧客：茶花紅烏龍純茶無糖去冰\n顧客：桂花那杯取消",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

# A3: 不要了（取消唯一一杯）
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：算了不要了",
    {"orders": [], "total": 0, "note": "顧客取消所有品項"}))

# A4: 取消其中一杯再加新的
examples.append(make(
    "顧客：一杯琥珀鐵觀音鮮奶半糖少冰\n顧客：一杯金杯蜜香紅奶茶無糖去冰\n顧客：鐵觀音那杯不要了，換一杯茶花烏龍鮮奶微糖去冰",
    {"orders": [
        order("金杯蜜香紅","rich_milk_tea","M","去冰","無糖",[],1,60),
        order("茶花烏龍","fresh_milk_tea","M","去冰","微糖",[],1,65),
    ], "total":125}))

# A5: 第一杯不要
examples.append(make(
    "顧客：三窨十五茉純茶無糖去冰\n顧客：朱槿普洱紅純茶無糖少冰\n顧客：米香玉露菁鮮奶半糖少冰\n顧客：第一杯不要了",
    {"orders": [
        order("朱槿普洱紅","pure_tea",None,"少冰","無糖",[],1,40),
        order("米香玉露菁","fresh_milk_tea","M","少冰","半糖",[],1,60),
    ], "total":100}))

# A6: 取消加料
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰加茶凍\n顧客：茶凍不要了",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

# ============================================================
# B. 果茶點熱飲衝突 — 果香四溢僅供冷飲
# ============================================================

# B1: 蜜桃熱的 → 衝突提示
examples.append(make(
    "蜜桃紅烏龍熱的半糖",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,None,"半糖",[],1,75,"果香四溢系列僅供冷飲，無法做熱飲，請顧客重新選擇冰量")], "total":75}))

# B2: 葡柚熱飲 → 衝突提示
examples.append(make(
    "葡柚十五茉熱飲半糖",
    {"orders": [order("葡柚十五茉","fruit_tea",None,None,"半糖",[],1,80,"果香四溢系列僅供冷飲，無法做熱飲，請顧客重新選擇冰量")], "total":80}))

# B3: 青檸桂蜜溫的 → 衝突提示
examples.append(make(
    "青檸桂蜜溫的少糖",
    {"orders": [order("青檸桂蜜","fruit_tea",None,None,"少糖",[],1,65,"果香四溢系列僅供冷飲，無法做熱飲，請顧客重新選擇冰量")], "total":65}))

# B4: 果茶正常冷飲 → 正常（對照組）
examples.append(make(
    "蜜桃紅烏龍少冰半糖",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,"少冰","半糖",[],1,75)], "total":75}))

# ============================================================
# C. 同品項不同規格
# ============================================================

# C1: 兩杯茉莉鮮奶，一杯半糖一杯無糖
examples.append(make(
    "兩杯茉莉鮮奶少冰，一杯半糖一杯無糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("三窨十五茉","fresh_milk_tea","M","少冰","無糖",[],1,65),
    ], "total":130}))

# C2: 兩杯鐵觀音鮮奶，一杯大杯一杯中杯
examples.append(make(
    "兩杯鐵觀音鮮奶半糖少冰，一杯大杯一杯中杯",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",[],1,75),
        order("琥珀鐵觀音","fresh_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":140}))

# C3: 三杯桂花，一杯純茶一杯鮮奶一杯奶茶
examples.append(make(
    "三杯桂花輕烏龍，一杯純茶去冰無糖，一杯鮮奶半糖少冰，一杯奶茶微糖去冰",
    {"orders": [
        order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45),
        order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","微糖",[],1,65),
    ], "total":175}))

# C4: 兩杯三窨十五茉鮮奶，一杯加茶凍一杯不加
examples.append(make(
    "兩杯三窨十五茉鮮奶半糖少冰，一杯加茶凍一杯不加",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80),
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":145}))

# C5: 多輪 — 同品項不同冰量
examples.append(make(
    "顧客：兩杯金杯蜜香紅鮮奶半糖\n顧客：一杯少冰一杯去冰",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","M","少冰","半糖",[],1,60),
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","半糖",[],1,60),
    ], "total":120}))

# ============================================================
# D. 混合 not_on_menu + 正常（補強 Round 9 失敗場景）
# ============================================================

# D1: 珍珠奶茶 + 正常品項（精確重現測試場景）
examples.append(make(
    "一杯珍珠奶茶，一杯鐵觀音鮮奶半糖少冰",
    {"orders": [
        not_on_menu_order("珍珠奶茶","本店無珍珠奶茶"),
        order("琥珀鐵觀音","fresh_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":65}))

# D2: 正常 + not_on_menu（順序反過來）
examples.append(make(
    "一杯三窨十五茉鮮奶半糖少冰，一杯珍珠綠茶",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        not_on_menu_order("珍珠綠茶","本店無珍珠綠茶"),
    ], "total":65}))

# D3: 兩個正常 + 一個 not_on_menu
examples.append(make(
    "一杯茉莉鮮奶半糖少冰，一杯抹茶拿鐵，一杯桂花純茶無糖去冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        not_on_menu_order("抹茶拿鐵","本店無抹茶拿鐵"),
        order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":110}))

# D4: 多輪 not_on_menu + 正常
examples.append(make(
    "顧客：一杯紅茶拿鐵半糖去冰\n顧客：一杯桂花輕烏龍鮮奶半糖少冰",
    {"orders": [
        not_on_menu_order("紅茶拿鐵","本店無紅茶拿鐵"),
        order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":65}))

# D5: 兩個 not_on_menu + 一個正常
examples.append(make(
    "一杯多多綠茶，一杯冬瓜茶，一杯金杯蜜香紅鮮奶大杯無糖去冰",
    {"orders": [
        not_on_menu_order("多多綠茶","本店無多多綠茶"),
        not_on_menu_order("冬瓜茶","本店無冬瓜茶"),
        order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70),
    ], "total":70}))

# D6: 顧客自己發現沒有 → 改點
examples.append(make(
    "顧客：有沒有紅茶拿鐵\n顧客：沒有喔，那一杯茶花紅烏龍純茶無糖去冰",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

# D7: 簡稱 not_on_menu
examples.append(make(
    "一杯奶綠半糖少冰，一杯茉莉鮮奶不要糖不要冰",
    {"orders": [
        not_on_menu_order("奶綠","本店無奶綠"),
        order("三窨十五茉","fresh_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":65}))

# ============================================================
# E. 純茶指定尺寸衝突 — 純茶為單一尺寸
# ============================================================

examples.append(make(
    "大杯桂花輕烏龍純茶去冰無糖",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45,"純茶為單一尺寸，無法選擇大杯")], "total":45}))

examples.append(make(
    "中杯三窨十五茉純茶無糖少冰",
    {"orders": [order("三窨十五茉","pure_tea",None,"少冰","無糖",[],1,45,"純茶為單一尺寸，無需指定尺寸")], "total":45}))

# Write out
with open("/Users/xiechengru/ug-finetune/data/round10.jsonl", "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} Round 10 examples")
