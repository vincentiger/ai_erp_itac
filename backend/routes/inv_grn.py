# backend/routes/inv_grn.py
from __future__ import annotations

from datetime import datetime
from flask import Blueprint, current_app, jsonify, request
from utils.include import rows_to_dicts

bp = Blueprint("inv_grn_api", __name__, url_prefix="/api/inv/grn")


def get_db_conn():
    return current_app.config["GET_DB_CONN"]()


def _ok(**payload):
    return jsonify({"ok": True, **payload})


def _bad(msg, code=400):
    return jsonify({"ok": False, "msg": msg}), code


def _get_user() -> str:
    # 你有登入系統就換成你既有取用戶的方法
    return (request.headers.get("X-User") or current_app.config.get("DEFAULT_USER") or "system").strip()


def _gen_grn_no(cur) -> str:
    # 例：GRN2502010001（可依你編號規則再調）
    yymmdd = datetime.now().strftime("%y%m%d")
    prefix = f"GRN{yymmdd}"
    cur.execute(
        "SELECT ISNULL(MAX(grn_no),'') FROM dbo.inv_grn WHERE grn_no LIKE ?",
        (prefix + "%",),
    )
    max_no = (cur.fetchone()[0] or "").strip()
    if not max_no:
        return prefix + "0001"
    seq = int(max_no[-4:]) + 1
    return prefix + f"{seq:04d}"

def rows_to_dicts(cur):
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _ok(**kwargs):
    return jsonify({"ok": True, **kwargs})


def _bad(msg, code=400):
    return jsonify({"ok": False, "msg": msg}), code


@bp.get("/lines")
def list_grn_lines():
    """
    進貨明細列表（兩列一筆給前端用）
    GET /api/inv/grn/lines?status=&kw=&page=1&pageSize=20
    """
    status = (request.args.get("status") or "").strip().upper()
    kw = (request.args.get("kw") or "").strip()

    try:
        page = int(request.args.get("page") or 1)
    except Exception:
        page = 1
    try:
        page_size = int(request.args.get("pageSize") or 20)
    except Exception:
        page_size = 20

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 200:
        page_size = 200  # 防呆

    where = ["1=1"]
    params = []

    if status:
        where.append("g.status = ?")
        params.append(status)

    if kw:
        like = f"%{kw}%"
        where.append(
            "("
            "g.grn_no LIKE ? OR "
            "ISNULL(g.po_no,'') LIKE ? OR "
            "ISNULL(ap.po_no,'') LIKE ? OR "
            "ISNULL(g.po_form_no,'') LIKE ? OR "
            "ISNULL(l.item_no,'') LIKE ? OR "
            "ISNULL(ap.description,'') LIKE ? OR "
            "ISNULL(ap.factory,'') LIKE ?"
            ")"
        )
        params.extend([like, like, like, like, like, like, like])

    where_sql = " AND ".join(where)

    # ✅ 共用 FROM/JOIN
    # ai_purchase.id = inv_grn_line.purchase_list_id
    from_join_sql = f"""
        FROM dbo.inv_grn_line l
        INNER JOIN dbo.inv_grn g ON g.grn_id = l.grn_id
        LEFT JOIN dbo.ai_purchase ap ON ap.id = l.purchase_list_id
        WHERE {where_sql}
    """

    # ✅ 欄位（前端列表會用到）
    select_cols = """
        l.grn_line_id,
        CAST(l.grn_id AS INT) AS grn_id,
        g.grn_no,
        g.status,
        g.grn_date,
        g.po_form_no,
        ISNULL(ap.po_no, ISNULL(g.po_no, '')) AS po_no,
        ISNULL(ap.factory, '') AS factory,
        l.item_no,
        ISNULL(ap.description, '') AS description,
        l.po_qty,
        l.recv_qty,
        l.currency,
        l.unit_price
    """

    conn = get_db_conn()
    cur = conn.cursor()

    try:
        # ✅ total
        cur.execute(f"SELECT COUNT(1) AS total {from_join_sql}", tuple(params))
        total = int(cur.fetchone()[0] or 0)

        # ✅ 分頁：ROW_NUMBER（SQL 2005+）
        offset = (page - 1) * page_size
        start_row = offset + 1
        end_row = offset + page_size

        try:
            sql_rn = f"""
                SELECT *
                FROM (
                    SELECT
                        {select_cols},
                        ROW_NUMBER() OVER (ORDER BY l.grn_line_id DESC) AS rn
                    {from_join_sql}
                ) X
                WHERE X.rn BETWEEN ? AND ?
                ORDER BY X.rn
            """
            cur.execute(sql_rn, tuple(params) + (start_row, end_row))
            items = rows_to_dicts(cur)
            return _ok(items=items, total=total, page=page, pageSize=page_size)

        except Exception:
            # ✅ fallback：SQL Server 2000 舊式分頁（最小可用）
            if offset <= 0:
                sql_top = f"""
                    SELECT TOP {page_size}
                        {select_cols}
                    {from_join_sql}
                    ORDER BY l.grn_line_id DESC
                """
                cur.execute(sql_top, tuple(params))
                items = rows_to_dicts(cur)
                return _ok(items=items, total=total, page=page, pageSize=page_size)

            sql_fallback = f"""
                SELECT TOP {page_size}
                    {select_cols}
                {from_join_sql}
                AND l.grn_line_id NOT IN (
                    SELECT TOP {offset} l2.grn_line_id
                    FROM dbo.inv_grn_line l2
                    INNER JOIN dbo.inv_grn g2 ON g2.grn_id = l2.grn_id
                    LEFT JOIN dbo.ai_purchase ap2 ON ap2.id = l2.purchase_list_id
                    WHERE {where_sql}
                    ORDER BY l2.grn_line_id DESC
                )
                ORDER BY l.grn_line_id DESC
            """
            cur.execute(sql_fallback, tuple(params))
            items = rows_to_dicts(cur)
            return _ok(items=items, total=total, page=page, pageSize=page_size)

    except Exception as e:
        return _bad(f"系統錯誤: {str(e)}", 500)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        
# ------------------------------------------------------------
# GET: open POs (for creating GRN)
# ------------------------------------------------------------
@bp.get("/po/open")
def po_open():
    page = int(request.args.get("page") or 1)
    pageSize = int(request.args.get("pageSize") or 20)
    if page < 1: page = 1
    if pageSize < 1: pageSize = 20
    if pageSize > 200: pageSize = 200

    date_from = request.args.get("from")
    date_to = request.args.get("to")
    factory_kw = (request.args.get("factory_kw") or "").strip()
    item_kw = (request.args.get("item_kw") or "").strip()
    po_kw = (request.args.get("po_kw") or "").strip()

    where = " where left(right(p.form_no,3),1)<>'R' "
    params = []

    if date_from:
        where += " and p.original_date >= ? "
        params.append(date_from)
    if date_to:
        where += " and p.original_date <= ? "
        params.append(date_to)

    if factory_kw:
        where += " and isnull(f.company_c,f.company) like ? "
        params.append(f"%{factory_kw}%")

    if item_kw:
        where += " and pl.item_no like ? "
        params.append(f"%{item_kw}%")

    if po_kw:
        where += " and (p.po_no like ? or p.form_no like ?) "
        params.extend([f"%{po_kw}%", f"%{po_kw}%"])

    base_sql = f"""
    from purchase p
    inner join purchase_list pl on p.form_no=pl.form_no
    inner join factory f on f.id=p.factory_id
    {where}
    """

    count_sql = "select count(1) as cnt " + base_sql

    select_sql = """
    select
      p.original_date as poDate,
      p.po_no,
      p.form_no as po_form_no,
      isnull(f.company_c,f.company) as factory,
      pl.id as purchase_list_id,
      pl.item_no,
      pl.f_qty as po_qty,
      ISNULL(pl.DescriptionC, pl.description) AS description 
    """ + base_sql + """
    order by p.original_date desc, p.po_no desc, pl.item_no asc
    offset ? rows fetch next ? rows only
    """

    offset = (page - 1) * pageSize

    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute(count_sql, params)
    total = int(cur.fetchone()[0])

    cur.execute(select_sql, params + [offset, pageSize])
    items = rows_to_dicts(cur)

    # 預設 recv_qty=0（前端會改成=po_qty）
    for r in items:
        r["recv_qty"] = 0

    return _ok(items=items, total=total, page=page, pageSize=pageSize)


# ------------------------------------------------------------
# GET: PO lines (for preview)
# ------------------------------------------------------------
@bp.get("/po/<po_form_no>/lines")
def po_lines(po_form_no: str):
    # ⚠️ 這裡假設 purchase_list 主鍵是 id；若不是，請改欄位名
    sql = """
    select
      pl.id as purchase_list_id,
      pl.item_no as item_no,
      pl.pi_item_no as pi_item_no,
      pl.f_qty as po_qty,
      (pl.f_price / isnull(pl.unit_value,1)) as unit_price,
      pl.currency as currency,
      pl.memo as memo
    from purchase_list pl
    where pl.form_no = ?
    order by pl.id
    """
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(sql, (po_form_no,))
    lines = rows_to_dicts(cur)
    if not lines:
        return _bad("PO 無明細或找不到 purchase_list", 404)
    # 預設 recv_qty = 0
    for r in lines:
        r["recv_qty"] = 0
    return _ok(lines=lines)


# ------------------------------------------------------------
# POST: create GRN from PO
# body: { po_form_no, wh_id?, grn_date?, memo? }
# ------------------------------------------------------------
@bp.post("/create")
def create_grn():
    data = request.get_json(silent=True) or {}
    po_form_no = (data.get("po_form_no") or "").strip()
    if not po_form_no:
        return _bad("po_form_no 必填")

    wh_id = data.get("wh_id")
    wh_id = int(wh_id) if wh_id not in (None, "") else None

    grn_date = (data.get("grn_date") or datetime.now().strftime("%Y-%m-%d")).strip()
    memo = (data.get("memo") or "").strip()
    user = _get_user()

    # ✅ 前端可帶入：lines=[{purchase_list_id, recv_qty}, ...]
    incoming_lines = data.get("lines") or []
    line_overrides = {}
    try:
        for ln in incoming_lines:
            pid = int((ln or {}).get("purchase_list_id") or 0)
            rq = float((ln or {}).get("recv_qty") or 0)
            if pid > 0:
                line_overrides[pid] = rq
    except Exception:
        line_overrides = {}

    conn = get_db_conn()
    cur = conn.cursor()

    try:
        # -----------------------
        # 讀 PO head
        # -----------------------
        cur.execute(
            """
            select top 1
              p.po_no,
              p.factory_id,
              p.sales_rep as sales_rep_id,
              m.title as company_title
            from purchase p
            left join manage m on p.company_title=m.id
            where p.form_no=?
            """,
            (po_form_no,),
        )
        head = cur.fetchone()
        if not head:
            conn.rollback()
            return _bad("找不到 PO(form_no)", 404)

        po_no, factory_id, sales_rep_id, company_title = head[0], head[1], head[2], head[3]

        # -----------------------
        # 讀 PO lines
        # -----------------------
        cur.execute(
            """
            select
            pl.id as purchase_list_id,
            pl.item_no,
            cast(null as varchar(50)) as pi_item_no,
            cast(pl.f_qty as decimal(18,4)) as po_qty,
            cast((pl.f_price / isnull(pl.unit_value,1)) as decimal(18,6)) as unit_price,
            cast(p.currency as varchar(10)) as currency,
            cast(null as nvarchar(500)) as memo
            from purchase_list pl
            inner join purchase p on p.form_no = pl.form_no
            where pl.form_no=?
            order by pl.id
            """,
            (po_form_no,),
        )
        po_lines = rows_to_dicts(cur)
        if not po_lines:
            conn.rollback()
            return _bad("PO 無明細", 400)

        # ✅ 只允許套用本 PO 的 purchase_list_id，避免前端亂塞
        valid_ids = {int(r.get("purchase_list_id") or 0) for r in po_lines}
        if line_overrides:
            line_overrides = {pid: qty for pid, qty in line_overrides.items() if pid in valid_ids}

        # -----------------------
        # 建 GRN（✅ 用 OUTPUT 拿 grn_id；不要再 scope_identity）
        # -----------------------
        grn_no = _gen_grn_no(cur)

        cur.execute(
            """
            insert into dbo.inv_grn
              (grn_no, po_form_no, grn_date, status, created_by, wh_id, po_no, factory_id, sales_rep_id, company_title, memo)
            output inserted.grn_id
            values
              (?, ?, ?, 'OPEN', ?, ?, ?, ?, ?, ?, ?)
            """,
            (grn_no, po_form_no, grn_date, user, wh_id, po_no, factory_id, sales_rep_id, company_title, memo),
        )

        row = cur.fetchone()
        grn_id = int(row[0]) if row and row[0] is not None else None
        if not grn_id:
            raise Exception("建立 GRN 成功但無法取得 grn_id（OUTPUT inserted.grn_id 為空）")

        # -----------------------
        # 建 GRN lines（recv_qty 依前端帶入，未勾/未填就 0）
        # -----------------------
        for pl in po_lines:
            plid = int(pl.get("purchase_list_id") or 0)
            recv_qty = float(line_overrides.get(plid, 0) or 0)

            cur.execute(
                """
                insert into dbo.inv_grn_line
                  (grn_id, purchase_list_id, item_no, pi_item_no, po_qty, recv_qty, unit_price, currency, memo)
                values
                  (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    grn_id,
                    plid,
                    pl.get("item_no"),
                    pl.get("pi_item_no"),
                    pl.get("po_qty") or 0,
                    recv_qty,
                    pl.get("unit_price"),
                    pl.get("currency"),
                    pl.get("memo"),
                ),
            )

        conn.commit()
        return _ok(grn_id=grn_id, grn_no=grn_no)

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return _bad(f"建立 GRN 失敗: {str(e)}", 500)


# ------------------------------------------------------------
# GET: GRN list
# ------------------------------------------------------------
@bp.get("/list")
def grn_list():
    status = (request.args.get("status") or "").strip()
    sql = """
    select top 200
      g.grn_id, g.grn_no, g.po_no, g.po_form_no, g.grn_date, g.status, g.created_at,
      isnull(f.company_c,f.company) as factory
    from dbo.inv_grn g
    left join factory f on f.id=g.factory_id
    where 1=1
    """
    params = []
    if status:
        sql += " and g.status=?"
        params.append(status)
    sql += " order by g.grn_id desc"

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    return _ok(items=rows_to_dicts(cur))


# ------------------------------------------------------------
# GET: GRN detail
# ------------------------------------------------------------
@bp.get("/<int:grn_id>")
def grn_detail(grn_id: int):
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute(
        """
        select
          grn_id, grn_no, po_form_no, po_no, grn_date, status, created_by, created_at,
          wh_id, factory_id, sales_rep_id, company_title, memo, posted_by, posted_at
        from dbo.inv_grn
        where grn_id=?
        """,
        (grn_id,),
    )
    head = rows_to_dicts(cur)
    if not head:
        return _bad("找不到 GRN", 404)

    cur.execute(
        """
        select
          grn_line_id, purchase_list_id, item_no, pi_item_no, po_qty, recv_qty, unit_price, currency, memo, created_at
        from dbo.inv_grn_line
        where grn_id=?
        order by grn_line_id
        """,
        (grn_id,),
    )
    lines = rows_to_dicts(cur)
    return _ok(head=head[0], lines=lines)


# ------------------------------------------------------------
# POST: save GRN lines
# body: { grn_date?, wh_id?, memo?, lines:[{grn_line_id, recv_qty, memo?}] }
# ------------------------------------------------------------
@bp.post("/<int:grn_id>/save")
def grn_save(grn_id: int):
    data = request.get_json(silent=True) or {}
    user = _get_user()

    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("select status from dbo.inv_grn where grn_id=?", (grn_id,))
    row = cur.fetchone()
    if not row:
        return _bad("找不到 GRN", 404)

    status = (row[0] or "").upper()
    if status not in ("OPEN", "DRAFT"):
        return _bad("目前狀態不可修改（只允許 OPEN/DRAFT）", 400)

    grn_date = data.get("grn_date")
    wh_id = data.get("wh_id")
    memo = data.get("memo")
    if wh_id == "":
        wh_id = None

    if grn_date is not None or wh_id is not None or memo is not None:
        cur.execute(
            """
            update dbo.inv_grn
            set grn_date = isnull(?, grn_date),
                wh_id = ?,
                memo = isnull(?, memo)
            where grn_id=?
            """,
            (grn_date, wh_id, memo, grn_id),
        )

    lines = data.get("lines") or []
    for ln in lines:
        grn_line_id = int(ln.get("grn_line_id") or 0)
        recv_qty = float(ln.get("recv_qty") or 0)
        line_memo = ln.get("memo")
        cur.execute(
            """
            update dbo.inv_grn_line
            set recv_qty=?, memo=isnull(?, memo)
            where grn_id=? and grn_line_id=?
            """,
            (recv_qty, line_memo, grn_id, grn_line_id),
        )

    conn.commit()
    return _ok(grn_id=grn_id, saved_by=user)


# ------------------------------------------------------------
# POST: post GRN (minimal)
# - set status=POSTED, posted_by/posted_at
# ------------------------------------------------------------
@bp.post("/<int:grn_id>/post")
def grn_post(grn_id: int):
    user = _get_user()
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("select grn_no, status from dbo.inv_grn where grn_id=?", (grn_id,))
    row = cur.fetchone()
    if not row:
        return _bad("找不到 GRN", 404)

    grn_no = row[0]
    status = (row[1] or "").upper()
    if status == "POSTED":
        return _bad("已過帳", 400)
    if status not in ("OPEN", "DRAFT"):
        return _bad("目前狀態不可過帳", 400)

    # 至少一筆 recv_qty > 0
    cur.execute("select count(1) from dbo.inv_grn_line where grn_id=? and recv_qty>0", (grn_id,))
    cnt = int(cur.fetchone()[0] or 0)
    if cnt <= 0:
        return _bad("沒有任何實收數量(recv_qty)>0，不能過帳", 400)

    cur.execute(
        """
        update dbo.inv_grn
        set status='POSTED',
            posted_by=?,
            posted_at=getdate()
        where grn_id=?
        """,
        (user, grn_id),
    )
    conn.commit()
    return _ok(grn_id=grn_id, grn_no=grn_no)


@bp.post("/line/stock-move")
def stock_move_line():
    data = request.get_json(silent=True) or {}
    grn_line_id = data.get("grn_line_id")
    if not grn_line_id:
        return _bad("grn_line_id 必填")

    move_date = (data.get("move_date") or datetime.now().strftime("%Y-%m-%d")).strip()
    qty = data.get("qty")
    memo = (data.get("memo") or "").strip()

    try:
        qty = Decimal(str(qty))
    except Exception:
        return _bad("qty 格式錯誤")

    if qty <= 0:
        return _bad("qty 必須 > 0")

    user = _get_user()
    conn = get_db_conn()
    cur = conn.cursor()

    # 取 line + head + 必要欄位
    cur.execute(
        """
        select top 1
          gl.grn_line_id, gl.grn_id, gl.item_no, gl.po_qty, gl.recv_qty, gl.unit_price, gl.currency,
          g.grn_no, g.wh_id, g.po_no, g.po_form_no
        from dbo.inv_grn_line gl
        inner join dbo.inv_grn g on g.grn_id = gl.grn_id
        where gl.grn_line_id=?
        """,
        (grn_line_id,),
    )
    r = cur.fetchone()
    if not r:
        return _bad("找不到 grn_line", 404)

    (_grn_line_id, grn_id, item_no, po_qty, recv_qty, unit_price, currency,
     grn_no, wh_id, po_no, po_form_no) = r

    # ✅ 寫入庫存異動表（只是記錄異動，不代表真正入庫）
    cur.execute(
        """
        insert into dbo.inv_stock_move
          (move_date, move_type, wh_id, item_no, qty, currency, unit_price,
           source_type, source_no, source_id, source_line_id, po_no, po_form_no, memo, created_by)
        values
          (?, 'IN', ?, ?, ?, ?, ?,
           'GRN', ?, ?, ?, ?, ?, ?, ?)
        """,
        (move_date, wh_id, item_no, qty, currency, unit_price,
         grn_no, grn_id, grn_line_id, po_no, po_form_no, memo, user),
    )

    # ✅ 同步更新該行 recv_qty（讓列表的「進貨數量」變成你剛確認的 qty）
    cur.execute(
        "update dbo.inv_grn_line set recv_qty=? where grn_line_id=?",
        (qty, grn_line_id),
    )

    conn.commit()
    return _ok(move_id=True)
