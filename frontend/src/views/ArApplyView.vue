<template>
  <div class="p-3 sm:p-5 max-w-6xl mx-auto">
    <!-- 頁首 -->
    <div class="flex items-start justify-between gap-3 mb-3">
      <div>
        <div class="text-lg sm:text-xl font-bold">應收帳款收款沖帳</div>
        <div class="text-xs sm:text-sm text-gray-500">
          收款 → 可沖帳清單 → 單筆沖帳 / 先進先出分攤 → 明細反沖
        </div>
      </div>

      <div class="flex items-center gap-2">
        <el-button :loading="loadingAll" @click="reloadAll" plain>重新載入</el-button>
      </div>
    </div>

    <!-- 查詢 / 收款資訊 -->
    <el-card shadow="never" class="mb-3">
      <div class="flex flex-col sm:flex-row gap-3 sm:items-end">
        <div class="flex-1">
          <div class="text-xs text-gray-500 mb-1">收款編號（receipt_id）</div>
          <el-input
            v-model="receiptIdInput"
            placeholder="例如：6"
            inputmode="numeric"
            clearable
            @keyup.enter="reloadAll"
          />
          <div class="text-[11px] text-gray-400 mt-1">
            * 從收款清單點進來會自動帶入；也可手動輸入後按 Enter / 查詢
          </div>
        </div>

        <div class="flex-1">
          <div class="text-xs text-gray-500 mb-1">分攤備註（先進先出用）</div>
          <el-input v-model="memoInput" placeholder="例如：收款自動分攤（先進先出）" clearable />
        </div>

        <div class="w-full sm:w-auto flex gap-2">
          <el-button type="primary" :loading="loadingAll" @click="reloadAll">查詢</el-button>

          <el-button
            type="success"
            :disabled="!effectiveReceiptId || receiptUnappliedNum <= 0"
            :loading="loadingFifo"
            @click="doFifo()"
          >
            先進先出：全額分攤
          </el-button>

          <el-button
            :disabled="!effectiveReceiptId || receiptUnappliedNum <= 0"
            :loading="loadingFifo"
            @click="fifoDialogOpen = true"
            plain
          >
            先進先出：指定金額
          </el-button>
        </div>
      </div>

      <div class="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <div class="p-3 rounded bg-gray-50">
          <div class="text-xs text-gray-500">幣別</div>
          <div class="font-semibold">{{ receipt?.currency ?? '-' }}</div>
        </div>
        <div class="p-3 rounded bg-gray-50">
          <div class="text-xs text-gray-500">客戶</div>
          <div class="font-semibold">
            <span v-if="receipt?.customer_name">
              {{ receipt.customer_name }}
              <span class="text-gray-400 text-xs" v-if="receipt?.customer_refno">
                （{{ String(receipt.customer_refno).trim() }}）
              </span>
            </span>
            <span v-else>-</span>
          </div>
        </div>
        <div class="p-3 rounded bg-gray-50">
          <div class="text-xs text-gray-500">收款金額</div>
          <div class="font-semibold">{{ receipt?.receipt_amount ?? '-' }}</div>
        </div>
        <div class="p-3 rounded bg-gray-50">
          <div class="text-xs text-gray-500">未分攤金額</div>
          <div class="font-semibold" :class="receiptUnappliedNum > 0 ? 'text-green-700' : 'text-gray-700'">
            {{ receipt?.unapplied_amount ?? '-' }}
          </div>
        </div>
      </div>
    </el-card>

    <!-- 可沖帳清單 -->
    <el-card shadow="never" class="mb-3">
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="font-semibold">可沖帳清單（待沖帳項目）</div>
        <div class="text-xs text-gray-500">
          共 {{ invoices.length }} 筆（顯示前 {{ top }} 筆）
        </div>
      </div>

      <el-table
        :data="invoices"
        height="420"
        stripe
        border
        style="width: 100%"
        v-loading="loadingCandidates"
      >
        <el-table-column prop="ar_id" label="應收編號" width="95" />
        <el-table-column prop="form_no" label="單據號碼" min-width="140" />
        <el-table-column prop="in_no" label="發票號碼" min-width="140" />
        <el-table-column prop="pi_no" label="PI 號碼" min-width="140" />
        <el-table-column prop="status" label="狀態" width="90" />
        <el-table-column prop="open_amount" label="未沖金額" width="110" />
        <el-table-column prop="paid_amount" label="已沖金額" width="110" />
        <el-table-column prop="payable_amount" label="應付參考" width="110" />

        <el-table-column label="沖帳金額" width="200">
          <template #default="{ row }">
            <div class="flex gap-2 items-center">
              <el-input
                v-model="applyAmountMap[row.ar_id]"
                placeholder="金額"
                inputmode="decimal"
                size="small"
              />
              <el-button
                type="primary"
                size="small"
                :loading="payingArId === row.ar_id"
                :disabled="!effectiveReceiptId || receiptUnappliedNum <= 0"
                @click="doPay(row)"
              >
                沖帳
              </el-button>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="快速填入" width="180">
          <template #default="{ row }">
            <div class="flex gap-2">
              <el-button size="small" plain @click="setQuickAmount(row, 'min')">最小</el-button>
              <el-button size="small" plain @click="setQuickAmount(row, 'open')">全額未沖</el-button>
              <el-button size="small" plain @click="setQuickAmount(row, 'all')">可沖上限</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="text-xs text-gray-500 mt-2">
        * 「最小」：填 1；「全額未沖」：填該筆未沖金額；「可沖上限」：填「收款未分攤」與「該筆未沖金額」兩者較小值
      </div>
    </el-card>

    <!-- 已沖帳明細 -->
    <el-card shadow="never">
      <div class="flex items-center justify-between gap-2 mb-2">
        <div class="font-semibold">已沖帳明細</div>
        <div class="text-xs text-gray-500">共 {{ applies.length }} 筆</div>
      </div>

      <el-table
        :data="applies"
        height="320"
        stripe
        border
        style="width: 100%"
        v-loading="loadingApplies"
      >
        <el-table-column prop="apply_id" label="明細編號" width="95" />
        <el-table-column prop="ar_id" label="應收編號" width="95" />
        <el-table-column prop="apply_date" label="沖帳日期" width="130" />
        <el-table-column prop="apply_amount" label="沖帳金額" width="110" />
        <el-table-column prop="memo" label="備註" min-width="200" />
        <el-table-column prop="form_no" label="單據號碼" min-width="140" />
        <el-table-column prop="in_no" label="發票號碼" min-width="140" />

        <el-table-column label="反沖" width="260">
          <template #default="{ row }">
            <div class="flex gap-2 items-center">
              <el-input
                v-model="unapplyAmountMap[row.apply_id]"
                placeholder="不填=全反沖"
                inputmode="decimal"
                size="small"
              />
              <el-button
                type="danger"
                size="small"
                :loading="unpayingApplyId === row.apply_id"
                @click="doUnapply(row)"
              >
                反沖
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="text-xs text-gray-500 mt-2">
        * 反沖：不填金額 → 全部反沖（刪除該筆沖帳明細）；填金額 → 部分反沖（需後端程序支援 unapply_amount）
      </div>
    </el-card>

    <!-- 先進先出：指定金額 -->
    <el-dialog v-model="fifoDialogOpen" title="先進先出：指定分攤金額" width="420px">
      <div class="space-y-2">
        <div class="text-sm text-gray-600">
          目前未分攤：<b>{{ receipt?.unapplied_amount ?? '-' }}</b>
        </div>
        <el-input v-model="fifoAmountInput" placeholder="例如：500" inputmode="decimal" />
        <div class="text-xs text-gray-500">
          * 分攤總額會交由後端程序依先進先出規則，自動分攤到同幣別、同客戶的「未沖帳項目」
        </div>
      </div>
      <template #footer>
        <el-button @click="fifoDialogOpen = false">取消</el-button>
        <el-button
          type="success"
          :loading="loadingFifo"
          :disabled="!effectiveReceiptId"
          @click="doFifo(fifoAmountInput)"
        >
          執行先進先出分攤
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'

const route = useRoute()

// ✅ 從 query 讀 receipt_id（ar_manage 點進來會帶）
const receiptIdFromQuery = computed(() => {
  const v = route.query.receipt_id
  return v ? Number(v) : 0
})

// ✅ template 需要：手動輸入也可查
const receiptIdInput = ref('')

// ✅ 若 URL 有 receipt_id，就自動填入輸入框
watch(
  () => route.query.receipt_id,
  (v) => {
    if (v != null && String(v).trim() !== '') {
      receiptIdInput.value = String(v)
    }
  },
  { immediate: true }
)

// ✅ 實際用的 receipt_id：優先 query，沒有才用輸入框
const effectiveReceiptId = computed(() => {
  return receiptIdFromQuery.value || Number(receiptIdInput.value || 0)
})

const memoInput = ref('')
const receipt = ref(null)
const invoices = ref([])
const top = ref(20)
const applies = ref([])

const loadingCandidates = ref(false)
const loadingApplies = ref(false)
const loadingFifo = ref(false)
const payingArId = ref(null)
const unpayingApplyId = ref(null)

const applyAmountMap = ref({})     // { [ar_id]: '10' }
const unapplyAmountMap = ref({})   // { [apply_id]: '5' }

const fifoDialogOpen = ref(false)
const fifoAmountInput = ref('')

function num(v) {
  const n = Number(String(v ?? '').replace(/,/g, ''))
  return Number.isFinite(n) ? n : 0
}
const receiptUnappliedNum = computed(() => num(receipt.value?.unapplied_amount))
const loadingAll = computed(() => loadingCandidates.value || loadingApplies.value)

// -----------------------------
// API helper
// -----------------------------
async function apiGet(url) {
  const res = await fetch(url, { method: 'GET' })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json?.ok === false) throw new Error(json?.msg || `HTTP ${res.status}`)
  return json
}

async function apiPost(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json?.ok === false) throw new Error(json?.msg || `HTTP ${res.status}`)
  return json
}

// -----------------------------
// Loaders
// -----------------------------
async function loadCandidates() {
  if (!effectiveReceiptId.value) return
  loadingCandidates.value = true
  try {
    const j = await apiGet(`/api/ar/apply/candidates?receipt_id=${effectiveReceiptId.value}&top=20`)
    receipt.value = j.receipt
    invoices.value = j.invoices || []
    top.value = j.top ?? 20

    // 初始化每一列的預設沖帳金額（空字串）
    const nextMap = { ...applyAmountMap.value }
    for (const r of invoices.value) {
      if (nextMap[r.ar_id] === undefined) nextMap[r.ar_id] = ''
    }
    applyAmountMap.value = nextMap
  } catch (e) {
    ElMessage.error(String(e.message || e))
  } finally {
    loadingCandidates.value = false
  }
}

async function loadApplies() {
  if (!effectiveReceiptId.value) return
  loadingApplies.value = true
  try {
    const j = await apiGet(`/api/ar/apply/receipt-applies?receipt_id=${effectiveReceiptId.value}`)
    applies.value = j.applies || []

    const nextMap = { ...unapplyAmountMap.value }
    for (const a of applies.value) {
      if (nextMap[a.apply_id] === undefined) nextMap[a.apply_id] = ''
    }
    unapplyAmountMap.value = nextMap
  } catch (e) {
    ElMessage.error(String(e.message || e))
  } finally {
    loadingApplies.value = false
  }
}

async function reloadAll() {
  if (!effectiveReceiptId.value) {
    ElMessage.warning('請輸入 receipt_id')
    return
  }
  await loadCandidates()
  await loadApplies()
}

// -----------------------------
// Actions
// -----------------------------
function setQuickAmount(row, mode) {
  if (!row?.ar_id) return
  const open = num(row.open_amount)

  if (mode === 'min') {
    applyAmountMap.value[row.ar_id] = '1'
    return
  }
  if (mode === 'open') {
    applyAmountMap.value[row.ar_id] = String(open)
    return
  }

  // all = min(open, receipt_unapplied)
  const all = Math.max(0, Math.min(open, receiptUnappliedNum.value))
  applyAmountMap.value[row.ar_id] = String(all)
}

async function doPay(row) {
  if (!effectiveReceiptId.value) return
  const arId = Number(row?.ar_id)
  if (!arId) return

  const amountStr = applyAmountMap.value[arId]
  const amount = num(amountStr)
  if (amount <= 0) {
    ElMessage.warning('沖帳金額必須 > 0')
    return
  }

  payingArId.value = arId
  try {
    await apiPost('/api/ar/apply/payment', {
      receipt_id: effectiveReceiptId.value,
      ar_id: arId,
      apply_amount: amount,
      memo: memoInput.value || '手動沖帳',
    })
    ElMessage.success('沖帳成功')
    await reloadAll()
  } catch (e) {
    ElMessage.error(String(e.message || e))
  } finally {
    payingArId.value = null
  }
}

async function doUnapply(applyRow) {
  const applyId = Number(applyRow?.apply_id)
  if (!applyId) return

  const amtStr = unapplyAmountMap.value[applyId]
  const amt = amtStr === '' || amtStr == null ? null : num(amtStr)

  if (amt !== null && amt <= 0) {
    ElMessage.warning('部分反沖金額必須 > 0（或留空做全反沖）')
    return
  }

  unpayingApplyId.value = applyId
  try {
    await apiPost('/api/ar/apply/unapply', {
      apply_id: applyId,
      unapply_amount: amt, // null = 全反沖
      memo: memoInput.value || '反沖',
    })
    ElMessage.success('反沖成功')
    await reloadAll()
  } catch (e) {
    ElMessage.error(String(e.message || e))
  } finally {
    unpayingApplyId.value = null
  }
}

async function doFifo(applyTotalMaybe) {
  if (!effectiveReceiptId.value) return

  let applyTotal = null
  if (applyTotalMaybe !== undefined && applyTotalMaybe !== null && String(applyTotalMaybe).trim() !== '') {
    applyTotal = num(applyTotalMaybe)
    if (applyTotal <= 0) {
      ElMessage.warning('FIFO 指定金額必須 > 0')
      return
    }
  }

  loadingFifo.value = true
  try {
    await apiPost('/api/ar/apply/fifo', {
      receipt_id: effectiveReceiptId.value,
      apply_total: applyTotal,
      memo: memoInput.value || 'FIFO 分攤',
    })
    ElMessage.success('FIFO 分攤完成')
    fifoDialogOpen.value = false
    fifoAmountInput.value = ''
    await reloadAll()
  } catch (e) {
    ElMessage.error(String(e.message || e))
  } finally {
    loadingFifo.value = false
  }
}

// ✅ 一進頁如果 query 已帶 receipt_id 就自動載入
onMounted(() => {
  if (effectiveReceiptId.value) {
    reloadAll()
  }
})
</script>

<style scoped>
/* 讓表格在手機上不要太擠 */
:deep(.el-table .cell) {
  padding-left: 8px;
  padding-right: 8px;
}
</style>
