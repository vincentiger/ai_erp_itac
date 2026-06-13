# backend/routes/ai.py
import json
import os
import re
from flask import Blueprint, request, jsonify
from datetime import date, datetime, timedelta

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")
_KB_CACHE = None
_KB_MTIME = None

def _safe_str(x, max_len=None):
    s = "" if x is None else str(x).strip()
    return s[:max_len] if (max_len and s) else s

def _ymd(d: date):
    return d.strftime("%Y-%m-%d")

def _month_range(y: int, m: int):
    start = date(y, m, 1)
    if m == 12:
        end = date(y + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(y, m + 1, 1) - timedelta(days=1)
    return start, end


def _normalize_text(text):
    t = _safe_str(text, 2000).lower()
    t = t.replace("　", " ")
    t = re.sub(r"[\r\n\t,，。:：;；()（）/\\\\]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _knowledge_file():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(root_dir, "docs", "knowledge-base.json")


def _load_knowledge_entries():
    global _KB_CACHE, _KB_MTIME
    path = _knowledge_file()
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        _KB_CACHE = []
        _KB_MTIME = None
        return []

    if _KB_CACHE is not None and _KB_MTIME == mtime:
        return _KB_CACHE

    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    entries = payload.get("entries") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        entries = []
    _KB_CACHE = entries
    _KB_MTIME = mtime
    return entries


def _search_knowledge(question):
    q = _normalize_text(question)
    if not q:
        return None

    entries = _load_knowledge_entries()
    best = None
    best_score = 0

    for entry in entries:
        title = _safe_str(entry.get("title"))
        category = _safe_str(entry.get("category"))
        answer = _safe_str(entry.get("answer"), 4000)
        keywords = entry.get("keywords") or []
        phrases = [_normalize_text(title), _normalize_text(category)]
        phrases.extend(_normalize_text(v) for v in keywords if _safe_str(v))

        score = 0
        matched = []
        for phrase in phrases:
            if phrase and phrase in q:
                score += max(4, len(phrase))
                matched.append(phrase)

        for kw in keywords:
            token = _normalize_text(kw)
            if token and token in q and token not in matched:
                score += 2

        if title and _normalize_text(title) in q:
            score += 10
        if category and _normalize_text(category) in q:
            score += 3

        if score > best_score and answer:
            best_score = score
            best = entry

    if best_score < 4:
        return None
    return best


@ai_bp.post("/knowledge")
def ai_knowledge():
    body = request.get_json(silent=True) or {}
    text = _safe_str(body.get("text"), 400)
    if not text:
        return jsonify(ok=False, msg="missing text"), 400

    entry = _search_knowledge(text)
    if not entry:
        return jsonify(ok=True, data={"hit": False})

    return jsonify(
        ok=True,
        data={
            "hit": True,
            "title": _safe_str(entry.get("title"), 120),
            "category": _safe_str(entry.get("category"), 80),
            "answer": _safe_str(entry.get("answer"), 4000),
            "sources": entry.get("sources") or [],
            "keywords": entry.get("keywords") or [],
        },
    )

@ai_bp.post("/parse")
def ai_parse():
    """
    input: { text: "去年所有訂單" }
    output:
    {
      ok:true,
      data:{
        action:"navigate",
        target:"order_view",
        reply:"已開啟訂單列表：2025-01-01 ~ 2025-12-31",
        filters:{ date_from:"...", date_to:"...", cust_name:"...", sales_rep:"...", kw:"..." }
      }
    }
    """
    body = request.get_json(silent=True) or {}
    text = _safe_str(body.get("text"), 400)

    if not text:
        return jsonify({"ok": False, "msg": "missing text"}), 400

    t = text.replace("　", " ").strip()

    # ====== 只先做「訂單相對日期」這一類（你列的那些）======
    today = date.today()
    y = today.year
    m = today.month

    def reply_range(df, dt):
        return f"已開啟訂單列表：{df} ~ {dt}"

    filters = {}

    # 近30天
    if "近30天" in t:
        df = _ymd(today - timedelta(days=30))
        dt = _ymd(today)
        filters.update({"date_from": df, "date_to": dt})

    # 本月 / 上月
    elif "本月" in t:
        s, e = _month_range(y, m)
        filters.update({"date_from": _ymd(s), "date_to": _ymd(e)})

    elif "上個月" in t or "上月" in t:
        py, pm = (y - 1, 12) if m == 1 else (y, m - 1)
        s, e = _month_range(py, pm)
        filters.update({"date_from": _ymd(s), "date_to": _ymd(e)})

    # 今年 / 去年 / 指定年份
    elif "今年" in t:
        filters.update({"date_from": f"{y}-01-01", "date_to": f"{y}-12-31"})

    elif "去年" in t:
        filters.update({"date_from": f"{y-1}-01-01", "date_to": f"{y-1}-12-31"})

    else:
        # 例如：2024年訂單
        m_year = re.search(r"(20\d{2})\s*年", t)
        if m_year:
            yy = int(m_year.group(1))
            filters.update({"date_from": f"{yy}-01-01", "date_to": f"{yy}-12-31"})

    # 客戶A / 公司A（簡化：抓「客戶/公司」後面的字串）
    # 你之後可以改成更嚴謹的 parser
    m_cust = re.search(r"(客戶|公司)\s*([^\s]+)", t)
    if m_cust:
        filters["cust_name"] = m_cust.group(2)

    # 業務張三 / 我（簡化）
    m_rep = re.search(r"業務\s*([^\s]+)", t)
    if m_rep:
        filters["sales_rep"] = m_rep.group(1)
    if t.startswith("我"):
        # 你可在這裡接登入使用者 name → sales_rep
        # 先保留空，讓前端可傳 currentUserName 再補
        pass

    # 尚未出清（先用旗標，後端 order/list 你之後再接）
    if "未出清" in t:
        filters["unshipped"] = "1"

    # 如果這句根本沒解析出日期條件，就回 chat
    if not filters:
        return jsonify({
            "ok": True,
            "data": {
                "action": "chat",
                "reply": "請輸入例如：去年所有訂單 / 本月訂單 / 近30天訂單 / 客戶A 去年所有訂單"
            }
        })

    df = filters.get("date_from", "")
    dt = filters.get("date_to", "")
    return jsonify({
        "ok": True,
        "data": {
            "action": "navigate",
            "target": "order_view",
            "reply": reply_range(df, dt) if df or dt else "已開啟訂單列表",
            "filters": filters
        }
    })
