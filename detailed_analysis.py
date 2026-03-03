#!/usr/bin/env python3
"""
Detailed analysis of specific issues found in audit.
"""

import json
from collections import defaultdict

def analyze_invalid_menu_items():
    """Find all invalid menu item cases."""
    print("\n" + "="*80)
    print("INVALID MENU ITEMS DETAILED ANALYSIS")
    print("="*80)

    issues = []

    for filename in ['train.jsonl', 'valid.jsonl']:
        filepath = f'/Users/xiechengru/ug-finetune/data/{filename}'
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                sample = json.loads(line.strip())
                messages = sample['messages']
                assistant_msg = messages[2]['content']
                try:
                    response = json.loads(assistant_msg)
                    if 'orders' in response:
                        for i, order in enumerate(response['orders']):
                            item = order.get('item', '')
                            category = order.get('category', '')

                            # Check for specific problematic patterns
                            if item == '琥珀鐵觀音' and category == 'pure_tea':
                                issues.append({
                                    'file': filename,
                                    'line': line_num,
                                    'item': item,
                                    'category': category,
                                    'correct_categories': ['fresh_milk_tea', 'rich_milk_tea'],
                                    'user': messages[1]['content']
                                })
                            elif item == '茶花紅烏龍' and category == 'fresh_milk_tea':
                                issues.append({
                                    'file': filename,
                                    'line': line_num,
                                    'item': item,
                                    'category': category,
                                    'correct_categories': ['pure_tea', 'rich_milk_tea', 'cloud_velvet'],
                                    'user': messages[1]['content']
                                })
                            elif item == '茶花烏龍' and category == 'rich_milk_tea':
                                issues.append({
                                    'file': filename,
                                    'line': line_num,
                                    'item': item,
                                    'category': category,
                                    'correct_categories': ['fresh_milk_tea'],
                                    'user': messages[1]['content']
                                })
                            elif item == '紅玉紅茶':
                                issues.append({
                                    'file': filename,
                                    'line': line_num,
                                    'item': item,
                                    'category': category,
                                    'note': 'NOT ON MENU - should have not_on_menu flag',
                                    'user': messages[1]['content']
                                })
                except:
                    pass

    # Group by type
    by_type = defaultdict(list)
    for issue in issues:
        key = f"{issue['item']} in {issue['category']}"
        by_type[key].append(issue)

    for key, items in sorted(by_type.items()):
        print(f"\n🔴 {key} ({len(items)} cases)")
        print("-" * 80)
        for item in items[:5]:
            print(f"  {item['file']}:{item['line']}")
            print(f"    User: {item['user'][:80]}")
            if 'correct_categories' in item:
                print(f"    Should be: {', '.join(item['correct_categories'])}")
            if 'note' in item:
                print(f"    Note: {item['note']}")
        if len(items) > 5:
            print(f"  ... and {len(items)-5} more")

def analyze_mixed_intents():
    """Analyze mixed intent samples."""
    print("\n" + "="*80)
    print("MIXED INTENT SAMPLES (order + recommendation)")
    print("="*80)

    for filename in ['train.jsonl', 'valid.jsonl']:
        filepath = f'/Users/xiechengru/ug-finetune/data/{filename}'
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                sample = json.loads(line.strip())
                messages = sample['messages']
                assistant_msg = messages[2]['content']
                user_msg = messages[1]['content']
                try:
                    response = json.loads(assistant_msg)
                    if (response.get('intent') == 'order' and
                        response.get('orders', []) and
                        response.get('recommendations', [])):
                        print(f"\n{filename}:{line_num}")
                        print(f"User: {user_msg}")
                        print(f"Orders: {len(response['orders'])} items")
                        print(f"Recommendations: {len(response['recommendations'])} items")
                        print(f"Full response: {json.dumps(response, ensure_ascii=False, indent=2)[:300]}...")
                except:
                    pass

def analyze_intent_mismatches():
    """Analyze cases where intent seems wrong."""
    print("\n" + "="*80)
    print("INTENT MISMATCH ANALYSIS")
    print("="*80)

    print("\n🔴 Users asking for recommendations but labeled as 'order':")
    print("-" * 80)

    recommendation_keywords = ['推薦', '建議', '介紹', '什麼好喝', '不知道', '選什麼']

    for filename in ['train.jsonl', 'valid.jsonl']:
        filepath = f'/Users/xiechengru/ug-finetune/data/{filename}'
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                sample = json.loads(line.strip())
                messages = sample['messages']
                assistant_msg = messages[2]['content']
                user_msg = messages[1]['content']
                try:
                    response = json.loads(assistant_msg)
                    if response.get('intent') == 'order':
                        # Check if user asks for recommendation
                        if any(kw in user_msg for kw in recommendation_keywords):
                            # But has empty recommendations in response
                            if not response.get('recommendations', []):
                                print(f"\n{filename}:{line_num}")
                                print(f"User: {user_msg}")
                                print(f"Intent: {response.get('intent')}")
                                print(f"Orders: {len(response.get('orders', []))} items")
                                print(f"Recommendations: {len(response.get('recommendations', []))} items")
                except:
                    pass

def analyze_duplicates():
    """Find duplicate user messages."""
    print("\n" + "="*80)
    print("DUPLICATE USER MESSAGES")
    print("="*80)

    user_messages = defaultdict(list)

    for filename in ['train.jsonl', 'valid.jsonl']:
        filepath = f'/Users/xiechengru/ug-finetune/data/{filename}'
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                sample = json.loads(line.strip())
                messages = sample['messages']
                user_msg = messages[1]['content']
                user_messages[user_msg].append((filename, line_num))

    duplicates = {msg: locs for msg, locs in user_messages.items() if len(locs) > 1}

    print(f"\nFound {len(duplicates)} duplicate user messages:")
    for msg, locs in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"\n'{msg[:80]}...' ({len(locs)} occurrences)")
        for filename, line_num in locs:
            print(f"  {filename}:{line_num}")

def check_recommend_format_issues():
    """Check for issues in recommend responses."""
    print("\n" + "="*80)
    print("RECOMMEND RESPONSE FORMAT ISSUES")
    print("="*80)

    issues = []

    for filename in ['train.jsonl', 'valid.jsonl']:
        filepath = f'/Users/xiechengru/ug-finetune/data/{filename}'
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                sample = json.loads(line.strip())
                messages = sample['messages']
                assistant_msg = messages[2]['content']
                user_msg = messages[1]['content']
                try:
                    response = json.loads(assistant_msg)
                    if response.get('intent') == 'recommend':
                        # Check for common issues
                        if response.get('orders') != []:
                            issues.append({
                                'file': filename,
                                'line': line_num,
                                'issue': 'non-empty orders',
                                'user': user_msg,
                                'orders': response['orders']
                            })
                        if 'preferences' not in response:
                            issues.append({
                                'file': filename,
                                'line': line_num,
                                'issue': 'missing preferences',
                                'user': user_msg
                            })
                        elif not isinstance(response['preferences'], dict):
                            issues.append({
                                'file': filename,
                                'line': line_num,
                                'issue': 'preferences not dict',
                                'user': user_msg,
                                'preferences': response['preferences']
                            })
                        if 'recommendations' not in response:
                            issues.append({
                                'file': filename,
                                'line': line_num,
                                'issue': 'missing recommendations',
                                'user': user_msg
                            })
                        elif not response['recommendations']:
                            issues.append({
                                'file': filename,
                                'line': line_num,
                                'issue': 'empty recommendations array',
                                'user': user_msg
                            })
                except:
                    pass

    if not issues:
        print("\n✅ All recommend responses have correct format!")
        return

    # Group by issue type
    by_type = defaultdict(list)
    for issue in issues:
        by_type[issue['issue']].append(issue)

    for issue_type, items in sorted(by_type.items()):
        print(f"\n🔴 {issue_type} ({len(items)} cases)")
        print("-" * 80)
        for item in items[:5]:
            print(f"  {item['file']}:{item['line']}")
            print(f"    User: {item['user'][:80]}")
            if 'orders' in item:
                print(f"    Orders: {item['orders']}")
            if 'preferences' in item:
                print(f"    Preferences: {item['preferences']}")
        if len(items) > 5:
            print(f"  ... and {len(items)-5} more")

if __name__ == '__main__':
    analyze_invalid_menu_items()
    analyze_mixed_intents()
    analyze_intent_mismatches()
    analyze_duplicates()
    check_recommend_format_issues()
