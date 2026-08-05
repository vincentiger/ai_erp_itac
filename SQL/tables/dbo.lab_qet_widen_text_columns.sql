IF OBJECT_ID(N'dbo.lab_qet_form', N'U') IS NULL
BEGIN
    RAISERROR('dbo.lab_qet_form not found.', 16, 1);
    RETURN;
END
GO

IF COL_LENGTH('dbo.lab_qet_form', 'product_name') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN product_name nvarchar(300) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'specification') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN specification nvarchar(300) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'dimension_standard') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN dimension_standard nvarchar(500) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'drawing_no') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN drawing_no nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'regulation') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN regulation nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'lot_no') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN lot_no nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'material') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN material nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'manufacturer') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN manufacturer nvarchar(300) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'sampling_plan') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN sampling_plan nvarchar(300) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'tester') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN tester nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'reviewer') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN reviewer nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'remarks') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN remarks nvarchar(2000) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'created_by') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN created_by nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'updated_by') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN updated_by nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'deleted_by') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN deleted_by nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_form', 'judge_reviewer') IS NOT NULL
    ALTER TABLE dbo.lab_qet_form ALTER COLUMN judge_reviewer nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_item', 'item_name') IS NOT NULL
    ALTER TABLE dbo.lab_qet_item ALTER COLUMN item_name nvarchar(200) NOT NULL;
GO

IF COL_LENGTH('dbo.lab_qet_item', 'std_value') IS NOT NULL
    ALTER TABLE dbo.lab_qet_item ALTER COLUMN std_value nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_item', 'actual_value') IS NOT NULL
    ALTER TABLE dbo.lab_qet_item ALTER COLUMN actual_value nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_item', 'gauge_no') IS NOT NULL
    ALTER TABLE dbo.lab_qet_item ALTER COLUMN gauge_no nvarchar(200) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_item', 'remark') IS NOT NULL
    ALTER TABLE dbo.lab_qet_item ALTER COLUMN remark nvarchar(500) NULL;
GO

IF COL_LENGTH('dbo.lab_qet_measure', 'measure_value') IS NOT NULL
    ALTER TABLE dbo.lab_qet_measure ALTER COLUMN measure_value nvarchar(200) NULL;
GO
