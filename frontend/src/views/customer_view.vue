<template>
  <div class="min-h-screen bg-slate-50 overflow-hidden">
    <!-- ✅ Loading overlay（置頂最上層、置中） -->
    <div
      v-if="loading"
      class="fixed inset-0 z-[9999] flex items-start justify-center pt-24 bg-black/10"
    >
      <div class="rounded-2xl bg-white border border-slate-200 shadow-xl px-5 py-3 text-sm font-semibold text-slate-700">
        載入中…
      </div>
    </div>

    <main class="mx-auto w-[92vw] max-w-[1400px] pt-4 pb-6">

      <!-- ✅ Grid 卡片（外層不 scroll，grid 自己 scroll） -->
      <section class="bg-white border border-slate-200 overflow-hidden">
        <div class="px-4 py-3 flex items-center justify-between border-b border-slate-200">
          <!-- 左側標題：手機隱藏 -->
          <div class="font-semibold text-slate-900 hidden sm:block">
            客戶列表
          </div>
          <!-- 右側工具 -->
          <div class="fixed-tools-wrap">
            <div class="fixed-tools-inner">
              <button
                class="tool-btn"
                type="button"
                title="使用說明"
                @click="openManualPdf('客戶管理.pdf')"
              >
                <span class="tool-text hidden md:inline">使用說明</span>
                <span class="tool-text md:hidden">說明</span>
              </button>
              <div class="fixed-search inline-search">
                <input
                  ref="searchInputRef"
                  class="input-group-field"
                  placeholder="搜尋：客戶代號 / 公司 / 簡稱 / 電話 / 地址…"
                  inputmode="text"
                  v-model="kw"
                  @keydown.enter="goFirstPageAndReload"
                />
              </div>

              <button
                class="tool-btn tool-btn-search"
                type="button"
                :disabled="loading"
                title="搜尋"
                @click="goFirstPageAndReload"
              >
                <svg viewBox="0 0 24 24" class="icon-search" aria-hidden="true">
                  <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/>
                  <line x1="16.5" y1="16.5" x2="21" y2="21" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span class="tool-text hidden md:inline">搜尋</span>
              </button>

              <!-- Excel -->
              <button
                class="tool-btn tool-btn-excel"
                :disabled="loading"
                @click="exportCsvAll"
                type="button"
                title="匯出 Excel（全部資料）"
              >
                <!-- (你的 SVG 原封不動) -->
                <svg viewBox="0 0 48 48" class="icon-search" aria-hidden="true">
                  <path fill="#107C41" d="M28 4H10a2 2 0 0 0-2 2v36a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2V14L28 4z"/>
                  <path fill="#21A366" d="M28 4v10h10z"/>
                  <path fill="#ffffff" d="M14.5 18h4.2l3.1 5.1 3.2-5.1h4.2l-5.2 8 5.4 8h-4.3l-3.3-5.4-3.3 5.4h-4.3l5.4-8z"/>
                </svg>
                <span class="tool-text hidden md:inline">匯出 Excel</span>
              </button>
            </div>
          </div>
        </div>

        <!-- ✅ 表格 scroll 容器：固定高度 -->
        <div class="table-scroll">
          <table class="grid-table w-full text-sm">
            <thead class="sticky top-0 z-10 bg-slate-50 text-slate-600">
              <tr>
                <th v-if="mode === 'delete'" class="th" style="width:56px;min-width:56px;max-width:56px;">
                  刪除
                </th>
                <!-- ✅ 欄位要可調寬：th 用 style + resizer -->
                <th class="th" :style="colStyle('refno')">
                  客戶代號
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'refno')"></i>
                </th>

                <th class="th" :style="colStyle('company')">
                  公司名稱
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'company')"></i>
                </th>

                <th class="th" :style="colStyle('short')">
                  簡稱
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'short')"></i>
                </th>

                <th class="th" :style="colStyle('Address')">
                  地址
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'Address')"></i>
                </th>

                <th class="th" :style="colStyle('tel')">
                  電話
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'tel')"></i>
                </th>

                <th class="th" :style="colStyle('ceo')">
                  負責人
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'ceo')"></i>
                </th>

                <th class="th" :style="colStyle('country')">
                  國家
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'country')"></i>
                </th>

                <th class="th" :style="colStyle('payment')">
                  付款方式
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'payment')"></i>
                </th>

                <th class="th" :style="colStyle('credit')">
                  信用額度
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'credit')"></i>
                </th>

                <th class="th" :style="colStyle('sales_rep')">
                  業務代表
                  <i class="col-resizer" @mousedown.prevent="startResize($event,'sales_rep')"></i>
                </th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="(r, idx) in displayRows"
                :key="`${r.refno}-${idx}`"
                class="tr hover:bg-slate-100"
                :class="rowClass(r)"
              >
                <td v-if="mode === 'delete'" class="td text-center" style="width:56px;min-width:56px;max-width:56px;">
                  <input type="checkbox" v-model="selectedRefnos" :value="r.refno" />
                </td>
                <td class="td" :style="colStyle('refno')">
                  <template v-if="r.__d.refno">
                    <a
                      href="javascript:void(0)"
                      class="text-[#5F1CB9]  font-semibold hover:underline"
                      @click="goEdit(r.refno)"
                    >
                      {{ r.__d.refno }}
                    </a>
                  </template>
                </td>

                <td class="td" :style="colStyle('company')">{{ r.__d.company }}</td>
                <td class="td" :style="colStyle('short')">{{ r.__d.short }}</td>
                <td class="td td-multiline" :style="colStyle('Address')">
                  {{ safeMultiline(r.__d.Address) }}
                </td>
                <td class="td" :style="colStyle('tel')">{{ r.__d.tel }}</td>
                <td class="td" :style="colStyle('ceo')">{{ r.__d.ceo }}</td>
                <td class="td" :style="colStyle('country')">{{ r.__d.country }}</td>
                <td class="td" :style="colStyle('payment')">{{ r.__d.payment }}</td>
                <td class="td" :style="colStyle('credit')">{{ r.__d.credit }}</td>
                <td class="td" :style="colStyle('sales_rep')">{{ r.__d.sales_rep }}</td>
              </tr>

              <tr v-if="!loading && rows.length === 0">
                <td class="px-3 py-8 text-center text-slate-500" :colspan="10">
                  無資料
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- ✅ Pagination：用明確函式，避免換頁出錯 -->
        <div class="px-4 py-3 flex items-center justify-between border-t border-slate-200">
          <div class="text-xs text-slate-500">
            第 {{ page }} 頁 / 每頁 {{ pageSize }} 筆
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="mode === 'delete'"
              class="h-9 px-3 bg-rose-600 text-white disabled:opacity-40"
              :disabled="loading || selectedRefnos.length === 0"
              @click="deleteSelected"
              type="button"
            >
              刪除勾選
            </button>
            <button
              class="h-9 px-3  bg-white disabled:opacity-40 flex items-center gap-2"
              :disabled="page <= 1 || loading"
              @click="goPrev"
              type="button"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 18l-6-6 6-6" />
              </svg>
              上一頁
            </button>
            <button
              class="h-9 px-3  bg-white disabled:opacity-40 flex items-center gap-2"
              :disabled="!hasNext || loading"
              @click="goNext"
              type="button"
            >
              下一頁
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 6l6 6-6 6" />
              </svg>
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>


<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiFetch } from '@/utils/apiFetch'

const props = defineProps({
  mode: { type: String, default: 'view' },
})

const router = useRouter()
const route = useRoute()
function openManualPdf(fileName) {
  if (!fileName) return
  const target = `${import.meta.env.BASE_URL}manuals/${encodeURIComponent(String(fileName))}`
  window.open(target, '_blank', 'noopener')
}
const mode = computed(() => String(props.mode || 'view').trim().toLowerCase())

console.log('[customer_view] script setup loaded', location.href)

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const kw = ref('')
const page = ref(1)
const pageSize = ref(20)
const selectedRefnos = ref([])
let hasLoadedOnce = false

// ✅ 下一頁判斷：有 total 就用 total，沒有就用本頁筆數推測
const hasNext = computed(() => {
  if (total.value > 0) return page.value * pageSize.value < total.value
  return rows.value.length === pageSize.value
})

async function reload() {
  loading.value = true
  try {
    const qs = new URLSearchParams({
      kw: kw.value || '',
      page: String(page.value),
      pageSize: String(pageSize.value),
    }).toString()

    const url = `/ai/api/customer/list?${qs}`
    console.log('[customer_view] fetch =>', url)

    // ✅ 統一走 apiFetch：自動帶 token + credentials
    const resp = await apiFetch(url, { method: 'GET' })

    const ct = resp.headers.get('content-type') || ''
    console.log('[customer_view] status=', resp.status, 'content-type=', ct)

    let payload
    if (ct.includes('application/json')) {
      payload = await resp.json()
    } else {
      const text = await resp.text()
      console.log('[customer_view] non-json response head=', text.slice(0, 200))
      throw new Error('API did not return JSON (likely rewrite/proxy returned HTML)')
    }

    console.log('[customer_view] json=', payload)

    // ✅ 後端若回 {ok:false,msg:"Token is missing"} 也會走到這
    if (!resp.ok || payload?.ok === false) {
      throw new Error(payload?.msg || `HTTP ${resp.status}`)
    }

    const data = payload.data || payload
    rows.value = data.rows || data.items || data.list || []
    total.value = data.total ?? rows.value.length ?? 0
    selectedRefnos.value = selectedRefnos.value.filter(refno => rows.value.some(row => row.refno === refno))
  } catch (e) {
    console.error('[customer_view] reload error:', e)
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
  return rows.value
}

// ✅ 搜尋：回到第一頁再 reload（避免「在第 N 頁搜尋」造成以為沒資料）
function goFirstPageAndReload() {
  page.value = 1
  reload()
}

// ✅ 分頁（不要 inline page-- 再 reload，改成明確函式）
function goPrev() {
  if (page.value <= 1 || loading.value) return
  page.value -= 1
  reload()
}

function goNext() {
  if (!hasNext.value || loading.value) return
  page.value += 1
  reload()
}

// ✅ 點 refno 進編輯（先用 querystring；之後你也可改 postMessage）
function goEdit(refno) {
  const r = String(refno || '').trim()
  if (!r) return

  // ✅ 用 router.push，才能留在 MainDashboard iframe 裡，不會整頁跳走
  router.push({
    name: 'customer_create',
    query: {
      refno: r,
      from: mode.value === 'delete' ? 'customer_del' : 'customer_edit',
    },
  })
}

async function deleteSelected() {
  const refnos = Array.from(new Set(selectedRefnos.value.map(v => String(v || '').trim()).filter(Boolean)))
  if (!refnos.length) return
  if (!window.confirm(`確定要刪除 ${refnos.length} 筆客戶資料？`)) return

  loading.value = true
  try {
    const resp = await apiFetch('/ai/api/form/customer_create/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refnos }),
    })
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) {
      throw new Error(payload?.msg || `HTTP ${resp.status}`)
    }
    selectedRefnos.value = []
    await reload()
  } catch (e) {
    console.error('[customer_view] deleteSelected error:', e)
    window.alert(String(e?.message || e))
  } finally {
    loading.value = false
  }
}

function first(v) {
  if (Array.isArray(v)) return (v.find(x => String(x ?? '').trim()) ?? '').toString()
  return String(v ?? '').trim()
}

function fmtNum(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return ''
  return n.toLocaleString()
}
async function exportCsvAll() {
  // 匯出時用相同搜尋條件（kw）
  const pageSizeExport = 5000  // 你可以調大/調小（看後端允許）
  const all = []

  loading.value = true
  try {
    // 先抓第 1 頁，順便拿 total
    const first = await fetchPage(1, pageSizeExport)
    const totalRows = first.total ?? 0
    all.push(...first.rows)

    // 若後端沒給 total，就用「回來筆數 < pageSize」當終止
    if (totalRows > 0) {
      const totalPages = Math.ceil(totalRows / pageSizeExport)
      for (let p = 2; p <= totalPages; p++) {
        const res = await fetchPage(p, pageSizeExport)
        all.push(...res.rows)
      }
    } else {
      // 沒 total：一頁一頁抓到沒滿為止
      let p = 2
      while (first.rows.length === pageSizeExport) {
        const res = await fetchPage(p, pageSizeExport)
        if (!res.rows.length) break
        all.push(...res.rows)
        if (res.rows.length < pageSizeExport) break
        p += 1
      }
    }

    // ✅ 依你目前畫面邏輯排序（company -> refno）
    const list = Array.isArray(all) ? [...all] : []
    sortRows(list) // 你前面已經有 sortRows(list)

    // ✅ 匯出欄位（保留完整值，不用 displayRows、不空白化）
    const headers = [
      'refno','company','short','Address','tel','ceo','country','payment','credit','sales_rep'
    ]

    const lines = []
    lines.push(headers.map(csvEscape).join(','))

    for (const r of list) {
      const row = [
        r?.refno ?? '',
        r?.company ?? '',
        r?.short ?? '',
        normFirst(r?.Address),
        normFirst(r?.tel),
        r?.ceo ?? '',
        r?.country ?? '',
        r?.payment ?? '',
        r?.credit ?? '',
        r?.sales_rep ?? '',
      ].map(csvEscape)

      lines.push(row.join(','))
    }

    const csv = '\uFEFF' + lines.join('\r\n') // BOM：Excel 開啟不亂碼
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `customer_all_${new Date().toISOString().slice(0,10)}.csv`
    a.click()
    URL.revokeObjectURL(a.href)

  } catch (e) {
    console.error('[customer_view] exportCsvAll error:', e)
  } finally {
    loading.value = false
  }
}

// 抽出來：抓某一頁（沿用你的 API 格式）
async function fetchPage(p, ps) {
  const qs = new URLSearchParams({
    kw: kw.value || '',
    page: String(p),
    pageSize: String(ps),
  }).toString()

  const url = `/ai/api/customer/list?${qs}`

  // ✅ 匯出也要帶 token，否則一樣 Token is missing
  const resp = await apiFetch(url, { method: 'GET' })

  const ct = resp.headers.get('content-type') || ''
  if (!ct.includes('application/json')) {
    const text = await resp.text()
    throw new Error('API did not return JSON: ' + text.slice(0, 120))
  }

  const payload = await resp.json()
  if (!resp.ok || payload?.ok === false) {
    throw new Error(payload?.msg || `HTTP ${resp.status}`)
  }

  const data = payload.data || payload
  const rows = data.rows || data.items || data.list || []
  const total = data.total ?? 0
  return { rows, total }
}
function csvEscape(v) {
  const s = String(v ?? '')
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s
}

function normScalar(v) {
  return String(v ?? '').trim()
}

function normFirst(v) {
  if (Array.isArray(v)) return (v.find(x => String(x ?? '').trim()) ?? '').toString().trim()
  return String(v ?? '').trim()
}

// ✅ formatterFactory：回傳「欄位處理器」
// - onlyUnderSameCompany: 只在同公司下才比較/隱藏
function formatterFactory(field, { onlyUnderSameCompany = true, useFirst = false } = {}) {
  const get = (r) => {
    if (useFirst) return normFirst(r?.[field])
    return normScalar(r?.[field])
  }

  return (curRow, prevRow, sameCompany) => {
    const cur = get(curRow)
    if (!prevRow) return cur
    if (onlyUnderSameCompany && !sameCompany) return cur
    const prev = get(prevRow)
    return (cur && cur === prev) ? '' : cur
  }
}


function exportCsvRaw() {
  // 依你表格目前顯示的欄位匯出（原始值）
  const headers = [
    'refno','company','short','Address','tel','ceo','country','payment','credit','sales_rep'
  ]

  const lines = []
  lines.push(headers.map(csvEscape).join(','))

  // 匯出原始 rows（不空白化），但也按目前排序輸出更直覺
  const list = Array.isArray(rows.value) ? [...rows.value] : []
  sortRows(list)

  for (const r of list) {
    const row = [
      r?.refno ?? '',
      r?.company ?? '',
      r?.short ?? '',
      normFirst(r?.Address),  // Address/tel 若是 array，匯出也取第一個非空
      normFirst(r?.tel),
      r?.ceo ?? '',
      r?.country ?? '',
      r?.payment ?? '',
      r?.credit ?? '',
      r?.sales_rep ?? '',
    ].map(csvEscape)

    lines.push(row.join(','))
  }

  const csv = '\uFEFF' + lines.join('\r\n') // BOM: Excel 直接開中文不亂碼
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `customer_${new Date().toISOString().slice(0,10)}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

/* =========================
   Column resize
========================= */
const colWidth = reactive({
  refno: 120,
  company: 240,
  short: 120,
  Address: 260,
  tel: 160,
  ceo: 140,
  country: 110,
  payment: 140,
  credit: 120,
  sales_rep: 160,
})

function colStyle(key) {
  const w = Number(colWidth[key] || 120)
  return { width: w + 'px', minWidth: w + 'px', maxWidth: w + 'px' }
}

function safeMultiline(value) {
  return String(value ?? '').replace(/<br\s*\/?>/gi, '\n')
}

let _rsKey = ''
let _rsStartX = 0
let _rsStartW = 0

function startResize(e, key) {
  _rsKey = key
  _rsStartX = e.clientX
  _rsStartW = Number(colWidth[key] || 120)

  document.addEventListener('mousemove', onResizing)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizing(e) {
  if (!_rsKey) return
  const dx = e.clientX - _rsStartX
  const next = Math.max(80, _rsStartW + dx) // ✅ 最小寬度 80
  colWidth[_rsKey] = next
}

function stopResize() {
  _rsKey = ''
  document.removeEventListener('mousemove', onResizing)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// ✅ 定義你要「連續重複就空白」的欄位規則（含 company）
const fmt = {
  refno:     formatterFactory('refno', { onlyUnderSameCompany: true }),
  company:   formatterFactory('company',   { onlyUnderSameCompany: true }),
  short:     formatterFactory('short',     { onlyUnderSameCompany: true }),
  Address:   formatterFactory('Address',   { onlyUnderSameCompany: true, useFirst: true }),
  tel:       formatterFactory('tel',       { onlyUnderSameCompany: true, useFirst: true }),
  ceo:       formatterFactory('ceo',       { onlyUnderSameCompany: true }),
  country:   formatterFactory('country',   { onlyUnderSameCompany: true }),
  payment:   formatterFactory('payment',   { onlyUnderSameCompany: true }),
  credit:    (cur, prev, sameCompany) => {
    const curTxt = fmtNum(cur?.credit)
    if (!prev) return curTxt
    if (!sameCompany) return curTxt
    const prevTxt = fmtNum(prev?.credit)
    return (curTxt && curTxt === prevTxt) ? '' : curTxt
  },
  sales_rep: formatterFactory('sales_rep', { onlyUnderSameCompany: true }),
}

// ✅ 決定「連續」的排序：為了同公司下才隱藏，建議先 company 再 refno
function sortRows(list) {
  return list.sort((a, b) => {
    const ac = normScalar(a?.company)
    const bc = normScalar(b?.company)
    const cmp1 = ac.localeCompare(bc, 'zh-Hant', { numeric: true })
    if (cmp1 !== 0) return cmp1

    const ar = normScalar(a?.refno)
    const br = normScalar(b?.refno)
    return ar.localeCompare(br, 'zh-Hant', { numeric: true })
  })
}

// ✅ 顯示用 rows：同公司下，欄位各自連續相同就空白；公司群組第一筆加線/交錯底色
const displayRows = computed(() => {
  const list = Array.isArray(rows.value) ? [...rows.value] : []
  // ✅ 不要排序，完全用 API 給的順序
  // sortRows(list)

  let group = -1

  return list.map((r, i) => {
    const prev = i > 0 ? list[i - 1] : null
    const company = normScalar(r?.company)
    const prevCompany = normScalar(prev?.company)
    const sameCompany = !!prev && company && company === prevCompany
    const isCompanyStart = !prev || company !== prevCompany
    if (isCompanyStart) group += 1

    return {
      ...r,
      __d: {
        refno:   fmt.refno(r, prev, sameCompany),
        company: fmt.company(r, prev, sameCompany),
        short: fmt.short(r, prev, sameCompany),
        Address: fmt.Address(r, prev, sameCompany),
        tel: fmt.tel(r, prev, sameCompany),
        ceo: fmt.ceo(r, prev, sameCompany),
        country: fmt.country(r, prev, sameCompany),
        payment: fmt.payment(r, prev, sameCompany),
        credit: fmt.credit(r, prev, sameCompany),
        sales_rep: fmt.sales_rep(r, prev, sameCompany),
      },
      __companyStart: isCompanyStart,
      __group: group,
    }
  })
})

function rowClass(r) {
  const zebra = (r.__group % 2 === 0) ? 'bg-white' : 'bg-slate-50'
  const startLine = r.__companyStart ? 'row-start' : ''
  return [zebra, startLine].join(' ').trim()
}



const voiceKey = ref('')
const voiceFields = ref([])     // e.g. ['refno','company','short'] or ['address']
const voiceAuto = ref('0')      // '1' or '0'

// ✅ 你主系統的 origin（同網域就用 window.location.origin 也行）
const lastVoice = ref({ key: '', fields: [], auto: '0' })
const ALLOWED_ORIGINS = new Set([
  window.location.origin
  // 'https://www.volx.com:8080', // 若 parent 在不同網域再加
])

function normalizeFields(fields) {
  const arr = Array.isArray(fields)
    ? fields
    : String(fields || '').split(',').map(s => s.trim()).filter(Boolean)

  const map = {
    '地址': 'address',
    '電話': 'tel',
    '聯絡人': 'contact',
  }
  return arr.map(x => map[x] || x).filter(Boolean)
}

// ✅ 讓 reload() 能回傳 rows，才可以做到 auto=1 單筆自動開啟
// （不改你原本邏輯，只是在最後 return rows）
async function reloadAndReturnRows() {
  await reload()
  return Array.isArray(rows.value) ? rows.value : []
}

async function doSearchFromVoice({ key, fields, auto }) {
  const rawKey = String(key ?? '')
  const k = rawKey.trim()
  const a = String(auto ?? '0')
  const f = normalizeFields(fields)

  // ✅ debug：確認 iframe 真的收到 key
  console.log('[customer_view] doSearchFromVoice rawKey=', rawKey, 'k=', k, 'fields=', f, 'auto=', a)

  if (!k) {
    console.warn('[customer_view] doSearchFromVoice: empty key -> skip')
    return
  }

  // ✅ 保險：如果 key 還是整句（例如「客戶查詢 39001」），先簡單清掉前導詞
  // （你未來 registry parse 會更精準，這裡先做防呆）
  const cleaned = k.replace(/^(客戶查詢|查詢客戶|搜尋客戶|請找出客戶)\s*/g, '').trim()

  // 記錄（debug 用）
  lastVoice.value = { key: cleaned, fields: f, auto: a }

  // ✅ 用 kw 完成查詢
  kw.value = cleaned
  page.value = 1

  console.log('[customer_view] set kw=', kw.value, '=> reload()')
  const list = await reloadAndReturnRows()
  console.log('[customer_view] reload result rows=', Array.isArray(list) ? list.length : 'N/A')

  // ✅ auto=1 且只有一筆：直接進編輯（等同 loadCustomer）
  if (a === '1' && Array.isArray(list) && list.length === 1) {
    const refno = list[0]?.refno
    console.log('[customer_view] auto=1 single row refno=', refno)
    if (refno) goEdit(refno)
  }
}

//ui

const searchInputRef = ref(null)

let isAlive = true
onBeforeUnmount(() => {
  isAlive = false
})
async function focusSearchSafe() {
  // ✅ 任何錯誤都吞掉，絕對不能 throw（避免 scheduler flush / native handler 爆）
  try {
    if (!isAlive) return
    await nextTick()
    if (!isAlive) return

    const el = searchInputRef.value
    if (!el) return

    // ✅ 支援：原生 input、ElementPlus ElInput、或你自訂元件
    if (typeof el.focus === 'function') el.focus()
    else if (el?.$el && typeof el.$el.focus === 'function') el.$el.focus()

    if (typeof el.select === 'function') el.select()
    else if (el?.$el && typeof el.$el.select === 'function') el.$el.select()
  } catch (e) {
    console.debug('[customer_view] focusSearchSafe ignored:', e)
  }
}

function onMessage(ev) {
  // 同網域通常 OK；若你有跨網域就把 origin 加進白名單
  if (ALLOWED_ORIGINS.size && !ALLOWED_ORIGINS.has(ev.origin)) return

  const msg = ev.data
  if (!msg || typeof msg !== 'object') return

  if (msg.type === 'VOICE_SEARCH') {
    console.log('[customer_view] VOICE_SEARCH msg=', msg)
    doSearchFromVoice(msg.data || {})
  }
}

onMounted(() => {
  console.log('[customer_view] onMounted')

  window.addEventListener('message', onMessage)

  const qs = new URLSearchParams(window.location.search)
  const key = qs.get('key') || ''      // 你原本用 key
  const fields = qs.get('fields') || ''
  const auto = qs.get('auto') || '0'

  if (key) {
    // ✅ 有語音帶進來的 key：用 doSearchFromVoice 接手（它裡面會 reload）
    doSearchFromVoice({ key, fields, auto })
  } else {
    // ✅ 沒帶 key：維持原本行為
    reload()
  }
  hasLoadedOnce = true
  void focusSearchSafe()
})

watch(
  () => route.fullPath,
  () => {
    if (!hasLoadedOnce) return
    page.value = 1
    reload()
  }
)

onUnmounted(() => {
  stopResize()
  window.removeEventListener('message', onMessage)
})

</script>
<style scoped>
/* ✅ 表格 scroll：固定高度，避免外層 div 出現 scrollbar */
.table-scroll{
  height: calc(105vh - 240px); /* 你要更高/更低就調這裡 */
  overflow: auto;
  scrollbar-color: #dddddd #eeeeee; /* Firefox：thumb / track */
  scrollbar-width: thin;
}
/* WebKit: Chrome/Edge/Safari */
.table-scroll::-webkit-scrollbar{
  width: 10px;
  height: 10px;
}
.table-scroll::-webkit-scrollbar-track{
  background: #eeeeee;
}
.table-scroll::-webkit-scrollbar-thumb{
  background: #eeeeee;
  border-radius: 0;               /* ✅ 你偏好直角可保持 0 */
  border: 2px solid #eeeeee;      /* 讓 thumb 看起來不會太粗 */
}
.table-scroll::-webkit-scrollbar-thumb:hover{
  background: #bbbbbb;
}

/* ✅ grid 分隔線 + 固定欄寬 + 可拖拉 */
.grid-table{
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed; /* ✅ 搭配固定欄寬 + 拖拉 */
}

.th, .td{
  padding: 12px;
  border-right: 1px solid #e2e8f0;  /* slate-200 */
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.th{
  font-weight: 700;
}

.td{
  font-size:10pt;
  font-weight:normal;
}

.td-multiline{
  white-space: pre-line;
  line-height: 1.45;
}

/* 最右邊不要多一條 */
.grid-table tr > *:last-child{
  border-right: none;
}

/* ✅ resizer handle */
.col-resizer{
  position: absolute;
  top: 0;
  right: 0;
  width: 8px;
  height: 100%;
  cursor: col-resize;
}
.col-resizer:hover{
  background: rgba(148,163,184,.35); /* slate-400/35% */
}

.input-group-btn {
  background-color: #5F1CB9;
  color: #fff;
}
.icon-search {
  width: 18px;
  height: 18px;
  display: block;
}
/* === 工具列：放在「客戶列表那一行」右側 === */
/* === 工具列：放在「客戶列表那一行」右側 === */
.fixed-tools-wrap {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.fixed-tools-inner {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* 共用按鈕：預設透明 */
.tool-btn {
  height: 36px;
  padding: 0 10px;
  border-radius: 10px;
  background: transparent;
  color: #0f172a;
  border: 1px solid rgba(15, 23, 42, 0.12);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: none;
  transition: background-color .15s ease, border-color .15s ease, color .15s ease;
}

.tool-btn:disabled {
  opacity: .45;
  cursor: not-allowed;
}

/* hover / focus-visible 才變綠 */
.tool-btn:hover:not(:disabled),
.tool-btn:focus-visible:not(:disabled) {
  background: #91C51B;
  border-color: #91C51B;
  color: #ffffff;
  outline: none;
}

/* Excel 按鈕文字 */
.tool-text {
  white-space: nowrap;
}

.fixed-search {
  display: flex;
  align-items: center;
}

/* input 樣式 */
.fixed-search .input-group-field {
  width: min(420px, 46vw);
  height: 40px;
  padding: 0 12px;
  font-size: 12pt;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.14);
  background: #fff;
  outline: none;
}

/* focus */
.fixed-search .input-group-field:focus {
  border-color: #5F1CB9;
  box-shadow: 0 0 0 3px rgba(95, 28, 185, 0.12);
}

/* ✅ 手機板 */
@media (max-width: 640px) {
  .tool-btn {
    height: 34px;
    padding: 0 10px;
    border-radius: 10px;
  }
  .tool-text {
    display: none; /* 手機只留 icon */
  }

  .fixed-search .input-group-field {
    width: min(100vw - 120px, 320px);
  }
}

/* 輔助：無障礙 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
/* 全部 td：黑字、一般字重 */
.td{
  font-size: 10pt;
  font-weight: 400;   /* 一般 */
  color: #333333;        /* 黑字 */
}

/* ✅ 只有第一欄（refno）要粗體黑字 */
.grid-table tbody td:nth-child(1){
  font-weight: 700;
  color: #000;
}

/* ✅ 第一欄裡面的 <a> 也要黑字粗體（蓋過你 template 的紫色 class） */
.grid-table tbody td:nth-child(1) a{
  color: #000 !important;
  font-weight: 700 !important;
  text-decoration: none;
}
/* refno：hover 底線為綠色 */
.grid-table tbody td:nth-child(1) a:hover{
  text-decoration: underline;
  text-decoration-color: #91C51B; /* 綠色底線 */
  text-underline-offset: 3px;     /* 底線離字一點距離（可調） */
}
/* ✅ 公司群組第一筆：上方群組線更明顯 */

</style>
