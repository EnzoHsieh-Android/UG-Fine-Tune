#!/usr/bin/env python3
"""批次測試 7 個案例"""
import subprocess, json, sys

SYSTEM_PROMPT = (
    "你是 No.315 Unique Green 的點單助手。根據顧客的自然語言，輸出 JSON 格式的訂單。\n\n"
    "菜單分類：研選純茶(pure_tea)、牧場直達(fresh_milk_tea)、UG奶茶(rich_milk_tea)、果香四溢(fruit_tea)、雲頂奶蓋(cloud_velvet)。\n\n"
    "純茶為單一尺寸；鮮奶茶、UG奶茶、雲頂奶蓋有 M/L；果香四溢僅供冷飲。\n"
    "加料：紅烏龍茶凍(+15)、燕麥粒(+15)。\n"
    "甜度：正常糖/少糖/半糖/微糖/無糖。冰量：正常冰/少冰/微冰/去冰/熱飲。\n"
    "未指定甜度或冰量時設為 null，由店員確認。未指定尺寸的鮮奶茶/奶茶預設 M。\n"
    "若品項不在菜單上，回傳 not_on_menu 欄位。\n\n"
    '輸出格式：{"orders":[{"item":"品名","category":"分類","size":"M/L/null","ice":"冰量/null","sugar":"甜度/null","addon":[],"qty":1,"note":""}]}'
)

MODEL = "model/Qwen3-4B-UG-order-v4"

TESTS = [
    ("Test 1 Off-topic", "廁所在哪裡？"),
    ("Test 7 Modification", "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：第一杯改微糖"),
    ("Test 8 Chitchat→Order", "顧客：你們幾點關門？\n顧客：那來一杯桂花輕烏龍鮮奶半糖少冰"),
    ("Test 9 Abbreviation", "茉莉鮮奶不要糖不要冰"),
    ("Test 10 Mixed not_on_menu", "一杯珍珠奶茶，一杯鐵觀音鮮奶半糖少冰"),
    ("Test 11 Cancel", "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：第二杯不要了"),
    ("Test 12 Confirmation", "就這樣"),
]

def run_test(name, user_input):
    prompt = (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_input}<|im_end|>\n"
        f"<|im_start|>assistant\n/no_think\n"
    )
    result = subprocess.run(
        [".venv/bin/python3", "-m", "mlx_lm.generate",
         "--model", MODEL,
         "--max-tokens", "512",
         "--prompt", prompt],
        capture_output=True, text=True, timeout=120
    )
    output = result.stdout
    # 從輸出中提取生成的文字（去掉 prompt echo）
    lines = output.strip().split("\n")
    # 找到 ==========  之後的內容
    gen_text = ""
    capture = False
    for line in lines:
        if "==========" in line:
            capture = True
            continue
        if capture:
            gen_text += line + "\n"
    gen_text = gen_text.strip()
    # 去掉 prompt 部分和特殊 token
    if "<|im_end|>" in gen_text:
        gen_text = gen_text.split("<|im_end|>")[0]
    return gen_text


print(f"模型: {MODEL}\n")
for name, user_input in TESTS:
    print(f"{'='*60}")
    print(f"[{name}]")
    print(f"  輸入: {user_input[:60]}...")
    try:
        output = run_test(name, user_input)
        print(f"  輸出: {output[:300]}")
        # 簡單檢查
        if name == "Test 10 Mixed not_on_menu":
            if "not_on_menu" in output:
                print("  ✅ 包含 not_on_menu")
            else:
                print("  ❌ 缺少 not_on_menu")
        if name == "Test 11 Cancel":
            if "桂花" not in output or output.count("orders") > 0:
                orders_text = output
                try:
                    parsed = json.loads(orders_text)
                    items = [o.get("item","") for o in parsed.get("orders",[])]
                    if "桂花輕烏龍" not in items and len(items) == 1:
                        print("  ✅ 成功取消第二杯")
                    else:
                        print(f"  ❌ 取消失敗: {items}")
                except:
                    pass
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
    print()
