import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from goal_manager.utils import get_today_dates

def save_or_update_daily_goal(user_id: str, goal_data: dict):
    """
    指定されたユーザーの目標データを 'Goals' シートに「上書き or 追加」する。
    同じ user_id + 日付のデータがあれば削除してから追加。
    """
    start_date, end_date, created_at = get_today_dates()

    # スプレッドシート認証と接続
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds_dict = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("StudyMeBotStudyLog").worksheet("Goals")

    # シート全体を読み込み
    records = sheet.get_all_records()
    delete_row_index = None

    # user_id & start_date が一致する行を検索（1行目はヘッダー）
    for i, row in enumerate(records, start=2):
        if row["user_id"] == user_id and row["start_date"] == start_date:
            delete_row_index = i
            break

    if delete_row_index:
        sheet.delete_rows(delete_row_index)

    new_row = [
        user_id,
        goal_data["unit"],
        goal_data["type"],
        goal_data["value"],
        start_date,
        end_date,
        created_at
    ]
    sheet.append_row(new_row, value_input_option="USER_ENTERED")
