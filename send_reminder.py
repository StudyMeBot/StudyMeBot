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
USER_ID = "YOUR_USER_ID"  # 自分のLINE IDに書き換える

# ★ ここを時間別に切り替えてCronで使う
push_message(USER_ID, "おはようございます！今日の勉強は何しますか？")  # 朝用
# push_message(USER_ID, "1日お疲れ様でした！今日の進捗はどうでしたか？")  # 夜用
