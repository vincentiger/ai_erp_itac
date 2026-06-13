// src/composables/useLabMechJudge.js

function toNumber(v) {
  if (v === '' || v === null || v === undefined) return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function toInt(v, fallback = 0) {
  const n = parseInt(v, 10)
  return Number.isFinite(n) ? n : fallback
}

/**
 * 四捨六入，五成雙
 * 例：
 * 24.5 -> 24
 * 25.5 -> 26
 */
export function roundHalfEven(value) {
  const n = toNumber(value)
  if (n === null) return null

  const floor = Math.floor(n)
  const diff = n - floor

  if (diff < 0.5) return floor
  if (diff > 0.5) return floor + 1
  return floor % 2 === 0 ? floor : floor + 1
}

export function roundHalfUp(value) {
  const n = toNumber(value)
  if (n === null) return null
  return Math.floor(n + 0.5)
}

export function roundHardnessValue(value, mode = '') {
  return String(mode || '').trim() === '四捨五入'
    ? roundHalfUp(value)
    : roundHalfEven(value)
}

export function calcAverage(values = []) {
  const nums = values.map(toNumber).filter(v => v !== null)
  if (!nums.length) return null
  return nums.reduce((s, x) => s + x, 0) / nums.length
}

export function formatAvg(value, digits = 3) {
  const n = toNumber(value)
  if (n === null) return ''
  return n.toFixed(digits).replace(/\.000$/, '').replace(/(\.\d*?)0+$/, '$1')
}

export function inRange(value, min, max) {
  const v = toNumber(value)
  const mn = toNumber(min)
  const mx = toNumber(max)

  if (v === null) return false
  if (mn !== null && v < mn) return false
  if (mx !== null && v > mx) return false
  return true
}

export function judgeHardnessRow(row, specMin, specMax, roundingMode = '') {
  const avg = calcAverage(row.values || [])
  const judgeValue = roundHardnessValue(avg, roundingMode)
  const ok = inRange(judgeValue, specMin, specMax)

  return {
    ...row,
    avg_value: avg === null ? '' : formatAvg(avg),
    judge_value: judgeValue ?? '',
    result: ok ? 'PASS' : 'FAIL',
    is_out_of_spec: !ok,
  }
}

export function judgeNumericRow(row, specMin, specMax) {
  const value = toNumber(row.value)
  if (value === null) {
    return {
      ...row,
      value: row.value,
      result: '',
      is_out_of_spec: false,
    }
  }
  const ok = inRange(value, specMin, specMax)

  return {
    ...row,
    value: row.value,
    result: ok ? 'PASS' : 'FAIL',
    is_out_of_spec: !ok,
  }
}

export function judgeOkNgRow(row) {
  const status = String(row.status || '').trim().toUpperCase()
  if (!status) {
    return {
      ...row,
      status: '',
      result: '',
      is_out_of_spec: false,
    }
  }
  const ok = status === 'OK'

  return {
    ...row,
    status,
    result: ok ? 'PASS' : 'FAIL',
    is_out_of_spec: !ok,
  }
}

export function judgeDecarbRow(row) {
  const hv1 = toNumber(row.hv1)
  const hv2 = toNumber(row.hv2)
  const hv3 = toNumber(row.hv3)

  if (hv1 === null || hv2 === null || hv3 === null) {
    return {
      ...row,
      hv2_ok: null,
      hv3_ok: null,
      result: '',
    }
  }

  const hv2_ok = hv2 >= hv1 - 30
  const hv3_ok = hv3 <= hv1 + 30
  const ok = hv2_ok && hv3_ok

  return {
    ...row,
    hv2_ok,
    hv3_ok,
    result: ok ? 'PASS' : 'FAIL',
  }
}

export function calcSummaryFromRows(rows = []) {
  const pass_count = rows.filter(r => r.result === 'PASS').length
  const fail_count = rows.filter(r => r.result === 'FAIL').length
  const result = fail_count > 0 ? 'FAIL' : (pass_count > 0 ? 'PASS' : '')

  return { pass_count, fail_count, result }
}

export function judgeHardnessSection(section) {
  const rows = (section.rows || []).map(row =>
    judgeHardnessRow(row, section.spec_min, section.spec_max, section.spec_text)
  )

  return {
    rows,
    summary: calcSummaryFromRows(rows),
  }
}

export function judgeNumericSection(section) {
  const rows = (section.rows || []).map(row =>
    judgeNumericRow(row, section.spec_min, section.spec_max)
  )

  return {
    rows,
    summary: calcSummaryFromRows(rows),
  }
}

export function judgeOkNgSection(section) {
  const rows = (section.rows || []).map(judgeOkNgRow)

  return {
    rows,
    summary: calcSummaryFromRows(rows),
  }
}

export function judgeDecarbSection(section) {
  const rows = (section.rows || []).map(judgeDecarbRow)

  return {
    rows,
    summary: calcSummaryFromRows(rows),
  }
}

export function calcDateTimeByHours(startAt, hours) {
  if (!startAt || hours === '' || hours === null || hours === undefined) return ''

  const dt = new Date(String(startAt).replace(' ', 'T'))
  if (Number.isNaN(dt.getTime())) return ''

  const h = toInt(hours, 0)
  dt.setHours(dt.getHours() + h)

  const yyyy = dt.getFullYear()
  const mm = String(dt.getMonth() + 1).padStart(2, '0')
  const dd = String(dt.getDate()).padStart(2, '0')
  const hh = String(dt.getHours()).padStart(2, '0')
  const mi = String(dt.getMinutes()).padStart(2, '0')
  const ss = String(dt.getSeconds()).padStart(2, '0')

  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

export function judgeSaltSprayData(data = {}) {
  const specHours = toNumber(data.spec_hours)
  const whiteSpecHours = toNumber(data.white_spec_hours)
  const redSpecHours = toNumber(data.red_spec_hours)
  const actualHours = toNumber(data.actual_hours)
  const endSpecHours = Math.max(
    ...[specHours, whiteSpecHours, redSpecHours].filter(value => value !== null)
  )

  const noRust = toInt(data.no_rust_pcs, 0)
  const whiteRust = toInt(data.white_rust_pcs, 0)
  const redRust = toInt(data.red_rust_pcs, 0)

  let result = ''
  let is_out_of_spec = false

  const checks = []
  if (whiteSpecHours !== null && actualHours !== null) {
    checks.push(actualHours >= whiteSpecHours && whiteRust === 0)
  }
  if (redSpecHours !== null && actualHours !== null) {
    checks.push(actualHours >= redSpecHours && redRust === 0)
  }
  if (!checks.length && specHours !== null && actualHours !== null) {
    const rustType = String(data.spec_rust_type || 'white').toLowerCase()
    const rustCount = rustType === 'red' ? redRust : whiteRust
    checks.push(actualHours >= specHours && rustCount === 0)
  }
  if (checks.length) {
    result = checks.every(Boolean) ? 'PASS' : 'FAIL'
    is_out_of_spec = result === 'FAIL'
  }

  return {
    ...data,
    spec_hours: specHours ?? whiteSpecHours ?? redSpecHours ?? '',
    white_spec_hours: data.white_spec_hours ?? '',
    red_spec_hours: data.red_spec_hours ?? '',
    end_at: Number.isFinite(endSpecHours) ? calcDateTimeByHours(data.start_at, endSpecHours) : '',
    no_rust_pcs: noRust,
    white_rust_pcs: whiteRust,
    red_rust_pcs: redRust,
    result,
    is_out_of_spec,
    pass_count: noRust,
    fail_count: whiteRust + redRust,
  }
}

export function judgeHydrogenSection(section) {
  const rows = (section.rows || []).map(row => {
    const status = String(row.status || '').trim().toUpperCase()
    const ok = status === 'OK'
    return {
      ...row,
      status,
      result: ok ? 'PASS' : 'FAIL',
    }
  })

  return {
    rows,
    summary: calcSummaryFromRows(rows),
  }
}

export function getOverallSummary(sections = []) {
  const passCount = sections.reduce((s, x) => s + Number(x.pass_count || 0), 0)
  const failCount = sections.reduce((s, x) => s + Number(x.fail_count || 0), 0)
  const judgedSections = sections.filter(x => x.result).length
  const failSections = sections.filter(x => x.result === 'FAIL').length

  return {
    passCount,
    failCount,
    judgedSections,
    failSections,
    finalResult: failSections > 0 ? 'FAIL' : (judgedSections > 0 ? 'PASS' : ''),
  }
}
