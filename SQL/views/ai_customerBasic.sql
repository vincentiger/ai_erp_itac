CREATE VIEW [dbo].[ai_customers]
AS
SELECT          TOP (100) PERCENT CB.customer_id, CB.refno, CB.company, CB.short, CB.no1, CB.no2, CB.country, CB.headquarter, 
                            CB.URL, CB.ceo, CB.class2, CB.items, CB.employee, CB.quit, CB.secret, CB.licenceNo, CB.payment, CB.credit, 
                            CB.commission, CB.remarks, X.item_type, X.item_value, X.item_seq
FROM               (SELECT          A.id AS customer_id, A.refno, ISNULL(NULLIF (A.company, N''), A.company_c) AS company, 
                                                         ISNULL(NULLIF (A.short, N''), A.short_c) AS short, A.no1, A.no2, A.country, C.company AS headquarter, 
                                                         A.URL, A.ceo, A.class2, A.items, A.employee, CASE WHEN ISNULL(A.quit, '') 
                                                         = 'Y' THEN N'已離職' ELSE N'' END AS quit, CASE WHEN ISNULL(A.secret, 0) 
                                                         = 1 THEN N'自營工廠' ELSE N'' END AS secret, A.licenceNo, A.payment, A.credit, A.commission, 
                                                         A.remarks
                             FROM               dbo.customer AS A LEFT OUTER JOIN
                                                         dbo.customer AS C ON C.id = A.headquarter
                             WHERE           (A.del = 0) OR
                                                         (A.del IS NULL)) AS CB INNER JOIN
                                (SELECT          refno, 'TEL' AS item_type, num AS item_value, ISNULL(tel_seq, 999999) AS item_seq
                                  FROM               dbo.tel AS E
                                  WHERE           (cate = 'c') AND (ISNULL(Def, 'T') = 'T') AND (ISNULL(tel_seq, 999999) <= 3)
                                  UNION ALL
                                  SELECT          refno, 'FAX' AS item_type, num AS item_value, ISNULL(tel_seq, 999999) AS item_seq
                                  FROM               dbo.tel AS E
                                  WHERE           (cate = 'c') AND (ISNULL(Def, 'F') = 'F') AND (ISNULL(tel_seq, 999999) <= 3)
                                  UNION ALL
                                  SELECT          refno, 'EMAIL' AS item_type, email AS item_value, ISNULL(email_seq, 999999) AS item_seq
                                  FROM               dbo.email AS F
                                  WHERE           (cate = 'c') AND (ISNULL(email_seq, 999999) <= 3)
                                  UNION ALL
                                  SELECT          refno, 'ADDR' AS item_type, Address AS item_value, ISNULL(addr_seq, 999999) AS item_seq
                                  FROM               dbo.Address AS B
                                  WHERE           (cate = 'c') AND (ISNULL(addr_seq, 999999) <= 3)
                                  UNION ALL
                                  SELECT          refno, 'CONTACT' AS item_type, CASE WHEN ISNULL(D .c_name, '') = '' THEN (ISNULL(D .first_name, '') 
                                                              + ' ' + ISNULL(D .last_name, '')) ELSE D .c_name END AS item_value, ISNULL(contact_seq, 999999) 
                                                              AS item_seq
                                  FROM               dbo.contact AS D
                                  WHERE           (cate = 'c') AND (ISNULL(contact_seq, 999999) <= 3)
                                  UNION ALL
                                  SELECT          R.refno, 'REP' AS item_type, S.name AS item_value, ISNULL(R.rep_seq, 999999) AS item_seq
                                  FROM               dbo.cus_rep AS R INNER JOIN
                                                              dbo.staff AS S ON S.id = R.sales_rep
                                  WHERE           (ISNULL(R.rep_seq, 999999) <= 3)) AS X ON X.refno = CB.refno
ORDER BY    CB.refno, X.item_type, X.item_seq
GO

