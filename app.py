from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
import os
from dotenv import load_dotenv
import re
from spreadsheet_utils import update_notification_time, record_study_log

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
        converted_time = convert_to_24h(f"{hour}:{minute}", time_period)
        return True, time_period, converted_time  # ✅ 通知変更と確定
    return False, None, None  # ✅ 通知変更ではない

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
    import re
    import datetime
    from spreadsheet_utils import record_study_log, update_notification_time

    user_id = event.source.user_id
    text = event.message.text.strip()

    # 🔍 通知変更メッセージかどうか判定（戻り値を3つに変更！）
    is_notification, time_period, new_time = parse_message(text)

    if is_notification:
        # ✅ 通知時間の更新処理
        reply = update_notification_time(user_id, time_period, new_time)

    else:
        # 📝 学習記録処理（例：「英語30分」「#数学1時間」など）
        time_match = re.search(r'(\d+)\s*分|(\d+)\s*時間', text)
        if time_match:
            if time_match.group(1):
                minutes = int(time_match.group(1))
            elif time_match.group(2):
                minutes = int(time_match.group(2)) * 60
        else:
            reply = "⚠️ 学習時間が見つかりませんでした（例：30分、1時間など）"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
            return

        # subject の抽出（タグ優先、なければ文頭）
        tags = re.findall(r'#(\w+)', text)
        if not tags:
            subject_match = re.match(r'^([\wぁ-んァ-ン一-龥]+)', text)
            subject = subject_match.group(1) if subject_match else "不明"
        else:
            subject = '・'.join(tags)

        try:
            record_study_log({
                'datetime': datetime.datetime.now().isoformat(),
                'user_id': user_id,
                'subject': subject,
                'minutes': minutes,
                'raw_message': text
            })
            reply = f"✅ {subject}を{minutes}分 記録しました！"
        except Exception as e:
            reply = f"❌ スプレッドシート記録中にエラーが発生しました：{e}"

    # 💬 共通の返信処理
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
