#!/usr/bin/env python3
"""
GPTQ 8-bit 量化腳本，在 RunPod A40 上執行。
將 FP16 合併模型量化為 GPTQ 8-bit，用校準資料做權重校準。
"""

import json
import time
from pathlib import Path

from gptqmodel import GPTQModel, QuantizeConfig
from transformers import AutoTokenizer

# 路徑設定（RunPod 上的路徑）
MODEL_PATH = "/workspace/model/Qwen3-8B-UG-order-v11"
CALIBRATION_PATH = "/workspace/calibration_data.json"
OUTPUT_PATH = "/workspace/model/Qwen3-8B-UG-order-v11-gptq-8bit"

# 量化參數
BITS = 8
GROUP_SIZE = 128


def main():
    print("=" * 60)
    print("GPTQ 8-bit Quantization")
    print(f"  Model: {MODEL_PATH}")
    print(f"  Bits: {BITS}, Group Size: {GROUP_SIZE}")
    print("=" * 60)

    # 1. 載入校準資料
    print("\n[1/4] Loading calibration data...")
    with open(CALIBRATION_PATH, "r", encoding="utf-8") as f:
        calibration_texts = json.load(f)
    print(f"  Loaded {len(calibration_texts)} calibration samples")

    # 2. 載入 tokenizer 並 tokenize 校準資料
    print("\n[2/4] Loading tokenizer and tokenizing...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

    calibration_dataset = []
    for text in calibration_texts:
        tokenized = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048)
        calibration_dataset.append(tokenized)
    print(f"  Tokenized {len(calibration_dataset)} samples")

    # 3. 載入模型並量化
    print("\n[3/4] Loading model and quantizing (this may take 30-60 minutes)...")
    quantize_config = QuantizeConfig(
        bits=BITS,
        group_size=GROUP_SIZE,
    )

    start_time = time.time()
    model = GPTQModel.load(
        MODEL_PATH,
        quantize_config=quantize_config,
    )

    model.quantize(calibration_dataset)
    elapsed = time.time() - start_time
    print(f"  Quantization completed in {elapsed:.0f} seconds ({elapsed/60:.1f} minutes)")

    # 4. 儲存
    print(f"\n[4/4] Saving quantized model to {OUTPUT_PATH}...")
    model.save(OUTPUT_PATH)
    tokenizer.save_pretrained(OUTPUT_PATH)

    # 驗證輸出
    output_files = list(Path(OUTPUT_PATH).iterdir())
    total_size = sum(f.stat().st_size for f in output_files if f.is_file())
    print(f"\n  Output files: {len(output_files)}")
    print(f"  Total size: {total_size / 1024**3:.2f} GB")
    for f in sorted(output_files):
        if f.is_file():
            print(f"    {f.name}: {f.stat().st_size / 1024**2:.1f} MB")

    print("\nDone!")


if __name__ == "__main__":
    main()
