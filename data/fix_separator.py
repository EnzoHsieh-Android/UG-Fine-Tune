#!/usr/bin/env python3
"""Fix multi-turn separator: newline → semicolon"""

import json
from pathlib import Path

data_dir = Path(__file__).parent

def fix_separator(sample):
    """Replace newlines with semicolons in user input"""
    messages = sample.get("messages", [])

    for msg in messages:
        if msg.get("role") == "user":
            content = msg["content"]
            # Replace newlines with semicolons (with proper spacing)
            content = content.replace("\n", ";")
            msg["content"] = content

    return sample

def process_file(filepath):
    """Process a single jsonl file"""
    samples = []
    newline_count = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                sample = json.loads(line)

                # Count newlines in user content
                user_content = sample["messages"][1]["content"]
                newline_count += user_content.count("\n")

                samples.append(fix_separator(sample))

    # Write back
    with open(filepath, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    return len(samples), newline_count

# Process both files
train_count, train_newlines = process_file(data_dir / "train.jsonl")
valid_count, valid_newlines = process_file(data_dir / "valid.jsonl")

print("=== 分隔符修正完成 ===")
print(f"\ntrain.jsonl: {train_count} 樣本")
print(f"  - 換行 → 分號: {train_newlines} 處")

print(f"\nvalid.jsonl: {valid_count} 樣本")
print(f"  - 換行 → 分號: {valid_newlines} 處")

print(f"\n總計: {train_newlines + valid_newlines} 處換行已改為分號")
