IF OBJECT_ID(N'dbo.lab_test_category', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_test_category (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        cate_key nvarchar(50) NOT NULL,
        cate_name nvarchar(100) NOT NULL,
        sort_no int NOT NULL CONSTRAINT DF_lab_test_category_sort_no DEFAULT 0
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_test_category_cate_key'
      AND object_id = OBJECT_ID(N'dbo.lab_test_category')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_lab_test_category_cate_key
        ON dbo.lab_test_category(cate_key)
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_category WHERE cate_key = N'dimension')
    INSERT INTO dbo.lab_test_category(cate_key, cate_name, sort_no) VALUES (N'dimension', N'尺寸精度', 10)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_category WHERE cate_key = N'mechanical')
    INSERT INTO dbo.lab_test_category(cate_key, cate_name, sort_no) VALUES (N'mechanical', N'機械性能', 20)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_category WHERE cate_key = N'functional')
    INSERT INTO dbo.lab_test_category(cate_key, cate_name, sort_no) VALUES (N'functional', N'功能測試', 30)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_category WHERE cate_key = N'surface')
    INSERT INTO dbo.lab_test_category(cate_key, cate_name, sort_no) VALUES (N'surface', N'表面處理', 40)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_category WHERE cate_key = N'other')
    INSERT INTO dbo.lab_test_category(cate_key, cate_name, sort_no) VALUES (N'other', N'其他', 50)
GO
