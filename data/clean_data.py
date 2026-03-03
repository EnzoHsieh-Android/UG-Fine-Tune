#!/usr/bin/env python3
"""Clean training data for Round 26:
1. Remove all "other" intent samples
2. Update system prompt (remove "other" intent)
3. Deduplicate (keep first occurrence of each user message)
4. Standardize not_on_menu format
5. Backup original files
"""

import json
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent

# ── New system prompt (without "other" intent) ──────────────────────────
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


def get_intent(sample):
    """Extract intent from sample's assistant message."""
    for msg in sample["messages"]:
        if msg["role"] == "assistant":
            try:
                resp = json.loads(msg["content"])
                return resp.get("intent", "unknown")
            except json.JSONDecodeError:
                return "parse_error"
    return "unknown"


def get_user_msg(sample):
    """Extract user message from sample."""
    for msg in sample["messages"]:
        if msg["role"] == "user":
            return msg["content"]
    return ""


def standardize_not_on_menu(sample):
    """Ensure not_on_menu items have consistent format."""
    for msg in sample["messages"]:
        if msg["role"] == "assistant":
            try:
                resp = json.loads(msg["content"])
                if resp.get("intent") == "order":
                    changed = False
                    for order in resp.get("orders", []):
                        if order.get("not_on_menu"):
                            # Ensure consistent fields for not_on_menu
                            if "category" not in order:
                                order["category"] = None
                                changed = True
                            if "qty" not in order:
                                order["qty"] = 1
                                changed = True
                            if "size" not in order:
                                order["size"] = None
                                changed = True
                            if "ice" not in order:
                                order["ice"] = None
                                changed = True
                            if "sugar" not in order:
                                order["sugar"] = None
                                changed = True
                            if "addon" not in order:
                                order["addon"] = []
                                changed = True
                    if changed:
                        msg["content"] = json.dumps(resp, ensure_ascii=False)
            except json.JSONDecodeError:
                pass
    return sample


def clean_file(input_path, output_path):
    """Clean a single JSONL file."""
    samples = []
    with open(input_path) as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line.strip()))

    original_count = len(samples)
    stats = {"original": original_count, "removed_other": 0, "removed_dupes": 0, "standardized_nom": 0}

    # Step 1: Remove "other" intent
    cleaned = []
    for s in samples:
        intent = get_intent(s)
        if intent == "other":
            stats["removed_other"] += 1
            continue
        cleaned.append(s)

    # Step 2: Update system prompt
    for s in cleaned:
        for msg in s["messages"]:
            if msg["role"] == "system":
                msg["content"] = NEW_SYSTEM_PROMPT

    # Step 3: Deduplicate (keep first occurrence)
    seen_msgs = set()
    deduped = []
    for s in cleaned:
        user_msg = get_user_msg(s)
        if user_msg in seen_msgs:
            stats["removed_dupes"] += 1
            continue
        seen_msgs.add(user_msg)
        deduped.append(s)

    # Step 4: Standardize not_on_menu format
    final = []
    for s in deduped:
        s_std = standardize_not_on_menu(s)
        final.append(s_std)

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        for s in final:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    stats["final"] = len(final)
    return stats


def main():
    train_in = DATA_DIR / "train.jsonl"
    valid_in = DATA_DIR / "valid.jsonl"

    # Backup originals
    print("=== Backing up original files ===")
    shutil.copy2(train_in, DATA_DIR / "train.jsonl.bak_r25")
    shutil.copy2(valid_in, DATA_DIR / "valid.jsonl.bak_r25")
    print("  Backed up to train.jsonl.bak_r25 and valid.jsonl.bak_r25")

    # Clean train
    print("\n=== Cleaning train.jsonl ===")
    train_stats = clean_file(train_in, train_in)
    print(f"  Original: {train_stats['original']}")
    print(f"  Removed other: {train_stats['removed_other']}")
    print(f"  Removed dupes: {train_stats['removed_dupes']}")
    print(f"  Final: {train_stats['final']}")

    # Clean valid
    print("\n=== Cleaning valid.jsonl ===")
    valid_stats = clean_file(valid_in, valid_in)
    print(f"  Original: {valid_stats['original']}")
    print(f"  Removed other: {valid_stats['removed_other']}")
    print(f"  Removed dupes: {valid_stats['removed_dupes']}")
    print(f"  Final: {valid_stats['final']}")

    # Final distribution
    print("\n=== Final Distribution ===")
    for fname in ["train.jsonl", "valid.jsonl"]:
        intents = {}
        total = 0
        with open(DATA_DIR / fname) as f:
            for line in f:
                if line.strip():
                    total += 1
                    d = json.loads(line)
                    intent = get_intent(d)
                    intents[intent] = intents.get(intent, 0) + 1
        print(f"\n{fname}: {total} samples")
        for k, v in sorted(intents.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v} ({v*100/total:.1f}%)")

    total_final = train_stats["final"] + valid_stats["final"]
    total_removed = (train_stats["removed_other"] + train_stats["removed_dupes"] +
                     valid_stats["removed_other"] + valid_stats["removed_dupes"])
    print(f"\n=== Summary ===")
    print(f"Total removed: {total_removed} ({train_stats['removed_other'] + valid_stats['removed_other']} other + {train_stats['removed_dupes'] + valid_stats['removed_dupes']} dupes)")
    print(f"Total remaining: {total_final}")


if __name__ == "__main__":
    main()
