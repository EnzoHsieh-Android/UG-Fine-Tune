#!/bin/bash
cd /Users/xiechengru/ug-finetune
export PYTHONUNBUFFERED=1
.venv/bin/python3 -m mlx_lm.lora \
    --model model/Qwen3-8B-4bit \
    --data data \
    --train \
    --num-layers 24 \
    --learning-rate 5e-6 \
    --batch-size 1 \
    --iters 1000 \
    --val-batches 5 \
    --steps-per-report 10 \
    --steps-per-eval 50 \
    --save-every 100 \
    --adapter-path adapters-8b \
    --grad-checkpoint
