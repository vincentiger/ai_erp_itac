IF OBJECT_ID(N'dbo.lab_heat_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_heat_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        heat_no nvarchar(100) NOT NULL,
        created_at datetime NOT NULL CONSTRAINT DF_lab_heat_option_created_at DEFAULT GETDATE()
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_heat_option_heat_no'
      AND object_id = OBJECT_ID(N'dbo.lab_heat_option')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_lab_heat_option_heat_no
        ON dbo.lab_heat_option(heat_no)
END
GO
