"""Round 28: 補強低頻品項×分類、STT 錯字、熱飲、少糖/正常糖/正常冰/Size M。

缺口分析：
- 茶花紅烏龍×rich_milk_tea (7→), 米香玉露菁×rich_milk_tea (4→), 朱槿普洱紅×rich_milk_tea (9→)
- 青檸桂蜜 (19 total), 葡柚十五茉 (18 total), 米香玉露菁×pure_tea (9)
- STT 錯字 (13→), 熱飲 (21→)
- 少糖 (32), 正常糖 (49), 正常冰 (36), Size M (41) 偏少
"""
import json

system_prompt = """你是 No.315 Unique Green 的點單助手。根據顧客的自然語言輸出 JSON。

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
未指定的甜度、冰量、尺寸設為 null。未指定分類時 category 設 null。

輸出格式（必須為合法 JSON）：
{"orders":[],"preferences":{},"recommendations":[]}
- 顧客點餐：填入 orders，每筆格式 {"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}
- 顧客想要推薦：填入 preferences（口味/溫度/場景/排除，無明確偏好時為空物件）與 recommendations（僅推薦 1 項），格式 {"item":"品名","category":"分類","reason":"推薦理由"}
- 點餐同時想推薦：orders 和 recommendations 同時填入，preferences 一併填入
- 閒聊或無法辨識：三個欄位皆為空
- 若最後一段已做出點餐決定，清空 recommendations。"""

def order(item, category=None, size=None, ice=None, sugar=None, addon=None, qty=1, note=""):
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

def make(user_text, orders=None, preferences=None, recommendations=None):
    resp = {
        "orders": orders or [],
        "preferences": preferences or {},
        "recommendations": recommendations or []
    }
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(resp, ensure_ascii=False)}
        ]
    }

samples = []

# ============================================================
# 1. 茶花紅烏龍 × rich_milk_tea (+8)
# ============================================================

samples.append(make(
    "茶花紅烏龍奶茶半糖少冰",
    [order("茶花紅烏龍", "rich_milk_tea", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "紅烏龍奶茶正常糖去冰",
    [order("茶花紅烏龍", "rich_milk_tea", ice="去冰", sugar="正常糖")]
))

samples.append(make(
    "茶花紅烏龍奶茶大杯少糖微冰",
    [order("茶花紅烏龍", "rich_milk_tea", size="L", ice="微冰", sugar="少糖")]
))

samples.append(make(
    "茶花紅烏龍;奶茶的;正常冰無糖",
    [order("茶花紅烏龍", "rich_milk_tea", ice="正常冰", sugar="無糖")]
))

samples.append(make(
    "茶花紅烏龍奶茶中杯微糖少冰",
    [order("茶花紅烏龍", "rich_milk_tea", size="M", ice="少冰", sugar="微糖")]
))

samples.append(make(
    "紅烏龍奶茶熱的微糖",
    [order("茶花紅烏龍", "rich_milk_tea", ice="熱飲", sugar="微糖")]
))

samples.append(make(
    "茶花紅烏龍奶茶加茶凍半糖去冰",
    [order("茶花紅烏龍", "rich_milk_tea", ice="去冰", sugar="半糖", addon=["紅烏龍茶凍"])]
))

samples.append(make(
    "兩杯茶花紅烏龍奶茶少糖少冰",
    [order("茶花紅烏龍", "rich_milk_tea", ice="少冰", sugar="少糖", qty=2)]
))

# ============================================================
# 2. 米香玉露菁 × rich_milk_tea (+8)
# ============================================================

samples.append(make(
    "米香玉露菁奶茶半糖少冰",
    [order("米香玉露菁", "rich_milk_tea", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "玉露菁奶茶正常冰正常糖",
    [order("米香玉露菁", "rich_milk_tea", ice="正常冰", sugar="正常糖")]
))

samples.append(make(
    "米香玉露菁奶茶大杯無糖去冰",
    [order("米香玉露菁", "rich_milk_tea", size="L", ice="去冰", sugar="無糖")]
))

samples.append(make(
    "玉露奶茶中杯少糖微冰",
    [order("米香玉露菁", "rich_milk_tea", size="M", ice="微冰", sugar="少糖")]
))

samples.append(make(
    "米香玉露菁;奶茶的;半糖;少冰",
    [order("米香玉露菁", "rich_milk_tea", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "米香玉露菁奶茶熱的微糖",
    [order("米香玉露菁", "rich_milk_tea", ice="熱飲", sugar="微糖")]
))

samples.append(make(
    "玉露菁奶茶加燕麥粒半糖少冰",
    [order("米香玉露菁", "rich_milk_tea", ice="少冰", sugar="半糖", addon=["燕麥粒"])]
))

samples.append(make(
    "米香玉露菁奶茶少糖去冰加茶凍",
    [order("米香玉露菁", "rich_milk_tea", ice="去冰", sugar="少糖", addon=["紅烏龍茶凍"])]
))

# ============================================================
# 3. 朱槿普洱紅 × rich_milk_tea (+6)
# ============================================================

samples.append(make(
    "普洱奶茶半糖少冰",
    [order("朱槿普洱紅", "rich_milk_tea", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "朱槿普洱紅奶茶正常糖正常冰",
    [order("朱槿普洱紅", "rich_milk_tea", ice="正常冰", sugar="正常糖")]
))

samples.append(make(
    "普洱紅奶茶大杯微糖去冰",
    [order("朱槿普洱紅", "rich_milk_tea", size="L", ice="去冰", sugar="微糖")]
))

samples.append(make(
    "朱槿普洱紅奶茶中杯少糖微冰",
    [order("朱槿普洱紅", "rich_milk_tea", size="M", ice="微冰", sugar="少糖")]
))

samples.append(make(
    "朱槿普洱紅奶茶熱的無糖",
    [order("朱槿普洱紅", "rich_milk_tea", ice="熱飲", sugar="無糖")]
))

samples.append(make(
    "普洱奶茶加茶凍半糖少冰",
    [order("朱槿普洱紅", "rich_milk_tea", ice="少冰", sugar="半糖", addon=["紅烏龍茶凍"])]
))

# ============================================================
# 4. 青檸桂蜜 (+6，fruit_tea 僅冷飲、單一尺寸)
# ============================================================

samples.append(make(
    "青檸桂蜜半糖少冰",
    [order("青檸桂蜜", "fruit_tea", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "青檸桂蜜微糖去冰",
    [order("青檸桂蜜", "fruit_tea", ice="去冰", sugar="微糖")]
))

samples.append(make(
    "一杯青檸桂蜜正常糖少冰",
    [order("青檸桂蜜", "fruit_tea", ice="少冰", sugar="正常糖")]
))

samples.append(make(
    "青檸桂蜜無糖微冰加茶凍",
    [order("青檸桂蜜", "fruit_tea", ice="微冰", sugar="無糖", addon=["紅烏龍茶凍"])]
))

samples.append(make(
    "青檸桂蜜少糖正常冰",
    [order("青檸桂蜜", "fruit_tea", ice="正常冰", sugar="少糖")]
))

# 多品搭配
samples.append(make(
    "一杯青檸桂蜜半糖少冰;再來一杯三窨十五茉鮮奶無糖去冰",
    [order("青檸桂蜜", "fruit_tea", ice="少冰", sugar="半糖"),
     order("三窨十五茉", "fresh_milk_tea", ice="去冰", sugar="無糖")]
))

# ============================================================
# 5. 葡柚十五茉 (+6，fruit_tea 僅冷飲、單一尺寸)
# ============================================================

samples.append(make(
    "葡柚十五茉半糖少冰",
    [order("葡柚十五茉", "fruit_tea", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "葡柚十五茉微糖去冰",
    [order("葡柚十五茉", "fruit_tea", ice="去冰", sugar="微糖")]
))

samples.append(make(
    "來杯葡柚十五茉正常糖微冰",
    [order("葡柚十五茉", "fruit_tea", ice="微冰", sugar="正常糖")]
))

samples.append(make(
    "葡柚十五茉無糖少冰",
    [order("葡柚十五茉", "fruit_tea", ice="少冰", sugar="無糖")]
))

samples.append(make(
    "葡柚十五茉少糖正常冰",
    [order("葡柚十五茉", "fruit_tea", ice="正常冰", sugar="少糖")]
))

# 多品搭配
samples.append(make(
    "葡柚十五茉半糖少冰;加一杯琥珀鐵觀音奶茶無糖去冰",
    [order("葡柚十五茉", "fruit_tea", ice="少冰", sugar="半糖"),
     order("琥珀鐵觀音", "rich_milk_tea", ice="去冰", sugar="無糖")]
))

# ============================================================
# 6. 米香玉露菁 × pure_tea (+5，單一尺寸)
# ============================================================

samples.append(make(
    "米香玉露菁純茶半糖少冰",
    [order("米香玉露菁", "pure_tea", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "玉露菁純茶微糖去冰",
    [order("米香玉露菁", "pure_tea", ice="去冰", sugar="微糖")]
))

samples.append(make(
    "米香玉露菁純茶正常糖少冰",
    [order("米香玉露菁", "pure_tea", ice="少冰", sugar="正常糖")]
))

samples.append(make(
    "米香玉露菁;純茶;少糖微冰",
    [order("米香玉露菁", "pure_tea", ice="微冰", sugar="少糖")]
))

samples.append(make(
    "米香玉露菁純茶熱的無糖",
    [order("米香玉露菁", "pure_tea", ice="熱飲", sugar="無糖")]
))

# ============================================================
# 7. STT 錯字 (+12)
# ============================================================

# 貴花→桂花
samples.append(make(
    "貴花輕烏龍鮮奶半糖少冰",
    [order("桂花輕烏龍", "fresh_milk_tea", ice="少冰", sugar="半糖")]
))

# 規花→桂花 + 奶茶 + L
samples.append(make(
    "規花輕烏龍奶茶大杯無糖去冰",
    [order("桂花輕烏龍", "rich_milk_tea", size="L", ice="去冰", sugar="無糖")]
))

# 鐵關音→鐵觀音 + 仙奶→鮮奶
samples.append(make(
    "鐵關音仙奶半糖少冰",
    [order("琥珀鐵觀音", "fresh_milk_tea", ice="少冰", sugar="半糖")]
))

# 三因→三窨 + 純茶
samples.append(make(
    "三因十五茉純茶微糖去冰",
    [order("三窨十五茉", "pure_tea", ice="去冰", sugar="微糖")]
))

# 三印→三窨 + 仙奶→鮮奶
samples.append(make(
    "三印十五茉仙奶少糖微冰",
    [order("三窨十五茉", "fresh_milk_tea", ice="微冰", sugar="少糖")]
))

# 不理→普洱 + 奶茶
samples.append(make(
    "不理普洱紅奶茶正常糖少冰",
    [order("朱槿普洱紅", "rich_milk_tea", ice="少冰", sugar="正常糖")]
))

# 湖泊→琥珀 + 奶茶
samples.append(make(
    "湖泊鐵觀音奶茶半糖去冰",
    [order("琥珀鐵觀音", "rich_milk_tea", ice="去冰", sugar="半糖")]
))

# 鬼花→桂花 + 奶蓋
samples.append(make(
    "鬼花輕烏龍奶蓋微糖去冰",
    [order("桂花輕烏龍", "cloud_velvet", ice="去冰", sugar="微糖")]
))

# 鐵觀因→鐵觀音 + 鮮奶 + L
samples.append(make(
    "鐵觀因鮮奶大杯無糖少冰",
    [order("琥珀鐵觀音", "fresh_milk_tea", size="L", ice="少冰", sugar="無糖")]
))

# 不耳→普洱 + 純茶
samples.append(make(
    "不耳普洱紅純茶半糖去冰",
    [order("朱槿普洱紅", "pure_tea", ice="去冰", sugar="半糖")]
))

# 鐵官音→鐵觀音 + 奶茶 + M
samples.append(make(
    "鐵官音奶茶中杯半糖去冰",
    [order("琥珀鐵觀音", "rich_milk_tea", size="M", ice="去冰", sugar="半糖")]
))

# 貴花→桂花 + 奶蓋 + 正常糖正常冰
samples.append(make(
    "貴花奶蓋正常糖正常冰",
    [order("桂花輕烏龍", "cloud_velvet", ice="正常冰", sugar="正常糖")]
))

# ============================================================
# 8. 熱飲 (+8，不含 fruit_tea)
# ============================================================

samples.append(make(
    "三窨十五茉純茶熱的微糖",
    [order("三窨十五茉", "pure_tea", ice="熱飲", sugar="微糖")]
))

samples.append(make(
    "桂花輕烏龍鮮奶熱的半糖",
    [order("桂花輕烏龍", "fresh_milk_tea", ice="熱飲", sugar="半糖")]
))

samples.append(make(
    "琥珀鐵觀音奶茶熱的少糖",
    [order("琥珀鐵觀音", "rich_milk_tea", ice="熱飲", sugar="少糖")]
))

samples.append(make(
    "金杯蜜香紅鮮奶熱的無糖",
    [order("金杯蜜香紅", "fresh_milk_tea", ice="熱飲", sugar="無糖")]
))

samples.append(make(
    "朱槿普洱紅純茶熱飲少糖",
    [order("朱槿普洱紅", "pure_tea", ice="熱飲", sugar="少糖")]
))

samples.append(make(
    "桂花輕烏龍奶蓋熱的微糖",
    [order("桂花輕烏龍", "cloud_velvet", ice="熱飲", sugar="微糖")]
))

samples.append(make(
    "金杯蜜香紅奶茶熱的正常糖",
    [order("金杯蜜香紅", "rich_milk_tea", ice="熱飲", sugar="正常糖")]
))

samples.append(make(
    "三窨十五茉鮮奶;要熱的;半糖",
    [order("三窨十五茉", "fresh_milk_tea", ice="熱飲", sugar="半糖")]
))

# ============================================================
# 9. Size M 補強 (+5，僅 fresh_milk_tea / rich_milk_tea)
# ============================================================

samples.append(make(
    "三窨十五茉鮮奶中杯半糖少冰",
    [order("三窨十五茉", "fresh_milk_tea", size="M", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "金杯蜜香紅奶茶中杯無糖去冰",
    [order("金杯蜜香紅", "rich_milk_tea", size="M", ice="去冰", sugar="無糖")]
))

samples.append(make(
    "桂花輕烏龍鮮奶中杯微糖微冰",
    [order("桂花輕烏龍", "fresh_milk_tea", size="M", ice="微冰", sugar="微糖")]
))

samples.append(make(
    "朱槿普洱紅鮮奶中杯半糖少冰",
    [order("朱槿普洱紅", "fresh_milk_tea", size="M", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "米香玉露菁鮮奶中杯正常糖去冰",
    [order("米香玉露菁", "fresh_milk_tea", size="M", ice="去冰", sugar="正常糖")]
))

# ============================================================
# 10. 米香玉露菁 × fresh_milk_tea 補強 (+3)
# ============================================================

samples.append(make(
    "玉露菁鮮奶大杯半糖少冰",
    [order("米香玉露菁", "fresh_milk_tea", size="L", ice="少冰", sugar="半糖")]
))

samples.append(make(
    "米香玉露菁鮮奶無糖去冰加燕麥粒",
    [order("米香玉露菁", "fresh_milk_tea", ice="去冰", sugar="無糖", addon=["燕麥粒"])]
))

samples.append(make(
    "米香玉露菁;鮮奶的;少糖少冰",
    [order("米香玉露菁", "fresh_milk_tea", ice="少冰", sugar="少糖")]
))

# ============================================================
# 11. 混合場景：多品含低頻品項 (+5)
# ============================================================

# 兩杯果茶
samples.append(make(
    "一杯青檸桂蜜半糖少冰;一杯葡柚十五茉微糖去冰",
    [order("青檸桂蜜", "fruit_tea", ice="少冰", sugar="半糖"),
     order("葡柚十五茉", "fruit_tea", ice="去冰", sugar="微糖")]
))

# 果茶 + 奶茶
samples.append(make(
    "蜜桃紅烏龍半糖少冰;再來一杯米香玉露菁奶茶無糖去冰",
    [order("蜜桃紅烏龍", "fruit_tea", ice="少冰", sugar="半糖"),
     order("米香玉露菁", "rich_milk_tea", ice="去冰", sugar="無糖")]
))

# 三品含低頻品項
samples.append(make(
    "茶花紅烏龍奶茶半糖少冰;米香玉露菁純茶微糖去冰;青檸桂蜜無糖微冰",
    [order("茶花紅烏龍", "rich_milk_tea", ice="少冰", sugar="半糖"),
     order("米香玉露菁", "pure_tea", ice="去冰", sugar="微糖"),
     order("青檸桂蜜", "fruit_tea", ice="微冰", sugar="無糖")]
))

# 朱槿普洱紅奶茶 + 葡柚十五茉
samples.append(make(
    "朱槿普洱紅奶茶少糖少冰;葡柚十五茉正常糖微冰",
    [order("朱槿普洱紅", "rich_milk_tea", ice="少冰", sugar="少糖"),
     order("葡柚十五茉", "fruit_tea", ice="微冰", sugar="正常糖")]
))

# 全熱飲組合
samples.append(make(
    "桂花輕烏龍純茶熱的半糖;米香玉露菁鮮奶也要熱的微糖",
    [order("桂花輕烏龍", "pure_tea", ice="熱飲", sugar="半糖"),
     order("米香玉露菁", "fresh_milk_tea", ice="熱飲", sugar="微糖")]
))

# ============================================================
# Output
# ============================================================

with open("round28.jsonl", "w") as f:
    for s in samples:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"Generated {len(samples)} samples → round28.jsonl")

# Stats
from collections import Counter
cat_counter = Counter()
item_counter = Counter()
sugar_counter = Counter()
ice_counter = Counter()
size_counter = Counter()
for s in samples:
    resp = json.loads(s["messages"][2]["content"])
    for o in resp["orders"]:
        cat_counter[o.get("category") or "null"] += 1
        item_counter[o["item"]] += 1
        sugar_counter[o.get("sugar") or "null"] += 1
        ice_counter[o.get("ice") or "null"] += 1
        size_counter[o.get("size") or "null"] += 1

print(f"\n分類分布: {dict(cat_counter)}")
print(f"品項分布: {dict(item_counter)}")
print(f"甜度分布: {dict(sugar_counter)}")
print(f"冰量分布: {dict(ice_counter)}")
print(f"尺寸分布: {dict(size_counter)}")
