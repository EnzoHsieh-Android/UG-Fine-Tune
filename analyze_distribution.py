#!/usr/bin/env python3
"""資料比重分析（skill 2.1b 六維度）"""

import json
from pathlib import Path
from collections import Counter, defaultdict

DATA_DIR = Path(__file__).parent / "data"

ALL_ITEMS = {
    "三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁",
    "琥珀鐵觀音", "金杯蜜香紅", "青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉",
}

MULTI_CAT_ITEMS = {"三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"}


def load_all():
    samples = []
    for fname in ["train.jsonl", "valid.jsonl"]:
        with open(DATA_DIR / fname) as f:
            for line in f:
                samples.append(json.loads(line))
    return samples


def analyze(samples):
    # ====== 維度 1: 品項分佈 ======
    print("=" * 60)
    print("維度 1: 品項分佈")
    print("=" * 60)
    item_cnt = Counter()
    for s in samples:
        data = json.loads(s["messages"][2]["content"])
        for o in data.get("orders", []):
            item_cnt[o.get("item", "")] += 1
        for r in data.get("recommendations", []):
            item_cnt[r.get("item", "")] += 1

    menu_items = {k: v for k, v in item_cnt.items() if k in ALL_ITEMS}
    non_menu = {k: v for k, v in item_cnt.items() if k not in ALL_ITEMS}
    max_cnt = max(menu_items.values())
    min_cnt = min(menu_items.values())

    for item, cnt in sorted(menu_items.items(), key=lambda x: -x[1]):
        bar = "█" * (cnt // 5)
        flag = " ⚠️ 低頻" if cnt < max_cnt / 3 else ""
        print(f"  {item:8s} {cnt:>4d} {bar}{flag}")
    print(f"\n  最大/最小比: {max_cnt}/{min_cnt} = {max_cnt/min_cnt:.1f}x (建議 <3x)")
    print(f"  非菜單品項: {len(non_menu)} 種, {sum(non_menu.values())} 筆")

    # ====== 維度 2: Category 分佈 ======
    print(f"\n{'='*60}")
    print("維度 2: Category 分佈（多分類品項）")
    print("=" * 60)
    item_cat = defaultdict(Counter)
    for s in samples:
        data = json.loads(s["messages"][2]["content"])
        for o in data.get("orders", []):
            it, ct = o.get("item", ""), o.get("category") or "null"
            if it in MULTI_CAT_ITEMS:
                item_cat[it][ct] += 1

    cats = ["pure_tea", "fresh_milk_tea", "rich_milk_tea", "cloud_velvet", "null"]
    print(f"  {'品項':10s}" + "".join(f"{c:>14s}" for c in cats))
    for item in sorted(item_cat.keys()):
        d = item_cat[item]
        total = sum(d.values())
        row = f"  {item:10s}"
        for c in cats:
            n = d.get(c, 0)
            if n:
                row += f"  {n:>4d}({n/total*100:4.0f}%)"
            else:
                row += f"{'--':>11s}   "
        print(row)

    # null 佔比統計
    print(f"\n  null 佔比目標: 20-35%")
    for item in sorted(item_cat.keys()):
        d = item_cat[item]
        total = sum(d.values())
        null_pct = d.get("null", 0) / total * 100 if total else 0
        flag = " ✓" if 20 <= null_pct <= 35 else " ⚠️"
        print(f"    {item:10s} null={null_pct:4.0f}%{flag}")

    # ====== 維度 3: 甜度/冰量 ======
    print(f"\n{'='*60}")
    print("維度 3: 甜度/冰量分佈")
    print("=" * 60)
    sugar_cnt = Counter()
    ice_cnt = Counter()
    size_cnt = Counter()
    total_orders = 0
    for s in samples:
        data = json.loads(s["messages"][2]["content"])
        for o in data.get("orders", []):
            total_orders += 1
            sugar_cnt[o.get("sugar") or "null"] += 1
            ice_cnt[o.get("ice") or "null"] += 1
            size_cnt[o.get("size") or "null"] += 1

    print(f"  總 orders: {total_orders}")
    print(f"\n  甜度 (null 目標 >40%):")
    for k, v in sugar_cnt.most_common():
        pct = v / total_orders * 100
        print(f"    {k:>8s}: {v:>4d} ({pct:4.1f}%)")

    print(f"\n  冰量 (null 目標 >40%):")
    for k, v in ice_cnt.most_common():
        pct = v / total_orders * 100
        print(f"    {k:>8s}: {v:>4d} ({pct:4.1f}%)")

    print(f"\n  尺寸 (null 目標 >60%):")
    for k, v in size_cnt.most_common():
        pct = v / total_orders * 100
        print(f"    {k:>8s}: {v:>4d} ({pct:4.1f}%)")

    # ====== 維度 4: 單輪 vs 多輪 ======
    print(f"\n{'='*60}")
    print("維度 4: 單輪 vs 多輪")
    print("=" * 60)
    single = 0
    multi = 0
    seg_dist = Counter()
    for s in samples:
        user = s["messages"][1]["content"]
        segs = user.count(";") + user.count("；") + 1
        seg_dist[segs] += 1
        if segs == 1:
            single += 1
        else:
            multi += 1
    total = single + multi
    print(f"  單輪: {single} ({single/total*100:.0f}%)")
    print(f"  多輪: {multi} ({multi/total*100:.0f}%) (建議 15-25%)")
    print(f"  段數分佈:")
    for segs, cnt in sorted(seg_dist.items()):
        print(f"    {segs} 段: {cnt}")

    # ====== 維度 5: 推薦樣本 ======
    print(f"\n{'='*60}")
    print("維度 5: 含推薦樣本")
    print("=" * 60)
    pure_rec = 0
    mixed = 0
    multi_rec = 0
    no_rec = 0
    for s in samples:
        data = json.loads(s["messages"][2]["content"])
        intents = data.get("intents", [])
        orders = data.get("orders", [])
        recs = data.get("recommendations", [])
        has_rec = "recommend" in intents
        has_order = any(i in ("order", "modify") for i in intents)

        if has_rec and not has_order:
            pure_rec += 1
        elif has_rec and has_order:
            mixed += 1
        else:
            no_rec += 1

        if intents.count("recommend") > 1:
            multi_rec += 1

    rec_total = pure_rec + mixed
    print(f"  純推薦: {pure_rec} ({pure_rec/total*100:.0f}%)")
    print(f"  混合（order+recommend）: {mixed} ({mixed/total*100:.0f}%)")
    print(f"  多次推薦（recommend出現>1次）: {multi_rec}")
    print(f"  推薦類合計: {rec_total} ({rec_total/total*100:.0f}%) (建議 15-25%)")
    print(f"  無推薦: {no_rec} ({no_rec/total*100:.0f}%)")

    # ====== 維度 6: 修改/取消 ======
    print(f"\n{'='*60}")
    print("維度 6: 修改/取消樣本")
    print("=" * 60)
    modify_cnt = 0
    cancel_all = 0
    modify_types = Counter()
    for s in samples:
        data = json.loads(s["messages"][2]["content"])
        intents = data.get("intents", [])
        user = s["messages"][1]["content"]
        if "modify" in intents:
            modify_cnt += 1
            # 分類修改類型
            if "不要" in user or "取消" in user or "不點" in user or "拿掉" in user or "都不" in user:
                modify_types["取消"] += 1
            if "改" in user or "換" in user:
                modify_types["修改品項/屬性"] += 1
            if "都去冰" in user or "都半糖" in user or "都無糖" in user:
                modify_types["批量修改"] += 1
            if not data.get("orders"):
                cancel_all += 1

    print(f"  含 modify: {modify_cnt} ({modify_cnt/total*100:.0f}%) (建議 5-10%)")
    print(f"  全部取消: {cancel_all}")
    print(f"  修改類型:")
    for t, c in modify_types.most_common():
        print(f"    {t}: {c}")

    # ====== 維度額外: 多輪 category null 覆蓋 ======
    print(f"\n{'='*60}")
    print("額外: 多輪 category null 場景")
    print("=" * 60)
    cat_null_multi = 0
    cat_null_same_item = 0
    cat_null_diff_item = 0
    for s in samples:
        user = s["messages"][1]["content"]
        data = json.loads(s["messages"][2]["content"])
        orders = data.get("orders", [])
        segs = user.count(";") + user.count("；") + 1
        if segs < 2 or len(orders) < 2:
            continue
        # 檢查是否有「前有分類 + 後無分類 → null」
        has_cat = any(o.get("category") is not None for o in orders)
        has_null = any(o.get("category") is None for o in orders)
        if has_cat and has_null:
            cat_null_multi += 1
            items_with_cat = {o["item"] for o in orders if o.get("category")}
            items_null = {o["item"] for o in orders if o.get("category") is None}
            if items_with_cat & items_null:
                cat_null_same_item += 1
            else:
                cat_null_diff_item += 1

    print(f"  多輪含 category 混合（有值+null）: {cat_null_multi}")
    print(f"    同品項: {cat_null_same_item}")
    print(f"    不同品項: {cat_null_diff_item}")


if __name__ == "__main__":
    samples = load_all()
    print(f"總樣本: {len(samples)}\n")
    analyze(samples)
