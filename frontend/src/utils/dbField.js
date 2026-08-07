import { apiFetch } from '@/utils/apiFetch'

const API_BASE = '/ai/api'

const contextCache = new Map()

function sanitizePageName(page) {
  return String(page || '')
    .trim()
    .replace(/[^A-Za-z0-9_-]/g, '')
}

function toMaxLength(value) {
  const n = Number(value)
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : null
}

function unwrapContextPayload(payload) {
  if (!payload) return null
  if (payload.ok === false) return null
  return payload.data ?? payload
}

function normalizeFieldSpec(spec = {}) {
  if (!spec || typeof spec !== 'object') return {}

  const maxLength =
    toMaxLength(spec.maxLength) ??
    toMaxLength(spec.maxlength) ??
    toMaxLength(spec.length) ??
    toMaxLength(spec.dbMaxLength) ??
    null

  return {
    ...spec,
    maxLength,
  }
}

function flattenFieldSpecs(context) {
  const fields = Array.isArray(context?.fields) ? context.fields : []
  const map = new Map()

  for (const raw of fields) {
    const spec = normalizeFieldSpec(raw)
    const key = String(spec.key || '').trim()
    if (!key) continue
    map.set(key, spec)

    const group = Array.isArray(raw?.group) ? raw.group : []
    for (const item of group) {
      const nested = normalizeFieldSpec(item)
      const nestedKey = String(nested.key || '').trim()
      if (!nestedKey) continue
      map.set(nestedKey, {
        ...spec,
        ...nested,
      })
    }
  }

  return map
}

export async function loadDbContext(page, { force = false } = {}) {
  const safePage = sanitizePageName(page)
  if (!safePage) {
    throw new Error('page is required')
  }

  if (!force && contextCache.has(safePage)) {
    return contextCache.get(safePage)
  }

  const promise = (async () => {
    const resp = await apiFetch(`${API_BASE}/context/${encodeURIComponent(safePage)}`, {
      method: 'GET',
    })
    const payload = await resp.json().catch(() => ({}))
    const data = unwrapContextPayload(payload)
    if (!resp.ok || !data) {
      throw new Error(payload?.msg || `context load failed (${resp.status})`)
    }
    return data
  })()

  contextCache.set(safePage, promise)

  try {
    return await promise
  } catch (err) {
    contextCache.delete(safePage)
    throw err
  }
}

export function clampText(value, maxLength) {
  const max = toMaxLength(maxLength)
  if (!max) return value == null ? '' : String(value)
  return String(value ?? '').slice(0, max)
}

export function getFieldSpec(contextOrPage, fieldKey) {
  const key = String(fieldKey || '').trim()
  if (!key) return null

  const context = contextOrPage && typeof contextOrPage === 'object'
    ? contextOrPage
    : null

  if (!context) return null

  const map = flattenFieldSpecs(context)
  return map.get(key) || null
}

export function getFieldMaxLength(contextOrPage, fieldKey, fallbackMaxLength = null) {
  const spec = getFieldSpec(contextOrPage, fieldKey)
  const maxLength = toMaxLength(spec?.maxLength)
  return maxLength ?? toMaxLength(fallbackMaxLength)
}

export function buildFieldInputAttrs(contextOrPage, fieldKey, fallbackMaxLength = null) {
  const maxLength = getFieldMaxLength(contextOrPage, fieldKey, fallbackMaxLength)
  const attrs = {
    'data-db-field': String(fieldKey || ''),
  }

  if (maxLength) {
    attrs.maxlength = maxLength
    attrs['data-db-maxlength'] = maxLength
  }

  return attrs
}

export function normalizeRecordByContext(contextOrPage, record) {
  if (!record || typeof record !== 'object') return record

  const context = contextOrPage && typeof contextOrPage === 'object'
    ? contextOrPage
    : null
  if (!context) return { ...record }

  const map = flattenFieldSpecs(context)
  const next = { ...record }

  for (const [key, value] of Object.entries(next)) {
    const spec = map.get(key)
    const maxLength = toMaxLength(spec?.maxLength)
    if (!maxLength) continue
    if (typeof value === 'string') {
      next[key] = clampText(value, maxLength)
    }
  }

  return next
}

function resolveLimit(bindingValue) {
  if (bindingValue == null) return null
  if (typeof bindingValue === 'object' && bindingValue?.__dbLimitFallback__ != null) {
    return resolveLimit(bindingValue.__dbLimitFallback__)
  }
  if (typeof bindingValue === 'number' || typeof bindingValue === 'string') {
    return toMaxLength(bindingValue)
  }
  if (typeof bindingValue !== 'object') return null

  return (
    toMaxLength(bindingValue.maxLength) ??
    toMaxLength(bindingValue.maxlength) ??
    toMaxLength(bindingValue.length) ??
    toMaxLength(bindingValue.limit) ??
    toMaxLength(bindingValue.max)
  )
}

function getTargets(el) {
  if (!el) return []
  if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
    return [el]
  }
  if (typeof el.querySelectorAll !== 'function') return []
  return Array.from(el.querySelectorAll('input, textarea'))
}

function getNativeAttrLimit(target) {
  const raw = target?.getAttribute?.('maxlength')
  return toMaxLength(raw)
}

const listenerStore = new WeakMap()

function bindElementLimit(target, maxLength) {
  if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) return null

  const limit = toMaxLength(maxLength)
  if (!limit) {
    target.removeAttribute('maxlength')
    const prev = listenerStore.get(target)
    if (prev) {
      target.removeEventListener('input', prev, true)
      listenerStore.delete(target)
    }
    return null
  }

  target.setAttribute('maxlength', String(limit))

  const handler = () => {
    const current = String(target.value ?? '')
    if (current.length <= limit) return
    const next = current.slice(0, limit)
    if (next === current) return
    const start = target.selectionStart
    const end = target.selectionEnd
    target.value = next
    if (typeof start === 'number' && typeof end === 'number') {
      const nextPos = Math.min(next.length, start)
      try {
        target.setSelectionRange(nextPos, nextPos)
      } catch {
        // ignore selection errors for unsupported input types
      }
    }
  }

  const prev = listenerStore.get(target)
  if (prev) {
    target.removeEventListener('input', prev, true)
  }
  target.addEventListener('input', handler, true)
  listenerStore.set(target, handler)

  handler()
  return handler
}

export const dbLimitDirective = {
  mounted(el, binding) {
    for (const target of getTargets(el)) {
      const maxLength = resolveLimit(binding.value) ?? getNativeAttrLimit(target)
      bindElementLimit(target, maxLength)
    }
  },
  updated(el, binding) {
    for (const target of getTargets(el)) {
      const maxLength = resolveLimit(binding.value) ?? getNativeAttrLimit(target)
      bindElementLimit(target, maxLength)
    }
  },
  unmounted(el) {
    for (const target of getTargets(el)) {
      const prev = listenerStore.get(target)
      if (prev) {
        target.removeEventListener('input', prev, true)
        listenerStore.delete(target)
      }
    }
  },
}

export function useDbFieldContext(page) {
  return loadDbContext(page)
}
