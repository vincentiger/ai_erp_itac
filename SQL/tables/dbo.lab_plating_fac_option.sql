IF OBJECT_ID(N'dbo.lab_plating_fac_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_plating_fac_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        plating_fac nvarchar(255) NOT NULL,
        created_at datetime NOT NULL CONSTRAINT DF_lab_plating_fac_option_created_at DEFAULT GETDATE()
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_plating_fac_option_plating_fac'
      AND object_id = OBJECT_ID(N'dbo.lab_plating_fac_option')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_lab_plating_fac_option_plating_fac
        ON dbo.lab_plating_fac_option(plating_fac)
END
GO
