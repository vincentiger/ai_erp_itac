from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from flask import request


def json_safe(v: Any) -> Any:
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


def rows_to_dicts(cur) -> List[Dict[str, Any]]:
    cols = [c[0] for c in cur.description]
    out: List[Dict[str, Any]] = []
    for row in cur.fetchall():
        out.append({cols[i]: json_safe(row[i]) for i in range(len(cols))})
    return out


def qdate(name: str) -> Optional[str]:
    """read querystring date YYYY-MM-DD; return str or None"""
    v = (request.args.get(name) or "").strip()
    return v or None


def qint(name: str, default: int) -> int:
    try:
        return int(request.args.get(name, default))
    except Exception:
        return default


def qfloat(name: str, default: float) -> float:
    try:
        return float(request.args.get(name, default))
    except Exception:
        return default

def fmt_date_ymd(v):
    """
    將 date / datetime 轉為 yyyy-mm-dd
    其他型別原樣回傳
    """
    if isinstance(v, (date, datetime)):
        return v.strftime("%Y-%m-%d")
    return v

def ok(data, **meta):
    return {"ok": True, "data": data, **meta}


def err(msg, code=400):
    return {"ok": False, "error": msg}, code
