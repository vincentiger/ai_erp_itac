import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from utils.sqlclient_bridge import (
    execute_transaction as sc_execute_transaction,
    query_batch as sc_query_batch,
    query_all as sc_query_all,
    query_one as sc_query_one,
)


bp = Blueprint(
    "form_customer_create",
    __name__,
    url_prefix="/api/form/customer_create",
)


def get_db_conn():
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


def _to_decimal(value, default=0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _is_itac_db():
    return _safe_str(os.getenv("DB_DATABASE")).lower().startswith("itac")


def _lab_category_sc():
    row = sc_query_one(
        """
        SELECT TOP 1 id, ISNULL(c01, c01_e) AS name, symbol
        FROM dbo.cate_cust01
        WHERE cate = 'c'
          AND (
            UPPER(LTRIM(RTRIM(ISNULL(symbol, '')))) = 'LAB'
            OR LTRIM(RTRIM(ISNULL(c01, ''))) = N'實驗室'
          )
        ORDER BY
          CASE WHEN UPPER(LTRIM(RTRIM(ISNULL(symbol, '')))) = 'LAB' THEN 0 ELSE 1 END,
          id
        """
    )
    if not row:
        return None
    return {
        "id": row.get("id"),
        "name": _safe_str(row.get("name")),
        "symbol": _safe_str(row.get("symbol")),
    }


def _split_lines(value):
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value or "").splitlines()
    result = []
    for item in items:
        text = _safe_str(item)
        if text:
            result.append(text)
    return result


def _table_has_columns(cur, table_fullname, cols):
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
    existing = {row[0].lower() for row in rows}
    return {str(col).lower() for col in cols if str(col).lower() in existing}


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
    return {_safe_str(row.get("name")).lower() for row in rows}


_SCHEMA_CACHE = {}


def _email_field_sc():
    email_cols = _SCHEMA_CACHE.get("dbo.email")
    if email_cols is None:
        email_cols = _all_table_columns_sc("dbo.email")
        _SCHEMA_CACHE["dbo.email"] = email_cols
    if "email" in email_cols:
        return "email"
    if "num" in email_cols:
        return "num"
    return None


def _customer_cols_sc():
    cols = _SCHEMA_CACHE.get("dbo.customer")
    if cols is None:
        cols = _all_table_columns_sc("dbo.customer")
        _SCHEMA_CACHE["dbo.customer"] = cols
    return cols


def _load_customer_children_sc(refno):
    email_cols = _all_table_columns_sc("dbo.email")
    email_field = "email" if "email" in email_cols else "num" if "num" in email_cols else None
    statements = [
        {
            "sql": "SELECT address FROM dbo.address WHERE refno = ? AND cate = 'c' AND ISNULL(del, 0) = 0",
            "params": [refno],
        },
        {
            "sql": "SELECT c_name FROM dbo.contact WHERE refno = ? AND cate = 'c' AND ISNULL(del, 0) = 0",
            "params": [refno],
        },
        {
            "sql": "SELECT [Def], num FROM dbo.tel WHERE refno = ? AND cate = 'c' AND ISNULL(del, 0) = 0",
            "params": [refno],
        },
        {
            "sql": "SELECT sales_rep FROM dbo.cus_rep WHERE refno = ?",
            "params": [refno],
        },
        {
            "sql": """
            SELECT s.name
            FROM dbo.cus_rep cr
            LEFT JOIN dbo.staff s ON s.id = cr.sales_rep
            WHERE cr.refno = ?
            ORDER BY cr.rep_seq
            """,
            "params": [refno],
        },
    ]
    if email_field:
        statements.insert(
            3,
            {
                "sql": f"SELECT CAST([{email_field}] AS nvarchar(255)) AS [{email_field}] FROM dbo.email WHERE refno = ? AND cate = 'c' AND ISNULL(del, 0) = 0",
                "params": [refno],
            },
        )

    results = sc_query_batch(statements)
    idx = 0
    addresses = [
        _safe_str(row.get("address"))
        for row in (results[idx] if len(results) > idx else [])
        if _safe_str(row.get("address"))
    ]
    idx += 1
    contacts = [
        _safe_str(row.get("c_name"))
        for row in (results[idx] if len(results) > idx else [])
        if _safe_str(row.get("c_name"))
    ]
    idx += 1
    tel_rows = results[idx] if len(results) > idx else []
    idx += 1
    emails = []
    if email_field:
        emails = [
            _safe_str(row.get(email_field))
            for row in (results[idx] if len(results) > idx else [])
            if _safe_str(row.get(email_field))
        ]
        idx += 1
    tel = [_safe_str(row.get("num")) for row in tel_rows if _safe_str(row.get("Def")).upper() == "T" and _safe_str(row.get("num"))]
    fax = [_safe_str(row.get("num")) for row in tel_rows if _safe_str(row.get("Def")).upper() == "F" and _safe_str(row.get("num"))]
    sales_reps = [
        str(row.get("sales_rep"))
        for row in (results[idx] if len(results) > idx else [])
        if row.get("sales_rep") is not None
    ]
    idx += 1
    sales_rep_names = [
        _safe_str(row.get("name"))
        for row in (results[idx] if len(results) > idx else [])
        if _safe_str(row.get("name"))
    ]
    return {
        "addresses": addresses,
        "contacts": contacts,
        "emails": emails,
        "tel": tel,
        "fax": fax,
        "sales_reps": sales_reps,
        "sales_rep": ", ".join(sales_rep_names),
    }


def _load_customer_record_sc(refno):
    customer_cols = _all_table_columns_sc("dbo.customer")
    email_cols = _all_table_columns_sc("dbo.email")
    email_field = "email" if "email" in email_cols else "num" if "num" in email_cols else None
    select_parts = [
        "refno",
        "no1",
        "no2",
        "company",
        "short",
        "country",
        "[headquarter]" if "headquarter" in customer_cols else "CAST(NULL AS int) AS [headquarter]",
        "[URL]" if "url" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [URL]",
        "[ceo]" if "ceo" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [ceo]",
        "[Class2]" if "class2" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [Class2]",
        "[items]" if "items" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [items]",
        "[employee]" if "employee" in customer_cols else "CAST(NULL AS nvarchar(50)) AS [employee]",
        "[quit]" if "quit" in customer_cols else "CAST(NULL AS nvarchar(10)) AS [quit]",
        "[secret]" if "secret" in customer_cols else "CAST(NULL AS int) AS [secret]",
        "[licenceNo]" if "licenceno" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [licenceNo]",
        "[payment]" if "payment" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [payment]",
        "[credit]" if "credit" in customer_cols else "CAST(NULL AS decimal(18,2)) AS [credit]",
        "[commission]" if "commission" in customer_cols else "CAST(NULL AS decimal(18,2)) AS [commission]",
        "[remarks]" if "remarks" in customer_cols else "CAST(NULL AS nvarchar(2000)) AS [remarks]",
    ]
    statements = [
        {
            "sql": f"SELECT TOP 1 {', '.join(select_parts)} FROM dbo.customer WHERE refno = ?",
            "params": [refno],
        },
        {
            "sql": "SELECT address FROM dbo.address WHERE refno = ? AND cate = 'c'",
            "params": [refno],
        },
        {
            "sql": "SELECT c_name FROM dbo.contact WHERE refno = ? AND cate = 'c'",
            "params": [refno],
        },
        {
            "sql": "SELECT [Def], num FROM dbo.tel WHERE refno = ? AND cate = 'c'",
            "params": [refno],
        },
        {
            "sql": "SELECT sales_rep FROM dbo.cus_rep WHERE refno = ?",
            "params": [refno],
        },
        {
            "sql": """
            SELECT s.name
            FROM dbo.cus_rep cr
            LEFT JOIN dbo.staff s ON s.id = cr.sales_rep
            WHERE cr.refno = ?
            ORDER BY cr.rep_seq
            """,
            "params": [refno],
        },
    ]
    if email_field:
        statements.insert(
            4,
            {
                "sql": f"SELECT CAST([{email_field}] AS nvarchar(255)) AS [{email_field}] FROM dbo.email WHERE refno = ? AND cate = 'c'",
                "params": [refno],
            },
        )
    results = sc_query_batch(statements)
    customer_rows = results[0] if len(results) > 0 else []
    row = customer_rows[0] if customer_rows else None
    if row is None:
        return None

    idx = 1
    addresses = [
        _safe_str(item.get("address"))
        for item in (results[idx] if len(results) > idx else [])
        if _safe_str(item.get("address"))
    ]
    idx += 1
    contacts = [
        _safe_str(item.get("c_name"))
        for item in (results[idx] if len(results) > idx else [])
        if _safe_str(item.get("c_name"))
    ]
    idx += 1
    tel_rows = results[idx] if len(results) > idx else []
    idx += 1
    emails = []
    if email_field:
        emails = [
            _safe_str(item.get(email_field))
            for item in (results[idx] if len(results) > idx else [])
            if _safe_str(item.get(email_field))
        ]
        idx += 1
    sales_reps = [
        str(item.get("sales_rep"))
        for item in (results[idx] if len(results) > idx else [])
        if item.get("sales_rep") is not None
    ]
    idx += 1
    sales_rep_names = [
        _safe_str(item.get("name"))
        for item in (results[idx] if len(results) > idx else [])
        if _safe_str(item.get("name"))
    ]
    tel = [_safe_str(item.get("num")) for item in tel_rows if _safe_str(item.get("Def")).upper() == "T" and _safe_str(item.get("num"))]
    fax = [_safe_str(item.get("num")) for item in tel_rows if _safe_str(item.get("Def")).upper() == "F" and _safe_str(item.get("num"))]
    data = {
        "refno": _safe_str(row.get("refno")),
        "no1": _to_int(row.get("no1"), ""),
        "no2": _to_int(row.get("no2"), ""),
        "company": _safe_str(row.get("company")),
        "short": _safe_str(row.get("short")),
        "country": row.get("country") if row.get("country") is not None else "",
        "headerquarter": row.get("headquarter") if row.get("headquarter") is not None else "",
        "url": _safe_str(row.get("URL"), 255),
        "ceo": _safe_str(row.get("ceo"), 100),
        "Class2": _safe_str(row.get("Class2"), 100),
        "items": _safe_str(row.get("items"), 100),
        "employee": _safe_str(row.get("employee"), 50),
        "quit": _safe_str(row.get("quit")).upper() == "Y",
        "secret": bool(row.get("secret")),
        "LicenceNo": _safe_str(row.get("licenceNo"), 100),
        "payment": _safe_str(row.get("payment"), 100),
        "credit": _to_decimal(row.get("credit"), 0),
        "commission": _to_decimal(row.get("commission"), 0),
        "remarks": _safe_str(row.get("remarks"), 2000),
        "addresses": addresses,
        "contacts": contacts,
        "emails": emails,
        "tel": tel,
        "fax": fax,
        "sales_reps": sales_reps,
        "sales_rep": ", ".join(sales_rep_names),
    }
    return data


def _get_prefix(cur, no1, no2):
    if not no1:
        return ""
    if no2:
        row = cur.execute(
            """
            SELECT
              LTRIM(RTRIM(ISNULL(c1.symbol, ''))) AS s1,
              LTRIM(RTRIM(ISNULL(c2.symbol, ''))) AS s2
            FROM dbo.cate_cust01 c1
            JOIN dbo.cate_cust02 c2 ON c2.no1 = c1.id
            WHERE c1.cate = 'c' AND c1.id = ? AND c2.cate = 'c' AND c2.id = ?
            """,
            (no1, no2),
        ).fetchone()
        if not row:
            return ""
        return f"{_safe_str(row.s1)}{_safe_str(row.s2)}"

    row = cur.execute(
        """
        SELECT LTRIM(RTRIM(ISNULL(symbol, ''))) AS s1
        FROM dbo.cate_cust01
        WHERE cate = 'c' AND id = ?
        """,
        (no1,),
    ).fetchone()
    return _safe_str(getattr(row, "s1", "")) if row else ""


def _get_prefix_sc(no1, no2):
    if not no1:
        return ""
    row1 = sc_query_one(
        """
        SELECT LTRIM(RTRIM(ISNULL(symbol, ''))) AS s1
        FROM dbo.cate_cust01
        WHERE cate = 'c' AND id = ?
        """,
        [no1],
    )
    if not row1:
        return ""
    prefix = _safe_str(row1.get("s1"))
    if not no2:
        return prefix
    row2 = sc_query_one(
        """
        SELECT LTRIM(RTRIM(ISNULL(symbol, ''))) AS s2
        FROM dbo.cate_cust02
        WHERE cate = 'c' AND id = ? AND no1 = ?
        """,
        [no2, no1],
    )
    if not row2:
        return ""
    return f"{prefix}{_safe_str(row2.get('s2'))}"


def _get_cate_symbols_sc(no1, no2):
    symbols = []
    if not no1:
        return symbols
    row1 = sc_query_one(
        """
        SELECT LTRIM(RTRIM(ISNULL(symbol, ''))) AS s1
        FROM dbo.cate_cust01
        WHERE cate = 'c' AND id = ?
        """,
        [no1],
    )
    if row1:
        s1 = _safe_str(row1.get("s1"))
        if s1:
            symbols.append(s1)
    if no2:
        row2 = sc_query_one(
            """
            SELECT LTRIM(RTRIM(ISNULL(symbol, ''))) AS s2
            FROM dbo.cate_cust02
            WHERE cate = 'c' AND id = ? AND no1 = ?
            """,
            [no2, no1],
        )
        if row2:
            s2 = _safe_str(row2.get("s2"))
            if s2:
                symbols.append(s2)
    return symbols


def _resolve_customer_prefix_meta_sc(no1, no2, refno):
    if not no1:
        return {
            "prefix": "",
            "cate": "",
            "is_update": False,
            "generated_refno": "",
        }

    statements = [
        {
            "sql": """
            SELECT
              LTRIM(RTRIM(ISNULL(symbol, ''))) AS symbol
            FROM dbo.cate_cust01
            WHERE cate = 'c' AND id = ?
            """,
            "params": [no1],
        }
    ]
    if no2:
        statements.append(
            {
                "sql": """
                SELECT
                  LTRIM(RTRIM(ISNULL(symbol, ''))) AS symbol
                FROM dbo.cate_cust02
                WHERE cate = 'c' AND id = ? AND no1 = ?
                """,
                "params": [no2, no1],
            }
        )
    if not refno:
        prefix_sql = """
        SELECT
          TOP 1 refno
        FROM dbo.customer
        WHERE refno LIKE (
          SELECT
            LTRIM(RTRIM(ISNULL(c1.symbol, '')))
            + CASE
                WHEN ? IS NULL OR ? = '' THEN ''
                ELSE LTRIM(RTRIM(ISNULL(c2.symbol, '')))
              END
          FROM dbo.cate_cust01 c1
          LEFT JOIN dbo.cate_cust02 c2
            ON c2.cate = 'c' AND c2.id = ? AND c2.no1 = c1.id
          WHERE c1.cate = 'c' AND c1.id = ?
        ) + '%'
        ORDER BY refno DESC
        """
        statements.append(
            {
                "sql": prefix_sql,
                "params": [no2, no2, no2, no1],
            }
        )
    if refno:
        statements.append(
            {
                "sql": "SELECT TOP 1 refno FROM dbo.customer WHERE refno = ?",
                "params": [refno],
            }
        )

    results = sc_query_batch(statements)
    row1 = results[0][0] if len(results) > 0 and results[0] else None
    if not row1:
        return {
            "prefix": "",
            "cate": "",
            "is_update": False,
            "generated_refno": "",
        }

    s1 = _safe_str(row1.get("symbol"))
    s2 = ""
    idx = 1
    if no2:
        row2 = results[idx][0] if len(results) > idx and results[idx] else None
        if not row2:
            return {
                "prefix": "",
                "cate": "",
                "is_update": False,
                "generated_refno": "",
            }
        s2 = _safe_str(row2.get("symbol"))
        idx += 1

    prefix = f"{s1}{s2}" if s2 else s1
    cate = ",".join([v for v in [s1, s2] if v])
    last_refno = ""
    if not refno:
        row_last = results[idx][0] if len(results) > idx and results[idx] else None
        last_refno = _safe_str(row_last.get("refno")) if row_last else ""
        idx += 1
    is_update = bool(refno and len(results) > idx and results[idx])

    generated_refno = ""
    if not refno and prefix:
        generated_refno = f"{prefix}{(_to_int(last_refno[-3:] if last_refno else 0, 0) + 1):03d}"

    return {
        "prefix": prefix,
        "cate": cate,
        "is_update": is_update,
        "generated_refno": generated_refno,
    }


def _next_refno(cur, prefix):
    row = cur.execute(
        "SELECT TOP 1 refno FROM dbo.customer WHERE refno LIKE ? ORDER BY refno DESC",
        (prefix + "%",),
    ).fetchone()
    if not row or not row[0]:
        return f"{prefix}001"
    last = _safe_str(row[0])
    suffix = last[-3:]
    number = _to_int(suffix, 0) + 1
    return f"{prefix}{number:03d}"


def _delete_customer_children(cur, refno):
    cur.execute("DELETE FROM dbo.address WHERE refno = ? AND cate = 'c'", (refno,))
    cur.execute("DELETE FROM dbo.contact WHERE refno = ? AND cate = 'c'", (refno,))
    cur.execute("DELETE FROM dbo.email WHERE refno = ? AND cate = 'c'", (refno,))
    cur.execute("DELETE FROM dbo.tel WHERE refno = ? AND cate = 'c'", (refno,))
    cur.execute("DELETE FROM dbo.cus_rep WHERE refno = ?", (refno,))


def _insert_many(cur, table, column, refno, values, extra_cols=None):
    extra_cols = extra_cols or {}
    clean_values = [_safe_str(v) for v in (values or []) if _safe_str(v)]
    if not clean_values:
        return

    cols = ["refno", column] + list(extra_cols.keys())
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
    for value in clean_values:
        params = [refno, value] + list(extra_cols.values())
        cur.execute(sql, params)


def _load_customer_children(cur, refno):
    addresses = [
        row[0]
        for row in cur.execute(
            "SELECT address FROM dbo.address WHERE refno = ? AND cate = 'c' ORDER BY id",
            (refno,),
        ).fetchall()
        if _safe_str(row[0])
    ]
    contacts = [
        row[0]
        for row in cur.execute(
            "SELECT c_name FROM dbo.contact WHERE refno = ? AND cate = 'c' ORDER BY id",
            (refno,),
        ).fetchall()
        if _safe_str(row[0])
    ]
    email_cols = _all_table_columns(cur, "dbo.email")
    email_field = "email" if "email" in email_cols else "num" if "num" in email_cols else None
    emails = []
    if email_field:
        emails = [
            row[0]
            for row in cur.execute(
                f"""
                SELECT CAST([{email_field}] AS nvarchar(255))
                FROM dbo.email
                WHERE refno = ? AND cate = 'c'
                ORDER BY id
                """,
                (refno,),
            ).fetchall()
            if _safe_str(row[0])
        ]
    tel_rows = cur.execute(
        """
        SELECT [Def], num
        FROM dbo.tel
        WHERE refno = ? AND cate = 'c'
        ORDER BY id
        """,
        (refno,),
    ).fetchall()
    tel = [_safe_str(row[1]) for row in tel_rows if _safe_str(row[0]).upper() == "T" and _safe_str(row[1])]
    fax = [_safe_str(row[1]) for row in tel_rows if _safe_str(row[0]).upper() == "F" and _safe_str(row[1])]

    sales_reps = [
        str(row[0])
        for row in cur.execute(
            "SELECT sales_rep FROM dbo.cus_rep WHERE refno = ? ORDER BY id",
            (refno,),
        ).fetchall()
        if row[0] is not None
    ]
    sales_rep_names = [
        _safe_str(row[0])
        for row in cur.execute(
            """
            SELECT s.name
            FROM dbo.cus_rep cr
            LEFT JOIN dbo.staff s ON s.id = cr.sales_rep
            WHERE cr.refno = ?
            ORDER BY cr.id
            """,
            (refno,),
        ).fetchall()
        if _safe_str(row[0])
    ]
    return {
        "addresses": addresses,
        "contacts": contacts,
        "emails": emails,
        "tel": tel,
        "fax": fax,
        "sales_reps": sales_reps,
        "sales_rep": ", ".join(sales_rep_names),
    }


def _load_customer_record(cur, refno):
    customer_cols = _all_table_columns(cur, "dbo.customer")
    select_parts = [
        "refno",
        "no1",
        "no2",
        "company",
        "short",
        "country",
        "[headquarter]" if "headquarter" in customer_cols else "CAST(NULL AS int) AS [headquarter]",
        "[URL]" if "url" in customer_cols else "CAST(NULL AS nvarchar(255)) AS [URL]",
        "[ceo]" if "ceo" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [ceo]",
        "[Class2]" if "class2" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [Class2]",
        "[items]" if "items" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [items]",
        "[employee]" if "employee" in customer_cols else "CAST(NULL AS nvarchar(50)) AS [employee]",
        "[quit]" if "quit" in customer_cols else "CAST(NULL AS nvarchar(10)) AS [quit]",
        "[secret]" if "secret" in customer_cols else "CAST(NULL AS int) AS [secret]",
        "[licenceNo]" if "licenceno" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [licenceNo]",
        "[payment]" if "payment" in customer_cols else "CAST(NULL AS nvarchar(100)) AS [payment]",
        "[credit]" if "credit" in customer_cols else "CAST(NULL AS decimal(18,2)) AS [credit]",
        "[commission]" if "commission" in customer_cols else "CAST(NULL AS decimal(18,2)) AS [commission]",
        "[remarks]" if "remarks" in customer_cols else "CAST(NULL AS nvarchar(2000)) AS [remarks]",
    ]
    row = cur.execute(
        f"SELECT TOP 1 {', '.join(select_parts)} FROM dbo.customer WHERE refno = ?",
        (refno,),
    ).fetchone()
    if not row:
        return None

    data = {
        "refno": _safe_str(row.refno),
        "no1": _to_int(row.no1, ""),
        "no2": _to_int(row.no2, ""),
        "company": _safe_str(row.company),
        "short": _safe_str(row.short),
        "country": row.country if row.country is not None else "",
        "headerquarter": row.headquarter if row.headquarter is not None else "",
        "url": _safe_str(row.URL, 255),
        "ceo": _safe_str(row.ceo, 100),
        "Class2": _safe_str(row.Class2, 100),
        "items": _safe_str(row.items, 100),
        "employee": _safe_str(row.employee, 50),
        "quit": _safe_str(row.quit).upper() == "Y",
        "secret": bool(row.secret),
        "LicenceNo": _safe_str(row.licenceNo, 100),
        "payment": _safe_str(row.payment, 100),
        "credit": _to_decimal(row.credit, 0),
        "commission": _to_decimal(row.commission, 0),
        "remarks": _safe_str(row.remarks, 2000),
    }
    data.update(_load_customer_children(cur, refno))
    return data


@bp.get("/options")
def customer_create_options():
    key = _safe_str(request.args.get("key"), 50)
    no1 = _to_int(request.args.get("no1"), None)

    try:
        if key == "no1":
            rows = sc_query_all(
                """
                SELECT id, ISNULL(c01, c01_e) AS label
                FROM dbo.cate_cust01
                WHERE cate = 'c'
                ORDER BY id
                """
            )
            data = [{"value": row.get("id"), "label": _safe_str(row.get("label"))} for row in rows]
            return jsonify(ok=True, data=data)

        if key == "no2":
            if not no1:
                return jsonify(ok=True, data=[])
            rows = sc_query_all(
                """
                SELECT id, ISNULL(c02, c02_e) AS label
                FROM dbo.cate_cust02
                WHERE cate = 'c' AND no1 = ?
                ORDER BY id
                """,
                [no1],
            )
            data = [{"value": row.get("id"), "label": _safe_str(row.get("label"))} for row in rows]
            return jsonify(ok=True, data=data)

        if key == "country":
            rows = sc_query_all("SELECT id, country FROM dbo.countries ORDER BY country")
            data = [{"value": row.get("id"), "label": _safe_str(row.get("country"))} for row in rows]
            return jsonify(ok=True, data=data)

        if key == "headerquarter":
            rows = sc_query_all(
                """
                SELECT id, company
                FROM dbo.customer
                WHERE ISNULL(del, 0) = 0
                ORDER BY company
                """
            )
            data = [{"value": row.get("id"), "label": _safe_str(row.get("company"))} for row in rows]
            return jsonify(ok=True, data=data)

        if key == "Class2":
            rows = sc_query_all("SELECT class2 FROM dbo.class2 WHERE class2 IS NOT NULL ORDER BY class2")
            data = [{"value": _safe_str(row.get("class2")), "label": _safe_str(row.get("class2"))} for row in rows if _safe_str(row.get("class2"))]
            return jsonify(ok=True, data=data)

        if key == "items":
            rows = sc_query_all("SELECT cateTxt FROM dbo.items_cf WHERE cateTxt IS NOT NULL ORDER BY cateTxt")
            data = [{"value": _safe_str(row.get("cateTxt")), "label": _safe_str(row.get("cateTxt"))} for row in rows if _safe_str(row.get("cateTxt"))]
            return jsonify(ok=True, data=data)

        if key == "payment":
            rows = sc_query_all("SELECT payment FROM dbo.payment WHERE payment IS NOT NULL ORDER BY payment")
            data = [{"value": _safe_str(row.get("payment")), "label": _safe_str(row.get("payment"))} for row in rows if _safe_str(row.get("payment"))]
            return jsonify(ok=True, data=data)

        if key == "sales_reps":
            rows = sc_query_all(
                """
                SELECT s.id, s.name
                FROM dbo.staff s
                JOIN dbo.department d ON s.dep = d.id
                JOIN dbo.manage m ON d.company_title = m.id
                WHERE m.id = 1
                  AND ISNULL(s.del, 0) = 0
                  AND ISNULL(s.quit, 0) = 0
                ORDER BY name
                """
            )
            data = [{"value": str(row.get("id")), "label": _safe_str(row.get("name"))} for row in rows]
            return jsonify(ok=True, data=data)

        return jsonify(ok=False, msg="unknown key"), 400
    except Exception as exc:
        return jsonify(ok=False, msg=str(exc)), 500


@bp.get("/load")
def customer_create_load():
    refno = _safe_str(request.args.get("refno"), 32)
    if not refno:
        return jsonify(ok=False, msg="missing refno"), 400

    conn = None
    try:
        raise RuntimeError("use sqlclient bridge on migrated host")
        conn = get_db_conn()
        cur = conn.cursor()
        data = _load_customer_record(cur, refno)
        if not data:
            return jsonify(ok=False, msg="not found"), 404
        return jsonify(ok=True, data=data)
    except Exception:
        data = _load_customer_record_sc(refno)
        if not data:
            return jsonify(ok=False, msg="not found"), 404
        return jsonify(ok=True, data=data)
    except Exception as exc:
        return jsonify(ok=False, msg=str(exc)), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.post("/delete")
def customer_delete():
    payload = request.get_json(silent=True) or {}
    refnos = payload.get("refnos")
    if not isinstance(refnos, list):
        single = _safe_str(payload.get("refno"))
        refnos = [single] if single else []
    refnos = [_safe_str(v, 50) for v in refnos if _safe_str(v, 50)]
    refnos = list(dict.fromkeys(refnos))
    if not refnos:
        return jsonify(ok=False, msg="refno required"), 400

    statements = []
    for refno in refnos:
        statements.extend([
            {"sql": "DELETE FROM dbo.address WHERE refno = ? AND cate = 'c'", "params": [refno]},
            {"sql": "DELETE FROM dbo.contact WHERE refno = ? AND cate = 'c'", "params": [refno]},
            {"sql": "DELETE FROM dbo.email WHERE refno = ? AND cate = 'c'", "params": [refno]},
            {"sql": "DELETE FROM dbo.tel WHERE refno = ? AND cate = 'c'", "params": [refno]},
            {"sql": "DELETE FROM dbo.cus_rep WHERE refno = ?", "params": [refno]},
            {"sql": "DELETE FROM dbo.customer WHERE refno = ?", "params": [refno]},
        ])
    try:
        sc_execute_transaction(statements)
        return jsonify(ok=True, deleted=len(refnos), refnos=refnos)
    except Exception as exc:
        return jsonify(ok=False, msg=str(exc)), 500


@bp.post("/save")
def customer_create_save():
    payload = request.get_json(silent=True) or {}

    itac_lab_mode = _is_itac_db()
    no1 = _to_int(payload.get("no1"), None)
    no2 = _to_int(payload.get("no2"), None)
    company = _safe_str(payload.get("company"), 100)
    short = _safe_str(payload.get("short"), 10)
    if itac_lab_mode and not no1:
        lab_category = _lab_category_sc()
        no1 = _to_int(lab_category.get("id") if lab_category else None, None)
    if not no1:
        return jsonify(ok=False, msg="請選擇分類第一層"), 400
    if not company:
        return jsonify(ok=False, msg="請輸入公司名稱"), 400
    if not short:
        return jsonify(ok=False, msg="請輸入公司簡稱"), 400

    refno = _safe_str(payload.get("refno"), 32)
    addresses = _split_lines(payload.get("addresses"))
    contacts = _split_lines(payload.get("contacts"))
    tel_list = _split_lines(payload.get("tel"))
    fax_list = _split_lines(payload.get("fax"))
    emails = _split_lines(payload.get("emails"))
    sales_reps = [str(_to_int(v)).strip() for v in (payload.get("sales_reps") or []) if _to_int(v, None)]

    if not addresses:
        return jsonify(ok=False, msg="至少要有一筆地址"), 400
    if not contacts:
        return jsonify(ok=False, msg="至少要有一筆聯絡人"), 400
    if not sales_reps:
        return jsonify(ok=False, msg="至少要選一位業務代表"), 400

    try:
        prefix_meta = _resolve_customer_prefix_meta_sc(no1, no2, refno)
        prefix = prefix_meta["prefix"]
        if not prefix:
            return jsonify(ok=False, msg="找不到分類 prefix"), 400

        is_update = prefix_meta["is_update"]
        if not refno:
            refno = prefix_meta["generated_refno"]
        cate = prefix_meta["cate"]
        customer_cols = _customer_cols_sc()
        base_values = {
            "refno": refno,
            "no1": no1,
            "no2": no2,
            "cate": cate,
            "lab": 1 if itac_lab_mode else _to_int(payload.get("lab"), 0),
            "country": payload.get("country") or None,
            "company": company,
            "short": short,
            "headquarter": payload.get("headerquarter") or None,
            "url": _safe_str(payload.get("url"), 255),
            "ceo": _safe_str(payload.get("ceo"), 100),
            "class2": _safe_str(payload.get("Class2"), 100),
            "items": _safe_str(payload.get("items"), 100),
            "employee": _safe_str(payload.get("employee"), 50),
            "quit": "Y" if _safe_str(payload.get("quit")).upper() == "Y" else "N",
            "secret": 1 if _to_int(payload.get("secret"), 0) else 0,
            "licenceno": _safe_str(payload.get("LicenceNo"), 100),
            "payment": _safe_str(payload.get("payment"), 100),
            "credit": _to_decimal(payload.get("credit"), 0),
            "commission": _to_decimal(payload.get("commission"), 0),
            "remarks": _safe_str(payload.get("remarks"), 2000),
            "add_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "del": 0,
        }
        editable_cols = ["no1","no2","cate","lab","country","company","short","headquarter","url","ceo","class2","items","employee","quit","secret","licenceno","payment","credit","commission","remarks","del"]
        insert_cols = ["refno"] + editable_cols + ["add_date"]
        statements = []
        if is_update:
            update_cols = [col for col in editable_cols if col.lower() in customer_cols]
            statements.append({
                "sql": f"UPDATE dbo.customer SET {', '.join([f'[{col}] = ?' for col in update_cols])} WHERE refno = ?",
                "params": [base_values[col.lower()] for col in update_cols] + [refno],
            })
        else:
            cols = [col for col in insert_cols if col.lower() in customer_cols]
            statements.append({
                "sql": f"INSERT INTO dbo.customer ({','.join([f'[{col}]' for col in cols])}) VALUES ({','.join(['?'] * len(cols))})",
                "params": [base_values[col.lower()] for col in cols],
            })

        statements.extend([
            {"sql": "DELETE FROM dbo.address WHERE refno = ? AND cate = 'c'", "params": [refno]},
            {"sql": "DELETE FROM dbo.contact WHERE refno = ? AND cate = 'c'", "params": [refno]},
            {"sql": "DELETE FROM dbo.email WHERE refno = ? AND cate = 'c'", "params": [refno]},
            {"sql": "DELETE FROM dbo.tel WHERE refno = ? AND cate = 'c'", "params": [refno]},
            {"sql": "DELETE FROM dbo.cus_rep WHERE refno = ?", "params": [refno]},
        ])
        for value in addresses:
            statements.append({"sql": "INSERT INTO dbo.address (refno,address,cate) VALUES (?,?,?)", "params": [refno, value, "c"]})
        for value in contacts:
            statements.append({"sql": "INSERT INTO dbo.contact (refno,c_name,cate) VALUES (?,?,?)", "params": [refno, value, "c"]})
        email_field = _email_field_sc()
        for value in emails:
            if email_field:
                statements.append({
                    "sql": f"INSERT INTO dbo.email (refno,[{email_field}],cate) VALUES (?,?,?)",
                    "params": [refno, value, "c"],
                })
        for value in tel_list:
            statements.append({"sql": "INSERT INTO dbo.tel (refno,num,cate,[Def]) VALUES (?,?,?,?)", "params": [refno, value, "c", "T"]})
        for value in fax_list:
            statements.append({"sql": "INSERT INTO dbo.tel (refno,num,cate,[Def]) VALUES (?,?,?,?)", "params": [refno, value, "c", "F"]})
        for rep_id in sales_reps:
            statements.append({"sql": "INSERT INTO dbo.cus_rep (refno,sales_rep) VALUES (?,?)", "params": [refno, int(rep_id)]})
        sc_execute_transaction(statements)
        return jsonify(ok=True, refno=refno, mode="update" if is_update else "create")
    except Exception as exc:
        return jsonify(ok=False, msg=str(exc)), 500
