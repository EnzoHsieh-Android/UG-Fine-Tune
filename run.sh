#!/bin/bash
# ============================================================
# UG 點單助手 - Qwen3-4B 微調訓練腳本
# 用途：訓練 LoRA、測試、互動生成、合併模型
# 請先執行 setup.sh 完成環境設定
# ============================================================

set -e

# 取得腳本所在目錄
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 啟動虛擬環境
source .venv/bin/activate

# === 步驟一：訓練 ===
# 使用 LoRA 進行微調，設定檔為 lora-config.yaml
# 訓練過程中每 50 步會在驗證集上評估，每 100 步儲存一次 adapter
# 預計在 MacBook M 系列晶片上需要約 30-60 分鐘
mlx_lm.lora \
  --model model/Qwen3-4B-4bit \
  --data data \
  --train \
  --config lora-config.yaml

# === 步驟二：測試（驗證集） ===
# 訓練完成後，取消下方註解來在驗證集上評估損失值
# mlx_lm.lora \
#   --model model/Qwen3-4B-4bit \
#   --adapter-path adapters \
#   --data data \
#   --test

# === 步驟三：互動測試 ===
# 用單一提示詞測試模型的生成效果
# 可修改 --prompt 中的顧客訊息來測試不同情境
# mlx_lm.generate \
#   --model model/Qwen3-4B-4bit \
#   --adapter-path adapters \
#   --max-tokens 512 \
#   --prompt '<|im_start|>system
# 你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。
#
# 菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。
#
# 純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。
# 加料：紅烏龍茶凍(+15)、燕麥粒(+15)。
# 甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。
# 未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。
# 若品項不在菜單上，回傳 not_on_menu 欄位。
#
# 輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"unit_price":0,"note":""}],"total":0}<|im_end|>
# <|im_start|>user
# 一杯大杯桂花輕烏龍鮮奶半糖少冰<|im_end|>
# <|im_start|>assistant
# '

# === 步驟四：合併模型 ===
# 將 LoRA adapter 合併回基礎模型，產生獨立的微調模型
# 合併後的模型可直接用 mlx_lm.generate 載入，不需再指定 adapter
# mlx_lm.fuse \
#   --model model/Qwen3-4B-4bit \
#   --adapter-path adapters \
#   --save-path model/Qwen3-4B-UG-order
