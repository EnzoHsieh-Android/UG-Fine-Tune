#!/bin/bash
# 持續監控訓練進度，每 5 分鐘輸出一次摘要
OUTPUT_FILE="/private/tmp/claude-501/-Users-xiechengru/tasks/b205e47.output"
TOTAL_ITERS=1400

while true; do
    if [ ! -f "$OUTPUT_FILE" ]; then
        echo "$(date '+%H:%M') | 等待輸出檔案..."
        sleep 60
        continue
    fi

    # 取最新的 iter 行
    LAST_ITER=$(grep -oP 'Iter \K[0-9]+' "$OUTPUT_FILE" | tail -1)
    LAST_VAL=$(grep 'Val loss' "$OUTPUT_FILE" | tail -1 | grep -oP 'Val loss \K[0-9.]+')
    LAST_TRAIN=$(grep 'Train loss' "$OUTPUT_FILE" | tail -1 | grep -oP 'Train loss \K[0-9.]+')
    LAST_SAVED=$(grep 'Saved adapter' "$OUTPUT_FILE" | tail -1 | grep -oP '000[0-9]+')

    if [ -z "$LAST_ITER" ]; then
        echo "$(date '+%H:%M') | 尚未開始訓練..."
        sleep 60
        continue
    fi

    PCT=$((LAST_ITER * 100 / TOTAL_ITERS))
    REMAINING=$((TOTAL_ITERS - LAST_ITER))
    # ~19 sec per iter
    ETA_MIN=$((REMAINING * 19 / 60))
    ETA_HR=$((ETA_MIN / 60))
    ETA_M=$((ETA_MIN % 60))

    echo "$(date '+%H:%M') | iter ${LAST_ITER}/${TOTAL_ITERS} (${PCT}%) | train=${LAST_TRAIN} val=${LAST_VAL} | saved=${LAST_SAVED} | ETA ~${ETA_HR}h${ETA_M}m"

    # 檢查是否已完成訓練
    if grep -q "Step 2" "$OUTPUT_FILE" 2>/dev/null; then
        echo "$(date '+%H:%M') | === 訓練完成，進入 checkpoint 評估 ==="
        # 持續顯示評估進度
        tail -f "$OUTPUT_FILE" &
        TAIL_PID=$!
        # 等到整個任務結束
        while [ -f "/proc/$TAIL_PID" ] 2>/dev/null; do
            if grep -q "所有測試完成\|eval.*完成\|測試結果" "$OUTPUT_FILE" 2>/dev/null; then
                kill $TAIL_PID 2>/dev/null
                break
            fi
            sleep 30
        done
        break
    fi

    # 檢查是否整個流程結束
    if grep -q "完成" "$OUTPUT_FILE" 2>/dev/null && [ "$LAST_ITER" -ge 1400 ]; then
        echo "$(date '+%H:%M') | === 全部完成 ==="
        break
    fi

    sleep 300  # 每 5 分鐘檢查一次
done
