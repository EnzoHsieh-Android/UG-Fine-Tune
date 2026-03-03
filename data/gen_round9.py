#!/usr/bin/env python3
"""Round 9: 高優先度場景 — 品名簡稱、口語化甜度冰量、混合 not_on_menu + 正常訂單"""
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
# A. 品名簡稱 — 顧客不會唸完整品名
# ============================================================

# --- 茉莉 / 茉莉鮮奶 → 三窨十五茉 ---
examples.append(make(
    "一杯茉莉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "茉莉純茶去冰無糖",
    {"orders": [order("三窨十五茉","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "大杯茉莉奶茶半糖少冰",
    {"orders": [order("三窨十五茉","rich_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))

examples.append(make(
    "茉莉鮮奶大杯微糖去冰加茶凍",
    {"orders": [order("三窨十五茉","fresh_milk_tea","L","去冰","微糖",["紅烏龍茶凍"],1,90)], "total":90}))

# --- 鐵觀音 → 琥珀鐵觀音 ---
examples.append(make(
    "鐵觀音鮮奶半糖少冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "鐵觀音奶茶大杯無糖去冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","L","去冰","無糖",[],1,75)], "total":75}))

# --- 桂花 → 桂花輕烏龍 ---
examples.append(make(
    "桂花純茶去冰無糖",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "桂花鮮奶半糖少冰",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "桂花奶蓋",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

# --- 普洱 / 普洱紅 → 朱槿普洱紅 ---
examples.append(make(
    "普洱紅純茶無糖去冰",
    {"orders": [order("朱槿普洱紅","pure_tea",None,"去冰","無糖",[],1,40)], "total":40}))

examples.append(make(
    "普洱鮮奶半糖少冰",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","M","少冰","半糖",[],1,60)], "total":60}))

# --- 玉露 → 米香玉露菁 ---
examples.append(make(
    "玉露純茶少冰無糖",
    {"orders": [order("米香玉露菁","pure_tea",None,"少冰","無糖",[],1,40)], "total":40}))

examples.append(make(
    "玉露鮮奶半糖去冰",
    {"orders": [order("米香玉露菁","fresh_milk_tea","M","去冰","半糖",[],1,60)], "total":60}))

# --- 蜜香紅 / 金杯 → 金杯蜜香紅 ---
examples.append(make(
    "蜜香紅鮮奶大杯半糖少冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","半糖",[],1,70)], "total":70}))

examples.append(make(
    "金杯奶茶半糖去冰",
    {"orders": [order("金杯蜜香紅","rich_milk_tea","M","去冰","半糖",[],1,60)], "total":60}))

# --- 蜜桃 → 蜜桃紅烏龍 ---
examples.append(make(
    "蜜桃少冰半糖",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,"少冰","半糖",[],1,75)], "total":75}))

# --- 葡柚 → 葡柚十五茉 ---
examples.append(make(
    "葡柚少冰",
    {"orders": [order("葡柚十五茉","fruit_tea",None,"少冰",None,[],1,80)], "total":80}))

# --- 青檸 → 青檸桂蜜 ---
examples.append(make(
    "青檸半糖少冰",
    {"orders": [order("青檸桂蜜","fruit_tea",None,"少冰","半糖",[],1,65)], "total":65}))

# --- 茶花 → 茶花紅烏龍(pure_tea) / 茶花烏龍(fresh_milk_tea/rich_milk_tea) ---
examples.append(make(
    "茶花純茶無糖去冰",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "茶花鮮奶半糖少冰",
    {"orders": [order("茶花烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "茶花奶蓋",
    {"orders": [order("茶花紅烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

# --- 混合簡稱多杯 ---
examples.append(make(
    "一杯茉莉鮮奶半糖少冰，一杯鐵觀音奶茶無糖去冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("琥珀鐵觀音","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：桂花鮮奶半糖少冰\n顧客：再一杯蜜桃少冰",
    {"orders": [
        order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75),
    ], "total":140}))

# ============================================================
# B. 甜度冰量口語化
# ============================================================

# --- 不要糖 / 不加糖 → 無糖 ---
examples.append(make(
    "三窨十五茉鮮奶不要糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "桂花輕烏龍純茶不加糖去冰",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

# --- 不要冰 / 不加冰 → 去冰 ---
examples.append(make(
    "茶花紅烏龍純茶無糖不要冰",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "琥珀鐵觀音鮮奶半糖不加冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","去冰","半糖",[],1,65)], "total":65}))

# --- 正常就好 / 正常 → 正常糖 + 正常冰 ---
examples.append(make(
    "三窨十五茉鮮奶正常就好",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","正常冰","正常糖",[],1,65)], "total":65}))

examples.append(make(
    "金杯蜜香紅奶茶甜度冰量正常",
    {"orders": [order("金杯蜜香紅","rich_milk_tea","M","正常冰","正常糖",[],1,60)], "total":60}))

# --- 冰少一點 → 少冰 ---
examples.append(make(
    "朱槿普洱紅純茶無糖，冰少一點",
    {"orders": [order("朱槿普洱紅","pure_tea",None,"少冰","無糖",[],1,40)], "total":40}))

# --- 甜一點 / 不要太甜 → 模糊需確認 ---
examples.append(make(
    "三窨十五茉鮮奶少冰，甜一點",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰",None,[],1,65,"顧客說甜一點，請店員確認甜度")], "total":65}))

examples.append(make(
    "桂花輕烏龍鮮奶去冰，不要太甜",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","去冰",None,[],1,65,"顧客說不要太甜，請店員確認甜度")], "total":65}))

# --- 溫的 → 熱飲（口語表達） ---
examples.append(make(
    "茉莉鮮奶溫的半糖",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","熱飲","半糖",[],1,65)], "total":65}))

examples.append(make(
    "桂花純茶無糖，要溫的",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"熱飲","無糖",[],1,45)], "total":45}))

# --- 混合口語 ---
examples.append(make(
    "鐵觀音鮮奶不要冰不要糖",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","去冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "金杯蜜香紅鮮奶大杯不加糖不加冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70)], "total":70}))

# --- 簡稱 + 口語甜度冰量 ---
examples.append(make(
    "顧客：茉莉鮮奶不要冰不要糖\n顧客：蜜桃不要冰半糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","去冰","無糖",[],1,65),
        order("蜜桃紅烏龍","fruit_tea",None,"去冰","半糖",[],1,75),
    ], "total":140}))

# ============================================================
# C. 混合 not_on_menu + 正常訂單
# ============================================================

examples.append(make(
    "一杯珍珠奶茶，一杯三窨十五茉鮮奶半糖少冰",
    {"orders": [
        not_on_menu_order("珍珠奶茶","本店無珍珠奶茶"),
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":65}))

examples.append(make(
    "顧客：一杯紅茶拿鐵半糖去冰\n顧客：一杯桂花輕烏龍純茶無糖去冰",
    {"orders": [
        not_on_menu_order("紅茶拿鐵","本店無紅茶拿鐵"),
        order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":45}))

examples.append(make(
    "一杯多多綠茶，一杯琥珀鐵觀音鮮奶半糖少冰，一杯四季春",
    {"orders": [
        not_on_menu_order("多多綠茶","本店無多多綠茶"),
        order("琥珀鐵觀音","fresh_milk_tea","M","少冰","半糖",[],1,65),
        not_on_menu_order("四季春","本店無四季春"),
    ], "total":65}))

examples.append(make(
    "顧客：有沒有綠茶\n顧客：沒有喔，那來杯茶花紅烏龍純茶無糖去冰",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "一杯冬瓜茶，一杯金杯蜜香紅鮮奶大杯無糖去冰，一杯葡柚十五茉少冰",
    {"orders": [
        not_on_menu_order("冬瓜茶","本店無冬瓜茶"),
        order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70),
        order("葡柚十五茉","fruit_tea",None,"少冰",None,[],1,80),
    ], "total":150}))

examples.append(make(
    "顧客：一杯抹茶拿鐵\n顧客：啊你們沒有喔，那一杯桂花奶蓋好了",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

# ============================================================
# D. 加料簡稱
# ============================================================

examples.append(make(
    "三窨十五茉鮮奶半糖少冰加凍",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80)], "total":80}))

examples.append(make(
    "桂花輕烏龍奶茶半糖少冰加燕麥",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",["燕麥粒"],1,80)], "total":80}))

examples.append(make(
    "鐵觀音鮮奶半糖少冰，兩種料都加",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍","燕麥粒"],1,95)], "total":95}))

examples.append(make(
    "茶花烏龍鮮奶大杯無糖去冰加茶凍加燕麥粒",
    {"orders": [order("茶花烏龍","fresh_milk_tea","L","去冰","無糖",["紅烏龍茶凍","燕麥粒"],1,105)], "total":105}))

examples.append(make(
    "茉莉鮮奶不要糖不要冰加凍加燕麥",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","去冰","無糖",["紅烏龍茶凍","燕麥粒"],1,95)], "total":95}))

# Write out
with open("/Users/xiechengru/ug-finetune/data/round9.jsonl", "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} Round 9 examples")
