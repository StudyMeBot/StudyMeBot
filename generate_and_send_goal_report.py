# generate_and_send_goal_report.py

from spreadsheet_utils.spreadsheet_utils import get_today_goal, get_today_study_minutes, get_all_user_ids
from linebot import LineBotApi
from datetime import datetime
import os

# LINE Bot API 初期化
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

# LINEにメッセージを送信する関数
def send_line_message(user_id, message):
    from linebot.models import TextSendMessage
    line_bot_api.push_message(user_id, TextSendMessage(text=message))

# メイン処理
def generate_and_send_goal_report():
    today = datetime.now().strftime("%Y/%m/%d")
    user_ids = get_all_user_ids()

    for user_id in user_ids:
        goal_minutes = get_today_goal(user_id, today)
        study_minutes = get_today_study_minutes(user_id, today)

        if goal_minutes:
            rate = int((study_minutes / goal_minutes) * 100) if goal_minutes > 0 else 0
            diff = goal_minutes - study_minutes
            if study_minutes >= goal_minutes:
                comment = "🎉 目標達成！素晴らしい一日でした！"
            else:
                comment = f"💡 あと{diff}分で目標達成です！あと少し！"
            message = f"📊 今日の記録：{study_minutes}分 ／ 目標：{goal_minutes}分（達成率 {rate}%）\n{comment}"
        else:
            message = "📌 今日の目標が未設定です。明日はぜひ設定してみましょう！"

        send_line_message(user_id, message)

if __name__ == "__main__":
    generate_and_send_goal_report()
