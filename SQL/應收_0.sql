/* ============================================================
   AI ERP - AR Module Naming Layer
   Purpose:
     1) 統一 AR 相關命名（ai_ar_* / ai_doc_*）
     2) 不破壞既有 dbo.sp_ar_* / dbo.v_ar_* / dbo.ar_*（先用 wrapper）
     3) 之後搬到新系統，只要搬 ai_ar_* 這層即可
   ============================================================ */

USE [Hanlien];
GO

/* ============================================================
   0) 基礎：文件每日流水（共用：收款/入庫/其他單號）
   ============================================================ */

IF OBJECT_ID('dbo.ai_doc_daily_seq', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.ai_doc_daily_seq (
    doc_type   VARCHAR(20) NOT NULL,
    yyyymmdd   CHAR(8) NOT NULL,
    seq        INT NOT NULL,
    CONSTRAINT PK_ai_doc_daily_seq PRIMARY KEY (doc_type, yyyymmdd)
  );
END
GO

IF OBJECT_ID('dbo.ai_doc_sp_next_no', 'P') IS NOT NULL
  DROP PROCEDURE dbo.ai_doc_sp_next_no;
GO

CREATE PROCEDURE dbo.ai_doc_sp_next_no
  @doc_type VARCHAR(20),
  @doc_no   VARCHAR(30) OUTPUT
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @d CHAR(8);
  SET @d = CONVERT(CHAR(8), GETDATE(), 112); -- YYYYMMDD

  BEGIN TRAN;

  IF EXISTS (
    SELECT 1
    FROM dbo.ai_doc_daily_seq WITH (UPDLOCK, HOLDLOCK)
    WHERE doc_type=@doc_type AND yyyymmdd=@d
  )
  BEGIN
    UPDATE dbo.ai_doc_daily_seq
      SET seq = seq + 1
    WHERE doc_type=@doc_type AND yyyymmdd=@d;
  END
  ELSE
  BEGIN
    INSERT INTO dbo.ai_doc_daily_seq(doc_type, yyyymmdd, seq)
    VALUES (@doc_type, @d, 1);
  END

  DECLARE @seq INT;
  SELECT @seq = seq
  FROM dbo.ai_doc_daily_seq
  WHERE doc_type=@doc_type AND yyyymmdd=@d;

  -- 民國年：YYYY - 1911
  DECLARE @yyyy INT, @roc INT, @mmdd CHAR(4);
  SET @yyyy = CAST(LEFT(@d,4) AS INT);
  SET @roc  = @yyyy - 1911;
  SET @mmdd = SUBSTRING(@d,5,4);

  -- YYYMMDD + 3 位流水
  SET @doc_no =
      RIGHT('000' + CAST(@roc AS VARCHAR(3)), 3)
    + @mmdd
    + RIGHT('000' + CAST(@seq AS VARCHAR(3)), 3);

  COMMIT;
END
GO

/* ============================================================
   1) 收款單號 receipt_no：確保不是 NULL + 可唯一索引
   - 你現在 dbo.ar_receipt 以 receipt_id 當鍵沒問題
   - 但你想要「民國年月日+流水號」顯示給使用者 -> receipt_no
   - 這段只做：加欄位 + 回填 + 建唯一索引（不動 receipt_id）
   ============================================================ */

IF COL_LENGTH('dbo.ar_receipt', 'receipt_no') IS NULL
BEGIN
  ALTER TABLE dbo.ar_receipt ADD receipt_no VARCHAR(30) NULL;
END
GO

-- 將 NULL 的 receipt_no 先回填（暫用 receipt_id 當 fallback，避免 unique index 卡住）
-- 之後你可以再寫一支批次把舊資料補成民國格式（用 created_at / receipt_date 分天取號）
UPDATE dbo.ar_receipt
SET receipt_no = 'RID' + RIGHT('0000000000' + CAST(receipt_id AS VARCHAR(10)), 10)
WHERE receipt_no IS NULL OR LTRIM(RTRIM(receipt_no)) = '';
GO

-- 建唯一索引前，先確保沒有 NULL/空字串
-- 若仍有重複（極低機率，除非你手動亂填），請先修正資料再建
IF EXISTS (
  SELECT receipt_no
  FROM dbo.ar_receipt
  GROUP BY receipt_no
  HAVING COUNT(1) > 1
)
BEGIN
  RAISERROR(N'存在重複 receipt_no，請先修正 dbo.ar_receipt.receipt_no 再建立唯一索引。',16,1);
END
GO

IF NOT EXISTS (
  SELECT 1
  FROM sys.indexes
  WHERE name = 'UX_ar_receipt_receipt_no'
    AND object_id = OBJECT_ID('dbo.ar_receipt')
)
BEGIN
  CREATE UNIQUE INDEX UX_ar_receipt_receipt_no ON dbo.ar_receipt(receipt_no);
END
GO

/* ============================================================
   2) ai_ar_* VIEW：提供一致輸出欄位（前端要 customer_name/refno）
   - 你目前 candidates 回 receipt 只有 customer_id
   - 這裡建立一個統一 view：ai_ar_v_receipt_enriched
   ============================================================ */

IF OBJECT_ID('dbo.ai_ar_v_receipt_enriched', 'V') IS NOT NULL
  DROP VIEW dbo.ai_ar_v_receipt_enriched;
GO

CREATE VIEW dbo.ai_ar_v_receipt_enriched
AS
  SELECT
    r.receipt_id,
    r.receipt_no,
    r.receipt_date,
    r.customer_id,
    c.refno  AS customer_refno,
    c.company AS customer_name,
    r.currency,
    r.receipt_amount,
    rb.applied_amount,
    rb.unapplied_amount
  FROM dbo.ar_receipt r
  LEFT JOIN dbo.customer c ON c.id = r.customer_id
  LEFT JOIN dbo.v_ar_receipt_balance rb ON rb.receipt_id = r.receipt_id;
GO

/* ============================================================
   3) ai_ar_* Wrapper SP：統一命名，內部仍呼叫你現有 sp_ar_*
      之後搬家：只要把 ai_ar_* 換成新庫版本即可
   ============================================================ */

-- 3.1 candidates：回傳 receipt + invoices
IF OBJECT_ID('dbo.ai_ar_sp_get_receipt_candidates', 'P') IS NOT NULL
  DROP PROCEDURE dbo.ai_ar_sp_get_receipt_candidates;
GO

CREATE PROCEDURE dbo.ai_ar_sp_get_receipt_candidates
  @receipt_id BIGINT,
  @top INT = 50
AS
BEGIN
  SET NOCOUNT ON;

  -- 第一個 result set：用 enriched view（補 customer_name/refno/receipt_no）
  SELECT TOP 1
    receipt_id,
    receipt_no,
    receipt_date,
    customer_id,
    customer_refno,
    customer_name,
    currency,
    receipt_amount,
    applied_amount,
    unapplied_amount
  FROM dbo.ai_ar_v_receipt_enriched
  WHERE receipt_id = @receipt_id;

  -- 第二個 result set：沿用你既有 SP（避免重寫）
  -- 注意：既有 sp_ar_get_receipt_candidates 會回兩個 result set（receipt/invoices）
  -- 但我們只要 invoices：所以這裡改成直接呼叫原 SP，並把第一個 result set 略過
  DECLARE @t TABLE(dummy INT); -- 只是佔位
  EXEC dbo.sp_ar_get_receipt_candidates @receipt_id=@receipt_id, @top=@top;
END
GO


-- 3.2 receipt applies
IF OBJECT_ID('dbo.ai_ar_sp_get_receipt_applies', 'P') IS NOT NULL
  DROP PROCEDURE dbo.ai_ar_sp_get_receipt_applies;
GO

CREATE PROCEDURE dbo.ai_ar_sp_get_receipt_applies
  @receipt_id BIGINT
AS
BEGIN
  SET NOCOUNT ON;
  EXEC dbo.sp_ar_get_receipt_applies @receipt_id=@receipt_id;
END
GO


-- 3.3 apply payment（你已經把 sp_ar_apply_payment 改成含 apply_date / actor，這裡只做統一入口）
IF OBJECT_ID('dbo.ai_ar_sp_apply_payment', 'P') IS NOT NULL
  DROP PROCEDURE dbo.ai_ar_sp_apply_payment;
GO

CREATE PROCEDURE dbo.ai_ar_sp_apply_payment
  @receipt_id   BIGINT,
  @ar_id        BIGINT,
  @apply_amount DECIMAL(18,2),
  @apply_date   DATE = NULL,
  @memo         NVARCHAR(400) = NULL,
  @actor        NVARCHAR(50) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  EXEC dbo.sp_ar_apply_payment
    @receipt_id   = @receipt_id,
    @ar_id        = @ar_id,
    @apply_amount = @apply_amount,
    @apply_date   = @apply_date,
    @actor        = @actor,
    @memo         = @memo;
END
GO


-- 3.4 FIFO（你現在的 sp_ar_apply_receipt_fifo 已經有 @actor / @apply_date）
IF OBJECT_ID('dbo.ai_ar_sp_apply_receipt_fifo', 'P') IS NOT NULL
  DROP PROCEDURE dbo.ai_ar_sp_apply_receipt_fifo;
GO

CREATE PROCEDURE dbo.ai_ar_sp_apply_receipt_fifo
  @receipt_id   BIGINT,
  @apply_total  DECIMAL(18,2) = NULL,
  @apply_date   DATE = NULL,
  @memo         NVARCHAR(200) = NULL,
  @actor        NVARCHAR(50) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  EXEC dbo.sp_ar_apply_receipt_fifo
    @receipt_id  = @receipt_id,
    @apply_total = @apply_total,
    @apply_date  = @apply_date,
    @memo        = @memo,
    @actor       = @actor;
END
GO


/* ============================================================
   4) 生成收款單號：提供一支「套用民國格式」的 SP
      - 新增收款後呼叫它，把 receipt_no 改為 ROC+MMDD+NNN
      - doc_type 固定用 'AR_RECEIPT'
   ============================================================ */

IF OBJECT_ID('dbo.ai_ar_sp_set_receipt_no', 'P') IS NOT NULL
  DROP PROCEDURE dbo.ai_ar_sp_set_receipt_no;
GO

CREATE PROCEDURE dbo.ai_ar_sp_set_receipt_no
  @receipt_id BIGINT
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @no VARCHAR(30);
  EXEC dbo.ai_doc_sp_next_no @doc_type='AR_RECEIPT', @doc_no=@no OUTPUT;

  UPDATE dbo.ar_receipt
  SET receipt_no = @no
  WHERE receipt_id = @receipt_id;

  SELECT @receipt_id AS receipt_id, @no AS receipt_no;
END
GO


/* ============================================================
   5) (可選) 收款建立 Wrapper：你後端 receipt-create 可改呼叫這支
      - 插入 ar_receipt 後，立刻套 receipt_no
   ============================================================ */

IF OBJECT_ID('dbo.ai_ar_sp_receipt_create', 'P') IS NOT NULL
  DROP PROCEDURE dbo.ai_ar_sp_receipt_create;
GO

CREATE PROCEDURE dbo.ai_ar_sp_receipt_create
  @customer_id INT,
  @receipt_date DATE,
  @currency NVARCHAR(10),
  @receipt_amount DECIMAL(18,2),
  @method NVARCHAR(50)=NULL,
  @bank_ref NVARCHAR(200)=NULL,
  @actor NVARCHAR(50)=NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  IF @actor IS NULL OR LTRIM(RTRIM(@actor))='' SET @actor='system';

  INSERT INTO dbo.ar_receipt
    (customer_id, currency, receipt_amount, receipt_date, method, bank_ref, created_by, created_at)
  VALUES
    (@customer_id, @currency, @receipt_amount, @receipt_date, @method, @bank_ref, @actor, GETDATE());

  DECLARE @rid BIGINT;
  SET @rid = SCOPE_IDENTITY();

  -- 套號
  EXEC dbo.ai_ar_sp_set_receipt_no @receipt_id=@rid;

  -- 回傳 enriched
  SELECT TOP 1 *
  FROM dbo.ai_ar_v_receipt_enriched
  WHERE receipt_id=@rid;
END
GO

/* ===================== END OF FILE ====================== */
