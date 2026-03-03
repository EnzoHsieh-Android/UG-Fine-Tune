"""Round 27: 補強多輪修改/新增區分、category null、同品項多杯場景。

規則：
1. 有修改詞（改/換/不對/第N杯）→ 替換該杯，只改提到的欄位
2. 有新增詞（再來/還要/加一杯）→ 新增
3. 無明確信號 → 預設新增
4. 只說品項名 → category null
5. 同品項多杯 → 各自獨立判斷 category，未指定的一律 null
6. 多輪用分號分隔，不使用「顧客：」前綴
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
# 類型 1：有修改詞 → 替換，只改提到的欄位
# ============================================================

# 改分類
samples.append(make(
    "桂花輕烏龍半糖去冰;改奶蓋",
    [order("桂花輕烏龍", "cloud_velvet", ice="去冰", sugar="半糖")]
))

samples.append(make(
    "三窨十五茉鮮奶;改純茶",
    [order("三窨十五茉", "pure_tea")]
))

samples.append(make(
    "茶花紅烏龍奶茶半糖;換奶蓋",
    [order("茶花紅烏龍", "cloud_velvet", sugar="半糖")]
))

samples.append(make(
    "琥珀鐵觀音鮮奶少冰;改奶茶",
    [order("琥珀鐵觀音", "rich_milk_tea", ice="少冰")]
))

samples.append(make(
    "金杯蜜香紅奶茶;換成鮮奶",
    [order("金杯蜜香紅", "fresh_milk_tea")]
))

samples.append(make(
    "桂花輕烏龍;要奶蓋的",
    [order("桂花輕烏龍", "cloud_velvet")]
))

# 改甜度/冰量
samples.append(make(
    "三窨十五茉鮮奶半糖少冰;改微糖",
    [order("三窨十五茉", "fresh_milk_tea", sugar="微糖", ice="少冰")]
))

samples.append(make(
    "琥珀鐵觀音奶茶大杯;改去冰",
    [order("琥珀鐵觀音", "rich_milk_tea", size="L", ice="去冰")]
))

samples.append(make(
    "金杯蜜香紅鮮奶半糖少冰;甜度改無糖",
    [order("金杯蜜香紅", "fresh_milk_tea", sugar="無糖", ice="少冰")]
))

# 改尺寸
samples.append(make(
    "桂花輕烏龍鮮奶;改大杯",
    [order("桂花輕烏龍", "fresh_milk_tea", size="L")]
))

# 多杯中修改某一杯
samples.append(make(
    "桂花輕烏龍鮮奶;三窨十五茉純茶;桂花改奶蓋",
    [order("桂花輕烏龍", "cloud_velvet"), order("三窨十五茉", "pure_tea")]
))

samples.append(make(
    "金杯蜜香紅鮮奶半糖;琥珀鐵觀音奶茶;金杯改去冰",
    [order("金杯蜜香紅", "fresh_milk_tea", sugar="半糖", ice="去冰"),
     order("琥珀鐵觀音", "rich_milk_tea")]
))

samples.append(make(
    "三窨十五茉鮮奶;桂花輕烏龍奶茶;三窨換純茶",
    [order("三窨十五茉", "pure_tea"), order("桂花輕烏龍", "rich_milk_tea")]
))

# 不對 → 修改
samples.append(make(
    "桂花輕烏龍鮮奶;不對，要奶蓋",
    [order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "三窨十五茉奶茶;不對，純茶就好",
    [order("三窨十五茉", "pure_tea")]
))

samples.append(make(
    "琥珀鐵觀音鮮奶半糖;不對改微糖",
    [order("琥珀鐵觀音", "fresh_milk_tea", sugar="微糖")]
))

# ============================================================
# 類型 2：第 N 杯指代 → 修改
# ============================================================

samples.append(make(
    "桂花輕烏龍;三窨十五茉;第一杯改奶蓋",
    [order("桂花輕烏龍", "cloud_velvet"), order("三窨十五茉")]
))

samples.append(make(
    "琥珀鐵觀音鮮奶;金杯蜜香紅奶茶;第二杯改鮮奶",
    [order("琥珀鐵觀音", "fresh_milk_tea"), order("金杯蜜香紅", "fresh_milk_tea")]
))

samples.append(make(
    "三窨十五茉鮮奶半糖;桂花輕烏龍純茶;第一杯改微糖",
    [order("三窨十五茉", "fresh_milk_tea", sugar="微糖"),
     order("桂花輕烏龍", "pure_tea")]
))

samples.append(make(
    "桂花輕烏龍鮮奶;茶花紅烏龍奶茶;米香玉露菁純茶;第二杯改去冰",
    [order("桂花輕烏龍", "fresh_milk_tea"),
     order("茶花紅烏龍", "rich_milk_tea", ice="去冰"),
     order("米香玉露菁", "pure_tea")]
))

samples.append(make(
    "金杯蜜香紅;琥珀鐵觀音;第一杯要鮮奶半糖",
    [order("金杯蜜香紅", "fresh_milk_tea", sugar="半糖"), order("琥珀鐵觀音")]
))

samples.append(make(
    "三窨十五茉;桂花輕烏龍;第二杯要奶蓋",
    [order("三窨十五茉"), order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "琥珀鐵觀音鮮奶;朱槿普洱紅奶茶;第一杯加茶凍",
    [order("琥珀鐵觀音", "fresh_milk_tea", addon=["紅烏龍茶凍"]),
     order("朱槿普洱紅", "rich_milk_tea")]
))

samples.append(make(
    "桂花輕烏龍鮮奶半糖;三窨十五茉鮮奶;第二杯改大杯微糖",
    [order("桂花輕烏龍", "fresh_milk_tea", sugar="半糖"),
     order("三窨十五茉", "fresh_milk_tea", size="L", sugar="微糖")]
))

# ============================================================
# 類型 3：有新增詞 → 新增
# ============================================================

samples.append(make(
    "桂花輕烏龍;再來一杯桂花輕烏龍奶蓋",
    [order("桂花輕烏龍"), order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "三窨十五茉鮮奶;還要一杯三窨十五茉純茶",
    [order("三窨十五茉", "fresh_milk_tea"), order("三窨十五茉", "pure_tea")]
))

samples.append(make(
    "琥珀鐵觀音奶茶;加一杯琥珀鐵觀音鮮奶",
    [order("琥珀鐵觀音", "rich_milk_tea"), order("琥珀鐵觀音", "fresh_milk_tea")]
))

samples.append(make(
    "桂花輕烏龍鮮奶半糖;再一杯桂花輕烏龍奶蓋",
    [order("桂花輕烏龍", "fresh_milk_tea", sugar="半糖"),
     order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "金杯蜜香紅;還要一杯金杯蜜香紅鮮奶",
    [order("金杯蜜香紅"), order("金杯蜜香紅", "fresh_milk_tea")]
))

samples.append(make(
    "三窨十五茉鮮奶;再來一杯三窨十五茉奶茶",
    [order("三窨十五茉", "fresh_milk_tea"), order("三窨十五茉", "rich_milk_tea")]
))

samples.append(make(
    "茶花紅烏龍奶蓋;再加一杯茶花紅烏龍純茶",
    [order("茶花紅烏龍", "cloud_velvet"), order("茶花紅烏龍", "pure_tea")]
))

# ============================================================
# 類型 4：無明確信號 → 預設新增
# ============================================================

samples.append(make(
    "桂花輕烏龍;桂花輕烏龍奶蓋",
    [order("桂花輕烏龍"), order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "三窨十五茉鮮奶;三窨十五茉純茶",
    [order("三窨十五茉", "fresh_milk_tea"), order("三窨十五茉", "pure_tea")]
))

samples.append(make(
    "琥珀鐵觀音鮮奶;琥珀鐵觀音奶茶",
    [order("琥珀鐵觀音", "fresh_milk_tea"), order("琥珀鐵觀音", "rich_milk_tea")]
))

samples.append(make(
    "桂花輕烏龍;三窨十五茉;桂花輕烏龍奶蓋",
    [order("桂花輕烏龍"), order("三窨十五茉"), order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "茶花紅烏龍;茶花紅烏龍奶蓋",
    [order("茶花紅烏龍"), order("茶花紅烏龍", "cloud_velvet")]
))

samples.append(make(
    "金杯蜜香紅;金杯蜜香紅鮮奶半糖",
    [order("金杯蜜香紅"), order("金杯蜜香紅", "fresh_milk_tea", sugar="半糖")]
))

# ============================================================
# 類型 5：只說品項名 → category null
# ============================================================

samples.append(make(
    "桂花輕烏龍",
    [order("桂花輕烏龍")]
))

samples.append(make(
    "三窨十五茉半糖去冰",
    [order("三窨十五茉", sugar="半糖", ice="去冰")]
))

samples.append(make(
    "琥珀鐵觀音少冰",
    [order("琥珀鐵觀音", ice="少冰")]
))

samples.append(make(
    "金杯蜜香紅微糖",
    [order("金杯蜜香紅", sugar="微糖")]
))

samples.append(make(
    "桂花輕烏龍和三窨十五茉",
    [order("桂花輕烏龍"), order("三窨十五茉")]
))

samples.append(make(
    "茶花紅烏龍一杯",
    [order("茶花紅烏龍")]
))

samples.append(make(
    "朱槿普洱紅無糖去冰",
    [order("朱槿普洱紅", sugar="無糖", ice="去冰")]
))

samples.append(make(
    "米香玉露菁",
    [order("米香玉露菁")]
))

samples.append(make(
    "來一杯桂花輕烏龍",
    [order("桂花輕烏龍")]
))

samples.append(make(
    "我要一杯琥珀鐵觀音",
    [order("琥珀鐵觀音")]
))

# 多杯都沒指定分類
samples.append(make(
    "桂花輕烏龍半糖;三窨十五茉去冰",
    [order("桂花輕烏龍", sugar="半糖"), order("三窨十五茉", ice="去冰")]
))

samples.append(make(
    "琥珀鐵觀音;金杯蜜香紅;米香玉露菁",
    [order("琥珀鐵觀音"), order("金杯蜜香紅"), order("米香玉露菁")]
))

# ============================================================
# 類型 6：同品項多杯，各自獨立判斷 category
# ============================================================

samples.append(make(
    "桂花輕烏龍鮮奶;桂花輕烏龍奶蓋",
    [order("桂花輕烏龍", "fresh_milk_tea"), order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "三窨十五茉純茶;三窨十五茉鮮奶;三窨十五茉奶茶",
    [order("三窨十五茉", "pure_tea"), order("三窨十五茉", "fresh_milk_tea"),
     order("三窨十五茉", "rich_milk_tea")]
))

samples.append(make(
    "桂花輕烏龍;桂花輕烏龍鮮奶",
    [order("桂花輕烏龍"), order("桂花輕烏龍", "fresh_milk_tea")]
))

samples.append(make(
    "茶花紅烏龍純茶;茶花紅烏龍奶蓋",
    [order("茶花紅烏龍", "pure_tea"), order("茶花紅烏龍", "cloud_velvet")]
))

samples.append(make(
    "琥珀鐵觀音;琥珀鐵觀音鮮奶半糖",
    [order("琥珀鐵觀音"), order("琥珀鐵觀音", "fresh_milk_tea", sugar="半糖")]
))

# 三杯同品項 - 第一杯沒指定 → null，其餘各自判斷
samples.append(make(
    "桂花輕烏龍;桂花輕烏龍鮮奶;桂花輕烏龍奶蓋",
    [order("桂花輕烏龍"), order("桂花輕烏龍", "fresh_milk_tea"),
     order("桂花輕烏龍", "cloud_velvet")]
))

# ============================================================
# 混合場景：修改 + 新增 + category null
# ============================================================

samples.append(make(
    "桂花輕烏龍;三窨十五茉;桂花改鮮奶;再來一杯茶花紅烏龍",
    [order("桂花輕烏龍", "fresh_milk_tea"), order("三窨十五茉"),
     order("茶花紅烏龍")]
))

samples.append(make(
    "琥珀鐵觀音半糖;金杯蜜香紅;第一杯改去冰;還要一杯米香玉露菁鮮奶",
    [order("琥珀鐵觀音", sugar="半糖", ice="去冰"), order("金杯蜜香紅"),
     order("米香玉露菁", "fresh_milk_tea")]
))

samples.append(make(
    "三窨十五茉鮮奶;桂花輕烏龍;第一杯換奶茶",
    [order("三窨十五茉", "rich_milk_tea"), order("桂花輕烏龍")]
))

samples.append(make(
    "朱槿普洱紅鮮奶;米香玉露菁;朱槿改純茶;再來一杯桂花輕烏龍奶蓋",
    [order("朱槿普洱紅", "pure_tea"), order("米香玉露菁"),
     order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "桂花輕烏龍半糖少冰;不對要奶蓋的;再來一杯三窨十五茉鮮奶",
    [order("桂花輕烏龍", "cloud_velvet", sugar="半糖", ice="少冰"),
     order("三窨十五茉", "fresh_milk_tea")]
))

# ============================================================
# Anchor 樣本：確保基本能力不回歸
# ============================================================

samples.append(make(
    "三窨十五茉鮮奶半糖去冰",
    [order("三窨十五茉", "fresh_milk_tea", sugar="半糖", ice="去冰")]
))

samples.append(make(
    "桂花輕烏龍奶蓋",
    [order("桂花輕烏龍", "cloud_velvet")]
))

samples.append(make(
    "琥珀鐵觀音奶茶大杯半糖少冰加紅烏龍茶凍",
    [order("琥珀鐵觀音", "rich_milk_tea", size="L", sugar="半糖", ice="少冰",
           addon=["紅烏龍茶凍"])]
))

samples.append(make(
    "青檸桂蜜半糖",
    [order("青檸桂蜜", "fruit_tea", sugar="半糖")]
))

samples.append(make(
    "蜜桃紅烏龍少冰",
    [order("蜜桃紅烏龍", "fruit_tea", ice="少冰")]
))

samples.append(make(
    "有沒有推薦的",
    [], {"flavor": "任意"},
    [{"item": "三窨十五茉", "category": "fresh_milk_tea",
      "reason": "茉莉鮮奶清香滑順，最受歡迎"}]
))

samples.append(make(
    "茶味重一點的有嗎",
    [], {"flavor": "茶味重"},
    [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea",
      "reason": "重焙鐵觀音鮮奶，焙火香濃郁回甘"}]
))

samples.append(make(
    "三窨十五茉鮮奶半糖少冰;再加一杯桂花輕烏龍奶茶微糖去冰",
    [order("三窨十五茉", "fresh_milk_tea", sugar="半糖", ice="少冰"),
     order("桂花輕烏龍", "rich_milk_tea", sugar="微糖", ice="去冰")]
))

samples.append(make(
    "你們幾點關門",
    []
))

samples.append(make(
    "一杯珍珠奶茶",
    [order("珍珠奶茶")]
))

# Output
output_path = "round27.jsonl"
with open(output_path, 'w') as f:
    for s in samples:
        f.write(json.dumps(s, ensure_ascii=False) + '\n')

print(f"Generated {len(samples)} samples → {output_path}")

# Stats
modify_count = sum(1 for s in samples for m in s['messages']
                   if m['role'] == 'user' and any(kw in m['content'] for kw in ['改', '換', '不對']))
nth_count = sum(1 for s in samples for m in s['messages']
                if m['role'] == 'user' and '第' in m['content'] and '杯' in m['content'])
add_count = sum(1 for s in samples for m in s['messages']
                if m['role'] == 'user' and any(kw in m['content'] for kw in ['再來', '還要', '加一杯', '再加', '再一杯']))
null_cat = sum(1 for s in samples for m in s['messages']
               if m['role'] == 'user' and ';' not in m['content'] and '鮮奶' not in m['content']
               and '奶茶' not in m['content'] and '純茶' not in m['content']
               and '奶蓋' not in m['content'] and '果茶' not in m['content'])

print(f"\nBreakdown:")
print(f"  修改詞場景: {modify_count}")
print(f"  第N杯指代: {nth_count}")
print(f"  新增詞場景: {add_count}")
print(f"  category null: ~{null_cat}")
