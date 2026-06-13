# backend/routes/customer.py
import os
import re
import pyodbc
from flask import Blueprint, request, jsonify, current_app
from dotenv import load_dotenv
from utils.db import get_db_conn
from utils.safe import _safe_str, _to_int,_safe_sort_dir,_safe_date_ymd
from utils.sqlclient_bridge import query_all as sc_query_all, query_one as sc_query_one, query_batch as sc_query_batch

load_dotenv()

customer_bp = Blueprint("customer", __name__)


def _sales_rep_sql():
    return """
        SELECT s.id, s.name
        FROM dbo.staff s
        JOIN dbo.department d ON s.dep = d.id
        JOIN dbo.manage m ON d.company_title = m.id
        WHERE m.id = 1
          AND ISNULL(s.del, 0) = 0
          AND ISNULL(s.quit, 0) = 0
        ORDER BY s.name
    """


def _is_itac_db():
    return _safe_str(os.getenv("DB_DATABASE")).lower().startswith("itac")


def _find_lab_category(cate_rows):
    for row in cate_rows or []:
        symbol = _safe_str(row.get("symbol"))
        name = _safe_str(row.get("name"))
        if symbol.upper() == "LAB" or name == "實驗室":
            return {"id": row.get("id"), "name": name, "symbol": symbol}
    return None


def _calc_next_refno(prefix: str, last_refno: str | None):
    prefix = _safe_str(prefix, 32)
    # 只允許英數（你 symbol 應該是 ABC 這種）
    prefix = re.sub(r"[^A-Za-z0-9]", "", prefix)
    if not prefix:
        return None

    if not last_refno:
        return f"{prefix}001"

    last_refno = str(last_refno).strip()
    # 取最後三碼做 +1（照你規則）
    suffix = last_refno[-3:]
    n = _to_int(suffix, 0) + 1
    return f"{prefix}{n:03d}"

@customer_bp.get("/meta")
def get_customer_meta():
    """
    一次回傳常用下拉資料：
    - countries
    - headerquarter list
    - staff list (sales reps)
    - class2 list
    - payment list
    - category level1 list
    """
    try:
        results = sc_query_batch([
            {"sql": "SELECT id, country FROM dbo.countries ORDER BY country", "params": []},
            {"sql": "SELECT id, company FROM dbo.customer WHERE ISNULL(del,0)=0 ORDER BY company", "params": []},
            {"sql": _sales_rep_sql(), "params": []},
            {"sql": "SELECT class2 FROM dbo.Class2 ORDER BY class2", "params": []},
            {"sql": "SELECT payment FROM dbo.payment ORDER BY payment", "params": []},
            {"sql": "SELECT id, ISNULL(c01,c01_e) AS name, symbol FROM dbo.cate_cust01 WHERE cate='c' ORDER BY id", "params": []},
            {"sql": "SELECT cateTxt FROM dbo.items_cf WHERE cateTxt IS NOT NULL ORDER BY cateTxt", "params": []},
        ])
        countries = results[0] if len(results) > 0 else []
        hq = results[1] if len(results) > 1 else []
        staff = results[2] if len(results) > 2 else []
        class2 = results[3] if len(results) > 3 else []
        payments = results[4] if len(results) > 4 else []
        cate1 = results[5] if len(results) > 5 else []
        items = results[6] if len(results) > 6 else []
        itac_lab_mode = _is_itac_db()
        default_lab_category = _find_lab_category(cate1) if itac_lab_mode else None
        return jsonify({
            "ok": True,
            "data": {
                "countries": [{"value": row.get("id"), "label": row.get("country")} for row in countries],
                "headerquarter": [{"value": row.get("id"), "label": row.get("company")} for row in hq],
                "staff": [{"value": row.get("id"), "label": row.get("name")} for row in staff],
                "class2": [{"value": row.get("class2"), "label": row.get("class2")} for row in class2],
                "payments": [{"value": row.get("payment"), "label": row.get("payment")} for row in payments],
                "cate_level1": [{"id": row.get("id"), "name": row.get("name"), "symbol": row.get("symbol")} for row in cate1],
                "items": [{"value": row.get("cateTxt"), "label": row.get("cateTxt")} for row in items],
                "itac_lab_mode": itac_lab_mode,
                "default_lab_category": default_lab_category,
            }
        })
    except Exception:
        conn = None
        try:
            conn = get_db_conn()
            cur = conn.cursor()

            cur.execute("SELECT id, country FROM dbo.countries ORDER BY country")
            countries = [{"value": row[0], "label": row[1]} for row in cur.fetchall()]

            cur.execute("SELECT id, company FROM dbo.customer WHERE ISNULL(del,0)=0 ORDER BY company")
            hq = [{"value": row[0], "label": row[1]} for row in cur.fetchall()]

            cur.execute(_sales_rep_sql())
            staff = [{"value": row[0], "label": row[1]} for row in cur.fetchall()]

            cur.execute("SELECT class2 FROM dbo.Class2 ORDER BY class2")
            class2 = [{"value": row[0], "label": row[0]} for row in cur.fetchall()]

            cur.execute("SELECT payment FROM dbo.payment ORDER BY payment")
            payments = [{"value": row[0], "label": row[0]} for row in cur.fetchall()]

            cur.execute("SELECT id, ISNULL(c01,c01_e) AS name, symbol FROM dbo.cate_cust01 WHERE cate='c' ORDER BY id")
            cate1 = [{"id": row[0], "name": row[1], "symbol": row[2]} for row in cur.fetchall()]
            cur.execute("SELECT cateTxt FROM dbo.items_cf WHERE cateTxt IS NOT NULL ORDER BY cateTxt")
            items = [{"value": row[0], "label": row[0]} for row in cur.fetchall()]
            itac_lab_mode = _is_itac_db()
            return jsonify({"ok": True, "data": {
                "countries": countries,
                "headerquarter": hq,
                "staff": staff,
                "class2": class2,
                "payments": payments,
                "cate_level1": cate1,
                "items": items,
                "itac_lab_mode": itac_lab_mode,
                "default_lab_category": _find_lab_category(cate1) if itac_lab_mode else None,
            }})
        except Exception as e:
            return jsonify({"ok": False, "msg": str(e)}), 500
        finally:
            try:
                if conn:
                    conn.close()
            except:
                pass

@customer_bp.get("/categories/level2")
def get_cate_level2():
    no1 = request.args.get("no1")
    no1_id = _to_int(no1, None)
    if not no1_id:
        return jsonify({"ok": False, "msg": "missing no1"}), 400

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, ISNULL(c02,c02_e) AS name, symbol FROM dbo.cate_cust02 WHERE cate='c' AND no1=? ORDER BY id",
            (no1_id,)
        )
        rows = cur.fetchall()
        data = [{"id": r[0], "name": r[1], "symbol": r[2]} for r in rows]
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

# ✅ 同時支援 GET 與 POST（避免前端用 GET、你後端寫 POST 又 405）
@customer_bp.route("/refno/preview", methods=["GET", "POST"])
def preview_refno():
    """
    GET:  /customer/refno/preview?no1=1&no2=10
    POST: body { "no1": 1, "no2": 10 }
    回傳: { ok:true, prefix:"ABC", refno:"ABC001" }
    """

    # ✅ 1) 先吃 GET querystring
    no1 = request.args.get("no1")
    no2 = request.args.get("no2")

    # ✅ 2) 若 GET 沒帶，再吃 POST JSON body
    if not no1:
        body = request.get_json(silent=True) or {}
        no1 = no1 or body.get("no1")
        no2 = no2 or body.get("no2")

    no1 = _to_int(no1, None)
    no2 = _to_int(no2, None)

    if not no1:
        return jsonify({"ok": False, "msg": "no1 required"}), 400

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        cur.execute("SELECT symbol FROM dbo.cate_cust01 WHERE cate='c' AND id=?", (no1,))
        r1 = cur.fetchone()
        r2 = None
        if no2:
            cur.execute("SELECT symbol FROM dbo.cate_cust02 WHERE cate='c' AND id=? AND no1=?", (no2, no1))
            r2 = cur.fetchone()

        if not r1 or (no2 and not r2):
            return jsonify({"ok": False, "msg": "invalid category"}), 400

        prefix = f"{_safe_str(r1[0])}{_safe_str(r2[0]) if r2 else ''}"
        prefix = re.sub(r"[^A-Za-z0-9]", "", prefix)

        cur.execute(
            "SELECT TOP 1 refno FROM dbo.customer WHERE refno LIKE ? ORDER BY refno DESC",
            (prefix + "%",)
        )
        last = cur.fetchone()
        last_refno = last[0] if last else None

        refno = _calc_next_refno(prefix, last_refno)
        if not refno:
            return jsonify({"ok": False, "msg": "cannot generate refno"}), 400

        return jsonify({"ok": True, "prefix": prefix, "refno": refno, "last": last_refno})

    except Exception:
        r1 = sc_query_one("SELECT symbol FROM dbo.cate_cust01 WHERE cate='c' AND id=?", [no1])
        r2 = sc_query_one("SELECT symbol FROM dbo.cate_cust02 WHERE cate='c' AND id=? AND no1=?", [no2, no1]) if no2 else None
        if not r1 or (no2 and not r2):
            return jsonify({"ok": False, "msg": "invalid category"}), 400

        prefix = f"{_safe_str(r1.get('symbol'))}{_safe_str(r2.get('symbol')) if r2 else ''}"
        prefix = re.sub(r"[^A-Za-z0-9]", "", prefix)
        last = sc_query_one("SELECT TOP 1 refno FROM dbo.customer WHERE refno LIKE ? ORDER BY refno DESC", [prefix + "%"])
        last_refno = last.get("refno") if last else None
        refno = _calc_next_refno(prefix, last_refno)
        if not refno:
            return jsonify({"ok": False, "msg": "cannot generate refno"}), 400
        return jsonify({"ok": True, "prefix": prefix, "refno": refno, "last": last_refno})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except:
            pass

@customer_bp.post("/create")
def create_customer():
    """
    body 範例：
    {
      "customer": {
        "no1": 1, "no2": 10,
        "refno": "ABC001",
        "company": "...",
        "short": "...",
        "country": 3,
        "headerquarter": 123,
        "url": "...",
        "gender": "M",
        "ceo_last_name": "...",
        "ceo_first_name": "...",
        "Class2": "ISO9001",
        "employee": "11~20",
        "quit": "N",
        "secret": 0,
        "LicenceNo": "...",
        "payment": "...",
        "credit": 0,
        "commission": 0,
        "remarks": "..."
      },
      "addresses": ["addr1","addr2"],
      "contacts": ["tom","mary"],
      "tel": ["02-xxxx","09xx"],
      "fax": ["02-xxxx"],
      "emails": ["a@b.com"],
      "sales_reps": [1,2,3]
    }
    """
    body = request.get_json(silent=True) or {}
    cust = body.get("customer") or {}

    # 必填最小集合（你可再加）
    no1 = _to_int(cust.get("no1"), None)
    no2 = _to_int(cust.get("no2"), None)
    company = _safe_str(cust.get("company"), 100)
    refno = _safe_str(cust.get("refno"), 32)

    if not no1 or not no2:
        return jsonify({"ok": False, "msg": "分類(no1/no2)必填"}), 400
    if not company:
        return jsonify({"ok": False, "msg": "公司名稱必填"}), 400

    try:
        conn = get_db_conn()
        conn.autocommit = False
        cur = conn.cursor()

        # 如果前端沒給 refno，就後端自己算（保底）
        if not refno:
            # 算 prefix
            cur.execute("SELECT symbol FROM dbo.cate_cust01 WHERE cate='c' AND id=?", (no1,))
            r1 = cur.fetchone()
            cur.execute("SELECT symbol FROM dbo.cate_cust02 WHERE cate='c' AND id=? AND no1=?", (no2, no1))
            r2 = cur.fetchone()
            if not r1 or not r2:
                conn.rollback()
                return jsonify({"ok": False, "msg": "invalid category"}), 400
            prefix = re.sub(r"[^A-Za-z0-9]", "", f"{_safe_str(r1[0])}{_safe_str(r2[0])}")
            cur.execute("SELECT TOP 1 refno FROM dbo.customer WHERE refno LIKE ? ORDER BY refno DESC", (prefix + "%",))
            last = cur.fetchone()
            refno = _calc_next_refno(prefix, last[0] if last else None)

        # 檢查 refno 是否已存在
        cur.execute("SELECT COUNT(1) FROM dbo.customer WHERE refno=?", (refno,))
        if cur.fetchone()[0] > 0:
            conn.rollback()
            return jsonify({"ok": False, "msg": f"客戶代號已存在：{refno}"}), 409

        # -------- insert dbo.customer --------
        # ⚠️ 這裡欄位很多，但我們用你指定的欄位（可再擴）
        sql = """
        INSERT INTO dbo.customer
        (refno, no1, no2, company, short, country, headerquarter, url,
         gender, ceo_last_name, ceo_first_name,
         Class2, employee, quit, secret,
         LicenceNo, payment, credit, commission, remarks)
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?,
         ?, ?, ?,
         ?, ?, ?, ?,
         ?, ?, ?, ?, ?)
        """
        params = (
            refno,
            no1,
            no2,
            company,
            _safe_str(cust.get("short"), 10),
            cust.get("country"),
            cust.get("headerquarter"),
            _safe_str(cust.get("url"), 255),
            _safe_str(cust.get("gender"), 1),
            _safe_str(cust.get("ceo_last_name"), 50),
            _safe_str(cust.get("ceo_first_name"), 50),
            _safe_str(cust.get("Class2"), 50),
            _safe_str(cust.get("employee"), 20),
            _safe_str(cust.get("quit"), 1) or "N",
            cust.get("secret") if cust.get("secret") is not None else 0,
            _safe_str(cust.get("LicenceNo"), 50),
            _safe_str(cust.get("payment"), 50),
            cust.get("credit"),
            cust.get("commission"),
            _safe_str(cust.get("remarks"), 2000)
        )
        cur.execute(sql, params)

        # -------- related helpers --------
        def insert_many(table, column, values, extra_cols=None):
            extra_cols = extra_cols or {}
            values = values or []
            values = [v for v in values if _safe_str(v)]
            if not values:
                return 0

            cols = ["refno", column] + list(extra_cols.keys())
            placeholders = ",".join(["?"] * len(cols))
            insert_sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"

            count = 0
            for v in values:
                row_params = [refno, _safe_str(v)] + list(extra_cols.values())
                cur.execute(insert_sql, row_params)
                count += 1
            return count

        # addresses / contacts / emails
        insert_many("dbo.address", "address", body.get("addresses"), {"cate": "c"})
        insert_many("dbo.contact", "c_name", body.get("contacts"), {"cate": "c"})
        insert_many("dbo.email", "num", body.get("emails"), {"cate": "c"})

        # tel/fax into dbo.tel with Def
        insert_many("dbo.tel", "num", body.get("tel"), {"cate": "c", "Def": "T"})
        insert_many("dbo.tel", "num", body.get("fax"), {"cate": "c", "Def": "F"})

        # sales reps into dbo.cus_rep
        reps = body.get("sales_reps") or []
        reps = [r for r in reps if _to_int(r, None)]
        for rep_id in reps:
            cur.execute("INSERT INTO dbo.cus_rep (refno, sales_rep) VALUES (?, ?)", (refno, int(rep_id)))

        conn.commit()
        return jsonify({"ok": True, "refno": refno})
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

# ✅ 在檔案末尾補上這個函數
@customer_bp.get("/list")
def get_customer_list():
    kw = (request.args.get("kw") or "").strip()
    page = _to_int(request.args.get("page"), 1)
    page_size = _to_int(request.args.get("pageSize"), 50)
    offset = (page - 1) * page_size

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        where_clause = "WHERE ISNULL(del,0)=0"
        params = []
        if kw:
            where_clause += " AND (company LIKE ? OR refno LIKE ? OR LicenceNo LIKE ?)"
            p = f"%{kw}%"
            params.extend([p, p, p])

        cur.execute(f"SELECT COUNT(1) FROM dbo.customer {where_clause}", params)
        total = cur.fetchone()[0]

        # ✅ 修正：根據您之前的代碼，dbo.tel 與 dbo.email 的號碼欄位應該是 [tel] 或 [email]
        # 如果還是錯，請檢查資料庫該表的欄位名
        sql = f"""
            SELECT id, refno, company, LicenceNo, 
                   (SELECT TOP 1 address FROM dbo.address WHERE refno = c.refno AND cate='c') as address,
                   (SELECT TOP 1 num FROM dbo.tel WHERE refno = c.refno AND cate='c' AND Def='T') as tel,
                   (SELECT TOP 1 email FROM dbo.email WHERE refno = c.refno AND cate='c') as email,
                   (SELECT TOP 1 c_name FROM dbo.contact WHERE refno = c.refno AND cate='c') as contact
            FROM dbo.customer c
            {where_clause}
            ORDER BY refno DESC
            OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
        """
        cur.execute(sql, params)
        
        rows = []
        for r in cur.fetchall():
            rows.append({
                "id": r[0],
                "refno": r[1],
                "company": r[2],
                "tax_id": r[3],
                "address": r[4],
                "tel": r[5],
                "email": r[6],
                "contact": r[7]
            })

        return jsonify({"ok": True, "total": total, "rows": rows})

    except Exception as e:
        # 如果報錯，把 SQL 也印出來方便偵錯
        current_app.logger.error(f"SQL Error: {str(e)}")
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        if conn: conn.close()
