#!/usr/bin/env python3
"""Together AI 雲端 LoRA Fine-tuning 腳本。

使用方式：
  1. 安裝: pip install together
  2. 設定: export TOGETHER_API_KEY=your_key
  3. 執行: python3 cloud_train_together.py

流程：上傳資料 → 啟動訓練 → 監控進度 → 下載 adapter
"""

import argparse
import json
import os
import sys
import time

try:
    from together import Together
except ImportError:
    print("請先安裝: pip install together")
    sys.exit(1)


# === 配置 ===
BASE_MODEL = "Qwen/Qwen3-8B"
TRAIN_FILE = "data/train.jsonl"
VALID_FILE = "data/valid.jsonl"
SUFFIX = "ug-order"

# 訓練超參數（雲端最佳化，無硬體限制）
# 參考：LoRA Without Regret, Learning Rate Matters (2025), Unsloth Guide
TRAINING_PARAMS = {
    "n_epochs": 3,                  # batch_size 最小 8 → 21 steps/epoch，3 epochs = 63 steps
    "learning_rate": 2e-5,          # 研究建議 LoRA LR ≈ 10× full FT；保守取 4× 本地
    "train_on_inputs": False,       # 等同 mask_prompt: true
    "n_checkpoints": 4,             # 多 checkpoint 供本地評估選最佳
    "warmup_ratio": 0.1,            # LR 較高，用 10% warmup 穩定開局
    "batch_size": 8,                # Together AI 最小值，~21 steps/epoch
    "weight_decay": 0.01,           # 輕度正則化，防過擬合
    "lr_scheduler_type": "cosine",  # 平滑衰減，研究推薦
    "lora_r": 32,                   # 雲端無記憶體限制，更多容量學結構化模式
    "lora_alpha": 64,               # 2×rank 經驗法則
    "lora_dropout": 0.05,           # 小資料集加輕度 dropout
}


def validate_data(filepath):
    """驗證 JSONL 格式符合 Together AI 要求。"""
    errors = []
    count = 0
    with open(filepath) as f:
        for i, line in enumerate(f):
            count += 1
            try:
                sample = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"L{i+1}: JSON 解析失敗")
                continue

            messages = sample.get("messages")
            if not messages:
                errors.append(f"L{i+1}: 缺少 messages 欄位")
                continue

            # 檢查角色順序
            roles = [m["role"] for m in messages]
            if roles[0] not in ("system", "user"):
                errors.append(f"L{i+1}: 首條必須是 system 或 user")
            if "assistant" not in roles:
                errors.append(f"L{i+1}: 缺少 assistant 回應")

            # 檢查每條訊息都有 role + content
            for j, m in enumerate(messages):
                if "role" not in m or "content" not in m:
                    errors.append(f"L{i+1}: messages[{j}] 缺少 role 或 content")

    return count, errors


def upload_file(client, filepath, purpose="fine-tune"):
    """上傳檔案到 Together AI。"""
    print(f"上傳 {filepath}...")
    resp = client.files.upload(file=filepath, purpose=purpose)
    print(f"  完成: id={resp.id}, size={resp.bytes:,} bytes")
    return resp.id


def create_job(client, train_file_id, valid_file_id=None):
    """建立 fine-tuning job。"""
    params = {
        "training_file": train_file_id,
        "model": BASE_MODEL,
        "suffix": SUFFIX,
        **TRAINING_PARAMS,
    }
    if valid_file_id:
        params["validation_file"] = valid_file_id

    print(f"\n建立 fine-tuning job...")
    print(f"  Model: {BASE_MODEL}")
    print(f"  Params: epochs={TRAINING_PARAMS['n_epochs']}, lr={TRAINING_PARAMS['learning_rate']}, "
          f"batch={TRAINING_PARAMS['batch_size']}, wd={TRAINING_PARAMS.get('weight_decay', 0)}")
    print(f"  LoRA: r={TRAINING_PARAMS.get('lora_r')}, alpha={TRAINING_PARAMS.get('lora_alpha')}, "
          f"dropout={TRAINING_PARAMS.get('lora_dropout')}")

    resp = client.fine_tuning.create(**params)
    print(f"  Job ID: {resp.id}")
    print(f"  Status: {resp.status}")
    return resp.id


def monitor_job(client, job_id):
    """監控訓練進度直到完成。"""
    print(f"\n監控訓練進度 (job: {job_id})...")
    print("  按 Ctrl+C 可中斷監控（訓練不會停止）\n")

    last_step = -1
    start_time = time.time()

    while True:
        try:
            job = client.fine_tuning.retrieve(id=job_id)
        except Exception as e:
            print(f"  查詢失敗: {e}, 30 秒後重試...")
            time.sleep(30)
            continue

        status = job.status
        elapsed = time.time() - start_time
        elapsed_str = f"{int(elapsed//60)}m{int(elapsed%60)}s"

        if status == "completed":
            print(f"\n  ✅ 訓練完成！({elapsed_str})")
            print(f"  Model: {job.model_output_name}")
            return job
        elif status == "failed":
            print(f"\n  ❌ 訓練失敗！")
            if hasattr(job, "error"):
                print(f"  Error: {job.error}")
            return job
        elif status == "cancelled":
            print(f"\n  ⚠ 訓練已取消")
            return job

        # 嘗試顯示進度
        events = []
        try:
            events = list(client.fine_tuning.list_events(id=job_id))
        except Exception:
            pass

        if events:
            latest = events[-1] if events else None
            if latest and hasattr(latest, "step") and latest.step != last_step:
                last_step = latest.step
                loss_str = f"loss={latest.training_loss:.4f}" if hasattr(latest, "training_loss") and latest.training_loss else ""
                print(f"  [{elapsed_str}] step {latest.step} {loss_str} (status: {status})")
        else:
            print(f"  [{elapsed_str}] status: {status}")

        time.sleep(30)


def download_adapter(client, job_id, output_dir="adapters-cloud"):
    """下載 fine-tuned adapter。"""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "adapter.zip")

    print(f"\n下載 adapter 到 {output_dir}/...")
    try:
        # Together API v2 download
        response = client.fine_tuning.download(id=job_id)
        with open(output_path, "wb") as f:
            for chunk in response:
                f.write(chunk)
        print(f"  已儲存: {output_path}")
        print(f"\n解壓:")
        print(f"  cd {output_dir} && unzip adapter.zip")
    except Exception as e:
        print(f"  下載失敗: {e}")
        print(f"  請手動至 Together AI 後台下載")

    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Together AI Fine-tuning")
    parser.add_argument("--validate-only", action="store_true", help="只驗證資料，不訓練")
    parser.add_argument("--resume", type=str, help="繼續監控已存在的 job ID")
    parser.add_argument("--download", type=str, help="下載指定 job ID 的結果")
    parser.add_argument("--epochs", type=int, help="覆蓋 epoch 數")
    parser.add_argument("--lr", type=float, help="覆蓋 learning rate")
    args = parser.parse_args()

    # 覆蓋超參數
    if args.epochs:
        TRAINING_PARAMS["n_epochs"] = args.epochs
    if args.lr:
        TRAINING_PARAMS["learning_rate"] = args.lr

    # Step 0: 驗證 API key
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key and not args.validate_only:
        print("錯誤: 請設定 TOGETHER_API_KEY")
        print("  export TOGETHER_API_KEY=your_key_here")
        sys.exit(1)

    # Step 1: 驗證資料
    print("=== Step 1: 驗證資料格式 ===")
    for f in [TRAIN_FILE, VALID_FILE]:
        count, errors = validate_data(f)
        if errors:
            print(f"  ❌ {f}: {count} 筆, {len(errors)} 錯誤")
            for e in errors[:5]:
                print(f"    {e}")
            sys.exit(1)
        else:
            print(f"  ✅ {f}: {count} 筆, 格式正確")

    if args.validate_only:
        print("\n驗證完成")
        return

    client = Together(api_key=api_key)

    # 繼續監控
    if args.resume:
        job = monitor_job(client, args.resume)
        if job.status == "completed":
            download_adapter(client, args.resume)
        return

    # 下載結果
    if args.download:
        download_adapter(client, args.download)
        return

    # Step 2: 上傳資料（只上傳 train，validation 本地做省錢）
    print("\n=== Step 2: 上傳資料 ===")
    train_id = upload_file(client, TRAIN_FILE)

    # Step 3: 建立訓練 job
    print("\n=== Step 3: 建立訓練 Job ===")
    job_id = create_job(client, train_id)

    # 儲存 job ID
    job_info = {
        "job_id": job_id,
        "model": BASE_MODEL,
        "train_file_id": train_id,
        "params": TRAINING_PARAMS,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open("cloud_job.json", "w") as f:
        json.dump(job_info, f, indent=2, ensure_ascii=False)
    print(f"\nJob 資訊已存到 cloud_job.json")

    # Step 4: 監控
    print("\n=== Step 4: 監控訓練 ===")
    job = monitor_job(client, job_id)

    # Step 5: 下載
    if job.status == "completed":
        print("\n=== Step 5: 下載結果 ===")
        download_adapter(client, job_id)

        print("\n=== 後續步驟 ===")
        print("1. 用 Together AI 推論 API 評估：")
        print(f"   python3 eval_cloud.py --model {job.model_output_name}")
        print()
        print("2. 或下載轉換為本地 MLX 格式：")
        print("   python3 convert_cloud_to_mlx.py --input adapters-cloud --output model/Qwen3-8B-UG-order-v11")


if __name__ == "__main__":
    main()
