/**
 * src/voice/index.js
 * ------------------------------------------------------------
 * Voice Engine – Single entry for all voice / AI command parsing.
 *
 * - Generic, registry-driven parser (NO hard-coded customer/supplier logic)
 * - One parser only; capabilities come from voice-registry.json
 * - Future-ready for LLM fallback (Gemini / ChatGPT)
 *
 * Usage:
 *   import { createVoiceEngine } from '@/voice'
 *   import registry from '@/voice/voice-registry.json'
 *
 *   const engine = createVoiceEngine(registry)
 *   const cmd = engine.parse('請找出客戶 地址 仁愛路')
 *   if (cmd) engine.execute(cmd, { router })
 */

// ============================================================
// internal helpers
// ============================================================
const _normText = (s) =>
  String(s ?? '').replace(/\s+/g, ' ').trim()

const _toArray = (v) =>
  Array.isArray(v) ? v : (v ? [v] : [])

const _safeStr = (v) =>
  String(v ?? '').trim()

// ============================================================
// build registry index (optimize matching)
// ============================================================
function buildRegistryIndex(registry) {
  const intents = _toArray(registry?.intents).filter(Boolean)

  const aliasRows = []
  for (const intent of intents) {
    const aliases = _toArray(intent.intent_aliases)
      .map(_safeStr)
      .filter(Boolean)

    for (const alias of aliases) {
      aliasRows.push({ intent, alias })
    }
  }

  // longest alias first (for "最長命中")
  aliasRows.sort((a, b) => b.alias.length - a.alias.length)

  return { intents, aliasRows }
}

// ============================================================
// matching steps
// ============================================================
function matchIntent(text, index) {
  let best = null

  for (const row of index.aliasRows) {
    const pos = text.indexOf(row.alias)
    if (pos === -1) continue

    const cand = {
      intent: row.intent,
      alias: row.alias,
      pos,
      len: row.alias.length
    }

    if (
      !best ||
      cand.len > best.len ||
      (cand.len === best.len && cand.pos < best.pos)
    ) {
      best = cand
    }
  }

  return best
}

function matchHint(text, intent) {
  const defaultFields = _toArray(intent?.defaultFields)
    .map(_safeStr)
    .filter(Boolean)

  const hints = intent?.hints && typeof intent.hints === 'object'
    ? intent.hints
    : null

  if (!hints) return { hint: null, fields: defaultFields }

  let best = null
  for (const hintText of Object.keys(hints)) {
    const h = _safeStr(hintText)
    if (!h) continue

    const pos = text.indexOf(h)
    if (pos === -1) continue

    const fields = _toArray(hints[hintText])
      .map(_safeStr)
      .filter(Boolean)

    const cand = { hint: h, pos, fields }
    if (!best || cand.pos < best.pos) best = cand
  }

  if (best) {
    return {
      hint: best.hint,
      fields: best.fields.length ? best.fields : defaultFields
    }
  }

  return { hint: null, fields: defaultFields }
}

function extractKey(text, alias, hint) {
  let s = text
  if (alias) s = s.replace(alias, ' ')
  if (hint) s = s.replace(hint, ' ')
  return s.replace(/\s+/g, ' ').trim()
}

// ============================================================
// public API
// ============================================================
export function createVoiceEngine(registry) {
  const index = buildRegistryIndex(registry)

  function parse(rawText, opts = {}) {
    const text = _normText(rawText)
    if (!text) return null

    const hit = matchIntent(text, index)
    if (!hit) return null

    const intent = hit.intent
    const { hint, fields } = matchHint(text, intent)
    const key = extractKey(text, hit.alias, hint)

    const confidence =
      hit.len >= 4 ? 0.92 :
      hit.len >= 2 ? 0.85 : 0.75

    return {
      source: opts.source || 'voice',
      rawText: text,

      // intent identity
      intent_key: _safeStr(intent.intent_key),
      intent_label: _safeStr(intent.intent_label || hit.alias),
      matched_alias: hit.alias,

      // navigation / entity
      entity: _safeStr(intent.entity),
      routeName: _safeStr(intent.routeName),
      aiView: _safeStr(intent.aiView),
      pkField: _safeStr(intent.pkField),

      // query
      key,
      fields,
      auto: intent.autoOpenOnSingle ? '1' : '0',
      src: opts.src || 'voice',

      // meta for UI / trace
      meta: {
        hint,
        aliasPos: hit.pos,
        confidence
      }
    }
  }

  function executeToIframe(cmd, { setCurrentUrl, base = '' } = {}) {
    if (!cmd || !setCurrentUrl) return false

    // 1) registry 可直接給一個 iframeUrl（最乾淨）
    // 2) 沒有就用 routeName 轉成 /xxx (你目前 children.url = customer_view)
    const path = cmd.iframeUrl
      ? String(cmd.iframeUrl)
      : `/${String(cmd.routeName || '').replace(/^\/+/, '')}`

    const u = new URL(base + path, window.location.origin)

    // 把 query 帶給 iframe 頁（你 customer_view 可以讀 query）
    if (cmd.key) u.searchParams.set('key', cmd.key)
    if (cmd.fields?.length) u.searchParams.set('fields', cmd.fields.join(','))
    if (cmd.auto != null) u.searchParams.set('auto', String(cmd.auto))
    if (cmd.src) u.searchParams.set('src', String(cmd.src))
    if (cmd.intent_key) u.searchParams.set('intent', String(cmd.intent_key))

    setCurrentUrl(u.pathname + u.search)
    return true
  }

  function execute(cmd, { router } = {}) {
    if (!cmd || !router || !cmd.routeName) return false

    const query = {
      ...(cmd.key ? { key: cmd.key } : {}),
      fields: (cmd.fields || []).join(','),
      auto: String(cmd.auto ?? '0'),
      src: cmd.src || 'voice',
      intent: cmd.intent_key || undefined
    }

    router.push({ name: cmd.routeName, query })
    return true
  }

  return {
    parse,
    execute,         // 保留給 router
    executeToIframe, // ✅ 新增給舊 UI
    registry: index.intents
  }
}


/**
 * Example registry JSON shape:
 * {
 *   "version": 1,
 *   "intents": [
 *     {
 *       "intent_key": "customer.search",
 *       "intent_aliases": ["查詢客戶","客戶查詢","搜尋客戶","請找出客戶"],
 *       "entity": "customer",
 *       "routeName": "customer_view",
 *       "aiView": "ai_customers",
 *       "pkField": "refno",
 *       "defaultFields": ["refno","company","short"],
 *       "hints": { "地址":["address"], "電話":["tel"], "聯絡人":["contact"] },
 *       "autoOpenOnSingle": true
 *     }
 *   ]
 * }
 */
