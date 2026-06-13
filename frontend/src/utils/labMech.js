// frontend/src/api/labMech.js
import { apiFetch } from '@/utils/apiFetch'

const api = (path) => `/ai/api/${String(path).replace(/^\/+/, '')}`
// --- fetch helpers ---
async function fetchJson(url, options) {
  const resp = await apiFetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  })

  const ct = resp.headers.get('content-type') || ''
  const text = await resp.text()

  if (!ct.includes('application/json')) {
    throw new Error(`Not JSON: ${resp.status} ${text.slice(0, 120)}`)
  }

  const json = JSON.parse(text)

  if (!resp.ok) {
    throw new Error(json?.msg || `HTTP ${resp.status}`)
  }

  return json
}

async function safeJson(r) {
  try {
    return await r.json()
  } catch (e) {
    return {
      ok: false,
      msg: 'Invalid JSON response',
      status: r.status
    }
  }
}


/* ===============================
   Template
================================ */

export async function fetchLabMechTemplate() {
  const r = await fetch(api('lab/mech/template'), {
    credentials: 'include'
  })
  return safeJson(r)
}


/* ===============================
   Judge
================================ */

export async function judgeLabMechTest(payload) {
  return await fetchJson(api('lab/mech/judge'), {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}


/* ===============================
   Reports
================================ */

export async function createLabMechReport(payload) {
  return await fetchJson(api('lab/mech/reports'), {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getLabMechReport(reportId) {
  return await fetchJson(api(`lab/mech/reports/${reportId}`))
}


export async function updateLabMechReport(reportId, payload) {
  return await fetchJson(api(`lab/mech/reports/${reportId}`), {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export async function fetchLabMechImages(reportId) {
  return await fetchJson(api(`lab/mech/reports/${reportId}/images`))
}

export async function uploadLabMechImages(reportId, files) {
  const formData = new FormData()
  for (const file of files || []) {
    formData.append('files', file)
  }

  const resp = await apiFetch(api(`lab/mech/reports/${reportId}/images`), {
    method: 'POST',
    body: formData,
  })

  const ct = resp.headers.get('content-type') || ''
  const text = await resp.text()

  if (resp.status === 413) {
    throw new Error('圖片檔案太大，請改用較小圖片或壓縮後再上傳')
  }

  if (!ct.includes('application/json')) {
    throw new Error(`Not JSON: ${resp.status} ${text.slice(0, 120)}`)
  }

  const json = JSON.parse(text)
  if (!resp.ok || json?.ok === false) {
    throw new Error(json?.msg || `HTTP ${resp.status}`)
  }
  return json
}

export async function deleteLabMechImage(reportId, name) {
  return await fetchJson(api(`lab/mech/reports/${reportId}/images/delete`), {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

/* ===============================
   DOCX Export
================================ */

export async function exportLabMechDocx(reportId) {
  return await fetchJson(api(`lab/mech/reports/${reportId}/export-docx`), {
    method: 'POST',
  })
}


export function downloadLabMechDocx(exportId) {
  const url = api(`lab/mech/exports/${exportId}.docx`)
  window.open(url, '_blank')
}
