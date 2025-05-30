from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
import os
from dotenv import load_dotenv

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
    text = event.message.text
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"「{text}」を受け取りました！")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
