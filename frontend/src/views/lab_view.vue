<template>
  <div class="min-h-screen bg-slate-50 overflow-hidden">
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
        <div class="px-4 py-3 flex items-center justify-between border-b border-slate-200 gap-3 flex-wrap">
          <div class="font-semibold text-slate-900 hidden sm:block">
            {{ isPickMode ? '選擇要匯入的委託測試單' : '委託測試單列表' }}
          </div>
          <div class="flex items-center gap-2 flex-wrap justify-end">
            <input
              v-model="searchLabNo"
              class="input-field"
              placeholder="委託編號"
              @keydown.enter="goFirstPageAndReload"
            />
            <input
              v-model="searchCustomer"
              class="input-field"
              placeholder="客戶名稱"
              @keydown.enter="goFirstPageAndReload"
            />
            <input
              v-model="searchPartNo"
              class="input-field"
              placeholder="Part No."
              @keydown.enter="goFirstPageAndReload"
            />
            <input
              v-model="searchDrawingNo"
              class="input-field"
              placeholder="圖號"
              @keydown.enter="goFirstPageAndReload"
            />
            <input
              v-model="searchSampleSpec"
              class="input-field"
              placeholder="尺寸 / 規格"
              @keydown.enter="goFirstPageAndReload"
            />
            <input
              v-model="searchDate"
              type="date"
              class="input-field"
              @keydown.enter="goFirstPageAndReload"
            />
            <button
              class="tool-btn"
              type="button"
              :disabled="loading"
              @click="goFirstPageAndReload"
            >
              搜尋
            </button>
          </div>
        </div>

        <div class="table-scroll">
          <table class="grid-table w-full text-sm">
            <thead class="sticky top-0 z-10 bg-slate-50 text-slate-600">
              <tr>
                <th class="th checkbox-col">刪除</th>
                <th class="th">委託編號</th>
                <th class="th">客戶名稱</th>
                <th class="th">品名</th>
                <th class="th">Part No.</th>
                <th class="th">圖號</th>
                <th class="th">尺寸</th>
                <th class="th">建立時間</th>
                <th class="th action-col">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rows" :key="r.form_id" class="tr hover:bg-slate-100">
                <td class="td checkbox-col text-center">
                  <input type="checkbox" v-model="selectedFormIds" :value="r.form_id" />
                </td>
                <td class="td">
                  <a
                    href="javascript:void(0)"
                    class="refno-link"
                    @click="openForm(r)"
                  >
                    {{ r.lab_no }}
                  </a>
                </td>
                <td class="td">{{ r.customer_name }}</td>
                <td class="td">{{ r.sample_desc }}</td>
                <td class="td">{{ r.part_no }}</td>
                <td class="td">{{ r.drawing_no }}</td>
                <td class="td">{{ r.sample_spec }}</td>
                <td class="td">{{ r.created_at }}</td>
                <td class="td action-col">
                  <div class="row-actions">
                    <button class="row-action-btn" type="button" @click="openQet(r)">
                      尺寸表
                    </button>
                    <button class="row-action-btn" type="button" @click="openMech(r)">
                      機械性質
                    </button>
                    <button class="row-action-btn is-copy" type="button" @click="copyForm(r)">
                      {{ isPickMode ? '匯入' : '複製' }}
                    </button>
                    <button class="row-action-btn is-export" type="button" @click="exportReport(r)">
                      匯出報告
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="!loading && rows.length === 0">
                <td class="px-3 py-8 text-center text-slate-500" colspan="9">
                  無資料
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="px-4 py-3 flex items-center justify-between border-t border-slate-200">
          <div class="text-xs text-slate-500">
            第 {{ page }} 頁 / 每頁 {{ pageSize }} 筆
          </div>
          <div class="flex items-center gap-2">
            <button
              class="h-9 px-3 bg-rose-600 text-white disabled:opacity-40"
              :disabled="loading || selectedFormIds.length === 0"
              @click="deleteSelected"
              type="button"
            >
              刪除勾選<span v-if="selectedCount > 0"> ({{ selectedCount }})</span>
            </button>
            <button
              class="h-9 px-3 bg-white disabled:opacity-40"
              :disabled="page <= 1 || loading"
              @click="goPrev"
              type="button"
            >
              上一頁
            </button>
            <button
              class="h-9 px-3 bg-white disabled:opacity-40"
              :disabled="!hasNext || loading"
              @click="goNext"
              type="button"
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
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '@/utils/apiFetch'

const router = useRouter()
const route = useRoute()

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const searchLabNo = ref('')
const searchCustomer = ref('')
const searchPartNo = ref('')
const searchDrawingNo = ref('')
const searchSampleSpec = ref('')
const searchDate = ref('')
const selectedFormIds = ref([])
const selectedCount = computed(() => selectedFormIds.value.length)
const isPickMode = computed(() => String(route.query.pick || '').trim() === 'import')

const hasNext = computed(() => {
  if (total.value > 0) return page.value * pageSize.value < total.value
  return rows.value.length === pageSize.value
})

async function reload() {
  loading.value = true
  try {
    const qs = new URLSearchParams({
      limit: '200',
      include_unreleased: '1',
    })
    if (searchLabNo.value) qs.set('lab_no', searchLabNo.value)
    if (searchCustomer.value) qs.set('customer', searchCustomer.value)
    if (searchPartNo.value) qs.set('part_no', searchPartNo.value)
    if (searchDrawingNo.value) qs.set('drawing_no', searchDrawingNo.value)
    if (searchSampleSpec.value) qs.set('sample_spec', searchSampleSpec.value)
    if (searchDate.value) qs.set('filled_date', searchDate.value)

    const resp = await apiFetch(`/ai/api/lab/instances/search?${qs.toString()}`, {
      method: 'GET',
    })
    const ct = resp.headers.get('content-type') || ''
    if (!ct.includes('application/json')) {
      const text = await resp.text()
      throw new Error(`API did not return JSON: ${text.slice(0, 120)}`)
    }

    const payload = await resp.json()
    if (!resp.ok || payload?.ok === false) {
      throw new Error(payload?.msg || `HTTP ${resp.status}`)
    }

    const list = Array.isArray(payload.rows) ? payload.rows : []
    const start = (page.value - 1) * pageSize.value
    rows.value = list.slice(start, start + pageSize.value)
    total.value = Number(payload.count || list.length || 0)
    selectedFormIds.value = selectedFormIds.value.filter(id => rows.value.some(row => row.form_id === id))
  } catch (e) {
    console.error('[lab_view] reload error:', e)
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function deleteSelected() {
  const formIds = Array.from(new Set(selectedFormIds.value.map(v => String(v || '').trim()).filter(Boolean)))
  if (!formIds.length) return
  if (!window.confirm(`確定要刪除 ${formIds.length} 筆委託測試單？此動作無法復原。`)) return

  loading.value = true
  try {
    const resp = await apiFetch('/ai/api/lab/instances/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ form_ids: formIds }),
    })
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) {
      throw new Error(payload?.msg || `HTTP ${resp.status}`)
    }
    const deleted = Number(payload?.deleted || 0)
    selectedFormIds.value = []
    await reload()
    if (deleted > 0) {
      window.alert('刪除成功')
    } else {
      window.alert('沒有刪除到任何委託測試單，請重新整理後再試一次。')
    }
  } catch (e) {
    console.error('[lab_view] deleteSelected error:', e)
    window.alert(String(e?.message || e))
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

function openForm(row) {
  const formId = String(row?.form_id || '').trim()
  if (!formId) return
  router.push({
    name: 'lab',
    query: { form_id: formId },
  })
}

function openQet(row) {
  const formId = String(row?.form_id || '').trim()
  if (!formId) return
  router.push({
    name: 'lab_qet',
    query: { source_form_id: formId },
  })
}

function openMech(row) {
  const formId = String(row?.form_id || '').trim()
  if (!formId) return
  router.push({
    name: 'lab_mech',
    query: { source_form_id: formId },
  })
}

function copyForm(row) {
  const formId = String(row?.form_id || '').trim()
  if (!formId) return
  router.push({
    name: 'lab',
    query: { copy_from: formId },
  })
}

function exportReport(row) {
  const formId = String(row?.form_id || '').trim()
  if (!formId) return

  const form = document.createElement('form')
  form.method = 'POST'
  form.action = `/ai/api/lab/final-report/forms/${encodeURIComponent(formId)}/export-docx`
  form.target = '_blank'
  form.style.display = 'none'
  document.body.appendChild(form)
  form.submit()
  form.remove()
}

onMounted(() => {
  reload()
})
</script>

<style scoped>
.table-scroll{
  height: calc(100vh - 220px);
  overflow: auto;
}

.grid-table{
  border-collapse: separate;
  border-spacing: 0;
  table-layout: fixed;
}

.th, .td{
  padding: 12px;
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.grid-table tr > *:last-child{
  border-right: none;
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

.input-field:focus{
  border-color: #5F1CB9;
  box-shadow: 0 0 0 3px rgba(95, 28, 185, 0.12);
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

.tool-btn:hover:not(:disabled){
  background: #91C51B;
  border-color: #91C51B;
  color: #fff;
}

.refno-link{
  color: #000 !important;
  font-weight: 700 !important;
  text-decoration: none;
}

.refno-link:hover{
  text-decoration: underline;
  text-decoration-color: #91C51B;
  text-underline-offset: 3px;
}

.checkbox-col{
  width: 56px;
  min-width: 56px;
  max-width: 56px;
}

.action-col{
  width: 330px;
  min-width: 330px;
  max-width: 330px;
}

.row-actions{
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.row-action-btn{
  height: 30px;
  padding: 0 10px;
  border: 1px solid rgba(15, 23, 42, 0.16);
  background: #fff;
  color: #0f172a;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.row-action-btn:hover{
  background: #91C51B;
  border-color: #91C51B;
  color: #fff;
}

.row-action-btn.is-copy{
  border-color: rgba(37, 99, 235, 0.32);
  color: #1d4ed8;
}

.row-action-btn.is-export:hover{
  background: #0f172a;
  border-color: #0f172a;
  color: #fff;
}
</style>
