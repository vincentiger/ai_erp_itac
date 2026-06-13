/*
尺寸原始紀錄表判定功能

這次沒有新增資料表，只有補 dbo.lab_qet_form 的判定欄位：
- judge_date
- judge_reviewer
*/

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
        ADD judge_reviewer nvarchar(200) NULL;
    END;
END;
