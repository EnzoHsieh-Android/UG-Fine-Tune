#!/usr/bin/env python3
"""Round 3: 針對三個頑固問題大幅生成訓練資料"""
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
# 問題 1：大杯 → L 映射 (35 examples)
# 各種說法：大杯、大的、L、大杯的、要大的、升級大杯
# ============================================================

# --- fresh_milk_tea 大杯 ---
examples.append(make("大杯三窨十五茉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))
examples.append(make("大杯桂花輕烏龍鮮奶茶",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","L",None,None,[],1,75)], "total":75}))
examples.append(make("大的茶花烏龍鮮奶少糖去冰",
    {"orders": [order("茶花烏龍","fresh_milk_tea","L","去冰","少糖",[],1,75)], "total":75}))
examples.append(make("L琥珀鐵觀音鮮奶正常糖正常冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","L","正常冰","正常糖",[],1,75)], "total":75}))
examples.append(make("金杯蜜香紅鮮奶要大杯的，微糖少冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","微糖",[],1,70)], "total":70}))
examples.append(make("大杯朱槿普洱紅鮮奶無糖去冰",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","L","去冰","無糖",[],1,70)], "total":70}))
examples.append(make("米香玉露菁鮮奶升級大杯，半糖微冰",
    {"orders": [order("米香玉露菁","fresh_milk_tea","L","微冰","半糖",[],1,70)], "total":70}))

# --- rich_milk_tea 大杯 ---
examples.append(make("大杯三窨十五茉奶茶少糖少冰",
    {"orders": [order("三窨十五茉","rich_milk_tea","L","少冰","少糖",[],1,75)], "total":75}))
examples.append(make("桂花輕烏龍奶茶大的，無糖去冰",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","L","去冰","無糖",[],1,75)], "total":75}))
examples.append(make("大杯茶花烏龍奶茶半糖少冰",
    {"orders": [order("茶花烏龍","rich_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))
examples.append(make("琥珀鐵觀音奶茶L微糖微冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","L","微冰","微糖",[],1,75)], "total":75}))
examples.append(make("大杯金杯蜜香紅奶茶正常糖正常冰",
    {"orders": [order("金杯蜜香紅","rich_milk_tea","L","正常冰","正常糖",[],1,70)], "total":70}))
examples.append(make("朱槿普洱紅奶茶要大的少糖去冰",
    {"orders": [order("朱槿普洱紅","rich_milk_tea","L","去冰","少糖",[],1,70)], "total":70}))
examples.append(make("大杯米香玉露菁奶茶無糖少冰",
    {"orders": [order("米香玉露菁","rich_milk_tea","L","少冰","無糖",[],1,70)], "total":70}))

# --- 大杯 + addon（unit_price 必須是算好的數字）---
examples.append(make("大杯桂花輕烏龍鮮奶加茶凍，半糖少冰",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,90)], "total":90}))
examples.append(make("大杯三窨十五茉奶茶加燕麥粒，無糖去冰",
    {"orders": [order("三窨十五茉","rich_milk_tea","L","去冰","無糖",["燕麥粒"],1,90)], "total":90}))
examples.append(make("大的茶花烏龍鮮奶加茶凍加燕麥粒",
    {"orders": [order("茶花烏龍","fresh_milk_tea","L",None,None,["紅烏龍茶凍","燕麥粒"],1,105)], "total":105}))
examples.append(make("大杯琥珀鐵觀音奶茶加茶凍，微糖少冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","L","少冰","微糖",["紅烏龍茶凍"],1,90)], "total":90}))
examples.append(make("金杯蜜香紅鮮奶大的加燕麥粒半糖微冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","微冰","半糖",["燕麥粒"],1,85)], "total":85}))

# --- 對比：中杯 / 沒指定 → M ---
examples.append(make("中杯桂花輕烏龍鮮奶半糖少冰",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))
examples.append(make("三窨十五茉奶茶少糖去冰",
    {"orders": [order("三窨十五茉","rich_milk_tea","M","去冰","少糖",[],1,65)], "total":65}))
examples.append(make("中的琥珀鐵觀音鮮奶正常糖正常冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","正常冰","正常糖",[],1,65)], "total":65}))

# --- 大杯 mixed orders ---
examples.append(make("一杯大杯桂花輕烏龍鮮奶，一杯中杯茶花烏龍奶茶，都半糖少冰",
    {"orders": [
        order("桂花輕烏龍","fresh_milk_tea","L","少冰","半糖",[],1,75),
        order("茶花烏龍","rich_milk_tea","M","少冰","半糖",[],1,65),
    ], "total":140}))
examples.append(make("兩杯大杯金杯蜜香紅鮮奶，都無糖去冰",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70),
        order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70),
    ], "total":140}))
examples.append(make("大杯三窨十五茉鮮奶微糖少冰，再一杯朱槿普洱紅純茶無糖去冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","L","少冰","微糖",[],1,75),
        order("朱槿普洱紅","pure_tea","null","去冰","無糖",[],1,40),
    ], "total":115}))

# --- 口語 + 大杯 ---
examples.append(make("茉莉鮮奶大杯的半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))
examples.append(make("大杯鐵觀音鮮奶無糖去冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","L","去冰","無糖",[],1,75)], "total":75}))
examples.append(make("桂花奶茶大的微糖微冰",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","L","微冰","微糖",[],1,75)], "total":75}))
examples.append(make("紅烏龍鮮奶大杯半糖少冰加茶凍",
    {"orders": [order("茶花紅烏龍","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,90)], "total":90}))
examples.append(make("普洱奶茶大的少糖去冰",
    {"orders": [order("朱槿普洱紅","rich_milk_tea","L","去冰","少糖",[],1,70)], "total":70}))
examples.append(make("蜜香紅鮮奶大杯加燕麥粒無糖少冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","無糖",["燕麥粒"],1,85)], "total":85}))
examples.append(make("玉露奶茶要大杯的半糖微冰",
    {"orders": [order("米香玉露菁","rich_milk_tea","L","微冰","半糖",[],1,70)], "total":70}))

# ============================================================
# 問題 2：not_on_menu 偵測 (35 examples)
# ============================================================

# --- 單純不在菜單上的飲料 ---
examples.append(make("一杯珍珠奶茶",
    {"orders": [not_on_menu_order("珍珠奶茶","本店無此品項，建議參考UG奶茶系列")], "total":0}))
examples.append(make("我要珍珠奶茶半糖少冰",
    {"orders": [not_on_menu_order("珍珠奶茶","本店無珍珠奶茶，建議參考UG奶茶系列")], "total":0}))
examples.append(make("來一杯珍奶",
    {"orders": [not_on_menu_order("珍珠奶茶","本店無珍珠奶茶")], "total":0}))
examples.append(make("綠茶一杯",
    {"orders": [not_on_menu_order("綠茶","本店無綠茶，建議參考研選純茶系列")], "total":0}))
examples.append(make("紅茶半糖少冰",
    {"orders": [not_on_menu_order("紅茶","本店無紅茶，建議參考金杯蜜香紅")], "total":0}))
examples.append(make("一杯拿鐵",
    {"orders": [not_on_menu_order("拿鐵","本店無咖啡類飲品")], "total":0}))
examples.append(make("美式咖啡",
    {"orders": [not_on_menu_order("美式咖啡","本店無咖啡類飲品")], "total":0}))
examples.append(make("卡布奇諾一杯",
    {"orders": [not_on_menu_order("卡布奇諾","本店無咖啡類飲品")], "total":0}))
examples.append(make("可可歐蕾",
    {"orders": [not_on_menu_order("可可歐蕾","本店無此品項")], "total":0}))
examples.append(make("我要多多綠",
    {"orders": [not_on_menu_order("多多綠","本店無多多綠")], "total":0}))
examples.append(make("冬瓜茶少糖",
    {"orders": [not_on_menu_order("冬瓜茶","本店無冬瓜茶")], "total":0}))
examples.append(make("四季春大杯半糖",
    {"orders": [not_on_menu_order("四季春","本店無四季春")], "total":0}))
examples.append(make("百香果綠茶少冰",
    {"orders": [not_on_menu_order("百香果綠茶","本店無百香果綠茶，建議參考果香四溢系列")], "total":0}))
examples.append(make("柚子茶一杯熱的",
    {"orders": [not_on_menu_order("柚子茶","本店無柚子茶")], "total":0}))
examples.append(make("奶綠半糖去冰",
    {"orders": [not_on_menu_order("奶綠","本店無奶綠")], "total":0}))
examples.append(make("仙草奶凍",
    {"orders": [not_on_menu_order("仙草奶凍","本店無此品項")], "total":0}))
examples.append(make("波霸鮮奶",
    {"orders": [not_on_menu_order("波霸鮮奶","本店無波霸鮮奶，建議參考牧場直達系列")], "total":0}))
examples.append(make("抹茶拿鐵大杯",
    {"orders": [not_on_menu_order("抹茶拿鐵","本店無抹茶拿鐵")], "total":0}))
examples.append(make("我想要一杯芋頭鮮奶",
    {"orders": [not_on_menu_order("芋頭鮮奶","本店無芋頭鮮奶，建議參考牧場直達系列")], "total":0}))
examples.append(make("檸檬紅茶微糖去冰",
    {"orders": [not_on_menu_order("檸檬紅茶","本店無檸檬紅茶，建議參考青檸桂蜜")], "total":0}))
examples.append(make("烏龍奶茶半糖",
    {"orders": [not_on_menu_order("烏龍奶茶","本店無烏龍奶茶，建議參考茶花烏龍奶茶")], "total":0}))
examples.append(make("養樂多綠茶少冰少糖",
    {"orders": [not_on_menu_order("養樂多綠茶","本店無此品項")], "total":0}))
examples.append(make("椰子水",
    {"orders": [not_on_menu_order("椰子水","本店無此品項")], "total":0}))
examples.append(make("黑糖鮮奶半糖去冰",
    {"orders": [not_on_menu_order("黑糖鮮奶","本店無黑糖鮮奶，建議參考牧場直達系列")], "total":0}))
examples.append(make("薄荷巧克力",
    {"orders": [not_on_menu_order("薄荷巧克力","本店無此品項")], "total":0}))

# --- 混合：一個在菜單，一個不在 ---
examples.append(make("一杯珍珠奶茶，一杯三窨十五茉純茶無糖去冰",
    {"orders": [
        not_on_menu_order("珍珠奶茶","本店無珍珠奶茶"),
        order("三窨十五茉","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":45}))
examples.append(make("綠茶一杯跟大杯桂花輕烏龍鮮奶半糖少冰",
    {"orders": [
        not_on_menu_order("綠茶","本店無綠茶"),
        order("桂花輕烏龍","fresh_milk_tea","L","少冰","半糖",[],1,75),
    ], "total":75}))
examples.append(make("拿鐵一杯還有茶花紅烏龍奶蓋",
    {"orders": [
        not_on_menu_order("拿鐵","本店無咖啡類飲品"),
        order("茶花紅烏龍","cloud_velvet",None,None,None,[],1,95),
    ], "total":95}))
examples.append(make("我要紅茶半糖和蜜桃紅烏龍少冰",
    {"orders": [
        not_on_menu_order("紅茶","本店無紅茶，建議參考金杯蜜香紅"),
        order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75),
    ], "total":75}))
examples.append(make("大杯波霸奶茶加一杯米香玉露菁鮮奶無糖微冰",
    {"orders": [
        not_on_menu_order("波霸奶茶","本店無波霸奶茶"),
        order("米香玉露菁","fresh_milk_tea","M","微冰","無糖",[],1,60),
    ], "total":60}))

# --- 不在菜單的加料 ---
examples.append(make("三窨十五茉鮮奶加珍珠半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,"本店無珍珠，可選紅烏龍茶凍或燕麥粒")], "total":65}))
examples.append(make("桂花輕烏龍奶茶加布丁去冰無糖",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65,"本店無布丁，可選紅烏龍茶凍或燕麥粒")], "total":65}))
examples.append(make("大杯茶花烏龍鮮奶加芋圓微糖少冰",
    {"orders": [order("茶花烏龍","fresh_milk_tea","L","少冰","微糖",[],1,75,"本店無芋圓，可選紅烏龍茶凍或燕麥粒")], "total":75}))
examples.append(make("琥珀鐵觀音鮮奶加椰果半糖去冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","去冰","半糖",[],1,65,"本店無椰果，可選紅烏龍茶凍或燕麥粒")], "total":65}))
examples.append(make("大杯金杯蜜香紅奶茶加粉條正常糖正常冰",
    {"orders": [order("金杯蜜香紅","rich_milk_tea","L","正常冰","正常糖",[],1,70,"本店無粉條，可選紅烏龍茶凍或燕麥粒")], "total":70}))

# ============================================================
# 問題 3：unit_price 必須是計算好的數字 (30 examples)
# 每個有 addon 的範例都強調 unit_price 是最終數字
# ============================================================

# --- M size + 1 addon = base_M + 15 ---
examples.append(make("三窨十五茉鮮奶加茶凍半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80)], "total":80}))
examples.append(make("桂花輕烏龍奶茶加燕麥粒無糖去冰",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",["燕麥粒"],1,80)], "total":80}))
examples.append(make("茶花烏龍鮮奶加茶凍正常糖正常冰",
    {"orders": [order("茶花烏龍","fresh_milk_tea","M","正常冰","正常糖",["紅烏龍茶凍"],1,80)], "total":80}))
examples.append(make("琥珀鐵觀音鮮奶加燕麥粒微糖微冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","微冰","微糖",["燕麥粒"],1,80)], "total":80}))
examples.append(make("金杯蜜香紅奶茶加茶凍少糖少冰",
    {"orders": [order("金杯蜜香紅","rich_milk_tea","M","少冰","少糖",["紅烏龍茶凍"],1,75)], "total":75}))
examples.append(make("朱槿普洱紅鮮奶加燕麥粒半糖去冰",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","M","去冰","半糖",["燕麥粒"],1,75)], "total":75}))
examples.append(make("米香玉露菁奶茶加茶凍無糖少冰",
    {"orders": [order("米香玉露菁","rich_milk_tea","M","少冰","無糖",["紅烏龍茶凍"],1,75)], "total":75}))

# --- L size + 1 addon = base_L + 15 ---
examples.append(make("大杯三窨十五茉鮮奶加茶凍半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,90)], "total":90}))
examples.append(make("大杯茶花烏龍奶茶加燕麥粒無糖去冰",
    {"orders": [order("茶花烏龍","rich_milk_tea","L","去冰","無糖",["燕麥粒"],1,90)], "total":90}))
examples.append(make("大杯金杯蜜香紅鮮奶加茶凍微糖微冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","微冰","微糖",["紅烏龍茶凍"],1,85)], "total":85}))
examples.append(make("大杯朱槿普洱紅奶茶加燕麥粒少糖少冰",
    {"orders": [order("朱槿普洱紅","rich_milk_tea","L","少冰","少糖",["燕麥粒"],1,85)], "total":85}))
examples.append(make("大杯米香玉露菁鮮奶加茶凍正常糖正常冰",
    {"orders": [order("米香玉露菁","fresh_milk_tea","L","正常冰","正常糖",["紅烏龍茶凍"],1,85)], "total":85}))

# --- M size + 2 addons = base_M + 30 ---
examples.append(make("三窨十五茉鮮奶加茶凍加燕麥粒半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍","燕麥粒"],1,95)], "total":95}))
examples.append(make("桂花輕烏龍奶茶加茶凍加燕麥粒無糖去冰",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",["紅烏龍茶凍","燕麥粒"],1,95)], "total":95}))
examples.append(make("金杯蜜香紅鮮奶加茶凍加燕麥粒微糖少冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","M","少冰","微糖",["紅烏龍茶凍","燕麥粒"],1,90)], "total":90}))

# --- L size + 2 addons = base_L + 30 ---
examples.append(make("大杯三窨十五茉鮮奶加茶凍加燕麥粒半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍","燕麥粒"],1,105)], "total":105}))
examples.append(make("大杯桂花輕烏龍奶茶加茶凍加燕麥粒無糖去冰",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","L","去冰","無糖",["紅烏龍茶凍","燕麥粒"],1,105)], "total":105}))
examples.append(make("大杯金杯蜜香紅鮮奶加茶凍加燕麥粒正常糖正常冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","正常冰","正常糖",["紅烏龍茶凍","燕麥粒"],1,100)], "total":100}))

# --- 純茶/果茶/雲頂 + addon ---
examples.append(make("三窨十五茉純茶加茶凍半糖去冰",
    {"orders": [order("三窨十五茉","pure_tea",None,"去冰","半糖",["紅烏龍茶凍"],1,60)], "total":60}))
examples.append(make("桂花輕烏龍純茶加燕麥粒微糖少冰",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"少冰","微糖",["燕麥粒"],1,60)], "total":60}))
examples.append(make("蜜桃紅烏龍加茶凍少冰",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,["紅烏龍茶凍"],1,90)], "total":90}))
examples.append(make("葡柚十五茉加茶凍加燕麥粒",
    {"orders": [order("葡柚十五茉","fruit_tea",None,None,None,["紅烏龍茶凍","燕麥粒"],1,110)], "total":110}))
examples.append(make("桂花輕烏龍奶蓋加茶凍",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,None,None,["紅烏龍茶凍"],1,110)], "total":110}))
examples.append(make("茶花紅烏龍奶蓋加燕麥粒",
    {"orders": [order("茶花紅烏龍","cloud_velvet",None,None,None,["燕麥粒"],1,110)], "total":110}))

# --- multi-item with addons (unit_price 都是數字) ---
examples.append(make("一杯三窨十五茉鮮奶加茶凍半糖少冰，一杯大杯桂花輕烏龍奶茶加燕麥粒無糖去冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80),
        order("桂花輕烏龍","rich_milk_tea","L","去冰","無糖",["燕麥粒"],1,90),
    ], "total":170}))
examples.append(make("大杯琥珀鐵觀音鮮奶加茶凍微糖少冰，再加一杯蜜桃紅烏龍加燕麥粒",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","微糖",["紅烏龍茶凍"],1,90),
        order("蜜桃紅烏龍","fruit_tea",None,None,None,["燕麥粒"],1,90),
    ], "total":180}))
examples.append(make("茶花紅烏龍純茶加茶凍無糖去冰，跟一杯大杯金杯蜜香紅鮮奶加燕麥粒半糖少冰",
    {"orders": [
        order("茶花紅烏龍","pure_tea",None,"去冰","無糖",["紅烏龍茶凍"],1,60),
        order("金杯蜜香紅","fresh_milk_tea","L","少冰","半糖",["燕麥粒"],1,85),
    ], "total":145}))

# --- qty > 1 with addons ---
examples.append(make("兩杯三窨十五茉鮮奶加茶凍半糖少冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80),
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80),
    ], "total":160}))

# Write out
with open("/Users/xiechengru/ug-finetune/data/round3.jsonl", "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} examples")
