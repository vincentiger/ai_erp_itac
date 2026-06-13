# backend/utils/safe.py
from datetime import datetime

def _safe_str(x, max_len=None):
    if x is None:
        return ""
    s = str(x).strip()
    if max_len:
        s = s[:max_len]
    return s

def _to_int(x, default=None):
    try:
        return int(x)
    except:
        return default

def _safe_sort_dir(x: str):
    x = _safe_str(x, 8).lower()
    return "asc" if x == "asc" else "desc"

def _safe_date_ymd(x: str):
    """
    允許 YYYY-MM-DD，回傳字串（給 SQL 參數），不合法回傳 ""
    """
    s = _safe_str(x, 10)
    if not s:
        return ""
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except:
        return ""
