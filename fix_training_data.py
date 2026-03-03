#!/usr/bin/env python3
"""
Round 32 訓練資料一次性修正腳本。

修正清單：
  1. 中文分號 `；` → 英文 `;`（user text）
  2. preferences key 統一為英文
  3. modify intent 修正（含修改語意但標為 order → 改為 modify）
  4. 個別修正（valid:30, valid:5, train:584, train:555, train:565）

用法：
  python3 fix_training_data.py
"""

import json
import re
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ====== 常數 ======

PREF_KEY_MAP = {
    "口味": "taste",
    "溫度": "temperature",
    "場景": "scenario",
    "排除": "avoid",
    "分類": "category",
    "flavor": "taste",
}

MODIFY_KEYWORDS = ["改", "換", "不要了", "取消", "去掉", "拿掉", "升大杯"]
# 不算修改的 false positive（是規格指定）
EXCLUDE_PATTERNS = ["不要冰", "不要糖", "不要加"]

# fruit_tea 品項（ColdOnly，不可推薦給要熱飲的用戶）
FRUIT_TEA_ITEMS = {"青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"}


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def save_jsonl(path, samples):
    with open(path, "w") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def get_user(s):
    return next(m for m in s["messages"] if m["role"] == "user")


def get_assistant(s):
    return next(m for m in s["messages"] if m["role"] == "assistant")


def parse_assistant(s):
    return json.loads(get_assistant(s)["content"])


def set_assistant(s, data):
    get_assistant(s)["content"] = json.dumps(data, ensure_ascii=False)


# ====== 修正函數 ======


def fix_chinese_semicolons(samples, label):
    """中文分號 → 英文分號（user text only）"""
    count = 0
    for s in samples:
        user_msg = get_user(s)
        if "；" in user_msg["content"]:
            user_msg["content"] = user_msg["content"].replace("；", ";")
            count += 1
    print(f"  [{label}] 中文分號修正: {count} 筆")
    return count


def fix_preference_keys(samples, label):
    """preferences key 統一為英文"""
    count = 0
    for s in samples:
        data = parse_assistant(s)
        prefs = data.get("preferences", {})
        if not prefs:
            continue

        new_prefs = {}
        changed = False
        for k, v in prefs.items():
            new_key = PREF_KEY_MAP.get(k, k)
            if new_key != k:
                changed = True
            new_prefs[new_key] = v

        if changed:
            data["preferences"] = new_prefs
            set_assistant(s, data)
            count += 1

    print(f"  [{label}] preferences key 修正: {count} 筆")
    return count


def fix_modify_intents(samples, label):
    """含修改語意但 intent=order → 改為 modify"""
    count = 0
    for s in samples:
        user_text = get_user(s)["content"]
        data = parse_assistant(s)
        intents = data.get("intents", [])

        segments = user_text.split(";")
        if len(segments) != len(intents):
            continue

        changed = False
        for i, (seg, intent) in enumerate(zip(segments, intents)):
            if intent != "order":
                continue

            has_modify = any(kw in seg for kw in MODIFY_KEYWORDS)
            if not has_modify:
                continue

            is_false_positive = any(ex in seg for ex in EXCLUDE_PATTERNS)
            if is_false_positive:
                continue

            intents[i] = "modify"
            changed = True

        if changed:
            data["intents"] = intents
            set_assistant(s, data)
            count += 1

    print(f"  [{label}] modify intent 修正: {count} 筆")
    return count


# ====== 主程式 ======


def main():
    print("=" * 60)
    print("Round 32 訓練資料修正")
    print("=" * 60)

    # 備份
    for fname in ["train.jsonl", "valid.jsonl"]:
        src = DATA_DIR / fname
        dst = DATA_DIR / f"{fname}.bak"
        shutil.copy2(src, dst)
        print(f"備份: {src} → {dst}")

    # 載入
    train = load_jsonl(DATA_DIR / "train.jsonl")
    valid = load_jsonl(DATA_DIR / "valid.jsonl")
    print(f"載入: train={len(train)}, valid={len(valid)}")

    # ---- Step 2a: 中文分號 → 英文分號 ----
    print("\n--- Step 2a: 中文分號修正 ---")
    fix_chinese_semicolons(train, "train")
    fix_chinese_semicolons(valid, "valid")

    # ---- Step 2b: preferences key 修正 ----
    print("\n--- Step 2b: preferences key 修正 ---")
    fix_preference_keys(train, "train")
    fix_preference_keys(valid, "valid")

    # ---- Step 2c: modify intent 修正 ----
    # 注意：必須在中文分號修正之後，因為要用 ; 分割 segments
    print("\n--- Step 2c: modify intent 修正 ---")
    fix_modify_intents(train, "train")
    fix_modify_intents(valid, "valid")

    # ---- Step 2d: 個別修正 ----
    print("\n--- Step 2d: 個別修正 ---")

    # valid:30 (1-based) = index 29
    # user: 朱槿普洱紅;加奶;大杯;微糖少冰
    # intents: [order,other,order,modify] → [order,modify,modify,modify]
    # size: null → L
    v29 = valid[29]
    v29_data = parse_assistant(v29)
    v29_user = get_user(v29)["content"]
    assert "朱槿普洱紅" in v29_user and "大杯" in v29_user, \
        f"valid:30 內容不符預期: {v29_user}"
    v29_data["intents"] = ["order", "modify", "modify", "modify"]
    v29_data["orders"][0]["size"] = "L"
    set_assistant(v29, v29_data)
    print(f"  valid:30 — intents 修正 + size=L")

    # valid:5 (1-based) = index 4
    # 金杯蜜香紅 size=M → null（用戶未指定尺寸）
    v4 = valid[4]
    v4_data = parse_assistant(v4)
    v4_user = get_user(v4)["content"]
    assert "金杯蜜香紅" in v4_user, f"valid:5 內容不符預期: {v4_user}"
    for o in v4_data["orders"]:
        if o["item"] == "金杯蜜香紅" and o["size"] == "M":
            o["size"] = None
            print(f"  valid:5 — 金杯蜜香紅 size=M → null")
            break
    set_assistant(v4, v4_data)

    # train:555 (1-based) = index 554
    # 推薦果茶給要熱飲用戶 → 改為非果茶品項
    t554 = train[554]
    t554_data = parse_assistant(t554)
    t554_user = get_user(t554)["content"]
    assert "熱" in t554_user, f"train:555 內容不符預期: {t554_user}"
    for r in t554_data["recommendations"]:
        if r["item"] in FRUIT_TEA_ITEMS:
            r["item"] = "桂花輕烏龍"
            r["category"] = "pure_tea"
            r["reason"] = "桂花蜜韻輕柔，熱飲香氣更濃"
            print(f"  train:555 — 推薦改為桂花輕烏龍純茶")
            break
    set_assistant(t554, t554_data)

    # train:565 (1-based) = index 564
    # 推薦果茶給要熱飲用戶 → 改為非果茶品項
    t564 = train[564]
    t564_data = parse_assistant(t564)
    t564_user = get_user(t564)["content"]
    assert "熱" in t564_user, f"train:565 內容不符預期: {t564_user}"
    for r in t564_data["recommendations"]:
        if r["item"] in FRUIT_TEA_ITEMS:
            r["item"] = "朱槿普洱紅"
            r["category"] = "pure_tea"
            r["reason"] = "洛神酸甜暖胃，雨天暖身好選擇"
            print(f"  train:565 — 推薦改為朱槿普洱紅純茶")
            break
    set_assistant(t564, t564_data)

    # train:584 (1-based) = index 583
    # intents=['recommend'] 但有 orders → 刪除
    t583 = train[583]
    t583_user = get_user(t583)["content"]
    assert "可可" in t583_user, f"train:584 內容不符預期: {t583_user}"
    train.pop(583)
    print(f"  train:584 — 已刪除（intents/orders 矛盾）")

    # ---- 儲存 ----
    print(f"\n--- 儲存 ---")
    save_jsonl(DATA_DIR / "train.jsonl", train)
    save_jsonl(DATA_DIR / "valid.jsonl", valid)
    print(f"儲存: train={len(train)}, valid={len(valid)}")

    # ---- 驗證 ----
    print(f"\n--- 驗證 ---")

    # 重新載入驗證
    train2 = load_jsonl(DATA_DIR / "train.jsonl")
    valid2 = load_jsonl(DATA_DIR / "valid.jsonl")
    all_data = train2 + valid2

    # 中文分號
    cn_semi = sum(1 for s in all_data if "；" in get_user(s)["content"])
    print(f"  中文分號: {cn_semi} 筆 {'✓' if cn_semi == 0 else '✗'}")

    # preferences 中文 key
    cn_pref = 0
    flavor_count = 0
    for s in all_data:
        prefs = parse_assistant(s).get("preferences", {})
        for k in prefs:
            if any(ord(c) > 127 for c in k):
                cn_pref += 1
            if k == "flavor":
                flavor_count += 1
    print(f"  中文 preference key: {cn_pref} 筆 {'✓' if cn_pref == 0 else '✗'}")
    print(f"  flavor key: {flavor_count} 筆 {'✓' if flavor_count == 0 else '✗'}")

    # modify-as-order
    modify_as_order = 0
    for s in all_data:
        user_text = get_user(s)["content"]
        data = parse_assistant(s)
        intents = data.get("intents", [])
        segments = user_text.split(";")
        if len(segments) != len(intents):
            continue
        for seg, intent in zip(segments, intents):
            if intent != "order":
                continue
            has_modify = any(kw in seg for kw in MODIFY_KEYWORDS)
            if not has_modify:
                continue
            is_fp = any(ex in seg for ex in EXCLUDE_PATTERNS)
            if is_fp:
                continue
            modify_as_order += 1
    print(f"  modify-as-order: {modify_as_order} 筆 {'✓' if modify_as_order == 0 else '✗'}")

    # valid:30 check
    v29_check = parse_assistant(valid2[29])
    v29_ok = (v29_check["intents"] == ["order", "modify", "modify", "modify"]
              and v29_check["orders"][0]["size"] == "L")
    print(f"  valid:30 intents+size: {'✓' if v29_ok else '✗'}")

    # valid:5 check
    v4_check = parse_assistant(valid2[4])
    v4_ok = all(o["size"] != "M" for o in v4_check["orders"]
                if o["item"] == "金杯蜜香紅")
    print(f"  valid:5 size=null: {'✓' if v4_ok else '✗'}")

    # train:584 deleted → train count should be 1906
    t_ok = len(train2) == 1906
    print(f"  train:584 已刪除 (train={len(train2)}): {'✓' if t_ok else '✗'}")

    # train:555, 565 non-fruit-tea recommendations
    # After deleting train:583, indices shift: 554 stays, 564 becomes 563
    recs_ok = True
    for s in train2:
        user_text = get_user(s)["content"]
        data = parse_assistant(s)
        recs = data.get("recommendations", [])
        has_hot = any(k in user_text for k in ["熱"])
        for r in recs:
            if has_hot and r.get("item") in FRUIT_TEA_ITEMS:
                # 排除「好熱」「大熱天」這類不是要熱飲的
                prefs = data.get("preferences", {})
                if prefs.get("temperature") == "熱":
                    print(f"    ✗ 仍有果茶推薦給熱飲用戶: {user_text[:40]}")
                    recs_ok = False
    print(f"  熱飲不推果茶: {'✓' if recs_ok else '✗'}")

    print(f"\n{'='*60}")
    print("修正完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
