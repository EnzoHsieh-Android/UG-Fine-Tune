#!/usr/bin/env python3
"""
Step 8: 新增多 intent 混合組合訓練樣本。
重點補強：order+recommend, recommend+order, modify+order+recommend, other+recommend
"""

import json, sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# 讀取現有 system prompt（從第一筆 train sample）
with open(DATA_DIR / "train.jsonl") as f:
    first = json.loads(f.readline())
    SYSTEM_PROMPT = next(m for m in first["messages"] if m["role"] == "system")["content"]


def make_sample(user_text: str, assistant_json: dict) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": json.dumps(assistant_json, ensure_ascii=False)},
        ]
    }


def o(item, cat, ice=None, sugar=None, size=None, addon=None, qty=1, note=""):
    """建立 order dict。"""
    return {
        "item": item, "category": cat,
        "size": size, "ice": ice, "sugar": sugar,
        "addon": addon or [], "qty": qty, "note": note,
    }


def r(item, cat, reason):
    """建立 recommendation dict。"""
    return {"item": item, "category": cat, "reason": reason}


# ============================================================
# order+recommend (點完餐再問推薦) — 18 筆
# ============================================================
ORDER_THEN_REC = [
    # 1
    make_sample("一杯琥珀鐵觀音鮮奶半糖少冰；有什麼純茶推薦", {
        "intents": ["order", "recommend"],
        "orders": [o("琥珀鐵觀音", "fresh_milk_tea", "少冰", "半糖")],
        "preferences": {"分類": "純茶"},
        "recommendations": [r("三窨十五茉", "pure_tea", "花香清雅帶甘甜")],
    }),
    # 2
    make_sample("三窨十五茉鮮奶去冰無糖；推薦果茶", {
        "intents": ["order", "recommend"],
        "orders": [o("三窨十五茉", "fresh_milk_tea", "去冰", "無糖")],
        "preferences": {"分類": "果茶"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "酸甜清爽消暑")],
    }),
    # 3
    make_sample("桂花輕烏龍奶茶半糖；有什麼花香的", {
        "intents": ["order", "recommend"],
        "orders": [o("桂花輕烏龍", "rich_milk_tea", None, "半糖")],
        "preferences": {"口味": "花香"},
        "recommendations": [r("三窨十五茉", "fresh_milk_tea", "茉莉鮮奶清香滑順")],
    }),
    # 4
    make_sample("金杯蜜香紅鮮奶大杯；推薦茶味重的", {
        "intents": ["order", "recommend"],
        "orders": [o("金杯蜜香紅", "fresh_milk_tea", None, None, "L")],
        "preferences": {"口味": "茶味重"},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "重焙鐵觀音鮮奶焙火香濃郁")],
    }),
    # 5
    make_sample("茶花紅烏龍純茶無糖去冰；有沒有酸的推薦", {
        "intents": ["order", "recommend"],
        "orders": [o("茶花紅烏龍", "pure_tea", "去冰", "無糖")],
        "preferences": {"口味": "酸"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜酸甜清爽")],
    }),
    # 6
    make_sample("蜜桃紅烏龍半糖少冰；有什麼配甜點的", {
        "intents": ["order", "recommend"],
        "orders": [o("蜜桃紅烏龍", "fruit_tea", "少冰", "半糖")],
        "preferences": {"場景": "配甜點"},
        "recommendations": [r("朱槿普洱紅", "pure_tea", "微酸回甘解膩")],
    }),
    # 7
    make_sample("一杯朱槿普洱紅鮮奶微糖去冰；推薦奶蓋", {
        "intents": ["order", "recommend"],
        "orders": [o("朱槿普洱紅", "fresh_milk_tea", "去冰", "微糖")],
        "preferences": {"分類": "奶蓋"},
        "recommendations": [r("桂花輕烏龍", "cloud_velvet", "桂花烏龍覆綿密奶蓋鹹甜交融")],
    }),
    # 8
    make_sample("米香玉露菁純茶去冰；推薦甜一點的鮮奶", {
        "intents": ["order", "recommend"],
        "orders": [o("米香玉露菁", "pure_tea", "去冰", None)],
        "preferences": {"口味": "甜", "分類": "鮮奶茶"},
        "recommendations": [r("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶天然蜜甜")],
    }),
    # 9
    make_sample("兩杯琥珀鐵觀音奶茶半糖少冰；還有其他推薦嗎", {
        "intents": ["order", "recommend"],
        "orders": [o("琥珀鐵觀音", "rich_milk_tea", "少冰", "半糖", None, [], 2)],
        "preferences": {},
        "recommendations": [r("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶蜜韻奶香溫潤")],
    }),
    # 10
    make_sample("葡柚十五茉；有什麼不甜的推薦", {
        "intents": ["order", "recommend"],
        "orders": [o("葡柚十五茉", "fruit_tea")],
        "preferences": {"口味": "不甜"},
        "recommendations": [r("朱槿普洱紅", "pure_tea", "微酸回甘解膩")],
    }),
    # 11
    make_sample("一杯桂花輕烏龍鮮奶半糖；有什麼消暑的", {
        "intents": ["order", "recommend"],
        "orders": [o("桂花輕烏龍", "fresh_milk_tea", None, "半糖")],
        "preferences": {"場景": "消暑"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "酸甜清爽消暑")],
    }),
    # 12
    make_sample("琥珀鐵觀音鮮奶L無糖去冰；推薦一下純茶", {
        "intents": ["order", "recommend"],
        "orders": [o("琥珀鐵觀音", "fresh_milk_tea", "去冰", "無糖", "L")],
        "preferences": {"分類": "純茶"},
        "recommendations": [r("桂花輕烏龍", "pure_tea", "桂花與輕發酵烏龍花果蜜韻輕柔")],
    }),
    # 13
    make_sample("茶花紅烏龍奶蓋；有什麼清爽的", {
        "intents": ["order", "recommend"],
        "orders": [o("茶花紅烏龍", "cloud_velvet")],
        "preferences": {"口味": "清爽"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜酸甜清爽")],
    }),
    # 14
    make_sample("金杯蜜香紅奶茶半糖少冰；適合送人的推薦一下", {
        "intents": ["order", "recommend"],
        "orders": [o("金杯蜜香紅", "rich_milk_tea", "少冰", "半糖")],
        "preferences": {"場景": "送人"},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
    # 15
    make_sample("三窨十五茉純茶去冰無糖；有什麼奶茶推薦", {
        "intents": ["order", "recommend"],
        "orders": [o("三窨十五茉", "pure_tea", "去冰", "無糖")],
        "preferences": {"分類": "奶茶"},
        "recommendations": [r("琥珀鐵觀音", "rich_milk_tea", "重焙鐵觀音奶茶茶韻醇厚")],
    }),
    # 16
    make_sample("一杯朱槿普洱紅純茶微糖去冰；幫我推薦鮮奶茶", {
        "intents": ["order", "recommend"],
        "orders": [o("朱槿普洱紅", "pure_tea", "去冰", "微糖")],
        "preferences": {"分類": "鮮奶茶"},
        "recommendations": [r("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶蜜韻奶香溫潤")],
    }),
    # 17
    make_sample("蜜桃紅烏龍；有什麼不苦的", {
        "intents": ["order", "recommend"],
        "orders": [o("蜜桃紅烏龍", "fruit_tea")],
        "preferences": {"排除": "苦"},
        "recommendations": [r("金杯蜜香紅", "fresh_milk_tea", "蜜香紅茶鮮奶天然蜜甜")],
    }),
    # 18
    make_sample("米香玉露菁鮮奶半糖少冰；有什麼招牌", {
        "intents": ["order", "recommend"],
        "orders": [o("米香玉露菁", "fresh_milk_tea", "少冰", "半糖")],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
]

# ============================================================
# recommend+order (問推薦後點餐) — 12 筆
# ============================================================
REC_THEN_ORDER = [
    # 1
    make_sample("有什麼推薦的；好那來一杯桂花輕烏龍鮮奶半糖少冰", {
        "intents": ["recommend", "order"],
        "orders": [r_:=None or o("桂花輕烏龍", "fresh_milk_tea", "少冰", "半糖")],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
    # 2
    make_sample("推薦一下純茶；那三窨十五茉去冰無糖", {
        "intents": ["recommend", "order"],
        "orders": [o("三窨十五茉", "pure_tea", "去冰", "無糖")],
        "preferences": {"分類": "純茶"},
        "recommendations": [r("桂花輕烏龍", "pure_tea", "桂花與輕發酵烏龍花果蜜韻輕柔")],
    }),
    # 3
    make_sample("什麼最受歡迎；來兩杯琥珀鐵觀音鮮奶半糖", {
        "intents": ["recommend", "order"],
        "orders": [o("琥珀鐵觀音", "fresh_milk_tea", None, "半糖", None, [], 2)],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
    # 4
    make_sample("有清爽一點的嗎；那青檸桂蜜少糖", {
        "intents": ["recommend", "order"],
        "orders": [o("青檸桂蜜", "fruit_tea", None, "少糖")],
        "preferences": {"口味": "清爽"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "青檸搭桂花蜜酸甜清爽消暑")],
    }),
    # 5
    make_sample("推薦花香的奶茶；好那桂花輕烏龍奶茶微糖去冰", {
        "intents": ["recommend", "order"],
        "orders": [o("桂花輕烏龍", "rich_milk_tea", "去冰", "微糖")],
        "preferences": {"口味": "花香", "分類": "奶茶"},
        "recommendations": [r("桂花輕烏龍", "rich_milk_tea", "桂花烏龍蜜韻輕柔")],
    }),
    # 6
    make_sample("不知道喝什麼好；那來杯金杯蜜香紅鮮奶半糖", {
        "intents": ["recommend", "order"],
        "orders": [o("金杯蜜香紅", "fresh_milk_tea", None, "半糖")],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
    # 7
    make_sample("有什麼果茶推薦；蜜桃紅烏龍好了半糖少冰", {
        "intents": ["recommend", "order"],
        "orders": [o("蜜桃紅烏龍", "fruit_tea", "少冰", "半糖")],
        "preferences": {"分類": "果茶"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "酸甜清爽消暑")],
    }),
    # 8
    make_sample("推薦茶味重的；那琥珀鐵觀音純茶去冰無糖", {
        "intents": ["recommend", "order"],
        "orders": [o("琥珀鐵觀音", "pure_tea", "去冰", "無糖")],
        "preferences": {"口味": "茶味重"},
        "recommendations": [r("茶花紅烏龍", "pure_tea", "重焙火紅烏龍天然花香與熟果甜韻")],
    }),
    # 9
    make_sample("有什麼奶蓋推薦；好那茶花紅烏龍奶蓋", {
        "intents": ["recommend", "order"],
        "orders": [o("茶花紅烏龍", "cloud_velvet")],
        "preferences": {"分類": "奶蓋"},
        "recommendations": [r("桂花輕烏龍", "cloud_velvet", "桂花烏龍覆綿密奶蓋鹹甜交融")],
    }),
    # 10
    make_sample("幫我選一杯不太甜的；就米香玉露菁純茶去冰", {
        "intents": ["recommend", "order"],
        "orders": [o("米香玉露菁", "pure_tea", "去冰", None)],
        "preferences": {"口味": "不太甜"},
        "recommendations": [r("朱槿普洱紅", "pure_tea", "微酸回甘解膩")],
    }),
    # 11
    make_sample("招牌是哪個；那來一杯琥珀鐵觀音鮮奶大杯半糖去冰", {
        "intents": ["recommend", "order"],
        "orders": [o("琥珀鐵觀音", "fresh_milk_tea", "去冰", "半糖", "L")],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
    # 12
    make_sample("想喝解膩的；朱槿普洱紅鮮奶微糖少冰", {
        "intents": ["recommend", "order"],
        "orders": [o("朱槿普洱紅", "fresh_milk_tea", "少冰", "微糖")],
        "preferences": {"口味": "解膩"},
        "recommendations": [r("朱槿普洱紅", "fresh_milk_tea", "洛神普洱鮮奶微酸風味獨特")],
    }),
]

# ============================================================
# order+recommend+modify / modify+order+recommend 混合 — 8 筆
# ============================================================
TRIPLE_MIX = [
    # 1: order → recommend → modify
    make_sample("一杯三窨十五茉鮮奶半糖少冰；有什麼推薦的果茶；第一杯改去冰", {
        "intents": ["order", "recommend", "modify"],
        "orders": [o("三窨十五茉", "fresh_milk_tea", "去冰", "半糖")],
        "preferences": {"分類": "果茶"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "酸甜清爽消暑")],
    }),
    # 2: order → modify → recommend
    make_sample("琥珀鐵觀音奶茶半糖少冰；改無糖；有什麼純茶推薦", {
        "intents": ["order", "modify", "recommend"],
        "orders": [o("琥珀鐵觀音", "rich_milk_tea", "少冰", "無糖")],
        "preferences": {"分類": "純茶"},
        "recommendations": [r("三窨十五茉", "pure_tea", "花香清雅帶甘甜")],
    }),
    # 3: recommend → order → modify
    make_sample("有什麼推薦；那來一杯桂花輕烏龍鮮奶半糖；改去冰", {
        "intents": ["recommend", "order", "modify"],
        "orders": [o("桂花輕烏龍", "fresh_milk_tea", "去冰", "半糖")],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
    # 4: order → recommend → order (推薦完又點)
    make_sample("茶花紅烏龍鮮奶半糖；推薦一下果茶；好加一杯青檸桂蜜", {
        "intents": ["order", "recommend", "order"],
        "orders": [o("茶花紅烏龍", "fresh_milk_tea", None, "半糖"), o("青檸桂蜜", "fruit_tea")],
        "preferences": {"分類": "果茶"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "酸甜清爽消暑")],
    }),
    # 5: order → modify → recommend → order
    make_sample("金杯蜜香紅鮮奶半糖；改大杯；推薦純茶；那加三窨十五茉去冰無糖", {
        "intents": ["order", "modify", "recommend", "order"],
        "orders": [o("金杯蜜香紅", "fresh_milk_tea", None, "半糖", "L"), o("三窨十五茉", "pure_tea", "去冰", "無糖")],
        "preferences": {"分類": "純茶"},
        "recommendations": [r("三窨十五茉", "pure_tea", "花香清雅帶甘甜")],
    }),
    # 6: other → order → recommend
    make_sample("你好；一杯琥珀鐵觀音鮮奶半糖少冰；有什麼清爽的推薦", {
        "intents": ["other", "order", "recommend"],
        "orders": [o("琥珀鐵觀音", "fresh_milk_tea", "少冰", "半糖")],
        "preferences": {"口味": "清爽"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "酸甜清爽消暑")],
    }),
    # 7: order → order → recommend
    make_sample("一杯桂花輕烏龍純茶去冰；再一杯茶花紅烏龍奶茶；有什麼果茶", {
        "intents": ["order", "order", "recommend"],
        "orders": [o("桂花輕烏龍", "pure_tea", "去冰", None), o("茶花紅烏龍", "rich_milk_tea")],
        "preferences": {"分類": "果茶"},
        "recommendations": [r("蜜桃紅烏龍", "fruit_tea", "水蜜桃果香與紅烏龍交織甜蜜芬芳")],
    }),
    # 8: recommend → modify (推薦後修改 → 不顯示推薦，但 recs 仍有值)
    make_sample("有什麼推薦；好那來桂花輕烏龍鮮奶；改無糖去冰", {
        "intents": ["recommend", "order", "modify"],
        "orders": [o("桂花輕烏龍", "fresh_milk_tea", "去冰", "無糖")],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
]

# ============================================================
# other+recommend — 7 筆
# ============================================================
OTHER_REC = [
    # 1
    make_sample("你好；推薦一下", {
        "intents": ["other", "recommend"],
        "orders": [],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
    # 2
    make_sample("請問營業到幾點；有什麼好喝的", {
        "intents": ["other", "recommend"],
        "orders": [],
        "preferences": {},
        "recommendations": [r("琥珀鐵觀音", "fresh_milk_tea", "人氣招牌焙火香濃郁")],
    }),
    # 3
    make_sample("等一下朋友；有什麼推薦的", {
        "intents": ["other", "recommend"],
        "orders": [],
        "preferences": {},
        "recommendations": [r("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶蜜韻奶香溫潤")],
    }),
    # 4
    make_sample("今天好熱；有什麼消暑的", {
        "intents": ["other", "recommend"],
        "orders": [],
        "preferences": {"場景": "消暑"},
        "recommendations": [r("青檸桂蜜", "fruit_tea", "酸甜清爽消暑")],
    }),
    # 5
    make_sample("好久沒來了；有什麼新品嗎", {
        "intents": ["other", "recommend"],
        "orders": [],
        "preferences": {},
        "recommendations": [r("茶花紅烏龍", "cloud_velvet", "紅烏龍焙火韻搭奶蓋茶香奶鹹平衡")],
    }),
    # 6
    make_sample("路過看到的；推薦適合下午茶的", {
        "intents": ["other", "recommend"],
        "orders": [],
        "preferences": {"場景": "下午茶"},
        "recommendations": [r("桂花輕烏龍", "fresh_milk_tea", "桂花烏龍鮮奶蜜韻奶香溫潤")],
    }),
    # 7
    make_sample("你們菜單好特別；有什麼推薦的純茶", {
        "intents": ["other", "recommend"],
        "orders": [],
        "preferences": {"分類": "純茶"},
        "recommendations": [r("三窨十五茉", "pure_tea", "三次窨花茉莉綠茶花香清雅帶甘甜")],
    }),
]


ALL_NEW = ORDER_THEN_REC + REC_THEN_ORDER + TRIPLE_MIX + OTHER_REC


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"新增 {len(ALL_NEW)} 筆混合組合樣本")
    print(f"  order+recommend: {len(ORDER_THEN_REC)}")
    print(f"  recommend+order: {len(REC_THEN_ORDER)}")
    print(f"  三方混合: {len(TRIPLE_MIX)}")
    print(f"  other+recommend: {len(OTHER_REC)}")

    # 驗證
    errors = 0
    for i, s in enumerate(ALL_NEW):
        asst = json.loads(s["messages"][2]["content"])
        intents = asst.get("intents", [])
        user = s["messages"][1]["content"]
        segments = user.split(";") if ";" in user else user.split("；")

        if len(intents) != len(segments):
            print(f"  [ERROR] #{i+1}: intents={len(intents)} != segments={len(segments)}")
            errors += 1
        for intent in intents:
            if intent not in ("order", "recommend", "modify", "other"):
                print(f"  [ERROR] #{i+1}: invalid intent '{intent}'")
                errors += 1
        if "recommend" in intents and not asst.get("recommendations"):
            print(f"  [ERROR] #{i+1}: recommend intent but no recs")
            errors += 1

    if errors:
        print(f"\n{errors} 個驗證錯誤，停止")
        return

    print("驗證通過 ✓")

    if not dry_run:
        filepath = DATA_DIR / "train.jsonl"
        with open(filepath, "a") as f:
            for s in ALL_NEW:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"已追加到: {filepath}")
    else:
        print("[DRY RUN] 不寫入")

    # 顯示前 5 筆
    print("\n--- 範例 ---")
    for s in ALL_NEW[:5]:
        user = s["messages"][1]["content"]
        asst = json.loads(s["messages"][2]["content"])
        print(f"  user: {user}")
        print(f"  intents: {asst['intents']}")
        orders = [o_["item"] for o_ in asst.get("orders", [])]
        recs = [r_["item"] for r_ in asst.get("recommendations", [])]
        print(f"  orders: {orders}, recs: {recs}")
        print()


if __name__ == "__main__":
    main()
