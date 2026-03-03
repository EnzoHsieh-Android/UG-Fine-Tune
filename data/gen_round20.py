#!/usr/bin/env python3
"""
Round 20: 修復四個失敗案例 + 防回歸錨定樣本

問題分析：
1. 加料模式：「品項加茶凍」(無分類詞) → 模型輸出奇怪連接
2. 多品項：「A和B」模式 → B 被放到 note
3. 同品不同規格：「品項甜度A、品項甜度B」→ sugar 變 array

策略：
- 50% 新模式修復 (25 筆)
- 50% 錨定樣本防回歸 (25 筆)
"""

import json
import random

# System prompt (same as existing training data)
SYSTEM_PROMPT = """你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。

菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。

純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。
加料：紅烏龍茶凍(+15)、燕麥粒(+15)。
甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。
未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。
若品項不在菜單上，回傳 not_on_menu 欄位。

輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}]}"""

def make_sample(user_content, orders):
    """Generate a training sample"""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": json.dumps({"orders": orders}, ensure_ascii=False)}
        ]
    }

def generate_samples():
    samples = []

    # ============================================================
    # Part 1: 修復加料模式 (品項加茶凍，無分類詞) - 10 筆
    # ============================================================

    # 單純加料
    samples.append(make_sample(
        "琥珀鐵觀音加紅烏龍茶凍",
        [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "朱槿普洱紅加紅烏龍茶凍",
        [{"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "三窨十五茉加燕麥粒",
        [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["燕麥粒"], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "金杯蜜香紅加茶凍",
        [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "桂花輕烏龍加燕麥粒",
        [{"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["燕麥粒"], "qty": 1, "note": ""}]
    ))

    # 加料 + 雙加料
    samples.append(make_sample(
        "朱槿普洱紅加紅烏龍茶凍和燕麥粒",
        [{"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "琥珀鐵觀音加茶凍跟燕麥粒",
        [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "note": ""}]
    ))

    # 加料 + 選項
    samples.append(make_sample(
        "琥珀鐵觀音半糖加茶凍",
        [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "半糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "三窨十五茉無糖去冰加燕麥粒",
        [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": "無糖", "addon": ["燕麥粒"], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "金杯蜜香紅微糖少冰加茶凍和燕麥粒",
        [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "微糖", "addon": ["紅烏龍茶凍", "燕麥粒"], "qty": 1, "note": ""}]
    ))

    # ============================================================
    # Part 2: 修復多品項「和」模式 - 8 筆
    # ============================================================

    samples.append(make_sample(
        "三窨十五茉和金杯蜜香紅",
        [
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""},
            {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "琥珀鐵觀音和桂花輕烏龍",
        [
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""},
            {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "朱槿普洱紅和蜜桃紅烏龍",
        [
            {"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""},
            {"item": "蜜桃紅烏龍", "category": "fruit_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # 「和」+ 選項
    samples.append(make_sample(
        "三窨十五茉半糖和金杯蜜香紅無糖",
        [
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # 「和」+ 修改
    samples.append(make_sample(
        "三窨十五茉和金杯蜜香紅，茉莉改半糖",
        [
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "琥珀鐵觀音和桂花輕烏龍，鐵觀音加茶凍",
        [
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""},
            {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # 「和」+ 取消
    samples.append(make_sample(
        "三窨十五茉和金杯蜜香紅，金杯不要了",
        [
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "琥珀鐵觀音和桂花，鐵觀音取消",
        [
            {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # ============================================================
    # Part 3: 修復同品項不同規格 (拆成多筆訂單) - 7 筆
    # ============================================================

    samples.append(make_sample(
        "三窨十五茉半糖、三窨十五茉無糖",
        [
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "金杯蜜香紅半糖少冰、金杯蜜香紅無糖去冰",
        [
            {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "琥珀鐵觀音微糖、琥珀鐵觀音半糖、琥珀鐵觀音無糖",
        [
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "微糖", "addon": [], "qty": 1, "note": ""},
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "桂花輕烏龍正常冰、桂花輕烏龍去冰",
        [
            {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "正常冰", "sugar": None, "addon": [], "qty": 1, "note": ""},
            {"item": "桂花輕烏龍", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # 混合：同品不同規格 + 縮寫
    samples.append(make_sample(
        "茉莉半糖、茉莉無糖",
        [
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "鐵觀音鮮奶半糖少冰、鐵觀音鮮奶無糖去冰",
        [
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "普洱熱的、普洱去冰",
        [
            {"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": "熱飲", "sugar": None, "addon": [], "qty": 1, "note": ""},
            {"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": "去冰", "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # ============================================================
    # Part 4: 錨定樣本 - 防止回歸 (25 筆)
    # 從各輪訓練中挑選代表性場景
    # ============================================================

    # --- 基礎點單 (R3) ---
    samples.append(make_sample(
        "三窨十五茉鮮奶半糖少冰",
        [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "大杯琥珀鐵觀音奶茶無糖去冰",
        [{"item": "琥珀鐵觀音", "category": "rich_milk_tea", "size": "L", "ice": "去冰", "sugar": "無糖", "addon": [], "qty": 1, "note": ""}]
    ))

    # --- 多輪對話 (R4) - 保留顧客前缀格式 ---
    samples.append(make_sample(
        "顧客：三窨十五茉鮮奶\n顧客：半糖少冰\n顧客：大杯",
        [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "L", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""}]
    ))

    # --- 修改 (R5) - 单句格式 ---
    samples.append(make_sample(
        "三窨十五茉鮮奶半糖，改無糖",
        [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "桂花輕烏龍奶茶半糖少冰，改大杯",
        [{"item": "桂花輕烏龍", "category": "rich_milk_tea", "size": "L", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""}]
    ))

    # --- 閒聊 (R6/R7) ---
    samples.append(make_sample(
        "廁所在哪裡",
        []
    ))

    samples.append(make_sample(
        "你們幾點關門？那我點一杯茉莉好了",
        [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}]
    ))

    # --- 縮寫 (R9) ---
    samples.append(make_sample(
        "茉莉半糖少冰",
        [{"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "鐵觀音鮮奶微糖去冰",
        [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "微糖", "addon": [], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "普洱熱的無糖",
        [{"item": "朱槿普洱紅", "category": "pure_tea", "size": None, "ice": "熱飲", "sugar": "無糖", "addon": [], "qty": 1, "note": ""}]
    ))

    # --- 取消 (R10/R11) - 单句格式 ---
    samples.append(make_sample(
        "三窨十五茉鮮奶和桂花輕烏龍奶茶，茉莉不要了",
        [{"item": "桂花輕烏龍", "category": "rich_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "兩杯鐵觀音鮮奶，第一杯取消",
        [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}]
    ))

    # --- 菜單外 (R14) ---
    samples.append(make_sample(
        "珍珠奶茶半糖少冰",
        [{"item": "珍珠奶茶", "category": "not_on_menu", "size": None, "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "not_on_menu": True, "note": ""}]
    ))

    samples.append(make_sample(
        "紅茶拿鐵和三窨十五茉",
        [
            {"item": "紅茶拿鐵", "category": "not_on_menu", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "not_on_menu": True, "note": ""},
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # --- 同品不同規格 + qty (R15/R17) ---
    samples.append(make_sample(
        "兩杯鐵觀音鮮奶，一杯半糖一杯無糖",
        [
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "M", "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "三杯茉莉，兩杯半糖一杯無糖",
        [
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "半糖", "addon": [], "qty": 2, "note": ""},
            {"item": "三窨十五茉", "category": "pure_tea", "size": None, "ice": None, "sugar": "無糖", "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # --- 加料 (正常格式，帶分類詞) - 单句格式 ---
    samples.append(make_sample(
        "三窨十五茉鮮奶半糖少冰加茶凍",
        [{"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "琥珀鐵觀音奶茶無糖去冰加燕麥粒",
        [{"item": "琥珀鐵觀音", "category": "rich_milk_tea", "size": "M", "ice": "去冰", "sugar": "無糖", "addon": ["燕麥粒"], "qty": 1, "note": ""}]
    ))

    # --- 複雜組合 - 单句格式 ---
    samples.append(make_sample(
        "三窨十五茉鮮奶半糖少冰和金杯蜜香紅奶茶無糖去冰加茶凍",
        [
            {"item": "三窨十五茉", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "金杯蜜香紅", "category": "rich_milk_tea", "size": "M", "ice": "去冰", "sugar": "無糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}
        ]
    ))

    samples.append(make_sample(
        "兩杯桂花輕烏龍鮮奶，一杯半糖少冰、一杯無糖去冰加茶凍",
        [
            {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 1, "note": ""},
            {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "size": "M", "ice": "去冰", "sugar": "無糖", "addon": ["紅烏龍茶凍"], "qty": 1, "note": ""}
        ]
    ))

    # --- 果茶 ---
    samples.append(make_sample(
        "蜜桃紅烏龍少冰",
        [{"item": "蜜桃紅烏龍", "category": "fruit_tea", "size": None, "ice": "少冰", "sugar": None, "addon": [], "qty": 1, "note": ""}]
    ))

    samples.append(make_sample(
        "青檸桂蜜和葡柚十五茉",
        [
            {"item": "青檸桂蜜", "category": "fruit_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""},
            {"item": "葡柚十五茉", "category": "fruit_tea", "size": None, "ice": None, "sugar": None, "addon": [], "qty": 1, "note": ""}
        ]
    ))

    # --- 奶蓋 ---
    samples.append(make_sample(
        "茶花紅烏龍奶蓋微糖少冰",
        [{"item": "茶花紅烏龍", "category": "cloud_velvet", "size": None, "ice": "少冰", "sugar": "微糖", "addon": [], "qty": 1, "note": ""}]
    ))

    return samples


def main():
    samples = generate_samples()

    # Shuffle samples
    random.seed(42)
    random.shuffle(samples)

    # Write to file
    output_file = "/Users/xiechengru/ug-finetune/data/round20.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(f"Generated {len(samples)} samples")
    print(f"Output: {output_file}")

    # Count by category
    addon_fix = 10
    multi_item_fix = 8
    same_item_fix = 7
    anchor = len(samples) - addon_fix - multi_item_fix - same_item_fix

    print(f"\n=== 樣本分布 ===")
    print(f"加料模式修復: {addon_fix}")
    print(f"多品項「和」修復: {multi_item_fix}")
    print(f"同品不同規格修復: {same_item_fix}")
    print(f"錨定防回歸: {anchor}")


if __name__ == "__main__":
    main()
