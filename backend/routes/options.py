# routes/options.py
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("options_api", __name__, url_prefix="/api/options")

def get_db_conn():
    return current_app.config["GET_DB_CONN"]()

# --- 設定每個 key 對應的表與欄位 ---
CFG = {
    "Class2": {
        "table": "dbo.class2",
        "col":   "class2",
    },
    "items": {
        "table": "dbo.items_cf",
        "col":   "cateTxt",
    },
    "payment": {
        "table": "dbo.payment",
        "col":   "payment",
    },
    "material_no": {
        "table": "dbo.lab_material_option",
        "col":   "material_no",
        "ensure_sql": """
IF OBJECT_ID(N'dbo.lab_material_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_material_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        material_no nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
""",
    },
    "heat_no": {
        "table": "dbo.lab_heat_option",
        "col":   "heat_no",
        "ensure_sql": """
IF OBJECT_ID(N'dbo.lab_heat_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_heat_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        heat_no nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
""",
    }
}

def _cfg(key):
    return CFG.get(key)


def _ensure_table(cur, cfg):
    sql = (cfg or {}).get("ensure_sql")
    if not sql:
        return
    cur.execute(sql)

@bp.get("/<key>")
def list_options(key):
    c = _cfg(key)
    if not c:
        return jsonify(ok=False, msg="unknown key"), 400

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        _ensure_table(cur, c)
        sql = f"SELECT DISTINCT {c['col']} FROM {c['table']} WHERE {c['col']} IS NOT NULL ORDER BY {c['col']}"
        rows = cur.execute(sql).fetchall()
        data = [{"value": r[0], "label": r[0]} for r in rows if r and str(r[0]).strip() != ""]
        return jsonify(ok=True, data=data)
    finally:
        if conn:
            conn.close()

@bp.post("/<key>")
def create_option(key):
    c = _cfg(key)
    if not c:
        return jsonify(ok=False, msg="unknown key"), 400

    body = request.get_json(silent=True) or {}
    label = str(body.get("label", "")).strip()
    if not label:
        return jsonify(ok=False, msg="label required"), 400

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        _ensure_table(cur, c)

        # 防重複
        chk = cur.execute(
            f"SELECT COUNT(1) FROM {c['table']} WHERE {c['col']} = ?",
            (label,)
        ).fetchone()[0]
        if chk:
            return jsonify(ok=False, msg="已存在同名項目"), 409

        cur.execute(
            f"INSERT INTO {c['table']} ({c['col']}) VALUES (?)",
            (label,)
        )
        conn.commit()

        # ✅ 回傳給前端即時更新用
        return jsonify(ok=True, value=label, label=label)
    finally:
        if conn:
            conn.close()

@bp.put("/<key>")
def update_option(key):
    c = _cfg(key)
    if not c:
        return jsonify(ok=False, msg="unknown key"), 400

    body = request.get_json(silent=True) or {}
    value = str(body.get("value", "")).strip()
    label = str(body.get("label", "")).strip()
    if not value or not label:
        return jsonify(ok=False, msg="value/label required"), 400

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        _ensure_table(cur, c)

        # 若改名成已存在的名稱，也擋掉
        if value != label:
            chk = cur.execute(
                f"SELECT COUNT(1) FROM {c['table']} WHERE {c['col']} = ?",
                (label,)
            ).fetchone()[0]
            if chk:
                return jsonify(ok=False, msg="新名稱已存在"), 409

        cur.execute(
            f"UPDATE {c['table']} SET {c['col']} = ? WHERE {c['col']} = ?",
            (label, value)
        )
        if cur.rowcount == 0:
            return jsonify(ok=False, msg="找不到要修改的項目"), 404

        conn.commit()
        return jsonify(ok=True, value=value, label=label)
    finally:
        if conn:
            conn.close()

@bp.delete("/<key>/<path:value>")
def delete_option(key, value):
    c = _cfg(key)
    if not c:
        return jsonify(ok=False, msg="unknown key"), 400

    value = str(value or "").strip()
    if not value:
        return jsonify(ok=False, msg="value required"), 400

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        _ensure_table(cur, c)

        cur.execute(
            f"DELETE FROM {c['table']} WHERE {c['col']} = ?",
            (value,)
        )
        if cur.rowcount == 0:
            return jsonify(ok=False, msg="找不到要刪除的項目"), 404

        conn.commit()
        return jsonify(ok=True)
    finally:
        if conn:
            conn.close()
