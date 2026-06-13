# C:\ai_erp\backend\routes\form.py
import os, json
import pyodbc
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv

form_bp = Blueprint("form", __name__)

# --- contexts 讀取 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ...\backend
CONTEXT_DIR = os.path.join(BASE_DIR, "contexts")

def load_context(page: str) -> dict:
    fp = os.path.join(CONTEXT_DIR, f"{page}.json")
    if not os.path.exists(fp):
        raise FileNotFoundError(fp)
    with open(fp, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 支援 raw = {ok,data}, {data}, 或 ctx 本體
    if isinstance(raw, dict) and "ok" in raw and "data" in raw and isinstance(raw["data"], dict):
        return raw["data"]
    if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], dict) and "fields" in raw["data"]:
        return raw["data"]
    return raw

# --- DB (pyodbc) ---
def get_db_conn() -> pyodbc.Connection:
    load_dotenv()
    conn_str = (
        f"DRIVER={os.getenv('DB_DRIVER')};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_UID')};"
        f"PWD={os.getenv('DB_PWD')};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

def run_sql_options(query: str, params: dict | None = None):
    params = params or {}

    # 1) 把 :no1 轉成 pyodbc 的 ? 佔位符
    # 2) 依序收集參數值
    import re
    keys = re.findall(r":([A-Za-z_]\w*)", query)
    q2 = re.sub(r":[A-Za-z_]\w*", "?", query)

    values = []
    for k in keys:
        if k not in params:
            raise ValueError(f"missing param: {k}")
        values.append(params[k])

    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(q2, values)
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, r)) for r in rows]

# --- 找欄位定義：先找 fields，再找 category.levels ---
def _find_field_in_ctx(ctx: dict, key: str) -> dict | None:
    # fields
    for f in ctx.get("fields", []):
        if f.get("key") == key:
            return f

    # category.levels (你 no1/no2 在這裡)
    cat = ctx.get("category") or {}
    for lv in cat.get("levels", []):
        if lv.get("key") == key:
            return lv

    return None

@form_bp.get("/form/<page>/options", endpoint="form_get_options")
def get_options(page: str):
    try:
        key = request.args.get("key", "").strip()
        if not key:
            return jsonify({"ok": False, "msg": "missing key"}), 400

        ctx = load_context(page)
        field = _find_field_in_ctx(ctx, key)
        if not field:
            return jsonify({"ok": False, "msg": f"key not found: {key}"}), 404

        src = field.get("source")
        if not src or src.get("type") != "sql" or not src.get("query"):
            return jsonify({"ok": False, "msg": f"key not found or no source: {key}"}), 404

        q = src["query"]

        # querystring 參數全部帶進去，支援 :no1
        params = dict(request.args)
        params.pop("key", None)

        data = run_sql_options(q, params)
        return jsonify({"ok": True, "data": data})

    except Exception as e:
        return jsonify({"ok": False, "msg": f"options failed: {e}"}), 500
