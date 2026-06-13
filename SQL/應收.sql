/* =========================================================
   AR 主檔 (dbo.ar_invoice)
   - 每張出貨/發票單 form_no 只會有一筆 AR
   - payable_amount = product_amount + additional_amount
   ========================================================= */

IF OBJECT_ID('dbo.ar_invoice', 'U') IS NOT NULL
  DROP TABLE dbo.ar_invoice;
GO

CREATE TABLE dbo.ar_invoice (
  ar_id               BIGINT IDENTITY(1,1) NOT NULL,
  -- 來源單據（你現在的資料邏輯）
  pi_no               NVARCHAR(50)  NOT NULL,  -- r.pi_no (或你系統 PI)
  form_no             NVARCHAR(50)  NOT NULL,  -- r.form_no (你要對到 y.pi_no)
  in_no               NVARCHAR(50)  NULL,      -- y.in_no (a.form_no2)
  
  -- 客戶/業務/公司別（報表維度）
  customer_id         INT           NULL,
  customer_name       NVARCHAR(200) NOT NULL,
  sales_rep_id        INT           NULL,
  sales_rep_name      NVARCHAR(100) NOT NULL,
  company_title       NVARCHAR(100) NULL,      -- 若你有公司別欄位可補，沒有先留

  currency            NVARCHAR(10)  NOT NULL,

  -- 金額拆分（應收 = 產品金額 + 額外費用）
  product_amount      DECIMAL(18,2) NOT NULL CONSTRAINT DF_ar_invoice_product_amount DEFAULT(0),
  additional_amount   DECIMAL(18,2) NOT NULL CONSTRAINT DF_ar_invoice_additional_amount DEFAULT(0),
  payable_amount      AS (ISNULL(product_amount,0) + ISNULL(additional_amount,0)) PERSISTED,

  -- 日期
  order_date          DATE          NULL,
  ship_date           DATE          NULL,

  -- === 未來銷帳/承接會計用（先預留，不影響你現在報表） ===
  paid_amount         DECIMAL(18,2) NOT NULL CONSTRAINT DF_ar_invoice_paid_amount DEFAULT(0),
  open_amount         AS (ISNULL(product_amount,0) + ISNULL(additional_amount,0) - ISNULL(paid_amount,0)) PERSISTED,

  status              VARCHAR(10)   NOT NULL CONSTRAINT DF_ar_invoice_status DEFAULT('OPEN'),
  -- OPEN / CLOSED / PARTIAL (你也可用你習慣的字)

  -- 系統欄位
  source_tag          NVARCHAR(50)  NULL,      -- 例如 'ERP'/'IMPORT'/'SYNC'
  remark              NVARCHAR(400) NULL,

  created_at          DATETIME2(0)  NOT NULL CONSTRAINT DF_ar_invoice_created_at DEFAULT(SYSDATETIME()),
  updated_at          DATETIME2(0)  NOT NULL CONSTRAINT DF_ar_invoice_updated_at DEFAULT(SYSDATETIME()),

  CONSTRAINT PK_ar_invoice PRIMARY KEY CLUSTERED (ar_id),

  -- ✅ 核心：一張 form_no 只能有一筆 AR
  CONSTRAINT UQ_ar_invoice_form_no UNIQUE (form_no)
);
GO

/* =========================================================
   Indexes（依你最常查的條件）
   ========================================================= */

-- 常用：依客戶 + 幣別 + 日期
CREATE INDEX IX_ar_invoice_customer_currency_date
ON dbo.ar_invoice (customer_name, currency, ship_date)
INCLUDE (pi_no, form_no, product_amount, additional_amount, paid_amount, status);
GO

-- 常用：依業務 + 日期（業務績效、催收清單）
CREATE INDEX IX_ar_invoice_salesrep_date
ON dbo.ar_invoice (sales_rep_name, ship_date)
INCLUDE (pi_no, form_no, customer_name, currency, payable_amount, paid_amount, open_amount, status);
GO

-- 常用：依 PI 查（對帳/追單）
CREATE INDEX IX_ar_invoice_pi_no
ON dbo.ar_invoice (pi_no)
INCLUDE (form_no, customer_name, currency, payable_amount, open_amount, ship_date, status);
GO

/* =========================================================
   updated_at 自動更新（可選）
   ========================================================= */
IF OBJECT_ID('dbo.trg_ar_invoice_updated_at', 'TR') IS NOT NULL
  DROP TRIGGER dbo.trg_ar_invoice_updated_at;
GO

CREATE TRIGGER dbo.trg_ar_invoice_updated_at
ON dbo.ar_invoice
AFTER UPDATE
AS
BEGIN
  SET NOCOUNT ON;
  UPDATE t
    SET updated_at = SYSDATETIME()
  FROM dbo.ar_invoice t
  INNER JOIN inserted i ON t.ar_id = i.ar_id;
END
GO


;WITH x0 AS ( 
  SELECT
    r.form_no AS order_form_no,
    r.pi_no,
    r.original_date AS order_date,
    s.id   AS sales_rep_id,
    s.name AS sales_rep_name,
    c.id   AS customer_id,
    c.company AS customer_name,
    r.currency,
    CAST(NULL AS nvarchar(100)) AS company_title
  FROM orders r
  INNER JOIN staff s    ON r.sales_rep   = s.id
  INNER JOIN customer c ON r.customer_id = c.id
  WHERE LEFT(RIGHT(r.form_no,3),1) <> 'R'
),
-- ✅ 每個 order_form_no 只留一筆（避免 join 乘開）
x AS (
  SELECT
    order_form_no,
    MAX(pi_no)          AS pi_no,
    MAX(order_date)     AS order_date,
    MAX(sales_rep_id)   AS sales_rep_id,
    MAX(sales_rep_name) AS sales_rep_name,
    MAX(customer_id)    AS customer_id,
    MAX(customer_name)  AS customer_name,
    MAX(currency)       AS currency,
    MAX(company_title)  AS company_title
  FROM x0
  GROUP BY order_form_no
),
y AS (
  SELECT
    s.form_no  AS ship_form_no,          -- ✅ 出貨單系統 key（唯一鍵要用它）
    s.form_no2 AS in_no,
    s.close_date AS ship_date,

    SUM(i.quantity * i.unit_price / ISNULL(i.unit_value,1)) AS product_amount,
    ISNULL(ac.additional_amount,0) AS additional_amount,

    MAX(i.pi_no) AS link_order_form_no   -- invoice_list.pi_no = orders.form_no（你確認正確）
  FROM shipment_docs s
  INNER JOIN invoice_list i
    ON i.form_no = s.form_no
  LEFT JOIN (
    SELECT form_no, SUM(charge) AS additional_amount
    FROM additional_charge
    WHERE LEFT(RIGHT(form_no,3),1) <> 'R'
    GROUP BY form_no
  ) ac
    ON ac.form_no = s.form_no
  WHERE LEFT(RIGHT(s.form_no,3),1) <> 'R'
  GROUP BY s.form_no, s.form_no2, s.close_date, ac.additional_amount
),
src0 AS (
  SELECT
    y.ship_form_no,
    y.in_no,
    x.pi_no,
    x.customer_id,
    x.customer_name,
    x.sales_rep_id,
    x.sales_rep_name,
    x.company_title,
    x.currency,
    CAST(y.product_amount AS decimal(18,2))    AS product_amount,
    CAST(y.additional_amount AS decimal(18,2)) AS additional_amount,
    x.order_date,
    y.ship_date
  FROM y
  LEFT JOIN x
    ON x.order_form_no = y.link_order_form_no
),
-- ✅ 最後保險：同一個 ship_form_no 如果還是重複，只留 1 筆（以 ship_date 新的優先）
src AS (
  SELECT *
  FROM (
    SELECT
      *,
      ROW_NUMBER() OVER (
        PARTITION BY ship_form_no
        ORDER BY ISNULL(ship_date,'19000101') DESC, ISNULL(order_date,'19000101') DESC
      ) AS rn
    FROM src0
  ) t
  WHERE rn = 1
)
MERGE dbo.ar_invoice WITH (HOLDLOCK) AS T
USING src AS S
ON T.form_no = S.ship_form_no    -- ✅ ar_invoice.form_no = shipment_docs.form_no
WHEN MATCHED AND (
     ISNULL(T.in_no,'')              <> ISNULL(S.in_no,'')
  OR ISNULL(T.pi_no,'')              <> ISNULL(S.pi_no,'')
  OR ISNULL(T.customer_id,0)         <> ISNULL(S.customer_id,0)
  OR ISNULL(T.customer_name,'')      <> ISNULL(S.customer_name,'')
  OR ISNULL(T.sales_rep_id,0)        <> ISNULL(S.sales_rep_id,0)
  OR ISNULL(T.sales_rep_name,'')     <> ISNULL(S.sales_rep_name,'')
  OR ISNULL(T.company_title,'')      <> ISNULL(S.company_title,'')
  OR ISNULL(T.currency,'')           <> ISNULL(S.currency,'')
  OR ISNULL(T.product_amount,0)      <> ISNULL(S.product_amount,0)
  OR ISNULL(T.additional_amount,0)   <> ISNULL(S.additional_amount,0)
  OR ISNULL(T.order_date,'19000101') <> ISNULL(S.order_date,'19000101')
  OR ISNULL(T.ship_date,'19000101')  <> ISNULL(S.ship_date,'19000101')
)
THEN UPDATE SET
  T.in_no             = S.in_no,
  T.pi_no             = S.pi_no,
  T.customer_id       = S.customer_id,
  T.customer_name     = S.customer_name,
  T.sales_rep_id      = S.sales_rep_id,
  T.sales_rep_name    = S.sales_rep_name,
  T.company_title     = S.company_title,
  T.currency          = S.currency,
  T.product_amount    = S.product_amount,
  T.additional_amount = S.additional_amount,
  T.order_date        = S.order_date,
  T.ship_date         = S.ship_date,
  T.source_tag        = ISNULL(T.source_tag,'SHIP'),
  T.updated_at        = SYSDATETIME()
WHEN NOT MATCHED BY TARGET
THEN INSERT (
  pi_no, form_no, in_no,
  customer_id, customer_name,
  sales_rep_id, sales_rep_name,
  company_title, currency,
  product_amount, additional_amount,
  order_date, ship_date,
  paid_amount, status,
  source_tag, remark,
  created_at, updated_at
)
VALUES (
  ISNULL(S.pi_no,''), S.ship_form_no, S.in_no,
  S.customer_id, ISNULL(S.customer_name,''),
  S.sales_rep_id, ISNULL(S.sales_rep_name,''),
  S.company_title, ISNULL(S.currency,''),
  ISNULL(S.product_amount,0), ISNULL(S.additional_amount,0),
  S.order_date, S.ship_date,
  0, 'OPEN',
  'SHIP', NULL,
  SYSDATETIME(), SYSDATETIME()
);

IF OBJECT_ID('dbo.ar_receipt','U') IS NULL
BEGIN
  CREATE TABLE dbo.ar_receipt(
    receipt_id        BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_ar_receipt PRIMARY KEY,
    customer_id       INT NULL,
    customer_name     NVARCHAR(200) NOT NULL,

    currency          NVARCHAR(10) NOT NULL,
    receipt_amount    DECIMAL(18,2) NOT NULL CONSTRAINT DF_ar_receipt_amount DEFAULT(0),

    receipt_date      DATE NOT NULL,
    method            NVARCHAR(30) NULL,   -- cash/tt/check/credit...
    bank_ref          NVARCHAR(80) NULL,   -- 匯款帳號末五碼/票號/交易序號
    memo              NVARCHAR(400) NULL,

    source_tag        NVARCHAR(50) NULL,   -- 來源：import/manual/accounting_sync...
    created_at        DATETIME2(0) NOT NULL CONSTRAINT DF_ar_receipt_created DEFAULT (SYSDATETIME()),
    updated_at        DATETIME2(0) NOT NULL CONSTRAINT DF_ar_receipt_updated DEFAULT (SYSDATETIME())
  );

  CREATE INDEX IX_ar_receipt_customer_date
  ON dbo.ar_receipt(customer_id, receipt_date);

  CREATE INDEX IX_ar_receipt_currency_date
  ON dbo.ar_receipt(currency, receipt_date);
END
GO


IF OBJECT_ID('dbo.ar_apply','U') IS NULL
BEGIN
  CREATE TABLE dbo.ar_apply(
    apply_id      BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_ar_apply PRIMARY KEY,

    receipt_id    BIGINT NOT NULL,
    ar_id         BIGINT NOT NULL,            -- 對應 dbo.ar_invoice.ar_id

    apply_type    VARCHAR(20) NOT NULL CONSTRAINT DF_ar_apply_type DEFAULT('PAYMENT'),
    -- 建議值：PAYMENT / DISCOUNT / FEE / FX / ADJUST（你要更嚴謹可加 CHECK）

    apply_amount  DECIMAL(18,2) NOT NULL,     -- 正數=沖帳，負數=回沖/撤銷也可以
    apply_date    DATE NOT NULL CONSTRAINT DF_ar_apply_date DEFAULT (CONVERT(date, GETDATE())),
    memo          NVARCHAR(400) NULL,

    created_at    DATETIME2(0) NOT NULL CONSTRAINT DF_ar_apply_created DEFAULT (SYSDATETIME())
  );

  ALTER TABLE dbo.ar_apply
    ADD CONSTRAINT FK_ar_apply_receipt
    FOREIGN KEY (receipt_id) REFERENCES dbo.ar_receipt(receipt_id);

  ALTER TABLE dbo.ar_apply
    ADD CONSTRAINT FK_ar_apply_invoice
    FOREIGN KEY (ar_id) REFERENCES dbo.ar_invoice(ar_id);

  -- ✅ 防止同一張收款、同一張發票、同一類型重複打一筆（最常見重複來源）
  -- 若你要允許同類型拆多筆，把 apply_type 從唯一鍵移除即可
  CREATE UNIQUE INDEX UQ_ar_apply_receipt_invoice_type
  ON dbo.ar_apply(receipt_id, ar_id, apply_type);

  CREATE INDEX IX_ar_apply_arid ON dbo.ar_apply(ar_id);
  CREATE INDEX IX_ar_apply_receipt ON dbo.ar_apply(receipt_id);
END
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_recalc_invoice_paid
  @ar_id BIGINT = NULL
AS
BEGIN
  SET NOCOUNT ON;

  ;WITH s AS (
    SELECT
      a.ar_id,
      SUM(ISNULL(a.apply_amount,0)) AS paid_sum
    FROM dbo.ar_apply a
    WHERE (@ar_id IS NULL OR a.ar_id = @ar_id)
    GROUP BY a.ar_id
  )
  UPDATE inv
  SET
    inv.paid_amount = ISNULL(s.paid_sum, 0),
    inv.status =
      CASE
        WHEN (ISNULL(inv.product_amount,0) + ISNULL(inv.additional_amount,0) - ISNULL(s.paid_sum,0)) <= 0 THEN 'CLOSED'
        WHEN ISNULL(s.paid_sum,0) > 0 THEN 'PARTIAL'
        ELSE 'OPEN'
      END,
    inv.updated_at = SYSDATETIME()
  FROM dbo.ar_invoice inv
  LEFT JOIN s ON s.ar_id = inv.ar_id
  WHERE (@ar_id IS NULL OR inv.ar_id = @ar_id);
END
GO


CREATE OR ALTER VIEW dbo.v_ar_receipt_balance
AS
WITH a AS (
  SELECT
    receipt_id,
    applied_amount = SUM(ISNULL(apply_amount, 0.0))
  FROM dbo.ar_apply
  WHERE apply_type = 'PAYMENT'
  GROUP BY receipt_id
)
SELECT
  r.receipt_id,
  r.customer_id,
  r.currency,
  r.receipt_amount,
  applied_amount   = ISNULL(a.applied_amount, 0.0),
  unapplied_amount = CAST(ISNULL(r.receipt_amount, 0.0) - ISNULL(a.applied_amount, 0.0) AS DECIMAL(18,2))
FROM dbo.ar_receipt r
LEFT JOIN a ON a.receipt_id = r.receipt_id;
GO


CREATE VIEW dbo.v_ar_invoice_balance
AS
SELECT
  i.ar_id,
  i.form_no,
  i.customer_id,
  i.customer_name,
  i.currency,
  i.payable_amount,
  ISNULL(SUM(a.apply_amount), 0) AS applied_amount,
  i.payable_amount - ISNULL(SUM(a.apply_amount), 0) AS open_amount
FROM dbo.ar_invoice i
LEFT JOIN dbo.ar_apply a
  ON a.ar_id = i.ar_id
  AND a.apply_type = 'PAYMENT'
GROUP BY
  i.ar_id, i.form_no, i.customer_id, i.customer_name, i.currency, i.payable_amount;
GO


ALTER TABLE dbo.ar_apply
ADD CONSTRAINT CK_ar_apply_amount_pos
CHECK (apply_amount > 0);
GO

ALTER TABLE dbo.ar_receipt
ADD CONSTRAINT CK_ar_receipt_amount_pos
CHECK (receipt_amount > 0);
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_apply_payment
  @receipt_id   BIGINT,
  @ar_id        BIGINT,
  @apply_amount DECIMAL(18,2),
  @apply_date   DATE = NULL,
  @remark       NVARCHAR(200) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  IF @apply_amount IS NULL OR @apply_amount <= 0
  BEGIN
    RAISERROR(N'沖帳金額必須 > 0', 16, 1);
    RETURN;
  END

  IF @apply_date IS NULL SET @apply_date = CAST(GETDATE() AS date);

  BEGIN TRAN;

  -- 1) 鎖住 receipt 與 invoice（避免同時兩個人沖同一筆造成超沖）
  DECLARE @rc_customer_id INT, @rc_currency NVARCHAR(10), @rc_amount DECIMAL(18,2);
  DECLARE @iv_customer_id INT, @iv_currency NVARCHAR(10), @iv_payable DECIMAL(18,2);

  SELECT
    @rc_customer_id = r.customer_id,
    @rc_currency    = r.currency,
    @rc_amount      = r.receipt_amount
  FROM dbo.ar_receipt r WITH (UPDLOCK, HOLDLOCK)
  WHERE r.receipt_id = @receipt_id;

  IF @rc_customer_id IS NULL
  BEGIN
    ROLLBACK;
    RAISERROR(N'找不到收款 receipt_id', 16, 1);
    RETURN;
  END

  SELECT
    @iv_customer_id = i.customer_id,
    @iv_currency    = i.currency,
    @iv_payable     = i.payable_amount
  FROM dbo.ar_invoice i WITH (UPDLOCK, HOLDLOCK)
  WHERE i.ar_id = @ar_id;

  IF @iv_currency IS NULL
  BEGIN
    ROLLBACK;
    RAISERROR(N'找不到發票 ar_id', 16, 1);
    RETURN;
  END

  -- 2) 防呆：同客戶、同幣別才可沖
  IF ISNULL(@rc_customer_id, -1) <> ISNULL(@iv_customer_id, -2)
  BEGIN
    ROLLBACK;
    RAISERROR(N'不可跨客戶沖帳', 16, 1);
    RETURN;
  END

  IF ISNULL(@rc_currency,'') <> ISNULL(@iv_currency,'')
  BEGIN
    ROLLBACK;
    RAISERROR(N'不可跨幣別沖帳', 16, 1);
    RETURN;
  END

  -- 3) 算「收款未分攤」與「發票未沖」
  DECLARE @receipt_unapplied DECIMAL(18,2);
  DECLARE @invoice_open      DECIMAL(18,2);

  SELECT @receipt_unapplied = rb.unapplied_amount
  FROM dbo.v_ar_receipt_balance rb
  WHERE rb.receipt_id = @receipt_id;

  SELECT @invoice_open = ib.open_amount
  FROM dbo.v_ar_invoice_balance ib
  WHERE ib.ar_id = @ar_id;

  IF @receipt_unapplied IS NULL SET @receipt_unapplied = 0;
  IF @invoice_open IS NULL SET @invoice_open = 0;

  -- 4) 防呆：不可超沖
  IF @apply_amount > @receipt_unapplied
  BEGIN
    ROLLBACK;
    RAISERROR(N'沖帳金額超過收款未分攤餘額', 16, 1);
    RETURN;
  END

  IF @apply_amount > @invoice_open
  BEGIN
    ROLLBACK;
    RAISERROR(N'沖帳金額超過發票未沖餘額', 16, 1);
    RETURN;
  END

  -- 5) 寫入 apply（方案A：不改資料表）
  INSERT INTO dbo.ar_apply
  (
    receipt_id, ar_id, apply_type, apply_date,
    apply_amount
  )
  VALUES
  (
    @receipt_id, @ar_id, 'PAYMENT', @apply_date,
    @apply_amount
  );

  -- 6) 重算狀態（動態執行：避免建立時相依性警告）
  IF OBJECT_ID(N'dbo.sp_ar_recalc_invoice', N'P') IS NOT NULL
  BEGIN
    EXEC sys.sp_executesql
      N'EXEC dbo.sp_ar_recalc_invoice @ar_id = @p1;',
      N'@p1 BIGINT',
      @p1 = @ar_id;
  END

  IF OBJECT_ID(N'dbo.sp_ar_recalc_receipt', N'P') IS NOT NULL
  BEGIN
    EXEC sys.sp_executesql
      N'EXEC dbo.sp_ar_recalc_receipt @receipt_id = @p1;',
      N'@p1 BIGINT',
      @p1 = @receipt_id;
  END

  COMMIT;
END
GO




CREATE OR ALTER PROCEDURE dbo.sp_ar_recalc_invoice
  @ar_id BIGINT
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @paid DECIMAL(18,2);

  SELECT @paid = ISNULL(SUM(apply_amount), 0)
  FROM dbo.ar_apply
  WHERE ar_id = @ar_id
    AND apply_type = 'PAYMENT';

  UPDATE dbo.ar_invoice
  SET
    paid_amount = ISNULL(@paid, 0),
    status =
      CASE
        WHEN (payable_amount - ISNULL(@paid,0)) <= 0 THEN 'CLOSED'
        WHEN ISNULL(@paid,0) > 0 THEN 'PARTIAL'
        ELSE 'OPEN'
      END,
    updated_at = SYSDATETIME()
  WHERE ar_id = @ar_id;
END
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_recalc_receipt
  @receipt_id BIGINT
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @applied   DECIMAL(18,2) = 0,
          @rc_amount DECIMAL(18,2) = 0;

  SELECT @rc_amount = ISNULL(receipt_amount, 0)
  FROM dbo.ar_receipt
  WHERE receipt_id = @receipt_id;

  SELECT @applied = ISNULL(SUM(apply_amount), 0)
  FROM dbo.ar_apply
  WHERE receipt_id = @receipt_id
    AND apply_type = 'PAYMENT';

  -- ✅ 只要 ar_receipt 存在 applied_amount 或 status 或 updated_at 任一欄位，就動態更新存在的欄位
  DECLARE @has_applied BIT = CASE WHEN COL_LENGTH('dbo.ar_receipt', 'applied_amount') IS NOT NULL THEN 1 ELSE 0 END;
  DECLARE @has_status  BIT = CASE WHEN COL_LENGTH('dbo.ar_receipt', 'status')        IS NOT NULL THEN 1 ELSE 0 END;
  DECLARE @has_upd     BIT = CASE WHEN COL_LENGTH('dbo.ar_receipt', 'updated_at')    IS NOT NULL THEN 1 ELSE 0 END;

  IF (@has_applied = 1 OR @has_status = 1 OR @has_upd = 1)
  BEGIN
    DECLARE @sql NVARCHAR(MAX) = N'UPDATE dbo.ar_receipt SET ';
    DECLARE @sep NVARCHAR(2) = N'';

    IF @has_applied = 1
    BEGIN
      SET @sql += @sep + N'applied_amount = @p_applied';
      SET @sep = N', ';
    END

    IF @has_status = 1
    BEGIN
      -- status 依你原本邏輯：CLOSED / PARTIAL / OPEN
      SET @sql += @sep + N'status = CASE
        WHEN (@p_rc_amount - @p_applied) <= 0 THEN N''CLOSED''
        WHEN @p_applied > 0 THEN N''PARTIAL''
        ELSE N''OPEN''
      END';
      SET @sep = N', ';
    END

    IF @has_upd = 1
    BEGIN
      SET @sql += @sep + N'updated_at = SYSDATETIME()';
      SET @sep = N', ';
    END

    SET @sql += N' WHERE receipt_id = @p_receipt_id;';

    EXEC sys.sp_executesql
      @sql,
      N'@p_applied DECIMAL(18,2), @p_rc_amount DECIMAL(18,2), @p_receipt_id BIGINT',
      @p_applied = @applied,
      @p_rc_amount = @rc_amount,
      @p_receipt_id = @receipt_id;
  END
END
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_recalc_invoice
  @ar_id BIGINT
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @paid  DECIMAL(18,2);
  DECLARE @total DECIMAL(18,2);

  SET @paid  = 0;
  SET @total = NULL;

  -- 1) 取得發票總額：優先 payable_amount，其次 invoice_amount（用動態SQL避免編譯期欄位檢查）
  IF COL_LENGTH('dbo.ar_invoice', 'payable_amount') IS NOT NULL
  BEGIN
    EXEC sys.sp_executesql
      N'SELECT @o_total = CONVERT(DECIMAL(18,2), payable_amount)
        FROM dbo.ar_invoice
        WHERE ar_id = @p_ar_id;',
      N'@p_ar_id BIGINT, @o_total DECIMAL(18,2) OUTPUT',
      @p_ar_id = @ar_id,
      @o_total = @total OUTPUT;
  END
  ELSE IF COL_LENGTH('dbo.ar_invoice', 'invoice_amount') IS NOT NULL
  BEGIN
    EXEC sys.sp_executesql
      N'SELECT @o_total = CONVERT(DECIMAL(18,2), invoice_amount)
        FROM dbo.ar_invoice
        WHERE ar_id = @p_ar_id;',
      N'@p_ar_id BIGINT, @o_total DECIMAL(18,2) OUTPUT',
      @p_ar_id = @ar_id,
      @o_total = @total OUTPUT;
  END
  -- else: total 保持 NULL（仍可更新 paid_amount；status 會用保守規則）

  -- 2) 計算已沖帳金額（PAYMENT）
  SELECT @paid = ISNULL(SUM(apply_amount), 0)
  FROM dbo.ar_apply
  WHERE ar_id = @ar_id
    AND apply_type = 'PAYMENT';

  -- 3) 動態更新存在的欄位（paid_amount / status / updated_at）
  DECLARE @has_paid   BIT;
  DECLARE @has_status BIT;
  DECLARE @has_upd    BIT;

  SET @has_paid   = CASE WHEN COL_LENGTH('dbo.ar_invoice', 'paid_amount') IS NOT NULL THEN 1 ELSE 0 END;
  SET @has_status = CASE WHEN COL_LENGTH('dbo.ar_invoice', 'status')      IS NOT NULL THEN 1 ELSE 0 END;
  SET @has_upd    = CASE WHEN COL_LENGTH('dbo.ar_invoice', 'updated_at')  IS NOT NULL THEN 1 ELSE 0 END;

  IF (@has_paid = 1 OR @has_status = 1 OR @has_upd = 1)
  BEGIN
    DECLARE @sql NVARCHAR(MAX);
    DECLARE @sep NVARCHAR(2);

    SET @sql = N'UPDATE dbo.ar_invoice SET ';
    SET @sep = N'';

    IF @has_paid = 1
    BEGIN
      SET @sql = @sql + @sep + N'paid_amount = @p_paid';
      SET @sep = N', ';
    END

    IF @has_status = 1
    BEGIN
      -- total 有值：可判 CLOSED / PARTIAL / OPEN
      -- total 無值：保守判斷（paid>0 => PARTIAL，否則 OPEN；不判 CLOSED）
      SET @sql = @sql + @sep + N'status = CASE
        WHEN @p_total IS NOT NULL AND (@p_total - @p_paid) <= 0 THEN N''CLOSED''
        WHEN @p_paid > 0 THEN N''PARTIAL''
        ELSE N''OPEN''
      END';
      SET @sep = N', ';
    END

    IF @has_upd = 1
    BEGIN
      SET @sql = @sql + @sep + N'updated_at = SYSDATETIME()';
      SET @sep = N', ';
    END

    SET @sql = @sql + N' WHERE ar_id = @p_ar_id;';

    EXEC sys.sp_executesql
      @sql,
      N'@p_paid DECIMAL(18,2), @p_total DECIMAL(18,2), @p_ar_id BIGINT',
      @p_paid = @paid,
      @p_total = @total,
      @p_ar_id = @ar_id;
  END
END
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_recalc_invoice
  @ar_id BIGINT
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @paid  DECIMAL(18,2);
  DECLARE @total DECIMAL(18,2);
  DECLARE @open  DECIMAL(18,2);

  -- 1) 取得 payable_amount
  SELECT @total = ISNULL(payable_amount, 0)
  FROM dbo.ar_invoice
  WHERE ar_id = @ar_id;

  IF @total IS NULL SET @total = 0;

  -- 2) 計算已沖帳金額（PAYMENT）
  SELECT @paid = ISNULL(SUM(apply_amount), 0)
  FROM dbo.ar_apply
  WHERE ar_id = @ar_id
    AND apply_type = 'PAYMENT';

  IF @paid IS NULL SET @paid = 0;

  -- 3) 算 open（僅用於狀態判斷，不寫回 open_amount）
  SET @open = @total - @paid;

  -- 4) 更新可更新欄位（避免 open_amount 計算欄位報錯）
  UPDATE dbo.ar_invoice
  SET
    paid_amount = @paid,
    status = CASE
      WHEN @open <= 0 THEN 'CLOSED'
      WHEN @paid > 0 THEN 'PARTIAL'
      ELSE 'OPEN'
    END,
    updated_at = SYSDATETIME()
  WHERE ar_id = @ar_id;
END
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_unapply_payment
  @apply_id     BIGINT = NULL,            -- ✅ 推薦：直接指定 ar_apply 主鍵
  @receipt_id   BIGINT = NULL,            -- 備用：用條件找要反沖的那筆
  @ar_id        BIGINT = NULL,
  @apply_amount DECIMAL(18,2) = NULL,
  @apply_date   DATE = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @x_apply_id   BIGINT;
  DECLARE @x_receipt_id BIGINT;
  DECLARE @x_ar_id      BIGINT;

  BEGIN TRAN;

  /* 1) 找到要反沖的 ar_apply 那筆（並鎖住） */
  IF @apply_id IS NOT NULL
  BEGIN
    -- ⚠️ 假設 ar_apply 主鍵欄位叫 apply_id
    SELECT
      @x_apply_id   = a.apply_id,
      @x_receipt_id = a.receipt_id,
      @x_ar_id      = a.ar_id
    FROM dbo.ar_apply a WITH (UPDLOCK, HOLDLOCK)
    WHERE a.apply_id = @apply_id
      AND a.apply_type = 'PAYMENT';

    IF @x_apply_id IS NULL
    BEGIN
      ROLLBACK;
      RAISERROR(N'找不到要反沖的沖帳記錄（apply_id 不存在或 apply_type 非 PAYMENT）', 16, 1);
      RETURN;
    END
  END
  ELSE
  BEGIN
    -- 走條件模式：receipt_id + ar_id (+ amount/date 可選)
    IF @receipt_id IS NULL OR @ar_id IS NULL
    BEGIN
      ROLLBACK;
      RAISERROR(N'未提供 apply_id 時，必須提供 receipt_id 與 ar_id 才能反沖', 16, 1);
      RETURN;
    END

    SELECT TOP 1
      @x_apply_id   = a.apply_id,      -- ⚠️ 同樣假設主鍵 apply_id
      @x_receipt_id = a.receipt_id,
      @x_ar_id      = a.ar_id
    FROM dbo.ar_apply a WITH (UPDLOCK, HOLDLOCK)
    WHERE a.receipt_id = @receipt_id
      AND a.ar_id = @ar_id
      AND a.apply_type = 'PAYMENT'
      AND (@apply_amount IS NULL OR a.apply_amount = @apply_amount)
      AND (@apply_date   IS NULL OR a.apply_date   = @apply_date)
    ORDER BY a.apply_date DESC;

    IF @x_apply_id IS NULL
    BEGIN
      ROLLBACK;
      RAISERROR(N'找不到符合條件的沖帳記錄可反沖', 16, 1);
      RETURN;
    END
  END

  /* 2) 執行反沖：刪除該筆 apply（方案A：不改表） */
  DELETE FROM dbo.ar_apply
  WHERE apply_id = @x_apply_id;

  /* 3) 重算狀態（存在才執行，避免相依問題） */
  IF OBJECT_ID(N'dbo.sp_ar_recalc_invoice', N'P') IS NOT NULL
    EXEC dbo.sp_ar_recalc_invoice @ar_id = @x_ar_id;

  IF OBJECT_ID(N'dbo.sp_ar_recalc_receipt', N'P') IS NOT NULL
    EXEC dbo.sp_ar_recalc_receipt @receipt_id = @x_receipt_id;

  COMMIT;
END
GO


CREATE OR ALTER PROCEDURE dbo.sp_ar_unapply_payment
  @apply_id     BIGINT = NULL,            -- ✅ 推薦：直接指定 ar_apply.apply_id
  @receipt_id   BIGINT = NULL,            -- 備用：用條件找要反沖的那筆
  @ar_id        BIGINT = NULL,
  @apply_amount DECIMAL(18,2) = NULL,
  @apply_date   DATE = NULL,
  @allow_any_type BIT = 0                 -- 0=只允許 PAYMENT；1=任何 apply_type 都可反沖
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @x_apply_id   BIGINT;
  DECLARE @x_receipt_id BIGINT;
  DECLARE @x_ar_id      BIGINT;
  DECLARE @x_type       NVARCHAR(20);

  BEGIN TRAN;

  /* 1) 找到要反沖的 ar_apply 那筆（並鎖住） */
  IF @apply_id IS NOT NULL
  BEGIN
    SELECT
      @x_apply_id   = a.apply_id,
      @x_receipt_id = a.receipt_id,
      @x_ar_id      = a.ar_id,
      @x_type       = a.apply_type
    FROM dbo.ar_apply a WITH (UPDLOCK, HOLDLOCK)
    WHERE a.apply_id = @apply_id;

    IF @x_apply_id IS NULL
    BEGIN
      ROLLBACK;
      RAISERROR(N'找不到要反沖的沖帳記錄（apply_id 不存在）', 16, 1);
      RETURN;
    END
  END
  ELSE
  BEGIN
    -- 走條件模式：receipt_id + ar_id (+ amount/date 可選)
    IF @receipt_id IS NULL OR @ar_id IS NULL
    BEGIN
      ROLLBACK;
      RAISERROR(N'未提供 apply_id 時，必須提供 receipt_id 與 ar_id 才能反沖', 16, 1);
      RETURN;
    END

    SELECT TOP 1
      @x_apply_id   = a.apply_id,
      @x_receipt_id = a.receipt_id,
      @x_ar_id      = a.ar_id,
      @x_type       = a.apply_type
    FROM dbo.ar_apply a WITH (UPDLOCK, HOLDLOCK)
    WHERE a.receipt_id = @receipt_id
      AND a.ar_id = @ar_id
      AND (@apply_amount IS NULL OR a.apply_amount = @apply_amount)
      AND (@apply_date   IS NULL OR a.apply_date   = @apply_date)
    ORDER BY a.apply_date DESC, a.apply_id DESC;

    IF @x_apply_id IS NULL
    BEGIN
      ROLLBACK;
      RAISERROR(N'找不到符合條件的沖帳記錄可反沖', 16, 1);
      RETURN;
    END
  END

  /* 2) 防呆：預設只允許反沖 PAYMENT */
  IF (@allow_any_type = 0) AND (ISNULL(@x_type, N'') <> N'PAYMENT')
  BEGIN
    ROLLBACK;
    RAISERROR(N'此筆 apply_type 不是 PAYMENT，無法反沖（目前 apply_type=%s）。如需強制反沖，請帶 @allow_any_type=1', 16, 1, @x_type);
    RETURN;
  END

  /* 3) 執行反沖：刪除該筆 apply */
  DELETE FROM dbo.ar_apply
  WHERE apply_id = @x_apply_id;

  /* 4) 重算狀態（存在才執行） */
  IF OBJECT_ID(N'dbo.sp_ar_recalc_invoice', N'P') IS NOT NULL
    EXEC dbo.sp_ar_recalc_invoice @ar_id = @x_ar_id;

  IF OBJECT_ID(N'dbo.sp_ar_recalc_receipt', N'P') IS NOT NULL
    EXEC dbo.sp_ar_recalc_receipt @receipt_id = @x_receipt_id;

  COMMIT;
END
GO




CREATE OR ALTER PROCEDURE dbo.sp_ar_apply_payment
  @receipt_id   BIGINT,
  @ar_id        BIGINT,
  @apply_amount DECIMAL(18,2),
  @apply_date   DATE = NULL,
  @memo         NVARCHAR(200) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  IF @apply_amount IS NULL OR @apply_amount <= 0
  BEGIN
    RAISERROR(N'沖帳金額必須 > 0', 16, 1);
    RETURN;
  END

  IF @apply_date IS NULL SET @apply_date = CAST(GETDATE() AS date);

  BEGIN TRAN;

  -- 1) 鎖住 receipt 與 invoice（避免併發超沖）
  DECLARE @rc_customer_id INT, @rc_currency NVARCHAR(10), @rc_amount DECIMAL(18,2);
  DECLARE @iv_customer_id INT, @iv_currency NVARCHAR(10), @iv_payable DECIMAL(18,2);

  SELECT
    @rc_customer_id = r.customer_id,
    @rc_currency    = r.currency,
    @rc_amount      = r.receipt_amount
  FROM dbo.ar_receipt r WITH (UPDLOCK, HOLDLOCK)
  WHERE r.receipt_id = @receipt_id;

  IF @rc_customer_id IS NULL
  BEGIN
    ROLLBACK;
    RAISERROR(N'找不到收款 receipt_id', 16, 1);
    RETURN;
  END

  SELECT
    @iv_customer_id = i.customer_id,
    @iv_currency    = i.currency,
    @iv_payable     = i.payable_amount
  FROM dbo.ar_invoice i WITH (UPDLOCK, HOLDLOCK)
  WHERE i.ar_id = @ar_id;

  IF @iv_currency IS NULL
  BEGIN
    ROLLBACK;
    RAISERROR(N'找不到發票 ar_id', 16, 1);
    RETURN;
  END

  -- 2) 防呆：同客戶、同幣別才可沖
  IF ISNULL(@rc_customer_id, -1) <> ISNULL(@iv_customer_id, -2)
  BEGIN
    ROLLBACK;
    RAISERROR(N'不可跨客戶沖帳', 16, 1);
    RETURN;
  END

  IF ISNULL(@rc_currency,'') <> ISNULL(@iv_currency,'')
  BEGIN
    ROLLBACK;
    RAISERROR(N'不可跨幣別沖帳', 16, 1);
    RETURN;
  END

  -- 3) 算「收款未分攤」與「發票未沖」
  DECLARE @receipt_unapplied DECIMAL(18,2);
  DECLARE @invoice_open      DECIMAL(18,2);

  SELECT @receipt_unapplied = rb.unapplied_amount
  FROM dbo.v_ar_receipt_balance rb
  WHERE rb.receipt_id = @receipt_id;

  SELECT @invoice_open = ib.open_amount
  FROM dbo.v_ar_invoice_balance ib
  WHERE ib.ar_id = @ar_id;

  IF @receipt_unapplied IS NULL SET @receipt_unapplied = 0;
  IF @invoice_open      IS NULL SET @invoice_open      = 0;

  -- 4) 防呆：不可超沖
  IF @apply_amount > @receipt_unapplied
  BEGIN
    ROLLBACK;
    RAISERROR(N'沖帳金額超過收款未分攤餘額', 16, 1);
    RETURN;
  END

  IF @apply_amount > @invoice_open
  BEGIN
    ROLLBACK;
    RAISERROR(N'沖帳金額超過發票未沖餘額', 16, 1);
    RETURN;
  END

  -- 5) Upsert 寫入 ar_apply（符合唯一索引 UQ_ar_apply_receipt_invoice_type）
  DECLARE @exists_apply_id BIGINT;

  SELECT @exists_apply_id = a.apply_id
  FROM dbo.ar_apply a WITH (UPDLOCK, HOLDLOCK)
  WHERE a.receipt_id = @receipt_id
    AND a.ar_id = @ar_id
    AND a.apply_type = N'PAYMENT';

  IF @exists_apply_id IS NULL
  BEGIN
    INSERT INTO dbo.ar_apply
    (
      receipt_id,
      ar_id,
      apply_type,
      apply_amount,
      apply_date,
      memo,
      created_at
    )
    VALUES
    (
      @receipt_id,
      @ar_id,
      N'PAYMENT',
      @apply_amount,
      @apply_date,
      @memo,
      SYSDATETIME()
    );
  END
  ELSE
  BEGIN
    UPDATE dbo.ar_apply
    SET
      apply_amount = apply_amount + @apply_amount,
      apply_date   = @apply_date,
      memo         = CASE
                      WHEN @memo IS NULL OR LTRIM(RTRIM(@memo)) = N'' THEN memo
                      WHEN memo IS NULL OR LTRIM(RTRIM(memo)) = N'' THEN @memo
                      ELSE memo + N'；' + @memo
                    END
    WHERE apply_id = @exists_apply_id;
  END

  -- 6) 重算狀態
  IF OBJECT_ID(N'dbo.sp_ar_recalc_invoice', N'P') IS NOT NULL
    EXEC dbo.sp_ar_recalc_invoice @ar_id = @ar_id;

  IF OBJECT_ID(N'dbo.sp_ar_recalc_receipt', N'P') IS NOT NULL
    EXEC dbo.sp_ar_recalc_receipt @receipt_id = @receipt_id;

  COMMIT;
END
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_apply_receipt_fifo
  @receipt_id   BIGINT,
  @apply_total  DECIMAL(18,2) = NULL,       -- NULL=用收款未分攤全額
  @apply_date   DATE = NULL,
  @memo         NVARCHAR(200) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  IF @apply_date IS NULL
    SET @apply_date = CAST(GETDATE() AS DATE);

  BEGIN TRAN;

  /* 1) 鎖住 receipt，抓 customer/currency */
  DECLARE @cust INT, @cur NVARCHAR(10);

  SELECT
    @cust = r.customer_id,
    @cur  = r.currency
  FROM dbo.ar_receipt r WITH (UPDLOCK, HOLDLOCK)
  WHERE r.receipt_id = @receipt_id;

  IF @cust IS NULL
  BEGIN
    ROLLBACK;
    RAISERROR(N'找不到收款 receipt_id', 16, 1);
    RETURN;
  END

  /* 2) 算可用金額 */
  DECLARE @unapplied DECIMAL(18,2);
  SELECT @unapplied = rb.unapplied_amount
  FROM dbo.v_ar_receipt_balance rb
  WHERE rb.receipt_id = @receipt_id;

  IF @unapplied IS NULL SET @unapplied = 0;

  DECLARE @remain DECIMAL(18,2);

  IF @apply_total IS NULL
    SET @remain = @unapplied;
  ELSE
    SET @remain = @apply_total;

  IF @remain <= 0
  BEGIN
    ROLLBACK;
    RAISERROR(N'可分攤金額必須 > 0', 16, 1);
    RETURN;
  END

  IF @remain > @unapplied
  BEGIN
    ROLLBACK;
    RAISERROR(N'分攤金額超過收款未分攤餘額', 16, 1);
    RETURN;
  END

  /* 3) 找同客戶同幣別、未結清發票，FIFO 分攤 */
  DECLARE @ar_id BIGINT, @open DECIMAL(18,2), @do DECIMAL(18,2);

  DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
    SELECT i.ar_id
    FROM dbo.ar_invoice i
    WHERE i.customer_id = @cust
      AND i.currency = @cur
      AND ISNULL(i.status,'') <> 'CLOSED'
    ORDER BY ISNULL(i.order_date, '1900-01-01') ASC, i.ar_id ASC;

  OPEN cur;
  FETCH NEXT FROM cur INTO @ar_id;

  WHILE @@FETCH_STATUS = 0 AND @remain > 0
  BEGIN
    -- 取該張發票未沖金額（用 view）
    SELECT @open = ib.open_amount
    FROM dbo.v_ar_invoice_balance ib
    WHERE ib.ar_id = @ar_id;

    IF @open IS NULL SET @open = 0;

    IF @open > 0
    BEGIN
      SET @do = CASE WHEN @remain < @open THEN @remain ELSE @open END;

      -- 用既有單筆沖帳 SP 寫入（含 memo + 防超沖 + 鎖）
      EXEC dbo.sp_ar_apply_payment
        @receipt_id = @receipt_id,
        @ar_id = @ar_id,
        @apply_amount = @do,
        @apply_date = @apply_date,
        @memo = @memo;

      SET @remain = @remain - @do;
    END

    FETCH NEXT FROM cur INTO @ar_id;
  END

  CLOSE cur;
  DEALLOCATE cur;

  COMMIT;
END
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_apply_receipt_fifo
  @receipt_id   BIGINT,
  @apply_total  DECIMAL(18,2) = NULL,       -- NULL=用收款未分攤全額
  @apply_date   DATE = NULL,
  @memo         NVARCHAR(200) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;
  SET ANSI_WARNINGS OFF;  -- ✅ 關掉「彙總已刪除 Null 值」警告

  IF @apply_date IS NULL
    SET @apply_date = CAST(GETDATE() AS DATE);

  BEGIN TRAN;

  DECLARE @cust INT, @cur NVARCHAR(10);

  SELECT
    @cust = r.customer_id,
    @cur  = r.currency
  FROM dbo.ar_receipt r WITH (UPDLOCK, HOLDLOCK)
  WHERE r.receipt_id = @receipt_id;

  IF @cust IS NULL
  BEGIN
    ROLLBACK;
    SET ANSI_WARNINGS ON;
    RAISERROR(N'找不到收款 receipt_id', 16, 1);
    RETURN;
  END

  DECLARE @unapplied DECIMAL(18,2);
  SELECT @unapplied = rb.unapplied_amount
  FROM dbo.v_ar_receipt_balance rb
  WHERE rb.receipt_id = @receipt_id;

  IF @unapplied IS NULL SET @unapplied = 0;

  DECLARE @remain DECIMAL(18,2);
  SET @remain = ISNULL(@apply_total, @unapplied);

  IF @remain <= 0
  BEGIN
    ROLLBACK;
    SET ANSI_WARNINGS ON;
    RAISERROR(N'可分攤金額必須 > 0', 16, 1);
    RETURN;
  END

  IF @remain > @unapplied
  BEGIN
    ROLLBACK;
    SET ANSI_WARNINGS ON;
    RAISERROR(N'分攤金額超過收款未分攤餘額', 16, 1);
    RETURN;
  END

  DECLARE @ar_id BIGINT, @open DECIMAL(18,2), @do DECIMAL(18,2);

  DECLARE curInv CURSOR LOCAL FAST_FORWARD FOR
    SELECT i.ar_id
    FROM dbo.ar_invoice i
    WHERE i.customer_id = @cust
      AND i.currency = @cur
      AND ISNULL(i.status,'') <> 'CLOSED'
    ORDER BY ISNULL(i.order_date, '1900-01-01') ASC, i.ar_id ASC;

  OPEN curInv;
  FETCH NEXT FROM curInv INTO @ar_id;

  WHILE @@FETCH_STATUS = 0 AND @remain > 0
  BEGIN
    SELECT @open = ib.open_amount
    FROM dbo.v_ar_invoice_balance ib
    WHERE ib.ar_id = @ar_id;

    IF @open IS NULL SET @open = 0;

    IF @open > 0
    BEGIN
      SET @do = CASE WHEN @remain < @open THEN @remain ELSE @open END;

      EXEC dbo.sp_ar_apply_payment
        @receipt_id   = @receipt_id,
        @ar_id        = @ar_id,
        @apply_amount = @do,
        @apply_date   = @apply_date,
        @memo         = @memo;

      SET @remain = @remain - @do;
    END

    FETCH NEXT FROM curInv INTO @ar_id;
  END

  CLOSE curInv;
  DEALLOCATE curInv;

  COMMIT;
  SET ANSI_WARNINGS ON;
END
GO




CREATE OR ALTER PROCEDURE dbo.sp_ar_get_apply_context
  @receipt_id BIGINT,
  @ar_id      BIGINT
AS
BEGIN
  SET NOCOUNT ON;

  -- receipt
  SELECT
    r.receipt_id,
    r.customer_id,
    r.currency,
    r.receipt_amount,
    rb.unapplied_amount
  FROM dbo.ar_receipt r
  LEFT JOIN dbo.v_ar_receipt_balance rb
    ON rb.receipt_id = r.receipt_id
  WHERE r.receipt_id = @receipt_id;

  -- invoice
  SELECT
    i.ar_id,
    i.customer_id,
    i.currency,
    i.payable_amount,
    i.paid_amount,
    ib.open_amount,
    i.status
  FROM dbo.ar_invoice i
  LEFT JOIN dbo.v_ar_invoice_balance ib
    ON ib.ar_id = i.ar_id
  WHERE i.ar_id = @ar_id;
END
GO



CREATE OR ALTER PROCEDURE dbo.sp_ar_get_receipt_candidates
  @receipt_id BIGINT,
  @top        INT = 50
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @cust INT, @cur NVARCHAR(10);

  SELECT
    @cust = r.customer_id,
    @cur  = r.currency
  FROM dbo.ar_receipt r
  WHERE r.receipt_id = @receipt_id;

  -- receipt info
  SELECT
    r.receipt_id,
    r.customer_id,
    r.currency,
    r.receipt_amount,
    rb.unapplied_amount
  FROM dbo.ar_receipt r
  LEFT JOIN dbo.v_ar_receipt_balance rb
    ON rb.receipt_id = r.receipt_id
  WHERE r.receipt_id = @receipt_id;

  -- invoice candidates
  SELECT TOP (@top)
    i.ar_id,
    i.pi_no,
    i.form_no,
    i.in_no,
    i.order_date,
    i.payable_amount,
    i.paid_amount,
    ib.open_amount,
    i.status
  FROM dbo.ar_invoice i
  LEFT JOIN dbo.v_ar_invoice_balance ib
    ON ib.ar_id = i.ar_id
  WHERE i.customer_id = @cust
    AND i.currency = @cur
    AND ISNULL(i.status,'') <> 'CLOSED'
    AND ISNULL(ib.open_amount, 0) > 0
  ORDER BY ISNULL(i.order_date,'1900-01-01') ASC, i.ar_id ASC;
END
GO




USE [Hanlien];
GO

-- 1) 建立 db 角色（只做 EXEC 權限管理）
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'role_api_exec')
    CREATE ROLE [role_api_exec];
GO

-- 2) 授權該角色可以執行你這些 SP
GRANT EXECUTE ON dbo.sp_ar_get_apply_context     TO [role_api_exec];
GRANT EXECUTE ON dbo.sp_ar_get_receipt_candidates TO [role_api_exec];

-- 之後你把 apply/unapply/fifo 接 API，也一起授權：
-- GRANT EXECUTE ON dbo.sp_ar_apply_payment        TO [role_api_exec];
-- GRANT EXECUTE ON dbo.sp_ar_unapply_payment      TO [role_api_exec];
-- GRANT EXECUTE ON dbo.sp_ar_apply_receipt_fifo   TO [role_api_exec];
GO



CREATE LOGIN [ai_erp_api]
WITH PASSWORD = N'ChangeThis_StrongPwd_2026!',
     CHECK_POLICY = ON,
     CHECK_EXPIRATION = OFF;
GO



CREATE USER [ai_erp_api] FOR LOGIN [ai_erp_api];
GO

-- 若你之前已建立 role_api_exec，這句直接加
EXEC sp_addrolemember N'role_api_exec', N'ai_erp_api';
GO



USE [Hanlien];
GO
GRANT EXECUTE ON dbo.sp_ar_get_apply_context       TO [role_api_exec];
GRANT EXECUTE ON dbo.sp_ar_get_receipt_candidates  TO [role_api_exec];
GO



USE [Hanlien];
GO

-- 如果已存在就先不建
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'ai_erp_api')
BEGIN
  CREATE USER [ai_erp_api] FOR LOGIN [ai_erp_api];
END
GO


ALTER LOGIN [ai_erp_api]
WITH PASSWORD = N'1688';
GO

USE Hanlien;
GO

GRANT EXECUTE ON dbo.sp_ar_apply_payment        TO role_api_exec;
GRANT EXECUTE ON dbo.sp_ar_apply_receipt_fifo   TO role_api_exec;
GRANT EXECUTE ON dbo.sp_ar_unapply_payment      TO role_api_exec;
GO



USE Hanlien;
GO
CREATE OR ALTER PROCEDURE dbo.sp_ar_get_receipt_applies
  @receipt_id BIGINT
AS
BEGIN
  SET NOCOUNT ON;

  SELECT
    a.apply_id,
    a.receipt_id,
    a.ar_id,
    a.apply_type,
    a.apply_amount,
    a.apply_date,
    a.memo,
    a.created_at,
    i.form_no,
    i.in_no,
    i.pi_no,
    i.currency,
    i.payable_amount,
    i.paid_amount,
    i.status
  FROM dbo.ar_apply a
  LEFT JOIN dbo.ar_invoice i ON i.ar_id = a.ar_id
  WHERE a.receipt_id = @receipt_id
    AND a.apply_type = 'PAYMENT'
  ORDER BY a.apply_date DESC, a.apply_id DESC;
END
GO

GRANT EXECUTE ON dbo.sp_ar_get_receipt_applies TO role_api_exec;
GO


ALTER TABLE dbo.shipment_docs
ADD isCanceled BIT NOT NULL CONSTRAINT DF_shipment_docs_isCanceled DEFAULT(0),
    canceled_by NVARCHAR(50) NULL,
    canceled_at DATETIME NULL,
    cancel_reason NVARCHAR(200) NULL;

ALTER TABLE dbo.ar_invoice
ADD isCanceled BIT NOT NULL CONSTRAINT DF_ar_invoice_isCanceled DEFAULT(0),
    canceled_by NVARCHAR(50) NULL,
    canceled_at DATETIME NULL,
    cancel_reason NVARCHAR(200) NULL;


USE Hanlien;
GO

IF OBJECT_ID('dbo.ar_action_log', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.ar_action_log (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    action NVARCHAR(30) NOT NULL,         -- CANCEL / UNCANCEL / ...
    form_no VARCHAR(50) NULL,
    form_no2 VARCHAR(50) NULL,
    actor NVARCHAR(50) NOT NULL,
    action_at DATETIME NOT NULL DEFAULT(GETDATE()),
    reason NVARCHAR(200) NULL,
    extra NVARCHAR(400) NULL
  );

  CREATE INDEX IX_ar_action_log_formno_at ON dbo.ar_action_log(form_no, action_at DESC);
END
GO




USE Hanlien;
GO

CREATE OR ALTER PROCEDURE dbo.sp_ar_set_canceled
  @form_no      VARCHAR(50),    -- shipment_docs.form_no / ar_invoice.form_no / invoice_list.form_no
  @isCanceled   BIT,            -- 1=取消, 0=取消復原
  @actor        NVARCHAR(50),   -- 操作人（由前端 X-User 帶入）
  @reason       NVARCHAR(200) = NULL
AS
BEGIN
  SET NOCOUNT ON;

  IF (@form_no IS NULL OR LTRIM(RTRIM(@form_no)) = '')
  BEGIN
    RAISERROR(N'缺少 form_no', 16, 1);
    RETURN;
  END

  -- 防呆：假單(N/R)不允許進入作帳/沖帳流程（也不需要取消）
  IF (LEFT(RIGHT(@form_no, 3), 1) IN ('N','R'))
  BEGIN
    RAISERROR(N'此單據屬於 N/R 假單，不允許作帳/沖帳/取消操作', 16, 1);
    RETURN;
  END

  DECLARE @now DATETIME = GETDATE();

  BEGIN TRY
    BEGIN TRAN;

    -- 1) 更新 shipment_docs
    UPDATE s
      SET
        s.isCanceled    = @isCanceled,
        s.canceled_by   = CASE WHEN @isCanceled = 1 THEN @actor ELSE NULL END,
        s.canceled_at   = CASE WHEN @isCanceled = 1 THEN @now   ELSE NULL END,
        s.cancel_reason = CASE WHEN @isCanceled = 1 THEN @reason ELSE NULL END
    FROM dbo.shipment_docs s
    WHERE s.form_no = @form_no;

    -- 2) 更新 ar_invoice
    UPDATE a
      SET
        a.isCanceled    = @isCanceled,
        a.canceled_by   = CASE WHEN @isCanceled = 1 THEN @actor ELSE NULL END,
        a.canceled_at   = CASE WHEN @isCanceled = 1 THEN @now   ELSE NULL END,
        a.cancel_reason = CASE WHEN @isCanceled = 1 THEN @reason ELSE NULL END
    FROM dbo.ar_invoice a
    WHERE a.form_no = @form_no;

    -- 3) 寫 DB log
    INSERT INTO dbo.ar_action_log(action, form_no, actor, action_at, reason, extra)
    VALUES(
      CASE WHEN @isCanceled = 1 THEN N'CANCEL' ELSE N'UNCANCEL' END,
      @form_no,
      @actor,
      @now,
      @reason,
      N'同步更新 shipment_docs + ar_invoice'
    );

    COMMIT;
  END TRY
  BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    DECLARE @msg NVARCHAR(4000) = ERROR_MESSAGE();
    RAISERROR(@msg, 16, 1);
  END CATCH
END
GO

USE Hanlien;
GO

ALTER TABLE dbo.ar_apply ADD
  created_by NVARCHAR(50) NULL,
  is_void BIT NOT NULL CONSTRAINT DF_ar_apply_is_void DEFAULT(0),
  void_by NVARCHAR(50) NULL,
  void_at DATETIME NULL,
  void_reason NVARCHAR(200) NULL;
GO



USE Hanlien;
GO

IF COL_LENGTH('dbo.ar_apply', 'created_by') IS NULL
  ALTER TABLE dbo.ar_apply ADD created_by NVARCHAR(50) NULL;
GO

IF COL_LENGTH('dbo.ar_apply', 'is_void') IS NULL
  ALTER TABLE dbo.ar_apply ADD is_void BIT NOT NULL CONSTRAINT DF_ar_apply_is_void DEFAULT(0);
GO

IF COL_LENGTH('dbo.ar_apply', 'void_by') IS NULL
  ALTER TABLE dbo.ar_apply ADD void_by NVARCHAR(50) NULL;
GO

IF COL_LENGTH('dbo.ar_apply', 'void_at') IS NULL
  ALTER TABLE dbo.ar_apply ADD void_at DATETIME NULL;
GO

IF COL_LENGTH('dbo.ar_apply', 'void_reason') IS NULL
  ALTER TABLE dbo.ar_apply ADD void_reason NVARCHAR(200) NULL;
GO




USE Hanlien;
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID('dbo.ar_apply')
    AND name = 'IX_ar_apply_receipt'
)
BEGIN
  CREATE INDEX IX_ar_apply_receipt
  ON dbo.ar_apply(receipt_id)
  INCLUDE(ar_id, apply_amount, apply_date, is_void);
END
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE object_id = OBJECT_ID('dbo.ar_apply')
    AND name = 'IX_ar_apply_arid'
)
BEGIN
  CREATE INDEX IX_ar_apply_arid
  ON dbo.ar_apply(ar_id)
  INCLUDE(receipt_id, apply_amount, apply_date, is_void);
END
GO



ALTER PROCEDURE dbo.sp_ar_apply_payment
  @receipt_id     BIGINT,
  @ar_id          BIGINT,
  @apply_amount   DECIMAL(18,2),
  @actor          NVARCHAR(50),
  @memo           NVARCHAR(400) = NULL
AS
BEGIN
  SET NOCOUNT ON;

  -- 基本防呆
  IF @apply_amount <= 0
  BEGIN
    RAISERROR(N'沖帳金額必須大於 0', 16, 1);
    RETURN;
  END

  -- 1️⃣ 寫入 ar_apply（沖帳紀錄）
  INSERT INTO dbo.ar_apply
  (
    receipt_id,
    ar_id,
    apply_type,
    apply_amount,
    memo,
    created_by
  )
  VALUES
  (
    @receipt_id,
    @ar_id,
    'PAYMENT',
    @apply_amount,
    @memo,
    @actor
  );

  -- 2️⃣ 更新 ar_invoice（累加已沖金額）
  UPDATE dbo.ar_invoice
  SET
    paid_amount = paid_amount + @apply_amount,
    updated_at = SYSDATETIME()
  WHERE ar_id = @ar_id;

END
GO



GRANT EXECUTE ON dbo.sp_ar_apply_payment TO ai_erp_api;


DROP INDEX UQ_ar_apply_receipt_invoice_type ON dbo.ar_apply;


DROP INDEX UX_ar_apply_receipt_arid_type_active ON dbo.ar_apply;
GO

CREATE UNIQUE NONCLUSTERED INDEX UX_ar_apply_receipt_arid_type_active
ON dbo.ar_apply(receipt_id, ar_id, apply_type)
WHERE is_void = 0;
GO



CREATE OR ALTER PROC dbo.sp_ar_apply_candidates
  @receipt_id BIGINT,
  @top INT = 200
AS
BEGIN
  SET NOCOUNT ON;

  -- 收款基本資料
  SELECT TOP 1
    receipt_id, customer_id, currency, receipt_amount, applied_amount, unapplied_amount
  FROM dbo.v_ar_receipt_balance
  WHERE receipt_id = @receipt_id;

  -- candidates：同客戶、同幣別、open > 0、未取消、排除 N/R 假單
  SELECT TOP (@top)
    ai.ar_id,
    ai.form_no,
    ai.in_no,
    ai.currency,
    b.open_amount,
    ai.ship_date,
    ai.payable_amount,
    ai.paid_amount,
    ai.status
  FROM dbo.v_ar_invoice_balance b
  JOIN dbo.ar_invoice ai ON ai.ar_id = b.ar_id
  WHERE b.customer_id = (SELECT customer_id FROM dbo.v_ar_receipt_balance WHERE receipt_id=@receipt_id)
    AND b.currency     = (SELECT currency     FROM dbo.v_ar_receipt_balance WHERE receipt_id=@receipt_id)
    AND b.open_amount > 0
    AND ISNULL(ai.isCanceled,0) = 0
    AND LEFT(RIGHT(ai.form_no, 3), 1) NOT IN ('N','R')
  ORDER BY ai.ship_date DESC, ai.in_no;
END
GO



CREATE OR ALTER PROC dbo.sp_ar_apply_unapply
  @apply_id BIGINT,
  @actor NVARCHAR(50),
  @memo  NVARCHAR(200) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @ar_id BIGINT, @receipt_id BIGINT, @amt DECIMAL(18,2);

  SELECT
    @ar_id = ar_id,
    @receipt_id = receipt_id,
    @amt = apply_amount
  FROM dbo.ar_apply WITH (UPDLOCK, HOLDLOCK)
  WHERE apply_id = @apply_id;

  IF @ar_id IS NULL
    RAISERROR(N'找不到 apply_id', 16, 1);

  -- 已反沖就不重複做
  IF EXISTS (SELECT 1 FROM dbo.ar_apply WHERE apply_id=@apply_id AND is_void=1)
    RETURN;

  BEGIN TRAN;

  -- 1) 作廢沖帳紀錄（保留）
  UPDATE dbo.ar_apply
  SET
    is_void = 1,
    void_by = @actor,
    void_at = GETDATE(),
    void_reason = COALESCE(@memo, N'反沖')
  WHERE apply_id = @apply_id;

  -- 2) 回沖發票已沖金額
  UPDATE dbo.ar_invoice
  SET
    paid_amount = ISNULL(paid_amount,0) - @amt,
    updated_at = SYSDATETIME()
  WHERE ar_id = @ar_id;

  COMMIT;
END
GO



CREATE OR ALTER PROC dbo.sp_ar_apply_fifo
  @receipt_id  BIGINT,
  @apply_total DECIMAL(18,2) = NULL,  -- NULL = 用未分攤全額
  @actor       NVARCHAR(50),
  @memo        NVARCHAR(400) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @cust INT, @cur NVARCHAR(10), @unapplied DECIMAL(18,2);

  SELECT TOP 1
    @cust = customer_id,
    @cur  = currency,
    @unapplied = unapplied_amount
  FROM dbo.v_ar_receipt_balance
  WHERE receipt_id = @receipt_id;

  IF @cust IS NULL
    RAISERROR(N'找不到 receipt_id', 16, 1);

  IF @unapplied <= 0
    RAISERROR(N'此收款目前沒有未分攤金額', 16, 1);

  DECLARE @remain DECIMAL(18,2) =
    CASE
      WHEN @apply_total IS NULL OR @apply_total <= 0 THEN @unapplied
      WHEN @apply_total > @unapplied THEN @unapplied
      ELSE @apply_total
    END;

  BEGIN TRAN;

  -- 依 ship_date 由舊到新（FIFO），逐筆沖
  DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
    SELECT
      ai.ar_id,
      b.open_amount
    FROM dbo.v_ar_invoice_balance b
    JOIN dbo.ar_invoice ai ON ai.ar_id = b.ar_id
    WHERE b.customer_id = @cust
      AND b.currency = @cur
      AND b.open_amount > 0
      AND ISNULL(ai.isCanceled,0) = 0
      AND LEFT(RIGHT(ai.form_no, 3), 1) NOT IN ('N','R')
    ORDER BY ai.ship_date ASC, ai.in_no ASC;

  DECLARE @ar_id BIGINT, @open DECIMAL(18,2), @amt DECIMAL(18,2);

  OPEN cur;
  FETCH NEXT FROM cur INTO @ar_id, @open;

  WHILE @@FETCH_STATUS = 0 AND @remain > 0
  BEGIN
    SET @amt = CASE WHEN @remain < @open THEN @remain ELSE @open END;

    -- 若同 receipt+ar_id 已有未反沖 PAYMENT，這裡我採「累加」避免卡 unique
    IF EXISTS (
      SELECT 1 FROM dbo.ar_apply
      WHERE receipt_id=@receipt_id AND ar_id=@ar_id AND apply_type='PAYMENT' AND is_void=0
    )
    BEGIN
      UPDATE dbo.ar_apply
      SET apply_amount = apply_amount + @amt,
          memo = CASE
                  WHEN @memo IS NULL OR @memo=N'' THEN memo
                  WHEN memo IS NULL OR memo=N'' THEN @memo
                  ELSE memo + N' | ' + @memo
                END
      WHERE receipt_id=@receipt_id AND ar_id=@ar_id AND apply_type='PAYMENT' AND is_void=0;
    END
    ELSE
    BEGIN
      INSERT dbo.ar_apply(receipt_id, ar_id, apply_type, apply_amount, apply_date, memo, created_at, created_by, is_void)
      VALUES(@receipt_id, @ar_id, 'PAYMENT', @amt, CONVERT(date,GETDATE()),
             COALESCE(@memo, N'FIFO 分攤'), SYSDATETIME(), @actor, 0);
    END

    UPDATE dbo.ar_invoice
    SET paid_amount = ISNULL(paid_amount,0) + @amt,
        updated_at  = SYSDATETIME()
    WHERE ar_id = @ar_id;

    SET @remain = @remain - @amt;

    FETCH NEXT FROM cur INTO @ar_id, @open;
  END

  CLOSE cur;
  DEALLOCATE cur;

  COMMIT;
END
GO



GRANT EXECUTE ON dbo.sp_ar_apply_candidates TO ai_erp_api;
GRANT EXECUTE ON dbo.sp_ar_apply_payment   TO ai_erp_api;
GRANT EXECUTE ON dbo.sp_ar_apply_unapply   TO ai_erp_api;
GRANT EXECUTE ON dbo.sp_ar_apply_fifo      TO ai_erp_api;



/* shipment_docs：新增 canceled_at / canceled_reason */
IF COL_LENGTH('dbo.shipment_docs', 'canceled_at') IS NULL
BEGIN
    ALTER TABLE dbo.shipment_docs
    ADD canceled_at DATETIME NULL;
END
GO

IF COL_LENGTH('dbo.shipment_docs', 'canceled_reason') IS NULL
BEGIN
    ALTER TABLE dbo.shipment_docs
    ADD canceled_reason NVARCHAR(100) NULL;
END
GO



/* ar_invoice：新增 canceled_at / canceled_reason */
IF COL_LENGTH('dbo.ar_invoice', 'canceled_at') IS NULL
BEGIN
    ALTER TABLE dbo.ar_invoice
    ADD canceled_at DATETIME NULL;
END
GO

IF COL_LENGTH('dbo.ar_invoice', 'canceled_reason') IS NULL
BEGIN
    ALTER TABLE dbo.ar_invoice
    ADD canceled_reason NVARCHAR(100) NULL;
END
GO



IF COL_LENGTH('dbo.ar_receipt', 'created_by') IS NULL
    ALTER TABLE dbo.ar_receipt ADD created_by NVARCHAR(50) NULL;
GO

IF COL_LENGTH('dbo.ar_receipt', 'created_at') IS NULL
    ALTER TABLE dbo.ar_receipt ADD created_at DATETIME NULL;
GO

IF COL_LENGTH('dbo.ar_receipt', 'memo') IS NULL
    ALTER TABLE dbo.ar_receipt ADD memo NVARCHAR(200) NULL;
GO




/* ar_receipt：建檔資訊 */
IF COL_LENGTH('dbo.ar_receipt', 'created_by') IS NULL
    ALTER TABLE dbo.ar_receipt ADD created_by NVARCHAR(50) NULL;
GO

IF COL_LENGTH('dbo.ar_receipt', 'created_at') IS NULL
    ALTER TABLE dbo.ar_receipt ADD created_at DATETIME NULL;
GO

/* ar_receipt：取消資訊（可選，但我建議一起加） */
IF COL_LENGTH('dbo.ar_receipt', 'isCanceled') IS NULL
    ALTER TABLE dbo.ar_receipt ADD isCanceled BIT NOT NULL CONSTRAINT DF_ar_receipt_isCanceled DEFAULT(0);
GO

IF COL_LENGTH('dbo.ar_receipt', 'canceled_at') IS NULL
    ALTER TABLE dbo.ar_receipt ADD canceled_at DATETIME NULL;
GO

IF COL_LENGTH('dbo.ar_receipt', 'canceled_reason') IS NULL
    ALTER TABLE dbo.ar_receipt ADD canceled_reason NVARCHAR(100) NULL;
GO



USE Hanlien;
GO

-- 1) 確認 database user 是否存在（授權是給 DB user）
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'ai_erp_api')
BEGIN
    CREATE USER [ai_erp_api] FOR LOGIN [ai_erp_api];
END
GO

-- 2) 只針對 ar_receipt 開 INSERT/SELECT（最小權限）
GRANT INSERT ON dbo.ar_receipt TO [ai_erp_api];
GRANT SELECT ON dbo.ar_receipt TO [ai_erp_api];
GO



ALTER TABLE dbo.ar_receipt
ADD
  receipt_no     nvarchar(20) NULL,   -- 你要的民國編號
  source_doc_no  nvarchar(50) NULL,   -- 來源單據（例如 shipment_docs.form_no2）
  source_desc    nvarchar(200) NULL;  -- 來源說明（例如「對帳單/匯款通知/某某專案」）




CREATE TABLE dbo.ar_receipt_no_seq (
  ymd char(8) NOT NULL,      -- YYYYMMDD
  last_no int NOT NULL,
  CONSTRAINT PK_ar_receipt_no_seq PRIMARY KEY (ymd)
);



CREATE UNIQUE INDEX UX_ar_receipt_receipt_no
ON dbo.ar_receipt(receipt_no)
WHERE receipt_no IS NOT NULL;



CREATE PROCEDURE dbo.sp_ar_next_receipt_no
  @receipt_date date,
  @receipt_no nvarchar(20) OUTPUT
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @ymd char(8) = CONVERT(char(8), @receipt_date, 112);
  DECLARE @last int;

  BEGIN TRAN;

  IF EXISTS (SELECT 1 FROM dbo.ar_receipt_no_seq WITH (UPDLOCK, HOLDLOCK) WHERE ymd = @ymd)
  BEGIN
    SELECT @last = last_no FROM dbo.ar_receipt_no_seq WITH (UPDLOCK, HOLDLOCK) WHERE ymd = @ymd;
    SET @last = @last + 1;
    UPDATE dbo.ar_receipt_no_seq SET last_no = @last WHERE ymd = @ymd;
  END
  ELSE
  BEGIN
    SET @last = 1;
    INSERT INTO dbo.ar_receipt_no_seq(ymd, last_no) VALUES (@ymd, @last);
  END

  COMMIT TRAN;

  DECLARE @yy int = YEAR(@receipt_date) - 1911;
  DECLARE @mm char(2) = RIGHT('0' + CAST(MONTH(@receipt_date) AS varchar(2)), 2);
  DECLARE @dd char(2) = RIGHT('0' + CAST(DAY(@receipt_date) AS varchar(2)), 2);
  DECLARE @seq char(3) = RIGHT('000' + CAST(@last AS varchar(3)), 3);

  SET @receipt_no = CAST(@yy AS varchar(3)) + @mm + @dd + @seq;
END




USE [Hanlien]
GO
/****** Object:  StoredProcedure [dbo].[sp_ar_apply_payment]    Script Date: 2026/1/31 下午 04:06:19 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE [dbo].[sp_ar_apply_payment]
  @receipt_id     BIGINT,
  @ar_id          BIGINT,
  @apply_amount   DECIMAL(18,2),
  @actor          NVARCHAR(50) =null,
  @memo           NVARCHAR(400) = NULL
AS
BEGIN
  SET NOCOUNT ON;
    IF @actor IS NULL OR LTRIM(RTRIM(@actor)) = ''
    SET @actor = 'system';     -- ✅ 給預設值
  -- 基本防呆
  IF @apply_amount <= 0
  BEGIN
    RAISERROR(N'沖帳金額必須大於 0', 16, 1);
    RETURN;
  END

  -- 1️⃣ 寫入 ar_apply（沖帳紀錄）
  INSERT INTO dbo.ar_apply
  (
    receipt_id,
    ar_id,
    apply_type,
    apply_amount,
    memo,
    created_by
  )
  VALUES
  (
    @receipt_id,
    @ar_id,
    'PAYMENT',
    @apply_amount,
    @memo,
    @actor
  );

  -- 2️⃣ 更新 ar_invoice（累加已沖金額）
  UPDATE dbo.ar_invoice
  SET
    paid_amount = paid_amount + @apply_amount,
    updated_at = SYSDATETIME()
  WHERE ar_id = @ar_id;

END




USE [Hanlien]
GO
/****** Object:  StoredProcedure [dbo].[sp_ar_apply_payment]    Script Date: 2026/1/31 下午 05:09:33 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE dbo.sp_ar_apply_payment
  @receipt_id   BIGINT,
  @ar_id        BIGINT,
  @apply_amount DECIMAL(18,2),
  @apply_date   DATE = NULL,
  @actor        NVARCHAR(50) = NULL,
  @memo         NVARCHAR(400) = NULL
AS
BEGIN
  SET NOCOUNT ON;

  -- ✅ 防呆
  IF @apply_amount <= 0
  BEGIN
    RAISERROR(N'沖帳金額必須大於 0', 16, 1);
    RETURN;
  END

  IF @actor IS NULL OR LTRIM(RTRIM(@actor)) = ''
    SET @actor = 'system';

  IF @apply_date IS NULL
    SET @apply_date = CAST(GETDATE() AS DATE);


  INSERT INTO dbo.ar_apply
  (
    receipt_id,
    ar_id,
    apply_type,
    apply_amount,
    apply_date,
    memo,
    created_by
  )
  VALUES
  (
    @receipt_id,
    @ar_id,
    'PAYMENT',
    @apply_amount,
    @apply_date,
    @memo,
    @actor
  );

  -- 2️⃣ 更新應收主檔
  UPDATE dbo.ar_invoice
  SET
    paid_amount = paid_amount + @apply_amount,
    updated_at  = SYSDATETIME()
  WHERE ar_id = @ar_id;
END







ALTER PROCEDURE [dbo].[sp_ar_apply_payment]
  @receipt_id     BIGINT,
  @ar_id          BIGINT,
  @apply_amount   DECIMAL(18,2),
  @apply_date     DATE = NULL,
  @actor          NVARCHAR(50) = NULL,
  @memo           NVARCHAR(400) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;
  SET ANSI_WARNINGS ON;

  IF @apply_date IS NULL SET @apply_date = CAST(GETDATE() AS DATE);

  IF @actor IS NULL OR LTRIM(RTRIM(@actor)) = ''
    SET @actor = 'system';

  IF @apply_amount <= 0
  BEGIN
    RAISERROR(N'沖帳金額必須大於 0', 16, 1);
    RETURN;
  END

  BEGIN TRAN;

  DECLARE @apply_id BIGINT;

  -- ✅ 找同一筆 receipt + ar_id + PAYMENT（active）
  SELECT TOP 1 @apply_id = a.apply_id
  FROM dbo.ar_apply a WITH (UPDLOCK, HOLDLOCK)
  WHERE a.receipt_id = @receipt_id
    AND a.ar_id = @ar_id
    AND a.apply_type = 'PAYMENT'
    AND ISNULL(a.is_void, 0) = 0;

  IF @apply_id IS NULL
  BEGIN
    INSERT INTO dbo.ar_apply
      (receipt_id, ar_id, apply_type, apply_amount, apply_date, memo, created_by)
    VALUES
      (@receipt_id, @ar_id, 'PAYMENT', @apply_amount, @apply_date, @memo, @actor);
  END
  ELSE
  BEGIN
    UPDATE dbo.ar_apply
    SET
      apply_amount = apply_amount + @apply_amount,
      apply_date   = @apply_date,
      memo         = CASE
                      WHEN @memo IS NULL OR LTRIM(RTRIM(@memo)) = '' THEN memo
                      ELSE @memo
                    END
    WHERE apply_id = @apply_id;
  END

  -- ✅ 發票累加
  UPDATE dbo.ar_invoice
  SET
    paid_amount = paid_amount + @apply_amount,
    updated_at  = SYSDATETIME()
  WHERE ar_id = @ar_id;

  COMMIT;
END
GO
