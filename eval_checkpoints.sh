#!/bin/bash
# 評估不同 checkpoint 的表現，找出最佳 iter

set -e

MODEL_BASE="/Users/xiechengru/ug-finetune/model/Qwen3-8B-4bit"
ADAPTER_DIR="/Users/xiechengru/ug-finetune/adapters-8b"
EVAL_MODEL_DIR="/Users/xiechengru/ug-finetune/model/Qwen3-8B-eval-temp"
VENV="/Users/xiechengru/ug-finetune/.venv/bin"
BACKEND_DIR="/Users/xiechengru/ug-backend"
RESULTS_FILE="/Users/xiechengru/ug-finetune/checkpoint_results.txt"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================" | tee "$RESULTS_FILE"
echo "  Checkpoint 評估測試" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# Find all checkpoint files
CHECKPOINTS=$(ls -1 "$ADAPTER_DIR"/*_adapters.safetensors 2>/dev/null | sort -t'_' -k1 -n || true)

if [ -z "$CHECKPOINTS" ]; then
    echo "找不到 checkpoint 檔案，請確認訓練已產生 checkpoint"
    exit 1
fi

echo "找到以下 checkpoints:" | tee -a "$RESULTS_FILE"
for ckpt in $CHECKPOINTS; do
    basename "$ckpt" | tee -a "$RESULTS_FILE"
done
echo "" | tee -a "$RESULTS_FILE"

# Also test the final adapters.safetensors
if [ -f "$ADAPTER_DIR/adapters.safetensors" ]; then
    CHECKPOINTS="$CHECKPOINTS $ADAPTER_DIR/adapters.safetensors"
fi

# Function to test a checkpoint
test_checkpoint() {
    local adapter_file="$1"
    local name=$(basename "$adapter_file" .safetensors)

    echo -e "${YELLOW}測試 checkpoint: $name${NC}"

    # Create temp directory for this evaluation
    rm -rf "$EVAL_MODEL_DIR"
    mkdir -p "$EVAL_MODEL_DIR"

    # Copy adapter file as adapters.safetensors for fuse
    cp "$adapter_file" "$ADAPTER_DIR/adapters.safetensors.bak" 2>/dev/null || true
    cp "$adapter_file" "$ADAPTER_DIR/adapters.safetensors"

    # Fuse model
    echo "  Fusing model..."
    "$VENV/python3" -m mlx_lm.fuse \
        --model "$MODEL_BASE" \
        --adapter-path "$ADAPTER_DIR" \
        --save-path "$EVAL_MODEL_DIR" \
        --de-quantize 2>/dev/null

    # Update server model path and restart
    echo "  Restarting LLM server..."
    pkill -f "llm_server_mlx.py" 2>/dev/null || true
    sleep 2

    # Start server with eval model
    PYTHONUNBUFFERED=1 "$VENV/python3" /Users/xiechengru/ug-finetune/model/llm_server_mlx.py \
        --model "$EVAL_MODEL_DIR" &
    SERVER_PID=$!

    # Wait for server to start
    echo "  Waiting for server..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Run tests
    echo "  Running tests..."
    cd "$BACKEND_DIR"

    # Count pass/fail
    RESULT=$(./test_diversity_v2.sh 2>&1 | tail -10)
    PASS=$(echo "$RESULT" | grep -oP '通過: \K\d+' || echo "0")
    FAIL=$(echo "$RESULT" | grep -oP '失敗: \K\d+' || echo "0")
    TOTAL=$((PASS + FAIL))

    # Stop server
    kill $SERVER_PID 2>/dev/null || true

    echo -e "${GREEN}  結果: $PASS/$TOTAL 通過${NC}"
    echo "$name: $PASS/$TOTAL" >> "$RESULTS_FILE"

    # Return pass count for comparison
    echo "$PASS"
}

# Test each checkpoint
BEST_CKPT=""
BEST_SCORE=0

for ckpt in $CHECKPOINTS; do
    SCORE=$(test_checkpoint "$ckpt")

    if [ "$SCORE" -gt "$BEST_SCORE" ]; then
        BEST_SCORE=$SCORE
        BEST_CKPT=$ckpt
    fi

    echo ""
done

echo "========================================" | tee -a "$RESULTS_FILE"
echo "  評估結果" | tee -a "$RESULTS_FILE"
echo "========================================" | tee -a "$RESULTS_FILE"
cat "$RESULTS_FILE"
echo ""
echo -e "${GREEN}最佳 checkpoint: $(basename $BEST_CKPT) ($BEST_SCORE 通過)${NC}"
echo ""
echo "最佳 checkpoint: $(basename $BEST_CKPT) ($BEST_SCORE 通過)" >> "$RESULTS_FILE"

# Cleanup
rm -rf "$EVAL_MODEL_DIR"

echo ""
echo "若要使用最佳 checkpoint 進行最終融合，執行："
echo "  cp $BEST_CKPT $ADAPTER_DIR/adapters.safetensors"
echo "  然後執行 fuse 命令"
