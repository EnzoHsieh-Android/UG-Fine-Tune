#!/usr/bin/env python3
"""
Telegram 訓練通知 Bot

用法:
  # 發送訊息
  python3 notify_telegram.py "訓練完成！最佳 checkpoint: iter 700"

  # 發送檔案內容
  python3 notify_telegram.py --file /tmp/eval_result.txt

設定:
  在同目錄建立 .telegram_config，內容為兩行:
    BOT_TOKEN=your_bot_token
    CHAT_ID=your_chat_id

  取得方式:
    1. Telegram 搜尋 @BotFather → /newbot → 取得 token
    2. 搜尋你建的 bot，發送任意訊息
    3. 執行: python3 notify_telegram.py --get-chat-id
"""

import json
import sys
import os
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urlencode

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".telegram_config")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"設定檔不存在: {CONFIG_PATH}")
        print("請建立 .telegram_config，內容:")
        print("  BOT_TOKEN=your_bot_token")
        print("  CHAT_ID=your_chat_id")
        sys.exit(1)

    config = {}
    with open(CONFIG_PATH) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()
    return config

def send_message(token, chat_id, text):
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Telegram message limit is 4096 chars
    if len(text) > 4000:
        text = text[:4000] + "\n... (truncated)"

    data = urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()

    req = Request(url, data=data, method="POST")
    try:
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read())
        if result.get("ok"):
            print(f"已發送通知到 Telegram (chat_id: {chat_id})")
        else:
            print(f"發送失敗: {result}")
    except URLError as e:
        print(f"網路錯誤: {e}")

def get_chat_id(token):
    """Get chat ID from recent messages to the bot."""
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    req = Request(url, method="GET")
    try:
        resp = urlopen(req, timeout=10)
        result = json.loads(resp.read())
        if result.get("ok") and result.get("result"):
            for update in result["result"]:
                msg = update.get("message", {})
                chat = msg.get("chat", {})
                if chat.get("id"):
                    print(f"Chat ID: {chat['id']}")
                    print(f"使用者: {chat.get('first_name', '')} {chat.get('last_name', '')}")
                    print(f"\n請將此 ID 填入 {CONFIG_PATH}:")
                    print(f"  CHAT_ID={chat['id']}")
                    return
            print("沒有找到訊息。請先在 Telegram 對你的 bot 發送任意訊息，再重試。")
        else:
            print("無法取得更新。請確認 BOT_TOKEN 正確。")
    except URLError as e:
        print(f"網路錯誤: {e}")

def main():
    if len(sys.argv) < 2:
        print("用法: python3 notify_telegram.py <訊息>")
        print("      python3 notify_telegram.py --file <檔案路徑>")
        print("      python3 notify_telegram.py --get-chat-id")
        sys.exit(1)

    config = load_config()
    token = config.get("BOT_TOKEN", "")

    if sys.argv[1] == "--get-chat-id":
        if not token:
            print("請先在 .telegram_config 填入 BOT_TOKEN")
            sys.exit(1)
        get_chat_id(token)
        return

    chat_id = config.get("CHAT_ID", "")
    if not token or not chat_id:
        print("請確認 .telegram_config 中有 BOT_TOKEN 和 CHAT_ID")
        sys.exit(1)

    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("請提供檔案路徑")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            text = f.read()
    else:
        text = " ".join(sys.argv[1:])

    send_message(token, chat_id, text)

if __name__ == "__main__":
    main()
