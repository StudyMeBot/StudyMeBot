from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
import os
from dotenv import load_dotenv
import re
import datetime

from subject_dict import get_all_subjects
from spreadsheet_utils import update_notification_time, record_study_log

ALL_SUBJECTS = get_all_subjects()

# ✅ 時間帯の日本語→英語変換
label_mapping = {
    "朝": "morning",
    "昼": "noon",
    "夕方": "evening",
    "夜": "night"
}

# ✅ 時刻を24時間表記に変換
def convert_to_24h(time_str, time_period):
    h, m = map(int, time_str.split(":"))
    if time_period == "朝":
        if h == 12:
            h = 0
    elif time_period in ["昼", "夕方", "夜"]:
        if h < 12:
            h += 12
    return f"{h:02}:{m:02}"

# ✅ 通知メッセージ解析
def parse_message(text):
    pattern = r"(朝|昼|夕方|夜)の通知を(?:\s*(\d{1,2})(?::|：| )?(\d{2})?|(\d{1,2})時半?)にして|やめて"
    match = re.search(pattern, text)

    if match:
        time_period = match.group(1)

        # パターン①：「7時30分」「7:30」など
        if match.group(2):
            hour = match.group(2)
            minute = match.group(3) if match.group(3) else "00"
        # パターン②：「7時半」など（group(4) が存在）
        elif match.group(4):
            hour = match.group(4)
            minute = "30"
        else:
            return False, None, None

        converted_time = convert_to_24h(f"{hour}:{minute}", time_period)
        return True, time_period, converted_time

    return False, None, None

# ✅ 通知メッセージであるかの判定（補助）
def is_notification_message(text):
    time_keywords = ["朝", "昼", "夕方", "夜"]
    action_keywords = ["通知", "リマインド", "知らせ", "設定", "変更", "して", "お願い", "送って"]
    has_time_word = any(tk in text for tk in time_keywords)
    has_action_word = any(ak in text for ak in action_keywords)
    has_time_format = bool(re.search(r"\d{1,2}(:|：)?\d{2}", text))
    return has_time_word and has_action_word and has_time_format

# ✅ 学習記録メッセージであるかの判定（辞書 + 時間形式）
def is_study_log_message(text):
    has_time = bool(re.search(r"([0-9０-９]+)\s*(分|ふん|時間)", text))
    has_subject = any(subject in text for subject in KNOWN_SUBJECTS)
    return has_time and has_subject

# ✅ subject を辞書から抽出
def parse_subject(text: str) -> str | None:
    for subject in ALL_SUBJECTS:
        if subject in text:
            return subject
    return None

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
    import datetime
    from spreadsheet_utils import record_study_log, update_notification_time
    from subject_dict import CATEGORIZED_SUBJECTS

    user_id = event.source.user_id
    text = event.message.text.strip()

    # 🧠 通知変更メッセージかどうか判定
    is_notification, time_period, new_time = parse_message(text)
    if is_notification:
        if time_period and new_time:
            reply = update_notification_time(user_id, time_period, new_time)
        else:
            reply = "⚠️ 通知時間の形式が正しくありません（例：「朝の通知を7時30分にして」）"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 🧠 学習記録メッセージかどうか判定
    import re
    time_match = re.search(r"([0-9０-９]+)\s*(分|ふん|時間)", text)
    if not time_match:
        reply = (
            "⚠️ 入力形式が判別できませんでした。\n\n"
            "📌 通知変更 → 例：「朝の通知を7時30分にして」\n"
            "📌 学習記録 → 例：「英語30分」「情報 1時間」"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # 分数に変換
    if time_match.group(2) in ["分", "ふん"]:
        minutes = int(time_match.group(1))
    elif time_match.group(2) == "時間":
        minutes = int(time_match.group(1)) * 60
    else:
        minutes = 0

    # 📚 subject 抽出（辞書ベースで検索）
    subject = None
    for word in KNOWN_SUBJECTS:
        if word in text:
            subject = word
            break

    if not subject:
        reply = (
            "⚠️ 科目名が見つかりませんでした。\n\n"
            "📌 例：「英語30分」「数学 1時間」などの形式で送ってください。"
        )
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
        return

    # ✅ スプレッドシートに記録
    try:
        record_study_log({
            "datetime": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "subject": subject,
            "minutes": minutes,
            "raw_message": text
        })
        reply = f"✅ 『{subject}』を{minutes}分 記録しました！"
    except Exception as e:
        reply = f"❌ スプレッドシート記録中にエラーが発生しました: {e}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
