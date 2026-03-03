#!/usr/bin/env python3
"""
修正審計發現的 17 個 violations。

修正項目：
1. R7-COMBO (5): 金杯蜜香紅 pure_tea → category=null（菜單無此組合）
2. R3-INTENT-BUG (6): 非菜單品項 intent=other+orders非空 → intents=["order"]
3. R1-ORDER (5): intent=order 但 orders=[] 矛盾
   - 推薦語境(2): → intents=["recommend"], 補 recommendations
   - 詢問語境(3): → intents=["other"], orders=[]
4. C2 (1): valid.jsonl 內部重複 → 刪除 line 341
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# 菜單品項（用於識別非菜單品項）
ALL_ITEMS = {
    "三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁",
    "琥珀鐵觀音", "金杯蜜香紅", "青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉",
}


def fix_file(fname, fixes, delete_lines=None):
    """修正指定檔案的指定行。fixes = {line_num: fix_func}"""
    path = DATA_DIR / fname
    with open(path) as f:
        lines = f.readlines()

    changed = 0
    deleted = 0
    delete_lines = delete_lines or set()

    new_lines = []
    for i, line in enumerate(lines, 1):
        if i in delete_lines:
            deleted += 1
            continue

        if i in fixes:
            sample = json.loads(line)
            sample = fixes[i](sample)
            new_lines.append(json.dumps(sample, ensure_ascii=False) + "\n")
            changed += 1
        else:
            new_lines.append(line)

    with open(path, "w") as f:
        f.writelines(new_lines)

    print(f"{fname}: {changed} 筆修正, {deleted} 筆刪除 (剩 {len(new_lines)} 筆)")


# ====== Fix 1: R7-COMBO — 金杯蜜香紅 pure_tea → null ======
def fix_r7_combo(sample):
    """金杯蜜香紅不存在 pure_tea 分類，改為 null。"""
    data = json.loads(sample["messages"][2]["content"])
    for o in data.get("orders", []):
        if o.get("item") == "金杯蜜香紅" and o.get("category") == "pure_tea":
            o["category"] = None
    sample["messages"][2]["content"] = json.dumps(data, ensure_ascii=False)
    return sample


# ====== Fix 2: R3-INTENT-BUG — 非菜單品項 intents=["order"] ======
def fix_r3_intent(sample):
    """非菜單品項：intents 改為 ["order"]，保留 orders 忠實輸出。"""
    data = json.loads(sample["messages"][2]["content"])
    data["intents"] = ["order"]
    sample["messages"][2]["content"] = json.dumps(data, ensure_ascii=False)
    return sample


# ====== Fix 3a: R1-ORDER 推薦語境 → recommend ======
def fix_r1_recommend_545(sample):
    """'給我一杯好喝的' → recommend"""
    data = json.loads(sample["messages"][2]["content"])
    data["intents"] = ["recommend"]
    data["orders"] = []
    data["preferences"] = {}
    data["recommendations"] = [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "花果蜜韻搭配鮮奶，清甜順口很受歡迎"}
    ]
    sample["messages"][2]["content"] = json.dumps(data, ensure_ascii=False)
    return sample


def fix_r1_recommend_89(sample):
    """'隨便來一杯' → recommend"""
    data = json.loads(sample["messages"][2]["content"])
    data["intents"] = ["recommend"]
    data["orders"] = []
    data["preferences"] = {}
    data["recommendations"] = [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶，天然蜜甜順口，大家都喜歡"}
    ]
    sample["messages"][2]["content"] = json.dumps(data, ensure_ascii=False)
    return sample


# ====== Fix 3b: R1-ORDER 詢問語境 → other ======
def fix_r1_other(sample):
    """詢價/詢問菜單 → other，清空所有欄位"""
    data = json.loads(sample["messages"][2]["content"])
    data["intents"] = ["other"]
    data["orders"] = []
    data["preferences"] = {}
    data["recommendations"] = []
    sample["messages"][2]["content"] = json.dumps(data, ensure_ascii=False)
    return sample


def main():
    import sys
    dry_run = "--dry-run" in sys.argv

    # train.jsonl 修正
    train_fixes = {
        # R7-COMBO: 金杯蜜香紅 pure_tea
        1445: fix_r7_combo,
        1446: fix_r7_combo,
        1447: fix_r7_combo,
        1448: fix_r7_combo,
        1449: fix_r7_combo,
        # R3-INTENT-BUG: 非菜單品項
        24: fix_r3_intent,
        438: fix_r3_intent,
        682: fix_r3_intent,
        768: fix_r3_intent,
        790: fix_r3_intent,
        # R1-ORDER: 推薦語境
        545: fix_r1_recommend_545,
        # R1-ORDER: 詢問語境
        706: fix_r1_other,
        713: fix_r1_other,
    }

    # valid.jsonl 修正
    valid_fixes = {
        # R3-INTENT-BUG: 非菜單品項
        33: fix_r3_intent,
        # R1-ORDER: 推薦語境
        89: fix_r1_recommend_89,
        # R1-ORDER: 詢問語境
        120: fix_r1_other,
    }
    valid_deletes = {341}  # C2: 重複

    print(f"Train fixes: {len(train_fixes)} 筆修正")
    print(f"Valid fixes: {len(valid_fixes)} 筆修正, {len(valid_deletes)} 筆刪除")

    if dry_run:
        print("\n[DRY RUN] 不寫入")
        # 驗證修正
        for fname, fixes in [("train.jsonl", train_fixes), ("valid.jsonl", valid_fixes)]:
            path = DATA_DIR / fname
            with open(path) as f:
                lines = f.readlines()
            for ln, fix_fn in fixes.items():
                sample = json.loads(lines[ln - 1])
                user = sample["messages"][1]["content"]
                old_data = json.loads(sample["messages"][2]["content"])
                fixed = fix_fn(json.loads(lines[ln - 1]))
                new_data = json.loads(fixed["messages"][2]["content"])
                print(f"\n  {fname}:{ln} [{user[:40]}]")
                print(f"    before: intents={old_data.get('intents')}, orders={len(old_data.get('orders',[]))}, recs={len(old_data.get('recommendations',[]))}")
                print(f"    after:  intents={new_data.get('intents')}, orders={len(new_data.get('orders',[]))}, recs={len(new_data.get('recommendations',[]))}")
        return

    fix_file("train.jsonl", train_fixes)
    fix_file("valid.jsonl", valid_fixes, delete_lines=valid_deletes)


if __name__ == "__main__":
    main()
