IF OBJECT_ID(N'dbo.lab_test_method', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_test_method (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        item_id int NOT NULL,
        method_text nvarchar(500) NOT NULL,
        sort_no int NOT NULL CONSTRAINT DF_lab_test_method_sort_no DEFAULT 0
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.foreign_keys
    WHERE name = N'FK_lab_test_method_item_id'
)
BEGIN
    ALTER TABLE dbo.lab_test_method
    ADD CONSTRAINT FK_lab_test_method_item_id
        FOREIGN KEY (item_id) REFERENCES dbo.lab_test_item(id)
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_lab_test_method_item_id_sort_no'
      AND object_id = OBJECT_ID(N'dbo.lab_test_method')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_lab_test_method_item_id_sort_no
        ON dbo.lab_test_method(item_id, sort_no)
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_test_method_item_id_method_text'
      AND object_id = OBJECT_ID(N'dbo.lab_test_method')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_lab_test_method_item_id_method_text
        ON dbo.lab_test_method(item_id, method_text)
END
GO
