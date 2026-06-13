# backend/routes/order.py
import re
from flask import Blueprint, request, jsonify
from utils.db import get_db_conn
from utils.safe import _safe_str, _to_int, _safe_sort_dir, _safe_date_ymd
from utils.fuzzy import fuzzy_like_patterns
from utils.include import fmt_date_ymd

order_bp = Blueprint("order", __name__)

# ✅ 快取表（API 查這個）
CACHE_TABLE = "dbo.ai_orders_cache"

# ✅ 來源 view（refresh 時用這個算）
SOURCE_VIEW = "dbo.ai_orders"

SORT_WHITELIST = {
    "company": "company",
    "pi_no": "pi_no",
    "c_order_no": "c_order_no",
    "form_no": "form_no",
    "original_date": "original_date",
    "currency": "currency",
    "amount": "amount",
    "sales_rep": "sales_rep",
    "company_title": "company_title",
}

DISPLAY_COLS = [
    "company",
    "pi_no",
    "c_order_no",
    "original_date",
    "currency",
    "amount",
    "sales_rep",
    "company_title",
    "form_no",
]

DEFAULT_SORT_BY = DISPLAY_COLS[0]
DEFAULT_SORT_DIR = "asc"

# ✅ 回傳欄位順序：依你前端要求
SELECT_COLS = ", ".join(DISPLAY_COLS)


# =========================
# Common helpers
# =========================
_RE_TAIL_WORDS = re.compile(
    r"(所有訂單|全部訂單|所有|全部|訂單|明細|資料|查詢|搜尋|"
    r"去年|今年|本月|這個月|上月|上個月|近30天|最近30天|三十天內|截至目前|截至今天|到目前為止|至今|"
    r"去$|今$)"
)

def _normalize_person_name(s: str) -> str:
    """
    把「業務高建明去年所有訂單」之類的輸入，清成較像人名的片段：
    - 去掉尾巴詞/時間詞
    - 去空白
    - 取 2~4 個中文字（台灣姓名常見）
    """
    s = (s or "").strip()
    if not s:
        return ""

    s = _RE_TAIL_WORDS.sub("", s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"(去|今)$", "", s)


    m = re.search(r"[\u4e00-\u9fff]{2,4}", s)
    return m.group(0) if m else s


def refresh_orders_cache(conn):
    """
    作法 B：雙表交換（無感刷新）
    - 用 applock 防止同時 refresh
    - 先 SELECT INTO new table
    - rename swap
    - drop old
    """
    cur = conn.cursor()
    sql = f"""
    SET NOCOUNT ON;

    DECLARE @lockResult int;
    EXEC @lockResult = sp_getapplock
        @Resource = 'ai_orders_cache_refresh',
        @LockMode = 'Exclusive',
        @LockOwner = 'Transaction',
        @LockTimeout = 10000;  -- 10 秒

    IF @lockResult < 0
    BEGIN
        RAISERROR('Cannot acquire refresh lock', 16, 1);
        RETURN;
    END

    BEGIN TRY
        BEGIN TRAN;

        DECLARE @new sysname = 'ai_orders_cache_new_' + REPLACE(CONVERT(varchar(36), NEWID()), '-', '');
        DECLARE @old sysname = 'ai_orders_cache_old_' + REPLACE(CONVERT(varchar(36), NEWID()), '-', '');

        -- 1) 先建立 new（用 SOURCE_VIEW 算）
        DECLARE @sql nvarchar(max) = N'
            SELECT
                company, pi_no, c_order_no, form_no, original_date, currency, amount, sales_rep, company_title
            INTO dbo.' + @new + N'
            FROM {SOURCE_VIEW} WITH (NOLOCK);
        ';
        EXEC sp_executesql @sql;

        -- 2) 建索引（非常重要）
        SET @sql = N'
            CREATE INDEX IX_' + @new + '_date ON dbo.' + @new + N'(original_date);
            CREATE INDEX IX_' + @new + '_pi   ON dbo.' + @new + N'(pi_no);
            CREATE INDEX IX_' + @new + '_co   ON dbo.' + @new + N'(company);
            CREATE INDEX IX_' + @new + '_rep  ON dbo.' + @new + N'(sales_rep);
            CREATE INDEX IX_' + @new + '_form ON dbo.' + @new + N'(form_no);
        ';
        EXEC sp_executesql @sql;

        -- 3) swap：把現有 cache 先改名成 old（若不存在就略過）
        IF OBJECT_ID('{CACHE_TABLE}', 'U') IS NOT NULL
        BEGIN
            EXEC sp_rename '{CACHE_TABLE}', @old;
        END

        -- 4) 把 new 改成正式 cache 名稱
        EXEC sp_rename ('dbo.' + @new), 'ai_orders_cache';

        -- 5) drop old
        IF OBJECT_ID('dbo.' + @old, 'U') IS NOT NULL
        BEGIN
            SET @sql = N'DROP TABLE dbo.' + @old + N';';
            EXEC sp_executesql @sql;
        END

        COMMIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        DECLARE @msg nvarchar(4000) = ERROR_MESSAGE();
        RAISERROR(@msg, 16, 1);
    END CATCH
    """
    cur.execute(sql)


@order_bp.post("/order/cache/refresh")
def api_refresh_cache():
    """
    手動刷新快取（建議只給內部/管理者使用）
    POST /api/order/cache/refresh
    """
    conn = None
    try:
        conn = get_db_conn()
        conn.autocommit = True
        refresh_orders_cache(conn)
        return jsonify({"ok": True, "msg": "cache refreshed"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except:
            pass


@order_bp.get("/order/list")
def list_orders():
    """
    GET /api/order/list?kw=&company=&date_from=&date_to=&sales_rep=&company_title=&page=1&pageSize=20
        &sortBy=company&sortDir=asc
    """
    conn = None
    try:
        kw = _safe_str(request.args.get("kw"), 200)
        company = _safe_str(request.args.get("company"), 100)
        sales_rep = _safe_str(request.args.get("sales_rep"), 50)
        company_title = _safe_str(request.args.get("company_title"), 100)
        date_from = _safe_date_ymd(request.args.get("date_from"))
        date_to = _safe_date_ymd(request.args.get("date_to"))

        # ✅ 修正：把「高建明去」「高見明所有訂單」等清為較像人名的字串
        sales_rep = _normalize_person_name(sales_rep)

        page = _to_int(request.args.get("page"), 1) or 1
        pageSize = _to_int(request.args.get("pageSize"), 20) or 20
        page = max(1, page)
        pageSize = min(max(1, pageSize), 200)

        # ✅ sortBy 缺省 → 預設（第1欄）
        req_sortBy = _safe_str(request.args.get("sortBy"), 50) or DEFAULT_SORT_BY
        # ✅ sortDir 缺省 → 預設 asc
        req_sortDir = _safe_sort_dir(request.args.get("sortDir")) or DEFAULT_SORT_DIR

        # ✅ 不是每個欄位都能排序：不在白名單就回到預設欄位
        sortBy = req_sortBy if req_sortBy in SORT_WHITELIST else DEFAULT_SORT_BY
        sortDir = req_sortDir
        order_col = SORT_WHITELIST[sortBy]

        # ✅ 抽成函數：可以重跑（exact / fuzzy）
        def _build_where_params(sales_rep_mode: str):
            where = []
            params = []

            if kw:
                like = f"%{kw}%"
                where.append(
                    "(company LIKE ? OR pi_no LIKE ? OR c_order_no LIKE ? OR company_title LIKE ? OR sales_rep LIKE ?)"
                )
                params += [like, like, like, like, like]

            if company:
                where.append("company LIKE ?")
                params.append(f"%{company}%")

            if sales_rep:
                if sales_rep_mode == "exact":
                    where.append("sales_rep LIKE ?")
                    params.append(f"%{sales_rep}%")
                else:
                    pats = fuzzy_like_patterns(
                        sales_rep,
                        max_patterns=8,
                        include_single_chars=True
                    )
                    # pats 可能為空（例如只剩空白），就退回 exact
                    if not pats:
                        where.append("sales_rep LIKE ?")
                        params.append(f"%{sales_rep}%")
                    else:
                        where.append("(" + " OR ".join(["sales_rep LIKE ?"] * len(pats)) + ")")
                        params += pats

            if company_title:
                where.append("company_title LIKE ?")
                params.append(f"%{company_title}%")

            if date_from:
                where.append("original_date >= ?")
                params.append(date_from)

            if date_to:
                where.append("original_date <= ?")
                params.append(date_to)

            where_sql = (" WHERE " + " AND ".join(where)) if where else ""
            return where_sql, params

        conn = get_db_conn()
        cur = conn.cursor()

        # ✅ 先精準查
        where_sql, params = _build_where_params("exact")
        sql_total = f"SELECT COUNT(1) FROM {CACHE_TABLE}{where_sql}"
        cur.execute(sql_total, params)
        total = int(cur.fetchone()[0] or 0)

        # ✅ 精準查不到才嘗試 fuzzy；只有 fuzzy 有結果才切換（避免更差）
        used_fuzzy = False
        if total == 0 and sales_rep:
            where_sql2, params2 = _build_where_params("fuzzy")
            sql_total2 = f"SELECT COUNT(1) FROM {CACHE_TABLE}{where_sql2}"
            cur.execute(sql_total2, params2)
            total2 = int(cur.fetchone()[0] or 0)

            if total2 > 0:
                where_sql, params, total = where_sql2, params2, total2
                used_fuzzy = True

        # ✅✅✅ 穩定排序（避免翻頁漂移）
        tie_cols = ["pi_no", "form_no", "c_order_no"]
        tie_cols = [c for c in tie_cols if c != order_col]
        stable_order = ", ".join([f"{order_col} {sortDir}"] + [f"{c} {sortDir}" for c in tie_cols])

        offset = (page - 1) * pageSize

        sql_page = f"""
        SELECT {SELECT_COLS}
        FROM {CACHE_TABLE}
        {where_sql}
        ORDER BY {stable_order}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        page_params = list(params) + [offset, pageSize]
        cur.execute(sql_page, page_params)

        # ✅ 先取得欄位
        cols = [d[0] for d in cur.description]
        rows = []
        for r in cur.fetchall():
            row = dict(zip(cols, r))
            row["original_date"] = fmt_date_ymd(row.get("original_date"))
            rows.append(row)

        return jsonify({
            "ok": True,
            "data": {
                "rows": rows,
                "total": total,
                "page": page,
                "pageSize": pageSize,
                "sortBy": sortBy,
                "sortDir": sortDir,
                "usedFuzzy": used_fuzzy,
            }
        })

    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except:
            pass
