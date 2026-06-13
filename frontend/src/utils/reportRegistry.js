export const COMMANDS = [
  { id:'alerts', title:'出貨提醒總覽（未出清/已出清/全部）', route:'/ai_alerts', keywords:['提醒','出貨提醒','未出清','已出清','全部'] },
  { id:'aging', title:'未出清 Aging 報表', route:'/rpt_aging', keywords:['aging','未出清','卡單','天數'] },
  { id:'fulfill', title:'出貨達成率（客戶/業務/公司別）', route:'/rpt_fulfill', keywords:['達成率','出貨率','完成率'] },
  { id:'top_customer', title:'出貨金額 Top 10 客戶', route:'/rpt_top_customers', keywords:['前10名','top10','客戶','出貨金額'] },
  { id:'top_product', title:'最暢銷產品 Top 10', route:'/rpt_top_products', keywords:['前10名','top10','產品','暢銷'] },
  { id:'sales_perf', title:'業務績效儀表板', route:'/rpt_sales_perf', keywords:['業務績效','績效','排行'] },
  { id:'ai_todo', title:'AI 今日優先處理清單', route:'/ai_todo', keywords:['今日','優先','待辦','建議','催單'] },
]

export function matchCommand(text) {
  const t = String(text || '').trim().toLowerCase()
  if (!t) return null

  // 1) 直接命中 title
  let hit = COMMANDS.find(c => c.title.toLowerCase().includes(t))
  if (hit) return hit

  // 2) 命中 keyword（任何一個）
  hit = COMMANDS.find(c => c.keywords.some(k => t.includes(String(k).toLowerCase())))
  if (hit) return hit

  // 3) 進階：取最高分（包含多關鍵字）
  let best = null
  let bestScore = 0
  for (const c of COMMANDS) {
    let score = 0
    for (const k of c.keywords) {
      if (t.includes(String(k).toLowerCase())) score += 1
    }
    if (score > bestScore) {
      bestScore = score
      best = c
    }
  }
  return bestScore > 0 ? best : null
}
