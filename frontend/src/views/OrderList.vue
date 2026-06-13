<template>
  <div class="p-3 md:p-4">
    <div class="flex items-start justify-between gap-3 mb-3">
      <div>
        <h1 class="text-xl font-semibold">訂單列表</h1>
        <p class="text-sm text-gray-600 mt-1" v-if="summary">
          {{ summary }}
        </p>
      </div>

      <div class="flex gap-2">
        <button
          class="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded"
          @click="reload"
          :disabled="loading"
        >
          重新查詢
        </button>
      </div>
    </div>

    <div class="bg-white border rounded overflow-hidden">
      <div class="p-3 border-b flex items-center justify-between">
        <div class="text-sm text-gray-600">
          共 <span class="font-medium">{{ total }}</span> 筆
        </div>
        <div class="text-sm text-gray-600" v-if="loading">載入中...</div>
      </div>

      <div class="overflow-auto">
        <table class="min-w-[1100px] w-full text-sm">
          <thead class="bg-gray-50 text-gray-700">
            <tr>
              <th class="text-left p-2 border-b">客戶名稱</th>
              <th class="text-left p-2 border-b">業務代表</th>
              <th class="text-left p-2 border-b">訂單日期</th>
              <th class="text-left p-2 border-b">訂單編號</th>
              <th class="text-left p-2 border-b">form_no</th>
              <th class="text-left p-2 border-b">幣別</th>
              <th class="text-right p-2 border-b">訂單金額</th>
              <th class="text-left p-2 border-b">公司抬頭</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="(r, idx) in rows" :key="idx" class="hover:bg-gray-50">
              <td class="p-2 border-b">{{ r['客戶名稱'] }}</td>
              <td class="p-2 border-b">{{ r['業務代表'] }}</td>
              <td class="p-2 border-b">{{ fmtDate(r['訂單日期']) }}</td>
              <td class="p-2 border-b">{{ r['訂單編號'] }}</td>
              <td class="p-2 border-b">{{ r['form_no'] }}</td>
              <td class="p-2 border-b">{{ r['幣別'] }}</td>
              <td class="p-2 border-b text-right">{{ fmtMoney(r['訂單金額']) }}</td>
              <td class="p-2 border-b">{{ r['公司抬頭'] }}</td>
            </tr>

            <tr v-if="!loading && rows.length === 0">
              <td colspan="8" class="p-6 text-center text-gray-500">
                查無資料
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="p-3 flex items-center justify-between">
        <div class="text-sm text-gray-600">
          第 {{ page }} 頁 / 每頁 {{ pageSize }} 筆
        </div>

        <div class="flex gap-2">
          <button
            class="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
            :disabled="page <= 1 || loading"
            @click="go(page - 1)"
          >
            上一頁
          </button>
          <button
            class="px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded disabled:opacity-50"
            :disabled="page * pageSize >= total || loading"
            @click="go(page + 1)"
          >
            下一頁
          </button>
        </div>
      </div>
    </div>

    <div class="mt-3 text-xs text-gray-500">
      Debug Query: <code class="bg-gray-100 px-1 py-0.5 rounded">{{ queryObj }}</code>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const page = ref(Number(route.query.page || 1))
const pageSize = ref(Number(route.query.pageSize || 50))

/**
 * q = base64(JSON.stringify(QueryJSON))
 * QueryJSON 格式建議：
 * {
 *   dataset:"ai_orders",
 *   select:[...],
 *   filters:[...],
 *   sort:[...],
 *   limit:1000
 * }
 */
function decodeQ(q) {
  if (!q) return null
  try {
    const json = atob(String(q))
    return JSON.parse(json)
  } catch (e) {
    console.error('decode q failed', e)
    return null
  }
}

const queryObj = computed(() => decodeQ(route.query.q))

const summary = computed(() => {
  const q = queryObj.value
  if (!q) return ''
  const period = (q.filters || []).find(f => f.field?.includes('日期') && f.op === 'between')
  const sort = (q.sort || []).map(s => `${s.field} ${String(s.dir || 'asc').toUpperCase()}`).join(' → ')
  const ptxt = period ? `期間：${period.value?.[0]} ~ ${period.value?.[1]}` : ''
  const stxt = sort ? `排序：${sort}` : ''
  return [ptxt, stxt].filter(Boolean).join('｜')
})

function fmtDate(v) {
  if (!v) return ''
  // v 可能是 "2025-01-01T00:00:00" 或 Date string
  return String(v).slice(0, 10)
}
function fmtMoney(v) {
  const n = Number(v ?? 0)
  return n.toLocaleString()
}

decodeQ
function go(p) {
  router.replace({
    query: { ...route.query, page: String(p) },
  })
}

function reload() {
  fetchData()
}

watch(
  () => [route.query.q, route.query.page, route.query.pageSize],
  () => {
    page.value = Number(route.query.page || 1)
    pageSize.value = Number(route.query.pageSize || 50)
    fetchData()
  }
)

onMounted(fetchData)
</script>
