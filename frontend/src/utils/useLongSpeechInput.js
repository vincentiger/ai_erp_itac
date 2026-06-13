// src/utils/useLongSpeechInput.js
import { ref } from 'vue'

export function useLongSpeechInput(opts = {}) {
  const {
    lang = 'zh-TW',
    autoAppendToInput = false, // 若 true：停止就自動塞到輸入框；你要像 ChatGPT -> false
  } = opts

  const isRecording = ref(false)
  const isTranscribing = ref(false)  // Web Speech 其實是即時辨識，但這裡用狀態模擬「轉文字中」
  const draftText = ref('')          // 暫存的語音內容（按上傳才送到 aiInput）
  const error = ref('')

  let recognition = null
  let finalBuffer = '' // 累積最終文字
  let startedAt = 0

  function ensureSupport() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      error.value = '此瀏覽器不支援語音辨識'
      return null
    }
    return SR
  }

  function init() {
    if (recognition) return true

    const SR = ensureSupport()
    if (!SR) return false

    recognition = new SR()
    recognition.lang = lang
    recognition.continuous = true
    recognition.interimResults = true // 允許 interim，讓長語音更穩
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      error.value = ''
      isRecording.value = true
      isTranscribing.value = false
      startedAt = Date.now()
      // 開始新一段錄音時，不清掉 draftText，交給外面決定要不要清
      finalBuffer = ''
    }

    recognition.onresult = (e) => {
      // 這裡做「像 ChatGPT」：把 interim 顯示在 draftText，但最終只累積 finalBuffer
      let interim = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i]
        const t = (r[0]?.transcript || '')
        if (r.isFinal) {
          finalBuffer += t
        } else {
          interim += t
        }
      }
      // draftText = finalBuffer + interim（停止時會只留下 finalBuffer）
      draftText.value = (finalBuffer + interim).trim()
    }

    recognition.onerror = (e) => {
      // 常見：not-allowed / audio-capture / no-speech
      error.value = e?.error ? `語音錯誤：${e.error}` : '語音錯誤'
      isRecording.value = false
      isTranscribing.value = false
      try { recognition.stop() } catch {}
    }

    recognition.onend = () => {
      // 使用者停止後會進來
      isRecording.value = false

      // 模擬「轉文字中」：如果講很長，給一個短暫狀態更像 ChatGPT
      const dur = Date.now() - startedAt
      if (dur > 1200) {
        isTranscribing.value = true
        setTimeout(() => {
          isTranscribing.value = false
          // 停止時：把 interim 去掉，只留 final
          draftText.value = finalBuffer.trim()
        }, 350)
      } else {
        draftText.value = finalBuffer.trim()
      }
    }

    return true
  }

  async function primeMic() {
    // 先拿麥克風權限（避免 SpeechRecognition start 直接 not-allowed）
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(t => t.stop())
      return true
    } catch (e) {
      error.value = '麥克風權限被拒或不可用'
      return false
    }
  }

  async function start() {
    if (!init()) return false
    error.value = ''

    const ok = await primeMic()
    if (!ok) return false

    // 開始前清掉上一段 buffer，但保留 draftText（你可以外面手動清）
    finalBuffer = ''
    draftText.value = ''
    try {
      recognition.start()
      return true
    } catch (e) {
      error.value = '語音啟動失敗（可能已在啟動中）'
      return false
    }
  }

  function stop() {
    if (!recognition) return
    try { recognition.stop() } catch {}
  }

  function toggle() {
    if (isRecording.value) stop()
    else start()
  }

  function clearDraft() {
    draftText.value = ''
    finalBuffer = ''
  }

  // 按「上傳」：把 draftText 回傳給外面塞 aiInput
  function commit() {
    const t = String(draftText.value || '').trim()
    if (!t) return ''
    if (autoAppendToInput) {
      // 由外面決定怎麼塞；這裡只回傳
    }
    return t
  }

  function stopAndCommit(timeoutMs = 2500) {
     return new Promise((resolve) => {
     const t0 = Date.now()

     // 已經沒在錄音：直接 commit
     if (!isRecording.value) {
          resolve(commit())
          return
     }

     // stop 後會觸發 onend，onend 裡會把 draftText 變成 finalBuffer.trim()
     try { recognition?.stop?.() } catch {}

     const timer = setInterval(() => {
          const done = !isRecording.value && !isTranscribing.value
          const tooLong = Date.now() - t0 > timeoutMs
          if (done || tooLong) {
          clearInterval(timer)
          resolve(commit())
          }
     }, 60)
     })
  }

  return {
     isRecording,
     isTranscribing,
     draftText,
     error,
     start,
     stop,
     toggle,
     clearDraft,
     commit,
     stopAndCommit, // ✅ 新增
  }
}
