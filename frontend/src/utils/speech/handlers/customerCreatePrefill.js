// src/utils/speech/handlers/customerCreatePrefill.js
function parseCustomerCreate(text) {
  const t = String(text || '').trim()
  if (!t) return null
  if (!/新增\s*客戶/.test(t)) return null

  const ALL_KEYS = ['公司名稱', '名稱', '地址', '電話', 'tel', 'phone', '信用額度', '信用']
  const pick = (key) => {
    const stopKeys = ALL_KEYS.filter(k => k !== key).join('|')
    const re = new RegExp(
      `${key}\\s*[:：]?\\s*(.+?)(?=(${stopKeys})\\s*[:：]?|$)`,
      'i'
    )
    return (t.match(re)?.[1] || '').trim()
  }

  const company = pick('公司名稱') || pick('名稱')
  const address = pick('地址')
  const tel = pick('電話') || pick('tel') || pick('phone')
  const credit = pick('信用額度') || pick('信用')

  if (!company && !address && !tel && !credit) return null
  return { company, address, tel, credit }
}

export default {
  id: 'customerCreatePrefill',
  match(text) {
    const r = parseCustomerCreate(text)
    return r ? r : null
  },
  async run(text, ctx, m) {
    // 1) 開 customer_create（iframe）
    ctx.openPage?.('customer_create', '新增客戶')

    // 2) 準備 payload（一定要是純 JSON）
    const payload = {
      type: 'PREFILL_CUSTOMER_CREATE',
      data: {
        company: String(m.company || ''),
        address: String(m.address || ''),
        tel: String(m.tel || ''),
        credit: String(m.credit || ''),
      }
    }

    // 3) iframe ready 就送；不然暫存
    const ok = ctx.postToIframe?.(payload)
    if (!ok) ctx.setPending?.(payload)

    ctx.notify?.('success', '已開啟新增客戶並帶入資料')
  },
}
