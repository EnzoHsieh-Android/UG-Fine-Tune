#!/usr/bin/env python3
"""Round 8: 混合強化 — 閒聊→點餐 + modification 同時訓練
問題：Round 7 修好了閒聊→點餐，但 modification 退化。
策略：
  1. 保留閒聊→點餐範例
  2. 加入「閒聊 + modification」混合範例
  3. 重新加入純 modification 範例以鞏固
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
# A. 閒聊→點餐（保留 Round 7 核心範例，確保不退化）
# ============================================================

examples.append(make(
    "顧客：你們幾點關門？\n顧客：那來一杯桂花輕烏龍奶茶微糖去冰大杯",
    {"orders": [order("桂花輕烏龍","rich_milk_tea","L","去冰","微糖",[],1,75)], "total":75}))

examples.append(make(
    "顧客：廁所在哪裡？\n顧客：謝謝，我要一杯三窨十五茉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：可以刷卡嗎？\n顧客：好，一杯茶花紅烏龍純茶去冰無糖",
    {"orders": [order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

examples.append(make(
    "顧客：有Wi-Fi嗎\n顧客：給我一杯金杯蜜香紅鮮奶大杯無糖少冰",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","無糖",[],1,70)], "total":70}))

examples.append(make(
    "顧客：附近有停車場嗎\n顧客：先點一杯琥珀鐵觀音奶茶半糖少冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","M","少冰","半糖",[],1,65)], "total":65}))

examples.append(make(
    "顧客：你們有集點卡嗎\n顧客：那來杯朱槿普洱紅純茶無糖去冰",
    {"orders": [order("朱槿普洱紅","pure_tea",None,"去冰","無糖",[],1,40)], "total":40}))

examples.append(make(
    "顧客：還有位子嗎\n顧客：好，一杯米香玉露菁鮮奶半糖少冰",
    {"orders": [order("米香玉露菁","fresh_milk_tea","M","少冰","半糖",[],1,60)], "total":60}))

examples.append(make(
    "顧客：可以開發票嗎\n顧客：一杯蜜桃紅烏龍少冰半糖",
    {"orders": [order("蜜桃紅烏龍","fruit_tea",None,"少冰","半糖",[],1,75)], "total":75}))

# ============================================================
# B. 閒聊→點餐→modification（核心混合場景）
# ============================================================

# B1: 問時間 → 點兩杯 → 改第一杯甜度
examples.append(make(
    "顧客：你們幾點關門\n顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍純茶去冰無糖\n顧客：第一杯改微糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","微糖",[],1,65),
        order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":110}))

# B2: 問廁所 → 點兩杯 → 改第二杯冰量
examples.append(make(
    "顧客：廁所在哪\n顧客：一杯茶花紅烏龍純茶少冰無糖\n顧客：一杯金杯蜜香紅鮮奶半糖少冰\n顧客：第二杯改去冰",
    {"orders": [
        order("茶花紅烏龍","pure_tea",None,"少冰","無糖",[],1,45),
        order("金杯蜜香紅","fresh_milk_tea","M","去冰","半糖",[],1,60),
    ], "total":105}))

# B3: 問刷卡 → 點 → 改甜度和冰量
examples.append(make(
    "顧客：可以用LINE Pay嗎\n顧客：一杯琥珀鐵觀音奶茶半糖少冰\n顧客：改無糖去冰",
    {"orders": [order("琥珀鐵觀音","rich_milk_tea","M","去冰","無糖",[],1,65)], "total":65}))

# B4: 問集點 → 點兩杯 → 改第一杯尺寸
examples.append(make(
    "顧客：有集點活動嗎\n顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：再一杯茶花烏龍奶茶微糖去冰\n顧客：第一杯改大杯",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","L","少冰","半糖",[],1,75),
        order("茶花烏龍","rich_milk_tea","M","去冰","微糖",[],1,65),
    ], "total":140}))

# B5: 問外送 → 點 → 加料
examples.append(make(
    "顧客：你們有外送嗎\n顧客：那內用好了，一杯桂花輕烏龍鮮奶半糖少冰\n顧客：加茶凍",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",["紅烏龍茶凍"],1,80)], "total":80}))

# B6: 稱讚 → 點兩杯 → 茉莉那杯改無糖
examples.append(make(
    "顧客：你們店好漂亮\n顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯朱槿普洱紅純茶微糖去冰\n顧客：茉莉那杯改無糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","無糖",[],1,65),
        order("朱槿普洱紅","pure_tea",None,"去冰","微糖",[],1,40),
    ], "total":105}))

# B7: 問座位 → 點三杯 → 第二杯改半糖
examples.append(make(
    "顧客：還有位子嗎\n顧客：三窨十五茉鮮奶無糖去冰\n顧客：金杯蜜香紅奶茶微糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：第二杯改半糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","去冰","無糖",[],1,65),
        order("金杯蜜香紅","rich_milk_tea","M","少冰","半糖",[],1,60),
        order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":170}))

# ============================================================
# C. 純 modification 鞏固（重新強化，防退化）
# ============================================================

# C1: 改甜度
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：改微糖",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","微糖",[],1,65)], "total":65}))

# C2: 改冰量
examples.append(make(
    "顧客：一杯桂花輕烏龍純茶少冰無糖\n顧客：改去冰",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45)], "total":45}))

# C3: 第一杯改微糖（精確重現測試場景）
examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：再一杯桂花輕烏龍純茶去冰無糖\n顧客：第一杯改微糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","微糖",[],1,65),
        order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":110}))

# C4: 第二杯改去冰
examples.append(make(
    "顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：茶花紅烏龍純茶無糖少冰\n顧客：第二杯改去冰",
    {"orders": [
        order("金杯蜜香紅","fresh_milk_tea","M","少冰","半糖",[],1,60),
        order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[],1,45),
    ], "total":105}))

# C5: 兩杯都改大杯
examples.append(make(
    "顧客：兩杯琥珀鐵觀音鮮奶半糖少冰\n顧客：兩杯都改大杯",
    {"orders": [
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",[],1,75),
        order("琥珀鐵觀音","fresh_milk_tea","L","少冰","半糖",[],1,75),
    ], "total":150}))

# C6: 改多項（甜度+冰量）
examples.append(make(
    "顧客：一杯三窨十五茉奶茶半糖少冰\n顧客：改無糖去冰",
    {"orders": [order("三窨十五茉","rich_milk_tea","M","去冰","無糖",[],1,65)], "total":65}))

# C7: 茉莉那杯改微糖
examples.append(make(
    "顧客：三窨十五茉鮮奶半糖少冰\n顧客：桂花輕烏龍奶茶無糖去冰\n顧客：茉莉那杯改微糖",
    {"orders": [
        order("三窨十五茉","fresh_milk_tea","M","少冰","微糖",[],1,65),
        order("桂花輕烏龍","rich_milk_tea","M","去冰","無糖",[],1,65),
    ], "total":130}))

# C8: 改大杯加茶凍
examples.append(make(
    "顧客：一杯金杯蜜香紅鮮奶半糖少冰\n顧客：改大杯加茶凍",
    {"orders": [order("金杯蜜香紅","fresh_milk_tea","L","少冰","半糖",["紅烏龍茶凍"],1,85)], "total":85}))

# C9: 第一杯改熱飲
examples.append(make(
    "顧客：一杯米香玉露菁鮮奶半糖少冰\n顧客：一杯朱槿普洱紅純茶無糖去冰\n顧客：第一杯改熱飲",
    {"orders": [
        order("米香玉露菁","fresh_milk_tea","M","熱飲","半糖",[],1,60),
        order("朱槿普洱紅","pure_tea",None,"去冰","無糖",[],1,40),
    ], "total":100}))

# C10: 加燕麥粒
examples.append(make(
    "顧客：一杯茶花烏龍鮮奶半糖少冰\n顧客：加燕麥粒",
    {"orders": [order("茶花烏龍","fresh_milk_tea","M","少冰","半糖",["燕麥粒"],1,80)], "total":80}))

# Write out
with open("/Users/xiechengru/ug-finetune/data/round8.jsonl", "w") as f:
    for ex in examples:
        f.write(ex + "\n")

print(f"Generated {len(examples)} Round 8 examples")
