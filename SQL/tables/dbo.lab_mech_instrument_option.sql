IF OBJECT_ID(N'dbo.lab_mech_instrument_option', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_mech_instrument_option (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        instrument_no nvarchar(255) NOT NULL,
        created_at datetime NOT NULL CONSTRAINT DF_lab_mech_instrument_option_created_at DEFAULT(GETDATE())
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_mech_instrument_option_instrument_no'
      AND object_id = OBJECT_ID(N'dbo.lab_mech_instrument_option')
)
BEGIN
    CREATE UNIQUE INDEX UX_lab_mech_instrument_option_instrument_no
    ON dbo.lab_mech_instrument_option(instrument_no)
END
GO
