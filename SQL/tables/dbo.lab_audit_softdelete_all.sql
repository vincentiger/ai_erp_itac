/* =========================================================
   Lab Audit / Soft Delete / Judgment Columns Installer
   Target tables:
     - dbo.lab_qet_form
     - dbo.labMechRptMain
   Generated on: 2026-04-28
   ========================================================= */

PRINT 'Start installing lab audit / soft delete columns...';
GO

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

PRINT 'Lab audit / soft delete columns installation finished.';
GO
