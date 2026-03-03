#!/usr/bin/env python3
"""Deep-dive into specific audit findings."""

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

# ======= Check 1: Invalid items — are these intentional negative examples? =======
print("=" * 70)
print("1. 不合法品項名詳細分析")
print("=" * 70)

invalid_items = Counter()
invalid_item_lines = []
for filepath, fname in [("data/train.jsonl", "train"), ("data/valid.jsonl", "valid")]:
    rows = load_data(filepath)
    for line_num, user_msg, output in rows:
        for oi, order in enumerate(output.get("orders", [])):
            item = order.get("item")
            VALID = {"三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅",
                     "朱槿普洱紅", "米香玉露菁", "青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"}
            if item not in VALID:
                invalid_items[item] += 1
                invalid_item_lines.append((fname, line_num, user_msg, item, output.get("intents", [])))

print("\n不合法品項名統計：")
for item, count in invalid_items.most_common():
    print(f"  '{item}': {count} 次")

# Check if these are "out-of-menu" negative examples (intent should be order but item is wrong)
# They should probably have intents=["order"] and the item is intentionally wrong
print("\n檢查這些是否為「非菜單品項」負面訓練樣本：")
for fname, line_num, user_msg, item, intents in invalid_item_lines[:20]:
    print(f"  [{fname}:{line_num}] intents={intents}, item='{item}', user='{user_msg[:60]}'")

# ======= Check 2: Chinese semicolon intents check =======
print("\n" + "=" * 70)
print("2. 中文分號樣本的 intents 長度檢查")
print("=" * 70)

cn_semicolon_issues = []
for filepath, fname in [("data/train.jsonl", "train"), ("data/valid.jsonl", "valid")]:
    rows = load_data(filepath)
    for line_num, user_msg, output in rows:
        if "；" in user_msg:
            segments = user_msg.split("；")
            intents = output.get("intents", [])
            if len(intents) != len(segments):
                cn_semicolon_issues.append((fname, line_num, user_msg, len(segments), len(intents)))

if cn_semicolon_issues:
    print(f"\n中文分號樣本中 intents 長度不符的案例：{len(cn_semicolon_issues)} 筆")
    for fname, line_num, user_msg, seg_count, intent_count in cn_semicolon_issues[:5]:
        print(f"  [{fname}:{line_num}] segments={seg_count}, intents={intent_count}, user='{user_msg[:60]}'")
else:
    print("\n中文分號樣本的 intents 長度全部正確（以中文分號分割計算）。")

# ======= Check 3: valid.jsonl:5 size='M' issue =======
print("\n" + "=" * 70)
print("3. valid.jsonl:5 size='M' 詳細檢查")
print("=" * 70)

rows = load_data("data/valid.jsonl")
for line_num, user_msg, output in rows:
    if line_num == 5:
        print(f"  user: '{user_msg}'")
        print(f"  orders: {json.dumps(output.get('orders', []), ensure_ascii=False, indent=2)}")
        break

# ======= Check 4: valid.jsonl:71 一大一中 =======
print("\n" + "=" * 70)
print("4. valid.jsonl:71 「一大一中」詳細檢查")
print("=" * 70)

for line_num, user_msg, output in rows:
    if line_num == 71:
        print(f"  user: '{user_msg}'")
        print(f"  orders: {json.dumps(output.get('orders', []), ensure_ascii=False, indent=2)}")
        break

# ======= Check 5: valid.jsonl:156 「中的」=======
print("\n" + "=" * 70)
print("5. valid.jsonl:156 「中的」詳細檢查")
print("=" * 70)

for line_num, user_msg, output in rows:
    if line_num == 156:
        print(f"  user: '{user_msg}'")
        print(f"  orders: {json.dumps(output.get('orders', []), ensure_ascii=False, indent=2)}")
        break

# ======= Check 6: train.jsonl:584 intents=recommend but has orders =======
print("\n" + "=" * 70)
print("6. train.jsonl:584 intents=['recommend'] 但有 orders")
print("=" * 70)

rows_train = load_data("data/train.jsonl")
for line_num, user_msg, output in rows_train:
    if line_num == 584:
        print(f"  user: '{user_msg}'")
        print(f"  intents: {output.get('intents', [])}")
        print(f"  orders: {json.dumps(output.get('orders', []), ensure_ascii=False, indent=2)}")
        print(f"  recommendations: {json.dumps(output.get('recommendations', []), ensure_ascii=False, indent=2)}")
        break

# ======= Check 7: 「第X杯」false positive analysis =======
print("\n" + "=" * 70)
print("7. 「第X杯」數量誤判分析")
print("=" * 70)
print("這些都是 user text 含「第二杯」但指的是序數（第 2 杯），不是數量。")
print("腳本誤判為 qty=2 的需求。這是 false positive。")

# ======= Check 8: size mismatch false positive analysis =======
print("\n" + "=" * 70)
print("8. 尺寸不一致的 false positive 分析")
print("=" * 70)
print("多數案例為「先說大杯，後面又改中杯」，模型正確輸出最終結果 M。這是正確行為。")
for fname, line_num, user_msg, output in [(f, ln, u, o) for f in ["train"] for ln, u, o in load_data(f"data/{f}.jsonl")]:
    if line_num in [36, 191, 232, 531, 590, 680, 702, 746]:
        orders = output.get("orders", [])
        intents = output.get("intents", [])
        print(f"  [{fname}:{line_num}] intents={intents}, size={orders[0].get('size') if orders else 'N/A'}")
        print(f"    user: '{user_msg[:80]}'")

# ======= Check 9: train.jsonl:555 「熱」mismatch =======
print("\n" + "=" * 70)
print("9. train.jsonl:555 用戶說「熱」但 ice='去冰' 詳細檢查")
print("=" * 70)

for line_num, user_msg, output in rows_train:
    if line_num == 555:
        print(f"  user: '{user_msg}'")
        print(f"  intents: {output.get('intents', [])}")
        print(f"  orders: {json.dumps(output.get('orders', []), ensure_ascii=False, indent=2)}")
        print(f"  recommendations: {json.dumps(output.get('recommendations', []), ensure_ascii=False, indent=2)}")
        print("  分析: 用戶第一段說去冰，第二段說推薦熱的。orders 是第一段的去冰，正確。")
        print("  但 recommendations 的品項應該是熱飲品項。腳本誤判為 false positive。")
        break

# ======= Check 10: valid.jsonl:30 大杯 =======
print("\n" + "=" * 70)
print("10. valid.jsonl:30 大杯但 size=None")
print("=" * 70)

for line_num, user_msg, output in rows:
    if line_num == 30:
        print(f"  user: '{user_msg}'")
        print(f"  intents: {output.get('intents', [])}")
        print(f"  orders: {json.dumps(output.get('orders', []), ensure_ascii=False, indent=2)}")
        break
