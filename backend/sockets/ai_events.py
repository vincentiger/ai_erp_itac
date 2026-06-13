# C:\ai_erp\backend\sockets\ai_events.py
import os
import json
import logging
import base64
import urllib.parse
from datetime import date

from flask import request
from flask_socketio import emit

from sockets import socketio
from sockets.auth_events import online_users  # account -> user_info
from path_config import VOICE_REGISTRY_PATH

logger = logging.getLogger(__name__)

# ============================================================
# Optional LLM fallback (only when SOP parser cannot match)
# ============================================================
try:
    import google.generativeai as genai
except Exception:
    genai = None

api_key = os.getenv("GEMINI_API_KEY")
if genai and api_key:
    genai.configure(api_key=api_key)
    _model = genai.GenerativeModel(
        "models/gemini-2.0-flash",
        generation_config={"response_mime_type": "application/json"}
    )
else:
    _model = None


# ============================================================
# Registry loader
#   - 建議你把 voice-registry.json 放在 backend/voice
# ============================================================
def _load_registry():
    p = VOICE_REGISTRY_PATH
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ load voice registry failed: {e}")
        return {"version": 1, "intents": []}


REGISTRY = _load_registry()


# ============================================================
# SOP Helpers
# ============================================================
def _get_user_info_by_sid(sid: str) -> dict:
    for acc, info in online_users.items():
        if info.get("sid") == sid:
            return info
    return {}


def _norm_text(s: str) -> str:
    s = str(s or "").strip()
    s = s.replace("。", " ").replace("．", " ").replace("，", " ").replace("、", " ")
    s = " ".join(s.split())
    return s


def _utf8_b64_json(obj) -> str:
    # 與前端一致：btoa(encodeURIComponent(json))
    j = json.dumps(obj, ensure_ascii=False)
    return base64.b64encode(urllib.parse.quote(j).encode("utf-8")).decode("ascii")


def _build_allowed_menu_index(user_info: dict):
    """
    從 login 取得的 menus 建索引：
    - allowed_vue_set: 可用 vue 名稱集合（= secondRoles.vue）
    - by_vue: vue -> menu item {title,url,vue,view,refno,serial}
    - title_rows: 用 title 做 match（最長優先）
    """
    menus = user_info.get("menus") or []
    allowed_vue_set = set()
    by_vue = {}
    title_rows = []

    for m in menus:
        for c in (m.get("children") or []):
            vue = (c.get("vue") or c.get("url") or "").strip()
            if not vue:
                continue
            allowed_vue_set.add(vue)
            by_vue[vue] = c

            title = (c.get("title") or "").strip()
            if title:
                title_rows.append({"title": title, "item": c})

    # 最長命中（title 越長優先）
    title_rows.sort(key=lambda r: len(r["title"]), reverse=True)

    return allowed_vue_set, by_vue, title_rows


def _build_registry_alias_rows(registry: dict):
    rows = []
    for intent in (registry.get("intents") or []):
        aliases = intent.get("intent_aliases") or []
        for a in aliases:
            a = str(a or "").strip()
            if a:
                rows.append({"alias": a, "intent": intent})
    # 最長命中
    rows.sort(key=lambda r: len(r["alias"]), reverse=True)
    return rows


REG_ALIAS_ROWS = _build_registry_alias_rows(REGISTRY)


def _match_intent_by_registry(text: str):
    """
    Step 2: Intent matching（最長命中；同長度取較早出現）
    """
    best = None
    for row in REG_ALIAS_ROWS:
        alias = row["alias"]
        pos = text.find(alias)
        if pos < 0:
            continue
        cand = {"intent": row["intent"], "alias": alias, "pos": pos, "len": len(alias)}
        if (best is None) or (cand["len"] > best["len"]) or (cand["len"] == best["len"] and cand["pos"] < best["pos"]):
            best = cand
    return best


def _match_hint(text: str, intent: dict):
    default_fields = [x for x in (intent.get("defaultFields") or []) if str(x).strip()]
    hints = intent.get("hints")
    if not isinstance(hints, dict) or not hints:
        return None, default_fields

    best = None
    for hint_text, fields in hints.items():
        ht = str(hint_text or "").strip()
        if not ht:
            continue
        pos = text.find(ht)
        if pos < 0:
            continue
        fs = [str(x).strip() for x in (fields or []) if str(x).strip()]
        cand = {"hint": ht, "pos": pos, "fields": fs}
        if best is None or cand["pos"] < best["pos"]:
            best = cand

    if best:
        return best["hint"], (best["fields"] or default_fields)
    return None, default_fields


def _extract_key(text: str, alias: str, hint: str | None):
    s = text
    if alias:
        s = s.replace(alias, " ")
    if hint:
        s = s.replace(hint, " ")
    return " ".join(s.split()).strip()


def _last_year_range():
    y = date.today().year - 1
    return f"{y}-01-01", f"{y}-12-31"


def _this_year_range():
    y = date.today().year
    return f"{y}-01-01", f"{y}-12-31"


def _month_range(offset_months: int):
    """
    offset_months:
      0 = 本月
     -1 = 上個月
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    today = datetime.today()
    first = (today.replace(day=1) + relativedelta(months=offset_months)).date()
    next_first = (first + relativedelta(months=1))
    last = (next_first - relativedelta(days=1))
    return str(first), str(last)


def _semantic_build_query(intent: dict, cmd_text: str, menu_item: dict):
    """
    依 semanticRules(period/sort) + menu_item.view 決定 dataset
    回傳 queryJson + q(base64)
    """
    rules = intent.get("semanticRules") or {}
    period_words = rules.get("period") or []
    sort_map = (rules.get("sort") or {})

    dataset = (menu_item.get("view") or intent.get("aiView") or "").strip()
    if not dataset:
        # 沒有 view 就沒法跑語意列表
        return None

    date_field = (intent.get("dateField") or "日期").strip()
    select_fields = intent.get("defaultFields") or []
    limit = int(intent.get("limit") or 1000)

    filters = []
    # period
    if "去年" in cmd_text:
        d1, d2 = _last_year_range()
        filters.append({"field": date_field, "op": "between", "value": [d1, d2]})
    elif "今年" in cmd_text:
        d1, d2 = _this_year_range()
        filters.append({"field": date_field, "op": "between", "value": [d1, d2]})
    elif "上個月" in cmd_text:
        d1, d2 = _month_range(-1)
        filters.append({"field": date_field, "op": "between", "value": [d1, d2]})
    elif "本月" in cmd_text:
        d1, d2 = _month_range(0)
        filters.append({"field": date_field, "op": "between", "value": [d1, d2]})

    # sort
    sort = []
    # 你例句：「以客戶，日期排序」
    if "客戶" in cmd_text:
        sort.append({"field": sort_map.get("客戶", "客戶名稱"), "dir": "asc"})
    if "日期" in cmd_text:
        sort.append({"field": sort_map.get("日期", date_field), "dir": "asc"})
    if "金額" in cmd_text:
        sort.append({"field": sort_map.get("金額", "金額"), "dir": "desc"})

    if not sort:
        sort.append({"field": date_field, "dir": "desc"})

    query_json = {
        "dataset": dataset,
        "select": select_fields,
        "filters": filters,
        "sort": sort,
        "limit": limit
    }
    q = _utf8_b64_json(query_json)
    return query_json, q


def _resolve_menu_for_intent(intent: dict, allowed_vue_set: set, by_vue: dict):
    """
    SOP Step 1：先對應左側功能選單（權限）
    - route intent：用 intent.routeName -> secondRoles.vue
    - semantic intent：也必須找到對應的 vue（通常同 entity 的列表頁，例如 order_view）
      這裡我們採：
        intent.routeName 有就用
        沒有就嘗試用 entity 的 route intent（order.search 的 routeName）當容器頁
    """
    itype = (intent.get("type") or "").strip().lower()
    route_name = (intent.get("routeName") or "").strip()

    if itype == "route":
        if route_name and route_name in allowed_vue_set:
            return by_vue.get(route_name)
        return None

    if itype == "semantic":
        # 1) 若 semantic intent 自己有 routeName（你也可以在 JSON 補上），優先用
        if route_name and route_name in allowed_vue_set:
            return by_vue.get(route_name)

        # 2) 沒 routeName：用同 entity 的「查詢頁」當容器（例：order.search -> order_view）
        entity = (intent.get("entity") or "").strip()
        if not entity:
            return None

        # 找 registry 中 type=route 且 entity 相同的 intent
        for it in (REGISTRY.get("intents") or []):
            if (it.get("type") or "").strip().lower() != "route":
                continue
            if (it.get("entity") or "").strip() != entity:
                continue
            rn = (it.get("routeName") or "").strip()
            if rn and rn in allowed_vue_set:
                return by_vue.get(rn)

        return None

    return None


# ============================================================
# Main handler
# ============================================================
def register_ai_socket_handlers():
    @socketio.on("ai_command")
    def handle_ai_command(data):
        data = data or {}
        raw_text = (data.get("text") or "").strip()
        user_text = _norm_text(raw_text)
        sid = request.sid

        user_info = _get_user_info_by_sid(sid)
        if not user_info:
            emit("ai_response", {
                "action": "chat",
                "reply": "目前未登入或連線已失效，請重新登入後再試一次。"
            })
            return

        # SOP: 先建權限選單索引
        allowed_vue_set, by_vue, title_rows = _build_allowed_menu_index(user_info)

        if not user_text:
            emit("ai_response", {"action": "chat", "reply": "請說明你要做什麼（例如：客戶查詢 39001、列出去年訂單）。"})
            return

        # ====================================================
        # SOP Step 1 + Step 2：先用 registry match intent
        # ====================================================
        hit = _match_intent_by_registry(user_text)

        if not hit:
            # 沒 match registry -> 可選：再用「左側選單 title」做最後一次 match（保底）
            matched_menu = None
            for row in title_rows:
                if row["title"] and row["title"] in user_text:
                    matched_menu = row["item"]
                    break

            if matched_menu:
                # 有命中選單 title，但 registry 沒意圖：只做 navigate
                target_vue = (matched_menu.get("vue") or matched_menu.get("url") or "").strip()
                emit("ai_response", {
                    "action": "navigate",
                    "target": target_vue,
                    "reply": f"已切換至：{matched_menu.get('title')}",
                })
                return

            # SOP 無法判斷 -> fallback LLM（仍要限制只能回傳權限內 target）
            if _model:
                try:
                    available = []
                    for m in (user_info.get("menus") or []):
                        for c in (m.get("children") or []):
                            vue = (c.get("vue") or c.get("url") or "").strip()
                            if vue:
                                available.append(f"{c.get('title')}({vue})")

                    prompt = f"""
你是 ERP 助手。請從使用者可用功能中選擇最合適的 target。
只能在清單內選 target，否則 action=chat 說明無法操作。

可用功能：
{", ".join(available) if available else "無"}

使用者指令：
"{user_text}"

回傳 JSON:
{{"action":"navigate/chat","target":"(vue)","reply":"..."}}
""".strip()

                    resp = _model.generate_content(prompt)
                    clean = (resp.text or "").replace("```json", "").replace("```", "").strip()
                    ai_logic = json.loads(clean)

                    target = (ai_logic.get("target") or "").strip()
                    if ai_logic.get("action") == "navigate":
                        # 權限守門
                        if target not in allowed_vue_set:
                            emit("ai_response", {
                                "action": "chat",
                                "reply": "此功能不在你目前的權限選單內，無法操作。"
                            })
                            return

                    emit("ai_response", ai_logic)
                    return
                except Exception as e:
                    logger.error(f"❌ LLM fallback failed: {e}", exc_info=True)

            emit("ai_response", {
                "action": "chat",
                "reply": "我找不到對應的功能選單（請用：客戶查詢 / 訂單查詢 / 列出去年訂單…）。"
            })
            return

        intent = hit["intent"]
        matched_alias = hit["alias"]

        # ====================================================
        # SOP Step 1：必須先對應左側功能選單(權限) -> 找 secondRoles.vue / view
        # ====================================================
        menu_item = _resolve_menu_for_intent(intent, allowed_vue_set, by_vue)
        if not menu_item:
            # registry match 到了，但使用者沒權限
            emit("ai_response", {
                "action": "chat",
                "reply": "此指令對應的功能不在你目前的權限選單內，無法操作。"
            })
            return

        target_vue = (menu_item.get("vue") or menu_item.get("url") or "").strip()
        itype = (intent.get("type") or "").strip().lower()

        # ====================================================
        # SOP Step 3/4：route/semantic 分流
        # ====================================================
        if itype == "route":
            # route：照原本 parser SOP
            hint, fields = _match_hint(user_text, intent)
            key = _extract_key(user_text, matched_alias, hint)

            # 回傳給前端（可直接 router.push）
            emit("ai_response", {
                "action": "navigate",
                "target": target_vue,
                "reply": f"已開啟：{menu_item.get('title')}",
                "cmd": {
                    "type": "route",
                    "intent_key": intent.get("intent_key"),
                    "matched_alias": matched_alias,
                    "key": key,
                    "fields": fields,
                    "auto": True if intent.get("autoOpenOnSingle") else False
                },
                "query": {
                    "key": key,
                    "fields": ",".join(fields or []),
                    "auto": "1" if intent.get("autoOpenOnSingle") else "0",
                    "src": "ai",
                    "intent": intent.get("intent_key") or ""
                }
            })
            return

        if itype == "semantic":
            # semantic：一定要用 secondRoles.view（資料檢視表）+ semanticRules 組 q
            built = _semantic_build_query(intent, user_text, menu_item)
            if not built:
                emit("ai_response", {
                    "action": "chat",
                    "reply": "此功能缺少 view 設定（secondRoles.view 或 registry.aiView），無法產生列表查詢。"
                })
                return

            query_json, q = built
            emit("ai_response", {
                "action": "navigate",
                "target": target_vue,
                "reply": f"正在前往：{menu_item.get('title')}（已依語意產生列表條件）",
                "cmd": {
                    "type": "semantic",
                    "intent_key": intent.get("intent_key"),
                    "matched_alias": matched_alias,
                    "dataset": query_json.get("dataset"),
                    "queryJson": query_json
                },
                "query": {
                    "q": q,
                    "page": "1",
                    "pageSize": "50"
                }
            })
            return

        # 未知 type：保守處理
        emit("ai_response", {
            "action": "chat",
            "reply": "此指令的 intent.type 設定不正確（需為 route 或 semantic）。"
        })
