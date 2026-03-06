#!/bin/bash
# vLLM FP8 + LoRA 啟動腳本 — Qwen3.5-9B on GCP L4
# 部署到 /opt/scripts/start_vllm_qwen35_fp8.sh
#
# 需求：vLLM >= 0.17.0 或 nightly（DeltaNet Triton kernels）
# 安裝：pip install vllm --extra-index-url https://wheels.vllm.ai/nightly

set -euo pipefail

MODEL_PATH="/opt/models/Qwen3.5-9B-Text"
ADAPTER_PATH="/opt/models/adapter-qwen35-r1"
LOG_FILE="/opt/scripts/vllm.log"

# 檢查模型目錄
if [ ! -d "$MODEL_PATH" ]; then
    echo "錯誤: 模型目錄不存在: $MODEL_PATH"
    echo "請先下載: gsutil -m cp -r gs://ug-llm-models/Qwen3.5-9B $MODEL_PATH"
    exit 1
fi

# 殺掉舊的 vLLM 進程
echo "清理舊進程..."
pkill -f "vllm serve" 2>/dev/null || true
sleep 2

# 確認 GPU 可用
if ! nvidia-smi &>/dev/null; then
    echo "錯誤: 找不到 GPU"
    exit 1
fi

echo "啟動 vLLM Qwen3.5-9B FP8 + LoRA..."
echo "  Model: $MODEL_PATH"
echo "  Adapter: $ADAPTER_PATH"
echo "  Log: $LOG_FILE"

nohup /opt/vllm-env/bin/python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --host 127.0.0.1 \
    --port 8080 \
    --dtype float16 \
    --quantization fp8 \
    --max-model-len 2048 \
    --enable-prefix-caching \
    --enable-lora \
    --lora-modules "ug=$ADAPTER_PATH" \
    --max-lora-rank 32 \
    --gpu-memory-utilization 0.90 \
    > "$LOG_FILE" 2>&1 &

echo "vLLM PID: $!"
echo "等待啟動（約 2-3 分鐘）..."
echo "查看日誌: tail -f $LOG_FILE"
