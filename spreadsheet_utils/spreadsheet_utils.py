# spreadsheet_utils.py

import gspread
from google.oauth2.service_account import Credentials
import json, os, tempfile
from goal_manager.utils import get_today_dates
GOAL_SHEET_NAME = "Goals (daily)".strip()

# 📌 credentials.json を tempファイルで扱う形式

def get_credentials_from_env():
    creds_dict = json.loads(os.getenv("GOOGLE_CREDS_JSON"))
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp:
        json.dump(creds_dict, tmp)
        return tmp.name

# 🔁 通知時間の更新
def update_notification_time(user_id, time_period_jp, new_time):
    label_mapping = {
        "朝": "morning",
        "昼": "noon",
        "夕方": "evening",
        "夜": "night"
    }
    col_label = label_mapping.get(time_period_jp)
    if not col_label:
        return "時間帯の指定が正しくありません。"

    try:
        # Google認証
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        cred_path = get_credentials_from_env()
        credentials = Credentials.from_service_account_file(cred_path, scopes=scope)
        gc = gspread.authorize(credentials)

        # スプレッドシートを開く
        sh = gc.open("StudyMeBotNotify")
        worksheet = sh.sheet1
        records = worksheet.get_all_records()

        # user_idがあるかチェック
        found = False
        for idx, record in enumerate(records, start=2):
            if record.get("user_id") == user_id:
                col_num = worksheet.find(col_label).col
                worksheet.update_cell(idx, col_num, new_time)
                return f"{time_period_jp}の通知時間を「{new_time}」に更新しました。"

        # なければ新規追加
        if not found:
            header = worksheet.row_values(1)
            new_row = []
            for col in header:
                if col == "user_id":
                    new_row.append(user_id)
                elif col == col_label:
                    new_row.append(new_time)
                else:
                    new_row.append("OFF")

            worksheet.append_row(new_row)
            return f"{time_period_jp}の通知時間を「{new_time}」に設定し、新しいユーザーとして登録しました。"

    except Exception as e:
        return f"スプレッドシートの更新中にエラーが発生しました: {e}"


# 📝 学習記録用の関数（新規追加）
def record_study_log(data):
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        cred_path = get_credentials_from_env()
        credentials = Credentials.from_service_account_file(cred_path, scopes=scope)
        gc = gspread.authorize(credentials)

        sh = gc.open("StudyMeBotStudyLog")

        # == StudyLog に記録 ==
        main_ws = sh.worksheet("StudyLog")
        main_row = [
            data["datetime"],
            data["user_id"],
            data["subject"],
            data["minutes"],
            data["raw_message"]
        ]
        main_ws.append_row(main_row)

        # == 各 user_id シートにも記録 ==
        user_id = data["user_id"]
        try:
            user_ws = sh.worksheet(user_id)
        except gspread.exceptions.WorksheetNotFound:
            user_ws = sh.add_worksheet(title=user_id, rows="1000", cols="4")
            user_ws.append_row(["datetime", "subject", "minutes", "raw_message"])

        user_ws.append_row([
            data["datetime"],
            data["subject"],
            data["minutes"],
            data["raw_message"]
        ])

        print(f"✅ {user_id} に記録を追加しました")

    except Exception as e:
        print(f"❌ 学習記録の記入中にエラーが発生しました: {e}")


# 👥 学習記録または目標に登場する全 user_id を取得
def get_all_user_ids():
    print(f"🧪 GOAL_SHEET_NAME: '{GOAL_SHEET_NAME}'")
    client = authorize_sheet()
    sheet_names = [ws.title for ws in client.open("StudyMeBotStudyLog").worksheets()]
    print("📄 存在するシート一覧:", sheet_names)
    goal_sheet = client.open("StudyMeBotStudyLog").worksheet(GOAL_SHEET_NAME)
    study_sheet = client.open("StudyMeBotStudyLog").worksheet("StudyLog")

    goal_ids = [row["user_id"] for row in goal_sheet.get_all_records()]
    study_ids = [row["user_id"] for row in study_sheet.get_all_records()]
    return list(set(goal_ids + study_ids))

# 🎯 今日の目標（分）を取得
def get_today_goal(user_id, date_str):
    client = authorize_sheet()
    sheet = client.open("StudyMeBotStudyLog").worksheet(GOAL_SHEET_NAME)
    records = sheet.get_all_records()
    for row in records:
        if row["user_id"] == user_id and row["start_date"] == date_str:
            return int(row["value"])
    return None

# 📚 今日の学習合計時間（分）を取得
def get_today_study_minutes(user_id, date_str):
    client = authorize_sheet()
    sheet = client.open("StudyMeBotStudyLog").worksheet("StudyLog")
    records = sheet.get_all_records()
    total = 0
    for row in records:
        if row["user_id"] == user_id and row["datetime"].startswith(date_str):
            total += int(row["minutes"])
    return total

# 🔐 gspread 接続用共通関数
def authorize_sheet():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds_dict = json.loads(os.environ["GOOGLE_CREDS_JSON"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)
