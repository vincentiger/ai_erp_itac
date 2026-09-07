from __future__ import annotations

import os
import shutil
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from utils.lab_export_signature import validate_export_signature

try:
    from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
except Exception:  # pragma: no cover
    def jwt_required():
        def _wrap(fn):
            return fn

        return _wrap

    def get_jwt():
        return {}

    def get_jwt_identity():
        return None

try:
    jwt_required  # type: ignore[name-defined]
except NameError:  # pragma: no cover
    def jwt_required(*args, **kwargs):
        def _wrap(fn):
            return fn

        return _wrap


def jwt_required(*args, **kwargs):  # type: ignore[no-redef]
    def _wrap(fn):
        return fn

    return _wrap


bp = Blueprint("lab_workflow", __name__)

PIC_ROOT = r"C:\inetpub\wwwroot\newweb2021\pic\itac"

STATUS_OPTIONS = [
    {"value": "TEMP", "label": "臨時", "order": 1},
    {"value": "RECEIVED_LOGO", "label": "收到樣品/確認/有logo", "order": 2},
    {"value": "RECEIVED_NOLOGO", "label": "收到樣品/確認/無logo", "order": 3},
    {"value": "REVIEW_DONE", "label": "主管審核完成", "order": 4},
]


def _now_ymd() -> str:
    return datetime.now().strftime("%Y%m%d")


def _now_ym() -> str:
    return datetime.now().strftime("%Y%m")


def _safe_str(value, default=""):
    text = default if value is None else str(value).strip()
    return text


def _get_conn():
    return current_app.config["GET_DB_CONN"]()


def _ensure_workflow_columns(conn) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        IF OBJECT_ID(N'dbo.lab_workflow_state', N'U') IS NULL
        BEGIN
            CREATE TABLE dbo.lab_workflow_state (
                form_id NVARCHAR(36) NOT NULL PRIMARY KEY,
                workflow_status NVARCHAR(30) NOT NULL
                    CONSTRAINT DF_lab_workflow_state_status DEFAULT(N'TEMP'),
                workflow_has_logo BIT NOT NULL
                    CONSTRAINT DF_lab_workflow_state_has_logo DEFAULT(0),
                workflow_confirmed_by NVARCHAR(100) NULL,
                workflow_confirmed_at DATETIME NULL,
                workflow_reviewed_by NVARCHAR(100) NULL,
                workflow_reviewed_at DATETIME NULL,
                workflow_signature_file NVARCHAR(255) NULL,
                workflow_signature_date DATE NULL,
                workflow_temp_no NVARCHAR(30) NULL,
                workflow_formal_no NVARCHAR(30) NULL,
                workflow_report_no NVARCHAR(30) NULL,
                created_at DATETIME NOT NULL CONSTRAINT DF_lab_workflow_state_created_at DEFAULT(GETDATE()),
                updated_at DATETIME NOT NULL CONSTRAINT DF_lab_workflow_state_updated_at DEFAULT(GETDATE())
            );
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_status') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_status NVARCHAR(30) NOT NULL
                CONSTRAINT DF_lab_workflow_state_status DEFAULT(N'TEMP');
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_has_logo') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_has_logo BIT NOT NULL
                CONSTRAINT DF_lab_workflow_state_has_logo DEFAULT(0);
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_confirmed_by') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_confirmed_by NVARCHAR(100) NULL;
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_confirmed_at') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_confirmed_at DATETIME NULL;
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_reviewed_by') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_reviewed_by NVARCHAR(100) NULL;
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_reviewed_at') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_reviewed_at DATETIME NULL;
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_signature_file') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_signature_file NVARCHAR(255) NULL;
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_signature_date') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_signature_date DATE NULL;
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_temp_no') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_temp_no NVARCHAR(30) NULL;
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_formal_no') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_formal_no NVARCHAR(30) NULL;
        END

        IF COL_LENGTH('dbo.lab_workflow_state', 'workflow_report_no') IS NULL
        BEGIN
            ALTER TABLE dbo.lab_workflow_state
            ADD workflow_report_no NVARCHAR(30) NULL;
        END
        """
    )


def _attachments_dir(form_id: str) -> str:
    base = os.path.join(current_app.root_path, "..", "uploads", "lab_attachments")
    return os.path.abspath(os.path.join(base, form_id))


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _attachment_rows(form_id: str):
    folder = _attachments_dir(form_id)
    if not os.path.isdir(folder):
        return []
    rows = []
    for name in sorted(os.listdir(folder)):
        file_path = os.path.join(folder, name)
        if not os.path.isfile(file_path):
            continue
        rows.append(
            {
                "name": name,
                "url": f"/ai/api/lab/instances/{form_id}/attachments/{name}",
                "size": os.path.getsize(file_path),
                "mtime": os.path.getmtime(file_path),
            }
        )
    return rows


def _current_account() -> str:
    account = _safe_str(request.headers.get("X-User-Account"))
    if account:
        return account
    try:
        claims = get_jwt() or {}
    except Exception:
        claims = {}
    account = _safe_str(claims.get("account"))
    if account:
        return account
    try:
        identity = get_jwt_identity()
    except Exception:
        identity = None
    return _safe_str(identity)


def _is_manager() -> bool:
    account = _current_account()
    if not account:
        return False
    conn = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1
                   ISNULL(authority, ''),
                   ISNULL(dep_manager, 0)
            FROM dbo.staff
            WHERE LTRIM(RTRIM(ISNULL(eid, ''))) = ?
            """,
            (account,),
        )
        row = cur.fetchone()
        if not row:
            return False
        authority = _safe_str(row[0])
        dep_manager = str(row[1] or "").strip() in {"1", "true", "True"}
        return authority in {"12", "90", "99"} or dep_manager
    except Exception:
        return False
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def _next_running_no(cursor, code_key: str, ymd: str) -> int:
    cursor.execute(
        """
        SELECT current_no
        FROM dbo.lab_running_no WITH (UPDLOCK, HOLDLOCK)
        WHERE code_key = ? AND ymd = ?
        """,
        (code_key, ymd),
    )
    row = cursor.fetchone()
    if row:
        current_no = int(row[0] or 0) + 1
        cursor.execute(
            """
            UPDATE dbo.lab_running_no
               SET current_no = ?
             WHERE code_key = ? AND ymd = ?
            """,
            (current_no, code_key, ymd),
        )
        return current_no

    cursor.execute("DELETE FROM dbo.lab_running_no WHERE code_key = ?", (code_key,))
    cursor.execute(
        """
        INSERT INTO dbo.lab_running_no(code_key, ymd, current_no)
        VALUES (?, ?, 1)
        """,
        (code_key, ymd),
    )
    return 1


def _format_no(prefix: str, ymd: str, seq: int) -> str:
    return f"{prefix}{ymd}-{seq:03d}"


@bp.get("/workflow/status-options")
@jwt_required()
def status_options():
    return jsonify(
        {
            "ok": True,
            "data": {
                "options": STATUS_OPTIONS if _is_manager() else STATUS_OPTIONS[:1],
                "can_see_full_list": _is_manager(),
            },
        }
    )


@bp.get("/workflow/form-status")
@bp.get("/form-status")
@jwt_required()
def get_form_status():
    form_id = _safe_str(request.args.get("form_id"))
    if not form_id:
        return jsonify({"ok": False, "msg": "form_id required"}), 400

    conn = None
    try:
        conn = _get_conn()
        _ensure_workflow_columns(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1 ISNULL(workflow_status, 'TEMP') AS status
            FROM dbo.lab_workflow_state
            WHERE CONVERT(varchar(36), form_id) = ?
            """,
            (form_id,),
        )
        row = cur.fetchone()
        status = _safe_str(row[0]) if row else "TEMP"
        if status not in {opt["value"] for opt in STATUS_OPTIONS}:
            status = "TEMP"
        return jsonify({"ok": True, "data": {"form_id": form_id, "status": status}})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.get("/workflow/current-signature")
@jwt_required()
def current_signature():
    # Always use the department manager's signature, not the exporting account.

    conn = None
    try:
        conn = _get_conn()
        _ensure_workflow_columns(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1
                   ISNULL(sign_e, sign_c) AS signature,
                   sign_c,
                   sign_e
            FROM dbo.staff
            WHERE ISNULL(dep_manager, 0) = 1
            ORDER BY id
            """,
        )
        row = cur.fetchone()
        signature = ""
        if row:
            candidates = [_safe_str(row[0]), _safe_str(row[1]), _safe_str(row[2])]
            for candidate in candidates:
                if not candidate:
                    continue
                clean_candidate = candidate.split("?", 1)[0].split("#", 1)[0]
                filename = os.path.basename(clean_candidate)
                resolved = clean_candidate if os.path.isabs(clean_candidate) else os.path.join(PIC_ROOT, filename)
                if os.path.isfile(resolved):
                    signature = clean_candidate
                    break
            if not signature:
                signature = next((candidate for candidate in candidates if candidate), "")
        if not signature:
            return jsonify({"ok": True, "data": {"signature": "", "filename": "", "path": ""}})

        signature = signature.split("?", 1)[0].split("#", 1)[0]
        filename = os.path.basename(signature)
        resolved = signature
        if not os.path.isabs(resolved):
            resolved = os.path.join(PIC_ROOT, filename)

        return jsonify(
            {
                "ok": True,
                "data": {
                    "signature": signature,
                    "account": "dep_manager=1",
                    "filename": filename,
                    "path": resolved,
                    "public_path": f"/pic/itac/{filename}",
                },
            }
        )
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.get("/workflow/signature-check/<form_id>")
@jwt_required()
def signature_check(form_id):
    """Preflight the fixed supervisor signature before Word export."""
    try:
        result = validate_export_signature(_safe_str(form_id), "manager")
        return jsonify({"ok": True, "data": result})
    except FileNotFoundError as exc:
        return jsonify({"ok": False, "code": "MANAGER_SIGNATURE_MISSING", "msg": str(exc)}), 409
    except Exception as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 500


@bp.route("/workflow/form-status", methods=["POST"])
@bp.route("/form-status", methods=["POST"])
@jwt_required()
def update_form_status():
    body = request.get_json(silent=True) or {}
    form_id = _safe_str(body.get("form_id"))
    status = _safe_str(body.get("status"))
    has_logo = bool(body.get("has_logo"))
    if not form_id:
        return jsonify({"ok": False, "msg": "form_id required"}), 400
    if status not in {opt["value"] for opt in STATUS_OPTIONS}:
        return jsonify({"ok": False, "msg": "invalid status"}), 400

    conn = None
    try:
        conn = _get_conn()
        _ensure_workflow_columns(conn)
        conn.autocommit = False
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP 1
                   ISNULL(workflow_status, 'TEMP') AS workflow_status,
                   ISNULL(workflow_has_logo, 0) AS workflow_has_logo,
                   ISNULL(workflow_formal_no, '') AS workflow_formal_no,
                   ISNULL(workflow_report_no, '') AS workflow_report_no
            FROM dbo.lab_workflow_state
            WHERE CONVERT(varchar(36), form_id) = ?
            """,
            (form_id,),
        )
        row = cur.fetchone()
        current_status = _safe_str(row[0]) if row else "TEMP"
        current_has_logo = bool(row[1]) if row else False
        current_formal_no = _safe_str(row[2]) if row else ""
        current_report_no = _safe_str(row[3]) if row else ""

        if current_status in {"RECEIVED_LOGO", "RECEIVED_NOLOGO", "REVIEW_DONE"} and status == "TEMP":
            conn.rollback()
            return jsonify({"ok": False, "msg": "正式委託單不可回復為臨時"}), 400
        if current_status == "REVIEW_DONE" and status != "REVIEW_DONE":
            conn.rollback()
            return jsonify({"ok": False, "msg": "已主管審核完成，不可再變更狀態"}), 400

        if current_status == "TEMP" and status in {"RECEIVED_LOGO", "RECEIVED_NOLOGO"}:
            has_logo = status == "RECEIVED_LOGO"
        elif current_status in {"RECEIVED_LOGO", "RECEIVED_NOLOGO"} and status in {"RECEIVED_LOGO", "RECEIVED_NOLOGO"}:
            has_logo = status == "RECEIVED_LOGO"
        else:
            has_logo = current_has_logo

        cur.execute(
            """
            UPDATE dbo.lab_workflow_state
               SET workflow_status = ?,
                   workflow_has_logo = ?,
                   updated_at = GETDATE()
             WHERE CONVERT(varchar(36), form_id) = ?
            """,
            (status, 1 if has_logo else 0, form_id),
        )
        if cur.rowcount <= 0:
            cur.execute(
                """
                SELECT TOP 1 1
                FROM dbo.lab_workflow_state
                WHERE CONVERT(varchar(36), form_id) = ?
                """,
                (form_id,),
            )
            if cur.fetchone() is None:
                cur.execute(
                    """
                    INSERT INTO dbo.lab_workflow_state(
                        form_id, workflow_status, workflow_has_logo, created_at, updated_at
                    )
                    VALUES (?, ?, ?, GETDATE(), GETDATE())
                    """,
                    (form_id, status, 1 if has_logo else 0),
                )
        if status in {"RECEIVED_LOGO", "RECEIVED_NOLOGO"} and not current_formal_no:
            formal_key = "LAB_FORMAL_LOGO" if has_logo else "LAB_FORMAL_NOLOGO"
            formal_period = _now_ymd()
            seq = _next_running_no(cur, formal_key, formal_period)
            formal_no = _format_no("" if has_logo else "A", formal_period, seq)
            cur.execute(
                """
                UPDATE dbo.lab_workflow_state
                   SET workflow_formal_no = ?,
                       workflow_confirmed_by = ISNULL(workflow_confirmed_by, ?),
                       workflow_confirmed_at = ISNULL(workflow_confirmed_at, GETDATE())
                 WHERE CONVERT(varchar(36), form_id) = ?
                """,
                (formal_no, _current_account(), form_id),
            )
        if status == "RECEIVED_LOGO":
            cur.execute(
                """
                UPDATE dbo.lab_workflow_state
                   SET workflow_confirmed_at = GETDATE()
                 WHERE CONVERT(varchar(36), form_id) = ?
                """,
                (form_id,),
            )
        elif status == "RECEIVED_NOLOGO":
            cur.execute(
                """
                UPDATE dbo.lab_workflow_state
                   SET workflow_confirmed_at = GETDATE()
                 WHERE CONVERT(varchar(36), form_id) = ?
                """,
                (form_id,),
            )
        elif status == "REVIEW_DONE":
            cur.execute(
                """
                SELECT TOP 1 ISNULL(sign_e, sign_c) AS signature
                  FROM dbo.staff
                 WHERE ISNULL(dep_manager, 0) = 1
                 ORDER BY id
                """
            )
            manager_row = cur.fetchone()
            manager_signature = os.path.basename(
                _safe_str(manager_row[0]).split("?", 1)[0].split("#", 1)[0].replace("\\", "/")
            ) if manager_row else ""
            if not current_report_no:
                report_key = "LAB_REPORT_LOGO" if has_logo else "LAB_REPORT_NOLOGO"
                report_period = _now_ym() if has_logo else _now_ymd()
                seq = _next_running_no(cur, report_key, report_period)
                report_no = _format_no("" if has_logo else "R", report_period, seq)
                cur.execute(
                    """
                    UPDATE dbo.lab_workflow_state
                       SET workflow_report_no = ?,
                           workflow_reviewed_by = ISNULL(workflow_reviewed_by, ?),
                           workflow_reviewed_at = ISNULL(workflow_reviewed_at, GETDATE())
                     WHERE CONVERT(varchar(36), form_id) = ?
                    """,
                    (report_no, _current_account(), form_id),
                )
            cur.execute(
                """
                UPDATE dbo.lab_workflow_state
                   SET workflow_reviewed_at = GETDATE(),
                       workflow_signature_file = ISNULL(workflow_signature_file, ?),
                       workflow_signature_date = ISNULL(workflow_signature_date, CONVERT(date, GETDATE()))
                 WHERE CONVERT(varchar(36), form_id) = ?
                """,
                (manager_signature or None, form_id),
            )
        conn.commit()
        return jsonify({"ok": True, "data": {"form_id": form_id, "status": status, "has_logo": has_logo}})
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.post("/workflow/next-no")
@jwt_required()
def next_no():
    body = request.get_json(silent=True) or {}
    kind = _safe_str(body.get("kind")).lower()
    has_logo = bool(body.get("has_logo"))
    if kind not in {"temp", "formal", "report"}:
        return jsonify({"ok": False, "msg": "invalid kind"}), 400

    ymd = _now_ymd()
    ym = _now_ym()
    conn = None
    try:
        conn = _get_conn()
        _ensure_workflow_columns(conn)
        conn.autocommit = False
        cur = conn.cursor()

        if kind == "temp":
            seq = _next_running_no(cur, "LAB_TEMP", ymd)
            no = _format_no("T", ymd, seq)
        elif kind == "formal":
            key = "LAB_FORMAL_LOGO" if has_logo else "LAB_FORMAL_NOLOGO"
            seq = _next_running_no(cur, key, ymd)
            no = _format_no("" if has_logo else "A", ymd, seq)
        else:
            key = "LAB_REPORT_LOGO" if has_logo else "LAB_REPORT_NOLOGO"
            seq = _next_running_no(cur, key, ym)
            no = _format_no("" if has_logo else "R", ym, seq)

        conn.commit()
        return jsonify(
            {
                "ok": True,
                "data": {
                    "kind": kind,
                    "has_logo": has_logo,
                    "no": no,
                    "sequence": seq,
                    "period": ym if kind == "report" else ymd,
                },
            }
        )
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.get("/next-lab-no")
@jwt_required()
def legacy_next_lab_no():
    """Compatibility endpoint for existing frontend bundle."""
    filled_date = _safe_str(request.args.get("filled_date"))
    if not filled_date:
        filled_date = _now_ymd()

    conn = None
    try:
        conn = _get_conn()
        _ensure_workflow_columns(conn)
        conn.autocommit = False
        cur = conn.cursor()
        seq = _next_running_no(cur, "LAB_TEMP", filled_date.replace("-", ""))
        lab_no = _format_no("T", filled_date.replace("-", ""), seq)
        conn.commit()
        return jsonify({"ok": True, "lab_no": lab_no, "sequence": seq})
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def _legacy_shared_option_config(key):
    specs = {
        "material_no": ("dbo.lab_material_option", "material_no", 100),
        "heat_no": ("dbo.lab_heat_option", "heat_no", 100),
        "plating_cate": ("dbo.lab_plating_cate_option", "plating_cate", 100),
        "plating_fac": ("dbo.lab_plating_fac_option", "plating_fac", 100),
        "rule_spec": ("dbo.lab_rule_spec_option", "rule_spec", 200),
    }
    spec = specs.get(key)
    if not spec:
        return None
    table, col, length = spec
    ensure_sql = f"""
IF OBJECT_ID(N'{table}', N'U') IS NULL
BEGIN
    CREATE TABLE {table} (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        {col} nvarchar({length}) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""
    return table, col, ensure_sql


@bp.get("/shared-options/<key>")
@jwt_required()
def legacy_shared_options(key):
    key = _safe_str(key)
    config = _legacy_shared_option_config(key)
    if not config:
        return jsonify({"ok": False, "msg": "invalid key"}), 400

    table, col, ensure_sql = config
    conn = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(ensure_sql)
        rows = cur.execute(
            f"""
SELECT DISTINCT {col}
  FROM {table}
 WHERE {col} IS NOT NULL
   AND LTRIM(RTRIM({col})) <> ''
 ORDER BY {col}
"""
        ).fetchall()
        conn.commit()
        data = [
            {"value": str(row[0]).strip(), "label": str(row[0]).strip()}
            for row in rows
            if row and str(row[0]).strip()
        ]
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.post("/shared-options/<key>")
@jwt_required()
def legacy_shared_options_add(key):
    key = _safe_str(key)
    if key not in {"material_no", "heat_no", "plating_cate", "plating_fac", "rule_spec"}:
        return jsonify({"ok": False, "msg": "invalid key"}), 400
    body = request.get_json(silent=True) or {}
    label = _safe_str(body.get("label"))
    if not label:
        return jsonify({"ok": False, "msg": "label required"}), 400

    cfg = {
        "material_no": ("dbo.lab_material_option", "material_no", """
IF OBJECT_ID(N'dbo.lab_material_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_material_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        material_no nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
        "heat_no": ("dbo.lab_heat_option", "heat_no", """
IF OBJECT_ID(N'dbo.lab_heat_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_heat_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        heat_no nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
        "plating_cate": ("dbo.lab_plating_cate_option", "plating_cate", """
IF OBJECT_ID(N'dbo.lab_plating_cate_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_plating_cate_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        plating_cate nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
        "plating_fac": ("dbo.lab_plating_fac_option", "plating_fac", """
IF OBJECT_ID(N'dbo.lab_plating_fac_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_plating_fac_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        plating_fac nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
        "rule_spec": ("dbo.lab_rule_spec_option", "rule_spec", """
IF OBJECT_ID(N'dbo.lab_rule_spec_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_rule_spec_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        rule_spec nvarchar(200) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
    }
    table, col, ensure_sql = cfg[key]
    conn = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(ensure_sql)
        cur.execute(f"SELECT COUNT(1) FROM {table} WHERE {col} = ?", (label,))
        if int(cur.fetchone()[0] or 0):
            return jsonify(
                {
                    "ok": True,
                    "value": label,
                    "label": label,
                    "already_exists": True,
                }
            )
        cur.execute(f"INSERT INTO {table} ({col}) VALUES (?)", (label,))
        conn.commit()
        return jsonify({"ok": True, "value": label, "label": label})
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.put("/shared-options/<key>")
@jwt_required()
def legacy_shared_options_update(key):
    key = _safe_str(key)
    if key not in {"material_no", "heat_no", "plating_cate", "plating_fac", "rule_spec"}:
        return jsonify({"ok": False, "msg": "invalid key"}), 400
    body = request.get_json(silent=True) or {}
    value = _safe_str(body.get("value"))
    label = _safe_str(body.get("label"))
    if not value or not label:
        return jsonify({"ok": False, "msg": "value/label required"}), 400

    cfg = {
        "material_no": ("dbo.lab_material_option", "material_no", """
IF OBJECT_ID(N'dbo.lab_material_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_material_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        material_no nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
        "heat_no": ("dbo.lab_heat_option", "heat_no", """
IF OBJECT_ID(N'dbo.lab_heat_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_heat_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        heat_no nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
        "plating_cate": ("dbo.lab_plating_cate_option", "plating_cate", """
IF OBJECT_ID(N'dbo.lab_plating_cate_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_plating_cate_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        plating_cate nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
        "plating_fac": ("dbo.lab_plating_fac_option", "plating_fac", """
IF OBJECT_ID(N'dbo.lab_plating_fac_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_plating_fac_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        plating_fac nvarchar(100) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
        "rule_spec": ("dbo.lab_rule_spec_option", "rule_spec", """
IF OBJECT_ID(N'dbo.lab_rule_spec_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_rule_spec_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        rule_spec nvarchar(200) NOT NULL,
        created_at datetime NOT NULL DEFAULT GETDATE()
    )
END
"""),
    }
    table, col, ensure_sql = cfg[key]
    conn = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(ensure_sql)
        if value != label:
            cur.execute(f"SELECT COUNT(1) FROM {table} WHERE {col} = ?", (label,))
            if int(cur.fetchone()[0] or 0):
                return jsonify({"ok": False, "msg": "已存在同名項目"}), 409
        cur.execute(f"UPDATE {table} SET {col} = ? WHERE {col} = ?", (label, value))
        if cur.rowcount <= 0:
            return jsonify({"ok": False, "msg": "item not found"}), 404
        conn.commit()
        return jsonify({"ok": True, "value": label, "label": label})
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.get("/test-config")
@jwt_required()
def legacy_test_config():
    category_defs = [
        ("dimension", "尺寸精度"),
        ("mechanical", "機械性能"),
        ("functional", "功能測試"),
        ("surface", "表面處理"),
        ("other", "其他"),
    ]
    conn = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT i.id,
                   i.cate_key,
                   i.item_name,
                   ISNULL(i.sort_no, 0) AS item_sort,
                   m.method_text,
                   ISNULL(m.sort_no, 0) AS method_sort
            FROM dbo.lab_test_item i
            LEFT JOIN dbo.lab_test_method m ON m.item_id = i.id
            ORDER BY CASE i.cate_key
                       WHEN N'dimension' THEN 1
                       WHEN N'mechanical' THEN 2
                       WHEN N'functional' THEN 3
                       WHEN N'surface' THEN 4
                       WHEN N'other' THEN 5
                       ELSE 99
                     END,
                     ISNULL(i.sort_no, 0), i.id,
                     ISNULL(m.sort_no, 0), m.id
            """
        )

        items_by_category = {key: {} for key, _ in category_defs}
        for row in cur.fetchall():
            item_id = int(row[0])
            cate_key = _safe_str(row[1])
            if cate_key not in items_by_category:
                continue
            item = items_by_category[cate_key].setdefault(
                item_id,
                {
                    "item_id": item_id,
                    "name": _safe_str(row[2]),
                    "sort_no": int(row[3] or 0),
                    "methods": [],
                },
            )
            method = _safe_str(row[4])
            if method and method not in item["methods"]:
                item["methods"].append(method)

        categories = []
        for key, label in category_defs:
            items = list(items_by_category[key].values())
            for item in items:
                item["methods_text"] = "\n".join(item["methods"])
            categories.append({"key": key, "label": label, "items": items})
        return jsonify({"ok": True, "categories": categories})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.put("/test-config/methods")
@jwt_required()
def legacy_test_config_methods():
    body = request.get_json(silent=True) or {}
    items = body.get("items")
    if not isinstance(items, list) or not items:
        return jsonify({"ok": False, "msg": "items required"}), 400

    conn = None
    try:
        conn = _get_conn()
        conn.autocommit = False
        cur = conn.cursor()
        updated = 0
        for payload in items:
            if not isinstance(payload, dict):
                continue
            try:
                item_id = int(payload.get("item_id"))
            except (TypeError, ValueError):
                continue
            methods = []
            for line in _safe_str(payload.get("methods_text")).replace("\r", "").split("\n"):
                method = line.strip()
                if method and method not in methods:
                    methods.append(method)

            cur.execute("SELECT TOP 1 1 FROM dbo.lab_test_item WHERE id = ?", (item_id,))
            if cur.fetchone() is None:
                continue
            cur.execute("DELETE FROM dbo.lab_test_method WHERE item_id = ?", (item_id,))
            for index, method in enumerate(methods, start=1):
                cur.execute(
                    "INSERT INTO dbo.lab_test_method(item_id, method_text, sort_no) VALUES (?, ?, ?)",
                    (item_id, method, index * 10),
                )
            updated += 1
        if updated <= 0:
            conn.rollback()
            return jsonify({"ok": False, "msg": "no valid test items"}), 400
        conn.commit()
        return jsonify({"ok": True, "updated": updated})
    except Exception as e:
        try:
            if conn:
                conn.rollback()
        except Exception:
            pass
        return jsonify({"ok": False, "msg": str(e)}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


@bp.get("/instances/<form_id>/attachments")
@bp.get("/lab/instances/<form_id>/attachments")
@bp.get("/api/lab/instances/<form_id>/attachments")
@bp.get("/ai/api/lab/instances/<form_id>/attachments")
def list_attachments(form_id):
    form_id = _safe_str(form_id)
    if not form_id:
        return jsonify({"ok": False, "msg": "form_id required"}), 400
    return jsonify({"ok": True, "files": _attachment_rows(form_id)})


@bp.post("/instances/<form_id>/attachments")
@bp.post("/lab/instances/<form_id>/attachments")
@bp.post("/api/lab/instances/<form_id>/attachments")
@bp.post("/ai/api/lab/instances/<form_id>/attachments")
def upload_attachment(form_id):
    form_id = _safe_str(form_id)
    if not form_id:
        return jsonify({"ok": False, "msg": "form_id required"}), 400
    file_obj = request.files.get("file")
    if not file_obj or not file_obj.filename:
        return jsonify({"ok": False, "msg": "file required"}), 400

    folder = _attachments_dir(form_id)
    _ensure_dir(folder)
    filename = secure_filename(file_obj.filename)
    if not filename:
        return jsonify({"ok": False, "msg": "invalid filename"}), 400

    target = os.path.join(folder, filename)
    file_obj.save(target)
    return jsonify(
        {
            "ok": True,
            "file": {
                "name": filename,
                "size": os.path.getsize(target),
                "url": f"/ai/api/lab/instances/{form_id}/attachments/{filename}",
            },
        }
    )


@bp.get("/instances/<form_id>/attachments/<path:filename>")
@bp.get("/lab/instances/<form_id>/attachments/<path:filename>")
@bp.get("/api/lab/instances/<form_id>/attachments/<path:filename>")
@bp.get("/ai/api/lab/instances/<form_id>/attachments/<path:filename>")
def download_attachment(form_id, filename):
    form_id = _safe_str(form_id)
    filename = _safe_str(filename)
    folder = _attachments_dir(form_id)
    if not os.path.isfile(os.path.join(folder, filename)):
        return jsonify({"ok": False, "msg": "file not found"}), 404
    return send_from_directory(folder, filename, as_attachment=False)


@bp.delete("/instances/<form_id>/attachments/<path:filename>")
@bp.delete("/lab/instances/<form_id>/attachments/<path:filename>")
@bp.delete("/api/lab/instances/<form_id>/attachments/<path:filename>")
@bp.delete("/ai/api/lab/instances/<form_id>/attachments/<path:filename>")
def delete_attachment(form_id, filename):
    form_id = _safe_str(form_id)
    filename = _safe_str(filename)
    path = os.path.join(_attachments_dir(form_id), filename)
    if not os.path.isfile(path):
        return jsonify({"ok": False, "msg": "file not found"}), 404
    os.remove(path)
    return jsonify({"ok": True})
