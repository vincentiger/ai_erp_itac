# C:\ai_erp\backend\sockets\socketio.py
from flask_socketio import SocketIO

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",   # ✅ 真正支援 websocket
)



