#!/usr/bin/env python3
"""Round 6: 不相干對話、閒聊夾帶點單、數量>1、模糊不完整"""
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
# A. 純粹不相干對話 — 回傳空訂單 + note
# ============================================================

examples.append(make(
    "廁所在哪裡？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問廁所位置"}))

examples.append(make(
    "你們幾點關門？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問營業時間"}))

examples.append(make(
    "可以刷卡嗎？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問付款方式"}))

examples.append(make(
    "有Wi-Fi嗎？密碼是什麼？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問Wi-Fi"}))

examples.append(make(
    "今天天氣好熱喔",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客閒聊"}))

examples.append(make(
    "請問有位子嗎？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問座位"}))

examples.append(make(
    "我想找你們店長",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客要找店長"}))

examples.append(make(
    "你們有賣吃的嗎？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問餐點"}))

examples.append(make(
    "外面可以停車嗎？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問停車"}))

examples.append(make(
    "有沒有集點卡？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問集點"}))

examples.append(make(
    "你們的杯子好可愛",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客閒聊"}))

examples.append(make(
    "我只是看看菜單",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客瀏覽菜單中"}))

examples.append(make(
    "請問洗手間在哪邊",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問洗手間"}))

examples.append(make(
    "可以外帶嗎？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問外帶"}))

examples.append(make(
    "你們有做UberEats嗎？",
    {"orders": [], "total": 0, "note": "非點餐內容，顧客詢問外送服務"}))

# ============================================================
# B. 閒聊夾帶點單 — 忽略閒聊、擷取訂單
# ============================================================

examples.append(make(
    "好熱喔，來杯去冰的茶花紅烏龍純茶無糖",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "走了好遠才找到你們，先給我一杯三窨十五茉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "朋友推薦來的，我要一杯桂花輕烏龍奶蓋",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

examples.append(make(
    "上次的金杯蜜香紅很好喝，再來一杯，鮮奶的大杯無糖去冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70)], "total":70}))

examples.append(make(
    "等下要開會好累，給我一杯琥珀鐵觀音奶茶大杯半糖少冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))

examples.append(make(
    "你們裝潢好好看！我要一杯朱槿普洱紅純茶，無糖去冰",
    {"orders": [order("朱槿普洱紅","pure_tea",None,"去冰","無糖",[],1,40)], "total":40}))

examples.append(make(
    "剛好路過看到，點一杯葡柚十五茉好了，少冰",
    {"orders": [order("葡柚十五茉","fruit_tea",None,"少冰",None,[],1,80)], "total":80}))

examples.append(make(
    "第一次來不知道點什麼，那來杯蜜桃紅烏龍好了，少冰",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75)], "total":75}))

examples.append(make(
    "天氣好冷，有熱的嗎？我要一杯桂花輕烏龍鮮奶，半糖熱飲",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","熱飲","半糖",[],1,65)], "total":65}))

examples.append(make(
    "今天心情好好，來杯茶花烏龍奶茶加茶凍，大杯微糖少冰",
    {"orders": [order("茶花烏龍","rich_milk_tea","L","少冰","微糖",["紅烏龍茶凍"],1,90)], "total":90}))

# ============================================================
# C. 閒聊夾帶多輪 — 夾雜不相干的話
# ============================================================

examples.append(make(
    "顧客：你們生意很好耶\n顧客：我要三窨十五茉鮮奶\n顧客：半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：桂花輕烏龍奶茶半糖少冰\n顧客：對了你們有賣蛋糕嗎\n顧客：還要一杯茶花紅烏龍純茶無糖去冰",
    {"orders": [
        order("桂花輕烏龍","rich_milk_tea","M","少冰","半糖",[],1,65),
        order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":110}))

examples.append(make(
    "顧客：先給我一杯金杯蜜香紅鮮奶無糖去冰\n顧客：你們幾點關啊\n顧客：再一杯米香玉露菁純茶少糖少冰",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","無糖",[],1,60),
        order("米香玉露菁","pure_tea",None,"少冰","少糖",[],1,40),
    ], "total":100}))

examples.append(make(
    "顧客：哇你們杯子好漂亮\n顧客：我想要琥珀鐵觀音\n顧客：鮮奶大杯半糖少冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：我朋友說你們茉莉很好喝\n顧客：那我也來一杯三窨十五茉奶茶\n顧客：無糖去冰\n顧客：可以加茶凍嗎",
    {"orders": [order("三窨十五茉","rich_milk_tea","M","去冰","無糖",["紅烏龍茶凍"],1,80)], "total":80}))

# ============================================================
# D. 數量 > 1 — qty 欄位
# ============================================================

examples.append(make(
    "兩杯三窨十五茉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,""),
                order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,"")], "total":130}))

examples.append(make(
    "三杯桂花輕烏龍純茶無糖去冰",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45,""),
                order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45,""),
                order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45,"")], "total":135}))

examples.append(make(
    "來兩杯金杯蜜香紅鮮奶大杯無糖去冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70,""),
                order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70,"")], "total":140}))

examples.append(make(
    "四杯蜜桃紅烏龍少冰",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75,""),
                order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75,""),
                order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75,""),
                order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75,"")], "total":300}))

examples.append(make(
    "兩杯琥珀鐵觀音奶茶大杯半糖少冰加茶凍",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,90,""),
                order("琥珀鐵觀音","rich_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,90,"")], "total":180}))

examples.append(make(
    "我要兩杯茶花紅烏龍奶蓋",
    {"orders": [order("茶花紅烏龍","cloud_velvet",None,None,None,[],1,95,""),
                order("茶花紅烏龍","cloud_velvet",None,None,None,[],1,95,"")], "total":190}))

# --- 多種品項各帶數量 ---
examples.append(make(
    "兩杯三窨十五茉鮮奶半糖少冰，一杯桂花輕烏龍純茶無糖去冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,""),
                order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,""),
                order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45,"")], "total":175}))

examples.append(make(
    "三杯金杯蜜香紅奶茶無糖去冰，兩杯蜜桃紅烏龍少冰",
    {"orders": [order("金杯蜜香紅","rich_milk_tea","M","去冰","無糖",[],1,60,""),
                order("金杯蜜香紅","rich_milk_tea","M","去冰","無糖",[],1,60,""),
                order("金杯蜜香紅","rich_milk_tea","M","去冰","無糖",[],1,60,""),
                order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75,""),
                order("蜜桃紅烏龍","fruit_tea",None,"少冰",None,[],1,75,"")], "total":330}))

# --- 口語化數量 ---
examples.append(make(
    "幫我來個兩杯朱槿普洱紅鮮奶微糖去冰",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","M","去冰","微糖",[],1,60,""),
                order("朱槿普洱紅","fresh_milk_tea","M","去冰","微糖",[],1,60,"")], "total":120}))

examples.append(make(
    "三窨十五茉鮮奶半糖少冰要兩杯",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,""),
                order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,"")], "total":130}))

# ============================================================
# E. 模糊/不完整 — 無法明確點單
# ============================================================

examples.append(make(
    "隨便來一杯",
    {"orders": [], "total": 0, "note": "顧客未指定品項，請店員推薦"}))

examples.append(make(
    "有什麼推薦的？",
    {"orders": [], "total": 0, "note": "顧客詢問推薦，請店員推薦"}))

examples.append(make(
    "給我一杯好喝的",
    {"orders": [], "total": 0, "note": "顧客未指定品項，請店員推薦"}))

examples.append(make(
    "最多人點的是什麼？",
    {"orders": [], "total": 0, "note": "顧客詢問熱門品項，請店員推薦"}))

examples.append(make(
    "有什麼冰的",
    {"orders": [], "total": 0, "note": "顧客詢問冰飲選項，請店員介紹"}))

examples.append(make(
    "不加奶的有哪些",
    {"orders": [], "total": 0, "note": "顧客詢問純茶選項，請店員介紹"}))

# ============================================================
# F. 模糊 → 接著明確點單（多輪）
# ============================================================

examples.append(make(
    "顧客：有什麼推薦的\n顧客：那來杯三窨十五茉鮮奶好了\n顧客：半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：你們什麼最好喝\n顧客：那我要桂花輕烏龍奶蓋",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

examples.append(make(
    "顧客：隨便來一杯\n顧客：好那給我金杯蜜香紅鮮奶\n顧客：大杯無糖去冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","去冰","無糖",[],1,70)], "total":70}))

examples.append(make(
    "顧客：有沒有不甜的推薦\n顧客：那來杯茶花紅烏龍純茶\n顧客：無糖去冰",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

# ============================================================
# G. 數量+閒聊+多輪混合
# ============================================================

examples.append(make(
    "顧客：我們三個人\n顧客：兩杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍奶蓋",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,""),
                order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65,""),
                order("桂花輕烏龍","cloud_velvet",None,None,None,[],1,95,"")], "total":225}))

examples.append(make(
    "顧客：幫辦公室的人點\n顧客：四杯琥珀鐵觀音奶茶半糖少冰\n顧客：都要大杯",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","L","少冰","半糖",[],1,75,""),
                order("琥珀鐵觀音","rich_milk_tea","L","少冰","半糖",[],1,75,""),
                order("琥珀鐵觀音","rich_milk_tea","L","少冰","半糖",[],1,75,""),
                order("琥珀鐵觀音","rich_milk_tea","L","少冰","半糖",[],1,75,"")], "total":300}))

examples.append(make(
    "顧客：開會要用的\n顧客：三杯金杯蜜香紅鮮奶無糖去冰\n顧客：兩杯三窨十五茉純茶無糖去冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","M","去冰","無糖",[],1,60,""),
                order("金杯蜜香紅","fresh_milk_tea","M","去冰","無糖",[],1,60,""),
                order("金杯蜜香紅","fresh_milk_tea","M","去冰","無糖",[],1,60,""),
                order("三窨十五茉","pure_tea",None,"去冰","無糖",[],1,45,""),
                order("三窨十五茉","pure_tea",None,"去冰","無糖",[],1,45,"")], "total":270}))

# Write out
with open("/Users/xiechengru/ug-finetune/data/round6.jsonl", "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} Round 6 examples")
