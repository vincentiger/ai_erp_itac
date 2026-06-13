// src/utils/speech/router.js
export function createSpeechRouter(handlers = []) {
  const list = [...handlers]

  function register(handler) {
    if (!handler?.id) throw new Error('handler requires id')
    list.push(handler)
  }

  function normalizeText(text) {
    return String(text || '')
      .trim()
      .replace(/\s+/g, ' ')
  }

  async function handle(rawText, ctx = {}) {
    const text = normalizeText(rawText)
    if (!text) return { handled: false }

    for (const h of list) {
      try {
        const m = await h.match?.(text, ctx)
        if (!m) continue
        await h.run?.(text, ctx, m)
        return { handled: true, handler: h.id }
      } catch (e) {
        console.error(`[speech] handler error: ${h?.id}`, e)
        // 不中斷整體（但避免吞掉錯誤）
        ctx?.notify?.('error', `語音指令錯誤：${h?.id}`)
        return { handled: true, handler: h?.id, error: String(e?.message || e) }
      }
    }

    return { handled: false }
  }

  return { register, handle }
}
