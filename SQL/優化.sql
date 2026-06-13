/* =========================================================
   1) TEL: add tel_seq + backfill (cate='c')
   - 規則：同 refno + cate，依 def(T 優先) + num 排序
   ========================================================= */
IF COL_LENGTH('dbo.tel', 'tel_seq') IS NULL
BEGIN
  ALTER TABLE dbo.tel ADD tel_seq INT NULL;
END;

;WITH x AS (
  SELECT
    t.*,
    ROW_NUMBER() OVER (
      PARTITION BY t.refno, t.cate
      ORDER BY
        CASE WHEN ISNULL(t.def,'')='T' THEN 0 ELSE 1 END,   -- T 優先
        ISNULL(t.num,'')
    ) AS rn
  FROM dbo.tel t
  WHERE t.cate = 'c'
)
UPDATE x
SET tel_seq = rn;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_tel_refno_cate_def_seq' AND object_id = OBJECT_ID('dbo.tel'))
BEGIN
  CREATE INDEX IX_tel_refno_cate_def_seq ON dbo.tel(refno, cate, def, tel_seq);
END;


/* =========================================================
   2) EMAIL: add email_seq + backfill (cate='c')
   - 規則：同 refno + cate，依 email 排序
   ========================================================= */
IF COL_LENGTH('dbo.email', 'email_seq') IS NULL
BEGIN
  ALTER TABLE dbo.email ADD email_seq INT NULL;
END;

;WITH x AS (
  SELECT
    e.*,
    ROW_NUMBER() OVER (
      PARTITION BY e.refno, e.cate
      ORDER BY ISNULL(e.email,'')
    ) AS rn
  FROM dbo.email e
  WHERE e.cate = 'c'
)
UPDATE x
SET email_seq = rn;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_email_refno_cate_seq' AND object_id = OBJECT_ID('dbo.email'))
BEGIN
  CREATE INDEX IX_email_refno_cate_seq ON dbo.email(refno, cate, email_seq);
END;


/* =========================================================
   3) CONTACT: add contact_seq + backfill (cate='c')
   - 規則：同 refno + cate，依「顯示名稱」排序
   ========================================================= */
IF COL_LENGTH('dbo.contact', 'contact_seq') IS NULL
BEGIN
  ALTER TABLE dbo.contact ADD contact_seq INT NULL;
END;

;WITH x AS (
  SELECT
    c.*,
    ROW_NUMBER() OVER (
      PARTITION BY c.refno, c.cate
      ORDER BY
        ISNULL(
          CASE
            WHEN ISNULL(c.c_name,'') = ''
              THEN LTRIM(RTRIM(ISNULL(c.first_name,''))) + ' ' + LTRIM(RTRIM(ISNULL(c.last_name,'')))
            ELSE c.c_name
          END
        ,'')
    ) AS rn
  FROM dbo.contact c
  WHERE c.cate = 'c'
)
UPDATE x
SET contact_seq = rn;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_contact_refno_cate_seq' AND object_id = OBJECT_ID('dbo.contact'))
BEGIN
  CREATE INDEX IX_contact_refno_cate_seq ON dbo.contact(refno, cate, contact_seq);
END;


/* =========================================================
   4) SALES REP: add rep_seq + backfill
   - 規則：同 refno 依 sales_rep 排序
   ========================================================= */
IF COL_LENGTH('dbo.cus_rep', 'rep_seq') IS NULL
BEGIN
  ALTER TABLE dbo.cus_rep ADD rep_seq INT NULL;
END;

;WITH x AS (
  SELECT
    r.*,
    ROW_NUMBER() OVER (
      PARTITION BY r.refno
      ORDER BY r.sales_rep
    ) AS rn
  FROM dbo.cus_rep r
)
UPDATE x
SET rep_seq = rn;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_cusrep_refno_seq' AND object_id = OBJECT_ID('dbo.cus_rep'))
BEGIN
  CREATE INDEX IX_cusrep_refno_seq ON dbo.cus_rep(refno, rep_seq);
END;


/* =========================================================
   5) ADDRESS: add addr_seq + backfill (cate='c')
   - 規則：同 refno + cate，依 Address 排序
   ========================================================= */
IF COL_LENGTH('dbo.[Address]', 'addr_seq') IS NULL
BEGIN
  ALTER TABLE dbo.[Address] ADD addr_seq INT NULL;
END;

;WITH x AS (
  SELECT
    a.*,
    ROW_NUMBER() OVER (
      PARTITION BY a.refno, a.cate
      ORDER BY ISNULL(a.[Address],'')
    ) AS rn
  FROM dbo.[Address] a
  WHERE a.cate = 'c'
)
UPDATE x
SET addr_seq = rn;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_Address_refno_cate_seq' AND object_id = OBJECT_ID('dbo.[Address]'))
BEGIN
  CREATE INDEX IX_Address_refno_cate_seq ON dbo.[Address](refno, cate, addr_seq);
END;

CREATE OR ALTER VIEW dbo.ai_A_quotation_lines AS
SELECT
  ql.id AS quotation_id,

  r.customer_id AS customer_id,
  c.company AS customer_name,          -- 客戶名稱（建議用英文欄名，API/JSON 穩定）

  ql.form_no AS pi_form_no,
  r.pi_no AS order_no,
  ql.c_order_no,

  r.original_date AS order_date,
  r.sales_rep AS sales_rep_id,
  st.name AS sales_rep_name,

  ql.item_no AS product_no,
  p.cate AS product_cate,

  ql.quantity AS order_qty,
  ql.unit_price,
  ql.unit_value,

  CAST(
    ql.quantity * ISNULL(ql.unit_price,0) / ISNULL(NULLIF(ql.unit_value, 0), 1)
    AS decimal(18,2)
  ) AS order_amount,

  CAST(ISNULL(ql.ssum,0) AS decimal(18,2)) AS ship_amount_cached

FROM dbo.quotation_list ql
JOIN dbo.orders r
  ON r.form_no = ql.form_no
JOIN dbo.customer c
  ON r.customer_id = c.id
JOIN dbo.staff st
  ON r.sales_rep = st.id
LEFT JOIN dbo.products p
  ON ql.item_no = p.item_no
WHERE RIGHT(r.form_no, 3) NOT LIKE 'R%';




-- orders 常用：排序 & join
CREATE INDEX IX_orders_original_date ON dbo.orders(original_date);
CREATE INDEX IX_orders_form_no       ON dbo.orders(form_no);
CREATE INDEX IX_orders_pi_no         ON dbo.orders(pi_no);
CREATE INDEX IX_orders_customer_id   ON dbo.orders(customer_id);

-- quotation_list：join/group by 的核心
CREATE INDEX IX_quotation_list_form_no ON dbo.quotation_list(form_no);
CREATE INDEX IX_quotation_list_form_no_corder ON dbo.quotation_list(form_no, c_order_no);

-- additional_Charge：join/group by
CREATE INDEX IX_additional_Charge_form_no ON dbo.additional_Charge(form_no);

-- customer join
CREATE INDEX IX_customer_id ON dbo.customer(id);

-- invoice_list：用 quotation_id 查詢/彙總一定要有
CREATE INDEX IX_invoice_list_quotation_id
ON dbo.invoice_list(quotation_id)
INCLUDE (form_no, item_no, quantity, unit_price, unit_value, c_order_no);



CREATE INDEX IX_shipment_docs_form_no
ON dbo.shipment_docs(form_no)
INCLUDE (form_no2, close_date);


CREATE TABLE dbo.ai_ql_ssum_reconcile_log (
  id              INT IDENTITY(1,1) PRIMARY KEY,
  quotation_id    INT NOT NULL,
  old_ssum        DECIMAL(18,2) NULL,
  new_ssum        DECIMAL(18,2) NULL,
  diff_amount     DECIMAL(18,2) NULL,
  row_cnt         INT NULL,
  last_ship_date  DATETIME NULL,
  created_at      DATETIME NOT NULL DEFAULT(GETDATE())
);

CREATE INDEX IX_ai_ql_ssum_reconcile_log_qid
ON dbo.ai_ql_ssum_reconcile_log(quotation_id, created_at);


CREATE OR ALTER PROCEDURE dbo.sp_reconcile_orders_ssum
  @date_from DATE = NULL,   -- 可選：只校正特定區間的出貨
  @date_to   DATE = NULL    -- 可選
AS
BEGIN
  SET NOCOUNT ON;

  ;WITH ship_calc AS (
    SELECT
      o.form_no AS pi_form_no,
      CAST(SUM(
        ISNULL(il.quantity,0) *
        (ISNULL(il.unit_price,0) / ISNULL(NULLIF(il.unit_value,0), 1))
      ) AS DECIMAL(18,2)) AS calc_ssum,
      COUNT(*) AS row_cnt,
      MAX(sd.close_date) AS last_ship_date
    FROM dbo.orders o
    JOIN dbo.invoice_list il
      ON il.pi_no = o.form_no
    JOIN dbo.shipment_docs sd
      ON sd.form_no = il.form_no
    WHERE (@date_from IS NULL OR sd.close_date >= @date_from)
      AND (@date_to   IS NULL OR sd.close_date < DATEADD(day,1,@date_to))
    GROUP BY o.form_no
  ),
  diff AS (
    SELECT
      o.form_no AS pi_form_no,
      CAST(ISNULL(o.ssum,0) AS DECIMAL(18,2)) AS old_ssum,
      sc.calc_ssum AS new_ssum,
      CAST(sc.calc_ssum - CAST(ISNULL(o.ssum,0) AS DECIMAL(18,2)) AS DECIMAL(18,2)) AS diff_amount,
      sc.row_cnt,
      sc.last_ship_date
    FROM dbo.orders o
    JOIN ship_calc sc
      ON sc.pi_form_no = o.form_no
    WHERE CAST(ISNULL(o.ssum,0) AS DECIMAL(18,2)) <> sc.calc_ssum
  )
  -- 1) 先寫 log（稽核）
  INSERT INTO dbo.ai_ssum_reconcile_log
    (pi_form_no, old_ssum, new_ssum, diff_amount, row_cnt, last_ship_date)
  SELECT
    pi_form_no, old_ssum, new_ssum, diff_amount, row_cnt, last_ship_date
  FROM diff;

  -- 2) 再更新 orders.ssum
  UPDATE o
  SET o.ssum = d.new_ssum
  FROM dbo.orders o
  JOIN diff d
    ON d.pi_form_no = o.form_no;

END



/****** Object:  Job [reconcile_quotation_ssum]    Script Date: 2026/1/25 下午 05:20:07 ******/
BEGIN TRANSACTION
DECLARE @ReturnCode INT
SELECT @ReturnCode = 0
/****** Object:  JobCategory [[Uncategorized (Local)]]    Script Date: 2026/1/25 下午 05:20:07 ******/
IF NOT EXISTS (SELECT name FROM msdb.dbo.syscategories WHERE name=N'[Uncategorized (Local)]' AND category_class=1)
BEGIN
EXEC @ReturnCode = msdb.dbo.sp_add_category @class=N'JOB', @type=N'LOCAL', @name=N'[Uncategorized (Local)]'
IF (@@ERROR <> 0 OR @ReturnCode <> 0) GOTO QuitWithRollback

END

DECLARE @jobId BINARY(16)
EXEC @ReturnCode =  msdb.dbo.sp_add_job @job_name=N'reconcile_quotation_ssum', 
		@enabled=1, 
		@notify_level_eventlog=0, 
		@notify_level_email=0, 
		@notify_level_netsend=0, 
		@notify_level_page=0, 
		@delete_level=0, 
		@description=N'reconcile_quotation_ssum', 
		@category_name=N'[Uncategorized (Local)]', 
		@owner_login_name=N'sa', @job_id = @jobId OUTPUT
IF (@@ERROR <> 0 OR @ReturnCode <> 0) GOTO QuitWithRollback
/****** Object:  Step [reconcile_quotation_ssum]    Script Date: 2026/1/25 下午 05:20:07 ******/
EXEC @ReturnCode = msdb.dbo.sp_add_jobstep @job_id=@jobId, @step_name=N'reconcile_quotation_ssum', 
		@step_id=1, 
		@cmdexec_success_code=0, 
		@on_success_action=1, 
		@on_success_step_id=0, 
		@on_fail_action=2, 
		@on_fail_step_id=0, 
		@retry_attempts=0, 
		@retry_interval=0, 
		@os_run_priority=0, @subsystem=N'TSQL', 
		@command=N'EXEC dbo.sp_ai_reconcile_quotation_ssum;
', 
		@database_name=N'Hanlien', 
		@flags=0
IF (@@ERROR <> 0 OR @ReturnCode <> 0) GOTO QuitWithRollback
EXEC @ReturnCode = msdb.dbo.sp_update_job @job_id = @jobId, @start_step_id = 1
IF (@@ERROR <> 0 OR @ReturnCode <> 0) GOTO QuitWithRollback
EXEC @ReturnCode = msdb.dbo.sp_add_jobschedule @job_id=@jobId, @name=N'reconcile_quotation_ssum;', 
		@enabled=1, 
		@freq_type=4, 
		@freq_interval=1, 
		@freq_subday_type=1, 
		@freq_subday_interval=0, 
		@freq_relative_interval=0, 
		@freq_recurrence_factor=0, 
		@active_start_date=20260125, 
		@active_end_date=99991231, 
		@active_start_time=115959, 
		@active_end_time=235959, 
		@schedule_uid=N'118addb1-78d4-4905-bae6-68d04ad7a7b1'
IF (@@ERROR <> 0 OR @ReturnCode <> 0) GOTO QuitWithRollback
EXEC @ReturnCode = msdb.dbo.sp_add_jobserver @job_id = @jobId, @server_name = N'(local)'
IF (@@ERROR <> 0 OR @ReturnCode <> 0) GOTO QuitWithRollback
COMMIT TRANSACTION
GOTO EndSave
QuitWithRollback:
    IF (@@TRANCOUNT > 0) ROLLBACK TRANSACTION
EndSave:
GO


DECLARE @idx_ok bit = 0;

;WITH idxcols AS (
  SELECT
    i.name AS index_name,
    c.name AS col_name,
    ic.key_ordinal
  FROM sys.indexes i
  JOIN sys.index_columns ic
    ON i.object_id = ic.object_id AND i.index_id = ic.index_id
  JOIN sys.columns c
    ON c.object_id = ic.object_id AND c.column_id = ic.column_id
  WHERE i.object_id = OBJECT_ID('dbo.ar_invoice')
    AND i.name = 'UQ_ar_invoice_form_no'
)
SELECT @idx_ok =
  CASE
    WHEN EXISTS (SELECT 1 FROM idxcols WHERE col_name = 'form_no' AND key_ordinal = 1)
     AND NOT EXISTS (SELECT 1 FROM idxcols WHERE key_ordinal = 1 AND col_name <> 'form_no')
    THEN 1 ELSE 0
  END;

IF EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE object_id = OBJECT_ID('dbo.ar_invoice')
    AND name = 'UQ_ar_invoice_form_no'
)
AND @idx_ok = 0
BEGIN
  PRINT 'Drop wrong UQ_ar_invoice_form_no ...';
  DROP INDEX UQ_ar_invoice_form_no ON dbo.ar_invoice;
END

IF NOT EXISTS (
  SELECT 1 FROM sys.indexes
  WHERE object_id = OBJECT_ID('dbo.ar_invoice')
    AND name = 'UQ_ar_invoice_form_no'
)
BEGIN
  PRINT 'Create UQ_ar_invoice_form_no on dbo.ar_invoice(form_no) ...';
  CREATE UNIQUE INDEX UQ_ar_invoice_form_no
  ON dbo.ar_invoice(form_no);
END
GO


;WITH x AS ( 
  SELECT
    r.form_no AS order_form_no,       -- 訂單系統編號（會重複於 view）
    r.pi_no,                          -- PI號（顯示用）
    r.original_date AS order_date,
    s.id   AS sales_rep_id,
    s.name AS sales_rep_name,
    c.id   AS customer_id,
    c.company AS customer_name,
    r.currency,
    NULL AS company_title
  FROM orders r
  INNER JOIN staff s    ON r.sales_rep   = s.id
  INNER JOIN customer c ON r.customer_id = c.id
  WHERE LEFT(RIGHT(r.form_no,3),1) <> 'R'
),
y AS (
  SELECT
    s.form_no  AS ship_form_no,       -- ✅ 出貨單系統 key（唯一）
    s.form_no2 AS in_no,              -- 可改，僅顯示
    s.close_date AS ship_date,

    SUM(i.quantity * i.unit_price / ISNULL(i.unit_value,1)) AS product_amount,

    ISNULL(ac.additional_amount,0) AS additional_amount,

    -- 連回訂單的橋：invoice_list.pi_no = orders.form_no（你已確認）
    MAX(i.pi_no) AS link_order_form_no

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
src AS (
  SELECT
    y.ship_form_no,                    -- -> ar_invoice.form_no
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
)
MERGE dbo.ar_invoice WITH (HOLDLOCK) AS T
USING src AS S
ON T.form_no = S.ship_form_no          -- ✅ 唯一鍵：出貨單系統編號
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
  T.in_no            = S.in_no,
  T.pi_no            = S.pi_no,
  T.customer_id      = S.customer_id,
  T.customer_name    = S.customer_name,
  T.sales_rep_id     = S.sales_rep_id,
  T.sales_rep_name   = S.sales_rep_name,
  T.company_title    = S.company_title,
  T.currency         = S.currency,
  T.product_amount   = S.product_amount,
  T.additional_amount= S.additional_amount,
  T.order_date       = S.order_date,
  T.ship_date        = S.ship_date,
  T.source_tag       = ISNULL(T.source_tag,'SHIP'),
  T.updated_at       = SYSDATETIME()
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
GO







