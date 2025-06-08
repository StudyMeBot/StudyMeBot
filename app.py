# app.py（整理・再構築・更新：1時間半対応＋目標上書き）

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
from dotenv import load_dotenv
import os
import datetime
import re

# 自作モジュール
from data_utils.subject_dict import ALL_SUBJECTS
from spreadsheet_utils.spreadsheet_utils import update_notification_time, record_study_log
from goal_manager.parse_goal import parse_daily_goal_message
from goal_manager.save_goal import save_or_update_daily_goal

# Flaskアプリ設定
load_dotenv()
app = Flask(__name__, static_folder='static')

# LINE認証情報
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# =========================
# 🔁 通知変更メッセージ解析
# =========================
def parse_message(text):
    pattern = r"(朝|昼|夕方|夜)の通知を(?:\s*(\d{1,2})(?::|：| |時)?(\d{1,2})?|\s*(\d{1,2})時半)にして"
    match = re.search(pattern, text)
    if not match:
        return False, None, None

    time_period = match.group(1)
    if match.group(2):
        hour = int(match.group(2))
        minute = int(match.group(3)) if match.group(3) else 0
    elif match.group(4):
        hour = int(match.group(4))
        minute = 30
    else:
        return False, None, None

    time_24 = convert_to_24h(f"{hour}:{minute}", time_period)
    return True, time_period, time_24

# 通知の時間帯を24時間制に変換
def convert_to_24h(time_str, period):
    hour, minute = map(int, time_str.split(":"))
    if period == "朝" and hour == 12:
        hour = 0
    elif period in ["昼", "夕方", "夜"] and hour < 12:
        hour += 12
    return f"{hour:02}:{minute:02}"

# =========================
# 📌 フォローイベント
# =========================
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=f"あなたのユーザーIDは:\n{user_id}")
    )

# =========================
# 💬 通常メッセージ応答
# =========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # ① 通知変更メッセージか？
    is_notification, period, new_time = parse_message(text)
    if is_notification:
        if new_time:
            update_notification_time(user_id, period, new_time)
            reply = f"✅ {period}の通知時間を {new_time} に変更しました！"
        else:
            reply = "⚠️ 通知時間の形式が正しくありません（例：朝の通知を7時30分にして）"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # ② 毎日目標の設定か？
    goal_data = parse_daily_goal_message(text)
    if goal_data:
        try:
            save_or_update_daily_goal(user_id, goal_data)
            unit_label = "分" if goal_data["type"] == "time" else "回"
            reply = f"✅ 毎日の目標「{goal_data['value']}{unit_label}」を設定しました！"
        except Exception as e:
            reply = f"⚠️ 目標の保存中にエラーが発生しました: {e}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # ③ 学習記録か？
    time_match = re.search(r"([0-9０-９]+)時間([0-9０-９]+)?分?|([0-9０-９]+)時間半|([0-9０-９]+)分|([0-9０-９])半", text)
    if not time_match:
        reply = "⚠️ 入力形式が正しくありません。\n例：「英語30分」「数学1時間」"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 時間抽出
    minutes = 0
    if time_match.group(1):  # 1時間 or 1時間30分
        minutes += int(time_match.group(1)) * 60
        if time_match.group(2):
            minutes += int(time_match.group(2))
    elif time_match.group(3):  # 1時間半
        minutes += int(time_match.group(3)) * 60 + 30
    elif time_match.group(4):  # 30分など
        minutes += int(time_match.group(4))
    elif time_match.group(5):  # 「1半」など
        minutes += 30

    # 科目抽出
    subject = None
    for word in ALL_SUBJECTS:
        if word in text:
            subject = word
            break
    if not subject:
        reply = "⚠️ 科目名が見つかりませんでした。\n例：「英語30分」「数学1時間」"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # スプレッドシートに記録
    try:
        record_study_log({
            "datetime": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "subject": subject,
            "minutes": minutes,
            "raw_message": text
        })
        reply = f"✅ 「{subject}」を{minutes}分 記録しました！"
    except Exception as e:
        reply = f"❌ スプレッドシート記録中にエラーが発生しました: {e}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# =========================
# 🚪 Webhookエンドポイント
# =========================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
