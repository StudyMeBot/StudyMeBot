import gspread
from google.oauth2.service_account import Credentials

# スコープ設定（Google Sheets & Drive）
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 認証情報を読み込み
creds = Credentials.from_service_account_file(
    "credentials.json", scopes=SCOPES
)

# スプレッドシートにアクセス
gc = gspread.authorize(creds)

# スプレッドシート名を指定して開く
sh = gc.open("StudyMeBotNotify")
worksheet = sh.sheet1

# 中身を確認（全行）
records = worksheet.get_all_records()
for row in records:
    print(row)
