#!/usr/bin/env python3
"""Split training data into 80/20 train/valid sets"""

import json
import random
from pathlib import Path

# Set seed for reproducibility
random.seed(42)

data_dir = Path(__file__).parent

# Load all data
all_samples = []

# Load current train.jsonl
train_file = data_dir / "train.jsonl"
with open(train_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            all_samples.append(json.loads(line))

# Load current valid.jsonl
valid_file = data_dir / "valid.jsonl"
with open(valid_file, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            all_samples.append(json.loads(line))

print(f"Total samples: {len(all_samples)}")

# Shuffle
random.shuffle(all_samples)

# Split 80/20
split_idx = int(len(all_samples) * 0.8)
train_samples = all_samples[:split_idx]
valid_samples = all_samples[split_idx:]

print(f"Train samples: {len(train_samples)} ({len(train_samples)/len(all_samples)*100:.1f}%)")
print(f"Valid samples: {len(valid_samples)} ({len(valid_samples)/len(all_samples)*100:.1f}%)")

# Backup old files
train_file.rename(data_dir / "train.jsonl.bak")
valid_file.rename(data_dir / "valid.jsonl.bak")

# Write new files
with open(train_file, "w", encoding="utf-8") as f:
    for sample in train_samples:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")

with open(valid_file, "w", encoding="utf-8") as f:
    for sample in valid_samples:
        f.write(json.dumps(sample, ensure_ascii=False) + "\n")

print(f"\nDone! Old files backed up as .bak")
print(f"New train.jsonl: {len(train_samples)} samples")
print(f"New valid.jsonl: {len(valid_samples)} samples")
