#!/usr/bin/env python3
"""
Round 23：推薦 + 混合意圖訓練資料

產生三類資料：
1. 純推薦 ~90 筆
2. 混合意圖（點餐+推薦） ~30 筆
3. Anchor 點餐樣本 ~30 筆（防止回歸）
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 與 rebuild_train_v2.py 相同的 system prompt
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


examples = []

# ============================================================
# 1. 純推薦（intent=recommend）
# ============================================================

# --- 直接推薦 ~15 筆 ---
examples.append(make("有什麼推薦的嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，蜜韻奶香溫潤，廣受好評"),
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶，花香清雅適合入門"),
    ]
}))

examples.append(make("推薦一下", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音鮮奶，焙火香濃郁，人氣首選"),
        rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香配紅烏龍，甜蜜芬芳"),
    ]
}))

examples.append(make("你們招牌是什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "桂花烏龍覆綿密奶蓋，鹹甜交融，招牌必喝"),
        rec("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音鮮奶，焙火香濃郁"),
    ]
}))

examples.append(make("有什麼好喝的", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜，人人都愛"),
        rec("桂花輕烏龍", "pure_tea", "桂花與輕烏龍，花果蜜韻輕柔"),
    ]
}))

examples.append(make("最多人點的是哪個", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音鮮奶，茶味濃郁最受歡迎"),
        rec("三窨十五茉", "fresh_milk_tea", "茉莉鮮奶，清香滑順也很熱門"),
    ]
}))

examples.append(make("幫我推薦一杯", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，蜜韻奶香溫潤"),
    ]
}))

examples.append(make("哪個比較好喝", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "焙火香濃郁的鐵觀音鮮奶"),
        rec("金杯蜜香紅", "fresh_milk_tea", "天然蜜甜的蜜香紅茶鮮奶"),
    ]
}))

examples.append(make("第一次來，推薦什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "第一次"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜好入口，新客首選"),
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶，花香清雅適合認識我們"),
    ]
}))

examples.append(make("你們人氣飲品是什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "焙火鐵觀音鮮奶，最受歡迎"),
        rec("桂花輕烏龍", "cloud_velvet", "桂花烏龍奶蓋，鹹甜交融招牌之選"),
    ]
}))

examples.append(make("有什麼特別的嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("朱槿普洱紅", "fresh_milk_tea", "洛神花搭普洱紅茶鮮奶，微酸風味獨特"),
        rec("葡柚十五茉", "fruit_tea", "葡萄柚酸香配茉莉，清新微苦大人味"),
    ]
}))

examples.append(make("今天喝什麼好", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，蜜韻奶香溫潤"),
        rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽"),
    ]
}))

examples.append(make("不知道要喝什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，甜度適中好入口"),
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶，清新百搭"),
    ]
}))

examples.append(make("幫我選一杯吧", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音鮮奶，茶味濃厚滿足"),
    ]
}))

examples.append(make("隨便推薦一個", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，花香奶香兼具"),
    ]
}))

examples.append(make("你覺得哪個好", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("茶花紅烏龍", "cloud_velvet", "紅烏龍奶蓋，茶香奶鹹完美平衡"),
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火香濃郁"),
    ]
}))

# --- 口味偏好 ~20 筆 ---
examples.append(make("有沒有不太甜的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "不太甜"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "純茶無糖也好喝，花香清雅不甜膩"),
        rec("茶花紅烏龍", "pure_tea", "焙火烏龍本身帶微甜，可選無糖"),
    ]
}))

examples.append(make("我想喝茶味重一點的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "茶味重"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音，茶味最濃郁"),
        rec("茶花紅烏龍", "rich_milk_tea", "紅烏龍奶茶，焙火茶香醇厚"),
    ]
}))

examples.append(make("有花香的推薦嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "花香"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "三次窨花茉莉，花香最突出"),
        rec("桂花輕烏龍", "pure_tea", "桂花蜜韻輕柔，花香優雅"),
    ]
}))

examples.append(make("想喝甜一點的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "甜"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜最對味"),
        rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香，甜蜜芬芳"),
    ]
}))

examples.append(make("清爽一點的有什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "清爽"},
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜清爽消暑"),
        rec("米香玉露菁", "pure_tea", "日式玉露菁，鮮爽細膩"),
    ]
}))

examples.append(make("有沒有比較濃郁的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "濃郁"},
    "recommendations": [
        rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音奶茶，重焙火香氣濃郁"),
        rec("茶花紅烏龍", "cloud_velvet", "紅烏龍奶蓋，茶香奶鹹飽滿"),
    ]
}))

examples.append(make("有酸的飲料嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "酸"},
    "recommendations": [
        rec("朱槿普洱紅", "pure_tea", "洛神花搭普洱紅茶，微酸回甘"),
        rec("青檸桂蜜", "fruit_tea", "青檸酸甜清爽"),
        rec("葡柚十五茉", "fruit_tea", "葡萄柚酸香配茉莉"),
    ]
}))

examples.append(make("想喝奶味重的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "奶味重"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火香與鮮奶完美融合"),
        rec("米香玉露菁", "fresh_milk_tea", "玉露菁鮮奶，穀物奶香療癒"),
    ]
}))

examples.append(make("有沒有帶果香的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "果香"},
    "recommendations": [
        rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香與紅烏龍交織"),
        rec("葡柚十五茉", "fruit_tea", "葡萄柚酸香配茉莉花茶"),
        rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，清爽果香"),
    ]
}))

examples.append(make("不要太苦的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "不苦", "avoid": "苦"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶天然甜，完全不苦"),
        rec("桂花輕烏龍", "fresh_milk_tea", "輕發酵烏龍，蜜韻柔和無苦澀"),
    ]
}))

examples.append(make("想喝溫潤一點的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "溫潤"},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，蜜韻奶香溫潤"),
        rec("米香玉露菁", "fresh_milk_tea", "玉露菁鮮奶，穀物奶香溫暖療癒"),
    ]
}))

examples.append(make("有什麼特殊風味的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "特殊"},
    "recommendations": [
        rec("朱槿普洱紅", "fresh_milk_tea", "洛神花搭普洱紅茶鮮奶，微酸獨特"),
        rec("葡柚十五茉", "fruit_tea", "葡萄柚配茉莉，大人味果茶"),
    ]
}))

examples.append(make("我怕太膩", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "不膩", "avoid": "膩"},
    "recommendations": [
        rec("朱槿普洱紅", "pure_tea", "微酸回甘解膩，飯後適合"),
        rec("三窨十五茉", "pure_tea", "茉莉花茶清爽不膩"),
    ]
}))

examples.append(make("喝起來順口的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "順口"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，自然甜滑順口"),
        rec("茶花烏龍", "fresh_milk_tea", "烏龍鮮奶，茶奶平衡圓潤"),
    ]
}))

examples.append(make("我喜歡焙火味的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "焙火"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音鮮奶，焙火香最濃"),
        rec("茶花紅烏龍", "pure_tea", "重焙火紅烏龍，熟果甜韻"),
    ]
}))

examples.append(make("有沒有帶蜜味的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "蜜味"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜"),
        rec("桂花輕烏龍", "pure_tea", "桂花蜜韻輕柔"),
    ]
}))

examples.append(make("不要奶的", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "茉莉花茶，花香清雅無奶"),
        rec("朱槿普洱紅", "pure_tea", "普洱紅茶，微酸回甘無奶"),
        rec("青檸桂蜜", "fruit_tea", "青檸果茶，酸甜清爽無奶"),
    ]
}))

examples.append(make("想喝日式風格的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "日式"},
    "recommendations": [
        rec("米香玉露菁", "pure_tea", "日式玉露菁帶米穀香，鮮爽細膩"),
    ]
}))

examples.append(make("比較養生的有什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "養生"},
    "recommendations": [
        rec("朱槿普洱紅", "pure_tea", "洛神花配普洱，開胃助消化"),
        rec("米香玉露菁", "pure_tea", "玉露菁帶米穀香，溫和養胃"),
    ]
}))

examples.append(make("層次豐富一點的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "層次豐富"},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "桂花烏龍覆綿密奶蓋，鹹甜花香層次交疊"),
        rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音奶茶，焙火與奶香層次分明"),
    ]
}))

# --- 溫度/季節 ~10 筆 ---
examples.append(make("想喝熱的", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "熱"},
    "recommendations": [
        rec("茶花紅烏龍", "pure_tea", "焙火紅烏龍熱飲，花香與熟果甜韻更明顯"),
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶熱飲，焙火奶香暖胃"),
    ]
}))

examples.append(make("夏天適合喝什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "冰", "scenario": "夏天"},
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜消暑最適合夏天"),
        rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香配冰飲，清涼甜蜜"),
    ]
}))

examples.append(make("天氣好冷想喝暖的", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "熱", "scenario": "冬天"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶熱飲，焙火暖胃最適合冷天"),
        rec("米香玉露菁", "fresh_milk_tea", "玉露菁鮮奶熱飲，穀物奶香溫暖療癒"),
    ]
}))

examples.append(make("想喝冰的", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "冰"},
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "酸甜清爽，冰飲最消暑"),
        rec("三窨十五茉", "pure_tea", "茉莉花茶冰飲，清香甘甜"),
    ]
}))

examples.append(make("有適合冬天的嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "熱", "scenario": "冬天"},
    "recommendations": [
        rec("茶花紅烏龍", "pure_tea", "重焙火紅烏龍熱飲，暖身暖心"),
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶熱飲，溫潤舒適"),
    ]
}))

examples.append(make("有沒有溫的可以喝", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "溫"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，去冰喝溫溫甜甜的"),
        rec("桂花輕烏龍", "pure_tea", "桂花烏龍去冰，花蜜溫潤"),
    ]
}))

examples.append(make("消暑的飲料", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "冰", "scenario": "消暑"},
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜，酸甜消暑聖品"),
        rec("朱槿普洱紅", "pure_tea", "洛神普洱冰飲，微酸解熱"),
    ]
}))

examples.append(make("秋天喝什麼好", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "秋天"},
    "recommendations": [
        rec("茶花紅烏龍", "pure_tea", "焙火烏龍帶熟果韻，秋天最對味"),
        rec("桂花輕烏龍", "pure_tea", "桂花清香，秋意盎然"),
    ]
}))

examples.append(make("下雨天想喝熱飲", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "熱", "scenario": "下雨天"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶熱飲，焙火暖胃"),
        rec("米香玉露菁", "fresh_milk_tea", "玉露菁鮮奶熱飲，米穀香溫暖"),
    ]
}))

examples.append(make("適合涼爽天氣的", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "熱", "scenario": "涼爽"},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，蜜韻溫潤適合涼天"),
        rec("茶花紅烏龍", "rich_milk_tea", "紅烏龍奶茶，焙火醇厚暖身"),
    ]
}))

# --- 場景 ~15 筆 ---
examples.append(make("吃飯後適合喝什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "飯後"},
    "recommendations": [
        rec("朱槿普洱紅", "pure_tea", "普洱紅茶微酸回甘，飯後解膩開胃"),
        rec("三窨十五茉", "pure_tea", "茉莉花茶清爽，飯後去油解膩"),
    ]
}))

examples.append(make("想配甜點", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "配甜點"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "焙火鐵觀音配甜點，茶香解甜膩"),
        rec("茶花紅烏龍", "cloud_velvet", "紅烏龍奶蓋配甜點，鹹甜平衡"),
    ]
}))

examples.append(make("下午茶適合什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "下午茶"},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，午後花香奶韻最悠閒"),
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，午後甜蜜時光"),
    ]
}))

examples.append(make("上班提神的", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "提神"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音鮮奶，茶韻強烈提神醒腦"),
        rec("茶花紅烏龍", "pure_tea", "焙火紅烏龍，濃茶提振精神"),
    ]
}))

examples.append(make("約會帶女朋友來，推薦什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "約會"},
    "recommendations": [
        rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香甜蜜，適合約會氣氛"),
        rec("桂花輕烏龍", "cloud_velvet", "桂花奶蓋精緻浪漫，很適合約會"),
    ]
}))

examples.append(make("帶給長輩喝的", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "長輩"},
    "recommendations": [
        rec("琥珀鐵觀音", "pure_tea", "鐵觀音純茶，傳統茶韻長輩最熟悉"),
        rec("朱槿普洱紅", "pure_tea", "普洱紅茶溫和，養胃適合長輩"),
    ]
}))

examples.append(make("運動後想喝", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "運動後"},
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "酸甜清爽補充活力，運動後最解渴"),
        rec("三窨十五茉", "pure_tea", "茉莉花茶冰飲，清爽解渴"),
    ]
}))

examples.append(make("讀書的時候配什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "讀書"},
    "recommendations": [
        rec("米香玉露菁", "pure_tea", "玉露菁米穀香，安靜沉穩適合讀書"),
        rec("桂花輕烏龍", "pure_tea", "桂花清香，讀書配茶最舒心"),
    ]
}))

examples.append(make("外帶給同事的，推薦幾杯", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "外帶給同事"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，接受度高適合分享"),
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，甜度適中人人愛"),
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶，不挑人"),
    ]
}))

examples.append(make("小孩可以喝什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "小孩"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜小孩也愛"),
        rec("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香甜蜜，可選少糖"),
    ]
}))

examples.append(make("減肥中有推薦嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "減肥", "avoid": "甜"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "純茶無糖零負擔，花香清雅"),
        rec("朱槿普洱紅", "pure_tea", "普洱無糖助消化，微酸解膩"),
    ]
}))

examples.append(make("睡前可以喝什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "睡前"},
    "recommendations": [
        rec("桂花輕烏龍", "pure_tea", "輕發酵烏龍茶因較低，桂花香助放鬆"),
        rec("米香玉露菁", "pure_tea", "米穀香溫和，適合睡前放鬆"),
    ]
}))

examples.append(make("待客用的", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "待客"},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "桂花奶蓋精緻大方，待客有面子"),
        rec("茶花紅烏龍", "cloud_velvet", "紅烏龍奶蓋高級感十足"),
    ]
}))

examples.append(make("想喝放鬆一下", {
    "intent": "recommend", "orders": [],
    "preferences": {"scenario": "放鬆"},
    "recommendations": [
        rec("桂花輕烏龍", "pure_tea", "桂花清香，放鬆身心"),
        rec("米香玉露菁", "fresh_milk_tea", "穀物奶香，溫暖療癒"),
    ]
}))

examples.append(make("我不喜歡花味的", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "花香"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音焙火香為主，沒有花香"),
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶，蜜甜為主"),
    ]
}))

# --- 排除偏好 ~10 筆 ---
examples.append(make("不要奶茶", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "奶茶"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "純茶花香清雅，無奶無負擔"),
        rec("青檸桂蜜", "fruit_tea", "果茶酸甜清爽，無奶類"),
    ]
}))

examples.append(make("不喜歡太苦的茶", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "苦"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶天然甜不苦"),
        rec("桂花輕烏龍", "fresh_milk_tea", "輕發酵烏龍蜜韻柔和"),
    ]
}))

examples.append(make("不要太甜也不要太苦", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "太甜太苦"},
    "recommendations": [
        rec("茶花烏龍", "fresh_milk_tea", "烏龍鮮奶茶奶平衡，不甜不苦"),
        rec("桂花輕烏龍", "pure_tea", "花果蜜韻自然，口感均衡"),
    ]
}))

examples.append(make("不要有咖啡因的", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "咖啡因"},
    "recommendations": [],
    "note": "本店飲品均為茶類，含有咖啡因。建議選擇輕發酵的桂花輕烏龍或金杯蜜香紅，咖啡因含量相對較低"
}))

examples.append(make("我不喝普洱", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "普洱"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火濃郁"),
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，蜜韻溫潤"),
    ]
}))

examples.append(make("不要冰的推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"temperature": "熱", "avoid": "冰"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶熱飲，焙火暖胃"),
        rec("茶花紅烏龍", "pure_tea", "焙火紅烏龍熱飲，花香馥郁"),
    ]
}))

examples.append(make("除了果茶還有什麼推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"avoid": "果茶"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火濃郁人氣首選"),
        rec("桂花輕烏龍", "cloud_velvet", "桂花奶蓋，鹹甜交融招牌"),
    ]
}))

# --- 分類查詢 ~10 筆 ---
examples.append(make("純茶有什麼推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "純茶"},
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶，花香清雅"),
        rec("桂花輕烏龍", "pure_tea", "桂花蜜韻輕柔"),
        rec("茶花紅烏龍", "pure_tea", "焙火紅烏龍，茶味厚實"),
    ]
}))

examples.append(make("鮮奶茶推薦哪個", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "鮮奶茶"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火香最濃郁"),
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，蜜韻奶香溫潤"),
    ]
}))

examples.append(make("果茶推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "果茶"},
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "酸甜清爽消暑"),
        rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香甜蜜芬芳"),
        rec("葡柚十五茉", "fruit_tea", "葡萄柚微苦大人味"),
    ]
}))

examples.append(make("奶蓋推薦哪個", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "奶蓋"},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "桂花奶蓋，鹹甜交融口感豐富"),
        rec("茶花紅烏龍", "cloud_velvet", "紅烏龍奶蓋，茶香奶鹹平衡"),
    ]
}))

examples.append(make("奶茶有什麼好的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "奶茶"},
    "recommendations": [
        rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音奶茶，焙火濃郁"),
        rec("三窨十五茉", "rich_milk_tea", "茉莉奶茶，花香層次豐富"),
    ]
}))

examples.append(make("紅茶類推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "紅茶"},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜"),
        rec("朱槿普洱紅", "pure_tea", "普洱紅茶，微酸回甘"),
    ]
}))

examples.append(make("烏龍茶推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "烏龍"},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火烏龍最濃郁"),
        rec("桂花輕烏龍", "pure_tea", "桂花與輕發酵烏龍，花果蜜韻"),
        rec("茶花紅烏龍", "pure_tea", "重焙火紅烏龍，茶味厚實"),
    ]
}))

examples.append(make("平價的推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "平價"},
    "recommendations": [
        rec("朱槿普洱紅", "pure_tea", "40元純茶，微酸回甘性價比高"),
        rec("金杯蜜香紅", "fresh_milk_tea", "60元起鮮奶茶，蜜甜好喝"),
    ]
}))

examples.append(make("最貴的是什麼", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "cloud_velvet", "95元，桂花奶蓋鹹甜交融，最頂級享受"),
        rec("茶花紅烏龍", "cloud_velvet", "95元，紅烏龍奶蓋茶香奶鹹平衡"),
    ]
}))

examples.append(make("便宜一點的推薦", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "便宜"},
    "recommendations": [
        rec("朱槿普洱紅", "pure_tea", "40元，微酸回甘最划算"),
        rec("金杯蜜香紅", "fresh_milk_tea", "M杯60元，蜜甜好喝"),
    ]
}))

# --- 模糊/對話 ~10 筆 ---
examples.append(make("不確定要喝什麼欸", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，甜度適中最好入手"),
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，花香奶韻都有"),
    ]
}))

examples.append(make("我選擇障礙", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，茶味濃郁不踩雷"),
    ]
}))

examples.append(make("都可以啦你推薦就好", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶，溫潤百搭最推薦"),
    ]
}))

examples.append(make("你們這邊有什麼可以喝", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，人氣第一"),
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶，招牌之一"),
        rec("青檸桂蜜", "fruit_tea", "酸甜果茶，清爽消暑"),
    ]
}))

examples.append(make("菜單好多看不懂", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，甜甜好喝最容易上手"),
        rec("三窨十五茉", "pure_tea", "茉莉花茶，名字特別但口味經典好喝"),
    ]
}))

examples.append(make("我朋友說你們很好喝", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，回購率最高"),
        rec("桂花輕烏龍", "cloud_velvet", "桂花奶蓋，拍照打卡也很美"),
    ]
}))

examples.append(make("有沒有什麼跟別家不一樣的", {
    "intent": "recommend", "orders": [],
    "preferences": {"taste": "獨特"},
    "recommendations": [
        rec("朱槿普洱紅", "fresh_milk_tea", "洛神花配普洱鮮奶，別家喝不到"),
        rec("米香玉露菁", "pure_tea", "日式玉露帶米穀香，獨特風味"),
    ]
}))

examples.append(make("最近有新品嗎", {
    "intent": "recommend", "orders": [],
    "preferences": {},
    "recommendations": [
        rec("葡柚十五茉", "fruit_tea", "葡萄柚配茉莉花茶，清新大人味"),
        rec("茶花紅烏龍", "cloud_velvet", "紅烏龍奶蓋，焙火與奶鹹的完美結合"),
    ]
}))

examples.append(make("給我看看菜單", {
    "intent": "other", "orders": [], "recommendations": [],
    "note": "請參考菜單"
}))

examples.append(make("你們飲料都是現做的嗎", {
    "intent": "other", "orders": [], "recommendations": [],
    "note": "顧客詢問製作方式"
}))

# ============================================================
# 2. 混合意圖（點餐+推薦） ~30 筆
# ============================================================

# --- 先點再問推薦 ~10 筆 ---
examples.append(make("三窨十五茉鮮奶半糖少冰；再推薦一個配甜點的", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖")],
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "焙火鐵觀音配甜點，茶香解甜膩"),
    ]
}))

examples.append(make("桂花輕烏龍純茶去冰無糖；還有什麼好喝的", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "pure_tea", None, "去冰", "無糖")],
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，焙火濃郁推薦試試"),
        rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香清爽也很好喝"),
    ]
}))

examples.append(make("先來一杯琥珀鐵觀音鮮奶；有沒有果茶推薦", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": [
        rec("青檸桂蜜", "fruit_tea", "酸甜清爽最消暑"),
        rec("蜜桃紅烏龍", "fruit_tea", "蜜桃果香甜蜜"),
    ]
}))

examples.append(make("金杯蜜香紅鮮奶半糖；推薦一個給我朋友", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "半糖")],
    "recommendations": [
        rec("桂花輕烏龍", "fresh_milk_tea", "桂花鮮奶溫潤百搭，很多人喜歡"),
    ]
}))

examples.append(make("青檸桂蜜微糖；還有什麼不甜的推薦", {
    "intent": "order",
    "orders": [order("青檸桂蜜", "fruit_tea", None, "正常冰", "微糖")],
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "茉莉花茶無糖也好喝"),
        rec("茶花紅烏龍", "pure_tea", "焙火紅烏龍，可選無糖"),
    ]
}))

examples.append(make("茶花紅烏龍奶蓋一杯；再推薦一個奶茶", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "cloud_velvet", None, "正常冰", "正常糖")],
    "recommendations": [
        rec("琥珀鐵觀音", "rich_milk_tea", "鐵觀音奶茶焙火香濃郁"),
    ]
}))

examples.append(make("米香玉露菁純茶去冰；推薦一個熱的", {
    "intent": "order",
    "orders": [order("米香玉露菁", "pure_tea", None, "去冰", "正常糖")],
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶熱飲，焙火暖胃"),
    ]
}))

examples.append(make("朱槿普洱紅鮮奶半糖少冰；有什麼適合小孩的", {
    "intent": "order",
    "orders": [order("朱槿普洱紅", "fresh_milk_tea", "M", "少冰", "半糖")],
    "recommendations": [
        rec("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜小孩也愛"),
    ]
}))

examples.append(make("琥珀鐵觀音奶茶L半糖去冰；純茶推薦什麼", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "rich_milk_tea", "L", "去冰", "半糖")],
    "recommendations": [
        rec("三窨十五茉", "pure_tea", "經典茉莉花茶，花香清雅"),
        rec("桂花輕烏龍", "pure_tea", "桂花蜜韻輕柔"),
    ]
}))

examples.append(make("葡柚十五茉半糖；推薦一個茶味重的", {
    "intent": "order",
    "orders": [order("葡柚十五茉", "fruit_tea", None, "正常冰", "半糖")],
    "recommendations": [
        rec("琥珀鐵觀音", "fresh_milk_tea", "鐵觀音鮮奶，茶味最濃郁"),
    ]
}))

# --- 先推薦再點 ~10 筆（推薦→做出決定→清空 recommendations）---
examples.append(make("推薦一下；好那桂花輕烏龍鮮奶半糖少冰", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖")],
    "recommendations": []
}))

examples.append(make("有什麼好喝的；那來一杯琥珀鐵觀音鮮奶", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": []
}))

examples.append(make("不知道喝什麼；好那三窨十五茉純茶去冰無糖", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "去冰", "無糖")],
    "recommendations": []
}))

examples.append(make("推薦果茶；那蜜桃紅烏龍半糖", {
    "intent": "order",
    "orders": [order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "半糖")],
    "recommendations": []
}))

examples.append(make("招牌是什麼；就來招牌的桂花奶蓋", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "cloud_velvet", None, "正常冰", "正常糖")],
    "recommendations": []
}))

examples.append(make("茶味重的推薦；好那琥珀鐵觀音奶茶M半糖少冰", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "半糖")],
    "recommendations": []
}))

examples.append(make("有什麼不甜的；金杯蜜香紅鮮奶微糖去冰", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "M", "去冰", "微糖")],
    "recommendations": []
}))

examples.append(make("適合夏天的推薦；那青檸桂蜜少糖", {
    "intent": "order",
    "orders": [order("青檸桂蜜", "fruit_tea", None, "正常冰", "少糖")],
    "recommendations": []
}))

examples.append(make("幫我選一杯；好那就米香玉露菁純茶", {
    "intent": "order",
    "orders": [order("米香玉露菁", "pure_tea", None, "正常冰", "正常糖")],
    "recommendations": []
}))

examples.append(make("人氣推薦；那來兩杯琥珀鐵觀音鮮奶半糖", {
    "intent": "order",
    "orders": [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "正常冰", "sugar": "半糖", "addon": [], "qty": 2, "note": ""}],
    "recommendations": []
}))

# --- 點餐+推薦+點餐 ~10 筆（最後做了決定→清空 recommendations）---
examples.append(make("三窨十五茉鮮奶半糖；推薦果茶；那加一杯葡柚十五茉", {
    "intent": "order",
    "orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "正常冰", "半糖"),
        order("葡柚十五茉", "fruit_tea", None, "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

examples.append(make("琥珀鐵觀音奶茶半糖；有什麼清爽的；那加青檸桂蜜微糖", {
    "intent": "order",
    "orders": [
        order("琥珀鐵觀音", "rich_milk_tea", "M", "正常冰", "半糖"),
        order("青檸桂蜜", "fruit_tea", None, "正常冰", "微糖"),
    ],
    "recommendations": []
}))

examples.append(make("桂花輕烏龍純茶；推薦鮮奶茶；那加桂花鮮奶半糖", {
    "intent": "order",
    "orders": [
        order("桂花輕烏龍", "pure_tea", None, "正常冰", "正常糖"),
        order("桂花輕烏龍", "fresh_milk_tea", "M", "正常冰", "半糖"),
    ],
    "recommendations": []
}))

examples.append(make("金杯蜜香紅鮮奶；推薦茶味重的；好那來琥珀鐵觀音鮮奶", {
    "intent": "order",
    "orders": [
        order("金杯蜜香紅", "fresh_milk_tea", "M", "正常冰", "正常糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

examples.append(make("蜜桃紅烏龍半糖；有什麼配甜點的；那加茶花紅烏龍奶蓋", {
    "intent": "order",
    "orders": [
        order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "半糖"),
        order("茶花紅烏龍", "cloud_velvet", None, "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

examples.append(make("朱槿普洱紅純茶；推薦一下；好那加三窨十五茉純茶", {
    "intent": "order",
    "orders": [
        order("朱槿普洱紅", "pure_tea", None, "正常冰", "正常糖"),
        order("三窨十五茉", "pure_tea", None, "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

examples.append(make("茶花烏龍鮮奶少冰；有沒有酸的；那青檸桂蜜少糖", {
    "intent": "order",
    "orders": [
        order("茶花烏龍", "fresh_milk_tea", "M", "少冰", "正常糖"),
        order("青檸桂蜜", "fruit_tea", None, "正常冰", "少糖"),
    ],
    "recommendations": []
}))

examples.append(make("米香玉露菁鮮奶；推薦奶蓋；好那桂花奶蓋", {
    "intent": "order",
    "orders": [
        order("米香玉露菁", "fresh_milk_tea", "M", "正常冰", "正常糖"),
        order("桂花輕烏龍", "cloud_velvet", None, "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

examples.append(make("琥珀鐵觀音鮮奶L去冰半糖；推薦純茶；那加桂花純茶去冰無糖", {
    "intent": "order",
    "orders": [
        order("琥珀鐵觀音", "fresh_milk_tea", "L", "去冰", "半糖"),
        order("桂花輕烏龍", "pure_tea", None, "去冰", "無糖"),
    ],
    "recommendations": []
}))

examples.append(make("葡柚十五茉；有什麼甜的推薦；那蜜桃紅烏龍", {
    "intent": "order",
    "orders": [
        order("葡柚十五茉", "fruit_tea", None, "正常冰", "正常糖"),
        order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "正常糖"),
    ],
    "recommendations": []
}))

# ============================================================
# 3. Anchor 點餐樣本（防止回歸）~30 筆
# ============================================================
anchors = []

anchors.append(make("一杯三窨十五茉鮮奶半糖少冰", {
    "intent": "order",
    "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("桂花輕烏龍純茶去冰無糖", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "pure_tea", None, "去冰", "無糖")],
    "recommendations": []
}))

anchors.append(make("琥珀鐵觀音鮮奶L半糖去冰", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "L", "去冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("茶花紅烏龍奶蓋", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "cloud_velvet", None, "正常冰", "正常糖")],
    "recommendations": []
}))

anchors.append(make("兩杯金杯蜜香紅鮮奶半糖少冰", {
    "intent": "order",
    "orders": [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 2, "note": ""}],
    "recommendations": []
}))

anchors.append(make("蜜桃紅烏龍微糖", {
    "intent": "order",
    "orders": [order("蜜桃紅烏龍", "fruit_tea", None, "正常冰", "微糖")],
    "recommendations": []
}))

anchors.append(make("青檸桂蜜少糖", {
    "intent": "order",
    "orders": [order("青檸桂蜜", "fruit_tea", None, "正常冰", "少糖")],
    "recommendations": []
}))

anchors.append(make("葡柚十五茉半糖", {
    "intent": "order",
    "orders": [order("葡柚十五茉", "fruit_tea", None, "正常冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("朱槿普洱紅純茶微冰無糖", {
    "intent": "order",
    "orders": [order("朱槿普洱紅", "pure_tea", None, "微冰", "無糖")],
    "recommendations": []
}))

anchors.append(make("米香玉露菁鮮奶M正常糖正常冰", {
    "intent": "order",
    "orders": [order("米香玉露菁", "fresh_milk_tea", "M", "正常冰", "正常糖")],
    "recommendations": []
}))

anchors.append(make("茶花烏龍鮮奶少冰半糖加紅烏龍茶凍", {
    "intent": "order",
    "orders": [order("茶花烏龍", "fresh_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

anchors.append(make("桂花輕烏龍奶茶L微糖去冰加燕麥粒", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "rich_milk_tea", "L", "去冰", "微糖", ["燕麥粒"])],
    "recommendations": []
}))

anchors.append(make("琥珀鐵觀音奶茶M半糖少冰", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "rich_milk_tea", "M", "少冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("三窨十五茉奶茶半糖去冰", {
    "intent": "order",
    "orders": [order("三窨十五茉", "rich_milk_tea", "M", "去冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("茶花紅烏龍純茶無糖去冰", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "pure_tea", None, "去冰", "無糖")],
    "recommendations": []
}))

anchors.append(make("桂花輕烏龍奶蓋", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "cloud_velvet", None, "正常冰", "正常糖")],
    "recommendations": []
}))

anchors.append(make("金杯蜜香紅奶茶M少糖微冰", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "rich_milk_tea", "M", "微冰", "少糖")],
    "recommendations": []
}))

anchors.append(make("熱的琥珀鐵觀音鮮奶半糖", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "熱飲", "半糖")],
    "recommendations": []
}))

anchors.append(make("朱槿普洱紅鮮奶少冰微糖", {
    "intent": "order",
    "orders": [order("朱槿普洱紅", "fresh_milk_tea", "M", "少冰", "微糖")],
    "recommendations": []
}))

anchors.append(make("一杯茉莉鮮奶半糖少冰；一杯鐵觀音鮮奶半糖去冰", {
    "intent": "order",
    "orders": [
        order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖"),
        order("琥珀鐵觀音", "fresh_milk_tea", "M", "去冰", "半糖"),
    ],
    "recommendations": []
}))

anchors.append(make("米香玉露菁奶茶L半糖", {
    "intent": "order",
    "orders": [order("米香玉露菁", "rich_milk_tea", "L", "正常冰", "半糖")],
    "recommendations": []
}))

anchors.append(make("三杯桂花輕烏龍純茶去冰無糖", {
    "intent": "order",
    "orders": [{"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 3, "note": ""}],
    "recommendations": []
}))

anchors.append(make("琥珀鐵觀音鮮奶M半糖少冰加茶凍", {
    "intent": "order",
    "orders": [order("琥珀鐵觀音", "fresh_milk_tea", "M", "少冰", "半糖", ["紅烏龍茶凍"])],
    "recommendations": []
}))

anchors.append(make("茶花紅烏龍奶茶M少糖去冰", {
    "intent": "order",
    "orders": [order("茶花紅烏龍", "rich_milk_tea", "M", "去冰", "少糖")],
    "recommendations": []
}))

anchors.append(make("金杯蜜香紅鮮奶L正常糖正常冰", {
    "intent": "order",
    "orders": [order("金杯蜜香紅", "fresh_milk_tea", "L", "正常冰", "正常糖")],
    "recommendations": []
}))

anchors.append(make("桂花輕烏龍鮮奶M無糖去冰加燕麥粒", {
    "intent": "order",
    "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "去冰", "無糖", ["燕麥粒"])],
    "recommendations": []
}))

anchors.append(make("熱的三窨十五茉純茶無糖", {
    "intent": "order",
    "orders": [order("三窨十五茉", "pure_tea", None, "熱飲", "無糖")],
    "recommendations": []
}))

anchors.append(make("朱槿普洱紅奶茶M半糖少冰", {
    "intent": "order",
    "orders": [order("朱槿普洱紅", "rich_milk_tea", "M", "少冰", "半糖")],
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

anchors.append(make("茶花烏龍鮮奶L半糖微冰加紅烏龍茶凍跟燕麥粒", {
    "intent": "order",
    "orders": [order("茶花烏龍", "fresh_milk_tea", "L", "微冰", "半糖", ["紅烏龍茶凍", "燕麥粒"])],
    "recommendations": []
}))

# ============================================================
# 寫出
# ============================================================
all_examples = examples + anchors

outpath = os.path.join(BASE_DIR, "round23.jsonl")
with open(outpath, "w") as f:
    for ex in all_examples:
        f.write(ex + "\n")

print(f"=== Round 23 訓練資料 ===")
print(f"純推薦: {len([e for e in examples if '\"intent\": \"recommend\"' in e or '\"intent\":\"recommend\"' in e])} 筆")
print(f"混合意圖: {len([e for e in examples if '\"recommendations\": [' in e and '\"orders\": [{' in e])} 筆")
print(f"其他: {len([e for e in examples if '\"intent\": \"other\"' in e or '\"intent\":\"other\"' in e])} 筆")
print(f"Anchor 點餐: {len(anchors)} 筆")
print(f"總計: {len(all_examples)} 筆 → {outpath}")
