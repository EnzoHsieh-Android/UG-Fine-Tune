#!/usr/bin/env python3
"""
訓練資料品質審計腳本（依 finetune-optimization skill 2.3~2.5）。
檢查 train.jsonl + valid.jsonl 的所有規則一致性。

用法:
  python audit_training_data.py
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

DATA_DIR = Path(__file__).parent / "data"

# ====== 菜單定義（與 menu.go 一致）======

MENU_CATEGORIES = {
    "pure_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁"],
    "fresh_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "rich_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "fruit_tea": ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"],
    "cloud_velvet": ["桂花輕烏龍", "茶花紅烏龍"],
}

ALL_ITEMS = set()
for items in MENU_CATEGORIES.values():
    ALL_ITEMS.update(items)

VALID_COMBOS = set()
for cat, items in MENU_CATEGORIES.items():
    for item in items:
        VALID_COMBOS.add((item, cat))

SINGLE_SIZE_CATS = {"pure_tea", "cloud_velvet", "fruit_tea"}
COLD_ONLY_CATS = {"fruit_tea"}

VALID_SUGARS = {
    "全糖", "五分糖", "三分糖", "一分糖", "無糖",
    "正常糖", "半糖", "少糖", "微糖", None,
}

VALID_ICES = {"正常冰", "少冰", "微冰", "去冰", "熱飲", None}
VALID_SIZES = {"M", "L", None}
VALID_ADDONS = {"紅烏龍茶凍", "燕麥粒"}
VALID_INTENTS = {"order", "recommend", "modify", "other"}

# ====== Category keyword extraction (for D4-TEXT-CAT) ======

CAT_KEYWORDS_PRIORITY = ["鮮奶茶", "純茶", "奶蓋", "奶精", "奶茶"]
CAT_KEYWORD_MAP = {
    "鮮奶茶": "fresh_milk_tea",
    # 「鮮奶」已永久禁止（C5 規則）：鮮奶茶就是鮮奶茶，不允許口語化「鮮奶」
    "奶茶": "rich_milk_tea",
    "奶精": "rich_milk_tea",
    "純茶": "pure_tea",
    "奶蓋": "cloud_velvet",
}


def extract_cat_keywords(text):
    """Extract category keywords from text, longer-match-first to avoid overlaps."""
    found = []
    covered = set()
    for kw in CAT_KEYWORDS_PRIORITY:
        start = 0
        while True:
            pos = text.find(kw, start)
            if pos == -1:
                break
            positions = set(range(pos, pos + len(kw)))
            if not positions & covered:
                found.append(CAT_KEYWORD_MAP[kw])
                covered |= positions
            start = pos + 1
    return found


def load_data():
    """載入 train + valid，附上來源資訊。"""
    samples = []
    for fname in ["train.jsonl", "valid.jsonl"]:
        path = DATA_DIR / fname
        with open(path) as f:
            for i, line in enumerate(f, 1):
                s = json.loads(line)
                s["_src"] = fname
                s["_ln"] = i
                samples.append(s)
    return samples


def loc(s):
    return f"{s['_src']}:{s['_ln']}"


def run_audit():
    samples = load_data()
    V = defaultdict(list)  # violations: rule_id → [(loc, detail)]

    # Aggregate data for distribution checks (D1-D3)
    mt_null_count = 0      # multi-turn with null+explicit categories
    mt_explicit_count = 0  # multi-turn with all explicit categories
    mt_seg1_cats = []      # seg1 category for null-pattern samples
    item_cat_dist = defaultdict(Counter)  # for D3 + cross-category matrix

    # ================================================================
    # 2.3 資料清洗檢查
    # ================================================================

    # ---- C1: System prompt 一致性 ----
    prompts = set()
    for s in samples:
        prompts.add(next(m for m in s["messages"] if m["role"] == "system")["content"])
    c1_ok = len(prompts) == 1
    print(f"[C1] System Prompt 一致性: {'✓' if c1_ok else '✗'} ({len(prompts)} 種)")
    if not c1_ok:
        V["C1"].append(("global", f"{len(prompts)} 種不同 system prompt"))

    # ---- C2: 無重複 user message ----
    user_counter = Counter()
    user_locs = defaultdict(list)
    user_outputs = defaultdict(set)  # user → set of assistant outputs
    for s in samples:
        u = next(m for m in s["messages"] if m["role"] == "user")["content"]
        a = next(m for m in s["messages"] if m["role"] == "assistant")["content"]
        user_counter[u] += 1
        user_locs[u].append(loc(s))
        user_outputs[u].add(a)
    dupes = {k: v for k, v in user_counter.items() if v > 1}
    conflicts = {k for k in dupes if len(user_outputs[k]) > 1}
    exact_dupes = {k for k in dupes if k not in conflicts}
    print(f"[C2] 重複 User Message: {'✓ 無重複' if not dupes else f'✗ {len(dupes)} 筆重複'}")
    for msg, cnt in sorted(dupes.items(), key=lambda x: -x[1]):
        V["C2"].append((user_locs[msg][0], f"[{cnt}x] {msg[:60]}"))

    # ---- C2b: 同 user text 不同 output（訓練衝突）----
    if conflicts:
        print(f"[C2b] ⚠️ 訓練衝突（同 user 不同 output）: {len(conflicts)} 筆")
        for msg in list(conflicts)[:5]:
            V["C2b-CONFLICT"].append((user_locs[msg][0], f"衝突: {msg[:60]}"))
    else:
        print(f"[C2b] 訓練衝突: ✓ 無衝突")

    # ---- C3: Train/Valid 洩漏 ----
    train_u = {next(m for m in s["messages"] if m["role"] == "user")["content"]
               for s in samples if s["_src"] == "train.jsonl"}
    valid_u = {next(m for m in s["messages"] if m["role"] == "user")["content"]
               for s in samples if s["_src"] == "valid.jsonl"}
    leaks = train_u & valid_u
    print(f"[C3] Train/Valid 洩漏: {'✓ 無洩漏' if not leaks else f'✗ {len(leaks)} 筆'}")
    for msg in list(leaks)[:5]:
        V["C3"].append(("global", msg[:60]))

    # ---- C5: 禁止獨立「鮮奶」（憲法級規則）----
    # 「鮮奶茶」是唯一合法用語，「鮮奶」作為口語化縮寫永久禁止
    c5_violations = []
    for s in samples:
        u = next(m for m in s["messages"] if m["role"] == "user")["content"]
        cleaned = u.replace("鮮奶茶", "___")
        if "鮮奶" in cleaned:
            c5_violations.append((loc(s), f"含獨立「鮮奶」: {u[:60]}"))
    if c5_violations:
        print(f"[C5] 禁止獨立「鮮奶」: ✗ {len(c5_violations)} 筆")
        V["C5-BANNED-鮮奶"] = c5_violations
    else:
        print(f"[C5] 禁止獨立「鮮奶」: ✓ 0 筆")

    # ================================================================
    # 2.5 System Prompt ↔ 訓練資料自洽性審計
    # ================================================================

    print("\n--- 規則逐筆審計 ---")

    for s in samples:
        assistant_raw = next(m for m in s["messages"] if m["role"] == "assistant")["content"]
        user = next(m for m in s["messages"] if m["role"] == "user")["content"]
        l = loc(s)

        # R0: JSON 可解析
        try:
            data = json.loads(assistant_raw)
        except json.JSONDecodeError:
            V["R0-JSON"].append((l, f"JSON parse 失敗: {assistant_raw[:80]}"))
            continue

        intents = data.get("intents", [])
        orders = data.get("orders", [])
        recs = data.get("recommendations", [])
        prefs = data.get("preferences")

        # R0b: 必要 key 存在
        for key in ["intents", "orders", "preferences", "recommendations"]:
            if key not in data:
                V["R0-KEY"].append((l, f"缺少 '{key}'"))

        # ---- Intents 規則 ----

        # R-I1: intents 長度 = 分號數 + 1（半形 ; 或全形 ；）
        semicolons = user.count(";") + user.count("；")
        if len(intents) != semicolons + 1:
            V["R-I1-LEN"].append((l, f"len={len(intents)}≠{semicolons+1}: {user[:50]}"))

        # R-I2: intents 值域
        for idx, intent in enumerate(intents):
            if intent not in VALID_INTENTS:
                V["R-I2-VAL"].append((l, f"intents[{idx}]='{intent}'"))

        # ---- Intent-Content 一致性 ----

        has_order = any(i in ("order", "modify") for i in intents)
        has_rec = "recommend" in intents
        all_other = all(i == "other" for i in intents) and intents

        # R1: 有 order intent + 無 recommend → orders 非空, recs 空
        # 例外：最後 intent=modify 且 orders=[] 表示全部取消，合法
        last_intent = intents[-1] if intents else ""
        if has_order and not has_rec:
            if not orders and last_intent not in ("modify", "other"):
                V["R1-ORDER"].append((l, f"order intent 但 orders=[]: {user[:50]}"))
            if recs:
                V["R1-REC"].append((l, f"純 order 但 recs 非空: {user[:50]}"))

        # R2: intents 含 recommend → recommendations 必須非空
        if has_rec and not recs:
            V["R2-REC"].append((l, f"recommend intent 但 recs=[]: {user[:50]}"))

        # R3: 閒聊 → orders + recs 皆空
        # 例外：非菜單品項 intent=other + orders 非空 → 改標為 R3-INTENT-BUG
        if all_other:
            if orders:
                # 非菜單品項忠實輸出 → intent 應為 order，標記為 intent bug
                non_menu = [o.get("item", "") for o in orders if o.get("item", "") not in ALL_ITEMS]
                if non_menu:
                    V["R3-INTENT-BUG"].append((l, f"非菜單品項 intent 應為 order: {non_menu}: {user[:50]}"))
                else:
                    V["R3-OTHER"].append((l, f"other 但 orders 非空（菜單品項）: {user[:50]}"))
            if recs:
                V["R3-OTHER"].append((l, f"other 但 recs 非空: {user[:50]}"))

        # R4: preferences 型別 = dict
        if prefs is not None and not isinstance(prefs, dict):
            V["R4-PREF"].append((l, f"preferences 不是 dict: {type(prefs).__name__}"))

        # R5: recommendations ≤ 1 項
        if len(recs) > 1:
            V["R5-REC-CNT"].append((l, f"recs 有 {len(recs)} 項 (限 1): {user[:50]}"))

        # ---- Orders 逐筆檢查 ----

        for oi, order in enumerate(orders):
            item = order.get("item", "")
            cat = order.get("category")
            size = order.get("size")
            ice = order.get("ice")
            sugar = order.get("sugar")
            addon = order.get("addon", [])
            qty = order.get("qty")

            # R6: 品項名稱（非菜單品項為預期行為，僅統計不報 violation）
            if item not in ALL_ITEMS:
                V["R6-INFO"].append((l, f"[{oi}] item='{item}'"))

            # R7: (item, category) 合法組合
            if cat is not None and item in ALL_ITEMS:
                if (item, cat) not in VALID_COMBOS:
                    V["R7-COMBO"].append((l, f"[{oi}] ({item}, {cat})"))

            # R7b: category 值域
            if cat is not None and cat not in MENU_CATEGORIES:
                V["R7b-CAT"].append((l, f"[{oi}] category='{cat}'"))

            # R8: 單一尺寸分類 → size=null
            if cat in SINGLE_SIZE_CATS and size is not None:
                V["R8-SIZE"].append((l, f"[{oi}] {cat} size={size}"))

            # R8b: size 值域
            if size not in VALID_SIZES:
                V["R8b-SIZE"].append((l, f"[{oi}] size='{size}'"))

            # R9: sugar 值域
            if sugar not in VALID_SUGARS:
                V["R9-SUGAR"].append((l, f"[{oi}] sugar='{sugar}'"))

            # R10: ice 值域
            if ice not in VALID_ICES:
                V["R10-ICE"].append((l, f"[{oi}] ice='{ice}'"))

            # R11: addon 合法（值域 + 型別）
            if not isinstance(addon, list):
                V["R11-ADDON-TYPE"].append((l, f"[{oi}] addon 不是 list: {type(addon).__name__}"))
            else:
                for a in addon:
                    if a not in VALID_ADDONS:
                        V["R11-ADDON"].append((l, f"[{oi}] addon='{a}'"))

            # R12: qty ≥ 1
            if not isinstance(qty, int) or qty < 1:
                V["R12-QTY"].append((l, f"[{oi}] qty={qty}"))

            # R13: order 必要欄位
            for field in ["item", "category", "size", "ice", "sugar", "addon", "qty", "note"]:
                if field not in order:
                    V["R13-FIELD"].append((l, f"[{oi}] 缺少 '{field}'"))

            # R14: ColdOnly — fruit_tea 不可熱飲
            if cat in COLD_ONLY_CATS and ice == "熱飲":
                V["R14-COLD"].append((l, f"[{oi}] {cat} item={item} ice=熱飲"))

            # R15: 非菜單品項 + category!=null（應為照錄 + null）
            if item not in ALL_ITEMS and cat is not None:
                V["R15-NONMENU-CAT"].append((l, f"[{oi}] 非菜單品項 '{item}' 卻有 category='{cat}'"))

            # R16: note 型別 = string
            note = order.get("note")
            if note is not None and not isinstance(note, str):
                V["R16-NOTE"].append((l, f"[{oi}] note 不是 str: {type(note).__name__}"))

        # ---- Recommendations 逐筆檢查 ----
        for ri, rec in enumerate(recs):
            r_item = rec.get("item", "")
            r_cat = rec.get("category")

            if r_item not in ALL_ITEMS:
                V["R6-REC-ITEM"].append((l, f"recs[{ri}] item='{r_item}'"))

            if r_cat is not None and r_item in ALL_ITEMS:
                if (r_item, r_cat) not in VALID_COMBOS:
                    V["R7-REC-COMBO"].append((l, f"recs[{ri}] ({r_item}, {r_cat})"))

            for field in ["item", "category", "reason"]:
                if field not in rec:
                    V["R13-REC-FIELD"].append((l, f"recs[{ri}] 缺少 '{field}'"))

            # R17: recommendation reason 非空
            r_reason = rec.get("reason", "")
            if isinstance(r_reason, str) and r_reason.strip() == "":
                V["R17-REC-REASON"].append((l, f"recs[{ri}] reason 為空"))

        # ---- D4-TEXT-CAT: User text category keyword vs output category ----
        # 兩層檢查，只在無 modify intent 時執行（取消/修改會移除 category，導致誤報）
        has_modify = "modify" in intents
        if orders and not has_modify:
            # Mask non-menu item names to avoid false keyword matches
            masked_user = user
            for o in orders:
                nm_item = o.get("item", "")
                if nm_item not in ALL_ITEMS and nm_item in masked_user:
                    masked_user = masked_user.replace(nm_item, "\x00" * len(nm_item))

            # Only extract keywords from "order" intent segments
            segments = masked_user.split(";")
            text_cats = set()
            for seg_idx, seg in enumerate(segments):
                seg_intent = intents[seg_idx] if seg_idx < len(intents) else "order"
                if seg_intent == "order":
                    text_cats.update(extract_cat_keywords(seg))

            if text_cats:
                menu_orders = [(o.get("item"), o.get("category"))
                               for o in orders if o.get("item") in ALL_ITEMS]
                menu_items = [item for item, _ in menu_orders]
                unique_menu = set(menu_items)

                if len(unique_menu) == 1:
                    the_item = next(iter(unique_menu))
                    supported = {c for c, its in MENU_CATEGORIES.items()
                                 if the_item in its}
                    expected = text_cats & supported

                    if len(menu_items) > 1:
                        # Tier 2: 同品項多筆 — 檢查所有 expected cats 都在 output
                        output_cats = {cat for _, cat in menu_orders
                                       if cat is not None}
                        missing = expected - output_cats
                        if missing:
                            V["D4-TEXT-CAT"].append(
                                (l, f"{the_item}: text 含 {missing} "
                                     f"但 output 無: {user[:60]}"))
                    elif len(expected) == 1:
                        # Tier 1: 單筆菜單品項 — keyword 應匹配 category
                        the_cat = menu_orders[0][1]
                        exp_cat = next(iter(expected))
                        if the_cat is None:
                            V["D4-TEXT-CAT"].append(
                                (l, f"{the_item}: text 含 {exp_cat} "
                                     f"但 category=null: {user[:60]}"))
                        elif the_cat != exp_cat:
                            V["D4-TEXT-CAT"].append(
                                (l, f"{the_item}: text 含 {exp_cat} "
                                     f"但 category={the_cat}: {user[:60]}"))

        # ---- Accumulate item_cat_dist (for D3 + cross-category matrix) ----
        for o in orders:
            it = o.get("item", "")
            ct = o.get("category") or "null"
            if it in ALL_ITEMS:
                item_cat_dist[it][ct] += 1

        # ---- Collect multi-turn stats for D1-D2 ----
        if ";" in user and len(orders) >= 2:
            has_null = any(o.get("category") is None for o in orders)
            has_explicit = any(o.get("category") is not None for o in orders)
            all_explicit_cats = all(o.get("category") is not None for o in orders)

            if has_null and has_explicit:
                mt_null_count += 1
                seg1 = user.split(";")[0]
                seg1_cat_found = None
                for kw in CAT_KEYWORDS_PRIORITY:
                    if kw in seg1:
                        seg1_cat_found = CAT_KEYWORD_MAP[kw]
                        break
                if seg1_cat_found is None:
                    for fi in ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"]:
                        if fi in seg1:
                            seg1_cat_found = "fruit_tea"
                            break
                if seg1_cat_found:
                    mt_seg1_cats.append(seg1_cat_found)
            elif all_explicit_cats:
                mt_explicit_count += 1

    # ================================================================
    # 分佈健康度檢查 (D1-D3)
    # ================================================================

    # D1: 多輪 null category 比例 — 過低表示模型傾向總是填 category
    mt_total = mt_null_count + mt_explicit_count
    if mt_total > 0:
        null_ratio = mt_null_count / mt_total
        if null_ratio < 0.35:
            V["D1-NULL-RATIO"].append(
                ("分佈", f"多輪 null 佔比 {null_ratio:.1%} < 35% "
                         f"(null={mt_null_count}, explicit={mt_explicit_count})"))

    # D2: 多輪 seg1 category 均衡度 — 過度集中會讓模型只學到特定 category 不洩漏
    if mt_seg1_cats:
        seg1_counter = Counter(mt_seg1_cats)
        seg1_total = sum(seg1_counter.values())
        for cat, cnt in seg1_counter.most_common():
            pct = cnt / seg1_total
            if pct > 0.50:
                V["D2-SEG1-BALANCE"].append(
                    ("分佈", f"seg1 category '{cat}' 佔 {pct:.0%} "
                             f"({cnt}/{seg1_total}) > 50%"))

    # D3: 跨分類覆蓋度 — 有效組合過低可能導致模型不認識該組合
    multi_items = sorted([it for it in ALL_ITEMS
                          if sum(1 for c, items in MENU_CATEGORIES.items() if it in items) > 1])
    for item in multi_items:
        supported_cats = [c for c, items in MENU_CATEGORIES.items() if item in items]
        dist = item_cat_dist[item]
        total = sum(dist.values())
        if total < 20:
            continue
        for cat in supported_cats:
            cnt = dist.get(cat, 0)
            pct = cnt / total
            if pct < 0.05:
                V["D3-CAT-COVERAGE"].append(
                    ("分佈", f"({item}, {cat}): {pct:.1%} ({cnt}/{total}) < 5%"))

    # ================================================================
    # 報告
    # ================================================================

    # 分離 INFO（預期行為）和 VIOLATION（需修正）
    info_keys = {k for k in V if k.endswith("-INFO")}
    real_V = {k: v for k, v in V.items() if k not in info_keys}
    total_v = sum(len(v) for v in real_V.values())

    print(f"\n{'='*60}")
    if total_v == 0:
        print(f"✅ 審計通過！0 violations（{len(samples)} 筆樣本）")
    else:
        print(f"❌ {total_v} violations\n")
        for rule in sorted(real_V.keys()):
            items = real_V[rule]
            print(f"  [{rule}] {len(items)} 筆:")
            for location, detail in items[:8]:
                print(f"    {location}: {detail}")
            if len(items) > 8:
                print(f"    ... 還有 {len(items)-8} 筆")
            print()

    # INFO 統計
    if info_keys:
        print("--- INFO（預期行為）---")
        for k in sorted(info_keys):
            print(f"  [{k}] {len(V[k])} 筆（非菜單品項忠實輸出）")

    # ================================================================
    # 2.4 跨分類矩陣
    # ================================================================

    print(f"{'='*60}")
    print("跨分類矩陣（多分類品項）")
    print(f"{'='*60}")

    # item_cat_dist + multi_items already computed above (D3 section)
    cats = ["pure_tea", "fresh_milk_tea", "rich_milk_tea", "cloud_velvet", "null"]

    header = f"{'品項':12s}" + "".join(f"{c:>16s}" for c in cats) + f"{'total':>8s}"
    print(header)
    print("-" * len(header))

    for item in multi_items:
        dist = item_cat_dist[item]
        total = sum(dist.values())
        row = f"{item:12s}"
        for c in cats:
            cnt = dist.get(c, 0)
            if cnt:
                pct = cnt / total * 100
                row += f"{cnt:>8d}({pct:4.0f}%)"
            else:
                row += f"{'--':>13s}   "
        row += f"{total:>8d}"
        print(row)

    # ================================================================
    # 摘要
    # ================================================================

    n_train = sum(1 for s in samples if s["_src"] == "train.jsonl")
    n_valid = sum(1 for s in samples if s["_src"] == "valid.jsonl")
    print(f"\n{'='*60}")
    print(f"審計摘要: {len(samples)} 筆 (train {n_train}, valid {n_valid}), {total_v} violations")
    print(f"{'='*60}")

    return total_v


if __name__ == "__main__":
    exit(0 if run_audit() == 0 else 1)
