"""修正訓練資料中的 category 錯誤。

目標：找出用戶明確指定分類後綴但 model output 給了錯誤 category 的樣本，修正之。

策略：
1. 在同一 segment 中找到品項（或簡稱）+ 分類後綴 → 該品項的 category 應對應此後綴
2. 若無法在同一 segment 找到 → 檢查前後 segment 是否有「分段點餐」模式
3. 修改詞（改/換/不對）+ 後綴 → 修正引用的品項
4. 若 category 不匹配 → 修正
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

def normalize(text):
    for typo, correct in STT_TYPOS.items():
        text = text.replace(typo, correct)
    return text

def item_in_seg(item, seg):
    """Check if item or any alias is in segment."""
    if item in seg:
        return True
    for alias in ITEM_ALIASES.get(item, []):
        if alias in seg:
            return True
    return False

def find_suffix_in_seg(seg):
    """Find category suffix in segment. Returns (suffix, category) or None."""
    # Order matters: 鮮奶 before 奶 to avoid partial match
    # Also check 奶蓋 before 奶茶 to avoid partial match
    for suffix in ["鮮奶", "奶蓋", "奶茶", "純茶", "果茶"]:
        if suffix in seg:
            return suffix, SUFFIX_TO_CAT[suffix]
    return None, None

def determine_intended_category(item, user_text):
    """Determine what category the user intended for this item.

    Returns: (category, confidence)
      - category: the intended category ID
      - confidence: 'high' if found in same segment, 'medium' if adjacent, None if not found
    """
    normalized = normalize(user_text)
    segments = re.split(r'[;；。]', normalized)

    # Pass 1: Check same segment (highest confidence)
    for si, seg in enumerate(segments):
        if item_in_seg(item, seg):
            suffix, cat = find_suffix_in_seg(seg)
            if cat and item in ITEM_CATEGORIES and cat in ITEM_CATEGORIES[item]:
                return cat, 'high'

    # Pass 2: Check adjacent segment (item in seg N, suffix in seg N+1 with no other item)
    for si, seg in enumerate(segments):
        if item_in_seg(item, seg):
            # Check next segment
            if si + 1 < len(segments):
                next_seg = segments[si + 1]
                # Only if next segment doesn't contain another item
                has_other_item = any(
                    item_in_seg(other, next_seg)
                    for other in ALL_ITEMS
                    if other != item
                )
                if not has_other_item:
                    suffix, cat = find_suffix_in_seg(next_seg)
                    if cat and item in ITEM_CATEGORIES and cat in ITEM_CATEGORIES[item]:
                        return cat, 'medium'
                    # Also check N+2 for patterns like "品項;鮮奶的;半糖"
                    if si + 2 < len(segments):
                        next2 = segments[si + 2]
                        has_other_item2 = any(
                            item_in_seg(other, next2)
                            for other in ALL_ITEMS
                            if other != item
                        )
                        if not has_other_item2:
                            suffix2, cat2 = find_suffix_in_seg(next2)
                            if cat2 and item in ITEM_CATEGORIES and cat2 in ITEM_CATEGORIES[item]:
                                return cat2, 'medium'

    # Pass 3: Check modify segments (改/換/不對 + suffix)
    for si, seg in enumerate(segments):
        modify_words = ["改", "換", "不對", "換成"]
        has_modify = any(kw in seg for kw in modify_words)
        if has_modify:
            suffix, cat = find_suffix_in_seg(seg)
            if cat and item in ITEM_CATEGORIES and cat in ITEM_CATEGORIES[item]:
                # This is a modify, applies to some item
                # But which item? Check if this modify references our item
                if item_in_seg(item, seg):
                    return cat, 'high'
                # If no item in this segment, it modifies the most recently mentioned item
                # This is ambiguous so we skip it

    # Pass 4: Global category (e.g., "兩杯奶蓋" or "都要鮮奶")
    for seg in segments:
        if re.search(r'(杯|都|全部|通通|兩|三)', seg):
            suffix, cat = find_suffix_in_seg(seg)
            if cat and item in ITEM_CATEGORIES and cat in ITEM_CATEGORIES[item]:
                return cat, 'medium'

    return None, None

def fix_file(filepath, dry_run=True):
    with open(filepath) as f:
        lines = f.readlines()

    fixes = []
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

            intended_cat, confidence = determine_intended_category(item, user_text)

            if intended_cat and intended_cat != cat:
                # Only fix high-confidence mismatches
                if confidence == 'high':
                    fixes.append(f"  L{i} O[{j}] '{item}': {cat} → {intended_cat} (text: {user_text[:60]})")
                    o['category'] = intended_cat
                    changed = True
                elif confidence == 'medium':
                    fixes.append(f"  L{i} O[{j}] '{item}': {cat} → {intended_cat} [medium] (text: {user_text[:60]})")
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
    print(f"  {filepath}: {len(fixes)} fixes")
    print(f"{'='*60}")
    for f_msg in fixes:
        print(f_msg)

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
    for path in ['round27.jsonl', 'train.jsonl', 'valid.jsonl']:
        total += fix_file(path, dry_run=dry_run)

    print(f"\nTotal: {total} fixes {'(dry run)' if dry_run else '(applied)'}")
