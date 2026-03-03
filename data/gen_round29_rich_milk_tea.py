#!/usr/bin/env python3
"""Round 29: 補充 rich_milk_tea 訓練資料，拉近 fresh/rich 比例"""

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
        "item": item,
        "category": category,
        "size": size,
        "ice": ice,
        "sugar": sugar,
        "addon": addon or [],
        "qty": qty,
        "note": note
    }


def make_example(user_input, orders, preferences=None, recommendations=None):
    output = {
        "orders": orders,
        "preferences": preferences or {},
        "recommendations": recommendations or []
    }
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": json.dumps(output, ensure_ascii=False)}
        ]
    }


examples = []

# === A. 單品 rich_milk_tea（明確說「奶茶」）===
# 三窨十五茉 (最失衡 6.2:1，多補)
examples.append(make_example("三窨十五茉奶茶", [make_order("三窨十五茉", "rich_milk_tea")]))
examples.append(make_example("三窨十五茉奶茶半糖去冰", [make_order("三窨十五茉", "rich_milk_tea", sugar="半糖", ice="去冰")]))
examples.append(make_example("三窨十五茉奶茶大杯", [make_order("三窨十五茉", "rich_milk_tea", size="L")]))
examples.append(make_example("三窨十五茉奶茶中杯無糖少冰", [make_order("三窨十五茉", "rich_milk_tea", size="M", sugar="無糖", ice="少冰")]))
examples.append(make_example("三窨十五茉奶茶微糖微冰", [make_order("三窨十五茉", "rich_milk_tea", sugar="微糖", ice="微冰")]))
examples.append(make_example("一杯三窨十五茉奶茶三分糖", [make_order("三窨十五茉", "rich_milk_tea", sugar="三分糖")]))
examples.append(make_example("茉莉奶茶", [make_order("三窨十五茉", "rich_milk_tea")]))
examples.append(make_example("茉莉奶茶大杯五分糖去冰", [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="五分糖", ice="去冰")]))

# 金杯蜜香紅 (3.1:1)
examples.append(make_example("金杯蜜香紅奶茶", [make_order("金杯蜜香紅", "rich_milk_tea")]))
examples.append(make_example("金杯蜜香紅奶茶大杯半糖", [make_order("金杯蜜香紅", "rich_milk_tea", size="L", sugar="半糖")]))
examples.append(make_example("金杯蜜香紅奶茶中杯無糖去冰", [make_order("金杯蜜香紅", "rich_milk_tea", size="M", sugar="無糖", ice="去冰")]))
examples.append(make_example("蜜香紅奶茶少冰", [make_order("金杯蜜香紅", "rich_milk_tea", ice="少冰")]))
examples.append(make_example("金杯蜜香紅奶茶微糖", [make_order("金杯蜜香紅", "rich_milk_tea", sugar="微糖")]))

# 茶花紅烏龍 (2:1)
examples.append(make_example("茶花紅烏龍奶茶", [make_order("茶花紅烏龍", "rich_milk_tea")]))
examples.append(make_example("茶花紅烏龍奶茶大杯半糖少冰", [make_order("茶花紅烏龍", "rich_milk_tea", size="L", sugar="半糖", ice="少冰")]))
examples.append(make_example("茶花紅烏龍奶茶無糖去冰", [make_order("茶花紅烏龍", "rich_milk_tea", sugar="無糖", ice="去冰")]))

# 米香玉露菁 (2.2:1)
examples.append(make_example("米香玉露菁奶茶", [make_order("米香玉露菁", "rich_milk_tea")]))
examples.append(make_example("米香玉露菁奶茶中杯五分糖少冰", [make_order("米香玉露菁", "rich_milk_tea", size="M", sugar="五分糖", ice="少冰")]))
examples.append(make_example("玉露奶茶大杯", [make_order("米香玉露菁", "rich_milk_tea", size="L")]))

# 琥珀鐵觀音 (1.9:1)
examples.append(make_example("琥珀鐵觀音奶茶", [make_order("琥珀鐵觀音", "rich_milk_tea")]))
examples.append(make_example("琥珀鐵觀音奶茶大杯無糖", [make_order("琥珀鐵觀音", "rich_milk_tea", size="L", sugar="無糖")]))
examples.append(make_example("鐵觀音奶茶半糖去冰", [make_order("琥珀鐵觀音", "rich_milk_tea", sugar="半糖", ice="去冰")]))

# 桂花輕烏龍 (1.9:1)
examples.append(make_example("桂花輕烏龍奶茶", [make_order("桂花輕烏龍", "rich_milk_tea")]))
examples.append(make_example("桂花輕烏龍奶茶中杯三分糖微冰", [make_order("桂花輕烏龍", "rich_milk_tea", size="M", sugar="三分糖", ice="微冰")]))
examples.append(make_example("桂花奶茶大杯", [make_order("桂花輕烏龍", "rich_milk_tea", size="L")]))

# 朱槿普洱紅 (≈1:1 但也補一些)
examples.append(make_example("朱槿普洱紅奶茶半糖", [make_order("朱槿普洱紅", "rich_milk_tea", sugar="半糖")]))
examples.append(make_example("普洱奶茶去冰", [make_order("朱槿普洱紅", "rich_milk_tea", ice="去冰")]))


# === B. 使用「奶精的」「一般奶茶」「UG奶茶」等口語 ===
examples.append(make_example("三窨十五茉奶精的", [make_order("三窨十五茉", "rich_milk_tea")]))
examples.append(make_example("琥珀鐵觀音奶精的半糖去冰", [make_order("琥珀鐵觀音", "rich_milk_tea", sugar="半糖", ice="去冰")]))
examples.append(make_example("金杯蜜香紅一般奶茶大杯", [make_order("金杯蜜香紅", "rich_milk_tea", size="L")]))
examples.append(make_example("桂花輕烏龍一般奶茶微糖少冰", [make_order("桂花輕烏龍", "rich_milk_tea", sugar="微糖", ice="少冰")]))
examples.append(make_example("茶花紅烏龍UG奶茶", [make_order("茶花紅烏龍", "rich_milk_tea")]))
examples.append(make_example("來杯UG奶茶三窨十五茉大杯半糖", [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="半糖")]))
examples.append(make_example("米香玉露菁奶精的中杯無糖", [make_order("米香玉露菁", "rich_milk_tea", size="M", sugar="無糖")]))
examples.append(make_example("朱槿普洱紅奶精的少冰", [make_order("朱槿普洱紅", "rich_milk_tea", ice="少冰")]))


# === C. 多品項含 rich_milk_tea ===
examples.append(make_example("三窨十五茉奶茶半糖、金杯蜜香紅奶茶無糖",
    [make_order("三窨十五茉", "rich_milk_tea", sugar="半糖"),
     make_order("金杯蜜香紅", "rich_milk_tea", sugar="無糖")]))

examples.append(make_example("琥珀鐵觀音奶茶大杯去冰、桂花輕烏龍奶茶中杯少冰",
    [make_order("琥珀鐵觀音", "rich_milk_tea", size="L", ice="去冰"),
     make_order("桂花輕烏龍", "rich_milk_tea", size="M", ice="少冰")]))

examples.append(make_example("兩杯奶茶，一杯三窨十五茉大杯半糖，一杯茶花紅烏龍中杯無糖",
    [make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="半糖"),
     make_order("茶花紅烏龍", "rich_milk_tea", size="M", sugar="無糖")]))

examples.append(make_example("米香玉露菁奶茶跟朱槿普洱紅奶茶各一杯",
    [make_order("米香玉露菁", "rich_milk_tea"),
     make_order("朱槿普洱紅", "rich_milk_tea")]))


# === D. 跨分類對比：鮮奶茶 vs 奶茶 (強化區分) ===
examples.append(make_example("琥珀鐵觀音鮮奶茶半糖去冰，再一杯琥珀鐵觀音奶茶無糖少冰",
    [make_order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="去冰"),
     make_order("琥珀鐵觀音", "rich_milk_tea", sugar="無糖", ice="少冰")]))

examples.append(make_example("三窨十五茉鮮奶中杯半糖，再一杯三窨十五茉奶茶大杯無糖",
    [make_order("三窨十五茉", "fresh_milk_tea", size="M", sugar="半糖"),
     make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="無糖")]))

examples.append(make_example("金杯蜜香紅加鮮奶去冰，再來一杯奶茶的半糖",
    [make_order("金杯蜜香紅", "fresh_milk_tea", ice="去冰"),
     make_order("金杯蜜香紅", "rich_milk_tea", sugar="半糖")]))

examples.append(make_example("桂花輕烏龍鮮奶大杯，再一杯桂花輕烏龍奶茶中杯微糖",
    [make_order("桂花輕烏龍", "fresh_milk_tea", size="L"),
     make_order("桂花輕烏龍", "rich_milk_tea", size="M", sugar="微糖")]))

examples.append(make_example("茶花紅烏龍鮮奶的半糖少冰，再一杯奶精的無糖去冰",
    [make_order("茶花紅烏龍", "fresh_milk_tea", sugar="半糖", ice="少冰"),
     make_order("茶花紅烏龍", "rich_milk_tea", sugar="無糖", ice="去冰")]))

examples.append(make_example("一杯米香玉露菁鮮奶，再一杯米香玉露菁奶茶大杯半糖去冰",
    [make_order("米香玉露菁", "fresh_milk_tea"),
     make_order("米香玉露菁", "rich_milk_tea", size="L", sugar="半糖", ice="去冰")]))


# === E. 多輪跨分類（分號分隔）===
examples.append(make_example("琥珀鐵觀音奶茶半糖去冰;再一杯鮮奶的無糖少冰",
    [make_order("琥珀鐵觀音", "rich_milk_tea", sugar="半糖", ice="去冰"),
     make_order("琥珀鐵觀音", "fresh_milk_tea", sugar="無糖", ice="少冰")]))

examples.append(make_example("三窨十五茉奶茶大杯;再來一杯鮮奶的中杯半糖",
    [make_order("三窨十五茉", "rich_milk_tea", size="L"),
     make_order("三窨十五茉", "fresh_milk_tea", size="M", sugar="半糖")]))

examples.append(make_example("金杯蜜香紅奶精的微糖;再一杯鮮奶的去冰",
    [make_order("金杯蜜香紅", "rich_milk_tea", sugar="微糖"),
     make_order("金杯蜜香紅", "fresh_milk_tea", ice="去冰")]))

examples.append(make_example("桂花輕烏龍奶茶中杯無糖去冰;再一杯鮮奶大杯半糖少冰",
    [make_order("桂花輕烏龍", "rich_milk_tea", size="M", sugar="無糖", ice="去冰"),
     make_order("桂花輕烏龍", "fresh_milk_tea", size="L", sugar="半糖", ice="少冰")]))


# === F. 易混淆品項 + rich_milk_tea ===
examples.append(make_example("蜜桃紅烏龍一杯，再一杯茶花紅烏龍奶茶半糖少冰",
    [make_order("蜜桃紅烏龍", "fruit_tea"),
     make_order("茶花紅烏龍", "rich_milk_tea", sugar="半糖", ice="少冰")]))

examples.append(make_example("葡柚十五茉一杯，再一杯三窨十五茉奶茶大杯無糖",
    [make_order("葡柚十五茉", "fruit_tea"),
     make_order("三窨十五茉", "rich_milk_tea", size="L", sugar="無糖")]))

examples.append(make_example("青檸桂蜜一杯，再一杯桂花輕烏龍奶茶中杯半糖",
    [make_order("青檸桂蜜", "fruit_tea"),
     make_order("桂花輕烏龍", "rich_milk_tea", size="M", sugar="半糖")]))


# === G. 加料 + rich_milk_tea ===
examples.append(make_example("琥珀鐵觀音奶茶加茶凍半糖去冰",
    [make_order("琥珀鐵觀音", "rich_milk_tea", sugar="半糖", ice="去冰", addon=["紅烏龍茶凍"])]))

examples.append(make_example("三窨十五茉奶茶大杯加燕麥粒",
    [make_order("三窨十五茉", "rich_milk_tea", size="L", addon=["燕麥粒"])]))


# === H. Anchor 樣本（防回歸）===
# 確保 fresh_milk_tea 不被影響
examples.append(make_example("琥珀鐵觀音鮮奶大杯半糖去冰",
    [make_order("琥珀鐵觀音", "fresh_milk_tea", size="L", sugar="半糖", ice="去冰")]))

examples.append(make_example("三窨十五茉鮮奶中杯無糖",
    [make_order("三窨十五茉", "fresh_milk_tea", size="M", sugar="無糖")]))

examples.append(make_example("金杯蜜香紅鮮奶茶大杯五分糖少冰",
    [make_order("金杯蜜香紅", "fresh_milk_tea", size="L", sugar="五分糖", ice="少冰")]))

# 推薦 anchor
examples.append(make_example("有什麼好喝的奶茶推薦嗎", {
    "orders": [],
    "preferences": {"flavor": "奶茶"},
    "recommendations": [{"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "重焙鐵觀音搭配濃郁奶香，茶味厚實回甘"}]
}))

# 閒聊 anchor
examples.append(make_example("奶茶跟鮮奶茶差在哪", {
    "orders": [],
    "preferences": {},
    "recommendations": []
}))


# Split train/valid (80/20)
random.seed(42)
random.shuffle(examples)

# Fix: the recommend/other examples use different format
fixed_examples = []
for ex in examples:
    if isinstance(ex, dict) and "messages" in ex:
        fixed_examples.append(ex)
    else:
        # This shouldn't happen with make_example, but just in case
        fixed_examples.append(ex)

# Handle the special cases (recommend anchor and chat anchor)
# They were passed as dicts directly, need to fix
final_examples = []
for ex in fixed_examples:
    msgs = ex.get("messages", [])
    if len(msgs) == 3 and isinstance(msgs[2].get("content"), dict):
        # Fix: assistant content should be JSON string
        msgs[2]["content"] = json.dumps(msgs[2]["content"], ensure_ascii=False)
    final_examples.append(ex)

n_valid = max(1, len(final_examples) // 5)
valid_set = final_examples[:n_valid]
train_set = final_examples[n_valid:]

print(f"Total: {len(final_examples)}")
print(f"Train: {len(train_set)}")
print(f"Valid: {len(valid_set)}")

# Count rich_milk_tea in new data
rich_count = sum(1 for ex in final_examples
                 for msg in ex["messages"]
                 if msg["role"] == "assistant" and '"rich_milk_tea"' in msg["content"])
print(f"含 rich_milk_tea 的樣本: {rich_count}")

# Write
with open("data/round29_train.jsonl", "w") as f:
    for ex in train_set:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

with open("data/round29_valid.jsonl", "w") as f:
    for ex in valid_set:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print("\nSaved to data/round29_train.jsonl and data/round29_valid.jsonl")
