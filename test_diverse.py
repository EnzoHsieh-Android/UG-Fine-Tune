#!/usr/bin/env python3
"""多樣性測試：涵蓋更多邊界情境"""
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
    # === 基本點單 ===
    ("D1 純茶基本", "桂花輕烏龍純茶去冰無糖"),
    ("D2 鮮奶大杯", "大杯琥珀鐵觀音鮮奶半糖少冰"),
    ("D3 奶茶+加料", "三窨十五茉奶茶半糖少冰加茶凍"),
    ("D4 熱飲", "桂花輕烏龍鮮奶微糖熱飲"),

    # === 多杯 ===
    ("D5 兩杯同品不同規格", "兩杯鐵觀音鮮奶，一杯半糖一杯無糖，都少冰"),
    ("D6 三杯不同品項", "一杯三窨十五茉純茶去冰無糖，一杯桂花輕烏龍鮮奶半糖少冰，一杯琥珀鐵觀音奶茶微糖微冰"),
    ("D7 幫同事點", "幫我點三杯桂花輕烏龍奶茶半糖少冰，都要大杯"),

    # === 加料變化 ===
    ("D8 雙加料", "鐵觀音鮮奶半糖少冰，茶凍和燕麥粒都加"),
    ("D9 不在菜單的加料", "三窨十五茉鮮奶半糖少冰加珍珠"),

    # === 修改場景 ===
    ("D10 改甜度+冰量", "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：改無糖去冰"),
    ("D11 改尺寸", "顧客：鐵觀音鮮奶半糖少冰\n顧客：改大杯"),
    ("D12 改品項", "顧客：三窨十五茉鮮奶半糖少冰\n顧客：換桂花輕烏龍好了，其他一樣"),
    ("D13 改類別", "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：不要鮮奶改純茶"),

    # === not_on_menu 各種 ===
    ("D14 咖啡", "來一杯拿鐵"),
    ("D15 波霸紅茶+正常品項", "一杯波霸紅茶，一杯金杯蜜香紅鮮奶半糖少冰"),
    ("D16 綠茶", "一杯綠茶半糖少冰"),
    ("D17 not_on_menu後改點", "顧客：來杯拿鐵\n顧客：沒有喔？那三窨十五茉鮮奶半糖少冰"),

    # === 取消 ===
    ("D18 用品名取消", "顧客：鐵觀音鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：鐵觀音不要了"),
    ("D19 全部取消", "顧客：三窨十五茉鮮奶半糖少冰\n顧客：算了都不要了"),

    # === 閒聊/非點餐 ===
    ("D20 問價格", "鐵觀音鮮奶多少錢？"),
    ("D21 問推薦", "你們什麼最好喝？"),
    ("D22 閒聊+點餐+確認", "顧客：今天好熱喔\n顧客：來杯桂花輕烏龍鮮奶半糖少冰\n顧客：就這樣"),

    # === 模糊/口語 ===
    ("D23 極簡口語", "鐵觀音奶茶"),
    ("D24 口語甜冰", "茉莉鮮奶不要太甜少一點冰"),
    ("D25 數量詞變化", "茉莉純茶去冰無糖來兩杯"),
]

def run_test(user_input):
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
    lines = output.strip().split("\n")
    gen_text = ""
    capture = False
    for line in lines:
        if "==========" in line:
            capture = True
            continue
        if capture:
            gen_text += line + "\n"
    gen_text = gen_text.strip()
    if "<|im_end|>" in gen_text:
        gen_text = gen_text.split("<|im_end|>")[0]
    # 去掉 <think>\n\n</think>\n\n 前綴
    if gen_text.startswith("<think>"):
        idx = gen_text.find("</think>")
        if idx != -1:
            gen_text = gen_text[idx + len("</think>"):].strip()
    return gen_text


print(f"模型: {MODEL}")
print(f"測試案例: {len(TESTS)} 個\n")

for name, user_input in TESTS:
    print(f"{'─'*60}")
    print(f"[{name}]")
    print(f"  輸入: {user_input}")
    try:
        output = run_test(user_input)
        # 嘗試格式化 JSON
        try:
            parsed = json.loads(output)
            formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
            for line in formatted.split("\n"):
                print(f"  {line}")
        except:
            print(f"  輸出: {output}")
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
    print()
