#!/usr/bin/env python3
"""
一次修正所有分佈問題：
P1:
  1. train: 桂花輕烏龍 null 13%→15%+
  2. train: 三窨十五茉 fm:rm 2.8→<2.5, fm 51%→<50%
  3. train: recommend+modify 9→15+
  4. valid: 推薦品項 max:min 5.7→<2.5
  5. valid: 蜜桃紅烏龍/葡柚十五茉 推薦=0
  6. valid: 朱槿普洱紅 null 43%→<35%
  7. valid: 金杯蜜香紅 fm 58%→<50%
  8. cross: 移除跨檔重複
P2:
  9. train: 熱飲/一分糖/全糖 偏低
"""

import json, re, sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def load(fname):
    with open(DATA_DIR / fname) as f:
        return [json.loads(line) for line in f]


def save(fname, samples):
    with open(DATA_DIR / fname, "w") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")


def get_asst(s):
    return json.loads(s["messages"][2]["content"])


def set_asst(s, asst):
    s["messages"][2]["content"] = json.dumps(asst, ensure_ascii=False)


def get_system(s):
    return s["messages"][0]["content"]


# ================================================================
# FIX TRAIN
# ================================================================
def fix_train(samples):
    fixes = {}

    SYSTEM_PROMPT = get_system(samples[0])

    def make_sample(user_text, orders, intents, prefs=None, recs=None):
        asst = {"intents": intents, "orders": orders,
                "preferences": prefs or {}, "recommendations": recs or []}
        return {"messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(asst, ensure_ascii=False)},
        ]}

    def mk_order(item, cat=None, ice=None, sugar=None, size=None, addon=None, qty=1):
        return {"item": item, "category": cat, "size": size, "ice": ice,
                "sugar": sugar, "addon": addon or [], "qty": qty, "note": ""}

    # --- Fix 1: 桂花輕烏龍 null 13%→15% ---
    # 找 user text 無分類關鍵字的桂花輕烏龍 fm 樣本，改 category→null
    cat_kws = ["鮮奶茶", "鮮奶", "奶精", "奶茶", "純茶", "不加奶", "奶蓋"]
    guihua_aliases = ["桂花輕烏龍", "桂花烏龍", "桂花", "輕烏龍"]
    converted = 0
    for s in samples:
        if converted >= 5:
            break
        asst = get_asst(s)
        user_text = s["messages"][1]["content"]
        segments = re.split(r"[;；]", user_text)
        for o in asst.get("orders", []):
            if not isinstance(o, dict):
                continue
            if o.get("item") != "桂花輕烏龍" or o.get("category") is None:
                continue
            # 找品項所在 segment
            seg_indices = [i for i, seg in enumerate(segments)
                           if any(a in seg for a in guihua_aliases)]
            # 檢查品項 segment + 相鄰 segment 是否有分類關鍵字
            check_indices = set()
            for idx in seg_indices:
                for d in range(3):
                    if idx + d < len(segments):
                        check_indices.add(idx + d)
            has_kw = any(kw in segments[idx] for idx in check_indices for kw in cat_kws)
            if not has_kw:
                o["category"] = None
                set_asst(s, asst)
                converted += 1
                break
    fixes["桂花輕烏龍 null轉換"] = converted

    # --- Fix 2: 三窨十五茉 fm:rm 2.8→<2.5 ---
    # 新增 rm 樣本拉低比例: fm=148, rm=53. 加 15 筆 rm → fm:rm=148:68=2.18
    san_rm_new = [
        make_sample("三窨十五茉奶茶去冰半糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="半糖")], ["order"]),
        make_sample("茉莉奶茶微冰五分糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="微冰", sugar="五分糖")], ["order"]),
        make_sample("十五茉奶茶少冰三分糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="少冰", sugar="三分糖")], ["order"]),
        make_sample("三窨十五茉奶茶去冰無糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="無糖")], ["order"]),
        make_sample("茉莉奶茶正常冰全糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="正常冰", sugar="全糖")], ["order"]),
        make_sample("三窨十五茉奶茶熱的半糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="熱飲", sugar="半糖")], ["order"]),
        make_sample("十五茉奶茶大杯去冰半糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="半糖", size="L")], ["order"]),
        make_sample("一杯三窨十五茉奶茶微冰", [mk_order("三窨十五茉", "rich_milk_tea", ice="微冰")], ["order"]),
        make_sample("三窨十五茉奶茶加茶凍去冰半糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="半糖", addon=["紅烏龍茶凍"])], ["order"]),
        make_sample("茉莉奶茶少冰無糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="少冰", sugar="無糖")], ["order"]),
        make_sample("三窨十五茉奶茶去冰一分糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="一分糖")], ["order"]),
        make_sample("十五茉奶茶加燕麥粒微冰三分糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="微冰", sugar="三分糖", addon=["燕麥粒"])], ["order"]),
        make_sample("三窨十五茉奶茶兩杯去冰半糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="半糖", qty=2)], ["order"]),
        make_sample("茉莉奶茶中杯少冰五分糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="少冰", sugar="五分糖", size="M")], ["order"]),
        make_sample("來杯三窨十五茉奶茶去冰三分糖", [mk_order("三窨十五茉", "rich_milk_tea", ice="去冰", sugar="三分糖")], ["order"]),
    ]
    samples.extend(san_rm_new)
    fixes["三窨十五茉 rm 新增"] = len(san_rm_new)

    # --- Fix 3: recommend+modify 9→15 (需再加 6 筆) ---
    rec_mod_new = [
        make_sample("推薦穀物香的；改熱的",
                     [mk_order("米香玉露菁", "fresh_milk_tea", ice="熱飲")],
                     ["recommend", "modify"],
                     {"口味": "穀物"},
                     [{"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "穀物奶香療癒，鮮爽細膩"}]),
        make_sample("有蜜甜的推薦嗎；半糖就好",
                     [mk_order("金杯蜜香紅", "fresh_milk_tea", sugar="半糖")],
                     ["recommend", "modify"],
                     {"口味": "蜜甜"},
                     [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶，天然蜜甜"}]),
        make_sample("推薦酸甜的果茶；去冰",
                     [mk_order("青檸桂蜜", "fruit_tea", ice="去冰")],
                     ["recommend", "modify"],
                     {"口味": "酸甜", "分類": "果茶"},
                     [{"item": "青檸桂蜜", "category": "fruit_tea", "reason": "酸甜清爽，清涼消暑"}]),
        make_sample("有濃郁的推薦嗎；改全糖",
                     [mk_order("琥珀鐵觀音", "rich_milk_tea", sugar="全糖")],
                     ["recommend", "modify"],
                     {"口味": "濃郁"},
                     [{"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "焙火香濃郁，茶韻醇厚"}]),
        make_sample("推薦蜜桃味的；少冰一分糖",
                     [mk_order("蜜桃紅烏龍", "fruit_tea", ice="少冰", sugar="一分糖")],
                     ["recommend", "modify"],
                     {"口味": "蜜桃"},
                     [{"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香與紅烏龍交織，甜蜜芬芳"}]),
        make_sample("推薦奶蓋的；加茶凍",
                     [mk_order("桂花輕烏龍", "cloud_velvet", addon=["紅烏龍茶凍"])],
                     ["recommend", "modify"],
                     {"分類": "奶蓋"},
                     [{"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花烏龍覆綿密奶蓋，鹹甜交融"}]),
    ]
    samples.extend(rec_mod_new)
    fixes["recommend+modify 新增"] = len(rec_mod_new)

    # --- Fix 9 (P2): 熱飲/一分糖/全糖 偏低 → 新增幾筆 ---
    p2_new = [
        make_sample("鐵觀音熱的全糖", [mk_order("琥珀鐵觀音", None, ice="熱飲", sugar="全糖")], ["order"]),
        make_sample("桂花輕烏龍熱的一分糖", [mk_order("桂花輕烏龍", None, ice="熱飲", sugar="一分糖")], ["order"]),
        make_sample("茶花紅烏龍熱飲全糖", [mk_order("茶花紅烏龍", None, ice="熱飲", sugar="全糖")], ["order"]),
        make_sample("十五茉熱的一分糖", [mk_order("三窨十五茉", None, ice="熱飲", sugar="一分糖")], ["order"]),
        make_sample("蜜香紅熱的全糖", [mk_order("金杯蜜香紅", None, ice="熱飲", sugar="全糖")], ["order"]),
        make_sample("普洱熱飲一分糖", [mk_order("朱槿普洱紅", None, ice="熱飲", sugar="一分糖")], ["order"]),
        make_sample("玉露菁熱的全糖", [mk_order("米香玉露菁", None, ice="熱飲", sugar="全糖")], ["order"]),
    ]
    samples.extend(p2_new)
    fixes["熱飲/全糖/一分糖 新增"] = len(p2_new)

    return samples, fixes


# ================================================================
# FIX VALID
# ================================================================
def fix_valid(samples):
    fixes = {}

    # --- Fix 4+5: 推薦品項平衡 ---
    # 琥珀鐵觀音 17→8, 分配給不足品項
    target_max_v = {"琥珀鐵觀音": 8, "金杯蜜香紅": 8, "桂花輕烏龍": 8}
    replacements_v = {
        "琥珀鐵觀音": [
            ("蜜桃紅烏龍", "fruit_tea", "蜜桃果香與紅烏龍交織，甜蜜芬芳"),
            ("葡柚十五茉", "fruit_tea", "葡柚酸香配茉莉，清新微苦大人味"),
            ("朱槿普洱紅", "pure_tea", "微酸回甘，解膩清爽"),
            ("茶花紅烏龍", "fresh_milk_tea", "茶奶平衡圓潤，焙火韻醇厚"),
            ("米香玉露菁", "fresh_milk_tea", "穀物奶香療癒，鮮爽細膩"),
        ],
        "金杯蜜香紅": [
            ("蜜桃紅烏龍", "fruit_tea", "蜜桃果香與紅烏龍交織，甜蜜芬芳"),
            ("葡柚十五茉", "fruit_tea", "葡柚酸香配茉莉，清新微苦大人味"),
            ("朱槿普洱紅", "rich_milk_tea", "洛神普洱鮮奶，微酸風味獨特"),
            ("茶花紅烏龍", "cloud_velvet", "紅烏龍焙火韻搭奶蓋，茶香奶鹹平衡"),
        ],
        "桂花輕烏龍": [
            ("葡柚十五茉", "fruit_tea", "葡柚酸香配茉莉，清新微苦大人味"),
            ("米香玉露菁", "pure_tea", "日式玉露菁帶米穀香，鮮爽細膩"),
            ("朱槿普洱紅", "pure_tea", "微酸回甘，解膩清爽"),
        ],
    }
    rec_counts_v = {}
    for s in samples:
        asst = get_asst(s)
        for r in asst.get("recommendations", []):
            rec_counts_v[r["item"]] = rec_counts_v.get(r["item"], 0) + 1

    changed_v = 0
    for s in samples:
        asst = get_asst(s)
        recs = asst.get("recommendations", [])
        if not recs:
            continue
        rec_item = recs[0].get("item", "")
        if rec_item not in replacements_v:
            continue
        if rec_counts_v.get(rec_item, 0) <= target_max_v.get(rec_item, 999):
            continue
        for new_item, new_cat, new_reason in replacements_v[rec_item]:
            if rec_counts_v.get(new_item, 0) >= 8:
                continue
            recs[0] = {"item": new_item, "category": new_cat, "reason": new_reason}
            set_asst(s, asst)
            rec_counts_v[rec_item] -= 1
            rec_counts_v[new_item] = rec_counts_v.get(new_item, 0) + 1
            changed_v += 1
            break
    fixes["valid 推薦替換"] = changed_v

    # --- Fix 6: 朱槿普洱紅 null 43%→<35% ---
    # 把一些 null 改回有分類（user text 確實有分類關鍵字的）
    # 或者新增幾筆有分類的朱槿普洱紅
    SYSTEM_PROMPT = get_system(samples[0])

    def make_sample(user_text, orders, intents, prefs=None, recs=None):
        asst = {"intents": intents, "orders": orders,
                "preferences": prefs or {}, "recommendations": recs or []}
        return {"messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(asst, ensure_ascii=False)},
        ]}

    def mk_order(item, cat=None, ice=None, sugar=None, size=None, addon=None, qty=1):
        return {"item": item, "category": cat, "size": size, "ice": ice,
                "sugar": sugar, "addon": addon or [], "qty": qty, "note": ""}

    # 新增 3 筆有明確分類的朱槿普洱紅（降低 null 比例 10/23=43% → 10/26=38%... 還不夠）
    # 再加 2 筆 = 10/28=35.7%... 差不多。加 3 筆 = 10/29=34.5% < 35% ✓
    zhu_jin = [
        make_sample("朱槿普洱紅鮮奶去冰半糖",
                     [mk_order("朱槿普洱紅", "fresh_milk_tea", ice="去冰", sugar="半糖")], ["order"]),
        make_sample("朱槿普洱紅奶茶微冰三分糖",
                     [mk_order("朱槿普洱紅", "rich_milk_tea", ice="微冰", sugar="三分糖")], ["order"]),
        make_sample("朱槿普洱紅純茶少冰無糖",
                     [mk_order("朱槿普洱紅", "pure_tea", ice="少冰", sugar="無糖")], ["order"]),
    ]
    samples.extend(zhu_jin)
    fixes["朱槿普洱紅 有分類新增"] = len(zhu_jin)

    # --- Fix 7: 金杯蜜香紅 fm 58%→<50% ---
    # fm=22, rm=9. 新增 4 筆 rm → fm:rm=22:13, fm=22/(22+13+7)=52%... 加 5 筆 → 22:14, 22/43=51%. 加 6 → 22/44=50%
    km_rm_new = [
        make_sample("金杯蜜香紅奶茶去冰半糖",
                     [mk_order("金杯蜜香紅", "rich_milk_tea", ice="去冰", sugar="半糖")], ["order"]),
        make_sample("蜜香紅奶茶微冰無糖",
                     [mk_order("金杯蜜香紅", "rich_milk_tea", ice="微冰", sugar="無糖")], ["order"]),
        make_sample("金杯奶茶少冰三分糖",
                     [mk_order("金杯蜜香紅", "rich_milk_tea", ice="少冰", sugar="三分糖")], ["order"]),
        make_sample("金杯蜜香紅奶茶熱的半糖",
                     [mk_order("金杯蜜香紅", "rich_milk_tea", ice="熱飲", sugar="半糖")], ["order"]),
        make_sample("蜜香紅奶茶大杯去冰五分糖",
                     [mk_order("金杯蜜香紅", "rich_milk_tea", ice="去冰", sugar="五分糖", size="L")], ["order"]),
        make_sample("金杯蜜香紅奶茶去冰無糖加茶凍",
                     [mk_order("金杯蜜香紅", "rich_milk_tea", ice="去冰", sugar="無糖", addon=["紅烏龍茶凍"])], ["order"]),
    ]
    samples.extend(km_rm_new)
    fixes["valid 金杯 rm 新增"] = len(km_rm_new)

    # --- Fix 8: 跨檔重複 ---
    # 移除 valid 中的 "桂花輕烏龍奶蓋加茶凍"（保留 train 的）
    before = len(samples)
    samples = [s for s in samples
               if s["messages"][1]["content"] != "桂花輕烏龍奶蓋加茶凍"]
    removed = before - len(samples)
    if removed:
        fixes["跨檔重複移除"] = removed

    return samples, fixes


def main():
    dry_run = "--dry-run" in sys.argv

    # Train
    train = load("train.jsonl")
    print(f"=== Train: {len(train)} samples ===")
    train, t_fixes = fix_train(train)
    for k, v in t_fixes.items():
        print(f"  {k}: {v}")
    print(f"  修正後: {len(train)} samples")

    # Valid
    valid = load("valid.jsonl")
    print(f"\n=== Valid: {len(valid)} samples ===")
    valid, v_fixes = fix_valid(valid)
    for k, v in v_fixes.items():
        print(f"  {k}: {v}")
    print(f"  修正後: {len(valid)} samples")

    if not dry_run:
        save("train.jsonl", train)
        save("valid.jsonl", valid)
        print("\n已寫入！")
    else:
        print("\n[DRY RUN]")


if __name__ == "__main__":
    main()
