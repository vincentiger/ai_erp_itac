IF OBJECT_ID(N'dbo.lab_qet_form', N'U') IS NULL
BEGIN
    RAISERROR('dbo.lab_qet_form not found.', 16, 1);
    RETURN;
END
GO

IF COL_LENGTH('dbo.lab_qet_form', 'judge_date') IS NULL
    ALTER TABLE dbo.lab_qet_form ADD judge_date datetime NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'judge_reviewer') IS NULL
    ALTER TABLE dbo.lab_qet_form ADD judge_reviewer nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'is_deleted') IS NULL
    ALTER TABLE dbo.lab_qet_form ADD is_deleted bit NOT NULL CONSTRAINT DF_lab_qet_form_is_deleted DEFAULT(0);
GO

IF COL_LENGTH('dbo.lab_qet_form', 'deleted_at') IS NULL
    ALTER TABLE dbo.lab_qet_form ADD deleted_at datetime NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'deleted_by') IS NULL
    ALTER TABLE dbo.lab_qet_form ADD deleted_by nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'created_by') IS NULL
    ALTER TABLE dbo.lab_qet_form ADD created_by nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'updated_by') IS NULL
    ALTER TABLE dbo.lab_qet_form ADD updated_by nvarchar(100) NULL;
GO

UPDATE dbo.lab_qet_form
SET is_deleted = 0
WHERE is_deleted IS NULL;
GO
