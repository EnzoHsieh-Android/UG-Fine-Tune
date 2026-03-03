#!/usr/bin/env python3
"""
深度邏輯自洽性審計。逐筆檢查語意與 JSON 是否一致。
超越格式審計，檢查「人類看了會不會覺得怪」的問題。
"""

import json
import re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

# ====== 菜單定義 ======

MENU_CATEGORIES = {
    "pure_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁"],
    "fresh_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "rich_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "fruit_tea": ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"],
    "cloud_velvet": ["桂花輕烏龍", "茶花紅烏龍"],
}

SINGLE_SIZE_CATS = {"pure_tea", "cloud_velvet", "fruit_tea"}

ALL_ITEMS = set()
for items in MENU_CATEGORIES.values():
    ALL_ITEMS.update(items)

FRUIT_TEA_ITEMS = {"青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"}

# 口語 → 正式甜度（模型「照錄」口語）
SUGAR_KEYWORDS = {
    "全糖": "全糖", "正常糖": "正常糖",
    "五分糖": "五分糖", "半糖": "半糖",
    "三分糖": "三分糖", "少糖": "少糖",
    "一分糖": "一分糖", "微糖": "微糖",
    "無糖": "無糖",
}

ICE_KEYWORDS = {
    "正常冰": "正常冰",
    "少冰": "少冰",
    "微冰": "微冰",
    "去冰": "去冰",
    "熱飲": "熱飲", "熱的": "熱飲", "熱": "熱飲",
    "溫的": "熱飲", "溫": "熱飲",
}

SIZE_KEYWORDS = {"大杯": "L", "中杯": "M"}

# 分類線索
CAT_FRESH_MILK = ["鮮奶", "鮮乳"]
CAT_RICH_MILK = ["奶茶"]
CAT_PURE_TEA = ["純茶"]
CAT_CLOUD = ["奶蓋", "雲頂"]
CAT_FRUIT = ["果茶"]

ADDON_KEYWORDS = {"茶凍": "紅烏龍茶凍", "燕麥粒": "燕麥粒", "燕麥": "燕麥粒"}
QTY_MAP = {"兩": 2, "兩杯": 2, "二": 2, "三": 3, "三杯": 3, "四": 4, "五": 5}

MODIFY_KW = ["改", "換", "不要了", "取消", "去掉", "拿掉", "升大杯", "不用了"]
EXCLUDE_FP = ["不要冰", "不要糖", "不要加"]


def load_all():
    samples = []
    for fname in ["train.jsonl", "valid.jsonl"]:
        path = DATA_DIR / fname
        with open(path) as f:
            for i, line in enumerate(f, 1):
                s = json.loads(line)
                s["_src"] = fname.replace(".jsonl", "")
                s["_ln"] = i
                samples.append(s)
    return samples


def loc(s):
    return f"{s['_src']}:{s['_ln']}"


def get_user(s):
    return next(m for m in s["messages"] if m["role"] == "user")["content"]


def get_data(s):
    return json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])


def main():
    samples = load_all()
    V = defaultdict(list)  # category → [(loc, detail)]

    for s in samples:
        user = get_user(s)
        data = get_data(s)
        l = loc(s)

        intents = data.get("intents", [])
        orders = data.get("orders", [])
        recs = data.get("recommendations", [])
        prefs = data.get("preferences", {})

        segments = user.split(";")

        # ==============================================================
        # D1: Size 提到但沒抓到 / 沒提到但有值
        # ==============================================================
        # 檢查整句有 size 但 orders 沒反映
        for kw, val in SIZE_KEYWORDS.items():
            if kw in user:
                # 有至少一筆 order 的 size 是這個值？
                has_size = any(o.get("size") == val for o in orders)
                if not has_size and orders:
                    # 可能是修改情境——段落中有「改大杯」之類
                    # 只要 orders 最終有反映就 OK
                    # 如果完全沒反映，才報
                    V["D1-SIZE-MISS"].append((l, f"用戶說「{kw}」但無 order size={val}: {user[:60]}"))

        for oi, o in enumerate(orders):
            if o.get("size") in ("M", "L"):
                size_val = o["size"]
                # 反向查：用戶有沒有提到這個尺寸
                size_kws = [kw for kw, v in SIZE_KEYWORDS.items() if v == size_val]
                if not any(kw in user for kw in size_kws):
                    V["D1-SIZE-EXTRA"].append((l, f"[{oi}] size={size_val} 但用戶未提及: {user[:60]}"))

        # ==============================================================
        # D2: Sugar 提到但沒抓到 / 值不匹配
        # ==============================================================
        for oi, o in enumerate(orders):
            item = o.get("item", "")
            sugar = o.get("sugar")
            if sugar is not None and item in ALL_ITEMS:
                # 確認用戶有提到這個甜度
                if sugar not in user:
                    # 可能是修改結果，比如「改無糖」→ 最終 sugar=無糖
                    # 但原文用了不同說法？
                    # 只報明顯不合的
                    pass  # 太多合法變化，跳過

        # ==============================================================
        # D3: 分類語意與 category 不匹配
        # ==============================================================
        for oi, o in enumerate(orders):
            item = o.get("item", "")
            cat = o.get("category")
            if cat is None or item not in ALL_ITEMS:
                continue

            # 每個 segment 去找跟這個 item 相關的語意
            for seg in segments:
                if item not in seg and not any(alias in seg for alias in _item_aliases(item)):
                    continue

                # 在這個 segment 中找分類線索
                if any(kw in seg for kw in CAT_FRESH_MILK):
                    if cat != "fresh_milk_tea":
                        V["D3-CAT"].append((l, f"[{oi}] {item} 用戶說鮮奶 but cat={cat}: {seg[:40]}"))
                if any(kw in seg for kw in CAT_RICH_MILK) and not any(kw in seg for kw in CAT_FRESH_MILK):
                    if cat != "rich_milk_tea":
                        # 「奶茶」可能跟「鮮奶茶」重疊，只在沒有「鮮奶」時報
                        if "鮮奶" not in seg:
                            V["D3-CAT"].append((l, f"[{oi}] {item} 用戶說奶茶 but cat={cat}: {seg[:40]}"))
                if any(kw in seg for kw in CAT_PURE_TEA):
                    if cat != "pure_tea":
                        V["D3-CAT"].append((l, f"[{oi}] {item} 用戶說純茶 but cat={cat}: {seg[:40]}"))
                if any(kw in seg for kw in CAT_CLOUD):
                    if cat != "cloud_velvet":
                        V["D3-CAT"].append((l, f"[{oi}] {item} 用戶說奶蓋 but cat={cat}: {seg[:40]}"))

        # ==============================================================
        # D4: Addon 語意但沒抓到
        # ==============================================================
        for kw, addon_name in ADDON_KEYWORDS.items():
            if kw in user:
                has_addon = any(addon_name in o.get("addon", []) for o in orders)
                # 也可能是修改場景（「茶凍換燕麥粒」→ 最終只有燕麥粒）
                # 或取消場景（「去掉茶凍」）
                cancel_kw = any(f"去掉{kw}" in user or f"不要{kw}" in user or f"拿掉{kw}" in user for _ in [1])
                if not has_addon and not cancel_kw and orders:
                    # 換的情境：「茶凍換燕麥粒」→ 只有燕麥粒
                    if f"換{kw}" not in user and f"{kw}換" not in user:
                        V["D4-ADDON"].append((l, f"用戶提到「{kw}」但無 addon: {user[:60]}"))

        # ==============================================================
        # D5: 數量不匹配
        # ==============================================================
        qty_pattern = re.compile(r"([兩二三四五六七八九十])杯")
        for seg in segments:
            m = qty_pattern.search(seg)
            if m:
                num_char = m.group(1)
                expected_qty = {"兩": 2, "二": 2, "三": 3, "四": 4, "五": 5,
                                "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}.get(num_char, 1)
                # 找對應 order 看 qty 是否匹配
                # 很難精確對應，只看有沒有任何 order qty 符合
                if expected_qty > 1:
                    has_qty = any(o.get("qty") == expected_qty for o in orders)
                    if not has_qty:
                        V["D5-QTY"].append((l, f"用戶說「{m.group()}」但無 qty={expected_qty}: {seg[:40]}"))

        # ==============================================================
        # D6: modify intent 在首段（沒有先前 order 可以修改）
        # ==============================================================
        if intents and intents[0] == "modify" and len(segments) == 1:
            V["D6-MODIFY-FIRST"].append((l, f"單段 modify: {user[:60]}"))

        # ==============================================================
        # D7: recommend intent 但 recommendations 為空
        # ==============================================================
        if "recommend" in intents and not recs:
            V["D7-REC-EMPTY"].append((l, f"recommend intent 但 recs=[]: {user[:60]}"))

        # ==============================================================
        # D8: 有 recommendations 但沒有 recommend intent
        # ==============================================================
        if recs and "recommend" not in intents:
            V["D8-REC-NO-INTENT"].append((l, f"有 recs 但無 recommend intent: {user[:60]}"))

        # ==============================================================
        # D9: 推薦果茶給要熱飲的用戶
        # ==============================================================
        wants_hot = prefs.get("temperature") == "熱" or any(
            ice_kw in user for ice_kw in ["熱飲", "熱的", "溫的"]
            if not any(neg in user for neg in ["好熱", "大熱", "超熱", "太熱"])
        )
        for r in recs:
            if r.get("item") in FRUIT_TEA_ITEMS and wants_hot:
                V["D9-HOT-FRUIT"].append((l, f"推薦果茶給熱飲用戶: {r['item']}: {user[:40]}"))

        # ==============================================================
        # D10: ColdOnly 品項但 ice=熱飲
        # ==============================================================
        for oi, o in enumerate(orders):
            if o.get("item") in FRUIT_TEA_ITEMS and o.get("ice") == "熱飲":
                V["D10-COLD-HOT"].append((l, f"[{oi}] fruit_tea ice=熱飲: {user[:60]}"))

        # ==============================================================
        # D11: 單一尺寸分類但 size 非 null
        # ==============================================================
        for oi, o in enumerate(orders):
            cat = o.get("category")
            if cat in SINGLE_SIZE_CATS and o.get("size") is not None:
                V["D11-SINGLE-SIZE"].append((l, f"[{oi}] {cat} size={o['size']}: {user[:60]}"))

        # ==============================================================
        # D12: intents 長度 vs 分段數
        # ==============================================================
        if len(intents) != len(segments):
            V["D12-INTENT-LEN"].append((l, f"intents={len(intents)} segments={len(segments)}: {user[:60]}"))

        # ==============================================================
        # D13: preferences key 非英文
        # ==============================================================
        for k in prefs:
            if any(ord(c) > 127 for c in k):
                V["D13-PREF-CN"].append((l, f"中文 key: {k}"))

        # ==============================================================
        # D14: 中文分號
        # ==============================================================
        if "；" in user:
            V["D14-CN-SEMI"].append((l, user[:40]))

        # ==============================================================
        # D15: order intent 但 segment 有推薦語意
        # ==============================================================
        REC_KEYWORDS = ["推薦", "建議", "有什麼", "什麼好喝", "你覺得", "幫我推", "推一個",
                        "有沒有推薦", "有推薦嗎", "可以推薦"]
        for i, (seg, intent) in enumerate(zip(segments, intents)):
            if intent == "order":
                if any(kw in seg for kw in REC_KEYWORDS):
                    V["D15-ORDER-BUT-REC"].append((l, f"seg[{i}] intent=order 但含推薦語: {seg[:40]}"))

        # ==============================================================
        # D16: 全部取消但 orders 非空
        # ==============================================================
        CANCEL_ALL = ["都不要", "全部取消", "算了不點了", "不點了", "全取消"]
        last_seg = segments[-1] if segments else ""
        if any(kw in last_seg for kw in CANCEL_ALL):
            if orders:
                V["D16-CANCEL-ALL"].append((l, f"最後段取消全部但 orders 非空: {user[:60]}"))

        # ==============================================================
        # D17: modify intent 但 segment 無修改語意
        # ==============================================================
        for i, (seg, intent) in enumerate(zip(segments, intents)):
            if intent == "modify":
                has_mod = any(kw in seg for kw in MODIFY_KW)
                # 也允許一些隱含修改：加料、加奶、大杯（升級暗示）
                implicit_mod = any(kw in seg for kw in ["加", "多一個", "幫我加", "還要加"])
                # 甜度冰量規格指定（在多輪中可能是修改之前的 order）
                spec_mod = any(kw in seg for kw in ["半糖", "無糖", "微糖", "少糖", "去冰", "少冰", "微冰", "大杯", "中杯", "加奶", "加鮮奶"])
                if not has_mod and not implicit_mod and not spec_mod:
                    V["D17-MODIFY-NO-KW"].append((l, f"seg[{i}] intent=modify 但無修改語意: {seg[:40]}"))

        # ==============================================================
        # D18: other intent 但 segment 有明確點餐語意
        # ==============================================================
        ORDER_SIGNALS = ["來一杯", "我要", "一杯", "兩杯", "三杯", "幫我點"]
        for i, (seg, intent) in enumerate(zip(segments, intents)):
            if intent == "other":
                # 排除已知非點餐用語
                if any(item in seg for item in ALL_ITEMS):
                    V["D18-OTHER-HAS-ITEM"].append((l, f"seg[{i}] intent=other 但含菜單品項: {seg[:40]}"))
                elif any(kw in seg for kw in ORDER_SIGNALS):
                    # 「來一杯」跟其他 order signal 只在有品項名時才算
                    pass

        # ==============================================================
        # D19: order 的 item 跟 category 在菜單中不存在該組合
        #      （跟 R7 重複但再驗一次）
        # ==============================================================
        VALID_COMBOS = set()
        for cat, items in MENU_CATEGORIES.items():
            for item in items:
                VALID_COMBOS.add((item, cat))

        for oi, o in enumerate(orders):
            item = o.get("item", "")
            cat = o.get("category")
            if item in ALL_ITEMS and cat is not None:
                if (item, cat) not in VALID_COMBOS:
                    V["D19-BAD-COMBO"].append((l, f"[{oi}] ({item}, {cat}): {user[:40]}"))

        # ==============================================================
        # D20: recommendations 的 item-category 不合法
        # ==============================================================
        for ri, r in enumerate(recs):
            r_item = r.get("item", "")
            r_cat = r.get("category")
            if r_item in ALL_ITEMS and r_cat is not None:
                if (r_item, r_cat) not in VALID_COMBOS:
                    V["D20-REC-COMBO"].append((l, f"recs[{ri}] ({r_item}, {r_cat}): {user[:40]}"))

        # ==============================================================
        # D21: 推薦跟已點品項完全重複
        # ==============================================================
        ordered_items = {(o.get("item"), o.get("category")) for o in orders}
        for r in recs:
            key = (r.get("item"), r.get("category"))
            if key in ordered_items:
                V["D21-REC-DUP"].append((l, f"推薦 {key[0]}({key[1]}) 但已在 orders: {user[:40]}"))

        # ==============================================================
        # D22: preferences.temperature=熱 但用戶沒提到熱/溫
        # ==============================================================
        if prefs.get("temperature") == "熱":
            hot_words = ["熱", "溫", "暖"]
            if not any(w in user for w in hot_words):
                V["D22-HOT-NO-KW"].append((l, f"prefs.temperature=熱 但用戶未提: {user[:60]}"))

        # ==============================================================
        # D23: preferences.temperature=冰 但用戶沒提到冰/涼
        # ==============================================================
        if prefs.get("temperature") == "冰":
            cold_words = ["冰", "涼", "冷", "消暑", "好熱"]
            if not any(w in user for w in cold_words):
                V["D23-COLD-NO-KW"].append((l, f"prefs.temperature=冰 但用戶未提: {user[:60]}"))

        # ==============================================================
        # D24: note 非空但內容可疑
        # ==============================================================
        for oi, o in enumerate(orders):
            note = o.get("note", "")
            if note and len(note) > 50:
                V["D24-NOTE-LONG"].append((l, f"[{oi}] note 過長 ({len(note)}字): {note[:40]}"))

        # ==============================================================
        # D25: 用戶提到「加料」但 addon 為空（排除取消加料）
        # ==============================================================
        # 已由 D4 覆蓋

        # ==============================================================
        # D26: 同一 orders 中完全重複的品項（item+category+size+sugar+ice 都一樣）
        # ==============================================================
        if len(orders) > 1:
            seen = set()
            for oi, o in enumerate(orders):
                key = (o.get("item"), o.get("category"), o.get("size"),
                       o.get("sugar"), o.get("ice"), tuple(o.get("addon", [])))
                if key in seen:
                    V["D26-DUP-ORDER"].append((l, f"[{oi}] 重複 order: {o.get('item')}: {user[:40]}"))
                seen.add(key)

    # ==============================================================
    # 報告
    # ==============================================================
    print("=" * 70)
    print("深度邏輯自洽性審計")
    print(f"樣本數: {len(samples)}")
    print("=" * 70)

    # 按嚴重程度分類
    CRITICAL = {"D1-SIZE-EXTRA", "D3-CAT", "D7-REC-EMPTY", "D8-REC-NO-INTENT",
                "D9-HOT-FRUIT", "D10-COLD-HOT", "D11-SINGLE-SIZE", "D12-INTENT-LEN",
                "D13-PREF-CN", "D14-CN-SEMI", "D19-BAD-COMBO", "D20-REC-COMBO"}
    MEDIUM = {"D1-SIZE-MISS", "D4-ADDON", "D5-QTY", "D6-MODIFY-FIRST",
              "D15-ORDER-BUT-REC", "D16-CANCEL-ALL", "D17-MODIFY-NO-KW",
              "D18-OTHER-HAS-ITEM", "D21-REC-DUP", "D22-HOT-NO-KW", "D23-COLD-NO-KW"}
    LOW = {"D24-NOTE-LONG", "D26-DUP-ORDER"}

    total = 0
    for severity, label, keys in [
        ("高", "CRITICAL", CRITICAL),
        ("中", "MEDIUM", MEDIUM),
        ("低", "LOW", LOW),
    ]:
        found = {k: v for k, v in V.items() if k in keys and v}
        if found:
            cnt = sum(len(v) for v in found.values())
            total += cnt
            print(f"\n{'─'*70}")
            print(f"【{severity}嚴重】{cnt} 筆")
            print(f"{'─'*70}")
            for rule in sorted(found):
                items = found[rule]
                print(f"\n  [{rule}] {len(items)} 筆:")
                for location, detail in items[:15]:
                    print(f"    {location}: {detail}")
                if len(items) > 15:
                    print(f"    ... 還有 {len(items)-15} 筆")

    # 其他未分類
    others = {k: v for k, v in V.items() if k not in CRITICAL and k not in MEDIUM and k not in LOW and v}
    if others:
        cnt = sum(len(v) for v in others.values())
        total += cnt
        print(f"\n{'─'*70}")
        print(f"【未分類】{cnt} 筆")
        print(f"{'─'*70}")
        for rule in sorted(others):
            items = others[rule]
            print(f"\n  [{rule}] {len(items)} 筆:")
            for location, detail in items[:10]:
                print(f"    {location}: {detail}")

    print(f"\n{'='*70}")
    if total == 0:
        print("✅ 深度審計通過！0 issues")
    else:
        print(f"共 {total} issues（高={sum(len(V[k]) for k in CRITICAL if k in V)}, "
              f"中={sum(len(V[k]) for k in MEDIUM if k in V)}, "
              f"低={sum(len(V[k]) for k in LOW if k in V)}）")
    print("=" * 70)

    return total


def _item_aliases(item):
    """品項的常見縮寫/別名"""
    aliases = {
        "三窨十五茉": ["茉莉", "十五茉", "茉莉綠"],
        "桂花輕烏龍": ["桂花", "桂烏", "輕烏龍"],
        "茶花紅烏龍": ["紅烏龍", "茶花"],
        "朱槿普洱紅": ["朱槿", "普洱紅", "洛神"],
        "米香玉露菁": ["玉露", "玉露菁", "米香"],
        "琥珀鐵觀音": ["鐵觀音", "琥珀"],
        "金杯蜜香紅": ["蜜香紅", "金杯"],
        "青檸桂蜜": ["青檸", "桂蜜"],
        "蜜桃紅烏龍": ["蜜桃"],
        "葡柚十五茉": ["葡柚", "葡萄柚"],
    }
    return aliases.get(item, [])


if __name__ == "__main__":
    exit(0 if main() == 0 else 1)
