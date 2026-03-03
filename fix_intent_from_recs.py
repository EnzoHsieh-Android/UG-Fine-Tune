#!/usr/bin/env python3
"""
修正 intents 分類：原始資料有 recommendations 但 intents 不含 recommend 的樣本。
這些是隱含推薦請求（「想配甜點」「不要奶的」等），分類器未能抓到。
策略：根據原始 recs 存在來反推正確的 intent。
"""

import json, re, sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def fix_file(filename: str, dry_run: bool = False):
    filepath = DATA_DIR / filename
    with open(filepath) as f:
        samples = [json.loads(line) for line in f]

    fixed = 0
    for i, sample in enumerate(samples):
        asst_msg = next(m for m in sample["messages"] if m["role"] == "assistant")
        user_msg = next(m for m in sample["messages"] if m["role"] == "user")
        asst = json.loads(asst_msg["content"])
        intents = asst.get("intents", [])
        recs = asst.get("recommendations", [])

        if "recommend" not in intents and recs:
            user_text = user_msg["content"]
            segments = re.split(r"[;；]", user_text)

            # 找最佳候選 segment 改為 recommend
            # 優先選 "other"，其次選第一個 segment
            best_idx = None
            for j, intent in enumerate(intents):
                if intent == "other":
                    best_idx = j
                    break
            if best_idx is None:
                # 沒有 other → 選第一個 segment（通常是隱含推薦的整段）
                best_idx = 0

            old_intent = intents[best_idx]
            intents[best_idx] = "recommend"
            asst["intents"] = intents
            asst_msg["content"] = json.dumps(asst, ensure_ascii=False)
            fixed += 1

            if dry_run and fixed <= 10:
                seg_text = segments[best_idx].strip() if best_idx < len(segments) else "?"
                print(f"  [{filename}#{i+1}] seg[{best_idx}] {old_intent}→recommend: \"{seg_text}\"")
                print(f"    user: {user_text[:70]}")
                print(f"    recs: {[r['item'] for r in recs]}")
                print()

    print(f"{filename}: 修正 {fixed} 筆 intents")

    if not dry_run:
        with open(filepath, "w") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"已寫入: {filepath}")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    for fname in ["train.jsonl", "valid.jsonl"]:
        fix_file(fname, dry_run=dry_run)
