// frontend/src/utils/socket.js
import { io } from 'socket.io-client'
import { ref } from 'vue'

function trimSlashRight(s) {
  return String(s || '').replace(/\/+$/, '')
}
function ensureSlashLeft(s) {
  const v = String(s || '').trim()
  if (!v) return ''
  return v.startsWith('/') ? v : `/${v}`
}
function normalizeBaseUrl(v) {
  let s = String(v || '/').trim()
  if (!s.startsWith('/')) s = '/' + s
  if (!s.endsWith('/')) s = s + '/'
  return s
}
function getAppBase() {
  return normalizeBaseUrl(import.meta.env.BASE_URL || '/')
}

function resolveSocketTarget() {
  const rawEnvUrl = (import.meta.env.VITE_SOCKET_URL || '').trim()
  const rawEnvPath = (import.meta.env.VITE_SOCKET_PATH || '').trim()

  // 1) 指定直連（例如 ws server 在不同 host）
  if (rawEnvUrl) {
    const base = trimSlashRight(rawEnvUrl)
    const path = rawEnvPath ? ensureSlashLeft(rawEnvPath) : '/socket.io'
    return { base, path, mode: 'direct' }
  }

  // 2) 同源 + 跟著 BASE_URL（'/' or '/ai/'）
  const APP_BASE = getAppBase()
  const base = window.location.origin
  const path = ensureSlashLeft(`${APP_BASE}socket.io`) // '/socket.io' or '/ai/socket.io'
  return { base, path, mode: 'same-origin' }
}

export const { base: SOCKET_BASE, path: SOCKET_PATH, mode: SOCKET_MODE } = resolveSocketTarget()

export const isConnected = ref(false)
export const onlineUsers = ref([])

// ✅ websocket-only（避免 polling 被 Cloudflare 擋）
export const socket = io(SOCKET_BASE, {
  path: SOCKET_PATH,

  // ✅ 只走 websocket（你環境一定要）
  transports: ['websocket'],
  upgrade: false,

  autoConnect: false,
  timeout: 20000,

  // ✅ 讓它穩定重連，但不要打爆
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 8000,
  randomizationFactor: 0.2,

  // ✅ 同源不需要 credentials，避免 cookie 干擾
  withCredentials: false,

  // ❌ 不要 forceNew（很常導致 timeout/連線累積）
  forceNew: false,
})

// 登入後再連線（如果你用 token）
export function afterLogin(token) {
  if (token) socket.auth = { token }
  connectSocket()
}

export function connectSocket() {
  const eng = socket.io?.engine
  const isConnecting = !!eng && eng.readyState === 'opening'
  if (socket.connected || isConnecting) return
  socket.connect()
}

export function disconnectSocket() {
  if (socket.connected) socket.disconnect()
}

export function waitSocketConnected(timeoutMs = 20000) {
  return new Promise((resolve, reject) => {
    if (socket.connected) return resolve(true)

    const t = setTimeout(() => {
      cleanup()
      reject(new Error('socket connect timeout'))
    }, timeoutMs)

    function cleanup() {
      clearTimeout(t)
      socket.off('connect', onConnect)
      socket.off('connect_error', onErr)
    }

    function onConnect() {
      cleanup()
      resolve(true)
    }

    function onErr(err) {
      cleanup()
      reject(err)
    }

    socket.once('connect', onConnect)
    socket.once('connect_error', onErr)
    connectSocket()
  })
}

let _inited = false
export function initSocketEvent(currentUserRef = null, onLogout = null) {
  if (_inited) return
  _inited = true
  
let _pingTimer = null
socket.on('connect', () => {
  isConnected.value = true

  const transport = socket.io?.engine?.transport?.name
  console.log(
    '[socket] connected',
    socket.id,
    'transport=',
    transport,
    'mode=',
    SOCKET_MODE,
    'base=',
    SOCKET_BASE,
    'path=',
    SOCKET_PATH
  )

  // ✅ 保活 ping（避免 Cloudflare / IIS idle timeout）
  if (_pingTimer) clearInterval(_pingTimer)
  _pingTimer = setInterval(() => {
    try {
      socket.emit('rt:ping')
    } catch (e) {
      console.warn('[socket] ping error', e)
    }
  }, 20000)
})

socket.on('disconnect', (reason) => {
  isConnected.value = false
  console.warn('[socket] disconnected', reason)

  // ✅ 清掉保活 timer
  if (_pingTimer) {
    clearInterval(_pingTimer)
    _pingTimer = null
  }
})
socket.on('connect_error', (err) => {
  isConnected.value = false

  const msg = String(err?.message || err || '')
  console.error(
    '[socket] connect_error',
    msg,
    'mode=',
    SOCKET_MODE,
    'base=',
    SOCKET_BASE,
    'path=',
    SOCKET_PATH
  )

  // ✅ timeout 時做一次 reset（避免 engine 卡死一直 timeout）
  if (msg.toLowerCase().includes('timeout')) {
    try { socket.disconnect() } catch {}
    setTimeout(() => {
      try { socket.connect() } catch {}
    }, 800)
  }
})

  socket.on('updateUserList', (list) => {
    onlineUsers.value = Array.isArray(list) ? list : []
  })

  socket.on('forceLogout', (msg) => {
    if (typeof onLogout === 'function') onLogout(msg)
  })
}
