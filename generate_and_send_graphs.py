import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import requests
import tempfile
import shutil

# === LINE設定 ===
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")  # 環境変数から読み込み

# === Google認証 ===
def get_credentials_from_env():
    creds_dict = json.loads(os.environ.get("GOOGLE_CREDS_JSON"))
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump(creds_dict, f)
        return f.name

scope = [
    'https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'
]
cred_path = get_credentials_from_env()
credentials = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
gc = gspread.authorize(credentials)
sh = gc.open("StudyMeBotStudyLog")

# === 日付 ===
today = datetime.today().date()
start_of_day = today
periods = {
    "day": start_of_day
}

# === LINE送信関数 ===
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

def send_text_to_line(user_id, message):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": message
        }]
    }
    r = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload)
    print(f"Text sent to {user_id}: {r.status_code}, {r.text}")

# === グラフ生成関数 ===
def generate_graph(df, user_id, period_label, start_date):
    df_period = df[df["date"] >= start_date]
    summary = df_period.groupby("subject")["minutes"].sum().sort_values(ascending=False)

    if summary.empty:
        print(f"⚠️ No study data for {user_id} in {period_label}. Skipping.")
        return None

    total = summary.sum()

    plt.figure(figsize=(6, 4))
    summary.plot(kind="bar", color="skyblue")
    plt.title(f"{period_label.upper()}の学習時間 (合計: {total}分)")
    plt.ylabel("学習時間（分）")
    plt.xlabel("科目")
    plt.xticks(rotation=0)
    plt.tight_layout()

    os.makedirs("static", exist_ok=True)
    filename = f"study_chart_{period_label}_{user_id}.png"
    path = f"static/{filename}"
    plt.savefig(path)
    plt.close()
    print(f"✅ 保存パス: {path}")
    print(f"✅ URL: https://studymebot-1lgo.onrender.com/static/{filename}")

    return filename

# === user_id → line_user_id のマッピングをStudyLogから取得 ===
df_log = pd.DataFrame(sh.worksheet("StudyLog").get_all_records())
id_map = {uid: uid for uid in df_log["user_id"].unique()}

# === 各ユーザーを処理 ===
for user_id, line_user_id in id_map.items():
    if user_id not in [ws.title for ws in sh.worksheets()]:
        continue

    sheet = sh.worksheet(user_id)
    df = pd.DataFrame(sheet.get_all_records())
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["date"] = df["datetime"].dt.date
    df["minutes"] = df["minutes"].astype(int)
    print(f"📆 最新データ: {df['date'].max()}")

    # === 今日のグラフだけ生成・送信 ===
    filename = generate_graph(df, user_id, "day", start_of_day)
    if filename:
        image_url = f"https://studymebot-1lgo.onrender.com/static/{filename}"
        send_image_to_line(line_user_id, image_url)
    else:
        message = "今日は学習記録がありませんでした。明日は忘れずに記録をつけましょう！📚"
        send_text_to_line(line_user_id, message)
