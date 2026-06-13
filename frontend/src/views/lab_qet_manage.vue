<template>
  <div class="min-h-screen bg-slate-50 overflow-hidden">
    <main class="mx-auto w-[94vw] max-w-[1500px] pt-4 pb-6">
      <section class="bg-white border border-slate-200 overflow-hidden">
        <div class="px-4 py-3 flex items-center justify-between border-b border-slate-200 gap-3 flex-wrap">
          <div>
            <div class="font-semibold text-slate-900">原始尺寸紀錄表查修</div>
            <div class="text-xs text-slate-500 mt-1">可查詢、進入修改，或勾選後刪除。</div>
          </div>
          <div class="flex items-center gap-2 flex-wrap justify-end">
            <input v-model="searchEntrustNo" class="input-field" placeholder="委託單編號" @keydown.enter="reloadFromFirstPage" />
            <input v-model="searchFormNo" class="input-field" placeholder="記錄表標號" @keydown.enter="reloadFromFirstPage" />
            <input v-model="searchCustomer" class="input-field" placeholder="客戶名稱" @keydown.enter="reloadFromFirstPage" />
            <button class="tool-btn" type="button" :disabled="loading" @click="reloadFromFirstPage">搜尋</button>
          </div>
        </div>

        <div class="table-scroll">
          <table class="grid-table w-full text-sm">
            <thead class="sticky top-0 z-10 bg-slate-50 text-slate-600">
              <tr>
                <th class="th checkbox-col">刪除</th>
                <th class="th">記錄表標號</th>
                <th class="th">委託單編號</th>
                <th class="th">客戶名稱</th>
                <th class="th">測試件品名</th>
                <th class="th">日期</th>
                <th class="th">判定</th>
                <th class="th">建立者</th>
                <th class="th">最後修改者</th>
                <th class="th">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in pagedRows" :key="row.form_id" class="tr hover:bg-slate-100">
                <td class="td checkbox-col text-center">
                  <input type="checkbox" v-model="selectedFormIds" :value="row.form_id" />
                </td>
                <td class="td">
                  <a href="javascript:void(0)" class="refno-link" @click="openForm(row)">
                    {{ row.form_no || '-' }}
                  </a>
                </td>
                <td class="td">{{ row.entrust_no || '-' }}</td>
                <td class="td">{{ row.customer_name || '-' }}</td>
                <td class="td">{{ row.product_name || '-' }}</td>
                <td class="td">{{ row.filled_date || '-' }}</td>
                <td class="td">{{ row.final_result || 'PENDING' }}</td>
                <td class="td">{{ row.created_by || '-' }}</td>
                <td class="td">{{ row.updated_by || '-' }}</td>
                <td class="td">
                  <button
                    class="row-btn row-btn-success"
                    type="button"
                    :disabled="loading || !row.entrust_no"
                    @click="openMech(row)"
                  >
                    機械性質表
                  </button>
                </td>
              </tr>
              <tr v-if="!loading && rows.length === 0">
                <td class="px-3 py-8 text-center text-slate-500" colspan="10">無資料</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-4 py-3 flex items-center justify-between border-t border-slate-200 gap-3 flex-wrap">
          <div class="text-xs text-slate-500">
            共 {{ rows.length }} 筆，第 {{ page }} / {{ totalPages }} 頁，每頁 {{ pageSize }} 筆
          </div>
          <div class="flex items-center gap-2">
            <button class="h-9 px-3 bg-rose-600 text-white disabled:opacity-40" :disabled="loading || selectedFormIds.length === 0" type="button" @click="deleteSelected">
              刪除勾選
            </button>
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
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiFetch } from '@/utils/apiFetch'

const router = useRouter()
const rows = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const selectedFormIds = ref([])
const searchEntrustNo = ref('')
const searchFormNo = ref('')
const searchCustomer = ref('')
const BASE_URL = import.meta.env.BASE_URL || '/ai/'
const qetApi = (p) => {
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL : `${BASE_URL}/`
  return `${cleanBase}api/lab/qet/${String(p || '').replace(/^\/+/, '')}`
}
const labApi = (p) => {
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL : `${BASE_URL}/`
  return `${cleanBase}api/lab/${String(p || '').replace(/^\/+/, '')}`
}

const totalPages = computed(() => Math.max(1, Math.ceil(rows.value.length / pageSize)))
const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return rows.value.slice(start, start + pageSize)
})

async function reload() {
  loading.value = true
  try {
    const qs = new URLSearchParams({ limit: '300' })
    if (searchEntrustNo.value) qs.set('entrust_no', searchEntrustNo.value)
    if (searchFormNo.value) qs.set('form_no', searchFormNo.value)
    if (searchCustomer.value) qs.set('customer', searchCustomer.value)
    const resp = await apiFetch(qetApi(`forms/search?${qs.toString()}`))
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) throw new Error(payload?.msg || `HTTP ${resp.status}`)
    rows.value = Array.isArray(payload.rows) ? payload.rows : []
    selectedFormIds.value = selectedFormIds.value.filter(id => rows.value.some(row => row.form_id === id))
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
  router.push({ name: 'lab_qet', query: { form_id: row.form_id } })
}

async function resolveSourceFormId(row) {
  const entrustNo = String(row?.entrust_no || '').trim()
  if (!entrustNo) return ''
  const qs = new URLSearchParams({ lab_no: entrustNo, limit: '20' })
  const resp = await apiFetch(labApi(`instances/search?${qs.toString()}`))
  const payload = await resp.json().catch(() => ({}))
  if (!resp.ok || payload?.ok === false) throw new Error(payload?.msg || `HTTP ${resp.status}`)
  const list = Array.isArray(payload.rows) ? payload.rows : []
  const matched = list.find(item => String(item?.lab_no || '').trim() === entrustNo) || list[0]
  return String(matched?.form_id || '').trim()
}

async function openMech(row) {
  loading.value = true
  try {
    const sourceFormId = await resolveSourceFormId(row)
    if (!sourceFormId) {
      ElMessage.warning('找不到來源委託單，無法帶入機械性質表')
      return
    }
    router.push({ name: 'lab_mech', query: { source_form_id: sourceFormId } })
  } catch (e) {
    ElMessage.error(String(e?.message || e || '無法開啟機械性質表'))
  } finally {
    loading.value = false
  }
}

async function deleteSelected() {
  const formIds = Array.from(new Set(selectedFormIds.value.map(v => String(v || '').trim()).filter(Boolean)))
  if (!formIds.length) return
  if (!window.confirm(`確定要刪除 ${formIds.length} 筆原始尺寸紀錄表？`)) return
  loading.value = true
  try {
    const resp = await apiFetch(qetApi('forms/delete'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ form_ids: formIds }),
    })
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) throw new Error(payload?.msg || `HTTP ${resp.status}`)
    selectedFormIds.value = []
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
.row-btn{
  height: 32px;
  padding: 0 10px;
  border: 1px solid rgb(203 213 225);
  background: white;
  font-size: 13px;
}
.row-btn-success{
  border-color: rgb(22 163 74);
  color: rgb(22 101 52);
}
.row-btn:disabled{
  opacity: 0.45;
  cursor: not-allowed;
}
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
</style>
