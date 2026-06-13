USE [Hanlien];
GO

/* =========================================================
   1) 倉庫主檔（你目前只有一倉，但先留擴充）
   ========================================================= */
IF OBJECT_ID('dbo.inv_warehouse', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.inv_warehouse (
    wh_id      INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    wh_code    VARCHAR(20) NOT NULL,
    wh_name    NVARCHAR(50) NOT NULL,
    is_active  BIT NOT NULL DEFAULT(1),
    created_at DATETIME NOT NULL DEFAULT(GETDATE())
  );

  CREATE UNIQUE INDEX UX_inv_warehouse_code ON dbo.inv_warehouse(wh_code);

  -- 預設建立「主倉」
  INSERT INTO dbo.inv_warehouse(wh_code, wh_name) VALUES ('MAIN', N'主倉');
END
GO


/* =========================================================
   2) 入庫單(表頭) GRN Header
   - 可追溯採購單：po_form_no / po_no / factory_id / company_title / sales_rep
   - 單號：grn_no（民國年mmdd+流水）
   ========================================================= */
IF OBJECT_ID('dbo.inv_grn', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.inv_grn (
    grn_id        BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    grn_no        VARCHAR(30) NULL,              -- 入庫單號(顯示用)
    grn_date      DATE NOT NULL,
    wh_id         INT NOT NULL,
    po_form_no    VARCHAR(20) NOT NULL,          -- purchase.form_no
    po_no         VARCHAR(30) NULL,              -- purchase.po_no（顯示）
    factory_id    INT NULL,                      -- purchase.factory_id
    sales_rep_id  INT NULL,                      -- purchase.sales_rep
    company_title INT NULL,                      -- purchase.company_title
    memo          NVARCHAR(200) NULL,
    status        VARCHAR(20) NOT NULL DEFAULT('DRAFT'),  -- DRAFT/POSTED/VOID
    created_by    NVARCHAR(50) NULL,
    created_at    DATETIME NOT NULL DEFAULT(GETDATE()),
    posted_by     NVARCHAR(50) NULL,
    posted_at     DATETIME NULL
  );

  CREATE INDEX IX_inv_grn_po_form_no ON dbo.inv_grn(po_form_no);
  CREATE INDEX IX_inv_grn_grn_date   ON dbo.inv_grn(grn_date);
  CREATE INDEX IX_inv_grn_wh_id      ON dbo.inv_grn(wh_id);
END
GO


/* =========================================================
   3) 入庫單(明細) GRN Lines
   - 核心追溯：purchase_list.id
   - 收到數量：recv_qty（允許多/少進 -> 用 SP 做檢核）
   ========================================================= */
IF OBJECT_ID('dbo.inv_grn_line', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.inv_grn_line (
    grn_line_id     BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    grn_id          BIGINT NOT NULL,
    purchase_list_id BIGINT NOT NULL,     -- purchase_list.id
    item_no         VARCHAR(50) NOT NULL,
    pi_item_no      VARCHAR(50) NULL,     -- pl.p_item_no（你 view 有）
    po_qty          DECIMAL(18,4) NULL,   -- 參考採購量（當下快照）
    recv_qty        DECIMAL(18,4) NOT NULL DEFAULT(0),
    unit_price      DECIMAL(18,6) NULL,   -- 參考單價（當下快照）
    currency        VARCHAR(10) NULL,
    memo            NVARCHAR(200) NULL
  );

  ALTER TABLE dbo.inv_grn_line
    ADD CONSTRAINT FK_inv_grn_line_grn
    FOREIGN KEY (grn_id) REFERENCES dbo.inv_grn(grn_id);

  CREATE INDEX IX_inv_grn_line_grn_id ON dbo.inv_grn_line(grn_id);
  CREATE INDEX IX_inv_grn_line_pl_id  ON dbo.inv_grn_line(purchase_list_id);
  CREATE INDEX IX_inv_grn_line_item   ON dbo.inv_grn_line(item_no);
END
GO


/* =========================================================
   4) 庫存異動帳（Kardex / Ledger）
   - 每一次入庫/出庫都寫一筆（未來出貨會用同一張表）
   - 你說先做進貨：先支援 type='GRN'
   ========================================================= */
IF OBJECT_ID('dbo.inv_stock_ledger', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.inv_stock_ledger (
    led_id      BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    tx_date     DATETIME NOT NULL DEFAULT(GETDATE()),
    wh_id       INT NOT NULL,
    item_no     VARCHAR(50) NOT NULL,
    tx_type     VARCHAR(20) NOT NULL,         -- GRN / SHIP / ADJ...
    ref_table   VARCHAR(50) NULL,             -- inv_grn / shipment...
    ref_id      BIGINT NULL,                  -- grn_id
    ref_line_id BIGINT NULL,                  -- grn_line_id
    qty_in      DECIMAL(18,4) NOT NULL DEFAULT(0),
    qty_out     DECIMAL(18,4) NOT NULL DEFAULT(0),
    memo        NVARCHAR(200) NULL,
    created_by  NVARCHAR(50) NULL
  );

  CREATE INDEX IX_inv_stock_ledger_item_date ON dbo.inv_stock_ledger(item_no, tx_date);
  CREATE INDEX IX_inv_stock_ledger_wh_item   ON dbo.inv_stock_ledger(wh_id, item_no);
  CREATE INDEX IX_inv_stock_ledger_ref       ON dbo.inv_stock_ledger(ref_table, ref_id);
END
GO


/* =========================================================
   5) (可選) 即時庫存餘額表（快取用）
   - 如果你之後做「可用庫存」查詢會很快
   - 先建起來不影響現在開發
   ========================================================= */
IF OBJECT_ID('dbo.inv_stock_balance', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.inv_stock_balance (
    wh_id      INT NOT NULL,
    item_no    VARCHAR(50) NOT NULL,
    qty_onhand DECIMAL(18,4) NOT NULL DEFAULT(0),
    updated_at DATETIME NOT NULL DEFAULT(GETDATE()),
    CONSTRAINT PK_inv_stock_balance PRIMARY KEY (wh_id, item_no)
  );
END
GO


/* =========================================================
   6) 入庫單號：grn_no 唯一索引（避免 NULL 卡住）
   - 先把 NULL 回填成 GID+id，避免你之前 receipt_no unique index 的坑
   ========================================================= */
IF COL_LENGTH('dbo.inv_grn', 'grn_no') IS NOT NULL
BEGIN
  UPDATE dbo.inv_grn
  SET grn_no = 'GID' + RIGHT('0000000000' + CAST(grn_id AS VARCHAR(10)), 10)
  WHERE grn_no IS NULL OR LTRIM(RTRIM(grn_no)) = '';
END
GO

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE name='UX_inv_grn_grn_no' AND object_id=OBJECT_ID('dbo.inv_grn')
)
BEGIN
  CREATE UNIQUE INDEX UX_inv_grn_grn_no ON dbo.inv_grn(grn_no);
END
GO


/* =========================================================
   7) 產生入庫單號 SP：用 ai_doc_sp_next_no（民國年mmdd+流水）
   - doc_type = 'GRN'
   ========================================================= */
IF OBJECT_ID('dbo.sp_inv_grn_set_no', 'P') IS NOT NULL
  DROP PROCEDURE dbo.sp_inv_grn_set_no;
GO

CREATE PROCEDURE dbo.sp_inv_grn_set_no
  @grn_id BIGINT
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @no VARCHAR(30);
  -- 你前面已經有 dbo.ai_doc_sp_next_no
  EXEC dbo.ai_doc_sp_next_no @doc_type='GRN', @doc_no=@no OUTPUT;

  UPDATE dbo.inv_grn
  SET grn_no = @no
  WHERE grn_id = @grn_id;

  SELECT @grn_id AS grn_id, @no AS grn_no;
END
GO




USE [Hanlien];
GO

/*============================================================
  0) 取號表：ai_doc_no (每天每單據代碼各自流水)
============================================================*/
IF OBJECT_ID('dbo.ai_doc_no', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.ai_doc_no
  (
    doc_code VARCHAR(20) NOT NULL,
    ymd      CHAR(8)     NOT NULL,   -- YYYYMMDD
    next_seq INT         NOT NULL,
    updated_at DATETIME  NOT NULL CONSTRAINT DF_ai_doc_no_updated_at DEFAULT(GETDATE()),
    CONSTRAINT PK_ai_doc_no PRIMARY KEY (doc_code, ymd)
  );
END
GO

/*============================================================
  1) 取下一碼流水：dbo.ai_doc_sp_next_no
     @doc_code + @ymd (YYYYMMDD) 每天重置
============================================================*/
IF OBJECT_ID('dbo.ai_doc_sp_next_no', 'P') IS NOT NULL
  DROP PROCEDURE dbo.ai_doc_sp_next_no;
GO

CREATE PROCEDURE dbo.ai_doc_sp_next_no
  @doc_code VARCHAR(20),
  @ymd      CHAR(8),
  @next_seq INT OUTPUT
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  IF @doc_code IS NULL OR LTRIM(RTRIM(@doc_code)) = ''
  BEGIN
    RAISERROR(N'doc_code 不可為空', 16, 1);
    RETURN;
  END

  IF @ymd IS NULL OR LEN(@ymd) <> 8
  BEGIN
    RAISERROR(N'ymd 必須為 YYYYMMDD', 16, 1);
    RETURN;
  END

  BEGIN TRAN;

  -- 先鎖住該組 key
  IF EXISTS (SELECT 1 FROM dbo.ai_doc_no WITH (UPDLOCK, HOLDLOCK) WHERE doc_code=@doc_code AND ymd=@ymd)
  BEGIN
    UPDATE dbo.ai_doc_no
      SET next_seq = next_seq + 1,
          updated_at = GETDATE()
    WHERE doc_code=@doc_code AND ymd=@ymd;

    SELECT @next_seq = next_seq
    FROM dbo.ai_doc_no
    WHERE doc_code=@doc_code AND ymd=@ymd;
  END
  ELSE
  BEGIN
    INSERT INTO dbo.ai_doc_no(doc_code, ymd, next_seq)
    VALUES(@doc_code, @ymd, 1);

    SET @next_seq = 1;
  END

  COMMIT;
END
GO

/*============================================================
  2) 入庫單取號：dbo.sp_inv_grn_set_no
     將 inv_grn.grn_no 依 grn_date 產生：ROC + MM + DD + 3碼流水
============================================================*/
IF OBJECT_ID('dbo.sp_inv_grn_set_no', 'P') IS NOT NULL
  DROP PROCEDURE dbo.sp_inv_grn_set_no;
GO

CREATE PROCEDURE dbo.sp_inv_grn_set_no
  @grn_id     BIGINT = NULL,         -- ✅ 有給：會寫回 inv_grn
  @grn_date   DATE   = NULL,         -- ✅ 沒給 grn_id 時必填：只產生號碼回傳
  @grn_no_out VARCHAR(30) OUTPUT     -- ✅ 回傳產生的 grn_no（或既有號碼）
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  DECLARE @grn_no VARCHAR(30);

  -- -----------------------------
  -- 模式 A：用 grn_id（讀表 + 必要時更新）
  -- -----------------------------
  IF @grn_id IS NOT NULL
  BEGIN
    SELECT
      @grn_date = grn_date,
      @grn_no   = grn_no
    FROM dbo.inv_grn WITH (UPDLOCK, HOLDLOCK)
    WHERE grn_id = @grn_id;

    IF @grn_date IS NULL
    BEGIN
      RAISERROR(N'找不到入庫單或 grn_date 為空', 16, 1);
      RETURN;
    END

    -- 已有號碼就不再取
    IF @grn_no IS NOT NULL AND LTRIM(RTRIM(@grn_no)) <> ''
    BEGIN
      SET @grn_no_out = @grn_no;
      RETURN;
    END
  END
  ELSE
  BEGIN
    -- -----------------------------
    -- 模式 B：只給日期（不寫回表，只回傳號碼）
    -- -----------------------------
    IF @grn_date IS NULL
    BEGIN
      RAISERROR(N'@grn_id 與 @grn_date 不可同時為 NULL', 16, 1);
      RETURN;
    END
  END

  -- -----------------------------
  -- 取號：doc_code='GRN' + ymd
  -- -----------------------------
  DECLARE @ymd CHAR(8) = CONVERT(CHAR(8), @grn_date, 112);
  DECLARE @roc VARCHAR(3) = RIGHT('000' + CAST((YEAR(@grn_date) - 1911) AS VARCHAR(3)), 3);
  DECLARE @mm  VARCHAR(2) = RIGHT('0' + CAST(MONTH(@grn_date) AS VARCHAR(2)), 2);
  DECLARE @dd  VARCHAR(2) = RIGHT('0' + CAST(DAY(@grn_date) AS VARCHAR(2)), 2);

  DECLARE @seq INT;
  EXEC dbo.ai_doc_sp_next_no @doc_code='GRN', @ymd=@ymd, @next_seq=@seq OUTPUT;

  DECLARE @seq3 VARCHAR(3) = RIGHT('000' + CAST(@seq AS VARCHAR(3)), 3);

  -- 最終號碼：ROC + MM + DD + seq3
  SET @grn_no = @roc + @mm + @dd + @seq3;

  -- -----------------------------
  -- 模式 A：寫回表
  -- -----------------------------
  IF @grn_id IS NOT NULL
  BEGIN
    UPDATE dbo.inv_grn
      SET grn_no = @grn_no
    WHERE grn_id = @grn_id;
  END

  -- 回傳
  SET @grn_no_out = @grn_no;
END
GO







USE [Hanlien];
GO

IF OBJECT_ID('dbo.inv_warehouse','U') IS NULL
BEGIN
  CREATE TABLE dbo.inv_warehouse
  (
    wh_id      INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    wh_code    VARCHAR(20) NOT NULL,
    wh_name    NVARCHAR(100) NOT NULL,
    is_active  BIT NOT NULL CONSTRAINT DF_inv_warehouse_is_active DEFAULT(1),
    created_at DATETIME NOT NULL CONSTRAINT DF_inv_warehouse_created_at DEFAULT(GETDATE())
  );

  CREATE UNIQUE INDEX UX_inv_warehouse_wh_code ON dbo.inv_warehouse(wh_code);
END
GO

-- 補一筆預設倉（如果尚未存在）
IF NOT EXISTS (SELECT 1 FROM dbo.inv_warehouse WHERE wh_code='MAIN')
BEGIN
  INSERT INTO dbo.inv_warehouse(wh_code, wh_name) VALUES('MAIN', N'主倉');
END
GO




USE [Hanlien];
GO
SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

ALTER PROCEDURE [dbo].[sp_inv_grn_create_from_po]
  @po_form_no   VARCHAR(20),
  @grn_date     DATE = NULL,
  @actor        NVARCHAR(50) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  BEGIN TRY
    IF @actor IS NULL OR LTRIM(RTRIM(@actor)) = '' SET @actor = N'system';
    IF @grn_date IS NULL SET @grn_date = CAST(GETDATE() AS DATE);

    -- 取主倉
    DECLARE @wh_id INT;
    SELECT TOP 1 @wh_id = wh_id
    FROM dbo.inv_warehouse
    WHERE wh_code = 'MAIN' AND is_active = 1;

    IF @wh_id IS NULL
    BEGIN
      RAISERROR(N'找不到主倉(inv_warehouse wh_code=MAIN)', 16, 1);
      RETURN;
    END

    -- 驗證採購單存在，抓表頭資訊
    DECLARE
      @po_no        VARCHAR(30),
      @factory_id   INT,
      @sales_rep_id INT,
      @company_title NVARCHAR(100);

    SELECT
      @po_no         = p.po_no,
      @factory_id    = p.factory_id,
      @sales_rep_id  = p.sales_rep,
      @company_title = CAST(p.company_title AS NVARCHAR(100))
    FROM dbo.purchase p
    WHERE p.form_no = @po_form_no
      AND LEFT(RIGHT(p.form_no,3),1) <> 'R';

    IF @po_no IS NULL
    BEGIN
      RAISERROR(N'找不到採購單(purchase.form_no) 或此單為作廢/退回類型', 16, 1);
      RETURN;
    END

    -- 驗證採購明細存在
    IF NOT EXISTS (SELECT 1 FROM dbo.purchase_list WHERE form_no = @po_form_no)
    BEGIN
      RAISERROR(N'採購單沒有明細(purchase_list)', 16, 1);
      RETURN;
    END

    -- ✅ 先取號：避免 inv_grn.grn_no NOT NULL 造成 515
    DECLARE @grn_no VARCHAR(30);
    EXEC dbo.sp_inv_grn_set_no
      NULL,         -- @grn_id
      @grn_date,    -- @grn_date
      @grn_no OUTPUT; -- @grn_no_out

    IF @grn_no IS NULL OR LTRIM(RTRIM(@grn_no)) = ''
    BEGIN
      RAISERROR(N'取號失敗(sp_inv_grn_set_no)', 16, 1);
      RETURN;
    END

    BEGIN TRAN;

    -- 建表頭
    DECLARE @grn_id BIGINT;

    INSERT INTO dbo.inv_grn
    (
      grn_no, grn_date, wh_id,
      po_form_no, po_no,
      factory_id, sales_rep_id, company_title,
      memo, status,
      created_by, created_at
    )
    VALUES
    (
      @grn_no, @grn_date, @wh_id,
      @po_form_no, @po_no,
      @factory_id, @sales_rep_id, @company_title,
      NULL, 'DRAFT',
      @actor, GETDATE()
    );

    SET @grn_id = CAST(SCOPE_IDENTITY() AS BIGINT);

    -- 建明細（把 PO qty/price snapshot 到入庫明細）
    INSERT INTO dbo.inv_grn_line
    (
      grn_id, purchase_list_id,
      item_no, pi_item_no,
      po_qty, recv_qty,
      unit_price, currency,
      memo
    )
    SELECT
      @grn_id,
      pl.id,
      pl.item_no,
      pl.p_item_no,
      CAST(pl.f_qty AS DECIMAL(18,4)) AS po_qty,
      CAST(0 AS DECIMAL(18,4))        AS recv_qty,
      CAST(pl.f_price / ISNULL(pl.unit_value,1) AS DECIMAL(18,6)) AS unit_price,
      NULL AS currency,
      NULL AS memo
    FROM dbo.purchase_list pl
    WHERE pl.form_no = @po_form_no;

    COMMIT;

    -- 回傳：表頭+明細（方便前端直接顯示）
    SELECT * FROM dbo.inv_grn WHERE grn_id = @grn_id;
    SELECT * FROM dbo.inv_grn_line WHERE grn_id = @grn_id ORDER BY grn_line_id;

  END TRY
  BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;

    DECLARE @err NVARCHAR(4000) =
      N'create_from_po 失敗：' + ERROR_MESSAGE()
      + N' (line ' + CAST(ERROR_LINE() AS NVARCHAR(10)) + N')';

    RAISERROR(@err, 16, 1);
    RETURN;
  END CATCH
END
GO

USE [Hanlien];
GO

IF OBJECT_ID('dbo.inv_grn_line', 'U') IS NULL
BEGIN
  CREATE TABLE dbo.inv_grn_line
  (
    grn_line_id      BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    grn_id           BIGINT NOT NULL,          -- 對應 inv_grn.grn_id
    purchase_list_id BIGINT NULL,              -- 對應 purchase_list.id（你 SP 用 pl.id）
    item_no          VARCHAR(50) NOT NULL,
    pi_item_no       VARCHAR(50) NULL,

    po_qty           DECIMAL(18,4) NOT NULL CONSTRAINT DF_inv_grn_line_po_qty DEFAULT(0),
    recv_qty         DECIMAL(18,4) NOT NULL CONSTRAINT DF_inv_grn_line_recv_qty DEFAULT(0),

    unit_price       DECIMAL(18,6) NULL,
    currency         VARCHAR(10) NULL,
    memo             NVARCHAR(500) NULL,

    created_at       DATETIME NOT NULL CONSTRAINT DF_inv_grn_line_created_at DEFAULT(GETDATE())
  );

  -- 常用查詢索引：依 grn_id 拉明細
  CREATE INDEX IX_inv_grn_line_grn_id ON dbo.inv_grn_line(grn_id);

  -- 建議：避免同一張 GRN 重複塞同一筆 purchase_list_id
  --（如果你允許分批入庫同一 purchase_list_id，這個 UNIQUE 就不要加）
  --CREATE UNIQUE INDEX UX_inv_grn_line_grn_pl
  --ON dbo.inv_grn_line(grn_id, purchase_list_id);

  -- FK（若你想嚴格一點，可打開；先跑通流程也可以暫時不加）
  --ALTER TABLE dbo.inv_grn_line
  --ADD CONSTRAINT FK_inv_grn_line_grn
  --FOREIGN KEY (grn_id) REFERENCES dbo.inv_grn(grn_id);
END
GO



CREATE TABLE dbo.inv_grn (
    grn_id        INT IDENTITY(1,1) PRIMARY KEY,
    grn_no        NVARCHAR(20) NOT NULL,        -- GRN單號
    po_form_no    NVARCHAR(20) NOT NULL,        -- 對應 PO
    grn_date      DATE NOT NULL,
    status        NVARCHAR(20) NOT NULL DEFAULT 'OPEN',

    created_by    NVARCHAR(50) NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT GETDATE()
);


ALTER TABLE dbo.inv_grn ADD
    wh_id          INT NULL,
    po_no          NVARCHAR(30) NULL,
    factory_id     INT NULL,
    sales_rep_id   INT NULL,
    company_title  NVARCHAR(100) NULL,
    memo           NVARCHAR(500) NULL;


-- posted_by
IF COL_LENGTH('dbo.inv_grn', 'posted_by') IS NULL
BEGIN
  ALTER TABLE dbo.inv_grn
  ADD posted_by NVARCHAR(50) NULL;
END

-- posted_at
IF COL_LENGTH('dbo.inv_grn', 'posted_at') IS NULL
BEGIN
  ALTER TABLE dbo.inv_grn
  ADD posted_at DATETIME NULL;
END




/*============================================================
  3) 修正版：dbo.sp_inv_grn_post
     - 修正 RAISERROR 2748：不再用 %f 直接帶 DECIMAL，改成字串訊息
============================================================*/
IF OBJECT_ID('dbo.sp_inv_grn_post', 'P') IS NOT NULL
  DROP PROCEDURE dbo.sp_inv_grn_post;
GO

CREATE PROCEDURE dbo.sp_inv_grn_post
  @grn_id BIGINT,
  @actor  NVARCHAR(50) = NULL
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  IF @actor IS NULL OR LTRIM(RTRIM(@actor)) = '' SET @actor = N'system';

  DECLARE
    @status VARCHAR(20),
    @po_form_no VARCHAR(20),
    @wh_id INT,
    @grn_no VARCHAR(30);

  SELECT
    @status    = g.status,
    @po_form_no= g.po_form_no,
    @wh_id     = g.wh_id,
    @grn_no    = g.grn_no
  FROM dbo.inv_grn g WITH (UPDLOCK, HOLDLOCK)
  WHERE g.grn_id = @grn_id;

  IF @po_form_no IS NULL
  BEGIN
    RAISERROR(N'找不到入庫單(inv_grn)', 16, 1);
    RETURN;
  END

  IF @status = 'POSTED'
  BEGIN
    RAISERROR(N'此入庫單已過帳(POSTED)，不可重複過帳', 16, 1);
    RETURN;
  END

  IF @status = 'VOID'
  BEGIN
    RAISERROR(N'此入庫單已作廢(VOID)，不可過帳', 16, 1);
    RETURN;
  END

  -- 若未取號，補取號
  IF @grn_no IS NULL OR LTRIM(RTRIM(@grn_no)) = ''
  BEGIN
    DECLARE @tmp_grn_no VARCHAR(30);
    EXEC dbo.sp_inv_grn_set_no @grn_id = @grn_id, @grn_no_out = @tmp_grn_no OUTPUT;

    SELECT @grn_no = grn_no FROM dbo.inv_grn WHERE grn_id = @grn_id;
  END

  -- 允許%（少進不擋；只擋超收 uplimit）
  DECLARE @uplimit DECIMAL(18,6);
  SELECT @uplimit = ISNULL(CAST(p.uplimit AS DECIMAL(18,6)), 0)
  FROM dbo.purchase p
  WHERE p.form_no = @po_form_no;

  IF @uplimit IS NULL SET @uplimit = 0;

  IF NOT EXISTS (SELECT 1 FROM dbo.inv_grn_line WHERE grn_id = @grn_id)
  BEGIN
    RAISERROR(N'入庫單沒有明細(inv_grn_line)', 16, 1);
    RETURN;
  END

  IF NOT EXISTS (SELECT 1 FROM dbo.inv_grn_line WHERE grn_id = @grn_id AND ISNULL(recv_qty,0) > 0)
  BEGIN
    RAISERROR(N'沒有任何入庫數量(recv_qty) > 0，無法過帳', 16, 1);
    RETURN;
  END

  ;WITH cur AS (
    SELECT
      l.purchase_list_id,
      MAX(ISNULL(l.po_qty,0)) AS po_qty,
      SUM(ISNULL(l.recv_qty,0)) AS this_recv
    FROM dbo.inv_grn_line l
    WHERE l.grn_id = @grn_id
    GROUP BY l.purchase_list_id
  ),
  posted AS (
    SELECT
      l.purchase_list_id,
      SUM(ISNULL(l.recv_qty,0)) AS posted_recv
    FROM dbo.inv_grn g
    JOIN dbo.inv_grn_line l ON l.grn_id = g.grn_id
    WHERE g.status = 'POSTED'
      AND g.po_form_no = @po_form_no
      AND g.grn_id <> @grn_id
    GROUP BY l.purchase_list_id
  )
  SELECT TOP 1
    c.purchase_list_id,
    c.po_qty,
    ISNULL(p.posted_recv,0) AS posted_recv,
    c.this_recv AS this_recv,
    (ISNULL(p.posted_recv,0) + c.this_recv) AS total_after,
    (c.po_qty * (1 + (@uplimit/100.0))) AS max_allow
  INTO #chk
  FROM cur c
  LEFT JOIN posted p ON p.purchase_list_id = c.purchase_list_id
  WHERE (ISNULL(p.posted_recv,0) + c.this_recv) > (c.po_qty * (1 + (@uplimit/100.0)))
    AND c.po_qty > 0;

  IF EXISTS (SELECT 1 FROM #chk)
  BEGIN
    DECLARE
      @pl_id BIGINT,
      @po_qty DECIMAL(18,4),
      @posted_recv DECIMAL(18,4),
      @this_recv DECIMAL(18,4),
      @max_allow DECIMAL(18,6);

    SELECT TOP 1
      @pl_id = purchase_list_id,
      @po_qty = po_qty,
      @posted_recv = posted_recv,
      @this_recv = this_recv,
      @max_allow = max_allow
    FROM #chk;

    DROP TABLE #chk;

    DECLARE @msg NVARCHAR(400);
    SET @msg =
      N'入庫超過允許上限：purchase_list_id=' + CAST(@pl_id AS NVARCHAR(20)) +
      N'，PO=' + CAST(@po_qty AS NVARCHAR(40)) +
      N'，已入=' + CAST(@posted_recv AS NVARCHAR(40)) +
      N'，本次=' + CAST(@this_recv AS NVARCHAR(40)) +
      N'，上限=' + CAST(@max_allow AS NVARCHAR(40));

    RAISERROR(@msg, 16, 1);
    RETURN;
  END

  DROP TABLE #chk;

  BEGIN TRAN;

  DECLARE
    @grn_line_id BIGINT,
    @item_no VARCHAR(50),
    @qty DECIMAL(18,4);

  DECLARE curLine CURSOR LOCAL FAST_FORWARD FOR
    SELECT grn_line_id, item_no, CAST(ISNULL(recv_qty,0) AS DECIMAL(18,4)) AS recv_qty
    FROM dbo.inv_grn_line
    WHERE grn_id = @grn_id
      AND ISNULL(recv_qty,0) > 0;

  OPEN curLine;
  FETCH NEXT FROM curLine INTO @grn_line_id, @item_no, @qty;

  WHILE @@FETCH_STATUS = 0
  BEGIN
    INSERT INTO dbo.inv_stock_ledger
    (
      tx_date, wh_id, item_no,
      tx_type, ref_table, ref_id, ref_line_id,
      qty_in, qty_out, memo, created_by
    )
    VALUES
    (
      GETDATE(), @wh_id, @item_no,
      'GRN', 'inv_grn', @grn_id, @grn_line_id,
      @qty, 0,
      N'GRN ' + ISNULL(@grn_no, ''),
      @actor
    );

    IF EXISTS (SELECT 1 FROM dbo.inv_stock_balance WHERE wh_id=@wh_id AND item_no=@item_no)
    BEGIN
      UPDATE dbo.inv_stock_balance
      SET qty_onhand = qty_onhand + @qty,
          updated_at = GETDATE()
      WHERE wh_id=@wh_id AND item_no=@item_no;
    END
    ELSE
    BEGIN
      INSERT INTO dbo.inv_stock_balance(wh_id, item_no, qty_onhand, updated_at)
      VALUES(@wh_id, @item_no, @qty, GETDATE());
    END

    FETCH NEXT FROM curLine INTO @grn_line_id, @item_no, @qty;
  END

  CLOSE curLine;
  DEALLOCATE curLine;

  UPDATE dbo.inv_grn
  SET
    status = 'POSTED',
    posted_by = @actor,
    posted_at = GETDATE()
  WHERE grn_id = @grn_id;

  COMMIT;

  SELECT grn_id, grn_no, status, posted_by, posted_at
  FROM dbo.inv_grn
  WHERE grn_id = @grn_id;
END
GO



CREATE VIEW dbo.v_inv_grn_list
AS
SELECT
  g.grn_id, g.grn_no, g.grn_date,
  g.po_form_no, g.po_no,
  g.status, g.posted_at,
  w.wh_code
FROM dbo.inv_grn g
LEFT JOIN dbo.inv_warehouse w ON w.wh_id = g.wh_id;



CREATE INDEX IX_purchase_original_date ON dbo.purchase(original_date) INCLUDE(form_no, po_no, factory_id);
CREATE INDEX IX_purchase_po_no ON dbo.purchase(po_no) INCLUDE(form_no, original_date, factory_id);

-- purchase_list：form_no join + item_no like
CREATE INDEX IX_purchase_list_form_no ON dbo.purchase_list(form_no) INCLUDE(id, item_no, f_qty, f_price, unit_value);
CREATE INDEX IX_purchase_list_item_no ON dbo.purchase_list(item_no) INCLUDE(form_no, id, f_qty);



USE [Hanlien];
GO

IF OBJECT_ID('dbo.inv_stock_move', 'U') IS NOT NULL
  DROP TABLE dbo.inv_stock_move;
GO

CREATE TABLE dbo.inv_stock_move (
  move_id        bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
  move_date      date          NOT NULL,
  move_type      nvarchar(10)  NOT NULL,        -- IN / OUT / ADJ
  wh_id          int           NULL,
  item_no        varchar(50)   NOT NULL,
  qty            decimal(18,4) NOT NULL,        -- 允許小數
  currency       varchar(10)   NULL,
  unit_price     decimal(18,6) NULL,

  source_type    nvarchar(20)  NOT NULL,        -- GRN
  source_no      nvarchar(20)  NULL,            -- grn_no
  source_id      int           NULL,            -- grn_id
  source_line_id bigint        NULL,            -- grn_line_id
  po_no          nvarchar(30)  NULL,
  po_form_no     nvarchar(20)  NULL,

  memo           nvarchar(500) NULL,
  created_by     nvarchar(50)  NOT NULL,
  created_at     datetime      NOT NULL CONSTRAINT DF_inv_stock_move_created_at DEFAULT (getdate())
);
GO

CREATE INDEX IX_inv_stock_move_item_date ON dbo.inv_stock_move(item_no, move_date);
CREATE INDEX IX_inv_stock_move_source     ON dbo.inv_stock_move(source_type, source_line_id);
GO




-- inv_grn_line：排序/分頁主鍵 + join key
CREATE INDEX IX_inv_grn_line_grnlineid ON dbo.inv_grn_line(grn_line_id);
CREATE INDEX IX_inv_grn_line_purchase_list_id ON dbo.inv_grn_line(purchase_list_id);

-- inv_grn：常用篩選
CREATE INDEX IX_inv_grn_status_grnid ON dbo.inv_grn(status, grn_id);

-- ai_purchase：用 id join（通常 id 已是 PK，就不用再加）


GRANT INSERT ON dbo.inv_grn TO [ai_erp_api];
GRANT INSERT ON dbo.inv_grn_line TO [ai_erp_api];


GRANT UPDATE ON dbo.inv_grn TO [ai_erp_api];
GRANT UPDATE ON dbo.inv_grn_line TO [ai_erp_api];

