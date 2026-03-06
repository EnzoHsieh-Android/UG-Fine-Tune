# UG Fine-Tune

語音點餐 LLM fine-tuning 專案，將基座模型微調為能解析中文口語點餐指令的 JSON 結構化輸出模型。

## 模型版本

| 版本 | 基座 | 訓練方式 | Eval | 資料量 |
|------|------|----------|------|--------|
| v11 (目前) | Qwen3-8B | 8-bit QLoRA, RunPod A40 | 60/60 (100%) | 1887 train + 442 valid |
| Qwen3.5-4B R1 | Qwen3.5-4B | 8-bit QLoRA, RunPod A40 | 60/60 (100%) | 同上 |
| Qwen3.5-9B R1 | Qwen3.5-9B | 8-bit QLoRA, RunPod A6000 | 待測 | 同上 |

## 專案結構

```
ug-finetune/
├── data/                        # 訓練資料 (JSONL)
├── model/                       # 基座模型 (gitignored)
├── adapters-*/                  # LoRA adapters (gitignored)
├── cloud_train_runpod.py        # RunPod 雲端訓練 + 評估腳本
├── runpod_deploy.sh             # 一鍵部署 RunPod (建 pod → 訓練 → 下載 → 刪 pod)
├── train_and_eval.sh            # 本地 MLX 訓練 + 評估 (Apple Silicon)
├── eval_checkpoints_direct.py   # 本地 checkpoint 評估 (60 cases)
├── eval_vllm_remote.py          # 遠端 vLLM/SGLang 評估
├── lora-config-8b.yaml          # 本地 MLX LoRA 設定 (Qwen3-8B)
├── lora-config-qwen35-4b.yaml   # RunPod LoRA 設定 (Qwen3.5-4B)
├── scripts/                     # GCP VM 啟動腳本
│   └── start_vllm_qwen35_fp8.sh
├── WORKFLOW.md                  # 訓練流程文件
└── add_*.py / fix_*.py          # 訓練資料增補/修正腳本
```

## 快速開始

### RunPod 雲端訓練（主力）

```bash
# 一鍵：建 pod → 上傳資料 → 訓練 → 評估 → 下載 → 刪 pod
./runpod_deploy.sh

# 指定模型和精度
./runpod_deploy.sh --model Qwen/Qwen3.5-4B --fp16

# 調整步數
./runpod_deploy.sh --max-steps 1200 --save-steps 100

# 使用已存在的 pod
./runpod_deploy.sh --pod-id <POD_ID> --skip-delete
```

需要設定環境變數：
```bash
export RUNPOD_API_KEY=your_key
```

### 本地訓練（Apple Silicon）

```bash
# 一鍵訓練 + 評估
./train_and_eval.sh

# 從 checkpoint 恢復
./train_and_eval.sh --resume adapters-8b/0000400_adapters.safetensors
```

需要 Python 虛擬環境：
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install mlx-lm
```

## 訓練超參數

| 參數 | RunPod (雲端) | MLX (本地) |
|------|--------------|-----------|
| Rank | 32 | 16 |
| Alpha | 64 | — (scale=20) |
| Dropout | 0.05 | 0.0 |
| Batch size | 4 (×2 grad accum = 8) | 1 (×4 grad accum = 4) |
| Learning rate | 1e-5 | 5e-6 |
| Scheduler | Cosine + 10% warmup | — |
| Optimizer | AdamW 8-bit | AdamW |
| Max steps | 1000 | 1400 |

## 部署架構

```
用戶 → Cloud Run (Go 後端)
         → vLLM/SGLang (GPU, merged 或 LoRA adapter)
         → DashScope API (STT)
```

### GCP VM 部署

```bash
# 上傳 adapter
gcloud compute scp adapter_model.safetensors ug-server:/opt/models/adapter-rXX/

# 啟動 vLLM
gcloud compute ssh ug-server --command="sudo bash /opt/scripts/start_vllm_fp16.sh"

# 跑測試
bash test_diversity_v2.sh && bash test_generalization.sh
```

## 關鍵設計決策

- **預設值由後端處理**：模型對未指定欄位輸出 `null`，後端 `fillDefaults()` 填入預設值
- **Intent 由模型輸出**：per-segment 意圖分類 (order/recommend/modify/other)
- **甜度照錄**：模型照錄顧客原話，後端負責映射（正常糖→全糖、半糖→五分糖等）
- **Loss 最低 ≠ 最好**：一律用實際測試 (60 cases) 選擇最佳 checkpoint
- **增量訓練**：每輪新增資料 ≤ 20%，包含 anchor 樣本防止回歸
