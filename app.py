from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
import os
from dotenv import load_dotenv
import re

label_mapping = {
    "朝": "morning",
    "昼": "noon",
    "夕方": "evening",
    "夜": "night"
}

def convert_to_24h(time_str, time_period):
    h, m = map(int, time_str.split(':'))
    if time_period == "朝":
        if h == 12:
            h = 0
    elif time_period in ["昼", "夕方", "夜"]:
        if h < 12:
            h += 12
    return f"{h:02}:{m:02}"

def parse_message(text):
   pattern = r"(朝|昼|夕方|夜)の通知を(?:(\d{1,2})(?:[:：](\d{2}))?時?(?:\d{1,2}分)?にして|やめて)"
    match = re.search(pattern, text)
    if match:
        time_period = match.group(1)
        hour = match.group(2)
        minute = match.group(3) if match.group(3) else "00"
        if hour:
            raw_time = f"{hour}:{minute}"
            converted_time = convert_to_24h(raw_time, time_period)
        else:
            converted_time = "OFF"
        return time_period, converted_time
    return None, None

# .envファイルの読み込み
load_dotenv()

app = Flask(__name__)

# LINE Messaging APIの認証情報
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# 👇 フォローイベント（友だち追加時）を処理
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=f"あなたのユーザーIDは:\n{user_id}")
    )

# 通常のメッセージ応答
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text

    time_period, new_time = parse_message(text)

    if time_period and new_time:
        # 仮でスプレッドシート更新の代わりに応答メッセージ
        reply = f"{time_period}の通知時間を「{new_time}」に設定します。"
        # 本番ではここで `update_notification_time(user_id, time_period, new_time)` を呼び出します
    else:
        reply = "通知変更の形式が正しくありません。例：『朝の通知を7:30にして』"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
