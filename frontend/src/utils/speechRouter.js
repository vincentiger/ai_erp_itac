// src/utils/speechRouter.js
const rules = []

export function registerRule(rule) {
  if (!rule) return
  rules.push(rule)
}

/**
 * 支援兩種 rule：
 * 1) function(text, ctx) => {handled:boolean}
 * 2) object: { id?, match(text, ctx) => matchResult|null, run(text, ctx, matchResult) }
 */
export async function handleSpeech(text, ctx = {}) {
  const t = String(text || '').trim()
  if (!t) return { handled: false }

  for (const rule of rules) {
    try {
      // A) 舊版 function rule
      if (typeof rule === 'function') {
        const res = await rule(t, ctx)
        if (res?.handled) return res
        continue
      }

      // B) 新版 handler object
      if (rule && typeof rule.match === 'function' && typeof rule.run === 'function') {
        const match = await rule.match(t, ctx)
        if (!match) continue

        await rule.run(t, ctx, match)
        return { handled: true, id: rule.id || 'handler' }
      }
    } catch (e) {
      console.error('[speechRouter] rule error:', rule?.id || rule, e)
      // 單一規則錯誤不要中斷整個語音流程
      continue
    }
  }

  return { handled: false }
}
export const handle = handleSpeech
