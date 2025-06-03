import gspread
import os
import json
import pandas as pd
import tempfile
from oauth2client.service_account import ServiceAccountCredentials

# 環境変数から credentials.json を読み込む（Render用）
def get_credentials_from_env():
    creds_dict = json.loads(os.environ.get("GOOGLE_CREDS_JSON"))
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(creds_dict, f)
        return f.name

# 認証とクライアント生成
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
cred_path = get_credentials_from_env()
creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
client = gspread.authorize(creds)

# 以降は今まで通りの処理でOK
spreadsheet = client.open("StudyMeBotStudyLog")
main_sheet = spreadsheet.worksheet("StudyLog")
data = main_sheet.get_all_records()
df = pd.DataFrame(data)
df.columns = [col.strip() for col in df.columns]
df = df.dropna(subset=["user_id"])

# ユーザーごとに分割
for user_id in df['user_id'].unique():
    user_df = df[df['user_id'] == user_id]

    try:
        ws = spreadsheet.worksheet(user_id)
        spreadsheet.del_worksheet(ws)
        print(f"🔁 既存シート '{user_id}' を削除しました")
    except gspread.exceptions.WorksheetNotFound:
        print(f"✅ 新規シート '{user_id}' を作成します")

    new_sheet = spreadsheet.add_worksheet(title=user_id, rows="1000", cols="5")
    new_sheet.append_row(["datetime", "subject", "minutes", "raw_message"])
    for _, row in user_df.iterrows():
        new_sheet.append_row([
            row["datetime"], row["subject"], row["minutes"], row["raw_message"]
        ])

print("✅ 全ユーザーのシート分割が完了しました！")
