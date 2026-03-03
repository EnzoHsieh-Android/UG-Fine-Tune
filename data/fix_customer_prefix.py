"""Convert 顧客：prefix multi-round format to semicolon-separated format."""
import json
import re
import sys

def convert_user_text(text: str) -> str:
    """Convert '顧客：A\n顧客：B' to 'A;B'"""
    if '顧客' not in text:
        return text
    # Split by lines, strip 顧客：/顧客: prefix, join with ;
    lines = text.strip().split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        # Remove 顧客：or 顧客: prefix
        line = re.sub(r'^顧客[：:]', '', line).strip()
        if line:
            cleaned.append(line)
    return ';'.join(cleaned)

def process_file(input_path: str, output_path: str):
    converted = 0
    total = 0
    results = []

    with open(input_path, 'r') as f:
        for line in f:
            total += 1
            obj = json.loads(line)
            changed = False
            for msg in obj['messages']:
                if msg['role'] == 'user' and '顧客' in msg['content']:
                    old = msg['content']
                    msg['content'] = convert_user_text(old)
                    if old != msg['content']:
                        changed = True
            if changed:
                converted += 1
            results.append(json.dumps(obj, ensure_ascii=False))

    with open(output_path, 'w') as f:
        for r in results:
            f.write(r + '\n')

    print(f'Total: {total}, Converted: {converted}')

if __name__ == '__main__':
    for path in ['train.jsonl', 'valid.jsonl']:
        print(f'Processing {path}...')
        process_file(path, path)
