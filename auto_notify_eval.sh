#!/bin/bash
# 自動監控評估完成並發送 Telegram 通知

LOG_FILE="/tmp/eval_r26.log"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTIFY_SCRIPT="$SCRIPT_DIR/notify_telegram.py"

echo "[$(date +%H:%M:%S)] 開始監控評估進度..."

# 等待評估完成（檢測到總結部分）
while true; do
    if grep -q "🏆 最佳 checkpoint" "$LOG_FILE" 2>/dev/null; then
        echo "[$(date +%H:%M:%S)] 評估完成！"
        break
    fi

    # 檢查進程是否還在運行
    if ! pgrep -f "eval_checkpoints_direct.py" > /dev/null 2>&1; then
        echo "[$(date +%H:%M:%S)] 評估進程已結束"
        break
    fi

    sleep 30
done

# 等待檔案完全寫入
sleep 5

# 提取結果總結
SUMMARY=$(grep -A 50 "評估結果總結" "$LOG_FILE" | head -60)
BEST=$(grep "🏆 最佳 checkpoint" "$LOG_FILE")

# 格式化中文通知
NOTIFICATION="
🎯 Round 26 訓練評估完成

$SUMMARY

$BEST

📊 完整日誌：$LOG_FILE
"

# 發送 Telegram 通知
if [ -f "$SCRIPT_DIR/.telegram_config" ]; then
    echo "[$(date +%H:%M:%S)] 發送 Telegram 通知..."
    python3 "$NOTIFY_SCRIPT" "$NOTIFICATION"
    echo "[$(date +%H:%M:%S)] 通知已發送！"
else
    echo "[$(date +%H:%M:%S)] 未設定 Telegram 配置"
    echo "$NOTIFICATION"
fi

echo "[$(date +%H:%M:%S)] 完成"
