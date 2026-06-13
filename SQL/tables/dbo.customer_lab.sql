IF COL_LENGTH('dbo.customer', 'lab') IS NULL
BEGIN
    ALTER TABLE dbo.customer
    ADD lab bit NOT NULL
        CONSTRAINT DF_customer_lab DEFAULT (0);
END
ELSE
BEGIN
    UPDATE dbo.customer
    SET lab = 0
    WHERE lab IS NULL;
END

UPDATE dbo.customer
SET lab = 0
WHERE ISNULL(lab, 0) <> 0;
