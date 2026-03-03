#!/usr/bin/env python3
"""Round 5: 大幅加強中途修改範例 — 單杯修改、多杯指定修改、多重修改"""
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

examples = []

# ============================================================
# A. 單杯修改 — 甜度 (各種觸發詞)
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：改微糖",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","微糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖去冰\n顧客：甜度改無糖",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：琥珀鐵觀音鮮奶無糖少冰\n顧客：算了還是少糖好了",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","少冰","少糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：金杯蜜香紅奶茶大杯半糖去冰\n顧客：糖度改正常糖",
    {"orders": [order("金杯蜜香紅","rich_milk_tea","L","去冰","正常糖",[],1,70)], "total":70}))

examples.append(make(
    "顧客：茶花烏龍鮮奶半糖少冰\n顧客：不對不對，要無糖",
    {"orders": [order("茶花烏龍","fresh_milk_tea","M","少冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：朱槿普洱紅鮮奶微糖去冰\n顧客：幫我改半糖",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","M","去冰","半糖",[],1,60)], "total":60}))

examples.append(make(
    "顧客：米香玉露菁鮮奶半糖少冰\n顧客：啊等等，改無糖",
    {"orders": [order("米香玉露菁","fresh_milk_tea","M","少冰","無糖",[],1,60)], "total":60}))

# ============================================================
# B. 單杯修改 — 冰量
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：冰改去冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","去冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶無糖少冰\n顧客：冰量改微冰就好",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","微冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖去冰\n顧客：其實我要熱的",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","M","熱飲","半糖",[],1,60)], "total":60}))

examples.append(make(
    "顧客：琥珀鐵觀音奶茶微糖正常冰\n顧客：冰少一點好了，少冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","M","少冰","微糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：茶花烏龍鮮奶半糖微冰\n顧客：不要微冰了，改去冰",
    {"orders": [order("茶花烏龍","fresh_milk_tea","M","去冰","半糖",[],1,65)], "total":65}))

# ============================================================
# C. 單杯修改 — 尺寸
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：改大杯",
    {"orders": [order("三窨十五茉","fresh_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶大杯無糖去冰\n顧客：改中杯就好",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：要大的",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","半糖",[],1,70)], "total":70}))

examples.append(make(
    "顧客：琥珀鐵觀音奶茶大杯微糖去冰\n顧客：其實中杯就夠了",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","M","去冰","微糖",[],1,65)], "total":65}))

# ============================================================
# D. 單杯修改 — 加料增減
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：欸幫我加茶凍",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80)], "total":80}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖少冰加茶凍\n顧客：茶凍不要了",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖去冰加燕麥粒\n顧客：燕麥粒換茶凍",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","M","去冰","半糖",["紅烏龍茶凍"],1,75)], "total":75}))

examples.append(make(
    "顧客：茶花烏龍鮮奶大杯半糖少冰\n顧客：再加茶凍跟燕麥粒",
    {"orders": [order("茶花烏龍","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍","燕麥粒"],1,105)], "total":105}))

examples.append(make(
    "顧客：琥珀鐵觀音奶茶半糖去冰加茶凍加燕麥粒\n顧客：燕麥粒不要了",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","M","去冰","半糖",["紅烏龍茶凍"],1,80)], "total":80}))

# ============================================================
# E. 單杯修改 — 類別切換
# ============================================================

examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：改奶茶好了",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：茶花紅烏龍奶茶半糖去冰\n顧客：算了改純茶",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","半糖",[],1,45)], "total":45}))

examples.append(make(
    "顧客：桂花輕烏龍純茶無糖去冰\n顧客：還是改奶蓋好了",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,"去冰","無糖",[],1,95)], "total":95}))

examples.append(make(
    "顧客：三窨十五茉奶茶半糖少冰\n顧客：換鮮奶的",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

# ============================================================
# F. 單杯修改 — 同時改多項
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：改無糖去冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","去冰","無糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖少冰\n顧客：改大杯微糖",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","L","少冰","微糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：改大杯無糖去冰加茶凍",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",["紅烏龍茶凍"],1,85)], "total":85}))

examples.append(make(
    "顧客：琥珀鐵觀音奶茶大杯正常糖正常冰\n顧客：改中杯半糖少冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：茶花烏龍鮮奶半糖少冰\n顧客：改大杯然後加燕麥粒",
    {"orders": [order("茶花烏龍","fresh_milk_tea","L","少冰","半糖",["燕麥粒"],1,90)], "total":90}))

# ============================================================
# G. 多杯 — 用「第N杯」序號指定修改 (重點加強)
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍奶茶無糖去冰\n顧客：第一杯改微糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","微糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖少冰\n顧客：再一杯金杯蜜香紅鮮奶無糖去冰\n顧客：第二杯改半糖",
    {"orders": [
        order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65),
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","半糖",[],1,60),
    ], "total":125}))

examples.append(make(
    "顧客：琥珀鐵觀音鮮奶大杯半糖少冰\n顧客：再一杯茶花烏龍奶茶無糖去冰\n顧客：第一杯改無糖",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","無糖",[],1,75),
        order("茶花烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":140}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：還要一杯三窨十五茉奶茶無糖去冰\n顧客：第一杯改大杯",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","L","少冰","半糖",[],1,70),
        order("三窨十五茉","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":135}))

examples.append(make(
    "顧客：朱槿普洱紅鮮奶半糖少冰\n顧客：再一杯米香玉露菁鮮奶無糖去冰\n顧客：第二杯改半糖少冰",
    {"orders": [
        order("朱槿普洱紅","fresh_milk_tea","M","少冰","半糖",[],1,60),
        order("米香玉露菁","fresh_milk_tea","M","少冰","半糖",[],1,60),
    ], "total":120}))

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍奶茶半糖去冰\n顧客：第一杯加茶凍",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","半糖",[],1,65),
    ], "total":145}))

examples.append(make(
    "顧客：茶花烏龍鮮奶半糖少冰\n顧客：再一杯琥珀鐵觀音奶茶無糖去冰\n顧客：第二杯改大杯加燕麥粒",
    {"orders": [
        order("茶花烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("琥珀鐵觀音","rich_milk_tea","L","去冰","無糖",["燕麥粒"],1,90),
    ], "total":155}))

examples.append(make(
    "顧客：大杯金杯蜜香紅鮮奶半糖少冰\n顧客：再一杯朱槿普洱紅奶茶微糖去冰\n顧客：第一杯改微糖去冰",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","L","去冰","微糖",[],1,70),
        order("朱槿普洱紅","rich_milk_tea","M","去冰","微糖",[],1,60),
    ], "total":130}))

# ============================================================
# H. 多杯 — 用品名指定修改 (重點加強)
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍奶茶無糖去冰\n顧客：茉莉那杯改微糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","微糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖少冰\n顧客：還要一杯琥珀鐵觀音鮮奶無糖去冰\n顧客：鐵觀音改半糖",
    {"orders": [
        order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65),
        order("琥珀鐵觀音","fresh_milk_tea","M","去冰","半糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：再一杯茶花烏龍奶茶無糖去冰\n顧客：蜜香紅那杯改大杯",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","L","少冰","半糖",[],1,70),
        order("茶花烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":135}))

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯朱槿普洱紅奶茶微糖去冰\n顧客：普洱那杯加茶凍",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("朱槿普洱紅","rich_milk_tea","M","去冰","微糖",["紅烏龍茶凍"],1,75),
    ], "total":140}))

examples.append(make(
    "顧客：琥珀鐵觀音鮮奶大杯半糖少冰\n顧客：再一杯米香玉露菁鮮奶無糖去冰\n顧客：玉露那杯改大杯",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",[],1,75),
        order("米香玉露菁","fresh_milk_tea","L","去冰","無糖",[],1,70),
    ], "total":145}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖少冰加茶凍\n顧客：再一杯金杯蜜香紅鮮奶無糖去冰\n顧客：桂花那杯茶凍不要了",
    {"orders": [
        order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65),
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","無糖",[],1,60),
    ], "total":125}))

examples.append(make(
    "顧客：大杯三窨十五茉鮮奶半糖去冰\n顧客：再來一杯茶花烏龍奶茶微糖少冰\n顧客：茶花那杯改大杯加燕麥粒",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","L","去冰","半糖",[],1,75),
        order("茶花烏龍","rich_milk_tea","L","少冰","微糖",["燕麥粒"],1,90),
    ], "total":165}))

# ============================================================
# I. 多杯 — 修改後再追加 / 連續修改
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：改無糖\n顧客：再一杯桂花輕烏龍奶茶半糖去冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","無糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","半糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：琥珀鐵觀音鮮奶半糖少冰\n顧客：再一杯金杯蜜香紅奶茶無糖去冰\n顧客：兩杯都改大杯",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",[],1,75),
        order("金杯蜜香紅","rich_milk_tea","L","去冰","無糖",[],1,70),
    ], "total":145}))

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍奶茶半糖去冰\n顧客：兩杯都改無糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","無糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：改大杯\n顧客：再加茶凍\n顧客：啊甜度改微糖",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","微糖",["紅烏龍茶凍"],1,85)], "total":85}))

# ============================================================
# J. 三杯 + 指定修改
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍奶茶無糖去冰\n顧客：還要一杯蜜桃紅烏龍少冰\n顧客：第一杯改微糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","微糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
        order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75),
    ], "total":205}))

examples.append(make(
    "顧客：琥珀鐵觀音鮮奶半糖少冰\n顧客：再一杯茶花烏龍奶茶無糖去冰\n顧客：還要一杯朱槿普洱紅純茶微糖微冰\n顧客：第二杯改大杯",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("茶花烏龍","rich_milk_tea","L","去冰","無糖",[],1,75),
        order("朱槿普洱紅","pure_tea",None,"微冰","微糖",[],1,40),
    ], "total":180}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：再一杯三窨十五茉奶茶微糖去冰\n顧客：還要一杯桂花輕烏龍奶蓋\n顧客：第三杯甜度半糖",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","M","少冰","半糖",[],1,60),
        order("三窨十五茉","rich_milk_tea","M","去冰","微糖",[],1,65),
        order("桂花輕烏龍","cloud_velvet",None,None,"半糖",[],1,95),
    ], "total":220}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖少冰\n顧客：再一杯金杯蜜香紅鮮奶無糖去冰\n顧客：還要一杯茶花紅烏龍純茶微糖微冰\n顧客：茉莉...不對，蜜香紅那杯加茶凍",
    {"orders": [
        order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65),
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","無糖",["紅烏龍茶凍"],1,75),
        order("茶花紅烏龍","pure_tea",None,"微冰","微糖",[],1,45),
    ], "total":185}))

# ============================================================
# K. 口語化修改 — 更自然的表達
# ============================================================

examples.append(make(
    "顧客：桂花輕烏龍奶茶大杯半糖少冰\n顧客：欸等一下，我不要大杯了，中杯就好",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：可以幫我加茶凍嗎\n顧客：然後改無糖",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","M","少冰","無糖",["紅烏龍茶凍"],1,75)], "total":75}))

examples.append(make(
    "顧客：三窨十五茉奶茶半糖去冰\n顧客：想一想還是大杯好了",
    {"orders": [order("三窨十五茉","rich_milk_tea","L","去冰","半糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：琥珀鐵觀音鮮奶半糖少冰\n顧客：對了，幫我多加一個燕麥粒\n顧客：然後升大杯",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",["燕麥粒"],1,90)], "total":90}))

examples.append(make(
    "顧客：茶花烏龍奶茶半糖少冰\n顧客：糖少一點好了，微糖\n顧客：冰也少一點，微冰",
    {"orders": [order("茶花烏龍","rich_milk_tea","M","微冰","微糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：朱槿普洱紅鮮奶半糖少冰\n顧客：sorry 改無糖好了",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","M","少冰","無糖",[],1,60)], "total":60}))

examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖去冰\n顧客：再一杯三窨十五茉奶茶無糖少冰\n顧客：啊對了桂花那杯幫我加茶凍",
    {"orders": [
        order("桂花輕烏龍","fresh_milk_tea","M","去冰","半糖",["紅烏龍茶凍"],1,80),
        order("三窨十五茉","rich_milk_tea","M","少冰","無糖",[],1,65),
    ], "total":145}))

examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：再來一杯琥珀鐵觀音奶茶微糖去冰\n顧客：蜜香紅那杯幫我升大杯然後改無糖",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","L","少冰","無糖",[],1,70),
        order("琥珀鐵觀音","rich_milk_tea","M","去冰","微糖",[],1,65),
    ], "total":135}))

# ============================================================
# L. 修改品項本身 — 整杯換掉
# ============================================================

examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：等等，我不要茉莉了，改桂花輕烏龍",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：金杯蜜香紅奶茶半糖去冰\n顧客：換琥珀鐵觀音好了，其他一樣",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","M","去冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：再一杯茶花烏龍奶茶無糖去冰\n顧客：第一杯換三窨十五茉好了",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("茶花烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

# Write out
with open("/Users/xiechengru/ug-finetune/data/round5.jsonl", "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} modification-focused examples")
