#!/usr/bin/env python3
"""Round 26 extra: fill uncovered sentence patterns for recommend.
Target: ~55 train + ~13 valid = ~68 new samples.
Focus: patterns with 0-2 existing samples.
"""

import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent

# Read system prompt from existing data
with open(DATA_DIR / "train.jsonl") as f:
    SP = json.loads(f.readline())["messages"][0]["content"]


def rec(user_input, preferences, recommendations):
    resp = {
        "intent": "recommend",
        "orders": [],
        "preferences": preferences,
        "recommendations": recommendations,
    }
    return {
        "messages": [
            {"role": "system", "content": SP},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": json.dumps(resp, ensure_ascii=False)},
        ]
    }


EXTRA = []

# ━━━ 1. 複合偏好：多條件組合 (8 筆) ━━━
EXTRA += [
    rec("冰的但不要太甜", {"temperature": "冰", "avoid": "太甜"}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "冰飲酸甜清爽可減糖"},
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶冰飲微糖就好喝"}]),
    rec("想喝有花香又不苦的", {"taste": "花香", "avoid": "苦"}, [
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "桂花蜜韻輕柔不苦"},
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "茉莉花香清雅帶甘甜"}]),
    rec("熱的鮮奶茶不要太濃", {"temperature": "熱", "taste": "清淡", "scenario": "鮮奶茶"}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜潤不搶味"},
        {"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "玉露菁鮮奶柔和細膩"}]),
    rec("清爽一點但要有奶的", {"taste": "清爽", "scenario": "有奶"}, [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶清香滑順"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香鮮奶甜潤清爽"}]),
    rec("果香的但不要太酸", {"taste": "果香", "avoid": "太酸"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃甜香為主不酸"}]),
    rec("想喝濃一點的而且要熱的", {"taste": "濃郁", "temperature": "熱"}, [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "熱鐵觀音奶茶焙火濃厚"},
        {"item": "茶花紅烏龍", "category": "rich_milk_tea", "reason": "熱紅烏龍奶茶焙火醇厚"}]),
    rec("便宜又好喝的冰飲", {"scenario": "預算低", "temperature": "冰"}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "M杯60元蜜香鮮奶好喝"},
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶平價花香清雅"}]),
    rec("甜一點的不要有茶味", {"taste": "甜", "avoid": "茶味"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香甜蜜茶味柔"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "桂花蜜甜酸交織清爽"}]),
]

# ━━━ 2. 心情/情緒 (6 筆) ━━━
EXTRA += [
    rec("心情不好想喝個東西", {"scenario": "心情低落"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃甜蜜果香療癒心情"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香鮮奶甜潤暖心"}]),
    rec("今天超累的", {"scenario": "疲倦"}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音焙火提神"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙烏龍回甘振奮"}]),
    rec("壓力好大想放鬆", {"scenario": "舒壓"}, [
        {"item": "米香玉露菁", "category": "pure_tea", "reason": "玉露菁米穀香鮮爽療癒"},
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "桂花蜜韻輕柔放鬆"}]),
    rec("今天心情很好想犒賞自己", {"scenario": "犒賞自己"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋精緻鹹甜犒賞首選"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚茉莉清新大人味"}]),
    rec("好煩喔來杯飲料吧", {"scenario": "心煩"}, [
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "酸甜清爽轉換心情"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃甜蜜療癒"}]),
    rec("很開心想慶祝一下", {"scenario": "慶祝"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋特別適合慶祝"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香甜蜜應景"}]),
]

# ━━━ 3. 時段 (6 筆) ━━━
EXTRA += [
    rec("早上適合喝什麼", {"scenario": "早上"}, [
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶清爽開啟一天"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶補充活力"}]),
    rec("中午吃飽想來一杯", {"scenario": "午餐後"}, [
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "普洱微酸回甘飯後解膩"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "青檸酸甜清爽助消化"}]),
    rec("晚上喝什麼不會睡不著", {"scenario": "晚上", "avoid": "失眠"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "果茶相對咖啡因低"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶清爽助眠"}]),
    rec("下班來一杯", {"scenario": "下班"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤放鬆"},
        {"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "玉露菁鮮奶穀物香療癒"}]),
    rec("宵夜配什麼飲料好", {"scenario": "宵夜"}, [
        {"item": "金杯蜜香紅", "category": "rich_milk_tea", "reason": "蜜香奶茶甜潤配宵夜"},
        {"item": "桂花輕烏龍", "category": "rich_milk_tea", "reason": "桂花奶茶溫潤搭餐"}]),
    rec("早餐配什麼茶", {"scenario": "早餐"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "茉莉花茶清香搭早餐"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶提神配早餐"}]),
]

# ━━━ 4. 回購/換口味 (6 筆) ━━━
EXTRA += [
    rec("上次喝鮮奶茶很好喝，類似的還有嗎", {"taste": "鮮奶茶"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶焙火香濃"}]),
    rec("每次都喝一樣的，換個口味", {}, [
        {"item": "朱槿普洱紅", "category": "fresh_milk_tea", "reason": "洛神普洱風味獨特少見"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚茉莉清新微苦大人味"}]),
    rec("之前喝過純茶，這次想試奶的", {"scenario": "換類型"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻奶香"},
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "鐵觀音奶茶焙火奶香濃"}]),
    rec("沒喝過你們家的，推薦入門款", {}, [
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香鮮奶甜潤好入口"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶接受度高"}]),
    rec("想試試看沒喝過的口味", {}, [
        {"item": "米香玉露菁", "category": "pure_tea", "reason": "日式玉露菁帶米穀香少見"},
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "洛神普洱微酸風味獨特"}]),
    rec("上次來喝過茉莉的，還有別的推薦嗎", {"avoid": "茉莉"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻與茉莉不同風格"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音焙火香濃郁"}]),
]

# ━━━ 5. 口感/質地 (5 筆) ━━━
EXTRA += [
    rec("有什麼QQ的可以加", {}, [
        {"item": "紅烏龍茶凍", "category": "fresh_milk_tea", "reason": "茶凍口感QQ帶茶香，搭鮮奶茶好喝"}]),
    rec("想喝有嚼勁的", {"taste": "有嚼勁"}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "加燕麥粒增加咀嚼感"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "加茶凍QQ有口感"}]),
    rec("奶蓋是什麼口感", {"taste": "奶蓋口感"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "綿密奶蓋覆蓋茶面鹹甜滑順"},
        {"item": "茶花紅烏龍", "category": "cloud_velvet", "reason": "奶蓋綿密配焙火茶香"}]),
    rec("口感豐富一點的", {"taste": "口感豐富"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "奶蓋鹹甜配茶香多層次口感"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "加茶凍跟燕麥粒口感最豐富"}]),
    rec("喝起來很絲滑的", {"taste": "絲滑"}, [
        {"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "玉露菁鮮奶細膩柔滑"},
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶清香滑順"}]),
]

# ━━━ 6. 多人配搭 (5 筆) ━━━
EXTRA += [
    rec("我們三個人要喝不一樣的", {"scenario": "三人各一杯"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "鮮奶茶溫潤一款"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶清爽一款"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "純茶回甘一款"}]),
    rec("兩個人不知道要點什麼", {"scenario": "兩人"}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶焙火濃郁"}]),
    rec("幫我配一杯甜的一杯不甜的", {"scenario": "一甜一不甜"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香甜蜜（甜的）"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "焙火烏龍回甘無糖（不甜的）"}]),
    rec("買四杯回辦公室", {"scenario": "辦公室四杯"}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶接受度高"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香鮮奶甜潤"},
        {"item": "三窨十五茉", "category": "fresh_milk_tea", "reason": "茉莉鮮奶清香"}]),
    rec("男生女生各推薦一杯", {"scenario": "男女各一杯"}, [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "鐵觀音奶茶焙火濃郁適合男生"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香甜蜜適合女生"}]),
]

# ━━━ 7. 社群/推薦來源 (4 筆) ━━━
EXTRA += [
    rec("IG上看到你們家很紅", {}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋最熱門好看好喝"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃紅烏龍也很受歡迎"}]),
    rec("網路上說你們茶很厲害", {}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "三窨茉莉工藝花香清雅"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙紅烏龍天然花香"}]),
    rec("同事推薦我來喝的", {}, [
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫潤回購率高"},
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "鐵觀音鮮奶焙火香濃"}]),
    rec("聽說你們有一個很特別的飲料", {}, [
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "洛神花搭普洱微酸回甘最獨特"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚茉莉微苦大人味少見"}]),
]

# ━━━ 8. 特殊場合 (5 筆) ━━━
EXTRA += [
    rec("生日想喝特別一點的", {"scenario": "生日"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋精緻特別適合慶生"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香甜蜜慶祝"}]),
    rec("要送朋友的禮物", {"scenario": "送禮"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "奶蓋外觀精緻適合送禮"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚茉莉口味獨特有心意"}]),
    rec("紀念日想買好一點的", {"scenario": "紀念日"}, [
        {"item": "茶花紅烏龍", "category": "cloud_velvet", "reason": "紅烏龍奶蓋茶香鹹甜高級感"},
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋精緻適合紀念日"}]),
    rec("帶去派對的", {"scenario": "派對"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃果香甜蜜派對適合"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "酸甜清爽氣氛好"}]),
    rec("母親節想買給媽媽", {"scenario": "母親節"}, [
        {"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "穀物奶香溫潤療癒適合長輩"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "桂花鮮奶蜜韻溫暖"}]),
]

# ━━━ 9. 健康考量 (5 筆) ━━━
EXTRA += [
    rec("喉嚨不太舒服可以喝什麼", {"scenario": "喉嚨不適"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "溫熱茉莉花茶溫潤舒緩"},
        {"item": "桂花輕烏龍", "category": "pure_tea", "reason": "桂花茶溫和不刺激"}]),
    rec("我有乳糖不耐", {"avoid": "乳製品"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶無乳製品"},
        {"item": "青檸桂蜜", "category": "fruit_tea", "reason": "果茶無奶成分"}]),
    rec("怕胖有低熱量的嗎", {"avoid": "高熱量"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶無糖熱量最低"},
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "普洱紅茶助消化微酸"}]),
    rec("胃不太好喝什麼比較不刺激", {"avoid": "刺激", "scenario": "胃不好"}, [
        {"item": "米香玉露菁", "category": "fresh_milk_tea", "reason": "玉露菁鮮奶溫和不刺激"},
        {"item": "金杯蜜香紅", "category": "fresh_milk_tea", "reason": "蜜香紅茶鮮奶甜潤溫和"}]),
    rec("想喝健康一點的", {"scenario": "健康"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "純茶無糖最健康"},
        {"item": "米香玉露菁", "category": "pure_tea", "reason": "日式玉露菁天然鮮爽"}]),
]

# ━━━ 10. 視覺/外觀 (4 筆) ━━━
EXTRA += [
    rec("有沒有好看的適合拍照", {"scenario": "拍照"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "奶蓋漸層好看適合拍照"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃色澤好看"}]),
    rec("想拍IG打卡的", {"scenario": "打卡"}, [
        {"item": "茶花紅烏龍", "category": "cloud_velvet", "reason": "紅烏龍奶蓋漸層超好拍"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚色澤鮮豔好上鏡"}]),
    rec("哪杯顏色最漂亮", {"scenario": "外觀"}, [
        {"item": "朱槿普洱紅", "category": "pure_tea", "reason": "洛神花紅色澤深豔漂亮"},
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃橘紅色澤好看"}]),
    rec("有沒有看起來很厲害的", {"scenario": "外觀"}, [
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "奶蓋漸層視覺精緻"},
        {"item": "葡柚十五茉", "category": "fruit_tea", "reason": "葡柚清新視覺吸睛"}]),
]

# ━━━ 11. 條件/假設句式 (4 筆) ━━━
EXTRA += [
    rec("如果想喝奶茶的話推薦哪個", {"scenario": "奶茶"}, [
        {"item": "琥珀鐵觀音", "category": "rich_milk_tea", "reason": "鐵觀音奶茶焙火奶香濃"},
        {"item": "三窨十五茉", "category": "rich_milk_tea", "reason": "茉莉奶茶清香順口"}]),
    rec("假設我不喝冰的還有什麼選擇", {"temperature": "熱", "avoid": "冰"}, [
        {"item": "琥珀鐵觀音", "category": "fresh_milk_tea", "reason": "熱鐵觀音鮮奶焙火暖身"},
        {"item": "桂花輕烏龍", "category": "fresh_milk_tea", "reason": "熱桂花鮮奶蜜韻溫潤"}]),
    rec("如果要點純茶的話呢", {"scenario": "純茶"}, [
        {"item": "三窨十五茉", "category": "pure_tea", "reason": "茉莉花茶花香清雅經典"},
        {"item": "茶花紅烏龍", "category": "pure_tea", "reason": "重焙紅烏龍回甘有層次"}]),
    rec("如果是女生的話會喜歡哪杯", {"scenario": "女生"}, [
        {"item": "蜜桃紅烏龍", "category": "fruit_tea", "reason": "蜜桃甜蜜果香女生最愛"},
        {"item": "桂花輕烏龍", "category": "cloud_velvet", "reason": "桂花奶蓋精緻好看又好喝"}]),
]


def main():
    random.seed(123)

    print(f"Total extra samples: {len(EXTRA)}")

    # Check for duplicate user messages against existing data
    existing_users = set()
    for fname in ["train.jsonl", "valid.jsonl"]:
        with open(DATA_DIR / fname) as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    for msg in d["messages"]:
                        if msg["role"] == "user":
                            existing_users.add(msg["content"])

    # Filter out any duplicates
    unique_extras = []
    dupes = 0
    for s in EXTRA:
        user_msg = s["messages"][1]["content"]
        if user_msg in existing_users:
            dupes += 1
            print(f"  DUPE skipped: {user_msg}")
        else:
            unique_extras.append(s)
            existing_users.add(user_msg)

    print(f"After dedup: {len(unique_extras)} (skipped {dupes} dupes)")

    # Shuffle and split 80/20
    indices = list(range(len(unique_extras)))
    random.shuffle(indices)

    split = int(len(unique_extras) * 0.8)
    train_indices = sorted(indices[:split])
    valid_indices = sorted(indices[split:])

    train_new = [unique_extras[i] for i in train_indices]
    valid_new = [unique_extras[i] for i in valid_indices]

    print(f"Train new: {len(train_new)}, Valid new: {len(valid_new)}")

    # Save round reference
    with open(DATA_DIR / "round26_extra.jsonl", "w") as f:
        for s in unique_extras:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Append
    with open(DATA_DIR / "train.jsonl", "a") as f:
        for s in train_new:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(DATA_DIR / "valid.jsonl", "a") as f:
        for s in valid_new:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Final stats
    for fname in ["train.jsonl", "valid.jsonl"]:
        intents = {}
        total = 0
        with open(DATA_DIR / fname) as f:
            for line in f:
                if line.strip():
                    total += 1
                    d = json.loads(line)
                    for msg in d["messages"]:
                        if msg["role"] == "assistant":
                            try:
                                r = json.loads(msg["content"])
                                intents[r.get("intent", "unknown")] = intents.get(r.get("intent", "unknown"), 0) + 1
                            except:
                                pass
        rec_count = intents.get("recommend", 0)
        print(f"\n{fname}: {total} (order {intents.get('order',0)}, recommend {rec_count}, ratio {rec_count*100/total:.1f}%)")


if __name__ == "__main__":
    main()
