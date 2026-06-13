<!-- frontend/src/views/InvGrnView.vue -->
<template>
  <main class="mx-auto w-[92vw] max-w-[1400px] pt-4 pb-6">
    <div class="inv-wrap">
      <!-- ✅ title bar + actions(靠右) -->
      <div class="inv-titlebar">
        <h4 class="inv-title">
          <span class="inv-title-accent">進</span>貨單維護
        </h4>

        <!-- ✅ 新增/搜尋/重新載入靠右 -->
        <div class="inv-actions">
          <el-tooltip content="搜尋" placement="bottom">
            <button
              class="icon-btn"
              :class="{ active: searchOpen }"
              type="button"
              title="搜尋"
              @click="searchOpen = !searchOpen"
            >
              <img src="@/assets/icons/search.png" alt="搜尋" />
            </button>
          </el-tooltip>

          <el-tooltip content="重新載入" placement="bottom">
            <button
              class="icon-btn"
              type="button"
              title="重新載入"
              :disabled="loading"
              @click="reload"
            >
              <img v-if="!loading" src="@/assets/icons/reload.png" alt="重新載入" />
              <span v-else class="loading-dot"></span>
            </button>
          </el-tooltip>

          <el-button type="primary" size="small" @click="openPoPicker" style="margin-top: 4px;">
            新增進貨單
          </el-button>
        </div>
      </div>

      <!-- ✅ search bar -->
      <div v-show="searchOpen" class="inv-search">
        <el-select v-model="status" size="small" class="inv-search__status" placeholder="狀態">
          <el-option label="狀態" value="" />
          <el-option label="已入庫" value="POSTED" />
          <el-option label="未入庫" value="OPEN" />
        </el-select>

        <el-input
          v-model="kw"
          size="small"
          class="inv-search__kw"
          placeholder="採購單號 / 產品編號 / 進貨單號 / 廠商"
          clearable
          @keyup.enter="doSearch"
        />

        <el-button size="small" type="primary" :loading="loading" @click="doSearch">Go</el-button>
        <el-button size="small" @click="clearSearch" plain>清除</el-button>
      </div>

      <!-- ✅ list area -->
      <div class="inv-list">
        <!-- ======== Mobile: Cards ======== -->
        <div v-if="isMobile" class="m-cards">
          <div v-for="row in items" :key="row.grn_line_id" class="m-card">
            <div class="m-card__head">
              <div class="m-card__line1">
                <span class="k">進貨單號</span> <span class="mono">{{ row.grn_no }}</span>
              </div>
              <div class="m-card__line1">
                <span class="k">廠商</span> <span class="ellipsis">{{ row.factory }}</span>
              </div>
              <div class="m-card__line2">
                {{ fmtDateYMD(row.grn_date) }} ｜ <span class="k">採購單</span>
                <span class="mono">{{ row.po_no }}</span>
              </div>
            </div>

            <div class="m-card__grid">
              <div class="cell">
                <div class="k">產品編號</div>
                <div class="v mono">{{ row.item_no }}</div>
              </div>

              <div class="cell cell--desc">
                <div class="k">產品敘述</div>
                <div class="v desc" v-html="row.description || '-'"></div>
              </div>

              <div class="cell">
                <div class="k">採購數量</div>
                <div class="v num">{{ fmtInt(row.po_qty) }}</div>
              </div>

              <div class="cell">
                <div class="k">進貨數量</div>
                <div class="v num">{{ fmtInt(row.recv_qty) }}</div>
              </div>

              <div class="cell">
                <div class="k">幣別</div>
                <div class="v">{{ row.currency || '-' }}</div>
              </div>

              <div class="cell">
                <div class="k">單價</div>
                <div class="v num">{{ fmtMoney2(row.unit_price) }}</div>
              </div>

              <div class="cell">
                <div class="k">狀態</div>
                <div class="v">
                  <span class="pill" :data-s="row.status">{{ grnStatusLabel(row.status) }}</span>
                </div>
              </div>

              <div class="cell">
                <div class="k">入庫</div>
                <div class="v">
                  <el-button size="small" type="success" @click="openInlineStock(row)">入庫</el-button>
                </div>
              </div>
            </div>

            <!-- ✅ inline 入庫（手機） -->
            <div v-if="stockEdit.openId === row.grn_line_id" class="inline-edit">
              <el-date-picker
                v-model="stockEdit.date"
                type="date"
                value-format="YYYY-MM-DD"
                size="small"
                class="w-full"
              />

              <!-- ✅ 原生 input：整數 -->
              <input
                v-model.number="stockEdit.qty"
                type="number"
                inputmode="numeric"
                min="0"
                step="1"
                class="w-full h-9 px-3 rounded-lg border border-slate-200 bg-white text-right tabular-nums
                       focus:outline-none focus:ring-1 focus:ring-blue-400"
              />

              <el-input v-model="stockEdit.memo" size="small" placeholder="備註" class="w-full" />
              <el-button
                type="primary"
                size="small"
                class="w-full"
                :loading="stockEdit.saving"
                @click="confirmInlineStock(row)"
              >
                確認
              </el-button>
            </div>
          </div>
        </div>

        <!-- ======== Desktop: Table ======== -->
        <table v-else class="inv-table">
          <thead>
            <tr>
              <th class="c-no">序號</th>
              <th>採購單號</th>
              <th>產品編號</th>
              <th class="c-desc">產品敘述</th>
              <th class="c-num">採購數量</th>
              <th class="c-num">進貨數量</th>
              <th class="c-num">單價</th>
              <th class="c-ccy">幣別</th>
              <th class="c-st">狀態</th>
              <th class="c-act">入庫</th>
            </tr>
          </thead>

          <tbody>
            <template v-for="(row, idx) in items" :key="row.grn_line_id">
              <tr class="grp">
                <td colspan="3">進貨單號: <span class="mono">{{ row.grn_no }}</span></td>
                <td colspan="7">廠商: {{ row.factory }}</td>
              </tr>

              <tr class="dat">
                <td class="c-no">{{ (page - 1) * pageSize + idx + 1 }}</td>
                <td class="mono">{{ row.po_no }}</td>
                <td class="mono">{{ row.item_no }}</td>
                <td class="c-desc">
                  <div class="desc" v-html="row.description || '-'"></div>
                </td>
                <td class="c-num">{{ fmtInt(row.po_qty) }}</td>
                <td class="c-num">{{ fmtInt(row.recv_qty) }}</td>
                <td class="c-num">{{ fmtMoney2(row.unit_price) }}</td>
                <td class="c-ccy">{{ row.currency || '-' }}</td>
                <td class="c-st">
                  <span class="pill" :data-s="row.status">{{ grnStatusLabel(row.status) }}</span>
                </td>
                <td class="c-act">
                  <el-button size="small" type="success" @click="openInlineStock(row)">入庫</el-button>
                </td>
              </tr>

              <!-- inline 入庫（桌機） -->
              <tr v-if="stockEdit.openId === row.grn_line_id" class="inline-row">
                <td colspan="10">
                  <div class="inline-edit inline-edit--row">
                    <el-date-picker
                      v-model="stockEdit.date"
                      type="date"
                      value-format="YYYY-MM-DD"
                      size="small"
                      style="width: 150px"
                    />

                    <!-- ✅ 原生 input：整數 -->
                    <input
                      v-model.number="stockEdit.qty"
                      type="number"
                      inputmode="numeric"
                      min="0"
                      step="1"
                      class="h-8 w-[160px] px-2 rounded-md border border-slate-200 bg-white text-right tabular-nums
                             focus:outline-none focus:ring-1 focus:ring-blue-400"
                    />

                    <el-input v-model="stockEdit.memo" size="small" placeholder="備註" style="flex: 1" />

                    <el-button
                      type="primary"
                      size="small"
                      :loading="stockEdit.saving"
                      @click="confirmInlineStock(row)"
                    >
                      確認
                    </el-button>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- ✅ pagination -->
      <div class="inv-pager">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @update:current-page="p => { page = p; loadLines() }"
          @update:page-size="s => { pageSize = s; page = 1; loadLines() }"
        />
      </div>

      <!-- ✅ PO Picker Dialog -->
      <el-dialog
        v-model="poPickerOpen"
        class="po-picker-dialog"
        title="選擇採購單（PO）"
        width="1200px"
        top="2vh"
        :fullscreen="isMobile"
        :append-to-body="true"
        :destroy-on-close="true"
        :close-on-click-modal="false"
      >
        <!-- 查詢區 -->
        <div class="po-query-area">
          <div class="flex flex-col sm:flex-row sm:items-center gap-2">
            <el-select
              v-model="queryField"
              class="query-select w-full sm:w-auto"
              :style="{ width: isMobile ? '100%' : '240px' }"
            >
              <el-option label="產品編號" value="item" />
              <el-option label="廠商" value="factory" />
              <el-option label="採購日期" value="date" />
              <el-option label="採購單號" value="po" />
            </el-select>

            <el-input
              v-if="queryField !== 'date'"
              v-model="queryText"
              size="small"
              placeholder="輸入關鍵字（可累計）"
              class="query-input w-full sm:w-72"
              clearable
              @keyup.enter="addCondition"
            />

            <template v-else>
              <el-date-picker v-model="poFrom" type="date" placeholder="From" :teleported="false" class="w-full sm:w-40" />
              <el-date-picker v-model="poTo" type="date" placeholder="To" :teleported="false" class="w-full sm:w-40" />
            </template>

            <el-button v-if="queryField !== 'date'" plain class="w-full sm:w-auto" @click="addCondition">
              加入條件
            </el-button>

            <div class="flex gap-2 w-full sm:w-auto">
              <el-button :loading="loadingPo" type="primary" class="flex-1 sm:flex-none" @click="doSearchPo">
                查詢
              </el-button>

              <el-button plain class="flex-1 sm:flex-none" @click="cancelSearchPo">
                取消
              </el-button>
            </div>

            <span v-if="loadingPo" class="text-xs text-gray-500 flex items-center gap-1">
              <span class="po-loading-dot"></span>
              執行中...
            </span>
          </div>

          <div class="text-xs text-gray-500 mt-2">
            條件：
            <span v-if="itemKw">產品={{ itemKw }}；</span>
            <span v-if="factoryKw">廠商={{ factoryKw }}；</span>
            <span v-if="poKw">採購單={{ poKw }}；</span>
            <span v-if="poFrom || poTo">日期={{ fmtDateYMD(poFrom) }}~{{ fmtDateYMD(poTo) }}；</span>
          </div>
        </div>

        <!-- 表格捲動區 -->
        <div class="po-table-scroll">
          <!-- ✅ Mobile: Cards -->
          <div v-if="isMobile" class="po-cards">
            <div v-for="row in safeOpenPos" :key="row.purchase_list_id" class="po-card">
              <div class="po-card-top">
                <div class="po-card-title">
                  <div class="font-bold">{{ row.item_no }}</div>
                  <div class="text-xs text-gray-500">{{ row.factory }}</div>
                </div>

                <div class="flex items-center gap-2">
                  <div class="text-xs text-gray-500">
                    {{ fmtDateYMD(row.poDate) }}｜{{ row.po_no }}
                  </div>

                  <!-- ✅ 原生 checkbox（預設不勾） -->
                  <input
                    type="checkbox"
                    v-model="row.checked"
                    class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div class="text-sm mt-1">
                <span class="text-gray-500">品名：</span>{{ row.description || '-' }}
              </div>

              <div class="po-card-bottom">
                <div class="text-sm">
                  <div class="text-gray-500 text-xs">採購數量</div>
                  <div class="font-bold">{{ fmtInt(row.po_qty) }}</div>
                </div>

                <div class="text-sm">
                  <div class="text-gray-500 text-xs">進貨數量</div>

                  <!-- ✅ 原生 input（整數） -->
                  <input
                    v-model.number="row.recv_qty"
                    type="number"
                    inputmode="numeric"
                    min="0"
                    step="1"
                    class="w-full h-9 px-3 rounded-lg border border-slate-200 bg-white text-right tabular-nums
                           focus:outline-none focus:ring-1 focus:ring-blue-400"
                    @input="onRecvQtyChange(row)"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- ✅ Desktop: el-table + 原生 input -->
          <el-table
            v-else
            :data="safeOpenPos"
            height="100%"
            size="small"
            :row-key="row => row.purchase_list_id"
          >
            <el-table-column label="選" width="60" align="center">
              <template #default="{ row }">
                <input
                  type="checkbox"
                  v-model="row.checked"
                  class="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
              </template>
            </el-table-column>

            <el-table-column label="採購日期" width="110">
              <template #default="{ row }">{{ fmtDateYMD(row.poDate) }}</template>
            </el-table-column>

            <el-table-column prop="po_no" label="採購單編號" width="150" />
            <el-table-column prop="factory" label="廠商" min-width="180" />
            <el-table-column prop="item_no" label="產品編號" width="160" />
            <el-table-column
              prop="description"
              label="品名 / 說明"
              min-width="240"
            >
              <template #default="{ row }">
                <el-tooltip
                  placement="top"
                  effect="dark"
                  :show-after="300"
                  popper-class="desc-tooltip"
                >
                  <template #content>
                    <div class="whitespace-pre-wrap text-xs max-w-[480px]">
                      {{ normalizeDesc(row.description) }}
                    </div>
                  </template>

                  <div class="truncate">
                    {{ normalizeDesc(row.description) }}
                  </div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="po_qty" label="採購數量" width="110" align="right">
              <template #default="{ row }">{{ fmtInt(row.po_qty) }}</template>
            </el-table-column>

            <el-table-column label="進貨數量" width="140" align="right">
              <template #default="{ row }">
                <div class="flex justify-end">
                <input
                  :value="row.recv_qty"
                  type="number"
                  inputmode="numeric"
                  min="0"
                  step="1"
                  class="h-8 w-[110px] px-2 border border-slate-200 bg-white
                        text-right tabular-nums text-[10pt]
                        focus:outline-none focus:ring-1 focus:ring-blue-400"
                  style="border-radius: 0;font-size: 10pt;margin: 3px;"
                  @input="
                    row.recv_qty = Number(($event.target.value ?? '').toString().replace(/[^\d]/g, '') || 0);
                    row.checked = true
                  "
                />
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 底部固定區 -->
        <div class="po-bottom-area">
          <div class="po-pagination">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next"
              :total="poTotal"
              :page-size="poPageSize"
              :current-page="poPage"
              @update:current-page="p => { poPage = p; loadOpenPos() }"
              @update:page-size="s => { poPageSize = s; poPage = 1; loadOpenPos() }"
            />
          </div>

          <div class="po-footer-actions">
            <div class="text-xs text-gray-500">
              勾選要建立的項目（checkbox），並可輸入「進貨數量」。
            </div>

            <div class="flex gap-2">
              <el-button size="small" @click="poPickerOpen=false">關閉</el-button>
              <el-button type="primary" size="small" :loading="creatingGrn" @click="createGrnFromDialog">
                建立進貨單
              </el-button>
            </div>
          </div>
        </div>
      </el-dialog>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { fmtDateYMD } from '@/utils/include'
import { useRouter } from 'vue-router'

const router = useRouter()

async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...options
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok || data.ok === false) throw new Error(data.msg || `HTTP ${res.status}`)
  return data
}

/* =========================
 * 主列表：進貨單明細 lines
 * ========================= */
const searchOpen = ref(false)
const status = ref('') // POSTED / OPEN / ''
const kw = ref('')

const loading = ref(false)
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

/* mobile detect */
const isMobile = ref(false)
function syncMobile() {
  isMobile.value = window.innerWidth < 640
}
function normalizeDesc(v) {
  return (v || '').replace(/<br\s*\/?>/gi, '\n')
}

/* status label */
function grnStatusLabel(s) {
  const v = String(s || '').toUpperCase()
  if (v === 'POSTED') return '已入庫'
  if (v === 'OPEN') return '未入庫'
  if (v === 'DRAFT') return '草稿'
  return v || '-'
}

/* format helpers */
function fmtInt(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '0'
  return String(Math.trunc(n))
}
function fmtMoney2(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '0.00'
  return n.toFixed(2)
}

/* load lines */
async function loadLines() {
  if (loading.value) return
  loading.value = true
  try {
    const q = new URLSearchParams()
    if (status.value) q.set('status', status.value)
    if (kw.value) q.set('kw', kw.value)
    q.set('page', String(page.value))
    q.set('pageSize', String(pageSize.value))

    const data = await apiFetch(`/api/inv/grn/lines?${q.toString()}`)
    items.value = Array.isArray(data.items) ? data.items : []
    total.value = Number(data.total ?? 0)
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

/* buttons */
function doSearch() {
  page.value = 1
  loadLines()
}
function clearSearch() {
  status.value = ''
  kw.value = ''
  page.value = 1
  loadLines()
}
function reload() {
  loadLines()
}

/* =========================
 * Inline 入庫（toggle）
 * ========================= */
const stockEdit = ref({
  openId: null,
  date: fmtDateYMD(new Date()),
  qty: 0,
  memo: '',
  saving: false
})

function openInlineStock(row) {
  if (stockEdit.value.openId === row.grn_line_id) {
    stockEdit.value.openId = null
    return
  }
  stockEdit.value.openId = row.grn_line_id
  stockEdit.value.date = fmtDateYMD(new Date())
  stockEdit.value.qty = Math.trunc(Number(row.po_qty ?? 0)) // ✅ 整數
  stockEdit.value.memo = ''
}

async function confirmInlineStock(row) {
  // TODO: 接庫存異動 API
  ElMessage.success('已送出（請接庫存異動 API）')
  stockEdit.value.openId = null
}

/* =========================
 * PO Picker：查詢 / 分頁 / 建立進貨單
 * ========================= */
const poPickerOpen = ref(false)
const loadingPo = ref(false)
const openPos = ref([])

const safeOpenPos = computed(() => (Array.isArray(openPos.value) ? openPos.value : []))

// 查詢條件
const queryField = ref('item') // item | factory | date | po
const queryText = ref('')

const itemKw = ref('')
const factoryKw = ref('')
const poKw = ref('')

// 日期條件
const poFrom = ref(null)
const poTo = ref(null)

// 分頁
const poPage = ref(1)
const poPageSize = ref(20)
const poTotal = ref(0)

function addCondition() {
  const t = (queryText.value || '').trim()
  if (!t) return

  if (queryField.value === 'item') {
    itemKw.value = itemKw.value ? `${itemKw.value} ${t}` : t
  } else if (queryField.value === 'factory') {
    factoryKw.value = factoryKw.value ? `${factoryKw.value} ${t}` : t
  } else if (queryField.value === 'po') {
    poKw.value = poKw.value ? `${poKw.value} ${t}` : t
  }
  queryText.value = ''
}

async function openPoPicker() {
  openPos.value = []
  poTotal.value = 0
  loadingPo.value = false
  poPickerOpen.value = true
  await nextTick()
}

function doSearchPo() {
  poPage.value = 1
  loadOpenPos()
}

function cancelSearchPo() {
  queryField.value = 'item'
  queryText.value = ''
  itemKw.value = ''
  factoryKw.value = ''
  poKw.value = ''
  poFrom.value = null
  poTo.value = null
  poPage.value = 1

  openPos.value = []
  poTotal.value = 0
  loadingPo.value = false
}

async function loadOpenPos() {
  if (loadingPo.value) return
  loadingPo.value = true
  try {
    const q = new URLSearchParams()

    const f = fmtDateYMD(poFrom.value)
    const t = fmtDateYMD(poTo.value)
    if (f) q.set('from', f)
    if (t) q.set('to', t)

    if (factoryKw.value) q.set('factory_kw', factoryKw.value)
    if (itemKw.value) q.set('item_kw', itemKw.value)
    if (poKw.value) q.set('po_kw', poKw.value)

    q.set('page', String(poPage.value))
    q.set('pageSize', String(poPageSize.value))

    const data = await apiFetch(`/api/inv/grn/po/open?${q.toString()}`)

    poTotal.value = Number(data.total ?? 0)
    openPos.value = (Array.isArray(data.items) ? data.items : []).map(r => {
      const po_qty = Math.trunc(Number(r.po_qty ?? 0))
      const recv_qty = Math.trunc(Number(r.recv_qty ?? po_qty))
      return {
        ...r,
        po_qty,
        recv_qty: po_qty,
        description: r.description ?? '',
        checked: false // ✅ 預設都不勾
      }
    })
  } catch (e) {
    openPos.value = []
    poTotal.value = 0
    ElMessage.error(e.message)
  } finally {
    loadingPo.value = false
  }
}

function onRecvQtyChange(row) {
  // ✅ 只要輸入數量變更，就自動勾選（你之前的需求）
  row.checked = true
  // ✅ 確保整數
  const n = Number(row.recv_qty)
  row.recv_qty = Number.isFinite(n) ? Math.trunc(n) : 0
}

const creatingGrn = ref(false)

async function createGrnFromDialog() {
  if (!safeOpenPos.value.length) {
    ElMessage.error('沒有可建立的採購資料')
    return
  }

  const selected = safeOpenPos.value.filter(r => r.checked)
  if (!selected.length) {
    ElMessage.error('請至少勾選一筆要建立的進貨項目')
    return
  }

  const forms = new Set(selected.map(r => r.po_form_no).filter(Boolean))
  if (forms.size !== 1) {
    ElMessage.error('請先用查詢條件縮小到同一張採購單，再建立進貨單')
    return
  }
  const po_form_no = [...forms][0]

  creatingGrn.value = true
  try {
    const payload = {
      po_form_no,
      grn_date: fmtDateYMD(new Date()),
      wh_id: 1,
      lines: selected.map(r => ({
        purchase_list_id: r.purchase_list_id,
        recv_qty: Math.trunc(Number(r.recv_qty ?? 0)) // ✅ 整數
      }))
    }

    const data = await apiFetch('/api/inv/grn/create', {
      method: 'POST',
      body: JSON.stringify(payload)
    })

    ElMessage.success(`已建立 ${data.grn_no}`)
    poPickerOpen.value = false
    await loadLines()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    creatingGrn.value = false
  }
}
/* mount */
onMounted(() => {
  syncMobile()
  window.addEventListener('resize', syncMobile)
  loadLines()
})
onUnmounted(() => window.removeEventListener('resize', syncMobile))
</script>

<style scoped>
.inv-wrap{ padding:0; }

.inv-titlebar{
  background: transparent !important;
  padding: 10px !important;
  border-radius: 0 !important;
  display:flex;
  align-items:flex-start;
  gap: 12px;
}
.inv-title{ margin:0; font-size:18px; font-weight:800; }
.inv-title-accent{
  color:#0063C6;
  padding-bottom:2px;
  border-bottom:5px #0063C6 solid;
  margin-right: 2px;
}
.inv-actions{
  margin-left:auto;
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  justify-content:flex-end;
}

.inv-search{
  display:flex;
  gap:8px;
  align-items:center;
  flex-wrap:wrap;
  padding:10px 0;
}
.inv-search__status{ width:140px; }
.inv-search__kw{ flex:1; min-width:260px; }

.inv-list{ margin-top:6px; }
.inv-pager{ margin-top:10px; display:flex; justify-content:flex-end; }

.inv-table{ width:100%; border-collapse:collapse; table-layout:fixed; }
.inv-table th, .inv-table td{
  font-size:10pt !important;
  border:1px solid #e5e7eb;
  padding:8px;
  vertical-align:top;
}
.inv-table thead th{ background:#f3f4f6; font-weight:800; }
.grp td{ background:#fafafa; font-weight:700; }
.c-no{ width:60px; text-align:center; }
.c-desc{ width:18%; }
.c-num{ width:110px; text-align:right; }
.c-ccy{ width:80px; text-align:center; }
.c-st{ width:90px; text-align:center; }
.c-act{ width:90px; text-align:center; }

.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono","Courier New", monospace; }
.desc{ max-height:90px; overflow:auto; line-height:1.35; white-space:normal; }

.pill{
  display:inline-block;
  padding:2px 8px;
  border-radius:999px;
  font-size:12px;
  font-weight:800;
  background:#eef2ff;
  color:#3730a3;
}
.pill[data-s="OPEN"]{ background:#ecfeff; color:#155e75; }
.pill[data-s="POSTED"]{ background:#ecfdf5; color:#065f46; }
.pill[data-s="DRAFT"]{ background:#fff7ed; color:#9a3412; }

.inline-row td{ background:#fff; }
.inline-edit{
  display:flex;
  gap:8px;
  flex-wrap:wrap;
  align-items:center;
  padding:8px;
  background:#f9fafb;
  border:1px dashed #e5e7eb;
  border-radius:8px;
}
.inline-edit--row{ flex-wrap:nowrap; }

.m-cards{ display:flex; flex-direction:column; gap:10px; }
.m-card{ border:1px solid #e5e7eb; border-radius:10px; padding:10px; background:#fff; }
.m-card__head{ padding-bottom:8px; border-bottom:1px dashed #e5e7eb; }
.m-card__line1{ display:flex; gap:6px; font-weight:800; font-size:13px; }
.m-card__line2{ margin-top:4px; font-size:12px; color:#6b7280; }
.k{ color:#6b7280; font-size:12px; }
.ellipsis{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:220px; }
.m-card__grid{
  margin-top:8px;
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap:8px;
}
.cell{
  background:#f9fafb;
  border:1px solid #eef2f7;
  border-radius:8px;
  padding:8px;
  min-height:52px;
}
.cell--desc{ grid-column:1 / -1; }
.num{ font-variant-numeric: tabular-nums; }

.icon-btn{
  width:32px; height:32px; padding:4px;
  display:inline-flex; align-items:center; justify-content:center;
  border-radius:6px;
  border:1px solid transparent;
  background:transparent;
  cursor:pointer;
  transition: background .15s ease, border-color .15s ease, transform .12s ease;
}
.icon-btn img{ width:20px; height:20px; opacity:.75; transition: opacity .15s ease; }
.icon-btn:hover{ background:#f3f4f6; border-color:#e5e7eb; }
.icon-btn:hover img{ opacity:1; }
.icon-btn.active{ background:#e0f2fe; border-color:#93c5fd; }
.icon-btn.active img{ opacity:1; }
.icon-btn:active{ transform: translateY(1px); }
.icon-btn:disabled{ opacity:.5; cursor:not-allowed; }

.loading-dot{
  width:14px; height:14px;
  border-radius:50%;
  border:2px solid #9ca3af;
  border-top-color: transparent;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.po-query-area{ flex:0 0 auto; }
.po-table-scroll{
  flex:1 1 auto;
  min-height:0;
  overflow:auto;
  border:1px solid #e5e7eb;
  border-radius:8px;
  padding:8px;
  background:#fff;
}
.po-bottom-area{
  flex:0 0 auto;
  display:flex;
  flex-direction:column;
  gap:6px;
}
.po-pagination{ display:flex; justify-content:flex-end; }
.po-footer-actions{
  display:flex;
  align-items:center;
  justify-content: space-between;
  gap:10px;
}
.po-loading-dot{
  width:12px; height:12px;
  border-radius:50%;
  border:2px solid #9ca3af;
  border-top-color: transparent;
  display:inline-block;
  animation: spin .8s linear infinite;
}
.desc-tooltip{
  white-space: pre-wrap !important;
  max-width: 480px;
  line-height: 1.4;
}

</style>

<style>
/* ✅ 不要 scoped：append-to-body 才吃得到 */
.po-picker-dialog .el-dialog{
  top: 2vh !important;
  margin: 0 auto !important;
  max-height: calc(100vh - 4vh) !important;
}
.po-picker-dialog .el-dialog__body{
  height: 78vh !important;
  max-height: 780px !important;
  display:flex !important;
  flex-direction:column !important;
  gap:10px !important;
  overflow:hidden !important;
}
.po-picker-dialog .po-table-scroll{
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
}

/* ✅ 原生 number input：隱藏上下箭頭（可選，想保留就刪掉） */
.po-picker-dialog input[type=number]::-webkit-outer-spin-button,
.po-picker-dialog input[type=number]::-webkit-inner-spin-button{
  -webkit-appearance: none;
  margin: 0;
}
.po-picker-dialog input[type=number]{ -moz-appearance: textfield; }
</style>
