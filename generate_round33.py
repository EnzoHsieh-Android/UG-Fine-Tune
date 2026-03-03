#!/usr/bin/env python3
"""Generate Round 33 training data for targeted improvements."""
import json
import random

random.seed(42)

# System prompt (same as existing training data)
with open("data/train.jsonl") as f:
    SYS_PROMPT = json.loads(f.readline())["messages"][0]["content"]

# Load existing user texts to avoid duplicates (C2)
EXISTING_INPUTS = set()
for split in ["train", "valid"]:
    with open(f"data/{split}.jsonl") as f:
        for line in f:
            d = json.loads(line)
            for m in d["messages"]:
                if m["role"] == "user":
                    EXISTING_INPUTS.add(m["content"])


def make_sample(user_text, assistant_json):
    """Create a training sample in chat format."""
    return {
        "messages": [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(assistant_json, ensure_ascii=False)},
        ]
    }


def order(item, category=None, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
    return {
        "item": item, "category": category, "size": size,
        "ice": ice, "sugar": sugar, "addon": addon or [], "qty": qty, "note": note,
    }


# ============================================================
# 1. 多輪 seg2 category=null (30 筆)
#    模式：seg1 有明確分類標記，seg2 只有品名+客製 → category=null
# ============================================================
multi_turn_cat_null = []

# seg1=fresh_milk_tea, seg2=null (10 筆)
mt_fresh = [
    ("琥珀鐵觀音鮮奶茶半糖少冰;再一杯金杯蜜香紅無糖去冰",
     [order("琥珀鐵觀音", "fresh_milk_tea", ice="少冰", sugar="半糖"),
      order("金杯蜜香紅", ice="去冰", sugar="無糖")]),
    ("三窨十五茉鮮奶茶大杯五分糖;再一杯琥珀鐵觀音去冰",
     [order("三窨十五茉", "fresh_milk_tea", size="L", sugar="五分糖"),
      order("琥珀鐵觀音", ice="去冰")]),
    ("金杯蜜香紅鮮奶茶半糖;再一杯三窨十五茉去冰",
     [order("金杯蜜香紅", "fresh_milk_tea", sugar="半糖"),
      order("三窨十五茉", ice="去冰")]),
    ("朱槿普洱紅鮮奶茶微冰;再一杯米香玉露菁半糖",
     [order("朱槿普洱紅", "fresh_milk_tea", ice="微冰"),
      order("米香玉露菁", sugar="半糖")]),
    ("米香玉露菁鮮奶茶半糖微冰;再來一杯茶花紅烏龍少冰",
     [order("米香玉露菁", "fresh_milk_tea", ice="微冰", sugar="半糖"),
      order("茶花紅烏龍", ice="少冰")]),
    ("茶花紅烏龍鮮奶茶大杯無糖;再一杯桂花輕烏龍三分糖少冰",
     [order("茶花紅烏龍", "fresh_milk_tea", size="L", sugar="無糖"),
      order("桂花輕烏龍", ice="少冰", sugar="三分糖")]),
    ("桂花輕烏龍鮮奶茶少冰半糖;再一杯朱槿普洱紅無糖去冰",
     [order("桂花輕烏龍", "fresh_milk_tea", ice="少冰", sugar="半糖"),
      order("朱槿普洱紅", ice="去冰", sugar="無糖")]),
    ("琥珀鐵觀音鮮奶茶大杯去冰;再一杯米香玉露菁一分糖",
     [order("琥珀鐵觀音", "fresh_milk_tea", size="L", ice="去冰"),
      order("米香玉露菁", sugar="一分糖")]),
    ("金杯蜜香紅鮮奶茶無糖少冰;再一杯朱槿普洱紅半糖",
     [order("金杯蜜香紅", "fresh_milk_tea", ice="少冰", sugar="無糖"),
      order("朱槿普洱紅", sugar="半糖")]),
    ("三窨十五茉鮮奶茶微冰;再一杯桂花輕烏龍五分糖去冰",
     [order("三窨十五茉", "fresh_milk_tea", ice="微冰"),
      order("桂花輕烏龍", ice="去冰", sugar="五分糖")]),
]

# seg1=cloud_velvet, seg2=null (5 筆)
mt_cloud = [
    ("茶花紅烏龍奶蓋;再一杯桂花輕烏龍半糖少冰",
     [order("茶花紅烏龍", "cloud_velvet"),
      order("桂花輕烏龍", ice="少冰", sugar="半糖")]),
    ("桂花輕烏龍奶蓋;再來一杯琥珀鐵觀音無糖去冰",
     [order("桂花輕烏龍", "cloud_velvet"),
      order("琥珀鐵觀音", ice="去冰", sugar="無糖")]),
    ("茶花紅烏龍奶蓋;再一杯金杯蜜香紅三分糖",
     [order("茶花紅烏龍", "cloud_velvet"),
      order("金杯蜜香紅", sugar="三分糖")]),
    ("桂花輕烏龍奶蓋;再一杯三窨十五茉半糖去冰",
     [order("桂花輕烏龍", "cloud_velvet"),
      order("三窨十五茉", ice="去冰", sugar="半糖")]),
    ("茶花紅烏龍奶蓋;再一杯米香玉露菁大杯少冰",
     [order("茶花紅烏龍", "cloud_velvet"),
      order("米香玉露菁", size="L", ice="少冰")]),
]

# seg1=pure_tea, seg2=null (5 筆)
mt_pure = [
    ("三窨十五茉純茶無糖去冰;再一杯米香玉露菁半糖少冰",
     [order("三窨十五茉", "pure_tea", ice="去冰", sugar="無糖"),
      order("米香玉露菁", ice="少冰", sugar="半糖")]),
    ("朱槿普洱紅純茶一杯去冰;再一杯桂花輕烏龍大杯五分糖",
     [order("朱槿普洱紅", "pure_tea", ice="去冰"),
      order("桂花輕烏龍", size="L", sugar="五分糖")]),
    ("桂花輕烏龍純茶無糖;再一杯金杯蜜香紅半糖微冰",
     [order("桂花輕烏龍", "pure_tea", sugar="無糖"),
      order("金杯蜜香紅", ice="微冰", sugar="半糖")]),
    ("茶花紅烏龍純茶去冰;再一杯琥珀鐵觀音大杯半糖",
     [order("茶花紅烏龍", "pure_tea", ice="去冰"),
      order("琥珀鐵觀音", size="L", sugar="半糖")]),
    ("米香玉露菁純茶少冰;再一杯三窨十五茉無糖去冰",
     [order("米香玉露菁", "pure_tea", ice="少冰"),
      order("三窨十五茉", ice="去冰", sugar="無糖")]),
]

# seg1=rich_milk_tea, seg2=null (5 筆)
mt_rich = [
    ("茶花紅烏龍奶茶大杯半糖少冰;再一杯朱槿普洱紅去冰無糖",
     [order("茶花紅烏龍", "rich_milk_tea", size="L", ice="少冰", sugar="半糖"),
      order("朱槿普洱紅", ice="去冰", sugar="無糖")]),
    ("琥珀鐵觀音奶茶半糖;再一杯桂花輕烏龍去冰",
     [order("琥珀鐵觀音", "rich_milk_tea", sugar="半糖"),
      order("桂花輕烏龍", ice="去冰")]),
    ("金杯蜜香紅奶茶大杯少冰;再一杯三窨十五茉無糖",
     [order("金杯蜜香紅", "rich_milk_tea", size="L", ice="少冰"),
      order("三窨十五茉", sugar="無糖")]),
    ("三窨十五茉奶茶五分糖微冰;再一杯琥珀鐵觀音去冰",
     [order("三窨十五茉", "rich_milk_tea", ice="微冰", sugar="五分糖"),
      order("琥珀鐵觀音", ice="去冰")]),
    ("朱槿普洱紅奶茶無糖去冰;再一杯茶花紅烏龍半糖",
     [order("朱槿普洱紅", "rich_milk_tea", ice="去冰", sugar="無糖"),
      order("茶花紅烏龍", sugar="半糖")]),
]

# seg1=fruit_tea, seg2=null (5 筆)
mt_fruit = [
    ("蜜桃紅烏龍一杯;再來一杯金杯蜜香紅半糖少冰",
     [order("蜜桃紅烏龍", "fruit_tea"),
      order("金杯蜜香紅", ice="少冰", sugar="半糖")]),
    ("葡柚十五茉一杯;再一杯琥珀鐵觀音大杯無糖去冰",
     [order("葡柚十五茉", "fruit_tea"),
      order("琥珀鐵觀音", size="L", ice="去冰", sugar="無糖")]),
    ("青檸桂蜜一杯;再一杯桂花輕烏龍三分糖",
     [order("青檸桂蜜", "fruit_tea"),
      order("桂花輕烏龍", sugar="三分糖")]),
    ("蜜桃紅烏龍;再一杯三窨十五茉半糖去冰",
     [order("蜜桃紅烏龍", "fruit_tea"),
      order("三窨十五茉", ice="去冰", sugar="半糖")]),
    ("葡柚十五茉;再一杯米香玉露菁少冰無糖",
     [order("葡柚十五茉", "fruit_tea"),
      order("米香玉露菁", ice="少冰", sugar="無糖")]),
]

for user, orders_list in mt_fresh + mt_cloud + mt_pure + mt_rich + mt_fruit:
    multi_turn_cat_null.append(make_sample(user, {
        "intents": ["order", "order"],
        "orders": orders_list,
        "preferences": {},
        "recommendations": [],
    }))


# ============================================================
# 2. 數量拆分 qty>1 (20 筆)
#    模式：同品項不同客製 → qty 欄位表示數量
# ============================================================
qty_split = []

# 同品項不同甜度拆分 (7 筆)
qty_sugar = [
    ("三杯三窨十五茉鮮奶茶少冰，兩杯半糖一杯無糖",
     [order("三窨十五茉", "fresh_milk_tea", ice="少冰", sugar="半糖", qty=2),
      order("三窨十五茉", "fresh_milk_tea", ice="少冰", sugar="無糖", qty=1)]),
    ("四杯琥珀鐵觀音奶茶，三杯半糖一杯全糖",
     [order("琥珀鐵觀音", "rich_milk_tea", sugar="半糖", qty=3),
      order("琥珀鐵觀音", "rich_milk_tea", sugar="全糖", qty=1)]),
    ("兩杯金杯蜜香紅鮮奶茶，一杯無糖一杯五分糖",
     [order("金杯蜜香紅", "fresh_milk_tea", sugar="無糖", qty=1),
      order("金杯蜜香紅", "fresh_milk_tea", sugar="五分糖", qty=1)]),
    ("五杯桂花輕烏龍純茶，三杯無糖兩杯三分糖",
     [order("桂花輕烏龍", "pure_tea", sugar="無糖", qty=3),
      order("桂花輕烏龍", "pure_tea", sugar="三分糖", qty=2)]),
    ("三杯茶花紅烏龍奶茶大杯，兩杯半糖一杯一分糖",
     [order("茶花紅烏龍", "rich_milk_tea", size="L", sugar="半糖", qty=2),
      order("茶花紅烏龍", "rich_milk_tea", size="L", sugar="一分糖", qty=1)]),
    ("兩杯米香玉露菁鮮奶茶，一杯半糖少冰一杯無糖去冰",
     [order("米香玉露菁", "fresh_milk_tea", ice="少冰", sugar="半糖", qty=1),
      order("米香玉露菁", "fresh_milk_tea", ice="去冰", sugar="無糖", qty=1)]),
    ("三杯朱槿普洱紅純茶去冰，一杯無糖兩杯三分糖",
     [order("朱槿普洱紅", "pure_tea", ice="去冰", sugar="無糖", qty=1),
      order("朱槿普洱紅", "pure_tea", ice="去冰", sugar="三分糖", qty=2)]),
]

# 同品項不同分類拆分 (7 筆)
qty_cat = [
    ("三杯桂花輕烏龍，兩杯奶茶半糖少冰，一杯純茶無糖去冰",
     [order("桂花輕烏龍", "rich_milk_tea", ice="少冰", sugar="半糖", qty=2),
      order("桂花輕烏龍", "pure_tea", ice="去冰", sugar="無糖", qty=1)]),
    ("兩杯琥珀鐵觀音，鮮奶茶的大杯半糖去冰，奶茶的無糖少冰",
     [order("琥珀鐵觀音", "fresh_milk_tea", size="L", ice="去冰", sugar="半糖", qty=1),
      order("琥珀鐵觀音", "rich_milk_tea", ice="少冰", sugar="無糖", qty=1)]),
    ("三杯茶花紅烏龍，一杯純茶無糖，一杯鮮奶茶半糖，一杯奶蓋",
     [order("茶花紅烏龍", "pure_tea", sugar="無糖", qty=1),
      order("茶花紅烏龍", "fresh_milk_tea", sugar="半糖", qty=1),
      order("茶花紅烏龍", "cloud_velvet", qty=1)]),
    ("兩杯三窨十五茉，一杯純茶無糖去冰，一杯奶茶半糖少冰",
     [order("三窨十五茉", "pure_tea", ice="去冰", sugar="無糖", qty=1),
      order("三窨十五茉", "rich_milk_tea", ice="少冰", sugar="半糖", qty=1)]),
    ("四杯金杯蜜香紅，兩杯鮮奶茶半糖，兩杯奶茶無糖",
     [order("金杯蜜香紅", "fresh_milk_tea", sugar="半糖", qty=2),
      order("金杯蜜香紅", "rich_milk_tea", sugar="無糖", qty=2)]),
    ("兩杯朱槿普洱紅，一杯鮮奶茶大杯少冰，一杯純茶去冰無糖",
     [order("朱槿普洱紅", "fresh_milk_tea", size="L", ice="少冰", qty=1),
      order("朱槿普洱紅", "pure_tea", ice="去冰", sugar="無糖", qty=1)]),
    ("三杯米香玉露菁，兩杯鮮奶茶半糖少冰，一杯純茶無糖",
     [order("米香玉露菁", "fresh_milk_tea", ice="少冰", sugar="半糖", qty=2),
      order("米香玉露菁", "pure_tea", sugar="無糖", qty=1)]),
]

# 同品項不同冰量拆分 (3 筆)
qty_ice = [
    ("三杯琥珀鐵觀音鮮奶茶半糖，一杯去冰兩杯少冰",
     [order("琥珀鐵觀音", "fresh_milk_tea", ice="去冰", sugar="半糖", qty=1),
      order("琥珀鐵觀音", "fresh_milk_tea", ice="少冰", sugar="半糖", qty=2)]),
    ("兩杯桂花輕烏龍奶茶無糖，一杯少冰一杯去冰",
     [order("桂花輕烏龍", "rich_milk_tea", ice="少冰", sugar="無糖", qty=1),
      order("桂花輕烏龍", "rich_milk_tea", ice="去冰", sugar="無糖", qty=1)]),
    ("四杯三窨十五茉純茶，兩杯去冰兩杯少冰",
     [order("三窨十五茉", "pure_tea", ice="去冰", qty=2),
      order("三窨十五茉", "pure_tea", ice="少冰", qty=2)]),
]

# 同品項不同尺寸拆分 (3 筆)
qty_size = [
    ("三杯金杯蜜香紅奶茶半糖，一杯中杯兩杯大杯",
     [order("金杯蜜香紅", "rich_milk_tea", size="M", sugar="半糖", qty=1),
      order("金杯蜜香紅", "rich_milk_tea", size="L", sugar="半糖", qty=2)]),
    ("兩杯茶花紅烏龍鮮奶茶無糖少冰，一杯中杯一杯大杯",
     [order("茶花紅烏龍", "fresh_milk_tea", size="M", ice="少冰", sugar="無糖", qty=1),
      order("茶花紅烏龍", "fresh_milk_tea", size="L", ice="少冰", sugar="無糖", qty=1)]),
    ("四杯琥珀鐵觀音鮮奶茶，兩杯大杯半糖兩杯中杯無糖",
     [order("琥珀鐵觀音", "fresh_milk_tea", size="L", sugar="半糖", qty=2),
      order("琥珀鐵觀音", "fresh_milk_tea", size="M", sugar="無糖", qty=2)]),
]

for user, orders_list in qty_sugar + qty_cat + qty_ice + qty_size:
    qty_split.append(make_sample(user, {
        "intents": ["order"],
        "orders": orders_list,
        "preferences": {},
        "recommendations": [],
    }))


# ============================================================
# 3. 雙份混合加料 (10 筆)
#    「雙份X和Y」→ [X, X, Y]
# ============================================================
double_addon_mix = []

da_samples = [
    ("琥珀鐵觀音鮮奶茶大杯半糖少冰加雙份茶凍和燕麥",
     order("琥珀鐵觀音", "fresh_milk_tea", size="L", ice="少冰", sugar="半糖",
           addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])),
    ("金杯蜜香紅奶茶加雙份燕麥和茶凍",
     order("金杯蜜香紅", "rich_milk_tea",
           addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])),
    ("三窨十五茉鮮奶茶半糖加雙份茶凍跟燕麥粒",
     order("三窨十五茉", "fresh_milk_tea", sugar="半糖",
           addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])),
    ("桂花輕烏龍鮮奶茶中杯無糖去冰加雙份茶凍和燕麥",
     order("桂花輕烏龍", "fresh_milk_tea", size="M", ice="去冰", sugar="無糖",
           addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])),
    ("茶花紅烏龍奶茶大杯半糖少冰加雙份燕麥跟茶凍",
     order("茶花紅烏龍", "rich_milk_tea", size="L", ice="少冰", sugar="半糖",
           addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])),
    ("朱槿普洱紅鮮奶茶加兩份茶凍和一份燕麥",
     order("朱槿普洱紅", "fresh_milk_tea",
           addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])),
    ("米香玉露菁奶茶半糖少冰加雙份茶凍還有燕麥",
     order("米香玉露菁", "rich_milk_tea", ice="少冰", sugar="半糖",
           addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])),
    ("琥珀鐵觀音鮮奶茶加兩份燕麥粒跟一份茶凍",
     order("琥珀鐵觀音", "fresh_milk_tea",
           addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])),
    ("金杯蜜香紅鮮奶茶大杯加雙份茶凍還要燕麥粒",
     order("金杯蜜香紅", "fresh_milk_tea", size="L",
           addon=["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"])),
    ("三窨十五茉奶茶半糖去冰加雙份燕麥再加茶凍",
     order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="半糖",
           addon=["燕麥粒", "燕麥粒", "紅烏龍茶凍"])),
]

for user, o in da_samples:
    double_addon_mix.append(make_sample(user, {
        "intents": ["order"],
        "orders": [o],
        "preferences": {},
        "recommendations": [],
    }))


# ============================================================
# 4. 桂花輕烏龍 category=null (5 筆)
#    單獨點「桂花輕烏龍」不指定分類 → null
# ============================================================
guihua_null = []

gn_samples = [
    ("桂花輕烏龍", order("桂花輕烏龍")),
    ("一杯桂花輕烏龍", order("桂花輕烏龍")),
    ("來杯桂花輕烏龍半糖少冰", order("桂花輕烏龍", ice="少冰", sugar="半糖")),
    ("桂花輕烏龍一杯去冰", order("桂花輕烏龍", ice="去冰")),
    ("桂花輕烏龍無糖", order("桂花輕烏龍", sugar="無糖")),
]

for user, o in gn_samples:
    guihua_null.append(make_sample(user, {
        "intents": ["order"],
        "orders": [o],
        "preferences": {},
        "recommendations": [],
    }))


# ============================================================
# 5. Anchor 回歸防護 (15 筆)
#    從已通過的測試類別中抽取代表性範例
# ============================================================
anchor = []

# 標準點餐 (3 筆 - 不與現有重複)
anchor.append(make_sample("來一杯朱槿普洱紅", {
    "intents": ["order"],
    "orders": [order("朱槿普洱紅")],
    "preferences": {}, "recommendations": [],
}))
anchor.append(make_sample("三窨十五茉跟琥珀鐵觀音鮮奶茶還有蜜桃紅烏龍", {
    "intents": ["order"],
    "orders": [
        order("三窨十五茉"),
        order("琥珀鐵觀音", "fresh_milk_tea"),
        order("蜜桃紅烏龍", "fruit_tea"),
    ],
    "preferences": {}, "recommendations": [],
}))
anchor.append(make_sample("兩杯米香玉露菁", {
    "intents": ["order"],
    "orders": [order("米香玉露菁", qty=2)],
    "preferences": {}, "recommendations": [],
}))

# 甜度照錄 (3 筆 - 不與現有重複)
anchor.append(make_sample("琥珀鐵觀音半糖少冰", {
    "intents": ["order"],
    "orders": [order("琥珀鐵觀音", ice="少冰", sugar="半糖")],
    "preferences": {}, "recommendations": [],
}))
anchor.append(make_sample("茶花紅烏龍少糖去冰", {
    "intents": ["order"],
    "orders": [order("茶花紅烏龍", ice="去冰", sugar="少糖")],
    "preferences": {}, "recommendations": [],
}))
anchor.append(make_sample("朱槿普洱紅微糖微冰", {
    "intents": ["order"],
    "orders": [order("朱槿普洱紅", ice="微冰", sugar="微糖")],
    "preferences": {}, "recommendations": [],
}))

# 推薦 (2 筆 - 不與現有重複)
anchor.append(make_sample("有沒有適合夏天喝的", {
    "intents": ["recommend"],
    "orders": [],
    "preferences": {"場景": "夏天"},
    "recommendations": [{"item": "青檸桂蜜", "category": "fruit_tea", "reason": "青檸搭桂花蜜，酸甜清爽消暑，適合夏天飲用"}],
}))
anchor.append(make_sample("我想喝奶茶類的有推薦嗎", {
    "intents": ["recommend"],
    "orders": [],
    "preferences": {"口味": "奶茶"},
    "recommendations": [{"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "重焙鐵觀音搭配奶茶，焙火香濃郁"}],
}))

# 閒聊 (1 筆 - 不與現有重複)
anchor.append(make_sample("可以外帶嗎", {
    "intents": ["other"],
    "orders": [],
    "preferences": {},
    "recommendations": [],
}))

# 跨分類 (3 筆 - 不與現有重複，避免獨立「鮮奶」)
anchor.append(make_sample("兩杯金杯蜜香紅，一杯鮮奶茶的半糖去冰，一杯奶茶的無糖少冰", {
    "intents": ["order"],
    "orders": [
        order("金杯蜜香紅", "fresh_milk_tea", ice="去冰", sugar="半糖"),
        order("金杯蜜香紅", "rich_milk_tea", ice="少冰", sugar="無糖"),
    ],
    "preferences": {}, "recommendations": [],
}))
anchor.append(make_sample("三窨十五茉純茶無糖，再一杯鮮奶茶的大杯半糖少冰", {
    "intents": ["order"],
    "orders": [
        order("三窨十五茉", "pure_tea", sugar="無糖"),
        order("三窨十五茉", "fresh_milk_tea", size="L", ice="少冰", sugar="半糖"),
    ],
    "preferences": {}, "recommendations": [],
}))
anchor.append(make_sample("茶花紅烏龍奶蓋微糖，再一杯茶花紅烏龍奶茶大杯無糖去冰", {
    "intents": ["order"],
    "orders": [
        order("茶花紅烏龍", "cloud_velvet", sugar="微糖"),
        order("茶花紅烏龍", "rich_milk_tea", size="L", ice="去冰", sugar="無糖"),
    ],
    "preferences": {}, "recommendations": [],
}))

# 雙份加料 (3 筆 - 不與現有重複)
anchor.append(make_sample("金杯蜜香紅鮮奶茶大杯半糖少冰加雙份茶凍", {
    "intents": ["order"],
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", size="L", ice="少冰", sugar="半糖",
                     addon=["紅烏龍茶凍", "紅烏龍茶凍"])],
    "preferences": {}, "recommendations": [],
}))
anchor.append(make_sample("三窨十五茉奶茶加兩份燕麥粒無糖去冰", {
    "intents": ["order"],
    "orders": [order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="無糖",
                     addon=["燕麥粒", "燕麥粒"])],
    "preferences": {}, "recommendations": [],
}))
anchor.append(make_sample("桂花輕烏龍奶蓋加雙份燕麥粒", {
    "intents": ["order"],
    "orders": [order("桂花輕烏龍", "cloud_velvet",
                     addon=["燕麥粒", "燕麥粒"])],
    "preferences": {}, "recommendations": [],
}))


# ============================================================
# Output — dedup against existing training data (C2 prevention)
# ============================================================
all_samples = multi_turn_cat_null + qty_split + double_addon_mix + guihua_null + anchor

# Filter out any samples whose user text already exists in train/valid
filtered = []
skipped = []
seen_new = set()
for sample in all_samples:
    user_text = next(m["content"] for m in sample["messages"] if m["role"] == "user")
    if user_text in EXISTING_INPUTS:
        skipped.append(user_text)
    elif user_text in seen_new:
        skipped.append(f"[self-dup] {user_text}")
    else:
        filtered.append(sample)
        seen_new.add(user_text)

print(f"多輪 category=null: {len(multi_turn_cat_null)}")
print(f"數量拆分 qty: {len(qty_split)}")
print(f"雙份混合加料: {len(double_addon_mix)}")
print(f"桂花輕烏龍 null: {len(guihua_null)}")
print(f"Anchor 回歸防護: {len(anchor)}")
print(f"總計(生成): {len(all_samples)}")
print(f"去重後: {len(filtered)} (跳過 {len(skipped)} 筆)")
if skipped:
    for s in skipped:
        print(f"  [SKIP] {s}")

with open("data/round33.jsonl", "w") as f:
    for sample in filtered:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")

print(f"\n已寫入 data/round33.jsonl ({len(filtered)} 筆)")
