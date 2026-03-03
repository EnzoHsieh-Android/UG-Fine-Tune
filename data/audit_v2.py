"""精準審計訓練資料品質 v2。

改善：
- 支援品項簡稱（桂花→桂花輕烏龍、鐵觀音→琥珀鐵觀音等）
- 支援分類後綴在品項前（兩杯奶蓋，桂花跟紅烏龍）
- 支援全域分類修飾（兩杯鮮奶）
- 支援修改場景（改/換/不對/要 + 分類後綴）
- 支援 STT 常見錯字
"""
import json
import re
import sys

# ===== 菜單 =====
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

SINGLE_SIZE_CATS = {"pure_tea", "fruit_tea", "cloud_velvet"}
VALID_SUGAR = {"全糖", "五分糖", "三分糖", "一分糖", "無糖", "正常糖", "少糖", "半糖", "微糖", None}
VALID_ICE = {"正常冰", "少冰", "微冰", "去冰", "熱飲", None}
VALID_SIZE = {"M", "L", None}
VALID_ADDON = {"紅烏龍茶凍", "燕麥粒"}

# 品項簡稱對照
ITEM_ALIASES = {
    "三窨十五茉": ["茉莉", "十五茉", "三窨"],
    "桂花輕烏龍": ["桂花", "桂花烏龍"],
    "茶花紅烏龍": ["紅烏龍", "茶花"],
    "茶花烏龍": ["茶花"],
    "琥珀鐵觀音": ["鐵觀音"],
    "金杯蜜香紅": ["蜜香紅", "金杯"],
    "朱槿普洱紅": ["普洱", "普洱紅", "朱槿"],
    "米香玉露菁": ["玉露", "玉露菁"],
    "青檸桂蜜": ["青檸"],
    "蜜桃紅烏龍": ["蜜桃"],
    "葡柚十五茉": ["葡柚"],
}

# 常見 STT 錯字
STT_TYPOS = {
    "貴花": "桂花", "規花": "桂花", "鬼花": "桂花",
    "鐵關音": "鐵觀音", "鐵官音": "鐵觀音",
    "三因": "三窨", "三印": "三窨",
    "仙奶": "鮮奶",
    "不理": "普洱", "不耳": "普洱",
}

CAT_SUFFIXES = {
    "fresh_milk_tea": "鮮奶",
    "rich_milk_tea": "奶茶",
    "pure_tea": "純茶",
    "cloud_velvet": "奶蓋",
    "fruit_tea": "果茶",
}

def normalize_text(text):
    """Apply known STT typo corrections for audit purposes."""
    for typo, correct in STT_TYPOS.items():
        text = text.replace(typo, correct)
    return text

def find_item_in_text(item, text):
    """Check if item (or its aliases) appears in text."""
    if item in text:
        return True
    for alias in ITEM_ALIASES.get(item, []):
        if alias in text:
            return True
    return False

def find_suffix_near_item(item, cat, text):
    """Check if category suffix is associated with this item in text."""
    suffix = CAT_SUFFIXES.get(cat, "")
    if not suffix:
        return False

    normalized = normalize_text(text)
    segments = re.split(r'[;；。]', normalized)

    # 1. 同 segment 中有品項（或簡稱）+ 後綴
    for seg in segments:
        item_found = item in seg or any(a in seg for a in ITEM_ALIASES.get(item, []))
        if item_found and suffix in seg:
            return True

    # 2. 全域分類修飾：segment 中有「N杯後綴」或「都要後綴」或「後綴+的」在其他 segment
    for seg in segments:
        if suffix in seg:
            # 常見全域修飾模式
            if re.search(r'(杯|都|全部|通通).*' + suffix, seg):
                return True
            if re.search(suffix + r'.*(杯|都|全部)', seg):
                return True

    # 3. 修改場景：modify segment 有修改詞 + 後綴
    modify_patterns = [
        r'(改|換|換成|要|不對).*' + suffix,
        suffix + r'.*就好',
        r'改成' + suffix,
    ]
    for seg in segments:
        for pat in modify_patterns:
            if re.search(pat, seg):
                return True

    # 4. 後綴在品項前面（如「鮮奶鐵觀音」或「奶蓋桂花」）
    for seg in segments:
        if suffix in seg:
            item_found = item in seg or any(a in seg for a in ITEM_ALIASES.get(item, []))
            if item_found:
                return True

    return False

errors = []
warnings = []

def err(line_no, msg):
    errors.append(f"  [ERROR] L{line_no}: {msg}")

def warn(line_no, msg):
    warnings.append(f"  [WARN]  L{line_no}: {msg}")

def audit_file(filepath):
    with open(filepath) as f:
        lines = f.readlines()

    print(f"\n{'='*60}")
    print(f"審計: {filepath} ({len(lines)} 筆)")
    print(f"{'='*60}")

    errors.clear()
    warnings.clear()

    for i, line in enumerate(lines, 1):
        obj = json.loads(line)
        msgs = obj.get("messages", [])

        if len(msgs) != 3:
            err(i, f"Expected 3 messages, got {len(msgs)}")
            continue

        sys_msg, user_msg, asst_msg = msgs[0], msgs[1], msgs[2]
        if sys_msg["role"] != "system":
            err(i, "First message should be system")
        if user_msg["role"] != "user":
            err(i, "Second message should be user")
        if asst_msg["role"] != "assistant":
            err(i, "Third message should be assistant")

        user_text = user_msg["content"]

        if "顧客" in user_text:
            err(i, f"Contains '顧客' prefix")

        try:
            resp = json.loads(asst_msg["content"])
        except json.JSONDecodeError:
            err(i, "Assistant content is not valid JSON")
            continue

        orders = resp.get("orders", [])
        recs = resp.get("recommendations", [])

        if len(recs) > 1:
            err(i, f"Too many recommendations: {len(recs)} (limit 1)")

        for j, o in enumerate(orders):
            item = o.get("item", "")
            cat = o.get("category")
            size = o.get("size")
            ice = o.get("ice")
            sugar = o.get("sugar")
            addon = o.get("addon", [])
            qty = o.get("qty", 1)

            # 品項是否在菜單（允許 NotOnMenu 樣本）
            if item not in ALL_ITEMS:
                # NotOnMenu items don't need further validation
                continue

            # Category 是否對該品項有效
            if cat is not None and item in ITEM_CATEGORIES:
                if cat not in ITEM_CATEGORIES[item]:
                    err(i, f"O[{j}] '{item}' cannot be '{cat}'. Valid: {ITEM_CATEGORIES[item]}")

            # 值合法性
            if sugar not in VALID_SUGAR:
                err(i, f"O[{j}] invalid sugar: '{sugar}'")
            if ice not in VALID_ICE:
                err(i, f"O[{j}] invalid ice: '{ice}'")
            if size not in VALID_SIZE:
                err(i, f"O[{j}] invalid size: '{size}'")
            for a in addon:
                if a not in VALID_ADDON:
                    err(i, f"O[{j}] invalid addon: '{a}'")
            if qty < 1:
                err(i, f"O[{j}] qty < 1")

            # 果茶不能熱飲
            if cat == "fruit_tea" and ice == "熱飲":
                err(i, f"O[{j}] fruit_tea cannot be 熱飲")

            # 單一尺寸不應有 size
            if cat in SINGLE_SIZE_CATS and size is not None:
                err(i, f"O[{j}] '{cat}' is single-size but size='{size}'")

            # ===== Category null 規則 =====
            if cat is not None and item in ITEM_CATEGORIES and len(ITEM_CATEGORIES[item]) > 1:
                if not find_suffix_near_item(item, cat, user_text):
                    err(i, f"O[{j}] '{item}' cat='{cat}' but user didn't specify. Text: {user_text[:80]}")

            # ===== Category 反向檢查：cat 為 null 但用戶有指定 =====
            if cat is None and item in ITEM_CATEGORIES and len(ITEM_CATEGORIES[item]) > 1:
                for possible_cat in ITEM_CATEGORIES[item]:
                    if find_suffix_near_item(item, possible_cat, user_text):
                        warn(i, f"O[{j}] '{item}' cat=null but user may have specified '{possible_cat}'")
                        break

    if errors:
        print(f"\n❌ {len(errors)} errors:")
        for e in errors:
            print(e)
    else:
        print(f"\n✅ No errors")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warnings:")
        for w in warnings:
            print(w)
    else:
        print(f"\n✅ No warnings")

    return len(errors), len(warnings)

# System prompt check
print("="*60)
print("System Prompt 比對")
print("="*60)
with open("/Users/xiechengru/ug-backend/service/llm.go") as f:
    go_content = f.read()
start = go_content.find('const systemPrompt = `') + len('const systemPrompt = `')
end = go_content.find('`', start)
go_prompt = go_content[start:end]

for path in ["round27.jsonl", "train.jsonl", "valid.jsonl"]:
    with open(path) as f:
        first = json.loads(f.readline())
    p = first["messages"][0]["content"]
    match = "✅" if go_prompt.strip() == p.strip() else "❌"
    print(f"  {match} {path}")

total_err = 0
total_warn = 0
for path in ["round27.jsonl", "train.jsonl", "valid.jsonl"]:
    e, w = audit_file(path)
    total_err += e
    total_warn += w

print(f"\n{'='*60}")
print(f"總計: {total_err} errors, {total_warn} warnings")
print(f"{'='*60}")
