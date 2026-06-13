// src/utils/speech/handlers/navigationFallback.js
export default {
  id: 'fallback',
  match() {
    // 永遠命中（但放最後）
    return { ok: true }
  },
  async run(text, ctx) {
    // 把控制權交回去給你現有的 AI/socket 邏輯
    if (typeof ctx.fallback === 'function') {
      await ctx.fallback(text)
      return
    }
    ctx.notify?.('info', `未處理指令：${text}`)
  },
}
