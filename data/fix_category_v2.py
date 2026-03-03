"""修正 train.jsonl/valid.jsonl 中的 category 錯誤 v2。

修正策略（保守）：
- 只在同一 segment 中品項+後綴明確不匹配時修正
- 修改詞後續的 segment 優先（後蓋前）
- 不處理 round27.jsonl（那些是刻意的修改場景）
- 同品項多筆 order 不自動修正（需人工審核）
"""
import json
import re
import sys

MENU = {
    "pure_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁"],
    "fresh_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "rich_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "fruit_tea": ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"],
    "cloud_velvet": ["桂花輕烏龍", "茶花紅烏龍"],
}
ALL_ITEMS = set()
for items in MENU.values():
    ALL_ITEMS.update(items)
ITEM_CATEGORIES = {}
for cat, items in MENU.items():
    for item in items:
        ITEM_CATEGORIES.setdefault(item, []).append(cat)

ITEM_ALIASES = {
    "三窨十五茉": ["茉莉", "十五茉", "三窨"],
    "桂花輕烏龍": ["桂花", "桂花烏龍"],
    "茶花紅烏龍": ["紅烏龍", "茶花"],
    "茶花烏龍": ["茶花"],
    "琥珀鐵觀音": ["鐵觀音"],
    "金杯蜜香紅": ["蜜香紅", "金杯"],
    "朱槿普洱紅": ["普洱", "普洱紅", "朱槿"],
    "米香玉露菁": ["玉露", "玉露菁"],
}

STT_TYPOS = {
    "貴花": "桂花", "規花": "桂花", "鬼花": "桂花",
    "鐵關音": "鐵觀音", "鐵官音": "鐵觀音", "鐵觀因": "鐵觀音",
    "三因": "三窨", "三印": "三窨",
    "仙奶": "鮮奶",
    "不理": "普洱", "不耳": "普洱",
    "湖泊": "琥珀",
}

SUFFIX_TO_CAT = {
    "鮮奶": "fresh_milk_tea",
    "奶茶": "rich_milk_tea",
    "純茶": "pure_tea",
    "奶蓋": "cloud_velvet",
    "果茶": "fruit_tea",
}

MODIFY_WORDS = ["改", "換", "不對", "換成"]

def normalize(text):
    for typo, correct in STT_TYPOS.items():
        text = text.replace(typo, correct)
    return text

def item_in_seg(item, seg):
    if item in seg:
        return True
    for alias in ITEM_ALIASES.get(item, []):
        if alias in seg:
            return True
    return False

def find_suffix_in_seg(seg):
    for suffix in ["鮮奶", "奶蓋", "奶茶", "純茶", "果茶"]:
        if suffix in seg:
            return suffix, SUFFIX_TO_CAT[suffix]
    return None, None

def count_item_orders(item, orders):
    """Count how many orders have this item."""
    return sum(1 for o in orders if o.get('item') == item)

def determine_final_category(item, user_text):
    """Determine the FINAL intended category for an item, accounting for modify overrides.

    Tracks the category through all segments, with later mentions overriding earlier ones.
    Returns (category, confidence) or (None, None) if cannot determine.
    """
    normalized = normalize(user_text)
    segments = re.split(r'[;；。]', normalized)

    found_cat = None
    found_confidence = None

    last_item_seg_idx = -1  # Track last segment that has our item

    for si, seg in enumerate(segments):
        # Check if this item (or alias) is in this segment
        if item_in_seg(item, seg):
            last_item_seg_idx = si
            suffix, cat = find_suffix_in_seg(seg)
            if cat and item in ITEM_CATEGORIES and cat in ITEM_CATEGORIES[item]:
                found_cat = cat
                found_confidence = 'high'

        # Check if this is a modify segment that affects this item
        has_modify = any(kw in seg for kw in MODIFY_WORDS)
        if has_modify:
            suffix, cat = find_suffix_in_seg(seg)
            if cat and item in ITEM_CATEGORIES and cat in ITEM_CATEGORIES[item]:
                if item_in_seg(item, seg):
                    # Modify explicitly references our item
                    found_cat = cat
                    found_confidence = 'high'
                elif last_item_seg_idx >= 0 and si == last_item_seg_idx + 1:
                    # Orphan modify right after the item segment
                    # Only apply if no other item in the modify segment
                    has_other = any(
                        item_in_seg(other, seg)
                        for other in ALL_ITEMS if other != item
                    )
                    if not has_other:
                        found_cat = cat
                        found_confidence = 'high'

    # Also check: item in seg N, suffix in seg N+1 where N+1 has no other item
    if found_cat is None:
        for si, seg in enumerate(segments):
            if item_in_seg(item, seg):
                for offset in [1, 2]:
                    if si + offset < len(segments):
                        next_seg = segments[si + offset]
                        # Only if next segment has no other menu item
                        has_other = any(
                            item_in_seg(other, next_seg)
                            for other in ALL_ITEMS if other != item
                        )
                        if not has_other:
                            suffix, cat = find_suffix_in_seg(next_seg)
                            if cat and item in ITEM_CATEGORIES and cat in ITEM_CATEGORIES[item]:
                                found_cat = cat
                                found_confidence = 'medium'
                                break
                if found_cat:
                    break

    # Final check: "change of mind" override in segments after the item
    # Patterns like "其實要鮮奶好了", "算了改奶蓋", "還是純茶好了"
    if found_cat and last_item_seg_idx >= 0:
        for si in range(last_item_seg_idx + 1, len(segments)):
            seg = segments[si]
            has_other_item = any(
                item_in_seg(other, seg)
                for other in ALL_ITEMS if other != item
            )
            if has_other_item:
                break
            change_mind = any(kw in seg for kw in ["其實", "算了", "還是"])
            if change_mind:
                suffix, cat = find_suffix_in_seg(seg)
                if cat and item in ITEM_CATEGORIES and cat in ITEM_CATEGORIES[item]:
                    found_cat = cat
                    found_confidence = 'high'

    return found_cat, found_confidence

def fix_file(filepath, dry_run=True):
    with open(filepath) as f:
        lines = f.readlines()

    fixes = []
    skips = []
    fixed_lines = []

    for i, line in enumerate(lines, 1):
        obj = json.loads(line)
        msgs = obj['messages']
        if len(msgs) != 3:
            fixed_lines.append(line)
            continue

        user_text = msgs[1]['content']

        try:
            resp = json.loads(msgs[2]['content'])
        except:
            fixed_lines.append(line)
            continue

        orders = resp.get('orders', [])
        changed = False

        for j, o in enumerate(orders):
            item = o.get('item', '')
            cat = o.get('category')

            if item not in ITEM_CATEGORIES:
                continue
            if len(ITEM_CATEGORIES[item]) <= 1:
                continue
            if cat is None:
                continue

            # Skip if same item appears multiple times (ambiguous)
            if count_item_orders(item, orders) > 1:
                skips.append(f"  L{i} O[{j}] '{item}': SKIP (same item multi-order)")
                continue

            intended_cat, confidence = determine_final_category(item, user_text)

            if intended_cat and intended_cat != cat:
                fixes.append(f"  L{i} O[{j}] '{item}': {cat} → {intended_cat} [{confidence}] | {user_text[:70]}")
                o['category'] = intended_cat
                changed = True

        if changed:
            resp['orders'] = orders
            msgs[2]['content'] = json.dumps(resp, ensure_ascii=False)
            obj['messages'] = msgs
            fixed_lines.append(json.dumps(obj, ensure_ascii=False) + '\n')
        else:
            fixed_lines.append(line)

    print(f"\n{'='*60}")
    print(f"  {filepath}: {len(fixes)} fixes, {len(skips)} skipped")
    print(f"{'='*60}")
    for f_msg in fixes:
        print(f_msg)
    if skips:
        print(f"\n  Skipped (same-item multi-order):")
        for s in skips[:5]:
            print(s)
        if len(skips) > 5:
            print(f"  ... and {len(skips)-5} more")

    if not dry_run and fixes:
        with open(filepath, 'w') as f:
            f.writelines(fixed_lines)
        print(f"  → Written to {filepath}")

    return len(fixes)

if __name__ == '__main__':
    dry_run = '--fix' not in sys.argv
    if dry_run:
        print("DRY RUN (use --fix to apply)")
    else:
        print("APPLYING FIXES")

    total = 0
    # Only fix existing data, not round27
    for path in ['train.jsonl', 'valid.jsonl']:
        total += fix_file(path, dry_run=dry_run)

    print(f"\nTotal: {total} fixes {'(dry run)' if dry_run else '(applied)'}")
