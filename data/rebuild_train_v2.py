#!/usr/bin/env python3
"""
重建 train.jsonl（v2 - 意圖分類版本）：
1. 從所有 round*.jsonl 讀取範例
2. 更新 system prompt（含品項描述 + 三種意圖）
3. 注入 "intent": "order" 到所有現有範例
4. 重新分類空訂單範例：閒聊→other、確認→order、推薦問句→recommend
5. 保留所有既有清洗邏輯（strip_prices, unify_not_on_menu, unify_item_name, merge_duplicates）
6. 追加低優先度範例（確認/結束語、品項歧義）
"""
import json
import glob
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 新 system prompt（含品項描述 + 三種意圖）
# ============================================================
NEW_SYSTEM = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，判斷意圖並輸出 JSON。\n\n"
    "意圖分類：\n"
    "- order：顧客要點餐（含具體品項）\n"
    "- recommend：顧客想要推薦（問推薦、不知道喝什麼、描述口味偏好）\n"
    "- other：閒聊或非點餐/推薦的問題\n\n"
    "菜單分類與品項描述：\n"
    "【研選純茶 pure_tea】單一尺寸\n"
    "- 三窨十五茉：三次窨花茉莉綠茶，花香清雅帶甘甜\n"
    "- 桂花輕烏龍：桂花與輕發酵烏龍，花果蜜韻輕柔\n"
    "- 茶花紅烏龍：重焙火紅烏龍，天然花香與熟果甜韻\n"
    "- 朱槿普洱紅：洛神花搭普洱紅茶，微酸回甘解膩\n"
    "- 米香玉露菁：日式玉露菁帶米穀香，鮮爽細膩\n\n"
    "【牧場直達 fresh_milk_tea】M/L\n"
    "- 三窨十五茉(65/75)：茉莉鮮奶，清香滑順\n"
    "- 桂花輕烏龍(65/75)：桂花烏龍鮮奶，蜜韻奶香溫潤\n"
    "- 茶花烏龍(65/75)：烏龍鮮奶，茶奶平衡圓潤\n"
    "- 琥珀鐵觀音(65/75)：重焙鐵觀音鮮奶，焙火香濃郁\n"
    "- 金杯蜜香紅(60/70)：蜜香紅茶鮮奶，天然蜜甜\n"
    "- 朱槿普洱紅(60/70)：洛神普洱鮮奶，微酸風味獨特\n"
    "- 米香玉露菁(60/70)：玉露菁鮮奶，穀物奶香療癒\n\n"
    "【UG奶茶 rich_milk_tea】M/L\n"
    "- 三窨十五茉(65/75)、桂花輕烏龍(65/75)、茶花紅烏龍(65/75)\n"
    "- 琥珀鐵觀音(65/75)、金杯蜜香紅(60/70)、朱槿普洱紅(60/70)、米香玉露菁(60/70)\n\n"
    "【果香四溢 fruit_tea】僅冷飲，單一尺寸\n"
    "- 青檸桂蜜(65)：青檸搭桂花蜜，酸甜清爽消暑\n"
    "- 蜜桃紅烏龍(75)：水蜜桃果香與紅烏龍交織，甜蜜芬芳\n"
    "- 葡柚十五茉(80)：葡萄柚酸香配茉莉，清新微苦大人味\n\n"
    "【雲頂奶蓋 cloud_velvet】單一尺寸\n"
    "- 桂花輕烏龍(95)：桂花烏龍覆綿密奶蓋，鹹甜交融\n"
    "- 茶花紅烏龍(95)：紅烏龍焙火韻搭奶蓋，茶香奶鹹平衡\n\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 正常糖/正常冰。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，設 not_on_menu。\n\n"
    "輸出格式（必須為合法 JSON）：\n"
    "點餐：{\"intent\":\"order\",\"orders\":[{\"item\":\"品名\",\"category\":\"分類\",\"size\":\"M/L/null\",\"ice\":\"冰量/null\",\"sugar\":\"甜度/null\",\"addon\":[],\"qty\":1,\"note\":\"\"}],\"recommendations\":[]}\n"
    "推薦：{\"intent\":\"recommend\",\"orders\":[],\"preferences\":{\"taste\":\"口味\",\"temperature\":\"溫度\",\"scenario\":\"場景\",\"avoid\":\"排除\"},\"recommendations\":[{\"item\":\"品名\",\"category\":\"分類\",\"reason\":\"推薦理由\"}]}\n"
    "混合（點餐+推薦）：orders 和 recommendations 同時有值。若最後一段已做出點餐決定，清空 recommendations。\n"
    "閒聊：{\"intent\":\"other\",\"orders\":[],\"recommendations\":[],\"note\":\"簡短回覆\"}"
)

# 用於辨識推薦意圖的關鍵字
RECOMMEND_KEYWORDS = [
    "推薦", "建議", "招牌", "人氣", "好喝", "熱門",
    "不知道喝什麼", "不確定", "幫我選", "隨便",
    "有什麼", "喝什麼好", "推一下",
]

# 用於辨識閒聊/其他意圖的關鍵字
OTHER_KEYWORDS = [
    "Wi-Fi", "wifi", "廁所", "營業", "幾點", "地址",
    "外帶", "內用", "等多久", "電話",
]

# 非菜單加料關鍵字（用於偵測加料拒絕範例）
ADDON_REJECT_KEYWORDS = ["無珍珠", "無椰果", "無波霸", "無布丁", "無仙草", "無粉圓", "無芋圓", "波霸非"]


def strip_prices(obj):
    """遞迴移除 unit_price, total"""
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if k in ("unit_price", "total"):
                continue
            new[k] = strip_prices(v)
        return new
    elif isinstance(obj, list):
        return [strip_prices(item) for item in obj]
    return obj


def unify_not_on_menu(order_obj):
    """統一 not_on_menu 為精簡格式：只保留 item, not_on_menu, note"""
    if order_obj.get("not_on_menu"):
        return {
            "item": order_obj["item"],
            "not_on_menu": True,
            "note": order_obj.get("note", "本店無此品項"),
        }
    return order_obj


def unify_item_name(order_obj):
    """統一品名：鐵觀音 → 琥珀鐵觀音（僅限正常品項）"""
    if order_obj.get("not_on_menu"):
        return order_obj
    item = order_obj.get("item", "")
    if item == "鐵觀音":
        order_obj["item"] = "琥珀鐵觀音"
    return order_obj


def merge_duplicate_orders(orders):
    """合併相同規格的 order，用 qty 表示數量"""
    merged = []
    for o in orders:
        if o.get("not_on_menu"):
            merged.append(o)
            continue
        key = (o.get("item"), o.get("category"), o.get("size"),
               o.get("ice"), o.get("sugar"),
               json.dumps(o.get("addon", []), ensure_ascii=False),
               o.get("note", ""))
        found = False
        for m in merged:
            if m.get("not_on_menu"):
                continue
            m_key = (m.get("item"), m.get("category"), m.get("size"),
                     m.get("ice"), m.get("sugar"),
                     json.dumps(m.get("addon", []), ensure_ascii=False),
                     m.get("note", ""))
            if key == m_key:
                m["qty"] = m.get("qty", 1) + o.get("qty", 1)
                found = True
                break
        if not found:
            merged.append(o)
    return merged


def is_addon_reject(order_obj):
    """判斷是否為加料拒絕範例"""
    if order_obj.get("not_on_menu"):
        return False
    note = order_obj.get("note", "")
    return any(kw in note for kw in ADDON_REJECT_KEYWORDS)


def should_skip_example(asst_obj, user_text):
    """判斷整筆範例是否應該跳過"""
    orders = asst_obj.get("orders", [])
    for o in orders:
        if is_addon_reject(o):
            if re.search(r"加(珍珠|椰果|波霸|布丁|仙草|粉圓|芋圓)", user_text):
                return True
    return False


def classify_intent(user_text, asst_obj):
    """根據用戶文字和回應內容判斷意圖"""
    orders = asst_obj.get("orders", [])

    # 有訂單 → order
    if len(orders) > 0:
        return "order"

    # 無訂單，檢查用戶文字
    text_lower = user_text.lower()

    # 推薦相關
    for kw in RECOMMEND_KEYWORDS:
        if kw in text_lower:
            return "recommend"

    # 其他閒聊
    for kw in OTHER_KEYWORDS:
        if kw.lower() in text_lower:
            return "other"

    # 預設：確認/結束語歸 order（空訂單 + note）
    return "order"


def inject_intent(asst_obj, intent):
    """注入 intent 欄位到 assistant 回應"""
    new_obj = {"intent": intent}

    if intent == "order":
        new_obj["orders"] = asst_obj.get("orders", [])
        new_obj["recommendations"] = []
    elif intent == "recommend":
        new_obj["orders"] = []
        new_obj["recommendations"] = []  # 現有資料沒有推薦，留空
        new_obj["preferences"] = {}
    elif intent == "other":
        new_obj["orders"] = []
        new_obj["recommendations"] = []
        new_obj["note"] = asst_obj.get("note", "")

    # 保留 note（如果有）
    if "note" in asst_obj and intent != "other":
        note = asst_obj["note"]
        if note:
            new_obj["note"] = note

    return new_obj


def clean_example(ex_str):
    """清洗單筆範例，回傳 None 表示應跳過"""
    ex = json.loads(ex_str)
    msgs = ex["messages"]

    # 更新 system prompt
    msgs[0]["content"] = NEW_SYSTEM

    # 解析 assistant output
    asst = json.loads(msgs[2]["content"])
    asst = strip_prices(asst)

    user_text = msgs[1]["content"]

    # 跳過加料拒絕範例
    if should_skip_example(asst, user_text):
        return None

    # 如果已有 intent 欄位（如 round23 資料），只更新 system prompt 和清洗 orders
    if "intent" in asst:
        # 清洗 orders（如果有）
        if "orders" in asst:
            asst["orders"] = [
                unify_item_name(unify_not_on_menu(o))
                for o in asst["orders"]
            ]
            asst["orders"] = merge_duplicate_orders(asst["orders"])
        msgs[2]["content"] = json.dumps(asst, ensure_ascii=False)
        return json.dumps(ex, ensure_ascii=False)

    # 舊格式：清洗 orders 並注入 intent
    if "orders" in asst:
        asst["orders"] = [
            unify_item_name(unify_not_on_menu(o))
            for o in asst["orders"]
        ]
        asst["orders"] = merge_duplicate_orders(asst["orders"])

    # 判斷意圖並注入
    intent = classify_intent(user_text, asst)
    asst = inject_intent(asst, intent)

    msgs[2]["content"] = json.dumps(asst, ensure_ascii=False)
    return json.dumps(ex, ensure_ascii=False)


# ============================================================
# 1. 從所有 round*.jsonl 讀取並清洗
# ============================================================
round_files = sorted(glob.glob(os.path.join(BASE_DIR, "round*.jsonl")))
cleaned = []
skipped = 0
intent_counts = {"order": 0, "recommend": 0, "other": 0}

for fpath in round_files:
    fname = os.path.basename(fpath)
    count = 0
    skip_count = 0
    with open(fpath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            result = clean_example(line)
            if result is None:
                skip_count += 1
                skipped += 1
            else:
                cleaned.append(result)
                count += 1
                # Count intents
                asst = json.loads(json.loads(result)["messages"][2]["content"])
                intent = asst.get("intent", "order")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
    msg = f"  {fname}: {count} examples"
    if skip_count:
        msg += f" (skipped {skip_count} addon-reject)"
    print(msg)

print(f"\nLoaded {len(cleaned)} examples from {len(round_files)} round files (skipped {skipped})")
print(f"Intent distribution: {intent_counts}")

# ============================================================
# 2. 低優先度：確認/結束語（不含特殊要求）
# ============================================================


def make(user, assistant):
    return json.dumps({"messages": [
        {"role": "system", "content": NEW_SYSTEM},
        {"role": "user", "content": user},
        {"role": "assistant", "content": json.dumps(assistant, ensure_ascii=False)},
    ]}, ensure_ascii=False)


def order(item, cat, size, ice, sugar, addon, note=""):
    return {"item": item, "category": cat, "size": size, "ice": ice, "sugar": sugar,
            "addon": addon, "qty": 1, "note": note}


new_examples = []

# --- 確認/結束語（intent=order） ---
new_examples.append(make("就這樣", {"intent": "order", "orders": [], "recommendations": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("沒了", {"intent": "order", "orders": [], "recommendations": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("以上", {"intent": "order", "orders": [], "recommendations": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("好，先這樣", {"intent": "order", "orders": [], "recommendations": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("對，就這些", {"intent": "order", "orders": [], "recommendations": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("可以了", {"intent": "order", "orders": [], "recommendations": [], "note": "顧客確認結束，無新增品項"}))

# 確認 + 前面有點餐
new_examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：就這樣",
    {"intent": "order", "orders": [order("三窨十五茉", "fresh_milk_tea", "M", "少冰", "半糖", [])], "recommendations": []}))
new_examples.append(make(
    "顧客：桂花輕烏龍純茶去冰無糖\n顧客：沒了，就這些",
    {"intent": "order", "orders": [order("桂花輕烏龍", "pure_tea", None, "去冰", "無糖", [])], "recommendations": []}))
new_examples.append(make(
    "顧客：茶花紅烏龍純茶無糖去冰\n顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：好，以上",
    {"intent": "order", "orders": [
        order("茶花紅烏龍", "pure_tea", None, "去冰", "無糖", []),
        order("金杯蜜香紅", "fresh_milk_tea", "M", "少冰", "半糖", []),
    ], "recommendations": []}))
new_examples.append(make(
    "顧客：兩杯琥珀鐵觀音奶茶半糖少冰\n顧客：對，就這樣",
    {"intent": "order", "orders": [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "size": "M", "ice": "少冰", "sugar": "半糖", "addon": [], "qty": 2, "note": ""},
    ], "recommendations": []}))

# --- 品項歧義 ---
new_examples.append(make(
    "一杯桂花輕烏龍半糖少冰",
    {"intent": "order", "orders": [order("桂花輕烏龍", None, "M", "少冰", "半糖", [],
                  "顧客未指定類別（純茶/鮮奶/奶茶/奶蓋），請店員確認")], "recommendations": []}))
new_examples.append(make(
    "一杯茶花紅烏龍無糖去冰",
    {"intent": "order", "orders": [order("茶花紅烏龍", None, None, "去冰", "無糖", [],
                  "顧客未指定類別（純茶/奶蓋），請店員確認")], "recommendations": []}))
new_examples.append(make(
    "一杯桂花輕烏龍加鮮奶半糖少冰",
    {"intent": "order", "orders": [order("桂花輕烏龍", "fresh_milk_tea", "M", "少冰", "半糖", [])], "recommendations": []}))
new_examples.append(make(
    "一杯茶花紅烏龍奶蓋",
    {"intent": "order", "orders": [order("茶花紅烏龍", "cloud_velvet", None, None, None, [])], "recommendations": []}))

# --- 閒聊（intent=other） ---
new_examples.append(make("有Wi-Fi嗎", {"intent": "other", "orders": [], "recommendations": [], "note": "顧客詢問Wi-Fi"}))
new_examples.append(make("廁所在哪", {"intent": "other", "orders": [], "recommendations": [], "note": "顧客詢問廁所位置"}))
new_examples.append(make("你們營業到幾點", {"intent": "other", "orders": [], "recommendations": [], "note": "顧客詢問營業時間"}))
new_examples.append(make("可以外帶嗎", {"intent": "other", "orders": [], "recommendations": [], "note": "顧客詢問外帶"}))
new_examples.append(make("你們有賣咖啡嗎", {"intent": "other", "orders": [], "recommendations": [], "note": "顧客詢問非菜單品項"}))
new_examples.append(make("等一下要多久", {"intent": "other", "orders": [], "recommendations": [], "note": "顧客詢問等候時間"}))

print(f"Generated {len(new_examples)} new examples (low priority + other intent)")

# ============================================================
# 3. 寫出
# ============================================================
all_examples = cleaned + new_examples

outpath = os.path.join(BASE_DIR, "combined.jsonl")
with open(outpath, "w") as f:
    for ex in all_examples:
        f.write(ex + "\n")

print(f"\nTotal: {len(all_examples)} examples written to combined.jsonl")

# ============================================================
# 4. 驗證
# ============================================================
print("\n=== 驗證 ===")
nom_full = 0
nom_simple = 0
iron_old = 0
iron_new = 0
addon_rej = 0
qty_gt1 = 0
final_intents = {"order": 0, "recommend": 0, "other": 0}
missing_intent = 0

with open(outpath) as f:
    for line in f:
        asst = json.loads(json.loads(line)["messages"][2]["content"])

        intent = asst.get("intent")
        if intent:
            final_intents[intent] = final_intents.get(intent, 0) + 1
        else:
            missing_intent += 1

        for o in asst.get("orders", []):
            if o.get("not_on_menu"):
                if "category" in o:
                    nom_full += 1
                else:
                    nom_simple += 1
            item = o.get("item", "")
            if item == "鐵觀音":
                iron_old += 1
            elif item == "琥珀鐵觀音":
                iron_new += 1
            if is_addon_reject(o):
                addon_rej += 1
            if o.get("qty", 1) > 1:
                qty_gt1 += 1

print(f"  Intent 分布: {final_intents}")
print(f"  缺少 intent: {missing_intent} (應為 0)")
print(f"  not_on_menu 完整格式: {nom_full} (應為 0)")
print(f"  not_on_menu 精簡格式: {nom_simple}")
print(f"  品名「鐵觀音」: {iron_old} (應為 0)")
print(f"  品名「琥珀鐵觀音」: {iron_new}")
print(f"  殘留加料拒絕: {addon_rej} (應為 0)")
print(f"  qty>1 的 order: {qty_gt1}")
