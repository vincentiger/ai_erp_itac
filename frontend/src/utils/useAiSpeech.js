import { ref } from 'vue'
import { useRouter } from 'vue-router'

export function useAiSpeech(onNavigation) {
  const router = useRouter()

  const isAiListening = ref(false)
  const aiSpeechStatus = ref('')
  const aiInput = ref('')

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    aiSpeechStatus.value = '此瀏覽器不支援語音辨識'
    return { aiInput, isAiListening, aiSpeechStatus, toggleAiVoice: () => {} }
  }

  const recognition = new SpeechRecognition()
  recognition.lang = 'zh-TW'
  recognition.continuous = false
  recognition.interimResults = false

  function normalizeCommand(text) {
    return String(text || '')
      .trim()
      .replace(/[。．，、]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
  }

  // UTF-8 safe base64
  function toBase64Json(obj) {
    const json = JSON.stringify(obj)
    return btoa(encodeURIComponent(json))
  }

  function lastYearRange() {
    const y = new Date().getFullYear() - 1
    return [`${y}-01-01`, `${y}-12-31`]
  }

  function isOrderMention(cmd) {
    const s = cmd.toLowerCase()
    return (
      cmd.includes('訂單') ||
      s.includes('pi') ||
      s.includes('proforma') ||
      s.includes('profoma') // 常見拼錯也吃
    )
  }

  /**
   * 語音只要提到「訂單/PI」：等同打開左側「訂單查詢(order_view)」
   * 並依語意帶 query 條件（例：去年、排序）
   */
  function handleOrderOpen(cmd) {
    if (!isOrderMention(cmd)) return false

    // 期間（先做去年；你之後可擴充今年/本月/上月）
    const filters = []
    if (cmd.includes('去年')) {
      const [d1, d2] = lastYearRange()
      filters.push({ field: '訂單日期', op: 'between', value: [d1, d2] })
    }

    // 排序（提到什麼就排什麼）
    const sort = []
    if (cmd.includes('客戶')) sort.push({ field: '客戶名稱', dir: 'asc' })
    if (cmd.includes('日期')) sort.push({ field: '訂單日期', dir: 'asc' })
    if (cmd.includes('金額')) sort.push({ field: '訂單金額', dir: 'desc' })
    if (sort.length === 0) {
      // 預設：日期新到舊
      sort.push({ field: '訂單日期', dir: 'desc' })
    }

    const queryJson = {
      dataset: 'ai_orders',
      select: ['客戶名稱', '業務代表', '訂單編號', 'form_no', '幣別', '訂單金額', '訂單日期', '公司抬頭'],
      filters,
      sort,
      limit: 1000
    }

    const q = toBase64Json(queryJson)

    router.push({
      name: 'order_view',     // ✅ 你權限對應的 route name
      query: { q, page: '1', pageSize: '50' }
    })

    aiSpeechStatus.value = '已開啟：訂單查詢'
    return true
  }

  function handleNavigation(cmd) {
    if (!cmd.includes('導航')) return false
    const target = cmd.replace('導航', '').replace(/至|到/g, '').trim()
    if (typeof onNavigation === 'function') onNavigation(target)
    aiSpeechStatus.value = `導航至: ${target}`
    return true
  }

  recognition.onresult = (event) => {
    const raw = event.results?.[0]?.[0]?.transcript || ''
    const command = normalizeCommand(raw)

    // ✅ 1) 訂單/PI：直接開啟訂單查詢（order_view）
    if (handleOrderOpen(command)) {
      isAiListening.value = false
      return
    }

    // ✅ 2) 原本導航指令
    if (handleNavigation(command)) {
      isAiListening.value = false
      return
    }

    // ✅ 3) 其他：一般文字
    aiInput.value = command
    aiSpeechStatus.value = `收到：${command}`
    isAiListening.value = false
  }

  recognition.onerror = () => {
    isAiListening.value = false
    aiSpeechStatus.value = '語音辨識失敗，請再試一次'
  }

  recognition.onend = () => {
    isAiListening.value = false
  }

  const toggleAiVoice = () => {
    if (!isAiListening.value) {
      recognition.start()
      isAiListening.value = true
      aiSpeechStatus.value = '語音辨識輸入中.....'
    } else {
      recognition.stop()
    }
  }

  return { aiInput, isAiListening, aiSpeechStatus, toggleAiVoice }
}
