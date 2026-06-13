<template>
  <section class="mt-4 bg-white rounded-2xl border border-slate-200 p-4">
    <div class="text-sm font-semibold text-slate-900">{{ title }}</div>

    <!-- Bootstrap-like input group (borderless input) -->
<div class="mt-3">
  <!-- 外框：唯一邊框 -->
  <div class="input-group-outer">
    <input
      ref="inputEl"
      class="input-group-field"
      :placeholder="placeholder"
      v-model="v"
      :inputmode="inputmode"
      :data-voice="voiceKey || null"
      @keydown="onKeydown"
    />

    <button
      type="button"
      class="input-group-btn"
      @click="add"
    >
      +
    </button>
  </div>
</div>

    <div v-if="list.length" class="mt-3 flex flex-wrap gap-2">
      <span
        v-for="(item, i) in list"
        :key="i"
        class="inline-flex items-center gap-2 px-3 py-2 rounded-full bg-slate-100 text-slate-800 text-sm"
      >
        <span class="break-all">{{ item }}</span>
        <button
          type="button"
          class="h-6 w-6 rounded-full bg-white border border-slate-200 text-slate-700 active:scale-[0.98]"
          @click="removeAt(i)"
          aria-label="remove"
          title="移除"
        >
          ×
        </button>
      </span>
    </div>
  </section>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'

const inputEl = ref(null)

function focus() {
  nextTick(() => {
    inputEl.value?.focus()
  })
}

const props = defineProps({
  title: { type: String, required: true },

  // ✅ 放寬型別，避免 String/null 進來就 warning / 爆炸
  modelValue: { type: [Array, String], default: () => [] },

  placeholder: { type: String, default: '新增…' },
  inputmode: { type: String, default: 'text' },
  voiceKey: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const v = ref('')

// ✅ 永遠把 modelValue 正規化成 Array
const list = computed(() => {
  const mv = props.modelValue
  if (Array.isArray(mv)) return mv
  if (mv == null) return []
  const s = String(mv).trim()
  return s ? [s] : []
})

function add() {
  const s = String(v.value || '').trim()
  if (!s) return
  emit('update:modelValue', [...list.value, s])
  v.value = ''
}

function commitDraft() {
  add()
}

function getDraft() {
  return String(v.value || '').trim()
}

function removeAt(i) {
  const arr = list.value.slice()
  arr.splice(i, 1)
  emit('update:modelValue', arr)
}

function onKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    add()
  }
}

defineExpose({ focus, commitDraft, getDraft })
</script>

<style scoped>
/* 外層：唯一邊框 */
.input-group-outer{
  display:flex;
  align-items:stretch;
  width:100%;
  height:48px;                 /* = h-12 */
  border:1px solid #e2e8f0;    /* slate-200 */
  border-radius:12px;          /* rounded-xl */
  background:#fff;
  overflow:hidden;             /* 讓內部不可能溢出變成「第二個框」視覺 */
}

/* input：強制「無框、無陰影、貼滿」 */
.input-group-field{
  display:block !important;
  flex:1 1 auto !important;
  width:100% !important;
  height:100% !important;

  margin:0 !important;
  padding:0 16px !important;

  border:0 !important;               /* ✅ 清框線 */
  outline:0 !important;
  box-shadow:none !important;        /* ✅ 清 inset/外陰影 */
  background:transparent !important;

  -webkit-appearance:none !important; /* ✅ 清 Safari/Chrome 原生樣式 */
  appearance:none !important;

  line-height:1 !important;          /* ✅ 避免文字偏下 */
}

/* focus 時也絕不出框 */
.input-group-field:focus{
  border:0 !important;
  outline:0 !important;
  box-shadow:none !important;
}

/* 右側按鈕 */
.input-group-btn{
  flex:0 0 48px;               /* 固定寬度 */
  width:48px;
  height:100%;

  border:0;
  background:#777777;
  color:#fff;

  font-size:18px;
  font-weight:700;
  cursor:pointer;

  display:flex;
  align-items:center;
  justify-content:center;

  transition:transform .08s ease, background .15s ease;
}
.input-group-btn:hover{ background:#666666; }
.input-group-btn:active{ transform:scale(.96); }
</style>

