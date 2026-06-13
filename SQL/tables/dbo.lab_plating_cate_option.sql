IF OBJECT_ID(N'dbo.lab_plating_cate_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_plating_cate_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        plating_cate nvarchar(100) NOT NULL,
        created_at datetime NOT NULL CONSTRAINT DF_lab_plating_cate_option_created_at DEFAULT GETDATE()
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_plating_cate_option_plating_cate'
      AND object_id = OBJECT_ID(N'dbo.lab_plating_cate_option')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_lab_plating_cate_option_plating_cate
        ON dbo.lab_plating_cate_option(plating_cate)
END
GO
