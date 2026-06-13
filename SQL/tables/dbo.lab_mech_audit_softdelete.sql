IF OBJECT_ID(N'dbo.labMechRptMain', N'U') IS NULL
BEGIN
    RAISERROR('dbo.labMechRptMain not found.', 16, 1);
    RETURN;
END
GO

IF COL_LENGTH('dbo.labMechRptMain', 'final_result') IS NULL
    ALTER TABLE dbo.labMechRptMain ADD final_result nvarchar(20) NULL;
GO

IF COL_LENGTH('dbo.labMechRptMain', 'judge_date') IS NULL
    ALTER TABLE dbo.labMechRptMain ADD judge_date datetime NULL;
GO

IF COL_LENGTH('dbo.labMechRptMain', 'judge_reviewer') IS NULL
    ALTER TABLE dbo.labMechRptMain ADD judge_reviewer nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.labMechRptMain', 'is_deleted') IS NULL
    ALTER TABLE dbo.labMechRptMain ADD is_deleted bit NOT NULL CONSTRAINT DF_labMechRptMain_is_deleted DEFAULT(0);
GO

IF COL_LENGTH('dbo.labMechRptMain', 'deleted_at') IS NULL
    ALTER TABLE dbo.labMechRptMain ADD deleted_at datetime NULL;
GO

IF COL_LENGTH('dbo.labMechRptMain', 'deleted_by') IS NULL
    ALTER TABLE dbo.labMechRptMain ADD deleted_by nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.labMechRptMain', 'created_by') IS NULL
    ALTER TABLE dbo.labMechRptMain ADD created_by nvarchar(100) NULL;
GO

IF COL_LENGTH('dbo.labMechRptMain', 'updated_by') IS NULL
    ALTER TABLE dbo.labMechRptMain ADD updated_by nvarchar(100) NULL;
GO

UPDATE dbo.labMechRptMain
SET is_deleted = 0
WHERE is_deleted IS NULL;
GO

UPDATE dbo.labMechRptMain
SET final_result = 'PENDING'
WHERE final_result IS NULL OR LTRIM(RTRIM(final_result)) = '';
GO
