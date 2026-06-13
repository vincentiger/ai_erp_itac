# backend/routes/ar_manage.py
from flask import Blueprint, current_app, jsonify, request
import logging
from datetime import date

bp = Blueprint("ar_manage_bp", __name__, url_prefix="/api/ar")
logger = logging.getLogger("ai_erp.backend")

def get_db_conn():
    return current_app.config["GET_DB_CONN"]()

def qstr(name, default=""):
    v = request.args.get(name, default)
    return (v or "").strip()

def actor():
    return (request.headers.get("X-User") or "").strip() or "unknown"

def qint(v, default=0):
    try:
        return int(v)
    except Exception:
        return default
def parse_ymd(s: str):
    # 允許 YYYY-MM-DD，失敗回 None
    try:
        if not s:
            return None
        y, m, d = s.split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None

def default_5y_range():
    today = date.today()
    # 以同月同日往回 5 年
    return (date(today.year - 5, today.month, today.day), today)

@bp.post("/cancel")
def ar_cancel():
    """
    取消/復原：呼叫 SP 同步更新 shipment_docs + ar_invoice
    body: { form_no, isCanceled, reason }
    """
    data = request.get_json(silent=True) or {}
    form_no = (data.get("form_no") or "").strip()
    is_canceled = 1 if str(data.get("isCanceled") or "0") in ("1","true","True") else 0
    reason = (data.get("reason") or "").strip() or None
    who = actor()

    if not form_no:
        return jsonify({"ok": False, "msg": "缺少 form_no"}), 400

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("EXEC dbo.sp_ar_set_canceled ?, ?, ?, ?", (form_no, is_canceled, who, reason))
        conn.commit()

        logger.info(f"[AR][cancel] actor={who} form_no={form_no} isCanceled={is_canceled} reason={reason}")
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception(f"[AR][cancel][ERR] actor={who} form_no={form_no} err={e}")
        return jsonify({"ok": False, "msg": str(e)}), 500

@bp.post("/cancel-batch")
def ar_cancel_batch():
    """
    批次取消/復原（多筆 form_no）：
    body: { form_nos:[], isCanceled:1|0, reason }
    """
    data = request.get_json(silent=True) or {}
    form_nos = data.get("form_nos") or []
    is_canceled = 1 if str(data.get("isCanceled") or "0") in ("1","true","True") else 0
    reason = (data.get("reason") or "").strip() or None
    who = actor()

    form_nos = [str(x).strip() for x in form_nos if str(x).strip()]
    if not form_nos:
        return jsonify({"ok": False, "msg": "缺少 form_nos"}), 400

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        ok_count = 0
        for form_no in form_nos:
            cur.execute("EXEC dbo.sp_ar_set_canceled ?, ?, ?, ?", (form_no, is_canceled, who, reason))
            ok_count += 1

        conn.commit()
        logger.info(f"[AR][cancel-batch] actor={who} count={ok_count} isCanceled={is_canceled} reason={reason}")
        return jsonify({"ok": True, "count": ok_count})
    except Exception as e:
        logger.exception(f"[AR][cancel-batch][ERR] actor={who} err={e}")
        return jsonify({"ok": False, "msg": str(e)}), 500

from datetime import datetime

def qnum(v, default=0):
    try:
        return float(v)
    except Exception:
        return default
    
def qint_from_body(data, name, default=0):
    try:
        return int(str(data.get(name, default)).strip())
    except Exception:
        return default


@bp.post("/receipt-create")
def receipt_create():
    """
    新增收款（dbo.ar_receipt）
    body: {
      customer_id,
      customer_name(optional),
      receipt_date(YYYY-MM-DD),
      currency,
      receipt_amount,
      method(optional),
      bank_ref(optional)
    }
    """
    data = request.get_json(silent=True) or {}
    customer_id = qint_from_body(data, "customer_id", 0)
    customer_name = (data.get("customer_name") or "").strip() or None
    receipt_date = (data.get("receipt_date") or "").strip()
    currency = (data.get("currency") or "").strip()
    receipt_amount = qnum(data.get("receipt_amount"), 0)
    method = (data.get("method") or "").strip() or None
    bank_ref = (data.get("bank_ref") or data.get("memo") or "").strip() or None  # ✅ 兼容前端還叫 memo 的情況
    who = actor()

    if not customer_id:
        return jsonify({"ok": False, "msg": "缺少 customer_id"}), 400
    if not receipt_date:
        return jsonify({"ok": False, "msg": "缺少 receipt_date"}), 400
    if not currency:
        return jsonify({"ok": False, "msg": "缺少 currency"}), 400
    if receipt_amount <= 0:
        return jsonify({"ok": False, "msg": "receipt_amount 必須 > 0"}), 400

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        # ✅ ar_receipt 實際欄位：customer_id/customer_name/currency/receipt_amount/receipt_date/method/bank_ref
        # ✅ 新增欄位：created_by/created_at
        sql = """
        INSERT INTO dbo.ar_receipt
          (customer_id, customer_name, currency, receipt_amount, receipt_date, method, bank_ref, created_by, created_at)
        OUTPUT INSERTED.receipt_id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
        """

        cur.execute(sql, (
            customer_id,
            customer_name,
            currency,
            receipt_amount,
            receipt_date,
            method,
            bank_ref,
            who,
        ))
        row = cur.fetchone()
        conn.commit()

        receipt_id = int(row[0]) if row else None
        return jsonify({"ok": True, "receipt_id": receipt_id})
    except Exception as e:
        logger.exception(f"[AR][receipt-create][ERR] actor={who} customer_id={customer_id} err={e}")
        return jsonify({"ok": False, "msg": str(e)}), 500

@bp.get("/open-list")
def open_list():
    customer_kw = qstr("customer_kw", "")
    date_from = qstr("from", "")
    date_to = qstr("to", "")

    page = qint("page", 1)
    pageSize = qint("pageSize", 50)
    if page < 1: page = 1
    if pageSize < 1: pageSize = 50
    if pageSize > 200: pageSize = 200  # 防呆：避免一次拉太多

    skip = (page - 1) * pageSize

    # ✅ 共用 WHERE（你原本條件）
    where_sql = """
      WHERE b.open_amount > 0
        AND ISNULL(ai.isCanceled, 0) = 0
        AND ISNULL(s.isCanceled, 0) = 0
        AND LEFT(RIGHT(src.ship_form_no, 3), 1) NOT IN ('N','R')
        AND (? = '' OR c.refno LIKE ? OR c.company LIKE ? OR c.short LIKE ?)
    """

    # ✅ 共用 FROM/JOIN（把你原本 FROM..JOIN 貼進來）
    from_sql = """
      FROM dbo.vw_ar_invoice_src src
      JOIN dbo.v_ar_invoice_balance b ON b.form_no = src.ship_form_no
      JOIN dbo.orders r ON r.form_no = src.order_form_no
      JOIN dbo.customer c ON c.id = r.customer_id
      JOIN dbo.shipment_docs s ON s.form_no = src.ship_form_no
      JOIN dbo.ar_invoice ai ON ai.form_no = src.ship_form_no
    """

    # ✅ 排序固定（一定要穩定，不然分頁會跳）
    order_sql = " ORDER BY s.close_date DESC, src.ship_form_no DESC "

    # 1) total
    sql_total = f"SELECT COUNT(1) AS total {from_sql} {where_sql}"

    # 2) page rows（SQL2000: TOP + NOT IN）
    sql_rows = f"""
      SELECT TOP {pageSize}
        s.close_date AS ship_date,
        c.id AS customer_id,
        c.refno AS customer_refno,
        c.short AS customer_short,
        c.company AS customer_name,
        src.in_no AS display_no,
        src.currency,
        b.payable_amount,
        b.applied_amount,
        b.open_amount,
        ISNULL(ai.isCanceled, 0) AS isCanceled,
        src.ship_form_no AS internal_form_no
      {from_sql}
      {where_sql}
      {"AND src.ship_form_no NOT IN (SELECT TOP " + str(skip) + " src2.ship_form_no " + from_sql.replace("src", "src2") + " " + where_sql.replace("src.", "src2.") + order_sql + ")" if skip > 0 else ""}
      {order_sql}
    """

    # ✅ LIKE 參數
    kw_like = f"%{customer_kw}%"
    params = (customer_kw, kw_like, kw_like, kw_like)

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        # total
        cur.execute(sql_total, params)
        total = int(cur.fetchone()[0] or 0)

        # rows
        if skip > 0:
            # 注意：skip 的子查詢也需要同樣 params（重複一次）
            cur.execute(sql_rows, params + params)
        else:
            cur.execute(sql_rows, params)

        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return jsonify({"ok": True, "total": total, "rows": rows})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@bp.get("/receipts")
def receipts():
    """
    收款清單（尚未分攤）：
    - 以 customer_kw（refno/company/short）找 customer_id（TOP 1）
    - 再查 v_ar_receipt_balance（未分攤>0），預設 5 年內
    """
    customer_kw = qstr("customer_kw", "")
    top = qstr("top", "")
    top_n = int(top) if top.isdigit() else 500

    d_from = parse_ymd(qstr("from", ""))
    d_to = parse_ymd(qstr("to", ""))
    if not d_from or not d_to:
        d_from, d_to = default_5y_range()

    if not customer_kw:
        return jsonify({"ok": False, "msg": "缺少 customer_kw"}), 400

    sql_find_cust = f"""
      SELECT TOP 1 id
      FROM dbo.customer
      WHERE
        refno  LIKE '%' + ? + '%' OR
        company LIKE '%' + ? + '%' OR
        short  LIKE '%' + ? + '%'
      ORDER BY refno
    """

    # ⚠️ 這裡假設 v_ar_receipt_balance 有 receipt_date 欄位
    sql_receipts = f"""
      SELECT TOP {top_n}
      c.company AS customer_name,
      c.refno AS customer_refno,
      vb.receipt_id,
      ar.receipt_date AS receipt_date,
      vb.customer_id,
      vb.currency,
      vb.receipt_amount,
      vb.applied_amount,
      vb.unapplied_amount
      FROM dbo.v_ar_receipt_balance vb
      LEFT JOIN dbo.customer c ON c.id = vb.customer_id
      JOIN dbo.ar_receipt ar
      ON ar.receipt_id = vb.receipt_id
      WHERE vb.customer_id = ?
      AND vb.unapplied_amount > 0
      AND ar.receipt_date >= ? AND ar.receipt_date <= ?
      ORDER BY vb.receipt_id DESC
     """

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute(sql_find_cust, (customer_kw, customer_kw, customer_kw))
        row = cur.fetchone()
        if not row:
            return jsonify({"ok": True, "rows": []})

        cust_id = row[0]

        cur.execute(sql_receipts, (cust_id, d_from, d_to))
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return jsonify({
          "ok": True,
          "customer_kw": customer_kw,
          "customer_id": cust_id,
          "rows": rows
          })
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
