import os
import requests
from datetime import datetime

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def push_message(to, text):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": to,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)

# JSTに変換
now_hour = datetime.utcnow().hour + 9

# 時間帯に応じたメッセージ
if 5 <= now_hour < 12:
    message_text = "おはようございます！今日も一日がんばりましょう！"
elif 12 <= now_hour < 18:
    message_text = "こんにちは！午後も集中していきましょう！"
elif 18 <= now_hour < 24:
    message_text = "1日おつかれさまでしたね！ゆっくり休んでくださいね。"
else:
    message_text = "夜遅いですね、おやすみなさい！"

# user_ids.txt から全ユーザーIDを読み込んで送信
if os.path.exists("user_ids.txt"):
    with open("user_ids.txt", "r") as f:
        user_ids = set(line.strip() for line in f if line.strip())  # 重複排除

    for uid in user_ids:
        push_message(uid, message_text)
else:
    print("user_ids.txt が見つかりませんでした。")
