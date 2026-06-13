# Voice SOP Registry & Generic Parser

本資料夾提供一套「設定驅動（config-driven）」的語音/文字指令解析機制：
- Parser 永遠只有一支（index.js）
- 能力全部來自 registry（voice-registry.json）
- 新增功能/同義詞/提示詞（hint）只改 JSON，不改主流程

---

## 檔案說明

- `index.js`
  - 通用解析器（Generic Voice Parser）
  - 依 registry 進行 Intent / Hint / Key 抽取
  - 輸出標準化 Command 物件
  - 可用 `execute()` 直接導頁（vue-router）

- `voice-registry.json`
  - Voice SOP Registry（意圖與同義詞、導頁資訊、預設欄位、hint 欄位）

---

## 解析 SOP（固定流程）

### Step 1：取語音全文
輸入任意字串，例如：`請找出客戶 地址 仁愛路`

### Step 2：Intent Matching（只做一次）
- 掃描 registry 中每個 intent 的 `intent_aliases`
- 找到「最長命中」（同長度取最先出現）
- 回傳 intent_key，例如：`customer.search`
- ❗只決定「做什麼」（去哪個 route / entity）

### Step 3：Hint Matching（可選）
- 在全文中尋找 hint（例如：地址/電話/聯絡人）
- 若找到，使用對應 fields
- 若沒找到，使用 defaultFields

### Step 4：抽取 key
- 從全文移除 alias + hint
- 剩下字串即為 key（可能是數字、中文、混合）

---

## Command 物件格式（輸出）

Parser 會回傳類似：

```json
{
  "source": "voice",
  "rawText": "請找出客戶 地址 仁愛路",
  "intent_key": "customer.search",
  "intent_label": "查詢客戶",
  "matched_alias": "請找出客戶",
  "entity": "customer",
  "routeName": "customer_view",
  "aiView": "ai_customers",
  "pkField": "refno",
  "key": "仁愛路",
  "fields": ["address"],
  "auto": "1",
  "src": "voice",
  "meta": {
    "hint": "地址",
    "confidence": 0.92
  }
}
