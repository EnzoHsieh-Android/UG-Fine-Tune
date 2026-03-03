#!/usr/bin/env python3
"""Generate Round 26 recommend samples for better intent generalization.

Focus: Sentence structure diversity, NOT menu item memorization.
Goal: ~80 train + ~20 valid = ~100 new recommend samples.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent

NEW_SYSTEM_PROMPT = """你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，判斷意圖並輸出 JSON。

意圖分類：
- order：顧客要點餐（含具體品項）
- recommend：顧客想要推薦（問推薦、不知道喝什麼、描述口味偏好、詢問菜單）

菜單分類與品項描述：
【研選純茶 pure_tea】單一尺寸
- 三窨十五茉：三次窨花茉莉綠茶，花香清雅帶甘甜
- 桂花輕烏龍：桂花與輕發酵烏龍，花果蜜韻輕柔
- 茶花紅烏龍：重焙火紅烏龍，天然花香與熟果甜韻
- 朱槿普洱紅：洛神花搭普洱紅茶，微酸回甘解膩
- 米香玉露菁：日式玉露菁帶米穀香，鮮爽細膩

【牧場直達 fresh_milk_tea】M/L
- 三窨十五茉(65/75)：茉莉鮮奶，清香滑順
- 桂花輕烏龍(65/75)：桂花烏龍鮮奶，蜜韻奶香溫潤
- 茶花烏龍(65/75)：烏龍鮮奶，茶奶平衡圓潤
- 琥珀鐵觀音(65/75)：重焙鐵觀音鮮奶，焙火香濃郁
- 金杯蜜香紅(60/70)：蜜香紅茶鮮奶，天然蜜甜
- 朱槿普洱紅(60/70)：洛神普洱鮮奶，微酸風味獨特
- 米香玉露菁(60/70)：玉露菁鮮奶，穀物奶香療癒

【UG奶茶 rich_milk_tea】M/L
- 三窨十五茉(65/75)、桂花輕烏龍(65/75)、茶花紅烏龍(65/75)
- 琥珀鐵觀音(65/75)、金杯蜜香紅(60/70)、朱槿普洱紅(60/70)、米香玉露菁(60/70)

【果香四溢 fruit_tea】僅冷飲，單一尺寸
- 青檸桂蜜(65)：青檸搭桂花蜜，酸甜清爽消暑
- 蜜桃紅烏龍(75)：水蜜桃果香與紅烏龍交織，甜蜜芬芳
- 葡柚十五茉(80)：葡萄柚酸香配茉莉，清新微苦大人味

【雲頂奶蓋 cloud_velvet】單一尺寸
- 桂花輕烏龍(95)：桂花烏龍覆綿密奶蓋，鹹甜交融
- 茶花紅烏龍(95)：紅烏龍焙火韻搭奶蓋，茶香奶鹹平衡

加料：紅烏龍茶凍(+15)、燕麥粒(+15)。
甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。
未指定甜度或冰量時設為 正常糖/正常冰。未指定尺寸的鮮奶茶/奶茶預設 M。
若品項不在菜單上，設 not_on_menu。

輸出格式（必須為合法 JSON）：
點餐：{"intent":"order","orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}],"recommendations":[]}
推薦：{"intent":"recommend","orders":[],"preferences":{"taste":"口味","temperature":"溫度","scenario":"場景","avoid":"排除"},"recommendations":[{"item":"品名","category":"分類","reason":"推薦理由"}]}
混合（點餐+推薦）：orders 和 recommendations 同時有值。若最後一段已做出點餐決定，清空 recommendations。"""


def rec(user_input, preferences, recommendations):
    """Build a recommend sample."""
    resp = {
        "intent": "recommend",
        "orders": [],
        "preferences": preferences,
        "recommendations": recommendations,
    }
    return {
        "messages": [
            {"role": "system", "content": NEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": json.dumps(resp, ensure_ascii=False)},
        ]
    }


# ── 新增 recommend 樣本 ─────────────────────────────────────────────────

NEW_SAMPLES = []

# ━━━ 1. 猶豫不決 / 選擇障礙 (12 筆) ━━━
NEW_SAMPLES += [
    rec("嗯...我想想", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花烏龍鮮奶，接受度高"}]),
    rec("讓我想想，你們有什麼好的", {}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "焙火鐵觀音鮮奶，茶味濃郁"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶，自然甜"}]),
    rec("不知道耶，有什麼建議嗎", {}, [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶，清香好入口"}]),
    rec("太多了吧，幫我選", {}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋鹹甜交融，獨特好喝"}]),
    rec("每個看起來都不錯欸", {}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶濃郁順口"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香清爽"}]),
    rec("好難選喔", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶，甜度適中"}]),
    rec("我第一次來不知道要點什麼", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花烏龍鮮奶，蜜韻溫潤"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶，入門首選"}]),
    rec("隨便來一個就好", {}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "焙火鐵觀音鮮奶，經典好喝"}]),
    rec("不知道自己想喝什麼", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "茉莉花茶清雅不膩"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻奶香"}]),
    rec("看了菜單還是不知道", {}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "青檸桂花蜜酸甜清爽"}]),
    rec("有選擇困難怎麼辦", {}, [
        {"item": "茶花紅烏龍", "category": "cloud_velvet", "reason": "紅烏龍奶蓋茶香鹹甜平衡"}]),
    rec("我不太會選飲料", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜度剛好"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花烏龍鮮奶溫潤好入口"}]),
]

# ━━━ 2. 比較詢問 (10 筆) ━━━
NEW_SAMPLES += [
    rec("鮮奶茶跟奶茶有什麼差別", {"taste": "比較鮮奶與奶茶"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "鮮奶系列用鮮奶，奶香更清爽"},
        {"item": "桂花輕烏龍", "category": "rich_milk_tea", "reason": "奶茶系列奶味更濃厚"}]),
    rec("奶蓋跟鮮奶茶差在哪", {"taste": "比較奶蓋與鮮奶"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "奶蓋是覆在茶上的綿密奶泡，鹹甜口感"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "鮮奶茶是茶與鮮奶混合，滑順"}]),
    rec("純茶跟鮮奶茶你比較推哪個", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶喝茶本味，花香清雅"},
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "加鮮奶更滑順，茉莉奶香"}]),
    rec("果茶跟純茶哪個好", {}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶酸甜清爽，適合喜歡水果味的"},
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "純茶清雅回甘，適合品茶"}]),
    rec("茉莉跟桂花哪個比較香", {"taste": "花香比較"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "茉莉花香清雅帶甘甜"},
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "桂花蜜韻輕柔溫潤"}]),
    rec("紅茶跟烏龍差很多嗎", {"taste": "比較紅茶與烏龍"}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶甜潤順口"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音焙火香濃郁有層次"}]),
    rec("哪一類比較適合不喝茶的人", {}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "果香蓋過茶味，不習慣喝茶也能接受"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜潤好入口"}]),
    rec("茶凍跟燕麥粒加哪個好", {}, [
        {"item": "紅烏龍茶凍", "category": "fresh_milk_tea", "reason": "茶凍口感QQ帶茶香"},
        {"item": "燕麥粒", "category": "fresh_milk_tea", "reason": "燕麥粒有穀物香增加咀嚼感"}]),
    rec("M跟L差多少", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "M杯65元，L杯75元，差10元容量更多"}]),
    rec("你們跟一般手搖飲差在哪", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "三次窨花工藝，花香層次與一般茶飲不同"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙火紅烏龍，天然花香與熟果甜韻"}]),
]

# ━━━ 3. 場景情境 - 新場景 (12 筆) ━━━
NEW_SAMPLES += [
    rec("趕時間有沒有快的", {"scenario": "趕時間"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶出杯快，清爽好喝"}]),
    rec("帶給小朋友的", {"scenario": "給小朋友"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香甜蜜，小朋友會喜歡"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "酸甜清爽適合小朋友"}]),
    rec("開會要用的幫我選", {"scenario": "開會"}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶提神又不失口感"},
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "茉莉花茶清雅不搶味"}]),
    rec("野餐帶什麼好", {"scenario": "野餐"}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "酸甜清爽適合戶外"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香冰飲消暑"}]),
    rec("想買給老婆喝", {"scenario": "送老婆"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋精緻好喝"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香甜蜜討喜"}]),
    rec("加班熬夜喝什麼", {"scenario": "加班熬夜", "temperature": "冰"}, [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "鐵觀音奶茶焙火提神"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙烏龍提神回甘"}]),
    rec("要請客人喝的", {"scenario": "請客"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "奶蓋精緻有特色，適合待客"},
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "茉莉花茶雅致不失禮"}]),
    rec("午餐吃太飽想來杯解膩的", {"scenario": "午餐後解膩"}, [
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "普洱紅茶微酸回甘解膩"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡萄柚酸香清新去油膩"}]),
    rec("一個人放空想喝點什麼", {"scenario": "放空"}, [
        {"item": "米香玉露菁", "category": "pure_tea", "reason": "日式玉露菁清幽療癒"},
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "桂花香輕柔放鬆"}]),
    rec("聚會要買給大家的", {"scenario": "聚會"}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜度適中人人愛"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶接受度高"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶清爽不挑人"}]),
    rec("考試前想提振精神", {"scenario": "考試提神"}, [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "焙火鐵觀音茶味濃提神"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙烏龍回甘提振精神"}]),
    rec("逛街逛累了想喝個東西", {"scenario": "逛街休息"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香冰飲消暑解渴"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶補充能量"}]),
]

# ━━━ 4. 溫度偏好 (8 筆) ━━━
NEW_SAMPLES += [
    rec("有常溫的嗎", {"temperature": "常溫"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶可做去冰，接近常溫"}]),
    rec("不要太冰也不要熱的", {"temperature": "微冰"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶微冰溫潤"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶去冰也好喝"}]),
    rec("今天好熱想喝冰的", {"temperature": "冰"}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "青檸桂花蜜冰飲酸甜消暑"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃冰茶清涼解渴"}]),
    rec("外面下雨好冷", {"temperature": "熱", "scenario": "下雨天"}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "熱鐵觀音鮮奶焙火暖身"},
        {"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "熱玉露菁鮮奶穀物香暖心"}]),
    rec("可以做溫的嗎", {"temperature": "溫"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶去冰口感溫潤"}]),
    rec("天冷推薦什麼暖暖的", {"temperature": "熱"}, [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "熱鐵觀音奶茶焙火暖胃"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "熱桂花鮮奶蜜韻暖手"}]),
    rec("大熱天的有什麼消暑的嗎", {"temperature": "冰", "scenario": "消暑"}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "酸甜清爽消暑聖品"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃冰茶清涼沁心"}]),
    rec("有沒有暖一點的飲料", {"temperature": "熱"}, [
        {"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "熱玉露菁鮮奶穀物香暖心"},
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "熱茉莉花茶清香暖胃"}]),
]

# ━━━ 5. 價格相關 (6 筆) ━━━
NEW_SAMPLES += [
    rec("有沒有六十塊以下的", {"scenario": "預算60以下"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶系列價格親民"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "M杯60元，蜜香紅茶鮮奶"}]),
    rec("最划算的是哪個", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "60元蜜香紅茶鮮奶，性價比高"},
        {"item": "朱槿普洱紅", "category": "fresh_milk_tea", "reason": "60元普洱鮮奶，獨特風味"}]),
    rec("預算一百想買兩杯", {"scenario": "預算100買兩杯"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶價格實惠"},
        {"item": "米香玉露菁", "category": "pure_tea", "reason": "玉露菁純茶也平價"}]),
    rec("想喝好一點的不怕貴", {"scenario": "不限預算"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋精緻鹹甜交融"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡萄柚茉莉清新大人味"}]),
    rec("CP值高的推薦", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "60元蜜香鮮奶甜潤好喝"},
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "65元茉莉鮮奶清香滑順"}]),
    rec("加料會很貴嗎", {}, [
        {"item": "紅烏龍茶凍", "category": "fresh_milk_tea", "reason": "加料每項+15元，搭鮮奶茶增加口感"}]),
]

# ━━━ 6. 菜單詢問 / 泛化 (10 筆) ━━━
NEW_SAMPLES += [
    rec("你們有賣咖啡嗎", {}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "本店以茶為主，鐵觀音焙火香可替代咖啡"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙烏龍醇厚回甘"}]),
    rec("你們有什麼類型的飲料", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶系列主打花茶"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "鮮奶茶系列茶奶融合"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶系列酸甜清爽"}]),
    rec("菜單上有幾種", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶五款、鮮奶茶七款、奶茶七款、果茶三款、奶蓋兩款"}]),
    rec("有賣珍珠奶茶嗎", {}, [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "本店無珍珠，奶茶系列有七款風味獨特"},
        {"item": "金杯蜜香紅", "category": "rich_milk_tea", "reason": "蜜香紅茶奶茶甜潤好喝"}]),
    rec("你們有果汁嗎", {}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "本店以茶為基底，果茶系列有清爽水果風味"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香與紅烏龍交織"}]),
    rec("有沒有無咖啡因的", {"avoid": "咖啡因"}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶咖啡因較低"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "果茶類咖啡因含量較少"}]),
    rec("有素食可以喝的嗎", {"avoid": "動物成分"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶系列全素"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶系列無動物成分"}]),
    rec("你們有鮮奶茶對吧", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花烏龍鮮奶蜜韻溫潤"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶焙火香濃郁"}]),
    rec("有沒有不含乳製品的", {"avoid": "乳製品"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶不含乳製品"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶系列無乳製品"}]),
    rec("你們都是茶類的嗎", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "以茶為主，有純茶、鮮奶茶、奶茶、果茶、奶蓋五大類"}]),
]

# ━━━ 7. 口味偏好 - 新口味描述 (8 筆) ━━━
NEW_SAMPLES += [
    rec("有沒有回甘的", {"taste": "回甘"}, [
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙烏龍回甘明顯"},
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "普洱紅茶微酸回甘"}]),
    rec("喝起來有層次感的", {"taste": "有層次"}, [
        {"item": "茶花紅烏龍", "category": "cloud_velvet", "reason": "紅烏龍焙火韻搭奶蓋鹹甜多層次"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡萄柚酸香配茉莉清新微苦層次豐富"}]),
    rec("口感滑順的", {"taste": "滑順"}, [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶清香滑順"},
        {"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "玉露菁鮮奶細膩柔滑"}]),
    rec("想要有香氣的", {"taste": "香氣"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "三次窨花茉莉，花香最清雅"},
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "桂花蜜韻香氣輕柔"}]),
    rec("想喝不那麼膩的", {"taste": "不膩"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶清爽不膩口"},
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "普洱微酸解膩"}]),
    rec("有點特殊口味的", {"taste": "特殊口味"}, [
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "洛神花搭普洱微酸回甘獨特"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡萄柚配茉莉微苦大人味"}]),
    rec("想喝帶一點鹹的", {"taste": "鹹甜"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋鹹甜交融"},
        {"item": "茶花紅烏龍", "category": "cloud_velvet", "reason": "紅烏龍奶蓋茶香奶鹹平衡"}]),
    rec("喝起來很香很療癒的", {"taste": "療癒", "scenario": "療癒"}, [
        {"item": "米香玉露菁", "category": "pure_tea", "reason": "日式玉露菁米穀香鮮爽療癒"},
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "桂花蜜韻輕柔放鬆"}]),
]

# ━━━ 8. 排除/否定 - 新模式 (8 筆) ━━━
NEW_SAMPLES += [
    rec("不要有茶味太重的", {"avoid": "茶味太重"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "果香為主茶味不重"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香甜潤茶味柔和"}]),
    rec("不喜歡酸的", {"avoid": "酸"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶溫潤不酸"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶焙火不酸"}]),
    rec("除了果茶以外有什麼", {"avoid": "果茶"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花烏龍鮮奶蜜韻溫潤"},
        {"item": "琥珀鐵觀音", "category": "cloud_velvet", "reason": "鐵觀音奶蓋焙火鹹甜"}]),
    rec("我不敢喝烏龍", {"avoid": "烏龍"}, [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶清香不苦"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜潤"}]),
    rec("不要加料", {"avoid": "加料"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶原味就好喝"},
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶原味清雅"}]),
    rec("有不是奶類的嗎", {"avoid": "奶"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶無奶花香清雅"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶無奶酸甜清爽"}]),
    rec("我不太能喝太甜的東西", {"avoid": "太甜"}, [
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "純茶可選無糖焙火回甘"},
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "普洱紅茶微酸不甜"}]),
    rec("不想喝跟上次一樣的", {}, [
        {"item": "朱槿普洱紅", "category": "fresh_milk_tea", "reason": "洛神普洱鮮奶風味獨特"},
        {"item": "米香玉露菁", "category": "pure_tea", "reason": "日式玉露菁米穀香少見"}]),
]

# ━━━ 9. 邊界案例：容易與 order 混淆 (10 筆) ━━━
NEW_SAMPLES += [
    rec("讓我想想...好，推薦一個吧", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤好入口"}]),
    rec("嗯...有沒有什麼適合我的", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜度適中"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶接受度高"}]),
    rec("你們有賣綠茶嗎", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "茉莉綠茶基底，花香清雅帶甘甜"}]),
    rec("想喝個飲料", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶酸甜清爽"}]),
    rec("有沒有紅茶拿鐵", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "本店無拿鐵，蜜香紅茶鮮奶風味近似"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶濃郁替代拿鐵"}]),
    rec("好像有聽朋友說什麼花茶很好喝", {"taste": "花茶"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "三窨茉莉花茶最經典"},
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "桂花蜜韻輕柔好喝"}]),
    rec("看你們店很多人買什麼", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶是熱門款"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶也很受歡迎"}]),
    rec("我想喝那個...什麼的", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜潤好喝"}]),
    rec("有沒有氣泡飲", {}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "本店無氣泡飲，青檸果茶酸甜也很清爽"}]),
    rec("你們有沒有季節限定的", {}, [
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚茉莉口味特殊值得一試"},
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "洛神普洱風味獨特少見"}]),
]

# ━━━ 10. 口語化/對話式 (8 筆) ━━━
NEW_SAMPLES += [
    rec("欸你們什麼最讚", {}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋鹹甜獨特最讚"}]),
    rec("ㄟ有推薦嗎", {}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶焙火濃郁"}]),
    rec("哈囉想請問一下有什麼好喝的", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶天然甜"}]),
    rec("就...想來一杯吧", {}, [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶清香好入口"}]),
    rec("我跟你說我超愛喝奶茶的", {"taste": "奶茶"}, [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "鐵觀音奶茶焙火奶香濃厚"},
        {"item": "三窨十五茉", "category": "rich_milk_tea", "reason": "茉莉奶茶清香好喝"}]),
    rec("什麼東西比較少人踩雷", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜度適中不踩雷"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶接受度高"}]),
    rec("朋友推薦我來的，什麼最紅啊", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶是招牌熱門"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶回購率高"}]),
    rec("老闆推薦一下啦", {}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋鹹甜交融招牌推薦"}]),
]

# ━━━ 11. 直接推薦 - 補強泛化 (6 筆) ━━━
NEW_SAMPLES += [
    rec("你會推什麼", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤"}]),
    rec("介紹一下", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "三窨茉莉花茶花香清雅"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花烏龍鮮奶蜜韻溫潤"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "青檸桂花蜜酸甜清爽"}]),
    rec("有什麼好的", {}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶焙火濃郁"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香清爽好喝"}]),
    rec("推薦個飲料", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶天然蜜甜"}]),
    rec("能不能推薦一兩杯", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶焙火香濃"}]),
    rec("有建議嗎", {}, [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶清香好入口"}]),
]


def main():
    random.seed(42)

    print(f"Total new samples: {len(NEW_SAMPLES)}")

    # Shuffle and split 80/20
    indices = list(range(len(NEW_SAMPLES)))
    random.shuffle(indices)

    split = int(len(NEW_SAMPLES) * 0.8)
    train_indices = sorted(indices[:split])
    valid_indices = sorted(indices[split:])

    train_new = [NEW_SAMPLES[i] for i in train_indices]
    valid_new = [NEW_SAMPLES[i] for i in valid_indices]

    print(f"Train new: {len(train_new)}")
    print(f"Valid new: {len(valid_new)}")

    # Save Round 26 samples for reference
    with open(DATA_DIR / "round26_recommend.jsonl", "w") as f:
        for s in NEW_SAMPLES:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Append to train.jsonl
    with open(DATA_DIR / "train.jsonl", "a") as f:
        for s in train_new:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Append to valid.jsonl
    with open(DATA_DIR / "valid.jsonl", "a") as f:
        for s in valid_new:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Final stats
    for fname in ["train.jsonl", "valid.jsonl"]:
        intents = {}
        total = 0
        with open(DATA_DIR / fname) as f:
            for line in f:
                if line.strip():
                    total += 1
                    d = json.loads(line)
                    for msg in d["messages"]:
                        if msg["role"] == "assistant":
                            try:
                                r = json.loads(msg["content"])
                                intent = r.get("intent", "unknown")
                                intents[intent] = intents.get(intent, 0) + 1
                            except:
                                pass
        print(f"\n{fname}: {total} samples")
        for k, v in sorted(intents.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v} ({v*100/total:.1f}%)")


if __name__ == "__main__":
    main()
