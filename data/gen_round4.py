#!/usr/bin/env python3
"""Round 4: 多輪對話場景 — 逐步補充、區分新杯、中途修改"""
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
# 場景 A：逐步補充同一杯（2~4 句拼成一杯）
# ============================================================

# --- 品項 → 類別 → 甜度 ---
examples.append(make(
    "顧客：金杯蜜香紅\n顧客：要鮮奶茶\n顧客：無糖",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","M",None,"無糖",[],1,60)], "total":60}))

examples.append(make(
    "顧客：桂花輕烏龍\n顧客：奶茶的\n顧客：半糖少冰",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：三窨十五茉\n顧客：加鮮奶\n顧客：微糖去冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","去冰","微糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：琥珀鐵觀音\n顧客：鮮奶茶\n顧客：少糖微冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","微冰","少糖",[],1,65)], "total":65}))

# --- 品項 → 類別 → 尺寸 → 甜度冰量 ---
examples.append(make(
    "顧客：茶花烏龍\n顧客：奶茶\n顧客：大杯\n顧客：半糖少冰",
    {"orders": [order("茶花烏龍","rich_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：金杯蜜香紅\n顧客：鮮奶的\n顧客：要大的\n顧客：無糖去冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70)], "total":70}))

examples.append(make(
    "顧客：朱槿普洱紅\n顧客：加奶\n顧客：大杯\n顧客：微糖少冰",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","L","少冰","微糖",[],1,70)], "total":70}))

# --- 品項 → 類別 → 加料 ---
examples.append(make(
    "顧客：三窨十五茉鮮奶\n顧客：加茶凍\n顧客：半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80)], "total":80}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶\n顧客：加燕麥粒\n顧客：無糖去冰",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",["燕麥粒"],1,80)], "total":80}))

examples.append(make(
    "顧客：茶花烏龍鮮奶大杯\n顧客：加茶凍加燕麥粒\n顧客：半糖少冰",
    {"orders": [order("茶花烏龍","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍","燕麥粒"],1,105)], "total":105}))

# --- 只說品項，後面才決定純茶還是奶茶 ---
examples.append(make(
    "顧客：茶花紅烏龍\n顧客：純茶就好\n顧客：無糖去冰",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "顧客：桂花輕烏龍\n顧客：我要奶蓋的\n顧客：不用加料",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

examples.append(make(
    "顧客：米香玉露菁\n顧客：純茶\n顧客：少糖少冰",
    {"orders": [order("米香玉露菁","pure_tea",None,"少冰","少糖",[],1,40)], "total":40}))

# --- 口語化逐步 ---
examples.append(make(
    "顧客：欸那個茉莉\n顧客：加奶的\n顧客：不要糖\n顧客：冰少一點",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：鐵觀音\n顧客：奶茶\n顧客：大杯半糖\n顧客：去冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","L","去冰","半糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：紅烏龍\n顧客：要鮮奶\n顧客：少糖微冰",
    {"orders": [order("茶花紅烏龍","fresh_milk_tea","M","微冰","少糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：蜜香紅\n顧客：鮮奶茶大杯\n顧客：正常糖正常冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","正常冰","正常糖",[],1,70)], "total":70}))

examples.append(make(
    "顧客：普洱\n顧客：奶茶的\n顧客：微糖去冰加茶凍",
    {"orders": [order("朱槿普洱紅","rich_milk_tea","M","去冰","微糖",["紅烏龍茶凍"],1,75)], "total":75}))

examples.append(make(
    "顧客：玉露\n顧客：加鮮奶大杯\n顧客：無糖少冰加燕麥粒",
    {"orders": [order("米香玉露菁","fresh_milk_tea","L","少冰","無糖",["燕麥粒"],1,85)], "total":85}))

# ============================================================
# 場景 B：多杯逐步點（區分「補充」vs「新的一杯」）
# ============================================================

# --- 第一杯完整 → 「再來/還要/另外」觸發新杯 ---
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再來一杯桂花輕烏龍純茶無糖去冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":110}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶無糖去冰\n顧客：還要一杯琥珀鐵觀音奶茶半糖少冰",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","無糖",[],1,60),
        order("琥珀鐵觀音","rich_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":125}))

examples.append(make(
    "顧客：蜜桃紅烏龍少冰\n顧客：另外要一杯茶花紅烏龍奶蓋",
    {"orders": [
        order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75),
        order("茶花紅烏龍","cloud_velvet",None,None,None,[],1,95),
    ], "total":170}))

# --- 第一杯分多句 → 「再來/還要」第二杯也分多句 ---
examples.append(make(
    "顧客：茶花烏龍\n顧客：鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍\n顧客：也是鮮奶\n顧客：無糖去冰",
    {"orders": [
        order("茶花烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("桂花輕烏龍","fresh_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：金杯蜜香紅\n顧客：奶茶大杯半糖少冰\n顧客：還要一杯三窨十五茉\n顧客：純茶就好\n顧客：無糖去冰",
    {"orders": [
        order("金杯蜜香紅","rich_milk_tea","L","少冰","半糖",[],1,70),
        order("三窨十五茉","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":115}))

examples.append(make(
    "顧客：琥珀鐵觀音鮮奶\n顧客：大杯無糖去冰加茶凍\n顧客：然後再一杯蜜桃紅烏龍\n顧客：少冰就好",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","去冰","無糖",["紅烏龍茶凍"],1,90),
        order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75),
    ], "total":165}))

# --- 第一杯 → 「我朋友要/幫我朋友點」→ 新杯 ---
examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：我朋友要一杯茶花紅烏龍純茶無糖去冰",
    {"orders": [
        order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":110}))

examples.append(make(
    "顧客：大杯三窨十五茉奶茶無糖去冰\n顧客：幫我朋友點一杯葡柚十五茉\n顧客：少冰",
    {"orders": [
        order("三窨十五茉","rich_milk_tea","L","去冰","無糖",[],1,75),
        order("葡柚十五茉","fruit_tea",None,"少冰",None,[],1,80),
    ], "total":155}))

# --- 三杯逐步 ---
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍奶茶無糖去冰\n顧客：還要一杯茶花紅烏龍純茶微糖微冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
        order("茶花紅烏龍","pure_tea",None,"微冰","微糖",[],1,45),
    ], "total":175}))

examples.append(make(
    "顧客：朱槿普洱紅\n顧客：純茶少糖少冰\n顧客：再來一杯米香玉露菁鮮奶半糖去冰\n顧客：對了再加一杯青檸桂蜜少冰",
    {"orders": [
        order("朱槿普洱紅","pure_tea",None,"少冰","少糖",[],1,40),
        order("米香玉露菁","fresh_milk_tea","M","去冰","半糖",[],1,60),
        order("青檸桂蜜","fruit_tea",None,"少冰",None,[],1,65),
    ], "total":165}))

# ============================================================
# 場景 C：中途修改已點的內容
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：等等，改無糖",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖少冰\n顧客：改大杯",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：琥珀鐵觀音鮮奶大杯半糖少冰\n顧客：啊不對，改中杯就好",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：幫我加茶凍",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,75)], "total":75}))

examples.append(make(
    "顧客：茶花烏龍奶茶半糖少冰加茶凍\n顧客：茶凍不要了",
    {"orders": [order("茶花烏龍","rich_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：等等，我不要鮮奶了，改純茶",
    {"orders": [order("三窨十五茉","pure_tea",None,"少冰","半糖",[],1,45)], "total":45}))

examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：算了改奶蓋好了",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,"少冰","半糖",[],1,95)], "total":95}))

examples.append(make(
    "顧客：大杯金杯蜜香紅鮮奶半糖少冰加茶凍\n顧客：甜度改微糖\n顧客：茶凍換燕麥粒",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","微糖",["燕麥粒"],1,85)], "total":85}))

examples.append(make(
    "顧客：三窨十五茉奶茶無糖去冰\n顧客：冰量改少冰就好",
    {"orders": [order("三窨十五茉","rich_milk_tea","M","少冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：茶花紅烏龍純茶無糖去冰\n顧客：欸還是加鮮奶好了\n顧客：大杯",
    {"orders": [order("茶花紅烏龍","fresh_milk_tea","L","去冰","無糖",[],1,75)], "total":75}))

# ============================================================
# 場景 D：多杯 + 修改混合
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍奶茶無糖去冰\n顧客：第一杯改無糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","無糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：大杯琥珀鐵觀音鮮奶半糖少冰\n顧客：還要一杯蜜桃紅烏龍少冰\n顧客：鐵觀音那杯加茶凍",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,90),
        order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75),
    ], "total":165}))

examples.append(make(
    "顧客：金杯蜜香紅奶茶半糖少冰\n顧客：再一杯朱槿普洱紅純茶\n顧客：普洱那杯無糖去冰\n顧客：蜜香紅改大杯",
    {"orders": [
        order("金杯蜜香紅","rich_milk_tea","L","少冰","半糖",[],1,70),
        order("朱槿普洱紅","pure_tea",None,"去冰","無糖",[],1,40),
    ], "total":110}))

# ============================================================
# 場景 E：「一樣的」「跟他一樣」「同上」
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再來一杯一樣的",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶大杯無糖去冰\n顧客：我朋友也要一杯一樣的",
    {"orders": [
        order("桂花輕烏龍","rich_milk_tea","L","去冰","無糖",[],1,75),
        order("桂花輕烏龍","rich_milk_tea","L","去冰","無糖",[],1,75),
    ], "total":150}))

examples.append(make(
    "顧客：大杯琥珀鐵觀音鮮奶半糖少冰加茶凍\n顧客：同上再一杯",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,90),
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,90),
    ], "total":180}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶無糖去冰\n顧客：再一杯一樣的，但要半糖",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","無糖",[],1,60),
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","半糖",[],1,60),
    ], "total":120}))

# ============================================================
# 場景 F：取消 / 不要了
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍純茶\n顧客：桂花那杯不要了",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：琥珀鐵觀音奶茶半糖少冰\n顧客：再一杯蜜桃紅烏龍\n顧客：算了鐵觀音不要了",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,None,None,[],1,75)], "total":75}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：再來一杯茶花烏龍奶茶\n顧客：還要葡柚十五茉\n顧客：茶花烏龍不要了",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","M","少冰","半糖",[],1,60),
        order("葡柚十五茉","fruit_tea",None,None,None,[],1,80),
    ], "total":140}))

# ============================================================
# 場景 G：混合 — 多輪 + not_on_menu
# ============================================================

examples.append(make(
    "顧客：珍珠奶茶\n顧客：你們沒有喔？那給我三窨十五茉奶茶好了\n顧客：半糖少冰",
    {"orders": [order("三窨十五茉","rich_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：紅茶拿鐵\n顧客：沒有的話，那金杯蜜香紅鮮奶\n顧客：大杯無糖去冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70)], "total":70}))

examples.append(make(
    "顧客：綠茶\n顧客：好那換三窨十五茉純茶\n顧客：無糖去冰",
    {"orders": [order("三窨十五茉","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "顧客：多多綠\n顧客：沒有多多綠啊，那蜜桃紅烏龍\n顧客：少冰",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75)], "total":75}))

# 一杯不在菜單 + 一杯正常（顧客沒有改選）
examples.append(make(
    "顧客：一杯珍珠奶茶\n顧客：還有一杯桂花輕烏龍鮮奶半糖少冰",
    {"orders": [
        not_on_menu_order("珍珠奶茶","本店無珍珠奶茶"),
        order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":65}))

# ============================================================
# 場景 H：確認語氣 / 猶豫不決
# ============================================================

examples.append(make(
    "顧客：嗯...桂花輕烏龍\n顧客：鮮奶的好了\n顧客：半糖\n顧客：冰...少冰",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：我想想...三窨十五茉好了\n顧客：奶茶\n顧客：欸其實要鮮奶好了\n顧客：大杯無糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","L","少冰","無糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：有什麼推薦？\n顧客：那來杯桂花輕烏龍奶蓋好了",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

examples.append(make(
    "顧客：朱槿普洱紅鮮奶\n顧客：等一下，半糖...不對，微糖好了\n顧客：少冰",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","M","少冰","微糖",[],1,60)], "total":60}))

# Write out
with open("/Users/xiechengru/ug-finetune/data/round4.jsonl", "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} multi-turn examples")
