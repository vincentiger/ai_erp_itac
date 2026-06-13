// frontend/src/utils/rt.js
import { ref } from 'vue'

const api = (path) => `/ai/api/${path}`; 

// reactive states
export const onlineUsers = ref([])
export const rtConnected = ref(false)
export const sessionId = ref(localStorage.getItem('rt_sid') || '')

let _mainLoopTimer = null // 唯一的循環計時器

export function clearSessionId() {
  sessionId.value = ''
  localStorage.removeItem('rt_sid')
}

function fallbackUuid() {
  const now = Date.now().toString(16)
  const perf = typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? Math.floor(performance.now() * 1000).toString(16)
    : Math.floor(Math.random() * 0xffffffff).toString(16)
  const rand = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).slice(1)
  return `${now}-${rand()}-${rand()}-${perf}-${rand()}${rand()}${rand()}`
}

export async function ensureSession() {
  if (sessionId.value) return sessionId.value
  const sid =
    (typeof globalThis !== 'undefined'
      && globalThis.crypto
      && typeof globalThis.crypto.randomUUID === 'function')
      ? globalThis.crypto.randomUUID()
      : fallbackUuid()
  sessionId.value = sid
  localStorage.setItem('rt_sid', sid)
  return sid
}

// --- fetch helpers ---
async function fetchJson(url, options) {
  const resp = await fetch(url, {
    credentials: 'include',
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
  })
  const ct = resp.headers.get('content-type') || ''
  const text = await resp.text()
  if (!ct.includes('application/json')) throw new Error(`Not JSON: ${resp.status} ${text.slice(0, 120)}`)
  const json = JSON.parse(text)
  if (!resp.ok) throw new Error(json?.msg || `HTTP ${resp.status}`)
  return json
}

/**
 * ✅ 核心：單一同步循環 (Heartbeat + Get Users)
 * 頻率設定為 60 秒一次，徹底避開 Cloudflare 403 封鎖
 */
async function syncLoop(getUserFn) {
  try {
    const sid = await ensureSession()
    const user = typeof getUserFn === 'function' ? getUserFn() : null
    
    // 如果沒有 user (未登入)，不跑 heartbeat，但可以跑 p-list 拿名單 (或直接跳過)
    if (!user?.account) {
       _mainLoopTimer = setTimeout(() => syncLoop(getUserFn), 10000); // 未登入縮短重試
       return;
    }

    // ✅ POST heartbeat：同時完成「報到」與「抓取名單」
    const json = await fetchJson(api('rt/heartbeat'), {
      method: 'POST',
      body: JSON.stringify({ sid, user }),
    })

    if (json.ok) {
      onlineUsers.value = Array.isArray(json.users) ? json.users : []
      rtConnected.value = true
      console.log(`[rt] 同步成功，在線人數: ${json.online_count}`)
    }
  } catch (err) {
    rtConnected.value = false
    console.warn('[rt] 同步失敗 (Heartbeat):', err)
  }

  // ✅ 設定 60 秒後再次執行，這頻率對 Cloudflare 非常安全
  _mainLoopTimer = setTimeout(() => syncLoop(getUserFn), 60000)
}

// --- API calls ---

// ✅ 給 loginView.vue 用
export async function rtLogin(account, password) {
  const sid = await ensureSession()
  const json = await fetchJson(api('rt/login'), {
    method: 'POST',
    body: JSON.stringify({ sid, account, password }),
  })

  if (json?.sid) {
    sessionId.value = json.sid
    localStorage.setItem('rt_sid', json.sid)
  }
  if (Array.isArray(json.users)) {
    onlineUsers.value = json.users
    rtConnected.value = true
  }
  return json
}

/**
 * ✅ 啟動監測 (取代舊的 startUserListWatch)
 */
export function startUserListWatch(getUserFn) {
  stopUserListWatch()
  // 立即執行第一次同步
  syncLoop(getUserFn)
}

/**
 * ✅ 停止監測
 */
export function stopUserListWatch() {
  if (_mainLoopTimer) clearTimeout(_mainLoopTimer)
  _mainLoopTimer = null
}

// 為了相容性保留空函式，避免其他檔案 import 報錯
export async function pullUsersOnce() {}
