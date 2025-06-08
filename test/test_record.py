from spreadsheet_utils import record_study_log
from datetime import datetime

# テストデータを作成
data = {
    "datetime": datetime.now().isoformat(),
    "user_id": "test_user_abc",
    "subject": "テスト科目",
    "minutes": 45,
    "raw_message": "テスト科目45分"
}

# 関数呼び出し
record_study_log(data)
