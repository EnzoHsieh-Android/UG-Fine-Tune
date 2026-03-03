#!/usr/bin/env python3
"""Round 7: 補強「閒聊/off-topic → 接著點餐」的多輪模式
問題：模型看到第一行是閒聊就回空 orders，忽略後續點餐行。
策略：大量範例教模型「看完所有行再判斷」。
"""
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
# A. Off-topic 問題 → 接著點餐（核心修正目標）
#    模式：顧客先問非點餐問題，接著點單
# ============================================================

# A1: 問營業時間 → 點餐
examples.append(make(
    "顧客：你們幾點關門？\n顧客：那來一杯桂花輕烏龍奶茶微糖去冰大杯",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","L","去冰","微糖",[],1,75)], "total":75}))

# A2: 問廁所 → 點餐
examples.append(make(
    "顧客：廁所在哪裡？\n顧客：好的謝謝，我要一杯三窨十五茉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

# A3: 問 Wi-Fi → 點餐
examples.append(make(
    "顧客：有Wi-Fi嗎？\n顧客：好，再幫我點一杯茶花紅烏龍純茶去冰無糖",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

# A4: 問停車 → 點餐
examples.append(make(
    "顧客：附近有停車場嗎\n顧客：先點一杯金杯蜜香紅鮮奶大杯無糖少冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","無糖",[],1,70)], "total":70}))

# A5: 問刷卡 → 點餐
examples.append(make(
    "顧客：可以刷卡嗎？\n顧客：那我要一杯琥珀鐵觀音鮮奶半糖少冰",
    {"orders": [order("琥珀鐵觀音","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

# A6: 問集點 → 點餐
examples.append(make(
    "顧客：你們有集點卡嗎\n顧客：我要一杯朱槿普洱紅純茶無糖去冰",
    {"orders": [order("朱槿普洱紅","pure_tea",None,"去冰","無糖",[],1,40)], "total":40}))

# A7: 問外送 → 點餐
examples.append(make(
    "顧客：你們有外送嗎\n顧客：沒關係那內用，給我一杯蜜桃紅烏龍少冰半糖",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,"少冰","半糖",[],1,75)], "total":75}))

# A8: 問座位 → 點餐
examples.append(make(
    "顧客：還有位子嗎\n顧客：好，那給我一杯桂花輕烏龍鮮奶微糖去冰",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","去冰","微糖",[],1,65)], "total":65}))

# A9: 問等候時間 → 點餐
examples.append(make(
    "顧客：現在要等很久嗎\n顧客：沒關係，我要一杯米香玉露菁純茶無糖少冰",
    {"orders": [order("米香玉露菁","pure_tea",None,"少冰","無糖",[],1,40)], "total":40}))

# A10: 問發票 → 點餐
examples.append(make(
    "顧客：可以開發票嗎\n顧客：好，來一杯葡柚十五茉少冰",
    {"orders": [order("葡柚十五茉","fruit_tea",None,"少冰",None,[],1,80)], "total":80}))

# ============================================================
# B. Off-topic → 點多杯
# ============================================================

# B1: 問營業時間 → 點兩杯
examples.append(make(
    "顧客：你們營業到幾點\n顧客：一杯三窨十五茉鮮奶半糖少冰，一杯桂花輕烏龍純茶無糖去冰",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65),
        order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":110}))

# B2: 問外帶 → 點兩杯
examples.append(make(
    "顧客：可以外帶嗎\n顧客：那幫我做兩杯琥珀鐵觀音奶茶無糖去冰",
    {"orders": [
        order("琥珀鐵觀音","rich_milk_tea","M","去冰","無糖",[],1,65),
        order("琥珀鐵觀音","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

# B3: 問優惠 → 點兩杯不同
examples.append(make(
    "顧客：有什麼優惠嗎\n顧客：好那一杯茶花紅烏龍純茶無糖去冰，一杯金杯蜜香紅鮮奶大杯半糖少冰",
    {"orders": [
        order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45),
        order("金杯蜜香紅","fresh_milk_tea","L","少冰","半糖",[],1,70),
    ], "total":115}))

# ============================================================
# C. 多行 off-topic → 最後點餐
# ============================================================

# C1: 兩行閒聊 → 點餐
examples.append(make(
    "顧客：你們幾點開門的\n顧客：裝潢好漂亮\n顧客：來一杯茶花烏龍鮮奶半糖少冰",
    {"orders": [order("茶花烏龍","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

# C2: 問問題 + 稱讚 → 點餐
examples.append(make(
    "顧客：有沒有停車位\n顧客：你們菜單很特別耶\n顧客：我要一杯桂花輕烏龍奶蓋",
    {"orders": [order("桂花輕烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

# C3: 三行閒聊 → 點餐
examples.append(make(
    "顧客：今天好熱\n顧客：你們有冷氣真好\n顧客：座位在哪裡\n顧客：點一杯青檸桂蜜少冰半糖",
    {"orders": [order("青檸桂蜜","fruit_tea",None,"少冰","半糖",[],1,65)], "total":65}))

# ============================================================
# D. Off-topic → 點餐 → 再閒聊（模型應只提取點餐部分）
# ============================================================

# D1: 問→點→問
examples.append(make(
    "顧客：可以用LINE Pay嗎\n顧客：我要三窨十五茉奶茶微糖去冰\n顧客：做好叫我一下",
    {"orders": [order("三窨十五茉","rich_milk_tea","M","去冰","微糖",[],1,65)], "total":65}))

# D2: 閒聊→點→閒聊
examples.append(make(
    "顧客：下雨天生意怎麼樣\n顧客：一杯茶花紅烏龍純茶無糖少冰\n顧客：等一下還要趕回公司",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"少冰","無糖",[],1,45)], "total":45}))

# D3: 問→點兩杯→問
examples.append(make(
    "顧客：你們外帶袋要錢嗎\n顧客：一杯金杯蜜香紅鮮奶半糖少冰\n顧客：再一杯朱槿普洱紅純茶無糖去冰\n顧客：大概幾分鐘會好",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","M","少冰","半糖",[],1,60),
        order("朱槿普洱紅","pure_tea",None,"去冰","無糖",[],1,40),
    ], "total":100}))

# ============================================================
# E. 帶感嘆詞/情緒的 off-topic → 點餐
# ============================================================

# E1: 感嘆→點
examples.append(make(
    "顧客：哇排隊排好久\n顧客：終於到了，我要一杯茶花烏龍奶茶大杯半糖少冰",
    {"orders": [order("茶花烏龍","rich_milk_tea","L","少冰","半糖",[],1,75)], "total":75}))

# E2: 抱怨→點
examples.append(make(
    "顧客：外面好曬喔\n顧客：趕快給我一杯三窨十五茉鮮奶去冰無糖",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","去冰","無糖",[],1,65)], "total":65}))

# E3: 稱讚→點
examples.append(make(
    "顧客：你們店好可愛喔\n顧客：我要桂花輕烏龍鮮奶大杯少糖少冰",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","L","少冰","少糖",[],1,75)], "total":75}))

# E4: 心情→點
examples.append(make(
    "顧客：今天上班超累的\n顧客：來杯琥珀鐵觀音奶茶半糖少冰加茶凍",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80)], "total":80}))

# E5: 問路→點
examples.append(make(
    "顧客：請問捷運站怎麼走\n顧客：對了幫我點一杯米香玉露菁鮮奶半糖去冰",
    {"orders": [order("米香玉露菁","fresh_milk_tea","M","去冰","半糖",[],1,60)], "total":60}))

# ============================================================
# F. 帶「那」「好」「對了」等轉折語氣詞的點餐
#    強化模型辨識：off-topic 結束後出現轉折詞 = 開始點餐
# ============================================================

# F1
examples.append(make(
    "顧客：你們幾點關門\n顧客：那幫我來一杯茶花紅烏龍奶蓋",
    {"orders": [order("茶花紅烏龍","cloud_velvet",None,None,None,[],1,95)], "total":95}))

# F2
examples.append(make(
    "顧客：附近哪裡可以停車\n顧客：好，先給我一杯三窨十五茉純茶無糖去冰",
    {"orders": [order("三窨十五茉","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

# F3
examples.append(make(
    "顧客：有集點活動嗎\n顧客：對了我要一杯金杯蜜香紅奶茶大杯微糖少冰",
    {"orders": [order("金杯蜜香紅","rich_milk_tea","L","少冰","微糖",[],1,75)], "total":75}))

# F4
examples.append(make(
    "顧客：等一下可以借充電器嗎\n顧客：還有，我要一杯桂花輕烏龍純茶去冰無糖",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

# F5
examples.append(make(
    "顧客：座位區在二樓嗎\n顧客：嗯那給我一杯朱槿普洱紅鮮奶少糖去冰",
    {"orders": [order("朱槿普洱紅","fresh_milk_tea","M","去冰","少糖",[],1,60)], "total":60}))

# Write out
with open("/Users/xiechengru/ug-finetune/data/round7.jsonl", "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} Round 7 examples")
