<template>
  <div class="min-h-screen bg-slate-50 overflow-hidden">
    <main class="mx-auto w-[94vw] max-w-[1500px] pt-4 pb-6">
      <section class="bg-white border border-slate-200 overflow-hidden">
        <div class="px-4 py-3 flex items-center justify-between border-b border-slate-200 gap-3 flex-wrap">
          <div>
            <div class="font-semibold text-slate-900">機械性質試驗紀錄表查修</div>
            <div class="text-xs text-slate-500 mt-1">
              {{ isStandardMode ? '主管設定模式：開啟後回到設定機械性質檢驗記錄表。' : '可查詢、進入修改，或勾選後刪除。' }}
            </div>
          </div>
          <div class="flex items-center gap-2 flex-wrap justify-end">
            <input v-model="searchReportNo" class="input-field" placeholder="報告編號" @keydown.enter="reloadFromFirstPage" />
            <input v-model="searchEntrustNo" class="input-field" placeholder="委託單編號" @keydown.enter="reloadFromFirstPage" />
            <input v-model="searchCustomer" class="input-field" placeholder="客戶名稱" @keydown.enter="reloadFromFirstPage" />
            <button class="tool-btn" type="button" :disabled="loading" @click="reloadFromFirstPage">搜尋</button>
          </div>
        </div>

        <div class="table-scroll">
          <table class="grid-table w-full text-sm">
            <thead class="sticky top-0 z-10 bg-slate-50 text-slate-600">
              <tr>
                <th class="th checkbox-col">刪除</th>
                <th class="th">報告編號</th>
                <th class="th">委託單編號</th>
                <th class="th">客戶名稱</th>
                <th class="th">測試件品名</th>
                <th class="th">日期</th>
                <th class="th">判定</th>
                <th class="th">建立者</th>
                <th class="th">最後修改者</th>
                <th class="th action-col">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in pagedRows" :key="row.report_id" class="tr hover:bg-slate-100">
                <td class="td checkbox-col text-center">
                  <input type="checkbox" v-model="selectedReportIds" :value="row.report_id" />
                </td>
                <td class="td">
                  <a href="javascript:void(0)" class="refno-link" @click="openForm(row)">
                    {{ row.report_no || `報告 ${row.report_id}` }}
                  </a>
                </td>
                <td class="td">{{ row.entrust_no || '-' }}</td>
                <td class="td">{{ row.customer_name || '-' }}</td>
                <td class="td">{{ row.product_name || '-' }}</td>
                <td class="td">{{ row.test_date || '-' }}</td>
                <td class="td">{{ row.final_result || 'PENDING' }}</td>
                <td class="td">{{ row.created_by || '-' }}</td>
                <td class="td">{{ row.updated_by || '-' }}</td>
                <td class="td action-col">
                  <button class="open-btn" type="button" @click="openForm(row)">開啟</button>
                </td>
              </tr>
              <tr v-if="!loading && rows.length === 0">
                <td class="px-3 py-8 text-center text-slate-500" colspan="10">無資料</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-4 py-3 flex items-center justify-between border-t border-slate-200 gap-3 flex-wrap">
          <div class="text-xs text-slate-500">共 {{ rows.length }} 筆，第 {{ page }} / {{ totalPages }} 頁，每頁 {{ pageSize }} 筆</div>
          <div class="flex items-center gap-2">
            <button class="h-9 px-3 bg-rose-600 text-white disabled:opacity-40" :disabled="loading || selectedReportIds.length === 0" type="button" @click="deleteSelected">刪除勾選</button>
            <button class="h-9 px-3 bg-white border border-slate-300 disabled:opacity-40" :disabled="page <= 1 || loading" type="button" @click="goPrev">上一頁</button>
            <button class="h-9 px-3 bg-white border border-slate-300 disabled:opacity-40" :disabled="page >= totalPages || loading" type="button" @click="goNext">下一頁</button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiFetch } from '@/utils/apiFetch'

const router = useRouter()
const route = useRoute()
const rows = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const selectedReportIds = ref([])
const searchReportNo = ref('')
const searchEntrustNo = ref('')
const searchCustomer = ref('')

const isStandardMode = computed(() => String(route.query.mode || '').toLowerCase() === 'standard')
const totalPages = computed(() => Math.max(1, Math.ceil(rows.value.length / pageSize)))
const pagedRows = computed(() => rows.value.slice((page.value - 1) * pageSize, page.value * pageSize))

async function reload() {
  loading.value = true
  try {
    const qs = new URLSearchParams({ limit: '300' })
    if (searchReportNo.value) qs.set('report_no', searchReportNo.value)
    if (searchEntrustNo.value) qs.set('entrust_no', searchEntrustNo.value)
    if (searchCustomer.value) qs.set('customer', searchCustomer.value)
    const resp = await apiFetch(`/ai/api/lab/mech/reports/search?${qs.toString()}`)
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) throw new Error(payload?.msg || `HTTP ${resp.status}`)
    rows.value = Array.isArray(payload.rows) ? payload.rows : []
    selectedReportIds.value = selectedReportIds.value.filter(id => rows.value.some(row => row.report_id === id))
    if (page.value > totalPages.value) page.value = 1
  } catch (e) {
    rows.value = []
    ElMessage.error(String(e?.message || e))
  } finally {
    loading.value = false
  }
}

function reloadFromFirstPage() {
  page.value = 1
  reload()
}

function openForm(row) {
  const reportId = row?.report_id
  if (!reportId) {
    ElMessage.warning('找不到報告 ID')
    return
  }
  router.push({
    name: isStandardMode.value ? 'lab_mech_standard' : 'lab_mech',
    query: { report_id: reportId },
  })
}

async function deleteSelected() {
  const reportIds = Array.from(new Set(selectedReportIds.value.map(v => Number(v)).filter(Boolean)))
  if (!reportIds.length) return
  if (!window.confirm(`確定要刪除 ${reportIds.length} 筆機械性質試驗紀錄表？`)) return
  loading.value = true
  try {
    const resp = await apiFetch('/ai/api/lab/mech/reports/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_ids: reportIds }),
    })
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) throw new Error(payload?.msg || `HTTP ${resp.status}`)
    selectedReportIds.value = []
    await reload()
    ElMessage.success('刪除成功')
  } catch (e) {
    ElMessage.error(String(e?.message || e))
  } finally {
    loading.value = false
  }
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
.table-scroll { overflow: auto; }
.grid-table { border-collapse: separate; border-spacing: 0; }
.th, .td { padding: 0.75rem 0.875rem; border-bottom: 1px solid rgb(226 232 240); white-space: nowrap; }
.th { font-weight: 600; text-align: left; }
.refno-link { color: rgb(37 99 235); text-decoration: underline; }
.checkbox-col { width: 56px; min-width: 56px; max-width: 56px; }
.action-col { width: 92px; min-width: 92px; max-width: 92px; text-align: center; }
.input-field{
  width: min(220px, 36vw);
  height: 40px;
  padding: 0 12px;
  font-size: 12pt;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.14);
  background: #fff;
  outline: none;
}
.tool-btn{
  height: 40px;
  padding: 0 14px;
  border-radius: 10px;
  background: transparent;
  color: #0f172a;
  border: 1px solid rgba(15, 23, 42, 0.12);
  font-size: 12px;
  font-weight: 600;
}
.open-btn{
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid rgba(37, 99, 235, 0.28);
  background: #fff;
  color: rgb(37 99 235);
  font-size: 12px;
  font-weight: 600;
}
</style>
