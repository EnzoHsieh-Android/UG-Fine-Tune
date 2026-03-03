#!/usr/bin/env python3
"""Round 28: Generate cross-category training data for same-item orders."""

import json
import random

# Extract system prompt from existing training data
with open('train.jsonl') as f:
    d = json.loads(f.readline())
    SYSTEM_PROMPT = d['messages'][0]['content']


def make_order(item, category, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
    return {
        "item": item,
        "category": category,
        "size": size,
        "ice": ice,
        "sugar": sugar,
        "addon": addon or [],
        "qty": qty,
        "note": note,
    }


def make_example(user_text, orders, preferences=None, recommendations=None):
    asst = {
        "orders": orders,
        "preferences": preferences or {},
        "recommendations": recommendations or [],
    }
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(asst, ensure_ascii=False)},
        ]
    }


examples = []

# ============================================================
# 3a. 鮮奶茶 vs 奶茶 (fresh_milk_tea vs rich_milk_tea) ~10 筆
# ============================================================

# 1. 琥珀鐵觀音: 鮮奶 vs 奶精
examples.append(make_example(
    "兩杯琥珀鐵觀音，一杯鮮奶的半糖去冰，一杯奶精的無糖少冰",
    [
        make_order("琥珀鐵觀音", "fresh_milk_tea", ice="去冰", sugar="半糖"),
        make_order("琥珀鐵觀音", "rich_milk_tea", ice="少冰", sugar="無糖"),
    ]
))

# 2. 琥珀鐵觀音: 鮮奶茶 vs 奶茶 with size
examples.append(make_example(
    "一杯琥珀鐵觀音鮮奶茶大杯半糖去冰，再一杯琥珀鐵觀音奶茶無糖少冰",
    [
        make_order("琥珀鐵觀音", "fresh_milk_tea", size="L", ice="去冰", sugar="半糖"),
        make_order("琥珀鐵觀音", "rich_milk_tea", ice="少冰", sugar="無糖"),
    ]
))

# 3. 金杯蜜香紅: 鮮奶茶 vs 奶茶
examples.append(make_example(
    "一杯金杯蜜香紅鮮奶茶大杯半糖，再一杯金杯蜜香紅奶茶微糖",
    [
        make_order("金杯蜜香紅", "fresh_milk_tea", size="L", sugar="半糖"),
        make_order("金杯蜜香紅", "rich_milk_tea", sugar="微糖"),
    ]
))

# 4. 三窨十五茉: 加鮮奶 vs 一般奶茶
examples.append(make_example(
    "三窨十五茉加鮮奶去冰，再一杯一般奶茶的半糖",
    [
        make_order("三窨十五茉", "fresh_milk_tea", ice="去冰"),
        make_order("三窨十五茉", "rich_milk_tea", sugar="半糖"),
    ]
))

# 5. 桂花輕烏龍: 鮮奶 vs 奶茶 with different specs
examples.append(make_example(
    "桂花輕烏龍鮮奶的中杯去冰無糖，再一杯桂花輕烏龍奶茶大杯半糖少冰",
    [
        make_order("桂花輕烏龍", "fresh_milk_tea", size="M", ice="去冰", sugar="無糖"),
        make_order("桂花輕烏龍", "rich_milk_tea", size="L", ice="少冰", sugar="半糖"),
    ]
))

# 6. 茶花紅烏龍: 鮮奶茶 vs UG奶茶
examples.append(make_example(
    "茶花紅烏龍鮮奶茶中杯微糖去冰，再來一杯茶花紅烏龍UG奶茶半糖少冰",
    [
        make_order("茶花紅烏龍", "fresh_milk_tea", size="M", ice="去冰", sugar="微糖"),
        make_order("茶花紅烏龍", "rich_milk_tea", ice="少冰", sugar="半糖"),
    ]
))

# 7. 金杯蜜香紅: 加鮮奶 vs 奶精的 with addon
examples.append(make_example(
    "金杯蜜香紅加鮮奶大杯無糖去冰加茶凍，再一杯奶精的微糖少冰",
    [
        make_order("金杯蜜香紅", "fresh_milk_tea", size="L", ice="去冰", sugar="無糖", addon=["紅烏龍茶凍"]),
        make_order("金杯蜜香紅", "rich_milk_tea", ice="少冰", sugar="微糖"),
    ]
))

# 8. 朱槿普洱紅: 鮮奶 vs 奶茶
examples.append(make_example(
    "朱槿普洱紅鮮奶中杯半糖去冰，再一杯朱槿普洱紅奶茶大杯無糖少冰",
    [
        make_order("朱槿普洱紅", "fresh_milk_tea", size="M", ice="去冰", sugar="半糖"),
        make_order("朱槿普洱紅", "rich_milk_tea", size="L", ice="少冰", sugar="無糖"),
    ]
))

# 9. 米香玉露菁: 鮮奶茶 vs 奶茶
examples.append(make_example(
    "米香玉露菁鮮奶茶中杯微糖微冰，再一杯米香玉露菁奶茶半糖去冰",
    [
        make_order("米香玉露菁", "fresh_milk_tea", size="M", ice="微冰", sugar="微糖"),
        make_order("米香玉露菁", "rich_milk_tea", ice="去冰", sugar="半糖"),
    ]
))

# 10. 琥珀鐵觀音: 鮮奶的 vs 奶茶 with size both specified
examples.append(make_example(
    "兩杯琥珀鐵觀音，鮮奶的大杯無糖去冰，奶茶的中杯半糖少冰",
    [
        make_order("琥珀鐵觀音", "fresh_milk_tea", size="L", ice="去冰", sugar="無糖"),
        make_order("琥珀鐵觀音", "rich_milk_tea", size="M", ice="少冰", sugar="半糖"),
    ]
))

# ============================================================
# 3b. 純茶 vs 鮮奶茶 (pure_tea vs fresh_milk_tea) ~6 筆
# ============================================================

# 11. 桂花輕烏龍: 純茶 + 鮮奶
examples.append(make_example(
    "一杯桂花輕烏龍純茶無糖，再一杯加鮮奶的半糖去冰大杯",
    [
        make_order("桂花輕烏龍", "pure_tea", sugar="無糖"),
        make_order("桂花輕烏龍", "fresh_milk_tea", size="L", ice="去冰", sugar="半糖"),
    ]
))

# 12. 茶花紅烏龍: 茶就好 + 鮮奶的
examples.append(make_example(
    "茶花紅烏龍茶就好不加奶無糖，另外要一杯鮮奶的中杯少冰微糖",
    [
        make_order("茶花紅烏龍", "pure_tea", sugar="無糖"),
        make_order("茶花紅烏龍", "fresh_milk_tea", size="M", ice="少冰", sugar="微糖"),
    ]
))

# 13. 朱槿普洱紅: 純茶 + 加鮮奶
examples.append(make_example(
    "朱槿普洱紅純茶微糖去冰，再一杯朱槿普洱紅加鮮奶大杯半糖",
    [
        make_order("朱槿普洱紅", "pure_tea", ice="去冰", sugar="微糖"),
        make_order("朱槿普洱紅", "fresh_milk_tea", size="L", sugar="半糖"),
    ]
))

# 14. 米香玉露菁: 不加奶 + 鮮奶茶
examples.append(make_example(
    "米香玉露菁不加奶無糖去冰，再一杯米香玉露菁鮮奶茶中杯半糖",
    [
        make_order("米香玉露菁", "pure_tea", ice="去冰", sugar="無糖"),
        make_order("米香玉露菁", "fresh_milk_tea", size="M", sugar="半糖"),
    ]
))

# 15. 三窨十五茉: 純茶 + 鮮奶
examples.append(make_example(
    "一杯三窨十五茉純茶無糖去冰，再來一杯三窨十五茉鮮奶大杯微糖",
    [
        make_order("三窨十五茉", "pure_tea", ice="去冰", sugar="無糖"),
        make_order("三窨十五茉", "fresh_milk_tea", size="L", sugar="微糖"),
    ]
))

# 16. 茶花紅烏龍: 純茶 + 鮮奶茶 with different sugar/ice
examples.append(make_example(
    "兩杯茶花紅烏龍，一杯純茶半糖去冰，一杯鮮奶茶大杯無糖少冰",
    [
        make_order("茶花紅烏龍", "pure_tea", ice="去冰", sugar="半糖"),
        make_order("茶花紅烏龍", "fresh_milk_tea", size="L", ice="少冰", sugar="無糖"),
    ]
))

# ============================================================
# 3c. 純茶/奶茶 vs 奶蓋 (cloud_velvet) ~6 筆
# ============================================================

# 17. 茶花紅烏龍: 奶蓋 + 奶茶
examples.append(make_example(
    "茶花紅烏龍奶蓋一杯無糖，再來一杯奶茶的半糖少冰",
    [
        make_order("茶花紅烏龍", "cloud_velvet", sugar="無糖"),
        make_order("茶花紅烏龍", "rich_milk_tea", ice="少冰", sugar="半糖"),
    ]
))

# 18. 桂花輕烏龍: 純茶 + 奶蓋
examples.append(make_example(
    "一杯桂花輕烏龍純茶無糖，再一杯加奶蓋半糖",
    [
        make_order("桂花輕烏龍", "pure_tea", sugar="無糖"),
        make_order("桂花輕烏龍", "cloud_velvet", sugar="半糖"),
    ]
))

# 19. 茶花紅烏龍: 鮮奶 + 奶蓋
examples.append(make_example(
    "茶花紅烏龍鮮奶的大杯半糖去冰，再一杯茶花紅烏龍奶蓋無糖",
    [
        make_order("茶花紅烏龍", "fresh_milk_tea", size="L", ice="去冰", sugar="半糖"),
        make_order("茶花紅烏龍", "cloud_velvet", sugar="無糖"),
    ]
))

# 20. 桂花輕烏龍: 奶蓋 + 鮮奶
examples.append(make_example(
    "桂花輕烏龍奶蓋一杯微糖，再來一杯桂花輕烏龍鮮奶大杯去冰半糖",
    [
        make_order("桂花輕烏龍", "cloud_velvet", sugar="微糖"),
        make_order("桂花輕烏龍", "fresh_milk_tea", size="L", ice="去冰", sugar="半糖"),
    ]
))

# 21. 桂花輕烏龍: 奶茶 + 奶蓋
examples.append(make_example(
    "桂花輕烏龍奶茶中杯半糖少冰，再一杯桂花輕烏龍奶蓋無糖",
    [
        make_order("桂花輕烏龍", "rich_milk_tea", size="M", ice="少冰", sugar="半糖"),
        make_order("桂花輕烏龍", "cloud_velvet", sugar="無糖"),
    ]
))

# 22. 茶花紅烏龍: 純茶 + 奶蓋
examples.append(make_example(
    "一杯茶花紅烏龍純茶去冰無糖，再一杯茶花紅烏龍加奶蓋微糖",
    [
        make_order("茶花紅烏龍", "pure_tea", ice="去冰", sugar="無糖"),
        make_order("茶花紅烏龍", "cloud_velvet", sugar="微糖"),
    ]
))

# ============================================================
# 3d. 同品項 3 杯跨 3+ 分類 ~4 筆
# ============================================================

# 23. 桂花輕烏龍 x3: 純茶 + 鮮奶 + 奶蓋
examples.append(make_example(
    "桂花輕烏龍純茶一杯無糖、鮮奶的一杯大杯半糖去冰、再一杯奶蓋微糖",
    [
        make_order("桂花輕烏龍", "pure_tea", sugar="無糖"),
        make_order("桂花輕烏龍", "fresh_milk_tea", size="L", ice="去冰", sugar="半糖"),
        make_order("桂花輕烏龍", "cloud_velvet", sugar="微糖"),
    ]
))

# 24. 茶花紅烏龍 x3: 純茶 + 奶精 + 奶蓋
examples.append(make_example(
    "三杯茶花紅烏龍，一杯純茶無糖、一杯奶精的半糖少冰、一杯奶蓋微糖",
    [
        make_order("茶花紅烏龍", "pure_tea", sugar="無糖"),
        make_order("茶花紅烏龍", "rich_milk_tea", ice="少冰", sugar="半糖"),
        make_order("茶花紅烏龍", "cloud_velvet", sugar="微糖"),
    ]
))

# 25. 桂花輕烏龍 x4: 全部分類
examples.append(make_example(
    "四杯桂花輕烏龍，純茶無糖去冰、鮮奶的中杯半糖少冰、奶茶大杯微糖微冰、奶蓋一分糖",
    [
        make_order("桂花輕烏龍", "pure_tea", ice="去冰", sugar="無糖"),
        make_order("桂花輕烏龍", "fresh_milk_tea", size="M", ice="少冰", sugar="半糖"),
        make_order("桂花輕烏龍", "rich_milk_tea", size="L", ice="微冰", sugar="微糖"),
        make_order("桂花輕烏龍", "cloud_velvet", sugar="一分糖"),
    ]
))

# 26. 茶花紅烏龍 x4: 全部分類
examples.append(make_example(
    "茶花紅烏龍我要四杯，純茶半糖、鮮奶的大杯去冰無糖、UG奶茶中杯微糖少冰、奶蓋半糖",
    [
        make_order("茶花紅烏龍", "pure_tea", sugar="半糖"),
        make_order("茶花紅烏龍", "fresh_milk_tea", size="L", ice="去冰", sugar="無糖"),
        make_order("茶花紅烏龍", "rich_milk_tea", size="M", ice="少冰", sugar="微糖"),
        make_order("茶花紅烏龍", "cloud_velvet", sugar="半糖"),
    ]
))

# ============================================================
# 3e. 易混淆品項名共存 ~6 筆
# ============================================================

# 27. 蜜桃紅烏龍(fruit_tea) + 茶花紅烏龍(rich_milk_tea)
examples.append(make_example(
    "一杯蜜桃紅烏龍，再一杯茶花紅烏龍奶茶半糖",
    [
        make_order("蜜桃紅烏龍", "fruit_tea"),
        make_order("茶花紅烏龍", "rich_milk_tea", sugar="半糖"),
    ]
))

# 28. 葡柚十五茉(fruit_tea) + 三窨十五茉(fresh_milk_tea)
examples.append(make_example(
    "葡柚十五茉一杯，還要一杯三窨十五茉鮮奶去冰",
    [
        make_order("葡柚十五茉", "fruit_tea"),
        make_order("三窨十五茉", "fresh_milk_tea", ice="去冰"),
    ]
))

# 29. 青檸桂蜜(fruit_tea) + 桂花輕烏龍(pure_tea)
examples.append(make_example(
    "青檸桂蜜一杯，再來一杯桂花輕烏龍純茶無糖",
    [
        make_order("青檸桂蜜", "fruit_tea"),
        make_order("桂花輕烏龍", "pure_tea", sugar="無糖"),
    ]
))

# 30. 蜜桃紅烏龍 + 茶花紅烏龍奶蓋
examples.append(make_example(
    "蜜桃紅烏龍跟茶花紅烏龍奶蓋各一杯",
    [
        make_order("蜜桃紅烏龍", "fruit_tea"),
        make_order("茶花紅烏龍", "cloud_velvet"),
    ]
))

# 31. 葡柚十五茉 + 三窨十五茉奶茶
examples.append(make_example(
    "葡柚十五茉半糖，再來一杯三窨十五茉奶茶微糖去冰",
    [
        make_order("葡柚十五茉", "fruit_tea", sugar="半糖"),
        make_order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="微糖"),
    ]
))

# 32. 蜜桃紅烏龍 + 茶花紅烏龍鮮奶 + 青檸桂蜜
examples.append(make_example(
    "蜜桃紅烏龍少冰、茶花紅烏龍鮮奶大杯半糖去冰、青檸桂蜜微糖",
    [
        make_order("蜜桃紅烏龍", "fruit_tea", ice="少冰"),
        make_order("茶花紅烏龍", "fresh_milk_tea", size="L", ice="去冰", sugar="半糖"),
        make_order("青檸桂蜜", "fruit_tea", sugar="微糖"),
    ]
))

# ============================================================
# 3f. 多輪對話版（分號分隔）~10 筆
# ============================================================

# 33. 琥珀鐵觀音 cross-category multi-turn
examples.append(make_example(
    "一杯琥珀鐵觀音鮮奶茶去冰半糖;再一杯琥珀鐵觀音奶精的無糖少冰",
    [
        make_order("琥珀鐵觀音", "fresh_milk_tea", ice="去冰", sugar="半糖"),
        make_order("琥珀鐵觀音", "rich_milk_tea", ice="少冰", sugar="無糖"),
    ]
))

# 34. 茶花紅烏龍 pure_tea then fresh_milk_tea
examples.append(make_example(
    "茶花紅烏龍純茶無糖;再來一杯茶花紅烏龍加鮮奶中杯半糖少冰",
    [
        make_order("茶花紅烏龍", "pure_tea", sugar="無糖"),
        make_order("茶花紅烏龍", "fresh_milk_tea", size="M", ice="少冰", sugar="半糖"),
    ]
))

# 35. 蜜桃紅烏龍 then 茶花紅烏龍奶蓋
examples.append(make_example(
    "來杯蜜桃紅烏龍;再加一杯茶花紅烏龍奶蓋微糖",
    [
        make_order("蜜桃紅烏龍", "fruit_tea"),
        make_order("茶花紅烏龍", "cloud_velvet", sugar="微糖"),
    ]
))

# 36. 桂花輕烏龍 cloud_velvet then fresh_milk_tea
examples.append(make_example(
    "桂花輕烏龍奶蓋一杯半糖;再一杯桂花輕烏龍鮮奶的大杯去冰無糖",
    [
        make_order("桂花輕烏龍", "cloud_velvet", sugar="半糖"),
        make_order("桂花輕烏龍", "fresh_milk_tea", size="L", ice="去冰", sugar="無糖"),
    ]
))

# 37. 三窨十五茉 fresh_milk_tea then 葡柚十五茉 fruit_tea
examples.append(make_example(
    "三窨十五茉鮮奶茶中杯半糖去冰;再一杯葡柚十五茉",
    [
        make_order("三窨十五茉", "fresh_milk_tea", size="M", ice="去冰", sugar="半糖"),
        make_order("葡柚十五茉", "fruit_tea"),
    ]
))

# 38. 金杯蜜香紅 fresh_milk_tea then rich_milk_tea (multi-turn with modify)
examples.append(make_example(
    "金杯蜜香紅鮮奶大杯半糖少冰;再一杯金杯蜜香紅奶茶無糖去冰;第二杯改大杯",
    [
        make_order("金杯蜜香紅", "fresh_milk_tea", size="L", ice="少冰", sugar="半糖"),
        make_order("金杯蜜香紅", "rich_milk_tea", size="L", ice="去冰", sugar="無糖"),
    ]
))

# 39. 茶花紅烏龍 rich_milk_tea then cloud_velvet (multi-turn)
examples.append(make_example(
    "茶花紅烏龍奶茶中杯微糖少冰;再一杯茶花紅烏龍奶蓋無糖",
    [
        make_order("茶花紅烏龍", "rich_milk_tea", size="M", ice="少冰", sugar="微糖"),
        make_order("茶花紅烏龍", "cloud_velvet", sugar="無糖"),
    ]
))

# 40. 桂花輕烏龍 pure_tea then rich_milk_tea (multi-turn)
examples.append(make_example(
    "桂花輕烏龍純茶半糖去冰;再來一杯桂花輕烏龍奶茶大杯無糖少冰",
    [
        make_order("桂花輕烏龍", "pure_tea", ice="去冰", sugar="半糖"),
        make_order("桂花輕烏龍", "rich_milk_tea", size="L", ice="少冰", sugar="無糖"),
    ]
))

# 41. 朱槿普洱紅 pure_tea then fresh_milk_tea (multi-turn)
examples.append(make_example(
    "朱槿普洱紅純茶無糖;再一杯朱槿普洱紅鮮奶中杯半糖去冰",
    [
        make_order("朱槿普洱紅", "pure_tea", sugar="無糖"),
        make_order("朱槿普洱紅", "fresh_milk_tea", size="M", ice="去冰", sugar="半糖"),
    ]
))

# 42. 青檸桂蜜 + 桂花輕烏龍奶蓋 (confusable, multi-turn)
examples.append(make_example(
    "青檸桂蜜半糖;再來一杯桂花輕烏龍奶蓋無糖",
    [
        make_order("青檸桂蜜", "fruit_tea", sugar="半糖"),
        make_order("桂花輕烏龍", "cloud_velvet", sugar="無糖"),
    ]
))

# ============================================================
# 3g. Anchor 樣本（防回歸）~2 筆
# ============================================================

# 43. 不同品項多杯（確認不退化）
examples.append(make_example(
    "一杯琥珀鐵觀音鮮奶大杯半糖去冰，一杯三窨十五茉純茶無糖，一杯蜜桃紅烏龍少冰",
    [
        make_order("琥珀鐵觀音", "fresh_milk_tea", size="L", ice="去冰", sugar="半糖"),
        make_order("三窨十五茉", "pure_tea", sugar="無糖"),
        make_order("蜜桃紅烏龍", "fruit_tea", ice="少冰"),
    ]
))

# 44. 單品項正常點餐
examples.append(make_example(
    "桂花輕烏龍鮮奶大杯微糖去冰加茶凍",
    [
        make_order("桂花輕烏龍", "fresh_milk_tea", size="L", ice="去冰", sugar="微糖", addon=["紅烏龍茶凍"]),
    ]
))

print(f"Total examples generated: {len(examples)}")

# Split: ~35 train + ~9 valid
random.seed(28)
random.shuffle(examples)
n_valid = 9
valid_examples = examples[:n_valid]
train_examples = examples[n_valid:]

print(f"Train: {len(train_examples)}, Valid: {len(valid_examples)}")

# Write to round28_cross_category files
with open('round28_cross_category.jsonl', 'w') as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')

# Append to train.jsonl and valid.jsonl
with open('train.jsonl', 'a') as f:
    for ex in train_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')

with open('valid.jsonl', 'a') as f:
    for ex in valid_examples:
        f.write(json.dumps(ex, ensure_ascii=False) + '\n')

print("Appended to train.jsonl and valid.jsonl")

# Verify counts
with open('train.jsonl') as f:
    train_count = sum(1 for _ in f)
with open('valid.jsonl') as f:
    valid_count = sum(1 for _ in f)
print(f"Final counts - train: {train_count}, valid: {valid_count}, total: {train_count + valid_count}")
