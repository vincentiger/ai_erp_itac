# backend/socket_handlers.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Any
from flask import request
from flask_socketio import emit, disconnect
from sockets.socketio import socketio

# =========================================================
# 線上使用者管理（記憶體版）
# 你要做成 DB 版也可以，但先用這個保證可跑
# =========================================================

@dataclass
class OnlineUser:
    sid: str
    account: str
    name: str
    ip: str


ONLINE_BY_SID: Dict[str, OnlineUser] = {}
SID_BY_ACCOUNT: Dict[str, str] = {}


def _ip() -> str:
    # 反代下取真實 IP（若 IIS/ARR 有帶 X-Forwarded-For）
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or ""


def _broadcast_user_list() -> None:
    users = [
        {"account": u.account, "name": u.name, "ip": u.ip}
        for u in ONLINE_BY_SID.values()
    ]
    socketio.emit("updateUserList", users)  # ✅ 全體廣播


def _kick_old_session_if_any(account: str, reason: str = "此帳號已在其他裝置登入") -> None:
    old_sid = SID_BY_ACCOUNT.get(account)
    if not old_sid:
        return
    if old_sid == request.sid:
        return

    # ✅ 通知舊連線強制登出（前端收到後做 logout/導回 login）
    socketio.emit("forceLogout", reason, to=old_sid)

    # ✅ 斷線舊連線（若失敗也沒關係，至少 forceLogout 已發）
    try:
        socketio.server.disconnect(old_sid)
    except Exception:
        pass

    # ✅ 清掉舊記錄
    old_u = ONLINE_BY_SID.pop(old_sid, None)
    if old_u:
        SID_BY_ACCOUNT.pop(old_u.account, None)


# =========================================================
# ✅ 事件：connect / disconnect
# =========================================================

@socketio.on("connect")
def on_connect():
    # 先不加入 ONLINE（要 login 後才算）
    # 但你可以用來 debug
    # print("[socket] connect", request.sid)
    pass


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    u = ONLINE_BY_SID.pop(sid, None)
    if u:
        # 若是目前 account 對應的 sid 才移除映射
        if SID_BY_ACCOUNT.get(u.account) == sid:
            SID_BY_ACCOUNT.pop(u.account, None)
        _broadcast_user_list()


# =========================================================
# ✅ 事件：login
# =========================================================

def _verify_user(account: str, password: str) -> Optional[Dict[str, Any]]:
    """
    TODO: 你要接你自己的驗證（DB / AD / 既有 ASP）
    這裡先給一個可跑的 demo：
    - admin / 1234 允許登入
    - 其他拒絕
    """
    if account == "admin" and password == "1234":
        return {
            "account": "admin",
            "name": "Administrator",
            "roles": ["admin"],
        }
    return None


@socketio.on("login")
def on_login(data):
    try:
        account = (data or {}).get("account", "") or ""
        password = (data or {}).get("password", "") or ""
        account = account.strip()
        password = password.strip()

        if not account or not password:
            emit("loginError", "請輸入帳號密碼")
            return

        user = _verify_user(account, password)
        if not user:
            emit("loginError", "登入失敗，請確認帳號密碼")
            return

        # ✅ 同帳號多開：踢掉舊連線
        _kick_old_session_if_any(account, reason="此帳號已在其他裝置登入，您已被登出")

        # ✅ 登入成功：寫入線上清單
        u = OnlineUser(
            sid=request.sid,
            account=account,
            name=(user.get("name") or account),
            ip=_ip(),
        )
        ONLINE_BY_SID[request.sid] = u
        SID_BY_ACCOUNT[account] = request.sid

        # ✅ 回傳給這個 client（只回給自己）
        emit("loginSuccess", user)

        # ✅ 廣播線上名單
        _broadcast_user_list()

    except Exception as e:
        emit("loginError", f"登入例外：{e}")


# =========================================================
# ✅ 事件：ping_test（你前端 debug 用）
# =========================================================

@socketio.on("ping_test")
def on_ping_test(data):
    emit("pong_test", {"ok": True, "echo": data})
