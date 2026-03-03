#!/usr/bin/env python3
"""
Spot-check random recommend samples for quality.
"""

import json
import random

def spot_check_recommends():
    """Spot check 20 random recommend samples."""
    print("\n" + "="*80)
    print("SPOT CHECK: RECOMMEND RESPONSE QUALITY (20 random samples)")
    print("="*80)

    recommend_samples = []

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
                        recommend_samples.append({
                            'file': filename,
                            'line': line_num,
                            'user': user_msg,
                            'response': response
                        })
                except:
                    pass

    # Random sample
    samples = random.sample(recommend_samples, min(20, len(recommend_samples)))

    for i, sample in enumerate(samples, 1):
        print(f"\n{'='*80}")
        print(f"Sample {i}/20: {sample['file']}:{sample['line']}")
        print(f"{'='*80}")
        print(f"\n👤 User: {sample['user']}")

        response = sample['response']

        print(f"\n🤖 Intent: {response.get('intent')}")

        # Check preferences
        prefs = response.get('preferences', {})
        print(f"\n📝 Preferences:")
        for key, value in prefs.items():
            print(f"  - {key}: {value}")

        # Check recommendations
        recs = response.get('recommendations', [])
        print(f"\n💡 Recommendations ({len(recs)} items):")
        for j, rec in enumerate(recs, 1):
            print(f"  {j}. {rec.get('item', 'N/A')} ({rec.get('category', 'N/A')})")
            print(f"     Reason: {rec.get('reason', 'N/A')}")

        # Quality checks
        issues = []

        # Check if orders is empty
        if response.get('orders') != []:
            issues.append("⚠️  'orders' is not empty")

        # Check if preferences is a dict
        if not isinstance(prefs, dict):
            issues.append("⚠️  'preferences' is not a dict")

        # Check if recommendations has items
        if not recs:
            issues.append("⚠️  No recommendations provided")

        # Check recommendation structure
        for rec in recs:
            if 'item' not in rec:
                issues.append("⚠️  Recommendation missing 'item'")
            if 'category' not in rec:
                issues.append("⚠️  Recommendation missing 'category'")
            if 'reason' not in rec:
                issues.append("⚠️  Recommendation missing 'reason'")
            elif not rec.get('reason') or rec.get('reason') == '':
                issues.append("⚠️  Empty reason field")

        # Check if recommendations match user query
        user_lower = sample['user'].lower()
        if '熱' in user_lower or '熱飲' in user_lower:
            # User wants hot drinks
            for rec in recs:
                if rec.get('category') == 'fruit_tea':
                    issues.append(f"⚠️  Recommended fruit_tea '{rec.get('item')}' but fruit tea is cold-only")

        if issues:
            print(f"\n❌ Issues found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"\n✅ No obvious issues")

    print(f"\n{'='*80}")
    print(f"Spot check complete. Total recommend samples: {len(recommend_samples)}")
    print(f"{'='*80}")

if __name__ == '__main__':
    random.seed(42)  # For reproducibility
    spot_check_recommends()
