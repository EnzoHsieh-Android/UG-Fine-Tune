#!/usr/bin/env python3
"""透過 vLLM /v1/completions API 評估 Qwen3.5 模型（遠端 GCP VM 用）"""

import json
import copy
import time
import sys
import requests

# ========== 設定 ==========
VLLM_URL = "http://127.0.0.1:8080/v1/completions"
MODEL_NAME = "/opt/models/Qwen3.5-4B-merged"

# 後端甜度映射
SUGAR_BACKEND_MAP = {
    "正常糖": "全糖",
    "半糖": "五分糖",
    "少糖": "五分糖",
    "微糖": "三分糖",
}


def sugar_equivalent(actual, expected):
    if actual == expected:
        return True
    actual_final = SUGAR_BACKEND_MAP.get(actual, actual)
    expected_final = SUGAR_BACKEND_MAP.get(expected, expected)
    return actual_final == expected_final


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


# ========== 測試案例 ==========

STANDARD_TESTS = [
    {"input": "一杯三窨十五茉", "expect": "order", "items": ["三窨十五茉"], "count": 1},
    {"input": "桂花輕烏龍鮮奶", "expect": "order", "items": ["桂花輕烏龍"], "count": 1},
    {"input": "青檸桂蜜", "expect": "order", "items": ["青檸桂蜜"], "count": 1},
    {"input": "我要三窨十五茉、金杯蜜香紅鮮奶、還有青檸桂蜜", "expect": "order", "items": ["三窨十五茉", "金杯蜜香紅", "青檸桂蜜"], "count": 3},
    {"input": "三杯桂花輕烏龍", "expect": "order", "items": ["桂花輕烏龍"], "count": 1},
    {"input": "一杯茉莉", "expect": "order", "items": ["三窨十五茉"], "count": 1},
    {"input": "鐵觀音微糖去冰", "expect": "order", "items": ["琥珀鐵觀音"], "count": 1},
    {"input": "普洱熱的", "expect": "order", "items": ["朱槿普洱紅"], "count": 1},
    {"input": "茶花紅烏龍奶蓋", "expect": "order", "items": ["茶花紅烏龍"], "count": 1},
    {"input": "三窨十五茉半糖、三窨十五茉無糖", "expect": "order", "items": ["三窨十五茉"], "count": 2},
    {"input": "三窨十五茉和金杯蜜香紅，金杯不要了", "expect": "order", "items": ["三窨十五茉"], "count": 1},
    {"input": "我要三窨十五茉，不對，改成桂花輕烏龍", "expect": "order", "items": ["桂花輕烏龍"], "count": 1},
    {"input": "一杯珍珠奶茶", "expect": "order", "items": ["珍珠奶茶"], "count": 1, "not_on_menu": True},
]

NULL_TESTS = [
    {"input": "三窨十五茉", "expect": "order", "items": ["三窨十五茉"], "count": 1,
     "check_null": {"sugar": True, "ice": True}},
    {"input": "桂花輕烏龍", "expect": "order", "items": ["桂花輕烏龍"], "count": 1,
     "check_null": {"category": True}},
    {"input": "金杯蜜香紅無糖", "expect": "order", "items": ["金杯蜜香紅"], "count": 1,
     "check_null": {"ice": True}, "check_value": {"sugar": "無糖"}},
    {"input": "琥珀鐵觀音去冰", "expect": "order", "items": ["琥珀鐵觀音"], "count": 1,
     "check_null": {"sugar": True}, "check_value": {"ice": "去冰"}},
    {"input": "桂花輕烏龍鮮奶無糖", "expect": "order", "items": ["桂花輕烏龍"], "count": 1,
     "check_null": {"size": True}},
]

SUGAR_TESTS = [
    {"input": "三窨十五茉全糖", "expect": "order", "items": ["三窨十五茉"], "count": 1,
     "check_value": {"sugar": "全糖"}},
    {"input": "桂花輕烏龍五分糖", "expect": "order", "items": ["桂花輕烏龍"], "count": 1,
     "check_value": {"sugar": "五分糖"}},
    {"input": "金杯蜜香紅三分糖", "expect": "order", "items": ["金杯蜜香紅"], "count": 1,
     "check_value": {"sugar": "三分糖"}},
    {"input": "琥珀鐵觀音一分糖", "expect": "order", "items": ["琥珀鐵觀音"], "count": 1,
     "check_value": {"sugar": "一分糖"}},
    {"input": "三窨十五茉半糖", "expect": "order", "items": ["三窨十五茉"], "count": 1,
     "check_value": {"sugar": "半糖"}},
    {"input": "桂花輕烏龍少糖", "expect": "order", "items": ["桂花輕烏龍"], "count": 1,
     "check_value": {"sugar": "少糖"}},
    {"input": "金杯蜜香紅微糖", "expect": "order", "items": ["金杯蜜香紅"], "count": 1,
     "check_value": {"sugar": "微糖"}},
    {"input": "茶花紅烏龍正常糖", "expect": "order", "items": ["茶花紅烏龍"], "count": 1,
     "check_value": {"sugar": "正常糖"}},
]

RECOMMEND_TESTS = [
    {"input": "你們有什麼推薦的", "expect": "recommend"},
    {"input": "有沒有不苦的茶", "expect": "recommend"},
    {"input": "想喝清爽一點的", "expect": "recommend"},
]

OTHER_TESTS = [
    {"input": "你們幾點關門", "expect": "other"},
    {"input": "謝謝", "expect": "other"},
]

GENERALIZED_TESTS = [
    {"input": "來杯玉露", "expect": "order", "items": ["米香玉露菁"], "count": 1},
    {"input": "給我蜜桃的", "expect": "order", "items": ["蜜桃紅烏龍"], "count": 1},
    {"input": "葡柚那個", "expect": "order", "items": ["葡柚十五茉"], "count": 1},
    {"input": "鐵觀音奶茶大杯", "expect": "order", "items": ["琥珀鐵觀音"], "count": 1},
    {"input": "米香玉露菁奶茶三分糖少冰", "expect": "order", "items": ["米香玉露菁"], "count": 1,
     "check_value": {"sugar": "三分糖", "ice": "少冰"}},
    {"input": "朱槿普洱紅鮮奶一分糖微冰", "expect": "order", "items": ["朱槿普洱紅"], "count": 1,
     "check_value": {"sugar": "一分糖", "ice": "微冰"}},
    {"input": "葡柚十五茉跟蜜桃紅烏龍各一杯", "expect": "order", "items": ["葡柚十五茉", "蜜桃紅烏龍"], "count": 2},
    {"input": "茶花紅烏龍鮮奶大杯五分糖加燕麥粒", "expect": "order", "items": ["茶花紅烏龍"], "count": 1,
     "check_value": {"sugar": "五分糖"}},
    {"input": "隨便給我一杯好喝的奶茶", "expect": "recommend"},
    {"input": "朋友推薦你們的茉莉，來一杯", "expect": "order", "items": ["三窨十五茉"], "count": 1},
    {"input": "金杯蜜香紅全糖，啊改五分就好", "expect": "order", "items": ["金杯蜜香紅"], "count": 1,
     "check_value": {"sugar": "五分糖"}},
    {"input": "桂花輕烏龍三分糖、琥珀鐵觀音無糖", "expect": "order",
     "items": ["桂花輕烏龍", "琥珀鐵觀音"], "count": 2},
]

CROSS_CATEGORY_TESTS = [
    {"input": "兩杯琥珀鐵觀音，一杯鮮奶的半糖去冰，一杯奶茶的無糖少冰",
     "expect": "order", "items": ["琥珀鐵觀音"], "count": 2,
     "check_orders": [
         {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "sugar": "半糖", "ice": "去冰"},
         {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "sugar": "無糖", "ice": "少冰"},
     ]},
    {"input": "茶花紅烏龍純茶無糖，再一杯鮮奶的大杯半糖去冰",
     "expect": "order", "items": ["茶花紅烏龍"], "count": 2,
     "check_orders": [
         {"item": "茶花紅烏龍", "category": "pure_tea", "sugar": "無糖"},
         {"item": "茶花紅烏龍", "category": "fresh_milk_tea", "sugar": "半糖", "ice": "去冰", "size": "L"},
     ]},
    {"input": "桂花輕烏龍奶蓋微糖，再一杯桂花輕烏龍奶茶大杯無糖去冰",
     "expect": "order", "items": ["桂花輕烏龍"], "count": 2,
     "check_orders": [
         {"item": "桂花輕烏龍", "category": "cloud_velvet", "sugar": "微糖"},
         {"item": "桂花輕烏龍", "category": "rich_milk_tea", "sugar": "無糖", "ice": "去冰", "size": "L"},
     ]},
    {"input": "三杯茶花紅烏龍，純茶無糖、鮮奶的中杯半糖、奶蓋微糖",
     "expect": "order", "items": ["茶花紅烏龍"], "count": 3,
     "check_orders": [
         {"item": "茶花紅烏龍", "category": "pure_tea", "sugar": "無糖"},
         {"item": "茶花紅烏龍", "category": "fresh_milk_tea", "sugar": "半糖", "size": "M"},
         {"item": "茶花紅烏龍", "category": "cloud_velvet", "sugar": "微糖"},
     ]},
    {"input": "蜜桃紅烏龍一杯，再一杯茶花紅烏龍奶茶半糖少冰",
     "expect": "order", "items": ["蜜桃紅烏龍", "茶花紅烏龍"], "count": 2,
     "check_orders": [
         {"item": "蜜桃紅烏龍", "category": "fruit_tea"},
         {"item": "茶花紅烏龍", "category": "rich_milk_tea", "sugar": "半糖", "ice": "少冰"},
     ]},
    {"input": "葡柚十五茉一杯，再一杯三窨十五茉鮮奶半糖去冰",
     "expect": "order", "items": ["葡柚十五茉", "三窨十五茉"], "count": 2,
     "check_orders": [
         {"item": "葡柚十五茉", "category": "fruit_tea"},
         {"item": "三窨十五茉", "category": "fresh_milk_tea", "sugar": "半糖", "ice": "去冰"},
     ]},
    {"input": "琥珀鐵觀音鮮奶茶半糖去冰;再一杯琥珀鐵觀音奶茶無糖少冰",
     "expect": "order", "items": ["琥珀鐵觀音"], "count": 2,
     "check_orders": [
         {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "sugar": "半糖", "ice": "去冰"},
         {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "sugar": "無糖", "ice": "少冰"},
     ]},
]

DOUBLE_ADDON_TESTS = [
    {"input": "琥珀鐵觀音鮮奶茶大杯半糖少冰加雙份茶凍",
     "expect": "order", "items": ["琥珀鐵觀音"], "count": 1,
     "check_value": {"category": "fresh_milk_tea", "size": "L", "sugar": "半糖", "ice": "少冰",
                     "addon": ["紅烏龍茶凍", "紅烏龍茶凍"]}},
    {"input": "金杯蜜香紅奶茶加兩份燕麥粒半糖少冰",
     "expect": "order", "items": ["金杯蜜香紅"], "count": 1,
     "check_value": {"category": "rich_milk_tea", "sugar": "半糖", "ice": "少冰",
                     "addon": ["燕麥粒", "燕麥粒"]}},
    {"input": "桂花輕烏龍鮮奶茶中杯無糖去冰加雙份茶凍和燕麥",
     "expect": "order", "items": ["桂花輕烏龍"], "count": 1,
     "check_value": {"category": "fresh_milk_tea", "sugar": "無糖", "ice": "去冰",
                     "addon": ["紅烏龍茶凍", "紅烏龍茶凍", "燕麥粒"]}},
]

MULTI_TURN_CATEGORY_TESTS = [
    {"input": "琥珀鐵觀音鮮奶茶半糖少冰;再一杯金杯蜜香紅無糖去冰",
     "expect": "order", "items": ["琥珀鐵觀音", "金杯蜜香紅"], "count": 2,
     "check_orders": [
         {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "sugar": "半糖", "ice": "少冰"},
         {"item": "金杯蜜香紅", "category": None, "sugar": "無糖", "ice": "去冰"},
     ]},
    {"input": "茶花紅烏龍奶蓋;再一杯桂花輕烏龍半糖少冰",
     "expect": "order", "items": ["茶花紅烏龍", "桂花輕烏龍"], "count": 2,
     "check_orders": [
         {"item": "茶花紅烏龍", "category": "cloud_velvet", "sugar": None, "ice": None},
         {"item": "桂花輕烏龍", "category": None, "sugar": "半糖", "ice": "少冰"},
     ]},
    {"input": "金杯蜜香紅一杯半糖少冰;再一杯琥珀鐵觀音鮮奶大杯去冰",
     "expect": "order", "items": ["金杯蜜香紅", "琥珀鐵觀音"], "count": 2,
     "check_orders": [
         {"item": "金杯蜜香紅", "category": "rich_milk_tea", "sugar": "半糖", "ice": "少冰"},
         {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "L", "ice": "去冰"},
     ]},
    {"input": "三窨十五茉純茶無糖去冰;再一杯米香玉露菁半糖少冰",
     "expect": "order", "items": ["三窨十五茉", "米香玉露菁"], "count": 2,
     "check_orders": [
         {"item": "三窨十五茉", "category": "pure_tea", "sugar": "無糖", "ice": "去冰"},
         {"item": "米香玉露菁", "category": None, "sugar": "半糖", "ice": "少冰"},
     ]},
]

QUANTITY_SPLIT_TESTS = [
    {"input": "三杯桂花輕烏龍，兩杯奶茶半糖少冰，一杯純茶無糖去冰",
     "expect": "order", "items": ["桂花輕烏龍"], "count": 2,
     "check_orders": [
         {"item": "桂花輕烏龍", "category": "rich_milk_tea", "qty": 2, "sugar": "半糖", "ice": "少冰"},
         {"item": "桂花輕烏龍", "category": "pure_tea", "qty": 1, "sugar": "無糖", "ice": "去冰"},
     ]},
    {"input": "兩杯琥珀鐵觀音，鮮奶茶的大杯半糖去冰，奶茶的無糖少冰",
     "expect": "order", "items": ["琥珀鐵觀音", "琥珀鐵觀音"], "count": 2,
     "check_orders": [
         {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "size": "L", "sugar": "半糖", "ice": "去冰"},
         {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "sugar": "無糖", "ice": "少冰"},
     ]},
    {"input": "三杯三窨十五茉鮮奶茶少冰，兩杯半糖一杯無糖",
     "expect": "order", "items": ["三窨十五茉"], "count": 2,
     "check_orders": [
         {"item": "三窨十五茉", "category": "fresh_milk_tea", "sugar": "半糖", "ice": "少冰", "qty": 2},
         {"item": "三窨十五茉", "category": "fresh_milk_tea", "sugar": "無糖", "ice": "少冰", "qty": 1},
     ]},
]

ALL_TESTS = (
    [("標準", t) for t in STANDARD_TESTS] +
    [("Null策略", t) for t in NULL_TESTS] +
    [("甜度", t) for t in SUGAR_TESTS] +
    [("推薦", t) for t in RECOMMEND_TESTS] +
    [("閒聊", t) for t in OTHER_TESTS] +
    [("泛化", t) for t in GENERALIZED_TESTS] +
    [("跨分類", t) for t in CROSS_CATEGORY_TESTS] +
    [("雙份加料", t) for t in DOUBLE_ADDON_TESTS] +
    [("多輪category", t) for t in MULTI_TURN_CATEGORY_TESTS] +
    [("數量拆分", t) for t in QUANTITY_SPLIT_TESTS]
)


# ========== 後端 fillDefaults 模擬 ==========

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


def is_valid_item_category(item_name, category_id):
    return item_name in MENU_CATEGORIES.get(category_id, [])


def get_default_category(item_name):
    cats = ITEM_CATEGORIES.get(item_name, [])
    if not cats:
        return None
    for priority_cat in CATEGORY_PRIORITY:
        if priority_cat in cats:
            return priority_cat
    return cats[0]


def simulate_fill_defaults(orders):
    for order in orders:
        item = order.get("item", "")
        cat = order.get("category")
        if cat is None or not is_valid_item_category(item, cat):
            default = get_default_category(item)
            if default:
                order["category"] = default
    return orders


# ========== vLLM API 推論 ==========

def build_prompt(user_input):
    """構造 /v1/completions 用的 prompt，與訓練格式一致"""
    return (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_input}<|im_end|>\n"
        f"<|im_start|>assistant\n/no_think\n"
    )


def generate_response(user_input):
    """透過 vLLM /v1/completions API 取得回應"""
    prompt = build_prompt(user_input)
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": 512,
        "temperature": 0,
        "stop": ["<|im_end|>"],
    }
    try:
        resp = requests.post(VLLM_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["text"].strip()
        # Strip thinking tags if present
        if "</think>" in text:
            text = text.split("</think>")[-1].strip()
        return text
    except Exception as e:
        print(f"  API error: {e}")
        return ""


def parse_response(response):
    for i, ch in enumerate(response):
        if ch == '{':
            depth = 0
            for j in range(i, len(response)):
                if response[j] == '{':
                    depth += 1
                elif response[j] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            data = json.loads(response[i:j+1])
                            intents = data.get("intents", [])
                            orders = data.get("orders", [])
                            recommendations = data.get("recommendations", [])
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
                            elif orders:
                                intent = "order"
                            elif recommendations:
                                intent = "recommend"
                            else:
                                intent = "other"
                            return intent, orders, recommendations, data
                        except json.JSONDecodeError:
                            break
    return "other", [], [], {}


def check_test(test, intent, orders, recommendations, data, raw_orders=None):
    expected = test["expect"]
    reasons = []

    if expected == "recommend":
        if intent != "recommend":
            reasons.append(f"intent={intent}≠recommend")
            return False, ", ".join(reasons)
        return True, ""

    if expected == "other":
        if intent != "other":
            reasons.append(f"intent={intent}≠other")
            return False, ", ".join(reasons)
        return True, ""

    if intent != "order":
        reasons.append(f"intent={intent}≠order")
        return False, ", ".join(reasons)

    expected_items = test.get("items", [])
    expected_count = test.get("count", 1)
    actual_items = [o.get("item", "") for o in orders]
    actual_count = len(orders)

    if actual_count != expected_count:
        reasons.append(f"count={actual_count}≠{expected_count}")
    if not all(item in actual_items for item in expected_items):
        reasons.append(f"items={actual_items}≠{expected_items}")

    if test.get("not_on_menu"):
        pass
    else:
        if any(o.get("not_on_menu") for o in orders):
            reasons.append("unexpected not_on_menu")

    null_check_orders = raw_orders if raw_orders else orders
    check_null = test.get("check_null", {})
    for field, should_be_null in check_null.items():
        if should_be_null and null_check_orders:
            val = null_check_orders[0].get(field, "MISSING")
            if val is not None:
                reasons.append(f"{field}={val}≠null")

    check_value = test.get("check_value", {})
    for field, expected_val in check_value.items():
        if orders:
            val = orders[0].get(field, "MISSING")
            if field == "sugar" and sugar_equivalent(val, expected_val):
                continue
            if val != expected_val:
                reasons.append(f"{field}={val}≠{expected_val}")

    check_orders = test.get("check_orders", [])
    if check_orders and len(orders) == len(check_orders):
        for idx, expected_order in enumerate(check_orders):
            actual = orders[idx]
            raw_actual = raw_orders[idx] if raw_orders and idx < len(raw_orders) else actual
            for field, expected_val in expected_order.items():
                if expected_val is None:
                    actual_val = raw_actual.get(field, "MISSING")
                else:
                    actual_val = actual.get(field, "MISSING")
                if field == "sugar" and expected_val is not None and sugar_equivalent(actual_val, expected_val):
                    continue
                if actual_val != expected_val:
                    reasons.append(f"order[{idx}].{field}={actual_val}≠{expected_val}")

    return len(reasons) == 0, ", ".join(reasons)


# ========== Main ==========

def main():
    print(f"Qwen3.5-4B Merged Model Evaluation")
    print(f"vLLM: {VLLM_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"測試案例: {len(ALL_TESTS)} 筆")
    print(f"{'='*60}")

    # Verify server is up
    try:
        r = requests.get(VLLM_URL.replace("/completions", "/models"), timeout=5)
        r.raise_for_status()
        print("vLLM server: OK")
    except Exception as e:
        print(f"vLLM server not reachable: {e}")
        sys.exit(1)

    category_results = {}
    total_passed = 0
    total_failed = 0
    failed_cases = []
    start_time = time.time()

    current_cat = ""
    for i, (cat, test) in enumerate(ALL_TESTS):
        if cat != current_cat:
            current_cat = cat
            if cat not in category_results:
                category_results[cat] = {"passed": 0, "total": 0}

        user_input = test["input"]
        response = generate_response(user_input)
        intent, orders, recommendations, data = parse_response(response)
        raw_orders = copy.deepcopy(orders)
        if orders:
            orders = simulate_fill_defaults(orders)
        passed, reason = check_test(test, intent, orders, recommendations, data, raw_orders=raw_orders)

        category_results[cat]["total"] += 1

        if passed:
            total_passed += 1
            category_results[cat]["passed"] += 1
            print(f"  ✓ [{cat}] {user_input[:40]}")
        else:
            total_failed += 1
            failed_cases.append({"cat": cat, "input": user_input, "reason": reason, "response": response[:300]})
            print(f"  ✗ [{cat}] {user_input[:40]} → {reason}")

    elapsed = time.time() - start_time
    total = total_passed + total_failed
    print(f"\n{'='*60}")
    print(f"結果: {total_passed}/{total} ({total_passed*100//total}%)")
    print(f"耗時: {elapsed:.1f}s ({elapsed/total:.1f}s/case)")

    print(f"\n分類結果:")
    for cat, r in category_results.items():
        status = "✓" if r["passed"] == r["total"] else "✗"
        print(f"  {status} {cat}: {r['passed']}/{r['total']}")

    if failed_cases:
        print(f"\n失敗案例:")
        for case in failed_cases:
            print(f"  [{case['cat']}] {case['input'][:50]}")
            print(f"    原因: {case['reason']}")
            print(f"    回應: {case['response'][:200]}")

    return total_passed, total


if __name__ == "__main__":
    main()
