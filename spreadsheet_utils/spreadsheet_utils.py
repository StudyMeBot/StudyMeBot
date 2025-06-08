# spreadsheet_utils.py

import gspread
from google.oauth2.service_account import Credentials
import json, os, tempfile

def get_credentials_from_env():
    creds_dict = json.loads(os.getenv("GOOGLE_CREDS_JSON"))
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp:
        json.dump(creds_dict, tmp)
        return tmp.name

def update_notification_time(user_id, time_period_jp, new_time):
    # ラベル変換（日本語 → 英語列名）
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
        sh = gc.open("StudyMeBotNotify")  # スプレッドシート名
        worksheet = sh.sheet1
        records = worksheet.get_all_records()

        # user_idがあるかどうか確認
        found = False
        for idx, record in enumerate(records, start=2):  # 2行目から
            if record.get("user_id") == user_id:
                col_num = worksheet.find(col_label).col
                worksheet.update_cell(idx, col_num, new_time)
                found = True
                return f"{time_period_jp}の通知時間を「{new_time}」に更新しました。"

        # なければ新しい行を追加（初期値は全てOFF）
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
        return f"スプレッドシートの更新中にエラーが発生しました：[e]"

# ✅ 学習記録用の関数（新規追加）
def record_study_log(data):
    """
    学習記録を StudyLog シートに記録し、
    各 user_id ごとの個別シートにも同時に追記します。
    """
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        cred_path = get_credentials_from_env()
        credentials = Credentials.from_service_account_file(cred_path, scopes=scope)
        gc = gspread.authorize(credentials)

        sh = gc.open("StudyMeBotStudyLog")

        # === StudyLog に記録 ===
        main_ws = sh.worksheet("StudyLog")
        main_row = [
            data["datetime"],
            data["user_id"],
            data["subject"],
            data["minutes"],
            data["raw_message"]
        ]
        main_ws.append_row(main_row)

        # === 各 user_id シートにも記録 ===
        user_id = data["user_id"]
        try:
            user_ws = sh.worksheet(user_id)
        except gspread.exceptions.WorksheetNotFound:
            user_ws = sh.add_worksheet(title=user_id, rows="1000", cols="4")
            user_ws.append_row(["datetime", "subject", "minutes", "raw_message"])  # ヘッダー追加

        user_ws.append_row([
            data["datetime"],
            data["subject"],
            data["minutes"],
            data["raw_message"]
        ])

        print(f"✅ {user_id} に記録を追加しました")

    except Exception as e:
        print(f"❌ 学習記録の記入中にエラーが発生しました：{e}")
