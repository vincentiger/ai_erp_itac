from __future__ import annotations

import json
import os
import socket
import traceback
import urllib.request
from datetime import datetime
from typing import Any


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "y", "on")


def webhook_enabled() -> bool:
    if not _truthy(os.getenv("ERROR_WEBHOOK_ENABLED", "1")):
        return False
    return bool(str(os.getenv("ERROR_WEBHOOK_URL", "")).strip())


def _safe_text(value: Any, limit: int = 4000) -> str:
    text = "" if value is None else str(value)
    return text[:limit]


def build_payload(kind: str, title: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "kind": kind,
        "title": _safe_text(title, 300),
        "app": "AI_ERP_ITAC",
        "host": socket.gethostname(),
        "time": datetime.now().isoformat(timespec="seconds"),
        "data": data or {},
    }


def notify_webhook(payload: dict[str, Any]) -> tuple[bool, str]:
    url = str(os.getenv("ERROR_WEBHOOK_URL", "")).strip()
    if not webhook_enabled():
        return False, "webhook disabled"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        timeout = float(os.getenv("ERROR_WEBHOOK_TIMEOUT", "5").strip() or "5")
    except Exception:
        timeout = 5.0

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = getattr(resp, "status", 200)
        return True, f"HTTP {status}"


def exception_payload(exc: Exception, context: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_payload(
        kind="backend_exception",
        title=str(exc),
        data={
            **(context or {}),
            "exception_type": exc.__class__.__name__,
            "traceback": _safe_text(traceback.format_exc(), 12000),
        },
    )
