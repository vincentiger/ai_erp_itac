// src/utils/speech/handlers/customerSearch.js
function parseCustomerSearch(text) {
  const t = String(text || '').trim()
  if (!t) return null

  const m =
    t.match(/^客戶\s*查詢\s*(.+)$/) ||
    t.match(/^(查詢|搜尋)\s*客戶\s*(.+)$/)

  if (!m) return null
  const q = String(m[2] ?? m[1] ?? '').trim()
  return q ? q : null
}

export default {
  id: 'customerSearch',
  match(text) {
    const q = parseCustomerSearch(text)
    return q ? { q } : null          // ✅ 回傳 object，給 run 用
  },
  async run(text, ctx, match) {
    const keyword = String(match?.q || '').trim()
    if (!keyword) return

    // ✅ 走 iframe 方案：用 openPage / handleMenuClick (你測試過 OK)
    // 你想用 q 或 kw 都行，但要跟 customer_view.vue syncKwFromRoute 一致
    ctx.openPage?.('customer_view', '客戶查詢', { q: keyword })

    ctx.notify?.('success', `已前往客戶查詢：${keyword}`)
  },
}
