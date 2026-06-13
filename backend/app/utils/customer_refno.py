import re
from datetime import datetime
from flask import request, jsonify

def _safe_int(x, default=None):
    try:
        return int(x)
    except:
        return default

def _get_prefix(cur, no1: int, no2: int) -> str:
    row = cur.execute("""
        SELECT
          LTRIM(RTRIM(ISNULL(c1.symbol,''))) AS s1,
          LTRIM(RTRIM(ISNULL(c2.symbol,''))) AS s2
        FROM dbo.cate_cust01 c1
        JOIN dbo.cate_cust02 c2 ON c2.no1 = c1.id
        WHERE c1.cate='c' AND c1.id=? AND c2.cate='c' AND c2.id=?
    """, (no1, no2)).fetchone()

    if not row:
        return ""
    return f"{row.s1}{row.s2}".strip()

def _next_refno(cur, prefix: str) -> str:
    # 找最新 refno（同 prefix）
    row = cur.execute("""
        SELECT TOP 1 refno
        FROM dbo.customer
        WHERE refno LIKE ?
        ORDER BY refno DESC
    """, (prefix + '%',)).fetchone()

    if not row or not row.refno:
        return f"{prefix}{1:03d}"

    last = str(row.refno).strip()
    # 取 suffix（最後連續數字）
    m = re.search(r'(\d+)$', last)
    if not m:
        return f"{prefix}{1:03d}"

    seq = int(m.group(1)) + 1
    return f"{prefix}{seq:03d}"
