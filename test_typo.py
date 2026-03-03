#!/usr/bin/env python3
"""錯別字/語音轉文字偏誤測試"""
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
    # === 品名同音/近音字 ===
    ("T01 三窨→三因", "三因十五茉鮮奶半糖少冰",
     "期望: item=三窨十五茉"),
    ("T02 三窨→三蔭", "三蔭十五茉鮮奶半糖少冰",
     "期望: item=三窨十五茉"),
    ("T03 三窨→三印", "三印十五茉鮮奶去冰無糖",
     "期望: item=三窨十五茉"),
    ("T04 琥珀→湖泊", "湖泊鐵觀音鮮奶半糖少冰",
     "期望: item=琥珀鐵觀音"),
    ("T05 琥珀→虎魄", "虎魄鐵觀音奶茶微糖去冰",
     "期望: item=琥珀鐵觀音"),
    ("T06 朱槿→珠槿", "珠槿普洱紅純茶去冰無糖",
     "期望: item=朱槿普洱紅"),
    ("T07 朱槿→朱瑾", "朱瑾普洱紅去冰無糖",
     "期望: item=朱槿普洱紅"),
    ("T08 米香→迷香", "迷香玉露菁鮮奶半糖少冰",
     "期望: item=米香玉露菁"),
    ("T09 玉露菁→玉露青", "米香玉露青鮮奶半糖少冰",
     "期望: item=米香玉露菁"),
    ("T10 蜜桃→密桃", "密桃紅烏龍少冰半糖",
     "期望: item=蜜桃紅烏龍"),
    ("T11 葡柚→葡油", "葡油十五茉少冰半糖",
     "期望: item=葡柚十五茉"),
    ("T12 青檸→清檸", "清檸桂蜜少冰半糖",
     "期望: item=青檸桂蜜"),
    ("T13 燕麥→燕賣", "鐵觀音鮮奶半糖少冰加燕賣",
     "期望: addon=燕麥粒"),
    ("T14 桂花→貴花", "貴花輕烏龍鮮奶半糖少冰",
     "期望: item=桂花輕烏龍"),

    # === 甜度/冰量同音 ===
    ("T15 半糖→伴糖", "三窨十五茉鮮奶伴糖少冰",
     "期望: sugar=半糖"),
    ("T16 微糖→為糖", "鐵觀音鮮奶為糖少冰",
     "期望: sugar=微糖"),
    ("T17 去冰→趣冰", "桂花輕烏龍鮮奶半糖趣冰",
     "期望: ice=去冰"),
    ("T18 微冰→為冰", "三窨十五茉鮮奶半糖為冰",
     "期望: ice=微冰"),

    # === Whisper 常見斷詞錯誤 ===
    ("T19 紅烏龍→紅烏隆", "桂花輕烏龍鮮奶半糖少冰加紅烏隆茶凍",
     "期望: addon=紅烏龍茶凍"),
    ("T20 鐵觀音→鐵觀因", "鐵觀因鮮奶半糖少冰",
     "期望: item=琥珀鐵觀音"),
    ("T21 茶花→插花(極端)", "插花烏龍鮮奶半糖少冰",
     "期望: item=茶花烏龍 或 not_on_menu"),

    # === 多字混合錯誤 ===
    ("T22 多錯混合", "三因十五茉鮮奶伴糖少冰加燕賣",
     "期望: item=三窨十五茉, sugar=半糖, addon=燕麥粒"),
    ("T23 口語+錯字", "湖泊鐵觀音奶茶不要太甜少一點冰",
     "期望: item=琥珀鐵觀音"),

    # === 數量詞誤聽 ===
    ("T24 兩杯→涼杯", "涼杯三窨十五茉鮮奶半糖少冰",
     "期望: qty=2 或 qty=1（涼杯不明確）"),
    ("T25 三杯→散杯", "散杯桂花輕烏龍鮮奶半糖少冰",
     "期望: qty=3 或 qty=1"),
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
    if gen_text.startswith("<think>"):
        idx = gen_text.find("</think>")
        if idx != -1:
            gen_text = gen_text[idx + len("</think>"):].strip()
    return gen_text


print(f"模型: {MODEL}")
print(f"測試案例: {len(TESTS)} 個")
print(f"場景: 語音轉文字 (STT) 錯別字容錯測試\n")

for name, user_input, expect in TESTS:
    print(f"{'─'*60}")
    print(f"[{name}]")
    print(f"  輸入: {user_input}")
    print(f"  {expect}")
    try:
        output = run_test(user_input)
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
