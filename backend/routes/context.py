# backend/routes/context.py
import os
import json
from flask import Blueprint, jsonify

context_bp = Blueprint("context", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
CONTEXT_DIR = os.path.join(BASE_DIR, "contexts")

@context_bp.get("/context/<page>")
def get_context(page: str):
    safe_name = "".join([c for c in page if c.isalnum() or c in ("_", "-")]).strip()
    fp = os.path.join(CONTEXT_DIR, f"{safe_name}.json")

    if not os.path.exists(fp):
        return jsonify({"ok": False, "msg": f"context not found: {safe_name}"}), 404

    with open(fp, "r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify({"ok": True, "data": data})
