#!/usr/bin/env python3
"""
UG 點單助手 - 互動測試腳本
用途：載入微調後的模型，以互動方式測試點單功能
使用方式：python test_order.py
"""

from mlx_lm import load, generate

# === 模型路徑設定 ===
MODEL_PATH = "model/Qwen3-4B-4bit"
ADAPTER_PATH = "adapters"

# === 系統提示詞（與訓練資料一致） ===
SYSTEM_PROMPT = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。\n"
    "\n"
    "菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、"
    "果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。\n"
    "\n"
    "純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，回傳 not_on_menu 欄位。\n"
    "\n"
    '輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null",'
    '"ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"unit_price":0,'
    '"note":""}],"total":0}'
)


def build_prompt(user_input: str) -> str:
    """組合 ChatML 格式的完整提示詞"""
    return (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_input}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def main():
    # --- 載入模型與 adapter ---
    print("=" * 50)
    print("  UG 點單助手 - 互動測試")
    print("=" * 50)
    print()
    print("正在載入模型與 LoRA adapter...")
    print(f"  模型路徑：{MODEL_PATH}")
    print(f"  Adapter 路徑：{ADAPTER_PATH}")

    model, tokenizer = load(
        MODEL_PATH,
        adapter_path=ADAPTER_PATH,
    )
    print("模型載入完成！")
    print()
    print("請輸入顧客的點單內容（輸入 q 或 quit 離開）：")
    print("-" * 50)

    # --- 互動迴圈 ---
    while True:
        try:
            user_input = input("\n顧客> ").strip()
        except (EOFError, KeyboardInterrupt):
            # 處理 Ctrl+D 或 Ctrl+C
            print("\n再見！")
            break

        # 檢查是否要離開
        if user_input.lower() in ("q", "quit", "exit", "bye"):
            print("再見！")
            break

        # 跳過空白輸入
        if not user_input:
            continue

        # 組合提示詞並生成回應
        prompt = build_prompt(user_input)
        response = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=512,
            verbose=False,
        )

        # 輸出結果
        # generate 回傳的文字可能包含結束標記，需要清理
        output = response.split("<|im_end|>")[0].strip()
        print(f"\n訂單> {output}")


if __name__ == "__main__":
    main()
