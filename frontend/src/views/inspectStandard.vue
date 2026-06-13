<template>
  <div class="qet-page p-3 sm:p-5 max-w-[1280px] mx-auto">
    <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between mb-4">
      <div>
        <div class="text-lg font-semibold">設定尺寸原始紀錄表</div>
        <div class="text-sm text-gray-500 mt-1">僅設定測試項目、標準值、量具與檢驗數</div>
      </div>

      <div class="flex flex-wrap gap-2">
        <el-button @click="openSourceDialog" plain>選擇委託單</el-button>
        <el-button plain @click="router.push({ name: 'lab_qet_manage' })">查修</el-button>
        <el-button @click="newForm" plain>新增設定</el-button>
        <el-button :loading="state.saving" type="primary" @click="saveForm">儲存設定</el-button>
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

    <el-card shadow="never" class="mb-4 rounded-2xl">
      <template #header>
        <div class="font-semibold">基本資料</div>
      </template>

      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        <el-form-item label="記錄表標號">
          <el-input v-model="state.header.form_no" placeholder="儲存後自動產生 / 或由後端帶回" readonly />
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
          <el-date-picker v-model="state.header.test_date" type="date" value-format="YYYY-MM-DD" format="YYYY-MM-DD" class="w-full" />
        </el-form-item>

        <el-form-item label="完成日期">
          <el-date-picker v-model="state.header.completed_date" type="date" value-format="YYYY-MM-DD" format="YYYY-MM-DD" class="w-full" />
        </el-form-item>

        <el-form-item label="填表日期">
          <el-date-picker v-model="state.header.filled_date" type="date" value-format="YYYY-MM-DD" format="YYYY-MM-DD" class="w-full" />
        </el-form-item>

        <el-form-item label="測試者">
          <el-input v-model="state.header.tester" readonly />
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

    <el-card shadow="never" class="mb-4 rounded-2xl">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div class="flex flex-wrap items-center gap-2">
          <div class="font-semibold">測試項目</div>
          <el-tag type="info">共 {{ state.items.length }} 項</el-tag>
        </div>

        <div class="flex flex-wrap gap-2">
          <el-button type="primary" @click="addItem()">新增測試項目</el-button>
          <el-button plain @click="addPresetItem('appearance')">Appearance</el-button>
          <el-button plain @click="addPresetItem('gauge')">Gauge</el-button>
          <el-button @click="bulkFillItemNames" plain>自動填 A/B/C...</el-button>
        </div>
      </div>
    </el-card>

    <div class="grid grid-cols-1 xl:grid-cols-[360px_minmax(0,1fr)] gap-4">
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
                <div class="font-semibold truncate">{{ item.item_name || `測試項目 ${idx + 1}` }}</div>
                <div class="text-xs text-gray-500 mt-1 truncate">
                  {{ isAppearanceItem(item) ? '依據標準' : '標準值' }}：{{ item.std_value || '-' }}
                </div>
                <div class="text-xs text-gray-500 truncate">量具：{{ item.gauge_no || '-' }}</div>
              </div>
              <span class="text-[11px] text-gray-400 shrink-0">#{{ idx + 1 }}</span>
            </div>

            <div class="mt-3 grid grid-cols-2 gap-2">
              <el-button size="small" @click.stop="duplicateItem(idx)">複製</el-button>
              <el-button size="small" type="danger" plain @click.stop="removeItem(idx)">刪除</el-button>
            </div>
          </div>

          <div v-if="!state.items.length" class="text-sm text-gray-500 border border-dashed rounded-2xl p-6 text-center">
            尚無測試項目，請先新增
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="rounded-2xl">
        <template #header>
          <div class="font-semibold">
            編輯設定
            <span v-if="currentItem" class="text-gray-500 font-normal ml-2">
              {{ currentItem.item_name || `第 ${state.activeItemIndex + 1} 項` }}
            </span>
          </div>
        </template>

        <div v-if="currentItem" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          <el-form-item label="項次">
            <el-input-number v-model="currentItem.seq_no" :min="1" class="w-full" />
          </el-form-item>

          <el-form-item label="測試項目">
            <div class="flex gap-2 w-full">
              <el-input v-model="currentItem.item_name" placeholder="例如 A / B / 外徑 / 厚度" />
              <el-button type="primary" plain @click="addItem()">+</el-button>
            </div>
          </el-form-item>

          <el-form-item :label="isAppearanceItem(currentItem) ? '依據標準' : '標準值'">
            <el-select
              v-if="isAppearanceItem(currentItem)"
              v-model="currentItem.std_value"
              class="w-full"
              @change="normalizeAppearanceItem(currentItem)"
            >
              <el-option :label="APPEARANCE_STANDARD" :value="APPEARANCE_STANDARD" />
            </el-select>
            <el-input v-else v-model="currentItem.std_value" placeholder="由下方標準值輔助帶入" readonly />
          </el-form-item>

          <el-form-item v-if="!isAppearanceItem(currentItem)" label="標準值輔助" class="xl:col-span-2">
            <div class="flex gap-2 w-full standard-helper">
              <el-input
                v-if="!isDiscreteStandardUnit(currentItem.std_unit) || isRefStandardUnit(currentItem.std_unit)"
                v-model="currentItem.std_min"
                :placeholder="isRefStandardUnit(currentItem.std_unit) ? 'REF 設定值' : '最小值'"
                inputmode="decimal"
                @input="handleStandardMinInput(currentItem)"
                @blur="normalizeStandardAngle(currentItem)"
              />
              <el-input
                v-if="!isDiscreteStandardUnit(currentItem.std_unit)"
                v-model="currentItem.std_max"
                placeholder="最大值"
                inputmode="decimal"
                @input="updateStandardValue(currentItem)"
                @blur="normalizeStandardAngle(currentItem)"
              />
              <el-select
                v-model="currentItem.std_unit"
                class="standard-unit-select"
                @change="updateStandardValue(currentItem)"
              >
                <el-option label="度數" value="°" />
                <el-option label="mm" value="mm" />
                <el-option label="inch" value="inch" />
                <el-option label="OK/NG" value="OK/NG" />
                <el-option label="Go/NoGo" value="Go/NoGo" />
                <el-option label="REF" value="REF" />
              </el-select>
            </div>
          </el-form-item>

          <el-form-item label="量具／編號">
            <div class="flex gap-2 w-full">
              <el-select
                v-model="currentItem.gauge_no"
                filterable
                allow-create
                clearable
                default-first-option
                placeholder="選擇或輸入量具／編號"
                class="flex-1"
              >
                <el-option
                  v-for="o in state.equipmentOptions"
                  :key="`equipment-${o.value}`"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button plain title="開啟設備 Excel" @click="openEquipmentExcel">Excel</el-button>
            </div>
          </el-form-item>

          <el-form-item label="檢驗數">
            <el-input-number v-model="currentItem.inspect_qty" :min="0" class="w-full" />
          </el-form-item>
        </div>

        <div v-else class="text-sm text-gray-500 p-8 text-center border border-dashed rounded-2xl">
          請先新增測試項目
        </div>
      </el-card>
    </div>

    <div class="qet-footer">
      <div class="qet-footer-inner">
        <el-button :loading="state.saving" type="primary" @click="saveForm">儲存設定</el-button>
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
import { ElMessage } from 'element-plus'
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

function ensureReviewerDefault() {
  if (!String(state.header.reviewer || '').trim()) {
    state.header.reviewer = currentUserName()
  }
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
    measurements: Array(measureCount).fill('')
  }
}

const state = reactive({
  formId: '',
  saving: false,
  loading: false,
  equipmentOptions: [],
  measureCount: 20,
  activeItemIndex: 0,
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
    tester: '',
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
  if (!resp.ok || !json?.ok) throw new Error(json?.msg || fallbackMessage)
  return json
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
  return parsePositiveInt(item?.inspect_qty) || state.measureCount || 1
}

function addItem() {
  state.items.push(createItem(state.items.length + 1, state.measureCount))
  state.activeItemIndex = state.items.length - 1
}

function addPresetItem(kind) {
  const item = createItem(state.items.length + 1, state.measureCount)
  if (kind === 'appearance') {
    item.item_name = 'Appearance'
    item.std_value = APPEARANCE_STANDARD
    item.std_unit = 'OK/NG'
    item.gauge_no = '目視'
    item.remark = `依據標準 - ${APPEARANCE_STANDARD}`
    normalizeAppearanceItem(item)
  } else if (kind === 'gauge') {
    item.item_name = 'Gauge'
    item.std_value = 'Go/NoGo'
    item.std_unit = 'Go/NoGo'
    item.gauge_no = '環規 / 牙規'
    item.remark = '測試方式：環規、牙規或其他'
  }
  state.items.push(item)
  state.activeItemIndex = state.items.length - 1
}

function removeItem(idx) {
  if (state.items.length <= 1) {
    ElMessage.warning('至少保留一個測試項目')
    return
  }
  state.items.splice(idx, 1)
  state.items.forEach((it, i) => { it.seq_no = i + 1 })
  if (state.activeItemIndex >= state.items.length) state.activeItemIndex = state.items.length - 1
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

function bulkFillItemNames() {
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  state.items.forEach((item, i) => {
    if (!item.item_name) item.item_name = letters[i] || `Item${i + 1}`
  })
}

function isAngleUnit(unit) {
  return /^(°|度|度數|angle)$/i.test(String(unit || '').trim())
}

function isDiscreteStandardUnit(unit) {
  return /^(OK\/NG|Go\/NoGo|REF)$/i.test(String(unit || '').trim())
}

function isRefStandardUnit(unit) {
  return /^REF$/i.test(String(unit || '').trim())
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

function formatStandardValueText(value, unit) {
  const text = String(value ?? '').trim()
  if (!text) return ''
  if (isAngleUnit(unit)) return formatAngleInput(text, { force: true })
  return [text, unit].filter(Boolean).join(' ')
}

function normalizeStandardAngle(item) {
  if (!item || !isAngleUnit(item.std_unit)) return
  item.std_min = formatAngleInput(item.std_min, { force: true })
  item.std_max = formatAngleInput(item.std_max, { force: true })
  updateStandardValue(item)
}

function updateStandardValue(item) {
  if (!item) return
  if (isAppearanceItem(item)) {
    normalizeAppearanceItem(item)
    return
  }
  const unit = String(item.std_unit || '').trim()
  const min = String(item.std_min ?? '').trim()
  const max = String(item.std_max ?? '').trim()
  if (unit === 'REF') {
    item.std_value = ['REF', min].filter(Boolean).join(' ')
    item.std_max = ''
    return
  }
  if (['OK/NG', 'Go/NoGo'].includes(unit)) {
    item.std_value = unit
    item.std_min = ''
    item.std_max = ''
    return
  }
  if (!min && !max) {
    item.std_value = ''
  } else if (min && max) {
    item.std_value = min === max ? formatStandardValueText(min, unit) : formatStandardRangeText(min, max, unit)
  } else if (min) {
    item.std_value = `${formatStandardValueText(min, unit)} MIN`
  } else {
    item.std_value = `${formatStandardValueText(max, unit)} MAX`
  }
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
  if (min && !max && !isRefStandardUnit(item.std_unit)) item.std_max = item.std_min
  updateStandardValue(item)
}

function parseStandardValue(raw) {
  const text = String(raw || '').trim()
  if (!text) return { minValue: '', maxValue: '', unit: '°' }
  const unitMatch = text.match(/(Go\/NoGo|OK\/NG|REF|inch|mm|°)/i)
  const unit = unitMatch ? unitMatch[1] : '°'
  if (isAngleUnit(unit)) {
    const body = text.replace(/\b(MIN|MAX)\b/gi, '').trim()
    const parts = body.split(/\s+(?:-|－|–|—|~|～|至)\s+|(?:－|–|—|~|～|至)/).map(x => x.trim()).filter(Boolean)
    const angleParts = parts.map(x => formatAngleInput(x, { force: true })).filter(Boolean)
    if (/\bMAX\b/i.test(text)) return { minValue: '', maxValue: angleParts[0] || '', unit }
    if (/\bMIN\b/i.test(text)) return { minValue: angleParts[0] || '', maxValue: '', unit }
    return { minValue: angleParts[0] || '', maxValue: angleParts[1] || '', unit }
  }
  const nums = text.match(/-?\d+(?:\.\d+)?/g) || []
  return { minValue: nums[0] || '', maxValue: nums[1] || '', unit }
}

function parseMaxMinValue(raw) {
  const text = String(raw || '').trim()
  if (!text || !/[\/／－–—~～至]/.test(text)) return { maxValue: '', minValue: '' }
  const parts = text.replace(/[－–—~～至]/g, '/').split('/').map(x => x.trim()).filter(Boolean)
  return parts.length >= 2 ? { minValue: parts[0], maxValue: parts[1] } : { maxValue: text, minValue: '' }
}

function buildPayload() {
  return {
    header: { ...state.header },
    items: state.items.map((rawItem, idx) => {
      const item = normalizeAppearanceItem({ ...rawItem })
      updateStandardValue(item)
      const count = itemMeasureCount(item)
      return ({
      seq_no: idx + 1,
      item_name: item.item_name,
      std_value: item.std_value,
      actual_value: item.actual_value,
      gauge_no: item.gauge_no,
      inspect_qty: count,
      result: item.result,
      remark: item.remark,
      measurements: normalizeMeasurements(item.measurements, count)
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
        measurements: normalizeMeasurements(it.measurements, Number(it.inspect_qty || state.measureCount || 1))
      })).map(normalizeAppearanceItem)
    : [createItem(1, state.measureCount)]
  state.items.forEach((item) => {
    updateStandardValue(item)
    item.measurements = normalizeMeasurements(item.measurements, itemMeasureCount(item))
  })
  state.activeItemIndex = 0
  ensureReviewerDefault()
}

function syncSourceStateFromHeader(header = {}) {
  sourceState.labNo = header.entrust_no || sourceState.labNo || ''
  sourceState.partNo = header.part_no || sourceState.partNo || ''
  if (header.product_name) sourceState.sampleDesc = header.product_name
  if (header.specification) sourceState.sampleSpec = header.specification
  if (header.material) sourceState.materialNo = header.material
  if (header.lot_no) sourceState.lotNo = header.lot_no
  if (header.filled_date) sourceState.filledDate = header.filled_date
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
  const qty = sourceInspectQty(values)
  if (qty) {
    state.measureCount = qty
    state.items.forEach((item) => {
      if (!parsePositiveInt(item.inspect_qty) || Number(item.inspect_qty) === 20) {
        item.inspect_qty = qty
      }
      item.measurements = normalizeMeasurements(item.measurements, itemMeasureCount(item))
    })
  }
  ensureReviewerDefault()
}

async function fetchSourceFormDetail(formId) {
  const resp = await fetch(api(`lab/instances/${formId}`), { credentials: 'include' })
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
  return json?.form_id ? json : null
}

async function selectSourceForm(formId) {
  try {
    const form = await fetchSourceFormDetail(formId)
    const entrustNo = form?.values?.lab_no || ''
    const saved = await findSavedFormByEntrustNo(entrustNo)
    if (saved?.form_id) {
      state.formId = saved.form_id
      hydrateFromResponse(saved.data || {})
      syncSourceStateFromHeader((saved.data || {}).header || {})
    } else {
      newForm(true)
    }
    applySourceToHeader(form.values || {}, formId)
    sourceState.dialogVisible = false
    router.replace({
      name: 'lab_qet_standard',
      query: saved?.form_id
        ? { form_id: saved.form_id, source_form_id: formId }
        : { ...route.query, source_form_id: formId }
    })
    ElMessage.success(saved?.form_id ? '已載入既有尺寸表設定' : '已帶入委託單資料')
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
    const resp = await fetch(api(`lab/instances/search?${q.toString()}`), { credentials: 'include' })
    const json = await readJsonOrThrow(resp, '搜尋委託單失敗')
    sourceState.results = json.rows || []
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
  Object.assign(state.header, {
    form_no: '',
    entrust_no: keepSource.labNo || '',
    part_no: keepSource.partNo || '',
    product_name: keepSource.sampleDesc || '',
    specification: keepSource.sampleSpec || '',
    plating_type: '',
    dimension_standard: '',
    drawing_no: '',
    regulation: '',
    lot_no: keepSource.lotNo || '',
    lot_qty: null,
    material: keepSource.materialNo || '',
    manufacturer: '',
    size_unit: 'mm',
    env_temp: null,
    env_humidity: null,
    sampling_plan: '無',
    test_date: keepSource.filledDate || todayStr(),
    completed_date: keepSource.filledDate || todayStr(),
    filled_date: keepSource.filledDate || todayStr(),
    tester: '',
    reviewer: currentUserName(),
    final_result: 'PENDING',
    remarks: ''
  })
  Object.assign(sourceState, keepSource)
  state.items = [createItem(1, 20)]
  ElMessage.success('已建立新設定')
}

async function saveForm() {
  state.saving = true
  try {
    if (!state.formId && !sourceState.labNo) {
      throw new Error('請先選擇來源委託單，取得 lab_no 後才能新增')
    }
    ensureReviewerDefault()
    const isEdit = !!state.formId
    const resp = await apiFetch(isEdit ? qetApi(`forms/${state.formId}`) : qetApi('forms'), {
      method: isEdit ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildPayload())
    })
    const json = await readJsonOrThrow(resp, '儲存失敗')
    state.formId = json.form_id || state.formId
    if (json.form_no) state.header.form_no = json.form_no
    ElMessage.success('設定已儲存')
  } catch (e) {
    ElMessage.error(e.message || '儲存失敗')
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
      applySourceToHeader(payload.source_values, payload.source_form_id || '')
    }
  } catch (e) {
    ElMessage.error(e.message || '讀取失敗')
  } finally {
    state.loading = false
  }
}

onMounted(async () => {
  await loadEquipmentOptions()
  const id = route.query.form_id || route.params.id
  if (id) {
    await loadForm(id)
    return
  }
  const sourceFormId = route.query.source_form_id
  if (sourceFormId) await selectSourceForm(sourceFormId)
  else ensureReviewerDefault()
})

async function loadEquipmentOptions() {
  try {
    const resp = await fetch(api('lab/equipment/options'), { credentials: 'include' })
    const json = await readJsonOrThrow(resp, '量具/設備清單載入失敗')
    state.equipmentOptions = Array.isArray(json.data) ? json.data : []
  } catch (e) {
    state.equipmentOptions = []
    console.warn(e)
  }
}

function openEquipmentExcel() {
  window.open(api('lab/equipment/source-file'), '_blank', 'noopener')
}
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
  max-width: 1280px;
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
</style>
