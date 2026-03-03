#!/bin/bash
# Round 28+ 訓練 + 自動評估腳本
# 用法: ./train_and_eval.sh
# 可選: ./train_and_eval.sh --resume adapters-8b/0000400_adapters.safetensors

set -e

cd /Users/xiechengru/ug-finetune

# 載入 .env（LangSmith API key 等）
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

RESUME_FLAG=""
if [ "$1" = "--resume" ] && [ -n "$2" ]; then
    RESUME_FLAG="--resume-adapter-file $2"
    echo "=== 從 checkpoint 恢復: $2 ==="
fi

echo "=== Step 1: 訓練 ==="
echo "開始時間: $(date)"
.venv/bin/python3 -m mlx_lm.lora --config lora-config-8b.yaml $RESUME_FLAG
echo "訓練完成: $(date)"

echo ""
echo "=== Step 2: Checkpoint 評估 ==="
EVAL_OUTPUT=$(PYTHONUNBUFFERED=1 .venv/bin/python3 eval_checkpoints_direct.py 2>&1 | tee /dev/stderr)

# 從 eval 輸出解析最佳 checkpoint（格式：🏆 最佳 checkpoint: 0000500 (47/50 通過)）
BEST_CP=$(echo "$EVAL_OUTPUT" | grep -o '最佳 checkpoint: [0-9]*' | grep -o '[0-9]*')

echo ""
echo "=== Step 3: LangSmith 評估（最佳 checkpoint）==="
if [ -n "$LANGSMITH_API_KEY" ]; then
    if [ -n "$BEST_CP" ]; then
        # 複製最佳 checkpoint 為 active adapter
        BEST_ADAPTER="adapters-8b/$(printf '%07d' $BEST_CP)_adapters.safetensors"
        if [ -f "$BEST_ADAPTER" ]; then
            cp "$BEST_ADAPTER" adapters-8b/adapters.safetensors
            echo "已複製最佳 checkpoint: $BEST_ADAPTER → adapters-8b/adapters.safetensors"
        fi
        echo "評估最佳 checkpoint: cp${BEST_CP}"
        PYTHONUNBUFFERED=1 .venv/bin/python3 eval_langsmith.py \
            --base-model model/Qwen3-8B-4bit \
            --adapter adapters-8b \
            --version "vNEW-cp${BEST_CP}"
    else
        echo "無法解析最佳 checkpoint，跳過 LangSmith 評估"
    fi
else
    echo "未設定 LANGSMITH_API_KEY，跳過 LangSmith 評估"
fi

echo ""
echo "=== 完成 ==="
echo "請根據評估結果選擇最佳 checkpoint，然後執行："
echo ""
echo "  # 1. 選擇 checkpoint"
echo "  cp adapters-8b/0000XXX_adapters.safetensors adapters-8b/adapters.safetensors"
echo ""
echo "  # 2. Fuse 成 FP16"
echo "  .venv/bin/python3 -m mlx_lm.fuse --model model/Qwen3-8B-4bit --adapter-path adapters-8b --save-path model/Qwen3-8B-UG-order-vX --dequantize"
echo ""
echo "  # 3. 量化成 8-bit 推論用"
echo "  .venv/bin/python3 -m mlx_lm.convert --hf-path model/Qwen3-8B-UG-order-vX --mlx-path model/Qwen3-8B-UG-order-vX-8bit --quantize --q-bits 8"
echo ""
echo "  # 4. 更新 llm_server_mlx.py 的 MODEL_PATH 指向 8-bit 版本，重啟 server"
