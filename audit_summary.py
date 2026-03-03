#!/usr/bin/env python3
"""Summarize and categorize audit findings."""

import json
import re
from collections import Counter, defaultdict

def categorize_results(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract all issue lines
    issues = []
    for line in content.split('\n'):
        line = line.strip()
        # Skip numbering prefix
        m = re.match(r'^\d+→(.+)$', line)
        if m:
            line = m.group(1)
        if line.startswith('[train.jsonl:') or line.startswith('[valid.jsonl:'):
            issues.append(line)

    categories = {
        'chinese_semicolon': [],
        'invalid_item': [],
        'invalid_category': [],
        'invalid_item_category_combo': [],
        'invalid_sugar': [],
        'invalid_ice': [],
        'invalid_size': [],
        'fruit_tea_hot': [],
        'no_size_has_size': [],
        'invalid_addon': [],
        'missing_fields': [],
        'intents_length_mismatch': [],
        'intents_invalid_value': [],
        'intents_order_mismatch': [],
        'intents_recommend_mismatch': [],
        'recommendations_empty': [],
        'recommendations_no_intent': [],
        'recommendations_over_1': [],
        'user_sugar_mismatch': [],
        'user_ice_mismatch': [],
        'user_size_mismatch': [],
        'user_qty_mismatch': [],
        'user_hot_mismatch': [],
        'size_should_be_null': [],
        'exact_duplicates': [],
        'near_duplicates': [],
        'other': [],
    }

    for issue in issues:
        if '使用中文分號' in issue:
            categories['chinese_semicolon'].append(issue)
        elif '.item 不合法' in issue:
            categories['invalid_item'].append(issue)
        elif '.category 不合法' in issue:
            categories['invalid_category'].append(issue)
        elif 'item+category 組合不合法' in issue:
            categories['invalid_item_category_combo'].append(issue)
        elif '.sugar 不合法' in issue:
            categories['invalid_sugar'].append(issue)
        elif '.ice 不合法' in issue:
            categories['invalid_ice'].append(issue)
        elif '.size 不合法' in issue:
            categories['invalid_size'].append(issue)
        elif '果茶品項' in issue and '熱飲' in issue:
            categories['fruit_tea_hot'].append(issue)
        elif '不應有 size' in issue:
            categories['no_size_has_size'].append(issue)
        elif '.addon 不合法' in issue:
            categories['invalid_addon'].append(issue)
        elif '缺少欄位' in issue:
            categories['missing_fields'].append(issue)
        elif 'intents 長度' in issue:
            categories['intents_length_mismatch'].append(issue)
        elif 'intents[' in issue and '值不合法' in issue:
            categories['intents_invalid_value'].append(issue)
        elif '有 orders 但 intents 不含' in issue:
            categories['intents_order_mismatch'].append(issue)
        elif 'intents 含 recommend 但 recommendations 為空' in issue:
            categories['recommendations_empty'].append(issue)
        elif '有 recommendations 但 intents 不含 recommend' in issue:
            categories['recommendations_no_intent'].append(issue)
        elif 'recommendations 超過 1 項' in issue:
            categories['recommendations_over_1'].append(issue)
        elif '用戶說「' in issue and 'sugar' in issue:
            categories['user_sugar_mismatch'].append(issue)
        elif '用戶說「' in issue and 'ice' in issue:
            categories['user_ice_mismatch'].append(issue)
        elif '用戶說「大杯' in issue or '用戶說「中杯' in issue:
            categories['user_size_mismatch'].append(issue)
        elif '用戶說「' in issue and 'qty' in issue:
            categories['user_qty_mismatch'].append(issue)
        elif '用戶說「熱' in issue:
            categories['user_hot_mismatch'].append(issue)
        elif '用戶未指定尺寸' in issue:
            categories['size_should_be_null'].append(issue)
        elif '純茶品項但 size' in issue or '奶蓋品項但 size' in issue:
            categories['no_size_has_size'].append(issue)
        elif '完全重複' in issue:
            categories['exact_duplicates'].append(issue)
        elif '近似重複' in issue:
            categories['near_duplicates'].append(issue)
        else:
            categories['other'].append(issue)

    return categories


result_file = '/Users/xiechengru/.claude/projects/-Users-xiechengru/ad35016a-2430-4749-9838-c054f1b1fb14/tool-results/b973fdd.txt'
cats = categorize_results(result_file)

print("=" * 70)
print("訓練資料品質審計摘要報告")
print("=" * 70)

category_labels = {
    'chinese_semicolon': '1. 中文分號（應用英文分號）',
    'invalid_item': '2. 不合法品項名（非菜單品項，含「其他品牌」訓練樣本）',
    'invalid_category': '3. 不合法分類值',
    'invalid_item_category_combo': '4. item+category 組合不合法',
    'invalid_sugar': '5. 不合法甜度值',
    'invalid_ice': '6. 不合法冰量值',
    'invalid_size': '7. 不合法尺寸值',
    'fruit_tea_hot': '8. 果茶品項設為熱飲',
    'no_size_has_size': '9. 單一尺寸品項設有 size',
    'invalid_addon': '10. 不合法加料',
    'missing_fields': '11. 缺少欄位',
    'intents_length_mismatch': '12. intents 長度與 segment 數不符',
    'intents_invalid_value': '13. intents 值不合法',
    'intents_order_mismatch': '14. 有 orders 但 intents 不含 order/modify',
    'recommendations_empty': '15. intents 含 recommend 但 recommendations 為空',
    'recommendations_no_intent': '16. 有 recommendations 但 intents 不含 recommend',
    'recommendations_over_1': '17. recommendations 超過 1 項',
    'user_sugar_mismatch': '18. 用戶甜度 vs 輸出甜度不一致',
    'user_ice_mismatch': '19. 用戶冰量 vs 輸出冰量不一致',
    'user_size_mismatch': '20. 用戶尺寸 vs 輸出尺寸不一致',
    'user_qty_mismatch': '21. 用戶數量 vs 輸出數量不一致（含「第X杯」誤判）',
    'user_hot_mismatch': '22. 用戶說「熱」但 ice 不是熱飲',
    'size_should_be_null': '23. 用戶未指定尺寸但 size 非 null',
    'exact_duplicates': '24. 完全重複 user text',
    'near_duplicates': '25. 近似重複 user text（差 1-2 字）',
    'other': '26. 其他問題',
}

total_real = 0
for key, label in category_labels.items():
    items = cats[key]
    count = len(items)
    if key == 'near_duplicates':
        # Don't count near duplicates in total since many are intentional
        print(f"\n{label}: {count} 筆（多為刻意設計的多樣性訓練樣本，需人工判斷）")
    else:
        total_real += count
        print(f"\n{label}: {count} 筆")

    if count > 0 and key != 'near_duplicates':
        # Show all items for small categories, first 10 for large
        show_items = items if len(items) <= 15 else items[:10]
        for item in show_items:
            print(f"  {item}")
        if len(items) > 15:
            print(f"  ... 還有 {len(items) - 10} 筆")

print(f"\n{'=' * 70}")
print(f"需要關注的問題（不含近似重複）: {total_real} 筆")
print(f"近似重複（需人工判斷）: {len(cats['near_duplicates'])} 筆")
print(f"{'=' * 70}")
