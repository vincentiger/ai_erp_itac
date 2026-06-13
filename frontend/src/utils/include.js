// frontend/src/utils/include.js
//共用字型 loader
import fontUrl from '@/assets/fonts/NotoSansTC-Regular.ttf?url'
import { jsPDF } from 'jspdf'
import autoTableImport from 'jspdf-autotable'
const autoTable = autoTableImport?.default || autoTableImport?.autoTable || autoTableImport

/**
 * 將各種日期值轉成 yyyy-mm-dd
 * - 支援 Date 物件
 * - 支援 ISO 字串 (2025-01-01T00:00:00)
 * - 已是 yyyy-mm-dd 會直接回傳
 */
export function fmtDateYMD(v) {
  if (!v) return ''

  // 已經是 yyyy-mm-dd
  if (typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v)) {
    return v
  }

  const d = (v instanceof Date) ? v : new Date(v)
  if (isNaN(d.getTime())) return String(v)

  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

// =====================================================
// 數值 / 百分比 / 安全除法（共用）
// =====================================================

export function safeDiv(a, b) {
  const x = Number(a || 0)
  const y = Number(b || 0)
  return y === 0 ? 0 : x / y
}

export function fmtInt(v) {
  const n = Number(v || 0)
  return Number.isFinite(n) ? n.toLocaleString() : '0'
}

/**
 * 數量格式化（預設 2 位小數，可覆寫）
 *
 * @param {number|string} v
 * @param {Object} [opt]
 * @param {number} [opt.min=2]  最少小數位（預設 2）
 * @param {number} [opt.max=2]  最多小數位（預設 2）
 */
export function fmtQty(v, opt = {}) {
  const n = Number(v || 0)
  if (!Number.isFinite(n)) return '0.00'

  const {
    min = 2,
    max = 2,
  } = opt

  return n.toLocaleString(undefined, {
    minimumFractionDigits: min,
    maximumFractionDigits: max,
  })
}

export function fmtMoney(v) {
  const n = Number(v || 0)
  return Number.isFinite(n)
    ? n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    : '0.00'
}

export function fmtPct(v) {
  const n = Number(v || 0)
  return Number.isFinite(n)
    ? (n * 100).toFixed(1) + '%'
    : '0.0%'
}




let _fontB64 = null
async function fetchAsBase64(url) {
  const res = await fetch(url)
  const buf = await res.arrayBuffer()
  const bytes = new Uint8Array(buf)

  let binary = ''
  const chunk = 0x8000
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk))
  }
  return btoa(binary)
}

export async function ensureNotoSansTC(doc) {
  if (!_fontB64) {
    _fontB64 = await fetchAsBase64(fontUrl)
  }
  // ✅ 每個 doc 都要註冊一次（doc 是新建的）
  doc.addFileToVFS('NotoSansTC-Regular.ttf', _fontB64)
  doc.addFont('NotoSansTC-Regular.ttf', 'NotoSansTC', 'normal')
}
/**
 * 匯出 PDF（支援中文 + 方向 + A4/A3）
 *
 * @param {Object} opt
 * @param {string} opt.filename  例：ai_lines_open_2026-01-27.pdf（不含副檔名也可）
 * @param {'portrait'|'landscape'} [opt.orientation='portrait']
 * @param {'a4'|'a3'} [opt.format='a4']
 * @param {string} [opt.title]   PDF 標題（可選）
 * @param {string[]} opt.headers 欄位標題（單列）
 * @param {(string|number|null|undefined)[][]} opt.rows 資料列（純值矩陣）
 * @param {Object} [opt.table]   autoTable 進階設定（可選）
 */

//共用 PDF 匯出器
export async function exportTablePDF(opt) {
  const {
    filename,
    orientation = 'portrait',
    format = 'a4',
    title = '',
    headers,
    rows,
    table = {},
  } = opt

  if (!rows || !rows.length) throw new Error('沒有資料可匯出')

  const o = (orientation === 'landscape' || orientation === 'l') ? 'landscape' : 'portrait'
  const f = (format === 'a3' || format === 'A3') ? 'a3' : 'a4'
  const doc = new jsPDF({ unit: 'pt', format: f, orientation: o })

  // ✅ 中文字型：每個 doc 都要註冊一次
  await ensureNotoSansTC(doc)
  doc.setFont('NotoSansTC', 'normal')

  // ✅ 標題（可選）
  let startY = 30
  if (title) {
    doc.setFontSize(14)
    doc.text(String(title), 20, 22)
    startY = 34
  }

  autoTable(doc, {
    head: [headers],
    body: rows,
    startY,
    margin: { top: 30, left: 20, right: 20 },
    tableWidth: 'auto',

    // ✅ 先鎖字型，再允許外部 table 覆寫其他設定
    styles: {
      font: 'NotoSansTC',
      fontStyle: 'normal',
      fontSize: 8,
      cellPadding: 2,
      ...(table.styles || {}),
    },
    headStyles: {
      font: 'NotoSansTC',
      fontStyle: 'normal',
      fontSize: 8,
      ...(table.headStyles || {}),
    },
    bodyStyles: {
      font: 'NotoSansTC',
      fontStyle: 'normal',
      ...(table.bodyStyles || {}),
    },

    columnStyles: table.columnStyles || undefined,
    didParseCell: table.didParseCell || undefined,

    // ✅ 有些版本在換頁/畫頁時會被重設 font：每頁再鎖一次
    didDrawPage: (data) => {
      doc.setFont('NotoSansTC', 'normal')
      if (typeof table.didDrawPage === 'function') table.didDrawPage(data)
    },

    // ✅ 讓你可以傳 theme/pageBreak 等其他 autoTable 參數（但不覆蓋掉上面鎖字型）
    ...Object.fromEntries(
      Object.entries(table).filter(([k]) =>
        !['styles', 'headStyles', 'bodyStyles', 'columnStyles', 'didParseCell', 'didDrawPage'].includes(k)
      )
    ),
  })

  const name = filename.toLowerCase().endsWith('.pdf') ? filename : `${filename}.pdf`
  doc.save(name)
}

function csvEscape(v) {
  const s = String(v ?? '')
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

/**
 * 匯出 CSV（Excel 可直接開；含 BOM 避免中文亂碼）
 * @param {Object} opt
 * @param {string} opt.filename 例：ai_lines_open_2026-01-27.csv
 * @param {string[]} opt.headers
 * @param {(string|number|null|undefined)[][]} opt.rows
 */
export function exportTableCSV(opt) {
  const { filename, headers, rows } = opt
  if (!rows || !rows.length) throw new Error('沒有資料可匯出')

  const lines = []
  lines.push(headers.map(csvEscape).join(','))
  for (const r of rows) {
    lines.push(r.map(csvEscape).join(','))
  }

  // ✅ BOM：Excel 中文不亂碼
  const csv = '\uFEFF' + lines.join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const name = filename.toLowerCase().endsWith('.csv') ? filename : `${filename}.csv`
  downloadBlob(blob, name)
}
