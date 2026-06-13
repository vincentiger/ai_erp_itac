# routes/customer_list.py
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("customer_list_api", __name__, url_prefix="/api/customer")


def get_db_conn():
    return current_app.config["GET_DB_CONN"]()


def _safe_int(v, default, min_v=None, max_v=None):
    try:
        n = int(v)
    except Exception:
        n = default
    if min_v is not None and n < min_v:
        n = min_v
    if max_v is not None and n > max_v:
        n = max_v
    return n


def _split_list(s):
    """
    DB 若存成：'a,b,c' 或 'a|b|c' 或 JSON string，都盡量轉成 list
    """
    if s is None:
        return []
    t = str(s).strip()
    if not t:
        return []
    # JSON array string
    if t.startswith("[") and t.endswith("]"):
        try:
            import json
            arr = json.loads(t)
            if isinstance(arr, list):
                return [str(x).strip() for x in arr if str(x).strip()]
        except Exception:
            pass
    # delimiter
    if "|" in t:
        parts = [p.strip() for p in t.split("|")]
    elif "," in t:
        parts = [p.strip() for p in t.split(",")]
    else:
        parts = [t]
    return [p for p in parts if p]


@bp.get("/list")
def list_customers():
    """
    GET /ai/api/customer/list?page=1&pageSize=20&kw=...
    回傳：
    { ok:true, rows:[...], total:123, page:1, pageSize:20 }
    """
    page = _safe_int(request.args.get("page", 1), 1, 1)
    pageSize = _safe_int(request.args.get("pageSize", 20), 20, 1, 200)
    kw = (request.args.get("kw") or "").strip()

    offset = (page - 1) * pageSize

    # ⚠️ 你資料表/欄位名稱可能不同：請把 dbo.customer 換成你的實際表
    base_where = "1=1"
    params = []

    if kw:
        base_where += """
        AND (
            refno LIKE ? OR
            company LIKE ? OR
            short LIKE ? OR
            ceo LIKE ? OR
            LicenceNo LIKE ? OR
            tel LIKE ? OR
            address LIKE ? OR
            contact LIKE ?
        )
        """
        like = f"%{kw}%"
        params += [like, like, like, like, like, like, like, like]

    sql_total = f"""
    SELECT COUNT(1) AS total
    FROM dbo.customer
    WHERE {base_where}
    """

    sql_rows = f"""
    SELECT
        refno,
        company,
        short,
        country,
        headerquarter,
        url,
        ceo,
        Class2,
        items,
        employee,
        quit,
        secret,
        LicenceNo,
        payment,
        credit,
        commission,
        remarks,
        address,
        contact,
        tel,
        fax,
        email,
        sales_rep
    FROM dbo.customer
    WHERE {base_where}
    ORDER BY refno DESC
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(sql_total, params)
        total = int(cur.fetchone()[0] or 0)

        cur.execute(sql_rows, params + [offset, pageSize])
        cols = [c[0] for c in cur.description]

        rows = []
        for row in cur.fetchall():
            d = dict(zip(cols, row))

            # 讓前端好用：把 multi 欄位轉 list
            d["addresses"] = _split_list(d.get("addresses"))
            d["contacts"] = _split_list(d.get("contacts"))
            d["tel"] = _split_list(d.get("tel"))
            d["fax"] = _split_list(d.get("fax"))
            d["emails"] = _split_list(d.get("emails"))
            d["sales_reps"] = _split_list(d.get("sales_reps"))

            rows.append(d)

        return jsonify({
            "ok": True,
            "rows": rows,
            "total": total,
            "page": page,
            "pageSize": pageSize,
        })

    except Exception as e:
        # 更詳細的錯誤訊息
        error_msg = f"Error occurred while processing request: {str(e)}"
        current_app.logger.error(error_msg)
        return jsonify({"ok": False, "msg": error_msg}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass