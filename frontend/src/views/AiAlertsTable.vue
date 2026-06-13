<template>
  <div class="p-3">
    <div class="flex items-center justify-between mb-2">
      <div class="text-base font-bold text-slate-800">AI 訂單出貨總覽</div>

      <!-- 查詢圖示 -->
      <el-button circle :disabled="loading" @click="drawer=true" title="查詢/過濾">
        <el-icon><Search /></el-icon>
      </el-button>
    </div>

    <!-- KPI 區（前10） -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">
      <el-card shadow="never">
        <template #header>
          <div class="font-semibold">出貨金額前 10 名客戶</div>
        </template>
        <el-table :data="topCustomers" size="small" border height="260" v-loading="loadingKpi">
          <el-table-column prop="customer_name" label="客戶" min-width="220" show-overflow-tooltip />
          <el-table-column prop="currency" label="幣別" width="70" />
          <el-table-column prop="ship_amount_sum" label="出貨金額" width="140">
            <template #default="{row}">{{ fmtQty(row.ship_amount_sum) }}</template>
          </el-table-column>
          <el-table-column prop="pi_count" label="PI數" width="80" />
        </el-table>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="font-semibold">最暢銷產品前 10 名</div>
        </template>
        <el-table :data="topProducts" size="small" border height="260" v-loading="loadingKpi">
          <el-table-column prop="product_no" label="產品" width="140" />
          <el-table-column prop="product_cate" label="類別" min-width="160" show-overflow-tooltip />
          <el-table-column prop="ship_amount_sum" label="出貨金額" width="140">
            <template #default="{row}">{{ fmtQty(row.ship_amount_sum) }}</template>
          </el-table-column>
          <el-table-column prop="line_count" label="筆數" width="80" />
        </el-table>
      </el-card>
    </div>

    <!-- 主清單 -->
    <el-card shadow="never">
      <template #header>
        <div class="flex items-center justify-between">
          <div class="font-semibold">
            明細清單（{{ statusLabel }}）
            <span class="text-xs text-slate-500 ml-2">共 {{ rows.length }} 筆（前端顯示 top={{ q.top }}）</span>
          </div>

          <div class="flex items-center gap-2">
            <el-button size="small" :disabled="loading || !rows.length" @click="exportExcel">匯出 Excel</el-button>
            <el-button size="small" :disabled="loading || !rows.length" @click="exportPDFLandscape">匯出 PDF(橫向)</el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="rows"
        size="small"
        border
        height="560"
        v-loading="loading"
      >
        <el-table-column prop="order_date" label="訂單日" width="110">
          <template #default="{row}">{{ fmtDateYMD(row.order_date) }}</template>
        </el-table-column>

        <el-table-column prop="pi_form_no" label="PI" width="140" show-overflow-tooltip />
        <el-table-column prop="c_order_no" label="客戶PO" width="140" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="客戶" min-width="220" show-overflow-tooltip />
        <el-table-column prop="sales_rep_name" label="業務" width="120" show-overflow-tooltip />
        <el-table-column prop="currency" label="幣別" width="70" />

        <el-table-column prop="product_no" label="產品" width="140" show-overflow-tooltip />
        <el-table-column prop="product_cate" label="類別" min-width="160" show-overflow-tooltip />

        <el-table-column prop="order_qty" label="下單量" width="110" align="right">
          <template #default="{row}">{{ fmtQty(row.order_qty) }}</template>
        </el-table-column>
        <el-table-column prop="ship_qty" label="已出貨量" width="110" align="right">
          <template #default="{row}">{{ fmtQty(row.ship_qty) }}</template>
        </el-table-column>
        <el-table-column prop="open_qty" label="未出貨量" width="110" align="right">
          <template #default="{row}">{{ fmtQty(row.open_qty) }}</template>
        </el-table-column>

        <el-table-column prop="order_amount" label="訂單金額" width="120" align="right">
          <template #default="{row}">{{ fmtQty(row.order_amount) }}</template>
        </el-table-column>
        <el-table-column prop="ship_amount_cached" label="出貨金額" width="120" align="right">
          <template #default="{row}">{{ fmtQty(row.ship_amount_cached) }}</template>
        </el-table-column>

        <el-table-column prop="last_ship_date" label="最後出貨日" width="120">
          <template #default="{row}">{{ fmtDateYMD(row.last_ship_date) }}</template>
        </el-table-column>
        <el-table-column prop="fulfill_status" label="狀態" width="90" />
      </el-table>
    </el-card>

    <!-- 查詢 Drawer -->
    <el-drawer v-model="drawer" title="查詢 / 過濾" size="360px">
      <div class="space-y-4">
        <div>
          <div class="text-xs text-slate-500 mb-1">狀態</div>
          <el-segmented v-model="q.status" :options="statusOptions" />
        </div>

        <div>
          <div class="text-xs text-slate-500 mb-1">日期區間（訂單日）</div>
          <el-date-picker
            v-model="q.dateRange"
            type="daterange"
            unlink-panels
            range-separator="~"
            start-placeholder="起日"
            end-placeholder="迄日"
            value-format="YYYY-MM-DD"
            style="width:100%;"
          />
        </div>

        <el-input v-model="q.customer" placeholder="客戶（模糊查詢）" clearable />
        <el-input v-model="q.sales_rep" placeholder="業務代表（模糊查詢）" clearable />
        <el-input v-model="q.company_title" placeholder="公司別（模糊查詢）" clearable />

        <el-input-number v-model="q.top" :min="10" :max="5000" :step="10" controls-position="right" style="width:100%;">
          <template #prefix>Top</template>
        </el-input-number>

        <div class="flex gap-2 justify-end">
          <el-button @click="resetFilters" :disabled="loading">重設</el-button>
          <el-button type="primary" @click="applyFilters" :disabled="loading">套用</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

// 你原本已裝 xlsx / file-saver / jspdf / autotable
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'
import { 
  exportTablePDF, 
  exportTableCSV,
  safeDiv,
  fmtInt,
  fmtQty,
  fmtMoney,
  fmtPct,
  fmtDateYMD,
} from '@/utils/include'
import { useRoute } from 'vue-router'
const route = useRoute()
console.log('[ar_apply] route.query=', route.query)

const drawer = ref(false)
const loading = ref(false)
const loadingKpi = ref(false)

const rows = ref([])
const topCustomers = ref([])
const topProducts = ref([])

const statusOptions = [
  { label: '全部', value: 'all' },
  { label: '未出清', value: 'open' },
  { label: '已出清', value: 'closed' },
]

const q = reactive({
  status: 'all',
  dateRange: null,         // ['2025-01-01','2025-12-31']
  customer: '',
  sales_rep: '',
  company_title: '',
  top: 500,
})

const statusLabel = computed(() => {
  const m = { all:'全部', open:'未出清', closed:'已出清' }
  return m[q.status] || q.status
})

function buildParams() {
  const p = {
    status: q.status,
    top: q.top,
    customer: q.customer || '',
    sales_rep: q.sales_rep || '',
    company_title: q.company_title || '',
  }
  if (Array.isArray(q.dateRange) && q.dateRange.length === 2) {
    p.from = q.dateRange[0]
    p.to = q.dateRange[1]
  }
  return p
}

async function loadList() {
  loading.value = true
  try {
    const r = await axios.get('/api/ai/list/lines', { params: buildParams() })
    rows.value = r.data?.data ?? []
    console.log('[ai_list] first row=', rows.value?.[0])
  } catch (e) {
    ElMessage.error(`讀取失敗: ${e?.message || e}`)
    rows.value = []
  } finally {
    loading.value = false
  }
}

async function loadKpis() {
  loadingKpi.value = true
  try {
    // 出貨金額前10名客戶（by=ship）
    const c = await axios.get('/api/ai/kpi/top-customers', { params: { top: 10, by: 'ship' } })
    topCustomers.value = c.data?.data ?? []

    // 最暢銷產品前10名（by=amount 代表出貨金額；要數量就 by=qty）
    const p = await axios.get('/api/ai/kpi/top-products', { params: { top: 10, by: 'amount' } })
    topProducts.value = p.data?.data ?? []
  } catch (e) {
    ElMessage.error(`KPI 讀取失敗: ${e?.message || e}`)
    topCustomers.value = []
    topProducts.value = []
  } finally {
    loadingKpi.value = false
  }
}

function applyFilters() {
  drawer.value = false
  loadList()
}
function resetFilters() {
  q.status = 'all'
  q.dateRange = null
  q.customer = ''
  q.sales_rep = ''
  q.company_title = ''
  q.top = 500
}

// ✅ 共用 headers / body（PDF & Excel 共用）
function buildLinesExport() {
  const headers = [
    '訂單日','PI','客戶PO','客戶','業務','幣別','產品','類別',
    '下單量','已出貨量','未出貨量','訂單金額','出貨金額','最後出貨日','狀態'
  ]

  const body = rows.value.map(r => ([
    fmtDateYMD(r.order_date),
    String(r.pi_form_no ?? ''),
    String(r.c_order_no ?? ''),
    String(r.customer_name ?? ''),
    String(r.sales_rep_name ?? ''),
    String(r.currency ?? ''),
    String(r.product_no ?? ''),
    String(r.product_cate ?? ''),
    // ✅ 匯出建議用「原始數字」避免 Excel/PDF 二次格式化出問題
    r.order_qty ?? 0,
    r.ship_qty ?? 0,
    r.open_qty ?? 0,
    r.order_amount ?? 0,
    r.ship_amount_cached ?? 0,
    fmtDateYMD(r.last_ship_date),
    String(r.fulfill_status ?? ''),
  ]))

  return { headers, body }
}

async function exportPDFLandscape() {
  if (!rows.value.length) return ElMessage.warning('沒有資料可匯出')

  const { headers, body } = buildLinesExport()

  await exportTablePDF({
    // ✅ include.js 會自動補 .pdf，所以這裡不要手動加也可
    filename: `ai_lines_${q.status}_${new Date().toISOString().slice(0,10)}`,
    orientation: 'landscape',
    format: 'a3',
    title: `出貨明細（${q.status}）`,
    headers,
    rows: body,
    table: {
      styles: { fontSize: 8 },
      // columnStyles: { 0:{cellWidth:50}, 1:{cellWidth:60} ... }
    }
  })
}

function exportExcel() {
  if (!rows.value.length) return ElMessage.warning('沒有資料可匯出')

  const { headers, body } = buildLinesExport()

  exportTableCSV({
    filename: `ai_lines_${q.status}_${new Date().toISOString().slice(0,10)}`,
    headers,
    rows: body
  })
}

// ✅ 一律從 query 拿 receipt_id
const receiptId = computed(() => Number(route.query?.receipt_id || 0))

// (可選) 你 ar_manage 帶過來的回跳資訊
const returnTo = computed(() => String(route.query?.return_to || 'ar_manage'))

// ✅ 你的資料容器
const receipt = ref(null)
const invoices = ref([])

// ✅ 走 Vite proxy：不要用 http://127.0.0.1:5000，避免 CORS
async function apiGet(path) {
  const res = await fetch(path, { method: 'GET' })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json?.ok === false) throw new Error(json?.msg || `HTTP ${res.status}`)
  return json
}

// ✅ 這裡你要改成你真正的 API：
// 例：/api/ar/apply/context?receipt_id=xxx&ar_id=yyy 或你目前有哪些 endpoint
async function loadReceiptAndInvoices() {
  loading.value = true
  try {
    // 先示範：抓收款 + 可沖的發票清單（你依你後端實際路由改）
    const j = await apiGet(`/api/ar/apply/context?receipt_id=${receiptId.value}`)
    receipt.value = j.receipt || null
    invoices.value = j.invoices || []
  } catch (e) {
    ElMessage.error(`讀取沖帳資料失敗：${e?.message || e}`)
    receipt.value = null
    invoices.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // ✅ 防呆：沒有 receipt_id 就不要進來
  if (!receiptId.value) {
    ElMessage.error('缺少 receipt_id，無法進入沖帳')
    // 可選：直接退回入口頁
    router.replace({ name: returnTo.value })
    return
  }
  loadReceiptAndInvoices()
})
</script>
