
#C:\ai_erp\backend\routes\realtime.py
from __future__ import annotations
from flask import Blueprint, request, jsonify, current_app
import logging
import os
import uuid
import time
import threading
import traceback
from logging.handlers import RotatingFileHandler

from path_config import LOG_DIR

# Socket.IO（可用就用；不可用就退化成純 HTTP）
try:
    from sockets import socketio  # 你專案現有的 socketio 實例
except Exception:
    socketio = None
    # 不 raise，讓純 HTTP 也能跑

bp = Blueprint("rt", __name__)  # 不要 url_prefix
logger = logging.getLogger("ai_erp")
# -----------------------------
# 全域記憶體（先簡單做）
# -----------------------------
sessions = {}       # sid -> { user, ts }
online_users = {}   # account -> user_info (含 sid, menus)
event_queues = {}   # sid -> [ events ]

_LOCK = threading.Lock()

# session 多久沒動就清掉（秒）
SESSION_TTL = 60 * 60  # 1 小時
_LOGIN_ERROR_LOGGER_NAME = "ai_erp.rt_login_error"
_login_error_logger = None
_LOGIN_ERROR_FILE = os.path.join(LOG_DIR, "rt_login_error.log")


# -----------------------------
# 工具
# -----------------------------
def _now():
    return int(time.time())


def _text(value) -> str:
    return "" if value is None else str(value).strip()


def _get_login_error_logger():
    global _login_error_logger
    if _login_error_logger is not None:
        return _login_error_logger

    os.makedirs(LOG_DIR, exist_ok=True)
    err_logger = logging.getLogger(_LOGIN_ERROR_LOGGER_NAME)
    err_logger.setLevel(logging.INFO)
    err_logger.propagate = False

    log_file = os.path.join(LOG_DIR, "rt_login_error.log")
    abs_log_file = os.path.abspath(log_file)
    if not any(
        isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == abs_log_file
        for h in err_logger.handlers
    ):
        handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        err_logger.addHandler(handler)

    _login_error_logger = err_logger
    return err_logger


def _append_login_error_log(message: str):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(_LOGIN_ERROR_FILE, "a", encoding="utf-8") as fh:
        fh.write(message.rstrip() + "\n")


def _log_login_exception(exc: Exception, account: str, sid: str):
    remote_addr = request.headers.get("X-Forwarded-For") or request.remote_addr or ""
    tb_text = traceback.format_exc()
    payload = request.get_json(silent=True)
    try:
        _get_login_error_logger().exception(
            "🚨 /api/rt/login failed account=%s sid=%s remote_addr=%s",
            account,
            sid,
            remote_addr,
        )
    except Exception:
        pass

    try:
        _append_login_error_log(
            "\n".join([
                f"[ERROR] /api/rt/login failed",
                f"account={account}",
                f"sid={sid}",
                f"remote_addr={remote_addr}",
                f"request_json={payload!r}",
                f"exception={exc!r}",
                tb_text.rstrip(),
                "",
            ])
        )
    except Exception:
        pass


def _new_sid():
    return str(uuid.uuid4())


def _touch_session(sid: str):
    sessions.setdefault(sid, {})
    sessions[sid]["ts"] = _now()


def _ensure_session(sid: str | None):
    """確保 sid 存在；sid 不存在就建立新的，回傳 sid。
    ✅ 允許 client 帶入 sid：不存在就用該 sid 建立（避免必打 /session）
    """
    sid = _text(sid)
    with _LOCK:
        if not sid:
            sid = _new_sid()

        # ✅ 不存在就用 sid 建立（而不是改成 _new_sid）
        if sid not in sessions or sid not in event_queues:
            sessions[sid] = {"ts": _now(), "user": None}
            event_queues[sid] = []
        else:
            _touch_session(sid)

    return sid

def _cleanup_expired():
    """清理過期 session（避免 dict 無限長）
    ✅ 若 online_users 有綁 sid，且 sid 過期，才移除在線（避免誤踢）
    """
    cut = _now() - SESSION_TTL
    with _LOCK:
        dead = [sid for sid, s in sessions.items() if int(s.get("ts") or 0) < cut]
        for sid in dead:
            u = (sessions.get(sid) or {}).get("user") or {}
            acc = _text(u.get("account"))
            if acc:
                cur = online_users.get(acc) or {}
                if (cur.get("sid") or "") == sid:
                    online_users.pop(acc, None)

            sessions.pop(sid, None)
            event_queues.pop(sid, None)


def _get_users_list():
    with _LOCK:
        return list(online_users.values())


def push_event(sid, event):
    with _LOCK:
        if sid not in event_queues:
            event_queues[sid] = []
        event_queues[sid].append(event)


def broadcast(event):
    # ✅ 用 list() 避免迭代期間 dict 改變
    with _LOCK:
        sids = list(event_queues.keys())
    for sid in sids:
        push_event(sid, event)


def _broadcast_user_list():
    """同時支援：
    - HTTP 長輪詢（event_queues）
    - Socket.IO 即時推播（updateUserList）
    """
    users = _get_users_list()

    # ✅ 給 HTTP poll/watch 用（event_queues）
    broadcast({"type": "updateUserList", "data": users})

    # ✅ 給 Socket.IO 用（即時推播）
    if socketio is not None:
        try:
            socketio.emit("updateUserList", users)
        except Exception:
            pass

# backend/routes/realtime.py
@bp.post("/heartbeat")
def heartbeat():
    _cleanup_expired()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}
    sid = _ensure_session(data.get("sid"))
    user = data.get("user") or {}
    acc = _text(user.get("account"))
    
    # 只要有帳號，就更新他在線狀態
    if acc:
        with _LOCK:
            user["sid"] = sid
            user["ts"] = _now() # 標記最後活動時間
            sessions[sid]["user"] = user
            online_users[acc] = user
            _touch_session(sid)
    
    # ✅ 關鍵：直接回傳當前所有在線名單，讓前端不用再額外發 GET 請求
    users = _get_users_list()
    return jsonify({
        "ok": True, 
        "sid": sid, 
        "users": users, 
        "online_count": len(users)
    })
# -----------------------------
# 建立 session
# -----------------------------
@bp.post("/session")
def create_session():
    sid = _ensure_session(None)
    return jsonify({"ok": True, "sid": sid})


# -----------------------------
# 登入（HTTP 版本，自癒 + 含 menus）
# -----------------------------
@bp.post("/login")
def login():
    conn = None
    sid = ""
    account = ""
    try:
        _cleanup_expired()

        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            data = {}
        sid = _ensure_session(data.get("sid"))

        account = _text(data.get("account"))
        password = _text(data.get("password"))

        if not account or not password:
            return jsonify({"ok": False, "msg": "請輸入帳號密碼", "sid": sid}), 400

        conn = current_app.config["GET_DB_CONN"]()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, dep, name, authority, eid, ISNULL(dep_manager, 0) AS dep_manager FROM staff WHERE eid = ? AND password = ?",
            (account, password),
        )
        staff = cursor.fetchone()
        if not staff:
            return jsonify({"ok": False, "msg": "帳號密碼錯誤", "sid": sid}), 401

        auth_id = staff[3]
        user_account = _text(staff[4])

        # --- 主選單 ---
        cursor.execute(
            """
            SELECT DISTINCT C.auTitle, C.refno
            FROM auFunctions B
            INNER JOIN mainRoles C ON B.refno = C.refno
            WHERE B.authoritiesId = ?
              AND ISNULL(C.au, 'N') = 'Y'
            ORDER BY C.refno
            """,
            (auth_id,),
        )
        main_raw = cursor.fetchall()

        menu_tree = []
        for m in main_raw:
            main_title = _text(m[0])
            refno = _text(m[1])

            cursor.execute(
                """
                SELECT
                    sr.secondAuTitle,
                    sr.vue,
                    sr.[view],
                    af.serial
                FROM auFunctions af
                INNER JOIN secondRoles sr
                    ON sr.id = af.secondAuId
                WHERE af.authoritiesId = ?
                  AND af.refno = ?
                  AND ISNULL(sr.au, 'Y') = 'Y'
                ORDER BY af.serial, sr.id
                """,
                (auth_id, refno),
            )

            subs = []
            for s in cursor.fetchall():
                title = _text(s[0])
                vue = _text(s[1]) if s[1] else ""
                view_name = _text(s[2]) if s[2] else ""
                serial = s[3] if len(s) > 3 else None

                subs.append({
                    "title": title,
                    "url": vue,        # ✅ 舊版相容（前端用 sub.url）
                    "vue": vue,
                    "view": view_name,
                    "serial": serial,
                    "refno": refno,
                })

            menu_tree.append({
                "title": main_title,
                "refno": refno,
                "children": subs,
            })

        user_info = {
            "id": staff[0],
            "account": user_account,
            "name": _text(staff[2]),
            "dep": _text(staff[1]),
            "authority": staff[3],
            "dep_manager": 1 if int(staff[5] or 0) == 1 else 0,
            "sid": sid,
            "menus": menu_tree,
        }

        with _LOCK:
            sessions[sid]["user"] = user_info
            _touch_session(sid)
            online_users[user_account] = user_info

        _broadcast_user_list()

        users = _get_users_list()
        return jsonify({
            "ok": True,
            "sid": sid,
            "user": user_info,
            "users": users,
            "online_count": len(users),
        })

    except Exception as e:
        logger.exception("🚨 /api/rt/login failed")
        _log_login_exception(e, account, sid)
        return jsonify({"ok": False, "msg": f"系統錯誤: {str(e)}", "sid": sid}), 500
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


# -----------------------------
# 直接取得在線名單（給 rt.js 用：GET /api/rt/users?sid=...）
# -----------------------------
@bp.get("/p-list/")
def get_p_list():
    _cleanup_expired()
    sid = _ensure_session(request.args.get("sid"))
    with _LOCK:
        _touch_session(sid)

    users_list = _get_users_list()
    return jsonify({
        "ok": True, 
        "sid": sid, 
        "users": users_list, 
        "online_count": len(users_list)
    })

# -----------------------------
# 長輪詢（自癒：sid 不存在就建立）
# -----------------------------
@bp.get("/poll")
def poll():
    _cleanup_expired()

    sid = _ensure_session(request.args.get("sid"))

    timeout = 20
    start = time.time()

    while time.time() - start < timeout:
        with _LOCK:
            q = event_queues.get(sid, [])
            if q:
                events = q[:]
                event_queues[sid] = []
                _touch_session(sid)
                return jsonify({"ok": True, "sid": sid, "events": events})
        time.sleep(0.5)

    with _LOCK:
        _touch_session(sid)

    return jsonify({"ok": True, "sid": sid, "events": []})


# -----------------------------
# 主動要求在線名單（HTTP 版）
# ✅ 直接回 users，前端不用 poll 也能立即顯示
# -----------------------------
@bp.post("/requestUserList")
def request_user_list():
    _cleanup_expired()

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}
    sid = _ensure_session(data.get("sid"))

    with _LOCK:
        _touch_session(sid)

    users = _get_users_list()

    # 兼容舊 poll client（仍可收到 event）
    push_event(sid, {"type": "updateUserList", "data": users})

    return jsonify({"ok": True, "sid": sid, "users": users, "online_count": len(users)})


# -----------------------------
# 登出
# -----------------------------
@bp.post("/logout")
def logout():
    _cleanup_expired()

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}
    sid = _text(data.get("sid"))
    if not sid:
        return jsonify({"ok": True})

    with _LOCK:
        user = (sessions.get(sid) or {}).get("user") or {}
        acc = _text(user.get("account"))

        if acc:
            cur = online_users.get(acc) or {}
            if (cur.get("sid") or "") == sid:
                online_users.pop(acc, None)

        sessions.pop(sid, None)
        event_queues.pop(sid, None)

    _broadcast_user_list()
    return jsonify({"ok": True})


# =========================================================
# Socket.IO handlers（可選：若 socketio 可用）
# =========================================================
if socketio is not None:
    from flask_socketio import emit
    from flask import request as sio_request

    @socketio.on("requestUserList")
    def _sio_request_user_list(*args, **kwargs):
        # ✅ 只回給「這個連線」，避免全站廣播造成混亂
        users = _get_users_list()
        try:
            emit("updateUserList", users, to=sio_request.sid)
        except Exception:
            pass
