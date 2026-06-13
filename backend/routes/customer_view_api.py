import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from utils.sqlclient_bridge import query_all as sc_query_all, query_batch as sc_query_batch


bp = Blueprint("customer_view_api", __name__, url_prefix="/ai/api/customer")
_SCHEMA_CACHE = {}


def _get_db_conn():
    return current_app.config["GET_DB_CONN"]()


def _safe_str(value, max_len=None):
    if value is None:
        return ""
    text = str(value).strip()
    if max_len:
        text = text[:max_len]
    return text


def _to_int(value, default=None):
    try:
        if value in (None, ""):
            return default
        return int(value)
    except Exception:
        return default


def _is_itac_db():
    return _safe_str(os.getenv("DB_DATABASE")).lower().startswith("itac")


def _all_table_columns(cur, table_fullname):
    schema, table = table_fullname.split(".")
    rows = cur.execute(
        """
        SELECT c.name
        FROM sys.columns c
        JOIN sys.objects o ON c.object_id = o.object_id
        JOIN sys.schemas s ON o.schema_id = s.schema_id
        WHERE s.name = ? AND o.name = ?
        """,
        (schema, table),
    ).fetchall()
    return {row[0].lower() for row in rows}


def _all_table_columns_sc(table_fullname):
    cached = _SCHEMA_CACHE.get(table_fullname.lower())
    if cached is not None:
        return cached
    schema, table = table_fullname.split(".")
    rows = sc_query_all(
        """
        SELECT c.name
        FROM sys.columns c
        JOIN sys.objects o ON c.object_id = o.object_id
        JOIN sys.schemas s ON o.schema_id = s.schema_id
        WHERE s.name = ? AND o.name = ?
        """,
        [schema, table],
    )
    cols = {_safe_str(row.get("name")).lower() for row in rows}
    _SCHEMA_CACHE[table_fullname.lower()] = cols
    return cols


def debug_log(msg, **kv):
    if not current_app.config.get("DEBUG", False):
        return
    try:
        req_id = getattr(request, "_req_id", None)
        if not req_id:
            req_id = request.headers.get("X-Req-Id") or uuid.uuid4().hex[:8]
            request._req_id = req_id
        tail = " ".join([f"{k}={_safe_str(v, 500)}" for k, v in kv.items()])
        current_app.logger.info(f"[customer_view_api:{req_id}] {msg} {tail}".strip())
    except Exception:
        pass


def _join_top3(values):
    clean = [_safe_str(v) for v in (values or []) if _safe_str(v)]
    return " / ".join(clean[:3])


def _empty_child_bucket(refnos):
    return {refno: {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []} for refno in refnos}


def _merge_child_buckets(target, source):
    for refno, children in (source or {}).items():
        bucket = target.setdefault(refno, {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        for key in ["Address", "contact", "tel", "fax", "email", "sales_rep"]:
            bucket[key].extend(children.get(key) or [])
    return target


def _chunks(values, size=500):
    values = list(values or [])
    for idx in range(0, len(values), size):
        yield values[idx:idx + size]


def _build_where_kw(kw, customer_cols, email_field):
    kw = _safe_str(kw, 100)
    base_filters = ["ISNULL(c.del, 0) = 0"]
    if _is_itac_db():
        base_filters.append("LEFT(LTRIM(RTRIM(CAST(c.refno AS nvarchar(50)))), 3) = 'LAB'")
    base_where = "WHERE " + " AND ".join(base_filters)
    if not kw:
        return base_where, []

    like = f"%{kw}%"
    clauses = []
    params = []

    for col in ["refno", "company", "short", "licenceno", "payment", "ceo"]:
        if col in customer_cols:
            clauses.append(f"CAST(c.[{col}] AS nvarchar(255)) LIKE ?")
            params.append(like)

    clauses.append("EXISTS (SELECT 1 FROM dbo.address a WHERE a.refno = c.refno AND a.cate = 'c' AND ISNULL(a.del, 0) = 0 AND a.address LIKE ?)")
    params.append(like)
    clauses.append("EXISTS (SELECT 1 FROM dbo.contact ct WHERE ct.refno = c.refno AND ct.cate = 'c' AND ISNULL(ct.del, 0) = 0 AND ct.c_name LIKE ?)")
    params.append(like)
    clauses.append("EXISTS (SELECT 1 FROM dbo.tel t WHERE t.refno = c.refno AND t.cate = 'c' AND ISNULL(t.del, 0) = 0 AND t.num LIKE ?)")
    params.append(like)
    if email_field:
        clauses.append(
            f"EXISTS (SELECT 1 FROM dbo.email e WHERE e.refno = c.refno AND e.cate = 'c' AND ISNULL(e.del, 0) = 0 AND CAST(e.[{email_field}] AS nvarchar(255)) LIKE ?)"
        )
        params.append(like)
    clauses.append(
        """
        EXISTS (
          SELECT 1
          FROM dbo.cus_rep cr
          LEFT JOIN dbo.staff s ON s.id = cr.sales_rep
          WHERE cr.refno = c.refno
            AND (
              CAST(cr.sales_rep AS nvarchar(50)) LIKE ?
              OR s.name LIKE ?
            )
        )
        """
    )
    params.extend([like, like])
    return base_where + " AND (" + " OR ".join(clauses) + ")", params


def _fetch_children(cur, refnos, email_field):
    if not refnos:
        return {}
    if len(refnos) > 500:
        bucket = _empty_child_bucket(refnos)
        for chunk in _chunks(refnos):
            _merge_child_buckets(bucket, _fetch_children(cur, chunk, email_field))
        return bucket

    placeholders = ",".join(["?"] * len(refnos))
    bucket = _empty_child_bucket(refnos)

    for row in cur.execute(
        f"SELECT refno, address FROM dbo.address WHERE cate = 'c' AND ISNULL(del, 0) = 0 AND refno IN ({placeholders}) ORDER BY id",
        refnos,
    ).fetchall():
        bucket.setdefault(row[0], {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        if _safe_str(row[1]):
            bucket[row[0]]["Address"].append(_safe_str(row[1]))

    for row in cur.execute(
        f"SELECT refno, c_name FROM dbo.contact WHERE cate = 'c' AND ISNULL(del, 0) = 0 AND refno IN ({placeholders}) ORDER BY id",
        refnos,
    ).fetchall():
        bucket.setdefault(row[0], {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        if _safe_str(row[1]):
            bucket[row[0]]["contact"].append(_safe_str(row[1]))

    for row in cur.execute(
        f"SELECT refno, [Def], num FROM dbo.tel WHERE cate = 'c' AND ISNULL(del, 0) = 0 AND refno IN ({placeholders}) ORDER BY id",
        refnos,
    ).fetchall():
        bucket.setdefault(row[0], {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        if _safe_str(row[2]) and _safe_str(row[1]).upper() == "T":
            bucket[row[0]]["tel"].append(_safe_str(row[2]))
        if _safe_str(row[2]) and _safe_str(row[1]).upper() == "F":
            bucket[row[0]]["fax"].append(_safe_str(row[2]))

    if email_field:
        for row in cur.execute(
            f"SELECT refno, CAST([{email_field}] AS nvarchar(255)) AS email FROM dbo.email WHERE cate = 'c' AND ISNULL(del, 0) = 0 AND refno IN ({placeholders}) ORDER BY id",
            refnos,
        ).fetchall():
            bucket.setdefault(row[0], {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
            if _safe_str(row[1]):
                bucket[row[0]]["email"].append(_safe_str(row[1]))

    for row in cur.execute(
        f"""
        SELECT cr.refno, s.name
        FROM dbo.cus_rep cr
        LEFT JOIN dbo.staff s ON s.id = cr.sales_rep
        WHERE cr.refno IN ({placeholders})
        ORDER BY cr.rep_seq
        """,
        refnos,
    ).fetchall():
        bucket.setdefault(row[0], {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        if _safe_str(row[1]):
            bucket[row[0]]["sales_rep"].append(_safe_str(row[1]))

    return bucket


def _fetch_children_sc(refnos, email_field):
    if not refnos:
        return {}
    if len(refnos) > 500:
        bucket = _empty_child_bucket(refnos)
        for chunk in _chunks(refnos):
            _merge_child_buckets(bucket, _fetch_children_sc(chunk, email_field))
        return bucket
    placeholders = ",".join(["?"] * len(refnos))
    bucket = _empty_child_bucket(refnos)

    statements = [
        {
            "sql": f"SELECT refno, address FROM dbo.address WHERE cate = 'c' AND ISNULL(del, 0) = 0 AND refno IN ({placeholders}) ORDER BY id",
            "params": refnos,
        },
        {
            "sql": f"SELECT refno, c_name FROM dbo.contact WHERE cate = 'c' AND ISNULL(del, 0) = 0 AND refno IN ({placeholders}) ORDER BY id",
            "params": refnos,
        },
        {
            "sql": f"SELECT refno, [Def], num FROM dbo.tel WHERE cate = 'c' AND ISNULL(del, 0) = 0 AND refno IN ({placeholders}) ORDER BY id",
            "params": refnos,
        },
    ]
    if email_field:
        statements.append(
            {
                "sql": f"SELECT refno, CAST([{email_field}] AS nvarchar(255)) AS email FROM dbo.email WHERE cate = 'c' AND ISNULL(del, 0) = 0 AND refno IN ({placeholders}) ORDER BY id",
                "params": refnos,
            }
        )
    statements.append(
        {
            "sql": f"""
            SELECT cr.refno, s.name
            FROM dbo.cus_rep cr
            LEFT JOIN dbo.staff s ON s.id = cr.sales_rep
            WHERE cr.refno IN ({placeholders})
            ORDER BY cr.rep_seq
            """,
            "params": refnos,
        }
    )
    results = sc_query_batch(statements)
    idx = 0

    for row in (results[idx] if len(results) > idx else []):
        refno = _safe_str(row.get("refno"))
        bucket.setdefault(refno, {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        if _safe_str(row.get("address")):
            bucket[refno]["Address"].append(_safe_str(row.get("address")))
    idx += 1

    for row in (results[idx] if len(results) > idx else []):
        refno = _safe_str(row.get("refno"))
        bucket.setdefault(refno, {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        if _safe_str(row.get("c_name")):
            bucket[refno]["contact"].append(_safe_str(row.get("c_name")))
    idx += 1

    for row in (results[idx] if len(results) > idx else []):
        refno = _safe_str(row.get("refno"))
        bucket.setdefault(refno, {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        if _safe_str(row.get("num")) and _safe_str(row.get("Def")).upper() == "T":
            bucket[refno]["tel"].append(_safe_str(row.get("num")))
        if _safe_str(row.get("num")) and _safe_str(row.get("Def")).upper() == "F":
            bucket[refno]["fax"].append(_safe_str(row.get("num")))
    if email_field:
        idx += 1
        for row in (results[idx] if len(results) > idx else []):
            refno = _safe_str(row.get("refno"))
            bucket.setdefault(refno, {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
            if _safe_str(row.get("email")):
                bucket[refno]["email"].append(_safe_str(row.get("email")))
    idx += 1
    for row in (results[idx] if len(results) > idx else []):
        refno = _safe_str(row.get("refno"))
        bucket.setdefault(refno, {"Address": [], "contact": [], "tel": [], "fax": [], "email": [], "sales_rep": []})
        if _safe_str(row.get("name")):
            bucket[refno]["sales_rep"].append(_safe_str(row.get("name")))
    return bucket


def _customer_list_sc(page, page_size, kw, offset):
    customer_cols = _all_table_columns_sc("dbo.customer")
    email_cols = _all_table_columns_sc("dbo.email")
    email_field = "email" if "email" in email_cols else "num" if "num" in email_cols else None
    where_sql, params = _build_where_kw(kw, customer_cols, email_field)
    select_parts = [
        "c.refno",
        "c.company",
        "c.short",
        "CAST(c.[country] AS nvarchar(255)) AS [country]" if "country" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [country]",
        "c.headquarter" if "headquarter" in customer_cols else "CAST(NULL AS int) AS headquarter",
        "CAST(c.[ceo] AS nvarchar(255)) AS [ceo]" if "ceo" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [ceo]",
        "CAST(c.[licenceNo] AS nvarchar(255)) AS [licenceNo]" if "licenceno" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [licenceNo]",
        "CAST(c.[payment] AS nvarchar(255)) AS [payment]" if "payment" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [payment]",
        "c.credit" if "credit" in customer_cols else "CAST(NULL AS decimal(18,2)) AS credit",
        "addr.address AS [Address]",
        "ct.c_name AS [contact]",
        "tel.num AS [tel]",
        "fax.num AS [fax]",
        (f"em.[{email_field}] AS [email]" if email_field else "CAST(NULL AS nvarchar(255)) AS [email]"),
        "rep.name AS [sales_rep]",
    ]
    email_apply = (
        f"""
        OUTER APPLY (
          SELECT TOP 1 CAST(e.[{email_field}] AS nvarchar(255)) AS [{email_field}]
          FROM dbo.email e
          WHERE e.refno = c.refno AND e.cate = 'c' AND ISNULL(e.del, 0) = 0
        ) em
        """
        if email_field
        else "OUTER APPLY (SELECT CAST(NULL AS nvarchar(255)) AS [email]) em"
    )
    rows = sc_query_all(
        f"""
        SELECT {', '.join(select_parts)}
        FROM dbo.customer c
        OUTER APPLY (
          SELECT TOP 1 a.address
          FROM dbo.address a
          WHERE a.refno = c.refno AND a.cate = 'c' AND ISNULL(a.del, 0) = 0
        ) addr
        OUTER APPLY (
          SELECT TOP 1 ct.c_name
          FROM dbo.contact ct
          WHERE ct.refno = c.refno AND ct.cate = 'c' AND ISNULL(ct.del, 0) = 0
        ) ct
        OUTER APPLY (
          SELECT TOP 1 t.num
          FROM dbo.tel t
          WHERE t.refno = c.refno AND t.cate = 'c' AND ISNULL(t.del, 0) = 0 AND t.[Def] = 'T'
        ) tel
        OUTER APPLY (
          SELECT TOP 1 t.num
          FROM dbo.tel t
          WHERE t.refno = c.refno AND t.cate = 'c' AND ISNULL(t.del, 0) = 0 AND t.[Def] = 'F'
        ) fax
        {email_apply}
        OUTER APPLY (
          SELECT TOP 1 s.name
          FROM dbo.cus_rep cr
          LEFT JOIN dbo.staff s ON s.id = cr.sales_rep
          WHERE cr.refno = c.refno
          ORDER BY cr.rep_seq
        ) rep
        {where_sql}
        ORDER BY c.company, c.refno
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """,
        params + [offset, page_size + 1],
    )
    has_more = len(rows) > page_size
    page_rows = rows[:page_size]
    total = offset + len(page_rows) + (1 if has_more else 0)
    result_rows = []
    for row in page_rows:
        refno = _safe_str(row.get("refno"))
        result_rows.append({
            "refno": refno,
            "company": _safe_str(row.get("company")),
            "short": _safe_str(row.get("short")),
            "country": _safe_str(row.get("country")),
            "headquarter": row.get("headquarter"),
            "ceo": _safe_str(row.get("ceo")),
            "licenceNo": _safe_str(row.get("licenceNo")),
            "tax_id": _safe_str(row.get("licenceNo")),
            "payment": _safe_str(row.get("payment")),
            "credit": row.get("credit") if row.get("credit") is not None else 0,
            "Address": _safe_str(row.get("Address")),
            "address": _safe_str(row.get("Address")),
            "contact": _safe_str(row.get("contact")),
            "contact_name": _safe_str(row.get("contact")),
            "tel": _safe_str(row.get("tel")),
            "contact_tel": _safe_str(row.get("tel")),
            "fax": _safe_str(row.get("fax")),
            "contact_fax": _safe_str(row.get("fax")),
            "email": _safe_str(row.get("email")),
            "contact_email": _safe_str(row.get("email")),
            "sales_rep": _safe_str(row.get("sales_rep")),
        })
    return jsonify(ok=True, data={"rows": result_rows, "total": total, "page": page, "pageSize": page_size})


@bp.get("/list")
def customer_list():
    page = max(_to_int(request.args.get("page"), 1), 1)
    page_size = min(max(_to_int(request.args.get("pageSize"), 20), 1), 5000)
    kw = _safe_str(request.args.get("kw"), 100)
    offset = (page - 1) * page_size
    request._req_id = request.headers.get("X-Req-Id") or uuid.uuid4().hex[:8]
    debug_log("request", page=page, pageSize=page_size, kw=kw, offset=offset)

    # On this migrated host pyodbc fails with SQL Client encryption errors.
    # Use the verified SqlClient bridge first so the list endpoint does not stall.
    try:
        return _customer_list_sc(page, page_size, kw, offset)
    except Exception as exc:
        try:
            current_app.logger.error(f"Error in /ai/api/customer/list SqlClient path: {exc}", exc_info=True)
        except Exception:
            pass
        return jsonify(ok=False, msg=str(exc)), 500

    conn = None
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        customer_cols = _all_table_columns(cur, "dbo.customer")
        email_cols = _all_table_columns(cur, "dbo.email")
        email_field = "email" if "email" in email_cols else "num" if "num" in email_cols else None

        where_sql, params = _build_where_kw(kw, customer_cols, email_field)
        total_sql = f"SELECT COUNT(1) FROM dbo.customer c {where_sql}"
        total = int(cur.execute(total_sql, params).fetchone()[0] or 0)

        select_parts = [
            "c.refno",
            "c.company",
            "c.short",
            "CAST(c.[country] AS nvarchar(255)) AS [country]" if "country" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [country]",
            "c.headquarter" if "headquarter" in customer_cols else "CAST(NULL AS int) AS headquarter",
            "CAST(c.[ceo] AS nvarchar(255)) AS [ceo]" if "ceo" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [ceo]",
            "CAST(c.[licenceNo] AS nvarchar(255)) AS [licenceNo]" if "licenceno" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [licenceNo]",
            "CAST(c.[payment] AS nvarchar(255)) AS [payment]" if "payment" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [payment]",
            "c.credit" if "credit" in customer_cols else "CAST(NULL AS decimal(18,2)) AS credit",
        ]
        sql = f"""
        SELECT
            {', '.join(select_parts)}
        FROM dbo.customer c
        {where_sql}
        ORDER BY c.company, c.refno
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        rows = cur.execute(sql, params + [offset, page_size]).fetchall()
        base_rows = []
        refnos = []
        for row in rows:
            refno = _safe_str(row.refno)
            refnos.append(refno)
            base_rows.append(
                {
                    "refno": refno,
                    "company": _safe_str(row.company),
                    "short": _safe_str(row.short),
                    "country": _safe_str(row.country),
                    "headquarter": row.headquarter,
                    "ceo": _safe_str(row.ceo),
                    "licenceNo": _safe_str(row.licenceNo),
                    "payment": _safe_str(row.payment),
                    "credit": row.credit if row.credit is not None else 0,
                }
            )

        child_bucket = _fetch_children(cur, refnos, email_field)
        result_rows = []
        for row in base_rows:
            children = child_bucket.get(row["refno"], {})
            row["Address"] = _join_top3(children.get("Address"))
            row["address"] = row["Address"]
            row["contact"] = _join_top3(children.get("contact"))
            row["contact_name"] = row["contact"]
            row["tel"] = _join_top3(children.get("tel"))
            row["contact_tel"] = row["tel"]
            row["fax"] = _join_top3(children.get("fax"))
            row["contact_fax"] = row["fax"]
            row["email"] = _join_top3(children.get("email"))
            row["contact_email"] = row["email"]
            row["sales_rep"] = _join_top3(children.get("sales_rep"))
            row["tax_id"] = _safe_str(row.get("licenceNo"))
            result_rows.append(row)

        return jsonify(
            ok=True,
            data={
                "rows": result_rows,
                "total": total,
                "page": page,
                "pageSize": page_size,
            },
        )
    except Exception as exc:
        try:
            current_app.logger.error(f"Error in /ai/api/customer/list: {exc}", exc_info=True)
        except Exception:
            pass
        customer_cols = _all_table_columns_sc("dbo.customer")
        email_cols = _all_table_columns_sc("dbo.email")
        email_field = "email" if "email" in email_cols else "num" if "num" in email_cols else None
        where_sql, params = _build_where_kw(kw, customer_cols, email_field)
        total_row = sc_query_all(f"SELECT COUNT(1) AS total FROM dbo.customer c {where_sql}", params)
        total = int((total_row[0].get("total") if total_row else 0) or 0)
        select_parts = [
            "c.refno",
            "c.company",
            "c.short",
            "CAST(c.[country] AS nvarchar(255)) AS [country]" if "country" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [country]",
            "c.headquarter" if "headquarter" in customer_cols else "CAST(NULL AS int) AS headquarter",
            "CAST(c.[ceo] AS nvarchar(255)) AS [ceo]" if "ceo" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [ceo]",
            "CAST(c.[licenceNo] AS nvarchar(255)) AS [licenceNo]" if "licenceno" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [licenceNo]",
            "CAST(c.[payment] AS nvarchar(255)) AS [payment]" if "payment" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [payment]",
            "c.credit" if "credit" in customer_cols else "CAST(NULL AS decimal(18,2)) AS credit",
        ]
        rows = sc_query_all(
            f"""
            SELECT {', '.join(select_parts)}
            FROM dbo.customer c
            {where_sql}
            ORDER BY c.company, c.refno
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            params + [offset, page_size],
        )
        refnos = [_safe_str(row.get("refno")) for row in rows]
        child_bucket = _fetch_children_sc(refnos, email_field)
        result_rows = []
        for row in rows:
            refno = _safe_str(row.get("refno"))
            children = child_bucket.get(refno, {})
            result_rows.append({
                "refno": refno,
                "company": _safe_str(row.get("company")),
                "short": _safe_str(row.get("short")),
                "country": _safe_str(row.get("country")),
                "headquarter": row.get("headquarter"),
                "ceo": _safe_str(row.get("ceo")),
                "licenceNo": _safe_str(row.get("licenceNo")),
                "tax_id": _safe_str(row.get("licenceNo")),
                "payment": _safe_str(row.get("payment")),
                "credit": row.get("credit") if row.get("credit") is not None else 0,
                "Address": _join_top3(children.get("Address")),
                "address": _join_top3(children.get("Address")),
                "contact": _join_top3(children.get("contact")),
                "contact_name": _join_top3(children.get("contact")),
                "tel": _join_top3(children.get("tel")),
                "contact_tel": _join_top3(children.get("tel")),
                "fax": _join_top3(children.get("fax")),
                "contact_fax": _join_top3(children.get("fax")),
                "email": _join_top3(children.get("email")),
                "contact_email": _join_top3(children.get("email")),
                "sales_rep": _join_top3(children.get("sales_rep")),
            })
        return jsonify(ok=True, data={"rows": result_rows, "total": total, "page": page, "pageSize": page_size})
    except Exception as exc2:
        return jsonify(ok=False, msg=str(exc2)), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
