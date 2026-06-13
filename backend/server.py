# C:\ai_erp\backend\server.py
import os
from dotenv import load_dotenv
from path_config import LOG_DIR

# ✅ ENV 最早載入
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))
load_dotenv(os.path.join(ROOT_DIR, ".env.local"), override=True)
machine_name = str(os.getenv("COMPUTERNAME") or "").strip()
if machine_name:
    load_dotenv(os.path.join(ROOT_DIR, f".env.{machine_name}"), override=True)

# ✅ 是否啟用 SocketIO
USE_SOCKETIO = os.getenv("USE_SOCKETIO", "1").strip().lower() in ("1", "true", "yes", "y")
_SOCKET_ASYNC_MODE = None

# ✅ eventlet monkey_patch 必須在 import flask/werkzeug 之前
if USE_SOCKETIO:
    import eventlet  # type: ignore
    eventlet.monkey_patch()
    _SOCKET_ASYNC_MODE = "eventlet"

# ---- monkey_patch 後才能 import 其他 ----
import logging
from logging.handlers import RotatingFileHandler
import pyodbc
import getpass
from decimal import Decimal
from datetime import datetime, date

from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_socketio import SocketIO, emit  # type: ignore
from werkzeug.exceptions import HTTPException
from utils.error_notify import build_payload, exception_payload, notify_webhook

# ✅ HTTP routes (Blueprints) —— 一定要在這裡 import，否則 order_bp 會未定義
from routes.order import order_bp
from routes.ai import ai_bp
from routes.ai_kpi import bp as ai_kpi_bp
from routes.ar_apply import bp as ar_apply_bp
from routes.ar_manage import bp as ar_manage_bp
from routes.inv_grn import bp as inv_grn_bp
from routes.lab_forms import bp as lab_forms_bp
from routes.realtime import bp as rt_bp
from routes.lab_qet import bp as lab_qet_bp
from routes.lab_mech import bp as lab_mech_bp
from routes.lab_final_report import bp as lab_final_report_bp

# 前端 /ai/api/rt/login -> Vite 轉發 /api/rt/login -> 這裡接到 /login
# --- Logging ---
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    log_file = os.path.join(LOG_DIR, "backend_app.log")
    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )
    return logging.getLogger("ai_erp.backend")


logger = setup_logging()


# --- DB helper ---
def get_db_conn():
    driver = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server").strip()
    if not (driver.startswith("{") and driver.endswith("}")):
        driver = "{" + driver + "}"

    server = os.getenv("DB_SERVER", "").strip()
    database = os.getenv("DB_DATABASE", "").strip()
    trusted = (os.getenv("DB_TRUSTED", "no").strip().lower() in ("1", "true", "yes", "y"))

    base = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
        "Connection Timeout=5;"
    )

    if trusted:
        conn_str = base + "Trusted_Connection=yes;"
    else:
        uid = os.getenv("DB_UID", "").strip()
        pwd = os.getenv("DB_PWD", "").strip()
        conn_str = base + f"UID={uid};PWD={pwd};"

    return pyodbc.connect(conn_str)


# ✅ SocketIO 全域物件（create_app 裡初始化）
# ✅ SocketIO 全域物件（create_app 裡初始化）
socketio: SocketIO | None = None

# ✅ 在線清單：先用「連線中的 socket id」當使用者（最小可用）
# 之後你要接 login user / account，再把 value 換成 username 即可
ONLINE = {}  # sid(socket.id) -> dict


class ERPJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def create_app():
    global socketio
    app = Flask(__name__)
    app.json = ERPJSONProvider(app)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "erp_secret")
    app.config["GET_DB_CONN"] = get_db_conn
    # ✅ 修正 CORS 設定，允許特定的 Origin 並支援 Credentials
    CORS(app, resources={r"/*": {
        "origins": [
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:81",
            "http://127.0.0.1:81",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        "supports_credentials": True,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
    }})
    # ✅ 統一 Blueprint 路由前綴，對應 Vite 的 rewrite 規則
    # 這樣前端請求 /ai/api/order 會變成 /api/order 送到這裡
    app.register_blueprint(order_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api")
    app.register_blueprint(ai_kpi_bp, url_prefix="/api")
    app.register_blueprint(ar_apply_bp, url_prefix="/api")
    app.register_blueprint(ar_manage_bp, url_prefix="/api")
    app.register_blueprint(inv_grn_bp, url_prefix="/api")
    app.register_blueprint(lab_forms_bp, url_prefix="/lab")
    app.register_blueprint(lab_forms_bp, url_prefix="/api/lab", name="lab_forms_api_compat")
    app.register_blueprint(lab_forms_bp, url_prefix="/ai/api/lab", name="lab_forms_ai_api_compat")
    app.register_blueprint(rt_bp, url_prefix="/api/rt")
    app.register_blueprint(lab_qet_bp, url_prefix="/lab/qet")
    app.register_blueprint(lab_qet_bp, url_prefix="/api/lab/qet", name="lab_qet_api_compat")
    app.register_blueprint(lab_qet_bp, url_prefix="/ai/api/lab/qet", name="lab_qet_ai_api_compat")
    app.register_blueprint(lab_mech_bp)
    app.register_blueprint(lab_final_report_bp)
    # ✅ Socket.IO 路徑修正
    if USE_SOCKETIO:
        # 注意：這裡對應的是 Vite 轉發後的最終路徑
        # 如果 Vite rewrite 了 /ai/socket.io -> /socket.io
        # 那麼這裡的 path 應該設為 "socket.io"
        sio_path = "socket.io" 

        if _SOCKET_ASYNC_MODE:
            socketio = SocketIO(
                app,
                cors_allowed_origins="*",
                async_mode=_SOCKET_ASYNC_MODE,
                path=sio_path, # 修正為不含 /ai 的路徑
                ping_interval=25,
                ping_timeout=120,
            )
            logger.info(f"✅ SocketIO enabled on path: /{sio_path}")

            # --- 基本事件（先給最小可用） ---
            # --- 基本事件（最小可用） ---
            @socketio.on("connect")
            def _on_connect():
                from flask import request

                sid = request.sid
                ONLINE[sid] = {"sid": sid}

                emit("serverHello", {"ok": True, "sid": sid})
                
            @socketio.on("disconnect")
            def _on_disconnect():
                try:
                    from flask import request as _req
                    sid = _req.sid
                    if sid in ONLINE:
                        ONLINE.pop(sid, None)
                except Exception:
                    pass

            # ✅ 前端會 emit('requestUserList')
            @socketio.on("requestUserList")
            def _request_user_list():
                # 先回傳所有在線 socket（最小可用）
                users = list(ONLINE.values())
                emit("updateUserList", users, broadcast=True)

            @socketio.on("rt:ping")
            def _rt_ping(msg=None):
                emit("rt:pong", {"ok": True})
    # 其他可選 BP
    try:
        from routes.customer import customer_bp
        app.register_blueprint(customer_bp, url_prefix="/api/customer")
        logger.info("✅ registered routes.customer.customer_bp")
    except Exception as e:
        logger.warning(f"⚠️ skip customer_bp (routes.customer): {e}")

    try:
        from routes.form import form_bp
        app.register_blueprint(form_bp, url_prefix="/api/customer")
        logger.info("✅ registered routes.form.form_bp")
    except Exception as e:
        logger.warning(f"⚠️ skip form_bp (routes.form): {e}")

    try:
        from contexts.context import context_bp as _context_bp
        app.register_blueprint(_context_bp, url_prefix="/api")
        logger.info("✅ registered contexts.context.context_bp")
    except Exception as e:
        logger.warning(f"⚠️ skip context_bp (contexts.context): {e}")

    try:
        import routes.form_customer_create as fcc
        logger.info(f"✅ form_customer_create module file = {fcc.__file__}")

        from routes.form_customer_create import bp as form_customer_create_bp
        app.register_blueprint(form_customer_create_bp)
        logger.info("✅ registered routes.form_customer_create.bp")
    except Exception as e:
        logger.warning(f"⚠️ skip form_customer_create_bp (routes.form_customer_create): {e}")

    try:
        from routes.options import bp as options_bp
        app.register_blueprint(options_bp)
        logger.info("✅ registered routes.options.bp")
    except Exception as e:
        logger.warning(f"⚠️ skip options_bp (routes.options): {e}")

    try:
        from routes.customer_view_api import bp as customer_view_api_bp
        app.register_blueprint(customer_view_api_bp)
        logger.info("✅ registered routes.customer_view_api.bp")
    except Exception as e:
        logger.warning(f"⚠️ skip customer_view_api_bp: {e}")

    @app.post("/api/client-error")
    def client_error_report():
        body = request.get_json(silent=True) or {}
        payload = build_payload(
            kind="client_error",
            title=str(body.get("message") or "client error"),
            data={
                "url": str(body.get("url") or ""),
                "source": str(body.get("source") or ""),
                "line": body.get("line"),
                "column": body.get("column"),
                "stack": str(body.get("stack") or "")[:12000],
                "user_agent": request.headers.get("User-Agent"),
                "remote_addr": request.headers.get("X-Forwarded-For") or request.remote_addr,
            },
        )
        logger.error("[client-error] %s", payload)
        sent = False
        detail = "webhook disabled"
        try:
            sent, detail = notify_webhook(payload)
        except Exception as e:
            logger.exception("client error webhook failed: %s", e)
            detail = str(e)
        return jsonify({"ok": True, "sent": sent, "detail": detail})

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        if isinstance(exc, HTTPException):
            return exc

        logger.exception("Unhandled exception on %s %s", request.method, request.path)

        if request.path != "/api/client-error":
            try:
                payload = exception_payload(
                    exc,
                    {
                        "method": request.method,
                        "path": request.path,
                        "query": request.query_string.decode("utf-8", errors="ignore"),
                        "remote_addr": request.headers.get("X-Forwarded-For") or request.remote_addr,
                        "user_agent": request.headers.get("User-Agent"),
                    },
                )
                notify_webhook(payload)
            except Exception as notify_exc:
                logger.exception("backend exception webhook failed: %s", notify_exc)

        return jsonify({"ok": False, "msg": str(exc)}), 500

    # ---------------------------------------------------------
    # Debug routes
    # ---------------------------------------------------------
    @app.get("/__routes")
    def __routes():
        out = []
        for r in app.url_map.iter_rules():
            out.append(f"{','.join(sorted(r.methods))}  {r.rule}  -> {r.endpoint}")
        return "<br>".join(sorted(out))

    @app.get("/api/_whoami")
    def whoami():
        return {
            "windows_user": getpass.getuser(),
            "username_env": os.getenv("USERNAME"),
            "userdomain": os.getenv("USERDOMAIN"),
        }

    logger.info("=== Flask url_map ===")
    for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x)):
        logger.info(str(r))

    return app


# ✅ build app
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("HTTP_PORT", os.getenv("PORT", "8080")))
    host = os.getenv("HTTP_HOST", "127.0.0.1")
    logger.info(f"🚀 ERP server starting on {host}:{port} USE_SOCKETIO={USE_SOCKETIO}")

    # ✅ 若 SocketIO 可用 → 用 eventlet 跑（支援 WebSocket）
    if USE_SOCKETIO and socketio is not None and _SOCKET_ASYNC_MODE is not None:
        # eventlet server
        socketio.run(app, host=host, port=port, debug=False)
    else:
        # ✅ HTTP only：waitress（IIS 反代友善）
        try:
            from waitress import serve
            serve(app, host=host, port=port, threads=8)
        except Exception as e:
            logger.warning(f"⚠️ waitress not available, fallback to Flask dev server: {e}")
            app.run(host=host, port=port, debug=False)
