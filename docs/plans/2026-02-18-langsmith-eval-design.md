# LangSmith 自動化評估 & A/B Testing 設計

## 目標

1. **自動化回歸監控**：每次訓練新版本後，自動跑標準化評估並上傳 LangSmith
2. **版本 A/B 對比**：新版本 vs 舊版本，在 Dashboard 上一眼看出退化
3. **全鏈路 trace**（第二階段）：ASR → Normalizer → LLM → Validate → FillDefaults → API Response

## 架構概覽

```
train_and_eval.sh（整合後流程）
  ├── 1. MLX LoRA 訓練                     ← 不動
  ├── 2. eval_checkpoints_direct.py         ← 不動，選出最佳 checkpoint
  └── 3.【新增】eval_langsmith.py           ← 只跑最佳 checkpoint
        ├── 載入 base model + best adapter
        ├── 跑 LangSmith Dataset（50+ 測試案例）
        ├── 5 個自定義 Evaluator 計算分數
        └── 上傳結果為 Experiment
```

- 現有 `eval_checkpoints_direct.py` 保留不動，負責快速挑選最佳 checkpoint
- LangSmith 評估在選完最佳 checkpoint 之後才跑，只評估最終候選人
- 沒有設定 `LANGSMITH_API_KEY` 時自動跳過，不影響原有流程

## Dataset 設計

### 資料來源

直接復用 `eval_checkpoints_direct.py` 裡的測試案例，透過 `sync_dataset.py` 同步。

### Dataset 結構（每筆）

| 欄位 | 說明 | 範例 |
|------|------|------|
| `input` | 用戶輸入文字 | "兩杯琥珀鐵觀音鮮奶茶去冰半糖" |
| `expected_intent` | 預期 intent | "order" |
| `expected_orders` | 預期訂單陣列 | `[{item:"琥珀鐵觀音", category:"fresh_milk_tea", ...}]` |
| `expected_recs` | 預期推薦（可選） | `[{item:"桂花輕烏龍"}]` |
| `category` | 測試分類標籤 | "跨分類" / "甜度" / "泛化" |
| `check_fields` | 要驗證的欄位清單 | `["item", "category", "sugar", "ice"]` |

### 同步機制

- `sync_dataset.py`：從 `eval_checkpoints_direct.py` 的測試案例自動轉換並上傳
- 每次新增測試案例時跑一次 sync
- LangSmith Dataset 名稱：`ug-order-eval`

## Evaluator 設計（5 個自定義指標）

### 1. JSON 合規率 (`json_valid`) — 0 或 1

模型輸出能否成功 parse 為合法 JSON。抓格式崩壞、多餘 token、截斷。

### 2. Intent 準確率 (`intent_accuracy`) — 0 或 1

推導出的 intent 是否正確（order / recommend / other）。

### 3. 品項準確率 (`item_accuracy`) — 0~1 連續分數

計算方式：正確品項數 / max(預期品項數, 實際品項數)。抓漏品項、多品項、品項名錯誤。

### 4. 欄位準確率 (`field_accuracy`) — 0~1 連續分數

針對 `check_fields` 指定的欄位逐一比對：
- 涵蓋：category、sugar、ice、size、qty、addon
- null 策略：預期 null 且實際 null = 正確
- 計算方式：正確欄位數 / 總檢查欄位數

### 5. 整體通過率 (`overall_pass`) — 0 或 1

所有欄位全部正確才算通過，等同於現有 eval 的 pass/fail。

## A/B Testing 對比機制

### 運作方式

```
Dataset: "ug-order-eval"（固定不變）
  ├── Experiment: "v10-cp800-20260218"   ← baseline
  ├── Experiment: "v11-cp700-20260220"   ← 新版本
  └── ...
```

- LangSmith Dashboard 內建 Experiment 對比功能
- 選取任意兩個 Experiment → 自動並排結果 + 指標差異
- 可篩選只看「退化」的案例

### Baseline 建立

第一次跑時用目前的 v10-8bit 跑一次完整評估作為 baseline。之後每輪訓練自動產生新 experiment。

### 命名規範

- 格式：`v{版本}-cp{checkpoint}-{日期}`
- 例：`v10-cp800-20260218`
- metadata：訓練資料量、base model、train loss

## train_and_eval.sh 整合

### eval_langsmith.py 執行邏輯

```python
# 1. 讀取最佳 checkpoint（從 step 2 的輸出解析）
# 2. 載入 base model + adapter（用 mlx_lm.load）
# 3. 從 LangSmith 拉 dataset（或本地 JSON fallback）
# 4. 對每筆測試案例：
#      - 組 prompt → 模型推論 → 記錄 raw output
#      - 模擬 fillDefaults（復用現有 eval 的邏輯）
#      - 跑 5 個 evaluator 計算分數
# 5. 上傳為 LangSmith Experiment
```

### 環境變數

| 變數 | 用途 | 預設值 |
|------|------|--------|
| `LANGSMITH_API_KEY` | API 認證 | 無（未設定則跳過） |
| `LANGSMITH_PROJECT` | 專案名稱 | `ug-order-eval` |
| `UG_MODEL_VERSION` | 模型版本標籤 | 從 adapter path 推斷 |

### 向後相容

沒有設定 `LANGSMITH_API_KEY` 時，`train_and_eval.sh` 行為跟現在完全一樣。

## 第二階段：全鏈路 Trace（未來擴充）

```
前端 (React/Next.js)
  │ trace_id 放在 request header
  ▼
Go 後端 (ug-backend)
  ├── span: normalizer（輸入原文 → 正規化結果）
  ├── span: LLM 呼叫（prompt → raw output）
  ├── span: validateOrders（修正了哪些欄位）
  ├── span: fillDefaults（填了哪些預設值）
  └── 回傳 trace_id 給前端
          ▼
      LangSmith（完整 trace 可視化）
```

- Go 後端：用 LangSmith REST API 送 trace
- Python LLM server：用 `langsmith` Python SDK 包 trace
- 前端：存 `trace_id` 供反查

## 實作步驟

### 第一階段（本次實作）

1. 安裝依賴：`pip install langsmith`
2. 建立 `sync_dataset.py`：從現有測試案例同步到 LangSmith Dataset
3. 建立 `eval_langsmith.py`：5 個 evaluator + 跑 experiment
4. 修改 `train_and_eval.sh`：尾巴接上 eval_langsmith.py
5. 設定 `.env`：加入 `LANGSMITH_API_KEY`
6. 跑一次 v10 baseline

### 第二階段（未來）

7. Python LLM server 加入 trace middleware
8. Go 後端加入 trace span
9. 前端傳遞 trace_id

## 新增檔案

| 檔案 | 用途 |
|------|------|
| `sync_dataset.py` | 同步測試案例到 LangSmith Dataset |
| `eval_langsmith.py` | LangSmith 評估主腳本 |
| `.env` | 存放 LANGSMITH_API_KEY |
