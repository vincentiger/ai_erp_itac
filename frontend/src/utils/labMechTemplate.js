// C:\ai_erp\frontend\src\utils\labMechTemplate.js
// LabMech 模板系統 API

const api = (path) => `/ai/api/${String(path).replace(/^\/+/, '')}`


// -----------------------------------------
// 共用 JSON fetch helper
// -----------------------------------------
async function fetchJson(url, options = {}) {

  const resp = await fetch(url, {
    credentials: 'include',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  })

  const contentType = resp.headers.get('content-type') || ''

  const text = await resp.text()

  if (!contentType.includes('application/json')) {
    console.error('API response not JSON:', text)
    throw new Error(`API錯誤 (${resp.status})`)
  }

  const json = JSON.parse(text)

  if (!resp.ok) {
    throw new Error(json?.msg || `HTTP ${resp.status}`)
  }

  return json
}


// -----------------------------------------
// 取得模板清單
// -----------------------------------------
export async function fetchLabMechTemplates(keyword = '') {

  const q = keyword
    ? `?q=${encodeURIComponent(keyword)}`
    : ''

  return fetchJson(
    api(`lab/mech/templates${q}`)
  )
}


// -----------------------------------------
// 取得模板內容
// -----------------------------------------
export async function getLabMechTemplate(templateId) {

  return fetchJson(
    api(`lab/mech/templates/${templateId}`)
  )
}


// -----------------------------------------
// 新增模板
// -----------------------------------------
export async function createLabMechTemplate(payload) {

  return fetchJson(
    api('lab/mech/templates'),
    {
      method: 'POST',
      body: JSON.stringify(payload)
    }
  )
}


// -----------------------------------------
// 由模板建立報告
// -----------------------------------------
export async function createReportFromTemplate(templateId, payload = {}) {

  return fetchJson(
    api(`lab/mech/templates/${templateId}/create-report`),
    {
      method: 'POST',
      body: JSON.stringify(payload)
    }
  )
}


// -----------------------------------------
// 刪除模板（未來 UI 會用到）
// -----------------------------------------
export async function deleteLabMechTemplate(templateId) {

  return fetchJson(
    api(`lab/mech/templates/${templateId}`),
    {
      method: 'DELETE'
    }
  )
}