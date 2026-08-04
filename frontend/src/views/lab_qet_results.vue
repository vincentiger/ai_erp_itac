<template>
  <div class="min-h-screen bg-slate-50 overflow-hidden">
    <main class="mx-auto w-[94vw] max-w-[1500px] pt-4 pb-6">
      <section class="bg-white border border-slate-200 overflow-hidden">
        <div class="px-4 py-3 flex items-center justify-between border-b border-slate-200 gap-3 flex-wrap">
          <div />
          <button
            class="h-9 px-3 bg-white border border-slate-300 disabled:opacity-40"
            :disabled="loading"
            type="button"
            @click="reload"
          >
            重新整理
          </button>
        </div>

        <div class="px-4 py-3 border-b border-slate-200 bg-slate-50">
          <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <input
              v-model.trim="searchLabNo"
              class="h-9 rounded border border-slate-300 bg-white px-3 text-sm"
              placeholder="委託單編號"
              type="text"
              @keyup.enter="applyFilters"
            >
            <input
              v-model.trim="searchCustomer"
              class="h-9 rounded border border-slate-300 bg-white px-3 text-sm"
              placeholder="客戶名稱"
              type="text"
              @keyup.enter="applyFilters"
            >
            <select
              v-model="searchResult"
              class="h-9 rounded border border-slate-300 bg-white px-3 text-sm"
            >
              <option value="">全部判定結果</option>
              <option value="PASS">PASS</option>
              <option value="FAIL">FAIL</option>
              <option value="PENDING">PENDING</option>
            </select>
            <input
              v-model.trim="searchReviewer"
              class="h-9 rounded border border-slate-300 bg-white px-3 text-sm"
              placeholder="審查人"
              type="text"
              @keyup.enter="applyFilters"
            >
          </div>
          <div class="mt-3 flex items-center gap-2">
            <button
              class="h-9 px-3 rounded bg-slate-900 text-white"
              type="button"
              @click="applyFilters"
            >
              搜尋
            </button>
            <button
              class="h-9 px-3 rounded bg-white border border-slate-300"
              type="button"
              @click="clearFilters"
            >
              清除
            </button>
          </div>
        </div>

        <div class="table-scroll">
          <table class="grid-table w-full text-sm">
            <thead class="sticky top-0 z-10 bg-slate-50 text-slate-600">
              <tr>
                <th class="th">委託單編號</th>
                <th class="th">客戶名稱</th>
                <th class="th">測試件品名</th>
                <th class="th">委託單日期</th>
                <th class="th">判定結果</th>
                <th class="th">判定日期</th>
                <th class="th">審查人</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in pagedRows" :key="row.form_id" class="tr hover:bg-slate-100">
                <td class="td">
                  <a href="javascript:void(0)" class="refno-link" @click="openForm(row)">
                    {{ row.entrust_no }}
                  </a>
                </td>
                <td class="td">{{ row.customer_name || '-' }}</td>
                <td class="td">{{ row.product_name || '-' }}</td>
                <td class="td">{{ row.filled_date || '-' }}</td>
                <td class="td">{{ row.final_result || '-' }}</td>
                <td class="td">{{ row.judge_date || '-' }}</td>
                <td class="td">{{ row.judge_reviewer || '-' }}</td>
              </tr>
              <tr v-if="!loading && rows.length === 0">
                <td class="px-3 py-8 text-center text-slate-500" colspan="7">
                  無資料
                </td>
              </tr>
              <tr v-else-if="!loading && filteredRows.length === 0">
                <td class="px-3 py-8 text-center text-slate-500" colspan="7">
                  查無符合條件的資料
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-4 py-3 flex items-center justify-between border-t border-slate-200 gap-3 flex-wrap">
          <div class="text-xs text-slate-500">
            共 {{ filteredRows.length }} 筆，第 {{ page }} / {{ totalPages }} 頁，每頁 {{ pageSize }} 筆
          </div>
          <div class="flex items-center gap-2">
            <button
              class="h-9 px-3 bg-white border border-slate-300 disabled:opacity-40"
              :disabled="page <= 1 || loading"
              type="button"
              @click="goPrev"
            >
              上一頁
            </button>
            <button
              class="h-9 px-3 bg-white border border-slate-300 disabled:opacity-40"
              :disabled="page >= totalPages || loading"
              type="button"
              @click="goNext"
            >
              下一頁
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiFetch } from '@/utils/apiFetch'

const router = useRouter()
const rows = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const searchLabNo = ref('')
const searchCustomer = ref('')
const searchResult = ref('')
const searchReviewer = ref('')
const BASE_URL = import.meta.env.BASE_URL || '/ai/'
const qetApi = (p) => {
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL : `${BASE_URL}/`
  return `${cleanBase}api/lab/qet/${String(p || '').replace(/^\/+/, '')}`
}

const filteredRows = computed(() => {
  const labNo = searchLabNo.value.toLowerCase()
  const customer = searchCustomer.value.toLowerCase()
  const result = searchResult.value.toUpperCase()
  const reviewer = searchReviewer.value.toLowerCase()
  return rows.value.filter((row) => {
    const entrustNo = String(row.entrust_no || '').toLowerCase()
    const customerName = String(row.customer_name || '').toLowerCase()
    const finalResult = String(row.final_result || '').toUpperCase()
    const judgeReviewer = String(row.judge_reviewer || '').toLowerCase()
    if (labNo && !entrustNo.includes(labNo)) return false
    if (customer && !customerName.includes(customer)) return false
    if (result && finalResult !== result) return false
    if (reviewer && !judgeReviewer.includes(reviewer)) return false
    return true
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / pageSize)))
const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredRows.value.slice(start, start + pageSize)
})

function applyFilters() {
  page.value = 1
}

function clearFilters() {
  searchLabNo.value = ''
  searchCustomer.value = ''
  searchResult.value = ''
  searchReviewer.value = ''
  page.value = 1
}

async function reload() {
  loading.value = true
  try {
    const resp = await apiFetch(qetApi('forms/judgment/results'))
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) {
      throw new Error(payload?.msg || `HTTP ${resp.status}`)
    }
    rows.value = Array.isArray(payload.rows) ? payload.rows : []
    if (page.value > Math.max(1, Math.ceil(rows.value.length / pageSize))) {
      page.value = 1
    }
  } catch (e) {
    console.error('[lab_qet_results] reload error:', e)
    rows.value = []
    ElMessage.error(String(e?.message || e))
  } finally {
    loading.value = false
  }
}

function openForm(row) {
  router.push({
    name: 'lab_qet',
    query: { form_id: row.form_id },
  })
}

function goPrev() {
  if (page.value <= 1 || loading.value) return
  page.value -= 1
}

function goNext() {
  if (page.value >= totalPages.value || loading.value) return
  page.value += 1
}

onMounted(() => {
  reload()
})
</script>

<style scoped>
.table-scroll {
  overflow: auto;
}

.grid-table {
  border-collapse: separate;
  border-spacing: 0;
}

.th,
.td {
  padding: 0.75rem 0.875rem;
  border-bottom: 1px solid rgb(226 232 240);
  white-space: nowrap;
}

.th {
  font-weight: 600;
  text-align: left;
}

.refno-link {
  color: rgb(37 99 235);
  text-decoration: underline;
}
</style>
