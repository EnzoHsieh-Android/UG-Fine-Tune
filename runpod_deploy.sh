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
VOLUME_GB=60
DISK_GB=100
MAX_STEPS=1000
SAVE_STEPS=100
SKIP_DELETE=false
EVAL_ONLY=false
EXISTING_POD_ID=""
MODEL_NAME=""
FP16_FLAG=""

# 解析參數
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-steps)   MAX_STEPS="$2"; shift 2 ;;
        --save-steps)  SAVE_STEPS="$2"; shift 2 ;;
        --skip-delete) SKIP_DELETE=true; shift ;;
        --eval-only)   EVAL_ONLY=true; shift ;;
        --pod-id)      EXISTING_POD_ID="$2"; shift 2 ;;
        --gpu)         GPU_TYPE="$2"; shift 2 ;;
        --model)       MODEL_NAME="$2"; shift 2 ;;
        --fp16)        FP16_FLAG="--fp16"; shift ;;
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
# ServerAliveInterval: 每 30 秒發 keepalive，避免閒置斷線
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=10 -o ServerAliveInterval=30 -o ServerAliveCountMax=120"

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
echo "  Model: ${MODEL_NAME:-Qwen/Qwen3.5-9B (default)}"
echo "  Precision: ${FP16_FLAG:+FP16 全精度}${FP16_FLAG:-8-bit QLoRA}"
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

TRAIN_ARGS="--train-only --max-steps $MAX_STEPS --save-steps $SAVE_STEPS"
[ -n "$MODEL_NAME" ] && TRAIN_ARGS="$TRAIN_ARGS --model $MODEL_NAME"
[ -n "$FP16_FLAG" ] && TRAIN_ARGS="$TRAIN_ARGS --fp16"
if [ "$EVAL_ONLY" = true ]; then
    TRAIN_ARGS="--eval-only"
    [ -n "$MODEL_NAME" ] && TRAIN_ARGS="$TRAIN_ARGS --model $MODEL_NAME"
    [ -n "$FP16_FLAG" ] && TRAIN_ARGS="$TRAIN_ARGS --fp16"
fi

# Foreground SSH + keepalive + 自動重連（SSH 斷線後 resume from checkpoint）
MAX_SSH_RETRIES=5
for SSH_RETRY in $(seq 1 $MAX_SSH_RETRIES); do
    echo "  [嘗試 $SSH_RETRY/$MAX_SSH_RETRIES]"
    set +e  # 暫時關閉 errexit，避免 SSH exit 255 直接終止腳本
    ssh $SSH_OPTS -p "$SSH_PORT" "root@$SSH_IP" \
        "cd /workspace && PYTHONUNBUFFERED=1 python3 cloud_train_runpod.py $TRAIN_ARGS" \
        2>&1 | tee -a "$SCRIPT_DIR/runpod_training.log"
    SSH_EXIT=${PIPESTATUS[0]}  # 取 ssh 的 exit code，非 tee 的
    set -e

    if [ $SSH_EXIT -eq 0 ]; then
        echo "  完成"
        break
    fi

    if [ $SSH_EXIT -eq 255 ] && [ $SSH_RETRY -lt $MAX_SSH_RETRIES ]; then
        echo ""
        echo "  ⚠ SSH 斷線 (exit 255)，等待 60 秒後重連..."
        echo "  （訓練腳本會自動從最新 checkpoint 恢復）"
        sleep 60
        # 確認 pod 還活著
        POD_STATUS=$(get_ssh_info "$POD_ID" | cut -d'|' -f1)
        if [ "$POD_STATUS" != "RUNNING" ]; then
            echo "  Pod 已停止 (status=$POD_STATUS)，無法重連"
            exit 1
        fi
        # 重新取得 SSH 資訊（port 可能變）
        wait_for_pod "$POD_ID"
        wait_for_ssh
        continue
    fi

    echo "  訓練失敗 (exit $SSH_EXIT)"
    exit $SSH_EXIT
done

echo "  完成時間: $(date)"

# ==================== Step 5: 下載 Checkpoint ====================

echo ""
echo "=== Step 5: 下載所有 checkpoint adapter ==="

mkdir -p "$SCRIPT_DIR/adapters-runpod"

if [ "$EVAL_ONLY" != true ]; then
    # 列出遠端 checkpoint 目錄
    CHECKPOINTS=$(ssh $SSH_OPTS -p "$SSH_PORT" "root@$SSH_IP" \
        "ls -d /workspace/adapters-runpod/checkpoint-* 2>/dev/null | sort -t- -k2 -n" 2>/dev/null) || true

    if [ -n "$CHECKPOINTS" ]; then
        CP_COUNT=$(echo "$CHECKPOINTS" | wc -l | tr -d ' ')
        echo "  找到 $CP_COUNT 個 checkpoint，開始下載..."
        for CP_PATH in $CHECKPOINTS; do
            CP_NAME=$(basename "$CP_PATH")
            echo "  下載 $CP_NAME..."
            mkdir -p "$SCRIPT_DIR/adapters-runpod/$CP_NAME"
            scp $SSH_OPTS -P "$SSH_PORT" \
                "root@$SSH_IP:$CP_PATH/adapter_model.safetensors" \
                "root@$SSH_IP:$CP_PATH/adapter_config.json" \
                "$SCRIPT_DIR/adapters-runpod/$CP_NAME/" 2>/dev/null || echo "    ($CP_NAME 下載失敗)"
        done
        echo "  所有 checkpoint 已下載到 $SCRIPT_DIR/adapters-runpod/"
    else
        echo "  (未找到 checkpoint)"
    fi
fi

# ==================== Step 6: 遠端評估 ====================

if [ "$EVAL_ONLY" != true ]; then
    echo ""
    echo "=== Step 6: 在 Pod 上執行評估 ==="

    set +e
    ssh $SSH_OPTS -p "$SSH_PORT" "root@$SSH_IP" \
        "cd /workspace && PYTHONUNBUFFERED=1 python3 cloud_train_runpod.py --eval-only${MODEL_NAME:+ --model $MODEL_NAME}${FP16_FLAG:+ $FP16_FLAG}" \
        2>&1 | tee -a "$SCRIPT_DIR/runpod_training.log"
    EVAL_EXIT=${PIPESTATUS[0]}
    set -e

    if [ $EVAL_EXIT -ne 0 ]; then
        echo "  ⚠ 評估失敗 (exit $EVAL_EXIT)，但 checkpoint 已下載到本地"
    fi
fi

# 下載 eval 結果和 best adapter
echo ""
echo "  下載評估結果..."
scp $SSH_OPTS -P "$SSH_PORT" \
    "root@$SSH_IP:/workspace/adapters-runpod/eval_results.json" \
    "$SCRIPT_DIR/adapters-runpod/" 2>/dev/null || echo "  (eval_results.json 未找到)"

scp -r $SSH_OPTS -P "$SSH_PORT" \
    "root@$SSH_IP:/workspace/adapters-runpod/best/" \
    "$SCRIPT_DIR/adapters-runpod/best/" 2>/dev/null || echo "  (best/ 未找到)"

echo "  下載完成"

# ==================== Step 7: 刪除 Pod ====================

if [ "$SKIP_DELETE" = true ]; then
    echo ""
    echo "=== 跳過刪除 Pod (--skip-delete) ==="
    echo "  Pod ID: $POD_ID"
    echo "  SSH: ssh -p $SSH_PORT root@$SSH_IP"
    echo "  ⚠ 費用持續計算！用完請手動刪除"
else
    echo ""
    echo "=== Step 7: 刪除 Pod ==="
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
echo "後續步驟（Qwen3.5-9B 不 merge，直接用 adapter）："
echo "  1. 上傳 adapter 到 GCP"
echo "     gsutil -m cp -r adapters-runpod/best/ gs://ug-llm-models/adapter-qwen35-rXX/"
echo ""
echo "  2. VM 上下載"
echo "     gsutil -m cp -r gs://ug-llm-models/adapter-qwen35-rXX/ /opt/models/"
echo ""
echo "  3. 啟動 vLLM FP8 + LoRA"
echo "     sudo bash /opt/scripts/start_vllm_qwen35_fp8.sh"
echo ""
echo "  4. 跑完整測試"
echo "     bash test_diversity_v2.sh && bash test_generalization.sh"
echo ""
echo "訓練日誌: $SCRIPT_DIR/runpod_training.log"
