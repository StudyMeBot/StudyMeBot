import gspread
from oauth2client.service_account import ServiceAccountCredentials
from goal_manager.utils import get_today_dates

def save_daily_goal(user_id: str, goal_data: dict):
    """
    指定されたユーザーの目標データを 'Goals' シートに追加保存
    goal_dataは以下の形式：
    {
        "unit": "daily",
        "type": "time",
        "value": 120
    }
    """
    start_date, end_date, created_at = get_today_dates()

    # スプレッドシート認証と接続
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("StudyMeBotStudyLog").worksheet("Goals")

    new_row = [
        user_id,
        goal_data["unit"],
        goal_data["type"],
        goal_data["value"],
        start_date,
        end_date,
        created_at
    ]

    sheet.append_row(new_row, value_input_option='USER_ENTERED')
