#!/usr/bin/env python3
"""
重建 train.jsonl：
1. 從所有 round*.jsonl 讀取範例
2. 移除 unit_price 和 total（舊格式殘留）
3. 更新 system prompt（無價格版本）
4. 統一 not_on_menu 格式（精簡：item + not_on_menu + note）
5. 統一品名（鐵觀音 → 琥珀鐵觀音）
6. 過濾非菜單加料拒絕範例（交由後端處理）
7. 合併重複 order 為 qty（同品同規格合併）
8. 追加低優先度範例（確認/結束語）
"""
import json
import glob
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 新 system prompt（無價格）
# ============================================================
NEW_SYSTEM = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。\n\n"
    "菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。\n\n"
    "純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，回傳 not_on_menu 欄位。\n\n"
    "輸出格式：{\"orders\":[{\"item\":\"品名\",\"category\":\"分類\",\"size\":\"M/L/null\",\"ice\":\"冰量/null\",\"sugar\":\"甜度/null\",\"addon\":[],\"qty\":1,\"note\":\"\"}]}"
)

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
        # 建立比較 key
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
    """判斷是否為加料拒絕範例（有正常 category 但 note 提到非菜單加料）"""
    if order_obj.get("not_on_menu"):
        return False  # 品項本身 not_on_menu 不算
    note = order_obj.get("note", "")
    return any(kw in note for kw in ADDON_REJECT_KEYWORDS)

def should_skip_example(asst_obj, user_text):
    """判斷整筆範例是否應該跳過"""
    orders = asst_obj.get("orders", [])
    # 如果任何一個 order 是加料拒絕，跳過整筆
    # 但排除多品項混合情境（只有加料拒絕的 order 才跳）
    for o in orders:
        if is_addon_reject(o):
            # 確認是「加非菜單加料」的情境（user 文字包含加XX）
            if re.search(r"加(珍珠|椰果|波霸|布丁|仙草|粉圓|芋圓)", user_text):
                return True
    return False

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

    # 清洗每個 order
    if "orders" in asst:
        asst["orders"] = [
            unify_item_name(unify_not_on_menu(o))
            for o in asst["orders"]
        ]
        # 合併重複 order 為 qty
        asst["orders"] = merge_duplicate_orders(asst["orders"])

    msgs[2]["content"] = json.dumps(asst, ensure_ascii=False)
    return json.dumps(ex, ensure_ascii=False)

# ============================================================
# 1. 從所有 round*.jsonl 讀取並清洗
# ============================================================
round_files = sorted(glob.glob(os.path.join(BASE_DIR, "round*.jsonl")))
cleaned = []
skipped = 0

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
    msg = f"  {fname}: {count} examples"
    if skip_count:
        msg += f" (skipped {skip_count} addon-reject)"
    print(msg)

print(f"Loaded {len(cleaned)} examples from {len(round_files)} round files (skipped {skipped})")

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

# --- 確認/結束語 ---
new_examples.append(make("就這樣", {"orders": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("沒了", {"orders": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("以上", {"orders": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("好，先這樣", {"orders": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("對，就這些", {"orders": [], "note": "顧客確認結束，無新增品項"}))
new_examples.append(make("可以了", {"orders": [], "note": "顧客確認結束，無新增品項"}))

# 確認 + 前面有點餐
new_examples.append(make(
    "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：就這樣",
    {"orders": [order("三窨十五茉","fresh_milk_tea","M","少冰","半糖",[])]}))
new_examples.append(make(
    "顧客：桂花輕烏龍純茶去冰無糖\n顧客：沒了，就這些",
    {"orders": [order("桂花輕烏龍","pure_tea",None,"去冰","無糖",[])]}))
new_examples.append(make(
    "顧客：茶花紅烏龍純茶無糖去冰\n顧客：金杯蜜香紅鮮奶半糖少冰\n顧客：好，以上",
    {"orders": [
        order("茶花紅烏龍","pure_tea",None,"去冰","無糖",[]),
        order("金杯蜜香紅","fresh_milk_tea","M","少冰","半糖",[]),
    ]}))
new_examples.append(make(
    "顧客：兩杯琥珀鐵觀音奶茶半糖少冰\n顧客：對，就這樣",
    {"orders": [
        {"item":"琥珀鐵觀音","category":"rich_milk_tea","size":"M","ice":"少冰","sugar":"半糖","addon":[],"qty":2,"note":""},
    ]}))

# --- 品項歧義 ---
new_examples.append(make(
    "一杯桂花輕烏龍半糖少冰",
    {"orders": [order("桂花輕烏龍",None,"M","少冰","半糖",[],
                      "顧客未指定類別（純茶/鮮奶/奶茶/奶蓋），請店員確認")]}))
new_examples.append(make(
    "一杯茶花紅烏龍無糖去冰",
    {"orders": [order("茶花紅烏龍",None,None,"去冰","無糖",[],
                      "顧客未指定類別（純茶/奶蓋），請店員確認")]}))
new_examples.append(make(
    "一杯桂花輕烏龍加鮮奶半糖少冰",
    {"orders": [order("桂花輕烏龍","fresh_milk_tea","M","少冰","半糖",[])]}))
new_examples.append(make(
    "一杯茶花紅烏龍奶蓋",
    {"orders": [order("茶花紅烏龍","cloud_velvet",None,None,None,[])]}))

print(f"Generated {len(new_examples)} new examples (low priority)")

# ============================================================
# 3. 寫出
# ============================================================
all_examples = cleaned + new_examples

with open(os.path.join(BASE_DIR, "train.jsonl"), "w") as f:
    for ex in all_examples:
        f.write(ex + "\n")

print(f"Total: {len(all_examples)} examples written to train.jsonl")

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

with open(os.path.join(BASE_DIR, "train.jsonl")) as f:
    for line in f:
        asst = json.loads(json.loads(line)["messages"][2]["content"])
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

print(f"  not_on_menu 完整格式: {nom_full} (應為 0)")
print(f"  not_on_menu 精簡格式: {nom_simple}")
print(f"  品名「鐵觀音」: {iron_old} (應為 0)")
print(f"  品名「琥珀鐵觀音」: {iron_new}")
print(f"  殘留加料拒絕: {addon_rej} (應為 0)")
print(f"  qty>1 的 order: {qty_gt1}")
