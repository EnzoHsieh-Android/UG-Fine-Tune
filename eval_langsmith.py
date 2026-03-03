#!/usr/bin/env python3
"""LangSmith 自動化評估腳本。

用法:
  # 評估已部署的 fused 模型（如 v10-8bit）
  python eval_langsmith.py --model-path model/Qwen3-8B-UG-order-v10-8bit --version v10-cp800

  # 評估訓練中的 checkpoint（base model + adapter）
  python eval_langsmith.py --base-model model/Qwen3-8B-4bit --adapter adapters-8b --version v11-cp700

整合進 train_and_eval.sh 時，自動從最佳 checkpoint 推斷參數。
"""

import argparse
import json
import os
import sys
from datetime import datetime

from langsmith import Client, evaluate

# ======== 菜單分類對照（與 menu.go 一致）========

MENU_CATEGORIES = {
    "pure_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁"],
    "fresh_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "rich_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "fruit_tea": ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"],
    "cloud_velvet": ["桂花輕烏龍", "茶花紅烏龍"],
}

ITEM_CATEGORIES = {}
for cat_id, items in MENU_CATEGORIES.items():
    for item in items:
        ITEM_CATEGORIES.setdefault(item, []).append(cat_id)

CATEGORY_PRIORITY = ["pure_tea", "rich_milk_tea"]


def is_valid_item_category(item_name: str, category_id: str) -> bool:
    """檢查 item + category 組合是否存在於菜單。"""
    return item_name in MENU_CATEGORIES.get(category_id, [])


def get_default_category(item_name: str) -> str | None:
    """取得品項預設分類（priority: pure_tea → rich_milk_tea → first）。"""
    cats = ITEM_CATEGORIES.get(item_name, [])
    if not cats:
        return None
    for priority_cat in CATEGORY_PRIORITY:
        if priority_cat in cats:
            return priority_cat
    return cats[0]


def simulate_fill_defaults(orders: list[dict]) -> list[dict]:
    """模擬後端 fillDefaults — 只處理 category（與最新後端一致）。

    邏輯：信任模型輸出 → 驗證 item+category 組合 → 無效/空則 fallback 到 default。
    """
    for order in orders:
        item = order.get("item", "")
        cat = order.get("category")
        if cat is None or not is_valid_item_category(item, cat):
            default = get_default_category(item)
            if default:
                order["category"] = default
    return orders


# ======== System Prompt（與 llm.go 一致）========

SYSTEM_PROMPT = """你是 No.315 Unique Green 的點單助手。根據顧客的自然語言輸出 JSON。

菜單分類與品項描述：
【研選純茶 pure_tea】單一尺寸
- 三窨十五茉：三次窨花茉莉綠茶，花香清雅帶甘甜
- 桂花輕烏龍：桂花與輕發酵烏龍，花果蜜韻輕柔
- 茶花紅烏龍：重焙火紅烏龍，天然花香與熟果甜韻
- 朱槿普洱紅：洛神花搭普洱紅茶，微酸回甘解膩
- 米香玉露菁：日式玉露菁帶米穀香，鮮爽細膩

【牧場直達 fresh_milk_tea】M/L
- 三窨十五茉(65/75)：茉莉鮮奶，清香滑順
- 桂花輕烏龍(65/75)：桂花烏龍鮮奶，蜜韻奶香溫潤
- 茶花紅烏龍(65/75)：烏龍鮮奶，茶奶平衡圓潤
- 琥珀鐵觀音(65/75)：重焙鐵觀音鮮奶，焙火香濃郁
- 金杯蜜香紅(60/70)：蜜香紅茶鮮奶，天然蜜甜
- 朱槿普洱紅(60/70)：洛神普洱鮮奶，微酸風味獨特
- 米香玉露菁(60/70)：玉露菁鮮奶，穀物奶香療癒

【UG奶茶 rich_milk_tea】M/L
- 三窨十五茉(65/75)、桂花輕烏龍(65/75)、茶花紅烏龍(65/75)
- 琥珀鐵觀音(65/75)、金杯蜜香紅(60/70)、朱槿普洱紅(60/70)、米香玉露菁(60/70)

【果香四溢 fruit_tea】僅冷飲，單一尺寸
- 青檸桂蜜(65)：青檸搭桂花蜜，酸甜清爽消暑
- 蜜桃紅烏龍(75)：水蜜桃果香與紅烏龍交織，甜蜜芬芳
- 葡柚十五茉(80)：葡萄柚酸香配茉莉，清新微苦大人味

【雲頂奶蓋 cloud_velvet】單一尺寸
- 桂花輕烏龍(95)：桂花烏龍覆綿密奶蓋，鹹甜交融
- 茶花紅烏龍(95)：紅烏龍焙火韻搭奶蓋，茶香奶鹹平衡

加料：紅烏龍茶凍(+15)、燕麥粒(+15)。
甜度：全糖/五分糖/三分糖/一分糖/無糖（顧客若說正常糖/半糖/少糖/微糖亦照錄）。冰量：正常冰/少冰/微冰/去冰/熱飲。
未指定的甜度、冰量、尺寸設為 null。未指定分類時 category 設 null。

intents 規則：
- intents 陣列，每個元素對應一段輸入（以分號分隔），值為 order/recommend/modify/other
- order：點餐或新增品項
- recommend：請求推薦（含口味偏好、場景描述等隱含推薦）
- modify：修改或取消既有品項
- other：閒聊或無法辨識
- 單段輸入時 intents 只有一個元素

輸出格式（必須為合法 JSON）：
{"intents":[],"orders":[],"preferences":{},"recommendations":[]}
- 顧客點餐：填入 orders，每筆格式 {"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}
- 顧客想要推薦：填入 preferences（口味/溫度/場景/排除，無明確偏好時為空物件）與 recommendations（僅推薦 1 項），格式 {"item":"品名","category":"分類","reason":"推薦理由"}
- 點餐同時想推薦：orders 和 recommendations 同時填入，preferences 一併填入
- 閒聊或無法辨識：三個欄位皆為空
- 若 intents 中有 recommend，recommendations 必須填入推薦結果（後端決定是否顯示）"""


# ======== 模型推論 ========

_model = None
_tokenizer = None


def load_model(model_path: str, adapter_path: str | None = None):
    """載入模型（含 cache，避免重複載入）。"""
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    from mlx_lm import load
    if adapter_path:
        _model, _tokenizer = load(model_path, adapter_path=adapter_path)
    else:
        _model, _tokenizer = load(model_path)
    return _model, _tokenizer


def run_inference(user_input: str) -> str:
    """用載入的模型跑推論，回傳 raw output。"""
    from mlx_lm import generate
    model, tokenizer = _model, _tokenizer

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    prompt += "/no_think\n"
    response = generate(model, tokenizer, prompt=prompt, max_tokens=512, verbose=False)
    if "</think>" in response:
        response = response.split("</think>")[-1].strip()
    return response.strip()


def parse_response(raw: str) -> tuple[str, list[dict], list[dict], dict]:
    """Parse JSON，從 intents 陣列推導 intent，fallback 到內容推導。"""
    for i, ch in enumerate(raw):
        if ch == "{":
            depth = 0
            for j in range(i, len(raw)):
                if raw[j] == "{":
                    depth += 1
                elif raw[j] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            data = json.loads(raw[i : j + 1])
                            intents = data.get("intents", [])
                            orders = data.get("orders", [])
                            recs = data.get("recommendations", [])
                            # Use model's intents output (Round 31+)
                            if intents:
                                last = intents[-1]
                                if last in ("order", "modify") and orders:
                                    intent = "order"
                                elif last == "recommend" and not orders:
                                    intent = "recommend"
                                elif orders:
                                    intent = "order"
                                elif last == "recommend":
                                    intent = "recommend"
                                elif last == "other":
                                    intent = "other"
                                else:
                                    intent = "other"
                            # Fallback: derive from content
                            elif orders:
                                intent = "order"
                            elif recs:
                                intent = "recommend"
                            else:
                                intent = "other"
                            return intent, orders, recs, data
                        except json.JSONDecodeError:
                            break
    return "other", [], [], {}


# ======== LangSmith target function ========


def target(inputs: dict) -> dict:
    """LangSmith evaluate 的 target function。"""
    user_input = inputs["input"]
    raw = run_inference(user_input)
    intent, orders, recs, data = parse_response(raw)

    # 保留模型原始輸出（用於 null 檢查）
    import copy
    raw_orders = copy.deepcopy(orders)

    # 模擬後端 fillDefaults（category）
    if orders:
        orders = simulate_fill_defaults(orders)

    return {
        "raw": raw,
        "intent": intent,
        "orders": orders,
        "raw_orders": raw_orders,
        "recommendations": recs,
        "parsed": data,
    }


# ======== 5 個 Evaluator ========


def json_valid(run, example) -> dict:
    """1. JSON 合規率：模型輸出能否 parse 為合法 JSON。"""
    raw = run.outputs.get("raw", "")
    try:
        # 嘗試找到 JSON
        for i, ch in enumerate(raw):
            if ch == "{":
                depth = 0
                for j in range(i, len(raw)):
                    if raw[j] == "{":
                        depth += 1
                    elif raw[j] == "}":
                        depth -= 1
                        if depth == 0:
                            json.loads(raw[i : j + 1])
                            return {"key": "json_valid", "score": 1.0}
        return {"key": "json_valid", "score": 0.0}
    except Exception:
        return {"key": "json_valid", "score": 0.0}


def intent_accuracy(run, example) -> dict:
    """2. Intent 準確率。"""
    actual = run.outputs.get("intent", "")
    expected = example.outputs.get("expected_intent", "")
    return {"key": "intent_accuracy", "score": 1.0 if actual == expected else 0.0}


def item_accuracy(run, example) -> dict:
    """3. 品項準確率：品項名稱正確性 + 數量正確性的平均。

    拆成兩個維度避免跨分類（同品項多杯）的誤判：
    - items_present: 預期的唯一品項名是否都出現
    - count_correct: 訂單數量是否正確
    """
    expected_items = example.outputs.get("expected_items", [])
    if not expected_items:
        # 非 order 測試（recommend/other），不計算
        return {"key": "item_accuracy", "score": 1.0}

    actual_items = [o.get("item", "") for o in run.outputs.get("orders", [])]
    expected_count = example.outputs.get("expected_count", len(expected_items))

    # 品項名稱：預期的唯一品項是否都出現在實際結果中
    items_present = sum(1 for item in expected_items if item in actual_items) / len(expected_items)

    # 數量：訂單數是否正確
    count_correct = 1.0 if len(actual_items) == expected_count else 0.0

    score = (items_present + count_correct) / 2
    return {"key": "item_accuracy", "score": score}


def field_accuracy(run, example) -> dict:
    """4. 欄位準確率：逐欄位比對。

    null 檢查用 raw_orders（fillDefaults 前），其他檢查用 orders（fillDefaults 後）。
    """
    orders = run.outputs.get("orders", [])
    raw_orders = run.outputs.get("raw_orders", orders)
    total_checks = 0
    correct_checks = 0

    # check_null — 用 raw_orders（模型原始輸出）
    check_null = example.outputs.get("check_null", {})
    if check_null and raw_orders:
        for field, should_be_null in check_null.items():
            if should_be_null:
                total_checks += 1
                if raw_orders[0].get(field) is None:
                    correct_checks += 1

    # check_value — 用 orders（fillDefaults 後）
    check_value = example.outputs.get("check_value", {})
    if check_value and orders:
        for field, expected_val in check_value.items():
            total_checks += 1
            if orders[0].get(field) == expected_val:
                correct_checks += 1

    # check_orders — 用 orders（fillDefaults 後）
    check_orders = example.outputs.get("check_orders", [])
    if check_orders and len(orders) == len(check_orders):
        for idx, expected_order in enumerate(check_orders):
            for field, expected_val in expected_order.items():
                total_checks += 1
                if orders[idx].get(field) == expected_val:
                    correct_checks += 1

    if total_checks == 0:
        return {"key": "field_accuracy", "score": 1.0}

    return {"key": "field_accuracy", "score": correct_checks / total_checks}


def overall_pass(run, example) -> dict:
    """5. 整體通過率：所有檢查全通過才算 1。"""
    # Intent
    actual_intent = run.outputs.get("intent", "")
    expected_intent = example.outputs.get("expected_intent", "")
    if actual_intent != expected_intent:
        return {"key": "overall_pass", "score": 0.0}

    # 非 order 測試只看 intent
    if expected_intent in ("recommend", "other"):
        return {"key": "overall_pass", "score": 1.0}

    orders = run.outputs.get("orders", [])
    expected_items = example.outputs.get("expected_items", [])
    expected_count = example.outputs.get("expected_count", 0)

    # Item count
    if len(orders) != expected_count:
        return {"key": "overall_pass", "score": 0.0}

    # Item names
    actual_items = [o.get("item", "") for o in orders]
    if not all(item in actual_items for item in expected_items):
        return {"key": "overall_pass", "score": 0.0}

    # not_on_menu
    if example.outputs.get("not_on_menu"):
        pass
    else:
        if any(o.get("not_on_menu") for o in orders):
            return {"key": "overall_pass", "score": 0.0}

    # check_null — 用 raw_orders（模型原始輸出）
    raw_orders = run.outputs.get("raw_orders", orders)
    for field, should_be_null in example.outputs.get("check_null", {}).items():
        if should_be_null and raw_orders and raw_orders[0].get(field) is not None:
            return {"key": "overall_pass", "score": 0.0}

    # check_value
    for field, expected_val in example.outputs.get("check_value", {}).items():
        if orders and orders[0].get(field) != expected_val:
            return {"key": "overall_pass", "score": 0.0}

    # check_orders
    check_orders = example.outputs.get("check_orders", [])
    if check_orders:
        if len(orders) != len(check_orders):
            return {"key": "overall_pass", "score": 0.0}
        for idx, expected_order in enumerate(check_orders):
            for field, expected_val in expected_order.items():
                if orders[idx].get(field) != expected_val:
                    return {"key": "overall_pass", "score": 0.0}

    return {"key": "overall_pass", "score": 1.0}


# ======== Main ========


def main():
    parser = argparse.ArgumentParser(description="LangSmith 模型評估")
    parser.add_argument("--model-path", help="Fused 模型路徑（如 model/Qwen3-8B-UG-order-v10-8bit）")
    parser.add_argument("--base-model", help="Base model 路徑（配合 --adapter 使用）")
    parser.add_argument("--adapter", help="Adapter 路徑（配合 --base-model 使用）")
    parser.add_argument("--version", required=True, help="版本標籤（如 v10-cp800）")
    parser.add_argument("--dataset", default=None, help="LangSmith dataset 名稱（預設從環境變數讀取）")
    args = parser.parse_args()

    # 檢查 API key
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("錯誤：未設定 LANGSMITH_API_KEY，跳過 LangSmith 評估")
        sys.exit(0)

    dataset_name = args.dataset or os.getenv("LANGSMITH_PROJECT", "ug-order-eval")
    today = datetime.now().strftime("%Y%m%d")
    experiment_name = f"{args.version}-{today}"

    # 載入模型
    if args.model_path:
        print(f"載入 fused 模型: {args.model_path}")
        load_model(args.model_path)
    elif args.base_model and args.adapter:
        print(f"載入 base model + adapter: {args.base_model} + {args.adapter}")
        load_model(args.base_model, adapter_path=args.adapter)
    else:
        print("錯誤：需要 --model-path 或 --base-model + --adapter")
        sys.exit(1)

    print(f"Dataset: {dataset_name}")
    print(f"Experiment: {experiment_name}")
    print(f"開始評估...")

    # 跑 LangSmith evaluate
    results = evaluate(
        target,
        data=dataset_name,
        evaluators=[json_valid, intent_accuracy, item_accuracy, field_accuracy, overall_pass],
        experiment_prefix=experiment_name,
        metadata={
            "model_version": args.version,
            "date": today,
            "model_path": args.model_path or f"{args.base_model}+{args.adapter}",
        },
    )

    # 印出摘要
    print(f"\n{'='*50}")
    print(f"LangSmith 評估完成: {experiment_name}")
    print(f"Dashboard: https://smith.langchain.com")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
