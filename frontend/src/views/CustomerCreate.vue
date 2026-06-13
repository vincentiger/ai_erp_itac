<template>
  <div class="min-h-screen bg-slate-50 relative">
    <!-- Alerts (absolute, centered) -->
    <div
      v-if="alert.show"
      class="absolute top-[96px] left-1/2 z-50 w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 px-4"
    >
      <div
        class="rounded-2xl border p-4 text-sm shadow-xl"
        :class="alert.type === 'error'
          ? 'border-rose-200 bg-rose-50 text-rose-800'
          : alert.type === 'success'
            ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
            : 'border-slate-200 bg-white text-slate-800'"
      >
        <div class="mb-1 text-base font-black tracking-wide">
          {{ alert.type === 'error' ? '注意' : alert.type === 'success' ? '完成' : '提示' }}
        </div>
        <div class="leading-relaxed whitespace-pre-line">{{ alert.message }}</div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div
      v-if="loading"
      class="fixed inset-0 z-[80] flex items-center justify-center bg-slate-50/78 backdrop-blur-[1px]"
    >
      <div class="rounded-2xl border border-slate-200 bg-white px-6 py-4 shadow-lg">
        <div class="text-lg font-black tracking-[0.2em] text-slate-700">LOADING</div>
        <div class="mt-1 text-xs font-semibold text-slate-400">背景載入資料中…</div>
      </div>
    </div>

    <main class="px-4 pb-28">
      <section class="mt-4 flex justify-end">
        <button
          class="h-11 px-4 rounded-xl border border-slate-200 bg-white text-sm font-semibold text-slate-700 active:scale-[0.98]"
          type="button"
          @click="openManualPdf('客戶管理.pdf')"
        >
          使用說明
        </button>
      </section>

      <!-- Category levels -->
      <section v-if="!itacLabMode" class="mt-4 bg-white rounded-2xl border border-slate-200 p-4">
        <div class="text-sm font-semibold text-slate-900">分類</div>

        <div class="mt-3 space-y-3">
          <!-- level1 -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">分類（第一層）</label>
            <select
              data-voice="no1"
              class="w-full h-12 px-3 rounded-xl border border-slate-200 bg-white"
              v-model="form.no1"
              @change="onChangeNo1"
            >
              <option value="">請選擇</option>
              <option v-for="o in options.no1" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>
          </div>

          <!-- level2 -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">分類（第二層，可不填）</label>
            <select
              data-voice="no2"
              class="w-full h-12 px-3 rounded-xl border border-slate-200 bg-white disabled:bg-slate-50"
              v-model="form.no2"
              @change="onChangeNo2"
              :disabled="!form.no1"
            >
              <option value="">請選擇</option>
              <option v-for="o in options.no2" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>

            <div v-if="form.no1 && options.no2.length === 0" class="mt-2 text-xs text-amber-700">
              目前此第一層沒有第二層資料（請確認 no1 參數對應資料表 no1 欄位）
            </div>
          </div>
        </div>
      </section>

      <!-- Refno preview -->
      <section class="mt-4 bg-white rounded-2xl border border-slate-200 p-4">
        <div class="flex items-center justify-between">
          <div class="text-sm font-semibold text-slate-900">客戶代號</div>
          <span class="text-xs text-slate-500">{{ isEditMode ? '編輯模式不可修改' : '可手動輸入，也可依分類自動產生' }}</span>
        </div>
        <div class="mt-2 flex items-center gap-2">
          <input
            data-voice="refno"
            class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white text-slate-900 font-mono disabled:bg-slate-50"
            v-model.trim="form.refno"
            :readonly="isEditMode"
            :disabled="isEditMode"
            placeholder="請輸入客戶代號"
          />
          <button
            class="h-12 px-3 rounded-xl border border-slate-200 bg-white active:scale-[0.98] disabled:opacity-50"
            @click="refreshRefno"
            :disabled="!form.no1 || isEditMode"
            title="重新預覽"
            type="button"
          >
            ↻
          </button>
        </div>
      </section>

      <!-- Basic info -->
      <section class="mt-4 bg-white rounded-2xl border border-slate-200 p-4">
        <div class="text-sm font-semibold text-slate-900">基本資料</div>

        <div class="mt-3 space-y-3">
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">公司名稱（最多100字）</label>
            <input
              data-voice="company"
              class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white"
              v-model.trim="form.company"
              maxlength="100"
              placeholder="請輸入公司名稱"
              autocomplete="organization"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">公司簡稱（最多10字）</label>
            <input
              data-voice="short"
              class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white"
              v-model.trim="form.short"
              maxlength="10"
              placeholder="請輸入簡稱"
              autocomplete="off"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">國家</label>
            <select
              data-voice="country"
              class="w-full h-12 px-3 rounded-xl border border-slate-200 bg-white"
              v-model="form.country"
            >
              <option value="">請選擇</option>
              <option v-for="o in options.country" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">總公司</label>
            <select
              data-voice="headerquarter"
              class="w-full h-12 px-3 rounded-xl border border-slate-200 bg-white"
              v-model="form.headerquarter"
            >
              <option value="">請選擇</option>
              <option v-for="o in options.headerquarter" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">網址</label>
            <input
              data-voice="url"
              class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white"
              v-model.trim="form.url"
              placeholder="https://"
              autocomplete="url"
            />
          </div>
        </div>
      </section>

      <!-- CEO -->
      <section class="mt-4 bg-white rounded-2xl border border-slate-200 p-4">
        <div class="text-sm font-semibold text-slate-900 mb-2">負責人</div>
        <input
          data-voice="ceo"
          class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-slate-300"
          v-model.trim="form.ceo"
          placeholder="請輸入負責人姓名"
        />
      </section>

      <!-- Multi inputs -->
      <MultiInputCard ref="addressesRef" title="地址" v-model="form.addresses" placeholder="新增地址…" voiceKey="addresses" />
      <MultiInputCard ref="contactsRef" title="聯絡人" v-model="form.contacts" placeholder="新增聯絡人…" voiceKey="contacts" />
      <MultiInputCard ref="telRef" title="電話" v-model="form.tel" placeholder="新增電話…" inputmode="tel" voiceKey="tel" />
      <MultiInputCard ref="faxRef" title="傳真" v-model="form.fax" placeholder="新增傳真…" inputmode="tel" voiceKey="fax" />
      <MultiInputCard ref="emailsRef" title="Email" v-model="form.emails" placeholder="新增 Email…" inputmode="email" voiceKey="emails" />

      <!-- Sales reps (multi select) -->
      <section class="mt-4 bg-white rounded-2xl border border-slate-200 p-4">
        <div class="flex items-center justify-between">
          <div class="text-sm font-semibold text-slate-900">業務代表（可多選）</div>
          <div class="text-xs text-slate-500">{{ form.sales_reps.length }} 已選</div>
        </div>

        <div class="mt-3">
          <input
            data-voice="sales_reps_search"
            class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white"
            v-model="repKeyword"
            placeholder="搜尋業務代表…"
          />
        </div>

        <div class="mt-3 max-h-56 overflow-auto rounded-xl border border-slate-200 bg-white">
          <label
            v-for="o in filteredSalesReps"
            :key="o.value"
            class="rep-item"
          >
            <input
              type="checkbox"
              class="rep-checkbox"
              :value="String(o.value)"
              v-model="form.sales_reps"
            />
            <span class="rep-text">{{ o.label }}</span>
          </label>
        </div>
      </section>

      <!-- Other -->
      <section class="mt-4 bg-white rounded-2xl border border-slate-200 p-4">
        <div class="text-sm font-semibold text-slate-900">其他</div>

        <div class="mt-3 space-y-3">
          <!-- 付款方式 -->
          <section class="mt-4 bg-white rounded-2xl border border-slate-200 p-4">
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-semibold text-slate-600">付款方式</label>

              <button
                type="button"
                class="h-8 w-8 rounded-full bg-slate-100 text-slate-600 inline-flex items-center justify-center
                      hover:bg-slate-200 active:scale-95 transition"
                @click="openOptionEditor('payment')"
                title="維護選項"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 20h9" />
                  <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
                </svg>
              </button>
            </div>

            <select
              data-voice="payment"
              class="w-full h-12 px-3 rounded-xl border border-slate-200 bg-white"
              v-model="form.payment"
            >
              <option value="">請選擇</option>
              <option v-for="o in options.payment" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>
          </section>

          <!-- 品質認證 (select + pencil) -->
          <section class="bg-white rounded-2xl border border-slate-200 p-4">
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-semibold text-slate-600">品質認證</label>

              <button
                type="button"
                class="h-8 w-8 rounded-full bg-slate-100 text-slate-600 inline-flex items-center justify-center
                       hover:bg-slate-200 active:scale-95 transition"
                @click="openOptionEditor('Class2')"
                title="維護選項"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 20h9" />
                  <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
                </svg>
              </button>
            </div>

            <select
              data-voice="Class2"
              class="w-full h-12 px-3 rounded-xl border border-slate-200 bg-white"
              v-model="form.Class2"
            >
              <option value="">請選擇</option>
              <option v-for="o in options.Class2" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>
          </section>

          <!-- 經營項目 (select + pencil) -->
          <section class="bg-white rounded-2xl border border-slate-200 p-4">
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-semibold text-slate-600">經營項目</label>

              <button
                type="button"
                class="h-8 w-8 rounded-full bg-slate-100 text-slate-600 inline-flex items-center justify-center
                       hover:bg-slate-200 active:scale-95 transition"
                @click="openOptionEditor('items')"
                title="維護選項"
              >
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 20h9" />
                  <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
                </svg>
              </button>
            </div>

            <select
              data-voice="items"
              class="w-full h-12 px-3 rounded-xl border border-slate-200 bg-white"
              v-model="form.items"
            >
              <option value="">請選擇</option>
              <option v-for="o in options.items" :key="o.value" :value="o.value">
                {{ o.label }}
              </option>
            </select>
          </section>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">員工人數</label>
            <select
              data-voice="employee"
              class="w-full h-12 px-3 rounded-xl border border-slate-200 bg-white"
              v-model="form.employee"
            >
              <option value="">請選擇</option>
              <option v-for="o in employeeOptions" :key="o.value" :value="o.value">
                {{ o.value }}
              </option>
            </select>
          </div>

          <!-- flags -->
          <div class="chk-grid">
            <label class="chk-card">
              <input class="chk" type="checkbox" v-model="form.quit" />
              <span class="chk-text">拒絕往來</span>
            </label>

            <label class="chk-card">
              <input class="chk" type="checkbox" v-model="form.secret" />
              <span class="chk-text">自營工廠</span>
            </label>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">統一編號</label>
            <input
              data-voice="LicenceNo"
              class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white"
              v-model.trim="form.LicenceNo"
              placeholder="8碼"
              autocomplete="off"
            />
          </div>


          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">信用額度(USD)</label>
              <input
                data-voice="credit"
                v-model.number="form.credit"
                class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white"
                type="number"
                inputmode="decimal"
                placeholder="0"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-600 mb-1">佣金(%)</label>
              <input
                data-voice="commission"
                class="w-full h-12 px-4 rounded-xl border border-slate-200 bg-white"
                v-model.number="form.commission"
                type="number"
                inputmode="decimal"
                placeholder="0"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">附註說明</label>
            <textarea
              data-voice="remarks"
              class="w-full min-h-[120px] p-4 rounded-xl border border-slate-200 bg-white"
              v-model.trim="form.remarks"
              placeholder="輸入備註…"
            />
          </div>
        </div>
      </section>

      <div class="h-6"></div>
    </main>

    <!-- Bottom sticky save bar (mobile) -->
    <footer class="fixed bottom-0 left-0 right-0 z-30 bg-slate-100 backdrop-blur border-t border-slate-200">
      <div class="mx-auto w-full max-w-4xl px-4 py-3 flex items-center justify-center gap-3">

        <!-- 🎤 語音 -->
        <button
          type="button"
          class="h-10 w-10 rounded-full bg-slate-200 text-slate-700 hover:bg-slate-300 active:scale-95 transition"
          @click="toggleVoice"
          :title="isListening ? '關閉語音' : '啟動語音'"
          aria-label="語音輸入"
        >
          🎤
        </button>
        <!-- 🎤 語音狀態 -->
        <div v-if="isListening" class="text-xs font-semibold text-slate-600">
          聆聽中.....
        </div>
        <!-- 取消 -->
        <button
          type="button"
          class="h-10 px-5 rounded-xl bg-white border border-slate-300 text-slate-700 font-semibold
                 hover:bg-slate-50 active:scale-[0.98] transition disabled:opacity-50"
          @click="resetForm"
          :disabled="saving"
        >
          取消
        </button>

        <button
          v-if="isEditMode && canDeleteCurrent"
          type="button"
          class="h-10 px-5 rounded-xl bg-rose-600 text-white font-semibold
                 hover:bg-rose-700 active:scale-[0.98] transition disabled:opacity-50"
          :disabled="saving || loading"
          @click="deleteCurrent"
        >
          刪除
        </button>

        <!-- 儲存 -->
        <button
          type="button"
          class="h-10 px-6 rounded-xl bg-emerald-600 text-white font-semibold
                 hover:bg-emerald-700 active:scale-[0.98] disabled:opacity-50 transition"
          :disabled="saving || loading"
          @click="save"
        >
          {{ saving ? '儲存中…' : '儲存客戶' }}
        </button>
      </div>
    </footer>

    <!-- Options Editor Modal -->
    <div v-if="optEditor.open" class="fixed inset-0 z-[60]">
      <div class="absolute inset-0 bg-black/30" @click="closeOptionEditor"></div>

      <div
        class="absolute left-1/2 top-1/2 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2
               rounded-2xl bg-white shadow-xl border border-slate-200 overflow-hidden"
      >
        <div class="px-4 py-3 flex items-center justify-between bg-slate-50 border-b border-slate-200">
          <div class="font-semibold text-slate-900">維護：{{ optEditor.title }}</div>
          <button type="button" class="h-8 w-8 rounded-full hover:bg-slate-200" @click="closeOptionEditor">×</button>
        </div>

        <div class="p-4 space-y-3">
          <!-- list -->
          <div class="max-h-52 overflow-auto rounded-xl border border-slate-200">
            <button
              v-for="o in optEditor.list"
              :key="o.value"
              type="button"
              class="w-full text-left px-3 py-3 border-b last:border-b-0 border-slate-100 hover:bg-slate-50"
              :class="String(optEditor.selected)===String(o.value) ? 'bg-slate-100' : ''"
              @click="pickOption(o.value)"
            >
              <div class="text-sm text-slate-900">{{ o.label }}</div>
              <!-- ✅ 不顯示 value -->
            </button>
          </div>

          <!-- input -->
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">
              {{ optEditor.mode === 'edit' ? '修改名稱' : '新增名稱' }}
            </label>
            <input
              class="w-full h-11 px-4 rounded-xl border border-slate-200 bg-white"
              v-model.trim="optEditor.input"
              placeholder="輸入項目名稱…"
            />
          </div>

          <!-- actions -->
          <div class="flex items-center justify-end gap-2 pt-1">
            <button
              type="button"
              class="h-10 px-4 rounded-xl bg-slate-100 text-slate-700 font-semibold
                     hover:bg-slate-200 active:scale-95 transition"
              @click="addOption"
            >
              新增
            </button>

            <button
              type="button"
              class="h-10 px-4 rounded-xl bg-amber-500 text-white font-semibold
                     hover:bg-amber-600 active:scale-95 transition disabled:opacity-50"
              :disabled="!optEditor.selected"
              @click="updateOption"
            >
              修改
            </button>

            <button
              type="button"
              class="h-10 px-4 rounded-xl bg-rose-600 text-white font-semibold
                     hover:bg-rose-700 active:scale-95 transition disabled:opacity-50"
              :disabled="!optEditor.selected"
              @click="deleteOption"
            >
              刪除
            </button>
          </div>

          <div class="text-xs text-slate-500">
            先點列表選一筆才能「修改 / 刪除」，不選就是「新增」。
          </div>
        </div>
      </div>
    </div>
    <!-- Toast (auto hide 1s) -->
    <div
      v-if="toast.show"
      class="fixed top-[86px] left-1/2 z-[70] -translate-x-1/2 w-[calc(100%-2rem)] max-w-sm px-4"
    >
      <div
        class="rounded-xl border px-3 py-2 text-sm shadow-lg"
        :class="toast.type==='success'
          ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
          : toast.type==='error'
            ? 'border-rose-200 bg-rose-50 text-rose-800'
            : 'border-slate-200 bg-white text-slate-800'"
      >
        {{ toast.message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import MultiInputCard from '../components/MultiInputCard.vue'
import { apiFetch } from '@/utils/apiFetch'

const API_BASE = '/ai/api'
const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const route = useRoute()

function openManualPdf(fileName) {
  if (!fileName) return
  const target = `${import.meta.env.BASE_URL}manuals/${encodeURIComponent(String(fileName))}`
  window.open(target, '_blank', 'noopener')
}

const addressesRef = ref(null)
const contactsRef = ref(null)
const telRef = ref(null)
const faxRef = ref(null)
const emailsRef = ref(null)

const refno = computed(() => (route.query.refno ? String(route.query.refno) : ''))
const isEdit = computed(() => !!refno.value)
const entryFrom = computed(() => String(route.query.from || '').trim().toLowerCase())
const canDeleteCurrent = computed(() => entryFrom.value === 'customer_del')
const pendingSalesReps = ref(null)

const alert = reactive({
  show: false,
  type: 'info', // info|success|error
  message: '',
})
const toast = reactive({
  show: false,
  type: 'info', // info|success|error
  message: '',
})

function applySalesRepsFromCustomer(c) {
  // ✅ 1) sales_reps 若是空陣列/空字串，改用 sales_rep
  let raw = c?.sales_reps
  const isEmptyArr = Array.isArray(raw) && raw.length === 0
  const isEmptyStr = (typeof raw === 'string' && raw.trim() === '')
  if (raw == null || isEmptyArr || isEmptyStr) {
    raw = c?.sales_rep ?? c?.Sales_Rep ?? c?.salesRep
  }
  if (raw == null) return

  // ✅ 2) 先把 raw 轉 tokens
  let tokens = []
  if (Array.isArray(raw)) {
    tokens = raw
  } else {
    const s = String(raw).trim()
    tokens = s ? s.split(/[,\n、;；]+/g) : []
  }
  tokens = tokens.map(x => String(x ?? '').trim()).filter(Boolean)

  // ✅ 3) options 還沒好 → pending
  if (!Array.isArray(options.sales_reps) || options.sales_reps.length === 0) {
    pendingSalesReps.value = tokens
    return
  }

  // ✅ 4) 建立「正規化」對照（避免空白/全形空白造成對不到）
  const norm = (s) => String(s ?? '')
    .replace(/[ 　\t\r\n]/g, '')   // 半形/全形空白都拿掉
    .trim()

  const mapNormLabelToValue = new Map(
    options.sales_reps.map(o => [norm(o.label), String(o.value)])
  )
  const valueSet = new Set(options.sales_reps.map(o => String(o.value)))

  // ✅ 5) token → value（先 value，再 label，再模糊包含）
  const mapped = []
  for (const t0 of tokens) {
    const t = String(t0).trim()
    const tn = norm(t)

    // token 本來就是 value
    if (valueSet.has(String(t))) { mapped.push(String(t)); continue }

    // token 是 label（正規化後比對）
    const v1 = mapNormLabelToValue.get(tn)
    if (v1) { mapped.push(String(v1)); continue }

    // 模糊：label 包含 token（或 token 包含 label）
    const hit = options.sales_reps.find(o => {
      const ln = norm(o.label)
      return ln.includes(tn) || tn.includes(ln)
    })
    if (hit) { mapped.push(String(hit.value)); continue }

    // 找不到就先保留（這種情況 checkbox 不會勾，但至少不會消失）
    mapped.push(String(t))
  }

  // ✅ 6) 去重/去空白，全轉字串
  form.sales_reps = Array.from(new Set(mapped.map(s => String(s).trim()).filter(Boolean)))
}

function onParentMessage(e) {
  // ✅ 同源才收
  if (e.origin !== window.location.origin) return

  const msg = e.data
  if (!msg || msg.type !== 'PREFILL_CUSTOMER_CREATE') return

  const company = String(msg.data?.company || '').trim()
  const address = String(msg.data?.address || '').trim()
  const tel = String(msg.data?.tel || msg.data?.phone || '').trim()
  const credit = String(msg.data?.credit || '').trim()
  const fax = String(msg.data?.fax || '').trim()
  const email = String(msg.data?.email || '').trim()
  const srRaw = msg.data?.sales_reps ?? msg.data?.sales_rep ?? msg.data?.sales ?? null

  // ✅ 公司
  if (company) form.company = company

  // ✅ 地址（覆蓋第一筆）
  if (address) {
    if (!Array.isArray(form.addresses)) form.addresses = []
    if (form.addresses.length === 0) form.addresses.push(address)
    else form.addresses[0] = address
  }

  // ✅ 電話（避免字串被 v-for 拆字元）
// ✅ 電話：你的表單是 MultiInputCard -> 一律用 Array
  if (tel) {
    // 你專案實際用的是 form.tel（payload 也有 tel）
    if (!Array.isArray(form.tel)) form.tel = []
    if (form.tel.length === 0) form.tel.push(tel)
    else form.tel[0] = tel
  }

  if (fax) {
    if (!Array.isArray(form.fax)) form.fax = []
    if (form.fax.length === 0) form.fax.push(fax)
    else form.fax[0] = fax
  }

  if (email) {
    if (!Array.isArray(form.emails)) form.emails = []
    if (form.emails.length === 0) form.emails.push(email)
    else form.emails[0] = email
  }

  // msg.data.sales_reps 允許: array / 'A01,A02' / 'A01' / {value:'A01'} / {id:'A01'} 之類
  // ✅ 業務代表（先暫存，等 options 載好再轉）
  if (srRaw != null) {
    let arr = []

    if (Array.isArray(srRaw)) {
      arr = srRaw
    } else if (typeof srRaw === 'string') {
      arr = srRaw.split(',').map(s => s.trim()).filter(Boolean)
    } else if (typeof srRaw === 'object') {
      const v = srRaw.value ?? srRaw.id ?? srRaw.code ?? ''
      if (v) arr = [String(v).trim()]
    } else {
      const v = String(srRaw).trim()
      if (v) arr = [v]
    }

    arr = Array.from(new Set(arr.map(x => String(x).trim()).filter(Boolean)))

    // ❗不要直接塞 form
    pendingSalesReps.value = arr
  }
  
  // ✅ 信用（如果你有這欄）
  // ✅ 信用額度：轉成 number（去掉逗號/非數字）
  const creditRaw = String(msg.data?.credit ?? '').trim()
  if (creditRaw) {
    const num = Number(String(creditRaw).replace(/[,，\s]/g, '').replace(/[^\d.]/g, ''))
    if (Number.isFinite(num)) {
      form.credit = num
    } else {
      console.warn('[PREFILL] credit not a number:', creditRaw)
    }
  }

  // ✅ (建議) debug 一下，確認真的有收到
  console.log('[PREFILL_CUSTOMER_CREATE] recv=', { company, address, tel, credit })

  // ✅ 自動 focus 公司名稱
  nextTick(() => {
    const el = document.querySelector('[data-voice="company"]')
    el?.focus?.()
    el?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  })
}

onMounted(() => {
  window.addEventListener('message', onParentMessage)
})

onUnmounted(() => {
  window.removeEventListener('message', onParentMessage)
})


function showToast(type, message, ms = 1000) {
  toast.type = type
  toast.message = message
  toast.show = true
  window.clearTimeout(showToast._t)
  showToast._t = window.setTimeout(() => (toast.show = false), ms)
}

let _dbgLastMsg = ''
let _dbgLastAt = 0
function debugLog(msg, ms = 1200) {
  const now = Date.now()
  const m = String(msg || '')

  // 1 秒內同一句不重複顯示
  if (m === _dbgLastMsg && (now - _dbgLastAt) < 1000) return
  _dbgLastMsg = m
  _dbgLastAt = now

  showToast('info', m.slice(0, 120), ms)
  try { console.log('[voice]', m) } catch {}
}

function showAlert(type, message) {
  alert.type = type
  alert.message = message
  alert.show = true
  if (type === 'error' && typeof window !== 'undefined') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  window.clearTimeout(showAlert._t)
  const ttl = type === 'success' ? 6500 : type === 'error' ? 5000 : 4200
  showAlert._t = window.setTimeout(() => (alert.show = false), ttl)
}

/* =========================
   Form
========================= */
const form = reactive({
  no1: '',
  no2: '',

  refno: '',
  company: '',
  short: '',
  country: '',
  headerquarter: '',
  url: '',
  ceo: '',

  Class2: '',
  items: '',

  employee: '',
  quit: false,
  secret: false,

  LicenceNo: '',
  payment: '',
  credit: 0,
  commission: 0,
  remarks: '',

  addresses: [],
  contacts: [],
  tel: [],
  fax: [],
  emails: [],

  sales_reps: [],
})

const options = reactive({
  no1: [],
  no2: [],
  country: [],
  headerquarter: [],
  Class2: [],
  items: [],       // ✅ 補齊
  payment: [],
  sales_reps: [],
})

const itacLabMode = ref(false)
const defaultLabCategory = ref(null)

const employeeOptions = [
  { value: '1~5' },
  { value: '6~10' },
  { value: '11~20' },
  { value: '21~50' },
  { value: '51~100' },
  { value: '101~' },
]
async function loadCustomer(refno) {
  const r = await apiFetch(`${API_BASE}/form/customer_create/load?refno=${encodeURIComponent(refno)}`, { method: 'GET' })
  const j = await r.json().catch(() => ({}))
  if (!r.ok || j?.ok === false) throw new Error(j?.msg || `load failed (${r.status})`)
  const customer = j.data ?? j   // ✅ 這行是關鍵
  Object.assign(form, customer)

  // ✅ 業務代表 mapping（用 customer）
  applySalesRepsFromCustomer(customer)

  form.sales_reps = (form.sales_reps || []).map(v => String(v)) // 確保型別一致
  console.log('[loadCustomer] sales reps raw =', customer?.sales_reps, customer?.sales_rep, customer?.Sales_Rep, customer?.salesRep)

}


// 支援在同頁面切換不同 refno（例如從列表點不同客戶）
watch(refno, async (nv, ov) => {
  if (!nv) return
  if (nv !== ov) await loadCustomer(nv)
})

/* =========================
   Edit mode (load by refno)
========================= */
const editRefno = computed(() => {
  // 支援兩種入口：
  // 1) /customer_edit/:custno
  // 2) /customer_create?refno=xxx
  return String(route.params?.custno || route.query?.refno || '').trim()
})
const isEditMode = computed(() => !!editRefno.value)

/* =========================
   Options editor modal
========================= */
const optEditor = reactive({
  open: false,
  key: '',
  title: '',
  list: [],
  selected: '',
  input: '',
  mode: 'add', // add|edit
})
function getOptionTitle(key) {
  if (key === 'Class2') return '品質認證'
  if (key === 'items') return '經營項目'
  if (key === 'payment') return '付款方式'
  return key
}
function openOptionEditor(key) {
  optEditor.key = key
  optEditor.title = getOptionTitle(key)
  optEditor.open = true
  optEditor.mode = 'add'
  optEditor.selected = ''
  optEditor.input = ''
  optEditor.list = [] // ✅ 先清空，避免殘影

  if (key === 'Class2') {
    optEditor.title = '品質認證'
    optEditor.list = [...(options.Class2 || [])]
  } else if (key === 'items') {
    optEditor.title = '經營項目'
    optEditor.list = [...(options.items || [])]
  } else if (key === 'payment') {
    optEditor.title = '付款方式'
    optEditor.list = [...(options.payment || [])]
  }
}

function closeOptionEditor() {
  optEditor.open = false
}

function pickOption(value) {
  optEditor.selected = value
  const hit = optEditor.list.find(x => String(x.value) === String(value))
  optEditor.input = hit ? hit.label : ''
  optEditor.mode = 'edit'
}

function genValueFromLabel(label) {
  // 本機模式：產生一個相對穩定的 value（你後端接上後可改）
  const base = String(label || '').trim().toUpperCase().replace(/\s+/g, '_')
  const rand = Math.random().toString(16).slice(2, 6).toUpperCase()
  return `${base || 'ITEM'}_${rand}`
}

async function apiOptionList(key) {
  const resp = await apiFetch(`${API_BASE}/options/${encodeURIComponent(key)}`, { method: 'GET' })
  const data = await resp.json().catch(() => ({}))
  if (!resp.ok || data?.ok === false) {
    throw new Error(data?.msg || `讀取失敗 (${resp.status})`)
  }
  return data.data || []
}

async function apiOptionCreate(key, label) {
  const resp = await apiFetch(`${API_BASE}/options/${encodeURIComponent(key)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label }),
  })
  const data = await resp.json().catch(() => ({}))
  if (!resp.ok || data?.ok === false) {
    throw new Error(data?.msg || `新增失敗 (${resp.status})`)
  }
  return data
}

async function apiOptionUpdate(key, value, label) {
  const resp = await apiFetch(`${API_BASE}/options/${encodeURIComponent(key)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value, label }),
  })
  const data = await resp.json().catch(() => ({}))
  if (!resp.ok || data?.ok === false) {
    throw new Error(data?.msg || `修改失敗 (${resp.status})`)
  }
  return data
}

async function apiOptionDelete(key, value) {
  const resp = await apiFetch(`${API_BASE}/options/${encodeURIComponent(key)}/${encodeURIComponent(value)}`, {
    method: 'DELETE',
  })
  const data = await resp.json().catch(() => ({}))
  if (!resp.ok || data?.ok === false) {
    throw new Error(data?.msg || `刪除失敗 (${resp.status})`)
  }
  return data
}

async function reloadOptionsFor(key) {
  const list = await apiOptionList(key)
  options[key] = list
  optEditor.list = [...list]
}

async function addOption() {
  const label = String(optEditor.input || '').trim()
  if (!label) return showToast('error', '請輸入要新增的項目名稱')

  try {
    await apiOptionCreate(optEditor.key, label)
    await reloadOptionsFor(optEditor.key)

    optEditor.input = ''
    optEditor.selected = ''
    optEditor.mode = 'add'
    showToast('success', '新增成功', 1000)
  } catch (e) {
    showToast('error', String(e?.message || e), 1500)
  }
}

async function updateOption() {
  const label = String(optEditor.input || '').trim()
  if (!optEditor.selected) return showToast('error', '請先選擇要修改的項目')
  if (!label) return showToast('error', '請輸入新的名稱')

  try {
    await apiOptionUpdate(optEditor.key, optEditor.selected, label)
    await reloadOptionsFor(optEditor.key)
    showToast('success', '修改成功', 1000)
  } catch (e) {
    showToast('error', String(e?.message || e), 1500)
  }
}

async function deleteOption() {
  if (!optEditor.selected) return showToast('error', '請先選擇要刪除的項目')
  if (!confirm('確定要刪除這個項目？')) return

  try {
    await apiOptionDelete(optEditor.key, optEditor.selected)
    await reloadOptionsFor(optEditor.key)

    // 若刪到目前表單選到的值，也清掉
    if (optEditor.key === 'Class2' && String(form.Class2) === String(optEditor.selected)) form.Class2 = ''
    if (optEditor.key === 'items' && String(form.items) === String(optEditor.selected)) form.items = ''
    if (optEditor.key === 'payment' && String(form.payment) === String(optEditor.selected)) form.payment = ''

    optEditor.selected = ''
    optEditor.input = ''
    optEditor.mode = 'add'
    showToast('success', '刪除成功', 1000)
  } catch (e) {
    showToast('error', String(e?.message || e), 1500)
  }
}


/* =========================
   Sales reps search + sort
========================= */
const repKeyword = ref('')
const filteredSalesReps = computed(() => {
  const kw = repKeyword.value.trim().toLowerCase()
  let list = options.sales_reps || []

  if (kw) {
    list = list.filter(o => String(o.label || '').toLowerCase().includes(kw))
  }

  // 英文在前、中文在後排序
  return [...list].sort((a, b) => {
    const la = String(a.label || '')
    const lb = String(b.label || '')

    const aIsEN = /^[A-Za-z]/.test(la)
    const bIsEN = /^[A-Za-z]/.test(lb)

    if (aIsEN && !bIsEN) return -1
    if (!aIsEN && bIsEN) return 1

    if (aIsEN && bIsEN) {
      return la.localeCompare(lb, 'en', { sensitivity: 'base' })
    }
    return la.localeCompare(lb, 'zh-Hant', { sensitivity: 'base', numeric: true })
  })
})

/* =========================
   Voice (single implementation)
========================= */
function focusByVoiceKey(key) {
  // 直接命中 data-voice
  const el = document.querySelector(`[data-voice="${key}"]`)
  if (el && typeof el.focus === 'function') {
    el.focus()
    try { el.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch {}
    return true
  }

  // MultiInputCard 包在外層的情況
  const wrap = document.querySelector(`[data-voice-wrap="${key}"]`)
  const inp = wrap?.querySelector?.('input,textarea,select')
  if (inp && typeof inp.focus === 'function') {
    inp.focus()
    try { inp.scrollIntoView({ behavior: 'smooth', block: 'center' }) } catch {}
    return true
  }

  console.warn('[voice] focus failed:', key)
  return false
}

const isListening = ref(false)
let recognition = null
let activeVoiceKey = '' // 目前 focus 的 data-voice key

const VOICE_FIELD_MAP = {
  '客戶代號': 'refno',
  '代號': 'refno',

  '分類第一層': 'no1',
  '第一層': 'no1',
  '分類第二層': 'no2',
  '第二層': 'no2',

  '公司名稱': 'company',
  '公司': 'company',

  '公司簡稱': 'short',
  '簡稱': 'short',

  '國家': 'country',
  '國別': 'country',

  '總公司': 'headerquarter',
  '網址': 'url',

  '負責人': 'ceo',

  '地址': 'addresses',
  '聯絡人': 'contacts',
  '電話': 'tel',
  '傳真': 'fax',
  '信箱': 'emails',
  '電子郵件': 'emails',
  'Email': 'emails',

  '品質認證': 'Class2',
  '經營項目': 'items',

  '員工人數': 'employee',
  '付款方式': 'payment',
  '信用額度': 'credit',
  '佣金': 'commission',
  '備註': 'remarks',
}
const activeInput = ref('')  // ✅ 目前 focus 欄位 key
const voiceShouldRun = ref(false)
const micReady = ref(false)

// ✅ 新增：列出可用音訊輸入裝置
async function debugListAudioInputs() {
  try {
    if (!navigator.mediaDevices?.enumerateDevices) return []
    const devices = await navigator.mediaDevices.enumerateDevices()
    const inputs = devices.filter(d => d.kind === 'audioinput')
    console.log('audioinput devices:', inputs)
    return inputs
  } catch (e) {
    console.log('enumerateDevices error:', e)
    return []
  }
}

function toggleVoice() {
  debugLog('toggleVoice clicked')  
  if (!recognition) initVoice()
  if (!recognition) return

  // 第一次：先取得麥克風權限（不啟動語音）
  if (!micReady.value) {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        stream.getTracks().forEach(t => t.stop())
        micReady.value = true
        showToast('success', '麥克風已就緒，請再按一次開始語音', 1200)
      })
      .catch(async (err) => {
        debugLog('getUserMedia fail', err?.name, err?.message)
        const name = err?.name || ''

        // ✅ 把裝置列出來（重要：NotFoundError 最需要）
        const inputs = await debugListAudioInputs()

        if (name === 'NotAllowedError' || name === 'SecurityError') {
          showToast('error', '麥克風被拒：請檢查 Chrome 網站麥克風權限 + Windows 麥克風隱私設定', 2600)
          return
        }

        if (name === 'NotFoundError') {
          // 可能真的沒有麥克風；也可能是 Windows 隱私設定關掉，導致 enumerateDevices 空/無 label
          if (!inputs.length) {
            showToast(
              'error',
              '找不到麥克風裝置：請確認 Windows 有可用麥克風（設定→隱私與安全性→麥克風、或裝置管理員/音效設定）',
              3200
            )
          } else {
            // 有列到 audioinput 但 getUserMedia 還 NotFound，多半是預設裝置/選擇裝置問題
            showToast(
              'error',
              '偵測到音訊裝置但仍無法啟用：請到 Chrome 設定→麥克風，改選正確輸入裝置後再試',
              3200
            )
          }
          return
        }

        if (name === 'NotReadableError') {
          showToast('error', '麥克風無法讀取（可能被其他程式佔用/獨占，例如 Teams/Zoom）', 2800)
          return
        }

        showToast('error', `麥克風啟動失敗：${name || 'unknown'}`, 2400)
      })
    return
  }

  // 第二次：真正啟動語音（同步呼叫）
  if (!isListening.value) {
    voiceShouldRun.value = true
    debugLog('start()')
    try { recognition.start() } catch {}
  } else {
    voiceShouldRun.value = false
    debugLog('stop()')
    try { recognition.stop() } catch {}
  }

}
function applyVoiceText(key, text) {
  const t = String(text || '').trim()
  if (!t) return

  // array fields
  if (['addresses', 'contacts', 'tel', 'fax', 'emails'].includes(key)) {
    form[key].push(t)
    showAlert('success', `已加入：${t}`)
    return
  }

  // numeric fields
  if (key === 'credit' || key === 'commission') {
    const num = Number(String(t).replace(/[^\d.]/g, ''))
    if (!Number.isFinite(num)) return
    form[key] = num
    return
  }

  // normal text fields
  if (key in form) form[key] = t
}

function initVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    showToast('error', '此瀏覽器不支援語音辨識', 1500)
    return
  }

  recognition = new SpeechRecognition()
  recognition.lang = 'zh-TW'
  recognition.continuous = true
  recognition.interimResults = false
  // ✅ 全事件 debug（一定要有）
  recognition.onaudiostart = () => console.log('[voice] onaudiostart')
  recognition.onaudioend   = () => console.log('[voice] onaudioend')
  recognition.onsoundstart = () => console.log('[voice] onsoundstart')
  recognition.onsoundend   = () => console.log('[voice] onsoundend')
  recognition.onspeechstart= () => console.log('[voice] onspeechstart')
  recognition.onspeechend  = () => console.log('[voice] onspeechend')
  recognition.onnomatch    = (e) => console.log('[voice] onnomatch', e)

  recognition.onstart = () => {
    debugLog('onstart')
    isListening.value = true
    showToast('info', '語音辨識輸入中.....', 900)
  }

  function norm(s) {
    return String(s || '')
      .toLowerCase()
      .replace(/[\s\u3000]/g, '')        // 半形/全形空白都拿掉
      .replace(/[，,。．.！!？?\-—_]/g, '') // 常見標點拿掉
  }

  recognition.onresult = (e) => {

    if (typeof focusByVoiceKey !== 'function') {
      showToast('error', 'focusByVoiceKey missing', 1500)
      return
    }
    if (typeof applyVoiceText !== 'function') {
      showToast('error', 'applyVoiceText missing', 1500)
      return
    }

    const raw = e.results[e.results.length - 1][0].transcript || ''
    const text = raw.trim()
    const ntext = norm(text)
    debugLog('onresult raw=', raw)

    // ✅ 讓「長字先匹配」，避免短字搶先命中
    const entries = Object.entries(VOICE_FIELD_MAP)
      .map(([k, v]) => [norm(k), k, v])               // [normKey, originalKey, field]
      .sort((a, b) => b[0].length - a[0].length)

    // 1) 說欄位名稱 -> focus
    for (const [nk, originalKey, field] of entries) {
      if (!nk) continue
      if (ntext.includes(nk)) {
        console.log('[voice] match key:', originalKey, '=> field:', field)

        // ✅ 有些瀏覽器對非使用者手勢 focus 比較龜毛，丟到下一個 tick 更穩
        setTimeout(() => {
          const ok = focusByVoiceKey(field)
          if (ok) {
            activeInput.value = field
            showToast('info', `已切換欄位：${originalKey}`, 900)
          } else {
            console.warn('[voice] focus failed for field:', field)
          }
        }, 0)
        return
      }
    }

    // 2) 沒有匹配到欄位名稱 -> 當成內容輸入到目前欄位
    if (activeInput.value) {
      applyVoiceText(activeInput.value, text.replace(/[。．]/g, ''))
      showToast('success', '已輸入', 600)
    } else {
      showToast('info', '請先說欄位名稱（例如：公司名稱、地址、電話…）', 1200)
    }
  }

  recognition.onerror = (e) => {
    const err = e?.error || 'unknown'
    debugLog(`onerror: ${err}`)

    // ✅ 一出錯就停止，避免 error/end/restart 迴圈
    voiceShouldRun.value = false
    try { recognition.stop() } catch {}

    isListening.value = false

    // 依錯誤顯示一次訊息（不要一直跳）
    if (err === 'not-allowed' || err === 'service-not-allowed') {
      showToast('error', '語音被拒：請確認 Chrome 麥克風權限 / 系統麥克風 / 重新整理後再試', 2000)
      return
    }
    if (err === 'no-speech') {
      showToast('info', '沒有聽到聲音，請再按一次🎤重試', 1600)
      return
    }
    if (err === 'audio-capture') {
      showToast('error', '找不到麥克風或被其他程式占用', 2000)
      return
    }

    showToast('error', `語音錯誤：${err}`, 1800)
  }

  recognition.onend = () => {
    debugLog('onend')
    isListening.value = false

    // ✅ 先不要自動重啟（否則一旦錯誤就會一直跳）
    // if (voiceShouldRun.value) { ... }  ← 先整段拿掉/註解
  }
}

/* =========================
   API helpers
========================= */
async function apiGet(url) {
  const resp = await apiFetch(url, { method: 'GET' })
  const data = await resp.json().catch(() => ({}))
  if (!resp.ok || data?.ok === false) {
    throw new Error(data?.msg || `GET 失敗 (${resp.status})`)
  }
  return data
}

async function loadOptionsByKey(key, extraParams = {}) {
  const qs = new URLSearchParams({ key, ...extraParams }).toString()
  const data = await apiGet(`${API_BASE}/form/customer_create/options?${qs}`)
  return data.data || []
}

async function initOptions() {
  // 小工具：避免某個 options key 出錯就整個 initOptions 爆掉
  const safeLoad = async (key, fallback = []) => {
    try {
      const res = await loadOptionsByKey(key)
      return Array.isArray(res) ? res : fallback
    } catch (e) {
      console.warn(`[initOptions] loadOptionsByKey("${key}") failed`, e)
      return fallback
    }
  }

  // 1) 載入 options（平行化，避免每支 API 依序卡住）
  const [
    no1,
    country,
    headerquarter,
    Class2,
    items,
    payment,
    sales_reps,
  ] = await Promise.all([
    safeLoad('no1'),
    safeLoad('country'),
    safeLoad('headerquarter'),
    safeLoad('Class2'),
    safeLoad('items'),
    safeLoad('payment'),
    safeLoad('sales_reps'),
  ])

  options.no1 = no1
  options.country = country
  options.headerquarter = headerquarter
  options.Class2 = Class2
  options.items = items
  options.payment = payment
  options.sales_reps = sales_reps

  // 2) pending 套用：一定要在 sales_reps options ready 之後
  if (
    pendingSalesReps.value &&
    Array.isArray(options.sales_reps) &&
    options.sales_reps.length
  ) {
    applySalesRepsFromCustomer({ sales_reps: pendingSalesReps.value })
    pendingSalesReps.value = null
  }

  // 3) 最終保險：把 form.sales_reps 統一成「合法 value 字串陣列」
  if (
    Array.isArray(form.sales_reps) &&
    Array.isArray(options.sales_reps) &&
    options.sales_reps.length
  ) {
    const labelToValue = new Map(
      options.sales_reps
        .map(o => [
          String(o.label ?? '').trim(),
          String(o.value ?? '').trim(),
        ])
        .filter(([label, value]) => label && value)
    )

    const valueSet = new Set(
      options.sales_reps
        .map(o => String(o.value ?? '').trim())
        .filter(Boolean)
    )

    const tokens = form.sales_reps
      .flatMap(x => String(x ?? '').split(/[,\n、;；]+/g))
      .map(s => s.trim())
      .filter(Boolean)

    const normalized = tokens
      .map(x => {
        // 直接是 value
        if (valueSet.has(x)) return x
        // 用 label 換成 value
        const v = labelToValue.get(x)
        return v && valueSet.has(v) ? v : null
      })
      .filter(Boolean)

    form.sales_reps = Array.from(new Set(normalized))
  }

  // 4) debug 放最後（多印 unknown 會更好抓）
  const formVals = (form.sales_reps || []).map(String)
  const optionVals = (options.sales_reps || []).map(o => String(o.value))

  const unknown =
    Array.isArray(form.sales_reps) && Array.isArray(options.sales_reps)
      ? formVals.filter(v => !optionVals.includes(v))
      : []

  console.log(
    '[sales reps check]',
    'form.sales_reps=', formVals,
    'options.len=', (options.sales_reps || []).length,
    'unknown=', unknown,
    'sampleMatched=', (options.sales_reps || []).slice(0, 5).map(o => ({
      value: String(o.value),
      checked: formVals.includes(String(o.value)),
      label: o.label,
    }))
  )
}

async function onChangeNo1() {
  form.no2 = ''
  form.refno = ''
  options.no2 = []
  if (!form.no1) return
  options.no2 = await loadOptionsByKey('no2', { no1: form.no1 })
  await refreshRefno()
}

async function onChangeNo2() {
  form.refno = ''
  await refreshRefno()
}

async function refreshRefno() {
  if (!form.no1 || isEditMode.value) return
  const qs = new URLSearchParams({ no1: form.no1 })
  if (form.no2) qs.set('no2', form.no2)
  const data = await apiGet(`${API_BASE}/customer/refno/preview?${qs}`)
  form.refno = data.refno || data.data?.refno || ''
}

async function applyItacLabDefault({ refresh = true } = {}) {
  if (!itacLabMode.value || isEditMode.value) return
  const labId = defaultLabCategory.value?.id
  if (!labId) return
  form.no1 = labId
  form.no2 = ''
  options.no2 = []
  if (refresh) {
    await refreshRefno()
  }
}

/* =========================
   Reset / Save
========================= */
async function resetForm() {
  if (saving.value) return
  Object.assign(form, {
    no1: '',
    no2: '',
    refno: '',
    company: '',
    short: '',
    country: '',
    headerquarter: '',
    url: '',
    ceo: '',
    Class2: '',
    items: '',
    employee: '',
    quit: false,
    secret: false,
    LicenceNo: '',
    payment: '',
    credit: 0,
    commission: 0,
    remarks: '',
    addresses: [],
    contacts: [],
    tel: [],
    fax: [],
    emails: [],
    sales_reps: [],
  })
  options.no2 = []
  repKeyword.value = ''
  await applyItacLabDefault()
  showAlert('info', '已清空')
}

function firstNonEmpty(arr) {
  if (!Array.isArray(arr)) return ''
  return arr.map(x => String(x ?? '').trim()).find(x => x.length > 0) || ''
}

function commitPendingMultiInputs() {
  ;[addressesRef.value, contactsRef.value, telRef.value, faxRef.value, emailsRef.value].forEach(card => {
    try {
      card?.commitDraft?.()
    } catch {}
  })
}

async function save() {
  alert.show = false
  commitPendingMultiInputs()

  if (itacLabMode.value && !form.no1) {
    await applyItacLabDefault({ refresh: false })
  }
  if (!form.no1) return showAlert('error', '必填：分類（第一層）')
  if (!String(form.company ?? '').trim()) return showAlert('error', '必填：公司名稱')
  if (!String(form.short ?? '').trim()) return showAlert('error', '必填：公司簡稱')
  if (!firstNonEmpty(form.addresses)) return showAlert('error', '必填：地址（至少輸入 1 筆）')
  if (!firstNonEmpty(form.contacts)) return showAlert('error', '必填：聯絡人（至少輸入 1 筆）')
  if (!Array.isArray(form.sales_reps) || form.sales_reps.length === 0) return showAlert('error', '必填：業務代表（至少選 1 位）')

  // ✅ 用 URL query 的 refno 判斷是否為編輯模式（你 router 已統一用 query refno）
  const routeRefno = String(editRefno?.value || refno?.value || '').trim()

  // ✅ 編輯模式下：如果 form.refno 被清空，強制用 routeRefno 補回來，避免被當新增
  if (isEditMode.value && !String(form.refno ?? '').trim()) {
    form.refno = routeRefno
  }

  // ✅ 新增模式：沒有 refno 才去產生
  if (!isEditMode.value && !String(form.refno ?? '').trim()) {
    try {
      await refreshRefno()
    } catch (e) {
      return showAlert('error', `客戶代號產生失敗：${String(e?.message || e)}`)
    }
    if (!String(form.refno ?? '').trim()) return showAlert('error', '必填：客戶代號（請先選擇分類以產生代號）')
  }

  saving.value = true
  try {
    const payload = {
      no1: form.no1,
      no2: form.no2,
      refno: form.refno,
      company: form.company,
      short: form.short,
      country: form.country,
      headerquarter: form.headerquarter,
      url: form.url,
      ceo: form.ceo,
      Class2: form.Class2,
      items: form.items,
      employee: form.employee,
      quit: form.quit ? 'Y' : 'N',
      secret: form.secret ? 1 : 0,
      LicenceNo: form.LicenceNo,
      payment: form.payment,
      credit: form.credit,
      commission: form.commission,
      remarks: form.remarks,
      addresses: form.addresses,
      contacts: form.contacts,
      tel: form.tel,
      fax: form.fax,
      emails: form.emails,
      sales_reps: form.sales_reps,
    }

    const resp = await apiFetch(`${API_BASE}/form/customer_create/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    const data = await resp.json().catch(() => ({}))
    if (!resp.ok || data?.ok === false) {
      throw new Error(data?.msg || `儲存失敗 (${resp.status})`)
    }

    const savedRefno = String(data.refno || form.refno || '').trim()
    showAlert('success', `儲存成功\n客戶代號：${savedRefno}`)

    // ✅ 如果原本是新增（網址沒有 refno），儲存成功後把網址切到編輯模式（避免下一次又新增一筆）
    if (!isEditMode.value && savedRefno) {
      // 你用的是 query refno（router 已統一）
      router.replace({ name: 'customer_create', query: { refno: savedRefno } })
    }
  } catch (e) {
    showAlert('error', String(e?.message || e))
  } finally {
    saving.value = false
  }
}
/* =========================
   Lifecycle
========================= */
const ctx = ref(null)
async function loadContext() {
  const data = await apiGet(`${API_BASE}/customer/meta`)
  ctx.value = data.data || data
}

function hydrateOptionsFromContext() {
  const meta = ctx.value || {}
  itacLabMode.value = Boolean(meta.itac_lab_mode)
  defaultLabCategory.value = meta.default_lab_category || null
  options.no1 = Array.isArray(meta.cate_level1)
    ? meta.cate_level1.map(x => ({
        value: x?.id ?? '',
        label: String(x?.name ?? '').trim(),
      })).filter(x => x.value !== '' && x.label)
    : []
  options.country = Array.isArray(meta.countries) ? [...meta.countries] : []
  options.headerquarter = Array.isArray(meta.headerquarter) ? [...meta.headerquarter] : []
  options.Class2 = Array.isArray(meta.class2) ? [...meta.class2] : []
  options.items = Array.isArray(meta.items) ? [...meta.items] : []
  options.payment = Array.isArray(meta.payments) ? [...meta.payments] : []
  options.sales_reps = Array.isArray(meta.staff) ? [...meta.staff] : []

  if (
    pendingSalesReps.value &&
    Array.isArray(options.sales_reps) &&
    options.sales_reps.length
  ) {
    applySalesRepsFromCustomer({ sales_reps: pendingSalesReps.value })
    pendingSalesReps.value = null
  }

  if (
    Array.isArray(form.sales_reps) &&
    Array.isArray(options.sales_reps) &&
    options.sales_reps.length
  ) {
    const labelToValue = new Map(
      options.sales_reps
        .map(o => [
          String(o.label ?? '').trim(),
          String(o.value ?? '').trim(),
        ])
        .filter(([label, value]) => label && value)
    )

    const valueSet = new Set(
      options.sales_reps
        .map(o => String(o.value ?? '').trim())
        .filter(Boolean)
    )

    const tokens = form.sales_reps
      .flatMap(x => String(x ?? '').split(/[,\n、;；]+/g))
      .map(s => s.trim())
      .filter(Boolean)

    const normalized = tokens
      .map(x => {
        if (valueSet.has(x)) return x
        const v = labelToValue.get(x)
        return v && valueSet.has(v) ? v : null
      })
      .filter(Boolean)

    form.sales_reps = Array.from(new Set(normalized))
  }
}

async function deleteCurrent() {
  const currentRefno = String(editRefno.value || form.refno || '').trim()
  if (!currentRefno) return
  if (!window.confirm(`確定要刪除客戶 ${currentRefno} ?`)) return

  saving.value = true
  try {
    const resp = await apiFetch(`${API_BASE}/form/customer_create/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refno: currentRefno }),
    })
    const data = await resp.json().catch(() => ({}))
    if (!resp.ok || data?.ok === false) {
      throw new Error(data?.msg || `刪除失敗 (${resp.status})`)
    }
    showAlert('success', `刪除成功\n客戶代號：${currentRefno}`)
    router.replace({ name: 'customer_del' })
  } catch (e) {
    showAlert('error', String(e?.message || e))
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await loadContext()
    hydrateOptionsFromContext()

    // ✅ 編輯模式：只在這裡載入一次
    const key = editRefno.value || refno.value
    if (key) {
      await loadCustomer(key)
    } else {
      await applyItacLabDefault()
    }
  } catch (e) {
    showAlert('error', String(e?.message || e))
  } finally {
    loading.value = false
  }
})


onUnmounted(() => {
  try { recognition?.stop?.() } catch {}
})
</script>

<style>
/* ===== Sales reps list items (fixed layout, no Tailwind clash) ===== */
.rep-item{
  display:flex;
  align-items:center;
  gap:12px;
  padding:12px;
  border-bottom:1px solid #f1f5f9; /* slate-100 */
  cursor:pointer;
}
.rep-item:last-child{ border-bottom:0; }
.rep-item:hover{ background:#f8fafc; } /* slate-50 */

.rep-checkbox{
  width:20px;
  height:20px;
  flex:0 0 20px;
  margin:0;
  accent-color:#2563eb;
}

.rep-text{
  font-size:14px;
  color:#0f172a; /* slate-900 */
  line-height:1.2;
  flex:1;
  min-width:0;
  word-break:break-word;
}

/* ===== Flags checkboxes (locked style, not radio) ===== */
.chk-grid{
  display:grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap:12px;
}
.chk-card{
  display:flex;
  align-items:center;
  gap:10px;
  padding:12px;
  border:1px solid #e2e8f0;   /* slate-200 */
  border-radius:12px;
  background:#fff;
  line-height:1;
  user-select:none;
  box-sizing:border-box;
}
.chk{
  -webkit-appearance:none;
  appearance:none;
  width:20px;
  height:20px;
  flex:0 0 20px;
  border-radius:6px;
  border:1px solid #cbd5e1;   /* slate-300 */
  background:#fff;
  display:inline-grid;
  place-items:center;
  margin:0;
  padding:0;
  box-sizing:border-box;
  vertical-align:middle;
  cursor:pointer;
}
.chk:checked{
  background:#334155;         /* slate-700 */
  border-color:#334155;
}
.chk:checked::after{
  content:"✓";
  color:#fff;
  font-size:14px;
  line-height:1;
}
.chk:focus{
  outline:none;
  box-shadow:0 0 0 3px rgba(148,163,184,.45); /* slate-400/45% */
}
.chk-text{
  font-size:14px;
  font-weight:600;
  color:#0f172a;
  line-height:1;
}
</style>
