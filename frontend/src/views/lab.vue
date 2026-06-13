<template>
  <div class="p-3 sm:p-5">
    <div class="max-w-6xl mx-auto">

      <div class="sticky top-0 z-40 bg-white/90 backdrop-blur border-b">
        <div class="py-3 space-y-2">
          <div class="flex items-center justify-end gap-2 flex-wrap">
            <el-button plain @click="openManualPdf('測試委託單.pdf')">
              使用說明
            </el-button>
            <el-button type="primary" plain @click="newLabForm">
              新增委託測試單
            </el-button>
            <el-button plain @click="openLabImport">
              匯入委託單
            </el-button>
            <el-button :loading="state.exporting" @click="exportDocxReal">
              匯出word/列印
            </el-button>
          </div>
          <div v-if="state.formId" class="lab-secondary-actions">
            <el-button plain @click="openInspectStandard">
              設定尺寸原始記錄表
            </el-button>
            <el-button plain @click="openInspectValues">
              開啟尺寸原始記錄表
            </el-button>
            <el-button plain @click="openLabMechStandard">
              設定機械性質檢驗記錄表
            </el-button>
            <el-button plain @click="openLabMech">
              開啟機械性質試驗表
            </el-button>
            <el-button :loading="state.exportingCustomerReport" plain @click="exportCustomerReport">
              匯出客戶報告
            </el-button>
          </div>
        </div>
      </div>

      <div class="mt-3">
        <div class="overflow-y-auto" style="height: calc(100vh - 170px);">
          <div class="space-y-3">
            
            <el-card shadow="never">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="font-semibold">1) 客戶選擇</div>
                </div>
              </template>
              <div class="grid grid-cols-1 sm:grid-cols-12 gap-3">
                <div class="sm:col-span-12">
                  <div class="text-xs text-gray-500 mb-1">客戶</div>
                  <div class="flex gap-2">
                    <el-select v-model="state.selectedCustomerRefno" filterable placeholder="請選客戶" class="flex-1" @change="onCustomerSelected">
                      <el-option v-for="c in customerOptions" :key="String(c.refno)" :label="`${c.company} (${c.refno})`" :value="String(c.refno)" />
                    </el-select>
                    <el-button plain @click="openCustomerCreate" title="新增客戶">+</el-button>
                    <el-button plain @click="clearCustomer()">清除</el-button>
                  </div>
                </div>
              </div>
            </el-card>

            <el-card shadow="never">
              <template #header><div class="font-semibold">2) 基本資訊</div></template>
              <el-form :model="form" label-position="top" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <el-form-item label="填表日期">
                  <el-date-picker v-model="form.filled_date" type="date" class="w-full" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
                </el-form-item>
                <el-form-item label="委託編號（系統自動產生）">
                  <el-tooltip
                    placement="top"
                    effect="dark"
                    :show-after="150"
                    popper-class="lab-debug-tooltip"
                  >
                    <template #content>
                      <div class="text-xs leading-6 break-all">
                        <div><strong>form_id:</strong> {{ state.formId || '-' }}</div>
                        <div><strong>template_id:</strong> {{ state.templateId || '-' }}</div>
                        <div><strong>lab_no:</strong> {{ form.lab_no || '-' }}</div>
                      </div>
                    </template>
                    <el-input v-model="form.lab_no" readonly />
                  </el-tooltip>
                </el-form-item>
                </el-form>
            </el-card>

            <el-card shadow="never">
              <template #header><div class="font-semibold">3) 委託顧客資訊</div></template>
              <el-form :model="form" label-position="top" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <el-form-item label="委託顧客名稱"><el-input v-model="form.customer_name" /></el-form-item>
                <el-form-item label="部門單位"><el-input v-model="form.dept" /></el-form-item>
                <el-form-item label="聯絡人（中/英文姓名）"><el-input v-model="form.contact_name" /></el-form-item>
                <el-form-item label="聯絡電話"><el-input v-model="form.contact_tel" /></el-form-item>
                <el-form-item label="傳真"><el-input v-model="form.contact_fax" /></el-form-item>
                <el-form-item label="E-mail"><el-input v-model="form.contact_email" /></el-form-item>
                <el-form-item label="顧客統一編號"><el-input v-model="form.tax_id" /></el-form-item>
                <el-form-item label="聯絡地址"><el-input v-model="form.address" /></el-form-item>
                <el-form-item label="顧客討論紀錄" class="sm:col-span-2">
                  <el-input v-model="form.discussion" type="textarea" :autosize="{ minRows: 3 }" />
                </el-form-item>
              </el-form>
            </el-card>

            <el-card shadow="never">
              <template #header><div class="font-semibold">4) 送驗樣品資訊</div></template>
              <el-alert
                v-if="previousLookup.matches.length"
                type="info"
                show-icon
                :closable="false"
                class="mb-3"
              >
                <template #title>
                  找到 {{ previousLookup.matches.length }} 筆相同 Part No. / Print No. 前單，可直接帶入前單資料。
                </template>
                <div class="mt-2 flex flex-wrap gap-2">
                  <el-button
                    v-for="row in previousLookup.matches"
                    :key="row.form_id"
                    size="small"
                    plain
                    @click="importLabFormFrom(row.form_id)"
                  >
                    {{ row.lab_no }}｜{{ row.customer_name || '-' }}｜{{ row.part_no || row.drawing_no || '-' }}
                  </el-button>
                </div>
              </el-alert>
              <el-form :model="form" label-position="top" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <el-form-item label="訂單號碼"><el-input v-model="form.order_no" /></el-form-item>
                <el-form-item label="材質編號">
                  <div class="flex gap-2 w-full">
                    <el-select
                      v-model="form.material_no"
                      filterable
                      allow-create
                      default-first-option
                      clearable
                      placeholder="可搜尋或直接輸入"
                      class="flex-1"
                      @change="onSharedOptionSelected('material_no', $event)"
                    >
                      <el-option
                        v-for="o in state.materialOptions"
                        :key="`material-${o.value}`"
                        :label="o.label"
                        :value="o.value"
                      />
                    </el-select>
                    <el-button plain @click="openSharedOptionEditor('material_no')">+</el-button>
                  </div>
                </el-form-item>
                <el-form-item label="爐號">
                  <el-input v-model="form.heat_no" />
                </el-form-item>
                <el-form-item label="製造批號"><el-input v-model="form.lot_no" /></el-form-item>
                <el-form-item label="產品產量">
                  <div class="flex gap-2 w-full">
                    <el-input-number
                      v-model="form.production_qty"
                      style="width: calc(100% - 120px)"
                      controls-position="right"
                      :formatter="formatNumberWithCommas"
                      :parser="parseCommaNumber"
                    />
                    <el-select v-model="form.production_unit" style="width: 112px" allow-create filterable>
                      <el-option v-for="unit in quantityUnits" :key="`production-${unit}`" :label="unit" :value="unit" />
                    </el-select>
                  </div>
                </el-form-item>
                <el-form-item label="送驗數量">
                  <div class="flex gap-2 w-full">
                    <el-input-number
                      v-model="form.sample_qty"
                      style="width: calc(100% - 120px)"
                      controls-position="right"
                      :formatter="formatNumberWithCommas"
                      :parser="parseCommaNumber"
                    />
                    <el-select v-model="form.sample_unit" style="width: 112px" allow-create filterable>
                      <el-option v-for="unit in quantityUnits" :key="`sample-${unit}`" :label="unit" :value="unit" />
                    </el-select>
                  </div>
                </el-form-item>
                <el-form-item label="測試件規格"><el-input v-model="form.sample_spec" /></el-form-item>
                <el-form-item label="Part No.">
                  <div class="flex gap-2 w-full">
                    <el-input
                      v-model="form.part_no"
                      placeholder="輸入後可查前單"
                      @keyup.enter="searchPreviousByPartOrPrint"
                      @blur="searchPreviousByPartOrPrint"
                    />
                    <el-button plain :loading="previousLookup.loading" @click="searchPreviousByPartOrPrint">查前單</el-button>
                  </div>
                </el-form-item>
                <el-form-item label="測試件品名"><el-input v-model="form.sample_desc" /></el-form-item>
                <el-form-item label="電鍍別">
                  <div class="flex gap-2 w-full">
                    <el-select
                      v-model="form.platingCate"
                      filterable
                      allow-create
                      default-first-option
                      clearable
                      placeholder="可搜尋或直接輸入"
                      class="flex-1"
                      @change="onSharedOptionSelected('plating_cate', $event)"
                    >
                      <el-option
                        v-for="o in state.platingCateOptions"
                        :key="`plating-${o.value}`"
                        :label="o.label"
                        :value="o.value"
                      />
                    </el-select>
                    <el-button plain @click="openSharedOptionEditor('plating_cate')">+</el-button>
                  </div>
                </el-form-item>
                <el-form-item label="廠商">
                  <div class="flex gap-2 w-full">
                    <el-select
                      v-model="form.platingFac"
                      filterable
                      allow-create
                      default-first-option
                      clearable
                      placeholder="可搜尋或直接輸入"
                      class="flex-1"
                      @change="onSharedOptionSelected('plating_fac', $event)"
                    >
                      <el-option
                        v-for="o in state.platingFacOptions"
                        :key="`plating-fac-${o.value}`"
                        :label="o.label"
                        :value="o.value"
                      />
                    </el-select>
                    <el-button plain @click="openSharedOptionEditor('plating_fac')">+</el-button>
                  </div>
                </el-form-item>
                <el-form-item label="收樣方式" class="sm:col-span-2">
                  <el-radio-group v-model="form.receive_method">
                    <el-radio label="自行郵寄貨運">自行郵寄貨運</el-radio>
                    <el-radio label="到貴公司收樣">到貴公司收樣</el-radio>
                    <el-radio label="其他">其他</el-radio>
                  </el-radio-group>
                  <el-input v-if="form.receive_method === '其他'" v-model="form.receive_method_other" class="mt-2" placeholder="請填寫其他方式" />
                </el-form-item>
              </el-form>
            </el-card>

            <el-card shadow="never">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="font-semibold">5) 試驗項目（多選）</div>
                </div>
              </template>

              <div class="space-y-3">
                <div
                  v-for="cate in state.testConfigCategories"
                  :key="cate.key"
                  class="border rounded-xl p-3"
                >
                  <div class="font-semibold mb-3">{{ cate.label }}</div>
                  <div v-if="cate.key === 'other'">
                    <div class="grid grid-cols-1 sm:grid-cols-12 gap-3 border rounded-lg p-3">
                      <div class="sm:col-span-4 flex items-center text-sm text-slate-600">
                        請直接選擇試驗方法
                      </div>
                      <div class="sm:col-span-8">
                        <div class="flex items-center gap-2">
                          <el-select
                            :model-value="selectedMethodsForOther(cate)"
                            multiple
                            collapse-tags
                            collapse-tags-tooltip
                            filterable
                            clearable
                            class="flex-1"
                            placeholder="請選擇試驗方法"
                            @change="updateMethodsForOther(cate, $event)"
                          >
                            <el-option
                              v-for="method in otherCategoryMethods(cate)"
                              :key="`other-${method}`"
                              :label="method"
                              :value="method"
                            />
                          </el-select>
                          <el-button plain @click="openTestMethodEditor(otherCategoryItem(cate), cate)">+</el-button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="space-y-3">
                    <div
                      v-for="item in cate.items"
                      :key="`${cate.key}-${item.item_id}`"
                      class="grid grid-cols-1 sm:grid-cols-12 gap-3 border rounded-lg p-3"
                    >
                      <div class="sm:col-span-4 flex items-center">
                        <el-checkbox
                          :model-value="isTestItemSelected(cate.key, item.name)"
                          @change="toggleTestItem(cate.key, item.name, $event)"
                        >
                          {{ item.name }}
                        </el-checkbox>
                      </div>

                      <div class="sm:col-span-8">
                        <div class="flex items-center gap-2">
                          <el-select
                            :model-value="selectedMethodsForItem(item.item_id)"
                            multiple
                            collapse-tags
                            collapse-tags-tooltip
                            filterable
                            clearable
                            class="flex-1"
                            placeholder="請選擇試驗方法"
                            :disabled="!isTestItemSelected(cate.key, item.name)"
                            @change="updateMethodsForItem(cate.key, item, $event)"
                          >
                            <el-option
                              v-for="method in item.methods"
                              :key="`${item.item_id}-${method}`"
                              :label="method"
                              :value="method"
                            />
                          </el-select>
                          <el-button plain @click="openTestMethodEditor(item, cate)">+</el-button>
                        </div>

                        <div
                          v-if="cate.key === 'mechanical' && ['心部硬度', '表面硬度'].includes(item.name) && isTestItemSelected(cate.key, item.name)"
                          class="mt-2"
                        >
                          <el-select
                            v-model="form.hardness_inspection_methods[hardnessInspectionKey(item.name)]"
                            clearable
                            class="w-full"
                            placeholder="檢測方式"
                          >
                            <el-option v-for="method in hardnessInspectionMethods" :key="`${item.name}-${method}`" :label="method" :value="method" />
                          </el-select>
                        </div>

                        <div
                          v-if="['mechanical', 'functional'].includes(cate.key) && isTestItemSelected(cate.key, item.name)"
                          class="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2"
                        >
                          <el-input
                            v-model="form.test_standard_ranges[testStandardKey(item.name)].min"
                            inputmode="decimal"
                            placeholder="標準值下限"
                          >
                            <template #prepend>下限</template>
                          </el-input>
                          <el-input
                            v-model="form.test_standard_ranges[testStandardKey(item.name)].max"
                            inputmode="decimal"
                            placeholder="標準值上限"
                          >
                            <template #prepend>上限</template>
                          </el-input>
                        </div>

                        <div
                          v-if="cate.key === 'surface' && item.name === '電鍍膜厚' && isTestItemSelected('surface', '電鍍膜厚')"
                          class="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2"
                        >
                          <el-input v-model="form.coating_thickness_spec.min" inputmode="decimal" placeholder="厚度最小值" />
                          <el-input v-model="form.coating_thickness_spec.max" inputmode="decimal" placeholder="厚度最大值" />
                          <el-select v-model="form.coating_thickness_spec.unit" placeholder="厚度單位">
                            <el-option label="μm" value="μm" />
                            <el-option label="inch" value="inch" />
                          </el-select>
                        </div>

                        <div
                          v-if="cate.key === 'surface' && item.name === '鹽水噴霧' && isTestItemSelected('surface', '鹽水噴霧')"
                          class="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2"
                        >
                          <el-input v-model="form.salt_spray_spec.white_hours" inputmode="decimal" placeholder="無白鏽標準時數 (H)">
                            <template #prepend>白鏽</template>
                          </el-input>
                          <el-input v-model="form.salt_spray_spec.red_hours" inputmode="decimal" placeholder="無紅鏽標準時數 (H)">
                            <template #prepend>紅鏽</template>
                          </el-input>
                          <el-input v-model="form.salt_spray_spec.other" class="sm:col-span-2" placeholder="其它鹽霧標準說明" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-card>
            <el-card shadow="never">
              <template #header><div class="font-semibold">6) 報告需求</div></template>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="border rounded-xl p-3">
                  <div class="font-semibold mb-2">報告需求</div>
                  <el-radio-group v-model="form.report.needs" @change="onReportNeedChange">
                    <el-radio label="無認證標誌">無認證標誌</el-radio>
                    <el-radio label="TAF認證標誌">TAF認證標誌</el-radio>
                    <el-radio label="PPAP">PPAP</el-radio>
                    <el-radio label="其它">其它</el-radio>
                  </el-radio-group>
                  <el-input v-if="form.report.needs === '其它'" v-model="form.report.needs_other" class="mt-2" />
                </div>
                <div class="border rounded-xl p-3">
                  <div class="font-semibold mb-2">符合性聲明</div>
                  <el-radio-group v-model="form.report.conformity">
                    <el-radio label="要">要</el-radio><el-radio label="不要">不要</el-radio>
                  </el-radio-group>
                </div>
                <div class="border rounded-xl p-3 sm:col-span-2">
                  <div class="font-semibold mb-2">判定規則</div>

                  <div class="mb-3">
                    <el-radio-group v-model="form.report.rule_type">
                      <el-radio label="依顧客提供規範">依顧客提供規範</el-radio>
                      <el-radio label="法規標準">法規標準</el-radio>
                    </el-radio-group>
                  </div>

                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <el-checkbox v-model="form.report.rule_has_drawing">附圖</el-checkbox>
                    <el-input
                      v-model="form.report.rule_drawing"
                      placeholder="圖號 / Print No."
                      @keyup.enter="searchPreviousByPartOrPrint"
                      @blur="searchPreviousByPartOrPrint"
                    />
                    <div class="flex gap-2 w-full">
                      <el-select
                        v-model="form.report.rule_spec"
                        filterable
                        allow-create
                        default-first-option
                        clearable
                        placeholder="規範/標準"
                        class="flex-1"
                        @change="onSharedOptionSelected('rule_spec', $event)"
                      >
                        <el-option
                          v-for="o in state.ruleSpecOptions"
                          :key="`rule-spec-${o.value}`"
                          :label="o.label"
                          :value="o.value"
                        />
                      </el-select>
                      <el-button plain @click="openSharedOptionEditor('rule_spec')">+</el-button>
                    </div>
                  </div>
                  <div v-if="form.report.rule_has_drawing" class="mt-3 border-t pt-3">
                    <div class="flex items-center gap-2 flex-wrap">
                      <input
                        ref="drawingAttachmentInput"
                        type="file"
                        class="hidden"
                        accept="image/*,.pdf,.doc,.docx,.xls,.xlsx"
                        @change="uploadDrawingAttachment"
                      />
                      <el-button plain :loading="attachmentState.uploading" @click="chooseDrawingAttachment">
                        上傳附圖
                      </el-button>
                      <span class="text-xs text-gray-500">客戶提供的附圖只供委託單點開查看，不會匯入 Word。</span>
                    </div>
                    <div v-if="attachmentState.files.length" class="mt-2 flex flex-wrap gap-2">
                      <el-button
                        v-for="file in attachmentState.files"
                        :key="file.name"
                        size="small"
                        plain
                        @click="openAttachment(file)"
                      >
                        {{ file.name }}
                      </el-button>
                    </div>
                  </div>
                </div>
                <div v-if="canSeeOutsource" class="border rounded-xl p-3 sm:col-span-2">
                  <div class="font-semibold mb-2">外包需求（主管）</div>
                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <el-select v-model="form.outsource.has" class="w-full">
                      <el-option label="無" value="無" />
                      <el-option label="有" value="有" />
                    </el-select>
                    <el-input v-model="form.outsource.items" placeholder="外包項目" />
                    <el-input v-model="form.outsource.vendor_info" placeholder="外包廠商 / 備註" />
                  </div>
                </div>
                <div class="border rounded-xl p-3 sm:col-span-2">
                  <div class="font-semibold mb-2">其他需求</div>
                  <el-input v-model="form.other_requirements" type="textarea" />
                </div>
                <div class="border rounded-xl p-3 sm:col-span-2">
                  <div class="font-semibold mb-2">測試後樣品處理</div>
                  <el-radio-group v-model="form.sample_return">
                    <el-radio label="需要取回">需要取回</el-radio>
                    <el-radio label="不需要取回">不需要取回</el-radio>
                  </el-radio-group>
                </div>
              </div>
            </el-card>

            <el-card shadow="never">
              <template #header><div class="font-semibold">7) 委託單成立確認</div></template>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div class="border rounded-xl p-3">
                  <el-checkbox v-model="form.approval.customer_signature_checked">委託方簽名已確認</el-checkbox>
                  <el-date-picker
                    v-model="form.approval.customer_signature_date"
                    type="date"
                    class="w-full mt-2"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    placeholder="委託方簽名日期"
                  />
                  <input
                    ref="customerSignatureInput"
                    type="file"
                    class="hidden"
                    accept="image/*,.pdf"
                    @change="uploadApprovalSignature('customer', $event)"
                  />
                  <div class="mt-2 flex items-center gap-2 flex-wrap">
                    <el-button size="small" plain :loading="signatureState.uploading === 'customer'" @click="chooseApprovalSignature('customer')">
                      上傳委託方簽名檔
                    </el-button>
                    <el-button
                      v-if="form.approval.customer_signature_file?.url"
                      size="small"
                      plain
                      @click="openAttachment(form.approval.customer_signature_file)"
                    >
                      {{ form.approval.customer_signature_file.name }}
                    </el-button>
                  </div>
                </div>
                <div class="border rounded-xl p-3">
                  <el-checkbox v-model="form.approval.manager_approval_checked" :disabled="!isSupervisorUser">主管審核已確認</el-checkbox>
                  <el-date-picker
                    v-model="form.approval.manager_approval_date"
                    type="date"
                    class="w-full mt-2"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    placeholder="主管審核日期"
                    :disabled="!isSupervisorUser"
                  />
                  <input
                    ref="managerSignatureInput"
                    type="file"
                    class="hidden"
                    accept="image/*,.pdf"
                    @change="uploadApprovalSignature('manager', $event)"
                  />
                  <div class="mt-2 flex items-center gap-2 flex-wrap">
                    <el-button
                      size="small"
                      plain
                      :disabled="!isSupervisorUser"
                      :loading="signatureState.uploading === 'manager'"
                      @click="chooseApprovalSignature('manager')"
                    >
                      上傳主管簽名檔
                    </el-button>
                    <el-button
                      v-if="form.approval.manager_signature_file?.url"
                      size="small"
                      plain
                      @click="openAttachment(form.approval.manager_signature_file)"
                    >
                      {{ form.approval.manager_signature_file.name }}
                    </el-button>
                  </div>
                  <div v-if="!isSupervisorUser" class="text-xs text-gray-500 mt-2">
                    主管審核由主管登入後確認。
                  </div>
                </div>
              </div>
            </el-card>

            <el-card v-if="showQuotationFields" shadow="never">
              <template #header><div class="font-semibold">8) 報價資訊</div></template>
              <el-form :model="form" label-position="top" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <el-form-item label="幣別">
                  <el-select v-model="form.quote_currency" placeholder="請選擇幣別" class="w-full">
                    <el-option
                      v-for="item in quoteCurrencyOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="報價金額">
                  <el-input-number
                    v-model="form.quote_amount"
                    class="w-full"
                    :min="0"
                    :precision="2"
                    :step="100"
                    controls-position="right"
                  />
                </el-form-item>
              </el-form>
            </el-card>
          </div>
        </div>
      </div>

      <div class="mt-3">
        <div class="fixed bottom-0 left-0 right-0 z-50 border-t bg-white/90 backdrop-blur">
          <div class="max-w-6xl mx-auto px-3 sm:px-5 py-3 flex justify-end gap-2">
            <el-button
              v-if="state.formId"
              type="danger"
              plain
              :loading="state.deleting"
              @click="deleteCurrentForm"
            >
              刪除
            </el-button>
            <el-button type="primary" :loading="state.saving" @click="saveDraftReal">
              儲存
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="sharedOptionEditor.open"
      :title="sharedOptionEditor.title"
      width="460px"
      destroy-on-close
    >
      <div class="space-y-3">
        <div class="border rounded-xl max-h-64 overflow-auto">
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

        <el-input
          v-model="sharedOptionEditor.input"
          :placeholder="`請輸入${sharedOptionEditor.title}`"
          @keydown.enter.prevent="submitSharedOptionEditor"
        />
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <el-button @click="closeSharedOptionEditor">取消</el-button>
          <el-button type="primary" :loading="sharedOptionEditor.saving" @click="submitSharedOptionEditor">
            {{ sharedOptionEditor.selected ? '修改' : '新增' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="testMethodEditor.open"
      :title="testMethodEditor.title || '試驗方法維護'"
      width="560px"
      destroy-on-close
    >
      <div class="space-y-3">
        <div class="text-sm text-slate-600">
          這個檢驗項目可建立多個試驗方法。可新增多列，各列會成為可多選選項。
        </div>
        <div class="space-y-2">
          <div
            v-for="(method, idx) in testMethodEditor.methods"
            :key="`method-row-${idx}`"
            class="flex items-center gap-2"
          >
            <el-input
              v-model="testMethodEditor.methods[idx]"
              :placeholder="`試驗方法 ${idx + 1}`"
            />
            <el-button
              plain
              type="danger"
              @click="removeTestMethodRow(idx)"
              :disabled="testMethodEditor.methods.length <= 1"
            >
              刪除
            </el-button>
          </div>
        </div>
        <div>
          <el-button plain @click="addTestMethodRow">新增一筆試驗方法</el-button>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <el-button @click="closeTestMethodEditor">取消</el-button>
          <el-button type="primary" :loading="testMethodEditor.saving" @click="saveTestMethodEditor">
            儲存
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

// URL Helper
const BASE_URL = import.meta.env.BASE_URL || '/ai/'
const api = (p) => {
  const cleanBase = BASE_URL.endsWith('/') ? BASE_URL : BASE_URL + '/'
  return `${cleanBase}api/${String(p || '').replace(/^\/+/, '')}`
}
const router = useRouter()
const route = useRoute()
const quoteCurrencyOptions = [
  { label: 'TWD', value: 'TWD' },
  { label: 'USD', value: 'USD' },
  { label: 'CNY', value: 'CNY' },
  { label: 'EUR', value: 'EUR' },
  { label: 'JPY', value: 'JPY' },
]
const showQuotationFields = computed(() => String(route.query.from || '').trim() === 'lab_quote_manage')
const currentUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || sessionStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
})
const isSupervisorUser = computed(() => {
  const user = currentUser.value || {}
  const authority = Number(user?.authority)
  const text = [
    user?.role,
    user?.title,
    user?.authority_name,
    user?.authorityName,
    user?.dep,
  ].map(v => String(v || '')).join(' ')
  return authority === 12 || text.includes('主管')
})
const canSeeOutsource = computed(() => isSupervisorUser.value)
const drawingAttachmentInput = ref(null)
const customerSignatureInput = ref(null)
const managerSignatureInput = ref(null)

const todayStr = (() => {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
})()

const state = reactive({
  templateName: 'LQP-08-01',
  templateDocx: 'LQP-08-01.docx',
  templateId: localStorage.getItem('lab_template_id') || '',
  formId: '',
  selectedCustomerRefno: '',
  customers: [],
  materialOptions: [],
  heatOptions: [],
  platingCateOptions: [],
  platingFacOptions: [],
  ruleSpecOptions: [],
  testConfigCategories: [],
  saving: false,
  exporting: false,
  exportingCustomerReport: false,
  deleting: false,
})

const attachmentState = reactive({
  loading: false,
  uploading: false,
  files: [],
})
const signatureState = reactive({
  uploading: '',
})

const sharedOptionEditor = reactive({
  open: false,
  key: '',
  title: '',
  list: [],
  selected: '',
  input: '',
  saving: false,
})

const testMethodEditor = reactive({
  open: false,
  saving: false,
  item_id: null,
  cate_key: '',
  item_name: '',
  title: '',
  methods: [''],
})

const previousLookup = reactive({
  loading: false,
  lastKey: '',
  matches: [],
})

const quantityUnits = ['PCS', 'KG', 'SET', 'LOT']
const hardnessInspectionMethods = ['洛式', '微小', '維克氏']
const testStandardKeyMap = {
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

function hardnessInspectionKey(itemName) {
  return itemName === '心部硬度' ? 'core' : 'surface'
}

function testStandardKey(itemName) {
  return testStandardKeyMap[itemName] || itemName
}

function createBlankTestStandardRanges() {
  return Object.fromEntries(
    Object.values(testStandardKeyMap).map(key => [key, { min: '', max: '' }])
  )
}

function onReportNeedChange(value) {
  form.report.customer_report_logo = value === 'TAF認證標誌' ? 'with_logo' : 'without_logo'
  if (value !== '其它') form.report.needs_other = ''
}

function formatNumberWithCommas(value) {
  if (value === null || value === undefined || value === '') return ''
  const text = String(value).replace(/,/g, '')
  const [intPart, decPart] = text.split('.')
  const sign = intPart.startsWith('-') ? '-' : ''
  const digits = intPart.replace(/^-/, '').replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return `${sign}${digits}${decPart != null ? `.${decPart}` : ''}`
}

function parseCommaNumber(value) {
  const cleaned = String(value ?? '').replace(/,/g, '')
  const num = Number(cleaned)
  return Number.isFinite(num) ? num : 0
}

function createBlankLabForm() {
  return {
  filled_date: todayStr,
  lab_no: '',

  customer_id: null,
  customer_refno: '',
  customer_name: '',
  dept: '',
  contact_name: '',
  contact_tel: '',
  contact_fax: '',
  contact_email: '',
  tax_id: '',
  address: '',
  discussion: '',

  order_no: '',
  material_no: '',
  heat_no: '',
  lot_no: '',
  production_qty: 0,
  production_unit: 'PCS',
  sample_qty: 0,
  sample_unit: 'PCS',
  sample_spec: '',
  part_no: '',
  sample_desc: '',
  platingCate: '',
  platingFac: '',

  receive_method: '自行郵寄貨運',
  receive_method_other: '',

  tests: {
    dimension: [],
    mechanical: [],
    functional: [],
    surface: [],
    other: []
  },
  test_method_map: {},
  test_method_by_name: {},
  hardness_inspection_methods: {
    core: '',
    surface: '',
  },
  test_standard_ranges: createBlankTestStandardRanges(),
  coating_thickness_spec: {
    min: '',
    max: '',
    unit: 'μm',
  },
  salt_spray_spec: {
    white_hours: '',
    red_hours: '',
    other: '',
  },

  test_methods: {
    dimension: '',
    mechanical: '',
    functional: '',
    surface: '',
    other: ''
  },

  salt_spray_hours: '',
  salt_spray_type: '',
  salt_spray_other: '',

  report: {
    needs: '無認證標誌',
    needs_other: '',
    conformity: '不要',

    // ✅ 新增，對應 template / schema
    rule_type: '',                  // '依顧客提供規範' 或 '法規標準'
    rule_has_drawing: false,        // true / false
    rule_drawing: '',
    rule_spec: '',
    customer_report_logo: 'without_logo'
  },

  outsource: {
    has: '無',
    items: '',
    vendor_info: ''
  },

  approval: {
    customer_signature_checked: false,
    customer_signature_date: '',
    customer_signature_file: null,
    manager_approval_checked: false,
    manager_approval_date: '',
    manager_signature_file: null,
  },

  other_requirements: '',

  // ✅ 新增，對應「測試後樣品處理」
  sample_return: '不需要取回',
  quote_currency: '',
  quote_amount: null,
  }
}

const form = reactive(createBlankLabForm())
const customerOptions = computed(() => state.customers)

function openManualPdf(fileName) {
  if (!fileName) return
  const target = `${import.meta.env.BASE_URL}manuals/${encodeURIComponent(String(fileName))}`
  window.open(target, '_blank', 'noopener')
}

function assignFormValues(values = {}) {
  const normalizeTests = (raw) => {
    if (Array.isArray(raw)) return raw.map(x => String(x || '').trim()).filter(Boolean)
    if (typeof raw === 'string') {
      return raw.split(/[、,，;；\n]+/).map(x => x.trim()).filter(Boolean)
    }
    return []
  }
  const normalizeOtherTests = (raw) => {
    const list = normalizeTests(raw)
    if (!list.length) return []
    return ['其他']
  }
  const normalizeTestBucket = (bucket) => ({
    dimension: normalizeTests(bucket?.dimension),
    mechanical: normalizeTests(bucket?.mechanical),
    functional: normalizeTests(bucket?.functional),
    surface: normalizeTests(bucket?.surface),
    other: normalizeOtherTests(bucket?.other),
  })
  const normalizeTestMethodMap = (src) => {
    const out = {}
    if (!src || typeof src !== 'object') return out
    for (const [k, v] of Object.entries(src)) {
      if (Array.isArray(v)) out[String(k)] = [...v].map(x => String(x || '').trim()).filter(Boolean)
      else if (typeof v === 'string' && v.trim()) out[String(k)] = [v.trim()]
    }
    return out
  }
  const legacySaltType = String(values.salt_spray_type || '').trim()
  const legacySaltHours = String(values.salt_spray_hours || '').trim()
  const saltSpraySpec = {
    white_hours: legacySaltType === '白鏽' ? legacySaltHours : '',
    red_hours: legacySaltType === '紅鏽' ? legacySaltHours : '',
    other: values.salt_spray_other || '',
    ...(values.salt_spray_spec || {}),
  }
  const rawReportNeeds = values.report?.needs
  const reportNeed = Array.isArray(rawReportNeeds)
    ? (rawReportNeeds.includes('TAF認證標誌') ? 'TAF認證標誌' : rawReportNeeds[0] || '無認證標誌')
    : (rawReportNeeds || '無認證標誌')
  const testStandardRanges = createBlankTestStandardRanges()
  for (const [key, range] of Object.entries(values.test_standard_ranges || {})) {
    if (!testStandardRanges[key]) testStandardRanges[key] = { min: '', max: '' }
    testStandardRanges[key] = {
      ...testStandardRanges[key],
      ...(range && typeof range === 'object' ? range : {}),
    }
  }
  Object.assign(form, {
    ...form,
    ...values,
    tests: normalizeTestBucket(values.tests || form.tests),
    test_method_map: normalizeTestMethodMap(values.test_method_map || form.test_method_map),
    production_unit: values.production_unit || 'PCS',
    sample_unit: values.sample_unit || 'PCS',
    hardness_inspection_methods: {
      ...form.hardness_inspection_methods,
      ...(values.hardness_inspection_methods || {}),
    },
    test_standard_ranges: testStandardRanges,
    coating_thickness_spec: {
      ...form.coating_thickness_spec,
      ...(values.coating_thickness_spec || {}),
    },
    salt_spray_spec: saltSpraySpec,
    test_methods: {
      ...form.test_methods,
      ...(values.test_methods || {})
    },
    report: {
      ...form.report,
      ...(values.report || {}),
      needs: reportNeed,
      customer_report_logo: reportNeed === 'TAF認證標誌' ? 'with_logo' : 'without_logo',
    },
    outsource: {
      ...form.outsource,
      ...(values.outsource || {})
    },
    approval: {
      ...form.approval,
      ...(values.approval || {})
    }
  })
  form.tests.functional = (Array.isArray(form.tests.functional) ? form.tests.functional : [])
    .filter(x => String(x || '').trim() !== '功能測試')
  syncCurrentSharedOptionValues()
}

async function resetFormForNew() {
  Object.assign(form, createBlankLabForm())
  state.selectedCustomerRefno = ''
  state.formId = ''
  attachmentState.files = []
  localStorage.removeItem('lab_form_id')
  syncAllTestMethods()
  await refreshLabNoPreview()
}

async function newLabForm() {
  await resetFormForNew()
  if (Object.keys(route.query || {}).length) {
    await router.replace({ name: 'lab', query: {} })
  }
  ElMessage.success('已切換為新的委託測試單')
}

async function importLabFormFrom(sourceFormId) {
  const formId = String(sourceFormId || '').trim()
  if (!formId) return false

  try {
    const resp = await fetch(api(`lab/instances/${encodeURIComponent(formId)}`), {
      credentials: 'include'
    })
    const json = await resp.json()
    if (!resp.ok || !json.ok || !json.form) {
      throw new Error(json.msg || '讀取來源委託單失敗')
    }

    const sourceValues = {
      ...(json.form.values || {}),
      filled_date: todayStr,
      lab_no: '',
    }
    Object.assign(form, createBlankLabForm())
    state.selectedCustomerRefno = ''
    state.formId = ''
    attachmentState.files = []
    localStorage.removeItem('lab_form_id')
    assignFormValues(sourceValues)
    await syncSelectedCustomerFromForm()
    form.filled_date = todayStr
    form.lab_no = ''
    syncAllTestMethods()
    await refreshLabNoPreview()
    await router.replace({ name: 'lab', query: {} }).catch(() => {})
    ElMessage.success('已匯入前單內容並產生新委託編號，請修改後儲存為新委託單')
    return true
  } catch (e) {
    console.error(e)
    ElMessage.error(e.message || '匯入委託單失敗')
    return false
  }
}

async function searchPreviousByPartOrPrint() {
  const partNo = String(form.part_no || '').trim()
  const drawingNo = String(form.report?.rule_drawing || '').trim()
  const lookupKey = `${partNo}|${drawingNo}|${state.formId || ''}`
  if (!partNo && !drawingNo) {
    previousLookup.matches = []
    previousLookup.lastKey = ''
    return
  }
  if (previousLookup.lastKey === lookupKey) return

  previousLookup.loading = true
  previousLookup.lastKey = lookupKey
  try {
    const q = new URLSearchParams({ limit: '10', include_unreleased: '1' })
    if (partNo) q.set('part_no', partNo)
    if (drawingNo) q.set('drawing_no', drawingNo)
    const resp = await fetch(api(`lab/instances/search?${q.toString()}`), {
      credentials: 'include'
    })
    const json = await resp.json().catch(() => ({}))
    if (!resp.ok || json?.ok === false) {
      throw new Error(json?.msg || '查詢前單失敗')
    }
    previousLookup.matches = (Array.isArray(json.rows) ? json.rows : [])
      .filter(row => String(row.form_id || '') !== String(state.formId || ''))
      .slice(0, 5)
  } catch (e) {
    previousLookup.matches = []
    ElMessage.warning(e.message || '查詢前單失敗')
  } finally {
    previousLookup.loading = false
  }
}

async function ensureTemplateId() {
  const currentTemplateId = String(state.templateId || '').trim()
  const looksLikeUuid = /^[0-9a-f]{32}$/i.test(currentTemplateId)
  if (looksLikeUuid) return currentTemplateId

  const resp = await fetch(api('lab/st-init/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      name: state.templateName,
      docx: state.templateDocx,
      strategy: 'vars'
    })
  })

  const contentType = String(resp.headers.get('content-type') || '')
  if (!contentType.includes('application/json')) {
    const text = await resp.text().catch(() => '')
    throw new Error(text ? `template 初始化失敗：${text.slice(0, 120)}` : 'template 初始化失敗：非 JSON 回應')
  }

  const json = await resp.json()
  if (!json.ok || !json.template_id) {
    throw new Error(json.msg || 'template 初始化失敗')
  }

  state.templateId = json.template_id
  localStorage.setItem('lab_template_id', json.template_id)
  return json.template_id
}

async function loadSavedForm() {
  if (!state.formId) return

  try {
    const resp = await fetch(api(`lab/instances/${state.formId}`), {
      credentials: 'include'
    })
    const json = await resp.json()

    if (!json.ok || !json.form) {
      localStorage.removeItem('lab_form_id')
      state.formId = ''
      return
    }

    if (json.form.template_id) {
      state.templateId = json.form.template_id
      localStorage.setItem('lab_template_id', json.form.template_id)
    }

    assignFormValues(json.form.values || {})
    await syncSelectedCustomerFromForm()
    await loadDrawingAttachments()
  } catch (e) {
    console.error(e)
  }
}

async function loadDrawingAttachments() {
  if (!state.formId) {
    attachmentState.files = []
    return
  }
  attachmentState.loading = true
  try {
    const resp = await fetch(api(`lab/instances/${encodeURIComponent(state.formId)}/attachments`), {
      credentials: 'include',
    })
    const json = await resp.json().catch(() => ({}))
    if (!resp.ok || json?.ok === false) {
      throw new Error(json?.msg || '附圖載入失敗')
    }
    attachmentState.files = Array.isArray(json.files) ? json.files : []
  } catch (e) {
    attachmentState.files = []
    console.error(e)
  } finally {
    attachmentState.loading = false
  }
}

async function chooseDrawingAttachment() {
  if (!state.formId) {
    const ok = await saveDraftReal()
    if (!ok || !state.formId) {
      ElMessage.warning('請先儲存委託單後再上傳附圖')
      return
    }
  }
  drawingAttachmentInput.value?.click()
}

async function uploadDrawingAttachment(event) {
  const file = event?.target?.files?.[0]
  if (event?.target) event.target.value = ''
  if (!file || !state.formId) return
  attachmentState.uploading = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const resp = await fetch(api(`lab/instances/${encodeURIComponent(state.formId)}/attachments`), {
      method: 'POST',
      credentials: 'include',
      body: fd,
    })
    const json = await resp.json().catch(() => ({}))
    if (!resp.ok || json?.ok === false) {
      throw new Error(json?.msg || '附圖上傳失敗')
    }
    form.report.rule_has_drawing = true
    await loadDrawingAttachments()
    ElMessage.success('附圖已上傳')
  } catch (e) {
    ElMessage.error(e.message || '附圖上傳失敗')
  } finally {
    attachmentState.uploading = false
  }
}

function openAttachment(file) {
  const url = String(file?.url || '').trim()
  if (!url) return
  window.open(url, '_blank', 'noopener')
}

async function chooseApprovalSignature(kind) {
  if (kind === 'manager' && !isSupervisorUser.value) {
    ElMessage.warning('主管審核簽名檔需由主管上傳')
    return
  }
  if (!state.formId) {
    const ok = await saveDraftReal()
    if (!ok || !state.formId) {
      ElMessage.warning('請先儲存委託單後再上傳簽名檔')
      return
    }
  }
  if (kind === 'customer') customerSignatureInput.value?.click()
  if (kind === 'manager') managerSignatureInput.value?.click()
}

async function uploadApprovalSignature(kind, event) {
  const file = event?.target?.files?.[0]
  if (event?.target) event.target.value = ''
  if (!file || !state.formId) return
  if (kind === 'manager' && !isSupervisorUser.value) {
    ElMessage.warning('主管審核簽名檔需由主管上傳')
    return
  }

  signatureState.uploading = kind
  try {
    const fd = new FormData()
    fd.append('file', file)
    const resp = await fetch(api(`lab/instances/${encodeURIComponent(state.formId)}/attachments`), {
      method: 'POST',
      credentials: 'include',
      body: fd,
    })
    const json = await resp.json().catch(() => ({}))
    if (!resp.ok || json?.ok === false) {
      throw new Error(json?.msg || '簽名檔上傳失敗')
    }
    const uploaded = json.file || {}
    const savedFile = {
      name: uploaded.name || file.name,
      size: uploaded.size || file.size,
      url: `/ai/api/lab/instances/${encodeURIComponent(state.formId)}/attachments/${encodeURIComponent(uploaded.name || file.name)}`,
    }
    if (kind === 'customer') {
      form.approval.customer_signature_file = savedFile
      form.approval.customer_signature_checked = true
      if (!form.approval.customer_signature_date) form.approval.customer_signature_date = todayStr
    }
    if (kind === 'manager') {
      form.approval.manager_signature_file = savedFile
      form.approval.manager_approval_checked = true
      if (!form.approval.manager_approval_date) form.approval.manager_approval_date = todayStr
    }
    await saveDraftReal()
    await loadDrawingAttachments()
    ElMessage.success('簽名檔已上傳')
  } catch (e) {
    ElMessage.error(e.message || '簽名檔上傳失敗')
  } finally {
    signatureState.uploading = ''
  }
}

async function syncFormIdFromRoute() {
  const routeFormId = String(route.query.form_id || '').trim()
  if (!routeFormId) {
    if (state.formId) await resetFormForNew()
    return false
  }
  if (routeFormId === state.formId) return true
  state.formId = routeFormId
  localStorage.setItem('lab_form_id', routeFormId)
  await loadSavedForm()
  return true
}

async function refreshLabNoPreview() {
  if (state.formId) return
  try {
    const filledDate = String(form.filled_date || todayStr)
    const qs = new URLSearchParams({
      filled_date: filledDate,
    }).toString()
    const resp = await fetch(api(`lab/next-lab-no?${qs}`), {
      credentials: 'include',
    })
    const json = await resp.json()
    if (json.ok && json.lab_no) {
      form.lab_no = json.lab_no
    }
  } catch (e) {
    console.error(e)
  }
}

function openLabView() {
  router.push({ name: 'lab_view' })
}

function openLabImport() {
  router.push({ name: 'lab_view', query: { pick: 'import' } })
}

function openLabQuoteManage() {
  router.push({ name: 'lab_quote_manage' })
}

function isLabFormReleased() {
  const approval = form.approval || {}
  return Boolean(
    approval.customer_signature_checked &&
    approval.customer_signature_date &&
    approval.manager_approval_checked &&
    approval.manager_approval_date
  )
}

function cloneTestConfigCategories(categories = []) {
  return (Array.isArray(categories) ? categories : []).map(cate => ({
    ...cate,
    items: Array.isArray(cate.items)
      ? cate.items
        .filter(item => !(cate.key === 'functional' && String(item?.name || '').trim() === '功能測試'))
        .map(item => ({
          ...item,
          methods: Array.isArray(item.methods) ? [...item.methods] : [],
          methods_text: String(item.methods_text || ''),
        }))
      : [],
  }))
}

function selectedMethodsForItem(itemId) {
  return Array.isArray(form.test_method_map?.[String(itemId)])
    ? form.test_method_map[String(itemId)]
    : []
}

function otherCategoryItem(cate) {
  return Array.isArray(cate?.items) && cate.items.length ? cate.items[0] : null
}

function otherCategoryMethods(cate) {
  const item = otherCategoryItem(cate)
  return Array.isArray(item?.methods) ? item.methods : []
}

function selectedMethodsForOther(cate) {
  const item = otherCategoryItem(cate)
  return item?.item_id ? selectedMethodsForItem(item.item_id) : []
}

function selectedTestMethodsText(categoryKey) {
  const selected = Array.isArray(form.tests?.[categoryKey]) ? form.tests[categoryKey] : []
  const cate = (state.testConfigCategories || []).find(x => x.key === categoryKey)
  if (!cate || !selected.length) return ''

  if (categoryKey === 'other') {
    const item = otherCategoryItem(cate)
    const selectedMethods = item?.item_id ? selectedMethodsForItem(item.item_id) : []
    return selectedMethods.join('、')
  }

  const blocks = []
  for (const item of cate.items || []) {
    if (!selected.includes(item.name)) continue
    const selectedMethods = selectedMethodsForItem(item.item_id)
    const lines = []
    if (selectedMethods.length) lines.push(`${item.name}：${selectedMethods.join('、')}`)
    if (categoryKey === 'mechanical' && item.name === '心部硬度' && form.hardness_inspection_methods.core) {
      lines.push(`心部硬度檢測方式：${form.hardness_inspection_methods.core}`)
    }
    if (categoryKey === 'mechanical' && item.name === '表面硬度' && form.hardness_inspection_methods.surface) {
      lines.push(`表面硬度檢測方式：${form.hardness_inspection_methods.surface}`)
    }
    if (['mechanical', 'functional'].includes(categoryKey)) {
      const range = form.test_standard_ranges?.[testStandardKey(item.name)] || {}
      if (range.min !== '' || range.max !== '') {
        lines.push(`標準值：${range.min || '-'} - ${range.max || '-'}`)
      }
    }
    if (categoryKey === 'surface' && item.name === '電鍍膜厚') {
      const spec = form.coating_thickness_spec
      if (spec.min || spec.max) lines.push(`膜厚標準：${spec.min || '-'} - ${spec.max || '-'} ${spec.unit || ''}`.trim())
    }
    if (categoryKey === 'surface' && item.name === '鹽水噴霧') {
      const salt = form.salt_spray_spec
      if (salt.white_hours) lines.push(`無白鏽：${salt.white_hours} H`)
      if (salt.red_hours) lines.push(`無紅鏽：${salt.red_hours} H`)
      if (salt.other) lines.push(`鹽霧其它：${salt.other}`)
    }
    if (lines.length) blocks.push(lines.join('\n'))
  }
  return blocks.join('\n')
}

function syncCategoryTestMethods(categoryKey) {
  form.test_methods[categoryKey] = selectedTestMethodsText(categoryKey)
}

function syncAllTestMethods() {
  for (const cate of state.testConfigCategories || []) {
    syncCategoryTestMethods(cate.key)
  }
}

function syncTestMethodsByName() {
  const out = {}
  for (const cate of state.testConfigCategories || []) {
    for (const item of cate.items || []) {
      const methods = selectedMethodsForItem(item.item_id)
      if (methods.length) out[item.name] = [...methods]
    }
  }
  form.test_method_by_name = out
}

async function saveDraftReal() {
  state.saving = true

  try {
    form.report.customer_report_logo = form.report.needs === 'TAF認證標誌'
      ? 'with_logo'
      : 'without_logo'
    form.salt_spray_hours = form.salt_spray_spec.white_hours || form.salt_spray_spec.red_hours || ''
    form.salt_spray_type = form.salt_spray_spec.white_hours && form.salt_spray_spec.red_hours
      ? '白鏽、紅鏽'
      : form.salt_spray_spec.white_hours
        ? '白鏽'
        : form.salt_spray_spec.red_hours
          ? '紅鏽'
          : ''
    form.salt_spray_other = form.salt_spray_spec.other || ''
    syncAllTestMethods()
    syncTestMethodsByName()
    await Promise.all([
      ensureSharedOption('material_no', form.material_no),
      ensureSharedOption('plating_cate', form.platingCate),
      ensureSharedOption('plating_fac', form.platingFac),
      ensureSharedOption('rule_spec', form.report?.rule_spec),
    ])

    const templateId = await ensureTemplateId()
    const isUpdate = Boolean(state.formId)
    const payload = {
      template_id: templateId,
      values: { ...form }
    }
    const url = isUpdate ? api(`lab/instances/${state.formId}`) : api('lab/instances/')
    const resp = await fetch(url, {
      method: isUpdate ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      credentials: 'include'
    })

    const json = await resp.json()

    if (!json.ok) {
      throw new Error(json.msg || '儲存失敗')
    }

    // 保存 form_id
    if (json.form_id) {
      state.formId = json.form_id
      localStorage.setItem('lab_form_id', json.form_id)
      if (String(route.query.form_id || '') !== json.form_id) {
        router.replace({
          name: 'lab',
          query: { ...route.query, form_id: json.form_id },
        }).catch(() => {})
      }
      await loadDrawingAttachments()
    }

    // ✅ 後端產生的委託編號
    if (json.lab_no) {
      form.lab_no = json.lab_no
    }

    ElMessage.success(isUpdate ? '更新成功' : '儲存成功')
    return true

  } catch (e) {
    console.error(e)
    ElMessage.error(e.message || '儲存失敗')
    return false
  } finally {
    state.saving = false
  }
}
async function exportDocxReal() {
  state.exporting = true
  try {
    const saveOk = await saveDraftReal()
    if (!saveOk || !state.formId) throw new Error('儲存失敗，無法匯出')

    const buildUrl = api(`lab/instances/${state.formId}/export-docx/`)
    const resp = await fetch(buildUrl, {
      method: 'POST',
      credentials: 'include'
    })
    const json = await resp.json()
    if (!json.ok) throw new Error(json.msg || '產檔失敗')

    // ✅ 用 top window 觸發下載，避開 iframe 的「需要權限」
    window.top.location.href = json.download_url

    ElMessage.success('正在準備下載...')
  } catch (e) {
    ElMessage.error(`匯出失敗：${e.message}`)
  } finally {
    state.exporting = false
  }
}

async function deleteCurrentForm() {
  const formId = String(state.formId || '').trim()
  if (!formId) {
    ElMessage.warning('尚未儲存，沒有可刪除的委託單')
    return false
  }
  if (!window.confirm('確定要刪除此委託測試單？此動作無法復原。')) {
    return false
  }

  state.deleting = true
  try {
    const resp = await fetch(api(`lab/instances/${formId}`), {
      method: 'DELETE',
      credentials: 'include',
    })
    const contentType = String(resp.headers.get('content-type') || '')
    if (!contentType.includes('application/json')) {
      const text = await resp.text().catch(() => '')
      throw new Error(text ? text.slice(0, 120) : '刪除失敗：非 JSON 回應')
    }
    const json = await resp.json()
    if (!resp.ok || json?.ok === false) {
      throw new Error(json?.msg || `HTTP ${resp.status}`)
    }

    localStorage.removeItem('lab_form_id')
    state.formId = ''
    ElMessage.success('刪除成功')
    router.push({ name: 'lab_view' })
    return true
  } catch (e) {
    console.error(e)
    ElMessage.error(e.message || '刪除失敗')
    return false
  } finally {
    state.deleting = false
  }
}

async function exportCustomerReport() {
  state.exportingCustomerReport = true
  try {
    const saveOk = await saveDraftReal()
    if (!saveOk || !state.formId) throw new Error('儲存失敗，無法匯出')

    const resp = await fetch(api(`lab/final-report/forms/${state.formId}/export-docx`), {
      method: 'POST',
      credentials: 'include'
    })

    if (!resp.ok) {
      let message = '匯出客戶報告失敗'
      try {
        const json = await resp.json()
        message = json.msg || json.error || message
      } catch (_) {
        // 非 JSON 錯誤時，保留預設訊息
      }
      throw new Error(message)
    }

    const reportNo = String(resp.headers.get('X-Report-No') || '').trim()
    const blob = await resp.blob()
    const safePart = (value) => String(value || '')
      .trim()
      .replace(/[\\/:*?"<>|]+/g, '-')
      .replace(/\s+/g, ' ')
      .slice(0, 60)
    const datePart = String(form.filled_date || todayStr).replace(/-/g, '')
    const nameParts = [
      safePart(form.customer_name),
      safePart(reportNo || form.lab_no),
      datePart,
      '客戶報告'
    ].filter(Boolean)
    const downloadName = `${nameParts.join('_')}.docx`
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = downloadName
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)

    ElMessage.success('客戶報告匯出成功')
  } catch (e) {
    ElMessage.error(`匯出失敗：${e.message}`)
  } finally {
    state.exportingCustomerReport = false
  }
}

async function loadCustomers() {
  try {
    const resp = await fetch(api('customer/list?pageSize=100'), {
      credentials: 'include',
    })
    const json = await resp.json()
    if (json.ok) {
      state.customers = json.rows || json.data?.rows || []
      await syncSelectedCustomerFromForm()
    }
  } catch (e) { console.error(e) }
}

function findCustomerForForm(values = form, customers = state.customers) {
  const list = Array.isArray(customers) ? customers : []
  const refno = String(values.customer_refno || '').trim()
  const customerId = String(values.customer_id ?? '').trim()
  const taxId = String(values.tax_id || '').trim().toLowerCase()
  const company = String(values.customer_name || '').trim().toLowerCase()

  return list.find(c => refno && String(c.refno || '').trim() === refno)
    || list.find(c => customerId && String(c.id ?? '').trim() === customerId)
    || list.find(c => {
      const candidateTaxId = String(c.tax_id || c.licenceNo || c.LicenceNo || '').trim().toLowerCase()
      return taxId && candidateTaxId === taxId
    })
    || list.find(c => company && String(c.company || '').trim().toLowerCase() === company)
    || null
}

async function syncSelectedCustomerFromForm() {
  if (!form.customer_refno && !form.customer_id && !form.tax_id && !form.customer_name) {
    state.selectedCustomerRefno = ''
    return
  }

  let customer = findCustomerForForm()
  if (!customer) {
    const keyword = String(form.customer_refno || form.tax_id || form.customer_name || '').trim()
    if (keyword) {
      try {
        const q = new URLSearchParams({ page: '1', pageSize: '20', kw: keyword })
        const resp = await fetch(api(`customer/list?${q.toString()}`), {
          credentials: 'include',
        })
        const json = await resp.json().catch(() => ({}))
        const rows = json.ok ? (json.rows || json.data?.rows || []) : []
        for (const row of rows) {
          if (!state.customers.some(c => String(c.refno) === String(row.refno))) {
            state.customers.push(row)
          }
        }
        customer = findCustomerForForm(form, rows) || findCustomerForForm()
      } catch (e) {
        console.error(e)
      }
    }
  }

  if (!customer?.refno) {
    state.selectedCustomerRefno = ''
    return
  }
  state.selectedCustomerRefno = String(customer.refno)
  form.customer_refno = String(customer.refno)
  if (customer.id != null && customer.id !== '') form.customer_id = customer.id
}

async function loadTestConfig() {
  try {
    const resp = await fetch(api('lab/test-config'), {
      credentials: 'include',
    })
    const json = await resp.json()
    if (!json.ok) throw new Error(json.msg || '試驗項目設定載入失敗')
    state.testConfigCategories = cloneTestConfigCategories(json.categories || [])
    syncAllTestMethods()
  } catch (e) {
    console.error(e)
    ElMessage.warning(e.message || '試驗項目設定載入失敗')
  }
}

async function loadSharedOptions(key) {
  try {
    const resp = await fetch(api(`lab/shared-options/${key}`), {
      credentials: 'include',
    })
    const json = await resp.json()
    const list = json.ok && Array.isArray(json.data) ? json.data : []
    if (key === 'material_no') state.materialOptions = list
    if (key === 'heat_no') state.heatOptions = list
    if (key === 'plating_cate') state.platingCateOptions = list
    if (key === 'plating_fac') state.platingFacOptions = list
    if (key === 'rule_spec') state.ruleSpecOptions = list
    syncCurrentSharedOptionValues()
  } catch (e) {
    console.error(e)
  }
}

function upsertLocalSharedOption(key, value) {
  const text = String(value || '').trim()
  if (!text) return
  const prop =
    key === 'material_no'
      ? 'materialOptions'
      : key === 'heat_no'
        ? 'heatOptions'
        : key === 'plating_cate'
          ? 'platingCateOptions'
          : key === 'plating_fac'
            ? 'platingFacOptions'
            : 'ruleSpecOptions'
  const list = Array.isArray(state[prop]) ? [...state[prop]] : []
  if (!list.some(x => String(x?.value || '').trim() === text)) {
    list.push({ value: text, label: text })
    list.sort((a, b) => String(a.label || '').localeCompare(String(b.label || ''), 'zh-Hant'))
    state[prop] = list
  }
}

function syncCurrentSharedOptionValues() {
  upsertLocalSharedOption('material_no', form.material_no)
  upsertLocalSharedOption('plating_cate', form.platingCate)
  upsertLocalSharedOption('plating_fac', form.platingFac)
  upsertLocalSharedOption('rule_spec', form.report?.rule_spec)
}

function replaceLocalSharedOption(key, oldValue, newValue) {
  const prop =
    key === 'material_no'
      ? 'materialOptions'
      : key === 'heat_no'
        ? 'heatOptions'
        : key === 'plating_cate'
          ? 'platingCateOptions'
          : key === 'plating_fac'
            ? 'platingFacOptions'
            : 'ruleSpecOptions'
  const oldText = String(oldValue || '').trim()
  const newText = String(newValue || '').trim()
  const list = Array.isArray(state[prop]) ? [...state[prop]] : []
  const next = list.map(item => {
    if (String(item?.value || '').trim() !== oldText) return item
    return { value: newText, label: newText }
  })
  state[prop] = next.sort((a, b) => String(a.label || '').localeCompare(String(b.label || ''), 'zh-Hant'))
}

async function ensureSharedOption(key, value) {
  const text = String(value || '').trim()
  if (!text) return
  upsertLocalSharedOption(key, text)
  try {
    const resp = await fetch(api(`lab/shared-options/${key}`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ label: text }),
    })
    if (resp.status === 409) return
    const json = await resp.json().catch(() => ({}))
    if (!resp.ok || json?.ok === false) {
      throw new Error(json?.msg || `HTTP ${resp.status}`)
    }
  } catch (e) {
    console.error(e)
    ElMessage.warning(`${sharedOptionTitle(key)}共用清單儲存失敗：${e.message || e}`)
  }
}

async function onSharedOptionSelected(key, value) {
  const text = String(value || '').trim()
  if (!text) return
  await ensureSharedOption(key, text)
}

function onTestSelectionChanged(categoryKey) {
  syncCategoryTestMethods(categoryKey)
}

function sharedOptionTitle(key) {
  if (key === 'material_no') return '材質編號'
  if (key === 'heat_no') return '爐號'
  if (key === 'plating_cate') return '電鍍別'
  if (key === 'plating_fac') return '廠商'
  return '法規標準'
}

function sharedOptionListByKey(key) {
  if (key === 'material_no') return [...state.materialOptions]
  if (key === 'heat_no') return [...state.heatOptions]
  if (key === 'plating_cate') return [...state.platingCateOptions]
  if (key === 'plating_fac') return [...state.platingFacOptions]
  return [...state.ruleSpecOptions]
}

function openSharedOptionEditor(key) {
  sharedOptionEditor.key = key
  sharedOptionEditor.title = sharedOptionTitle(key)
  sharedOptionEditor.list = sharedOptionListByKey(key)
  sharedOptionEditor.selected = ''
  sharedOptionEditor.input = ''
  sharedOptionEditor.open = true
}

function isTestItemSelected(categoryKey, itemName) {
  return Array.isArray(form.tests?.[categoryKey]) && form.tests[categoryKey].includes(itemName)
}

function toggleTestItem(categoryKey, itemName, checked) {
  const list = Array.isArray(form.tests?.[categoryKey]) ? [...form.tests[categoryKey]] : []
  const has = list.includes(itemName)
  if (checked && !has) list.push(itemName)
  if (!checked && has) {
    const next = list.filter(x => x !== itemName)
    form.tests[categoryKey] = next
  } else {
    form.tests[categoryKey] = list
  }
  syncCategoryTestMethods(categoryKey)
}

function updateMethodsForItem(categoryKey, item, values) {
  form.test_method_map[String(item.item_id)] = Array.isArray(values)
    ? values.map(x => String(x || '').trim()).filter(Boolean)
    : []
  syncCategoryTestMethods(categoryKey)
}

function updateMethodsForOther(cate, values) {
  const item = otherCategoryItem(cate)
  if (!item?.item_id) return
  const list = Array.isArray(values)
    ? values.map(x => String(x || '').trim()).filter(Boolean)
    : []
  form.test_method_map[String(item.item_id)] = list
  form.tests.other = list.length ? ['其他'] : []
  syncCategoryTestMethods('other')
}

function openTestMethodEditor(item, cate) {
  testMethodEditor.item_id = item?.item_id || null
  testMethodEditor.cate_key = cate?.key || ''
  testMethodEditor.item_name = item?.name || ''
  testMethodEditor.title = `${cate?.label || ''} / ${item?.name || ''} / 試驗方法`
  const lines = String(item?.methods_text || '')
    .replace(/\r/g, '')
    .split('\n')
    .map(x => x.trim())
    .filter(Boolean)
  testMethodEditor.methods = lines.length ? lines : ['']
  testMethodEditor.open = true
}

function closeTestMethodEditor() {
  testMethodEditor.open = false
  testMethodEditor.saving = false
  testMethodEditor.item_id = null
  testMethodEditor.cate_key = ''
  testMethodEditor.item_name = ''
  testMethodEditor.title = ''
  testMethodEditor.methods = ['']
}

function addTestMethodRow() {
  testMethodEditor.methods.push('')
}

function removeTestMethodRow(idx) {
  if (testMethodEditor.methods.length <= 1) return
  testMethodEditor.methods.splice(idx, 1)
}

async function saveTestMethodEditor() {
  testMethodEditor.saving = true
  try {
    const methodLines = testMethodEditor.methods
      .map(x => String(x || '').trim())
      .filter(Boolean)
    const items = [{
      item_id: testMethodEditor.item_id,
      methods_text: methodLines.join('\n'),
    }]

    const resp = await fetch(api('lab/test-config/methods'), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ items }),
    })
    const json = await resp.json().catch(() => ({}))
    if (!resp.ok || json?.ok === false) {
      throw new Error(json?.msg || `HTTP ${resp.status}`)
    }

    await loadTestConfig()
    syncAllTestMethods()
    closeTestMethodEditor()
    ElMessage.success('試驗方法已更新')
  } catch (e) {
    console.error(e)
    ElMessage.error(e.message || '試驗方法更新失敗')
  } finally {
    testMethodEditor.saving = false
  }
}

function closeSharedOptionEditor() {
  sharedOptionEditor.open = false
  sharedOptionEditor.key = ''
  sharedOptionEditor.title = ''
  sharedOptionEditor.list = []
  sharedOptionEditor.selected = ''
  sharedOptionEditor.input = ''
  sharedOptionEditor.saving = false
}

function pickSharedOption(item) {
  sharedOptionEditor.selected = String(item?.value || '')
  sharedOptionEditor.input = String(item?.label || item?.value || '')
}

async function submitSharedOptionEditor() {
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
      const resp = await fetch(api(`lab/shared-options/${key}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ value: oldValue, label: text }),
      })
      const json = await resp.json().catch(() => ({}))
      if (resp.status === 409) throw new Error(json?.msg || '新名稱已存在')
      if (!resp.ok || json?.ok === false) {
        throw new Error(json?.msg || `HTTP ${resp.status}`)
      }
      replaceLocalSharedOption(key, oldValue, text)
      if (key === 'material_no' && form.material_no === oldValue) form.material_no = text
      if (key === 'heat_no' && form.heat_no === oldValue) form.heat_no = text
      if (key === 'plating_cate' && form.platingCate === oldValue) form.platingCate = text
      if (key === 'plating_fac' && form.platingFac === oldValue) form.platingFac = text
      if (key === 'rule_spec' && form.report.rule_spec === oldValue) form.report.rule_spec = text
      ElMessage.success(`${sharedOptionEditor.title}已修改`)
    } else {
      await ensureSharedOption(key, text)
      if (key === 'material_no') form.material_no = text
      if (key === 'heat_no') form.heat_no = text
      if (key === 'plating_cate') form.platingCate = text
      if (key === 'plating_fac') form.platingFac = text
      if (key === 'rule_spec') form.report.rule_spec = text
      ElMessage.success(`${sharedOptionEditor.title}已新增`)
    }

    await loadSharedOptions(key)
    sharedOptionEditor.list = sharedOptionListByKey(key)
    closeSharedOptionEditor()
  } catch (e) {
    console.error(e)
    ElMessage.error(e.message || `${sharedOptionEditor.title}處理失敗`)
  } finally {
    sharedOptionEditor.saving = false
  }
}

async function onCustomerSelected(v) {
  const c = state.customers.find(x => String(x.refno) === v)
  if (c) {
    form.customer_id = c.id ?? null
    form.customer_refno = String(c.refno || '')
    form.customer_name = c.company || ''
    form.tax_id = c.tax_id || c.licenceNo || c.LicenceNo || ''
    form.address = c.address || c.Address || ''
    form.contact_name = c.contact_name || c.contact || ''
    form.contact_tel = c.contact_tel || c.tel || ''
    form.contact_fax = c.contact_fax || c.fax || ''
    form.contact_email = c.contact_email || c.email || ''
  }
}

function clearCustomer() {
  state.selectedCustomerRefno = ''
  form.customer_id = null
  form.customer_refno = ''
}

function openCustomerCreate() {
  const url = new URL(`${BASE_URL}#/customer_create`, window.location.origin)
  window.open(url.toString(), '_blank', 'noopener')
}

function onWindowFocus() {
  loadCustomers()
}

async function ensureSourceReady() {
  if (!state.formId || !form.lab_no) {
    const ok = await saveDraftReal()
    if (!ok || !state.formId || !form.lab_no) {
      throw new Error('請先完成儲存，並取得委託編號後再開啟')
    }
  }
  if (!isLabFormReleased()) {
    throw new Error('委託方簽名與主管審核都需勾選並填日期，委託單成立後才能開啟尺寸/機械性質表')
  }
}

async function openInspectValues() {
  try {
    await ensureSourceReady()
    router.push({
      name: 'lab_qet',
      query: { source_form_id: state.formId }
    })
  } catch (e) {
    ElMessage.warning(e.message || '無法開啟尺寸原始記錄表')
  }
}

async function openInspectStandard() {
  try {
    await ensureSourceReady()
    router.push({
      name: 'lab_qet_standard',
      query: { source_form_id: state.formId }
    })
  } catch (e) {
    ElMessage.warning(e.message || '無法開啟設定尺寸原始記錄表')
  }
}

async function openLabMech() {
  try {
    await ensureSourceReady()
    router.push({
      name: 'lab_mech',
      query: { source_form_id: state.formId }
    })
  } catch (e) {
    ElMessage.warning(e.message || '無法開啟機械性質試驗表')
  }
}

async function openLabMechStandard() {
  try {
    await ensureSourceReady()
    router.push({
      name: 'lab_mech_standard',
      query: { source_form_id: state.formId }
    })
  } catch (e) {
    ElMessage.warning(e.message || '無法開啟設定機械性質檢驗記錄表')
  }
}

onMounted(async () => {
  window.addEventListener('focus', onWindowFocus)
  await Promise.all([
    loadCustomers(),
    loadSharedOptions('material_no'),
    loadSharedOptions('plating_cate'),
    loadSharedOptions('plating_fac'),
    loadSharedOptions('rule_spec'),
    loadTestConfig(),
    ensureTemplateId().catch(console.error)
  ])
  const copyFrom = String(route.query.copy_from || route.query.import_form_id || '').trim()
  if (copyFrom) {
    await importLabFormFrom(copyFrom)
  } else {
    await syncFormIdFromRoute()
  }
  syncAllTestMethods()
  await refreshLabNoPreview()
})

onUnmounted(() => {
  window.removeEventListener('focus', onWindowFocus)
})

watch(() => form.filled_date, async () => {
  await refreshLabNoPreview()
})

watch(
  () => route.query.form_id,
  async () => {
    await syncFormIdFromRoute()
  }
)

watch(
  () => [route.query.copy_from, route.query.import_form_id],
  async ([copyFrom, importFormId]) => {
    const sourceFormId = String(copyFrom || importFormId || '').trim()
    if (sourceFormId) await importLabFormFrom(sourceFormId)
  }
)
</script>


<style scoped>
.lab-secondary-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.lab-secondary-actions :deep(.el-button) {
  margin-left: 0;
  background: #f3f4f6;
  border-color: #d1d5db;
  color: #374151;
}

.lab-secondary-actions :deep(.el-button:hover),
.lab-secondary-actions :deep(.el-button:focus) {
  background: #e5e7eb;
  border-color: #cbd5e1;
  color: #111827;
}

:global(.el-input__wrapper),
:global(.el-select__wrapper),
:global(.el-textarea__inner) {
  /* 讓高度與內距比較一致（文字不會掉到底） */
  --el-input-height: 38px;
}

:global(.el-input__inner),
:global(.el-select__selected-item),
:global(.el-textarea__inner) {
  line-height: 1.4;
}

/* 移除 focus 時那種淡藍色區域/內陰影 */
:global(.el-input.is-focus .el-input__wrapper),
:global(.el-select.is-focus .el-select__wrapper),
:global(.el-textarea.is-focus .el-textarea__inner),
:global(.el-input__wrapper.is-focus),
:global(.el-select__wrapper.is-focus) {
  box-shadow: none !important;
  background-color: #fff !important;
}

/* 讓 input 文字不要太靠下：微調 padding */
:global(.el-input__inner) {
  padding-top: 6px !important;
  padding-bottom: 6px !important;
}

:global(.el-textarea__inner) {
  padding-top: 10px !important;
  padding-bottom: 10px !important;
}
@media (max-width: 639px) {
  :global(body) {
    padding-bottom: 84px;
  }
}
</style>
