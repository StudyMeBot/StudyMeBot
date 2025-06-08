from datetime import datetime

def get_today_dates():
    """
    今日の日付を取得し、start_date / end_date / created_at として返す
    フォーマット：YYYY/MM/DD
    """
    today_str = datetime.today().strftime("%Y/%m/%d")
    return today_str, today_str, today_str
