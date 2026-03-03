#!/usr/bin/env python3
"""Final targeted audit checks."""

import json

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

rows_train = load_data("data/train.jsonl")
rows_valid = load_data("data/valid.jsonl")

# ======= Check train:565 =======
print("=" * 70)
print("1. train:565 推薦果茶但用戶想喝熱飲")
print("=" * 70)
for line_num, user_msg, output in rows_train:
    if line_num == 565:
        print(f"  user: '{user_msg}'")
        print(f"  intents: {output.get('intents')}")
        print(f"  prefs: {output.get('preferences')}")
        print(f"  recs: {json.dumps(output.get('recommendations'), ensure_ascii=False)}")
        print("  ** 果茶是冷飲，不適合推薦給想喝熱飲的用戶 **")

# ======= Check train:834,838 =======
print("\n" + "=" * 70)
print("2. train:834,838 — 用戶想冰的但推薦果茶（這其實是正確的）")
print("=" * 70)
for line_num, user_msg, output in rows_train:
    if line_num in [834, 838]:
        print(f"  [train:{line_num}] user: '{user_msg}'")
        print(f"    prefs: {output.get('preferences')}")
        print(f"    recs: {json.dumps(output.get('recommendations'), ensure_ascii=False)}")
        print("    (含「熱」字但語意是「天氣熱→想喝冰的」，推薦果茶是合理的)")

# ======= Check: preferences 格式一致性 =======
print("\n" + "=" * 70)
print("3. preferences 欄位格式一致性檢查")
print("=" * 70)

pref_keys = set()
for filepath, fname, rows in [("train", "train", rows_train), ("valid", "valid", rows_valid)]:
    for line_num, user_msg, output in rows:
        prefs = output.get("preferences", {})
        if prefs:
            for k in prefs.keys():
                pref_keys.add(k)

print(f"  所有出現過的 preferences key: {sorted(pref_keys)}")

# Check if there are mixed Chinese/English keys
cn_keys = set()
en_keys = set()
for k in pref_keys:
    if any('\u4e00' <= c <= '\u9fff' for c in k):
        cn_keys.add(k)
    else:
        en_keys.add(k)

if cn_keys and en_keys:
    print(f"  ** 混用中英文 key! **")
    print(f"    中文 key: {cn_keys}")
    print(f"    英文 key: {en_keys}")

    # Count occurrences
    cn_count = 0
    en_count = 0
    mixed_lines = []
    for filepath, fname, rows in [("train", "train", rows_train), ("valid", "valid", rows_valid)]:
        for line_num, user_msg, output in rows:
            prefs = output.get("preferences", {})
            if prefs:
                has_cn = any(any('\u4e00' <= c <= '\u9fff' for c in k) for k in prefs.keys())
                has_en = any(not any('\u4e00' <= c <= '\u9fff' for c in k) for k in prefs.keys())
                if has_cn:
                    cn_count += 1
                if has_en:
                    en_count += 1
    print(f"    含中文 key 的樣本數: {cn_count}")
    print(f"    含英文 key 的樣本數: {en_count}")

# ======= Check: intents 標註中 modify vs order 的邊界案例 =======
print("\n" + "=" * 70)
print("4. train:18 詳細檢查")
print("=" * 70)
for line_num, user_msg, output in rows_train:
    if line_num == 18:
        print(f"  user: '{user_msg}'")
        print(f"  intents: {output.get('intents')}")
        print(f"  orders: {json.dumps(output.get('orders'), ensure_ascii=False, indent=2)}")
        break

# ======= Check: train:68 =======
print("\n" + "=" * 70)
print("5. train:68 詳細檢查")
print("=" * 70)
for line_num, user_msg, output in rows_train:
    if line_num == 68:
        print(f"  user: '{user_msg}'")
        print(f"  intents: {output.get('intents')}")
        print(f"  orders: {json.dumps(output.get('orders'), ensure_ascii=False, indent=2)}")
        break

# ======= Check: valid.jsonl:30 =======
print("\n" + "=" * 70)
print("6. train:462 用戶點綠茶→換三窨十五茉的完整流程")
print("=" * 70)
for line_num, user_msg, output in rows_train:
    if line_num == 462:
        print(f"  user: '{user_msg}'")
        print(f"  intents: {output.get('intents')}")
        print(f"  orders: {json.dumps(output.get('orders'), ensure_ascii=False, indent=2)}")
        break

# ======= Check: train:573 =======
print("\n" + "=" * 70)
print("7. train:573 「換鮮奶的」")
print("=" * 70)
for line_num, user_msg, output in rows_train:
    if line_num == 573:
        print(f"  user: '{user_msg}'")
        print(f"  intents: {output.get('intents')}")
        print(f"  orders: {json.dumps(output.get('orders'), ensure_ascii=False, indent=2)}")
        break
