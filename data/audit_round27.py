"""全面審計 Round 27 訓練資料品質。

檢查項目：
1. System prompt 與後端 llm.go 一致
2. 品項名正確（在菜單內 or 刻意 NotOnMenu）
3. Category 對該品項有效
4. 甜度/冰量/尺寸值合法
5. 單一分類品項的 category 邏輯
6. 多分類品項未指定分類 → null
7. 果茶不能熱飲
8. 純茶/奶蓋/果茶沒有尺寸
9. Addon 值合法
10. 修改詞 → 只有替換（不新增重複）
11. 新增詞 → 有多筆 order
12. 無「顧客：」前綴
13. qty ≥ 1
14. recommendations 限 1 項
"""
import json
import re
import sys

# 菜單定義
MENU = {
    "pure_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁"],
    "fresh_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "rich_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "fruit_tea": ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"],
    "cloud_velvet": ["桂花輕烏龍", "茶花紅烏龍"],
}

# 所有品項
ALL_ITEMS = set()
for items in MENU.values():
    ALL_ITEMS.update(items)

# 品項 → 可用分類
ITEM_CATEGORIES = {}
for cat, items in MENU.items():
    for item in items:
        ITEM_CATEGORIES.setdefault(item, []).append(cat)

# 單一尺寸分類（沒有 M/L）
SINGLE_SIZE_CATS = {"pure_tea", "fruit_tea", "cloud_velvet"}
# 有 M/L 的分類
ML_CATS = {"fresh_milk_tea", "rich_milk_tea"}

VALID_SUGAR = {"正常糖", "少糖", "半糖", "微糖", "無糖", None}
VALID_ICE = {"正常冰", "少冰", "微冰", "去冰", "熱飲", None}
VALID_SIZE = {"M", "L", None}
VALID_ADDON = {"紅烏龍茶凍", "燕麥粒"}

MODIFY_WORDS = ["改", "換", "不對"]
ADD_WORDS = ["再來", "還要", "加一杯", "再加", "再一杯"]

errors = []
warnings = []

def err(line_no, msg):
    errors.append(f"  [ERROR] Line {line_no}: {msg}")

def warn(line_no, msg):
    warnings.append(f"  [WARN]  Line {line_no}: {msg}")

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

        # 檢查訊息格式
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

        # 檢查無「顧客：」前綴
        if "顧客" in user_text:
            err(i, f"Contains '顧客' prefix: {user_text[:50]}")

        # 解析 assistant 回覆
        try:
            resp = json.loads(asst_msg["content"])
        except json.JSONDecodeError:
            err(i, "Assistant content is not valid JSON")
            continue

        orders = resp.get("orders", [])
        recs = resp.get("recommendations", [])
        prefs = resp.get("preferences", {})

        # 推薦限 1 項
        if len(recs) > 1:
            err(i, f"Too many recommendations: {len(recs)} (limit 1)")

        # 檢查每筆 order
        for j, o in enumerate(orders):
            item = o.get("item", "")
            cat = o.get("category")
            size = o.get("size")
            ice = o.get("ice")
            sugar = o.get("sugar")
            addon = o.get("addon", [])
            qty = o.get("qty", 1)

            # 品項名檢查
            if item not in ALL_ITEMS and item != "珍珠奶茶":  # 珍珠奶茶是刻意的 NotOnMenu
                if item not in ALL_ITEMS:
                    warn(i, f"Order[{j}] item '{item}' not in menu")

            # Category 檢查
            if cat is not None and item in ITEM_CATEGORIES:
                if cat not in ITEM_CATEGORIES[item]:
                    err(i, f"Order[{j}] '{item}' cannot be '{cat}'. Valid: {ITEM_CATEGORIES[item]}")

            # 甜度/冰量/尺寸值合法性
            if sugar not in VALID_SUGAR:
                err(i, f"Order[{j}] invalid sugar: '{sugar}'")
            if ice not in VALID_ICE:
                err(i, f"Order[{j}] invalid ice: '{ice}'")
            if size not in VALID_SIZE:
                err(i, f"Order[{j}] invalid size: '{size}'")

            # Addon 合法性
            for a in addon:
                if a not in VALID_ADDON:
                    err(i, f"Order[{j}] invalid addon: '{a}'")

            # Qty 檢查
            if qty < 1:
                err(i, f"Order[{j}] qty < 1: {qty}")

            # 果茶不能熱飲
            if cat == "fruit_tea" and ice == "熱飲":
                err(i, f"Order[{j}] fruit_tea cannot be 熱飲")

            # 單一尺寸分類不應有 size
            if cat in SINGLE_SIZE_CATS and size is not None:
                err(i, f"Order[{j}] '{cat}' is single-size, but size='{size}'")

            # Category null 規則：多分類品項，只說品項名（用戶文本同segment中未出現分類後綴）→ null
            if cat is not None and item in ITEM_CATEGORIES and len(ITEM_CATEGORIES[item]) > 1:
                # 檢查用戶是否在文本中指定了分類
                cat_suffixes = {
                    "fresh_milk_tea": "鮮奶",
                    "rich_milk_tea": "奶茶",
                    "pure_tea": "純茶",
                    "cloud_velvet": "奶蓋",
                    "fruit_tea": "果茶",
                }
                suffix = cat_suffixes.get(cat, "")
                segments = re.split(r'[;；。]', user_text)

                # 找到包含此品項的 segments
                item_segments = [s for s in segments if item in s]
                suffix_found = any(suffix in s for s in item_segments) if suffix else False

                if not suffix_found:
                    # 也檢查修改詞指代的情況
                    has_modify_ref = any(
                        any(kw in s for kw in ["改" + suffix, "換" + suffix, "換成" + suffix, "要" + suffix])
                        for s in segments if suffix
                    )
                    if not has_modify_ref:
                        err(i, f"Order[{j}] '{item}' has cat='{cat}' but no suffix '{suffix}' found in user text for this item. Should be null?")

        # 修改詞邏輯檢查
        segments = user_text.split(";")
        has_modify = any(any(kw in seg for kw in MODIFY_WORDS) for seg in segments)
        has_add = any(any(kw in seg for kw in ADD_WORDS) for seg in segments)

        # 如果有修改詞且無新增詞 → 最終 order 數應 <= 第一輪 order 數
        if has_modify and not has_add and len(segments) >= 2:
            # 第一輪的品項數（分號分隔的前面 segments）
            first_round_items = []
            modify_start = -1
            for si, seg in enumerate(segments):
                if any(kw in seg for kw in MODIFY_WORDS + ["第"]):
                    modify_start = si
                    break
            if modify_start > 0:
                first_count = modify_start  # 前面有幾個 segment = 幾杯
                if len(orders) > first_count:
                    warn(i, f"Modify scenario: {first_count} items before modify, but {len(orders)} orders in output")

    # 報告
    if errors:
        print(f"\n❌ {len(errors)} errors found:")
        for e in errors:
            print(e)
    else:
        print(f"\n✅ No errors found")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warnings:")
        for w in warnings:
            print(w)

    return len(errors), len(warnings)

# System prompt 比對
print("="*60)
print("System Prompt 比對")
print("="*60)

with open("/Users/xiechengru/ug-backend/service/llm.go") as f:
    go_content = f.read()

# 提取 Go 的 system prompt
start = go_content.find('const systemPrompt = `') + len('const systemPrompt = `')
end = go_content.find('`', start)
go_prompt = go_content[start:end]

with open("round27.jsonl") as f:
    first_line = json.loads(f.readline())
    train_prompt = first_line["messages"][0]["content"]

if go_prompt.strip() == train_prompt.strip():
    print("✅ System prompt matches llm.go")
else:
    print("❌ System prompt MISMATCH!")
    # Show diff
    go_lines = go_prompt.strip().split('\n')
    train_lines = train_prompt.strip().split('\n')
    for i, (g, t) in enumerate(zip(go_lines, train_lines)):
        if g != t:
            print(f"  Line {i+1}:")
            print(f"    Go:    {g}")
            print(f"    Train: {t}")

# 也檢查既有訓練資料的 system prompt
with open("train.jsonl") as f:
    first_existing = json.loads(f.readline())
    existing_prompt = first_existing["messages"][0]["content"]

if go_prompt.strip() == existing_prompt.strip():
    print("✅ Existing train.jsonl system prompt matches llm.go")
else:
    print("❌ Existing train.jsonl system prompt MISMATCH!")

# 審計各檔案
total_err = 0
total_warn = 0

for path in ["round27.jsonl", "train.jsonl", "valid.jsonl"]:
    e, w = audit_file(path)
    total_err += e
    total_warn += w

print(f"\n{'='*60}")
print(f"總計: {total_err} errors, {total_warn} warnings")
print(f"{'='*60}")
