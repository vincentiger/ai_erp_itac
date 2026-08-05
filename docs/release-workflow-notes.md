# 發版與更新流程紀錄

## 目的

這份文件用來記錄目前專案的實際發版方式，避免之後再次混淆 `D:\ai_erp_itac` 與 `C:\ai_erp_itac` 的用途，也方便回溯「原始碼修改 -> 發版打包 -> 客戶主機更新」的完整流程。

## 目錄分工

### `D:\ai_erp_itac`

這是實際開發與修改的來源專案。

原始碼修正、除錯、功能調整都以這份為準。

### `C:\ai_erp_itac`

這是發版與部署的暫存/輸出目錄。

實務上會把需要交付的檔案同步到這裡，再由這裡產生 `release.zip`。

### 客戶主機

客戶端會執行 `update.bat`，將 `release.zip` 解壓縮並覆蓋到既定位置，完成更新。

## 實際流程

1. 在 `D:\ai_erp_itac` 修改原始碼。
2. 確認修正內容已涵蓋登入、後端 API、Socket 或前端相關檔案。
3. 依照既有流程把原始碼轉譯或同步到 `C:\ai_erp_itac`。
4. 先在 `frontend` 重新 `npm run build`，產出最新 `dist`。
5. 再把 `dist` 同步到 `C:\ai_erp_itac\nginx\html\ai`，讓部署目錄和最新前端一致。
6. 以目前輸出內容建立 `release.zip`。
7. 若需要驗證，先比對 `release.zip` 的 SHA256、大小與內含檔案。
8. 將 `release.zip` 送到客戶主機。
9. 由客戶主機執行 `update.bat`。
10. `update.bat` 解壓縮 `release.zip`，完成更新。

## 目前這套專案的慣例

- `D:\ai_erp_itac` 是來源專案，平常只改這裡的原始碼。
- `C:\ai_erp_itac` 是輸出/發版工作區，會放轉譯後的 `pyd`、前端打包檔、`nginx` 內容與 `release.zip`。
- 客戶主機不是直接拿 `D:` 的原始碼，而是吃 `release.zip` 更新。
- 所以只要要出給客戶，最後一定要確認 `C:\ai_erp_itac\release.zip` 是最新版本。

## 客戶主機上的另一套更新器

有些客戶環境不是直接跑 `C:\ai_erp_itac\update.bat`，而是透過 `C:\inetpub\wwwroot\xCPC\update\` 底下的更新器接收檔案。

如果 log 長得像這樣：

- `收到檔案：C:\inetpub\wwwroot\xCPC\update\inbox\update.zip`
- `開始解壓到：C:\inetpub\wwwroot\xCPC\update\work`
- `略過：...\SmartUpdate.bat`
- `略過：...\SmartUpdate.ps1`

那代表實際在跑的是 xCPC 的 web 更新流程，不是本機的 `release.zip -> update.bat -> startup.bat` 流程。

這種情況要注意：

1. 客戶端真正吃到的是 `update.zip`，不是本機的 `release.zip`。
2. 就算 `release.zip` 已更新，如果沒有同步到客戶主機的 `update.zip` 上傳入口，UI 也不會變。
3. `SmartUpdate.bat` / `SmartUpdate.ps1` 被略過，表示這套更新器本身可能只做複製與 SQL，不會額外幫你重啟瀏覽器或開登入頁。

## 這次登入錯誤的修正方式

本次處理的是登入階段的字串型別問題：

- 問題現象是 `"'int' object has no attribute 'strip'"`。
- 根因是登入流程中，某些欄位有機會是數字型別，但程式直接呼叫 `.strip()`。
- 修正方式是先把值安全轉成字串，再做 `.strip()`。
- 另外也確認到 `backend\routes\realtime.cp310-win_amd64.pyd` 會優先於 `backend\routes\realtime.py` 被載入，因此即使 `.py` 已更新，客戶主機若保留舊 `.pyd`，仍可能繼續吃到舊邏輯。
- 所以更新流程已補上「清除舊 `realtime.pyd` / `__pycache__`」的保險，避免登入修正被舊編譯模組蓋回去。

### 已涵蓋的登入入口

- HTTP 登入 API
- 舊版 `auth` blueprint
- Socket.IO 登入事件
- 線上名單同步相關流程

### 這次特別確認的部署路徑

- 實際執行的更新腳本以 `C:\ai_erp_itac\update.bat` 為主。
- `update.bat` 會在部署後刪除舊的 `backend\routes\realtime.cp310-win_amd64.pyd` 與相關 `__pycache__`。
- `startup.bat` 也有同樣的清理保險，確保啟動時不會再誤載舊模組。

## 發版時的檢查重點

1. 確認原始碼是改在 `D:\ai_erp_itac`。
2. 確認發版輸出是在 `C:\ai_erp_itac`。
3. 確認 `release.zip` 是最新時間戳。
4. 確認客戶主機上的 `update.bat` 仍然指向正確的解壓縮與更新路徑。
5. 確認登入後不會再出現型別造成的 `.strip()` 錯誤。
6. 確認被修正的頁面或 API，在 `D:`、`C:` 與 `release.zip` 三邊內容一致。

## 這次補上的標準值規則

- `inspectValues.vue` 與 `inspectStandard.vue` 都已補強英吋分數格式解析。
- 現在像 `1/8`、`1 1/2` 這類標準值，不會再被當成格式錯誤。
- `update.bat` 的實際更新流程是先讀取 `C:\ai_erp_itac\release.zip`，再在結尾接著執行 `startup.bat`。
- 因此只要有改到前端解析或判定流程，就一定要同步更新 `C:\ai_erp_itac\release.zip`，並依現場需要複製一份到 `C:\ai_erp_itac\release\release.zip` 方便比對。

## 這次補上的 live 目錄與 release.zip 對齊流程

這次再確認到一個容易混淆的點：

- `127.0.0.1:81` 實際是由 `C:\ai_erp_itac\nginx\nginx.exe` 提供服務。
- nginx 的靜態根目錄是 `C:\ai_erp_itac\nginx\html`。
- 所以瀏覽器目前看到的 `/ai/assets/*`，來源是 `C:\ai_erp_itac\nginx\html\ai\assets\*`，不是單純看 `release.zip` 裡的內容。

因此現在的正確對齊方式是：

1. 先確認 `C:\ai_erp_itac\nginx\html\ai` 是目前本機 live 版本。
2. 再以 `C:\ai_erp_itac` 現況重新打包 `release.zip`，讓壓縮檔內容跟 live 目錄一致。
3. 必要時把同一份 `release.zip` 複製到 `C:\ai_erp_itac\release\release.zip`，方便對照與部署。

這次實際驗到的對照結果：

- live page 目前引用的是 `index-AfCXgaGA.js`、`inspectStandard-Dbo7IJWt.js`、`inspectStandard-DjPmWYtU.css`
- 重打包後的 `release.zip` 已經跟這組 live assets 對齊
- 重新打包後的 `release.zip` SHA256 為 `31B41C3F58C3D1FB6DF2FA1E09467AE13A2D99F1DE366ABC5FDC45443469CD49`

## 這次更新的 `update.bat` 行為

目前 `C:\ai_erp_itac\update.bat` 已經改成以 `release.zip` 為主的完整更新器：

1. 先使用本機 `C:\ai_erp_itac\release.zip`，沒有的話才改下載遠端包。
2. 驗證 zip 是否可讀。
3. 解壓到暫存目錄。
4. 將暫存內容部署回安裝根目錄，包含 `frontend\dist` 與 `nginx\html\ai`。
5. 清掉舊的 `realtime` 編譯模組與快取。
6. 寫入 `release\version.txt`。
7. 最後啟動 `nginx` / `backend`，並自動開啟登入頁。

也就是說，現在更新流程已經不是「手動傳 zip 但不會生效」，而是 `update.bat` 真的會把 zip 內容部署到 live 目錄。

## 建議的後續做法

1. 每次修復後都先在 `D:\ai_erp_itac` 驗證。
2. 發版前再同步到 `C:\ai_erp_itac`。
3. 打包前確認 `release.zip` 的內容是最新版本。
4. 客戶端更新後先測登入，再測主功能。
