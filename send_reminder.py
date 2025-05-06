import os
import requests

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

# ★ ここに送る相手のユーザーIDを直接書く
USER_ID = "U02d3833747c411ee912a885b3f90df34"  # 自分のLINE IDに書き換える

# ★ ここを時間別に切り替えてCronで使う
from datetime import datetime

now_hour = datetime.utcnow().hour + 9  # UTC → JST に変換

if 5 <= now_hour < 12:
    message_text = "おはようございます！今日も一日がんばりましょう！"
elif 12 <= now_hour < 18:
    message_text = "こんにちは！午後も集中していきましょう！"
elif 18 <= now_hour < 24:
    message_text = "1日よくがんばりましたね！ゆっくり休んでくださいね。"
else:
    message_text = "夜更かしさん、おやすみなさい〜"

push_message(USER_ID, message_text)
