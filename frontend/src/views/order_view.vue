<template>
  <div class="min-h-screen bg-slate-50 overflow-hidden">
    <!-- Loading overlay -->
    <div
      v-if="loading"
      class="fixed inset-0 z-[9999] flex items-start justify-center pt-24 bg-black/10"
    >
      <div class="rounded-2xl bg-white border border-slate-200 shadow-xl px-5 py-3 text-sm font-semibold text-slate-700">
        載入中…
      </div>
    </div>

    <main class="mx-auto w-[92vw] max-w-[1400px] pt-4 pb-6">
      <section class="bg-white border border-slate-200 overflow-hidden">
        <div class="px-4 py-3 flex items-center justify-between border-b border-slate-200">
          <div class="font-semibold text-slate-900 hidden sm:block">
            訂單列表
          </div>

          <!-- tools -->
          <div class="fixed-tools-wrap" @mouseenter="onToolsEnter" @mouseleave="onToolsLeave">
            <div class="fixed-tools-inner">
              <!-- Excel -->
              <button
                class="tool-btn tool-btn-excel"
                :disabled="loading"
                @click="exportCsvAll"
                type="button"
                title="匯出 Excel（全部資料）"
              >
                <svg viewBox="0 0 48 48" class="icon-search" aria-hidden="true">
                  <path fill="#107C41" d="M28 4H10a2 2 0 0 0-2 2v36a2 2 0 0 0 2 2h28a2 2 0 0 0 2-2V14L28 4z"/>
                  <path fill="#21A366" d="M28 4v10h10z"/>
                  <path fill="#ffffff" d="M14.5 18h4.2l3.1 5.1 3.2-5.1h4.2l-5.2 8 5.4 8h-4.3l-3.3-5.4-3.3 5.4h-4.3l5.4-8z"/>
                </svg>
                <span class="tool-text hidden md:inline">匯出 Excel</span>
              </button>

              <!-- Search -->
              <button
                class="tool-btn tool-btn-search"
                type="button"
                :disabled="loading"
                title="搜尋"
                @click="toggleSearch"
              >
                <svg viewBox="0 0 24 24" class="icon-search" aria-hidden="true">
                  <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/>
                  <line x1="16.5" y1="16.5" x2="21" y2="21" stroke="currentColor" stroke-width="2"/>
                </svg>
                <span class="sr-only">搜尋</span>
              </button>
            </div>

            <!-- ✅ 進階搜尋面板（改成新 key） -->
            <div class="fixed-search" :class="{ show: showSearch }">
              <div class="p-3 bg-white border border-slate-200 rounded-xl shadow-md w-[min(680px,92vw)]">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input
                    ref="searchInputRef"
                    class="input-group-field"
                    placeholder="關鍵字：PI / 客戶 / 客戶單號 / 抬頭 / 業務…"
                    v-model="f_kw"
                    @keydown.enter="goFirstPageAndReload"
                  />
                  <input
                    class="input-group-field"
                    placeholder="客戶名稱"
                    v-model="f_company"
                    @keydown.enter="goFirstPageAndReload"
                  />

                  <input
                    class="input-group-field"
                    placeholder="公司別"
                    v-model="f_company_title"
                    @keydown.enter="goFirstPageAndReload"
                  />
                  <input
                    class="input-group-field"
                    placeholder="業務代表"
                    v-model="f_sales_rep"
                    @keydown.enter="goFirstPageAndReload"
                  />

                  <input
                    class="input-group-field"
                    type="date"
                    v-model="f_date_from"
                    title="起日"
                  />
                  <input
                    class="input-group-field"
                    type="date"
                    v-model="f_date_to"
                    title="迄日"
                  />
                </div>

                <div class="flex items-center justify-end gap-2 mt-3">
                  <button class="h-9 px-3 bg-white border border-slate-200" type="button" :disabled="loading" @click="clearFilters">
                    清除
                  </button>
                  <button class="h-9 px-3 bg-white border border-slate-200" type="button" :disabled="loading" @click="goFirstPageAndReload">
                    套用搜尋
                  </button>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- table -->
        <div class="table-scroll">
          <table class="grid-table w-full text-sm">
            <thead class="sticky top-0 z-10 bg-slate-50 text-slate-600">
              <tr>
                <th
                  v-for="c in columns"
                  :key="c.key"
                  class="th"
                  :class="[
                    isSortable(c.key) ? 'th-sortable' : 'th-nosort'
                  ]"
                  :style="colStyle(c.key)"
                  @click="onHeaderClick(c.key)"
                >
                  <span class="th-label">{{ c.label }}</span>

                  <!-- ✅ 只有可排序欄位才顯示 sort icon -->
                  <SortIcon v-if="isSortable(c.key)" :active="sortBy===c.key" :dir="sortDir" />

                  <i class="col-resizer" @mousedown.prevent="startResize($event, c.key)"></i>
                </th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="(r, idx) in displayRows"
                :key="`${r.pi_no || ''}-${r.c_order_no || ''}-${idx}`"
                class="tr hover:bg-slate-100"
                :class="rowClass(r)"
              >
                <td v-for="c in columns" :key="c.key" class="td" :style="colStyle(c.key)">
                  <span
                    :class="{
                      'pi-no': c.key === 'pi_no'
                    }"
                  >
                    <template v-if="c.key === 'amount'">
                      {{ fmtNum(r.__d?.amount ?? r.amount) }}
                    </template>
                    <template v-else>
                      {{ r.__d?.[c.key] ?? r[c.key] ?? '' }}
                    </template>
                  </span>
                </td>
              </tr>

              <tr v-if="!loading && rows.length === 0">
                <td class="px-3 py-8 text-center text-slate-500" :colspan="columns.length">無資料</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- pagination -->
        <div class="px-4 py-3 flex items-center justify-between border-t border-slate-200">
          <div class="text-xs text-slate-500">
            第 {{ page }} 頁 / 每頁 {{ pageSize }} 筆（共 {{ total }} 筆）
          </div>
          <div class="flex items-center gap-2">
            <button
              class="h-9 px-3 bg-white disabled:opacity-40 flex items-center gap-2"
              :disabled="page<=1 || loading"
              @click="goPrev"
              type="button"
            >
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 18l-6-6 6-6" />
              </svg>
              上一頁
            </button>

            <button
              class="h-9 px-3 bg-white disabled:opacity-40 flex items-center gap-2"
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
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, defineComponent, h } from 'vue'
import { fmtDateYMD } from '@/utils/include'

/* ========= SortIcon（不用 JSX，避免 vite plugin jsx 錯誤） ========= */
const SortIcon = defineComponent({
  name: 'SortIcon',
  props: { active: Boolean, dir: String },
  setup(props) {
    const upSvg = () => h('svg', { viewBox:'0 0 24 24', width:'14', height:'14' }, [
      h('path', { d:'M12 7l-6 6h12z', fill:'currentColor' })
    ])
    const downSvg = () => h('svg', { viewBox:'0 0 24 24', width:'14', height:'14' }, [
      h('path', { d:'M12 17l6-6H6z', fill:'currentColor' })
    ])
    const bothSvg = () => h('svg', { viewBox:'0 0 24 24', width:'14', height:'14', style:{ opacity:'.35' } }, [
      h('path', { d:'M12 7l-6 6h12z', fill:'currentColor' }),
      h('path', { d:'M12 17l6-6H6z', fill:'currentColor' }),
    ])

    return () => h('span', { style:{
      marginLeft:'6px', display:'inline-flex', verticalAlign:'middle', opacity:'0.75'
    }}, props.active ? (props.dir === 'asc' ? upSvg() : downSvg()) : bothSvg())
  }
})

/* ========= 欄位順序（你指定的） ========= */
const columns = [
  { key: 'company',        label: '客戶名稱' },
  { key: 'pi_no',          label: 'PI 編號' },
  { key: 'c_order_no',     label: '客戶訂單編號' },
  { key: 'original_date',  label: '訂單日期' },
  { key: 'currency',       label: '幣別' },
  { key: 'amount',         label: '訂單金額' },
  { key: 'sales_rep',      label: '業務代表' },
  { key: 'company_title',  label: '公司別' },
]

// ✅ 哪些欄位允許排序（不是每個欄位都能排）
const SORTABLE_KEYS = new Set([
  'company',
  'pi_no',
  'c_order_no',      // 訂單編號
  'original_date',
  'currency',
  'amount',
  'sales_rep',
  'company_title',
  // form_no 要不要給排序：你決定，先不放（不放就不能排序）
])

function isSortable(key) {
  return SORTABLE_KEYS.has(key)
}

// ✅ 表頭點擊：不可排序就直接 return
function onHeaderClick(key) {
  if (!isSortable(key)) return
  toggleSort(key) // 沿用你原本的排序切換 + reload 邏輯
}

// ✅ 預設排序：依列表欄位順序（第一欄）
// 如果第一欄不可排序，就往後找第一個可排序欄位
function getDefaultSortKey() {
  // ✅ columns 是一般 array，直接用
  for (const c of columns) {
    if (isSortable(c.key)) return c.key
  }
  return columns?.[0]?.key || 'company'
}

// ✅ 初始值（第一次載入就會用到）
const sortBy = ref(getDefaultSortKey())
const sortDir = ref('asc')

/* ========= state ========= */
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)

/* filters（改成新 key） */
const f_kw = ref('')
const f_company = ref('')
const f_date_from = ref('')
const f_date_to = ref('')
const f_sales_rep = ref('')
const f_company_title = ref('')


const hasNext = computed(() => {
  if (total.value > 0) return page.value * pageSize.value < total.value
  return rows.value.length === pageSize.value
})

function fmtNum(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return ''
  return n.toLocaleString()
}
function cleanSalesRepName(s) {
  s = String(s || '').trim()

  // 去掉常見尾巴詞/時間詞
  s = s.replace(/(所有訂單|全部訂單|所有|全部|訂單|明細|資料|查詢|搜尋|去年|今年|本月|這個月|上月|上個月|近30天|最近30天|三十天內|截至目前|截至今天|到目前為止|至今)/g, '')
  s = s.replace(/\s+/g, '')

  // ✅ 如果上游把「去年」拆壞成「去」，把尾端單字去掉
  s = s.replace(/(去|今)$/, '')

  // 只取 2~4 個中文字
  const m = s.match(/[\u4e00-\u9fff]{2,4}/)
  return m ? m[0] : s
}

function buildQS(p, ps) {
  const qs = new URLSearchParams({
    kw: f_kw.value || '',
    company: f_company.value || '',
    date_from: f_date_from.value || '',
    date_to: f_date_to.value || '',
    sales_rep: cleanSalesRepName(f_sales_rep.value || ''),
    company_title: f_company_title.value || '',
    page: String(p),
    pageSize: String(ps),
    sortBy: sortBy.value || 'original_date',
    sortDir: sortDir.value || 'desc',
  })
  return qs.toString()
}

async function reload() {
  loading.value = true
  try {
    const url = `/api/order/list?${buildQS(page.value, pageSize.value)}`
    console.log('[order_view] fetch =>', url)

    const resp = await fetch(url)
    const ct = resp.headers.get('content-type') || ''
    if (!ct.includes('application/json')) {
      const text = await resp.text()
      throw new Error('API did not return JSON: ' + text.slice(0, 200))
    }

    const payload = await resp.json()
    if (!resp.ok || payload?.ok === false) throw new Error(payload?.msg || `HTTP ${resp.status}`)

    const data = payload.data || payload
    rows.value = Array.isArray(data.rows) ? data.rows : []
    total.value = data.total ?? rows.value.length ?? 0

    // ✅ debug：快速確認 key 是否一致
    console.log('[order_view] first row keys=', rows.value?.[0] ? Object.keys(rows.value[0]) : null)

  } catch (e) {
    console.error('[order_view] reload error:', e)
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function goFirstPageAndReload() {
  page.value = 1
  reload()
}
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

/* ✅ 點表頭排序：同欄位切 asc/desc，不同欄位預設 asc */
function toggleSort(key) {
  if (loading.value) return
  if (sortBy.value === key) {
    sortDir.value = (sortDir.value === 'asc') ? 'desc' : 'asc'
  } else {
    sortBy.value = key
    sortDir.value = 'asc'
  }
  page.value = 1
  reload()
}

/* ========= 匯出（用新欄位 + 新順序） ========= */
function csvEscape(v) {
  const s = String(v ?? '')
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s
}

async function fetchPage(p, ps) {
  const url = `/api/order/list?${buildQS(p, ps)}`
  const resp = await fetch(url)
  const ct = resp.headers.get('content-type') || ''
  if (!ct.includes('application/json')) {
    const text = await resp.text()
    throw new Error('API did not return JSON: ' + text.slice(0, 200))
  }
  const payload = await resp.json()
  if (!resp.ok || payload?.ok === false) throw new Error(payload?.msg || `HTTP ${resp.status}`)
  const data = payload.data || payload
  return { rows: data.rows || [], total: data.total ?? 0 }
}

async function exportCsvAll() {
  const pageSizeExport = 2000
  const all = []
  loading.value = true
  try {
    const first = await fetchPage(1, pageSizeExport)
    const totalRows = first.total ?? 0
    all.push(...first.rows)

    if (totalRows > 0) {
      const totalPages = Math.ceil(totalRows / pageSizeExport)
      for (let p = 2; p <= totalPages; p++) {
        const res = await fetchPage(p, pageSizeExport)
        all.push(...res.rows)
      }
    } else {
      let p = 2
      while (first.rows.length === pageSizeExport) {
        const res = await fetchPage(p, pageSizeExport)
        if (!res.rows.length) break
        all.push(...res.rows)
        if (res.rows.length < pageSizeExport) break
        p += 1
      }
    }

    // ✅ headers 依 columns 順序
    const headers = columns.map(c => c.key)
    const lines = []
    lines.push(headers.map(csvEscape).join(','))

    for (const r of all) {
      const row = headers.map(k => {
        if (k === 'amount') return r?.amount ?? ''
        return r?.[k] ?? ''
      })
      lines.push(row.map(csvEscape).join(','))
    }

    const csv = '\uFEFF' + lines.join('\r\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `order_all_${new Date().toISOString().slice(0,10)}.csv`
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (e) {
    console.error('[order_view] exportCsvAll error:', e)
  } finally {
    loading.value = false
  }
}

/* ========= UI search panel ========= */
const showSearch = ref(false)
const searchInputRef = ref(null)

async function toggleSearch() {
  showSearch.value = !showSearch.value
  if (showSearch.value) {
    await nextTick()
    searchInputRef.value?.focus?.()
  }
}
function onToolsEnter() { showSearch.value = true }
function onToolsLeave() { /* hover 用 CSS 控制 */ }

function clearFilters() {
  f_kw.value = ''
  f_company.value = ''
  f_date_from.value = ''
  f_date_to.value = ''
  f_sales_rep.value = ''
  f_company_title.value = ''
  page.value = 1
  reload()
}

/* ========= VOICE_SEARCH（filters 優先） ========= */
const ALLOWED_ORIGINS = new Set([ window.location.origin ])

function onMessage(ev) {
  if (ALLOWED_ORIGINS.size && !ALLOWED_ORIGINS.has(ev.origin)) return
  const msg = ev.data
  if (!msg || typeof msg !== 'object') return

  if (msg.type === 'VOICE_SEARCH') {
    const d = msg.data || {}
    console.log('[order_view] VOICE_SEARCH msg=', msg)

    if (d.filters && typeof d.filters === 'object') {
      const f = d.filters
      if (f.kw != null) f_kw.value = String(f.kw || '')
      if (f.company != null) f_company.value = String(f.company || '')
      if (f.sales_rep != null) f_sales_rep.value = String(f.sales_rep || '')
      if (f.company_title != null) f_company_title.value = String(f.company_title || '')
      if (f.date_from != null) f_date_from.value = String(f.date_from || '')
      if (f.date_to != null) f_date_to.value = String(f.date_to || '')
      page.value = 1
      reload()
      return
    }

    // fallback：只有 key 就塞 kw
    const key = String(d.key ?? '').trim()
    if (key) {
      f_kw.value = key
      page.value = 1
      reload()
    }
  }
}

onMounted(() => {
  window.addEventListener('message', onMessage)

  // ✅ 讀 URL query（讓 MainDashboard 用 currentUrl 帶參數時立即生效）
  const qs = new URLSearchParams(window.location.search)

  if (qs.has('kw')) f_kw.value = qs.get('kw') || ''
  if (qs.has('cust_name')) f_company.value = qs.get('cust_name') || ''
  if (qs.has('company'))   f_company.value = qs.get('company') || f_company.value
  if (qs.has('sales_rep')) f_sales_rep.value = qs.get('sales_rep') || ''
  if (qs.has('company_title')) f_company_title.value = qs.get('company_title') || ''
  if (qs.has('date_from')) f_date_from.value = qs.get('date_from') || ''
  if (qs.has('date_to')) f_date_to.value = qs.get('date_to') || ''

  // 排序（可選）
  if (qs.has('sortBy')) sortBy.value = qs.get('sortBy') || sortBy.value
  if (qs.has('sortDir')) sortDir.value = qs.get('sortDir') || sortDir.value

  page.value = 1
  reload()
})
onUnmounted(() => {
  window.removeEventListener('message', onMessage)
  stopResize()
})

/* ========= column resize ========= */
const colWidth = reactive({
  company: 240,
  pi_no: 170,
  c_order_no: 190,
  original_date: 140,
  currency: 90,
  amount: 130,
  sales_rep: 130,
  company_title: 170,
})

function colStyle(key) {
  const w = Number(colWidth[key] || 120)
  return { width: w + 'px', minWidth: w + 'px', maxWidth: w + 'px' }
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
  const next = Math.max(80, _rsStartW + dx)
  colWidth[_rsKey] = next
}
function stopResize() {
  _rsKey = ''
  document.removeEventListener('mousemove', onResizing)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

/* ========= customer_view 風格：連續重複值就空白（前端顯示用） ========= */
function norm(v) { return String(v ?? '').trim() }

const displayRows = computed(() => {
  const list = Array.isArray(rows.value) ? rows.value : []
  let group = -1

  return list.map((r, i) => {
    const prev = i > 0 ? list[i - 1] : null

    // ✅ 你這邊可自行定義「同一組」的判斷
    // 我用 company + pi_no 當作主群組（同一張 PI 可能多筆 c_order_no）
    const curGroupKey = `${norm(r.company)}|${norm(r.pi_no)}`
    const prevGroupKey = prev ? `${norm(prev.company)}|${norm(prev.pi_no)}` : ''

    const sameGroup = !!prev && curGroupKey === prevGroupKey
    const isStart = !prev || !sameGroup
    if (isStart) group += 1

    // ✅ 如果跟上一列相同，就空白（你要的效果）
    const d = {}
    for (const c of columns) {
      const k = c.key
      const cur = norm(r?.[k])
      const p = prev ? norm(prev?.[k]) : ''
      d[k] = (prev && sameGroup && cur && cur === p) ? '' : r?.[k] ?? ''
    }

    return { ...r, __d: d, __group: group, __start: isStart }
  })
})

function rowClass(r) {
  const zebra = (r.__group % 2 === 0) ? 'bg-white' : 'bg-slate-50'
  return zebra
}
</script>

<style scoped>
/* 沿用 customer_view 的 CSS */
.table-scroll{
  height: calc(105vh - 240px);
  overflow: auto;
  scrollbar-color: #dddddd #eeeeee;
  scrollbar-width: thin;
}
.table-scroll::-webkit-scrollbar{ width:10px; height:10px; }
.table-scroll::-webkit-scrollbar-track{ background:#eeeeee; }
.table-scroll::-webkit-scrollbar-thumb{
  background:#eeeeee;
  border-radius:0;
  border:2px solid #eeeeee;
}
.table-scroll::-webkit-scrollbar-thumb:hover{ background:#bbbbbb; }

.grid-table{ border-collapse: separate; border-spacing:0; table-layout: fixed; }
.th, .td{
  padding: 12px;
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.th{ font-weight:700; cursor:pointer; user-select:none; }
.td{ font-size:10pt; font-weight:400; color:#333; }
.grid-table tr > *:last-child{ border-right:none; }
/* ✅ 表頭排序狀態（可點/不可點） */
.th-sortable{
  cursor: pointer;
  user-select: none;
}
.th-nosort{
  cursor: default;
  opacity: 0.85;
}
.col-resizer{
  position:absolute; top:0; right:0;
  width:8px; height:100%;
  cursor: col-resize;
}
.col-resizer:hover{ background: rgba(148,163,184,.35); }

.fixed-tools-wrap { position: relative; display:flex; align-items:center; justify-content:flex-end; gap:8px; }
.fixed-tools-inner { display:flex; align-items:center; gap:8px; }

.tool-btn{
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
  transition: background-color .15s ease, border-color .15s ease, color .15s ease;
}
.tool-btn:hover:not(:disabled),
.tool-btn:focus-visible:not(:disabled){
  background: #91C51B;
  border-color: #91C51B;
  color: #ffffff;
  outline:none;
}
.tool-btn:disabled{ opacity:.45; cursor:not-allowed; }

.icon-search{ width:18px; height:18px; display:block; }
.fixed-search{
  position:absolute;
  right:0;
  top: calc(100% + 8px);
  z-index:60;
  opacity:0;
  transform: translateY(-6px);
  pointer-events:none;
  transition: opacity .15s ease, transform .15s ease;
}
@media (hover: hover) and (pointer: fine) {
  .fixed-tools-wrap:hover .fixed-search{
    opacity:1; transform: translateY(0); pointer-events:auto;
  }
}
.fixed-search.show{ opacity:1; transform: translateY(0); pointer-events:auto; }

.input-group-field{
  width: 100%;
  height: 40px;
  padding: 0 12px;
  font-size: 12pt;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.14);
  background: #fff;
  outline: none;
}
.input-group-field:focus{
  border-color:#5F1CB9;
  box-shadow: 0 0 0 3px rgba(95, 28, 185, 0.12);
}
/* PI 編號：粗體黑字 + hover 綠色底線（加強優先權避免被覆蓋） */
td .pi-no{
  font-weight: 800 !important;
  color: #000 !important;
  cursor: pointer;
  display: inline-block;         /* ✅ 讓底線/邊框更穩 */
  border-bottom: 2px solid transparent;
  padding-bottom: 1px;
}
td .pi-no:hover{
  border-bottom-color: #91C51B;
}
.sr-only{ position:absolute; width:1px; height:1px; padding:0; margin:-1px; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }
</style>
