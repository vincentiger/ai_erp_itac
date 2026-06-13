# C:\ai_erp\backend\sockets\auth_events.py
import threading
import time
from flask import request
from flask_socketio import emit

from sockets import socketio

online_users = {}  # account -> user_info
_REGISTERED = False


def _broadcast_user_list():
    socketio.emit("updateUserList", list(online_users.values()))


def register_auth_socket_handlers(get_db_conn, logger):
    global _REGISTERED
    if _REGISTERED:
        logger.warning("⚠️ auth socket handlers already registered, skip.")
        return
    _REGISTERED = True

    logger.info("✅ register auth socket handlers ...")

    @socketio.on("connect")
    def handle_connect():
        logger.info(f"⚡ [socket] connect sid={request.sid}")

    @socketio.on("login")
    def handle_login(data):
        data = data or {}
        account = (data.get("account") or "").strip()
        password = (data.get("password") or "").strip()
        sid = request.sid

        logger.info(f"🔐 [socket] login attempt acc={account} sid={sid}")

        if not account or not password:
            emit("loginError", "請輸入帳號密碼")
            return

        conn = None
        try:
            conn = get_db_conn()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, dep, name, authority, eid FROM staff WHERE eid = ? AND password = ?",
                (account, password),
            )
            staff = cursor.fetchone()
            if not staff:
                emit("loginError", "帳號密碼錯誤")
                return

            auth_id = staff[3]
            user_account = str(staff[4] or "").strip()

            # ✅ 用真正的 user_account 再做一次重複登入檢查（最準）
            if user_account in online_users:
                emit("loginError", "此帳號已在其他地方登入")
                return

            # --- 主選單 ---
            cursor.execute(
                """
                SELECT DISTINCT B.secondAuId, C.auTitle, C.refno
                FROM auFunctions B
                INNER JOIN mainRoles C ON B.refno = C.refno
                WHERE B.authoritiesId = ?
                  AND ISNULL(C.au, 'N') = 'Y'
                ORDER BY C.refno
                """,
                (auth_id,),
            )
            main_raw = cursor.fetchall()

            menu_map = {}
            for m in main_raw:
                second_au_id = m[0]
                main_title = (m[1] or "").strip()
                refno = (m[2] or "").strip()

                cursor.execute(
                    """
                    SELECT secondAuTitle, vue, [view], serial
                    FROM secondRoles
                    WHERE refno = ?
                      AND id = ?
                      AND ISNULL(au, 'N') = 'Y'
                    ORDER BY serial
                    """,
                    (refno, second_au_id),
                )

                for s in cursor.fetchall():
                    title = (s[0] or "").strip()
                    vue = (s[1] or "").strip() if s[1] else ""
                    view_name = (s[2] or "").strip() if s[2] else ""
                    serial = s[3] if len(s) > 3 else None

                    if refno not in menu_map:
                        menu_map[refno] = {
                            "title": main_title,
                            "refno": refno,
                            "children": [],
                        }

                    menu_map[refno]["children"].append({
                        "title": title,
                        "url": vue,        # ✅ 舊版相容（前端選單還在用 url）
                        "vue": vue,        # ✅ 新版明確欄位
                        "view": view_name, # ✅ 關鍵：資料檢視表
                        "serial": serial,
                        "refno": refno,
                    })

            menu_tree = []
            for refno in sorted(menu_map.keys()):
                item = menu_map[refno]
                item["children"] = sorted(
                    item["children"],
                    key=lambda x: (
                        999999 if x.get("serial") is None else x.get("serial"),
                        x.get("title") or "",
                    ),
                )
                menu_tree.append(item)

            user_info = {
                "id": staff[0],
                "account": user_account,
                "name": (staff[2] or "").strip(),
                "sid": sid,
                "menus": menu_tree,
            }

            online_users[user_account] = user_info

            emit("loginSuccess", user_info)
            _broadcast_user_list()

            logger.info(f"✅ {user_info['name']} 登入成功 ({user_account}) sid={sid}")

        except Exception as e:
            logger.error(f"🚨 登入失敗: {e}", exc_info=True)
            emit("loginError", f"系統錯誤: {str(e)}")
        finally:
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass

    @socketio.on("disconnect")
    def handle_disconnect(*args, **kwargs):
        sid = request.sid

        target_account = None
        for acc, info in list(online_users.items()):
            if info.get("sid") == sid:
                target_account = acc
                break

        logger.info(f"🔌 [socket] disconnect sid={sid} acc={target_account}")

        if not target_account:
            return

        def delayed_check(acc_to_check, old_sid):
            time.sleep(3)
            info = online_users.get(acc_to_check)
            if info and info.get("sid") == old_sid:
                user = online_users.pop(acc_to_check, None)
                if user:
                    logger.info(f"🧹 使用者 {user.get('name')} 已離線移除 ({acc_to_check})")
                _broadcast_user_list()

        threading.Thread(
            target=delayed_check,
            args=(target_account, sid),
            daemon=True,
        ).start()

    @socketio.on("requestUserList")
    def handle_request_user_list():
        emit("updateUserList", list(online_users.values()))
        logger.info(f"📤 [socket] requestUserList -> {len(online_users)} users")
