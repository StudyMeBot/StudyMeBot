import os
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage

# .envファイルの読み込み
load_dotenv()

# アクセストークンでAPI初期化
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

# あなたのユーザーID（テスト用）
USER_ID = "U8a4ecdbbd8a9e27421ef720554900839"

# 通知メッセージ
message = TextSendMessage(text="🌇 お疲れさまです！夕方のひと踏ん張り、一緒に頑張りましょう🔥")

# メッセージ送信
line_bot_api.push_message(USER_ID, message)
