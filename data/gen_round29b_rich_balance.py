#!/usr/bin/env python3
"""Round 29b: 補充更多 rich_milk_tea 資料，目標 fresh:rich ≈ 1.5:1，含 pure_tea anchor"""

import json
import random

SYSTEM_PROMPT = """你是 No.315 Unique Green 的點單助手。根據顧客的自然語言輸出 JSON。

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
- 茶花紅烏龍(65/75)：烏龍鮮奶，茶奶平衡圓潤
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
甜度：全糖/五分糖/三分糖/一分糖/無糖（顧客若說正常糖/半糖/少糖/微糖亦照錄）。冰量：正常冰/少冰/微冰/去冰/熱飲。
未指定的甜度、冰量、尺寸設為 null。未指定分類時 category 設 null。

輸出格式（必須為合法 JSON）：
{"orders":[],"preferences":{},"recommendations":[]}
- 顧客點餐：填入 orders，每筆格式 {"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}
- 顧客想要推薦：填入 preferences（口味/溫度/場景/排除，無明確偏好時為空物件）與 recommendations（僅推薦 1 項），格式 {"item":"品名","category":"分類","reason":"推薦理由"}
- 點餐同時想推薦：orders 和 recommendations 同時填入，preferences 一併填入
- 閒聊或無法辨識：三個欄位皆為空
- 若最後一段已做出點餐決定，清空 recommendations。"""


def make_order(item, category, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
    return {
        "item": item, "category": category, "size": size,
        "ice": ice, "sugar": sugar, "addon": addon or [],
        "qty": qty, "note": note
    }

def make_example(user_input, orders, prefs=None, recs=None):
    output = {"orders": orders, "preferences": prefs or {}, "recommendations": recs or []}
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": json.dumps(output, ensure_ascii=False)}
        ]
    }

examples = []

# ============================================================
# A. 單品 rich_milk_tea — 各品項 x 各種甜度/冰量/尺寸排列
# ============================================================

ITEMS = ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"]
SUGARS = ["全糖", "五分糖", "三分糖", "一分糖", "無糖", "半糖", "少糖", "微糖", "正常糖"]
ICES = ["正常冰", "少冰", "微冰", "去冰", "熱飲"]
SIZES = ["中杯", "大杯"]
SIZE_MAP = {"中杯": "M", "大杯": "L"}

# A1. 三窨十五茉 (需要最多補充)
examples.append(make_example("茉莉奶茶中杯", [make_order("三窨十五茉", "rich_milk_tea", size="M")]))
examples.append(make_example("三窨十五茉奶茶正常糖正常冰", [make_order("三窨十五茉", "rich_milk_tea", sugar="正常糖", ice="正常冰")]))
examples.append(make_example("三窨十五茉奶茶一分糖去冰大杯", [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="一分糖", ice="去冰")]))
examples.append(make_example("三窨十五茉奶茶少糖微冰", [make_order("三窨十五茉", "rich_milk_tea", sugar="少糖", ice="微冰")]))
examples.append(make_example("茉莉奶茶熱的", [make_order("三窨十五茉", "rich_milk_tea", ice="熱飲")]))
examples.append(make_example("三窨十五茉奶精的大杯三分糖少冰", [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="三分糖", ice="少冰")]))
examples.append(make_example("一杯茉莉UG奶茶中杯", [make_order("三窨十五茉", "rich_milk_tea", size="M")]))
examples.append(make_example("三窨十五茉一般奶茶全糖少冰", [make_order("三窨十五茉", "rich_milk_tea", sugar="全糖", ice="少冰")]))
examples.append(make_example("茉莉奶茶少冰半糖中杯", [make_order("三窨十五茉", "rich_milk_tea", size="M", sugar="半糖", ice="少冰")]))
examples.append(make_example("三窨十五茉奶茶加茶凍無糖", [make_order("三窨十五茉", "rich_milk_tea", sugar="無糖", addon=["紅烏龍茶凍"])]))
examples.append(make_example("三窨十五茉奶茶加燕麥粒大杯微糖去冰", [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="微糖", ice="去冰", addon=["燕麥粒"])]))

# A2. 金杯蜜香紅
examples.append(make_example("蜜香紅奶茶大杯", [make_order("金杯蜜香紅", "rich_milk_tea", size="L")]))
examples.append(make_example("金杯蜜香紅奶茶正常糖正常冰", [make_order("金杯蜜香紅", "rich_milk_tea", sugar="正常糖", ice="正常冰")]))
examples.append(make_example("金杯蜜香紅奶茶一分糖微冰中杯", [make_order("金杯蜜香紅", "rich_milk_tea", size="M", sugar="一分糖", ice="微冰")]))
examples.append(make_example("金杯蜜香紅奶茶熱的半糖", [make_order("金杯蜜香紅", "rich_milk_tea", sugar="半糖", ice="熱飲")]))
examples.append(make_example("蜜香紅奶精的中杯少糖去冰", [make_order("金杯蜜香紅", "rich_milk_tea", size="M", sugar="少糖", ice="去冰")]))
examples.append(make_example("金杯蜜香紅一般奶茶五分糖", [make_order("金杯蜜香紅", "rich_milk_tea", sugar="五分糖")]))
examples.append(make_example("金杯蜜香紅UG奶茶大杯無糖少冰", [make_order("金杯蜜香紅", "rich_milk_tea", size="L", sugar="無糖", ice="少冰")]))
examples.append(make_example("蜜香紅奶茶加茶凍三分糖", [make_order("金杯蜜香紅", "rich_milk_tea", sugar="三分糖", addon=["紅烏龍茶凍"])]))

# A3. 茶花紅烏龍
examples.append(make_example("茶花紅烏龍奶茶中杯", [make_order("茶花紅烏龍", "rich_milk_tea", size="M")]))
examples.append(make_example("茶花紅烏龍奶茶正常糖", [make_order("茶花紅烏龍", "rich_milk_tea", sugar="正常糖")]))
examples.append(make_example("茶花紅烏龍奶精的大杯一分糖去冰", [make_order("茶花紅烏龍", "rich_milk_tea", size="L", sugar="一分糖", ice="去冰")]))
examples.append(make_example("茶花紅烏龍一般奶茶三分糖少冰", [make_order("茶花紅烏龍", "rich_milk_tea", sugar="三分糖", ice="少冰")]))
examples.append(make_example("茶花紅烏龍奶茶熱的", [make_order("茶花紅烏龍", "rich_milk_tea", ice="熱飲")]))
examples.append(make_example("茶花紅烏龍UG奶茶中杯微糖微冰", [make_order("茶花紅烏龍", "rich_milk_tea", size="M", sugar="微糖", ice="微冰")]))
examples.append(make_example("茶花紅烏龍奶茶加燕麥粒半糖", [make_order("茶花紅烏龍", "rich_milk_tea", sugar="半糖", addon=["燕麥粒"])]))

# A4. 米香玉露菁
examples.append(make_example("玉露奶茶中杯半糖", [make_order("米香玉露菁", "rich_milk_tea", size="M", sugar="半糖")]))
examples.append(make_example("米香玉露菁奶茶大杯正常糖正常冰", [make_order("米香玉露菁", "rich_milk_tea", size="L", sugar="正常糖", ice="正常冰")]))
examples.append(make_example("米香玉露菁奶精的一分糖去冰", [make_order("米香玉露菁", "rich_milk_tea", sugar="一分糖", ice="去冰")]))
examples.append(make_example("玉露UG奶茶熱的無糖", [make_order("米香玉露菁", "rich_milk_tea", sugar="無糖", ice="熱飲")]))
examples.append(make_example("米香玉露菁一般奶茶大杯三分糖少冰", [make_order("米香玉露菁", "rich_milk_tea", size="L", sugar="三分糖", ice="少冰")]))
examples.append(make_example("米香玉露菁奶茶加茶凍微糖", [make_order("米香玉露菁", "rich_milk_tea", sugar="微糖", addon=["紅烏龍茶凍"])]))

# A5. 琥珀鐵觀音
examples.append(make_example("鐵觀音奶茶中杯正常糖", [make_order("琥珀鐵觀音", "rich_milk_tea", size="M", sugar="正常糖")]))
examples.append(make_example("琥珀鐵觀音奶茶微冰三分糖", [make_order("琥珀鐵觀音", "rich_milk_tea", sugar="三分糖", ice="微冰")]))
examples.append(make_example("鐵觀音奶精的大杯少糖去冰", [make_order("琥珀鐵觀音", "rich_milk_tea", size="L", sugar="少糖", ice="去冰")]))
examples.append(make_example("琥珀鐵觀音一般奶茶熱的五分糖", [make_order("琥珀鐵觀音", "rich_milk_tea", sugar="五分糖", ice="熱飲")]))
examples.append(make_example("鐵觀音UG奶茶中杯一分糖少冰", [make_order("琥珀鐵觀音", "rich_milk_tea", size="M", sugar="一分糖", ice="少冰")]))
examples.append(make_example("琥珀鐵觀音奶茶加燕麥粒大杯", [make_order("琥珀鐵觀音", "rich_milk_tea", size="L", addon=["燕麥粒"])]))

# A6. 桂花輕烏龍
examples.append(make_example("桂花奶茶中杯五分糖", [make_order("桂花輕烏龍", "rich_milk_tea", size="M", sugar="五分糖")]))
examples.append(make_example("桂花輕烏龍奶茶正常糖正常冰大杯", [make_order("桂花輕烏龍", "rich_milk_tea", size="L", sugar="正常糖", ice="正常冰")]))
examples.append(make_example("桂花輕烏龍奶精的去冰無糖", [make_order("桂花輕烏龍", "rich_milk_tea", sugar="無糖", ice="去冰")]))
examples.append(make_example("桂花輕烏龍一般奶茶熱的半糖", [make_order("桂花輕烏龍", "rich_milk_tea", sugar="半糖", ice="熱飲")]))
examples.append(make_example("桂花UG奶茶大杯一分糖微冰", [make_order("桂花輕烏龍", "rich_milk_tea", size="L", sugar="一分糖", ice="微冰")]))
examples.append(make_example("桂花輕烏龍奶茶加茶凍少糖少冰", [make_order("桂花輕烏龍", "rich_milk_tea", sugar="少糖", ice="少冰", addon=["紅烏龍茶凍"])]))

# A7. 朱槿普洱紅
examples.append(make_example("普洱奶茶大杯三分糖", [make_order("朱槿普洱紅", "rich_milk_tea", size="L", sugar="三分糖")]))
examples.append(make_example("朱槿普洱紅奶茶正常糖少冰", [make_order("朱槿普洱紅", "rich_milk_tea", sugar="正常糖", ice="少冰")]))
examples.append(make_example("朱槿普洱紅奶精的中杯無糖去冰", [make_order("朱槿普洱紅", "rich_milk_tea", size="M", sugar="無糖", ice="去冰")]))
examples.append(make_example("普洱一般奶茶熱的微糖", [make_order("朱槿普洱紅", "rich_milk_tea", sugar="微糖", ice="熱飲")]))
examples.append(make_example("朱槿普洱紅UG奶茶大杯半糖微冰", [make_order("朱槿普洱紅", "rich_milk_tea", size="L", sugar="半糖", ice="微冰")]))


# ============================================================
# B. 多品項 rich_milk_tea
# ============================================================
examples.append(make_example("三窨十五茉奶茶跟金杯蜜香紅奶茶各一杯大杯",
    [make_order("三窨十五茉", "rich_milk_tea", size="L"),
     make_order("金杯蜜香紅", "rich_milk_tea", size="L")]))

examples.append(make_example("琥珀鐵觀音奶茶半糖、茶花紅烏龍奶茶無糖，都要去冰",
    [make_order("琥珀鐵觀音", "rich_milk_tea", sugar="半糖", ice="去冰"),
     make_order("茶花紅烏龍", "rich_milk_tea", sugar="無糖", ice="去冰")]))

examples.append(make_example("桂花輕烏龍奶茶中杯微糖、米香玉露菁奶茶大杯半糖",
    [make_order("桂花輕烏龍", "rich_milk_tea", size="M", sugar="微糖"),
     make_order("米香玉露菁", "rich_milk_tea", size="L", sugar="半糖")]))

examples.append(make_example("三杯奶茶，三窨十五茉、琥珀鐵觀音、金杯蜜香紅，都大杯半糖去冰",
    [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="半糖", ice="去冰"),
     make_order("琥珀鐵觀音", "rich_milk_tea", size="L", sugar="半糖", ice="去冰"),
     make_order("金杯蜜香紅", "rich_milk_tea", size="L", sugar="半糖", ice="去冰")]))

examples.append(make_example("朱槿普洱紅奶茶跟米香玉露菁奶茶各一杯中杯無糖",
    [make_order("朱槿普洱紅", "rich_milk_tea", size="M", sugar="無糖"),
     make_order("米香玉露菁", "rich_milk_tea", size="M", sugar="無糖")]))

examples.append(make_example("兩杯桂花輕烏龍奶茶，一杯半糖一杯無糖",
    [make_order("桂花輕烏龍", "rich_milk_tea", sugar="半糖"),
     make_order("桂花輕烏龍", "rich_milk_tea", sugar="無糖")]))

examples.append(make_example("茶花紅烏龍奶茶中杯、三窨十五茉奶茶大杯，都要少冰五分糖",
    [make_order("茶花紅烏龍", "rich_milk_tea", size="M", sugar="五分糖", ice="少冰"),
     make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="五分糖", ice="少冰")]))


# ============================================================
# C. 更多跨分類對比 fresh vs rich
# ============================================================
examples.append(make_example("三窨十五茉鮮奶茶大杯，再一杯奶茶的中杯半糖",
    [make_order("三窨十五茉", "fresh_milk_tea", size="L"),
     make_order("三窨十五茉", "rich_milk_tea", size="M", sugar="半糖")]))

examples.append(make_example("金杯蜜香紅鮮奶中杯五分糖，再一杯金杯蜜香紅奶茶大杯無糖去冰",
    [make_order("金杯蜜香紅", "fresh_milk_tea", size="M", sugar="五分糖"),
     make_order("金杯蜜香紅", "rich_milk_tea", size="L", sugar="無糖", ice="去冰")]))

examples.append(make_example("琥珀鐵觀音，一杯加鮮奶大杯，一杯奶茶中杯半糖去冰",
    [make_order("琥珀鐵觀音", "fresh_milk_tea", size="L"),
     make_order("琥珀鐵觀音", "rich_milk_tea", size="M", sugar="半糖", ice="去冰")]))

examples.append(make_example("茶花紅烏龍鮮奶半糖，再來一杯奶精的無糖",
    [make_order("茶花紅烏龍", "fresh_milk_tea", sugar="半糖"),
     make_order("茶花紅烏龍", "rich_milk_tea", sugar="無糖")]))

examples.append(make_example("米香玉露菁加鮮奶中杯去冰，再一杯一般奶茶大杯三分糖少冰",
    [make_order("米香玉露菁", "fresh_milk_tea", size="M", ice="去冰"),
     make_order("米香玉露菁", "rich_milk_tea", size="L", sugar="三分糖", ice="少冰")]))

examples.append(make_example("桂花輕烏龍鮮奶茶大杯無糖去冰，再一杯桂花輕烏龍奶茶中杯微糖少冰",
    [make_order("桂花輕烏龍", "fresh_milk_tea", size="L", sugar="無糖", ice="去冰"),
     make_order("桂花輕烏龍", "rich_milk_tea", size="M", sugar="微糖", ice="少冰")]))

examples.append(make_example("朱槿普洱紅鮮奶中杯半糖，再一杯奶茶大杯無糖",
    [make_order("朱槿普洱紅", "fresh_milk_tea", size="M", sugar="半糖"),
     make_order("朱槿普洱紅", "rich_milk_tea", size="L", sugar="無糖")]))


# ============================================================
# D. 多輪跨分類（分號分隔）
# ============================================================
examples.append(make_example("三窨十五茉奶茶大杯半糖去冰;再一杯鮮奶的中杯無糖",
    [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="半糖", ice="去冰"),
     make_order("三窨十五茉", "fresh_milk_tea", size="M", sugar="無糖")]))

examples.append(make_example("金杯蜜香紅奶茶中杯三分糖;再一杯鮮奶大杯去冰",
    [make_order("金杯蜜香紅", "rich_milk_tea", size="M", sugar="三分糖"),
     make_order("金杯蜜香紅", "fresh_milk_tea", size="L", ice="去冰")]))

examples.append(make_example("茶花紅烏龍奶精的半糖少冰;再加一杯鮮奶的大杯無糖去冰",
    [make_order("茶花紅烏龍", "rich_milk_tea", sugar="半糖", ice="少冰"),
     make_order("茶花紅烏龍", "fresh_milk_tea", size="L", sugar="無糖", ice="去冰")]))

examples.append(make_example("琥珀鐵觀音奶茶大杯無糖去冰;再一杯鮮奶的中杯半糖少冰",
    [make_order("琥珀鐵觀音", "rich_milk_tea", size="L", sugar="無糖", ice="去冰"),
     make_order("琥珀鐵觀音", "fresh_milk_tea", size="M", sugar="半糖", ice="少冰")]))

examples.append(make_example("桂花輕烏龍奶茶半糖;再一杯鮮奶的去冰大杯",
    [make_order("桂花輕烏龍", "rich_milk_tea", sugar="半糖"),
     make_order("桂花輕烏龍", "fresh_milk_tea", ice="去冰", size="L")]))


# ============================================================
# E. 數量 > 1
# ============================================================
examples.append(make_example("三窨十五茉奶茶大杯半糖兩杯", [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="半糖", qty=2)]))
examples.append(make_example("琥珀鐵觀音奶茶三杯中杯無糖去冰", [make_order("琥珀鐵觀音", "rich_milk_tea", size="M", sugar="無糖", ice="去冰", qty=3)]))
examples.append(make_example("金杯蜜香紅奶茶兩杯大杯", [make_order("金杯蜜香紅", "rich_milk_tea", size="L", qty=2)]))


# ============================================================
# F. 修改場景 (改成奶茶)
# ============================================================
examples.append(make_example("琥珀鐵觀音鮮奶，啊不對，改奶茶就好",
    [make_order("琥珀鐵觀音", "rich_milk_tea")]))

examples.append(make_example("三窨十五茉鮮奶茶大杯，等等，改成奶茶的",
    [make_order("三窨十五茉", "rich_milk_tea", size="L")]))

examples.append(make_example("金杯蜜香紅鮮奶半糖，不要鮮奶改奶茶",
    [make_order("金杯蜜香紅", "rich_milk_tea", sugar="半糖")]))


# ============================================================
# G. 混合品項（rich + 其他分類）
# ============================================================
examples.append(make_example("三窨十五茉奶茶大杯半糖，再一杯青檸桂蜜",
    [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="半糖"),
     make_order("青檸桂蜜", "fruit_tea")]))

examples.append(make_example("琥珀鐵觀音奶茶中杯去冰，加一杯桂花輕烏龍純茶無糖",
    [make_order("琥珀鐵觀音", "rich_milk_tea", size="M", ice="去冰"),
     make_order("桂花輕烏龍", "pure_tea", sugar="無糖")]))

examples.append(make_example("茶花紅烏龍奶蓋一杯，再一杯三窨十五茉奶茶大杯半糖",
    [make_order("茶花紅烏龍", "cloud_velvet"),
     make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="半糖")]))

examples.append(make_example("蜜桃紅烏龍跟琥珀鐵觀音奶茶各一杯，奶茶大杯半糖去冰",
    [make_order("蜜桃紅烏龍", "fruit_tea"),
     make_order("琥珀鐵觀音", "rich_milk_tea", size="L", sugar="半糖", ice="去冰")]))

examples.append(make_example("米香玉露菁純茶一杯，再一杯金杯蜜香紅奶茶大杯無糖",
    [make_order("米香玉露菁", "pure_tea"),
     make_order("金杯蜜香紅", "rich_milk_tea", size="L", sugar="無糖")]))


# ============================================================
# H. Pure tea anchor 樣本（防回歸）
# ============================================================
examples.append(make_example("三窨十五茉純茶無糖", [make_order("三窨十五茉", "pure_tea", sugar="無糖")]))
examples.append(make_example("桂花輕烏龍純茶去冰", [make_order("桂花輕烏龍", "pure_tea", ice="去冰")]))
examples.append(make_example("茶花紅烏龍茶就好不加奶", [make_order("茶花紅烏龍", "pure_tea")]))
examples.append(make_example("朱槿普洱紅純茶一分糖", [make_order("朱槿普洱紅", "pure_tea", sugar="一分糖")]))
examples.append(make_example("米香玉露菁不加奶無糖去冰", [make_order("米香玉露菁", "pure_tea", sugar="無糖", ice="去冰")]))


# ============================================================
# Split & Save
# ============================================================
random.seed(123)
random.shuffle(examples)

n_valid = max(1, len(examples) // 5)
valid_set = examples[:n_valid]
train_set = examples[n_valid:]

print(f"Total: {len(examples)}")
print(f"Train: {len(train_set)}")
print(f"Valid: {len(valid_set)}")

rich_count = sum(1 for ex in examples
                 for msg in ex["messages"]
                 if msg["role"] == "assistant" and '"rich_milk_tea"' in msg["content"])
print(f"含 rich_milk_tea 的樣本: {rich_count}")

with open("data/round29b_train.jsonl", "w") as f:
    for ex in train_set:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

with open("data/round29b_valid.jsonl", "w") as f:
    for ex in valid_set:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print("\nSaved to data/round29b_train.jsonl and data/round29b_valid.jsonl")
