# 委託單 Workflow 開發規格

日期：2026-07-14

## 一、需求背景

客戶希望在委託單流程中新增一個主管可見的狀態下拉選單，用來控制委託單從臨時建立、樣品確認、正式成立，到主管審核完成的流程。

同時系統需支援：

- 一登入就先抓取登入者簽名檔
- 依狀態自動帶入簽名檔與日期
- 依 `有 logo / 無 logo` 與流程階段自動產生不同編號
- 委託單匯出時自動抓取 `staff.dep_manager = 1` 員工簽名，不要求上傳
- 客戶報告匯出時使用固定 Charles 簽名檔

## 二、流程定義

### 2.1 狀態下拉選單

委託單新增一個欄位，僅主管可見：

1. `臨時(預設)`
2. `收到樣品/確認/有logo`
3. `收到樣品/確認/無logo`
4. `主管審核完成`

### 2.2 使用流程

1. 新增委託測試單
2. 預設狀態為 `臨時(預設)`
3. 收到樣品並確認時，主管選擇：
   - `收到樣品/確認/有logo`
   - 或 `收到樣品/確認/無logo`
4. 若選擇 `收到樣品/確認/無logo`
   - 系統自動帶入登入者簽名檔
   - 系統自動帶入日期
5. 檢驗完成後，主管切換為 `主管審核完成`
6. 報告匯出時附上主管簽名

## 三、編號規則

### 3.1 臨時編號

- 格式：`TYYYYMMDD-001`
- 規則：以當日流水碼計算

### 3.2 正式編號

當狀態由臨時轉為正式成立時產生：

- 有 logo：`YYYYMMDD-001`
- 無 logo：`AYYYYMMDD-001`

規則：

- 流水碼以當日計算
- 同日同類別累加

### 3.3 報告號碼

主管審核完成後產生報告號：

- 有 logo：`YYYYMM-001`
- 無 logo：`RYYYYMMDD-001`

規則：

- 流水碼以當月計算
- 同月同類別累加

## 四、簽名規則

### 4.1 登入者簽名檔

登入後立即讀取：

```sql
select isnull(sign_e, sign_c) as signature from staff
```

簽名檔路徑：

`C:\inetpub\wwwroot\newweb2021\pic\itac\`

### 4.2 選項 3 自動行為

當主管選擇 `收到樣品/確認/無logo` 時：

- 自動綁定登入者簽名檔
- 自動寫入簽名日期

### 4.3 選項 4 自動行為

當主管選擇 `主管審核完成` 時：

- 報告附上固定主管簽名
- 不使用表單上傳的主管簽名檔
- 固定檔案：

`C:\inetpub\wwwroot\newweb2021\pic\itac\Eeid_Charles-ch.jpg`

客戶報告匯出前先檢查固定檔案是否存在；不存在時先警告並停止匯出，不得先產生 Word 再失敗。委託單匯出則檢查 `staff.dep_manager = 1` 員工的簽名檔。

## 五、後端 API 規格

### 5.1 取得狀態選單

`GET /api/lab/workflow/status-options`

回傳內容：

- 主管可見完整 4 項
- 非主管僅回傳 `臨時(預設)`

### 5.2 取得登入者簽名

`GET /api/lab/workflow/current-signature`

用途：

- 登入後自動抓取登入者簽名檔
- 作為選項 3 的預設簽名來源

### 5.3 更新委託單狀態

`POST /api/lab/workflow/form-status`

參數：

- `form_id`
- `status`

用途：

- 更新委託單 workflow 狀態
- 由前端狀態下拉呼叫

### 5.4 產生編號

`POST /api/lab/workflow/next-no`

參數：

- `kind`
  - `temp`
  - `formal`
  - `report`
- `has_logo`

用途：

- 產生臨時編號
- 產生正式編號
- 產生報告號碼

## 六、資料庫欄位

### 6.1 `dbo.lab_qet_form`

新增欄位：

- `workflow_status`
- `workflow_has_logo`
- `workflow_confirmed_by`
- `workflow_confirmed_at`
- `workflow_reviewed_by`
- `workflow_reviewed_at`
- `workflow_signature_file`
- `workflow_signature_date`
- `workflow_temp_no`
- `workflow_formal_no`
- `workflow_report_no`

### 6.2 編號流水表

使用：

- `dbo.lab_running_no`

儲存不同類別的流水碼。

## 七、前端需求

### 7.1 欄位顯示

- 委託單畫面增加一個下拉選單
- 僅主管可見
- 預設值為 `臨時(預設)`

### 7.2 狀態切換行為

#### 選項 1

- 不產生正式編號
- 保持臨時編號或尚未編號狀態

#### 選項 2

- 標記有 logo
- 產生正式編號

#### 選項 3

- 標記無 logo
- 自動帶入登入者簽名檔
- 自動帶入簽名日期
- 產生正式編號

#### 選項 4

- 標記主管審核完成
- 於客戶報告匯出時帶入 Charles 固定簽名
- 產生報告號

### 7.3 UI 顯示規則

- 非主管登入時不顯示此下拉
- 主管登入時顯示完整流程
- 簽名檔若已抓取成功，應顯示檔名或縮圖狀態

## 八、後端處理邏輯

### 8.1 狀態流轉

建議流轉：

- `TEMP` -> `RECEIVED_LOGO`
- `TEMP` -> `RECEIVED_NOLOGO`
- `RECEIVED_LOGO` -> `REVIEW_DONE`
- `RECEIVED_NOLOGO` -> `REVIEW_DONE`

### 8.2 自動帶值

若切換為 `RECEIVED_NOLOGO`：

- 自動寫入 `workflow_signature_file`
- 自動寫入 `workflow_signature_date`
- 自動記錄 `workflow_confirmed_by`

若切換為 `REVIEW_DONE`：

- 自動記錄 `workflow_reviewed_by`
- 自動記錄 `workflow_reviewed_at`

### 8.3 報告輸出

匯出報告時：

- 若狀態為 `REVIEW_DONE`
- 客戶報告需在 Word 中插入 Charles 固定簽名；委託單 Word 則插入 `staff.dep_manager = 1` 員工簽名

## 九、驗收條件

1. 委託單主管登入後可看到 workflow 下拉選單
2. 非主管登入看不到此欄位
3. 選擇 `收到樣品/確認/無logo` 後，系統會自動帶入登入者簽名檔與日期
4. 登入後可取得 `staff.sign_e / staff.sign_c` 對應簽名
5. 新增委託單時可生成 `TYYYYMMDD-001`
6. 選擇有 logo 時可生成正式編號
7. 選擇無 logo 時可生成 `AYYYYMMDD-001`
8. 主管審核完成後可生成報告號
9. 報告匯出時會附上固定主管簽名

## 十、待確認事項

1. `staff` 資料表是否已正式存在 `sign_e` / `sign_c`
2. `有 logo` / `無 logo` 的判定是否只由 workflow 狀態控制
3. 報告號碼的 `YYYYMMDD` 格式是否固定維持日序號
4. 若同日同類別重送，是否要允許重取號或禁止重複

## 十一、建議實作順序

1. 先完成資料庫 migration
2. 再完成後端 workflow API
3. 再補前端委託單畫面的下拉與自動簽名
4. 最後補 Word 匯出簽名與報告號規則
