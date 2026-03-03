#!/usr/bin/env python3
"""Additional audit checks."""

import json
from collections import Counter

def load_data(filepath):
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                user_msg = None
                assistant_msg = None
                for msg in data["messages"]:
                    if msg["role"] == "user":
                        user_msg = msg["content"]
                    elif msg["role"] == "assistant":
                        assistant_msg = msg["content"]
                if user_msg and assistant_msg:
                    output = json.loads(assistant_msg)
                    rows.append((line_num, user_msg, output))
            except:
                pass
    return rows

# ======= Check: train.jsonl:555 recommendation 推薦果茶但用戶要熱的 =======
print("=" * 70)
print("1. 推薦與用戶偏好不符的案例")
print("=" * 70)

for filepath, fname in [("data/train.jsonl", "train"), ("data/valid.jsonl", "valid")]:
    rows = load_data(filepath)
    for line_num, user_msg, output in rows:
        recs = output.get("recommendations", [])
        prefs = output.get("preferences", {})
        if recs and "熱" in user_msg:
            for r in recs:
                FRUIT_TEA = {"青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"}
                if r.get("item") in FRUIT_TEA:
                    print(f"  [{fname}:{line_num}] 用戶要「熱的」但推薦果茶（僅冷飲）: {r.get('item')}")
                    print(f"    user: '{user_msg}'")
                    print(f"    prefs: {prefs}")

# ======= Check: valid.jsonl:30 size=null 但用戶說大杯 =======
print("\n" + "=" * 70)
print("2. valid.jsonl:30 — 用英文分號多段，「大杯」在第 3 段但 size=null")
print("=" * 70)
print("  這是真正的 bug：用戶在第3段說「大杯」，但最終 size=null")
print("  intents=['order','other','order','modify'] — 但沒有 modify 將 size 設為 L")

# ======= Check: 「不合法品項」的 sugar/ice 是否正確設為 null =======
print("\n" + "=" * 70)
print("3. 不合法品項的 sugar/ice 處理是否一致")
print("=" * 70)

VALID_ITEMS = {"三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅",
               "朱槿普洱紅", "米香玉露菁", "青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"}

non_menu_null_count = 0
non_menu_has_value_count = 0
non_menu_issues = []

for filepath, fname in [("data/train.jsonl", "train"), ("data/valid.jsonl", "valid")]:
    rows = load_data(filepath)
    for line_num, user_msg, output in rows:
        for oi, order in enumerate(output.get("orders", [])):
            item = order.get("item")
            if item not in VALID_ITEMS:
                sugar = order.get("sugar")
                ice = order.get("ice")
                size = order.get("size")
                if sugar is None and ice is None and size is None:
                    non_menu_null_count += 1
                else:
                    non_menu_has_value_count += 1
                    non_menu_issues.append((fname, line_num, item, sugar, ice, size))

print(f"  非菜單品項 sugar/ice/size 全為 null: {non_menu_null_count} 筆")
print(f"  非菜單品項 sugar/ice/size 有非 null 值: {non_menu_has_value_count} 筆")
if non_menu_issues:
    print("  有值的案例：")
    for fname, line_num, item, sugar, ice, size in non_menu_issues[:5]:
        print(f"    [{fname}:{line_num}] item='{item}', sugar={sugar}, ice={ice}, size={size}")

# ======= Check: 232, 531 — intents 應該是 order+modify 而不是 order+order =======
print("\n" + "=" * 70)
print("4. 「先說大杯再改中杯」的 intents 標註")
print("=" * 70)

rows_train = load_data("data/train.jsonl")
for line_num, user_msg, output in rows_train:
    if line_num in [232, 531]:
        print(f"  [train:{line_num}] intents={output.get('intents')}")
        print(f"    user: '{user_msg}'")
        if "modify" not in output.get("intents", []):
            print(f"    ** 問題：第二段是修改行為但 intent 標為 order 而非 modify **")

# ======= Check: intents 中有多段但只有 order 的 modify 案例 =======
print("\n" + "=" * 70)
print("5. 多段中含修改語意但 intent 不含 modify 的案例")
print("=" * 70)

modify_keywords = ["改", "換", "取消", "不要了", "不用了", "拿掉", "去掉"]
issues_5 = []
for filepath, fname in [("data/train.jsonl", "train"), ("data/valid.jsonl", "valid")]:
    rows = load_data(filepath)
    for line_num, user_msg, output in rows:
        intents = output.get("intents", [])
        # Use both ; and ；
        if ";" in user_msg:
            segments = user_msg.split(";")
        elif "；" in user_msg:
            segments = user_msg.split("；")
        else:
            continue

        for seg_i, seg in enumerate(segments):
            seg = seg.strip()
            has_modify_keyword = any(kw in seg for kw in modify_keywords)
            if has_modify_keyword and seg_i < len(intents):
                if intents[seg_i] != "modify":
                    issues_5.append((fname, line_num, seg_i, intents[seg_i], seg, user_msg))

if issues_5:
    print(f"  發現 {len(issues_5)} 個案例：")
    for fname, line_num, seg_i, intent, seg, user_msg in issues_5[:15]:
        print(f"  [{fname}:{line_num}] segment[{seg_i}] intent='{intent}' 但含修改語意")
        print(f"    segment: '{seg}'")
        print(f"    full user: '{user_msg[:80]}'")
else:
    print("  未發現。")

# ======= Check: valid.jsonl:30 intents issue =======
print("\n" + "=" * 70)
print("6. valid.jsonl:30 intents 合理性")
print("=" * 70)
print("  user: '朱槿普洱紅;加奶;大杯;微糖少冰'")
print("  intents: ['order','other','order','modify']")
print("  第2段「加奶」intent='other' — 應為 modify（加奶是修改品項分類）")
print("  第3段「大杯」intent='order' — 應為 modify（加大尺寸是修改屬性）")
print("  第4段「微糖少冰」intent='modify' — 正確")
print("  但最大問題是 size=null，用戶明確說了大杯")
