from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from sqlalchemy import text
from backend.extensions import db
import logging

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger("ai_erp")

@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    account_in = (data.get("account") or "").strip()
    password = (data.get("password") or "").strip()

    logger.info(f"🔐 Login attempt: {account_in}")

    if not account_in or not password:
        logger.warning("⚠️ Login missing account/password")
        return jsonify(ok=False, msg="帳號或密碼不可空白"), 400

    try:
        user = db.session.execute(
            text("""
                SELECT TOP 1 id, dep, name, authority, eid
                FROM staff
                WHERE eid = :eid AND password = :pwd
            """),
            {"eid": account_in, "pwd": password}
        ).mappings().first()

        if not user:
            logger.warning(f"❌ Login failed: {account_in}")
            return jsonify(ok=False, msg="帳號或密碼錯誤"), 401

        user_id = str(user["id"])  # ✅ identity 要字串
        account = str(user["eid"]).strip()
        name = str(user["name"]).strip()
        authority = str(user["authority"]).strip()

        token = create_access_token(
            identity=user_id,
            additional_claims={
                "account": account,
                "name": name,
                "authority": authority
            }
        )

        logger.info(f"✅ Login success: {account}")

        return jsonify(
            ok=True,
            access_token=token,
            user={"id": int(user_id), "account": account, "name": name, "authority": authority}
        )

    except Exception:
        logger.exception("🚨 Login exception")
        return jsonify(ok=False, msg="系統錯誤"), 500

@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()  # 字串
    claims = get_jwt()

    user = {
        "id": int(user_id),
        "account": claims.get("account"),
        "name": claims.get("name"),
        "authority": claims.get("authority")
    }

    logger.info(f"👤 /me called by {user.get('account')}")
    return jsonify(ok=True, user=user)



