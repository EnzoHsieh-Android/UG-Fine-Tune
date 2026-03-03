#!/usr/bin/env python3
"""Round 34 訓練資料生成 — 針對 6 個 generalization 失敗 pattern

失敗分析：
#33: 非菜單問句→推薦 — 只有 2 筆（嚴重不足）
#46: 鮮奶茶+addon → fresh_milk_tea — 模型在有 addon 時 category 輸出錯誤
#48: 雙份+單份混合 addon — 模型把雙份茶凍+燕麥變成只有單份
#49: 多輪 category leak（1st 鮮奶→2nd 漏）
#52: 多輪 category leak（1st 純茶→2nd 漏）
#53: 數量拆分 — 三杯X兩杯奶茶一杯純茶 → category 分錯
"""

import json
import os

# 讀取 system prompt（從現有訓練資料）
DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + "/data"
with open(f"{DATA_DIR}/train.jsonl", "r") as f:
    first_line = json.loads(f.readline())
    SYSTEM_PROMPT = first_line["messages"][0]["content"]


def make_sample(user_text, assistant_json):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(assistant_json, ensure_ascii=False)},
        ]
    }


def order_entry(item, category=None, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
    return {
        "item": item,
        "category": category,
        "size": size,
        "ice": ice,
        "sugar": sugar,
        "addon": addon or [],
        "qty": qty,
        "note": note,
    }


def order_response(intents, orders, preferences=None, recommendations=None):
    return {
        "intents": intents,
        "orders": orders,
        "preferences": preferences or {},
        "recommendations": recommendations or [],
    }


def rec_entry(item, category, reason):
    return {"item": item, "category": category, "reason": reason}


# ==========================================
# P4: 非菜單品項 + "有...嗎" → recommend
# 覆蓋：只有 2 筆，嚴重不足
# ==========================================
NON_MENU_RECOMMEND_TRAIN = [
    # 拿鐵類
    make_sample("有拿鐵嗎", order_response(
        ["recommend"], [],
        {"口味": "咖啡調飲"},
        [rec_entry("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音鮮奶，焙火香濃郁，口感接近拿鐵的厚實感")]
    )),
    make_sample("你們有沒有抹茶拿鐵", order_response(
        ["recommend"], [],
        {"口味": "抹茶"},
        [rec_entry("米香玉露菁", "fresh_milk_tea", "日式玉露菁鮮奶，帶抹茶般的鮮爽與穀物香")]
    )),
    make_sample("有賣焦糖瑪奇朵嗎", order_response(
        ["recommend"], [],
        {"口味": "焦糖甜香"},
        [rec_entry("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜帶焦糖般甘韻")]
    )),
    # 非茶類飲品詢問
    make_sample("有果汁嗎", order_response(
        ["recommend"], [],
        {"口味": "水果"},
        [rec_entry("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽如果汁般消暑")]
    )),
    make_sample("你們有賣可可嗎", order_response(
        ["recommend"], [],
        {"口味": "可可"},
        [rec_entry("茶花紅烏龍", "rich_milk_tea", "重焙火紅烏龍奶茶，熟果甜韻帶巧克力般的深度")]
    )),
    make_sample("有沒有薄荷飲料", order_response(
        ["recommend"], [],
        {"口味": "清涼"},
        [rec_entry("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑，清涼感十足")]
    )),
    make_sample("請問有賣豆漿嗎", order_response(
        ["recommend"], [],
        {"口味": "穀物"},
        [rec_entry("米香玉露菁", "fresh_milk_tea", "玉露菁鮮奶帶米穀香，穀物奶香療癒")]
    )),
    make_sample("有黑糖珍珠嗎", order_response(
        ["recommend"], [],
        {"口味": "黑糖"},
        [rec_entry("琥珀鐵觀音", "rich_milk_tea", "重焙鐵觀音奶茶，焙火香濃郁有黑糖般深沉甘韻")]
    )),
    # 帶否定/確認語氣
    make_sample("沒有波霸奶茶嗎", order_response(
        ["recommend"], [],
        {"口味": "奶茶"},
        [rec_entry("茶花紅烏龍", "rich_milk_tea", "紅烏龍奶茶，茶奶平衡圓潤，可加紅烏龍茶凍增添口感")]
    )),
    make_sample("有沒有檸檬紅茶", order_response(
        ["recommend"], [],
        {"口味": "檸檬酸甜"},
        [rec_entry("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽，有檸檬般的清新風味")]
    )),
]

NON_MENU_RECOMMEND_VALID = [
    make_sample("有賣奶昔嗎", order_response(
        ["recommend"], [],
        {"口味": "濃郁奶香"},
        [rec_entry("桂花輕烏龍", "cloud_velvet", "桂花烏龍覆綿密奶蓋，鹹甜交融如奶昔般滑順")]
    )),
    make_sample("你們有冬瓜茶嗎", order_response(
        ["recommend"], [],
        {"口味": "甘甜"},
        [rec_entry("金杯蜜香紅", "rich_milk_tea", "蜜香紅茶奶茶，天然蜜甜，甘韻類似冬瓜茶")]
    )),
]


# ==========================================
# P1+P3: 鮮奶茶+addon → fresh_milk_tea
# 覆蓋：單獨「鮮奶茶」夠多，但鮮奶茶+addon 組合可能不足
# ==========================================
FRESH_MILK_ADDON_TRAIN = [
    make_sample("琥珀鐵觀音鮮奶茶加茶凍", order_response(
        ["order"],
        [order_entry("琥珀鐵觀音", "fresh_milk_tea", addon=["紅烏龍茶凍"])]
    )),
    make_sample("金杯蜜香紅鮮奶茶大杯無糖加燕麥粒", order_response(
        ["order"],
        [order_entry("金杯蜜香紅", "fresh_milk_tea", size="L", sugar="無糖", addon=["燕麥粒"])]
    )),
    make_sample("三窨十五茉鮮奶茶半糖少冰加茶凍跟燕麥", order_response(
        ["order"],
        [order_entry("三窨十五茉", "fresh_milk_tea", sugar="半糖", ice="少冰", addon=["紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("朱槿普洱紅鮮奶茶微冰加茶凍", order_response(
        ["order"],
        [order_entry("朱槿普洱紅", "fresh_milk_tea", ice="微冰", addon=["紅烏龍茶凍"])]
    )),
    make_sample("茶花紅烏龍鮮奶茶中杯三分糖去冰加燕麥粒", order_response(
        ["order"],
        [order_entry("茶花紅烏龍", "fresh_milk_tea", size="M", sugar="三分糖", ice="去冰", addon=["燕麥粒"])]
    )),
    make_sample("米香玉露菁鮮奶茶加燕麥", order_response(
        ["order"],
        [order_entry("米香玉露菁", "fresh_milk_tea", addon=["燕麥粒"])]
    )),
]

FRESH_MILK_ADDON_VALID = [
    make_sample("桂花輕烏龍鮮奶茶大杯半糖加茶凍", order_response(
        ["order"],
        [order_entry("桂花輕烏龍", "fresh_milk_tea", size="L", sugar="半糖", addon=["紅烏龍茶凍"])]
    )),
]


# ==========================================
# P3: 雙份+單份混合 addon（不對稱）
# 覆蓋：9 筆 [A,A,B] pattern，需更多變體
# ==========================================
DOUBLE_ADDON_MIX_TRAIN = [
    # 雙份茶凍 + 燕麥 → [茶凍, 茶凍, 燕麥粒]
    make_sample("茶花紅烏龍奶茶大杯半糖少冰加雙份茶凍和燕麥", order_response(
        ["order"],
        [order_entry("茶花紅烏龍", "rich_milk_tea", size="L", sugar="半糖", ice="少冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("琥珀鐵觀音鮮奶茶無糖去冰加兩份茶凍還有燕麥", order_response(
        ["order"],
        [order_entry("琥珀鐵觀音", "fresh_milk_tea", sugar="無糖", ice="去冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("朱槿普洱紅鮮奶茶加雙份茶凍加燕麥粒", order_response(
        ["order"],
        [order_entry("朱槿普洱紅", "fresh_milk_tea",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    # 雙份燕麥 + 茶凍 → [燕麥, 燕麥, 茶凍]
    make_sample("三窨十五茉鮮奶茶半糖加雙份燕麥和茶凍", order_response(
        ["order"],
        [order_entry("三窨十五茉", "fresh_milk_tea", sugar="半糖",
                     addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])]
    )),
    make_sample("金杯蜜香紅奶茶大杯加兩份燕麥還有一份茶凍", order_response(
        ["order"],
        [order_entry("金杯蜜香紅", "rich_milk_tea", size="L",
                     addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])]
    )),
    # 不同措辭
    make_sample("桂花輕烏龍鮮奶茶少冰加兩份紅烏龍茶凍一份燕麥粒", order_response(
        ["order"],
        [order_entry("桂花輕烏龍", "fresh_milk_tea", ice="少冰",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
    make_sample("米香玉露菁奶茶三分糖加雙份茶凍跟一份燕麥", order_response(
        ["order"],
        [order_entry("米香玉露菁", "rich_milk_tea", sugar="三分糖",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
]

DOUBLE_ADDON_MIX_VALID = [
    make_sample("茶花紅烏龍鮮奶茶中杯加兩份茶凍和燕麥粒", order_response(
        ["order"],
        [order_entry("茶花紅烏龍", "fresh_milk_tea", size="M",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])]
    )),
]


# ==========================================
# P2: 多輪 category 不沿用（針對失敗案例的精確模式）
# #49: 1st 鮮奶 → 2nd null（不該變 fresh_milk_tea）
# #52: 1st 純茶 → 2nd null（不該變 fresh_milk_tea）
# ==========================================
MULTI_TURN_CATEGORY_NULL_TRAIN = [
    # Pattern: seg1 鮮奶 → seg2 不同品項 → null
    make_sample("金杯蜜香紅鮮奶茶半糖;再一杯琥珀鐵觀音無糖去冰", order_response(
        ["order", "order"],
        [order_entry("金杯蜜香紅", "fresh_milk_tea", sugar="半糖"),
         order_entry("琥珀鐵觀音", category=None, sugar="無糖", ice="去冰")]
    )),
    make_sample("三窨十五茉鮮奶茶少冰;再來一杯桂花輕烏龍半糖", order_response(
        ["order", "order"],
        [order_entry("三窨十五茉", "fresh_milk_tea", ice="少冰"),
         order_entry("桂花輕烏龍", category=None, sugar="半糖")]
    )),
    make_sample("朱槿普洱紅鮮奶茶大杯;再加一杯米香玉露菁三分糖", order_response(
        ["order", "order"],
        [order_entry("朱槿普洱紅", "fresh_milk_tea", size="L"),
         order_entry("米香玉露菁", category=None, sugar="三分糖")]
    )),
    make_sample("茶花紅烏龍鮮奶茶中杯無糖;再一杯金杯蜜香紅去冰", order_response(
        ["order", "order"],
        [order_entry("茶花紅烏龍", "fresh_milk_tea", size="M", sugar="無糖"),
         order_entry("金杯蜜香紅", category=None, ice="去冰")]
    )),
    make_sample("桂花輕烏龍鮮奶茶半糖去冰;再一杯朱槿普洱紅少冰", order_response(
        ["order", "order"],
        [order_entry("桂花輕烏龍", "fresh_milk_tea", sugar="半糖", ice="去冰"),
         order_entry("朱槿普洱紅", category=None, ice="少冰")]
    )),
    # Pattern: seg1 純茶 → seg2 不同品項 → null
    make_sample("桂花輕烏龍純茶無糖;再一杯金杯蜜香紅半糖少冰", order_response(
        ["order", "order"],
        [order_entry("桂花輕烏龍", "pure_tea", sugar="無糖"),
         order_entry("金杯蜜香紅", category=None, sugar="半糖", ice="少冰")]
    )),
    make_sample("朱槿普洱紅純茶去冰;再來一杯琥珀鐵觀音三分糖", order_response(
        ["order", "order"],
        [order_entry("朱槿普洱紅", "pure_tea", ice="去冰"),
         order_entry("琥珀鐵觀音", category=None, sugar="三分糖")]
    )),
    make_sample("茶花紅烏龍純茶無糖去冰;再一杯三窨十五茉半糖少冰", order_response(
        ["order", "order"],
        [order_entry("茶花紅烏龍", "pure_tea", sugar="無糖", ice="去冰"),
         order_entry("三窨十五茉", category=None, sugar="半糖", ice="少冰")]
    )),
    make_sample("米香玉露菁純茶;再加一杯朱槿普洱紅無糖微冰", order_response(
        ["order", "order"],
        [order_entry("米香玉露菁", "pure_tea"),
         order_entry("朱槿普洱紅", category=None, sugar="無糖", ice="微冰")]
    )),
    # Pattern: seg1 奶蓋 → seg2 不同品項 → null
    make_sample("桂花輕烏龍奶蓋無糖;再一杯琥珀鐵觀音半糖去冰", order_response(
        ["order", "order"],
        [order_entry("桂花輕烏龍", "cloud_velvet", sugar="無糖"),
         order_entry("琥珀鐵觀音", category=None, sugar="半糖", ice="去冰")]
    )),
    make_sample("茶花紅烏龍奶蓋;再一杯三窨十五茉無糖少冰", order_response(
        ["order", "order"],
        [order_entry("茶花紅烏龍", "cloud_velvet"),
         order_entry("三窨十五茉", category=None, sugar="無糖", ice="少冰")]
    )),
    # Pattern: seg1 奶茶 → seg2 不同品項 → null
    make_sample("琥珀鐵觀音奶茶大杯半糖;再一杯朱槿普洱紅無糖去冰", order_response(
        ["order", "order"],
        [order_entry("琥珀鐵觀音", "rich_milk_tea", size="L", sugar="半糖"),
         order_entry("朱槿普洱紅", category=None, sugar="無糖", ice="去冰")]
    )),
]

MULTI_TURN_CATEGORY_NULL_VALID = [
    make_sample("米香玉露菁鮮奶茶半糖少冰;再一杯三窨十五茉無糖", order_response(
        ["order", "order"],
        [order_entry("米香玉露菁", "fresh_milk_tea", sugar="半糖", ice="少冰"),
         order_entry("三窨十五茉", category=None, sugar="無糖")]
    )),
    make_sample("三窨十五茉純茶;再一杯桂花輕烏龍半糖去冰", order_response(
        ["order", "order"],
        [order_entry("三窨十五茉", "pure_tea"),
         order_entry("桂花輕烏龍", category=None, sugar="半糖", ice="去冰")]
    )),
    make_sample("茶花紅烏龍奶蓋微糖;再一杯金杯蜜香紅無糖少冰", order_response(
        ["order", "order"],
        [order_entry("茶花紅烏龍", "cloud_velvet", sugar="微糖"),
         order_entry("金杯蜜香紅", category=None, sugar="無糖", ice="少冰")]
    )),
]


# ==========================================
# P5: 數量拆分 — 同品項不同分類+數量
# ==========================================
QUANTITY_SPLIT_TRAIN = [
    # 三杯X，兩杯奶茶一杯純茶
    make_sample("三杯琥珀鐵觀音，兩杯奶茶半糖少冰，一杯純茶無糖去冰", order_response(
        ["order"],
        [order_entry("琥珀鐵觀音", "rich_milk_tea", sugar="半糖", ice="少冰", qty=2),
         order_entry("琥珀鐵觀音", "pure_tea", sugar="無糖", ice="去冰", qty=1)]
    )),
    make_sample("三杯三窨十五茉，兩杯奶茶無糖，一杯純茶去冰", order_response(
        ["order"],
        [order_entry("三窨十五茉", "rich_milk_tea", sugar="無糖", qty=2),
         order_entry("三窨十五茉", "pure_tea", ice="去冰", qty=1)]
    )),
    make_sample("三杯朱槿普洱紅，兩杯鮮奶茶半糖，一杯純茶無糖", order_response(
        ["order"],
        [order_entry("朱槿普洱紅", "fresh_milk_tea", sugar="半糖", qty=2),
         order_entry("朱槿普洱紅", "pure_tea", sugar="無糖", qty=1)]
    )),
    make_sample("三杯金杯蜜香紅，一杯鮮奶茶大杯，兩杯奶茶半糖", order_response(
        ["order"],
        [order_entry("金杯蜜香紅", "fresh_milk_tea", size="L", qty=1),
         order_entry("金杯蜜香紅", "rich_milk_tea", sugar="半糖", qty=2)]
    )),
    make_sample("四杯茶花紅烏龍，一杯純茶無糖、一杯鮮奶半糖、兩杯奶茶去冰", order_response(
        ["order"],
        [order_entry("茶花紅烏龍", "pure_tea", sugar="無糖", qty=1),
         order_entry("茶花紅烏龍", "fresh_milk_tea", sugar="半糖", qty=1),
         order_entry("茶花紅烏龍", "rich_milk_tea", ice="去冰", qty=2)]
    )),
    # 更自然的表述
    make_sample("米香玉露菁三杯，奶茶兩杯半糖少冰，純茶一杯無糖", order_response(
        ["order"],
        [order_entry("米香玉露菁", "rich_milk_tea", sugar="半糖", ice="少冰", qty=2),
         order_entry("米香玉露菁", "pure_tea", sugar="無糖", qty=1)]
    )),
    make_sample("桂花輕烏龍要三杯，兩杯奶茶三分糖，一杯純茶無糖去冰", order_response(
        ["order"],
        [order_entry("桂花輕烏龍", "rich_milk_tea", sugar="三分糖", qty=2),
         order_entry("桂花輕烏龍", "pure_tea", sugar="無糖", ice="去冰", qty=1)]
    )),
]

QUANTITY_SPLIT_VALID = [
    make_sample("三杯茶花紅烏龍，兩杯鮮奶茶少冰，一杯純茶無糖去冰", order_response(
        ["order"],
        [order_entry("茶花紅烏龍", "fresh_milk_tea", ice="少冰", qty=2),
         order_entry("茶花紅烏龍", "pure_tea", sugar="無糖", ice="去冰", qty=1)]
    )),
    make_sample("三杯桂花輕烏龍，一杯鮮奶茶半糖，兩杯奶茶無糖少冰", order_response(
        ["order"],
        [order_entry("桂花輕烏龍", "fresh_milk_tea", sugar="半糖", qty=1),
         order_entry("桂花輕烏龍", "rich_milk_tea", sugar="無糖", ice="少冰", qty=2)]
    )),
]


# ==========================================
# Anchor 樣本（防止回歸）
# ==========================================
ANCHOR_TRAIN = [
    # 基本單品
    make_sample("三窨十五茉無糖去冰", order_response(
        ["order"],
        [order_entry("三窨十五茉", category=None, sugar="無糖", ice="去冰")]
    )),
    make_sample("桂花輕烏龍奶茶大杯", order_response(
        ["order"],
        [order_entry("桂花輕烏龍", "rich_milk_tea", size="L")]
    )),
    # 多品項
    make_sample("青檸桂蜜和蜜桃紅烏龍各一杯", order_response(
        ["order"],
        [order_entry("青檸桂蜜", "fruit_tea"),
         order_entry("蜜桃紅烏龍", "fruit_tea")]
    )),
    # 推薦
    make_sample("有什麼好喝的推薦嗎", order_response(
        ["recommend"], [],
        {},
        [rec_entry("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜順口")]
    )),
    # 閒聊
    make_sample("你好", order_response(
        ["other"], [], {}, []
    )),
    # 修改
    make_sample("琥珀鐵觀音半糖少冰，不對改無糖", order_response(
        ["order"],
        [order_entry("琥珀鐵觀音", category=None, sugar="無糖", ice="少冰")]
    )),
    # 正常 addon（不是雙份）
    make_sample("金杯蜜香紅鮮奶茶加茶凍半糖", order_response(
        ["order"],
        [order_entry("金杯蜜香紅", "fresh_milk_tea", sugar="半糖", addon=["紅烏龍茶凍"])]
    )),
    # 正常多輪（seg2 有明確分類 → 保留）
    make_sample("三窨十五茉純茶;再一杯桂花輕烏龍鮮奶茶半糖", order_response(
        ["order", "order"],
        [order_entry("三窨十五茉", "pure_tea"),
         order_entry("桂花輕烏龍", "fresh_milk_tea", sugar="半糖")]
    )),
]

ANCHOR_VALID = [
    make_sample("茶花紅烏龍奶蓋", order_response(
        ["order"],
        [order_entry("茶花紅烏龍", "cloud_velvet")]
    )),
    make_sample("蜜桃紅烏龍加燕麥粒", order_response(
        ["order"],
        [order_entry("蜜桃紅烏龍", "fruit_tea", addon=["燕麥粒"])]
    )),
]


def main():
    train_samples = (
        NON_MENU_RECOMMEND_TRAIN
        + FRESH_MILK_ADDON_TRAIN
        + DOUBLE_ADDON_MIX_TRAIN
        + MULTI_TURN_CATEGORY_NULL_TRAIN
        + QUANTITY_SPLIT_TRAIN
        + ANCHOR_TRAIN
    )

    valid_samples = (
        NON_MENU_RECOMMEND_VALID
        + FRESH_MILK_ADDON_VALID
        + DOUBLE_ADDON_MIX_VALID
        + MULTI_TURN_CATEGORY_NULL_VALID
        + QUANTITY_SPLIT_VALID
        + ANCHOR_VALID
    )

    # Append to train.jsonl
    train_file = f"{DATA_DIR}/train.jsonl"
    with open(train_file, "a") as f:
        for s in train_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Append to valid.jsonl
    valid_file = f"{DATA_DIR}/valid.jsonl"
    with open(valid_file, "a") as f:
        for s in valid_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # 統計
    print(f"Round 34 資料生成完成")
    print(f"  Train: +{len(train_samples)} 筆")
    print(f"    P4 非菜單推薦: {len(NON_MENU_RECOMMEND_TRAIN)}")
    print(f"    P1 鮮奶茶+addon: {len(FRESH_MILK_ADDON_TRAIN)}")
    print(f"    P3 雙份混合addon: {len(DOUBLE_ADDON_MIX_TRAIN)}")
    print(f"    P2 多輪category null: {len(MULTI_TURN_CATEGORY_NULL_TRAIN)}")
    print(f"    P5 數量拆分: {len(QUANTITY_SPLIT_TRAIN)}")
    print(f"    Anchor: {len(ANCHOR_TRAIN)}")
    print(f"  Valid: +{len(valid_samples)} 筆")

    # 統計新總量
    train_total = sum(1 for _ in open(train_file))
    valid_total = sum(1 for _ in open(valid_file))
    print(f"\n  新總量: {train_total} train + {valid_total} valid = {train_total + valid_total}")
    print(f"  新增佔比: {len(train_samples)}/{train_total} = {len(train_samples)*100/train_total:.1f}%")


if __name__ == "__main__":
    main()
