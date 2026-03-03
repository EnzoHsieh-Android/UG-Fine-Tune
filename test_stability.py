#!/usr/bin/env python3
"""穩定性測試：每個場景多個變化，檢查哪些場景穩定、哪些不穩"""
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

TESTS = {
    # ─── A. 基本點單 ───
    "基本點單": [
        ("A1 鮮奶基本", "三窨十五茉鮮奶半糖少冰"),
        ("A2 純茶", "桂花輕烏龍純茶去冰無糖"),
        ("A3 奶茶大杯", "大杯琥珀鐵觀音奶茶微糖去冰"),
        ("A4 熱飲", "三窨十五茉鮮奶微糖熱飲"),
        ("A5 加茶凍", "桂花輕烏龍鮮奶半糖少冰加茶凍"),
        ("A6 加燕麥粒", "鐵觀音奶茶半糖少冰加燕麥粒"),
        ("A7 雙加料", "三窨十五茉鮮奶半糖少冰加茶凍加燕麥粒"),
    ],

    # ─── B. 多杯點單 ───
    "多杯點單": [
        ("B1 兩杯不同品", "一杯三窨十五茉鮮奶半糖少冰，一杯桂花輕烏龍純茶去冰無糖"),
        ("B2 三杯不同品", "一杯鐵觀音鮮奶半糖少冰，一杯桂花輕烏龍奶茶微糖去冰，一杯金杯蜜香紅純茶無糖去冰"),
        ("B3 同品兩杯", "兩杯三窨十五茉鮮奶半糖少冰"),
        ("B4 同品三杯", "三杯桂花輕烏龍奶茶半糖少冰都要大杯"),
        ("B5 數量在後面", "鐵觀音鮮奶半糖少冰來兩杯"),
    ],

    # ─── C. 同品不同規格 ───
    "同品不同規格": [
        ("C1 不同甜度", "兩杯鐵觀音鮮奶少冰，一杯半糖一杯無糖"),
        ("C2 不同冰量", "兩杯三窨十五茉鮮奶半糖，一杯少冰一杯去冰"),
        ("C3 不同尺寸", "兩杯桂花輕烏龍鮮奶半糖少冰，一杯大杯一杯中杯"),
        ("C4 甜冰都不同", "兩杯鐵觀音鮮奶，一杯半糖少冰一杯無糖去冰"),
        ("C5 三杯不對稱", "三杯三窨十五茉鮮奶少冰，兩杯半糖一杯無糖"),
    ],

    # ─── D. 修改 ───
    "修改": [
        ("D1 改甜度", "顧客：三窨十五茉鮮奶半糖少冰\n顧客：改微糖"),
        ("D2 改冰量", "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：改去冰"),
        ("D3 改尺寸", "顧客：鐵觀音鮮奶半糖少冰\n顧客：改大杯"),
        ("D4 改品項", "顧客：三窨十五茉鮮奶半糖少冰\n顧客：換桂花輕烏龍好了，其他一樣"),
        ("D5 改類別", "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：不要鮮奶改純茶"),
        ("D6 第N杯改", "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍鮮奶無糖去冰\n顧客：第一杯改微糖"),
    ],

    # ─── E. 取消 ───
    "取消": [
        ("E1 取消第二杯", "顧客：一杯三窨十五茉鮮奶半糖少冰\n顧客：一杯桂花輕烏龍純茶去冰無糖\n顧客：第二杯不要了"),
        ("E2 取消第一杯", "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：鐵觀音奶茶微糖去冰\n顧客：第一杯不要了"),
        ("E3 用品名取消", "顧客：鐵觀音鮮奶半糖少冰\n顧客：桂花輕烏龍純茶去冰無糖\n顧客：鐵觀音不要了"),
        ("E4 全部取消", "顧客：三窨十五茉鮮奶半糖少冰\n顧客：算了都不要了"),
        ("E5 取消後加新的", "顧客：桂花輕烏龍鮮奶半糖少冰\n顧客：那杯不要了\n顧客：改一杯鐵觀音鮮奶微糖去冰"),
    ],

    # ─── F. not_on_menu ───
    "not_on_menu": [
        ("F1 珍珠奶茶單點", "一杯珍珠奶茶"),
        ("F2 珍珠奶茶+正常", "一杯珍珠奶茶，一杯鐵觀音鮮奶半糖少冰"),
        ("F3 拿鐵+正常", "一杯拿鐵，一杯三窨十五茉鮮奶半糖少冰"),
        ("F4 多多綠+正常", "一杯多多綠，一杯桂花輕烏龍鮮奶半糖少冰"),
        ("F5 改點菜單品項", "顧客：來杯拿鐵\n顧客：沒有喔？那三窨十五茉鮮奶半糖少冰"),
        ("F6 兩個都不在菜單", "一杯珍珠奶茶，一杯拿鐵"),
    ],

    # ─── G. 非菜單加料 ───
    "非菜單加料": [
        ("G1 加珍珠", "三窨十五茉鮮奶半糖少冰加珍珠"),
        ("G2 加椰果", "鐵觀音鮮奶半糖少冰加椰果"),
        ("G3 加布丁", "桂花輕烏龍奶茶半糖少冰加布丁"),
        ("G4 菜單加料+非菜單加料", "鐵觀音鮮奶半糖少冰加茶凍加珍珠"),
    ],

    # ─── H. 非點餐 / 閒聊 ───
    "非點餐": [
        ("H1 問廁所", "廁所在哪裡？"),
        ("H2 問營業時間", "你們幾點關門？"),
        ("H3 問推薦", "你們什麼最好喝？"),
        ("H4 問價格", "鐵觀音鮮奶多少錢？"),
        ("H5 閒聊→點餐", "顧客：今天好熱喔\n顧客：來杯桂花輕烏龍鮮奶半糖少冰"),
        ("H6 問付款方式", "可以用LINE Pay嗎？"),
    ],

    # ─── I. 確認/結束 ───
    "確認結束": [
        ("I1 就這樣", "就這樣"),
        ("I2 沒了", "沒了"),
        ("I3 點餐+確認", "顧客：三窨十五茉鮮奶半糖少冰\n顧客：就這樣"),
        ("I4 閒聊+點餐+確認", "顧客：今天好熱喔\n顧客：來杯桂花輕烏龍鮮奶半糖少冰\n顧客：就這樣"),
    ],

    # ─── J. 口語/縮寫 ───
    "口語縮寫": [
        ("J1 茉莉=三窨十五茉", "茉莉鮮奶半糖少冰"),
        ("J2 鐵觀音省略琥珀", "鐵觀音奶茶半糖少冰"),
        ("J3 不要糖不要冰", "茉莉鮮奶不要糖不要冰"),
        ("J4 不要太甜", "鐵觀音鮮奶不要太甜少冰"),
        ("J5 極簡", "鐵觀音奶茶"),
    ],
}

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


total = sum(len(tests) for tests in TESTS.values())
print(f"模型: {MODEL}")
print(f"場景: {len(TESTS)} 類, 共 {total} 個測試\n")

for category, tests in TESTS.items():
    print(f"{'━'*60}")
    print(f"  【{category}】")
    print(f"{'━'*60}")
    for name, user_input in tests:
        try:
            output = run_test(user_input)
            # 壓成一行顯示
            try:
                parsed = json.loads(output)
                items = []
                for o in parsed.get("orders", []):
                    if o.get("not_on_menu"):
                        items.append(f"❗{o['item']}(not_on_menu)")
                    else:
                        parts = [o.get("item","?")]
                        if o.get("category"): parts.append(o["category"])
                        if o.get("size"): parts.append(o["size"])
                        if o.get("sugar"): parts.append(o["sugar"])
                        if o.get("ice"): parts.append(o["ice"])
                        if o.get("addon"): parts.append("+".join(o["addon"]))
                        items.append("/".join(parts))
                    if o.get("note"):
                        items[-1] += f' 📝{o["note"][:20]}'
                summary = " | ".join(items) if items else "(空)"
                if parsed.get("note"):
                    summary += f' 📝{parsed["note"][:25]}'
                print(f"  [{name}] → {summary}")
            except:
                print(f"  [{name}] → {output[:120]}")
        except Exception as e:
            print(f"  [{name}] → ❌ {e}")
    print()
