#!/bin/bash
# Monitor training output and send Telegram notifications for progress + completion
BOT_TOKEN="7635280352:AAGJhdamXlN9aCeqSYhXDP5cBX04xfB3tiU"
CHAT_ID="7820341839"
OUTPUT_FILE="/private/tmp/claude-501/-Users-xiechengru/tasks/b139ea9.output"

send_msg() {
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
        -d chat_id="${CHAT_ID}" \
        -d parse_mode="Markdown" \
        -d text="$1" > /dev/null
}

extract_val_iter() {
    echo "$1" | sed 's/.*Iter \([0-9]*\):.*/\1/'
}
extract_val_loss() {
    echo "$1" | sed 's/.*Val loss \([0-9.]*\).*/\1/'
}
extract_train_loss() {
    echo "$1" | sed 's/.*Train loss \([0-9.]*\).*/\1/'
}
extract_peak_mem() {
    grep "Peak mem" "$OUTPUT_FILE" | tail -1 | sed 's/.*Peak mem \([0-9.]* GB\).*/\1/'
}

LAST_REPORTED_ITER=0

echo "Monitoring training output: ${OUTPUT_FILE}"

while true; do
    if [ ! -f "$OUTPUT_FILE" ]; then
        sleep 30
        continue
    fi

    # Check for val loss lines (every 50 iters)
    LATEST_VAL=$(grep "Val loss" "$OUTPUT_FILE" | tail -1)
    if [ -n "$LATEST_VAL" ]; then
        LATEST_VAL_ITER=$(extract_val_iter "$LATEST_VAL")

        if [ -n "$LATEST_VAL_ITER" ] && [ "$LATEST_VAL_ITER" -gt "$LAST_REPORTED_ITER" ] 2>/dev/null; then
            LAST_REPORTED_ITER=$LATEST_VAL_ITER

            TRAIN_LINE=$(grep "Iter ${LATEST_VAL_ITER}:" "$OUTPUT_FILE" | grep "Train loss" | tail -1)
            TRAIN_LOSS=$(extract_train_loss "$TRAIN_LINE")
            VAL_LOSS=$(extract_val_loss "$LATEST_VAL")
            BEST_VAL=$(grep "Val loss" "$OUTPUT_FILE" | while read -r line; do extract_val_loss "$line"; done | sort -n | head -1)
            PCT=$((LATEST_VAL_ITER * 100 / 900))
            BAR=""
            FILLED=$((PCT / 5))
            EMPTY=$((20 - FILLED))
            for i in $(seq 1 $FILLED); do BAR="${BAR}▓"; done
            for i in $(seq 1 $EMPTY); do BAR="${BAR}░"; done

            if [ "$LATEST_VAL_ITER" -eq 900 ]; then
                PEAK_MEM=$(extract_peak_mem)
                MSG="✅ *UG Fine-tuning 訓練完成！*

${BAR} 100%

📊 Iter ${LATEST_VAL_ITER}/900
• Train Loss: \`${TRAIN_LOSS}\`
• Val Loss: \`${VAL_LOSS}\`
• 最低 Val Loss: \`${BEST_VAL}\`
• Peak Memory: \`${PEAK_MEM}\`

⏭ 下一步：執行 \`eval_checkpoints_direct.py\`"
                send_msg "$MSG"
                echo "Final notification sent!"
                exit 0
            else
                MSG="🔄 *UG Fine-tuning 進度*

${BAR} ${PCT}%

📊 Iter ${LATEST_VAL_ITER}/900
• Train Loss: \`${TRAIN_LOSS}\`
• Val Loss: \`${VAL_LOSS}\`
• 目前最低 Val: \`${BEST_VAL}\`"
                send_msg "$MSG"
                echo "Progress sent: Iter ${LATEST_VAL_ITER}"
            fi
        fi
    fi

    # Check for crash (only before training starts)
    if grep -qi "traceback" "$OUTPUT_FILE" 2>/dev/null; then
        if ! grep -q "Iter 10:" "$OUTPUT_FILE" 2>/dev/null; then
            ERROR=$(tail -10 "$OUTPUT_FILE")
            send_msg "❌ *訓練失敗* ${ERROR}"
            exit 1
        fi
    fi

    sleep 30
done
