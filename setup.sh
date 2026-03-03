#!/bin/bash
# ============================================================
# UG 點單助手 - 環境設定腳本
# 用途：建立 Python 虛擬環境、安裝依賴、下載模型
# ============================================================

set -e  # 遇到錯誤立即停止

# 取得腳本所在目錄，確保路徑正確
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  UG 點單助手 - 微調環境設定"
echo "=========================================="

# --- 步驟一：建立 Python 虛擬環境 ---
echo ""
echo "[1/3] 建立 Python 虛擬環境 (.venv)..."
if [ -d ".venv" ]; then
    echo "  虛擬環境已存在，跳過建立。"
else
    python3 -m venv .venv
    echo "  虛擬環境建立完成。"
fi

# 啟動虛擬環境
source .venv/bin/activate
echo "  已啟動虛擬環境：$(which python3)"

# --- 步驟二：安裝必要套件 ---
echo ""
echo "[2/3] 安裝 mlx-lm 與 huggingface-hub..."
pip install --upgrade pip
pip install mlx-lm huggingface-hub
echo "  套件安裝完成。"

# --- 步驟三：下載模型 ---
echo ""
echo "[3/3] 下載 Qwen3-4B-4bit 模型（約 2.5 GB）..."
echo "  模型來源：mlx-community/Qwen3-4B-4bit"
echo "  儲存位置：model/Qwen3-4B-4bit"

mkdir -p model

# 使用 huggingface-cli 下載模型到本地目錄
.venv/bin/hf download \
    mlx-community/Qwen3-4B-4bit \
    --local-dir model/Qwen3-4B-4bit

echo "  模型下載完成。"

# --- 完成 ---
echo ""
echo "=========================================="
echo "  環境設定完成！"
echo "  接下來請執行 ./run.sh 開始訓練"
echo "=========================================="
