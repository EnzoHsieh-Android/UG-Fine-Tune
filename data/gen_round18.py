#!/usr/bin/env python3
"""
Round 18: 語音轉文字 (STT) 錯別字容錯（~50 筆）
教模型將常見的同音/近音誤字自動修正為正確品名、甜度、冰量。

Whisper 常見錯誤模式：
- 同音替換：三窨→三因/三蔭/三印、琥珀→湖泊/虎魄、朱槿→珠槿/朱瑾
- 近音替換：桂花→貴花、蜜桃→密桃、米香→迷香
- 聲母混淆：葡柚→葡油、青檸→清檸
- 甜度/冰量：半糖→伴糖、微糖→為糖/威糖、去冰→趣冰、微冰→為冰
- 加料：燕麥→燕賣、烏龍→烏隆
- 數量：兩杯→涼杯/良杯、三杯→散杯
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
    '輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}]}'
)

def make(user_text, assistant_json):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(assistant_json, ensure_ascii=False)},
        ]
    }

def order(item, cat, size, ice, sugar, qty=1, addon=None, note=""):
    return {"item": item, "category": cat, "size": size, "ice": ice, "sugar": sugar,
            "addon": addon or [], "qty": qty, "note": note}

examples = []

# ============================================================
# A. 品名錯字：三窨十五茉（高頻品項，多種錯法）
# ============================================================

# A1 三因
examples.append(make(
    "三因十五茉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖")]}
))
# A2 三蔭
examples.append(make(
    "三蔭十五茉奶茶微糖去冰",
    {"orders": [order("三窨十五茉", "rich_milk_tea", "M", "去冰", "微糖")]}
))
# A3 三印
examples.append(make(
    "大杯三印十五茉鮮奶無糖少冰",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "L", "少冰", "無糖")]}
))
# A4 三因 純茶
examples.append(make(
    "三因十五茉純茶去冰無糖",
    {"orders": [order("三窨十五茉", "pure_tea", None, "去冰", "無糖")]}
))

# ============================================================
# B. 品名錯字：琥珀鐵觀音
# ============================================================

# B1 湖泊
examples.append(make(
    "湖泊鐵觀音鮮奶半糖少冰",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖")]}
))
# B2 虎魄
examples.append(make(
    "虎魄鐵觀音奶茶微糖去冰",
    {"orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "去冰", "微糖")]}
))
# B3 湖泊 大杯
examples.append(make(
    "大杯湖泊鐵觀音鮮奶半糖少冰",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "L", "少冰", "半糖")]}
))
# B4 鐵觀因（音→因）
examples.append(make(
    "湖泊鐵觀因奶茶無糖去冰",
    {"orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "去冰", "無糖")]}
))

# ============================================================
# C. 品名錯字：朱槿普洱紅
# ============================================================

# C1 珠槿
examples.append(make(
    "珠槿普洱紅純茶去冰無糖",
    {"orders": [order("朱槿普洱紅", "pure_tea", None, "去冰", "無糖")]}
))
# C2 朱瑾
examples.append(make(
    "朱瑾普洱紅去冰無糖",
    {"orders": [order("朱槿普洱紅", "pure_tea", None, "去冰", "無糖")]}
))
# C3 朱謹
examples.append(make(
    "朱謹普洱紅少冰半糖",
    {"orders": [order("朱槿普洱紅", "pure_tea", None, "少冰", "半糖")]}
))

# ============================================================
# D. 品名錯字：桂花輕烏龍
# ============================================================

# D1 貴花
examples.append(make(
    "貴花輕烏龍鮮奶半糖少冰",
    {"orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖")]}
))
# D2 桂花輕烏隆（龍→隆）
examples.append(make(
    "桂花輕烏隆鮮奶微糖去冰",
    {"orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "微糖")]}
))
# D3 貴花輕烏隆（雙錯）
examples.append(make(
    "貴花輕烏隆奶茶半糖少冰",
    {"orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "少冰", "半糖")]}
))

# ============================================================
# E. 品名錯字：米香玉露菁
# ============================================================

# E1 迷香
examples.append(make(
    "迷香玉露菁鮮奶半糖少冰",
    {"orders": [order("米香玉露菁", "fresh_milk_tea", "M", "少冰", "半糖")]}
))
# E2 玉露青
examples.append(make(
    "米香玉露青鮮奶無糖去冰",
    {"orders": [order("米香玉露菁", "fresh_milk_tea", "M", "去冰", "無糖")]}
))
# E3 迷香玉露青（雙錯）
examples.append(make(
    "迷香玉露青鮮奶微糖少冰",
    {"orders": [order("米香玉露菁", "fresh_milk_tea", "M", "少冰", "微糖")]}
))

# ============================================================
# F. 品名錯字：蜜桃紅烏龍
# ============================================================

# F1 密桃
examples.append(make(
    "密桃紅烏龍半糖少冰",
    {"orders": [order("蜜桃紅烏龍", "fruit_tea", None, "少冰", "半糖")]}
))
# F2 蜜桃紅烏隆
examples.append(make(
    "蜜桃紅烏隆微糖去冰",
    {"orders": [order("蜜桃紅烏龍", "fruit_tea", None, "去冰", "微糖")]}
))
# F3 密桃紅烏隆（雙錯）
examples.append(make(
    "密桃紅烏隆半糖少冰",
    {"orders": [order("蜜桃紅烏龍", "fruit_tea", None, "少冰", "半糖")]}
))

# ============================================================
# G. 品名錯字：葡柚十五茉
# ============================================================

# G1 葡油
examples.append(make(
    "葡油十五茉少冰半糖",
    {"orders": [order("葡柚十五茉", "fruit_tea", None, "少冰", "半糖")]}
))
# G2 葡又
examples.append(make(
    "葡又十五茉微糖去冰",
    {"orders": [order("葡柚十五茉", "fruit_tea", None, "去冰", "微糖")]}
))

# ============================================================
# H. 品名錯字：青檸桂蜜
# ============================================================

# H1 清檸
examples.append(make(
    "清檸桂蜜少冰半糖",
    {"orders": [order("青檸桂蜜", "fruit_tea", None, "少冰", "半糖")]}
))
# H2 青寧
examples.append(make(
    "青寧桂蜜微糖少冰",
    {"orders": [order("青檸桂蜜", "fruit_tea", None, "少冰", "微糖")]}
))

# ============================================================
# I. 品名錯字：金杯蜜香紅
# ============================================================

# I1 金杯密香紅
examples.append(make(
    "金杯密香紅鮮奶半糖少冰",
    {"orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "少冰", "半糖")]}
))

# ============================================================
# J. 品名錯字：茶花烏龍 / 茶花紅烏龍
# ============================================================

# J1 插花烏龍
examples.append(make(
    "插花烏龍鮮奶半糖少冰",
    {"orders": [order("茶花烏龍", "fresh_milk_tea", "M", "少冰", "半糖")]}
))
# J2 插花紅烏龍
examples.append(make(
    "插花紅烏龍奶蓋去冰半糖",
    {"orders": [order("茶花紅烏龍", "cloud_velvet", None, "去冰", "半糖")]}
))
# J3 茶花紅烏隆
examples.append(make(
    "茶花紅烏隆純茶去冰無糖",
    {"orders": [order("茶花紅烏龍", "pure_tea", None, "去冰", "無糖")]}
))

# ============================================================
# K. 品名錯字：紅玉紅茶
# ============================================================

# K1 紅玉紅查
examples.append(make(
    "紅玉紅查鮮奶半糖少冰",
    {"orders": [order("紅玉紅茶", "fresh_milk_tea", "M", "少冰", "半糖")]}
))

# ============================================================
# L. 甜度錯字
# ============================================================

# L1 伴糖→半糖
examples.append(make(
    "三窨十五茉鮮奶伴糖少冰",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖")]}
))
# L2 為糖→微糖
examples.append(make(
    "琥珀鐵觀音鮮奶為糖少冰",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "微糖")]}
))
# L3 威糖→微糖
examples.append(make(
    "桂花輕烏龍奶茶威糖去冰",
    {"orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "去冰", "微糖")]}
))
# L4 班糖→半糖
examples.append(make(
    "金杯蜜香紅鮮奶班糖少冰",
    {"orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "少冰", "半糖")]}
))

# ============================================================
# M. 冰量錯字
# ============================================================

# M1 趣冰→去冰
examples.append(make(
    "三窨十五茉鮮奶半糖趣冰",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "去冰", "半糖")]}
))
# M2 為冰→微冰
examples.append(make(
    "琥珀鐵觀音奶茶半糖為冰",
    {"orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "微冰", "半糖")]}
))
# M3 威冰→微冰
examples.append(make(
    "桂花輕烏龍鮮奶微糖威冰",
    {"orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "微冰", "微糖")]}
))
# M4 熱引→熱飲
examples.append(make(
    "朱槿普洱紅純茶無糖熱引",
    {"orders": [order("朱槿普洱紅", "pure_tea", None, "熱飲", "無糖")]}
))

# ============================================================
# N. 加料錯字
# ============================================================

# N1 燕賣→燕麥粒
examples.append(make(
    "三窨十五茉鮮奶半糖少冰加燕賣",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", addon=["燕麥粒"])]}
))
# N2 紅烏隆茶凍
examples.append(make(
    "琥珀鐵觀音鮮奶半糖少冰加紅烏隆茶凍",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖", addon=["紅烏龍茶凍"])]}
))
# N3 燕賣粒
examples.append(make(
    "桂花輕烏龍鮮奶微糖少冰加燕賣粒",
    {"orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "微糖", addon=["燕麥粒"])]}
))

# ============================================================
# O. 數量錯字
# ============================================================

# O1 涼杯→兩杯
examples.append(make(
    "涼杯三窨十五茉鮮奶半糖少冰",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", qty=2)]}
))
# O2 良杯→兩杯
examples.append(make(
    "良杯琥珀鐵觀音鮮奶微糖去冰",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "微糖", qty=2)]}
))
# O3 散杯→三杯
examples.append(make(
    "散杯桂花輕烏龍奶茶半糖少冰",
    {"orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "少冰", "半糖", qty=3)]}
))

# ============================================================
# P. 多錯混合（品名+甜度+加料）
# ============================================================

# P1 三因+伴糖+燕賣
examples.append(make(
    "三因十五茉鮮奶伴糖少冰加燕賣",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", addon=["燕麥粒"])]}
))
# P2 湖泊+為糖+烏隆
examples.append(make(
    "湖泊鐵觀音鮮奶為糖少冰加紅烏隆茶凍",
    {"orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "微糖", addon=["紅烏龍茶凍"])]}
))
# P3 貴花+趣冰
examples.append(make(
    "貴花輕烏龍鮮奶半糖趣冰",
    {"orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "半糖")]}
))
# P4 密桃+為冰
examples.append(make(
    "密桃紅烏龍伴糖為冰",
    {"orders": [order("蜜桃紅烏龍", "fruit_tea", None, "微冰", "半糖")]}
))
# P5 涼杯+三因+伴糖
examples.append(make(
    "涼杯三因十五茉鮮奶伴糖少冰",
    {"orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", qty=2)]}
))
# P6 多杯多錯
examples.append(make(
    "一杯湖泊鐵觀音鮮奶伴糖趣冰，一杯貴花輕烏隆奶茶為糖少冰",
    {"orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "半糖"),
        order("桂花輕烏龍", "rich_milk_tea", "M", "少冰", "微糖"),
    ]}
))

# ============================================================
# Write output
# ============================================================
output_path = "data/round18.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Generated {len(examples)} examples")
