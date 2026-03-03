#!/usr/bin/env python3
"""
Step 7a: 為訓練資料加入 per-segment intents 陣列。
讀取 train.jsonl / valid.jsonl，對每筆樣本：
  1. 切分 user text by ";" 或 "；"
  2. 對每段分類 intent: order / recommend / modify / other
  3. 插入 intents 到 assistant output JSON (放在最前面)
"""

import json, re, sys, shutil, os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ── 菜單品項名稱片段（用於偵測 order intent）──
ITEM_FRAGMENTS = [
    # 完整品名
    "三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁",
    "琥珀鐵觀音", "金杯蜜香紅", "青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉",
    # 常見簡稱 / 別名
    "鐵觀音", "茉莉", "紅烏龍", "輕烏龍", "蜜香紅", "普洱", "玉露",
    "桂蜜", "蜜桃", "葡柚", "十五茉", "玉露菁", "桂花",
    # ASR 常見變體
    "茶花烏龍", "桂花烏龍", "金杯", "朱槿",
]

# ── 推薦關鍵字 ──
REC_KEYWORDS = [
    "推薦", "建議", "有什麼", "有沒有", "適合", "招牌", "第一次",
    "幫我選", "幫我挑", "什麼好喝", "喝什麼", "來點什麼",
    "有哪些", "有啥", "選擇障礙", "不知道喝什麼", "不知道要什麼",
    "想試試", "試試看", "人氣", "熱門", "暢銷", "最多人點",
    "清爽", "解膩", "提神", "花香", "果香", "甜一點", "苦一點",
    "不太甜", "微苦", "帶酸", "回甘", "濃郁", "清新",
    "外帶給", "送人", "下午茶", "夏天", "冬天", "天氣熱", "天氣冷",
    "還有別的", "還有其他", "換一個", "其他推薦", "還有嗎",
]

# ── 修改關鍵字 ──
MODIFY_KEYWORDS = [
    "改", "換成", "不要了", "取消", "算了", "去掉", "拿掉", "不用",
    "不加", "少一點", "多一點",
]

# ── 點餐語境詞 ──
ORDER_PATTERNS = [
    "一杯", "兩杯", "三杯", "四杯", "五杯",
    "1杯", "2杯", "3杯", "來杯", "來一杯", "來兩杯",
    "再一杯", "再來", "再一個", "加一杯", "加點",
    "要一杯", "點一杯", "幫我點",
    "鮮奶", "奶茶", "純茶", "奶蓋", "大杯", "中杯",
    "加茶凍", "加燕麥", "燕麥粒", "茶凍",
]

# ── 甜度 / 冰量 / 尺寸（純客製化，用於判斷 modify）──
CUSTOM_ONLY_PATTERNS = [
    "全糖", "五分糖", "三分糖", "一分糖", "無糖", "半糖", "少糖", "微糖", "正常糖",
    "正常冰", "少冰", "微冰", "去冰", "熱飲", "熱的", "溫的",
    "大杯", "中杯",
]


def _has_item(seg: str) -> bool:
    """檢查 segment 是否包含菜單品項名稱片段。"""
    return any(item in seg for item in ITEM_FRAGMENTS)


# 「有什麼」「有沒有」後接這些詞時不算推薦
REC_EXCLUDE_AFTER = ["優惠", "不一樣", "差別", "區別", "折扣", "活動", "差"]

# 「有沒有」+ 非飲品名詞 → other
NON_DRINK_NOUNS = [
    "停車位", "停車場", "集點卡", "會員", "座位", "位子", "廁所",
    "插座", "WiFi", "wifi", "外送", "外帶袋", "發票", "統編", "載具",
    "LINE Pay", "line pay", "信用卡", "行動支付", "現金",
]

# 點餐動詞（用於判斷 recommend+item → order）
ORDERING_VERBS = ["來", "要", "點", "加", "給我", "幫我", "就"]


def _has_ordering_verb(seg: str) -> bool:
    """檢查是否含點餐動詞。"""
    return any(v in seg for v in ORDERING_VERBS)


def classify_segment(seg: str, seg_index: int, total_segs: int) -> str:
    """分類單一 segment 的 intent。"""
    seg = seg.strip()
    if not seg:
        return "other"

    # 1. 推薦（帶上下文檢查避免誤判）
    is_rec = False
    for kw in REC_KEYWORDS:
        if kw not in seg:
            continue

        # 「有什麼」「有沒有」需額外排除非推薦語境
        if kw in ("有什麼", "有沒有", "有哪些", "有啥"):
            pos = seg.index(kw) + len(kw)
            rest = seg[pos:]
            # 後面接排除詞 → 不算推薦
            if any(ex in rest for ex in REC_EXCLUDE_AFTER):
                continue
            # 「有沒有」+ 品項名 → other（問有沒有賣）
            if kw == "有沒有" and _has_item(seg):
                continue
            # 「有沒有」+ 非飲品名詞 → other
            if kw == "有沒有" and any(n in seg for n in NON_DRINK_NOUNS):
                continue

        # 口味偏好詞若同段有品項 → order 而非 recommend
        if kw in ("甜一點", "苦一點", "微苦", "微甜"):
            if _has_item(seg):
                continue

        # 「推薦」為引用（朋友推薦的/別人推薦/推薦來的）而非請求 → 不算 recommend
        if kw == "推薦" and re.search(r"(朋友|別人|同事|他|她|人家)推薦", seg):
            continue
        if kw == "推薦" and "推薦來的" in seg:
            continue
        if kw == "推薦" and "推薦的" in seg and _has_item(seg) and _has_ordering_verb(seg):
            continue

        # 「第一次」「不知道」但同段已有品項+點餐動詞 → 已決定，是 order
        if kw in ("第一次", "不知道喝什麼", "不知道要什麼"):
            if _has_item(seg) and _has_ordering_verb(seg):
                continue

        # 通用：recommend 關鍵字 + 品項 + 點餐動詞 → order（已決定）
        if _has_item(seg) and _has_ordering_verb(seg):
            continue

        is_rec = True
        break

    if is_rec:
        return "recommend"

    # 2. 修改（明確修改動詞）
    for kw in MODIFY_KEYWORDS:
        if kw in seg:
            # 特例："改" + 品項名 → 可能是換單（"改喝鐵觀音"），視為 order
            if kw == "改" and _has_item(seg):
                return "order"
            return "modify"

    # 3. 包含品項名稱 → order（但排除純粹問問題的語境）
    if _has_item(seg):
        # 「X跟Y有什麼不一樣」「X和Y差在哪」→ other
        if re.search(r"(跟|和|與).+(有什麼|差在|差別|不一樣|區別)", seg):
            return "other"
        return "order"

    # 4. 包含點餐語境詞 → order
    for pat in ORDER_PATTERNS:
        if pat in seg:
            return "order"

    # 5. 純客製化詞（非首段 → modify，首段 → order 的一部分）
    has_custom = any(c in seg for c in CUSTOM_ONLY_PATTERNS)
    if has_custom and seg_index > 0:
        return "modify"
    if has_custom and seg_index == 0:
        return "order"

    # 6. 其他
    return "other"


def process_sample(sample: dict) -> dict:
    """為單一樣本加入 intents 陣列。"""
    messages = sample["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    asst_msg = next(m for m in messages if m["role"] == "assistant")

    user_text = user_msg["content"]
    # 切分 segments（用中英文分號）
    segments = re.split(r"[;；]", user_text)

    intents = []
    for i, seg in enumerate(segments):
        intent = classify_segment(seg, i, len(segments))
        intents.append(intent)

    # 解析 assistant output 並插入 intents
    asst_json = json.loads(asst_msg["content"])
    # 建立新 dict，intents 放最前面
    new_asst = {"intents": intents}
    for k, v in asst_json.items():
        new_asst[k] = v

    asst_msg["content"] = json.dumps(new_asst, ensure_ascii=False)
    return sample


def validate_sample(sample: dict) -> list[str]:
    """驗證 intents 的正確性，回傳錯誤訊息列表。"""
    errors = []
    messages = sample["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    asst_msg = next(m for m in messages if m["role"] == "assistant")

    user_text = user_msg["content"]
    segments = re.split(r"[;；]", user_text)
    asst_json = json.loads(asst_msg["content"])
    intents = asst_json.get("intents", [])

    # 1. 長度一致
    if len(intents) != len(segments):
        errors.append(f"intents 長度 {len(intents)} != segments {len(segments)}")

    # 2. 每個值合法
    valid_values = {"order", "recommend", "modify", "other"}
    for i, intent in enumerate(intents):
        if intent not in valid_values:
            errors.append(f"intents[{i}]={intent} 不合法")

    return errors


def process_file(filename: str, dry_run: bool = False):
    """處理單一 JSONL 檔案。"""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"  [SKIP] {filepath} 不存在")
        return

    with open(filepath) as f:
        samples = [json.loads(line) for line in f]

    print(f"\n{'='*60}")
    print(f"處理 {filename}: {len(samples)} 筆樣本")
    print(f"{'='*60}")

    # 統計
    intent_counts = {"order": 0, "recommend": 0, "modify": 0, "other": 0}
    total_segments = 0
    error_count = 0
    processed = []

    for i, sample in enumerate(samples):
        try:
            result = process_sample(sample)
            errors = validate_sample(result)
            if errors:
                user = next(m for m in result["messages"] if m["role"] == "user")["content"]
                print(f"  [WARN] 樣本 #{i+1}: {errors}")
                print(f"         user: {user[:80]}")
                error_count += 1

            # 統計 intents
            asst = json.loads(next(m for m in result["messages"] if m["role"] == "assistant")["content"])
            for intent in asst.get("intents", []):
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
                total_segments += 1

            processed.append(result)
        except Exception as e:
            print(f"  [ERROR] 樣本 #{i+1}: {e}")
            error_count += 1
            processed.append(sample)

    # 顯示統計
    print(f"\n--- 統計 ---")
    print(f"總 segments: {total_segments}")
    for intent, count in sorted(intent_counts.items(), key=lambda x: -x[1]):
        pct = count * 100 / max(total_segments, 1)
        print(f"  {intent}: {count} ({pct:.1f}%)")
    if error_count:
        print(f"  驗證錯誤: {error_count}")

    if not dry_run:
        # 備份
        backup = filepath.with_suffix(".jsonl.bak_intents")
        if not backup.exists():
            shutil.copy2(filepath, backup)
            print(f"\n備份: {backup}")

        # 寫入
        with open(filepath, "w") as f:
            for s in processed:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"已寫入: {filepath}")
    else:
        print(f"\n[DRY RUN] 不寫入檔案")


def show_examples(filename: str, n: int = 10):
    """顯示前 n 筆的 intents 結果。"""
    filepath = DATA_DIR / filename
    with open(filepath) as f:
        samples = [json.loads(line) for line in f]

    print(f"\n--- {filename} 前 {n} 筆 intents 範例 ---")
    for i, sample in enumerate(samples[:n]):
        user = next(m for m in sample["messages"] if m["role"] == "user")["content"]
        asst = json.loads(next(m for m in sample["messages"] if m["role"] == "assistant")["content"])
        intents = asst.get("intents", [])
        segments = re.split(r"[;；]", user)
        print(f"\n#{i+1} user: {user[:80]}")
        for j, (seg, intent) in enumerate(zip(segments, intents)):
            print(f"    seg[{j}]: \"{seg.strip()}\" → {intent}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    examples_only = "--examples" in sys.argv

    if examples_only:
        # 先處理到記憶體看結果
        for fname in ["train.jsonl", "valid.jsonl"]:
            filepath = DATA_DIR / fname
            with open(filepath) as f:
                samples = [json.loads(line) for line in f]
            for s in samples[:15]:
                process_sample(s)
            show_examples_from_processed(samples[:15])
        sys.exit(0)

    for fname in ["train.jsonl", "valid.jsonl"]:
        process_file(fname, dry_run=dry_run)

    if not dry_run:
        # 顯示範例確認
        for fname in ["train.jsonl", "valid.jsonl"]:
            show_examples(fname, n=10)
