#!/usr/bin/env python3
"""PEFT merge: 將 LoRA adapter 合併回基座模型，輸出全精度 HF 格式。

用法:
  python3 peft_merge.py \
      --base Qwen/Qwen3-8B \
      --adapter adapters-runpod/best \
      --output model/Qwen3-8B-UG-order-v11

合併後自動修復 config.json（rope_theta, max_position_embeddings）。
"""

import argparse
import json
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="Qwen/Qwen3-8B", help="基座模型")
    parser.add_argument("--adapter", default="adapters-runpod/best", help="LoRA adapter 路徑")
    parser.add_argument("--output", required=True, help="合併後輸出路徑")
    args = parser.parse_args()

    print(f"=== PEFT Merge ===")
    print(f"  Base: {args.base}")
    print(f"  Adapter: {args.adapter}")
    print(f"  Output: {args.output}")

    # 修正 adapter_config.json 的 base_model_name_or_path
    # Unsloth 可能設成 unsloth/xxx，需要改回原始模型名
    adapter_config_path = os.path.join(args.adapter, "adapter_config.json")
    with open(adapter_config_path) as f:
        adapter_config = json.load(f)

    original_base = adapter_config.get("base_model_name_or_path", "")
    if original_base != args.base:
        print(f"  修正 base_model_name_or_path: {original_base} → {args.base}")
        adapter_config["base_model_name_or_path"] = args.base
        with open(adapter_config_path, "w") as f:
            json.dump(adapter_config, f, indent=2, ensure_ascii=False)

    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print("\n載入基座模型...")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base,
        torch_dtype="auto",
        device_map="cpu",
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base)

    print("載入 LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, args.adapter)

    print("合併權重...")
    merged = model.merge_and_unload()

    print(f"儲存到 {args.output}...")
    merged.save_pretrained(args.output)
    tokenizer.save_pretrained(args.output)

    # 修復 config.json
    config_path = os.path.join(args.output, "config.json")
    with open(config_path) as f:
        config = json.load(f)

    fixes = []
    if config.get("rope_theta") != 1000000:
        config["rope_theta"] = 1000000
        fixes.append("rope_theta=1000000")

    if config.get("max_position_embeddings") != 40960:
        config["max_position_embeddings"] = 40960
        fixes.append("max_position_embeddings=40960")

    if "rope_scaling" in config:
        del config["rope_scaling"]
        fixes.append("刪除 rope_scaling")

    if fixes:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"修復 config.json: {', '.join(fixes)}")
    else:
        print("config.json 無需修復")

    print("\n=== PEFT Merge 完成 ===")


if __name__ == "__main__":
    main()
