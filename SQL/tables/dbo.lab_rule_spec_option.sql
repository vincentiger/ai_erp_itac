IF OBJECT_ID(N'dbo.lab_rule_spec_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_rule_spec_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        rule_spec nvarchar(255) NOT NULL,
        created_at datetime NOT NULL CONSTRAINT DF_lab_rule_spec_option_created_at DEFAULT GETDATE()
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_rule_spec_option_rule_spec'
      AND object_id = OBJECT_ID(N'dbo.lab_rule_spec_option')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_lab_rule_spec_option_rule_spec
        ON dbo.lab_rule_spec_option(rule_spec)
END
GO
