import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# 認証
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# スプレッドシートを開く
spreadsheet = client.open("StudyMeBotStudyLog")
main_sheet = spreadsheet.worksheet("StudyLog")
data = main_sheet.get_all_records()
df = pd.DataFrame(data)

# ユーザーごとに分割（StudyLogは残す）
for user_id in df['user_id'].unique():
    user_df = df[df['user_id'] == user_id]

    # 既存のシートがあれば削除
    try:
        ws = spreadsheet.worksheet(user_id)
        spreadsheet.del_worksheet(ws)
        print(f"🔁 既存シート '{user_id}' を削除しました")
    except gspread.exceptions.WorksheetNotFound:
        print(f"✅ 新規シート '{user_id}' を作成します")

    # 新規シート作成
    new_sheet = spreadsheet.add_worksheet(title=user_id, rows="1000", cols="5")
    new_sheet.append_row(["datetime", "subject", "minutes", "raw_message"])

    for _, row in user_df.iterrows():
        new_sheet.append_row([
            row["datetime"],
            row["subject"],
            row["minutes"],
            row["raw_message"]
        ])

print("✅ ユーザーごとのシート分割が完了しました！")
