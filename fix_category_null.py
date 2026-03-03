#!/usr/bin/env python3
"""
Step 7e: 將多分類品項中使用者未明確指定分類的 category 改為 null。
判斷邏輯：對每筆 order，找到包含該品項的 segment，
檢查該 segment（含前後 modify 段）是否有分類關鍵字。
"""

import json, re, sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

MULTI_CAT_ITEMS = [
    "三窨十五茉", "桂花輕烏龍", "茶花紅烏龍",
    "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁",
]

# 品項簡稱（用於匹配 segment）
ITEM_ALIASES = {
    "三窨十五茉": ["三窨十五茉", "茉莉", "十五茉"],
    "桂花輕烏龍": ["桂花輕烏龍", "桂花烏龍", "桂花", "輕烏龍"],
    "茶花紅烏龍": ["茶花紅烏龍", "茶花烏龍", "紅烏龍"],
    "琥珀鐵觀音": ["琥珀鐵觀音", "鐵觀音"],
    "金杯蜜香紅": ["金杯蜜香紅", "金杯", "蜜香紅"],
    "朱槿普洱紅": ["朱槿普洱紅", "朱槿", "普洱"],
    "米香玉露菁": ["米香玉露菁", "玉露", "玉露菁"],
}

# 分類關鍵字（長的優先匹配）
CAT_KEYWORDS = [
    ("fresh_milk_tea", "鮮奶茶"),
    ("fresh_milk_tea", "鮮奶"),
    ("rich_milk_tea", "奶精"),
    ("rich_milk_tea", "奶茶"),
    ("pure_tea", "純茶"),
    ("pure_tea", "不加奶"),
    ("cloud_velvet", "奶蓋"),
]


def _find_item_segments(item: str, segments: list[str]) -> list[int]:
    """找出包含品項名或別名的 segment index。"""
    aliases = ITEM_ALIASES.get(item, [item])
    indices = []
    for i, seg in enumerate(segments):
        if any(alias in seg for alias in aliases):
            indices.append(i)
    return indices


def _has_cat_keyword_in_segments(segments: list[str], seg_indices: list[int]) -> bool:
    """檢查指定 segments（及相鄰段）是否有分類關鍵字。"""
    # 擴展到相鄰段（處理 "鐵觀音;要鮮奶" 這種跨段指定）
    check_indices = set()
    for idx in seg_indices:
        check_indices.add(idx)
        if idx + 1 < len(segments):
            check_indices.add(idx + 1)
        if idx + 2 < len(segments):
            check_indices.add(idx + 2)

    for idx in check_indices:
        seg = segments[idx]
        for _, kw in CAT_KEYWORDS:
            if kw in seg:
                return True
    return False


def process_file(filename: str, dry_run: bool = False):
    filepath = DATA_DIR / filename
    with open(filepath) as f:
        samples = [json.loads(line) for line in f]

    changed = 0
    item_changes = {item: 0 for item in MULTI_CAT_ITEMS}

    for i, sample in enumerate(samples):
        asst_msg = next(m for m in sample["messages"] if m["role"] == "assistant")
        user_msg = next(m for m in sample["messages"] if m["role"] == "user")
        asst = json.loads(asst_msg["content"])
        user_text = user_msg["content"]
        segments = re.split(r"[;；]", user_text)

        modified = False
        for order in asst.get("orders", []):
            if not isinstance(order, dict):
                continue
            item = order.get("item", "")
            cat = order.get("category")

            if item not in MULTI_CAT_ITEMS or cat is None:
                continue

            # 找品項所在 segment
            seg_indices = _find_item_segments(item, segments)
            if not seg_indices:
                # 品項名找不到（可能是簡稱匹配不到），用全文搜索
                has_kw = any(kw in user_text for _, kw in CAT_KEYWORDS)
                if not has_kw:
                    order["category"] = None
                    modified = True
                    item_changes[item] += 1
                continue

            if not _has_cat_keyword_in_segments(segments, seg_indices):
                old_cat = order["category"]
                order["category"] = None
                modified = True
                item_changes[item] += 1
                if dry_run and changed + (1 if modified else 0) <= 10:
                    seg_text = segments[seg_indices[0]].strip()
                    print(f"  #{i+1} [{item}] {old_cat}→null: \"{seg_text}\"")

        if modified:
            asst_msg["content"] = json.dumps(asst, ensure_ascii=False)
            changed += 1

    print(f"\n{filename}: {changed} 筆樣本修改")
    for item in MULTI_CAT_ITEMS:
        if item_changes[item]:
            print(f"  {item}: {item_changes[item]} orders → null")

    if not dry_run:
        with open(filepath, "w") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"已寫入: {filepath}")


def show_stats(filename: str):
    """顯示修正後的 null 比例。"""
    filepath = DATA_DIR / filename
    with open(filepath) as f:
        samples = [json.loads(line) for line in f]

    stats = {item: {"null": 0, "total": 0} for item in MULTI_CAT_ITEMS}
    for s in samples:
        asst = json.loads(next(m for m in s["messages"] if m["role"] == "assistant")["content"])
        for order in asst.get("orders", []):
            if not isinstance(order, dict):
                continue
            item = order.get("item", "")
            if item in stats:
                stats[item]["total"] += 1
                if order.get("category") is None:
                    stats[item]["null"] += 1

    print(f"\n--- {filename} category=null 比例 ---")
    for item in MULTI_CAT_ITEMS:
        s = stats[item]
        pct = s["null"] * 100 // max(s["total"], 1)
        bar = "█" * (pct // 3) + "░" * ((40 - pct) // 3)
        target = "✓" if pct >= 25 else "△" if pct >= 15 else "✗"
        print(f"  {item:<12} {s['null']:>3}/{s['total']:<3} ({pct:>2}%) {bar} {target}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    for fname in ["train.jsonl", "valid.jsonl"]:
        process_file(fname, dry_run=dry_run)

    if not dry_run:
        for fname in ["train.jsonl", "valid.jsonl"]:
            show_stats(fname)
