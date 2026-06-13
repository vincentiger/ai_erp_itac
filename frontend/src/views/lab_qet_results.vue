<template>
  <div class="min-h-screen bg-slate-50 overflow-hidden">
    <main class="mx-auto w-[94vw] max-w-[1500px] pt-4 pb-6">
      <section class="bg-white border border-slate-200 overflow-hidden">
        <div class="px-4 py-3 flex items-center justify-between border-b border-slate-200 gap-3 flex-wrap">
          <div>
            <div class="font-semibold text-slate-900">尺寸原始紀錄表判定結果</div>
            <div class="text-xs text-slate-500 mt-1">此頁僅供瀏覽，顯示已完成判定的記錄表。</div>
          </div>
          <button
            class="h-9 px-3 bg-white border border-slate-300 disabled:opacity-40"
            :disabled="loading"
            type="button"
            @click="reload"
          >
            重新整理
          </button>
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
            </tbody>
          </table>
        </div>

        <div class="px-4 py-3 flex items-center justify-between border-t border-slate-200 gap-3 flex-wrap">
          <div class="text-xs text-slate-500">
            共 {{ rows.length }} 筆，第 {{ page }} / {{ totalPages }} 頁，每頁 {{ pageSize }} 筆
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
const BASE_URL = import.meta.env.BASE_URL || '/ai/'
const qetApi = (p) => {
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL : `${BASE_URL}/`
  return `${cleanBase}api/lab/qet/${String(p || '').replace(/^\/+/, '')}`
}

const totalPages = computed(() => Math.max(1, Math.ceil(rows.value.length / pageSize)))
const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize
  return rows.value.slice(start, start + pageSize)
})

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
