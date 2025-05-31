# spreadsheet_utils.py

import gspread
from google.oauth2.service_account import Credentials

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
        credentials = Credentials.from_service_account_file("credentials.json", scopes=scope)
        gc = gspread.authorize(credentials)

        # スプレッドシートとワークシートを開く
        sh = gc.open("StudyMeBotLog")  # ← スプレッドシート名を確認
        worksheet = sh.sheet1

        # 全レコード取得
        records = worksheet.get_all_records()

        # user_idで行を探す（2行目から）
        for idx, record in enumerate(records, start=2):
            if record["user_id"] == user_id:
                # 対象列を見つけて更新
                col_num = worksheet.find(col_label).col
                worksheet.update_cell(idx, col_num, new_time)
                return f"{time_period_jp}の通知時間を「{new_time}」に更新しました。"

        return "ユーザー情報がスプレッドシートに見つかりませんでした。"

    except Exception as e:
        return f"スプレッドシートの更新中にエラーが発生しました：{e}"
