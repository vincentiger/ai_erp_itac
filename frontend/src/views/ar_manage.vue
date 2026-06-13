<template>
  <div class="p-3 sm:p-5 max-w-6xl mx-auto">
    <!-- 頁首 -->
    <div class="flex items-start justify-between gap-3 mb-3">
      <div>
        <div class="text-lg sm:text-xl font-bold">應收帳款維護作業</div>
        <div class="text-xs sm:text-sm text-gray-500">
          入口頁：先看所有未付清（預設 5 年內）並維護收款資料
        </div>
      </div>

      <div class="flex items-center gap-2">
        <el-button :loading="loadingAll" @click="reloadAll" plain>重新載入</el-button>
      </div>
    </div>

    <!-- 篩選區 -->
    <el-card shadow="never" class="mb-3">
      <div class="flex flex-col sm:flex-row gap-3 sm:items-end">
        <div class="flex-1">
          <div class="text-xs text-gray-500 mb-1">客戶（可不填=全部）</div>
          <el-input
            v-model="customerInput"
            placeholder="可輸入：客戶代號 / 客戶名稱 / 客戶簡稱"
            clearable
            @keyup.enter="reloadAll"
          />
        </div>

        <div class="w-full sm:w-auto flex gap-2">
          <el-button type="primary" :loading="loadingAll" @click="reloadAll">查詢全部</el-button>

          <el-button
            :disabled="!customerInput"
            :loading="loadingReceipts"
            @click="loadReceipts"
            type="success"
          >
            查詢該客戶收款
          </el-button>
        </div>
      </div>

      <div class="text-xs text-gray-500 mt-2">
        * 預設顯示「所有未付清（5 年內）」。輸入客戶關鍵字，可用代號/名稱/簡稱模糊查詢並查該客戶收款清單（尚未分攤者）。
      </div>
    </el-card>

    <!-- 未付清總覽 -->
    <el-card shadow="never" class="mb-3">
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="font-semibold">未付清總覽</div>
        <div class="text-xs text-gray-500">共 {{ openArList.length }} 筆</div>
      </div>

     <el-table
     :data="openArList"
     height="420"
     stripe
     border
     style="width: 100%"
     v-loading="loadingOpenAr"
     >
     <!-- ✅ 取消欄：最左固定 -->
     <el-table-column label="取消" width="80" align="center" fixed="left">
     <template #header>
          <div class="flex items-center justify-center gap-2">
          <el-checkbox
               v-model="checkAllOpen"
               :indeterminate="indeterminateOpen"
               @change="toggleAllOpen"
          />
          <span>取消</span>
          </div>
     </template>

     <template #default="{ row }">
          <el-checkbox
          :model-value="!!selectedOpenMap[rowKey(row)]"
          @click.stop
          @change="(v) => setRowSelected(row, v)"
          />
     </template>
     </el-table-column>

     <!-- 其他欄位 -->
     <el-table-column
     prop="ship_date"
     label="出貨日期"
     width="120"
     :formatter="(_, __, v) => (v ? fmtDateYMD(v) : '')"
     />
     <el-table-column prop="customer_name" label="客戶名稱" min-width="180" />
     <el-table-column prop="display_no" label="單據號碼" min-width="160" />
     <el-table-column prop="currency" label="幣別" width="80" />
     <el-table-column prop="payable_amount" label="應收金額" width="120" align="right" />
     <el-table-column prop="applied_amount" label="已沖金額" width="120" align="right" />
     <el-table-column prop="open_amount" label="未付清" width="120" align="right" />

     <!-- ✅ 收款欄：最右固定 -->
     <el-table-column label="收款" width="70" align="center" fixed="right">
     <template #default="{ row }">
          <el-button
          size="small"
          type="primary"
          plain
          @click.stop="openAddReceiptForRow(row)"
          >
          +
          </el-button>
     </template>
     </el-table-column>
     </el-table>
     <div class="mt-2 flex justify-end">
     <el-pagination
     background
     layout="prev, pager, next, jumper, ->, total"
     :total="openTotal"
     :page-size="openPageSize"
     :current-page="openPage"
     @current-change="(p) => { openPage = p; loadOpenAr() }"
     />
     </div>
      <div class="mt-2 flex items-center justify-between">
        <div class="text-xs text-gray-500">
          * 勾選後不會立即更新，請按「取消」才會寫入資料庫（下次不顯示）。
        </div>

        <el-button type="danger" :disabled="selectedOpenKeys.length === 0" @click="confirmCancelOpen">
          取消
        </el-button>
      </div>
    </el-card>

    <!-- 收款清單（供選一筆收款進沖帳） -->
    <el-card shadow="never">
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="font-semibold">收款清單（尚未分攤）</div>
        <div class="text-xs text-gray-500">
          {{ customerInput ? `客戶關鍵字：${customerInput}` : '請先輸入客戶再查詢' }}
          <span v-if="customerInput">，共 {{ receipts.length }} 筆</span>
        </div>
      </div>

      <el-table
        :data="receipts"
        height="320"
        stripe
        border
        style="width: 100%"
        v-loading="loadingReceipts"
      >
          <el-table-column
          prop="receipt_date"
          label="收款日期"
          width="120"
          :formatter="(_, __, v) => (v ? fmtDateYMD(v) : '')"
          />

          <el-table-column prop="receipt_id" label="收款編號" width="110" />

          <!-- ✅ 單筆：in_no -->
          <el-table-column prop="in_no" label="單據編號" min-width="180" />

          <!-- ✅ 客戶代號 + hover 顯示客戶名稱 -->
          <el-table-column label="客戶代號" width="140">
          <template #default="{ row }">
          <el-tooltip
               :content="row?.customer_name || ''"
               placement="top"
               :disabled="!row?.customer_name"
          >
               <span class="cursor-help">
               {{ (row?.customer_refno || '').trim() || '-' }}
               </span>
          </el-tooltip>
          </template>
          </el-table-column>

          <el-table-column prop="currency" label="幣別" width="80" />
          <el-table-column prop="receipt_amount" label="收款金額" width="120" align="right" />
          <el-table-column prop="applied_amount" label="已分攤" width="120" align="right" />
          <el-table-column prop="unapplied_amount" label="未分攤" width="120" align="right" />
      </el-table>

      <el-empty
        v-if="!loadingReceipts && customerInput && receipts.length === 0"
        description="此客戶目前沒有『尚未分攤』的收款（收款已全數分攤或尚未入收款）。"
      />

      <div class="text-xs text-gray-500 mt-2">
        * 目前此客戶端僅提供收款查詢與維護，未啟用沖帳功能。
      </div>
    </el-card>
     <el-dialog v-model="addReceiptDialog" title="新增收款" width="420px">
     <div class="space-y-3">
     <div class="text-xs text-gray-500">
          客戶：<span class="font-semibold text-gray-800">{{ selectedCustomerLabel || '-' }}</span>
          <span class="ml-2 text-gray-400">(ID={{ selectedCustomerId || '-' }})</span>
     </div>

     <div>
          <div class="text-xs text-gray-500 mb-1">收款日期</div>
          <el-date-picker
          v-model="addReceiptForm.receipt_date"
          type="date"
          value-format="YYYY-MM-DD"
          style="width:100%;"
          />
     </div>

     <div>
          <div class="text-xs text-gray-500 mb-1">幣別</div>
          <el-select v-model="addReceiptForm.currency" style="width:100%;">
          <el-option label="USD" value="USD" />
          <el-option label="TWD" value="TWD" />
          <el-option label="EUR" value="EUR" />
          <el-option label="JPY" value="JPY" />
          <el-option label="CNY" value="CNY" />
          </el-select>
          <div class="text-[11px] text-gray-400 mt-1">（先給常用幣別；之後可改成讀資料庫選項）</div>
     </div>

     <div>
          <div class="text-xs text-gray-500 mb-1">收款金額</div>
          <el-input-number
          v-model="addReceiptForm.receipt_amount"
          :min="0"
          :step="1"
          controls-position="right"
          style="width:100%;"
          />
     </div>

     <div>
          <div class="text-xs text-gray-500 mb-1">備註</div>
          <el-input v-model="addReceiptForm.memo" type="textarea" :rows="2" placeholder="匯款/支票號碼/備註" />
     </div>
     </div>

     <template #footer>
     <div class="flex justify-end gap-2">
          <el-button @click="addReceiptDialog=false" :disabled="savingReceipt">取消</el-button>
          <el-button type="primary" @click="submitAddReceipt" :loading="savingReceipt">
          儲存
          </el-button>
     </div>
     </template>
     </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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

import axios from 'axios'

const router = useRouter()
const customerInput = ref('')
// ✅ 日期範圍：預設 5 年（送後端做防呆查詢）
const dateFrom = ref('')
const dateTo = ref('')
const openArList = ref([])
const loadingOpenAr = ref(false)
// 收款（尚未分攤）
const receipts = ref([])
const loadingReceipts = ref(false)
const loadingAll = computed(() => loadingOpenAr.value || loadingReceipts.value)
// ✅ 未付清分頁
const openPage = ref(1)
const openPageSize = ref(50)     // 你可改 30/50/100
const openTotal = ref(0)

// ✅ API
const API_BASE = ''  // ✅ 強制走 Vite proxy (/api)
const who = computed(() => {
  const u = JSON.parse(localStorage.getItem('user') || 'null')
  return u?.username || u?.userno || u?.id || 'unknown'
})

function defaultRange5y() {
  const to = new Date()
  const from = new Date()
  from.setFullYear(from.getFullYear() - 5)
  return { from: fmtDateYMD(from), to: fmtDateYMD(to) }
}

// ✅ 單選：目前選到哪一筆未付清（用 rowKey 當 key）
const selectedOpenKey = ref('')

function selectOpenRow(row) {
  const key = rowKey(row)
  if (!key) {
    ElMessage.warning('此筆資料找不到 key，無法選取')
    return
  }
  selectedCustomerId.value = row?.customer_id || row?.cust_id || null
  selectedCustomerLabel.value = row?.customer_name || row?.customer_refno || ''
  const refno = String(row?.customer_refno || '').trim()
  const short = String(row?.customer_short || '').trim()
  const name  = String(row?.customer_name || '').trim()
  const kw = refno || short || name

  if (!kw) {
    ElMessage.warning('此筆資料找不到客戶資訊，無法載入收款清單')
    return
  }

  // ✅ 同客戶就不重查
  if (customerInput.value.trim() === kw) return

  customerInput.value = kw
  loadReceipts() // ✅ 這裡就會更新下面收款清單
}
// ✅ 目前選到的客戶（由 radio 選定）
const selectedCustomerId = ref(null)
const selectedCustomerLabel = ref('')

// ✅ 新增收款 Dialog
const addReceiptDialog = ref(false)
const savingReceipt = ref(false)
const addReceiptForm = reactive({
  receipt_date: '',
  currency: 'USD',
  receipt_amount: 0,
  method: '',
  bank_ref: '',
})

function openAddReceiptForRow(row) {
  // ✅ 從 open-list row 直接拿 customer_id / 客戶資訊
  const cid = Number(row?.customer_id || 0)
  if (!cid) {
    ElMessage.warning('此筆未付清沒有 customer_id（請後端 open-list 補回傳）')
    return
  }

  selectedCustomerId.value = cid
  selectedCustomerLabel.value = String(row?.customer_name || row?.customer_refno || '').trim()

  // ✅ 同步把 customerInput 帶入（方便下方收款清單查詢）
  const refno = String(row?.customer_refno || '').trim()
  if (refno) customerInput.value = refno

  openAddReceipt() // 開 dialog
}

function todayYMD() {
  return fmtDateYMD(new Date())
}

function openAddReceipt() {
  if (!selectedCustomerId.value) {
    ElMessage.warning('請先在未付清總覽用「選取」radio 選定客戶')
    return
  }
  addReceiptForm.receipt_date = todayYMD()
  addReceiptForm.currency = addReceiptForm.currency || 'USD'
  addReceiptForm.receipt_amount = 0
  addReceiptForm.memo = ''
  addReceiptDialog.value = true
}

async function submitAddReceipt() {
  if (!selectedCustomerId.value) return ElMessage.warning('未選定客戶')
  if (!addReceiptForm.receipt_date) return ElMessage.warning('請選收款日期')
  if (!addReceiptForm.currency) return ElMessage.warning('請選幣別')
  if (!(Number(addReceiptForm.receipt_amount) > 0)) return ElMessage.warning('收款金額需大於 0')

  savingReceipt.value = true
  try {
     const payload = {
     customer_id: Number(selectedCustomerId.value),
     customer_name: selectedCustomerLabel.value || '',
     receipt_date: addReceiptForm.receipt_date,
     currency: String(addReceiptForm.currency),
     receipt_amount: Number(addReceiptForm.receipt_amount),
     method: String(addReceiptForm.method || ''),
     bank_ref: String(addReceiptForm.bank_ref || ''),
     }

    const j = await apiPost('/api/ar/receipt-create', payload)

    ElMessage.success(`收款新增成功（receipt_id=${j.receipt_id}）`)
    addReceiptDialog.value = false

    // ✅ 立刻刷新下方收款清單
    await loadReceipts()
  } catch (e) {
    ElMessage.error(String(e.message || e))
  } finally {
    savingReceipt.value = false
  }
}
async function apiGet(path) {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, { method: 'GET' })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json?.ok === false) throw new Error(json?.msg || `HTTP ${res.status}`)
  return json
}
async function apiPost(path, body) {
  const url = `${API_BASE}${path}`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-User': String(who.value) },
    body: JSON.stringify(body ?? {}),
  })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json?.ok === false) throw new Error(json?.msg || `HTTP ${res.status}`)
  return json
}

// -----------------------------
// ✅ 取消勾選：只選取，不更新 DB
// -----------------------------
const selectedOpenMap = reactive({})
function rowKey(row) {
  return row?.internal_form_no || row?.form_no
}
const selectedOpenKeys = computed(() =>
  openArList.value.map(rowKey).filter(k => k && selectedOpenMap[k])
)

const checkAllOpen = ref(false)
const indeterminateOpen = ref(false)

function syncHeaderCheckState() {
  const total = openArList.value.length
  const checked = selectedOpenKeys.value.length
  checkAllOpen.value = total > 0 && checked === total
  indeterminateOpen.value = checked > 0 && checked < total
}
function toggleAllOpen(val) {
  openArList.value.forEach(r => {
    const k = rowKey(r)
    if (k) selectedOpenMap[k] = !!val
  })
  syncHeaderCheckState()
}
function setRowSelected(row, val) {
  const k = rowKey(row)
  if (!k) return
  selectedOpenMap[k] = !!val
  syncHeaderCheckState()
}

// ✅ 任何 reload 改變 openArList 時，重新同步 header 狀態
watch(openArList, () => {
  const keys = new Set(openArList.value.map(rowKey).filter(Boolean))

  Object.keys(selectedOpenMap).forEach(k => {
    if (!keys.has(k)) delete selectedOpenMap[k]
  })

  if (selectedOpenKey.value && !keys.has(selectedOpenKey.value)) {
    selectedOpenKey.value = ''
  }

  syncHeaderCheckState()
}, { deep: false })

async function confirmCancelOpen() {
  const formNos = selectedOpenKeys.value
  if (!formNos.length) {
    ElMessage.warning('請先勾選要取消的資料')
    return
  }

  try {
    await ElMessageBox.confirm(
      `你已選取 ${formNos.length} 筆未付清資料。\n確定要「取消（下次不顯示）」並更新資料庫嗎？`,
      '取消確認',
      { type: 'warning', confirmButtonText: '確定取消', cancelButtonText: '返回' }
    )

    await apiPost('/api/ar/cancel-batch', {
      form_nos: formNos,
      isCanceled: 1,
      reason: '會計取消',
    })

    ElMessage.success('已取消並更新完成')
    formNos.forEach(k => delete selectedOpenMap[k])
    syncHeaderCheckState()
    await reloadAll()
  } catch {
    // 使用者按返回，不做事
  }
}

// -----------------------------
// 載入：未付清總覽（5 年內）
// -----------------------------
async function loadOpenAr() {
  loadingOpenAr.value = true
  try {
    const params = new URLSearchParams()
    if (customerInput.value) params.set('customer_kw', customerInput.value.trim())
    if (dateFrom.value) params.set('from', dateFrom.value)
    if (dateTo.value) params.set('to', dateTo.value)

    // ✅ 分頁參數
    params.set('page', String(openPage.value))
    params.set('pageSize', String(openPageSize.value))

    const j = await apiGet(`/api/ar/open-list?${params.toString()}`)
    openArList.value = j.rows || []
    openTotal.value = Number(j.total || 0)
  } catch (e) {
    ElMessage.error(String(e.message || e))
  } finally {
    loadingOpenAr.value = false
  }
}

// -----------------------------
// 載入：收款清單（尚未分攤）（5 年內）
// -----------------------------
async function loadReceipts() {
  if (!customerInput.value) {
    ElMessage.warning('請先輸入客戶關鍵字（代號/名稱/簡稱），再查詢收款清單')
    return
  }
  loadingReceipts.value = true
  try {
    const params = new URLSearchParams()
    params.set('customer_kw', customerInput.value.trim())
    if (dateFrom.value) params.set('from', dateFrom.value)
    if (dateTo.value) params.set('to', dateTo.value)

    const j = await apiGet(`/api/ar/receipts?${params.toString()}`)
    receipts.value = j.rows || j.data || []
  } catch (e) {
    ElMessage.error(String(e.message || e))
  } finally {
    loadingReceipts.value = false
  }
}

// -----------------------------
// 重新載入
// -----------------------------
async function reloadAll() {
  openPage.value = 1
  await loadOpenAr()
  if (customerInput.value) {
    await loadReceipts()
  } else {
    receipts.value = [] // 沒客戶就清空收款清單，避免看舊資料
  }
}

// -----------------------------
// ✅ 進入沖帳頁（帶 receipt_id + 回跳資訊）
// -----------------------------
function goApply(receiptRow) {
  const receiptId = Number(receiptRow?.receipt_id)
  if (!receiptId) return

  const q = {
    receipt_id: receiptId,
    customer_kw: customerInput.value?.trim() || '',
    return_to: 'ar_manage',
  }
  if (dateFrom.value) q.from = dateFrom.value
  if (dateTo.value) q.to = dateTo.value

  router.push({ name: 'ar_apply', query: q })
}

onMounted(() => {
  const r = defaultRange5y()
  dateFrom.value = r.from
  dateTo.value = r.to
  reloadAll()
})
</script>

<style scoped>
:deep(.el-table .cell) {
  padding-left: 8px;
  padding-right: 8px;
}
/* ✅ 隱藏 radio 的文字（不顯示 label / form_no） */
:deep(.el-radio__label) {
  display: none !important;
}

</style>
