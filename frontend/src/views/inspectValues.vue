<template>
  <div class="qet-page p-3 sm:p-5 max-w-[1600px] mx-auto">
    <!-- 頁首 -->
    <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between mb-4">
      <div class="text-sm text-gray-500 mt-1">
        依主管設定的檢驗數輸入實測值，系統自動彙整最大值與最小值
      </div>

      <div class="flex flex-wrap gap-2">
        <el-button plain @click="openManualPdf('尺寸原始記錄表.pdf')">使用說明</el-button>
        <el-button @click="openSourceDialog" plain>選擇委託單</el-button>
        <el-button plain @click="router.push({ name: 'lab_qet_manage' })">查修</el-button>
        <el-button @click="newForm" plain>新增</el-button>
        <el-button
          v-if="state.formId || state.header.entrust_no"
          plain
          type="success"
          :disabled="!state.header.entrust_no"
          @click="goToMechanicalReport"
        >
          機械性質表
        </el-button>
        <el-button :disabled="!state.formId" :loading="state.exporting" @click="exportDocx">
          匯出 Word
        </el-button>
        <el-button :disabled="!state.formId" @click="copyForm" plain>複製表單</el-button>
      </div>
    </div>

    <el-card shadow="never" class="mb-4 rounded-2xl">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <div class="font-semibold">來源委託單</div>
          <el-button size="small" plain @click="openSourceDialog">搜尋 / 更換</el-button>
        </div>
      </template>

      <div class="source-grid text-sm">
        <div class="source-card">
          <div class="text-gray-500">委託單編號</div>
          <div class="font-semibold mt-1">{{ sourceState.labNo || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">客戶</div>
          <div class="font-semibold mt-1">{{ sourceState.customerName || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">日期</div>
          <div class="font-semibold mt-1">{{ sourceState.filledDate || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">聯絡人</div>
          <div class="font-semibold mt-1">{{ sourceState.contactName || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">電話</div>
          <div class="font-semibold mt-1">{{ sourceState.contactTel || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">E-mail</div>
          <div class="font-semibold mt-1 break-all">{{ sourceState.contactEmail || '-' }}</div>
        </div>
        <div class="source-card source-card-wide">
          <div class="text-gray-500">地址</div>
          <div class="font-semibold mt-1">{{ sourceState.address || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">Part No.</div>
          <div class="font-semibold mt-1">{{ sourceState.partNo || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">品名</div>
          <div class="font-semibold mt-1">{{ sourceState.sampleDesc || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">規格</div>
          <div class="font-semibold mt-1">{{ sourceState.sampleSpec || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">材質編號</div>
          <div class="font-semibold mt-1">{{ sourceState.materialNo || '-' }}</div>
        </div>
        <div class="source-card">
          <div class="text-gray-500">批號</div>
          <div class="font-semibold mt-1">{{ sourceState.lotNo || '-' }}</div>
        </div>
      </div>
    </el-card>

    <!-- 表單主資料 -->
    <el-card shadow="never" class="mb-4 rounded-2xl">
      <template #header>
        <div class="font-semibold">基本資料</div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        <el-form-item label="報告號碼">
          <el-input
            v-model="state.header.form_no"
            placeholder="儲存後自動產生 / 或由後端帶回報告號碼"
            readonly
          />
        </el-form-item>

        <el-form-item label="委託編號">
          <el-input v-model="state.header.entrust_no" />
        </el-form-item>

        <el-form-item label="Part No.">
          <el-input v-model="state.header.part_no" />
        </el-form-item>

        <el-form-item label="品名">
          <el-input v-model="state.header.product_name" />
        </el-form-item>

        <el-form-item label="規格">
          <el-input v-model="state.header.specification" />
        </el-form-item>

        <el-form-item label="鍍別">
          <el-input v-model="state.header.plating_type" />
        </el-form-item>

        <el-form-item label="尺寸依據標準">
          <el-input v-model="state.header.dimension_standard" />
        </el-form-item>

        <el-form-item label="圖號">
          <el-input v-model="state.header.drawing_no" />
        </el-form-item>

        <el-form-item label="法規">
          <el-input v-model="state.header.regulation" />
        </el-form-item>

        <el-form-item label="批號">
          <el-input v-model="state.header.lot_no" />
        </el-form-item>

        <el-form-item label="批量">
          <el-input-number v-model="state.header.lot_qty" :min="0" class="w-full" />
        </el-form-item>

        <el-form-item label="材質">
          <el-input v-model="state.header.material" />
        </el-form-item>

        <el-form-item label="製造廠商">
          <el-input v-model="state.header.manufacturer" />
        </el-form-item>

        <el-form-item label="尺寸單位">
          <el-select v-model="state.header.size_unit" class="w-full">
            <el-option label="mm" value="mm" />
            <el-option label="inch" value="inch" />
          </el-select>
        </el-form-item>

        <el-form-item label="溫度">
          <div class="flex items-center gap-2 w-full">
            <el-input-number v-model="state.header.env_temp" :precision="1" :step="0.1" class="flex-1" />
            <span class="text-sm text-gray-600 shrink-0">°C</span>
          </div>
        </el-form-item>

        <el-form-item label="相對濕度">
          <div class="flex items-center gap-2 w-full">
            <el-input-number v-model="state.header.env_humidity" :precision="1" :step="0.1" class="flex-1" />
            <span class="text-sm text-gray-600 shrink-0">%RH</span>
          </div>
        </el-form-item>

        <el-form-item label="抽樣計劃">
          <el-input v-model="state.header.sampling_plan" />
        </el-form-item>

        <el-form-item label="測試日期">
          <el-date-picker
            v-model="state.header.test_date"
            type="date"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            class="w-full"
          />
        </el-form-item>

        <el-form-item label="完成日期">
          <el-date-picker
            v-model="state.header.completed_date"
            type="date"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            class="w-full"
          />
        </el-form-item>

        <el-form-item label="填表日期">
          <el-date-picker
            v-model="state.header.filled_date"
            type="date"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            class="w-full"
          />
        </el-form-item>

        <el-form-item label="測試者">
          <el-select
            v-model="testerSelection"
            multiple
            filterable
            allow-create
            clearable
            default-first-option
            reserve-keyword
            class="w-full"
            placeholder="選擇或輸入多位測試者"
          >
            <el-option
              v-for="name in testerOptions"
              :key="`tester-${name}`"
              :label="name"
              :value="name"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="審查者">
          <el-input v-model="state.header.reviewer" readonly />
        </el-form-item>

        <el-form-item label="總判定">
          <el-select v-model="state.header.final_result" class="w-full" disabled>
            <el-option label="PENDING" value="PENDING" />
            <el-option label="PASS" value="PASS" />
            <el-option label="FAIL" value="FAIL" />
          </el-select>
        </el-form-item>
      </div>

      <div class="mt-3">
        <el-form-item label="備註">
          <el-input v-model="state.header.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </div>
    </el-card>

    <!-- 測試項目工具列 -->
    <el-card shadow="never" class="mb-4 rounded-2xl">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex flex-wrap items-center gap-2">
          <div class="font-semibold">測試項目</div>
          <el-tag type="info">共 {{ state.items.length }} 項</el-tag>
          <el-tag v-if="currentItem" type="success">本項 {{ itemMeasureCount(currentItem) }} 筆</el-tag>
        </div>

        <div class="flex flex-wrap gap-2">
          <el-button type="primary" @click="addItem()">新增測試項目</el-button>
          <el-button @click="bulkFillItemNames" plain>自動填 A/B/C...</el-button>
        </div>
      </div>
    </el-card>

    <div class="grid grid-cols-1 xl:grid-cols-[420px_minmax(0,1fr)] gap-4">
      <!-- 左側：測試項目清單 -->
      <el-card shadow="never" class="rounded-2xl">
        <template #header>
          <div class="font-semibold">項目清單</div>
        </template>

        <div class="flex flex-col gap-3">
          <div
            v-for="(item, idx) in state.items"
            :key="item._rowKey"
            class="border rounded-2xl p-3 cursor-pointer transition"
            :class="idx === state.activeItemIndex ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'"
            @click="state.activeItemIndex = idx"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <div class="font-semibold truncate">
                  {{ item.item_name || `測試項目 ${idx + 1}` }}
                </div>
                <div class="text-xs text-gray-500 mt-1 truncate">
                  {{ isAppearanceItem(item) ? '依據標準' : '標準值' }}：{{ item.std_value || '-' }}
                </div>
                <div class="text-xs text-gray-500 truncate">
                  量具：{{ item.gauge_no || '-' }}
                </div>
              </div>

              <div class="flex flex-col gap-1 items-end shrink-0">
                <el-tag size="small" :type="resultTagType(item.result)">
                  {{ item.result || 'PENDING' }}
                </el-tag>
                <span class="text-[11px] text-gray-400">#{{ idx + 1 }}</span>
              </div>
            </div>

            <div class="mt-3 grid grid-cols-3 gap-2">
              <el-button size="small" @click.stop="duplicateItem(idx)">複製</el-button>
              <el-button size="small" @click.stop="clearMeasurements(idx)">清空量測</el-button>
              <el-button size="small" type="danger" plain @click.stop="removeItem(idx)">刪除</el-button>
            </div>
          </div>

          <div v-if="!state.items.length" class="text-sm text-gray-500 border border-dashed rounded-2xl p-6 text-center">
            尚無測試項目，請先新增
          </div>
        </div>
      </el-card>

      <!-- 右側：目前編輯的項目 -->
      <el-card shadow="never" class="rounded-2xl">
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <div class="font-semibold">
              編輯測試項目
              <span v-if="currentItem" class="text-gray-500 font-normal ml-2">
                {{ currentItem.item_name || `第 ${state.activeItemIndex + 1} 項` }}
              </span>
            </div>

            <div class="flex gap-2" v-if="currentItem">
              <el-button size="small" @click="pasteFromClipboardPrompt">貼上量測值</el-button>
            </div>
          </div>
        </template>

        <div v-if="currentItem">
          <!-- 項目基本資訊 -->
          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 mb-4">
            <el-form-item :label="isAppearanceItem(currentItem) ? '依據標準' : '標準值'">
              <el-input v-model="currentItem.std_value" placeholder="由下方標準值輔助帶入" readonly />
            </el-form-item>

            <el-form-item label="實測值">
              <el-input v-model="currentItem.actual_value" placeholder="輸入量測值後自動彙整" readonly />
            </el-form-item>

            <el-form-item label="量具／編號">
              <el-input v-model="currentItem.gauge_no" clearable placeholder="請輸入本項量具／編號" />
            </el-form-item>

            <el-form-item label="檢驗數">
              <el-input-number
                v-model="currentItem.inspect_qty"
                :min="1"
                class="w-full"
                @change="normalizeItemMeasurementCount(currentItem)"
              />
            </el-form-item>

            <el-form-item label="最小值 / 最大值">
              <div class="flex gap-2 w-full">
                <el-input
                  v-model="currentItem.min_value"
                  placeholder="最小值"
                  inputmode="decimal"
                  readonly
                />
                <el-input
                  v-model="currentItem.max_value"
                  placeholder="最大值"
                  inputmode="decimal"
                  readonly
                />
              </div>
            </el-form-item>
          </div>

          <!-- 貼上區 -->
          <el-card shadow="never" class="mb-4 border-dashed">
            <template #header>
              <div class="font-semibold">快速貼上量測值</div>
            </template>

            <div class="text-sm text-gray-500 mb-2">
              可直接貼上 Excel 的一列或一欄，例如以 Tab、換行、逗號、空白分隔。
            </div>

            <div class="flex flex-col gap-2">
              <el-input
                v-model="currentItem.pasteText"
                type="textarea"
                :rows="4"
                placeholder="例如：9.98 9.99 10.00 ... 或一行一筆"
              />
              <div class="flex flex-wrap gap-2">
                <el-button @click="applyPasteText">套用到本項</el-button>
                <el-button @click="currentItem.pasteText = ''" plain>清空</el-button>
              </div>
            </div>
          </el-card>

          <!-- 量測輸入 -->
          <el-card shadow="never" class="border-dashed">
            <template #header>
              <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div class="font-semibold">量測值輸入（{{ itemMeasureCount(currentItem) }} 筆）</div>
                <div class="text-xs text-gray-500">
                  支援手機版；每格都可個別輸入，也可用上方批次貼上
                </div>
              </div>
            </template>

            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6 gap-3">
              <div
                v-for="(v, i) in currentItem.measurements"
                :key="`${currentItem._rowKey}-m-${i}`"
                class="border rounded-2xl p-3 bg-white"
              >
                <div class="text-xs text-gray-500 mb-2">{{ i + 1 }}</div>
                <el-select
                  v-if="isOkNgItem(currentItem)"
                  v-model="currentItem.measurements[i]"
                  clearable
                  class="w-full"
                  @change="handleMeasurementInput(currentItem, i)"
                >
                  <el-option label="OK" value="OK" />
                  <el-option label="NG" value="NG" />
                </el-select>
                <el-input
                  v-else
                  v-model="currentItem.measurements[i]"
                  inputmode="decimal"
                  clearable
                  @input="handleMeasurementInput(currentItem, i)"
                  @blur="normalizeMeasurementAngle(currentItem, i)"
                />
              </div>
            </div>
          </el-card>
        </div>

        <div v-else class="text-sm text-gray-500 p-8 text-center border border-dashed rounded-2xl">
          請先新增測試項目
        </div>
      </el-card>
    </div>

    <!-- 下方摘要 -->
    <el-card shadow="never" class="mt-4 rounded-2xl">
      <template #header>
        <div class="font-semibold">摘要</div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div class="border rounded-2xl p-4">
          <div class="text-sm text-gray-500">報告號碼</div>
          <div class="text-lg font-semibold mt-1">{{ state.header.form_no || '-' }}</div>
        </div>

        <div class="border rounded-2xl p-4">
          <div class="text-sm text-gray-500">測試項目數</div>
          <div class="text-lg font-semibold mt-1">{{ state.items.length }}</div>
        </div>

        <div class="border rounded-2xl p-4">
          <div class="text-sm text-gray-500">總判定</div>
          <div class="text-lg font-semibold mt-1">{{ state.header.final_result || 'PENDING' }}</div>
        </div>
      </div>
    </el-card>

    <div class="qet-footer">
      <div class="qet-footer-inner">
        <el-button :disabled="!state.formId" plain type="danger" @click="deleteForm">刪除</el-button>
        <el-button :disabled="!state.header.entrust_no" plain @click="goToMechanicalReport">
          機械性質表
        </el-button>
        <el-button :loading="state.saving" type="primary" @click="saveForm">儲存</el-button>
      </div>
    </div>

    <el-dialog v-model="sourceState.dialogVisible" title="選擇委託單" width="960px">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <el-input v-model="sourceState.searchLabNo" placeholder="委託單編號" @keyup.enter="searchSourceForms" />
          <el-input v-model="sourceState.searchCustomer" placeholder="客戶名稱" @keyup.enter="searchSourceForms" />
          <el-date-picker
            v-model="sourceState.searchDate"
            type="date"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            placeholder="日期"
          />
          <el-button :loading="sourceState.loading" type="primary" @click="searchSourceForms">搜尋</el-button>
        </div>

        <el-table :data="sourceState.results" border height="360">
          <el-table-column prop="lab_no" label="委託單編號" width="180" />
          <el-table-column prop="customer_name" label="客戶" min-width="200" />
          <el-table-column prop="filled_date" label="日期" width="130" />
          <el-table-column prop="sample_desc" label="品名" min-width="180" show-overflow-tooltip />
          <el-table-column prop="sample_spec" label="規格" min-width="180" show-overflow-tooltip />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="selectSourceForm(row.form_id)">選取</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from '@/utils/apiFetch'

const BASE_URL = import.meta.env.BASE_URL || '/ai/'
const api = (p) => {
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL : BASE_URL + '/'
  return `${window.location.origin}${cleanBase}api/${String(p || '').replace(/^\/+/, '')}`
}
const qetApi = (p) => {
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL : `${BASE_URL}/`
  return `${cleanBase}api/lab/qet/${String(p || '').replace(/^\/+/, '')}`
}
const route = useRoute()
const router = useRouter()

function openManualPdf(fileName) {
  if (!fileName) return
  const target = `${import.meta.env.BASE_URL}manuals/${encodeURIComponent(String(fileName))}`
  window.open(target, '_blank', 'noopener')
}

const todayStr = () => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${dd}`
}

const nextRowKey = () => `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
const APPEARANCE_STANDARD = '目視 ASTM F788-20e1'

function currentUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
}

function currentUserName() {
  const user = currentUser()
  return String(user?.name || user?.account || user?.id || '').trim()
}

function createItem(seqNo = 1, measureCount = 20) {
  return {
    _rowKey: nextRowKey(),
    seq_no: seqNo,
    item_name: '',
    std_value: '',
    std_min: '',
    std_max: '',
    std_unit: '°',
    actual_value: '',
    min_value: '',
    max_value: '',
    gauge_no: '',
    inspect_qty: measureCount,
    result: 'PENDING',
    remark: '',
    measurements: Array(measureCount).fill(''),
    pasteText: ''
  }
}

const state = reactive({
  formId: '',
  saving: false,
  exporting: false,
  loading: false,
  measureCount: 20,
  activeItemIndex: 0,
  pasteText: '',
  header: {
    form_no: '',
    entrust_no: '',
    part_no: '',
    product_name: '',
    specification: '',
    plating_type: '',
    dimension_standard: '',
    drawing_no: '',
    regulation: '',
    lot_no: '',
    lot_qty: null,
    material: '',
    manufacturer: '',
    size_unit: 'mm',
    env_temp: null,
    env_humidity: null,
    sampling_plan: '無',
    test_date: todayStr(),
    completed_date: todayStr(),
    filled_date: todayStr(),
    tester: currentUserName(),
    reviewer: '',
    final_result: 'PENDING',
    remarks: ''
  },
  items: [createItem(1, 20)]
})

const sourceState = reactive({
  dialogVisible: false,
  loading: false,
  sourceFormId: '',
  labNo: '',
  customerName: '',
  filledDate: '',
  contactName: '',
  contactTel: '',
  contactEmail: '',
  address: '',
  partNo: '',
  sampleDesc: '',
  sampleSpec: '',
  materialNo: '',
  lotNo: '',
  searchLabNo: '',
  searchCustomer: '',
  searchDate: '',
  results: []
})

const currentItem = computed(() => state.items[state.activeItemIndex] || null)
const testerSelection = computed({
  get() {
    return String(state.header.tester || '')
      .split(/[、,，;；\n]+/)
      .map(x => x.trim())
      .filter(Boolean)
  },
  set(values) {
    state.header.tester = Array.isArray(values)
      ? values.map(x => String(x || '').trim()).filter(Boolean).join('、')
      : ''
  }
})
const testerOptions = computed(() => {
  const names = new Set()
  const current = currentUserName()
  if (current) names.add(current)
  testerSelection.value.forEach(name => names.add(name))
  return [...names]
})

function isAppearanceItem(item) {
  return /appearance|外觀/i.test(String(item?.item_name || '').trim())
}

function normalizeAppearanceItem(item) {
  if (!item || !isAppearanceItem(item)) return item
  item.std_value = APPEARANCE_STANDARD
  item.std_min = ''
  item.std_max = ''
  item.std_unit = 'OK/NG'
  item.gauge_no = item.gauge_no || '目視'
  item.remark = item.remark || `依據標準 - ${APPEARANCE_STANDARD}`
  return item
}

async function readJsonOrThrow(resp, fallbackMessage) {
  const contentType = String(resp.headers.get('content-type') || '')
  if (!contentType.includes('application/json')) {
    const text = await resp.text().catch(() => '')
    throw new Error(text ? `非 JSON 回應：${text.slice(0, 120)}` : fallbackMessage)
  }
  const json = await resp.json()
  if (!resp.ok || !json?.ok) {
    throw new Error(json?.msg || fallbackMessage)
  }
  return json
}

function resultTagType(v) {
  if (v === 'PASS') return 'success'
  if (v === 'FAIL') return 'danger'
  return 'info'
}

function normalizeMeasurements(arr, targetCount) {
  const x = Array.isArray(arr) ? [...arr] : []
  while (x.length < targetCount) x.push('')
  return x.slice(0, targetCount).map(v => v == null ? '' : String(v))
}

function parsePositiveInt(value) {
  const num = Number(value)
  return Number.isFinite(num) && num > 0 ? Math.floor(num) : null
}

function formatSourceQuantity(value, unit = 'PCS') {
  const num = Number(String(value ?? '').replace(/,/g, ''))
  const text = Number.isFinite(num) ? num.toLocaleString('en-US') : String(value ?? '')
  return `${text} ${unit || 'PCS'}`.trim()
}

function sourceInspectQty(values = {}) {
  return parsePositiveInt(values.inspect_qty)
    || parsePositiveInt(values.inspection_qty)
    || parsePositiveInt(values.test_qty)
    || parsePositiveInt(values.sample_qty)
    || null
}

function itemMeasureCount(item) {
  const qty = Number(item?.inspect_qty)
  const existing = Array.isArray(item?.measurements) ? item.measurements.length : 0
  return Math.max(1, Number.isFinite(qty) && qty > 0 ? Math.floor(qty) : existing || state.measureCount || 1)
}

function normalizeItemMeasurementCount(item) {
  if (!item) return
  const count = itemMeasureCount(item)
  item.inspect_qty = count
  item.measurements = normalizeMeasurements(item.measurements, count)
}

function applySourceInspectQtyToItems(values = {}) {
  if (state.formId) return
  const qty = sourceInspectQty(values)
  if (!qty) return
  state.measureCount = qty
  state.items.forEach((item) => {
    if (!parsePositiveInt(item.inspect_qty) || Number(item.inspect_qty) === 20) {
      item.inspect_qty = qty
    }
    normalizeItemMeasurementCount(item)
  })
}

function addItem() {
  state.items.push(createItem(state.items.length + 1, state.measureCount))
  state.activeItemIndex = state.items.length - 1
}

function removeItem(idx) {
  if (state.items.length <= 1) {
    ElMessage.warning('至少保留一個測試項目')
    return
  }
  state.items.splice(idx, 1)
  state.items.forEach((it, i) => { it.seq_no = i + 1 })
  if (state.activeItemIndex >= state.items.length) {
    state.activeItemIndex = state.items.length - 1
  }
}

function duplicateItem(idx) {
  const src = state.items[idx]
  if (!src) return
  const cloned = JSON.parse(JSON.stringify(src))
  cloned._rowKey = nextRowKey()
  cloned.seq_no = idx + 2
  state.items.splice(idx + 1, 0, cloned)
  state.items.forEach((it, i) => { it.seq_no = i + 1 })
  state.activeItemIndex = idx + 1
}

function clearMeasurements(idx) {
  const item = state.items[idx]
  if (!item) return
  item.measurements = Array(itemMeasureCount(item)).fill('')
  syncActualValue(item)
}

function bulkFillItemNames() {
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  state.items.forEach((item, i) => {
    if (!item.item_name) item.item_name = letters[i] || `Item${i + 1}`
  })
}

function fillInspectQtyByMeasureCount() {
  if (!currentItem.value) return
  normalizeItemMeasurementCount(currentItem.value)
}

function parseMeasurementNumber(value) {
  const text = String(value ?? '').trim()
  if (!text) return null
  const shortcutAngle = text.match(/^(-?\d+(?:\.\d+)?)\s*'\s*(\d+(?:\.\d+)?)\s*(?:"|″)?$/)
  if (shortcutAngle) {
    const deg = Number(shortcutAngle[1] || 0)
    const min = Number(shortcutAngle[2] || 0)
    const sign = deg < 0 ? -1 : 1
    return sign * (Math.abs(deg) + min / 60)
  }
  const angle = text.match(/^(-?\d+(?:\.\d+)?)\s*(?:°|∘|度|d)?\s*(?:(\d+(?:\.\d+)?)\s*(?:'|′|分|m))?\s*(?:(\d+(?:\.\d+)?)\s*(?:"|″|秒|s))?$/i)
  if (angle && (/[°∘度'′分"″秒]/.test(text))) {
    const deg = Number(angle[1] || 0)
    const min = Number(angle[2] || 0)
    const sec = Number(angle[3] || 0)
    const sign = deg < 0 ? -1 : 1
    return sign * (Math.abs(deg) + min / 60 + sec / 3600)
  }
  const cleaned = text.replace(/[°∘度℃%]/g, '').trim()
  const num = Number(cleaned)
  return Number.isFinite(num) ? num : null
}

function isAngleUnit(unit) {
  return /^(°|度|度數|angle)$/i.test(String(unit || '').trim())
}

function isAngleItem(item) {
  return isAngleUnit(item?.std_unit)
}

function isOkNgItem(item) {
  const mode = `${item?.std_unit || ''} ${item?.std_value || ''}`
  return /OK\/NG/i.test(mode)
}

function isRefItem(item) {
  const mode = `${item?.std_unit || ''} ${item?.std_value || ''}`
  return /\bREF\b/i.test(mode)
}

function normalizeOkNgValue(value) {
  const text = String(value ?? '').trim().toUpperCase()
  if (!text) return ''
  if (['OK', 'PASS', 'P'].includes(text)) return 'OK'
  if (['NG', 'FAIL', 'F', 'N'].includes(text)) return 'NG'
  return text
}

function cleanAngleNumber(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return ''
  return Number.isInteger(n) ? String(n) : String(n).replace(/0+$/, '').replace(/\.$/, '')
}

function decimalDegreeToAngleText(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return ''
  const sign = n < 0 ? '-' : ''
  const abs = Math.abs(n)
  const deg = Math.floor(abs)
  const totalSeconds = Math.round((abs - deg) * 3600)
  const min = Math.floor(totalSeconds / 60)
  const sec = totalSeconds % 60
  if (sec) return `${sign}${deg}°${min}'${sec}"`
  if (min) return `${sign}${deg}°${min}'`
  return `${sign}${deg}°`
}

function formatAngleInput(value, { force = false } = {}) {
  const text = String(value ?? '').trim()
  if (!text) return ''

  const shortcut = text.match(/^(-?\d+(?:\.\d+)?)\s*'\s*(\d+(?:\.\d+)?)\s*(?:"|″)?$/)
  if (shortcut) {
    return `${cleanAngleNumber(shortcut[1])}°${cleanAngleNumber(shortcut[2])}'`
  }

  const angle = text.match(/^(-?\d+(?:\.\d+)?)\s*(?:°|∘|度|d)?\s*(?:(\d+(?:\.\d+)?)\s*(?:'|′|分|m))?\s*(?:(\d+(?:\.\d+)?)\s*(?:"|″|秒|s))?$/i)
  if (angle && (force || /[°∘度'′分"″秒]/.test(text))) {
    const deg = cleanAngleNumber(angle[1])
    const min = cleanAngleNumber(angle[2])
    const sec = cleanAngleNumber(angle[3])
    if (sec) return `${deg}°${min || 0}'${sec}"`
    if (min) return `${deg}°${min}'`
    if (force && String(angle[1] || '').includes('.')) return decimalDegreeToAngleText(angle[1])
    return `${deg}°`
  }

  return text
}

function normalizeMeasurementAngle(item, index) {
  if (!item || !isAngleItem(item)) return
  const measurements = Array.isArray(item.measurements) ? item.measurements : []
  const before = String(measurements[index] ?? '').trim()
  const next = formatAngleInput(before, { force: true })
  if (next !== before) measurements[index] = next
  syncActualValue(item)
}

function handleMeasurementInput(item, index) {
  if (item && isAngleItem(item)) {
    const measurements = Array.isArray(item.measurements) ? item.measurements : []
    const raw = String(measurements[index] ?? '').trim()
    if (/^-?\d+(?:\.\d+)?\s*'\s*\d+(?:\.\d+)?\s*(?:"|″)$/.test(raw)) {
      measurements[index] = formatAngleInput(raw)
    }
  }
  syncActualValue(item)
}

function normalizeItemAngleValues(item) {
  if (!item || !isAngleItem(item)) return
  item.measurements = (item.measurements || []).map(v => formatAngleInput(v, { force: true }))
  item.min_value = formatAngleInput(item.min_value, { force: true })
  item.max_value = formatAngleInput(item.max_value, { force: true })
  syncActualValue(item)
}

function normalizeActualRangeAngle(item) {
  if (!item || !isAngleItem(item)) return
  item.min_value = formatAngleInput(item.min_value, { force: true })
  item.max_value = formatAngleInput(item.max_value, { force: true })
  syncActualFromMaxMin(item)
}

function getNumericMeasurements(item) {
  return (item?.measurements || [])
    .map(v => String(v ?? '').trim())
    .filter(v => v !== '')
    .map(v => parseMeasurementNumber(v))
    .filter(v => v !== null)
}

function itemAvg(item) {
  const nums = getNumericMeasurements(item)
  if (!nums.length) return ''
  return (nums.reduce((a, b) => a + b, 0) / nums.length).toFixed(4)
}

function itemMin(item) {
  const nums = getNumericMeasurements(item)
  if (!nums.length) return ''
  return Math.min(...nums).toString()
}

function itemMax(item) {
  const nums = getNumericMeasurements(item)
  if (!nums.length) return ''
  return Math.max(...nums).toString()
}

function syncActualValue(item) {
  if (!item) return
  normalizeItemMeasurementCount(item)
  if (isOkNgItem(item)) {
    item.measurements = (item.measurements || []).map(normalizeOkNgValue)
    const values = item.measurements.map(v => String(v || '').trim()).filter(Boolean)
    item.min_value = ''
    item.max_value = ''
    item.actual_value = values.length
      ? (values.every(v => /^OK$/i.test(v)) ? 'OK' : 'NG')
      : ''
    autoJudgeItem(item)
    return
  }
  const min = itemMin(item)
  const max = itemMax(item)
  if (min || max) {
    item.min_value = isAngleItem(item) ? formatAngleInput(min, { force: true }) : min
    item.max_value = isAngleItem(item) ? formatAngleInput(max, { force: true }) : max
  }
  const avg = itemAvg(item)
  if (avg) item.actual_value = avg
  autoJudgeItem(item)
}

function parsePasteValues(raw) {
  return String(raw || '')
    .replace(/\r/g, '\n')
    .split(/[\n\t,，;；\s]+/)
    .map(x => x.trim())
    .filter(Boolean)
}

function applyPasteText() {
  if (!currentItem.value) return
  const vals = parsePasteValues(currentItem.value.pasteText)
  if (!vals.length) {
    ElMessage.warning('沒有可套用的量測值')
    return
  }

  const count = itemMeasureCount(currentItem.value)
  const arr = Array(count).fill('')
  vals.slice(0, count).forEach((v, i) => {
    arr[i] = isOkNgItem(currentItem.value)
      ? normalizeOkNgValue(v)
      : (isAngleItem(currentItem.value) ? formatAngleInput(v, { force: true }) : v)
  })
  currentItem.value.measurements = arr
  syncActualValue(currentItem.value)
  ElMessage.success(`已套用 ${Math.min(vals.length, count)} 筆量測值`)
}

function updateStandardValue(item) {
  if (!item) return
  if (isAppearanceItem(item)) {
    normalizeAppearanceItem(item)
    autoJudgeItem(item)
    return
  }
  const unit = String(item.std_unit || '').trim()
  const min = String(item.std_min ?? '').trim()
  const max = String(item.std_max ?? '').trim()
  if (unit === 'REF') {
    item.std_value = ['REF', min].filter(Boolean).join(' ')
    item.std_max = ''
    autoJudgeItem(item)
    return
  }
  if (['OK/NG', 'Go/NoGo'].includes(unit)) {
    item.std_value = unit
    item.std_min = ''
    item.std_max = ''
    autoJudgeItem(item)
    return
  }
  if (!min && !max) {
    item.std_value = ''
    return
  }
  if (min && max) {
    item.std_value = min === max
      ? formatStandardValueText(min, unit)
      : formatStandardRangeText(min, max, unit)
  } else if (min) {
    item.std_value = `${formatStandardValueText(min, unit)} MIN`
  } else {
    item.std_value = `${formatStandardValueText(max, unit)} MAX`
  }
  autoJudgeItem(item)
}

function formatStandardValueText(value, unit) {
  const text = String(value ?? '').trim()
  if (!text) return ''
  if (isAngleUnit(unit)) return formatAngleInput(text, { force: true })
  return [text, unit].filter(Boolean).join(' ')
}

function formatStandardRangeText(min, max, unit) {
  if (isAngleUnit(unit)) {
    return `${formatAngleInput(min, { force: true })} - ${formatAngleInput(max, { force: true })}`
  }
  return [`${String(min ?? '').trim()} - ${String(max ?? '').trim()}`, String(unit || '').trim()]
    .filter(Boolean)
    .join(' ')
}

function handleStandardMinInput(item) {
  if (!item) return
  const min = String(item.std_min ?? '').trim()
  const max = String(item.std_max ?? '').trim()
  if (min && !max && !/^REF$/i.test(String(item.std_unit || '').trim())) {
    item.std_max = item.std_min
  }
  updateStandardValue(item)
}

function parseMaxMinValue(raw) {
  const text = String(raw || '').trim()
  if (!text) return { maxValue: '', minValue: '' }
  if (!/[\/／－–—~～至]/.test(text)) return { maxValue: '', minValue: '' }
  const normalized = text.replace(/[－–—~～至]/g, '/')
  const parts = normalized.split('/').map(x => x.trim()).filter(Boolean)
  if (parts.length >= 2) {
    return { minValue: parts[0], maxValue: parts[1] }
  }
  return { maxValue: text, minValue: '' }
}

function parseStandardValue(raw) {
  const text = String(raw || '').trim()
  if (!text) return { minValue: '', maxValue: '', unit: '°' }
  const unitMatch = text.match(/(Go\/NoGo|OK\/NG|REF|inch|mm|°)/i)
  const unit = unitMatch ? unitMatch[1] : '°'
  if (isAngleUnit(unit)) {
    const body = text.replace(/\b(MIN|MAX)\b/gi, '').trim()
    const parts = body.split(/\s+(?:-|－|–|—|~|～|至)\s+|(?:－|–|—|~|～|至)/).map(x => x.trim()).filter(Boolean)
    const angleParts = parts.map(x => formatAngleInput(x.replace(/\s*°\s*$/, '°'), { force: true })).filter(Boolean)
    if (/\bMAX\b/i.test(text)) {
      return { minValue: '', maxValue: angleParts[0] || '', unit }
    }
    if (/\bMIN\b/i.test(text)) {
      return { minValue: angleParts[0] || '', maxValue: '', unit }
    }
    return {
      minValue: angleParts[0] || '',
      maxValue: angleParts[1] || '',
      unit
    }
  }
  const nums = text.match(/-?\d+(?:\.\d+)?/g) || []
  return {
    minValue: nums[0] || '',
    maxValue: nums[1] || '',
    unit
  }
}

function syncActualFromMaxMin(item) {
  if (!item) return
  const min = String(item.min_value || '').trim()
  const max = String(item.max_value || '').trim()
  item.actual_value = [min, max].filter(Boolean).join(' / ')
  autoJudgeItem(item)
}

function autoJudgeItem(item) {
  if (!item) return
  normalizeItemMeasurementCount(item)
  if (isOkNgItem(item)) {
    item.measurements = (item.measurements || []).map(normalizeOkNgValue)
  }
  const std = String(item.std_value || '').trim()
  const unit = String(item.std_unit || '').trim()
  const mode = unit || std
  const values = (item.measurements || []).map(v => String(v ?? '').trim()).filter(Boolean)
  if (/^REF$/i.test(mode) || /^REF$/i.test(std)) {
    item.result = values.length ? 'PASS' : 'PENDING'
    updateFinalResult()
    return
  }
  if (/OK\/NG/i.test(mode) || /OK\/NG/i.test(std)) {
    if (!values.length) {
      item.result = 'PENDING'
      updateFinalResult()
      return
    }
    item.result = values.every(v => /^OK$/i.test(v)) ? 'PASS' : 'FAIL'
    updateFinalResult()
    return
  }
  if (/Go\/NoGo/i.test(mode) || /Go\/NoGo/i.test(std)) {
    if (!values.length) {
      item.result = 'PENDING'
      updateFinalResult()
      return
    }
    item.result = values.every(v => /^(Go\/NoGo|Go|OK)$/i.test(v)) ? 'PASS' : 'FAIL'
    updateFinalResult()
    return
  }

  const nums = getNumericMeasurements(item)
  if (!nums.length) {
    item.result = 'PENDING'
    updateFinalResult()
    return
  }
  const minStd = parseMeasurementNumber(item.std_min)
  const maxStd = parseMeasurementNumber(item.std_max)
  const minActual = Math.min(...nums)
  const maxActual = Math.max(...nums)
  const passMin = minStd === null || minActual >= minStd
  const passMax = maxStd === null || maxActual <= maxStd
  item.result = passMin && passMax ? 'PASS' : 'FAIL'
  updateFinalResult()
}

function updateFinalResult() {
  const results = state.items.map(item => String(item.result || 'PENDING').trim().toUpperCase())
  if (results.some(result => result === 'FAIL')) {
    state.header.final_result = 'FAIL'
  } else if (results.length && results.every(result => result === 'PASS')) {
    state.header.final_result = 'PASS'
  } else {
    state.header.final_result = 'PENDING'
  }
}

function normalizeItemForSave(item) {
  const out = { ...item }
  normalizeAppearanceItem(out)
  updateStandardValue(out)
  autoJudgeItem(out)
  if (isOkNgItem(out)) {
    out.measurements = (out.measurements || []).map(normalizeOkNgValue)
    out.min_value = ''
    out.max_value = ''
    const values = out.measurements.map(v => String(v || '').trim()).filter(Boolean)
    out.actual_value = values.length
      ? (values.every(v => /^OK$/i.test(v)) ? 'OK' : 'NG')
      : ''
  }
  if (isAngleItem(out)) {
    out.measurements = (out.measurements || []).map(v => formatAngleInput(v, { force: true }))
    out.min_value = formatAngleInput(out.min_value, { force: true })
    out.max_value = formatAngleInput(out.max_value, { force: true })
  }
  const min = String(out.min_value || '').trim()
  const max = String(out.max_value || '').trim()
  if (max || min) {
    out.actual_value = [min, max].filter(Boolean).join(' / ')
  }
  return out
}

async function pasteFromClipboardPrompt() {
  try {
    const txt = await navigator.clipboard.readText()
    if (currentItem.value) currentItem.value.pasteText = txt || ''
    if (txt) {
      applyPasteText()
    } else {
      ElMessage.warning('剪貼簿沒有內容')
    }
  } catch {
    ElMessage.warning('無法直接讀取剪貼簿，請改用手動貼上')
  }
}

function buildPayload() {
  state.items.forEach((item) => {
    updateStandardValue(item)
    syncActualValue(item)
  })
  updateFinalResult()
  return {
    header: {
      ...state.header
    },
    items: state.items.map((rawItem, idx) => {
      const item = normalizeItemForSave(rawItem)
      return ({
      seq_no: idx + 1,
      item_name: item.item_name,
      std_value: item.std_value,
      actual_value: item.actual_value,
      gauge_no: item.gauge_no,
      inspect_qty: item.inspect_qty,
      result: item.result,
      remark: item.remark,
      measurements: normalizeMeasurements(item.measurements, itemMeasureCount(item))
    })
    })
  }
}

function hydrateFromResponse(data = {}) {
  const header = data.header || {}
  const items = Array.isArray(data.items) ? data.items : []

  Object.assign(state.header, {
    ...state.header,
    ...header,
    test_date: header.test_date || state.header.test_date || todayStr(),
    completed_date: header.completed_date || state.header.completed_date || todayStr(),
    filled_date: header.filled_date || state.header.filled_date || todayStr()
  })

  state.measureCount = Number(data.measure_count || state.measureCount || 20)

  state.items = items.length
    ? items.map((it, idx) => ({
        _rowKey: nextRowKey(),
        seq_no: it.seq_no || (idx + 1),
        item_name: it.item_name || '',
        std_value: it.std_value || '',
        std_min: parseStandardValue(it.std_value).minValue,
        std_max: parseStandardValue(it.std_value).maxValue,
        std_unit: parseStandardValue(it.std_value).unit,
        actual_value: it.actual_value || '',
        min_value: parseMaxMinValue(it.actual_value).minValue,
        max_value: parseMaxMinValue(it.actual_value).maxValue,
        gauge_no: it.gauge_no || '',
        inspect_qty: it.inspect_qty ?? state.measureCount,
        result: it.result || 'PENDING',
        remark: it.remark || '',
        measurements: normalizeMeasurements(it.measurements, Number(it.inspect_qty || state.measureCount || 1)),
        pasteText: ''
      })).map(normalizeAppearanceItem)
    : [createItem(1, state.measureCount)]

  state.items.forEach((item) => {
    updateStandardValue(item)
    normalizeItemAngleValues(item)
    normalizeItemMeasurementCount(item)
    autoJudgeItem(item)
  })
  updateFinalResult()
  state.activeItemIndex = 0
}

function syncSourceStateFromHeader(header = {}) {
  sourceState.labNo = header.entrust_no || sourceState.labNo || ''
  sourceState.partNo = header.part_no || sourceState.partNo || ''
  if (header.product_name) {
    sourceState.sampleDesc = header.product_name
  }
  if (header.specification) {
    sourceState.sampleSpec = header.specification
  }
  if (header.material) {
    sourceState.materialNo = header.material
  }
  if (header.lot_no) {
    sourceState.lotNo = header.lot_no
  }
  if (header.filled_date) {
    sourceState.filledDate = header.filled_date
  }
}

function syncSourceStateFromValues(values = {}, sourceFormId = '') {
  sourceState.sourceFormId = sourceFormId || sourceState.sourceFormId || ''
  sourceState.labNo = values.lab_no || sourceState.labNo || ''
  sourceState.customerName = values.customer_name || sourceState.customerName || ''
  sourceState.filledDate = values.filled_date || sourceState.filledDate || ''
  sourceState.contactName = values.contact_name || sourceState.contactName || ''
  sourceState.contactTel = values.contact_tel || sourceState.contactTel || ''
  sourceState.contactEmail = values.contact_email || sourceState.contactEmail || ''
  sourceState.address = values.address || sourceState.address || ''
  sourceState.partNo = values.part_no || sourceState.partNo || ''
  sourceState.sampleDesc = values.sample_desc || values.part_no || sourceState.sampleDesc || ''
  sourceState.sampleSpec = values.sample_spec || sourceState.sampleSpec || ''
  sourceState.materialNo = values.material_no || sourceState.materialNo || ''
  sourceState.lotNo = values.lot_no || sourceState.lotNo || ''
  applySourceInspectQtyToItems(values)
}

function applySourceToHeader(values = {}, sourceFormId = '') {
  const report = values.report || {}
  const outsource = values.outsource || {}
  const sourceFilledDate = values.filled_date || state.header.filled_date
  const sampleQty = values.sample_qty ?? null
  const productionQty = values.production_qty ?? null
  const receiveMethod = values.receive_method === '其他'
    ? [values.receive_method, values.receive_method_other].filter(Boolean).join('：')
    : (values.receive_method || '')
  const discussion = values.discussion || ''
  const dimensionMethods = values.test_methods?.dimension || ''

  sourceState.sourceFormId = sourceFormId || ''
  sourceState.labNo = values.lab_no || ''
  sourceState.customerName = values.customer_name || ''
  sourceState.filledDate = values.filled_date || ''
  sourceState.contactName = values.contact_name || ''
  sourceState.contactTel = values.contact_tel || ''
  sourceState.contactEmail = values.contact_email || ''
  sourceState.address = values.address || ''
  sourceState.partNo = values.part_no || ''
  sourceState.sampleDesc = values.sample_desc || values.part_no || ''
  sourceState.sampleSpec = values.sample_spec || ''
  sourceState.materialNo = values.material_no || ''
  sourceState.lotNo = values.lot_no || ''

  state.header.entrust_no = values.lab_no || ''
  state.header.part_no = values.part_no || state.header.part_no
  state.header.product_name = values.sample_desc || values.part_no || state.header.product_name
  state.header.specification = values.sample_spec || state.header.specification
  state.header.plating_type = values.platingCate || state.header.plating_type
  state.header.lot_no = values.lot_no || state.header.lot_no
  state.header.lot_qty = productionQty ?? state.header.lot_qty
  state.header.material = values.material_no || state.header.material
  state.header.manufacturer = values.platingFac || outsource.vendor_info || state.header.manufacturer
  state.header.dimension_standard = report.rule_spec || dimensionMethods || state.header.dimension_standard
  state.header.drawing_no = report.rule_drawing || state.header.drawing_no
  state.header.regulation = report.rule_type === '法規標準'
    ? (report.rule_spec || state.header.regulation)
    : state.header.regulation
  state.header.test_date = sourceFilledDate || state.header.test_date
  state.header.completed_date = sourceFilledDate || state.header.completed_date
  state.header.filled_date = sourceFilledDate
  state.header.remarks = [
    `來源委託單 ${values.lab_no || ''}`,
    values.customer_name ? `客戶 ${values.customer_name}` : '',
    values.contact_name ? `聯絡人 ${values.contact_name}` : '',
    values.contact_tel ? `電話 ${values.contact_tel}` : '',
    values.contact_email ? `E-mail ${values.contact_email}` : '',
    values.material_no ? `材質編號 ${values.material_no}` : '',
    values.platingCate ? `電鍍別 ${values.platingCate}` : '',
    values.platingFac ? `廠商 ${values.platingFac}` : '',
    receiveMethod ? `收件方式 ${receiveMethod}` : '',
    sampleQty != null ? `送驗數量 ${formatSourceQuantity(sampleQty, values.sample_unit)}` : '',
    productionQty != null ? `產品產量 ${formatSourceQuantity(productionQty, values.production_unit)}` : '',
    values.tests?.dimension?.length ? `尺寸項目 ${values.tests.dimension.join('、')}` : '',
    dimensionMethods ? `尺寸方法 ${dimensionMethods}` : '',
    values.hardness_inspection_methods?.core ? `心部硬度檢測方式 ${values.hardness_inspection_methods.core}` : '',
    values.hardness_inspection_methods?.surface ? `表面硬度檢測方式 ${values.hardness_inspection_methods.surface}` : '',
    values.coating_thickness_spec?.min || values.coating_thickness_spec?.max
      ? `膜厚標準 ${values.coating_thickness_spec.min || '-'} - ${values.coating_thickness_spec.max || '-'} ${values.coating_thickness_spec.unit || ''}`.trim()
      : '',
    values.salt_spray_spec?.white_hours ? `鹽霧無白鏽 ${values.salt_spray_spec.white_hours} H` : '',
    values.salt_spray_spec?.red_hours ? `鹽霧無紅鏽 ${values.salt_spray_spec.red_hours} H` : '',
    discussion ? `討論事項 ${discussion}` : '',
    outsource.has && outsource.has !== '無' ? `委外資訊 ${[outsource.items, outsource.vendor_info].filter(Boolean).join(' / ')}` : '',
    values.other_requirements ? `其他需求 ${values.other_requirements}` : '',
  ].filter(Boolean).join('\n')

  if (sampleQty != null) {
    state.header.sampling_plan = `送驗數量 ${formatSourceQuantity(sampleQty, values.sample_unit)}`
  }
  applySourceInspectQtyToItems(values)
}

async function fetchSourceFormDetail(formId) {
  const resp = await fetch(api(`lab/instances/${formId}`), {
    credentials: 'include'
  })
  const json = await readJsonOrThrow(resp, '讀取委託單失敗')
  if (!json.form) throw new Error('讀取委託單失敗')
  return json.form
}

async function findSavedFormByEntrustNo(entrustNo) {
  const no = String(entrustNo || '').trim()
  if (!no) return null
  const qs = new URLSearchParams({ entrust_no: no })
  const resp = await apiFetch(qetApi(`forms/by-entrust?${qs.toString()}`))
  const json = await readJsonOrThrow(resp, '查詢已存尺寸表失敗')
  if (!json?.form_id || !json?.data) {
    return null
  }
  return json
}

async function selectSourceForm(formId) {
  try {
    const form = await fetchSourceFormDetail(formId)
    const entrustNo = form?.values?.lab_no || ''
    const saved = await findSavedFormByEntrustNo(entrustNo)
    if (!saved?.form_id) {
      ElMessage.warning('此委託單尚未設定尺寸原始紀錄表，請先由主管完成設定')
      return
    }
    state.formId = saved.form_id
    hydrateFromResponse(saved.data || {})
    syncSourceStateFromHeader((saved.data || {}).header || {})
    syncSourceStateFromValues(form.values || {}, formId)
    sourceState.dialogVisible = false
    router.replace({
      name: 'lab_qet',
      query: { form_id: saved.form_id, source_form_id: formId }
    })
    ElMessage.success('已載入既有尺寸表資料')
  } catch (e) {
    ElMessage.error(e.message || '帶入委託單失敗')
  }
}

async function searchSourceForms() {
  sourceState.loading = true
  try {
    const q = new URLSearchParams()
    if (sourceState.searchLabNo) q.set('lab_no', sourceState.searchLabNo)
    if (sourceState.searchCustomer) q.set('customer', sourceState.searchCustomer)
    if (sourceState.searchDate) q.set('filled_date', sourceState.searchDate)

    const resp = await fetch(api(`lab/instances/search?${q.toString()}`), {
      credentials: 'include'
    })
    const json = await readJsonOrThrow(resp, '搜尋委託單失敗')
    const rows = Array.isArray(json.rows) ? json.rows : []
    const checkedRows = await Promise.all(rows.map(async (row) => {
      const saved = await findSavedFormByEntrustNo(row.lab_no)
      return saved?.form_id ? { ...row, qet_form_id: saved.form_id } : null
    }))
    sourceState.results = checkedRows.filter(Boolean)
    if (!sourceState.results.length) {
      ElMessage.info('查無已設定尺寸原始紀錄表的委託單')
    }
  } catch (e) {
    ElMessage.error(e.message || '搜尋失敗')
  } finally {
    sourceState.loading = false
  }
}

function openSourceDialog() {
  sourceState.dialogVisible = true
  searchSourceForms()
}

function newForm(force = false) {
  if (!force && !sourceState.labNo) {
    ElMessage.warning('請先選擇委託單，取得 lab_no 後才能新增')
    return
  }

  const keepSource = {
    sourceFormId: sourceState.sourceFormId,
    labNo: sourceState.labNo,
    customerName: sourceState.customerName,
    filledDate: sourceState.filledDate,
    contactName: sourceState.contactName,
    contactTel: sourceState.contactTel,
    contactEmail: sourceState.contactEmail,
    address: sourceState.address,
    partNo: sourceState.partNo,
    sampleDesc: sourceState.sampleDesc,
    sampleSpec: sourceState.sampleSpec,
    materialNo: sourceState.materialNo,
    lotNo: sourceState.lotNo
  }
  state.formId = ''
  state.measureCount = 20
  state.activeItemIndex = 0
  state.pasteText = ''
  Object.assign(state.header, {
    form_no: '',
    entrust_no: '',
    part_no: '',
    product_name: '',
    specification: '',
    plating_type: '',
    dimension_standard: '',
    drawing_no: '',
    regulation: '',
    lot_no: '',
    lot_qty: null,
    material: '',
    manufacturer: '',
    size_unit: 'mm',
    env_temp: null,
    env_humidity: null,
    sampling_plan: '無',
    test_date: todayStr(),
    completed_date: todayStr(),
    filled_date: todayStr(),
    tester: currentUserName(),
    reviewer: '',
    final_result: 'PENDING',
    remarks: ''
  })
  state.items = [createItem(1, 20)]
  Object.assign(sourceState, keepSource)
  if (keepSource.labNo) {
    state.header.entrust_no = keepSource.labNo
    state.header.part_no = keepSource.partNo || state.header.part_no
    state.header.product_name = keepSource.sampleDesc || state.header.product_name
    state.header.specification = keepSource.sampleSpec || state.header.specification
    state.header.material = keepSource.materialNo || state.header.material
    state.header.lot_no = keepSource.lotNo || state.header.lot_no
    state.header.remarks = keepSource.customerName
      ? `來源委託單 ${keepSource.labNo}\n客戶 ${keepSource.customerName}`
      : ''
  }
  router.replace({
    name: 'lab_qet',
    query: keepSource.sourceFormId ? { source_form_id: keepSource.sourceFormId } : {}
  })
  ElMessage.success('已建立新表單')
}

async function saveForm() {
  state.saving = true
  try {
    if (!state.formId && !sourceState.labNo) {
      throw new Error('請先選擇來源委託單，取得 lab_no 後才能新增')
    }
    const payload = buildPayload()
    const isEdit = !!state.formId
    const url = isEdit
      ? qetApi(`forms/${state.formId}`)
      : qetApi('forms')
    const method = isEdit ? 'PUT' : 'POST'

    const resp = await apiFetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    const json = await readJsonOrThrow(resp, '儲存失敗')

    state.formId = json.form_id || state.formId
    if (json.form_no) state.header.form_no = json.form_no
    ElMessage.success('儲存成功')
    try {
      await ElMessageBox.confirm('是否繼續輸入機械性質紀錄？', '儲存成功', {
        confirmButtonText: '前往機械性質',
        cancelButtonText: '留在尺寸表',
        type: 'success'
      })
      await goToMechanicalReport()
    } catch {
      // 使用者選擇留在目前頁面。
    }
  } catch (e) {
    ElMessage.error(e.message || '儲存失敗')
  } finally {
    state.saving = false
  }
}

async function resolveSourceFormIdByLabNo() {
  const labNo = String(state.header.entrust_no || sourceState.labNo || '').trim()
  if (sourceState.sourceFormId) return sourceState.sourceFormId
  if (!labNo) return ''
  const resp = await fetch(api(`lab/instances/search?lab_no=${encodeURIComponent(labNo)}`), {
    credentials: 'include'
  })
  const json = await readJsonOrThrow(resp, '查詢來源委託單失敗')
  const matched = Array.isArray(json.rows)
    ? json.rows.find((row) => String(row.lab_no || '').trim() === labNo)
    : null
  return matched?.form_id || ''
}

async function goToMechanicalReport() {
  try {
    const sourceFormId = await resolveSourceFormIdByLabNo()
    if (!sourceFormId) {
      ElMessage.warning('找不到來源委託單，請先由「選擇委託單」帶入資料')
      return
    }
    router.push({
      name: 'lab_mech',
      query: { source_form_id: sourceFormId }
    })
  } catch (e) {
    ElMessage.error(e.message || '無法前往機械性質紀錄')
  }
}

async function deleteForm() {
  if (!state.formId) {
    ElMessage.warning('請先儲存表單')
    return
  }
  if (!window.confirm(`確定要刪除記錄表 ${state.header.form_no || state.formId}？`)) return
  state.saving = true
  try {
    const resp = await apiFetch(qetApi(`forms/${encodeURIComponent(state.formId)}`), {
      method: 'DELETE',
    })
    const json = await resp.json().catch(() => ({}))
    if (!resp.ok || json?.ok === false) throw new Error(json?.msg || `HTTP ${resp.status}`)
    ElMessage.success('刪除成功')
    router.push({ name: 'lab_qet_manage' })
  } catch (e) {
    ElMessage.error(e.message || '刪除失敗')
  } finally {
    state.saving = false
  }
}

async function loadForm(formId) {
  state.loading = true
  try {
    const resp = await apiFetch(qetApi(`forms/${formId}`))
    const json = await readJsonOrThrow(resp, '讀取失敗')
    state.formId = json.form_id || formId
    const payload = json.data || json
    hydrateFromResponse(payload)
    syncSourceStateFromHeader(payload.header || {})
    if (payload.source_values) {
      syncSourceStateFromValues(payload.source_values, payload.source_form_id || '')
    }
  } catch (e) {
    ElMessage.error(e.message || '讀取失敗')
  } finally {
    state.loading = false
  }
}

async function exportDocx() {
  if (!state.formId) {
    ElMessage.warning('請先儲存表單')
    return
  }
  state.exporting = true
  try {
    const resp = await apiFetch(qetApi(`forms/${state.formId}/export-docx`), {
      method: 'POST',
    })
    if (!resp.ok) {
      throw new Error('匯出失敗')
    }
    const blob = await resp.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${state.header.form_no || 'QET-15-01'}.docx`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error(e.message || '匯出失敗')
  } finally {
    state.exporting = false
  }
}

async function copyForm() {
  if (!state.formId) {
    ElMessage.warning('請先儲存原表單')
    return
  }
  try {
    const { value: entrustNo } = await ElMessageBox.prompt(
      '請輸入要複製到的委託單編號',
      '複製表單',
      {
        confirmButtonText: '複製',
        cancelButtonText: '取消',
        inputPlaceholder: '委託單編號',
        inputValue: sourceState.labNo || '',
        inputValidator: (value) => {
          if (!String(value || '').trim()) return '請輸入委託單編號'
          return true
        }
      }
    )

    const targetEntrustNo = String(entrustNo || '').trim()

    const searchResp = await fetch(api(`lab/instances/search?lab_no=${encodeURIComponent(targetEntrustNo)}`), {
      credentials: 'include'
    })
    const searchJson = await readJsonOrThrow(searchResp, '查詢委託單失敗')
    const matched = Array.isArray(searchJson.rows)
      ? searchJson.rows.find((row) => String(row.lab_no || '').trim() === targetEntrustNo)
      : null

    if (!matched) {
      throw new Error('找不到該委託單編號，不能複製')
    }

    await ElMessageBox.confirm(`是否複製目前表單到委託單 ${targetEntrustNo}？`, '提示', {
      type: 'warning'
    })

    const resp = await apiFetch(qetApi(`forms/${state.formId}/copy`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ entrust_no: targetEntrustNo })
    })
    const json = await readJsonOrThrow(resp, '複製失敗')

    state.formId = json.form_id || ''
    if (json.data) {
      hydrateFromResponse(json.data)
    } else if (json.form_id) {
      await loadForm(json.form_id)
    }
    if (json.form_no) state.header.form_no = json.form_no
    sourceState.labNo = targetEntrustNo
    state.header.entrust_no = targetEntrustNo

    ElMessage.success('複製成功')
  } catch (e) {
    if (e === 'cancel') return
    ElMessage.error(e.message || '複製失敗')
  }
}

onMounted(async () => {
  const id = route.query.form_id || route.params.id
  if (id) {
    await loadForm(id)
    return
  }

  const sourceFormId = route.query.source_form_id
  if (sourceFormId) {
    await selectSourceForm(sourceFormId)
  }
})
</script>

<style scoped>
.qet-page {
  padding-bottom: 96px;
}

.qet-footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 30;
  background: rgba(255, 255, 255, 0.96);
  border-top: 1px solid #e5e7eb;
  box-shadow: 0 -8px 24px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(6px);
}

.qet-footer-inner {
  max-width: 1600px;
  margin: 0 auto;
  padding: 10px 20px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.source-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  align-items: stretch;
}

.source-card {
  min-height: 74px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  overflow-wrap: anywhere;
}

.source-card-wide {
  grid-column: span 2;
}

.standard-helper {
  align-items: stretch;
}

.standard-unit-select {
  width: 128px;
  flex: 0 0 128px;
}

:deep(.standard-unit-select .el-select__wrapper) {
  min-height: 32px;
}

@media (max-width: 1024px) {
  .source-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .source-grid {
    grid-template-columns: 1fr;
  }

  .source-card-wide {
    grid-column: span 1;
  }
}

:deep(.el-form-item) {
  margin-bottom: 10px;
}
:deep(.el-card) {
  border-radius: 1rem;
}
</style>
