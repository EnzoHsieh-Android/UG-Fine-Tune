#!/usr/bin/env python3
"""
Step 7b: 為 intents 含 recommend 但 recommendations=[] 的樣本補上推薦品項。
策略：從 recommend 段的關鍵字推斷偏好，匹配菜單品項，填入 1 項推薦。
"""

import json, re, sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ── 菜單品項與特性 ──
MENU = {
    # pure_tea
    "三窨十五茉":   {"cat": "pure_tea", "tags": ["花香", "清雅", "甘甜", "茉莉", "純茶"]},
    "桂花輕烏龍":   {"cat": "pure_tea", "tags": ["花香", "蜜韻", "輕柔", "桂花", "純茶"]},
    "茶花紅烏龍":   {"cat": "pure_tea", "tags": ["焙火", "熟果", "茶味重", "純茶"]},
    "朱槿普洱紅":   {"cat": "pure_tea", "tags": ["微酸", "回甘", "解膩", "普洱", "純茶"]},
    "米香玉露菁":   {"cat": "pure_tea", "tags": ["米穀香", "鮮爽", "日式", "純茶"]},
    # fresh_milk_tea
    "三窨十五茉_fm":   {"cat": "fresh_milk_tea", "tags": ["花香", "清香", "鮮奶", "奶茶"]},
    "桂花輕烏龍_fm":   {"cat": "fresh_milk_tea", "tags": ["花香", "蜜韻", "鮮奶", "奶茶", "溫潤"]},
    "茶花紅烏龍_fm":   {"cat": "fresh_milk_tea", "tags": ["茶奶平衡", "鮮奶", "奶茶"]},
    "琥珀鐵觀音_fm":   {"cat": "fresh_milk_tea", "tags": ["焙火", "濃郁", "鮮奶", "茶味重", "人氣", "招牌"]},
    "金杯蜜香紅_fm":   {"cat": "fresh_milk_tea", "tags": ["蜜甜", "甜", "鮮奶", "紅茶"]},
    "朱槿普洱紅_fm":   {"cat": "fresh_milk_tea", "tags": ["微酸", "風味獨特", "鮮奶"]},
    "米香玉露菁_fm":   {"cat": "fresh_milk_tea", "tags": ["穀物", "療癒", "鮮奶"]},
    # rich_milk_tea
    "琥珀鐵觀音_rm":   {"cat": "rich_milk_tea", "tags": ["焙火", "濃郁", "奶茶", "茶味重", "人氣"]},
    "金杯蜜香紅_rm":   {"cat": "rich_milk_tea", "tags": ["蜜甜", "甜", "奶茶", "紅茶"]},
    # fruit_tea
    "青檸桂蜜":   {"cat": "fruit_tea", "tags": ["酸甜", "清爽", "消暑", "夏天", "果茶", "冰"]},
    "蜜桃紅烏龍": {"cat": "fruit_tea", "tags": ["甜", "芬芳", "果茶", "水蜜桃"]},
    "葡柚十五茉": {"cat": "fruit_tea", "tags": ["酸", "清新", "微苦", "大人味", "果茶"]},
    # cloud_velvet
    "桂花輕烏龍_cv": {"cat": "cloud_velvet", "tags": ["奶蓋", "鹹甜", "綿密", "桂花"]},
    "茶花紅烏龍_cv": {"cat": "cloud_velvet", "tags": ["奶蓋", "焙火", "鹹甜"]},
}

# 偏好關鍵字 → tags 映射
PREFERENCE_MAP = {
    # 口味
    "甜": ["甜", "蜜甜"],
    "不甜": ["回甘", "微酸", "微苦"],
    "不太甜": ["回甘", "微酸"],
    "苦": ["微苦", "焙火"],
    "酸": ["微酸", "酸甜", "酸"],
    "清爽": ["清爽", "清新", "消暑"],
    "濃": ["濃郁", "焙火", "茶味重"],
    "濃郁": ["濃郁", "焙火"],
    "茶味重": ["茶味重", "焙火"],
    "花香": ["花香", "桂花", "茉莉"],
    "果香": ["果茶", "水蜜桃"],
    "清雅": ["清雅", "花香"],
    "回甘": ["回甘"],
    "解膩": ["解膩", "微酸"],
    "療癒": ["療癒", "穀物"],
    # 分類
    "果茶": ["果茶"],
    "水果": ["果茶"],
    "純茶": ["純茶"],
    "不加奶": ["純茶"],
    "鮮奶": ["鮮奶"],
    "鮮奶茶": ["鮮奶"],
    "奶茶": ["奶茶"],
    "奶蓋": ["奶蓋"],
    # 場景
    "夏天": ["消暑", "清爽", "果茶"],
    "冬天": ["焙火", "濃郁", "溫潤"],
    "天氣熱": ["消暑", "清爽"],
    "配甜點": ["解膩", "微酸", "純茶"],
    "下午茶": ["鮮奶", "花香"],
    "提神": ["焙火", "茶味重"],
    "送人": ["人氣", "招牌"],
    "外帶": ["人氣"],
    # 通用
    "招牌": ["人氣", "招牌"],
    "人氣": ["人氣", "招牌"],
    "最多人點": ["人氣", "招牌"],
    "暢銷": ["人氣"],
    "熱門": ["人氣"],
    "冰": ["冰", "清爽", "消暑"],
}

# 推薦結果的品項名（去掉 suffix）和分類
def _clean_name(key: str) -> tuple[str, str]:
    for suffix in ["_fm", "_rm", "_cv"]:
        if key.endswith(suffix):
            return key[:-len(suffix)], MENU[key]["cat"]
    return key, MENU[key]["cat"]


def pick_recommendation(rec_segments: list[str], existing_orders: list[str]) -> dict | None:
    """根據推薦段文字選擇最佳推薦品項。"""
    combined = " ".join(rec_segments)

    # 否定詞處理：「不甜」「不苦」等否定偏好
    negated_tags = set()
    if "不甜" in combined or "不太甜" in combined:
        negated_tags.update(["甜", "蜜甜"])
    if "不苦" in combined:
        negated_tags.update(["微苦"])
    if "不酸" in combined:
        negated_tags.update(["微酸", "酸甜", "酸"])

    # 收集匹配的 tags（長關鍵字優先，避免「不甜」被「甜」搶走）
    target_tags = set()
    matched_kws = set()
    # 先匹配長關鍵字
    for kw, tags in sorted(PREFERENCE_MAP.items(), key=lambda x: -len(x[0])):
        if kw in combined:
            # 跳過被否定的短關鍵字（如「甜」被「不甜」覆蓋）
            if kw in ("甜",) and ("不甜" in combined or "不太甜" in combined):
                continue
            if kw in ("苦",) and "不苦" in combined:
                continue
            if kw in ("酸",) and "不酸" in combined:
                continue
            target_tags.update(tags)
            matched_kws.add(kw)

    # 移除被否定的 tags
    target_tags -= negated_tags

    # 沒有明確偏好 → 預設推薦人氣品項
    if not target_tags:
        target_tags = {"人氣", "招牌"}

    # 計算每個品項的匹配分數
    scores = []
    for key, info in MENU.items():
        name, cat = _clean_name(key)
        # 排除已點的品項（同名同分類）
        if name in existing_orders:
            continue
        score = len(target_tags & set(info["tags"]))
        if score > 0:
            scores.append((score, name, cat, info["tags"]))

    if not scores:
        # Fallback: 推薦琥珀鐵觀音鮮奶（人氣品項）
        return {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "人氣招牌，焙火香濃郁"}

    # 取最高分，同分時優先選 fresh_milk_tea
    scores.sort(key=lambda x: (-x[0], x[2] != "fresh_milk_tea"))
    _, name, cat, tags = scores[0]

    # 生成推薦理由
    reason = _generate_reason(name, cat, target_tags, tags)
    return {"item": name, "category": cat, "reason": reason}


def _generate_reason(name: str, cat: str, target_tags: set, item_tags: list) -> str:
    """根據匹配的 tags 生成簡短推薦理由。"""
    matched = target_tags & set(item_tags)

    reasons = {
        "人氣": "人氣招牌",
        "招牌": "店內招牌",
        "花香": "花香清雅",
        "清爽": "清爽消暑",
        "清新": "清新爽口",
        "消暑": "清涼消暑",
        "甜": "天然蜜甜",
        "蜜甜": "蜜香甜潤",
        "微酸": "微酸回甘",
        "酸甜": "酸甜開胃",
        "酸": "酸香開胃",
        "焙火": "焙火香濃",
        "茶味重": "茶韻醇厚",
        "濃郁": "風味濃郁",
        "回甘": "回甘潤喉",
        "微苦": "微苦回甘",
        "解膩": "解膩清爽",
        "果茶": "果香四溢",
        "冰": "冰涼暢快",
        "純茶": "純茶韻味",
        "鮮奶": "鮮奶滑順",
        "奶茶": "奶茶經典",
        "奶蓋": "奶蓋綿密",
        "療癒": "穀物奶香療癒",
        "穀物": "穀物香氣",
        "水蜜桃": "蜜桃果香",
    }

    parts = [reasons.get(t, t) for t in matched if t in reasons]
    if parts:
        return "，".join(parts[:2])
    return "風味獨特，值得一試"


def process_file(filename: str, dry_run: bool = False):
    filepath = DATA_DIR / filename
    with open(filepath) as f:
        samples = [json.loads(line) for line in f]

    fixed = 0
    results = []
    for i, sample in enumerate(samples):
        asst_msg = next(m for m in sample["messages"] if m["role"] == "assistant")
        user_msg = next(m for m in sample["messages"] if m["role"] == "user")
        asst = json.loads(asst_msg["content"])
        intents = asst.get("intents", [])
        recs = asst.get("recommendations", [])

        if "recommend" in intents and not recs:
            user_text = user_msg["content"]
            segments = re.split(r"[;；]", user_text)
            rec_segs = [segments[j].strip() for j, intent in enumerate(intents)
                        if j < len(segments) and intent == "recommend"]
            existing_orders = [o["item"] if isinstance(o, dict) else o for o in asst.get("orders", [])]

            rec = pick_recommendation(rec_segs, existing_orders)
            if rec:
                asst["recommendations"] = [rec]
                # 補上 preferences（如果為空）
                if not asst.get("preferences"):
                    asst["preferences"] = _extract_preferences(rec_segs)
                asst_msg["content"] = json.dumps(asst, ensure_ascii=False)
                fixed += 1
                if dry_run or fixed <= 15:
                    print(f"  [{filename}#{i+1}] {user_text[:60]}")
                    print(f"    rec_segs: {rec_segs}")
                    print(f"    → {rec['item']} ({rec['category']}): {rec['reason']}")
                    print()

        results.append(sample)

    print(f"{filename}: 補了 {fixed} 筆 recommendations")

    if not dry_run:
        with open(filepath, "w") as f:
            for s in results:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"已寫入: {filepath}")


def _extract_preferences(rec_segs: list[str]) -> dict:
    """從推薦段文字提取 preferences。"""
    combined = " ".join(rec_segs)
    prefs = {}

    # 口味
    flavors = []
    if any(k in combined for k in ["甜", "蜜"]):
        flavors.append("甜")
    if any(k in combined for k in ["苦", "濃"]):
        flavors.append("苦")
    if "酸" in combined:
        flavors.append("酸")
    if any(k in combined for k in ["花香", "清雅"]):
        flavors.append("花香")
    if any(k in combined for k in ["清爽", "清新"]):
        flavors.append("清爽")
    if any(k in combined for k in ["茶味", "茶韻"]):
        flavors.append("茶味重")
    if flavors:
        prefs["口味"] = "、".join(flavors)

    # 分類偏好
    if any(k in combined for k in ["果茶", "水果"]):
        prefs["分類"] = "果茶"
    elif any(k in combined for k in ["純茶", "不加奶"]):
        prefs["分類"] = "純茶"
    elif any(k in combined for k in ["鮮奶", "鮮奶茶"]):
        prefs["分類"] = "鮮奶茶"
    elif any(k in combined for k in ["奶茶"]):
        prefs["分類"] = "奶茶"
    elif any(k in combined for k in ["奶蓋"]):
        prefs["分類"] = "奶蓋"

    # 場景
    if any(k in combined for k in ["夏天", "天氣熱", "消暑"]):
        prefs["場景"] = "夏天"
    elif any(k in combined for k in ["冬天", "天氣冷"]):
        prefs["場景"] = "冬天"
    elif any(k in combined for k in ["配甜點", "解膩"]):
        prefs["場景"] = "配甜點"

    # 溫度
    if any(k in combined for k in ["冰", "冰的"]):
        prefs["溫度"] = "冰"
    elif any(k in combined for k in ["熱", "溫"]):
        prefs["溫度"] = "熱"

    return prefs


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    for fname in ["train.jsonl", "valid.jsonl"]:
        process_file(fname, dry_run=dry_run)
