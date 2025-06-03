import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import requests
import tempfile

# === LINE設定 ===
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")  # 環境変数から読み込み
USER_ID_MAP = {
    "test_user_abc": os.getenv("LINE_USER_ID_TEST"),  # 各ユーザーのLINE IDをマッピング
    # 他のユーザーも追加可能
}

# === Google認証 ===
def get_credentials_from_env():
    creds_dict = json.loads(os.environ.get("GOOGLE_CREDS_JSON"))
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(creds_dict, f)
        return f.name

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
cred_path = get_credentials_from_env()
creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
client = gspread.authorize(creds)
spreadsheet = client.open("StudyMeBotStudyLog")

# === 日付 ===
today = datetime.today().date()
start_of_week = today - timedelta(days=today.weekday())
start_of_month = today.replace(day=1)

# === LINE送信処理 ===
def send_image_to_line(user_id, image_url):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": user_id,
        "messages": [{
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url
        }]
    }
    r = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)
    print(f"Sent to {user_id}: {r.status_code}, {r.text}")

# === グラフ生成 ===
def generate_graph(df, user_name, period_label, start_date):
    df_period = df[df["date"] >= start_date]
    summary = df_period.groupby("subject")["minutes"].sum().sort_values(ascending=False)
    total = summary.sum()

    plt.figure(figsize=(6, 4))
    summary.plot(kind="bar", color="skyblue")
    plt.title(f"{period_label.upper()}の学習時間（合計: {total}分）")
    plt.ylabel("学習時間（分）")
    plt.xlabel("科目")
    plt.xticks(rotation=0)
    plt.tight_layout()

    filename = f"study_chart_{period_label}_{user_name}.png"
    path = f"/mnt/data/{filename}"
    plt.savefig(path)
    plt.close()
    return filename

# === 各ユーザー処理 ===
def process_user_sheet(sheet):
    user_name = sheet.title
    if user_name == "StudyLog":
        return

    records = sheet.get_all_records()
    if not records:
        return

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    line_user_id = USER_ID_MAP.get(user_name)
    if not line_user_id:
        print(f"LINE ID not found for user {user_name}")
        return

    periods = {
        "day": today,
        "week": start_of_week,
        "month": start_of_month
    }

    for label, start in periods.items():
        filename = generate_graph(df, user_name, label, start)
        public_url = f"https://your-render-app.onrender.com/static/{filename}"
        send_image_to_line(line_user_id, public_url)

# === 実行 ===
for sheet in spreadsheet.worksheets():
    process_user_sheet(sheet)
