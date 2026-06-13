<template>
  <div class="p-3 md:p-6 space-y-4">
    <div class="flex items-start justify-between gap-3 flex-wrap">
      <div>
        <div class="text-xl font-bold text-slate-800">AI 今日優先處理訂單</div>
        <div class="text-sm text-slate-500 mt-1">
          依未出清金額 × 卡單天數排序（可切換排序模式）
        </div>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <el-date-picker v-model="from" type="date" value-format="YYYY-MM-DD" style="width:140px" />
        <el-date-picker v-model="to" type="date" value-format="YYYY-MM-DD" style="width:140px" />

        <el-select v-model="mode" style="width:150px">
          <el-option label="綜合分數(score)" value="score" />
          <el-option label="未出清金額(open_amount)" value="amount" />
          <el-option label="卡單天數(aging_days)" value="days" />
        </el-select>

        <el-input-number v-model="top" :min="10" :max="2000" :step="10" style="width:120px" />

        <el-button type="primary" :loading="loading" @click="load">查詢</el-button>

        <el-button :disabled="loading || !rows.length" @click="exportExcel">匯出 Excel</el-button>
        <el-button :disabled="loading || !rows.length" @click="exportPDF">匯出 PDF</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <template #header>
        <div class="flex items-center justify-between gap-3 flex-wrap">
          <div class="font-semibold">
            優先清單（共 {{ rows.length }} 筆）
          </div>
          <el-input v-model="kw" placeholder="搜尋：客戶/PI/業務/產品" clearable style="width:260px" />
        </div>
      </template>

      <el-table :data="rowsFiltered" border size="small" height="620" v-loading="loading">
        <el-table-column label="#" width="60">
          <template #default="{ $index }">{{ $index + 1 }}</template>
        </el-table-column>

        <el-table-column prop="aging_days" label="卡單天數" width="95" align="right" />
        <el-table-column prop="open_amount" label="未出清金額" width="120" align="right">
          <template #default="{row}">{{ fmtMoney(row.open_amount) }}</template>
        </el-table-column>
        <el-table-column prop="score" label="分數" width="110" align="right">
          <template #default="{row}">{{ fmtMoney(row.score) }}</template>
        </el-table-column>

        <el-table-column prop="order_date" label="訂單日" width="110">
          <template #default="{row}">{{ fmtDateYMD(row.order_date) }}</template>
        </el-table-column>

        <el-table-column prop="pi_form_no" label="PI" width="140" show-overflow-tooltip />
        <el-table-column prop="c_order_no" label="客戶PO" width="140" show-overflow-tooltip />
        <el-table-column prop="customer_name" label="客戶" min-width="220" show-overflow-tooltip />
        <el-table-column prop="sales_rep_name" label="業務" width="120" show-overflow-tooltip />

        <el-table-column prop="product_no" label="產品" width="140" show-overflow-tooltip />
        <el-table-column prop="product_cate" label="類別" min-width="160" show-overflow-tooltip />

        <el-table-column prop="open_qty" label="未出貨量" width="110" align="right">
          <template #default="{row}">{{ fmtQty(row.open_qty) }}</template>
        </el-table-column>
        <el-table-column prop="order_amount" label="訂單金額" width="120" align="right">
          <template #default="{row}">{{ fmtMoney(row.order_amount) }}</template>
        </el-table-column>
        <el-table-column prop="ship_amount_cached" label="出貨金額" width="120" align="right">
          <template #default="{row}">{{ fmtMoney(row.ship_amount_cached) }}</template>
        </el-table-column>

        <el-table-column prop="fulfill_status" label="狀態" width="90" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  fmtDateYMD,
  fmtQty,
  fmtMoney,
  exportTableCSV,
  exportTablePDF,
} from '@/utils/include'

const from = ref('2025-01-01')
const to = ref('2025-12-31')
const mode = ref('score')
const top = ref(200)

const loading = ref(false)
const rows = ref([])
const kw = ref('')

const rowsFiltered = computed(() => {
  const k = (kw.value || '').trim()
  if (!k) return rows.value
  return rows.value.filter(r => {
    const s = [
      r.customer_name, r.pi_form_no, r.sales_rep_name, r.product_no, r.c_order_no
    ].map(x => String(x || '')).join(' ')
    return s.includes(k)
  })
})

async function load(){
  loading.value = true
  try{
    const qs = new URLSearchParams()
    qs.set('mode', mode.value)
    qs.set('top', String(top.value || 200))
    if (from.value) qs.set('from', from.value)
    if (to.value) qs.set('to', to.value)

    const res = await fetch(`/api/ai/todo/priority?${qs.toString()}`)
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

function buildExportTable(){
  const headers = [
    '#','卡單天數','未出清金額','分數','訂單日','PI','客戶PO','客戶','業務','產品','類別','未出貨量','訂單金額','出貨金額','狀態'
  ]
  const body = rowsFiltered.value.map((r, idx) => ([
    String(idx + 1),
    String(r.aging_days ?? ''),
    fmtMoney(r.open_amount),
    fmtMoney(r.score),
    fmtDateYMD(r.order_date),
    r.pi_form_no,
    r.c_order_no,
    r.customer_name,
    r.sales_rep_name,
    r.product_no,
    r.product_cate,
    fmtQty(r.open_qty),
    fmtMoney(r.order_amount),
    fmtMoney(r.ship_amount_cached),
    r.fulfill_status,
  ]))
  return { headers, body }
}

function exportExcel(){
  if (!rowsFiltered.value.length) return ElMessage.warning('沒有資料可匯出')
  const { headers, body } = buildExportTable()
  exportTableCSV({
    filename: `ai_todo_${mode.value}_${new Date().toISOString().slice(0,10)}`,
    headers,
    rows: body,
  })
}

async function exportPDF(){
  if (!rowsFiltered.value.length) return ElMessage.warning('沒有資料可匯出')
  const { headers, body } = buildExportTable()
  await exportTablePDF({
    filename: `ai_todo_${mode.value}_${new Date().toISOString().slice(0,10)}.pdf`,
    orientation: 'landscape',
    format: 'a3',
    title: `AI 今日優先處理訂單（${mode.value}）`,
    headers,
    rows: body,
    table: { styles: { fontSize: 8 } }
  })
}

onMounted(load)
</script>
