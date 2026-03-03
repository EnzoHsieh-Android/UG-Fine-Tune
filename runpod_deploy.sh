#!/bin/bash
# RunPod 一鍵部署腳本：建 pod → 上傳資料 → 訓練 → 下載結果 → 刪 pod
#
# 前置作業：
#   1. export RUNPOD_API_KEY=rpa_xxxxx
#   2. 在 RunPod Web UI 設定 SSH public key
#   3. brew install jq  (JSON 解析)
#
# 用法：
#   ./runpod_deploy.sh                          # 完整流程
#   ./runpod_deploy.sh --max-steps 800          # 自訂步數
#   ./runpod_deploy.sh --skip-delete            # 訓練完不刪 pod（除錯用）
#   ./runpod_deploy.sh --eval-only              # 只跑評估
#   ./runpod_deploy.sh --pod-id xxx             # 連接已存在的 pod

set -euo pipefail

# ==================== 配置 ====================

RUNPOD_API_KEY="${RUNPOD_API_KEY:?請設定 RUNPOD_API_KEY: export RUNPOD_API_KEY=rpa_xxxxx}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GPU_TYPE="NVIDIA A40"
IMAGE="runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"
TEMPLATE_ID="runpod-torch-v240"
POD_NAME="ug-finetune-$(date +%m%d%H%M)"
VOLUME_GB=50
DISK_GB=50
MAX_STEPS=1000
SAVE_STEPS=100
SKIP_DELETE=false
EVAL_ONLY=false
EXISTING_POD_ID=""

# 解析參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-steps)   MAX_STEPS="$2"; shift 2 ;;
        --save-steps)  SAVE_STEPS="$2"; shift 2 ;;
        --skip-delete) SKIP_DELETE=true; shift ;;
        --eval-only)   EVAL_ONLY=true; shift ;;
        --pod-id)      EXISTING_POD_ID="$2"; shift 2 ;;
        --gpu)         GPU_TYPE="$2"; shift 2 ;;
        *)             echo "未知參數: $1"; exit 1 ;;
    esac
done

# 檢查依賴
if ! command -v jq &> /dev/null; then
    echo "錯誤: 需要 jq (brew install jq)"
    exit 1
fi

# 驗證數值參數
if ! [[ "$MAX_STEPS" =~ ^[0-9]+$ ]]; then
    echo "錯誤: --max-steps 必須為正整數"; exit 1
fi
if ! [[ "$SAVE_STEPS" =~ ^[0-9]+$ ]]; then
    echo "錯誤: --save-steps 必須為正整數"; exit 1
fi

# INTENTIONAL: 使用 StrictHostKeyChecking=no — RunPod pod 為臨時性機器，每次 IP 不同
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=10"

# ==================== Helper Functions ====================

gql() {
    local query="$1"
    local payload
    payload=$(jq -n --arg q "$query" '{"query": $q}')
    curl -s "https://api.runpod.io/graphql?api_key=${RUNPOD_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$payload"
}

cleanup() {
    local exit_code=$?
    if [ -n "${POD_ID:-}" ] && [ "$SKIP_DELETE" = false ] && [ "$exit_code" -ne 0 ]; then
        echo ""
        echo "⚠ 腳本異常結束 (exit=$exit_code)，自動刪除 pod..."
        gql "mutation { podTerminate(input: {podId: \"$POD_ID\"}) }" > /dev/null 2>&1 \
            && echo "Pod $POD_ID 已自動刪除" \
            || echo "自動刪除失敗！請手動刪除 Pod $POD_ID (費用持續計算)"
    fi
}
trap cleanup EXIT

get_ssh_info() {
    local pod_id="$1"
    local result
    result=$(gql "query { pod(input: {podId: \"$pod_id\"}) { id desiredStatus runtime { ports { ip isIpPublic privatePort publicPort type } } } }") || true

    local status
    status=$(echo "$result" | jq -r '.data.pod.desiredStatus // empty' 2>/dev/null) || true
    if [ -z "$status" ]; then
        echo "ERROR||"
        return 0
    fi

    local ssh_ip ssh_port
    ssh_ip=$(echo "$result" | jq -r '.data.pod.runtime.ports[]? | select(.privatePort==22) | .ip // empty' 2>/dev/null) || true
    ssh_port=$(echo "$result" | jq -r '.data.pod.runtime.ports[]? | select(.privatePort==22) | .publicPort // empty' 2>/dev/null) || true

    echo "$status|$ssh_ip|$ssh_port"
}

wait_for_pod() {
    local pod_id="$1"
    echo "等待 pod 就緒 ($pod_id)..."

    local attempts=0
    local max_attempts=60  # 10 分鐘超時

    while [ $attempts -lt $max_attempts ]; do
        local info
        info=$(get_ssh_info "$pod_id")
        local status ssh_ip ssh_port
        status=$(echo "$info" | cut -d'|' -f1)
        ssh_ip=$(echo "$info" | cut -d'|' -f2)
        ssh_port=$(echo "$info" | cut -d'|' -f3)

        if [ "$status" = "RUNNING" ] && [ -n "$ssh_ip" ] && [ "$ssh_ip" != "null" ] && [ -n "$ssh_port" ] && [ "$ssh_port" != "null" ]; then
            echo "  Pod 就緒: ssh -p $ssh_port root@$ssh_ip"
            SSH_IP="$ssh_ip"
            SSH_PORT="$ssh_port"
            return 0
        fi

        attempts=$((attempts + 1))
        echo "  [$attempts] status=$status, 等待 10 秒..."
        sleep 10
    done

    echo "錯誤: Pod 啟動超時 (10 分鐘)"
    return 1
}

wait_for_ssh() {
    echo "等待 SSH 服務就緒..."
    local attempts=0
    while [ $attempts -lt 12 ]; do
        if ssh $SSH_OPTS -p "$SSH_PORT" "root@$SSH_IP" "echo ok" &>/dev/null; then
            echo "  SSH 連線成功"
            return 0
        fi
        attempts=$((attempts + 1))
        echo "  [$attempts] SSH 未就緒，等待 10 秒..."
        sleep 10
    done
    echo "錯誤: SSH 連線超時"
    return 1
}

# ==================== Step 1: 建立 / 連接 Pod ====================

echo "================================================"
echo "RunPod 雲端 LoRA 訓練部署"
echo "================================================"
echo "  GPU: $GPU_TYPE"
echo "  Max steps: $MAX_STEPS"
echo "  Save every: $SAVE_STEPS steps"
echo "  Eval only: $EVAL_ONLY"
echo ""

if [ -n "$EXISTING_POD_ID" ]; then
    POD_ID="$EXISTING_POD_ID"
    echo "=== 連接已存在的 Pod: $POD_ID ==="
else
    echo "=== Step 1: 建立 RunPod ($GPU_TYPE) ==="
    CREATE_RESULT=$(gql "mutation { podFindAndDeployOnDemand(input: { name: \"$POD_NAME\", templateId: \"$TEMPLATE_ID\", gpuTypeId: \"$GPU_TYPE\", gpuCount: 1, volumeInGb: $VOLUME_GB, containerDiskInGb: $DISK_GB, startSsh: true, ports: \"22/tcp\" }) { id } }")

    POD_ID=$(echo "$CREATE_RESULT" | jq -r '.data.podFindAndDeployOnDemand.id // empty')

    if [ -z "$POD_ID" ]; then
        echo "錯誤: Pod 建立失敗"
        echo "API 回應: $CREATE_RESULT"
        echo ""
        echo "常見原因："
        echo "  - GPU 類型無庫存 → 換 --gpu 'NVIDIA RTX A5000'"
        echo "  - API key 無效 → 檢查 RUNPOD_API_KEY"
        echo "  - 餘額不足 → 檢查 RunPod 帳戶"
        exit 1
    fi

    echo "  Pod ID: $POD_ID"
    echo "  費用: ~\$0.35/hr (A40)"
fi

# ==================== Step 2: 等待 Pod 就緒 ====================

echo ""
echo "=== Step 2: 等待 Pod 就緒 ==="
wait_for_pod "$POD_ID"
wait_for_ssh

# ==================== Step 3: 上傳資料 ====================

echo ""
echo "=== Step 3: 上傳資料 ==="

# 建立遠端目錄
ssh $SSH_OPTS -p "$SSH_PORT" "root@$SSH_IP" "mkdir -p /workspace/data"

# 上傳檔案
echo "  上傳 cloud_train_runpod.py..."
scp $SSH_OPTS -P "$SSH_PORT" \
    "$SCRIPT_DIR/cloud_train_runpod.py" \
    "root@$SSH_IP:/workspace/"

echo "  上傳 train.jsonl + valid.jsonl..."
scp $SSH_OPTS -P "$SSH_PORT" \
    "$SCRIPT_DIR/data/train.jsonl" \
    "$SCRIPT_DIR/data/valid.jsonl" \
    "root@$SSH_IP:/workspace/data/"

TRAIN_COUNT=$(wc -l < "$SCRIPT_DIR/data/train.jsonl" | tr -d ' ')
VALID_COUNT=$(wc -l < "$SCRIPT_DIR/data/valid.jsonl" | tr -d ' ')
echo "  完成 (train: $TRAIN_COUNT, valid: $VALID_COUNT)"

# ==================== Step 4: 執行訓練 ====================

echo ""
echo "=== Step 4: 執行訓練 ==="
echo "  開始時間: $(date)"

TRAIN_ARGS="--max-steps $MAX_STEPS --save-steps $SAVE_STEPS"
if [ "$EVAL_ONLY" = true ]; then
    TRAIN_ARGS="--eval-only"
fi

# 使用 unbuffered output 確保即時顯示
ssh $SSH_OPTS -p "$SSH_PORT" "root@$SSH_IP" \
    "cd /workspace && PYTHONUNBUFFERED=1 python3 cloud_train_runpod.py $TRAIN_ARGS" \
    2>&1 | tee "$SCRIPT_DIR/runpod_training.log"

echo "  完成時間: $(date)"

# ==================== Step 5: 下載結果 ====================

echo ""
echo "=== Step 5: 下載結果 ==="

mkdir -p "$SCRIPT_DIR/adapters-runpod"

# 下載 eval 結果
echo "  下載 eval_results.json..."
scp $SSH_OPTS -P "$SSH_PORT" \
    "root@$SSH_IP:/workspace/adapters-runpod/eval_results.json" \
    "$SCRIPT_DIR/adapters-runpod/" 2>/dev/null || echo "  (eval_results.json 未找到)"

# 下載最佳 adapter
echo "  下載 best/ adapter..."
scp -r $SSH_OPTS -P "$SSH_PORT" \
    "root@$SSH_IP:/workspace/adapters-runpod/best/" \
    "$SCRIPT_DIR/adapters-runpod/best/" 2>/dev/null || echo "  (best/ 未找到)"

echo "  下載完成"

# ==================== Step 6: 刪除 Pod ====================

if [ "$SKIP_DELETE" = true ]; then
    echo ""
    echo "=== 跳過刪除 Pod (--skip-delete) ==="
    echo "  Pod ID: $POD_ID"
    echo "  SSH: ssh -p $SSH_PORT root@$SSH_IP"
    echo "  ⚠ 費用持續計算！用完請手動刪除"
else
    echo ""
    echo "=== Step 6: 刪除 Pod ==="
    gql "mutation { podTerminate(input: {podId: \"$POD_ID\"}) }" > /dev/null
    echo "  Pod $POD_ID 已刪除"
fi

# ==================== 完成 ====================

echo ""
echo "================================================"
echo "完成！"
echo "================================================"

if [ -f "$SCRIPT_DIR/adapters-runpod/eval_results.json" ]; then
    echo ""
    echo "評估結果："
    cat "$SCRIPT_DIR/adapters-runpod/eval_results.json" | jq '.best, .best_score'
fi

echo ""
echo "後續步驟："
echo "  1. PEFT merge（合併 adapter 到基座模型）"
echo "     cd $SCRIPT_DIR"
echo "     source .venv/bin/activate"
echo "     python3 -c \""
echo "       from peft import PeftModel"
echo "       from transformers import AutoModelForCausalLM, AutoTokenizer"
echo "       base = AutoModelForCausalLM.from_pretrained('Qwen/Qwen3-8B', torch_dtype='auto')"
echo "       model = PeftModel.from_pretrained(base, 'adapters-runpod/best')"
echo "       merged = model.merge_and_unload()"
echo "       merged.save_pretrained('model/Qwen3-8B-UG-order-v11')"
echo "       AutoTokenizer.from_pretrained('Qwen/Qwen3-8B').save_pretrained('model/Qwen3-8B-UG-order-v11')"
echo "     \""
echo ""
echo "  2. 修復 config.json（補 rope_theta + max_position_embeddings）"
echo ""
echo "  3. MLX 量化"
echo "     .venv/bin/python3 -m mlx_lm.convert \\"
echo "       --hf-path model/Qwen3-8B-UG-order-v11 \\"
echo "       --mlx-path model/Qwen3-8B-UG-order-v11-8bit \\"
echo "       --quantize --q-bits 8"
echo ""
echo "  4. 本地測試"
echo "     更新 llm_server_mlx.py MODEL_PATH → 重啟 → ./test_diversity_v2.sh + ./test_generalization.sh"
echo ""
echo "訓練日誌: $SCRIPT_DIR/runpod_training.log"
