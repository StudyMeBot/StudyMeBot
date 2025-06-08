import re

def parse_daily_goal_message(message: str):
    """
    毎日2時間 / 毎日30分 / 毎日1時間30分 / 毎日1時間半 などに対応
    戻り値: {"unit": "daily", "type": "time", "value": 分数}
    """
    # 「1時間30分」「1時間半」「90分」などをカバー
    match = re.search(r"毎日(?:(\d+)時間半|(\d+)時間(\d+)分|(\d+)時間|(\d+)分)", message)
    if not match:
        return None

    total_minutes = 0

    if match.group(1):  # 1時間半
        total_minutes = int(match.group(1)) * 60 + 30
    elif match.group(2) and match.group(3):  # 1時間30分
        total_minutes = int(match.group(2)) * 60 + int(match.group(3))
    elif match.group(4):  # 1時間
        total_minutes = int(match.group(4)) * 60
    elif match.group(5):  # 30分
        total_minutes = int(match.group(5))

    return {
        "unit": "daily",
        "type": "time",
        "value": total_minutes
    }
