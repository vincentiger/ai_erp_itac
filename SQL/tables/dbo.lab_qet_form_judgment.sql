IF OBJECT_ID(N'dbo.lab_qet_form', N'U') IS NOT NULL
BEGIN
    IF COL_LENGTH(N'dbo.lab_qet_form', N'judge_date') IS NULL
    BEGIN
        ALTER TABLE dbo.lab_qet_form
        ADD judge_date datetime NULL;
    END;

    IF COL_LENGTH(N'dbo.lab_qet_form', N'judge_reviewer') IS NULL
    BEGIN
        ALTER TABLE dbo.lab_qet_form
        ADD judge_reviewer nvarchar(100) NULL;
    END;
END;
