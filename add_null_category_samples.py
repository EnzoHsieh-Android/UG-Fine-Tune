#!/usr/bin/env python3
"""
Step 7e-2: 新增 category=null 的訓練樣本。
每個多分類品項均勻新增約 20 筆 null-category orders（train），~5 筆（valid）。
"""

import json, sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# 從現有資料讀取 system prompt
with open(DATA_DIR / "train.jsonl") as f:
    SYSTEM_PROMPT = json.loads(f.readline())["messages"][0]["content"]

MULTI_CAT_ITEMS = [
    "三窨十五茉", "桂花輕烏龍", "茶花紅烏龍",
    "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁",
]


def make_order(item, ice=None, sugar=None, size=None, addon=None, qty=1, note=""):
    return {
        "item": item, "category": None,
        "size": size, "ice": ice, "sugar": sugar,
        "addon": addon or [], "qty": qty, "note": note,
    }


def make_order_with_cat(item, category, ice=None, sugar=None, size=None, addon=None, qty=1, note=""):
    return {
        "item": item, "category": category,
        "size": size, "ice": ice, "sugar": sugar,
        "addon": addon or [], "qty": qty, "note": note,
    }


def sample(user_text, orders, intents=None, preferences=None, recommendations=None):
    segments = user_text.split(";")
    if intents is None:
        intents = ["order"] * len(segments)
    asst = {
        "intents": intents,
        "orders": orders,
        "preferences": preferences or {},
        "recommendations": recommendations or [],
    }
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(asst, ensure_ascii=False)},
        ]
    }


# ============================================================
# TRAIN SAMPLES (~70 samples, ~20 null per item)
# ============================================================

TRAIN = []

# --- Round 1: 單品項點餐 (7 samples, 7 null orders) ---
TRAIN.append(sample("一杯鐵觀音去冰半糖", [make_order("琥珀鐵觀音", ice="去冰", sugar="半糖")]))
TRAIN.append(sample("茉莉一杯微冰五分糖", [make_order("三窨十五茉", ice="微冰", sugar="五分糖")]))
TRAIN.append(sample("來杯桂花輕烏龍少冰三分糖", [make_order("桂花輕烏龍", ice="少冰", sugar="三分糖")]))
TRAIN.append(sample("茶花紅烏龍一杯去冰無糖", [make_order("茶花紅烏龍", ice="去冰", sugar="無糖")]))
TRAIN.append(sample("金杯蜜香紅正常冰全糖", [make_order("金杯蜜香紅", ice="正常冰", sugar="全糖")]))
TRAIN.append(sample("幫我點朱槿普洱紅微冰", [make_order("朱槿普洱紅", ice="微冰")]))
TRAIN.append(sample("玉露一杯半糖少冰", [make_order("米香玉露菁", ice="少冰", sugar="半糖")]))

# --- Round 2: 單品項，不同口語 (7 samples, 7 null orders) ---
TRAIN.append(sample("給我一杯十五茉去冰", [make_order("三窨十五茉", ice="去冰")]))
TRAIN.append(sample("我要輕烏龍微冰無糖", [make_order("桂花輕烏龍", ice="微冰", sugar="無糖")]))
TRAIN.append(sample("紅烏龍少冰五分糖一杯", [make_order("茶花紅烏龍", ice="少冰", sugar="五分糖")]))
TRAIN.append(sample("點一杯琥珀鐵觀音熱的三分糖", [make_order("琥珀鐵觀音", ice="熱飲", sugar="三分糖")]))
TRAIN.append(sample("蜜香紅去冰半糖", [make_order("金杯蜜香紅", ice="去冰", sugar="半糖")]))
TRAIN.append(sample("普洱一杯去冰無糖", [make_order("朱槿普洱紅", ice="去冰", sugar="無糖")]))
TRAIN.append(sample("米香玉露菁微冰三分糖", [make_order("米香玉露菁", ice="微冰", sugar="三分糖")]))

# --- Round 3: 單品項，簡稱/熱飲/大杯 (7 samples, 7 null orders) ---
TRAIN.append(sample("桂花一杯熱的半糖", [make_order("桂花輕烏龍", ice="熱飲", sugar="半糖")]))
TRAIN.append(sample("鐵觀音大杯去冰五分糖", [make_order("琥珀鐵觀音", ice="去冰", sugar="五分糖", size="L")]))
TRAIN.append(sample("三窨十五茉少冰", [make_order("三窨十五茉", ice="少冰")]))
TRAIN.append(sample("茶花烏龍中杯微冰半糖", [make_order("茶花紅烏龍", ice="微冰", sugar="半糖", size="M")]))
TRAIN.append(sample("金杯大杯去冰三分糖", [make_order("金杯蜜香紅", ice="去冰", sugar="三分糖", size="L")]))
TRAIN.append(sample("玉露菁熱的無糖", [make_order("米香玉露菁", ice="熱飲", sugar="無糖")]))
TRAIN.append(sample("朱槿普洱紅正常冰半糖", [make_order("朱槿普洱紅", ice="正常冰", sugar="半糖")]))

# --- Round 4: 雙品項（都是多分類，都 null）(7 samples, 14 null orders) ---
TRAIN.append(sample(
    "鐵觀音去冰半糖；茉莉微冰五分糖",
    [make_order("琥珀鐵觀音", ice="去冰", sugar="半糖"),
     make_order("三窨十五茉", ice="微冰", sugar="五分糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "桂花輕烏龍少冰三分糖；茶花紅烏龍去冰無糖",
    [make_order("桂花輕烏龍", ice="少冰", sugar="三分糖"),
     make_order("茶花紅烏龍", ice="去冰", sugar="無糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "金杯蜜香紅半糖少冰；朱槿微冰五分糖",
    [make_order("金杯蜜香紅", ice="少冰", sugar="半糖"),
     make_order("朱槿普洱紅", ice="微冰", sugar="五分糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "米香玉露菁去冰無糖；鐵觀音少冰半糖",
    [make_order("米香玉露菁", ice="去冰", sugar="無糖"),
     make_order("琥珀鐵觀音", ice="少冰", sugar="半糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "十五茉去冰；桂花少冰半糖",
    [make_order("三窨十五茉", ice="去冰"),
     make_order("桂花輕烏龍", ice="少冰", sugar="半糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "紅烏龍微冰三分糖；蜜香紅去冰無糖",
    [make_order("茶花紅烏龍", ice="微冰", sugar="三分糖"),
     make_order("金杯蜜香紅", ice="去冰", sugar="無糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "朱槿少冰半糖；玉露菁去冰三分糖",
    [make_order("朱槿普洱紅", ice="少冰", sugar="半糖"),
     make_order("米香玉露菁", ice="去冰", sugar="三分糖")],
    ["order", "order"],
))

# --- Round 5: 雙品項（換組合）(7 samples, 14 null orders) ---
TRAIN.append(sample(
    "桂花去冰半糖；鐵觀音微冰五分糖",
    [make_order("桂花輕烏龍", ice="去冰", sugar="半糖"),
     make_order("琥珀鐵觀音", ice="微冰", sugar="五分糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "茶花紅烏龍少冰半糖；三窨十五茉去冰無糖",
    [make_order("茶花紅烏龍", ice="少冰", sugar="半糖"),
     make_order("三窨十五茉", ice="去冰", sugar="無糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "普洱去冰三分糖；桂花輕烏龍微冰",
    [make_order("朱槿普洱紅", ice="去冰", sugar="三分糖"),
     make_order("桂花輕烏龍", ice="微冰")],
    ["order", "order"],
))
TRAIN.append(sample(
    "玉露微冰半糖；金杯去冰五分糖",
    [make_order("米香玉露菁", ice="微冰", sugar="半糖"),
     make_order("金杯蜜香紅", ice="去冰", sugar="五分糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "鐵觀音去冰；朱槿少冰三分糖",
    [make_order("琥珀鐵觀音", ice="去冰"),
     make_order("朱槿普洱紅", ice="少冰", sugar="三分糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "蜜香紅微冰半糖；茶花紅烏龍去冰",
    [make_order("金杯蜜香紅", ice="微冰", sugar="半糖"),
     make_order("茶花紅烏龍", ice="去冰")],
    ["order", "order"],
))
TRAIN.append(sample(
    "三窨十五茉少冰三分糖；玉露菁去冰無糖",
    [make_order("三窨十五茉", ice="少冰", sugar="三分糖"),
     make_order("米香玉露菁", ice="去冰", sugar="無糖")],
    ["order", "order"],
))

# --- Round 6: 多分類品項 + 果茶/奶蓋 (7 samples, 7 null orders) ---
TRAIN.append(sample(
    "鐵觀音去冰半糖；青檸桂蜜一杯",
    [make_order("琥珀鐵觀音", ice="去冰", sugar="半糖"),
     make_order_with_cat("青檸桂蜜", "fruit_tea", ice="正常冰", sugar=None)],
    ["order", "order"],
))
TRAIN.append(sample(
    "蜜桃紅烏龍一杯；再來一杯十五茉少冰",
    [make_order_with_cat("蜜桃紅烏龍", "fruit_tea", ice="正常冰"),
     make_order("三窨十五茉", ice="少冰")],
    ["order", "order"],
))
TRAIN.append(sample(
    "桂花輕烏龍微冰五分糖；葡柚十五茉一杯",
    [make_order("桂花輕烏龍", ice="微冰", sugar="五分糖"),
     make_order_with_cat("葡柚十五茉", "fruit_tea", ice="正常冰")],
    ["order", "order"],
))
TRAIN.append(sample(
    "茶花紅烏龍一杯去冰；蜜桃紅烏龍也來一杯",
    [make_order("茶花紅烏龍", ice="去冰"),
     make_order_with_cat("蜜桃紅烏龍", "fruit_tea", ice="正常冰")],
    ["order", "order"],
))
TRAIN.append(sample(
    "金杯蜜香紅微冰三分糖；青檸桂蜜",
    [make_order("金杯蜜香紅", ice="微冰", sugar="三分糖"),
     make_order_with_cat("青檸桂蜜", "fruit_tea", ice="正常冰")],
    ["order", "order"],
))
TRAIN.append(sample(
    "葡柚十五茉一杯；朱槿少冰無糖",
    [make_order_with_cat("葡柚十五茉", "fruit_tea", ice="正常冰"),
     make_order("朱槿普洱紅", ice="少冰", sugar="無糖")],
    ["order", "order"],
))
TRAIN.append(sample(
    "青檸桂蜜；玉露去冰半糖",
    [make_order_with_cat("青檸桂蜜", "fruit_tea", ice="正常冰"),
     make_order("米香玉露菁", ice="去冰", sugar="半糖")],
    ["order", "order"],
))

# --- Round 7: 含 modify intent (7 samples, 7 null orders) ---
TRAIN.append(sample(
    "鐵觀音一杯去冰半糖；改少冰",
    [make_order("琥珀鐵觀音", ice="少冰", sugar="半糖")],
    ["order", "modify"],
))
TRAIN.append(sample(
    "茉莉微冰五分糖；不要糖了",
    [make_order("三窨十五茉", ice="微冰", sugar="無糖")],
    ["order", "modify"],
))
TRAIN.append(sample(
    "桂花輕烏龍去冰半糖；加茶凍",
    [make_order("桂花輕烏龍", ice="去冰", sugar="半糖", addon=["紅烏龍茶凍"])],
    ["order", "modify"],
))
TRAIN.append(sample(
    "紅烏龍少冰三分糖；改去冰",
    [make_order("茶花紅烏龍", ice="去冰", sugar="三分糖")],
    ["order", "modify"],
))
TRAIN.append(sample(
    "金杯去冰半糖；改五分糖",
    [make_order("金杯蜜香紅", ice="去冰", sugar="五分糖")],
    ["order", "modify"],
))
TRAIN.append(sample(
    "朱槿正常冰全糖；改少冰三分糖",
    [make_order("朱槿普洱紅", ice="少冰", sugar="三分糖")],
    ["order", "modify"],
))
TRAIN.append(sample(
    "玉露菁去冰無糖；加燕麥粒",
    [make_order("米香玉露菁", ice="去冰", sugar="無糖", addon=["燕麥粒"])],
    ["order", "modify"],
))

# --- Round 8: 含 recommend intent (7 samples, 7 null orders) ---
TRAIN.append(sample(
    "鐵觀音去冰半糖；有推薦搭配的嗎",
    [make_order("琥珀鐵觀音", ice="去冰", sugar="半糖")],
    ["order", "recommend"],
    preferences={"口味": "搭配"},
    recommendations=[{"item": "紅烏龍茶凍", "category": "addon", "reason": "焙火茶凍搭配鐵觀音，口感層次更豐富"}],
))
TRAIN.append(sample(
    "三窨十五茉少冰；還有什麼推薦",
    [make_order("三窨十五茉", ice="少冰")],
    ["order", "recommend"],
    preferences={},
    recommendations=[{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "人氣招牌，焙火香濃郁"}],
))
TRAIN.append(sample(
    "桂花少冰半糖；朋友想喝什麼好喝的",
    [make_order("桂花輕烏龍", ice="少冰", sugar="半糖")],
    ["order", "recommend"],
    preferences={},
    recommendations=[{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "人氣招牌，焙火香濃郁"}],
))
TRAIN.append(sample(
    "茶花紅烏龍去冰無糖；有沒有清爽的推薦",
    [make_order("茶花紅烏龍", ice="去冰", sugar="無糖")],
    ["order", "recommend"],
    preferences={"口味": "清爽"},
    recommendations=[{"item": "青檸桂蜜", "category": "fruit_tea", "reason": "酸甜清爽，清涼消暑"}],
))
TRAIN.append(sample(
    "蜜香紅一杯去冰；有什麼甜的推薦嗎",
    [make_order("金杯蜜香紅", ice="去冰")],
    ["order", "recommend"],
    preferences={"口味": "甜"},
    recommendations=[{"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香，甜蜜芬芳"}],
))
TRAIN.append(sample(
    "朱槿去冰半糖；推薦一下",
    [make_order("朱槿普洱紅", ice="去冰", sugar="半糖")],
    ["order", "recommend"],
    preferences={},
    recommendations=[{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "人氣招牌，焙火香濃郁"}],
))
TRAIN.append(sample(
    "玉露微冰三分糖；有推薦的嗎",
    [make_order("米香玉露菁", ice="微冰", sugar="三分糖")],
    ["order", "recommend"],
    preferences={},
    recommendations=[{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "人氣招牌，焙火香濃郁"}],
))

# --- Round 9: 數量 > 1 (7 samples, 7 null orders) ---
TRAIN.append(sample("兩杯鐵觀音去冰半糖", [make_order("琥珀鐵觀音", ice="去冰", sugar="半糖", qty=2)]))
TRAIN.append(sample("茉莉兩杯微冰無糖", [make_order("三窨十五茉", ice="微冰", sugar="無糖", qty=2)]))
TRAIN.append(sample("桂花輕烏龍三杯少冰三分糖", [make_order("桂花輕烏龍", ice="少冰", sugar="三分糖", qty=3)]))
TRAIN.append(sample("茶花紅烏龍兩杯去冰", [make_order("茶花紅烏龍", ice="去冰", qty=2)]))
TRAIN.append(sample("兩杯金杯蜜香紅正常冰半糖", [make_order("金杯蜜香紅", ice="正常冰", sugar="半糖", qty=2)]))
TRAIN.append(sample("朱槿兩杯去冰五分糖", [make_order("朱槿普洱紅", ice="去冰", sugar="五分糖", qty=2)]))
TRAIN.append(sample("玉露菁兩杯少冰半糖", [make_order("米香玉露菁", ice="少冰", sugar="半糖", qty=2)]))

# --- Round 10: 加料 (7 samples, 7 null orders) ---
TRAIN.append(sample("鐵觀音加茶凍去冰半糖", [make_order("琥珀鐵觀音", ice="去冰", sugar="半糖", addon=["紅烏龍茶凍"])]))
TRAIN.append(sample("十五茉加燕麥粒微冰", [make_order("三窨十五茉", ice="微冰", addon=["燕麥粒"])]))
TRAIN.append(sample("桂花加茶凍少冰五分糖", [make_order("桂花輕烏龍", ice="少冰", sugar="五分糖", addon=["紅烏龍茶凍"])]))
TRAIN.append(sample("紅烏龍加茶凍去冰無糖", [make_order("茶花紅烏龍", ice="去冰", sugar="無糖", addon=["紅烏龍茶凍"])]))
TRAIN.append(sample("金杯加燕麥粒去冰三分糖", [make_order("金杯蜜香紅", ice="去冰", sugar="三分糖", addon=["燕麥粒"])]))
TRAIN.append(sample("朱槿加茶凍微冰半糖", [make_order("朱槿普洱紅", ice="微冰", sugar="半糖", addon=["紅烏龍茶凍"])]))
TRAIN.append(sample("玉露加燕麥粒去冰五分糖", [make_order("米香玉露菁", ice="去冰", sugar="五分糖", addon=["燕麥粒"])]))

# --- Round 11: 三品項組合 (5 samples, 15 null orders) ---
TRAIN.append(sample(
    "鐵觀音去冰半糖；桂花少冰三分糖；十五茉微冰無糖",
    [make_order("琥珀鐵觀音", ice="去冰", sugar="半糖"),
     make_order("桂花輕烏龍", ice="少冰", sugar="三分糖"),
     make_order("三窨十五茉", ice="微冰", sugar="無糖")],
    ["order", "order", "order"],
))
TRAIN.append(sample(
    "紅烏龍去冰；蜜香紅微冰五分糖；普洱少冰半糖",
    [make_order("茶花紅烏龍", ice="去冰"),
     make_order("金杯蜜香紅", ice="微冰", sugar="五分糖"),
     make_order("朱槿普洱紅", ice="少冰", sugar="半糖")],
    ["order", "order", "order"],
))
TRAIN.append(sample(
    "玉露去冰無糖；桂花輕烏龍半糖少冰；茶花紅烏龍微冰",
    [make_order("米香玉露菁", ice="去冰", sugar="無糖"),
     make_order("桂花輕烏龍", ice="少冰", sugar="半糖"),
     make_order("茶花紅烏龍", ice="微冰")],
    ["order", "order", "order"],
))
TRAIN.append(sample(
    "鐵觀音微冰半糖；金杯去冰五分糖；玉露菁少冰",
    [make_order("琥珀鐵觀音", ice="微冰", sugar="半糖"),
     make_order("金杯蜜香紅", ice="去冰", sugar="五分糖"),
     make_order("米香玉露菁", ice="少冰")],
    ["order", "order", "order"],
))
TRAIN.append(sample(
    "十五茉去冰；朱槿微冰半糖；桂花少冰三分糖",
    [make_order("三窨十五茉", ice="去冰"),
     make_order("朱槿普洱紅", ice="微冰", sugar="半糖"),
     make_order("桂花輕烏龍", ice="少冰", sugar="三分糖")],
    ["order", "order", "order"],
))

# --- Round 12: 更多口語變化 (7 samples, 7 null orders) ---
TRAIN.append(sample("就來杯鐵觀音去冰吧", [make_order("琥珀鐵觀音", ice="去冰")]))
TRAIN.append(sample("先來杯三窨十五茉半糖微冰", [make_order("三窨十五茉", ice="微冰", sugar="半糖")]))
TRAIN.append(sample("那就桂花輕烏龍好了去冰", [make_order("桂花輕烏龍", ice="去冰")]))
TRAIN.append(sample("茶花紅烏龍吧少冰三分糖", [make_order("茶花紅烏龍", ice="少冰", sugar="三分糖")]))
TRAIN.append(sample("好那來杯蜜香紅去冰無糖", [make_order("金杯蜜香紅", ice="去冰", sugar="無糖")]))
TRAIN.append(sample("就普洱吧去冰半糖", [make_order("朱槿普洱紅", ice="去冰", sugar="半糖")]))
TRAIN.append(sample("那就玉露菁微冰五分糖", [make_order("米香玉露菁", ice="微冰", sugar="五分糖")]))

# --- Round 13: 含 other intent (5 samples, 7 null orders) ---
TRAIN.append(sample(
    "你好；鐵觀音一杯去冰半糖",
    [make_order("琥珀鐵觀音", ice="去冰", sugar="半糖")],
    ["other", "order"],
))
TRAIN.append(sample(
    "嗨你好；桂花少冰三分糖；金杯微冰",
    [make_order("桂花輕烏龍", ice="少冰", sugar="三分糖"),
     make_order("金杯蜜香紅", ice="微冰")],
    ["other", "order", "order"],
))
TRAIN.append(sample(
    "請問一下；茶花紅烏龍去冰半糖",
    [make_order("茶花紅烏龍", ice="去冰", sugar="半糖")],
    ["other", "order"],
))
TRAIN.append(sample(
    "等一下；十五茉少冰無糖",
    [make_order("三窨十五茉", ice="少冰", sugar="無糖")],
    ["other", "order"],
))
TRAIN.append(sample(
    "你們今天有營業嗎；朱槿一杯去冰；玉露半糖微冰",
    [make_order("朱槿普洱紅", ice="去冰"),
     make_order("米香玉露菁", ice="微冰", sugar="半糖")],
    ["other", "order", "order"],
))

# --- Round 14: ASR 變體/口語化 (7 samples, 7 null orders) ---
TRAIN.append(sample("琥珀鐵觀音一杯微冰五分糖", [make_order("琥珀鐵觀音", ice="微冰", sugar="五分糖")]))
TRAIN.append(sample("三窨十五茉少冰正常糖", [make_order("三窨十五茉", ice="少冰", sugar="正常糖")]))
TRAIN.append(sample("桂花烏龍一杯去冰少糖", [make_order("桂花輕烏龍", ice="去冰", sugar="少糖")]))
TRAIN.append(sample("茶花烏龍去冰微糖", [make_order("茶花紅烏龍", ice="去冰", sugar="微糖")]))
TRAIN.append(sample("金杯蜜香紅少冰微糖", [make_order("金杯蜜香紅", ice="少冰", sugar="微糖")]))
TRAIN.append(sample("朱槿普洱紅去冰正常糖", [make_order("朱槿普洱紅", ice="去冰", sugar="正常糖")]))
TRAIN.append(sample("米香玉露菁一杯正常冰少糖", [make_order("米香玉露菁", ice="正常冰", sugar="少糖")]))


# ============================================================
# VALID SAMPLES (~15 samples, ~5 null per item)
# ============================================================

VALID = []

# --- V1: 單品項 (7 samples, 7 null orders) ---
VALID.append(sample("鐵觀音去冰三分糖", [make_order("琥珀鐵觀音", ice="去冰", sugar="三分糖")]))
VALID.append(sample("一杯茉莉少冰半糖", [make_order("三窨十五茉", ice="少冰", sugar="半糖")]))
VALID.append(sample("桂花輕烏龍微冰無糖", [make_order("桂花輕烏龍", ice="微冰", sugar="無糖")]))
VALID.append(sample("紅烏龍一杯去冰五分糖", [make_order("茶花紅烏龍", ice="去冰", sugar="五分糖")]))
VALID.append(sample("蜜香紅少冰三分糖", [make_order("金杯蜜香紅", ice="少冰", sugar="三分糖")]))
VALID.append(sample("朱槿一杯微冰半糖", [make_order("朱槿普洱紅", ice="微冰", sugar="半糖")]))
VALID.append(sample("玉露菁去冰五分糖", [make_order("米香玉露菁", ice="去冰", sugar="五分糖")]))

# --- V2: 雙品項 (7 samples, 14 null orders) ---
VALID.append(sample(
    "鐵觀音微冰半糖；桂花去冰三分糖",
    [make_order("琥珀鐵觀音", ice="微冰", sugar="半糖"),
     make_order("桂花輕烏龍", ice="去冰", sugar="三分糖")],
    ["order", "order"],
))
VALID.append(sample(
    "十五茉去冰；紅烏龍少冰五分糖",
    [make_order("三窨十五茉", ice="去冰"),
     make_order("茶花紅烏龍", ice="少冰", sugar="五分糖")],
    ["order", "order"],
))
VALID.append(sample(
    "金杯微冰半糖；普洱去冰無糖",
    [make_order("金杯蜜香紅", ice="微冰", sugar="半糖"),
     make_order("朱槿普洱紅", ice="去冰", sugar="無糖")],
    ["order", "order"],
))
VALID.append(sample(
    "玉露少冰三分糖；鐵觀音去冰",
    [make_order("米香玉露菁", ice="少冰", sugar="三分糖"),
     make_order("琥珀鐵觀音", ice="去冰")],
    ["order", "order"],
))
VALID.append(sample(
    "桂花輕烏龍少冰；三窨十五茉半糖微冰",
    [make_order("桂花輕烏龍", ice="少冰"),
     make_order("三窨十五茉", ice="微冰", sugar="半糖")],
    ["order", "order"],
))
VALID.append(sample(
    "茶花紅烏龍微冰三分糖；金杯去冰半糖",
    [make_order("茶花紅烏龍", ice="微冰", sugar="三分糖"),
     make_order("金杯蜜香紅", ice="去冰", sugar="半糖")],
    ["order", "order"],
))
VALID.append(sample(
    "朱槿少冰五分糖；玉露去冰三分糖",
    [make_order("朱槿普洱紅", ice="少冰", sugar="五分糖"),
     make_order("米香玉露菁", ice="去冰", sugar="三分糖")],
    ["order", "order"],
))


# ============================================================
# 寫入
# ============================================================

def count_items(samples):
    counts = {item: 0 for item in MULTI_CAT_ITEMS}
    for s in samples:
        asst = json.loads(s["messages"][2]["content"])
        for o in asst.get("orders", []):
            if isinstance(o, dict) and o["item"] in counts:
                counts[o["item"]] += 1
    return counts


def main():
    dry_run = "--dry-run" in sys.argv

    # 統計
    print(f"新增 train 樣本: {len(TRAIN)}")
    train_counts = count_items(TRAIN)
    for item, c in sorted(train_counts.items(), key=lambda x: -x[1]):
        print(f"  {item}: {c} null orders")

    print(f"\n新增 valid 樣本: {len(VALID)}")
    valid_counts = count_items(VALID)
    for item, c in sorted(valid_counts.items(), key=lambda x: -x[1]):
        print(f"  {item}: {c} null orders")

    if dry_run:
        print("\n[DRY RUN] 不寫入檔案")
        return

    # 追加到檔案
    for fname, new_samples in [("train.jsonl", TRAIN), ("valid.jsonl", VALID)]:
        filepath = DATA_DIR / fname
        with open(filepath, "a") as f:
            for s in new_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"\n已追加 {len(new_samples)} 筆到 {filepath}")

    # 寫入後統計
    print("\n=== 寫入後 null 比例 ===")
    for fname in ["train.jsonl", "valid.jsonl"]:
        filepath = DATA_DIR / fname
        with open(filepath) as f:
            all_samples = [json.loads(line) for line in f]
        print(f"\n{fname} ({len(all_samples)} samples):")
        for item in MULTI_CAT_ITEMS:
            total = 0
            null_count = 0
            for s in all_samples:
                asst = json.loads(s["messages"][2]["content"])
                for o in asst.get("orders", []):
                    if isinstance(o, dict) and o.get("item") == item:
                        total += 1
                        if o.get("category") is None:
                            null_count += 1
            pct = null_count * 100 // max(total, 1)
            mark = "✓" if pct >= 20 else "△" if pct >= 15 else "✗"
            print(f"  {item:<12} {null_count:>3}/{total:<3} ({pct:>2}%) {mark}")


if __name__ == "__main__":
    main()
