# routes/ai_kpi.py
from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional
from utils.include import fmt_date_ymd
from flask import Blueprint, current_app, jsonify, request
from utils.include import (
    json_safe,
    rows_to_dicts,
    qdate,
    qint,
    qfloat,
)

bp = Blueprint("ai_kpi_bp", __name__, url_prefix="/api/ai")

@bp.get("/todo/priority")
def todo_priority():
    """
    AI 今日優先處理訂單（未出清優先清單）
    依「未出清金額 open_amount」與「卡單天數 aging_days」做排序

    GET /api/ai/todo/priority?from=2025-01-01&to=2025-12-31&top=200&mode=amount|days|score
    """
    top = qint("top", 200)
    mode = (request.args.get("mode") or "score").lower()

    date_from = qdate("from")
    date_to = qdate("to")

    where = ["ISNULL(open_qty,0) > 0"]
    params = []

    if date_from:
        where.append("order_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("order_date < DATEADD(day,1,?)")
        params.append(date_to)

    where_sql = "WHERE " + " AND ".join(where)

    # ✅ open_amount：用比例估算（避免你 Fact 沒有 open_amount 欄位）
    #    open_amount = order_amount * (open_qty / NULLIF(order_qty,0))
    # ✅ aging_days：以訂單日到今天的天數（若你要改 last_ship_date 可再調）
    sql = f"""
    WITH X AS (
      SELECT
        quotation_id, customer_id, customer_name, currency,
        LTRIM(RTRIM(pi_form_no)) AS pi_form_no,
        LTRIM(RTRIM(order_no)) AS order_no,
        LTRIM(RTRIM(c_order_no)) AS c_order_no,
        order_date,
        sales_rep_id, sales_rep_name,
        LTRIM(RTRIM(product_no)) AS product_no,
        product_cate,
        order_qty, ship_qty, open_qty,
        order_amount, ship_amount_cached,
        last_ship_date, fulfill_status,

        CAST(DATEDIFF(day, CAST(order_date AS date), CAST(GETDATE() AS date)) AS int) AS aging_days,

        CAST(
          ISNULL(order_amount,0) *
          (ISNULL(open_qty,0) / NULLIF(ISNULL(order_qty,0),0))
          AS decimal(18,2)
        ) AS open_amount,

        CAST(
          (
            ISNULL(order_amount,0) *
            (ISNULL(open_qty,0) / NULLIF(ISNULL(order_qty,0),0))
          ) * (1 + (DATEDIFF(day, CAST(order_date AS date), CAST(GETDATE() AS date)) / 30.0))
          AS decimal(18,2)
        ) AS score
      FROM dbo.ai_Fact_order_ship
      {where_sql}
    )
    SELECT TOP ({top}) *
    FROM X
    ORDER BY
      CASE WHEN ? = 'amount' THEN open_amount END DESC,
      CASE WHEN ? = 'days'   THEN aging_days  END DESC,
      CASE WHEN ? = 'score'  THEN score      END DESC,
      score DESC, open_amount DESC, aging_days DESC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, params + [mode, mode, mode])
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "mode": mode, "data": data})

@bp.get("/kpi/fulfill")
def fulfill():
    """
    出貨達成率（客戶/業務/公司別）
    GET /api/ai/kpi/fulfill?from=2025-01-01&to=2025-12-31&by=customer|sales|company&top=200
    """
    date_from = qdate("from")
    date_to = qdate("to")
    top = qint("top", 200)
    by = (request.args.get("by") or "customer").lower()

    where = []
    params = []
    if date_from:
        where.append("order_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("order_date < DATEADD(day,1,?)")
        params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    # ✅ 分組欄位
    if by == "sales":
        g_id = "sales_rep_id"
        g_name = "sales_rep_name"
    elif by == "company":
        # ⚠️ 你 Fact 若沒有 company_title，這個要改成實際欄位或先不要開
        g_id = "company_title"
        g_name = "company_title"
    else:
        by = "customer"
        g_id = "customer_id"
        g_name = "customer_name"

    sql = f"""
    SELECT TOP ({top})
      {g_id} AS group_id,
      {g_name} AS group_name,
      SUM(ISNULL(order_amount,0)) AS order_amount_sum,
      SUM(ISNULL(ship_amount_cached,0)) AS ship_amount_sum,
      SUM(CASE WHEN ISNULL(open_qty,0) > 0 THEN 1 ELSE 0 END) AS open_line_count,
      COUNT(*) AS line_count
    FROM dbo.ai_Fact_order_ship
    {where_sql}
    GROUP BY {g_id}, {g_name}
    ORDER BY SUM(ISNULL(ship_amount_cached,0)) DESC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, params)
    data = rows_to_dicts(cur)
    conn.close()

    # ✅ 達成率在後端算也可以（避免前端除零）
    for r in data:
        oa = float(r.get("order_amount_sum") or 0)
        sa = float(r.get("ship_amount_sum") or 0)
        r["fulfill_rate"] = 0 if oa == 0 else (sa / oa)

    return jsonify({"ok": True, "by": by, "data": data})

@bp.get("/debug/by-quotation")
def debug_by_quotation():
    qid = qint("quotation_id", 0)
    if qid <= 0:
        return jsonify({"ok": False, "error": "missing quotation_id"}), 400

    sql = """
    SELECT TOP (50)
      quotation_id, customer_name, currency,
      pi_form_no, order_no, c_order_no, order_date,
      product_no, product_cate,
      order_qty, ship_qty, open_qty,
      order_amount, ship_amount_cached,
      last_ship_date, fulfill_status
    FROM dbo.ai_Fact_order_ship
    WHERE quotation_id = ?
    ORDER BY order_date DESC;
    """
    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, [qid])
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "quotation_id": qid, "data": data})

@bp.get("/list/lines")
def list_lines():
    """
    通用清單：全部 / 未出清 / 已出清
    GET /api/ai/list/lines?
      status=all|open|closed
      &from=2025-01-01&to=2025-12-31
      &customer=BEN
      &sales_rep=Tom
      &company_title=VOLX
      &top=500
    """
    status = (request.args.get("status") or "all").lower()
    top = qint("top", 500)

    date_from = qdate("from")
    date_to = qdate("to")

    customer = (request.args.get("customer") or "").strip()
    sales_rep = (request.args.get("sales_rep") or "").strip()
    company_title = (request.args.get("company_title") or "").strip()

    where = []
    params = []

    # 狀態
    if status == "open":
        where.append("ISNULL(open_qty,0) > 0")
    elif status == "closed":
        where.append("ISNULL(open_qty,0) = 0")

    # 日期區間（以 order_date）
    if date_from:
        where.append("order_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("order_date < DATEADD(day,1,?)")
        params.append(date_to)

    # 文字 filters（用 LIKE）
    if customer:
        where.append("customer_name LIKE ?")
        params.append(f"%{customer}%")
    if sales_rep:
        where.append("sales_rep_name LIKE ?")
        params.append(f"%{sales_rep}%")
    if company_title:
        # 如果你 Fact 表沒有 company_title，就先拿掉這段；或改成你實際欄位
        where.append("company_title LIKE ?")
        params.append(f"%{company_title}%")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
    SELECT TOP ({top})
      quotation_id, customer_id, customer_name, currency,
      LTRIM(RTRIM(pi_form_no)) AS pi_form_no,
      LTRIM(RTRIM(order_no)) AS order_no,
      LTRIM(RTRIM(c_order_no)) AS c_order_no,
      order_date,
      sales_rep_id, sales_rep_name,
      LTRIM(RTRIM(product_no)) AS product_no,
      product_cate,
      order_qty, ship_qty, open_qty,
      order_amount, ship_amount_cached,
      last_ship_date, fulfill_status
      -- company_title 若表內沒有就不要選
    FROM dbo.ai_Fact_order_ship
    {where_sql}
    ORDER BY order_date DESC, order_amount DESC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, params)
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "status": status, "data": data})

@bp.get("/debug/by-pi")
def debug_by_pi():
    pi = (request.args.get("pi_form_no") or "").strip()
    if not pi:
        return jsonify({"ok": False, "error": "missing pi_form_no"}), 400

    sql = """
    SELECT TOP (200)
      quotation_id, customer_name, currency,
      LTRIM(RTRIM(pi_form_no)) AS pi_form_no,
      LTRIM(RTRIM(order_no)) AS order_no,
      LTRIM(RTRIM(c_order_no)) AS c_order_no,
      order_date,
      product_no, product_cate,
      order_qty, ship_qty, open_qty,
      order_amount, ship_amount_cached,
      last_ship_date, fulfill_status
    FROM dbo.ai_Fact_order_ship
    WHERE LTRIM(RTRIM(pi_form_no)) = ?
       OR LTRIM(RTRIM(order_no)) = ?
    ORDER BY order_date DESC, quotation_id DESC;
    """
    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, [pi, pi])
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "pi_form_no": pi, "data": data})


# =========================================================
# 🔍 分析類
# =========================================================

@bp.get("/kpi/top-products")
def top_products():
    """
    最暢銷產品（依 ship_qty 或 ship_amount_cached）
    GET /api/ai/kpi/top-products?from=2025-01-01&to=2025-12-31&top=20&by=qty|amount
    """
    date_from = qdate("from")
    date_to = qdate("to")
    top = qint("top", 20)
    by = (request.args.get("by") or "qty").lower()

    metric = "SUM(ISNULL(ship_qty,0))" if by != "amount" else "SUM(ISNULL(ship_amount_cached,0))"
    metric_alias = "ship_qty_sum" if by != "amount" else "ship_amount_sum"

    where = []
    params = []

    if date_from:
        where.append("order_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("order_date < DATEADD(day,1,?)")
        params.append(date_to)

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
    SELECT TOP ({top})
      LTRIM(RTRIM(product_no)) AS product_no,
      product_cate,
      {metric} AS {metric_alias},
      COUNT(*) AS line_count,
      COUNT(DISTINCT customer_id) AS buyer_count
    FROM dbo.ai_Fact_order_ship
    {where_sql}
    GROUP BY LTRIM(RTRIM(product_no)), product_cate
    ORDER BY {metric_alias} DESC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, params)
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "data": data})

@bp.get("/debug/product-lines")
def debug_product_lines():
    product_no = (request.args.get("product_no") or "").strip()
    top = qint("top", 50)
    if not product_no:
        return jsonify({"ok": False, "error": "missing product_no"}), 400

    sql = f"""
    SELECT TOP ({top})
      quotation_id, customer_name,currency, pi_form_no, order_no, order_date,
      product_no, product_cate,
      order_qty, ship_qty, open_qty,
      order_amount, ship_amount_cached,
      last_ship_date
    FROM dbo.ai_Fact_order_ship
    WHERE product_no = ?
    ORDER BY order_date DESC;
    """
    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, [product_no])
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "product_no": product_no, "data": data})

@bp.get("/kpi/top-customers")
def top_customers():
    """
    最大買家（依出貨金額ship_amount_cached / 訂單金額order_amount）
    GET /api/ai/kpi/top-customers?from=...&to=...&top=20&by=ship|order
    """
    date_from = qdate("from")
    date_to = qdate("to")
    top = qint("top", 20)
    by = (request.args.get("by") or "ship").lower()

    metric = "SUM(ISNULL(ship_amount_cached,0))" if by != "order" else "SUM(ISNULL(order_amount,0))"
    metric_alias = "ship_amount_sum" if by != "order" else "order_amount_sum"

    where = []
    params = []
    if date_from:
        where.append("order_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("order_date < DATEADD(day,1,?)")
        params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
    SELECT TOP ({top})
      customer_id,
      customer_name,currency,
      {metric} AS {metric_alias},
      COUNT(DISTINCT pi_form_no) AS pi_count,
      COUNT(*) AS line_count
    FROM dbo.ai_Fact_order_ship
    {where_sql}
    GROUP BY customer_id, customer_name,currency
    ORDER BY {metric_alias} DESC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, params)
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "data": data})


@bp.get("/kpi/sales-perf")
def sales_perf():
    """
    業務績效（依出貨金額/訂單金額/未出貨筆數）
    GET /api/ai/kpi/sales-perf?from=...&to=...
    """
    date_from = qdate("from")
    date_to = qdate("to")

    where = []
    params = []
    if date_from:
        where.append("order_date >= ?")
        params.append(date_from)
    if date_to:
        where.append("order_date < DATEADD(day,1,?)")
        params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
    SELECT
      sales_rep_id,
      sales_rep_name,
      SUM(ISNULL(order_amount,0)) AS order_amount_sum,
      SUM(ISNULL(ship_amount_cached,0)) AS ship_amount_sum,
      SUM(CASE WHEN ISNULL(open_qty,0) > 0 THEN 1 ELSE 0 END) AS open_line_count,
      SUM(ISNULL(open_qty,0)) AS open_qty_sum,
      COUNT(DISTINCT pi_form_no) AS pi_count,
      COUNT(*) AS line_count
    FROM dbo.ai_Fact_order_ship
    {where_sql}
    GROUP BY sales_rep_id, sales_rep_name
    ORDER BY ship_amount_sum DESC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, params)
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "data": data})


@bp.get("/list/open-lines")
def open_lines():
    """
    未出貨清單（open_qty > 0）
    GET /api/ai/list/open-lines?top=200&sales_rep_id=...&customer_id=...
    """
    top = qint("top", 200)
    sales_rep_id = (request.args.get("sales_rep_id") or "").strip()
    customer_id = (request.args.get("customer_id") or "").strip()

    where = ["ISNULL(open_qty,0) > 0"]
    params = []

    if sales_rep_id:
        where.append("sales_rep_id = ?")
        params.append(sales_rep_id)
    if customer_id:
        where.append("customer_id = ?")
        params.append(customer_id)

    sql = f"""
    SELECT TOP ({top})
      quotation_id, customer_id, customer_name,currency,
      pi_form_no, order_no, c_order_no, order_date,
      sales_rep_id, sales_rep_name,
      LTRIM(RTRIM(product_no)) AS product_no, product_cate,
      order_qty, ship_qty, open_qty,
      order_amount, ship_amount_cached,
      last_ship_date, fulfill_status
    FROM dbo.ai_Fact_order_ship
    WHERE {" AND ".join(where)}
    ORDER BY order_date ASC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, params)
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "data": data})


@bp.get("/audit/ship-anomalies")
def ship_anomalies():
    """
    出貨異常：ship_amount_cached ≠ order_amount（可設門檻）
    GET /api/ai/audit/ship-anomalies?abs=1&ratio=0.01&top=200
    """
    top = qint("top", 200)
    abs_threshold = qfloat("abs", 1.0)     # 金額差 > 1 元才列
    ratio_threshold = qfloat("ratio", 0.0) # 例如 0.01 代表 1%

    # 注意：避免除以 0
    sql = f"""
    SELECT TOP ({top})
      quotation_id, customer_id, customer_name,currency,
      pi_form_no, order_no, order_date,
      sales_rep_name,
      LTRIM(RTRIM(product_no)) AS product_no, product_cate,
      order_amount, ship_amount_cached,
      (ISNULL(ship_amount_cached,0) - ISNULL(order_amount,0)) AS diff_amount,
      CASE WHEN ISNULL(order_amount,0) = 0 THEN NULL
           ELSE (ISNULL(ship_amount_cached,0) - ISNULL(order_amount,0)) / NULLIF(order_amount,0)
      END AS diff_ratio,
      fulfill_status, open_qty, last_ship_date
    FROM dbo.ai_Fact_order_ship
    WHERE ABS(ISNULL(ship_amount_cached,0) - ISNULL(order_amount,0)) >= ?
      AND (
        ? = 0
        OR (
          ISNULL(order_amount,0) <> 0
          AND ABS((ISNULL(ship_amount_cached,0) - ISNULL(order_amount,0)) / NULLIF(order_amount,0)) >= ?
        )
      )
    ORDER BY ABS(ISNULL(ship_amount_cached,0) - ISNULL(order_amount,0)) DESC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, [abs_threshold, ratio_threshold, ratio_threshold])
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "data": data})


# =========================================================
# 🔔 提醒類
# =========================================================

@bp.get("/alerts/no-ship-x-days")
def alert_no_ship_x_days():
    """
    客戶下單但 X 天未出貨（可用版）
    GET /api/ai/alerts/no-ship-x-days?days=7&window_days=180&min_amount=5000&top=200
    """
    days = qint("days", 7)
    window_days = qint("window_days", 180)      # ✅ 只看最近180天訂單
    min_amount = qfloat("min_amount", 0.0)      # ✅ 小單不吵人
    top = qint("top", 200)

    sql = f"""
    SELECT TOP ({top})
      quotation_id, customer_id, customer_name,currency,
      LTRIM(RTRIM(pi_form_no)) AS pi_form_no,
      LTRIM(RTRIM(order_no)) AS order_no,
      LTRIM(RTRIM(c_order_no)) AS c_order_no,
      order_date,
      sales_rep_name,
      LTRIM(RTRIM(product_no)) AS product_no,
      product_cate,
      order_qty, ship_qty, open_qty,
      order_amount, ship_amount_cached,
      last_ship_date, fulfill_status
    FROM dbo.ai_Fact_order_ship
    WHERE ISNULL(open_qty,0) > 0
      AND last_ship_date IS NULL
      AND order_date >= DATEADD(day, -?, CAST(GETDATE() AS date))   -- window_days
      AND order_date <= DATEADD(day, -?, CAST(GETDATE() AS date))   -- days
      AND ISNULL(order_amount,0) >= ?
    ORDER BY order_date ASC, order_amount DESC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, [window_days, days, min_amount])
    data = rows_to_dicts(cur)
    conn.close()

    return jsonify({"ok": True, "days": days, "window_days": window_days, "min_amount": min_amount, "data": data})


@bp.get("/alerts/partial-stuck")
def alert_partial_stuck():
    """
    部分出貨卡太久：PARTIAL 且 last_ship_date <= today - days
    GET /api/ai/alerts/partial-stuck?days=14&top=200
    """
    days = qint("days", 14)
    top = qint("top", 200)

    sql = f"""
    SELECT TOP ({top})
      quotation_id, customer_id, customer_name,currency,
      pi_form_no, order_no, order_date,
      sales_rep_name,
      LTRIM(RTRIM(product_no)) AS product_no, product_cate,
      order_qty, ship_qty, open_qty,
      order_amount, ship_amount_cached,
      last_ship_date, fulfill_status
    FROM dbo.ai_Fact_order_ship
    WHERE fulfill_status = 'PARTIAL'
      AND ISNULL(open_qty,0) > 0
      AND last_ship_date IS NOT NULL
      AND last_ship_date <= CAST(GETDATE() - ? AS date)
    ORDER BY last_ship_date ASC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, [days])
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "days": days, "data": data})


@bp.get("/alerts/big-open-orders")
def alert_big_open_orders():
    """
    訂單金額大但尚未全出：open_qty>0 且 order_amount >= threshold
    GET /api/ai/alerts/big-open-orders?amount=100000&top=200
    """
    amount = qfloat("amount", 100000.0)
    top = qint("top", 200)

    sql = f"""
    SELECT TOP ({top})
      quotation_id, customer_id, customer_name,currency,
      pi_form_no, order_no, order_date,
      sales_rep_name,
      LTRIM(RTRIM(product_no)) AS product_no, product_cate,
      order_qty, ship_qty, open_qty,
      order_amount, ship_amount_cached,
      last_ship_date, fulfill_status
    FROM dbo.ai_Fact_order_ship
    WHERE ISNULL(open_qty,0) > 0
      AND ISNULL(order_amount,0) >= ?
    ORDER BY order_amount DESC, order_date ASC;
    """

    conn = current_app.config["GET_DB_CONN"]()
    cur = conn.cursor()
    cur.execute(sql, [amount])
    data = rows_to_dicts(cur)
    conn.close()
    return jsonify({"ok": True, "amount": amount, "data": data})
