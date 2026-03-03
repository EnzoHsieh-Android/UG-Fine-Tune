#!/usr/bin/env python3
"""Update all training data: change null ice/sugar defaults to 正常糖/正常冰"""

import json
from pathlib import Path

data_dir = Path(__file__).parent

# Old and new system prompt
OLD_PROMPT_PART = "未指定甜度或冰量時設為 null，由店員確認"
NEW_PROMPT_PART = "未指定甜度或冰量時設為 正常糖/正常冰"

def update_sample(sample):
    """Update a single sample with new defaults"""
    messages = sample.get("messages", [])

    for msg in messages:
        # Update system prompt
        if msg.get("role") == "system":
            msg["content"] = msg["content"].replace(OLD_PROMPT_PART, NEW_PROMPT_PART)

        # Update assistant response (JSON with orders)
        if msg.get("role") == "assistant":
            content = msg["content"]
            try:
                # Parse the JSON
                data = json.loads(content)
                orders = data.get("orders", [])

                for order in orders:
                    # Skip not_on_menu items
                    if order.get("not_on_menu"):
                        continue

                    # Update null sugar to 正常糖
                    if order.get("sugar") is None:
                        order["sugar"] = "正常糖"

                    # Update null ice to 正常冰
                    # But keep 熱飲 if explicitly set, and skip fruit_tea (cold only)
                    if order.get("ice") is None:
                        # fruit_tea is cold only, default to 正常冰
                        order["ice"] = "正常冰"

                # Rebuild JSON
                msg["content"] = json.dumps(data, ensure_ascii=False)
            except json.JSONDecodeError:
                # Not valid JSON, skip
                pass

    return sample

def process_file(filepath):
    """Process a single jsonl file"""
    samples = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                sample = json.loads(line)
                samples.append(update_sample(sample))

    # Write back
    with open(filepath, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    return len(samples)

# Process train.jsonl and valid.jsonl
train_count = process_file(data_dir / "train.jsonl")
valid_count = process_file(data_dir / "valid.jsonl")

print(f"Updated {train_count} samples in train.jsonl")
print(f"Updated {valid_count} samples in valid.jsonl")
print(f"Total: {train_count + valid_count} samples")
print(f"\nSystem prompt changed:")
print(f"  Before: {OLD_PROMPT_PART}")
print(f"  After:  {NEW_PROMPT_PART}")
print(f"\nDefault values changed:")
print(f"  sugar: null → 正常糖")
print(f"  ice: null → 正常冰")
