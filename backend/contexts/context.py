# C:\ai_erp\backend\contexts\context.py
import os, json
from flask import Blueprint, jsonify

context_bp = Blueprint("context_bp", __name__)

BASE_DIR = os.path.dirname(__file__)  # ...\backend\contexts

@context_bp.get("/context/<page>")
def get_context(page):
    # 例如 /api/context/customer_create -> 讀 contexts/customer_create.json
    path = os.path.join(BASE_DIR, f"{page}.json")
    if not os.path.exists(path):
        return jsonify({"ok": False, "msg": f"context not found: {page}"}), 404

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify({"ok": True, "data": data})
