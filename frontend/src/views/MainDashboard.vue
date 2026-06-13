
<script setup>
import { ref, onMounted, onUnmounted, nextTick,computed, watch } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useRouter } from 'vue-router'
import { onlineUsers, rtConnected, startUserListWatch, stopUserListWatch, clearSessionId } from '@/utils/rt'


import '@/assets/css/dashboard.css'
import '@/assets/css/dashboard-view.css'
import { useAiSpeech } from '@/utils/useAiSpeech.js'

import { useLongSpeechInput } from '@/utils/useLongSpeechInput.js'
import { ArrowLeftBold, Expand } from '@element-plus/icons-vue'
import { createVoiceEngine } from '@/voice'
import voiceRegistry from '@/voice/voice-registry.json'
import { parseOrderVoice } from '@/utils/voiceOrderParser'
import { ensureSession } from '@/utils/rt'
import { h } from 'vue'
const voiceEngine = createVoiceEngine(voiceRegistry)


const router = useRouter()
const isMobileMenuOpen = ref(false)

function readCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
}

const currentUser = ref(readCurrentUser() || { name: '未登入', menus: [] })
const selectedUser = ref('')
const currentContext = ref('通用模式')
const kbDialogVisible = ref(false)
const kbAnswerTitle = ref('')
const kbAnswerCategory = ref('')
const kbAnswerBody = ref('')
const kbAnswerSources = ref([])

// ========= Logout（先宣告，避免時序問題）=========
const handleLogout = () => {
  localStorage.clear()
  clearSessionId()
  stopUserListWatch()
  router.push('/login')
}
// ========= 長語音（覆蓋輸入框）=========
const {
  isRecording,
  isTranscribing,
  draftText,
  error: speechError,
  toggle: toggleLongVoice,
  clearDraft,
  stopAndCommit,
} = useLongSpeechInput({ lang: 'zh-TW' })

const isUploadingVoice = ref(false)

const COMMIT_WORDS = ['開始', 'go', 'ok', 'okay', '送出', '執行']

function normalizeVoiceText(s) {
  return String(s || '').trim()
}

const COMMANDS = [
  {
    id:'alerts',
    intent:'alert',
    priority:1,
    cat:'提醒',
    title:'出貨提醒總覽（未出清/已出清/全部）',
    desc:'未出清清單、卡單提醒、異常檢查',
    route:'/ai_alerts',
    keywords:['提醒','出貨提醒','未出清','已出清','全部'],
    voice:{ verbs:['看','查','顯示','打開'], nouns:['出貨提醒','未出清','已出清'] }
  },

  {
    id:'aging',
    intent:'report',
    priority:2,
    cat:'報表',
    title:'未出清 Aging 報表',
    desc:'0-7/8-30/31-90/>90 天分桶',
    route:'/rpt_aging',
    keywords:['aging','未出清','卡單','天數','分桶'],
    voice:{ verbs:['看','查','顯示'], nouns:['aging','未出清','天數','分桶'] }
  },

  {
    id:'fulfill',
    intent:'report',
    priority:2,
    cat:'報表',
    title:'出貨達成率（客戶/業務/公司別）',
    desc:'ship_amount_cached / order_amount',
    route:'/rpt_fulfill',
    keywords:['達成率','出貨率','完成率','客戶','業務'],
    voice:{ verbs:['看','查','顯示'], nouns:['達成率','出貨率','完成率'] }
  },

  {
    id:'top_customer',
    intent:'report',
    priority:3,
    cat:'報表',
    title:'出貨金額 Top 10 客戶',
    desc:'Top customers by ship amount',
    route:'/rpt_top_customers',
    keywords:['top10','前10名','客戶','出貨金額'],
    voice:{ verbs:['看','查','顯示'], nouns:['top10','前10名','客戶','出貨金額'] }
  },

  {
    id:'top_product',
    intent:'report',
    priority:3,
    cat:'報表',
    title:'最暢銷產品 Top 10',
    desc:'Top products by ship qty/amount',
    route:'/rpt_top_products',
    keywords:['top10','前10名','產品','暢銷'],
    voice:{ verbs:['看','查','顯示'], nouns:['top10','前10名','產品','暢銷'] }
  },

  {
    id:'sales_perf',
    intent:'report',
    priority:2,
    cat:'報表',
    title:'業務績效儀表板',
    desc:'接單/出貨/未出清/平均出貨天數',
    route:'/rpt_sales_perf',
    keywords:['業務績效','績效','業務','排行'],
    voice:{ verbs:['看','查','顯示'], nouns:['業務績效','績效','排行'] }
  },

  {
    id:'ai_todo',
    intent:'suggest',
    priority:1,
    cat:'建議',
    title:'AI 今日優先處理清單',
    desc:'未出清金額 × 卡單天數排序',
    route:'/ai_todo',
    keywords:['建議','優先','今日','待辦','催單'],
    voice:{ verbs:['今天','幫我','列出','顯示'], nouns:['待辦','優先','催單'] }
  },
]

const cmdOpen = ref(false)
const cmdKw = ref('')

const filteredCommands = computed(() => {
  const kw = (cmdKw.value || '').trim().toLowerCase()
  if (!kw) return COMMANDS
  return COMMANDS.filter(c => {
    const hay = (c.title + ' ' + c.desc + ' ' + c.keywords.join(' ')).toLowerCase()
    return hay.includes(kw)
  })
})

function openCmd() {
  cmdOpen.value = true
  nextTick(() => { /* 可在這裡 focus input */ })
}

function goCmd(c) {
  const href = router.resolve(c.route).href
  window.open(href, '_blank', 'noopener')
}
function openFirst() {
  if (!filteredCommands.value.length) return ElMessage.warning('找不到符合的項目')
  goCmd(filteredCommands.value[0])
}
function onVoiceText(text) {
  const cmd = matchCommand(text)
  if (cmd) {
    router.push(cmd.route)         // ✅ 自動開新頁
    return true
  }
  return false
}
// 允許：
// 1) 結尾："... 客戶查詢 39001 開始"
// 2) 開頭："開始 客戶查詢 39001"
// 3) 單獨："OK"（只表示送出目前 draft）
function stripCommitWord(text) {
  let t = normalizeVoiceText(text)
  if (!t) return ''

  // 去掉結尾觸發詞（就算黏在一起也會被砍掉）
  t = t.replace(/(開始|送出|執行|go|ok|okay|ＯＫ)\s*[.。!！?？]*\s*$/i, '').trim()

  // 去掉開頭觸發詞（就算黏在一起也會被砍掉）
  t = t.replace(/^\s*(開始|送出|執行|go|ok|okay|ＯＫ)\s*/i, '').trim()

  return t
}
// ✅ 給「任意文字」做提交判斷（不要只看 draftText）
async function commitVoiceTextIfNeeded(t) {
  const raw = String(t || '').trim()
  if (!raw) return false

  // ✅ 觸發詞：開始 / go / ok（你原本的規則）
  const hasTrigger = /(開始|go|ok)$/i.test(raw) || /(開始|go|ok)\b/i.test(raw)
  if (!hasTrigger) return false

  // ✅ 去掉觸發詞
  let text = raw.replace(/(開始|go|ok)\s*$/i, '').trim()

  // ✅ 情境：客戶查詢（可依你系統的口令調整）
  // 例： "客戶查詢 39001" / "查詢客戶 39001" / "39001"
  const m =
    text.match(/(?:客戶查詢|查詢客戶|搜尋客戶)\s*([0-9A-Za-z\-]+)/) ||
    text.match(/^([0-9A-Za-z\-]+)$/)

  if (!m) {
    // 找不到可用關鍵字，就當作一般「送出 AI input」也可以
    // 但你若目前只做客戶查詢，就 return false 讓它回到 aiInput
    return false
  }

  const k = m[1].trim()
  if (!k) return false

  // ✅ 這裡才是真正執行「語音搜尋」
  console.log('[VOICE_COMMIT] customer search =>', k)

  kw.value = k
  page.value = 1
  reload()

  return true
}

function hasCommitWord(text) {
  const t = normalizeVoiceText(text)
  if (!t) return false

  // 開頭：開始xxx / OKxxx / GOxxx
  if (/^\s*(開始|送出|執行|go|ok|okay|ＯＫ)/i.test(t)) return true

  // 結尾：xxx開始 / xxxgo / xxxok / xxxokay  （允許後面有標點）
  if (/(開始|送出|執行|go|ok|okay|ＯＫ)\s*[.。!！?？]*\s*$/i.test(t)) return true

  return false
}



// ========= 跳頁 =========
// ========= 跳頁 =========
const currentUrl = ref('')

const routeMap = {
  lab: '/lab',
  labview: '/lab/view',
  lab_view: '/lab/view',
  lab_quote_manage: '/lab/quote/manage',
  labquotemanage: '/lab/quote/manage',
  quote_manage: '/lab/quote/manage',
  inspectvalues: '/lab/qet',
  lab_qet: '/lab/qet',
  qet1501view: '/lab/qet',
  inspectstandard: '/lab/qet/standard',
  lab_qet_standard: '/lab/qet/standard',
  qet_standard: '/lab/qet/standard',
  lab_qet_judge: '/lab/qet/judge',
  labqetjudge: '/lab/qet/judge',
  qet_judge: '/lab/qet/judge',
  lab_qet_manage: '/lab/qet/manage',
  labqetmanage: '/lab/qet/manage',
  qet_manage: '/lab/qet/manage',
  lab_qet_results: '/lab/qet/results',
  labqetresults: '/lab/qet/results',
  qet_results: '/lab/qet/results',
  labmech: '/lab/mech',
  lab_mech: '/lab/mech',
  lab_mech_standard: '/lab/mech/standard',
  labmechstandard: '/lab/mech/standard',
  mech_standard: '/lab/mech/standard',
  lab_mech_judge: '/lab/mech/judge',
  labmechjudge: '/lab/mech/judge',
  mech_judge: '/lab/mech/judge',
  lab_mech_results: '/lab/mech/results',
  labmechresults: '/lab/mech/results',
  mech_results: '/lab/mech/results',
  lab_mech_manage: '/lab/mech/manage',
  labmechmanage: '/lab/mech/manage',
  mech_manage: '/lab/mech/manage',
  customer_edit: '/customer_edit',
  customer_del: '/customer_del',
}

const menuTitleRouteMap = {
  委託測試單列表: '/lab/view',
  委託測試單查詢: '/lab/view',
  新增委託測試單: '/lab',
  設定機械性質檢驗記錄表: '/lab/mech/standard',
}

const handleMenuClick = (targetName, title = null) => {
  const normalizeVueKey = (p) => {
    if (!p) return ''
    let s = String(p).trim()

    // 移除 query/hash
    s = s.split('?')[0].split('#')[0]

    // 去前後斜線
    s = s.replace(/^\/+|\/+$/g, '')

    // 去 .vue
    s = s.replace(/\.vue$/i, '')

    // dbo.xxx 或 any.prefix.xxx → 取最後一段
    if (s.includes('.')) s = s.split('.').pop()

    // 轉小寫
    return s.toLowerCase().trim()
  }

  const key = normalizeVueKey(targetName)
  const titleKey = String(title || '').trim()
  const routePath = menuTitleRouteMap[titleKey] || routeMap[key] || (key ? `/${key}` : '')
  if (!routePath) {
    console.warn('[menu] 找不到對應頁面:', { targetName, title })
    return
  }

  const APP_BASE = import.meta.env.BASE_URL || '/ai/'
  const ORIGIN = window.location.origin
  const formattedBase = APP_BASE.endsWith('/') ? APP_BASE : `${APP_BASE}/`

  currentUrl.value = `${ORIGIN}${formattedBase}#${routePath}`

  console.log('導航至 URL:', currentUrl.value)

  if (title) {
    currentContext.value = title
    localStorage.setItem('currentContext', title)
  }

  if (typeof isMobileMenuOpen !== 'undefined') {
    isMobileMenuOpen.value = false
  }
}

// ========= AI 導航（你原本的匹配邏輯放這裡）=========
const handleNavigation = (targetName) => {
  console.log("🚀 AI 請求導航至:", targetName)
  // ...你原本的匹配與跳頁邏輯...
}

const { aiInput, isAiListening, aiSpeechStatus, toggleAiVoice } = useAiSpeech(handleNavigation)
async function commitVoiceIfNeeded() {
  const t = draftText.value || ''
  if (!t) return false
  if (!hasCommitWord(t)) return false

  // 去掉「開始/GO/OK」後的真正文句
  const cleaned = stripCommitWord(t)
  if (!cleaned) return false

  // 1) 把清理後文字放入輸入框
  aiInput.value = cleaned

  // 2) 清掉 draft（避免重複送）
  clearDraft?.()

  // 3) 直接等同按「AI 系統解析」
  await handleAiSubmit()
  return true
}

async function uploadVoiceToInput() {
  console.log('[uploadVoiceToInput] CLICK') // ✅ 一定要先看到這行

  if (isUploadingVoice.value) {
    console.log('[uploadVoiceToInput] blocked: isUploadingVoice')
    return
  }

  isUploadingVoice.value = true

  let t = ''
  try {
    console.log('[uploadVoiceToInput] calling stopAndCommit...')
    t = await stopAndCommit()
    console.log('[uploadVoiceToInput] stopAndCommit returned:', t)

    if (!t) {
      console.log('[uploadVoiceToInput] empty transcript -> return')
      return
    }

    // ✅ 先判斷是否含「開始/GO/OK」→ 直接送出
    const committed = await commitVoiceTextIfNeeded(t)
    console.log('[uploadVoiceToInput] commitVoiceTextIfNeeded =>', committed)

    if (committed) return

    // ✅ 沒觸發詞：只放入輸入框（維持原本行為）
    aiInput.value = String(t).trim()
    clearDraft?.()
    console.log('[uploadVoiceToInput] set aiInput=', aiInput.value)
  } catch (e) {
    console.error('[uploadVoiceToInput] ERROR:', e)
  } finally {
    isUploadingVoice.value = false
    console.log('[uploadVoiceToInput] FINALLY draftText=', draftText.value)
  }
}

// ========= iframe 通訊 =========
const iframeRef = ref(null)
const pendingIframeMessage = ref(null)

// ✅ 把 payload 轉成「可 postMessage」的純資料（避免 DataCloneError）
function toPostable(payload) {
  // 1) 優先 structuredClone（可保留更多型別；但遇到 function/proxy 一樣會丟）
  try {
    return structuredClone(payload)
  } catch {}

  // 2) fallback：JSON（最保險，會剝掉 proxy/ref/func）
  try {
    return JSON.parse(JSON.stringify(payload))
  } catch (e) {
    console.error('[postMessage] payload not clonable:', payload, e)
    return null
  }
}

function postToIframe(payload) {
  const iframe = iframeRef.value
  if (!iframe?.contentWindow) return false

  const plain = toPostable(payload)
  if (!plain) return false

  iframe.contentWindow.postMessage(plain, window.location.origin)
  return true
}

function onIframeLoad() {
  if (!pendingIframeMessage.value) return
  postToIframe(pendingIframeMessage.value)
  pendingIframeMessage.value = null
}

// ✅ Dashboard 只接 iframe 回來的訊息（不要碰 form）
function onMessage(e) {
  if (e.origin !== window.location.origin) return
  const msg = e.data
  if (!msg || !msg.type) return

  if (msg.type === 'CUSTOMER_CREATE_SAVED') {
    const refno = msg.data?.refno || ''
    ElNotification({
      title: '已儲存',
      message: refno ? `客戶代號：${refno}` : '已儲存成功',
      type: 'success'
    })
    return
  }
}

const handleMainButtonClick = () => {
  // 功能頁：優先返回 iframe 內上一頁，沒有上一頁才關閉 iframe
  if (currentUrl.value) {
    try {
      const iframeWindow = iframeRef.value?.contentWindow
      if (iframeWindow && iframeWindow.history.length > 1) {
        iframeWindow.history.back()
        return
      }
    } catch (e) {
      console.warn('[dashboard] iframe history back failed', e)
    }

    currentUrl.value = ''
    currentContext.value = '通用模式'
    isMobileMenuOpen.value = false
    return
  }

  // 首頁：切換手機側欄
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}


// ========= 本地解析（新增客戶+帶入）=========
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


  return {
    target: 'customer_create',
    data: { company, address, tel, credit },
  }
}

// ========= 小工具：安全拿 JSON（避免 <!doctype html> 造成 JSON.parse 爆炸） =========
async function safeFetchJson(url, options) {
  const resp = await fetch(url, options)
  const ct = resp.headers.get('content-type') || ''
  const text = await resp.text()

  if (!ct.includes('application/json')) {
    // 你之前的 <!doctype html> 就是這種情況
    throw new Error(`[safeFetchJson] not JSON. url=${url} status=${resp.status} ct=${ct} body=${text.slice(0,200)}`)
  }

  let json
  try {
    json = JSON.parse(text)
  } catch (e) {
    throw new Error(`[safeFetchJson] JSON parse fail. url=${url} status=${resp.status} body=${text.slice(0,200)}`)
  }

  if (!resp.ok || json?.ok === false) {
    throw new Error(json?.msg || `HTTP ${resp.status}`)
  }

  return json
}

function openKnowledgeAnswer(result) {
  kbAnswerTitle.value = String(result?.title || '知識庫回覆')
  kbAnswerCategory.value = String(result?.category || '')
  kbAnswerBody.value = String(result?.answer || '')
  kbAnswerSources.value = Array.isArray(result?.sources) ? result.sources : []
  kbDialogVisible.value = true
}

// ========= AI 系統解析 =========
const handleAiSubmit = async () => {
  const text = aiInput.value.trim()
  if (!text) return

  // ✅ 先查本機知識庫，查到就直接顯示答案
  try {
    const kbPayload = await safeFetchJson('/api/knowledge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    })
    if (kbPayload?.data?.hit) {
      openKnowledgeAnswer(kbPayload.data)
      return
    }
  } catch (e) {
    console.warn('[handleAiSubmit] knowledge lookup failed, continue:', e)
  }

  // ✅ 先本地解析：新增客戶（名稱/地址）
  const local = parseCustomerCreate(text)
  if (local) {
    handleMenuClick(local.target)

    const payload = {
      type: 'PREFILL_CUSTOMER_CREATE',
      data: {
        company: String(local.data.company || ''),
        address: String(local.data.address || ''),
        tel: String(local.data.tel || ''),
        credit: String(local.data.credit || ''),
      }
    }

    if (!postToIframe(payload)) pendingIframeMessage.value = payload

    ElNotification({
      title: 'AI 智能引導',
      message: '已開啟新增客戶並帶入名稱/地址',
      type: 'success'
    })
    return
  }

  // ✅✅✅ Voice SOP（查詢/導頁） → iframe
  const cmd =
    parseOrderVoice(text, { currentUserName: currentUser.value?.name }) ||
    voiceEngine.parse(text, { src: 'voice' })

  if (cmd?.routeName) {
    const routeName = String(cmd.routeName || '').trim()

    // ✅ A) customer_view / order_view 都用 URL query（最穩，不怕 postMessage 時序）
    if (routeName === 'customer_view') {
      const qs = new URLSearchParams()
      if (cmd.key) qs.set('key', String(cmd.key))
      if (Array.isArray(cmd.fields) && cmd.fields.length) qs.set('fields', cmd.fields.map(String).join(','))
      qs.set('auto', String(cmd.auto ?? '0'))
      currentUrl.value = `/customer_view?${qs.toString()}`
    }
    else if (routeName === 'order_view') {
      // ✅ order_view 我們改成用 filters 直接帶 querystring
      // order_view onMounted 也能讀 query（你若還沒加，我也給你版本）
      const qs = new URLSearchParams()
      const f = (cmd.filters && typeof cmd.filters === 'object') ? cmd.filters : {}

      // 允許你 voiceOrderParser 丟任何一種 key，這裡做相容轉換
      if (f.kw) qs.set('kw', String(f.kw))
      if (f.cust_name) qs.set('cust_name', String(f.cust_name))
      if (f.sales_rep) qs.set('sales_rep', String(f.sales_rep))
      if (f.company_title) qs.set('company_title', String(f.company_title))
      if (f.date_from) qs.set('date_from', String(f.date_from))
      if (f.date_to) qs.set('date_to', String(f.date_to))
      if (f.unshipped != null) qs.set('unshipped', String(f.unshipped)) // 你之後可用

      // 排序也可以一起帶（可選）
      if (cmd.sortBy) qs.set('sortBy', String(cmd.sortBy))
      if (cmd.sortDir) qs.set('sortDir', String(cmd.sortDir))

      currentUrl.value = `/order_view?${qs.toString()}`
    }
    else {
      // ✅ 其他頁仍用既有 handleMenuClick
      handleMenuClick(routeName)
    }

    // ✅ B) 備援：postMessage（iframe ready 就吃；沒吃也沒關係）
    const payload = {
      type: 'VOICE_SEARCH',
      data: {
        filters: cmd.filters || null,
        intent: cmd.intent_key || '',
        key: String(cmd.key || ''),
        fields: Array.isArray(cmd.fields) ? cmd.fields.map(String) : [],
        auto: String(cmd.auto ?? '0'),
        src: String(cmd.src || 'voice'),
      }
    }
    if (!postToIframe(payload)) pendingIframeMessage.value = payload

    ElNotification({
      title: 'AI 智能引導',
      message: cmd.key ? `已開啟 ${cmd.intent_label}：${cmd.key}` : `已開啟 ${cmd.intent_label}`,
      type: 'success'
    })
    return
  }

  // ✅✅✅【AI 解析】本地規則沒命中才交給 AI（避免亂跑）
  try {
    const payload = await safeFetchJson('/api/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    })

    const r = payload?.data || payload
    const action = String(r?.action || '')
    const target = String(r?.target || '')

    // 兼容 action: "navigate/chat" 或 "navigate"
    if (r && action.startsWith('navigate') && target) {
      // 1) 先開頁
      handleMenuClick(target)

      // 2) 有 filters 就送進 iframe（order_view / customer_view 都能吃）
      if (r?.filters && typeof r.filters === 'object') {
        const msg = { type: 'VOICE_SEARCH', data: { filters: r.filters } }
        if (!postToIframe(msg)) pendingIframeMessage.value = msg
      }

      // 3) 回覆提示
      ElNotification({
        title: 'AI 智能引導',
        message: String(r?.reply || `已開啟 ${target}`),
        type: 'success'
      })
      return
    }

    // ✅ AI 有回，但不是 navigate：就走 socket（例如聊天）
    console.log('[handleAiSubmit] ai parse returned non-navigate:', r)

  } catch (e) {
    // ✅ 這裡會把 HTML 404/500 的 body 前 200 字印出來，讓你立刻定位 proxy/route 問題
    console.warn('[handleAiSubmit] ai parse failed, fallback to socket:', e)
  }

  // ✅ fallback：走 socket（你原本的流程）
  const currentCtx = localStorage.getItem('currentContext') || '通用模式'
  socket.emit('ai_command', { text, user: currentUser.value.name, context: currentCtx })
}

async function stopAndCommitThenMaybeSubmit() {
  const t = await stopAndCommit()
  if (!t) return
  // 有「開始/go/ok」就直接提交，沒有就塞到 input
  const committed = await commitVoiceTextIfNeeded(t)
  if (!committed) {
    aiInput.value = String(t).trim()
    clearDraft?.()
  }
}
watch(draftText, async (v) => {
  // 避免錄音中/轉文字中就觸發
  if (isRecording.value || isTranscribing.value) return
  if (!v) return

  // ✅ draftText 一更新就檢查（例如你停止錄音後）
  await commitVoiceTextIfNeeded(v)
})

// ========= 生命週期：只留一組 onMounted/onUnmounted =========
onMounted(async () => {
  window.addEventListener('message', onMessage)

  try {
    currentUser.value = readCurrentUser()
  } catch {
    currentUser.value = { name: '未登入', menus: [] }
  }

  // ✅ 確保有 sid
  await ensureSession().catch(() => '')

  // ✅ 開始線上清單監看（內含 heartbeat + users poll）
  startUserListWatch(() => JSON.parse(localStorage.getItem('user') || '{}'))

  if (!localStorage.getItem('user') && !sessionStorage.getItem('user')) router.replace('/login')
})

onUnmounted(() => {
  window.removeEventListener('message', onMessage)
  stopUserListWatch()
})

</script>
<template>
  <el-container class="dashboard-view dashboard-view h-screen bg-slate-50 overflow-hidden text-slate-700">
    <div 
      v-if="isMobileMenuOpen" 
      class="fixed inset-0 bg-black/20 z-[998] lg:hidden"
      @click="isMobileMenuOpen = false"
    ></div>
    <el-aside width="250px"  :class="['white-sidebar', { 'mobile-active': isMobileMenuOpen }]" >
      <div class="p-6 flex-none">
        <div class="flex items-center gap-4 group" style="text-align: center;">
            <img 
              src="@/assets/img/logo.png" style="width:80%;margin: 0 auto;"
              alt="AI Logo" 
            />         
            </div>
            <el-dialog
              v-model="kbDialogVisible"
              :title="kbAnswerCategory ? `${kbAnswerCategory} / ${kbAnswerTitle}` : kbAnswerTitle"
              width="min(860px, 92vw)"
            >
              <div class="whitespace-pre-wrap leading-7 text-slate-700">{{ kbAnswerBody }}</div>
              <div v-if="kbAnswerSources.length" class="mt-4">
                <div class="text-xs font-semibold text-slate-500 mb-2">知識來源</div>
                <div class="space-y-1">
                  <div
                    v-for="src in kbAnswerSources"
                    :key="src"
                    class="text-xs text-slate-500 break-all"
                  >
                    {{ src }}
                  </div>
                </div>
              </div>
            </el-dialog>
        </div>
      <div class="sidebar-menu-container flex-1 overflow-y-auto custom-scrollbar" style="border:none">
        <el-menu
          default-active="1"
          class="custom-white-menu"
        >
          <template v-for="(menu, index) in currentUser.menus" :key="menu.refno">
            <el-sub-menu v-if="menu.children && menu.children.length > 0" :index="String(index + 1)">
              <template #title>
                <el-icon><cpu /></el-icon>
                <span>{{ menu.title }}</span>
              </template>
              <el-menu-item 
                v-for="(sub, subIdx) in menu.children" 
                :key="subIdx" 
                :index="`${index+1}-${subIdx+1}`"
                @click="handleMenuClick(sub.url, sub.title)"
              >
                {{ sub.title }}
              </el-menu-item>
            </el-sub-menu>

            <el-menu-item v-else :index="String(index + 1)">
              <el-icon><Document /></el-icon>
              <span>{{ menu.title }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </div>

      <div class="flex-none bg-white border-t border-slate-100">
        <div class="p-4 pb-2">
          <div class="flex items-center justify-between mb-2 px-2">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">在線人員動態</span>
            <el-badge :value="onlineUsers.length" :type="rtConnected ? 'success' : 'danger'"></el-badge>
          </div>
          
          <el-select v-model="selectedUser" placeholder="目前在線清單" size="small" class="w-full custom-select-white">
            <el-option v-for="user in onlineUsers" :key="user.account" :label="user.name" :value="user.account">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_5px_#22c55e]"></span>
                <span class="text-sm">{{ user.name }}</span>
              </div>
            </el-option>
          </el-select>
        </div>

        <div class="p-4 pt-2">
          <div class="flex items-center gap-3 p-2 rounded-lg bg-slate-50 border border-slate-100">
            <el-avatar :size="32" :src="`https://api.dicebear.com/7.x/initials/svg?seed=${currentUser.name}`" />
            <div class="overflow-hidden text-left">
              <p class="text-xs text-slate-700 truncate font-bold">{{ currentUser.name }}</p>
              <p class="text-[10px] text-green-600 flex items-center gap-1">
                <span class="w-1.5 h-1.5 bg-green-500 rounded-full"></span> 服務中
              </p>
            </div>
          </div>
        </div>
      </div>
    </el-aside>

    <el-container class="flex flex-col h-screen overflow-hidden">
      <el-header
        class="custom-gradient-header border-b border-slate-200
              flex items-center justify-between
              px-3 md:px-8
              h-14 shrink-0
              overflow-hidden"
      >
        <div class="flex items-center gap-3 min-w-0">
          <!-- 返回 / 展開 按鈕 -->
          <el-button
            v-if="currentUrl"
            class="mobile-toggle-btn pill-outline is-back"
            @click.stop="handleMainButtonClick"
          >
            <span class="arrow-text" style="font-size: 16pt;">⬅︎</span>
          </el-button>

          <el-button
            v-else
            class="mobile-toggle-btn pill-outline is-menu lg:hidden"
            @click.stop="handleMainButtonClick"
          >
            <span class="arrow-text">≡</span>
          </el-button>
          <h2
            class="dynamic-breadcrumb
                  text-base font-medium
                  truncate whitespace-nowrap overflow-hidden
                  max-w-[60vw] sm:max-w-[70vw] md:max-w-none"
            :title="currentUrl ? currentContext : '智能助手'"
          >
            {{ currentUrl ? currentContext : '智能助手' }}
          </h2>
        </div>
      </el-header>
      <el-main class="!p-0 flex flex-col items-center justify-center relative overflow-hidden bg-slate-50">
        <div v-if="!currentUrl" class="w-full max-w-4xl px-8 flex flex-col items-center">
          <div class="text-center mb-10 w-full">
            <h2 class="text-3xl sm:text-4xl font-black text-slate-800 tracking-tight">
              你好，{{ currentUser.name }}
            </h2>
            <div class="mt-4 flex items-center justify-center gap-2">
              <span class="text-slate-400 text-xl font-medium">
                今天想處理什麼業務？
              </span>

              <button
                type="button"
                @click="openCmd"
                title="搜尋報表 / 提醒 / 建議"
                class="
                  inline-flex items-center justify-center
                  w-9 h-9
                  rounded-full
                  border border-slate-300
                  text-slate-700
                  hover:bg-slate-200
                  hover:text-slate-900
                  transition
                "
              >
                <svg
                  viewBox="0 0 24 24"
                  class="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5" 
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="11" cy="11" r="7"></circle>
                  <path d="M20 20l-3.5-3.5"></path>
                </svg>
              </button>
            </div>
              <!-- Command Palette -->
            <el-dialog
              v-model="cmdOpen"
              title="報表 / 提醒 / 建議"
              width="min(820px, 92vw)"
              :close-on-click-modal="true"
            >
              <div class="flex items-center gap-2 mb-3">
                <el-input
                  v-model="cmdKw"
                  placeholder="搜尋：未出清 / 已出清 / 出貨達成率 / Top10 / 業務績效 / 催單..."
                  clearable
                  @keydown.enter="openFirst()"
                />
                <el-button type="primary" @click="openFirst()" :disabled="!filteredCommands.length">開啟</el-button>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  v-for="c in filteredCommands"
                  :key="c.id"
                  class="text-left p-3 border border-slate-200 hover:bg-slate-50"
                  type="button"
                  @click="goCmd(c)"
                >
                  <div class="font-semibold text-slate-800">{{ c.title }}</div>
                  <div class="text-xs text-slate-500 mt-1">{{ c.desc }}</div>
                  <div class="text-xs text-slate-400 mt-1">關鍵字：{{ c.keywords.join('、') }}</div>
                </button>
              </div>
            </el-dialog>
        </div>

          <!-- ✅ ChatGPT-like 輸入區：右側內嵌麥克風/上傳/送出 -->
          <div class="w-full">
            <div class="ai-input-wrap">
              <el-input
                v-model="aiInput"
                type="textarea"
                :rows="6"
                placeholder="在此輸入指令或使用語音..."
                class="custom-ai-input w-full"
              />

                <!-- ✅ 右下角並排：麥克風/停止/上傳/AI解析 -->
                <div class="ai-actions">
                  <!-- 🎤 / ⏹ 停止：同一顆按鈕切換 -->
                  <button
                    type="button"
                    class="ai-icon"
                    @click="isRecording ? stopAndCommitThenMaybeSubmit() : toggleLongVoice()"
                    :title="isRecording ? '停止錄音' : '語音輸入'"
                    aria-label="voice"
                  >
                    <!-- mic -->
                    <svg v-if="!isRecording" viewBox="0 0 24 24" class="ai-svg" aria-hidden="true">
                      <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3Z" fill="currentColor"/>
                      <path d="M19 11a1 1 0 1 0-2 0 5 5 0 0 1-10 0 1 1 0 1 0-2 0 7 7 0 0 0 6 6.92V20H9a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2h-2v-2.08A7 7 0 0 0 19 11Z" fill="currentColor"/>
                    </svg>
                    <!-- stop (square) -->
                    <svg v-else viewBox="0 0 24 24" class="ai-svg" aria-hidden="true">
                      <path d="M7 7h10v10H7z" fill="currentColor"/>
                    </svg>
                  </button>

                  <!-- ⬆️ 上傳：只有 draftText 或錄音/轉字時顯示 -->
                  <button
                    v-if="draftText || isRecording || isTranscribing"
                    type="button"
                    class="ai-icon"
                    :disabled="(!draftText && !isRecording) || isTranscribing || isUploadingVoice"
                    @click="uploadVoiceToInput"
                    title="把語音結果放入輸入框"
                    aria-label="upload"
                  >
                    <!-- UP arrow -->
                    <svg viewBox="0 0 24 24" class="ai-svg" aria-hidden="true">
                      <path
                        d="M12 20a1 1 0 0 1-1-1V7.83L7.41 11.4A1 1 0 1 1 6 9.99l5.3-5.3a1 1 0 0 1 1.4 0l5.3 5.3a1 1 0 1 1-1.41 1.41L13 7.83V19a1 1 0 0 1-1 1Z"
                        fill="currentColor"
                      />
                    </svg>
                  </button>

                  <!-- ➤ AI解析（送出） -->
                  <button
                    type="button"
                    class="ai-icon ai-send"
                    @click="handleAiSubmit"
                    title="AI 解析"
                    aria-label="send"
                  >
                    <svg viewBox="0 0 24 24" class="ai-svg" aria-hidden="true">
                      <path d="M3.4 11.2 20.6 4.3c.8-.3 1.6.5 1.3 1.3l-6.9 17.2c-.3.8-1.5.8-1.8 0l-2.2-5.4-5.4-2.2c-.8-.3-.8-1.5 0-1.8Zm6.7 2.7 2.9 1.2 1.2 2.9 4.5-11.2-11.2 4.5Z" fill="currentColor"/>
                    </svg>
                  </button>
                </div>
            </div>

            <!-- 狀態列（保留） -->
            <div class="mt-2 text-xs text-slate-600 flex items-center gap-3 min-h-[20px]">
              <template v-if="isRecording">
                <span class="rec-pill">聆聽中 .....</span>
                <span class="rec-wave" aria-hidden="true">
                  <i></i><i></i><i></i><i></i><i></i>
                </span>
              </template>
              <span v-else-if="isTranscribing">轉文字中…</span>
              <span v-else-if="draftText">已準備：{{ draftText }}</span>
              <span v-else> </span>
            </div>

            <div v-if="speechError" class="mt-1 text-xs text-rose-600">
              {{ speechError }}
            </div>
          </div>
        </div>

        <div v-else class="w-full h-full">
          <iframe
            ref="iframeRef"
            :src="currentUrl"
            class="w-full h-full border-none"
            @load="onIframeLoad"
          />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>
