import re

def parse_daily_goal_message(message: str):
    """
    毎日2時間 / 毎日30分 などの形式を解析して、
    {"unit": "daily", "type": "time", "value": 120} 形式で返す
    """
    match = re.search(r"毎日(\d+)(時間|分)", message)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    # 時間→分に変換
    if unit == "時間":
        value *= 60

    return {
        "unit": "daily",
        "type": "time",
        "value": value
    }
