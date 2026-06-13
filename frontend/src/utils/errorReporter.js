const API_BASE = (import.meta.env.BASE_URL || '/').replace(/\/?$/, '/')
const api = (p) => `${window.location.origin}${API_BASE}${String(p).replace(/^\/+/, '')}`

let lastSentAt = 0
let lastSignature = ''

function shouldSend(signature) {
  const now = Date.now()
  if (signature === lastSignature && now - lastSentAt < 10000) {
    return false
  }
  lastSignature = signature
  lastSentAt = now
  return true
}

export async function reportClientError(payload = {}) {
  const message = String(payload.message || 'client error')
  const signature = `${payload.source || ''}|${message}|${payload.line || ''}|${payload.column || ''}`
  if (!shouldSend(signature)) return

  try {
    await fetch(api('/ai/api/client-error'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        ...payload,
        url: payload.url || window.location.href,
      }),
    })
  } catch (_) {
    // Keep silent: local UI should not be blocked by reporting failure.
  }
}

export function installGlobalErrorReporter() {
  window.addEventListener('error', (event) => {
    reportClientError({
      message: event.message || 'window error',
      source: event.filename || '',
      line: event.lineno || 0,
      column: event.colno || 0,
      stack: event.error?.stack || '',
    })
  })

  window.addEventListener('unhandledrejection', (event) => {
    const reason = event.reason
    reportClientError({
      message: reason?.message || String(reason || 'unhandled rejection'),
      source: 'unhandledrejection',
      stack: reason?.stack || '',
    })
  })
}
