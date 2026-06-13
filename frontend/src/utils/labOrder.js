const API_BASE = (import.meta.env.BASE_URL || '/').replace(/\/?$/, '/')
const api = (p) => `${window.location.origin}${API_BASE}${String(p).replace(/^\/+/, '')}`

async function fetchJson(url, options) {
  const resp = await fetch(url, {
    credentials: 'include',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  })

  const json = await resp.json()
  if (!resp.ok || !json?.ok) {
    throw new Error(json?.msg || `HTTP ${resp.status}`)
  }
  return json
}

export async function fetchLabOrderByLabNo(labNo) {
  const clean = String(labNo || '').trim()
  if (!clean) {
    throw new Error('lab_no required')
  }
  return fetchJson(api(`/ai/api/lab/instances/by-lab-no/${encodeURIComponent(clean)}`))
}

export async function searchLabOrders(filters = {}) {
  const params = new URLSearchParams()

  for (const [key, value] of Object.entries(filters || {})) {
    const clean = String(value || '').trim()
    if (clean) {
      params.set(key, clean)
    }
  }

  if (![...params.keys()].length) {
    throw new Error('search filters required')
  }

  return fetchJson(api(`/ai/api/lab/instances/search?${params.toString()}`))
}
