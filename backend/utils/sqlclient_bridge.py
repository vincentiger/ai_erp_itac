import atexit
import base64
import json
import os
import subprocess
import threading
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _conn_str():
    server = os.getenv("DB_SERVER", "").strip()
    database = os.getenv("DB_DATABASE", "").strip()
    trusted = os.getenv("DB_TRUSTED", "no").strip().lower() in ("1", "true", "yes", "y")
    base = [
        f"Server={server}",
        f"Database={database}",
        "Encrypt=False",
        "TrustServerCertificate=True",
        "Connection Timeout=5",
    ]
    if trusted:
        base.append("Integrated Security=True")
    else:
        base.append(f"User ID={os.getenv('DB_UID', '').strip()}")
        base.append(f"Password={os.getenv('DB_PWD', '').strip()}")
    return ";".join(base)


def _normalize_sql(sql, params):
    sql = str(sql or "")
    params = list(params or [])
    out = []
    parts = sql.split("?")
    if len(parts) - 1 != len(params):
        raise ValueError("SQL parameter count does not match placeholders")
    for idx, part in enumerate(parts[:-1]):
        out.append(part)
        out.append(f"@p{idx}")
    out.append(parts[-1])
    named_params = [{"name": f"@p{idx}", "value": params[idx]} for idx in range(len(params))]
    return "".join(out), named_params


_WORKER = None
_WORKER_LOCK = threading.Lock()


def _worker_script():
    return str(Path(__file__).with_name("sqlclient_worker.ps1"))


def _start_worker():
    global _WORKER
    if _WORKER and _WORKER.poll() is None:
        return _WORKER

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    _WORKER = subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", _worker_script()],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
        creationflags=creationflags,
    )
    return _WORKER


def _stop_worker():
    global _WORKER
    proc = _WORKER
    _WORKER = None
    if not proc:
        return
    try:
        if proc.stdin:
            proc.stdin.close()
    except Exception:
        pass
    try:
        proc.terminate()
    except Exception:
        pass
    try:
        proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


atexit.register(_stop_worker)


def _run(payload):
    line = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")
    with _WORKER_LOCK:
        proc = _start_worker()
        try:
            if not proc.stdin or not proc.stdout:
                raise RuntimeError("sqlclient worker pipes are unavailable")
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
            out_line = proc.stdout.readline()
        except Exception:
            _stop_worker()
            raise

        if not out_line:
            stderr = ""
            try:
                stderr = proc.stderr.read() if proc.stderr else ""
            except Exception:
                pass
            _stop_worker()
            raise RuntimeError((stderr or "sqlclient worker exited unexpectedly").strip())

    data = json.loads(base64.b64decode(out_line.strip()).decode("utf-8"))
    if isinstance(data, dict) and not data.get("ok", True):
        detail = str(data.get("detail") or data.get("error") or "").strip()
        raise RuntimeError(detail or "sqlclient worker returned an error")
    return data


def query_all(sql, params=None):
    named_sql, named_params = _normalize_sql(sql, params or [])
    data = _run(
        {
            "mode": "query",
            "connection_string": _conn_str(),
            "sql": named_sql,
            "params": named_params,
        }
    )
    return data.get("rows", []) if isinstance(data, dict) else []


def query_one(sql, params=None):
    rows = query_all(sql, params=params)
    return rows[0] if rows else None


def execute(sql, params=None):
    named_sql, named_params = _normalize_sql(sql, params or [])
    data = _run(
        {
            "mode": "execute",
            "connection_string": _conn_str(),
            "sql": named_sql,
            "params": named_params,
        }
    )
    return int(data.get("rowcount", 0)) if isinstance(data, dict) else 0


def execute_transaction(statements):
    normalized = []
    for stmt in statements or []:
        sql = stmt.get("sql", "")
        params = stmt.get("params", [])
        named_sql, named_params = _normalize_sql(sql, params)
        normalized.append({"sql": named_sql, "params": named_params})
    data = _run(
        {
            "mode": "transaction",
            "connection_string": _conn_str(),
            "statements": normalized,
        }
    )
    return data


def query_batch(statements):
    normalized = []
    for stmt in statements or []:
        sql = stmt.get("sql", "")
        params = stmt.get("params", [])
        named_sql, named_params = _normalize_sql(sql, params)
        normalized.append({"sql": named_sql, "params": named_params})
    data = _run(
        {
            "mode": "batch_query",
            "connection_string": _conn_str(),
            "statements": normalized,
        }
    )
    if not isinstance(data, dict):
        return []
    results = data.get("results", [])
    flattened = []
    for rows in results:
        if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], list):
            flattened.append(rows[0])
        else:
            flattened.append(rows)
    return flattened
