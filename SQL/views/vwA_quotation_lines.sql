CREATE VIEW dbo.vwA_quotation_lines AS
SELECT
  ql.id              AS quotation_id,

  -- PI / 訂單識別
  ql.form_no         AS pi_form_no,      -- 系統用（穩定）
  r.pi_no            AS order_no,        -- 顯示用（可改）
  ql.c_order_no,                          -- 客戶訂單號（追溯）

  -- 人與時間
  r.original_date    AS order_date,
  r.sales_rep        AS sales_rep_id,
  st.name            AS sales_rep_name,

  -- 品項
  ql.item_no         AS product_no,
  ql.quantity        AS order_qty,
  ql.unit_price,
  ql.unit_value,

  -- 金額（unit_value NULL/0 都視為 1）
  CAST(
    ql.quantity * ql.unit_price / ISNULL(NULLIF(ql.unit_value,0), 1)
    AS decimal(18,2)
  ) AS order_amount

FROM dbo.quotation_list ql
JOIN dbo.orders r
  ON r.form_no = ql.form_no
JOIN dbo.staff st
  ON r.sales_rep = st.id
WHERE RIGHT(r.form_no, 3) NOT LIKE 'R%';


CREATE OR ALTER VIEW dbo.vwB_ship_lines_raw AS
SELECT
  -- 若 invoice_list 有 id/line id，強烈建議帶出來（便於追查）
  i.id AS invoice_line_id,                -- 若沒有這欄就刪掉

  ISNULL(sd.form_no2, sd.form_no) AS ship_no,   -- 顯示號優先，沒有就用系統號
  sd.form_no  AS ship_form_no,

  i.quotation_id,                          -- 核心：對回訂單品項
  i.c_order_no,                            -- 追溯用（要不要留你可決定）
  i.item_no   AS product_no,

  ISNULL(i.quantity, 0) AS ship_qty,

  -- 單價：unit_value NULL/0 視為 1；unit_price NULL 視為 0
  CAST(
    ISNULL(i.unit_price, 0) / ISNULL(NULLIF(i.unit_value, 0), 1)
    AS decimal(18,6)
  ) AS ship_unit_price

FROM dbo.shipment_docs sd
JOIN dbo.invoice_list i
  ON sd.form_no = i.form_no
WHERE i.quotation_id IS NOT NULL;
