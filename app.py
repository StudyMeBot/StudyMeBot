from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

import openai

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

def connect_to_sheet():
    credentials_dict = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(credentials)
    sheet = client.open("StudyMeBotLog").sheet1
    return sheet

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
def update_notification_time(user_id, time_type, new_time):
    sheet = connect_to_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if str(row['user_id']) == str(user_id):
            # スプレッドシートの2行目以降がデータ行なので +2
            sheet.update_cell(i + 2, {"morning": 2, "noon": 3, "night": 4}[time_type], new_time)
            return True
    return False

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"
    
from linebot.models import FollowEvent, TextSendMessage  # すでに import してなければ追加

@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    print(f"New follower: {user_id}")

    # ファイルに保存（簡易実装、複数回追加されないよう工夫も可能）
    with open("user_ids.txt", "a") as f:
        f.write(user_id + "\n")

    # ウェルカムメッセージ
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text="友だち追加ありがとうございます！")
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message = event.message.text
    
    # 通知時刻の変更指示を解析
    if any(x in message for x in ["朝", "昼", "夜"]):
        if "通知なし" in message:
            new_time = ""
        else:
            import re
            match = re.search(r"\d{1,2}[:：]\d{2}", message)
            if match:
                new_time = match.group().replace("：", ":")
            else:
                new_time = ""

        if "朝" in message:
            update_notification_time(user_id, "morning", new_time)
        elif "昼" in message:
            update_notification_time(user_id, "noon", new_time)
        elif "夜" in message:
            update_notification_time(user_id, "night", new_time)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="通知設定を更新しました！")
        )
        return  # それ以上の処理はしない
    
    print(f"User ID: {event.source.user_id}")

    sheet = connect_to_sheet()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, user_id, message])

  # ChatGPTの応答を生成
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": message}
        ]
    )
    reply_text = response["choices"][0]["message"]["content"]
    reply = TextSendMessage(text=reply_text)
    line_bot_api.reply_message(event.reply_token, reply)


if __name__ == "__main__":
    app.run()
