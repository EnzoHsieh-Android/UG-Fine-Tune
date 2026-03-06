#!/usr/bin/env python3
"""RunPod A40 雲端 LoRA 訓練 + 評估腳本。

在 RunPod pod 上執行：安裝環境 → 訓練 → 評估 checkpoint → 輸出最佳 adapter

用法：
  python3 cloud_train_runpod.py
  python3 cloud_train_runpod.py --max-steps 800
  python3 cloud_train_runpod.py --eval-only
"""

import subprocess
import sys
import os
import json
import copy
import glob
import shutil
import argparse
import re
import traceback


# === Auto-install dependencies ===
def install_deps():
    print("=== 安裝依賴 ===")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                          stdout=subprocess.DEVNULL)
    # 先清理舊版 torch 相關包，避免新舊版共存撐爆 disk/RAM
    print("  清理舊版 PyTorch...")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y",
                    "torch", "torchvision", "torchaudio", "triton", "xformers"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("  安裝 unsloth + 依賴...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "unsloth", "bitsandbytes"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets", "safetensors"])
    # Qwen3.5 需要最新 transformers（model_type=qwen3_5 尚未在穩定版中）
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                          "git+https://github.com/huggingface/transformers.git"])
    print("安裝完成\n")


try:
    from unsloth import FastLanguageModel
    from trl import SFTTrainer, SFTConfig
    from datasets import load_dataset
    import safetensors.torch as st
except ImportError:
    install_deps()
    from unsloth import FastLanguageModel
    from trl import SFTTrainer, SFTConfig
    from datasets import load_dataset
    import safetensors.torch as st

import torch
from peft import set_peft_model_state_dict


# ==================== 配置 ====================

BASE_MODEL = "Qwen/Qwen3.5-9B"
MAX_SEQ_LENGTH = 2048
OUTPUT_DIR = "adapters-runpod"
DATA_DIR = "data"


# ==================== System Prompt（與 llm.go 完全一致）====================

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


# ==================== 後端甜度映射 ====================

SUGAR_BACKEND_MAP = {
    "正常糖": "全糖",
    "半糖": "五分糖",
    "少糖": "五分糖",
    "微糖": "三分糖",
}


def sugar_equivalent(actual, expected):
    """比較甜度值是否功能等價（經後端映射後結果相同）。"""
    if actual == expected:
        return True
    return SUGAR_BACKEND_MAP.get(actual, actual) == SUGAR_BACKEND_MAP.get(expected, expected)


# ==================== 測試案例（與 eval_checkpoints_direct.py 完全同步）====================

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


# ==================== 後端 fillDefaults 模擬 ====================

MENU_CATEGORIES = {
    "pure_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "朱槿普洱紅", "米香玉露菁"],
    "fresh_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "rich_milk_tea": ["三窨十五茉", "桂花輕烏龍", "茶花紅烏龍", "琥珀鐵觀音", "金杯蜜香紅", "朱槿普洱紅", "米香玉露菁"],
    "fruit_tea": ["青檸桂蜜", "蜜桃紅烏龍", "葡柚十五茉"],
    "cloud_velvet": ["桂花輕烏龍", "茶花紅烏龍"],
}

ITEM_CATEGORIES = {}
for _cat, _items in MENU_CATEGORIES.items():
    for _item in _items:
        ITEM_CATEGORIES.setdefault(_item, []).append(_cat)

CATEGORY_PRIORITY = ["pure_tea", "rich_milk_tea"]


def is_valid_item_category(item_name, category_id):
    return item_name in MENU_CATEGORIES.get(category_id, [])


def get_default_category(item_name):
    cats = ITEM_CATEGORIES.get(item_name, [])
    if not cats:
        return None
    for p in CATEGORY_PRIORITY:
        if p in cats:
            return p
    return cats[0]


def simulate_fill_defaults(orders):
    """模擬後端 fillDefaults — 回傳新 list，不修改原始 orders。"""
    result = []
    for order in orders:
        item = order.get("item", "")
        cat = order.get("category")
        if cat is None or not is_valid_item_category(item, cat):
            default = get_default_category(item)
            if default:
                order = {**order, "category": default}
        result.append(order)
    return result


# ==================== 推論 + 評估 ====================

def generate_response(model, tokenizer, user_input):
    """GPU 推論（替代本地 MLX 的 mlx_lm.generate）。
    手動構造 prompt，繞過 Qwen3.5 VLM tokenizer 的 image processor。
    使用底層 text tokenizer 避免觸發 VLM processor。
    """
    text = (
        "<|im_start|>system\n" + SYSTEM_PROMPT + "<|im_end|>\n"
        "<|im_start|>user\n" + user_input + "<|im_end|>\n"
        "<|im_start|>assistant\n/no_think\n"
    )
    # 取得底層 text tokenizer（避免 VLM processor 把文字當圖片處理）
    text_tok = getattr(tokenizer, 'tokenizer', tokenizer)
    inputs = text_tok(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=text_tok.eos_token_id,
        )
    response = text_tok.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    response = re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL)
    return response.strip()


def parse_response(response):
    """Parse JSON, derive intent from intents array or fallback to content."""
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


def check_test(test, intent, orders, recommendations, raw_orders=None):
    """Check a single test case, return (passed, reason)."""
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

    if not test.get("not_on_menu"):
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


def run_eval(model, tokenizer):
    """執行全部測試案例。"""
    category_results = {}
    total_passed = 0
    total_failed = 0
    failed_cases = []

    for cat, test in ALL_TESTS:
        if cat not in category_results:
            category_results[cat] = {"passed": 0, "total": 0}

        response = generate_response(model, tokenizer, test["input"])
        intent, orders, recommendations, _ = parse_response(response)
        raw_orders = orders
        if orders:
            orders = simulate_fill_defaults(orders)
        passed, reason = check_test(test, intent, orders, recommendations, raw_orders=raw_orders)

        category_results[cat]["total"] += 1
        if passed:
            total_passed += 1
            category_results[cat]["passed"] += 1
            print(f"  ✓ [{cat}] {test['input'][:35]}")
        else:
            total_failed += 1
            failed_cases.append({"cat": cat, "input": test["input"], "reason": reason, "response": response[:200]})
            print(f"  ✗ [{cat}] {test['input'][:35]} → {reason}")

    total = total_passed + total_failed
    return total_passed, total, category_results, failed_cases


# ==================== 訓練 ====================

def do_train(args):
    """載入模型 → 配置 LoRA → 訓練。"""
    use_8bit = not getattr(args, 'fp16', False)
    precision_str = "8-bit QLoRA" if use_8bit else "FP16 全精度"
    print(f"=== 載入模型 ({precision_str}) ===")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=False,
        load_in_8bit=use_8bit,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id

    # Qwen3.5-9B: 32 layers (24 DeltaNet + 8 Full Attention)
    # 方案 A: LoRA 只作用於 Full Attention (8層) + MLP (32層)
    # DeltaNet 層的 in_proj_qkv/in_proj_z 等用不同名稱，不會被命中
    print("=== 配置 LoRA (rank=32, alpha=64, all 32 layers MLP + 8 attn layers) ===")
    model = FastLanguageModel.get_peft_model(
        model,
        r=32,
        lora_alpha=64,
        lora_dropout=0.05,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
        max_seq_length=MAX_SEQ_LENGTH,
    )

    print("=== 載入資料 ===")
    dataset = load_dataset("json", data_files={
        "train": f"{DATA_DIR}/train.jsonl",
        "validation": f"{DATA_DIR}/valid.jsonl",
    })
    print(f"  train: {len(dataset['train'])} 筆, validation: {len(dataset['validation'])} 筆")

    def formatting_func(examples):
        """手動構造 chat format，繞過 Qwen3.5 VLM tokenizer 的 image processor。"""
        texts = []
        for convo in examples["messages"]:
            parts = []
            for msg in convo:
                parts.append(f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n")
            texts.append("".join(parts))
        return {"text": texts}

    dataset = dataset.map(formatting_func, batched=True, num_proc=2)

    print("=== 訓練配置 ===")
    print(f"  max_steps={args.max_steps}, batch=4, grad_accum=2, effective_batch=8")
    print(f"  lr=1e-5, scheduler=cosine, warmup=10%, save_every={args.save_steps}")

    sft_config = SFTConfig(
        output_dir=OUTPUT_DIR,
        max_steps=args.max_steps,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        learning_rate=1e-5,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        weight_decay=0.01,
        optim="adamw_8bit",
        save_steps=args.save_steps,
        logging_steps=10,
        eval_steps=args.save_steps,
        eval_strategy="steps",
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        seed=42,
        packing=False,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=sft_config,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_text_field="text",
    )

    # mask prompt: 只在 assistant 回應上計算 loss
    _train_on_responses = None
    try:
        from unsloth.chat_templates import train_on_responses_only_trainer as _train_on_responses
    except ImportError:
        try:
            from unsloth import train_on_responses_only as _train_on_responses
        except ImportError:
            pass

    if _train_on_responses is not None:
        trainer = _train_on_responses(
            trainer,
            instruction_part="<|im_start|>user\n",
            response_part="<|im_start|>assistant\n",
        )
        print("  mask_prompt: enabled")
    else:
        print("  WARNING: mask_prompt disabled — loss 會計算在 prompt tokens 上")

    # 檢查是否有已存在的 checkpoint（SSH 斷線後重連 resume 用）
    existing_checkpoints = sorted(
        glob.glob(f"{OUTPUT_DIR}/checkpoint-*"),
        key=lambda x: int(os.path.basename(x).split("-")[-1])
    )
    if existing_checkpoints:
        last_cp = existing_checkpoints[-1]
        last_step = int(os.path.basename(last_cp).split("-")[-1])
        print(f"\n=== 從 checkpoint-{last_step} 恢復訓練 ===")
        trainer.train(resume_from_checkpoint=last_cp)
    else:
        print("\n=== 開始訓練 ===")
        trainer.train()
    print("訓練完成\n")

    return model, tokenizer


# ==================== Checkpoint 評估 ====================

def evaluate_checkpoints(model, tokenizer):
    """評估所有 checkpoint，找出最佳。"""
    checkpoints = sorted(
        glob.glob(f"{OUTPUT_DIR}/checkpoint-*"),
        key=lambda x: int(os.path.basename(x).split("-")[-1])
    )
    if not checkpoints:
        print("找不到 checkpoint")
        return None

    print(f"\n=== 評估 {len(checkpoints)} 個 checkpoints ({len(ALL_TESTS)} test cases) ===")

    device = str(next(model.parameters()).device)
    results = {}

    for cp_path in checkpoints:
        cp_name = os.path.basename(cp_path)
        step = int(cp_name.split("-")[-1])
        print(f"\n{'='*50}")
        print(f"Checkpoint: {cp_name} (step {step})")
        print(f"{'='*50}")

        adapter_file = os.path.join(cp_path, "adapter_model.safetensors")
        if not os.path.exists(adapter_file):
            print(f"  跳過（找不到 adapter_model.safetensors）")
            continue

        try:
            state_dict = st.load_file(adapter_file, device=device)
            set_peft_model_state_dict(model, state_dict)
        except (OSError, RuntimeError, ValueError) as e:
            print(f"  載入 adapter 失敗: {e}")
            traceback.print_exc()
            continue

        model.eval()
        passed, total, cat_results, failed = run_eval(model, tokenizer)
        pct = passed * 100 // total if total > 0 else 0

        results[cp_name] = {
            "step": step,
            "passed": passed,
            "total": total,
            "pct": pct,
            "categories": {c: {"passed": r["passed"], "total": r["total"]} for c, r in cat_results.items()},
            "failed": [{"cat": f["cat"], "input": f["input"], "reason": f["reason"]} for f in failed],
        }
        print(f"\n結果: {passed}/{total} ({pct}%)")

    if not results:
        print("沒有可用的 checkpoint 結果")
        return None

    # 找最佳（同分數取較早 step）
    best_name = max(results, key=lambda k: (results[k]["passed"], -results[k]["step"]))
    best = results[best_name]

    # 複製最佳到 best/
    best_dir = os.path.join(OUTPUT_DIR, "best")
    src_dir = os.path.join(OUTPUT_DIR, best_name)
    if os.path.exists(best_dir):
        shutil.rmtree(best_dir)
    shutil.copytree(src_dir, best_dir)

    # 儲存評估結果（含失敗案例供除錯）
    eval_output = {
        "best": best_name,
        "best_score": f"{best['passed']}/{best['total']}",
        "results": {
            k: {
                "step": v["step"], "passed": v["passed"],
                "total": v["total"], "pct": v["pct"],
                "failed": v["failed"][:10],
            }
            for k, v in sorted(results.items(), key=lambda x: x[1]["step"])
        }
    }
    eval_path = os.path.join(OUTPUT_DIR, "eval_results.json")
    with open(eval_path, "w") as f:
        json.dump(eval_output, f, indent=2, ensure_ascii=False)

    # 總結
    print(f"\n{'='*60}")
    print("評估結果總結")
    print(f"{'='*60}")
    for name, data in sorted(results.items(), key=lambda x: x[1]["step"]):
        cats = " | ".join(f"{c}:{r['passed']}/{r['total']}" for c, r in data["categories"].items())
        marker = " ← BEST" if name == best_name else ""
        print(f"  step {data['step']:4d}: {data['passed']}/{data['total']} ({data['pct']}%)  [{cats}]{marker}")

    # 過擬合分析
    sorted_results = sorted(results.items(), key=lambda x: x[1]["step"])
    if len(sorted_results) > 1:
        print(f"\n過擬合分析:")
        for i in range(1, len(sorted_results)):
            prev_name, prev = sorted_results[i-1]
            curr_name, curr = sorted_results[i]
            delta = curr["passed"] - prev["passed"]
            prev_gen = prev["categories"].get("泛化", {}).get("passed", 0)
            curr_gen = curr["categories"].get("泛化", {}).get("passed", 0)
            marker = ""
            if curr_gen < prev_gen:
                marker = " ⚠ 泛化下降"
            print(f"  step {prev['step']}→{curr['step']}: 總分 {delta:+d}, 泛化 {curr_gen-prev_gen:+d}{marker}")

    print(f"\n🏆 最佳: {best_name} ({best['passed']}/{best['total']}, {best['pct']}%)")
    print(f"已複製到: {best_dir}")
    print(f"評估結果: {eval_path}")

    return best_name


# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(description="RunPod A40 雲端 LoRA 訓練 + 評估")
    parser.add_argument("--max-steps", type=int, default=1000, help="最大訓練步數 (default: 1000)")
    parser.add_argument("--save-steps", type=int, default=100, help="Checkpoint 儲存間隔 (default: 100)")
    parser.add_argument("--eval-only", action="store_true", help="只跑評估，不訓練")
    parser.add_argument("--train-only", action="store_true", help="只跑訓練，不評估（先下載再評估）")
    parser.add_argument("--model", type=str, default=None, help="HuggingFace 模型名稱 (覆蓋 BASE_MODEL)")
    parser.add_argument("--fp16", action="store_true", help="全精度 FP16 訓練（不量化）")
    args = parser.parse_args()

    # 允許命令列覆蓋模型
    global BASE_MODEL
    if args.model:
        BASE_MODEL = args.model

    print(f"RunPod 雲端 LoRA 訓練腳本")
    print(f"  Model: {BASE_MODEL}")
    print(f"  Test cases: {len(ALL_TESTS)}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print()

    if args.eval_only:
        use_8bit = not getattr(args, 'fp16', False)
        precision_str = "8-bit" if use_8bit else "FP16"
        print(f"=== Eval-only mode ({precision_str}) ===")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=BASE_MODEL,
            max_seq_length=MAX_SEQ_LENGTH,
            load_in_4bit=False,
            load_in_8bit=use_8bit,
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token_id = tokenizer.eos_token_id
        # 建立 PEFT 結構（與訓練相同配置）
        model = FastLanguageModel.get_peft_model(
            model,
            r=32,
            lora_alpha=64,
            lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
            max_seq_length=MAX_SEQ_LENGTH,
        )
        evaluate_checkpoints(model, tokenizer)
    elif args.train_only:
        print("=== Train-only mode（訓練完不評估，先下載 checkpoint）===")
        model, tokenizer = do_train(args)
        print("\n訓練完成！Checkpoint 已儲存，請先下載再跑 --eval-only")
    else:
        model, tokenizer = do_train(args)
        evaluate_checkpoints(model, tokenizer)

    print("\n=== 完成 ===")
    print("後續步驟：")
    print("  1. 下載 adapters-runpod/best/ 到本地")
    print("  2. PEFT merge → fix config.json → MLX 量化")
    print("     同 Together AI 已驗證的 pipeline")


if __name__ == "__main__":
    main()
