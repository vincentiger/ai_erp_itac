<template>
  <div class="p-4 md:p-6 space-y-4">
    <!-- Header -->
    <div class="flex items-start justify-between gap-3 flex-wrap">
      <div>
        <div class="text-xl font-bold text-slate-800">業務績效儀表板</div>
        <div class="text-sm text-slate-500 mt-1">
          接單 / 出貨 / 未出清（依業務彙總）
        </div>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <el-date-picker
          v-model="from"
          type="date"
          placeholder="起日"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 140px"
        />
        <el-date-picker
          v-model="to"
          type="date"
          placeholder="迄日"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 140px"
        />
        <el-button type="primary" :loading="loading" @click="load">
          查詢
        </el-button>
        <el-button @click="exportExcel" :disabled="!rowsFilteredSorted.length">匯出 Excel</el-button>
          <el-button @click="exportPDF" :disabled="!rowsFilteredSorted.length">匯出 PDF</el-button>

        <el-button @click="resetRange" :disabled="loading">本年</el-button>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="border border-slate-200 p-3">
        <div class="text-xs text-slate-500">訂單金額合計</div>
        <div class="text-lg font-bold text-slate-800 mt-1">{{ fmtMoney(totals.order_amount_sum) }}</div>
      </div>
      <div class="border border-slate-200 p-3">
        <div class="text-xs text-slate-500">出貨金額合計</div>
        <div class="text-lg font-bold text-slate-800 mt-1">{{ fmtMoney(totals.ship_amount_sum) }}</div>
      </div>
      <div class="border border-slate-200 p-3">
        <div class="text-xs text-slate-500">未出清筆數（open_line_count）</div>
        <div class="text-lg font-bold text-slate-800 mt-1">{{ fmtInt(totals.open_line_count) }}</div>
      </div>
      <div class="border border-slate-200 p-3">
        <div class="text-xs text-slate-500">未出清量合計（open_qty_sum）</div>
        <div class="text-lg font-bold mt-1" :class="totals.open_qty_sum < 0 ? 'text-red-600' : 'text-slate-800'">
          {{ fmtQty(totals.open_qty_sum) }}
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="border border-slate-200">
      <div class="p-3 border-b border-slate-200 flex items-center justify-between gap-3 flex-wrap">
        <div class="font-semibold text-slate-800">業務排行</div>

        <div class="flex items-center gap-2 flex-wrap">
          <el-input
            v-model="kw"
            placeholder="搜尋：業務姓名/ID"
            clearable
            style="width: 220px"
          />
          <el-select v-model="sortKey" style="width: 180px">
            <el-option label="出貨金額 (ship_amount_sum)" value="ship_amount_sum" />
            <el-option label="訂單金額 (order_amount_sum)" value="order_amount_sum" />
            <el-option label="未出清筆數 (open_line_count)" value="open_line_count" />
            <el-option label="未出清量 (open_qty_sum)" value="open_qty_sum" />
            <el-option label="PI 數 (pi_count)" value="pi_count" />
            <el-option label="明細筆數 (line_count)" value="line_count" />
          </el-select>
          <el-select v-model="sortDir" style="width: 110px">
            <el-option label="DESC" value="desc" />
            <el-option label="ASC" value="asc" />
          </el-select>
        </div>
      </div>

      <el-table
        :data="rowsFilteredSorted"
        height="560"
        stripe
        @row-click="pickRow"
      >
        <el-table-column label="#" width="60">
          <template #default="{ $index }">
            {{ $index + 1 }}
          </template>
        </el-table-column>

        <el-table-column prop="sales_rep_name" label="業務" min-width="140" />
        <el-table-column prop="ship_amount_sum" label="出貨金額" min-width="140" align="right">
          <template #default="{ row }">{{ fmtMoney(row.ship_amount_sum) }}</template>
        </el-table-column>

        <el-table-column prop="order_amount_sum" label="訂單金額" min-width="140" align="right">
          <template #default="{ row }">{{ fmtMoney(row.order_amount_sum) }}</template>
        </el-table-column>

        <el-table-column prop="open_line_count" label="未出清筆數" min-width="120" align="right">
          <template #default="{ row }">{{ fmtInt(row.open_line_count) }}</template>
        </el-table-column>

        <el-table-column prop="open_qty_sum" label="未出清量" min-width="120" align="right">
          <template #default="{ row }">
            <span :class="row.open_qty_sum < 0 ? 'text-red-600' : ''">
              {{ fmtQty(row.open_qty_sum) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="pi_count" label="PI數" width="90" align="right">
          <template #default="{ row }">{{ fmtInt(row.pi_count) }}</template>
        </el-table-column>

        <el-table-column prop="line_count" label="明細筆數" width="100" align="right">
          <template #default="{ row }">{{ fmtInt(row.line_count) }}</template>
        </el-table-column>

        <el-table-column label="達成率" min-width="110" align="right">
          <template #default="{ row }">
            {{ fmtPct(safeDiv(row.ship_amount_sum, row.order_amount_sum)) }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Detail panel -->
    <div v-if="picked" class="border border-slate-200 p-3">
      <div class="flex items-center justify-between">
        <div class="font-semibold text-slate-800">
          選取：{{ picked.sales_rep_name }}
        </div>
        <el-button @click="picked=null">關閉</el-button>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mt-3">
        <div class="border border-slate-200 p-3">
          <div class="text-xs text-slate-500">出貨金額</div>
          <div class="text-base font-bold mt-1">{{ fmtMoney(picked.ship_amount_sum) }}</div>
        </div>
        <div class="border border-slate-200 p-3">
          <div class="text-xs text-slate-500">訂單金額</div>
          <div class="text-base font-bold mt-1">{{ fmtMoney(picked.order_amount_sum) }}</div>
        </div>
        <div class="border border-slate-200 p-3">
          <div class="text-xs text-slate-500">達成率</div>
          <div class="text-base font-bold mt-1">{{ fmtPct(safeDiv(picked.ship_amount_sum, picked.order_amount_sum)) }}</div>
        </div>
        <div class="border border-slate-200 p-3">
          <div class="text-xs text-slate-500">未出清筆數</div>
          <div class="text-base font-bold mt-1">{{ fmtInt(picked.open_line_count) }}</div>
        </div>
        <div class="border border-slate-200 p-3">
          <div class="text-xs text-slate-500">未出清量</div>
          <div class="text-base font-bold mt-1" :class="picked.open_qty_sum < 0 ? 'text-red-600' : ''">
            {{ fmtQty(picked.open_qty_sum) }}
          </div>
        </div>
      </div>

      <div class="text-xs text-slate-500 mt-2">
        ※ open_qty_sum 出現負數通常代表資料源的退貨/沖銷/或欄位計算含負值（不影響儀表板顯示，但可再做資料稽核）。
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  exportTablePDF,
  exportTableCSV,
  safeDiv,
  fmtInt,
  fmtQty,
  fmtMoney,
  fmtPct,
} from '@/utils/include'

const from = ref('2025-01-01')
const to = ref('2025-12-31')

const loading = ref(false)
const rows = ref([])
const picked = ref(null)

const kw = ref('')
const sortKey = ref('ship_amount_sum')
const sortDir = ref('desc')

function resetRange(){
  from.value = '2025-01-01'
  to.value = '2025-12-31'
  load()
}

const totals = computed(() => {
  const t = {
    order_amount_sum: 0,
    ship_amount_sum: 0,
    open_line_count: 0,
    open_qty_sum: 0,
  }
  for (const r of rows.value) {
    t.order_amount_sum += Number(r.order_amount_sum || 0)
    t.ship_amount_sum += Number(r.ship_amount_sum || 0)
    t.open_line_count += Number(r.open_line_count || 0)
    t.open_qty_sum += Number(r.open_qty_sum || 0)
  }
  return t
})

const rowsFilteredSorted = computed(() => {
  const k = (kw.value || '').trim()
  let out = rows.value

  if (k) {
     out = out.filter(r =>
     String(r.sales_rep_name || '').includes(k)
     )
  }

  const key = sortKey.value
  const dir = sortDir.value

  out = [...out].sort((a,b) => {
    const av = Number(a[key] ?? 0)
    const bv = Number(b[key] ?? 0)
    return dir === 'asc' ? av - bv : bv - av
  })

  return out
})

function pickRow(row){
  picked.value = row
}

async function load(){
  loading.value = true
  picked.value = null
  try{
    const qs = new URLSearchParams()
    if (from.value) qs.set('from', from.value)
    if (to.value) qs.set('to', to.value)

    const res = await fetch(`/api/ai/kpi/sales-perf?${qs.toString()}`)
    const js = await res.json()

    if (!js?.ok) {
      ElMessage.error(js?.error || 'API 回應失敗')
      rows.value = []
      return
    }

    rows.value = Array.isArray(js.data) ? js.data : []
  }catch(e){
    console.error(e)
    ElMessage.error('讀取失敗，請看 console')
  }finally{
    loading.value = false
  }
}
function exportExcel(){
  const data = rowsFilteredSorted.value || []
  if (!data.length) return ElMessage.warning('沒有資料可匯出')

  const headers = ['#','業務','出貨金額','訂單金額','未出清筆數','未出清量','PI數','明細筆數','達成率']
  const body = data.map((r, idx) => {
    const fulfill = safeDiv(r.ship_amount_sum, r.order_amount_sum)
    return [
      String(idx + 1),
      String(r.sales_rep_name ?? ''),
      r.ship_amount_sum ?? 0,
      r.order_amount_sum ?? 0,
      r.open_line_count ?? 0,
      r.open_qty_sum ?? 0,
      r.pi_count ?? 0,
      r.line_count ?? 0,
      fmtPct(fulfill),
    ]
  })

  exportTableCSV({
    filename: `業務績效_${from.value || ''}_${to.value || ''}`,
    headers,
    rows: body,
  })
}

async function exportPDF() {
  const data = rowsFilteredSorted.value || []
  if (!data.length) return ElMessage.warning('沒有資料可匯出')

  // ✅ 這份報表欄位（共用 header & body）
  const headers = ['#','業務','出貨金額','訂單金額','未出清筆數','未出清量','PI數','明細筆數','達成率']

  const body = data.map((r, idx) => {
    const fulfill = safeDiv(r.ship_amount_sum, r.order_amount_sum)
    return [
      String(idx + 1),
      String(r.sales_rep_name ?? ''),
      fmtMoney(r.ship_amount_sum),
      fmtMoney(r.order_amount_sum),
      fmtInt(r.open_line_count),
      fmtQty(r.open_qty_sum),
      fmtInt(r.pi_count),
      fmtInt(r.line_count),
      fmtPct(fulfill),
    ]
  })

  await exportTablePDF({
    filename: `業務績效_${from.value || ''}_${to.value || ''}`,
    orientation: 'landscape',
    format: 'a4',
    title: `業務績效儀表板（${from.value || ''} ~ ${to.value || ''}）`,
    headers,
    rows: body,
    table: {
      styles: { fontSize: 9 },
      columnStyles: {
        0: { cellWidth: 24 }, // #
        1: { cellWidth: 70 }, // 業務
        2: { halign: 'right' },
        3: { halign: 'right' },
        4: { halign: 'right' },
        5: { halign: 'right' },
        6: { halign: 'right' },
        7: { halign: 'right' },
        8: { halign: 'right' },
      }
    }
  })
}


// -------- helpers（若你頁面裡已經有同名就不要重複貼）--------
function csvEscape(v){
  const s = String(v ?? '')
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s
}
function num(v){
  const n = Number(v ?? 0)
  return Number.isFinite(n) ? String(n) : '0'
}
function intNum(v){
  const n = Number(v ?? 0)
  return Number.isFinite(n) ? String(Math.trunc(n)) : '0'
}
onMounted(load)
</script>
