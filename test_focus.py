#!/usr/bin/env python3
"""聚焦測試：重點看不穩定的場景"""
import subprocess, json

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

def run(user_input):
    prompt = (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_input}<|im_end|>\n"
        f"<|im_start|>assistant\n/no_think\n"
    )
    r = subprocess.run(
        [".venv/bin/python3", "-m", "mlx_lm.generate",
         "--model", "model/Qwen3-4B-UG-order-v4",
         "--max-tokens", "512", "--prompt", prompt],
        capture_output=True, text=True, timeout=120)
    out = r.stdout
    cap = False
    gen = ""
    for l in out.strip().split("\n"):
        if "========" in l:
            cap = True
            continue
        if cap:
            gen += l + "\n"
    gen = gen.strip()
    if "<|im_end|>" in gen:
        gen = gen.split("<|im_end|>")[0]
    if gen.startswith("<think>"):
        i = gen.find("</think>")
        if i >= 0:
            gen = gen[i+8:].strip()
    # 只取第一個 JSON 物件
    if "{" in gen:
        start = gen.index("{")
        depth = 0
        for idx, c in enumerate(gen[start:], start):
            if c == "{": depth += 1
            elif c == "}": depth -= 1
            if depth == 0:
                gen = gen[start:idx+1]
                break
    return gen

def fmt(output):
    try:
        p = json.loads(output)
        items = []
        for o in p.get("orders", []):
            if o.get("not_on_menu"):
                items.append(f"❗{o['item']}")
            else:
                s = o.get("item", "?")
                if o.get("size"):
                    s += f"({o['size']})"
                parts = []
                if o.get("sugar"):
                    parts.append(o["sugar"])
                if o.get("ice"):
                    parts.append(o["ice"])
                if parts:
                    s += " " + "/".join(parts)
                if o.get("addon"):
                    s += " +" + "+".join(o["addon"])
                if o.get("note"):
                    s += " 📝"
                items.append(s)
        r = " | ".join(items) if items else "(空單)"
        if p.get("note"):
            r += f"  📝{p['note'][:25]}"
        return r
    except:
        return output[:100]

tests = [
    ("", "── 同品不同規格 ──"),
    ("C1 不同甜度", "兩杯鐵觀音鮮奶少冰，一杯半糖一杯無糖"),
    ("C2 不同冰量", "兩杯三窨十五茉鮮奶半糖，一杯少冰一杯去冰"),
    ("C3 不同尺寸", "兩杯桂花輕烏龍鮮奶半糖少冰，一杯大杯一杯中杯"),
    ("C4 甜冰都不同", "兩杯鐵觀音鮮奶，一杯半糖少冰一杯無糖去冰"),
    ("C5 三杯不對稱", "三杯三窨十五茉鮮奶少冰，兩杯半糖一杯無糖"),

    ("", "── 取消 ──"),
    ("E1 取消第二杯", "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：第二杯不要了"),
    ("E2 取消第一杯", "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：鐵觀音奶茶微糖去冰\n顧客：第一杯不要了"),
    ("E3 品名取消", "顧客：鐵觀音鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：鐵觀音不要了"),
    ("E4 全部取消", "顧客：三窨十五茉鮮奶半糖少冰\n顧客：算了都不要了"),
    ("E5 取消加新", "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：那杯不要了\n顧客：改一杯鐵觀音鮮奶微糖去冰"),

    ("", "── not_on_menu ──"),
    ("F1 珍奶單點", "一杯珍珠奶茶"),
    ("F2 珍奶+正常", "一杯珍珠奶茶，一杯鐵觀音鮮奶半糖少冰"),
    ("F3 拿鐵+正常", "一杯拿鐵，一杯三窨十五茉鮮奶半糖少冰"),
    ("F4 多多綠+正常", "一杯多多綠，一杯桂花輕烏龍鮮奶半糖少冰"),
    ("F5 改點", "顧客：來杯拿鐵\n顧客：沒有喔？那三窨十五茉鮮奶半糖少冰"),
    ("F6 兩個不在", "一杯珍珠奶茶，一杯拿鐵"),

    ("", "── 非菜單加料 ──"),
    ("G1 加珍珠", "三窨十五茉鮮奶半糖少冰加珍珠"),
    ("G2 加椰果", "鐵觀音鮮奶半糖少冰加椰果"),
    ("G3 加布丁", "桂花輕烏龍奶茶半糖少冰加布丁"),
    ("G4 茶凍+珍珠", "鐵觀音鮮奶半糖少冰加茶凍加珍珠"),

    ("", "── 非點餐 ──"),
    ("H1 問廁所", "廁所在哪裡？"),
    ("H2 問營業", "你們幾點關門？"),
    ("H3 問推薦", "你們什麼最好喝？"),
    ("H4 問價格", "鐵觀音鮮奶多少錢？"),
]

for name, inp in tests:
    if not name:
        print(f"\n{inp}")
        continue
    out = run(inp)
    s = fmt(out)
    print(f"  [{name}] → {s}")
