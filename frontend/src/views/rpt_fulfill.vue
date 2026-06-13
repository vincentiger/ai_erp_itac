<template>
  <div class="p-4 md:p-6 space-y-4">
    <div class="flex items-start justify-between gap-3 flex-wrap">
      <div>
        <div class="text-xl font-bold text-slate-800">出貨達成率</div>
        <div class="text-sm text-slate-500 mt-1">
          依 客戶 / 業務 / 公司別 彙總（ship_amount / order_amount）
        </div>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <el-select v-model="by" style="width: 160px">
          <el-option label="依客戶" value="customer" />
          <el-option label="依業務" value="sales" />
          <el-option label="依公司別" value="company" />
        </el-select>

        <el-date-picker v-model="from" type="date" placeholder="起日" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 140px" />
        <el-date-picker v-model="to" type="date" placeholder="迄日" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 140px" />

        <el-button type="primary" :loading="loading" @click="load">查詢</el-button>

        <el-button @click="exportExcel" :disabled="!rowsFilteredSorted.length">匯出 Excel</el-button>
        <el-button @click="exportPDF" :disabled="!rowsFilteredSorted.length">匯出 PDF</el-button>

        <el-button @click="resetRange" :disabled="loading">本年</el-button>
      </div>
    </div>

    <div class="border border-slate-200">
      <div class="p-3 border-b border-slate-200 flex items-center justify-between gap-3 flex-wrap">
        <div class="font-semibold text-slate-800">達成率排行</div>
        <div class="flex items-center gap-2 flex-wrap">
          <el-input v-model="kw" placeholder="搜尋：名稱/ID" clearable style="width: 240px" />
          <el-select v-model="sortKey" style="width: 200px">
            <el-option label="出貨金額" value="ship_amount_sum" />
            <el-option label="訂單金額" value="order_amount_sum" />
            <el-option label="達成率" value="fulfill_rate" />
            <el-option label="未出清筆數" value="open_line_count" />
            <el-option label="明細筆數" value="line_count" />
          </el-select>
          <el-select v-model="sortDir" style="width: 110px">
            <el-option label="DESC" value="desc" />
            <el-option label="ASC" value="asc" />
          </el-select>
        </div>
      </div>

      <el-table :data="rowsFilteredSorted" height="560" stripe v-loading="loading">
        <el-table-column label="#" width="60">
          <template #default="{ $index }">{{ $index + 1 }}</template>
        </el-table-column>

        <el-table-column prop="group_name" :label="groupLabel" min-width="220" show-overflow-tooltip />
        <el-table-column prop="group_id" label="ID" width="90" show-overflow-tooltip />

        <el-table-column prop="order_amount_sum" label="訂單金額" min-width="140" align="right">
          <template #default="{ row }">{{ fmtMoney(row.order_amount_sum) }}</template>
        </el-table-column>

        <el-table-column prop="ship_amount_sum" label="出貨金額" min-width="140" align="right">
          <template #default="{ row }">{{ fmtMoney(row.ship_amount_sum) }}</template>
        </el-table-column>

        <el-table-column prop="fulfill_rate" label="達成率" width="110" align="right">
          <template #default="{ row }">{{ fmtPct(row.fulfill_rate) }}</template>
        </el-table-column>

        <el-table-column prop="open_line_count" label="未出清筆數" width="120" align="right">
          <template #default="{ row }">{{ fmtInt(row.open_line_count) }}</template>
        </el-table-column>

        <el-table-column prop="line_count" label="明細筆數" width="110" align="right">
          <template #default="{ row }">{{ fmtInt(row.line_count) }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  exportTablePDF,
  exportTableCSV,
  fmtInt,
  fmtMoney,
  fmtPct,
} from '@/utils/include'

const from = ref('2025-01-01')
const to = ref('2025-12-31')
const by = ref('customer')

const loading = ref(false)
const rows = ref([])

const kw = ref('')
const sortKey = ref('ship_amount_sum')
const sortDir = ref('desc')

const groupLabel = computed(() => {
  if (by.value === 'sales') return '業務'
  if (by.value === 'company') return '公司別'
  return '客戶'
})

function resetRange(){
  from.value = '2025-01-01'
  to.value = '2025-12-31'
  load()
}

async function load(){
  loading.value = true
  try{
    const qs = new URLSearchParams()
    qs.set('by', by.value)
    if (from.value) qs.set('from', from.value)
    if (to.value) qs.set('to', to.value)

    const res = await fetch(`/api/ai/kpi/fulfill?${qs.toString()}`)
    const js = await res.json()
    if (!js?.ok) throw new Error(js?.error || 'API 回應失敗')

    rows.value = Array.isArray(js.data) ? js.data : []
  }catch(e){
    console.error(e)
    rows.value = []
    ElMessage.error(e?.message || '讀取失敗')
  }finally{
    loading.value = false
  }
}

const rowsFilteredSorted = computed(() => {
  const k = (kw.value || '').trim()
  let out = rows.value

  if (k) {
    out = out.filter(r =>
      String(r.group_name ?? '').includes(k) ||
      String(r.group_id ?? '').includes(k)
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

// ✅ headers/body 共用
function buildExport(){
  const headers = ['#', groupLabel.value, 'ID', '訂單金額', '出貨金額', '達成率', '未出清筆數', '明細筆數']
  const body = rowsFilteredSorted.value.map((r, idx) => ([
    String(idx + 1),
    String(r.group_name ?? ''),
    String(r.group_id ?? ''),
    r.order_amount_sum ?? 0,
    r.ship_amount_sum ?? 0,
    fmtPct(r.fulfill_rate ?? 0),
    r.open_line_count ?? 0,
    r.line_count ?? 0,
  ]))
  return { headers, body }
}

function exportExcel(){
  if (!rowsFilteredSorted.value.length) return ElMessage.warning('沒有資料可匯出')
  const { headers, body } = buildExport()
  exportTableCSV({
    filename: `出貨達成率_${by.value}_${from.value || ''}_${to.value || ''}`,
    headers,
    rows: body,
  })
}

async function exportPDF(){
  if (!rowsFilteredSorted.value.length) return ElMessage.warning('沒有資料可匯出')
  const { headers, body } = buildExport()
  await exportTablePDF({
    filename: `出貨達成率_${by.value}_${from.value || ''}_${to.value || ''}`,
    orientation: 'landscape',
    format: 'a4',
    title: `出貨達成率（${groupLabel.value}）`,
    headers,
    rows: body,
    table: { styles: { fontSize: 9 } }
  })
}

onMounted(load)
</script>
