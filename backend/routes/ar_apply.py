# backend/routes/ar_apply.py
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from utils.include import qint  # 你專案現成的

bp = Blueprint("ar_apply_api", __name__, url_prefix="/api/ar/apply")


def get_db_conn():
    return current_app.config["GET_DB_CONN"]()


def _rows_to_dicts(cursor):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _sql_error_to_msg(e: Exception) -> str:
    return str(e)


def _actor() -> str:
    return (request.headers.get("X-User") or "").strip() or "unknown"

def _fill_customer_info(conn, receipt: dict) -> dict:
    if not receipt:
        return receipt

    cid = receipt.get("customer_id")
    if not cid:
        receipt["_debug_cust"] = "no customer_id in receipt"
        return receipt

    if receipt.get("customer_name") or receipt.get("customer_refno"):
        receipt["_debug_cust"] = "already has customer_name/refno"
        return receipt

    try:
        # ✅ 用新的 connection，避開「同連線 busy」
        conn2 = get_db_conn()
        cur2 = conn2.cursor()
        cur2.execute(
            """
            SELECT TOP 1
              c.company AS customer_name,
              c.refno   AS customer_refno,
              c.short   AS customer_short
            FROM dbo.customer c
            WHERE c.id = ?
            """,
            (cid,),
        )
        r = cur2.fetchone()
        cur2.close()
        conn2.close()

        if not r:
            receipt["_debug_cust"] = f"customer not found by id={cid}"
            return receipt

        receipt["customer_name"] = r[0]
        receipt["customer_refno"] = r[1]
        receipt["customer_short"] = r[2]
        receipt["_debug_cust"] = "ok"
        return receipt

    except Exception as e:
        receipt["_debug_cust"] = f"lookup error: {e}"
        return receipt

# -------------------------
# ✅ GET: db-whoami
# -------------------------
@bp.get("/db-whoami")
def db_whoami():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
              DB_NAME()            AS db_name,
              @@SERVERNAME         AS server_name,
              @@SERVICENAME        AS service_name,
              @@SPID               AS spid,
              SUSER_SNAME()        AS suser_sname,
              USER_NAME()          AS user_name,
              ORIGINAL_LOGIN()     AS original_login
            """
        )
        row = cur.fetchone()
        cols = [c[0] for c in cur.description]
        return jsonify({"ok": True, "info": dict(zip(cols, row))})
    except Exception as e:
        return jsonify({"ok": False, "msg": _sql_error_to_msg(e)}), 500


# -------------------------
# ✅ GET: context
# -------------------------
@bp.get("/context")
def get_apply_context():
    receipt_id = qint("receipt_id", None)
    ar_id = qint("ar_id", None)
    if not receipt_id or not ar_id:
        return jsonify({"ok": False, "msg": "receipt_id 與 ar_id 必填"}), 400

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("EXEC dbo.sp_ar_get_apply_context @receipt_id=?, @ar_id=?", (receipt_id, ar_id))
        receipt = receipt_rows[0] if receipt_rows else None
        receipt = _fill_customer_info(conn, receipt)

        return jsonify({
        "ok": True,
        "receipt": receipt,
        "invoice": invoice_rows[0] if invoice_rows else None
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": _sql_error_to_msg(e)}), 500


# -------------------------
# ✅ GET: candidates
# -------------------------
@bp.get("/candidates")
def get_receipt_candidates():
    receipt_id = qint("receipt_id", None)
    top = qint("top", 50)
    if not receipt_id:
        return jsonify({"ok": False, "msg": "receipt_id 必填"}), 400
    if top <= 0:
        top = 50
    if top > 500:
        top = 500

    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("EXEC dbo.sp_ar_get_receipt_candidates @receipt_id=?, @top=?", (receipt_id, top))

    # ✅ 逐個 result-set 取出並「吃乾淨」，避免 Connection busy
    receipt_rows = _rows_to_dicts(cur) if cur.description else []

    invoices = []
    # 第二個 result-set（invoices）
    if cur.nextset():
        if cur.description:
            invoices = _rows_to_dicts(cur)

    # ✅ 重要：把剩下的 result-set 全部 nextset 掃完（就算沒有用也要掃）
    while True:
        try:
            has_more = cur.nextset()
        except Exception:
            break
        if not has_more:
            break
        # 若還有沒用的 result-set，也要 fetch 掉
        if cur.description:
            cur.fetchall()

    cur.close()  # ✅ 關掉 SP cursor，連線才不會 busy

    receipt = receipt_rows[0] if receipt_rows else None
    receipt = _fill_customer_info(conn, receipt)  # ✅ 現在查 customer 就不會 busy

    return jsonify({"ok": True, "receipt": receipt, "invoices": invoices, "top": top})


# -------------------------
# ✅ GET: receipt-applies
# -------------------------
@bp.get("/receipt-applies")
def get_receipt_applies():
    receipt_id = qint("receipt_id", None)
    if not receipt_id:
        return jsonify({"ok": False, "msg": "receipt_id 必填"}), 400

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("EXEC dbo.sp_ar_get_receipt_applies @receipt_id=?", (receipt_id,))
        rows = _rows_to_dicts(cur) if cur.description else []
        return jsonify({"ok": True, "receipt_id": receipt_id, "applies": rows})
    except Exception as e:
        return jsonify({"ok": False, "msg": _sql_error_to_msg(e)}), 500


# -------------------------
# ✅ POST: apply payment
# -------------------------
@bp.post("/payment")
def post_apply_payment():
    """
    POST /api/ar/apply/payment
    body: { receipt_id, ar_id, apply_amount, memo? }
    header: X-User

    對應你目前的 SP：
    sp_ar_apply_payment(@receipt_id, @ar_id, @apply_amount, @actor, @memo)
    """
    data = request.get_json(silent=True) or {}

    receipt_id = int(data.get("receipt_id") or 0)
    ar_id = int(data.get("ar_id") or 0)
    try:
        apply_amount = float(data.get("apply_amount") or 0)
    except Exception:
        apply_amount = 0

    memo = (data.get("memo") or "").strip() or None
    who = _actor()

    if receipt_id <= 0 or ar_id <= 0 or apply_amount <= 0:
        return jsonify({"ok": False, "msg": "receipt_id、ar_id、apply_amount 必填且需 > 0"}), 400

    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "EXEC dbo.sp_ar_apply_payment "
            "@receipt_id=?, @ar_id=?, @apply_amount=?, @apply_date=?, @actor=?, @memo=?",
            (
                receipt_id,
                ar_id,
                apply_amount,
                apply_date,     # 可 None
                who,
                memo,
            ),
        )
        conn.commit()
        return jsonify({"ok": True, "msg": "沖帳成功", "receipt_id": receipt_id, "ar_id": ar_id, "actor": who})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "msg": _sql_error_to_msg(e)}), 400


# -------------------------
# ✅ POST: unapply
# -------------------------
@bp.post("/unapply")
def post_unapply_payment():
    """
    POST /api/ar/apply/unapply
    你的 sp_ar_unapply_payment 參數我這裡先「不改動簽名」
    但如果你 SP 也改成必填 @actor，請把 execute 裡面也補上 @actor=?。

    body:
      { apply_id, unapply_amount?, memo?, allow_any_type? }
      （你前端目前主要用 apply_id）
    """
    data = request.get_json(silent=True) or {}
    who = _actor()

    apply_id = data.get("apply_id")
    receipt_id = data.get("receipt_id")
    ar_id = data.get("ar_id")
    apply_amount = data.get("apply_amount")
    apply_date = data.get("apply_date")
    unapply_amount = data.get("unapply_amount")
    memo = data.get("memo")
    allow_any_type = int(data.get("allow_any_type") or 0)

    conn = get_db_conn()
    cur = conn.cursor()
    try:
        # ✅ 這段要依你實際的 sp_ar_unapply_payment 簽名
        # 若你已改 SP 要 @actor，請在最後加 who 並改 SQL 字串
        cur.execute(
            "EXEC dbo.sp_ar_unapply_payment "
            "@apply_id=?, @receipt_id=?, @ar_id=?, @apply_amount=?, @apply_date=?, "
            "@unapply_amount=?, @memo=?, @allow_any_type=?, @actor=?",
            (
                apply_id,
                receipt_id,
                ar_id,
                apply_amount,
                apply_date,
                unapply_amount,
                memo,
                allow_any_type,
                who,
            ),
        )
        conn.commit()
        return jsonify({"ok": True, "msg": "反沖成功", "actor": who})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "msg": _sql_error_to_msg(e)}), 400


# -------------------------
# ✅ POST: FIFO apply receipt
# -------------------------
@bp.post("/fifo")
def post_apply_fifo():
    """
    POST /api/ar/apply/fifo
    body: { receipt_id, apply_total?, memo? }
    header: X-User

    對應你目前的 SP：
    sp_ar_apply_receipt_fifo(@receipt_id, @apply_total, @apply_date, @memo, @actor)
    apply_date 讓 SP 自己預設 GETDATE()，所以傳 None
    """
    data = request.get_json(silent=True) or {}

    receipt_id = int(data.get("receipt_id") or 0)
    apply_total = data.get("apply_total")
    memo = (data.get("memo") or "").strip() or None
    who = _actor()

    if receipt_id <= 0:
        return jsonify({"ok": False, "msg": "receipt_id 必填且需 > 0"}), 400

    if apply_total is not None and str(apply_total).strip() != "":
        try:
            apply_total = float(apply_total)
        except Exception:
            return jsonify({"ok": False, "msg": "apply_total 必須是數字或不填"}), 400
    else:
        apply_total = None

    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "EXEC dbo.sp_ar_apply_receipt_fifo @receipt_id=?, @apply_total=?, @apply_date=?, @memo=?, @actor=?",
            (receipt_id, apply_total, None, memo, who),
        )
        conn.commit()
        return jsonify({"ok": True, "msg": "FIFO 分攤完成", "receipt_id": receipt_id, "actor": who})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "msg": _sql_error_to_msg(e)}), 400


# -------------------------
# ✅ GET: test-pick
# -------------------------
@bp.get("/test-pick")
def test_pick_receipt():
    top = qint("top", 20)
    if top <= 0:
        top = 20
    if top > 200:
        top = 200

    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("EXEC dbo.sp_ar_pick_unapplied_receipt")
        row = cur.fetchone()
        if not row:
            return jsonify({"ok": True, "msg": "目前找不到 unapplied_amount > 0 的 receipt", "receipt": None, "invoices": []})

        receipt_id = int(row[0])

        cur.execute("EXEC dbo.sp_ar_get_receipt_candidates @receipt_id=?, @top=?", (receipt_id, top))
        receipt_rows = _rows_to_dicts(cur) if cur.description else []
        invoices = []
        if cur.nextset() and cur.description:
            invoices = _rows_to_dicts(cur)

        return jsonify(
            {
                "ok": True,
                "picked_receipt_id": receipt_id,
                "receipt": receipt_rows[0] if receipt_rows else None,
                "invoices": invoices,
                "top": top,
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "msg": _sql_error_to_msg(e)}), 500
