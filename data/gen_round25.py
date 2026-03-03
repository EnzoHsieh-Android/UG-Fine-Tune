#!/usr/bin/env python3
"""
Round 25：長距離 addon 識別泛化

針對 v6 (Round 24, ckpt 700) 的泛化問題：
- 「琥珀鐵觀音鮮奶半糖少冰加紅烏龍茶凍」→ 被拆成兩筆訂單
- 根因：品項和 addon 之間插入多個修飾詞後，模型失去 addon 關聯

產生兩類資料：
1. 長距離 addon（品項+類別+選項+加+加料）~30 筆
2. Anchor 防回歸 ~15 筆
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

NEW_SYSTEM = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，判斷意圖並輸出 JSON。\n\n"
    "意圖分類：\n"
    "- order：顧客要點餐（含具體品項）\n"
    "- recommend：顧客想要推薦（問推薦、不知道喝什麼、描述口味偏好）\n"
    "- other：閒聊或非點餐/推薦的問題\n\n"
    "菜單分類與品項描述：\n"
    "【研選純茶 pure_tea】單一尺寸\n"
    "- 三窨十五茉：三次窨花茉莉綠茶，花香清雅帶甘甜\n"
    "- 桂花輕烏龍：桂花與輕發酵烏龍，花果蜜韻輕柔\n"
    "- 茶花紅烏龍：重焙火紅烏龍，天然花香與熟果甜韻\n"
    "- 朱槿普洱紅：洛神花搭普洱紅茶，微酸回甘解膩\n"
    "- 米香玉露菁：日式玉露菁帶米穀香，鮮爽細膩\n\n"
    "【牧場直達 fresh_milk_tea】M/L\n"
    "- 三窨十五茉(65/75)：茉莉鮮奶，清香滑順\n"
    "- 桂花輕烏龍(65/75)：桂花烏龍鮮奶，蜜韻奶香溫潤\n"
    "- 茶花烏龍(65/75)：烏龍鮮奶，茶奶平衡圓潤\n"
    "- 琥珀鐵觀音(65/75)：重焙鐵觀音鮮奶，焙火香濃郁\n"
    "- 金杯蜜香紅(60/70)：蜜香紅茶鮮奶，天然蜜甜\n"
    "- 朱槿普洱紅(60/70)：洛神普洱鮮奶，微酸風味獨特\n"
    "- 米香玉露菁(60/70)：玉露菁鮮奶，穀物奶香療癒\n\n"
    "【UG奶茶 rich_milk_tea】M/L\n"
    "- 三窨十五茉(65/75)、桂花輕烏龍(65/75)、茶花紅烏龍(65/75)\n"
    "- 琥珀鐵觀音(65/75)、金杯蜜香紅(60/70)、朱槿普洱紅(60/70)、米香玉露菁(60/70)\n\n"
    "【果香四溢 fruit_tea】僅冷飲，單一尺寸\n"
    "- 青檸桂蜜(65)：青檸搭桂花蜜，酸甜清爽消暑\n"
    "- 蜜桃紅烏龍(75)：水蜜桃果香與紅烏龍交織，甜蜜芬芳\n"
    "- 葡柚十五茉(80)：葡萄柚酸香配茉莉，清新微苦大人味\n\n"
    "【雲頂奶蓋 cloud_velvet】單一尺寸\n"
    "- 桂花輕烏龍(95)：桂花烏龍覆綿密奶蓋，鹹甜交融\n"
    "- 茶花紅烏龍(95)：紅烏龍焙火韻搭奶蓋，茶香奶鹹平衡\n\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 正常糖/正常冰。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，設 not_on_menu。\n\n"
    "輸出格式（必須為合法 JSON）：\n"
    "點餐：{\"intent\":\"order\",\"orders\":[{\"item\":\"品名\",\"category\":\"分類\",\"size\":\"M/L/null\",\"ice\":\"冰量/null\",\"sugar\":\"甜度/null\",\"addon\":[],\"qty\":1,\"note\":\"\"}],\"recommendations\":[]}\n"
    "推薦：{\"intent\":\"recommend\",\"orders\":[],\"preferences\":{\"taste\":\"口味\",\"temperature\":\"溫度\",\"scenario\":\"場景\",\"avoid\":\"排除\"},\"recommendations\":[{\"item\":\"品名\",\"category\":\"分類\",\"reason\":\"推薦理由\"}]}\n"
    "混合（點餐+推薦）：orders 和 recommendations 同時有值。若最後一段已做出點餐決定，清空 recommendations。\n"
    "閒聊：{\"intent\":\"other\",\"orders\":[],\"recommendations\":[],\"note\":\"簡短回覆\"}"
)


def make(user, assistant):
    return json.dumps({"messages": [
        {"role": "system", "content": NEW_SYSTEM},
        {"role": "user", "content": user},
        {"role": "assistant", "content": json.dumps(assistant, ensure_ascii=False)},
    ]}, ensure_ascii=False)


def rec(item, category, reason):
    return {"item": item, "category": category, "reason": reason}


def order(item, cat, size, ice, sugar, addon=None, note=""):
    return {"item": item, "category": cat, "size": size, "ice": ice, "sugar": sugar,
            "addon": addon or [], "qty": 1, "note": note}


# ============================================================
# 1. 長距離 addon（品項+類別+選項+加+加料）~30 筆
#    核心模式：item + category + sugar + ice + 加 + addon
#    模型需學會：無論中間插了多少修飾詞，「加」後面都是 addon
# ============================================================

long_addon = []

# --- 鮮奶茶 + 甜度冰量 + 紅烏龍茶凍 ---
long_addon.append(make("琥珀鐵觀音鮮奶半糖少冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("三窨十五茉鮮奶微糖去冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "去冰", "微糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("桂花輕烏龍鮮奶無糖少冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "無糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("金杯蜜香紅鮮奶半糖微冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "微冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("朱槿普洱紅鮮奶少糖去冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("朱槿普洱紅", "fresh_milk_tea", "M", "去冰", "少糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("茶花烏龍鮮奶半糖少冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花烏龍", "fresh_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

# --- 鮮奶茶 + 甜度冰量 + 燕麥粒 ---
long_addon.append(make("琥珀鐵觀音鮮奶無糖去冰加燕麥粒", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "無糖", ["燕麥粒"])],
    "recommendations": []
}))

long_addon.append(make("三窨十五茉鮮奶半糖少冰加燕麥粒", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", ["燕麥粒"])],
    "recommendations": []
}))

long_addon.append(make("金杯蜜香紅鮮奶微糖微冰加燕麥粒", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "微冰", "微糖", ["燕麥粒"])],
    "recommendations": []
}))

# --- 奶茶 + 甜度冰量 + addon ---
long_addon.append(make("琥珀鐵觀音奶茶半糖少冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("桂花輕烏龍奶茶微糖去冰加燕麥粒", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "去冰", "微糖", ["燕麥粒"])],
    "recommendations": []
}))

long_addon.append(make("茶花紅烏龍奶茶無糖少冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "rich_milk_tea", "M", "少冰", "無糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("金杯蜜香紅奶茶半糖去冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "rich_milk_tea", "M", "去冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

# --- 大杯 + 甜度冰量 + addon ---
long_addon.append(make("大杯琥珀鐵觀音鮮奶半糖少冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "L", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("大杯三窨十五茉奶茶微糖去冰加燕麥粒", {
    "intent": "order",
    "orders": [order("三窨十五茉", "rich_milk_tea", "L", "去冰", "微糖", ["燕麥粒"])],
    "recommendations": []
}))

long_addon.append(make("大杯金杯蜜香紅鮮奶無糖加紅烏龍茶凍和燕麥粒", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "L", "正常冰", "無糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

# --- 甜度冰量 + 雙加料 ---
long_addon.append(make("琥珀鐵觀音鮮奶半糖少冰加紅烏龍茶凍和燕麥粒", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

long_addon.append(make("桂花輕烏龍奶茶微糖去冰加紅烏龍茶凍跟燕麥粒", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "去冰", "微糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

long_addon.append(make("三窨十五茉鮮奶無糖微冰加紅烏龍茶凍還有燕麥粒", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "微冰", "無糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

# --- 純茶 + 甜度冰量 + addon ---
long_addon.append(make("三窨十五茉純茶半糖去冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "去冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("桂花輕烏龍純茶微糖少冰加燕麥粒", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "pure_tea", None, "少冰", "微糖", ["燕麥粒"])],
    "recommendations": []
}))

long_addon.append(make("茶花紅烏龍純茶無糖去冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "pure_tea", None, "去冰", "無糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

# --- 口語/自然語氣 + 長距離 addon ---
long_addon.append(make("我要一杯琥珀鐵觀音鮮奶半糖少冰，加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("來一杯桂花輕烏龍奶茶微糖去冰，再加燕麥粒", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "去冰", "微糖", ["燕麥粒"])],
    "recommendations": []
}))

long_addon.append(make("給我金杯蜜香紅鮮奶無糖少冰，要加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "少冰", "無糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

long_addon.append(make("幫我來一杯大杯茶花紅烏龍奶茶半糖少冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "rich_milk_tea", "L", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

# --- 多品項 + 長距離 addon ---
long_addon.append(make("琥珀鐵觀音鮮奶半糖少冰加茶凍，跟一杯三窨十五茉純茶", {
    "intent": "order",
    "orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍"]),
        order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

long_addon.append(make("金杯蜜香紅鮮奶微糖去冰加燕麥粒，還要一杯桂花輕烏龍奶茶", {
    "intent": "order",
    "orders": [
        order("金杯蜜香紅", "fresh_milk_tea", "M", "去冰", "微糖", ["燕麥粒"]),
        order("桂花輕烏龍", "rich_milk_tea", "M", "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

long_addon.append(make("兩杯琥珀鐵觀音鮮奶半糖少冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M",
                "ice": "少冰", "sugar": "半糖", "addon": ["紅烏龍茶凍"], "qty": 2, "note": ""}],
    "recommendations": []
}))


# ============================================================
# 2. Anchor 防回歸 ~15 筆
#    來自 test_diversity_v3 和 test_recommend 的代表性通過案例
# ============================================================

anchor = []

# 基本點單
anchor.append(make("一杯三窨十五茉", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

anchor.append(make("茉莉無糖去冰", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "去冰", "無糖")],
    "recommendations": []
}))

# 縮寫
anchor.append(make("鐵觀音半糖少冰", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "pure_tea", None, "少冰", "半糖")],
    "recommendations": []
}))

# 多品項
anchor.append(make("三窨十五茉跟金杯蜜香紅", {
    "intent": "order",
    "orders": [
        order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖"),
        order("金杯蜜香紅", "pure_tea", None, "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

# 修改
anchor.append(make("金杯蜜香紅，啊，換成琥珀鐵觀音", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

# 口語
anchor.append(make("嗯，那就茉莉好了", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

anchor.append(make("讓我想想...好，金杯蜜香紅無糖", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "pure_tea", None, "正常冰", "無糖")],
    "recommendations": []
}))

# 推薦
anchor.append(make("有什麼推薦的嗎", {
    "intent": "recommend",
    "orders": [],
    "preferences": {"taste": "", "temperature": "", "scenario": "", "avoid": ""},
    "recommendations": [rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火香濃郁")]
}))

anchor.append(make("不要奶的", {
    "intent": "recommend",
    "orders": [],
    "preferences": {"taste": "", "temperature": "", "scenario": "", "avoid": "奶"},
    "recommendations": [rec("三窨十五茉", "pure_tea", "茉莉花茶，無奶純茶清爽")]
}))

anchor.append(make("純茶有什麼推薦", {
    "intent": "recommend",
    "orders": [],
    "preferences": {"taste": "純茶", "temperature": "", "scenario": "", "avoid": ""},
    "recommendations": [rec("三窨十五茉", "pure_tea", "三次窨花茉莉，花香清雅最經典")]
}))

# 閒聊
anchor.append(make("廁所在哪", {
    "intent": "other",
    "orders": [],
    "recommendations": [],
    "note": "洗手間在店內右側"
}))

# 短距離 addon（確保不回歸）
anchor.append(make("琥珀鐵觀音加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

anchor.append(make("茶花紅烏龍加紅烏龍茶凍半糖", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "pure_tea", None, "正常冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

anchor.append(make("金杯蜜香紅鮮奶加紅烏龍茶凍和燕麥粒", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

# ============================================================
# 寫出 JSONL
# ============================================================

all_examples = long_addon + anchor

out_path = os.path.join(BASE_DIR, "round25.jsonl")
with open(out_path, "w", encoding="utf-8") as f:
    for ex in all_examples:
        f.write(ex + "\n")

print(f"Round 25: {len(all_examples)} examples written to {out_path}")
print(f"  長距離 addon: {len(long_addon)}")
print(f"  Anchor: {len(anchor)}")
