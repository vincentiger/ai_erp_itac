// C:\ai_erp\frontend\src\composables\useLabMech.js

import { reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  fetchLabMechTemplate,
  judgeLabMechTest,
  createLabMechReport,
  getLabMechReport,
  updateLabMechReport,
  exportLabMechDocx,
  downloadLabMechDocx,
} from '@/utils/labMech'

import {
  fetchLabMechTemplates,
  getLabMechTemplate,
  createReportFromTemplate,
} from '@/utils/labMechTemplate'

import {
  calcAverage,
  roundHardnessValue,
  formatAvg,
  judgeHardnessSection,
  judgeNumericSection,
  judgeOkNgSection,
  judgeDecarbSection,
  judgeSaltSprayData,
  judgeHydrogenSection,
  getOverallSummary,
} from '@/composables/useLabMechJudge'

function makeHardnessRows(n = 8) {
  return Array.from({ length: n }, (_, i) => ({
    sample_no: i + 1,
    values: ['', '', ''],
    avg_value: '',
    judge_value: '',
    result: '',
    is_out_of_spec: false,
    remark: '',
  }))
}

function makeNumericRows(n = 10) {
  return Array.from({ length: n }, (_, i) => ({
    sample_no: i + 1,
    value: '',
    avg_value: '',
    judge_value: '',
    result: '',
    is_out_of_spec: false,
    remark: '',
  }))
}

function makeOkNgRows(n = 10) {
  return Array.from({ length: n }, (_, i) => ({
    sample_no: i + 1,
    status: '',
    result: '',
    is_out_of_spec: false,
    remark: '',
  }))
}

function makeHydrogenRows(n = 10) {
  return Array.from({ length: n }, (_, i) => ({
    sample_no: i + 1,
    tighten_at: '',
    remove_at: '',
    status: '',
    result: '',
  }))
}

function makeDecarbRows(n = 5) {
  return Array.from({ length: n }, (_, i) => ({
    sample_no: i + 1,
    hv1: '',
    hv2: '',
    hv3: '',
    hv2_ok: true,
    hv3_ok: true,
    result: '',
  }))
}

function resizeRows(rows = [], count = 0, rowFactory = makeNumericRows) {
  const n = Math.max(0, Math.floor(Number(count) || 0))
  const next = Array.isArray(rows) ? rows.slice(0, n) : []
  const fresh = rowFactory(n)
  while (next.length < n) {
    next.push(fresh[next.length])
  }
  return next.map((row, idx) => ({ ...row, sample_no: idx + 1 }))
}

function defaultSpecTextFor(key) {
  if (key === 'core_hardness') return '四捨六入，五成雙'
  if (key === 'ductility') return '螺絲頭部與桿徑交接處不可發生斷裂'
  return ''
}

function normalizeSpecText(key, value) {
  const text = String(value ?? '').trim()
  if (key === 'ductility' && (!text || text === 'OK / NG')) return defaultSpecTextFor(key)
  return text || defaultSpecTextFor(key)
}

function buildInitialState() {
  return {
    loading: false,
    saving: false,
    exporting: false,
    reportId: null,

    header: {
      report_no: '',
      entrust_no: '',
      product_name: '',
      spec_desc: '',
      lot_no: '',
      lot_qty: null,
      plating: '',
      material: '',
      manufacturer: '',
      standard_type: '',
      standard_desc: '',
      env_temp: null,
      env_humidity: null,
      test_date: '',
      complete_date: '',
      tester: '',
      reviewer: '',
      remarks: '',
    },

    core_hardness: {
      test_code: 'core_hardness',
      test_name: '心部硬度',
      method_code: '',
      inspection_method: '',
      unit: 'HRC',
      sample_count: 8,
      spec_min: '',
      spec_max: '',
      spec_text: '四捨六入，五成雙',
      judge_mode: 'numeric_range',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 10,
      rows: makeHardnessRows(8),
    },

    surface_hardness: {
      test_code: 'surface_hardness',
      test_name: '表面硬度',
      method_code: '',
      inspection_method: '',
      unit: 'HRC',
      sample_count: 8,
      spec_min: '',
      spec_max: '',
      spec_text: '',
      judge_mode: 'numeric_range',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 20,
      rows: makeHardnessRows(8),
    },

    carburizing_depth: {
      test_code: 'carburizing_depth',
      test_name: '滲碳層測試',
      method_code: '',
      unit: 'HV/mm',
      sample_count: 3,
      spec_min: '',
      spec_max: '',
      spec_text: '',
      judge_mode: 'numeric_range',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 30,
      rows: makeNumericRows(3),
    },

    decarb: {
      test_code: 'decarb',
      test_name: '脫碳層測試',
      method_code: '',
      unit: 'HV',
      sample_count: 5,
      spec_min: '',
      spec_max: '',
      spec_text: 'HV2 ≥ HV1 - 30 且 HV3 ≤ HV1 + 30',
      judge_mode: 'decarb',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 40,
      rows: Array.from({ length: 5 }, (_, i) => ({
        sample_no: i + 1,
        hv1: '',
        hv2: '',
        hv3: '',
        hv2_ok: true,
        hv3_ok: true,
        result: '',
      })),
    },

    ductility: {
      test_code: 'ductility',
      test_name: '延展性測試',
      method_code: '',
      unit: '',
      sample_count: 10,
      spec_min: '',
      spec_max: '',
      spec_text: defaultSpecTextFor('ductility'),
      judge_mode: 'ok_ng',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 50,
      rows: makeOkNgRows(10),
    },

    hydrogen: {
      test_code: 'hydrogen',
      test_name: '氫脆測試',
      method_code: '',
      unit: '',
      sample_count: 10,
      spec_min: '',
      spec_max: '',
      spec_text: 'Tighter torque / No failures after hrs.',
      judge_mode: 'hydrogen',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 60,
      data: {
        plate_thickness: '',
        hole_diameter: '',
        plate_hardness: '',
        tighter_torque: '',
        no_failures_after_hours: '',
        test_hours: 24,
        sample_count: 10,
      },
      rows: makeHydrogenRows(10),
    },

    drilling_speed: {
      test_code: 'drilling_speed',
      test_name: '攻速測試',
      method_code: '',
      unit: 'sec',
      sample_count: 10,
      spec_min: '',
      spec_max: '',
      spec_text: '',
      judge_mode: 'numeric_range',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 70,
      rows: makeNumericRows(10),
      data: {
        plate_thickness: '',
        plate_hardness: '',
        test_time_sec: '',
      },
    },

    torque: {
      test_code: 'torque',
      test_name: '扭力測試',
      method_code: '',
      unit: 'kg/cm',
      sample_count: 10,
      spec_min: '',
      spec_max: '',
      spec_text: '',
      judge_mode: 'numeric_range',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 80,
      rows: makeNumericRows(10),
      data: {},
    },

    salt_spray: {
      test_code: 'salt_spray',
      test_name: '鹽霧測試',
      method_code: '',
      unit: 'H',
      sample_count: 0,
      spec_min: '',
      spec_max: '',
      spec_text: '',
      judge_mode: 'salt_spray',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 90,
      data: {
        spec_rust_type: 'white',
        spec_hours: '',
        white_spec_hours: '',
        red_spec_hours: '',
        start_at: '',
        end_at: '',
        actual_hours: '',
        no_rust_pcs: 0,
        white_rust_pcs: 0,
        red_rust_pcs: 0,
        result: '',
        angle_ok: true,
      },
      rows: [],
    },

    coating_thickness: {
      test_code: 'coating_thickness',
      test_name: '膜厚測試',
      method_code: 'ASTM B568',
      unit: 'μm',
      sample_count: 10,
      spec_min: '',
      spec_max: '',
      spec_text: '',
      judge_mode: 'numeric_range',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 100,
      rows: makeNumericRows(10),
      data: {},
    },

    drive_torque: {
      test_code: 'drive_torque',
      test_name: '旋入試驗-扭力',
      method_code: '',
      unit: 'kg/cm',
      sample_count: 10,
      spec_min: '',
      spec_max: '',
      spec_text: '',
      judge_mode: 'numeric_range',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 110,
      rows: makeNumericRows(10),
      data: {},
    },

    drive_performance: {
      test_code: 'drive_performance',
      test_name: '旋入性能',
      method_code: '',
      unit: '',
      sample_count: 10,
      spec_min: '',
      spec_max: '',
      spec_text: 'OK / NG',
      judge_mode: 'ok_ng',
      instrument_no: '',
      pass_count: 0,
      fail_count: 0,
      result: '',
      sort_no: 120,
      rows: makeOkNgRows(10),
      data: {},
    },
  }
}

export function useLabMech() {
  const state = reactive(buildInitialState())

  const templateState = reactive({
    loading: false,
    keyword: '',
    list: [],
    selectedId: null,
  })

  const testSections = computed(() => ([
    state.core_hardness,
    state.surface_hardness,
    state.carburizing_depth,
    state.decarb,
    state.ductility,
    state.hydrogen,
    state.drilling_speed,
    state.torque,
    state.salt_spray,
    state.coating_thickness,
    state.drive_torque,
    state.drive_performance,
  ]))

  const overallSummary = computed(() => getOverallSummary(testSections.value))

  function failClass(flag) {
    return flag ? 'text-red-600 font-bold' : ''
  }

  function rowFailByResult(row) {
    return row?.result === 'FAIL' || row?.status === 'NG' || row?.is_out_of_spec === true
  }

  function updateHardnessPreview(section) {
    ;(section.rows || []).forEach((row) => {
      const avg = calcAverage(row.values || [])
      const judgeValue = roundHardnessValue(avg, section.spec_text)

      row.avg_value = avg === null ? '' : formatAvg(avg)
      row.judge_value = judgeValue ?? ''
    })
  }

  function parseSaltSpraySpecText(text = '') {
    const out = { white_spec_hours: '', red_spec_hours: '' }
    String(text || '').split(/[;；,\n]+/).forEach(part => {
      const [rawKey, rawValue] = String(part || '').split(':')
      const key = String(rawKey || '').trim().toLowerCase()
      const value = String(rawValue || '').trim()
      if (!value) return
      if (key === 'white' || key === '白鏽') out.white_spec_hours = value
      if (key === 'red' || key === '紅鏽') out.red_spec_hours = value
    })
    return out
  }

  async function loadTemplate() {
    state.loading = true
    try {
      const r = await fetchLabMechTemplate()
      return r
    } catch (e) {
      return { ok: false, msg: e.message }
    } finally {
      state.loading = false
    }
  }

  function applySummary(section, summary) {
    section.pass_count = summary?.pass_count || 0
    section.fail_count = summary?.fail_count || 0
    section.result = summary?.result || ''
  }

  function applyTemplateToState(template) {
    if (!template) return

    state.reportId = null

    Object.assign(state.header, {
      report_no: '',
      entrust_no: '',
      product_name: template.product_name || '',
      spec_desc: template.spec_desc || '',
      lot_no: '',
      lot_qty: null,
      plating: template.plating || '',
      material: template.material || '',
      manufacturer: '',
      standard_type: template.standard_type || '',
      standard_desc: template.standard_desc || '',
      env_temp: null,
      env_humidity: null,
      test_date: '',
      complete_date: '',
      tester: '',
      reviewer: '',
      remarks: template.remarks || '',
    })

    for (const section of testSections.value) {
      section.pass_count = 0
      section.fail_count = 0
      section.result = ''
    }

    for (const item of (template.items || [])) {
      const key = item.test_code
      if (!state[key]) continue

      const target = state[key]
      Object.assign(target, {
        method_code: item.method_code || '',
        inspection_method: item.inspection_method || '',
        unit: item.unit || '',
        sample_count: item.sample_count,
        spec_min: item.spec_min,
        spec_max: item.spec_max,
        spec_text: normalizeSpecText(key, item.spec_text),
        judge_mode: item.judge_mode,
        instrument_no: item.instrument_no || '',
        pass_count: 0,
        fail_count: 0,
        result: '',
        sort_no: item.sort_no || 0,
      })

      if (item.data) {
        target.data = JSON.parse(JSON.stringify(item.data))
      }
      if (item.rows) {
        target.rows = JSON.parse(JSON.stringify(item.rows))
      }
    }

    updateHardnessPreview(state.core_hardness)
    updateHardnessPreview(state.surface_hardness)
  }

  async function loadTemplateList(keyword = '') {
    templateState.loading = true
    try {
      const r = await fetchLabMechTemplates(keyword)
      templateState.list = r.templates || []
      return r
    } catch (e) {
      ElMessage.error(e.message || '讀取模板清單失敗')
      return { ok: false, msg: e.message }
    } finally {
      templateState.loading = false
    }
  }

  async function loadTemplateDetail(templateId) {
    try {
      const r = await getLabMechTemplate(templateId)
      if (!r.ok) throw new Error(r.msg || '讀取模板失敗')
      applyTemplateToState(r.template)
      return r
    } catch (e) {
      ElMessage.error(e.message || '讀取模板失敗')
      return { ok: false, msg: e.message }
    }
  }

  async function createNewReportFromTemplate(templateId) {
    try {
      const r = await createReportFromTemplate(templateId, {
        header: {
          product_name: state.header.product_name,
          spec_desc: state.header.spec_desc,
          plating: state.header.plating,
          material: state.header.material,
          standard_type: state.header.standard_type,
          standard_desc: state.header.standard_desc,
        },
      })

      if (!r.ok) throw new Error(r.msg || '由模板建立報告失敗')

      state.reportId = r.report_id
      ElMessage.success(`已由模板建立新報告，報告ID：${r.report_id}`)
      return r
    } catch (e) {
      ElMessage.error(e.message || '由模板建立報告失敗')
      return { ok: false, msg: e.message }
    }
  }

  async function judgeSection(sectionKey) {
    try {
      const section = state[sectionKey]
      if (!section) return { ok: false, msg: 'section not found' }

      if (sectionKey === 'decarb') {
        const local = judgeDecarbSection(section)
        section.rows = local.rows
        applySummary(section, local.summary)

        try {
          const r = await judgeLabMechTest({
            test_code: section.test_code,
            rows: section.rows,
          })
          if (r.ok) {
            section.rows = r.rows || section.rows
            applySummary(section, r.summary || local.summary)
          }
        } catch (_) {}

        return { ok: true }
      }

      if (sectionKey === 'salt_spray') {
        const localData = judgeSaltSprayData(section.data)
        section.data = localData
        section.result = localData.result || ''
        section.pass_count = Number(localData.pass_count || 0)
        section.fail_count = Number(localData.fail_count || 0)

        try {
          const r = await judgeLabMechTest({
            test_code: section.test_code,
            ...section.data,
          })
          if (r.ok && r.data) {
            section.data = r.data
            section.result = section.data.result || ''
            section.pass_count = Number(section.data.pass_count || section.data.no_rust_pcs || 0)
            section.fail_count = Number(
              section.data.fail_count ||
              (Number(section.data.white_rust_pcs || 0) + Number(section.data.red_rust_pcs || 0))
            )
          }
        } catch (_) {}

        return { ok: true }
      }

      if (sectionKey === 'hydrogen') {
        const local = judgeHydrogenSection(section)
        section.rows = section.rows.map((row, idx) => ({ ...row, ...(local.rows[idx] || {}) }))
        applySummary(section, local.summary)

        try {
          const r = await judgeLabMechTest({
            test_code: section.test_code,
            rows: section.rows.map(x => ({
              sample_no: x.sample_no,
              tighten_at: x.tighten_at,
              remove_at: x.remove_at,
              status: x.status,
            })),
          })
          if (r.ok) {
            section.rows = section.rows.map((row, idx) => ({ ...row, ...(r.rows?.[idx] || {}) }))
            applySummary(section, r.summary || local.summary)
          }
        } catch (_) {}

        return { ok: true }
      }

      if (section.judge_mode === 'numeric_range') {
        if (section.test_code === 'core_hardness' || section.test_code === 'surface_hardness') {
          const local = judgeHardnessSection(section)
          section.rows = local.rows
          applySummary(section, local.summary)
        } else {
          const local = judgeNumericSection(section)
          section.rows = local.rows
          applySummary(section, local.summary)
        }

        try {
          const r = await judgeLabMechTest({
            test_code: section.test_code,
            spec_min: section.spec_min,
            spec_max: section.spec_max,
            rounding_mode: section.spec_text,
            rows: section.rows,
          })
          if (r.ok) {
            section.rows = r.rows || section.rows
            applySummary(section, r.summary)
          }
        } catch (_) {}

        return { ok: true }
      }

      if (section.judge_mode === 'ok_ng') {
        const local = judgeOkNgSection(section)
        section.rows = local.rows
        applySummary(section, local.summary)

        try {
          const r = await judgeLabMechTest({
            test_code: section.test_code,
            rows: section.rows,
          })
          if (r.ok) {
            section.rows = r.rows || section.rows
            applySummary(section, r.summary || local.summary)
          }
        } catch (_) {}

        return { ok: true }
      }

      return { ok: false, msg: 'unsupported section' }
    } catch (e) {
      ElMessage.error(e.message || '判定失敗')
      return { ok: false, msg: e.message }
    }
  }

  async function judgeAll() {
    for (const key of [
      'core_hardness',
      'surface_hardness',
      'carburizing_depth',
      'decarb',
      'ductility',
      'hydrogen',
      'drilling_speed',
      'torque',
      'salt_spray',
      'coating_thickness',
      'drive_torque',
      'drive_performance',
    ]) {
      await judgeSection(key)
    }
    ElMessage.success('全部判定完成')
  }

  function buildPayload() {
    return {
      header: { ...state.header },
      items: testSections.value.map(section => {
        const base = {
          test_code: section.test_code,
          test_name: section.test_name,
          method_code: section.method_code,
          inspection_method: section.inspection_method || '',
          unit: section.unit,
          sample_count: section.sample_count,
          spec_min: section.spec_min,
          spec_max: section.spec_max,
          spec_text: section.spec_text,
          judge_mode: section.judge_mode,
          instrument_no: section.instrument_no,
          pass_count: section.pass_count,
          fail_count: section.fail_count,
          result: section.result,
          sort_no: section.sort_no,
        }

        if (section.judge_mode === 'salt_spray') {
          const whiteHours = String(section.data?.white_spec_hours ?? '').trim()
          const redHours = String(section.data?.red_spec_hours ?? '').trim()
          const maxSpecHours = Math.max(
            ...[section.data?.spec_hours, whiteHours, redHours]
              .map(value => String(value ?? '').trim())
              .filter(value => value !== '')
              .map(value => Number(value))
              .filter(value => Number.isFinite(value))
          )
          return {
            ...base,
            spec_text: [
              whiteHours ? `white:${whiteHours}` : '',
              redHours ? `red:${redHours}` : '',
            ].filter(Boolean).join(';') || base.spec_text,
            data: {
              ...section.data,
              spec_rust_type: whiteHours && redHours ? 'both' : whiteHours ? 'white' : redHours ? 'red' : section.data?.spec_rust_type,
              spec_hours: Number.isFinite(maxSpecHours) ? maxSpecHours : (section.data?.spec_hours || whiteHours || redHours || ''),
            },
            rows: []
          }
        }

        if (section.judge_mode === 'hydrogen') {
          return {
            ...base,
            data: { ...section.data },
            rows: section.rows.map(x => ({ ...x })),
          }
        }

        return {
          ...base,
          data: section.data ? { ...section.data } : null,
          rows: section.rows.map(x => ({ ...x })),
        }
      }),
    }
  }

  async function saveReport() {
    state.saving = true
    try {
      const payload = buildPayload()
      let r

      if (state.reportId) {
        r = await updateLabMechReport(state.reportId, payload)
      } else {
        r = await createLabMechReport(payload)
      }

      if (!r.ok) throw new Error(r.msg || '儲存失敗')

      state.reportId = r.report_id || state.reportId
      ElMessage.success(`儲存成功，報告ID：${state.reportId}`)
      return r
    } catch (e) {
      ElMessage.error(e.message || '儲存失敗')
      return { ok: false, msg: e.message }
    } finally {
      state.saving = false
    }
  }

  async function loadReport(reportIdArg = null) {
    try {
      let reportId = reportIdArg

      if (!reportId) {
        const { value } = await ElMessageBox.prompt('請輸入報告 ID', '載入報告', {
          confirmButtonText: '載入',
          cancelButtonText: '取消',
          inputPattern: /^\d+$/,
          inputErrorMessage: '請輸入數字 ID',
        })
        reportId = value
      }

      state.loading = true
      const r = await getLabMechReport(reportId)
      if (!r.ok) throw new Error(r.msg || '載入失敗')

      const report = r.report || {}
      state.reportId = report.id

      Object.assign(state.header, {
        report_no: report.report_no || '',
        entrust_no: report.entrust_no || '',
        product_name: report.product_name || '',
        spec_desc: report.spec_desc || '',
        lot_no: report.lot_no || '',
        lot_qty: report.lot_qty,
        plating: report.plating || '',
        material: report.material || '',
        manufacturer: report.manufacturer || '',
        standard_type: report.standard_type || '',
        standard_desc: report.standard_desc || '',
        env_temp: report.env_temp,
        env_humidity: report.env_humidity,
        test_date: report.test_date || '',
        complete_date: report.complete_date || '',
        tester: report.tester || '',
        reviewer: report.reviewer || '',
        remarks: report.remarks || '',
      })

      for (const item of (report.items || [])) {
        const key = item.test_code
        if (!state[key]) continue

        const target = state[key]
        Object.assign(target, {
          method_code: item.method_code || '',
          inspection_method: item.inspection_method || '',
          unit: item.unit || '',
          sample_count: item.sample_count,
          spec_min: item.spec_min,
          spec_max: item.spec_max,
          spec_text: normalizeSpecText(key, item.spec_text),
          judge_mode: item.judge_mode,
          instrument_no: item.instrument_no || '',
          pass_count: item.pass_count || 0,
          fail_count: item.fail_count || 0,
          result: item.result || '',
          sort_no: item.sort_no || 0,
        })

        if (item.data) target.data = { ...(target.data || {}), ...item.data }
        if (key === 'salt_spray') {
          target.data = {
            ...(target.data || {}),
            ...parseSaltSpraySpecText(item.spec_text),
          }
        }
        if (item.rows) target.rows = JSON.parse(JSON.stringify(item.rows))
      }

      updateHardnessPreview(state.core_hardness)
      updateHardnessPreview(state.surface_hardness)

      ElMessage.success(`已載入報告 ${state.reportId}`)
      return r
    } catch (e) {
      if (e !== 'cancel' && e !== 'close') {
        ElMessage.error(e.message || '載入失敗')
      }
      return { ok: false, msg: e?.message || 'cancelled' }
    } finally {
      state.loading = false
    }
  }

  async function exportDocx() {
    if (!state.reportId) {
      ElMessage.warning('請先儲存報告')
      return { ok: false, msg: 'report not saved' }
    }

    state.exporting = true
    try {
      const r = await exportLabMechDocx(state.reportId)
      if (!r.ok) throw new Error(r.msg || '匯出失敗')
      downloadLabMechDocx(r.export_id)
      return r
    } catch (e) {
      ElMessage.error(e.message || '匯出失敗')
      return { ok: false, msg: e.message }
    } finally {
      state.exporting = false
    }
  }

  function resetForm() {
    const fresh = buildInitialState()
    Object.assign(state, fresh)
    updateHardnessPreview(state.core_hardness)
    updateHardnessPreview(state.surface_hardness)

    templateState.keyword = ''
    templateState.list = []
    templateState.selectedId = null
  }

  function syncSectionRowsToCount(sectionKey) {
    const section = state[sectionKey]
    if (!section) return
    const count = Number(section.sample_count || section.data?.sample_count || 0)
    if (sectionKey === 'core_hardness' || sectionKey === 'surface_hardness') {
      section.rows = resizeRows(section.rows, count, makeHardnessRows)
      updateHardnessPreview(section)
      return
    }
    if (section.judge_mode === 'numeric_range') {
      section.rows = resizeRows(section.rows, count, makeNumericRows)
      return
    }
    if (section.judge_mode === 'ok_ng') {
      section.rows = resizeRows(section.rows, count, makeOkNgRows)
      return
    }
    if (section.judge_mode === 'decarb') {
      section.rows = resizeRows(section.rows, count, makeDecarbRows)
      return
    }
    if (section.judge_mode === 'hydrogen') {
      section.rows = resizeRows(section.rows, count, makeHydrogenRows)
    }
  }

  watch(
    () => [
      state.core_hardness.spec_text,
      state.core_hardness.rows.map(r => [...(r.values || [])]),
    ],
    () => updateHardnessPreview(state.core_hardness),
    { deep: true }
  )

  watch(
    () => state.surface_hardness.rows.map(r => [...(r.values || [])]),
    () => updateHardnessPreview(state.surface_hardness),
    { deep: true }
  )

  watch(
    () => [
      state.salt_spray.data.start_at,
      state.salt_spray.data.spec_hours,
      state.salt_spray.data.white_spec_hours,
      state.salt_spray.data.red_spec_hours,
    ],
    () => {
      const d = judgeSaltSprayData(state.salt_spray.data)
      state.salt_spray.data.end_at = d.end_at
    },
    { deep: true }
  )

  onMounted(() => {
    updateHardnessPreview(state.core_hardness)
    updateHardnessPreview(state.surface_hardness)
  })

  return {
    state,
    testSections,
    overallSummary,

    templateState,
    loadTemplateList,
    loadTemplateDetail,
    createNewReportFromTemplate,

    failClass,
    rowFailByResult,

    loadTemplate,
    loadReport,
    saveReport,
    exportDocx,
    resetForm,

    judgeSection,
    judgeAll,

    buildPayload,
    updateHardnessPreview,
    syncSectionRowsToCount,
  }
}
