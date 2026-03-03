#!/bin/bash
# Round 26 Training: 8-bit + mask-prompt + adamw
# Note: num-layers reduced from 24 to 16 to fix OOM on 32GB Mac
#       8-bit model + mask-prompt + adamw needs more memory than 4-bit
cd /Users/xiechengru/ug-finetune

PYTHONUNBUFFERED=1 .venv/bin/python3 -m mlx_lm lora \
    --model model/Qwen3-8B-8bit \
    --data data \
    --train \
    --num-layers 16 \
    --learning-rate 5e-6 \
    --batch-size 1 \
    --iters 800 \
    --val-batches 5 \
    --steps-per-report 10 \
    --steps-per-eval 50 \
    --save-every 100 \
    --adapter-path adapters-8b-r26 \
    --grad-checkpoint \
    --mask-prompt \
    --optimizer adamw 2>&1 | tee /tmp/training_r26.log
