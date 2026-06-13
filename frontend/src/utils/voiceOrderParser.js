// utils/voiceOrderParser.js (或放進 voiceEngine)
function pad2(n){ return String(n).padStart(2,'0') }
function fmtYMD(d){
  return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}`
}
function startOfMonth(d){ return new Date(d.getFullYear(), d.getMonth(), 1) }
function endOfMonth(d){ return new Date(d.getFullYear(), d.getMonth()+1, 0) }

function rangeOfLastYear(now){
  const y = now.getFullYear() - 1
  return { from: `${y}-01-01`, to: `${y}-12-31` }
}
function rangeOfThisYear(now){
  const y = now.getFullYear()
  return { from: `${y}-01-01`, to: `${y}-12-31` }
}
function rangeOfYear(y){
  return { from: `${y}-01-01`, to: `${y}-12-31` }
}
function rangeOfLastMonth(now){
  const d = new Date(now.getFullYear(), now.getMonth()-1, 1)
  return { from: fmtYMD(startOfMonth(d)), to: fmtYMD(endOfMonth(d)) }
}
function rangeOfThisMonth(now){
  return { from: fmtYMD(startOfMonth(now)), to: fmtYMD(endOfMonth(now)) }
}
function rangeOfLastNDays(now, n){
  const to = new Date(now)
  const from = new Date(now)
  from.setDate(from.getDate() - (n-1))
  return { from: fmtYMD(from), to: fmtYMD(to) }
}

// 抽取「客戶/公司/業務」關鍵字（最保守：只抓你句型中明確的）
function cleanName(s){
  s = String(s || '').trim()

  // 去掉常見尾巴詞
  s = s.replace(/(所有訂單|全部訂單|所有|全部|訂單|明細|資料|查詢|搜尋)/g, '')
  s = s.replace(/(去年|今年|本月|這個月|上月|上個月|近30天|最近30天|三十天內|截至目前|截至今天|到目前為止|至今)/g, '')
  s = s.replace(/\s+/g, '')

  // 只抓 2~4 個中文字（台灣姓名）
  const m = s.match(/[\u4e00-\u9fff]{2,4}/)
  return m ? m[0] : s
}

function extractEntities(text){
  let customer = ''
  let sales_rep = ''

  // 客戶A ...
  let m = text.match(/客戶\s*([^\s]+)\s*/i)
  if (m) customer = m[1]

  // 公司A ...
  m = text.match(/公司\s*([^\s]+)\s*/i)
  if (m) customer = customer || m[1]

  // ✅ 業務張三（清理尾巴）
  m = text.match(/業務(?:代表)?\s*([\u4e00-\u9fff]{2,4})/i)
  if (m) sales_rep = m[1]

  return { customer, sales_rep }
}

function rangeOfYearMonth(y, m) {
  // m: 1~12
  const d = new Date(y, m - 1, 1)
  const from = fmtYMD(d)
  const to = fmtYMD(endOfMonth(d))
  return { from, to }
}

function rangeFromYearMonthTo(now, y, m, untilToday) {
  const start = new Date(y, m - 1, 1)
  const from = fmtYMD(start)
  const to = untilToday ? fmtYMD(now) : fmtYMD(endOfMonth(start))
  return { from, to }
}


// 主解析：命中就回傳 cmd，沒命中回 null
export function parseOrderVoice(text, { currentUserName = '' } = {}){
  const t = String(text || '').trim()
  if (!t) return null

  // 必須包含「訂單」或「PI/SC」才視為訂單指令（避免誤判）
  const isOrder = /(訂單|PI|SC)/i.test(t)
  if (!isOrder) return null

  const now = new Date()

  // 狀態：尚未出清
  const wantOpen = /(尚未出清|未出清|未結案|未完成|未出貨|未關單)/.test(t)

  // Top10：金額排名前十
  const wantTop10 = /(金額排名前十|金額前十|前十訂單|Top\s*10)/i.test(t)

  // 今年截至目前為止（to=today）
  const untilToday = /(截至目前|截至今天|到目前為止|至今)/.test(t)

  // 抽客戶/公司/業務
  let { customer, sales_rep } = extractEntities(t)

  // 「我」= 當前使用者業務
  if (/^我/.test(t) || /我(的)?/.test(t)) {
    if (currentUserName) sales_rep = currentUserName
  }

  // 日期範圍判斷（依你列的優先順序）
  // 日期範圍判斷
  let from = '', to = ''
  // ✅ 先抓「年月」(2025年8月 / 2025-08 / 2025/08 / 8月)
  const ym1 = t.match(/(19\d{2}|20\d{2})\s*年\s*(0?[1-9]|1[0-2])\s*月/)
  const ym2 = t.match(/(19\d{2}|20\d{2})[-\/](0?[1-9]|1[0-2])/)
  const mOnly = t.match(/(^|[^\d])(0?[1-9]|1[0-2])\s*月/)

  // ✅ 支援「去年8月」「今年8月」「上月」「本月」等
  const hasLastYear = /去年/.test(t)
  const hasThisYear = /今年/.test(t)

  if (ym1 || ym2) {
    const y = Number((ym1 ? ym1[1] : ym2[1]))
    const m = Number((ym1 ? ym1[2] : ym2[2]))
    // 2025年8月至今
    const r = rangeFromYearMonthTo(now, y, m, untilToday)
    from = r.from
    to = r.to

  } else if ((hasLastYear || hasThisYear) && mOnly) {
    const m = Number(mOnly[2])
    const y = hasLastYear ? (now.getFullYear() - 1) : now.getFullYear()
    // 去年8月至今 / 今年8月至今
    const r = rangeFromYearMonthTo(now, y, m, untilToday)
    from = r.from
    to = r.to

  } else {
    // ✅ 年份（整年）
    const yearM = t.match(/(19\d{2}|20\d{2})\s*年/)
    if (yearM) {
      const y = Number(yearM[1])
      const r = rangeOfYear(y)
      from = r.from
      to = untilToday ? fmtYMD(now) : r.to

    } else if (hasLastYear) {
      // 去年（整年）— 但若有 untilToday，代表「去年至今」= 去年 1/1 到今天
      const y = now.getFullYear() - 1
      from = `${y}-01-01`
      to = untilToday ? fmtYMD(now) : `${y}-12-31`

    } else if (hasThisYear) {
      const y = now.getFullYear()
      from = `${y}-01-01`
      to = untilToday ? fmtYMD(now) : `${y}-12-31`

    } else if (/(上個月|上月)/.test(t)) {
      const r = rangeOfLastMonth(now)
      from = r.from
      to = untilToday ? fmtYMD(now) : r.to

    } else if (/(本月|這個月)/.test(t)) {
      const r = rangeOfThisMonth(now)
      from = r.from
      to = untilToday ? fmtYMD(now) : r.to

    } else if (/(近30天|最近30天|三十天內)/.test(t)) {
      const r = rangeOfLastNDays(now, 30)
      from = r.from
      to = r.to

    } else {
      return null
    }
  }

  const filters = {
    date_from: from,
    date_to: to,
    customer: customer || '',
    company_title: '',           // 你若要分開再補規則
    sales_rep: sales_rep || '',
    status: wantOpen ? 'open' : '',
    top_n: wantTop10 ? 10 : null,
    sortBy: wantTop10 ? 'amount' : '',  // Top10預設金額排序
    sortDir: wantTop10 ? 'desc' : '',
  }

  return {
    routeName: 'order_view',
    intent_key: 'order_search',
    intent_label: '訂單查詢',
    filters
  }
}
