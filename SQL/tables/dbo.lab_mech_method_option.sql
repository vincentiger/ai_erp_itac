IF OBJECT_ID(N'dbo.lab_mech_method_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_mech_method_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        method_code nvarchar(255) NOT NULL,
        created_at datetime NOT NULL CONSTRAINT DF_lab_mech_method_option_created_at DEFAULT(GETDATE())
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_mech_method_option_method_code'
      AND object_id = OBJECT_ID(N'dbo.lab_mech_method_option')
)
BEGIN
    CREATE UNIQUE INDEX UX_lab_mech_method_option_method_code
    ON dbo.lab_mech_method_option(method_code)
END
GO
