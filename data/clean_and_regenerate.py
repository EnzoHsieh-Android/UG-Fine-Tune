#!/usr/bin/env python3
"""
清洗訓練資料：
1. 移除 not_on_menu 相關樣本
2. 移除非法加料相關樣本
3. 添加分類訓練資料
"""

import json
import os
import random

DATA_DIR = "/Users/xiechengru/ug-finetune/data"

# ============================================================
# 1. 清洗現有資料
# ============================================================
def clean_data():
    """移除 not_on_menu 和非法加料相關樣本"""

    cleaned_samples = []
    removed_count = 0

    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.startswith("round") or not fname.endswith(".jsonl"):
            continue

        fpath = os.path.join(DATA_DIR, fname)
        file_removed = 0
        file_kept = 0

        with open(fpath, 'r') as f:
            for line in f:
                data = json.loads(line)
                should_remove = False

                # Check assistant response
                for msg in data.get("messages", []):
                    if msg["role"] == "assistant":
                        content = msg["content"]
                        # Remove not_on_menu samples
                        if '"not_on_menu": true' in content or '"not_on_menu":true' in content:
                            should_remove = True
                            break
                        # Remove illegal addon training samples
                        if '不提供加料' in content or '本店無此加料' in content:
                            should_remove = True
                            break

                    # Also check user messages for off-menu items
                    if msg["role"] == "user":
                        user_text = msg["content"]
                        off_menu_items = ["珍珠奶茶", "拿鐵", "紅茶拿鐵", "烏龍拿鐵", "抹茶拿鐵",
                                         "多多綠", "冬瓜茶", "美式咖啡", "四季春", "波霸奶茶",
                                         "綠茶", "奶綠", "冰淇淋紅茶"]
                        for item in off_menu_items:
                            if item in user_text:
                                should_remove = True
                                break

                if should_remove:
                    removed_count += 1
                    file_removed += 1
                else:
                    cleaned_samples.append(data)
                    file_kept += 1

        if file_removed > 0:
            print(f"{fname}: kept={file_kept}, removed={file_removed}")

    print(f"\n總計：保留 {len(cleaned_samples)} 筆，移除 {removed_count} 筆")
    return cleaned_samples

# ============================================================
# 2. 分類訓練資料
# ============================================================

SYSTEM_PROMPT = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。\n\n"
    "菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。\n\n"
    "純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，回傳 not_on_menu 欄位。\n\n"
    '輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}]}'
)

# 完整品項分類對照表
MENU_ITEMS = {
    # 純茶 (pure_tea) - 無尺寸
    "純茶": {
        "三窨十五茉": "pure_tea",
        "桂花輕烏龍": "pure_tea",
        "茶花紅烏龍": "pure_tea",
        "朱槿普洱紅": "pure_tea",
    },
    # 牧場直達 (fresh_milk_tea) - 有尺寸
    "鮮奶": {
        "三窨十五茉": "fresh_milk_tea",
        "桂花輕烏龍": "fresh_milk_tea",
        "紅玉紅茶": "fresh_milk_tea",
        "米香玉露菁": "fresh_milk_tea",
        "茶花烏龍": "fresh_milk_tea",
        "金杯蜜香紅": "fresh_milk_tea",
        "琥珀鐵觀音": "fresh_milk_tea",
        "朱槿普洱紅": "fresh_milk_tea",
    },
    # UG奶茶 (rich_milk_tea) - 有尺寸
    "奶茶": {
        "三窨十五茉": "rich_milk_tea",
        "桂花輕烏龍": "rich_milk_tea",
        "紅玉紅茶": "rich_milk_tea",
        "米香玉露菁": "rich_milk_tea",
        "茶花烏龍": "rich_milk_tea",
        "金杯蜜香紅": "rich_milk_tea",
        "琥珀鐵觀音": "rich_milk_tea",
        "茶花紅烏龍": "rich_milk_tea",
    },
    # 果香四溢 (fruit_tea) - 僅冷飲
    "果茶": {
        "葡柚十五茉": "fruit_tea",
        "蜜桃紅烏龍": "fruit_tea",
        "青檸桂蜜": "fruit_tea",
    },
    # 雲頂奶蓋 (cloud_velvet) - 有尺寸
    "奶蓋": {
        "茶花紅烏龍": "cloud_velvet",
    },
}

# 簡稱對照
ABBREVIATIONS = {
    "茉莉": "三窨十五茉",
    "桂花": "桂花輕烏龍",
    "鐵觀音": "琥珀鐵觀音",
    "蜜香紅": "金杯蜜香紅",
    "金杯": "金杯蜜香紅",
    "普洱": "朱槿普洱紅",
    "紅玉": "紅玉紅茶",
    "玉露": "米香玉露菁",
    "蜜桃": "蜜桃紅烏龍",
    "葡柚": "葡柚十五茉",
    "青檸": "青檸桂蜜",
}

SUGARS = ["正常糖", "少糖", "半糖", "微糖", "無糖"]
ICES = ["正常冰", "少冰", "微冰", "去冰", "熱飲"]

def make_sample(user_text, orders):
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps({"orders": orders}, ensure_ascii=False)}
        ]
    }

def gen_order(item, category, sugar=None, ice=None, size=None, qty=1):
    # 根據分類設定尺寸
    if category in ["fresh_milk_tea", "rich_milk_tea", "cloud_velvet"]:
        size = size or "M"
    else:
        size = None

    return {
        "item": item,
        "category": category,
        "size": size,
        "ice": ice,
        "sugar": sugar,
        "addon": [],
        "qty": qty,
        "note": ""
    }

def generate_category_samples():
    """生成分類訓練資料"""
    samples = []

    # ============================================================
    # 1. 全稱 + 分類詞 (明確分類)
    # ============================================================

    # 鮮奶系列
    fresh_milk_items = ["三窨十五茉", "桂花輕烏龍", "紅玉紅茶", "米香玉露菁", "茶花烏龍", "金杯蜜香紅", "琥珀鐵觀音", "朱槿普洱紅"]
    for item in fresh_milk_items:
        sugar = random.choice(SUGARS)
        ice = random.choice(ICES)
        samples.append(make_sample(
            f"{item}鮮奶，{sugar}{ice}",
            [gen_order(item, "fresh_milk_tea", sugar=sugar, ice=ice)]
        ))

    # 奶茶系列
    rich_milk_items = ["三窨十五茉", "桂花輕烏龍", "紅玉紅茶", "米香玉露菁", "茶花烏龍", "金杯蜜香紅", "琥珀鐵觀音", "茶花紅烏龍"]
    for item in rich_milk_items:
        sugar = random.choice(SUGARS)
        ice = random.choice(ICES)
        samples.append(make_sample(
            f"{item}奶茶，{sugar}{ice}",
            [gen_order(item, "rich_milk_tea", sugar=sugar, ice=ice)]
        ))

    # 純茶系列
    pure_tea_items = ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅"]
    for item in pure_tea_items:
        sugar = random.choice(SUGARS)
        ice = random.choice(ICES)
        samples.append(make_sample(
            f"{item}純茶，{sugar}{ice}",
            [gen_order(item, "pure_tea", sugar=sugar, ice=ice)]
        ))

    # 奶蓋系列
    samples.append(make_sample(
        "茶花紅烏龍奶蓋，半糖少冰",
        [gen_order("茶花紅烏龍", "cloud_velvet", sugar="半糖", ice="少冰")]
    ))

    # 果茶系列
    fruit_items = [("葡柚十五茉", "fruit_tea"), ("蜜桃紅烏龍", "fruit_tea"), ("青檸桂蜜", "fruit_tea")]
    for item, cat in fruit_items:
        sugar = random.choice(SUGARS)
        ice = random.choice(["正常冰", "少冰", "微冰", "去冰"])  # 果茶僅冷飲
        samples.append(make_sample(
            f"{item}，{sugar}{ice}",
            [gen_order(item, cat, sugar=sugar, ice=ice)]
        ))

    # ============================================================
    # 2. 簡稱 + 分類詞 (確保簡稱對應正確)
    # ============================================================

    abbrev_category_samples = [
        ("茉莉鮮奶，半糖少冰", "三窨十五茉", "fresh_milk_tea", "半糖", "少冰"),
        ("茉莉奶茶，無糖去冰", "三窨十五茉", "rich_milk_tea", "無糖", "去冰"),
        ("桂花鮮奶，微糖微冰", "桂花輕烏龍", "fresh_milk_tea", "微糖", "微冰"),
        ("桂花奶茶，半糖少冰", "桂花輕烏龍", "rich_milk_tea", "半糖", "少冰"),
        ("鐵觀音鮮奶，無糖去冰", "琥珀鐵觀音", "fresh_milk_tea", "無糖", "去冰"),
        ("鐵觀音奶茶，半糖微冰", "琥珀鐵觀音", "rich_milk_tea", "半糖", "微冰"),
        ("蜜香紅鮮奶，微糖少冰", "金杯蜜香紅", "fresh_milk_tea", "微糖", "少冰"),
        ("金杯奶茶，無糖熱飲", "金杯蜜香紅", "rich_milk_tea", "無糖", "熱飲"),
        ("普洱鮮奶，半糖去冰", "朱槿普洱紅", "fresh_milk_tea", "半糖", "去冰"),
        ("紅玉鮮奶，無糖少冰", "紅玉紅茶", "fresh_milk_tea", "無糖", "少冰"),
        ("玉露奶茶，微糖微冰", "米香玉露菁", "rich_milk_tea", "微糖", "微冰"),
        ("蜜桃果茶，半糖少冰", "蜜桃紅烏龍", "fruit_tea", "半糖", "少冰"),
        ("葡柚果茶，無糖去冰", "葡柚十五茉", "fruit_tea", "無糖", "去冰"),
    ]

    for user_text, item, cat, sugar, ice in abbrev_category_samples:
        samples.append(make_sample(user_text, [gen_order(item, cat, sugar=sugar, ice=ice)]))

    # ============================================================
    # 3. 全稱（無分類詞）→ 預設為鮮奶茶
    # ============================================================

    default_fresh_milk = ["琥珀鐵觀音", "金杯蜜香紅", "三窨十五茉", "桂花輕烏龍", "紅玉紅茶", "米香玉露菁"]
    for item in default_fresh_milk:
        sugar = random.choice(SUGARS)
        ice = random.choice(ICES)
        samples.append(make_sample(
            f"{item}，{sugar}{ice}",
            [gen_order(item, "fresh_milk_tea", sugar=sugar, ice=ice)]
        ))
        # 帶「一杯」
        sugar = random.choice(SUGARS)
        ice = random.choice(ICES)
        samples.append(make_sample(
            f"一杯{item}，{sugar}{ice}",
            [gen_order(item, "fresh_milk_tea", sugar=sugar, ice=ice)]
        ))

    # ============================================================
    # 4. 簡稱（無分類詞）→ 預設為鮮奶茶
    # ============================================================

    abbrev_default_samples = [
        ("鐵觀音，半糖少冰", "琥珀鐵觀音", "fresh_milk_tea", "半糖", "少冰"),
        ("茉莉，無糖去冰", "三窨十五茉", "fresh_milk_tea", "無糖", "去冰"),
        ("桂花，微糖微冰", "桂花輕烏龍", "fresh_milk_tea", "微糖", "微冰"),
        ("蜜香紅，半糖少冰", "金杯蜜香紅", "fresh_milk_tea", "半糖", "少冰"),
        ("金杯，無糖去冰", "金杯蜜香紅", "fresh_milk_tea", "無糖", "去冰"),
        ("普洱，半糖熱飲", "朱槿普洱紅", "fresh_milk_tea", "半糖", "熱飲"),
        ("紅玉，微糖少冰", "紅玉紅茶", "fresh_milk_tea", "微糖", "少冰"),
        ("玉露，無糖微冰", "米香玉露菁", "fresh_milk_tea", "無糖", "微冰"),
    ]

    for user_text, item, cat, sugar, ice in abbrev_default_samples:
        samples.append(make_sample(user_text, [gen_order(item, cat, sugar=sugar, ice=ice)]))

    # ============================================================
    # 5. 混合點單（確保分類正確）
    # ============================================================

    samples.append(make_sample(
        "一杯鐵觀音鮮奶半糖少冰，一杯桂花奶茶無糖去冰",
        [
            gen_order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="少冰"),
            gen_order("桂花輕烏龍", "rich_milk_tea", sugar="無糖", ice="去冰"),
        ]
    ))

    samples.append(make_sample(
        "茉莉鮮奶微糖微冰，金杯奶茶無糖去冰",
        [
            gen_order("三窨十五茉", "fresh_milk_tea", sugar="微糖", ice="微冰"),
            gen_order("金杯蜜香紅", "rich_milk_tea", sugar="無糖", ice="去冰"),
        ]
    ))

    samples.append(make_sample(
        "琥珀鐵觀音半糖少冰，蜜桃紅烏龍無糖去冰",
        [
            gen_order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="少冰"),
            gen_order("蜜桃紅烏龍", "fruit_tea", sugar="無糖", ice="去冰"),
        ]
    ))

    samples.append(make_sample(
        "三窨十五茉純茶無糖去冰，桂花輕烏龍鮮奶半糖少冰",
        [
            gen_order("三窨十五茉", "pure_tea", sugar="無糖", ice="去冰"),
            gen_order("桂花輕烏龍", "fresh_milk_tea", sugar="半糖", ice="少冰"),
        ]
    ))

    # ============================================================
    # 6. 多杯同品（確保分類一致）
    # ============================================================

    samples.append(make_sample(
        "兩杯琥珀鐵觀音，半糖少冰",
        [gen_order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖", ice="少冰", qty=2)]
    ))

    samples.append(make_sample(
        "三杯金杯蜜香紅鮮奶，都無糖去冰",
        [gen_order("金杯蜜香紅", "fresh_milk_tea", sugar="無糖", ice="去冰", qty=3)]
    ))

    samples.append(make_sample(
        "兩杯茉莉奶茶，一杯半糖一杯無糖，都少冰",
        [
            gen_order("三窨十五茉", "rich_milk_tea", sugar="半糖", ice="少冰"),
            gen_order("三窨十五茉", "rich_milk_tea", sugar="無糖", ice="少冰"),
        ]
    ))

    print(f"生成分類訓練樣本: {len(samples)} 筆")
    return samples

# ============================================================
# 主程式
# ============================================================

if __name__ == "__main__":
    # 1. 清洗現有資料
    print("=== 清洗現有資料 ===")
    cleaned = clean_data()

    # 2. 生成分類訓練資料
    print("\n=== 生成分類訓練資料 ===")
    category_samples = generate_category_samples()

    # 3. 合併
    all_samples = cleaned + category_samples
    random.shuffle(all_samples)

    print(f"\n=== 總計 ===")
    print(f"清洗後樣本: {len(cleaned)}")
    print(f"新增分類樣本: {len(category_samples)}")
    print(f"合併後總數: {len(all_samples)}")

    # 4. 儲存
    train_path = os.path.join(DATA_DIR, "train.jsonl")
    with open(train_path, "w", encoding="utf-8") as f:
        for s in all_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"\n已儲存到 {train_path}")
