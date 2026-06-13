<template>
  <div
    class="lab-page"
    :class="{
      'is-standard-mode': isStandardMode,
      'is-entry-mode': !isStandardMode,
    }"
  >
    <!-- HEADER -->
    <header class="lab-header">
      <div class="lab-shell">
        <div class="lab-toolbar">
          <div class="lab-toolbar-actions">
            <el-button plain @click="openSourceDialog">選擇委託單</el-button>
            <el-button v-if="isStandardMode" type="primary" plain @click="openTemplatePicker">
              新建設定
            </el-button>
            <el-button @click="openReportDialog" :loading="state.loading">載入報告</el-button>
            <el-button plain @click="openManagePage">查修</el-button>
            <el-button v-if="isStandardMode" @click="handleResetForm">重設</el-button>
            <el-button v-if="!isStandardMode" @click="showDuplicate = true">複製成新報告</el-button>
            <el-button v-if="!isStandardMode" @click="judgeAll">全部判定</el-button>
            <el-button v-if="!isStandardMode" type="success" @click="exportDocx" :loading="state.exporting">匯出 DOCX</el-button>
            <el-button plain @click="openEquipmentExcel">設備 Excel</el-button>
            <el-button type="info" @click="showGuide = true">使用說明</el-button>
          </div>
        </div>
      </div>
    </header>

    <!-- MAIN -->
    <main class="lab-main">
      <div class="lab-shell lab-scroll-area">
        <el-card shadow="never" class="mb-4">
          <template #header>
            <div class="flex items-center justify-between gap-3">
              <div class="font-semibold">來源委託單</div>
              <el-button size="small" plain @click="openSourceDialog">搜尋 / 更換</el-button>
            </div>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">委託單編號</div>
              <div class="font-semibold mt-1">{{ sourceState.labNo || '-' }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">客戶</div>
              <div class="font-semibold mt-1">{{ sourceState.customerName || '-' }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">日期</div>
              <div class="font-semibold mt-1">{{ sourceState.filledDate || '-' }}</div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm mt-3">
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">聯絡人</div>
              <div class="font-semibold mt-1">{{ sourceState.contactName || '-' }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">電話</div>
              <div class="font-semibold mt-1">{{ sourceState.contactTel || '-' }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">E-mail</div>
              <div class="font-semibold mt-1 break-all">{{ sourceState.contactEmail || '-' }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">地址</div>
              <div class="font-semibold mt-1">{{ sourceState.address || '-' }}</div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm mt-3">
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">品名</div>
              <div class="font-semibold mt-1">{{ sourceState.sampleDesc || '-' }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">規格</div>
              <div class="font-semibold mt-1">{{ sourceState.sampleSpec || '-' }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">材質編號</div>
              <div class="font-semibold mt-1">{{ sourceState.materialNo || '-' }}</div>
            </div>
            <div class="rounded-lg border p-3">
              <div class="text-gray-500">批號</div>
              <div class="font-semibold mt-1">{{ sourceState.lotNo || '-' }}</div>
            </div>
          </div>
        </el-card>

        <!-- 基本資料 -->
        <el-card shadow="never" class="mb-4">
          <template #header>
            <div class="font-semibold">基本資料</div>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
            <el-input v-model="state.header.report_no" placeholder="委託編號 / 報告編號" />
            <el-input v-model="state.header.entrust_no" placeholder="委託單號" />
            <el-input v-model="state.header.product_name" placeholder="品名" />
            <el-input v-model="state.header.spec_desc" placeholder="規格" />

            <el-input v-model="state.header.lot_no" placeholder="批號" />
            <el-input-number v-model="state.header.lot_qty" :min="0" class="w-full" placeholder="批量" />
            <el-input v-model="state.header.plating" placeholder="鍍別" />
            <el-input v-model="state.header.material" placeholder="材質" />

            <el-input v-model="state.header.manufacturer" placeholder="製造廠商" />
            <el-select v-model="state.header.standard_type" placeholder="依據標準類型">
              <el-option label="圖號" value="drawing" />
              <el-option label="法規" value="regulation" />
            </el-select>
            <el-input v-model="state.header.standard_desc" placeholder="圖號 / 法規標準" />
            <el-select
              v-model="mechTesterSelection"
              multiple
              filterable
              allow-create
              default-first-option
              class="w-full entry-editable-input"
              placeholder="可輸入多位測試人員"
            />

            <el-input v-model="state.header.reviewer" placeholder="覆核人員" />
            <el-input-number v-model="state.header.env_temp" :step="0.1" class="w-full" placeholder="溫度 ℃" />
            <el-input-number v-model="state.header.env_humidity" :step="0.1" class="w-full" placeholder="濕度 %RH" />
            <el-date-picker
              v-model="state.header.test_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="測試日期"
            />

            <el-date-picker
              v-model="state.header.complete_date"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="完成日期"
            />
          </div>

          <div class="mt-3">
            <el-input
              v-model="state.header.remarks"
              type="textarea"
              :rows="3"
              placeholder="備註"
            />
          </div>
        </el-card>

        <!-- 心部硬度 -->
        <el-card shadow="never" class="mb-4">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="font-semibold">一．心部硬度</div>
              <el-button v-if="!isStandardMode" @click="judgeSection('core_hardness')">自動判定</el-button>
            </div>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-7 gap-3 mb-2">
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.core_hardness.method_code"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="試驗方法"
                class="flex-1"
                @change="onSharedOptionSelected('method_code', $event)"
              >
                <el-option
                  v-for="o in methodOptions"
                  :key="`method-core-${o.value}`"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'core_hardness')">+</el-button>
            </div>
            <el-select
              v-model="state.core_hardness.inspection_method"
              filterable
              allow-create
              default-first-option
              clearable
              placeholder="檢測方式"
              class="w-full"
              @change="onSharedOptionSelected('inspection_method', $event)"
            >
              <el-option
                v-for="o in hardnessInspectionMethodOptions"
                :key="`inspection-core-${o.value}`"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
            <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('inspection_method', 'core_hardness')">+</el-button>
            <el-input v-model="state.core_hardness.spec_min" placeholder="下限" />
            <el-input v-model="state.core_hardness.spec_max" placeholder="上限" />
            <el-input-number
              v-model="state.core_hardness.sample_count"
              :min="1"
              :controls="false"
              class="w-full entry-editable-input"
              placeholder="檢測數 PCS"
              @change="syncSectionRowsToCount('core_hardness')"
            />
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.core_hardness.unit"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="測試單位"
                class="flex-1"
                @change="onSharedOptionSelected('unit', $event)"
              >
                <el-option v-for="o in unitOptions" :key="`unit-core-${o.value}`" :label="o.label" :value="o.value" />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('unit', 'core_hardness')">+</el-button>
            </div>
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.core_hardness.instrument_no"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="儀器編號"
                class="flex-1"
                @change="onSharedOptionSelected('instrument_no', $event)"
              >
                <el-option
                  v-for="o in instrumentOptions"
                  :key="`instrument-core-${o.value}`"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'core_hardness')">+</el-button>
            </div>
            <el-select
              v-model="state.core_hardness.spec_text"
              placeholder="取位方式"
              class="w-full"
            >
              <el-option label="四捨六入，五成雙" value="四捨六入，五成雙" />
              <el-option label="四捨五入" value="四捨五入" />
            </el-select>
          </div>

          <div class="mb-3 text-xs text-gray-500">
            判定規則：{{ state.core_hardness.spec_text || '四捨六入，五成雙' }}。
            <span v-if="state.core_hardness.spec_text === '四捨五入'">例：24.5→25、25.5→26</span>
            <span v-else>例：24.5→24、25.5→26</span>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full border-collapse text-sm">
              <thead>
                <tr class="bg-gray-50">
                  <th class="border p-2">試片</th>
                  <th class="border p-2">值1</th>
                  <th class="border p-2">值2</th>
                  <th class="border p-2">值3</th>
                  <th class="border p-2">平均值</th>
                  <th class="border p-2">判定值</th>
                  <th class="border p-2">結果</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in state.core_hardness.rows" :key="`core-${row.sample_no}`">
                  <td class="border p-2 text-center">{{ row.sample_no }}</td>
                  <td class="border p-1"><el-input v-model="row.values[0]" class="test-value-input" /></td>
                  <td class="border p-1"><el-input v-model="row.values[1]" class="test-value-input" /></td>
                  <td class="border p-1"><el-input v-model="row.values[2]" class="test-value-input" /></td>
                  <td class="border p-2" :class="failClass(row.is_out_of_spec)">{{ row.avg_value }}</td>
                  <td class="border p-2" :class="failClass(row.is_out_of_spec)">{{ row.judge_value }}</td>
                  <td class="border p-2" :class="failClass(row.is_out_of_spec)">{{ row.result }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mt-3 text-sm">
            合格：{{ state.core_hardness.pass_count }}｜
            不合格：{{ state.core_hardness.fail_count }}｜
            結果：
            <span :class="failClass(state.core_hardness.result === 'FAIL')">
              {{ state.core_hardness.result }}
            </span>
          </div>
        </el-card>

        <!-- 表面硬度 -->
        <el-card shadow="never" class="mb-4">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="font-semibold">二．表面硬度</div>
              <el-button v-if="!isStandardMode" @click="judgeSection('surface_hardness')">自動判定</el-button>
            </div>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-7 gap-3 mb-2">
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.surface_hardness.method_code"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="試驗方法"
                class="flex-1"
                @change="onSharedOptionSelected('method_code', $event)"
              >
                <el-option
                  v-for="o in methodOptions"
                  :key="`method-surface-${o.value}`"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'surface_hardness')">+</el-button>
            </div>
            <el-select
              v-model="state.surface_hardness.inspection_method"
              filterable
              allow-create
              default-first-option
              clearable
              placeholder="檢測方式"
              class="w-full"
              @change="onSharedOptionSelected('inspection_method', $event)"
            >
              <el-option
                v-for="o in hardnessInspectionMethodOptions"
                :key="`inspection-surface-${o.value}`"
                :label="o.label"
                :value="o.value"
              />
            </el-select>
            <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('inspection_method', 'surface_hardness')">+</el-button>
            <el-input v-model="state.surface_hardness.spec_min" placeholder="下限" />
            <el-input v-model="state.surface_hardness.spec_max" placeholder="上限" />
            <el-input-number
              v-model="state.surface_hardness.sample_count"
              :min="1"
              :controls="false"
              class="w-full entry-editable-input"
              placeholder="檢測數 PCS"
              @change="syncSectionRowsToCount('surface_hardness')"
            />
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.surface_hardness.unit"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="測試單位"
                class="flex-1"
                @change="onSharedOptionSelected('unit', $event)"
              >
                <el-option v-for="o in unitOptions" :key="`unit-surface-${o.value}`" :label="o.label" :value="o.value" />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('unit', 'surface_hardness')">+</el-button>
            </div>
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.surface_hardness.instrument_no"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="儀器編號"
                class="flex-1"
                @change="onSharedOptionSelected('instrument_no', $event)"
              >
                <el-option
                  v-for="o in instrumentOptions"
                  :key="`instrument-surface-${o.value}`"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'surface_hardness')">+</el-button>
            </div>
            <el-input v-model="state.surface_hardness.spec_text" placeholder="規格說明" />
          </div>

          <div class="overflow-x-auto">
            <table class="w-full border-collapse text-sm">
              <thead>
                <tr class="bg-gray-50">
                  <th class="border p-2">試片</th>
                  <th class="border p-2">值1</th>
                  <th class="border p-2">值2</th>
                  <th class="border p-2">值3</th>
                  <th class="border p-2">平均值</th>
                  <th class="border p-2">判定值</th>
                  <th class="border p-2">結果</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in state.surface_hardness.rows" :key="`surface-${row.sample_no}`">
                  <td class="border p-2 text-center">{{ row.sample_no }}</td>
                  <td class="border p-1"><el-input v-model="row.values[0]" class="test-value-input" /></td>
                  <td class="border p-1"><el-input v-model="row.values[1]" class="test-value-input" /></td>
                  <td class="border p-1"><el-input v-model="row.values[2]" class="test-value-input" /></td>
                  <td class="border p-2" :class="failClass(row.is_out_of_spec)">{{ row.avg_value }}</td>
                  <td class="border p-2" :class="failClass(row.is_out_of_spec)">{{ row.judge_value }}</td>
                  <td class="border p-2" :class="failClass(row.is_out_of_spec)">{{ row.result }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mt-3 text-sm">
            合格：{{ state.surface_hardness.pass_count }}｜
            不合格：{{ state.surface_hardness.fail_count }}｜
            結果：
            <span :class="failClass(state.surface_hardness.result === 'FAIL')">
              {{ state.surface_hardness.result }}
            </span>
          </div>
        </el-card>

        <!-- 滲碳層 -->
        <el-card shadow="never" class="mb-4">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="font-semibold">三．滲碳層測試</div>
              <el-button v-if="!isStandardMode" @click="judgeSection('carburizing_depth')">自動判定</el-button>
            </div>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-5 gap-3 mb-3">
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.carburizing_depth.method_code"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="試驗方法"
                class="flex-1"
                @change="onSharedOptionSelected('method_code', $event)"
              >
                <el-option
                  v-for="o in methodOptions"
                  :key="`method-carb-${o.value}`"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'carburizing_depth')">+</el-button>
            </div>
            <el-input v-model="state.carburizing_depth.spec_min" placeholder="下限" />
            <el-input v-model="state.carburizing_depth.spec_max" placeholder="上限" />
            <el-input-number v-model="state.carburizing_depth.sample_count" :min="0" :controls="false" class="w-full entry-editable-input" placeholder="檢測數 PCS" @change="syncSectionRowsToCount('carburizing_depth')" />
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.carburizing_depth.unit"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="測試單位"
                class="flex-1"
                @change="onSharedOptionSelected('unit', $event)"
              >
                <el-option v-for="o in unitOptions" :key="`unit-carb-${o.value}`" :label="o.label" :value="o.value" />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('unit', 'carburizing_depth')">+</el-button>
            </div>
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.carburizing_depth.instrument_no"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="儀器編號"
                class="flex-1"
                @change="onSharedOptionSelected('instrument_no', $event)"
              >
                <el-option
                  v-for="o in instrumentOptions"
                  :key="`instrument-carb-${o.value}`"
                  :label="o.label"
                  :value="o.value"
                />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'carburizing_depth')">+</el-button>
            </div>
          </div>

          <div class="space-y-2">
            <div
              v-for="row in state.carburizing_depth.rows"
              :key="`carb-${row.sample_no}`"
              class="grid grid-cols-4 gap-2 items-center"
            >
              <div>{{ row.sample_no }}</div>
              <el-input v-model="row.value" class="test-value-input" />
              <div :class="failClass(rowFailByResult(row))">{{ row.result }}</div>
              <div></div>
            </div>
          </div>
          <div class="mt-3 text-sm">
            合格：{{ state.carburizing_depth.pass_count }}｜
            不合格：{{ state.carburizing_depth.fail_count }}｜
            結果：
            <span :class="failClass(state.carburizing_depth.result === 'FAIL')">
              {{ state.carburizing_depth.result }}
            </span>
          </div>
        </el-card>

        <!-- 脫碳層 / 鹽霧 -->
        <el-row :gutter="16" class="mb-4">
          <el-col :xs="24" :lg="12">
            <el-card shadow="never" class="h-full">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="font-semibold">四．脫碳層測試</div>
                  <el-button v-if="!isStandardMode" @click="judgeSection('decarb')">自動判定</el-button>
                </div>
              </template>

              <div class="grid grid-cols-1 md:grid-cols-5 gap-3 mb-3">
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.decarb.method_code"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="試驗方法"
                    class="flex-1"
                    @change="onSharedOptionSelected('method_code', $event)"
                  >
                    <el-option v-for="o in methodOptions" :key="`method-decarb-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'decarb')">+</el-button>
                </div>
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.decarb.unit"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="測試單位"
                    class="flex-1"
                    @change="onSharedOptionSelected('unit', $event)"
                  >
                    <el-option v-for="o in unitOptions" :key="`unit-decarb-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('unit', 'decarb')">+</el-button>
                </div>
                <el-input-number v-model="state.decarb.sample_count" :min="0" :controls="false" class="w-full entry-editable-input" placeholder="檢測數" @change="syncSectionRowsToCount('decarb')" />
                <el-input v-model="state.decarb.spec_text" placeholder="標準值" />
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.decarb.instrument_no"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="儀器編號"
                    class="flex-1"
                    @change="onSharedOptionSelected('instrument_no', $event)"
                  >
                    <el-option v-for="o in instrumentOptions" :key="`instrument-decarb-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'decarb')">+</el-button>
                </div>
              </div>

              <div class="mb-3 text-sm text-gray-500">
                判定公式：HV2 ≥ HV1 - 30 且 HV3 ≤ HV1 + 30
              </div>

              <div class="overflow-x-auto">
                <table class="w-full border-collapse text-sm">
                  <thead>
                    <tr class="bg-gray-50">
                      <th class="border p-2">試片</th>
                      <th class="border p-2">HV1</th>
                      <th class="border p-2">HV2</th>
                      <th class="border p-2">HV3</th>
                      <th class="border p-2">結果</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in state.decarb.rows" :key="`decarb-${row.sample_no}`">
                      <td class="border p-2 text-center">{{ row.sample_no }}</td>
                      <td class="border p-1"><el-input v-model="row.hv1" class="test-value-input" /></td>
                      <td class="border p-1" :class="failClass(row.hv2_ok === false)">
                        <el-input v-model="row.hv2" class="test-value-input" />
                      </td>
                      <td class="border p-1" :class="failClass(row.hv3_ok === false)">
                        <el-input v-model="row.hv3" class="test-value-input" />
                      </td>
                      <td class="border p-2" :class="failClass(row.result === 'FAIL')">{{ row.result }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="mt-3 text-sm">
                合格：{{ state.decarb.pass_count }}｜
                不合格：{{ state.decarb.fail_count }}｜
                結果：
                <span :class="failClass(state.decarb.result === 'FAIL')">
                  {{ state.decarb.result }}
                </span>
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :lg="12">
            <el-card shadow="never" class="h-full">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="font-semibold">五．鹽霧測試</div>
                  <el-button v-if="!isStandardMode" @click="judgeSection('salt_spray')">自動判定</el-button>
                </div>
              </template>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.salt_spray.method_code"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="試驗方法"
                    class="flex-1"
                    @change="onSharedOptionSelected('method_code', $event)"
                  >
                    <el-option v-for="o in methodOptions" :key="`method-salt-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'salt_spray')">+</el-button>
                </div>

                <el-input-number v-model="state.salt_spray.sample_count" :min="0" :controls="false" class="w-full entry-editable-input" placeholder="檢測數 PCS" />

                <el-input v-model="state.salt_spray.data.white_spec_hours" placeholder="白鏽標準時數(H)" />

                <el-input v-model="state.salt_spray.data.red_spec_hours" placeholder="紅鏽標準時數(H)" />

                <el-date-picker
                  v-model="state.salt_spray.data.start_at"
                  type="datetime"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  placeholder="開始時間"
                  class="test-value-input"
                />

                <el-input v-model="state.salt_spray.data.end_at" placeholder="結束時間(系統回填)" readonly class="test-value-input" />

                <el-input v-model="state.salt_spray.data.actual_hours" placeholder="實際時數" class="test-value-input" />

                <el-switch
                  v-model="state.salt_spray.data.angle_ok"
                  active-text="角度符合"
                  inactive-text="角度不符"
                  class="test-value-input"
                />

                <el-input-number
                  v-model="state.salt_spray.data.no_rust_pcs"
                  :min="0"
                  class="w-full"
                  placeholder="無鏽支數"
                  :class="'test-value-input'"
                />

                <el-input-number
                  v-model="state.salt_spray.data.white_rust_pcs"
                  :min="0"
                  class="w-full"
                  placeholder="白鏽支數"
                  :class="'test-value-input'"
                />

                <el-input-number
                  v-model="state.salt_spray.data.red_rust_pcs"
                  :min="0"
                  class="w-full"
                  placeholder="紅鏽支數"
                  :class="'test-value-input'"
                />
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.salt_spray.instrument_no"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="儀器編號"
                    class="flex-1"
                    @change="onSharedOptionSelected('instrument_no', $event)"
                  >
                    <el-option v-for="o in instrumentOptions" :key="`instrument-salt-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'salt_spray')">+</el-button>
                </div>
              </div>

              <div class="mt-4 rounded-lg bg-gray-50 p-3 text-sm">
                <div>開始：{{ state.salt_spray.data.start_at || '-' }}</div>
                <div>結束：{{ state.salt_spray.data.end_at || '-' }}</div>
                <div>
                  標準：白鏽 {{ state.salt_spray.data.white_spec_hours || '-' }} H /
                  紅鏽 {{ state.salt_spray.data.red_spec_hours || '-' }} H
                </div>
                <div>
                  結果：無鏽 {{ state.salt_spray.data.no_rust_pcs || 0 }} /
                  白鏽 {{ state.salt_spray.data.white_rust_pcs || 0 }} /
                  紅鏽 {{ state.salt_spray.data.red_rust_pcs || 0 }}
                </div>
                <div>
                  判定：
                  <span :class="failClass(state.salt_spray.data.result === 'FAIL')">
                    {{ state.salt_spray.data.result || state.salt_spray.result }}
                  </span>
                </div>
                <div>
                  合格：{{ state.salt_spray.pass_count }}｜
                  不合格：{{ state.salt_spray.fail_count }}｜
                  結果：
                  <span :class="failClass(state.salt_spray.result === 'FAIL')">
                    {{ state.salt_spray.result }}
                  </span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 氫脆 -->
        <el-card shadow="never" class="mb-4">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="font-semibold">六．氫脆測試</div>
              <el-button v-if="!isStandardMode" @click="judgeSection('hydrogen')">自動判定</el-button>
            </div>
          </template>

          <div class="grid grid-cols-1 md:grid-cols-5 gap-3 mb-3">
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.hydrogen.method_code"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="試驗方法"
                class="flex-1"
                @change="onSharedOptionSelected('method_code', $event)"
              >
                <el-option v-for="o in methodOptions" :key="`method-hydrogen-${o.value}`" :label="o.label" :value="o.value" />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'hydrogen')">+</el-button>
            </div>
            <el-select v-model="state.hydrogen.data.test_hours" placeholder="測試時間">
              <el-option label="24 小時" :value="24" />
              <el-option label="48 小時" :value="48" />
            </el-select>
            <el-input-number v-model="state.hydrogen.sample_count" :min="0" :controls="false" class="w-full entry-editable-input" placeholder="檢測數 PCS" @change="syncSectionRowsToCount('hydrogen')" />
            <el-input v-model="state.hydrogen.data.plate_thickness" placeholder="板厚" />
            <el-input v-model="state.hydrogen.data.hole_diameter" placeholder="孔徑" />
            <el-input v-model="state.hydrogen.data.plate_hardness" placeholder="板硬度" />
            <el-input v-model="state.hydrogen.data.tighter_torque" placeholder="Tighter torque (kg/cm)" />
            <el-input v-model="state.hydrogen.data.no_failures_after_hours" placeholder="No failures after (hrs)" />
            <el-input v-model="state.hydrogen.spec_text" placeholder="標準值" />
            <div class="flex items-center gap-2">
              <el-select
                v-model="state.hydrogen.instrument_no"
                filterable
                allow-create
                default-first-option
                clearable
                placeholder="儀器編號"
                class="flex-1"
                @change="onSharedOptionSelected('instrument_no', $event)"
              >
                <el-option v-for="o in instrumentOptions" :key="`instrument-hydrogen-${o.value}`" :label="o.label" :value="o.value" />
              </el-select>
              <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'hydrogen')">+</el-button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full border-collapse text-sm">
              <thead>
                <tr class="bg-gray-50">
                  <th class="border p-2">試片</th>
                  <th class="border p-2">旋入時間</th>
                  <th class="border p-2">拆卸時間</th>
                  <th class="border p-2">OK / NG</th>
                  <th class="border p-2">判定</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in state.hydrogen.rows" :key="`hydrogen-${row.sample_no}`">
                  <td class="border p-2 text-center">{{ row.sample_no }}</td>
                  <td class="border p-1">
                    <el-date-picker
                      v-model="row.tighten_at"
                      type="datetime"
                      value-format="YYYY-MM-DD HH:mm:ss"
                      class="test-value-input"
                    />
                  </td>
                  <td class="border p-1">
                    <el-date-picker
                      v-model="row.remove_at"
                      type="datetime"
                      value-format="YYYY-MM-DD HH:mm:ss"
                      class="test-value-input"
                    />
                  </td>
                  <td class="border p-1">
                    <el-select v-model="row.status" placeholder="選擇結果" class="test-value-input">
                      <el-option label="OK" value="OK" />
                      <el-option label="NG" value="NG" />
                    </el-select>
                  </td>
                  <td class="border p-2" :class="failClass(rowFailByResult(row))">
                    {{ row.result }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="mt-3 text-sm">
            合格：{{ state.hydrogen.pass_count }}｜
            不合格：{{ state.hydrogen.fail_count }}｜
            結果：
            <span :class="failClass(state.hydrogen.result === 'FAIL')">
              {{ state.hydrogen.result }}
            </span>
          </div>
        </el-card>

        <!-- 攻速 / 扭力 -->
        <el-row :gutter="16" class="mb-4">
          <el-col :xs="24" :lg="12">
            <el-card shadow="never" class="mb-4">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="font-semibold">七．攻速測試</div>
                  <el-button v-if="!isStandardMode" @click="judgeSection('drilling_speed')">自動判定</el-button>
                </div>
              </template>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.drilling_speed.method_code"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="試驗方法"
                    class="flex-1"
                    @change="onSharedOptionSelected('method_code', $event)"
                  >
                    <el-option v-for="o in methodOptions" :key="`method-drill-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'drilling_speed')">+</el-button>
                </div>
                <el-input v-model="state.drilling_speed.data.plate_thickness" placeholder="鐵板厚度" />
                <el-input v-model="state.drilling_speed.data.plate_hardness" placeholder="鐵板硬度" />
                <el-input v-model="state.drilling_speed.data.test_time_sec" placeholder="測試時間 Sec" />
                <el-input v-model="state.drilling_speed.spec_min" placeholder="下限(可空)" />
                <el-input v-model="state.drilling_speed.spec_max" placeholder="標準值上限" />
                <el-input-number v-model="state.drilling_speed.sample_count" :min="0" :controls="false" class="w-full entry-editable-input" placeholder="檢測數 PCS" @change="syncSectionRowsToCount('drilling_speed')" />
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.drilling_speed.unit"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="測試單位"
                    class="flex-1"
                    @change="onSharedOptionSelected('unit', $event)"
                  >
                    <el-option v-for="o in unitOptions" :key="`unit-drill-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('unit', 'drilling_speed')">+</el-button>
                </div>
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.drilling_speed.instrument_no"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="儀器編號"
                    class="flex-1"
                    @change="onSharedOptionSelected('instrument_no', $event)"
                  >
                    <el-option v-for="o in instrumentOptions" :key="`instrument-drill-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'drilling_speed')">+</el-button>
                </div>
              </div>

              <div class="space-y-2">
                <div
                  v-for="row in state.drilling_speed.rows"
                  :key="`drill-${row.sample_no}`"
                  class="grid grid-cols-4 gap-2 items-center"
                >
                  <div>{{ row.sample_no }}</div>
                  <el-input v-model="row.value" class="test-value-input" />
                  <div :class="failClass(rowFailByResult(row))">{{ row.result }}</div>
                  <div></div>
                </div>
              </div>
              <div class="mt-3 text-sm">
                合格：{{ state.drilling_speed.pass_count }}｜
                不合格：{{ state.drilling_speed.fail_count }}｜
                結果：
                <span :class="failClass(state.drilling_speed.result === 'FAIL')">
                  {{ state.drilling_speed.result }}
                </span>
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :lg="12">
            <el-card shadow="never" class="mb-4">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="font-semibold">八．扭力測試</div>
                  <el-button v-if="!isStandardMode" @click="judgeSection('torque')">自動判定</el-button>
                </div>
              </template>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.torque.method_code"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="試驗方法"
                    class="flex-1"
                    @change="onSharedOptionSelected('method_code', $event)"
                  >
                    <el-option v-for="o in methodOptions" :key="`method-torque-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'torque')">+</el-button>
                </div>
                <el-input-number v-model="state.torque.sample_count" :min="0" :controls="false" class="w-full entry-editable-input" placeholder="檢測數 PCS" @change="syncSectionRowsToCount('torque')" />
                <el-input v-model="state.torque.spec_min" placeholder="下限" />
                <el-input v-model="state.torque.spec_max" placeholder="上限" />
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.torque.unit"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="測試單位"
                    class="flex-1"
                    @change="onSharedOptionSelected('unit', $event)"
                  >
                    <el-option v-for="o in unitOptions" :key="`unit-torque-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('unit', 'torque')">+</el-button>
                </div>
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.torque.instrument_no"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="儀器編號"
                    class="flex-1"
                    @change="onSharedOptionSelected('instrument_no', $event)"
                  >
                    <el-option v-for="o in instrumentOptions" :key="`instrument-torque-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'torque')">+</el-button>
                </div>
              </div>

              <div class="space-y-2">
                <div
                  v-for="row in state.torque.rows"
                  :key="`torque-${row.sample_no}`"
                  class="grid grid-cols-4 gap-2 items-center"
                >
                  <div>{{ row.sample_no }}</div>
                  <el-input v-model="row.value" class="test-value-input" />
                  <div :class="failClass(rowFailByResult(row))">{{ row.result }}</div>
                  <div></div>
                </div>
              </div>
              <div class="mt-3 text-sm">
                合格：{{ state.torque.pass_count }}｜
                不合格：{{ state.torque.fail_count }}｜
                結果：
                <span :class="failClass(state.torque.result === 'FAIL')">
                  {{ state.torque.result }}
                </span>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 膜厚 / 旋入試驗扭力 -->
        <el-row :gutter="16" class="mb-4">
          <el-col :xs="24" :lg="12">
            <el-card shadow="never" class="mb-4">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="font-semibold">十．膜厚測試</div>
                  <el-button v-if="!isStandardMode" @click="judgeSection('coating_thickness')">自動判定</el-button>
                </div>
              </template>

              <div class="mb-3 text-xs text-gray-500">
                目前支援單一膜厚項目；請以此區設定 Cr、Ni 或 Cu 其中一種膜厚的最大/最小與單位。
              </div>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.coating_thickness.method_code"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="測試方法：ASTM B568"
                    class="flex-1"
                    @change="onSharedOptionSelected('method_code', $event)"
                  >
                    <el-option v-for="o in methodOptions" :key="`method-coating-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'coating_thickness')">+</el-button>
                </div>
                <el-input-number v-model="state.coating_thickness.sample_count" :min="0" :controls="false" class="w-full entry-editable-input" placeholder="檢測數 PCS" @change="syncSectionRowsToCount('coating_thickness')" />
                <el-input v-model="state.coating_thickness.spec_min" placeholder="標準值下限" />
                <el-input v-model="state.coating_thickness.spec_max" placeholder="標準值上限" />
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.coating_thickness.unit"
                    filterable
                    clearable
                    placeholder="標準值單位"
                    class="flex-1"
                  >
                    <el-option v-for="o in coatingUnitOptions" :key="`unit-coating-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                </div>
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.coating_thickness.instrument_no"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="儀器編號"
                    class="flex-1"
                    @change="onSharedOptionSelected('instrument_no', $event)"
                  >
                    <el-option v-for="o in instrumentOptions" :key="`instrument-coating-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'coating_thickness')">+</el-button>
                </div>
              </div>

              <div class="space-y-2">
                <div
                  v-for="row in state.coating_thickness.rows"
                  :key="`coat-${row.sample_no}`"
                  class="grid grid-cols-4 gap-2 items-center"
                >
                  <div>{{ row.sample_no }}</div>
                  <el-input v-model="row.value" class="test-value-input" />
                  <div :class="failClass(rowFailByResult(row))">{{ row.result }}</div>
                  <div></div>
                </div>
              </div>
              <div class="mt-3 text-sm">
                合格：{{ state.coating_thickness.pass_count }}｜
                不合格：{{ state.coating_thickness.fail_count }}｜
                結果：
                <span :class="failClass(state.coating_thickness.result === 'FAIL')">
                  {{ state.coating_thickness.result }}
                </span>
              </div>
            </el-card>
          </el-col>

          <el-col :xs="24" :lg="12">
            <el-card shadow="never" class="mb-4">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="font-semibold">十一．旋入試驗 / 旋入扭力</div>
                  <el-button v-if="!isStandardMode" @click="judgeSection('drive_torque')">自動判定</el-button>
                </div>
              </template>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.drive_torque.method_code"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="試驗方法"
                    class="flex-1"
                    @change="onSharedOptionSelected('method_code', $event)"
                  >
                    <el-option v-for="o in methodOptions" :key="`method-drive-torque-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'drive_torque')">+</el-button>
                </div>
                <el-input-number v-model="state.drive_torque.sample_count" :min="0" :controls="false" class="w-full entry-editable-input" placeholder="檢測數 PCS" @change="syncSectionRowsToCount('drive_torque')" />
                <el-input v-model="state.drive_torque.spec_min" placeholder="下限" />
                <el-input v-model="state.drive_torque.spec_max" placeholder="上限" />
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.drive_torque.unit"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="測試單位"
                    class="flex-1"
                    @change="onSharedOptionSelected('unit', $event)"
                  >
                    <el-option v-for="o in unitOptions" :key="`unit-drive-torque-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('unit', 'drive_torque')">+</el-button>
                </div>
                <div class="flex items-center gap-2">
                  <el-select
                    v-model="state.drive_torque.instrument_no"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="儀器編號"
                    class="flex-1"
                    @change="onSharedOptionSelected('instrument_no', $event)"
                  >
                    <el-option v-for="o in instrumentOptions" :key="`instrument-drive-torque-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'drive_torque')">+</el-button>
                </div>
              </div>

              <div class="space-y-2">
                <div
                  v-for="row in state.drive_torque.rows"
                  :key="`drive-torque-${row.sample_no}`"
                  class="grid grid-cols-4 gap-2 items-center"
                >
                  <div>{{ row.sample_no }}</div>
                  <el-input v-model="row.value" class="test-value-input" />
                  <div :class="failClass(rowFailByResult(row))">{{ row.result }}</div>
                  <div></div>
                </div>
              </div>
              <div class="mt-3 text-sm">
                合格：{{ state.drive_torque.pass_count }}｜
                不合格：{{ state.drive_torque.fail_count }}｜
                結果：
                <span :class="failClass(state.drive_torque.result === 'FAIL')">
                  {{ state.drive_torque.result }}
                </span>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 延展性 / 旋入性能 -->
        <el-card shadow="never" class="mb-4">
          <template #header>
            <div class="flex items-center justify-between">
              <div class="font-semibold">延展性測試 / 十一．旋入性能</div>
              <div class="flex gap-2">
                <el-button v-if="!isStandardMode" @click="judgeSection('drive_performance')">判定旋入性能</el-button>
                <el-button v-if="!isStandardMode" @click="judgeSection('ductility')">判定延展性</el-button>
              </div>
            </div>
          </template>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <div class="font-medium mb-2">旋入性能</div>
              <div class="flex items-center gap-2 mb-3">
                <el-select
                  v-model="state.drive_performance.method_code"
                  filterable
                  allow-create
                  default-first-option
                  clearable
                  placeholder="試驗方法"
                  class="flex-1"
                  @change="onSharedOptionSelected('method_code', $event)"
                >
                  <el-option v-for="o in methodOptions" :key="`method-drive-perf-${o.value}`" :label="o.label" :value="o.value" />
                </el-select>
                <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'drive_performance')">+</el-button>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-[160px_1fr] gap-3 mb-3">
                <el-input-number
                  v-model="state.drive_performance.sample_count"
                  :min="0"
                  :controls="false"
                  class="w-full entry-editable-input"
                  placeholder="檢測數 PCS"
                  @change="syncSectionRowsToCount('drive_performance')"
                />
                <el-input
                  v-model="state.drive_performance.spec_text"
                  placeholder="標準值"
                />
                <div class="flex items-center gap-2 md:col-span-2">
                  <el-select
                    v-model="state.drive_performance.instrument_no"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="儀器編號"
                    class="flex-1"
                    @change="onSharedOptionSelected('instrument_no', $event)"
                  >
                    <el-option v-for="o in instrumentOptions" :key="`instrument-drive-perf-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'drive_performance')">+</el-button>
                </div>
              </div>
              <div class="space-y-2">
                <div
                  v-for="row in state.drive_performance.rows"
                  :key="`drive-perf-${row.sample_no}`"
                  class="grid grid-cols-3 gap-2 items-center"
                >
                  <div>{{ row.sample_no }}</div>
                  <el-select v-model="row.status" placeholder="OK / NG" class="test-value-input">
                    <el-option label="OK" value="OK" />
                    <el-option label="NG" value="NG" />
                  </el-select>
                  <div :class="failClass(rowFailByResult(row))">{{ row.result }}</div>
                </div>
              </div>
              <div class="mt-3 text-sm">
                合格：{{ state.drive_performance.pass_count }}｜
                不合格：{{ state.drive_performance.fail_count }}｜
                結果：
                <span :class="failClass(state.drive_performance.result === 'FAIL')">
                  {{ state.drive_performance.result }}
                </span>
              </div>
            </div>

            <div>
              <div class="font-medium mb-2">延展性</div>
              <div class="flex items-center gap-2 mb-3">
                <el-select
                  v-model="state.ductility.method_code"
                  filterable
                  allow-create
                  default-first-option
                  clearable
                  placeholder="試驗方法"
                  class="flex-1"
                  @change="onSharedOptionSelected('method_code', $event)"
                >
                  <el-option v-for="o in methodOptions" :key="`method-ductility-${o.value}`" :label="o.label" :value="o.value" />
                </el-select>
                <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('method_code', 'ductility')">+</el-button>
              </div>
              <div class="grid grid-cols-1 xl:grid-cols-[180px_1fr] gap-3 mb-3 items-center">
                <div class="flex items-center gap-2">
                  <span class="text-sm text-gray-600">檢測數</span>
                  <el-input-number
                    v-model="state.ductility.sample_count"
                    :min="0"
                    :controls="false"
                    class="w-24 entry-editable-input"
                    @change="syncSectionRowsToCount('ductility')"
                  />
                  <span class="text-sm text-gray-600">PCS</span>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-sm text-gray-600">標準值</span>
                  <el-checkbox-group v-model="ductilityAngleSelection" class="flex flex-wrap gap-x-4 gap-y-1">
                    <el-checkbox
                      v-for="angle in ductilityAngleOptions"
                      :key="angle"
                      :label="angle"
                    >
                      {{ angle }}
                    </el-checkbox>
                  </el-checkbox-group>
                  <span class="text-sm text-gray-600">螺絲頭部與桿徑交接處不可發生斷裂</span>
                </div>
                <div class="flex items-center gap-2 xl:col-span-2">
                  <el-select
                    v-model="state.ductility.instrument_no"
                    filterable
                    allow-create
                    default-first-option
                    clearable
                    placeholder="儀器編號"
                    class="flex-1"
                    @change="onSharedOptionSelected('instrument_no', $event)"
                  >
                    <el-option v-for="o in instrumentOptions" :key="`instrument-ductility-${o.value}`" :label="o.label" :value="o.value" />
                  </el-select>
                  <el-button v-if="isStandardMode" plain @click="openSharedOptionEditor('instrument_no', 'ductility')">+</el-button>
                </div>
              </div>
              <div class="space-y-2">
                <div
                  v-for="row in state.ductility.rows"
                  :key="`ductility-${row.sample_no}`"
                  class="grid grid-cols-3 gap-2 items-center"
                >
                  <div>{{ row.sample_no }}</div>
                  <el-select v-model="row.status" placeholder="OK / NG" class="test-value-input">
                    <el-option label="OK" value="OK" />
                    <el-option label="NG" value="NG" />
                  </el-select>
                  <div :class="failClass(rowFailByResult(row))">{{ row.result }}</div>
                </div>
              </div>
              <div class="mt-3 text-sm">
                合格：{{ state.ductility.pass_count }}｜
                不合格：{{ state.ductility.fail_count }}｜
                結果：
                <span :class="failClass(state.ductility.result === 'FAIL')">
                  {{ state.ductility.result }}
                </span>
              </div>
            </div>
          </div>
        </el-card>

        <el-card v-if="!isStandardMode" shadow="never" class="mb-4">
          <template #header>
            <div class="flex items-center justify-between gap-3">
              <div class="font-semibold">上傳圖片</div>
              <div class="text-xs text-gray-500">上傳後會一併放到最終客戶報告最下方</div>
            </div>
          </template>

          <div class="space-y-3">
            <div class="flex flex-wrap items-center gap-2">
              <input
                ref="imageInputRef"
                type="file"
                accept="image/*"
                multiple
                class="hidden"
                @change="handleImageSelected"
              />
              <el-button plain @click="openImagePicker">選擇圖片</el-button>
              <el-button
                type="primary"
                :disabled="!pendingImageFiles.length || !state.reportId"
                :loading="imageState.uploading"
                @click="uploadSelectedImages"
              >
                上傳圖片
              </el-button>
              <div v-if="!state.reportId" class="text-xs text-amber-600">請先儲存報告，再上傳圖片</div>
            </div>

            <div v-if="pendingImageFiles.length" class="rounded-lg border border-dashed p-3">
              <div class="text-sm font-medium mb-2">待上傳</div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="file in pendingImageFiles"
                  :key="`${file.name}-${file.size}`"
                  class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
                >
                  {{ file.name }}
                </span>
              </div>
            </div>

            <div v-if="imageState.images.length" class="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div
                v-for="image in imageState.images"
                :key="image.name"
                class="rounded-lg border p-2 space-y-2"
              >
                <img :src="image.url" :alt="image.name" class="h-32 w-full rounded border bg-slate-50 object-cover" />
                <div class="text-xs break-all text-slate-600">{{ image.name }}</div>
                <div class="flex justify-between items-center gap-2">
                  <a :href="image.url" target="_blank" class="text-xs text-blue-600">檢視</a>
                  <el-button size="small" type="danger" plain @click="removeUploadedImage(image.name)">刪除</el-button>
                </div>
              </div>
            </div>

            <div v-else class="text-sm text-slate-500">目前尚未上傳圖片</div>
          </div>
        </el-card>
      </div>
    </main>

    <!-- FOOTER -->
    <footer class="lab-footer">
      <div class="lab-shell lab-footer-inner">
        <div class="text-sm text-gray-500">
          <span v-if="state.reportId">目前{{ isStandardMode ? '設定' : '報告' }} ID：{{ state.reportId }}</span>
        </div>
        <div class="lab-footer-actions">
          <el-button v-if="!isStandardMode && state.reportId" type="danger" plain @click="deleteReport">刪除</el-button>
          <el-button type="primary" @click="handleSaveReport" :loading="state.saving">
            {{ isStandardMode ? '儲存設定' : '儲存報告' }}
          </el-button>
        </div>
      </div>
    </footer>

    <!-- 使用說明 -->
    <el-dialog v-model="showGuide" title="機械性質試驗紀錄表－使用說明" width="700px">
      <div class="text-sm leading-6 space-y-2">
        <p><b>1. 基本資料</b>：先填寫報告編號、品名、批號、材質、測試人員與測試日期等資訊。</p>
        <p><b>2. 新建報告</b>：可點「新建報告」開啟模板清單，選擇模板後建立一份新的報告。</p>
        <p><b>3. 載入既有報告</b>：點擊「載入報告」後輸入報告 ID，系統會帶入舊有的檢驗紀錄。</p>
        <p><b>4. 複製成新報告</b>：先載入既有檢驗紀錄，再點擊「複製成新報告」，快速另存成一份新的檢驗紀錄。</p>
        <p><b>5. 複製模式</b>：可選擇「只複製模板」或「連同數據一起複製」。只複製模板時會保留規格與方法，但會清空量測值與判定結果。</p>
        <p><b>6. 輸入測試數據</b>：各測試區塊輸入量測值（硬度、扭力、膜厚、鹽霧、氫脆等）。</p>
        <p><b>7. 自動判定</b>：點擊各區塊「自動判定」或上方「全部判定」，系統會依規格自動判定 PASS / FAIL。</p>
        <p><b>8. 異常提示</b>：不符合規格的數據會以紅字顯示，方便 QC 快速檢查。</p>
        <p><b>9. 儲存報告</b>：完成輸入後點擊右下角「儲存報告」。若是複製後的新報告，系統會以新紀錄方式儲存。</p>
        <p><b>10. 匯出報告</b>：點擊「匯出 DOCX」可生成正式檢驗報告文件。</p>
      </div>
    </el-dialog>

    <!-- 複製成新報告 -->
    <el-dialog v-model="showDuplicate" title="複製成新報告" width="560px">
      <div class="space-y-4 text-sm">
        <div class="text-gray-600">
          目前可把已載入的檢驗紀錄另存成一份新的報告。新的報告會清除原本的報告 ID，並在下次按「儲存報告」時建立新紀錄。
        </div>

        <el-radio-group v-model="duplicateMode">
          <el-radio label="template">只複製模板（保留規格 / 方法，清空量測值與判定）</el-radio>
          <el-radio label="full">連同數據一起複製（保留量測值）</el-radio>
        </el-radio-group>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <el-button @click="showDuplicate = false">取消</el-button>
          <el-button type="primary" @click="doDuplicate">確認複製</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 模板選擇 -->
    <el-dialog v-model="showTemplatePicker" title="選擇模板" width="760px">
      <div class="space-y-4">
        <div class="flex gap-2">
          <el-input
            v-model="templateState.keyword"
            placeholder="搜尋模板代碼 / 模板名稱 / 品名 / 規格"
            @keyup.enter="searchTemplates"
          />
          <el-button @click="searchTemplates" :loading="templateState.loading">搜尋</el-button>
        </div>

        <div class="border rounded-md overflow-hidden">
          <div class="max-h-80 overflow-y-auto">
            <table class="w-full text-sm border-collapse">
              <thead>
                <tr class="bg-gray-50">
                  <th class="border p-2 w-12"></th>
                  <th class="border p-2">模板代碼</th>
                  <th class="border p-2">模板名稱</th>
                  <th class="border p-2">品名</th>
                  <th class="border p-2">規格</th>
                  <th class="border p-2">材質</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in templateState.list" :key="row.id">
                  <td class="border p-2 text-center">
                    <el-radio v-model="templateState.selectedId" :label="row.id"> </el-radio>
                  </td>
                  <td class="border p-2">{{ row.template_code }}</td>
                  <td class="border p-2">{{ row.template_name }}</td>
                  <td class="border p-2">{{ row.product_name }}</td>
                  <td class="border p-2">{{ row.spec_desc }}</td>
                  <td class="border p-2">{{ row.material }}</td>
                </tr>
                <tr v-if="!templateState.loading && templateState.list.length === 0">
                  <td class="border p-4 text-center text-gray-400" colspan="6">查無模板資料</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-between items-center">
          <div class="text-xs text-gray-500">
            可先選模板帶入畫面，或直接由模板建立一份新報告
          </div>
          <div class="flex gap-2">
            <el-button @click="showTemplatePicker = false">取消</el-button>
            <el-button @click="useSelectedTemplate">只載入模板</el-button>
            <el-button type="primary" @click="createReportBySelectedTemplate">建立新報告</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

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

    <el-dialog v-model="reportState.dialogVisible" title="載入報告" width="960px">
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <el-input v-model="reportState.searchReportNo" placeholder="報告編號" @keyup.enter="searchReports" />
          <el-input v-model="reportState.searchEntrustNo" placeholder="委託單編號" @keyup.enter="searchReports" />
          <el-input v-model="reportState.searchCustomer" placeholder="客戶名稱" @keyup.enter="searchReports" />
          <el-button :loading="reportState.loading" type="primary" @click="searchReports">搜尋</el-button>
        </div>

        <el-table :data="reportState.results" border height="360">
          <el-table-column prop="report_no" label="報告編號" width="180" />
          <el-table-column prop="entrust_no" label="委託單編號" width="180" />
          <el-table-column prop="customer_name" label="客戶名稱" min-width="180" />
          <el-table-column prop="product_name" label="測試件品名" min-width="180" show-overflow-tooltip />
          <el-table-column prop="test_date" label="日期" width="130" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="selectReport(row.report_id)">載入</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <el-dialog
      v-model="sharedOptionEditor.open"
      :title="sharedOptionEditor.title"
      width="460px"
      destroy-on-close
    >
      <div class="space-y-3">
        <div class="max-h-64 overflow-y-auto rounded-lg border border-slate-200 bg-white">
          <button
            v-for="o in sharedOptionEditor.list"
            :key="`${sharedOptionEditor.key}-${o.value}`"
            type="button"
            class="w-full text-left px-3 py-3 border-b last:border-b-0 border-slate-100 hover:bg-slate-50"
            :class="String(sharedOptionEditor.selected) === String(o.value) ? 'bg-slate-100' : ''"
            @click="pickSharedOption(o)"
          >
            {{ o.label }}
          </button>
          <div v-if="sharedOptionEditor.list.length === 0" class="px-3 py-6 text-sm text-slate-500 text-center">
            目前沒有資料，可直接新增
          </div>
        </div>

        <div class="space-y-2">
          <div v-if="sharedOptionEditor.sectionLabel" class="text-sm text-slate-500">
            目前欄位：{{ sharedOptionEditor.sectionLabel }}
          </div>
          <el-input
            v-model="sharedOptionEditor.input"
            :placeholder="`請輸入${sharedOptionEditor.title}`"
            @keydown.enter.prevent="submitSharedOptionEditor"
          />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <el-button @click="closeSharedOptionEditor">取消</el-button>
          <el-button type="primary" :loading="sharedOptionEditor.saving" @click="submitSharedOptionEditor">
            {{ sharedOptionEditor.selected ? '修改' : '新增' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useLabMech } from '@/composables/useLabMech'
import { apiFetch } from '@/utils/apiFetch'
import { fetchLabMechImages, uploadLabMechImages, deleteLabMechImage } from '@/utils/labMech'

const props = defineProps({
  standardMode: {
    type: Boolean,
    default: false,
  },
})

const isStandardMode = computed(() => !!props.standardMode)
const routeName = computed(() => isStandardMode.value ? 'lab_mech_standard' : 'lab_mech')

const {
  state,
  failClass,
  rowFailByResult,
  loadReport,
  saveReport,
  exportDocx,
  resetForm,
  judgeSection,
  judgeAll,
  templateState,
  loadTemplateList,
  loadTemplateDetail,
  createNewReportFromTemplate,
  syncSectionRowsToCount,
} = useLabMech()
const route = useRoute()
const router = useRouter()

const showGuide = ref(false)
const showDuplicate = ref(false)
const duplicateMode = ref('template')
const showTemplatePicker = ref(false)
const imageInputRef = ref(null)
const pendingImageFiles = ref([])
const methodOptions = ref([
  { label: 'ASTM E18', value: 'ASTM E18' },
  { label: 'ASTM F606', value: 'ASTM F606' },
  { label: 'ASTM F606M', value: 'ASTM F606M' },
  { label: 'ASTM E384', value: 'ASTM E384' },
  { label: 'ASTM E92', value: 'ASTM E92' },
  { label: 'SAE J1237', value: 'SAE J1237' },
  { label: 'SAE J78', value: 'SAE J78' },
  { label: 'SAE J81', value: 'SAE J81' },
  { label: 'SAE J933', value: 'SAE J933' },
  { label: 'ISO 7085', value: 'ISO 7085' },
  { label: 'ASME B18.6.3', value: 'ASME B18.6.3' },
  { label: 'ASME B18.6.4', value: 'ASME B18.6.4' },
  { label: 'ASME B18.6.5M', value: 'ASME B18.6.5M' },
  { label: 'ASME B18.22.1', value: 'ASME B18.22.1' },
  { label: 'FIP 1000', value: 'FIP 1000' },
  { label: 'F.I.P 1000', value: 'F.I.P 1000' },
  { label: 'IFI 504', value: 'IFI 504' },
  { label: 'ASTM B117', value: 'ASTM B117' },
  { label: 'ISO 9227', value: 'ISO 9227' },
  { label: 'ASTM B568', value: 'ASTM B568' },
])
const instrumentOptions = ref([])
const unitOptions = ref([
  { label: 'HRB', value: 'HRB' },
  { label: 'HRC', value: 'HRC' },
  { label: 'HV', value: 'HV' },
  { label: 'HV0.3', value: 'HV0.3' },
  { label: 'HV0.5', value: 'HV0.5' },
  { label: 'HV10', value: 'HV10' },
  { label: 'HV/mm', value: 'HV/mm' },
  { label: 'kg/cm', value: 'kg/cm' },
  { label: 'lb/inch', value: 'lb/inch' },
  { label: 'μm', value: 'μm' },
  { label: 'inch', value: 'inch' },
  { label: 'Sec', value: 'Sec' },
])
const coatingUnitOptions = computed(() => unitOptions.value.filter((o) => ['μm', 'inch'].includes(o.value)))
const hardnessInspectionMethodOptions = ref([
  { label: '洛式', value: '洛式' },
  { label: '微小', value: '微小' },
  { label: '維克氏', value: '維克氏' },
])
const ductilityAngleOptions = ['5°', '7°', '10°']
const ductilitySpecNote = '螺絲頭部與桿徑交接處不可發生斷裂'
const ductilityAngleSelection = computed({
  get() {
    const text = String(state.ductility.spec_text || '')
    return ductilityAngleOptions.filter((angle) => text.includes(angle))
  },
  set(values) {
    const selected = Array.isArray(values) ? values : []
    state.ductility.spec_text = selected.length
      ? `${selected.join(' / ')} (${ductilitySpecNote})`
      : ductilitySpecNote
  },
})
const mechTesterSelection = computed({
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
  },
})
const imageState = reactive({
  loading: false,
  uploading: false,
  images: [],
})
const sharedOptionEditor = reactive({
  open: false,
  key: '',
  title: '',
  list: [],
  selected: '',
  input: '',
  saving: false,
  sectionKey: '',
  sectionLabel: '',
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
  sampleDesc: '',
  sampleSpec: '',
  materialNo: '',
  lotNo: '',
  searchLabNo: '',
  searchCustomer: '',
  searchDate: '',
  results: []
})
const reportState = reactive({
  dialogVisible: false,
  loading: false,
  searchReportNo: '',
  searchEntrustNo: '',
  searchCustomer: '',
  results: [],
})

const sectionKeys = [
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
]

function sharedOptionTitle(key) {
  if (key === 'method_code') return '試驗方法'
  if (key === 'instrument_no') return '儀器編號'
  if (key === 'unit') return '測試單位'
  if (key === 'inspection_method') return '檢測方式'
  return '共用項目'
}

function sharedOptionListByKey(key) {
  if (key === 'method_code') return [...methodOptions.value]
  if (key === 'instrument_no') return [...instrumentOptions.value]
  if (key === 'unit') return [...unitOptions.value]
  if (key === 'inspection_method') return [...hardnessInspectionMethodOptions.value]
  return []
}

async function loadSharedOptions(key) {
  const resp = await apiFetch(`/ai/api/lab/mech/shared-options/${key}`)
  const payload = await resp.json().catch(() => ({}))
  if (!resp.ok || payload?.ok === false) {
    throw new Error(payload?.msg || `${sharedOptionTitle(key)}載入失敗`)
  }
  const list = Array.isArray(payload?.data) ? payload.data : []
  if (key === 'method_code') methodOptions.value = mergeOptionLists(methodOptions.value, list)
  if (key === 'instrument_no') {
    const equipmentOptions = await loadEquipmentOptions()
    instrumentOptions.value = mergeOptionLists(list, equipmentOptions)
  }
  if (key === 'unit') unitOptions.value = mergeOptionLists(unitOptions.value, list)
  if (key === 'inspection_method') hardnessInspectionMethodOptions.value = mergeOptionLists(hardnessInspectionMethodOptions.value, list)
}

async function loadEquipmentOptions() {
  try {
    const resp = await apiFetch('/ai/api/lab/equipment/options')
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) return []
    return Array.isArray(payload?.data) ? payload.data : []
  } catch {
    return []
  }
}

function openEquipmentExcel() {
  window.open('/ai/api/lab/equipment/source-file', '_blank', 'noopener')
}

function mergeOptionLists(base = [], incoming = []) {
  const map = new Map()
  ;[...base, ...incoming].forEach((row) => {
    const value = String(row?.value || row?.label || '').trim()
    if (value) map.set(value, { label: String(row?.label || value), value })
  })
  return [...map.values()].sort((a, b) => String(a.label).localeCompare(String(b.label), 'zh-Hant'))
}

function upsertLocalSharedOption(key, value) {
  const text = String(value || '').trim()
  if (!text) return
  const target = key === 'method_code'
    ? methodOptions
    : key === 'instrument_no'
      ? instrumentOptions
      : key === 'inspection_method'
        ? hardnessInspectionMethodOptions
        : unitOptions
  if (!target.value.some((row) => String(row?.value || '').trim() === text)) {
    target.value = [...target.value, { label: text, value: text }].sort((a, b) => String(a.label).localeCompare(String(b.label), 'zh-Hant'))
  }
}

function replaceLocalSharedOption(key, oldValue, newValue) {
  const target = key === 'method_code'
    ? methodOptions
    : key === 'instrument_no'
      ? instrumentOptions
      : key === 'inspection_method'
        ? hardnessInspectionMethodOptions
        : unitOptions
  target.value = target.value
    .map((row) => {
      const current = String(row?.value || '').trim()
      if (current === String(oldValue || '').trim()) {
        return { label: newValue, value: newValue }
      }
      return row
    })
    .sort((a, b) => String(a.label).localeCompare(String(b.label), 'zh-Hant'))
}

async function ensureSharedOption(key, value) {
  const text = String(value || '').trim()
  if (!text) return
  upsertLocalSharedOption(key, text)
  const resp = await apiFetch(`/ai/api/lab/mech/shared-options/${key}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value: text }),
  })
  const payload = await resp.json().catch(() => ({}))
  if (!resp.ok || payload?.ok === false) {
    throw new Error(payload?.msg || `${sharedOptionTitle(key)}儲存失敗`)
  }
}

async function onSharedOptionSelected(key, value) {
  if (!isStandardMode.value) return
  const text = String(value || '').trim()
  if (!text) return
  try {
    await ensureSharedOption(key, text)
  } catch (e) {
    ElMessage.warning(e.message || `${sharedOptionTitle(key)}共用清單儲存失敗`)
  }
}

function openSharedOptionEditor(key, sectionKey = '') {
  if (!isStandardMode.value) return
  sharedOptionEditor.key = key
  sharedOptionEditor.title = sharedOptionTitle(key)
  sharedOptionEditor.list = sharedOptionListByKey(key)
  sharedOptionEditor.selected = ''
  sharedOptionEditor.input = ''
  sharedOptionEditor.saving = false
  sharedOptionEditor.sectionKey = sectionKey
  sharedOptionEditor.sectionLabel =
    sectionKey === 'core_hardness'
      ? '心部硬度'
      : sectionKey === 'surface_hardness'
        ? '表面硬度'
        : sectionKey === 'carburizing_depth'
          ? '滲碳層測試'
            : sectionKey === 'decarb'
              ? '脫碳層測試'
              : sectionKey === 'ductility'
                ? '延展性測試'
                : sectionKey === 'hydrogen'
                  ? '氫脆測試'
                  : sectionKey === 'drilling_speed'
                    ? '攻速測試'
                    : sectionKey === 'torque'
                      ? '扭力測試'
                      : sectionKey === 'salt_spray'
                        ? '鹽霧測試'
                        : sectionKey === 'coating_thickness'
                          ? '膜厚測試'
                          : sectionKey === 'drive_torque'
                            ? '旋入扭力'
                            : sectionKey === 'drive_performance'
                              ? '旋入性能'
                              : ''
  sharedOptionEditor.open = true
}

function closeSharedOptionEditor() {
  sharedOptionEditor.open = false
  sharedOptionEditor.key = ''
  sharedOptionEditor.title = ''
  sharedOptionEditor.list = []
  sharedOptionEditor.selected = ''
  sharedOptionEditor.input = ''
  sharedOptionEditor.saving = false
  sharedOptionEditor.sectionKey = ''
  sharedOptionEditor.sectionLabel = ''
}

function pickSharedOption(item) {
  sharedOptionEditor.selected = String(item?.value || '')
  sharedOptionEditor.input = String(item?.label || item?.value || '')
}

function assignSharedOptionToSection(sectionKey, key, value) {
  const section = state[sectionKey]
  if (!section) return
  if (key === 'method_code') section.method_code = value
  if (key === 'instrument_no') section.instrument_no = value
  if (key === 'unit') section.unit = value
  if (key === 'inspection_method') section.inspection_method = value
}

async function submitSharedOptionEditor() {
  if (!isStandardMode.value) {
    closeSharedOptionEditor()
    return
  }
  const key = sharedOptionEditor.key
  const text = String(sharedOptionEditor.input || '').trim()
  if (!key || !text) {
    ElMessage.warning(`請輸入${sharedOptionEditor.title || '名稱'}`)
    return
  }
  sharedOptionEditor.saving = true
  try {
    if (sharedOptionEditor.selected) {
      const oldValue = String(sharedOptionEditor.selected || '').trim()
      const resp = await apiFetch(`/ai/api/lab/mech/shared-options/${key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_value: oldValue, value: text }),
      })
      const payload = await resp.json().catch(() => ({}))
      if (!resp.ok || payload?.ok === false) {
        throw new Error(payload?.msg || `${sharedOptionEditor.title}修改失敗`)
      }
      replaceLocalSharedOption(key, oldValue, text)
      if (sharedOptionEditor.sectionKey) {
        assignSharedOptionToSection(sharedOptionEditor.sectionKey, key, text)
      }
      ElMessage.success(`${sharedOptionEditor.title}已修改`)
    } else {
      await ensureSharedOption(key, text)
      if (sharedOptionEditor.sectionKey) {
        assignSharedOptionToSection(sharedOptionEditor.sectionKey, key, text)
      }
      ElMessage.success(`${sharedOptionEditor.title}已新增`)
    }
    await loadSharedOptions(key)
    sharedOptionEditor.list = sharedOptionListByKey(key)
    closeSharedOptionEditor()
  } catch (e) {
    ElMessage.error(e.message || `${sharedOptionEditor.title}處理失敗`)
  } finally {
    sharedOptionEditor.saving = false
  }
}

function resetSectionResult(section) {
  section.pass_count = 0
  section.fail_count = 0
  section.result = ''
}

function clearRowsByMode(section) {
  if (section.judge_mode === 'numeric_range') {
    if (section.test_code === 'core_hardness' || section.test_code === 'surface_hardness') {
      section.rows = (section.rows || []).map((row, idx) => ({
        ...row,
        sample_no: idx + 1,
        values: ['', '', ''],
        avg_value: '',
        judge_value: '',
        result: '',
        is_out_of_spec: false,
        remark: '',
      }))
    } else {
      section.rows = (section.rows || []).map((row, idx) => ({
        ...row,
        sample_no: idx + 1,
        value: '',
        avg_value: '',
        judge_value: '',
        result: '',
        is_out_of_spec: false,
        remark: '',
      }))
    }
  } else if (section.judge_mode === 'ok_ng') {
    section.rows = (section.rows || []).map((row, idx) => ({
      ...row,
      sample_no: idx + 1,
      status: '',
      result: '',
      is_out_of_spec: false,
      remark: '',
    }))
  } else if (section.judge_mode === 'decarb') {
    section.rows = (section.rows || []).map((row, idx) => ({
      ...row,
      sample_no: idx + 1,
      hv1: '',
      hv2: '',
      hv3: '',
      hv2_ok: true,
      hv3_ok: true,
      result: '',
    }))
  } else if (section.judge_mode === 'hydrogen') {
    section.rows = (section.rows || []).map((row, idx) => ({
      ...row,
      sample_no: idx + 1,
      tighten_at: '',
      remove_at: '',
      status: '',
      result: '',
    }))
    section.data = {
      ...section.data,
      plate_thickness: section.data?.plate_thickness || '',
      hole_diameter: section.data?.hole_diameter || '',
      plate_hardness: section.data?.plate_hardness || '',
      tighter_torque: section.data?.tighter_torque || '',
      no_failures_after_hours: section.data?.no_failures_after_hours || '',
      sample_count: section.data?.sample_count || section.sample_count || 10,
    }
  } else if (section.judge_mode === 'salt_spray') {
    section.data = {
      ...section.data,
      start_at: '',
      end_at: '',
      actual_hours: '',
      no_rust_pcs: 0,
      white_rust_pcs: 0,
      red_rust_pcs: 0,
      result: '',
    }
  }
}

function doDuplicate() {
  state.reportId = null
  imageState.images = []
  resetPendingImages()
  state.header.report_no = ''
  state.header.entrust_no = ''
  state.header.test_date = ''
  state.header.complete_date = ''
  state.header.remarks = ''

  for (const key of sectionKeys) {
    const section = state[key]
    if (!section) continue
    resetSectionResult(section)
    if (duplicateMode.value === 'template') {
      clearRowsByMode(section)
    }
  }

  applyDefaultHeaderValues()
  showDuplicate.value = false
  ElMessage.success(
    duplicateMode.value === 'template'
      ? '已複製為新報告（模板模式）'
      : '已複製為新報告（含原始數據）'
  )
}

function currentUserName() {
  try {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    return String(user?.name || user?.account || '').trim()
  } catch {
    return ''
  }
}

function todayText() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function applyDefaultHeaderValues() {
  if (!state.header.tester) {
    state.header.tester = currentUserName()
  }
  if (!state.header.test_date) {
    state.header.test_date = todayText()
  }
  if (!state.header.complete_date) {
    state.header.complete_date = todayText()
  }
}

function applySourceToHeader(values = {}, sourceFormId = '') {
  syncSourceStateFromValues(values, sourceFormId)

  const sampleCount = Number(values.sample_qty)
  const namedMethods = values.test_method_by_name || {}
  const hardnessMethods = values.hardness_inspection_methods || {}
  const standardRanges = values.test_standard_ranges || {}
  const coatingSpec = values.coating_thickness_spec || {}
  const saltSpec = values.salt_spray_spec || {}

  state.header.entrust_no = values.lab_no || ''
  state.header.product_name = values.sample_desc || values.part_no || state.header.product_name
  state.header.spec_desc = values.sample_spec || state.header.spec_desc
  state.header.lot_no = values.lot_no || state.header.lot_no
  state.header.lot_qty = values.production_qty ?? state.header.lot_qty
  state.header.plating = values.platingCate || state.header.plating
  state.header.material = values.material_no || state.header.material
  state.header.manufacturer = values.platingFac || values.outsource?.vendor_info || state.header.manufacturer
  if (values.report?.rule_type === '法規標準' && values.report?.rule_spec) {
    state.header.standard_type = 'regulation'
    state.header.standard_desc = values.report.rule_spec
  } else if (values.report?.rule_drawing) {
    state.header.standard_type = 'drawing'
    state.header.standard_desc = values.report.rule_drawing
  }

  const sourceTestMap = {
    心部硬度: 'core_hardness',
    表面硬度: 'surface_hardness',
    滲碳深度: 'carburizing_depth',
    脫碳測試: 'decarb',
    '延展性(鎚擊)': 'ductility',
    扭力: 'torque',
    氫脆化: 'hydrogen',
    攻速: 'drilling_speed',
    旋入: 'drive_torque',
  }
  for (const [itemName, sectionKey] of Object.entries(sourceTestMap)) {
    const methods = namedMethods[itemName]
    if (Array.isArray(methods) && methods.length) {
      state[sectionKey].method_code = methods[0]
    }
    const range = standardRanges[sectionKey]
    if (range && typeof range === 'object') {
      state[sectionKey].spec_min = range.min ?? state[sectionKey].spec_min
      state[sectionKey].spec_max = range.max ?? state[sectionKey].spec_max
    }
  }
  if (Array.isArray(namedMethods['電鍍膜厚']) && namedMethods['電鍍膜厚'].length) {
    state.coating_thickness.method_code = namedMethods['電鍍膜厚'][0]
  }
  if (Array.isArray(namedMethods['鹽水噴霧']) && namedMethods['鹽水噴霧'].length) {
    state.salt_spray.method_code = namedMethods['鹽水噴霧'][0]
  }
  state.core_hardness.inspection_method = hardnessMethods.core || state.core_hardness.inspection_method
  state.surface_hardness.inspection_method = hardnessMethods.surface || state.surface_hardness.inspection_method
  state.coating_thickness.spec_min = coatingSpec.min ?? state.coating_thickness.spec_min
  state.coating_thickness.spec_max = coatingSpec.max ?? state.coating_thickness.spec_max
  state.coating_thickness.unit = coatingSpec.unit || state.coating_thickness.unit
  state.salt_spray.data.white_spec_hours = saltSpec.white_hours || (
    values.salt_spray_type === '白鏽' ? values.salt_spray_hours : state.salt_spray.data.white_spec_hours
  )
  state.salt_spray.data.red_spec_hours = saltSpec.red_hours || (
    values.salt_spray_type === '紅鏽' ? values.salt_spray_hours : state.salt_spray.data.red_spec_hours
  )
  if (Number.isFinite(sampleCount) && sampleCount > 0) {
    for (const key of ['core_hardness', 'surface_hardness', 'coating_thickness', 'salt_spray']) {
      state[key].sample_count = Math.floor(sampleCount)
      if (key !== 'salt_spray') syncSectionRowsToCount(key)
    }
  }

  applyDefaultHeaderValues()
  state.header.remarks = [
    `來源委託單 ${values.lab_no || ''}`,
    values.customer_name ? `客戶 ${values.customer_name}` : '',
    values.contact_name ? `聯絡人 ${values.contact_name}` : '',
    values.contact_tel ? `電話 ${values.contact_tel}` : '',
    values.contact_email ? `E-mail ${values.contact_email}` : '',
    values.tests?.mechanical?.length ? `機械項目 ${values.tests.mechanical.join('、')}` : '',
    values.tests?.functional?.length ? `功能項目 ${values.tests.functional.join('、')}` : '',
    values.tests?.surface?.length ? `表面項目 ${values.tests.surface.join('、')}` : '',
    values.test_methods?.mechanical ? `機械方法 ${values.test_methods.mechanical}` : '',
    values.test_methods?.functional ? `功能方法 ${values.test_methods.functional}` : '',
    values.test_methods?.surface ? `表面方法 ${values.test_methods.surface}` : '',
    values.production_qty != null ? `產品產量 ${Number(values.production_qty).toLocaleString()} ${values.production_unit || 'PCS'}` : '',
    values.sample_qty != null ? `送驗數量 ${Number(values.sample_qty).toLocaleString()} ${values.sample_unit || 'PCS'}` : '',
    saltSpec.white_hours ? `鹽霧無白鏽 ${saltSpec.white_hours} H` : '',
    saltSpec.red_hours ? `鹽霧無紅鏽 ${saltSpec.red_hours} H` : '',
    saltSpec.other ? `鹽霧其它 ${saltSpec.other}` : '',
    values.other_requirements ? `其他需求 ${values.other_requirements}` : '',
  ].filter(Boolean).join('\n')
}

function syncSourceStateFromValues(values = {}, sourceFormId = '') {
  sourceState.sourceFormId = sourceFormId || ''
  sourceState.labNo = values.lab_no || ''
  sourceState.customerName = values.customer_name || ''
  sourceState.filledDate = values.filled_date || ''
  sourceState.contactName = values.contact_name || ''
  sourceState.contactTel = values.contact_tel || ''
  sourceState.contactEmail = values.contact_email || ''
  sourceState.address = values.address || ''
  sourceState.sampleDesc = values.sample_desc || values.part_no || ''
  sourceState.sampleSpec = values.sample_spec || ''
  sourceState.materialNo = values.material_no || ''
  sourceState.lotNo = values.lot_no || ''
}

async function fetchSourceFormDetail(formId) {
  const resp = await fetch(`/ai/api/lab/instances/${formId}`, {
    credentials: 'include'
  })
  const json = await resp.json()
  if (!json.ok || !json.form) {
    throw new Error(json.msg || '讀取委託單失敗')
  }
  return json.form
}

async function syncSourceStateFromEntrustNo(entrustNo) {
  const no = String(entrustNo || '').trim()
  if (!no || sourceState.labNo) return

  const qs = new URLSearchParams({ lab_no: no })
  const resp = await fetch(`/ai/api/lab/instances/search?${qs.toString()}`, {
    credentials: 'include'
  })
  const json = await resp.json()
  if (!resp.ok || !json.ok) {
    throw new Error(json.msg || '來源委託單查詢失敗')
  }

  const rows = Array.isArray(json.rows) ? json.rows : []
  const source = rows.find(row => String(row.lab_no || '').trim() === no) || rows[0]
  if (!source?.form_id) return

  const form = await fetchSourceFormDetail(source.form_id)
  syncSourceStateFromValues(form.values || {}, source.form_id)
}

async function findSavedReportByEntrustNo(entrustNo) {
  const no = String(entrustNo || '').trim()
  if (!no) return null
  const qs = new URLSearchParams({ entrust_no: no, limit: '50' })
  const resp = await fetch(`/ai/api/lab/mech/reports/search?${qs.toString()}`, {
    credentials: 'include'
  })
  const json = await resp.json()
  if (!resp.ok || !json.ok) {
    throw new Error(json.msg || '查詢已存機械性質報告失敗')
  }
  const rows = Array.isArray(json.rows) ? json.rows : []
  return rows.find(row => String(row.entrust_no || '').trim() === no) || null
}

async function selectSourceForm(formId) {
  try {
    const form = await fetchSourceFormDetail(formId)
    const values = form.values || {}
    const saved = await findSavedReportByEntrustNo(values.lab_no)
    if (saved?.report_id) {
      const result = await loadReport(saved.report_id)
      if (result?.ok) {
        syncSourceStateFromValues(values, formId)
        await loadUploadedImages()
        sourceState.dialogVisible = false
        router.replace({
          name: routeName.value,
          query: { report_id: saved.report_id, source_form_id: formId }
        })
        ElMessage.success('已載入既有機械性質資料')
        return
      }
    }

    if (!isStandardMode.value) {
      ElMessage.warning('此委託單尚未設定機械性質檢驗記錄表，請先由主管完成設定')
      return
    }

    resetForm()
    imageState.images = []
    resetPendingImages()
    applySourceToHeader(values, formId)
    sourceState.dialogVisible = false
    router.replace({
      name: routeName.value,
      query: { ...route.query, source_form_id: formId }
    })
    ElMessage.success('已帶入委託單資料')
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

    const resp = await fetch(`/ai/api/lab/instances/search?${q.toString()}`, {
      credentials: 'include'
    })
    const json = await resp.json()
    if (!json.ok) throw new Error(json.msg || '搜尋失敗')
    const rows = Array.isArray(json.rows) ? json.rows : []
    if (isStandardMode.value) {
      sourceState.results = rows
    } else {
      const checkedRows = await Promise.all(rows.map(async (row) => {
        const saved = await findSavedReportByEntrustNo(row.lab_no)
        return saved?.report_id ? { ...row, mech_report_id: saved.report_id } : null
      }))
      sourceState.results = checkedRows.filter(Boolean)
      if (!sourceState.results.length) {
        ElMessage.info('查無已設定機械性質檢驗記錄表的委託單')
      }
    }
  } catch (e) {
    ElMessage.error(e.message || '搜尋失敗')
  } finally {
    sourceState.loading = false
  }
}

function openSourceDialog() {
  sourceState.dialogVisible = true
  if (!sourceState.results.length) {
    searchSourceForms()
  }
}

function resetPendingImages() {
  pendingImageFiles.value = []
  if (imageInputRef.value) {
    imageInputRef.value.value = ''
  }
}

function openImagePicker() {
  if (!state.reportId) {
    ElMessage.warning('請先儲存報告，再上傳圖片')
    return
  }
  imageInputRef.value?.click()
}

function handleImageSelected(event) {
  pendingImageFiles.value = Array.from(event?.target?.files || [])
}

async function loadUploadedImages() {
  if (!state.reportId) {
    imageState.images = []
    return
  }
  imageState.loading = true
  try {
    const payload = await fetchLabMechImages(state.reportId)
    imageState.images = Array.isArray(payload?.images) ? payload.images : []
  } catch (e) {
    ElMessage.warning(e.message || '圖片清單載入失敗')
  } finally {
    imageState.loading = false
  }
}

async function uploadSelectedImages() {
  if (!state.reportId) {
    ElMessage.warning('請先儲存報告，再上傳圖片')
    return
  }
  if (!pendingImageFiles.value.length) {
    ElMessage.warning('請先選擇圖片')
    return
  }
  imageState.uploading = true
  try {
    const payload = await uploadLabMechImages(state.reportId, pendingImageFiles.value)
    imageState.images = Array.isArray(payload?.images) ? payload.images : []
    resetPendingImages()
    ElMessage.success('圖片上傳成功')
  } catch (e) {
    ElMessage.error(e.message || '圖片上傳失敗')
  } finally {
    imageState.uploading = false
  }
}

async function removeUploadedImage(name) {
  if (!state.reportId) return
  try {
    await ElMessageBox.confirm(`確定刪除圖片「${name}」？`, '警告', {
      type: 'warning',
      confirmButtonText: '刪除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    const payload = await deleteLabMechImage(state.reportId, name)
    imageState.images = Array.isArray(payload?.images) ? payload.images : []
    ElMessage.success('圖片刪除成功')
  } catch (e) {
    ElMessage.error(e.message || '圖片刪除失敗')
  }
}

async function searchReports() {
  reportState.loading = true
  try {
    const q = new URLSearchParams()
    if (reportState.searchReportNo) q.set('report_no', reportState.searchReportNo)
    if (reportState.searchEntrustNo) q.set('entrust_no', reportState.searchEntrustNo)
    if (reportState.searchCustomer) q.set('customer', reportState.searchCustomer)
    q.set('limit', '200')

    const resp = await fetch(`/ai/api/lab/mech/reports/search?${q.toString()}`, {
      credentials: 'include'
    })
    const ct = resp.headers.get('content-type') || ''
    const text = await resp.text()
    if (!ct.includes('application/json')) {
      throw new Error(`非 JSON 回應：${text.slice(0, 120)}`)
    }
    const json = JSON.parse(text)
    if (!resp.ok || !json.ok) throw new Error(json.msg || '搜尋報告失敗')
    reportState.results = json.rows || []
  } catch (e) {
    ElMessage.error(e.message || '搜尋報告失敗')
  } finally {
    reportState.loading = false
  }
}

function openReportDialog() {
  reportState.dialogVisible = true
  if (!reportState.results.length) {
    searchReports()
  }
}

async function loadReportWithSource(reportId, sourceFormId = '') {
  const result = await loadReport(reportId)
  if (result?.ok) {
    const report = result.report || {}
    if (sourceFormId) {
      try {
        const form = await fetchSourceFormDetail(sourceFormId)
        syncSourceStateFromValues(form.values || {}, sourceFormId)
      } catch (e) {
        ElMessage.warning(e.message || '來源委託單載入失敗')
      }
    } else if (report.source_values) {
      syncSourceStateFromValues(report.source_values, report.source_form_id || '')
    } else {
      try {
        await syncSourceStateFromEntrustNo(report.entrust_no || state.header.entrust_no)
      } catch (e) {
        ElMessage.warning(e.message || '來源委託單載入失敗')
      }
    }
    await loadUploadedImages()
  }
  return result
}

async function selectReport(reportId) {
  const result = await loadReportWithSource(reportId)
  if (result?.ok) {
    reportState.dialogVisible = false
    router.replace({
      name: routeName.value,
      query: {
        ...route.query,
        report_id: reportId,
      },
    })
  }
}

function openManagePage() {
  router.push({
    name: 'lab_mech_manage',
    query: isStandardMode.value ? { mode: 'standard' } : {},
  })
}

async function handleSaveReport() {
  if (!state.reportId && !sourceState.labNo) {
    ElMessage.warning('請先選擇委託單，取得 lab_no 後才能新增')
    return
  }
  const result = await saveReport()
  if (result?.ok) {
    await loadUploadedImages()
  }
}

function handleResetForm() {
  resetForm()
  imageState.images = []
  resetPendingImages()
  applyDefaultHeaderValues()
}

async function deleteReport() {
  if (!state.reportId) {
    ElMessage.warning('請先載入或儲存報告')
    return
  }
  if (!window.confirm(`確定要刪除報告 ${state.header.report_no || state.reportId}？`)) return
  state.loading = true
  try {
    const resp = await apiFetch(`/ai/api/lab/mech/reports/${state.reportId}`, {
      method: 'DELETE',
    })
    const payload = await resp.json().catch(() => ({}))
    if (!resp.ok || payload?.ok === false) throw new Error(payload?.msg || `HTTP ${resp.status}`)
    ElMessage.success('刪除成功')
    openManagePage()
  } catch (e) {
    ElMessage.error(e.message || '刪除失敗')
  } finally {
    state.loading = false
  }
}

async function openTemplatePicker() {
  showTemplatePicker.value = true
  await loadTemplateList(templateState.keyword)
}

async function searchTemplates() {
  await loadTemplateList(templateState.keyword)
}

async function useSelectedTemplate() {
  if (!templateState.selectedId) {
    ElMessage.warning('請先選擇模板')
    return
  }

  const r = await loadTemplateDetail(templateState.selectedId)
  if (r?.ok) {
    applyDefaultHeaderValues()
    showTemplatePicker.value = false
  }
}

async function createReportBySelectedTemplate() {
  if (!templateState.selectedId) {
    ElMessage.warning('請先選擇模板')
    return
  }

  const r1 = await loadTemplateDetail(templateState.selectedId)
  if (!r1?.ok) return

  const r2 = await createNewReportFromTemplate(templateState.selectedId)
  if (r2?.ok) {
    applyDefaultHeaderValues()
    showTemplatePicker.value = false
  }
}

function formatDateTime(value) {
  const dt = value instanceof Date ? value : new Date(String(value || '').replace(' ', 'T'))
  if (Number.isNaN(dt.getTime())) return ''
  const yyyy = dt.getFullYear()
  const mm = String(dt.getMonth() + 1).padStart(2, '0')
  const dd = String(dt.getDate()).padStart(2, '0')
  const hh = String(dt.getHours()).padStart(2, '0')
  const mi = String(dt.getMinutes()).padStart(2, '0')
  const ss = String(dt.getSeconds()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
}

function applyHydrogenTimeSchedule() {
  const rows = state.hydrogen.rows || []
  const first = rows[0]?.tighten_at
  if (!first) return
  const start = new Date(String(first).replace(' ', 'T'))
  if (Number.isNaN(start.getTime())) return
  const count = Number(state.hydrogen.sample_count || state.hydrogen.data?.sample_count || rows.length || 0)
  const hours = Number(state.hydrogen.data?.test_hours || state.hydrogen.data?.no_failures_after_hours || 24)
  rows.forEach((row, idx) => {
    if (idx >= count) return
    const tightenAt = new Date(start.getTime())
    tightenAt.setMinutes(tightenAt.getMinutes() + idx)
    const removeAt = new Date(tightenAt.getTime())
    removeAt.setHours(removeAt.getHours() + hours)
    row.tighten_at = formatDateTime(tightenAt)
    row.remove_at = formatDateTime(removeAt)
  })
  state.hydrogen.data.sample_count = count
  state.hydrogen.data.no_failures_after_hours = hours
}

watch(
  () => [
    state.hydrogen.rows?.[0]?.tighten_at,
    state.hydrogen.data?.test_hours,
    state.hydrogen.sample_count,
  ],
  applyHydrogenTimeSchedule
)

onMounted(async () => {
  try {
    await Promise.all([
      loadSharedOptions('method_code'),
      loadSharedOptions('instrument_no'),
      loadSharedOptions('unit'),
      loadSharedOptions('inspection_method'),
    ])
  } catch (e) {
    ElMessage.warning(e.message || '共用清單載入失敗')
  }
  const reportId = route.query.report_id
  if (reportId) {
    await loadReportWithSource(reportId, route.query.source_form_id || '')
    return
  }
  const sourceFormId = route.query.source_form_id
  if (sourceFormId) {
    await selectSourceForm(sourceFormId)
    return
  }
  applyDefaultHeaderValues()
})

watch(
  () => [route.query.report_id, route.query.source_form_id],
  async ([reportId, sourceFormId], [oldReportId, oldSourceFormId]) => {
    if (!reportId) return
    if (String(reportId || '') === String(oldReportId || '') && String(sourceFormId || '') === String(oldSourceFormId || '')) return
    await loadReportWithSource(reportId, sourceFormId || '')
  }
)
</script>

<style scoped>
.lab-page {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.lab-shell {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding-left: 16px;
  padding-right: 16px;
}

.lab-header {
  flex: 0 0 auto;
  position: sticky;
  top: 0;
  z-index: 20;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.lab-toolbar {
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 12px;
  padding-bottom: 12px;
}

.lab-toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.lab-main {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.lab-scroll-area {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding-top: 16px;
  padding-bottom: 16px;
}

.lab-footer {
  flex: 0 0 auto;
  position: sticky;
  bottom: 0;
  z-index: 20;
  background: #fff;
  border-top: 1px solid #e5e7eb;
}

.lab-footer-inner {
  min-height: 68px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 10px;
  padding-bottom: 10px;
}

.lab-footer-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

:deep(.el-input-number) {
  width: 100%;
}

.is-standard-mode :deep(.test-value-input) {
  display: none !important;
}

.is-entry-mode .lab-main :deep(.el-input:not(.test-value-input):not(.entry-editable-input) .el-input__wrapper),
.is-entry-mode .lab-main :deep(.el-select:not(.test-value-input):not(.entry-editable-input) .el-select__wrapper),
.is-entry-mode .lab-main :deep(.el-date-editor:not(.test-value-input):not(.entry-editable-input) .el-input__wrapper),
.is-entry-mode .lab-main :deep(.el-input-number:not(.test-value-input):not(.entry-editable-input) .el-input__wrapper),
.is-entry-mode .lab-main :deep(.el-checkbox-group),
.is-entry-mode .lab-main :deep(.el-checkbox) {
  pointer-events: none;
}

.is-entry-mode .lab-main :deep(.el-input:not(.test-value-input):not(.entry-editable-input) .el-input__wrapper),
.is-entry-mode .lab-main :deep(.el-select:not(.test-value-input):not(.entry-editable-input) .el-select__wrapper),
.is-entry-mode .lab-main :deep(.el-date-editor:not(.test-value-input):not(.entry-editable-input) .el-input__wrapper),
.is-entry-mode .lab-main :deep(.el-input-number:not(.test-value-input):not(.entry-editable-input) .el-input__wrapper) {
  background-color: #f8fafc;
  box-shadow: 0 0 0 1px #e5e7eb inset;
}
</style>

