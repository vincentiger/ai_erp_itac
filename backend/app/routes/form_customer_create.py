from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from app.utils.db import get_conn

from app.utils.customer_refno import _safe_int, _get_prefix, _next_refno

logger = logging.getLogger(__name__)

# ✅ 一定要先定義 Blueprint
bp = Blueprint("form_customer_create", __name__)

def _table_has_columns(cur, table_fullname: str, cols: list[str]) -> set[str]:
    schema, table = table_fullname.split(".")
    rows = cur.execute("""
        SELECT c.name
        FROM sys.columns c
        JOIN sys.objects o ON c.object_id=o.object_id
        JOIN sys.schemas s ON o.schema_id=s.schema_id
        WHERE s.name=? AND o.name=?
    """, (schema, table)).fetchall()
    existing = {r[0].lower() for r in rows}
    return {c.lower() for c in cols if c.lower() in existing}


@bp.post("/api/form/customer_create/save")
def customer_create_save():
    payload = request.get_json(silent=True) or {}

    no1 = _safe_int(payload.get("no1"))
    no2 = _safe_int(payload.get("no2"))
    company = (payload.get("company") or "").strip()

    if not no1 or not no2:
        return jsonify({"ok": False, "msg": "請選擇分類第一層與第二層"}), 400
    if not company:
        return jsonify({"ok": False, "msg": "請輸入公司名稱"}), 400

    short = (payload.get("short") or "").strip()
    country = payload.get("country")
    headquarter = payload.get("headerquarter")
    url = (payload.get("url") or "").strip()
    credit = payload.get("credit", 0) or 0
    commission = payload.get("commission", 0) or 0
    payment = payload.get("payment")
    employee = payload.get("employee")
    class2 = payload.get("Class2")
    quit_flag = payload.get("quit")
    secret = payload.get("secret")
    licenceNo = (payload.get("LicenceNo") or "").strip()
    remarks = (payload.get("remarks") or "").strip()

    addresses = payload.get("addresses") or []
    contacts  = payload.get("contacts") or []
    tel_list  = payload.get("tel") or []
    fax_list  = payload.get("fax") or []
    emails    = payload.get("emails") or []
    sales_reps = payload.get("sales_reps") or []

    conn = get_conn()
    try:
        conn.autocommit = False
        cur = conn.cursor()

        prefix = _get_prefix(cur, no1, no2)
        if not prefix:
            conn.rollback()
            return jsonify({"ok": False, "msg": "找不到分類 prefix"}), 400

        refno = _next_refno(cur, prefix)

        row = cur.execute("""
            SELECT
              LTRIM(RTRIM(ISNULL(c1.symbol,''))) AS s1,
              LTRIM(RTRIM(ISNULL(c2.symbol,''))) AS s2
            FROM dbo.cate_cust01 c1
            JOIN dbo.cate_cust02 c2 ON c2.no1=c1.id
            WHERE c1.cate='c' AND c1.id=? AND c2.cate='c' AND c2.id=?
        """, (no1, no2)).fetchone()

        cate = f"{(row.s1 or '').strip()},{(row.s2 or '').strip()}"

        insert_cols = [
            "refno","no1","no2","cate","country","company","short","headquarter",
            "secret","URL","credit","commission","payment","employee","class2",
            "remarks","add_date","quit","del","licenceNo"
        ]

        existing = _table_has_columns(cur, "dbo.customer", insert_cols)

        values_map = {
            "refno": refno,
            "no1": no1,
            "no2": no2,
            "cate": cate,
            "country": country,
            "company": company,
            "short": short,
            "headquarter": _safe_int(headquarter),
            "secret": _safe_int(secret, 0),
            "url": url[:50],
            "credit": credit,
            "commission": commission,
            "payment": payment,
            "employee": employee,
            "class2": class2,
            "remarks": remarks,
            "add_date": datetime.now(),
            "quit": quit_flag if quit_flag in ("Y","N") else None,
            "del": 0,
            "licenceno": licenceNo,
        }

        cols, params = [], []
        for c in insert_cols:
            if c.lower() in existing:
                cols.append(f"[{c}]")
                params.append(values_map[c.lower()])

        sql = f"INSERT INTO dbo.customer ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})"
        cur.execute(sql, params)

        conn.commit()
        return jsonify({"ok": True, "refno": refno})

    except Exception as e:
        conn.rollback()
        logger.exception("customer_create_save failed")
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        conn.close()
