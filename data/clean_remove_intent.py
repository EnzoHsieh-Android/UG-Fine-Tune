#!/usr/bin/env python3
"""
Remove intent field from all training data and add chitchat samples.
Also update system prompt to new version.
"""
import json
import random

# New system prompt (must match backend llm.go exactly)
NEW_SYSTEM_PROMPT = """你是 No.315 Unique Green 的點單助手。根據顧客的自然語言輸出 JSON。

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
未指定分類時，優先歸為純茶；若該品項無純茶選項，歸為奶茶。
若品項無法確定分類，category 設 null。

輸出格式（必須為合法 JSON）：
{"orders":[],"preferences":{},"recommendations":[]}
- 顧客點餐：填入 orders，每筆格式 {"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}
- 顧客想要推薦：填入 preferences（口味/溫度/場景/排除）與 recommendations，每筆格式 {"item":"品名","category":"分類","reason":"推薦理由"}
- 點餐同時想推薦：orders 和 recommendations 同時填入，preferences 一併填入
- 閒聊或無法辨識：三個欄位皆為空
- 若最後一段已做出點餐決定，清空 recommendations。""".strip()

EMPTY_RESPONSE = json.dumps({"orders": [], "preferences": {}, "recommendations": []}, ensure_ascii=False)

# Chitchat samples to add
CHITCHAT_SAMPLES = [
    # Greetings
    "你好",
    "嗨",
    "哈囉",
    "午安",
    "早安",
    "晚安",
    "嘿嘿",
    # Thanks / goodbye
    "謝謝",
    "感謝",
    "謝謝你",
    "好的謝謝",
    "掰掰",
    "再見",
    "下次見",
    # Non-order questions
    "可以用LINE Pay嗎",
    "有外送嗎",
    "你們幾點關",
    "廁所在哪裡",
    "可以內用嗎",
    "有Wi-Fi嗎",
    "你們在哪裡",
    "等一下",
    "我想一下",
    "還沒想好",
    # Random chatter
    "今天好熱",
    "下雨了",
    "人好多喔",
    "好香喔",
    "你是機器人嗎",
    "好的",
]


def make_chitchat_sample(user_text):
    return {
        "messages": [
            {"role": "system", "content": NEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": EMPTY_RESPONSE},
        ]
    }


def remove_intent_and_ensure_fields(asst_content):
    """Remove intent, ensure orders/preferences/recommendations exist."""
    try:
        parsed = json.loads(asst_content)
    except json.JSONDecodeError:
        return asst_content

    # Remove intent
    parsed.pop("intent", None)

    # Ensure all three fields exist
    if "orders" not in parsed:
        parsed["orders"] = []
    if "preferences" not in parsed:
        parsed["preferences"] = {}
    if "recommendations" not in parsed:
        parsed["recommendations"] = []

    # For samples with recommendations but missing preferences, add empty
    # For samples with orders + recommendations (mixed), ensure preferences present
    if len(parsed["recommendations"]) > 0 and not parsed.get("preferences"):
        parsed["preferences"] = {}

    # Remove any extra top-level fields (like "note" at top level)
    allowed_keys = {"orders", "preferences", "recommendations"}
    extra = set(parsed.keys()) - allowed_keys
    for k in extra:
        parsed.pop(k)

    # Rebuild in consistent key order
    result = {
        "orders": parsed["orders"],
        "preferences": parsed["preferences"],
        "recommendations": parsed["recommendations"],
    }

    return json.dumps(result, ensure_ascii=False)


def process_file(path):
    with open(path) as f:
        data = [json.loads(l) for l in f]

    for sample in data:
        for m in sample["messages"]:
            if m["role"] == "system":
                m["content"] = NEW_SYSTEM_PROMPT
            elif m["role"] == "assistant":
                m["content"] = remove_intent_and_ensure_fields(m["content"])

    return data


def main():
    # Process existing data
    train = process_file("/Users/xiechengru/ug-finetune/data/train.jsonl")
    valid = process_file("/Users/xiechengru/ug-finetune/data/valid.jsonl")

    print(f"Processed: train={len(train)}, valid={len(valid)}")

    # Add chitchat samples
    random.seed(42)
    random.shuffle(CHITCHAT_SAMPLES)

    # 80/20 split for chitchat
    split_idx = int(len(CHITCHAT_SAMPLES) * 0.8)
    chitchat_train = [make_chitchat_sample(t) for t in CHITCHAT_SAMPLES[:split_idx]]
    chitchat_valid = [make_chitchat_sample(t) for t in CHITCHAT_SAMPLES[split_idx:]]

    train.extend(chitchat_train)
    valid.extend(chitchat_valid)

    print(f"Added chitchat: train +{len(chitchat_train)}, valid +{len(chitchat_valid)}")
    print(f"Final: train={len(train)}, valid={len(valid)}, total={len(train)+len(valid)}")

    # Write
    with open("/Users/xiechengru/ug-finetune/data/train.jsonl", "w") as f:
        for s in train:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open("/Users/xiechengru/ug-finetune/data/valid.jsonl", "w") as f:
        for s in valid:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Verify
    print("\n--- Verification ---")
    for split, data in [("train", train), ("valid", valid)]:
        intent_count = 0
        empty_count = 0
        for s in data:
            for m in s["messages"]:
                if m["role"] == "assistant":
                    parsed = json.loads(m["content"])
                    if "intent" in parsed:
                        intent_count += 1
                    if not parsed["orders"] and not parsed["recommendations"]:
                        empty_count += 1
        print(f"{split}: {len(data)} samples, intent残留={intent_count}, chitchat(empty)={empty_count}")


if __name__ == "__main__":
    main()
