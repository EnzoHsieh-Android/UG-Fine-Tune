#!/usr/bin/env python3
"""
Round 24：加料識別 + 意圖邊界優化

針對 v5 (Round 23, ckpt 600) 的 7 個失敗案例：
- P0：加料被拆成獨立品項（「紅烏龍茶凍」→「茶花紅烏龍」+「茶凍」）
- P1-a：口語模糊被判為推薦（「嗯，那就茉莉好了」）
- P1-b：推薦意圖被判為點餐（「你們招牌是什麼」「不要奶的」）

產生四類資料：
1. 加料識別 ~40 筆（P0）
2. 口語模糊→點餐 ~20 筆（P1-a）
3. 推薦邊界釐清 ~15 筆（P1-b）
4. Anchor 防回歸 ~25 筆（P2）
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
# 1. P0：加料識別（~40 筆）
#    核心問題：「紅烏龍茶凍」被拆成「茶花紅烏龍」+「凍」
#    學習目標：「紅烏龍茶凍」是單一 addon，不可拆解
# ============================================================

addon_examples = []

# --- 各品項 + 紅烏龍茶凍（全名） ---
addon_examples.append(make("桂花輕烏龍奶茶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("琥珀鐵觀音鮮奶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("三窨十五茉鮮奶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("金杯蜜香紅鮮奶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("茶花烏龍鮮奶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花烏龍", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("朱槿普洱紅鮮奶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("朱槿普洱紅", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("米香玉露菁鮮奶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("米香玉露菁", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

# --- 易混淆：茶花紅烏龍 + 紅烏龍茶凍（品項名與 addon 名高度重疊） ---
addon_examples.append(make("茶花紅烏龍奶茶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "rich_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("茶花紅烏龍純茶加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "pure_tea", None, "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("茶花紅烏龍奶蓋加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "cloud_velvet", None, "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("茶花紅烏龍奶茶加紅烏龍茶凍半糖去冰", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "rich_milk_tea", "M", "去冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

# --- 各品項 + 燕麥粒 ---
addon_examples.append(make("琥珀鐵觀音鮮奶加燕麥粒", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖", ["燕麥粒"])],
    "recommendations": []
}))

addon_examples.append(make("三窨十五茉鮮奶加燕麥粒", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "正常糖", ["燕麥粒"])],
    "recommendations": []
}))

addon_examples.append(make("桂花輕烏龍鮮奶加燕麥粒", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "正常冰", "正常糖", ["燕麥粒"])],
    "recommendations": []
}))

addon_examples.append(make("金杯蜜香紅奶茶加燕麥粒", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "rich_milk_tea", "M", "正常冰", "正常糖", ["燕麥粒"])],
    "recommendations": []
}))

addon_examples.append(make("茶花紅烏龍奶茶加燕麥粒", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "rich_milk_tea", "M", "正常冰", "正常糖", ["燕麥粒"])],
    "recommendations": []
}))

# --- 雙加料 ---
addon_examples.append(make("桂花輕烏龍鮮奶加紅烏龍茶凍和燕麥粒", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

addon_examples.append(make("琥珀鐵觀音奶茶加茶凍跟燕麥粒", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

addon_examples.append(make("金杯蜜香紅鮮奶加茶凍和燕麥粒", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

addon_examples.append(make("三窨十五茉鮮奶加紅烏龍茶凍跟燕麥粒", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

# --- 簡稱：「茶凍」→紅烏龍茶凍、「燕麥」→燕麥粒 ---
addon_examples.append(make("三窨十五茉鮮奶加茶凍", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("桂花鮮奶加茶凍", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("鐵觀音鮮奶加茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("金杯鮮奶加茶凍半糖", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("茉莉奶茶加燕麥", {
    "intent": "order",
    "orders": [order("三窨十五茉", "rich_milk_tea", "M", "正常冰", "正常糖", ["燕麥粒"])],
    "recommendations": []
}))

# --- 加料 + 客製選項混合 ---
addon_examples.append(make("茉莉鮮奶半糖少冰加茶凍", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("桂花輕烏龍奶茶半糖去冰加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "去冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("琥珀鐵觀音鮮奶L半糖加茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "L", "正常冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("金杯蜜香紅鮮奶微糖微冰加燕麥粒", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "微冰", "微糖", ["燕麥粒"])],
    "recommendations": []
}))

# --- 不同動詞：要、再來個、再加 ---
addon_examples.append(make("桂花奶茶要茶凍", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "rich_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("鐵觀音鮮奶要燕麥粒", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖", ["燕麥粒"])],
    "recommendations": []
}))

addon_examples.append(make("金杯蜜香紅鮮奶要紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("茉莉鮮奶再來個茶凍", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("琥珀鐵觀音鮮奶半糖，再加茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

# --- 多品項 + 加料（加料只歸屬其中一杯 / 各自加料） ---
addon_examples.append(make("三窨十五茉鮮奶半糖少冰；琥珀鐵觀音鮮奶加茶凍", {
    "intent": "order",
    "orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"]),
    ],
    "recommendations": []
}))

addon_examples.append(make("桂花輕烏龍鮮奶加茶凍；金杯蜜香紅鮮奶加燕麥粒", {
    "intent": "order",
    "orders": [
        order("桂花輕烏龍", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"]),
        order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "正常糖", ["燕麥粒"]),
    ],
    "recommendations": []
}))

addon_examples.append(make("一杯茉莉鮮奶加茶凍，一杯鐵觀音鮮奶", {
    "intent": "order",
    "orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "正常糖", ["紅烏龍茶凍"]),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

# --- 果茶/奶蓋 + 加料 ---
addon_examples.append(make("蜜桃紅烏龍加茶凍", {
    "intent": "order",
    "orders": [order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("桂花輕烏龍奶蓋加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "cloud_velvet", None, "正常冰", "正常糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

addon_examples.append(make("青檸桂蜜加燕麥粒", {
    "intent": "order",
    "orders": [order("青檸桂蜜", "fruit_tea", None, "正常冰", "正常糖", ["燕麥粒"])],
    "recommendations": []
}))


# ============================================================
# 2. P1-a：口語模糊→正確判為點餐（~20 筆）
#    核心問題：含具體品項名但語氣猶豫/口語化，被誤判為 recommend
#    學習目標：只要有具體品項+決定語氣 = intent:order
# ============================================================

oral_examples = []

oral_examples.append(make("嗯，那就茉莉好了", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("請問有桂花嗎？那我要一杯", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("讓我想想...好，金杯蜜香紅無糖", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "無糖")],
    "recommendations": []
}))

oral_examples.append(make("好吧那鐵觀音鮮奶", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("算了還是桂花好了", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("那個...茉莉鮮奶吧", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("就桂花純茶去冰", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "pure_tea", None, "去冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("給我來杯蜜桃吧", {
    "intent": "order",
    "orders": [order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("我朋友推薦的茶花紅烏龍，來一杯", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("對，就茉莉鮮奶半糖", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "半糖")],
    "recommendations": []
}))

oral_examples.append(make("好久沒喝了，來杯鐵觀音鮮奶", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("嗯...那茉莉好了，半糖少冰", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "少冰", "半糖")],
    "recommendations": []
}))

oral_examples.append(make("啊對，我要桂花奶蓋", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "cloud_velvet", None, "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("想想看...好，普洱純茶去冰", {
    "intent": "order",
    "orders": [order("朱槿普洱紅", "pure_tea", None, "去冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("欸那就蜜桃紅烏龍吧", {
    "intent": "order",
    "orders": [order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("我看看...嗯那金杯蜜香紅鮮奶", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("你們有玉露嗎？那來一杯去冰", {
    "intent": "order",
    "orders": [order("米香玉露菁", "pure_tea", None, "去冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("好啦好啦，給我桂花鮮奶", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": []
}))

oral_examples.append(make("想一下...好，琥珀鐵觀音奶茶半糖", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "正常冰", "半糖")],
    "recommendations": []
}))

oral_examples.append(make("哦那就三窨十五茉純茶好了", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))


# ============================================================
# 3. P1-b：推薦意圖邊界（~15 筆）
#    核心問題：「你們招牌是什麼」「不要奶的」被判為 order
#    學習目標：沒有指定具體品項的詢問/偏好 = recommend
# ============================================================

recommend_examples = []

# 強化：直接對應失敗的測試案例
recommend_examples.append(make("你們招牌是什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "桂花烏龍覆綿密奶蓋，鹹甜交融，招牌必喝"),
    ]
}))

recommend_examples.append(make("不要奶的", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "茉莉花茶，花香清雅無奶"),
    ]
}))

# 「招牌」變體
recommend_examples.append(make("你們最紅的是哪杯", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶最多人點，茶味濃郁"),
    ]
}))

recommend_examples.append(make("什麼最受歡迎", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "焙火鐵觀音鮮奶，回購率最高"),
    ]
}))

recommend_examples.append(make("你們的招牌飲料是什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "桂花奶蓋鹹甜交融，招牌之選"),
    ]
}))

recommend_examples.append(make("哪幾款是招牌", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，茶味最濃郁人氣第一"),
    ]
}))

recommend_examples.append(make("最暢銷的推薦一下", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，回購率最高"),
    ]
}))

recommend_examples.append(make("你們哪些是必喝的", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "桂花奶蓋鹹甜交融，必喝招牌"),
    ]
}))

# 「不要奶」變體
recommend_examples.append(make("不喝奶的話有什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "茉莉花茶花香清雅，完全無奶"),
    ]
}))

recommend_examples.append(make("不加奶推薦什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶"},
    "recommendations": [
        rec("桂花輕烏龍", "pure_tea", "桂花蜜韻輕柔，無奶純茶"),
    ]
}))

recommend_examples.append(make("沒有奶的推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶"},
    "recommendations": [
        rec("米香玉露菁", "pure_tea", "日式玉露菁無奶，米穀香鮮爽"),
    ]
}))

recommend_examples.append(make("不想喝有奶的", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶"},
    "recommendations": [
        rec("朱槿普洱紅", "pure_tea", "普洱紅茶微酸回甘，無奶清爽"),
    ]
}))

recommend_examples.append(make("有什麼不含奶的選擇", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶"},
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "青檸果茶無奶，酸甜清爽消暑"),
    ]
}))

# 比較型（提到品項名但非點餐）
recommend_examples.append(make("茉莉跟桂花哪個好喝", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "pure_tea", "桂花蜜韻輕柔口感溫潤，兩者各有特色都值得試"),
    ]
}))

recommend_examples.append(make("除了奶茶還有什麼好喝的", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶茶"},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "奶蓋鹹甜交融，跟奶茶完全不同風味"),
    ]
}))


# ============================================================
# 3b. P1-c：口味偏好 × 分類交叉推薦（~15 筆）
#    核心問題：「茶味重的奶茶」應推薦 rich_milk_tea，不是 fresh_milk_tea
#    學習目標：推薦品項的 category 要對應顧客指定的分類
# ============================================================

category_taste_examples = []

# --- 奶茶 (rich_milk_tea) ---
category_taste_examples.append(make("茶味重一點的奶茶", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "茶味重", "scenario": "奶茶"},
    "recommendations": [
        rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音奶茶，重焙火香氣最濃郁"),
    ]
}))

category_taste_examples.append(make("花香的奶茶推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "花香", "scenario": "奶茶"},
    "recommendations": [
        rec("桂花輕烏龍", "rich_milk_tea", "桂花烏龍奶茶，蜜韻奶香濃厚"),
    ]
}))

category_taste_examples.append(make("甜一點的奶茶", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "甜", "scenario": "奶茶"},
    "recommendations": [
        rec("金杯蜜香紅", "rich_milk_tea", "蜜香紅茶奶茶，自然蜜甜奶滑"),
    ]
}))

category_taste_examples.append(make("有什麼特別的奶茶", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "特別", "scenario": "奶茶"},
    "recommendations": [
        rec("朱槿普洱紅", "rich_milk_tea", "洛神普洱奶茶，微酸奶香風味獨特"),
    ]
}))

category_taste_examples.append(make("濃郁的奶茶推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "濃郁", "scenario": "奶茶"},
    "recommendations": [
        rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音奶茶，重焙火香搭配奶底更顯濃郁"),
    ]
}))

# --- 鮮奶茶 (fresh_milk_tea) ---
category_taste_examples.append(make("茶味重的鮮奶推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "茶味重", "scenario": "鮮奶茶"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火香濃郁茶味最重"),
    ]
}))

category_taste_examples.append(make("花香的鮮奶茶有嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "花香", "scenario": "鮮奶茶"},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，蜜韻奶香溫潤"),
    ]
}))

category_taste_examples.append(make("不苦的鮮奶茶推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "不苦", "avoid": "苦", "scenario": "鮮奶茶"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜完全不苦"),
    ]
}))

category_taste_examples.append(make("溫潤一點的鮮奶茶", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "溫潤", "scenario": "鮮奶茶"},
    "recommendations": [
        rec("米香玉露菁", "fresh_milk_tea", "玉露菁鮮奶，穀物奶香溫暖療癒"),
    ]
}))

category_taste_examples.append(make("清爽的鮮奶推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "清爽", "scenario": "鮮奶茶"},
    "recommendations": [
        rec("三窨十五茉", "fresh_milk_tea", "茉莉鮮奶，清香滑順不膩"),
    ]
}))

# --- 純茶 (pure_tea) ---
category_taste_examples.append(make("清爽的純茶推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "清爽", "scenario": "純茶"},
    "recommendations": [
        rec("米香玉露菁", "pure_tea", "日式玉露菁帶米穀香，鮮爽細膩"),
    ]
}))

category_taste_examples.append(make("想喝純茶，不要太苦的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "不苦", "avoid": "苦", "scenario": "純茶"},
    "recommendations": [
        rec("桂花輕烏龍", "pure_tea", "輕發酵烏龍花果蜜韻輕柔，不苦不澀"),
    ]
}))

category_taste_examples.append(make("有酸味的純茶嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "酸", "scenario": "純茶"},
    "recommendations": [
        rec("朱槿普洱紅", "pure_tea", "洛神花搭普洱紅茶，微酸回甘解膩"),
    ]
}))

category_taste_examples.append(make("茶味重的純茶", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "茶味重", "scenario": "純茶"},
    "recommendations": [
        rec("茶花紅烏龍", "pure_tea", "重焙火紅烏龍，茶味厚實帶熟果甜韻"),
    ]
}))

category_taste_examples.append(make("想喝純茶花香的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "花香", "scenario": "純茶"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "三次窨花茉莉綠茶，花香最清雅"),
    ]
}))


# ============================================================
# 4. P2：Anchor 防回歸（~25 筆）
#    從已通過的測試案例中選取代表性樣本
# ============================================================

anchors = []

# --- 基本點餐 ---
anchors.append(make("來一杯三窨十五茉", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

anchors.append(make("琥珀鐵觀音鮮奶半糖去冰", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("大杯金杯蜜香紅奶茶", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "rich_milk_tea", "L", "正常冰", "正常糖")],
    "recommendations": []
}))

anchors.append(make("蜜桃紅烏龍微糖", {
    "intent": "order",
    "orders": [order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "微糖")],
    "recommendations": []
}))

anchors.append(make("茶花紅烏龍奶蓋", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "cloud_velvet", None, "正常冰", "正常糖")],
    "recommendations": []
}))

# --- 縮寫 ---
anchors.append(make("茉莉無糖去冰", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "去冰", "無糖")],
    "recommendations": []
}))

anchors.append(make("鐵觀音半糖少冰", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖")],
    "recommendations": []
}))

# --- 多品項 ---
anchors.append(make("三窨十五茉跟金杯蜜香紅", {
    "intent": "order",
    "orders": [
        order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖"),
        order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

anchors.append(make("一杯蜜桃紅烏龍半糖；一杯青檸桂蜜微糖", {
    "intent": "order",
    "orders": [
        order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "半糖"),
        order("青檸桂蜜", "fruit_tea", None, "正常冰", "微糖"),
    ],
    "recommendations": []
}))

# --- 數量 ---
anchors.append(make("兩杯桂花輕烏龍純茶", {
    "intent": "order",
    "orders": [{"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": "正常糖", "addon": [], "qty": 2, "note": ""}],
    "recommendations": []
}))

# --- 修改/取消 ---
anchors.append(make("金杯蜜香紅，啊，換成琥珀鐵觀音", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": []
}))

anchors.append(make("茉莉和桂花，桂花取消", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

# --- 尺寸/類別 ---
anchors.append(make("桂花輕烏龍鮮奶半糖少冰", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("青檸桂蜜少糖", {
    "intent": "order",
    "orders": [order("青檸桂蜜", "fruit_tea", None, "正常冰", "少糖")],
    "recommendations": []
}))

anchors.append(make("熱的琥珀鐵觀音鮮奶半糖", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "熱飲", "半糖")],
    "recommendations": []
}))

# --- 推薦 anchor ---
anchors.append(make("有什麼推薦的嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶蜜韻溫潤"),
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶清雅甘甜"),
    ]
}))

anchors.append(make("推薦一下", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶焙火香濃郁"),
        rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香甜蜜芬芳"),
    ]
}))

anchors.append(make("有沒有不太甜的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "不太甜"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "純茶無糖也好喝，花香清雅"),
        rec("茶花紅烏龍", "pure_tea", "焙火烏龍帶微甜，可選無糖"),
    ]
}))

anchors.append(make("夏天適合喝什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "冰", "scenario": "夏天"},
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "酸甜清爽消暑聖品"),
        rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香冰飲清涼"),
    ]
}))

anchors.append(make("想配甜點", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "配甜點"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "焙火鐵觀音配甜點解甜膩"),
        rec("茶花紅烏龍", "cloud_velvet", "紅烏龍奶蓋配甜點鹹甜平衡"),
    ]
}))

anchors.append(make("純茶有什麼推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "純茶"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶花香清雅"),
        rec("桂花輕烏龍", "pure_tea", "桂花蜜韻輕柔"),
    ]
}))

anchors.append(make("我想喝茶味重一點的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "茶味重"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音茶味最濃郁"),
        rec("茶花紅烏龍", "rich_milk_tea", "紅烏龍奶茶焙火茶香醇厚"),
    ]
}))

# --- 混合意圖 anchor ---
anchors.append(make("三窨十五茉鮮奶半糖少冰；再推薦一個配甜點的", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖")],
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "焙火鐵觀音配甜點茶香解甜膩"),
    ]
}))

anchors.append(make("推薦一下；好那桂花輕烏龍鮮奶半糖少冰", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("三窨十五茉鮮奶半糖；推薦果茶；那加一杯葡柚十五茉", {
    "intent": "order",
    "orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "半糖"),
        order("葡柚十五茉", "fruit_tea", None, "正常冰", "正常糖"),
    ],
    "recommendations": []
}))


# ============================================================
# 寫出
# ============================================================
all_examples = addon_examples + oral_examples + recommend_examples + category_taste_examples + anchors

outpath = os.path.join(BASE_DIR, "round24.jsonl")
with open(outpath, "w") as f:
    for ex in all_examples:
        f.write(ex + "\n")

print(f"=== Round 24 訓練資料 ===")
print(f"P0  加料識別: {len(addon_examples)} 筆")
print(f"P1a 口語→點餐: {len(oral_examples)} 筆")
print(f"P1b 推薦邊界: {len(recommend_examples)} 筆")
print(f"P1c 口味×分類: {len(category_taste_examples)} 筆")
print(f"P2  Anchor: {len(anchors)} 筆")
print(f"總計: {len(all_examples)} 筆 → {outpath}")
