#!/usr/bin/env python3
"""
修正資料分佈不均：
1. 推薦品項平衡（降低琥珀鐵觀音/桂花輕烏龍，提高葡柚/米香/茶花/金杯）
2. 新增金杯蜜香紅 pure_tea 樣本
3. 新增 recommend+modify 組合樣本
"""

import json, re, sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

with open(DATA_DIR / "train.jsonl") as f:
    SYSTEM_PROMPT = json.loads(f.readline())["messages"][0]["content"]

# ── Part 1: 替換過多的推薦品項 ──
# 目標：每個品項推薦次數 ~25-35 之間
# 琥珀鐵觀音 78→35, 桂花輕烏龍 65→35
# 分配給: 葡柚十五茉 6→25, 米香玉露菁 13→25, 茶花紅烏龍 21→30, 金杯蜜香紅 25→30

# 根據偏好關鍵字的合理替換映射
# key = 原推薦品項, value = [(新品項, 新分類, 新理由, 適用偏好pattern)]
REPLACEMENTS = {
    "琥珀鐵觀音": [
        ("葡柚十五茉", "fruit_tea", "葡柚酸香配茉莉，清新微苦大人味", r"清|爽|解膩|大人|微苦|不甜|酸"),
        ("蜜桃紅烏龍", "fruit_tea", "蜜桃果香與紅烏龍交織，甜蜜芬芳", r"甜|蜜|果|香|芬芳"),
        ("米香玉露菁", "fresh_milk_tea", "穀物奶香療癒，鮮爽細膩", r"療癒|穀物|溫|柔|特別|日式|鮮"),
        ("茶花紅烏龍", "fresh_milk_tea", "烏龍鮮奶茶奶平衡，焙火韻醇厚", r"焙|重|濃|茶味|烏龍"),
        ("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶，天然蜜甜", r"紅茶|順|滑"),
        ("葡柚十五茉", "fruit_tea", "葡柚酸香配茉莉，清新提神", r"提神|水果"),
        ("米香玉露菁", "pure_tea", "日式玉露菁帶米穀香，鮮爽細膩", r"米|輕|不膩"),
    ],
    "桂花輕烏龍": [
        ("茶花紅烏龍", "pure_tea", "重焙火紅烏龍，天然花香與熟果甜韻", r"焙|重|濃|茶味"),
        ("金杯蜜香紅", "rich_milk_tea", "蜜香紅茶奶茶，天然蜜甜", r"甜|蜜|奶|紅茶"),
        ("蜜桃紅烏龍", "fruit_tea", "蜜桃果香甜蜜芬芳", r"果|芬芳|桃"),
        ("米香玉露菁", "fresh_milk_tea", "玉露菁鮮奶穀物奶香療癒", r"特別|新|試|療癒"),
        ("葡柚十五茉", "fruit_tea", "葡柚酸香配茉莉清新微苦", r"清|爽|酸|夏"),
        ("茶花紅烏龍", "cloud_velvet", "紅烏龍焙火韻搭奶蓋，茶香奶鹹平衡", r"奶蓋|鹹|綿"),
    ],
}

# 目標推薦計數
TARGET_MAX = {"琥珀鐵觀音": 35, "桂花輕烏龍": 35}
TARGET_MIN = {"葡柚十五茉": 30, "米香玉露菁": 30, "茶花紅烏龍": 35, "金杯蜜香紅": 35, "蜜桃紅烏龍": 30}


def rebalance_recs(samples):
    """替換過多的推薦品項，保持偏好一致性。"""
    # 統計當前推薦分佈
    rec_counts = {}
    for s in samples:
        asst = json.loads(s["messages"][2]["content"])
        for r in asst.get("recommendations", []):
            item = r.get("item", "")
            rec_counts[item] = rec_counts.get(item, 0) + 1

    changed = 0
    for i, s in enumerate(samples):
        asst = json.loads(s["messages"][2]["content"])
        recs = asst.get("recommendations", [])
        if not recs:
            continue

        rec_item = recs[0].get("item", "")
        if rec_item not in REPLACEMENTS:
            continue
        if rec_counts.get(rec_item, 0) <= TARGET_MAX.get(rec_item, 999):
            continue

        # 找 user text 中的偏好
        user_text = s["messages"][1]["content"]

        # 嘗試匹配替換
        replaced = False
        for new_item, new_cat, new_reason, pattern in REPLACEMENTS[rec_item]:
            # 新品項已達標？跳過
            if rec_counts.get(new_item, 0) >= TARGET_MIN.get(new_item, 35):
                continue
            # 偏好匹配？
            if re.search(pattern, user_text):
                recs[0] = {"item": new_item, "category": new_cat, "reason": new_reason}
                asst["recommendations"] = recs
                s["messages"][2]["content"] = json.dumps(asst, ensure_ascii=False)
                rec_counts[rec_item] -= 1
                rec_counts[new_item] = rec_counts.get(new_item, 0) + 1
                changed += 1
                replaced = True
                break

        # 偏好都不匹配但仍超標 → 用通用替換（選最少的品項）
        if not replaced and rec_counts.get(rec_item, 0) > TARGET_MAX.get(rec_item, 999):
            candidates = [(rec_counts.get(item, 0), item, cat, reason)
                         for item, cat, reason, _ in REPLACEMENTS[rec_item]
                         if rec_counts.get(item, 0) < TARGET_MIN.get(item, 35)]
            if candidates:
                candidates.sort(key=lambda x: x[0])
                _, new_item, new_cat, new_reason = candidates[0]
                recs[0] = {"item": new_item, "category": new_cat, "reason": new_reason}
                asst["recommendations"] = recs
                s["messages"][2]["content"] = json.dumps(asst, ensure_ascii=False)
                rec_counts[rec_item] -= 1
                rec_counts[new_item] = rec_counts.get(new_item, 0) + 1
                changed += 1

    print(f"推薦替換: {changed} 筆")
    print("替換後分佈:")
    for item, c in sorted(rec_counts.items(), key=lambda x: -x[1]):
        print(f"  {item:<12} {c:>3}")
    return samples


# ── Part 2 & 3: 新增樣本 ──

def make_order(item, category=None, ice=None, sugar=None, size=None, addon=None, qty=1, note=""):
    return {"item": item, "category": category, "size": size, "ice": ice, "sugar": sugar,
            "addon": addon or [], "qty": qty, "note": note}


def sample(user_text, orders, intents=None, preferences=None, recommendations=None):
    segments = user_text.split(";")
    if intents is None:
        intents = ["order"] * len(segments)
    asst = {"intents": intents, "orders": orders, "preferences": preferences or {},
            "recommendations": recommendations or []}
    return {"messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": json.dumps(asst, ensure_ascii=False)},
    ]}


# 金杯蜜香紅 pure_tea 樣本 (5筆)
PURE_TEA_SAMPLES = [
    sample("金杯蜜香紅純茶去冰半糖",
           [make_order("金杯蜜香紅", "pure_tea", ice="去冰", sugar="半糖")]),
    sample("蜜香紅純茶微冰無糖",
           [make_order("金杯蜜香紅", "pure_tea", ice="微冰", sugar="無糖")]),
    sample("金杯純茶少冰三分糖",
           [make_order("金杯蜜香紅", "pure_tea", ice="少冰", sugar="三分糖")]),
    sample("金杯蜜香紅不加奶去冰五分糖",
           [make_order("金杯蜜香紅", "pure_tea", ice="去冰", sugar="五分糖")]),
    sample("蜜香紅純茶一杯熱的無糖",
           [make_order("金杯蜜香紅", "pure_tea", ice="熱飲", sugar="無糖")]),
]

# recommend + modify 組合樣本 (8筆)
REC_MODIFY_SAMPLES = [
    sample("有推薦清爽的嗎；改冰的",
           [make_order("青檸桂蜜", "fruit_tea", ice="正常冰")],
           ["recommend", "modify"],
           {"口味": "清爽"},
           [{"item": "青檸桂蜜", "category": "fruit_tea", "reason": "酸甜清爽，清涼消暑"}]),
    sample("推薦茶味重的；改無糖",
           [make_order("茶花紅烏龍", "pure_tea", ice=None, sugar="無糖")],
           ["recommend", "modify"],
           {"口味": "茶味重"},
           [{"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙火紅烏龍，天然花香與熟果甜韻"}]),
    sample("有推薦甜的嗎；改半糖就好",
           [make_order("金杯蜜香紅", "fresh_milk_tea", ice=None, sugar="半糖")],
           ["recommend", "modify"],
           {"口味": "甜"},
           [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶，天然蜜甜"}]),
    sample("推薦花香的；不要太甜改三分糖",
           [make_order("桂花輕烏龍", "fresh_milk_tea", ice=None, sugar="三分糖")],
           ["recommend", "modify"],
           {"口味": "花香", "排除": "太甜"},
           [{"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花烏龍鮮奶，蜜韻奶香溫潤"}]),
    sample("有什麼推薦的嗎；去冰就好",
           [make_order("琥珀鐵觀音", "fresh_milk_tea", ice="去冰")],
           ["recommend", "modify"],
           {},
           [{"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "人氣招牌，焙火香濃郁"}]),
    sample("推薦解膩的；少冰無糖",
           [make_order("朱槿普洱紅", "pure_tea", ice="少冰", sugar="無糖")],
           ["recommend", "modify"],
           {"場景": "解膩"},
           [{"item": "朱槿普洱紅", "category": "pure_tea", "reason": "微酸回甘，解膩清爽"}]),
    sample("推薦果茶；改微冰",
           [make_order("蜜桃紅烏龍", "fruit_tea", ice="微冰")],
           ["recommend", "modify"],
           {"分類": "果茶"},
           [{"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香，甜蜜芬芳"}]),
    sample("有推薦微苦的嗎；改去冰半糖",
           [make_order("葡柚十五茉", "fruit_tea", ice="去冰", sugar="半糖")],
           ["recommend", "modify"],
           {"口味": "微苦"},
           [{"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚酸香配茉莉，清新微苦大人味"}]),
]

# 推薦不足品項的新增推薦樣本 (12筆)
EXTRA_REC_SAMPLES = [
    # 葡柚十五茉
    sample("有什麼不會太甜的推薦", [],
           ["recommend"], {"口味": "不甜"},
           [{"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚酸香配茉莉，清新微苦大人味"}]),
    sample("推薦帶酸的茶", [],
           ["recommend"], {"口味": "酸"},
           [{"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚酸香清新，微苦大人味"}]),
    sample("有微苦大人味的推薦嗎", [],
           ["recommend"], {"口味": "微苦"},
           [{"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚酸香配茉莉，清新微苦大人味"}]),
    sample("一杯鐵觀音去冰半糖；推薦不甜的果茶",
           [make_order("琥珀鐵觀音", None, ice="去冰", sugar="半糖")],
           ["order", "recommend"], {"口味": "不甜", "分類": "果茶"},
           [{"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚酸香配茉莉，清新微苦"}]),
    # 米香玉露菁
    sample("推薦特別一點的", [],
           ["recommend"], {},
           [{"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "穀物奶香療癒，鮮爽細膩"}]),
    sample("有什麼比較特殊的推薦嗎", [],
           ["recommend"], {},
           [{"item": "米香玉露菁", "category": "pure_tea", "reason": "日式玉露菁帶米穀香，鮮爽細膩"}]),
    sample("想喝療癒的；少冰半糖",
           [make_order("米香玉露菁", "fresh_milk_tea", ice="少冰", sugar="半糖")],
           ["recommend", "modify"], {"口味": "療癒"},
           [{"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "穀物奶香療癒，鮮爽細膩"}]),
    # 茶花紅烏龍
    sample("推薦焙火香的", [],
           ["recommend"], {"口味": "焙火"},
           [{"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙火紅烏龍，天然花香與熟果甜韻"}]),
    sample("想喝茶味重的奶茶", [],
           ["recommend"], {"口味": "茶味重", "分類": "奶茶"},
           [{"item": "茶花紅烏龍", "category": "rich_milk_tea", "reason": "焙火韻醇厚，茶奶平衡"}]),
    # 金杯蜜香紅
    sample("推薦甜一點的", [],
           ["recommend"], {"口味": "甜"},
           [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶，天然蜜甜"}]),
    sample("有蜜甜香的推薦嗎", [],
           ["recommend"], {"口味": "蜜甜"},
           [{"item": "金杯蜜香紅", "category": "rich_milk_tea", "reason": "蜜香紅茶奶茶，甜潤順口"}]),
    sample("紅茶底的推薦什麼", [],
           ["recommend"], {"分類": "紅茶"},
           [{"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶，天然蜜甜"}]),
]


def main():
    dry_run = "--dry-run" in sys.argv

    # 讀取
    with open(DATA_DIR / "train.jsonl") as f:
        samples = [json.loads(line) for line in f]

    print(f"=== train.jsonl: {len(samples)} 樣本 ===\n")

    # Part 1: 推薦平衡
    samples = rebalance_recs(samples)

    # Part 2 & 3: 新增樣本
    new_samples = PURE_TEA_SAMPLES + REC_MODIFY_SAMPLES + EXTRA_REC_SAMPLES
    print(f"\n新增樣本: {len(new_samples)} 筆")
    print(f"  金杯蜜香紅 pure_tea: {len(PURE_TEA_SAMPLES)}")
    print(f"  recommend+modify: {len(REC_MODIFY_SAMPLES)}")
    print(f"  推薦不足品項: {len(EXTRA_REC_SAMPLES)}")

    samples.extend(new_samples)
    print(f"\n總計: {len(samples)} 樣本")

    # 最終推薦分佈
    print("\n=== 最終推薦品項分佈 ===")
    rec_counts = {}
    for s in samples:
        asst = json.loads(s["messages"][2]["content"])
        for r in asst.get("recommendations", []):
            rec_counts[r["item"]] = rec_counts.get(r["item"], 0) + 1
    for item, c in sorted(rec_counts.items(), key=lambda x: -x[1]):
        print(f"  {item:<12} {c:>3}")

    if not dry_run:
        with open(DATA_DIR / "train.jsonl", "w") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"\n已寫入: {DATA_DIR / 'train.jsonl'}")


if __name__ == "__main__":
    main()
