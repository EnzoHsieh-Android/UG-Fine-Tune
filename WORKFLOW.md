# 模型訓練與評估流程

## 目前模型

- **基座模型**：Qwen3-8B-4bit
- **目前版本**：Qwen3-8B-UG-order-v10-8bit（Round 30, iter 800, 96% eval — 48/50）
- **訓練資料**：1305 train + 313 valid = 1618 樣本

## 完整流程

```
訓練 → 評估各 checkpoint → 選擇最佳 → Fuse → 量化 8-bit → 部署 → 測試
```

## 一鍵訓練 + 評估

```bash
cd /Users/xiechengru/ug-finetune
./train_and_eval.sh

# 從 checkpoint 恢復：
./train_and_eval.sh --resume adapters-8b/0000400_adapters.safetensors
```

腳本會依序執行訓練 → checkpoint 評估。完成後依下方 Step 3~6 操作。

---

## Step 1: 訓練模型

```bash
cd /Users/xiechengru/ug-finetune

# 啟動訓練（使用 YAML 配置檔）
PYTHONUNBUFFERED=1 .venv/bin/python3 -m mlx_lm.lora \
    -c lora-config-8b.yaml 2>&1 | tee /tmp/training.log
```

**注意**：mlx-lm 0.30.5 不支援 `--lora-rank` 等 CLI 參數，必須用 `-c config.yaml`。
配置檔 `lora-config-8b.yaml` 內容：
```yaml
model: "model/Qwen3-8B-4bit"
num_layers: 24
lora_parameters:
  rank: 16
  dropout: 0.0
  scale: 20.0
learning_rate: 5.0e-6
batch_size: 1
grad_accumulation_steps: 4   # effective batch size = 4
iters: 1400
optimizer: "adamw"
mask_prompt: true
max_seq_length: 2048
grad_checkpoint: true
save_every: 100
adapter_path: "adapters-8b"
```

訓練過程會在 `adapters-8b/` 產生多個 checkpoint：
- `0000100_adapters.safetensors` (iter 100)
- `0000200_adapters.safetensors` (iter 200)
- ...
- `adapters.safetensors` (最終)

---

## Step 2: 評估各 Checkpoint

**不需要啟動 server**，直接用 MLX-LM 測試：

```bash
cd /Users/xiechengru/ug-finetune
.venv/bin/python3 eval_checkpoints_direct.py
```

腳本會：
1. 載入 base model + 各個 LoRA adapter
2. 跑 50 個測試案例（標準 + null 策略 + 甜度 + 推薦 + 閒聊 + 泛化 + 跨分類）
3. 模擬後端 fillDefaults（分類推斷）後再判定結果
4. 輸出每個 checkpoint 的通過率
5. 找出最佳 checkpoint

輸出範例：
```
評估結果總結
==================================================
   0000100: 30/37 (81%)
   0000200: 33/37 (89%)
   0000300: 35/37 (94%)  ← 最佳
   0000400: 34/37 (91%)
   0000500: 33/37 (89%)
     final: 32/37 (86%)

🏆 最佳 checkpoint: 0000300 (35 通過)
```

---

## Step 3: 選擇最佳 Checkpoint

```bash
# 複製最佳 checkpoint 作為最終 adapter
cp adapters-8b/0000300_adapters.safetensors adapters-8b/adapters.safetensors
```

---

## Step 4: Fuse 模型

```bash
cd /Users/xiechengru/ug-finetune

.venv/bin/python3 -m mlx_lm.fuse \
    --model model/Qwen3-8B-4bit \
    --adapter-path adapters-8b \
    --save-path model/Qwen3-8B-UG-order-vX \
    --dequantize
```

---

## Step 5: 量化為 8-bit 推論用

```bash
cd /Users/xiechengru/ug-finetune

.venv/bin/python3 -m mlx_lm.convert \
    --hf-path model/Qwen3-8B-UG-order-vX \
    --mlx-path model/Qwen3-8B-UG-order-vX-8bit \
    --quantize --q-bits 8
```

---

## Step 6: 更新 Server 並部署

```bash
# 1. 更新 llm_server_mlx.py 的 MODEL_PATH（指向 8-bit 版本）
#    MODEL_PATH = "/Users/xiechengru/ug-finetune/model/Qwen3-8B-UG-order-vX-8bit"

# 2. 重啟 LLM server
pkill -f llm_server_mlx.py
.venv/bin/python3 model/llm_server_mlx.py &

# 3. 重建並重啟後端
cd /Users/xiechengru/ug-backend
go build -o ug-backend . && ./ug-backend &
```

---

## Step 7: 最終驗證

```bash
cd /Users/xiechengru/ug-backend
./test_diversity_v2.sh    # 標準測試 (37 cases)
./test_generalization.sh  # 泛化測試 (45 cases)
```

---

## 重要提醒

- **Loss 最低 ≠ 表現最好**，一定要用實際測試評估
- Checkpoint 通常在 iter 700-900 之間最佳（8B 模型 + 1300 樣本）
- 如果所有 checkpoint 表現都差，問題可能在訓練資料
- 每輪新增資料 ≤ 20%，包含 anchor 樣本防止回歸

## 架構決策

- **模型輸出 null**，預設值由後端 `fillDefaults()` 處理
- **Intent 由後端推導**：orders 非空→order、recommendations 非空→recommend、兩者皆空→other
- **推薦限 1 項**：system prompt 指示「僅推薦 1 項」
- **甜度系統**：模型照錄顧客原話，後端映射（正常糖→全糖、半糖→五分糖、微糖→三分糖）
- **分類推斷**：`inferCategoryFromText()` 從 user text 推斷多分類品項的 category
- **ColdOnly 防護**：fruit_tea 品項 ice="熱飲" 自動修正為「正常冰」
