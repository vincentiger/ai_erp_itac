export async function apiFetch(url, options = {}) {
  const token =
    localStorage.getItem('token') ||
    localStorage.getItem('access_token') ||
    localStorage.getItem('jwt') ||
    ''
  const rtSid = localStorage.getItem('rt_sid') || ''
  let currentUser = {}
  try {
    currentUser = JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    currentUser = {}
  }

  const headers = new Headers(options.headers || {})
  if (!headers.has('Accept')) headers.set('Accept', 'application/json')
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (rtSid && !headers.has('X-RT-SID')) {
    headers.set('X-RT-SID', rtSid)
  }
  if (currentUser?.account && !headers.has('X-User-Account')) {
    headers.set('X-User-Account', String(currentUser.account))
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: options.credentials ?? 'include',
  })

  return res
}
