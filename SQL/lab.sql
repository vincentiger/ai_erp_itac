CREATE TABLE dbo.lab_qet_form (
    id               INT IDENTITY(1,1) PRIMARY KEY,
    form_id          UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    form_no          VARCHAR(30) NOT NULL,

    template_code    VARCHAR(30) NOT NULL DEFAULT 'QET-15-01',

    entrust_no       NVARCHAR(50) NULL,
    product_name     NVARCHAR(200) NULL,
    specification    NVARCHAR(200) NULL,
    plating_type     NVARCHAR(100) NULL,

    dimension_standard NVARCHAR(200) NULL,
    drawing_no       NVARCHAR(100) NULL,
    regulation       NVARCHAR(100) NULL,

    lot_no           NVARCHAR(100) NULL,
    lot_qty          INT NULL,

    material         NVARCHAR(100) NULL,
    manufacturer     NVARCHAR(200) NULL,

    size_unit        VARCHAR(10) NULL,     -- mm / inch

    env_temp         DECIMAL(10,2) NULL,
    env_humidity     DECIMAL(10,2) NULL,
    sampling_plan    NVARCHAR(100) NULL,

    test_date        DATE NULL,
    completed_date   DATE NULL,
    filled_date      DATE NULL,

    tester           NVARCHAR(100) NULL,
    reviewer         NVARCHAR(100) NULL,

    final_result     NVARCHAR(20) NULL,    -- PASS / FAIL / PENDING
    remarks          NVARCHAR(500) NULL,

    status           VARCHAR(20) NOT NULL DEFAULT 'DRAFT',

    created_at       DATETIME NOT NULL DEFAULT GETDATE(),
    created_by       NVARCHAR(100) NULL,
    updated_at       DATETIME NULL,
    updated_by       NVARCHAR(100) NULL
);
GO


CREATE UNIQUE INDEX IX_lab_qet_form_form_id
ON dbo.lab_qet_form(form_id);

CREATE UNIQUE INDEX IX_lab_qet_form_form_no
ON dbo.lab_qet_form(form_no);



CREATE TABLE dbo.lab_qet_item (
    id             INT IDENTITY(1,1) PRIMARY KEY,

    form_id        UNIQUEIDENTIFIER NOT NULL,

    seq_no         INT NOT NULL,

    item_name      NVARCHAR(50) NOT NULL,      -- A / B / C

    std_value      NVARCHAR(100) NULL,
    actual_value   NVARCHAR(100) NULL,

    gauge_no       NVARCHAR(100) NULL,

    inspect_qty    INT NULL,

    result         NVARCHAR(20) NULL,          -- PASS / FAIL

    remark         NVARCHAR(200) NULL
);
GO


CREATE INDEX IX_lab_qet_item_form
ON dbo.lab_qet_item(form_id, seq_no);



CREATE TABLE dbo.lab_qet_measure (
    id             INT IDENTITY(1,1) PRIMARY KEY,

    form_id        UNIQUEIDENTIFIER NOT NULL,

    item_id        INT NOT NULL,

    measure_no     INT NOT NULL,        -- 1~20 / 30

    measure_value  NVARCHAR(50) NULL
);
GO


CREATE INDEX IX_lab_qet_measure_item
ON dbo.lab_qet_measure(item_id, measure_no);



CREATE TABLE dbo.lab_running_no (
    code_key     VARCHAR(30) PRIMARY KEY,
    ymd          CHAR(8) NOT NULL,
    current_no   INT NOT NULL
);
GO



CREATE OR ALTER PROC dbo.sp_lab_qet_next_no
    @next_no VARCHAR(30) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @ymd CHAR(8) = CONVERT(CHAR(8), GETDATE(), 112);
    DECLARE @curr INT;

    IF EXISTS (
        SELECT 1
        FROM dbo.lab_running_no
        WHERE code_key='QET' AND ymd=@ymd
    )
    BEGIN
        UPDATE dbo.lab_running_no
           SET current_no = current_no + 1
         WHERE code_key='QET'
           AND ymd=@ymd;
    END
    ELSE
    BEGIN
        DELETE FROM dbo.lab_running_no WHERE code_key='QET';

        INSERT INTO dbo.lab_running_no(code_key, ymd, current_no)
        VALUES('QET', @ymd, 1);
    END

    SELECT @curr = current_no
    FROM dbo.lab_running_no
    WHERE code_key='QET'
      AND ymd=@ymd;

    SET @next_no =
        'QET'
        + @ymd
        + '-'
        + RIGHT('000' + CAST(@curr AS VARCHAR(3)), 3);
END
GO

-- 機械性質 ------------------------------------
-- 主表
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/* =========================================================
   lab 機械性質試驗資料表
   先刪除，再重建
   ========================================================= */

/* =========================================================
   1. DROP TABLE
   依相依順序：最子層 -> 最上層
   ========================================================= */

IF OBJECT_ID('dbo.labMechHydrogenData', 'U') IS NOT NULL
    DROP TABLE dbo.labMechHydrogenData;
GO

IF OBJECT_ID('dbo.labMechHydrogen', 'U') IS NOT NULL
    DROP TABLE dbo.labMechHydrogen;
GO

IF OBJECT_ID('dbo.labMechSaltSpray', 'U') IS NOT NULL
    DROP TABLE dbo.labMechSaltSpray;
GO

IF OBJECT_ID('dbo.labMechTestDecarb', 'U') IS NOT NULL
    DROP TABLE dbo.labMechTestDecarb;
GO

IF OBJECT_ID('dbo.labMechTestStatus', 'U') IS NOT NULL
    DROP TABLE dbo.labMechTestStatus;
GO

IF OBJECT_ID('dbo.labMechTestValues', 'U') IS NOT NULL
    DROP TABLE dbo.labMechTestValues;
GO

IF OBJECT_ID('dbo.labMechRptItem', 'U') IS NOT NULL
    DROP TABLE dbo.labMechRptItem;
GO

IF OBJECT_ID('dbo.labMechSpec', 'U') IS NOT NULL
    DROP TABLE dbo.labMechSpec;
GO

IF OBJECT_ID('dbo.labMechRptMain', 'U') IS NOT NULL
    DROP TABLE dbo.labMechRptMain;
GO

/* =========================================================
   2. CREATE TABLE
   ========================================================= */

-- 主表
CREATE TABLE dbo.labMechRptMain (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    report_no NVARCHAR(50) NOT NULL,
    entrust_no NVARCHAR(50) NULL,
    product_name NVARCHAR(100) NULL,
    spec_desc NVARCHAR(200) NULL,
    lot_no NVARCHAR(50) NULL,
    lot_qty INT NULL,
    plating NVARCHAR(100) NULL,
    material NVARCHAR(100) NULL,
    manufacturer NVARCHAR(100) NULL,
    standard_type NVARCHAR(30) NULL,      -- drawing / regulation
    standard_desc NVARCHAR(200) NULL,
    env_temp DECIMAL(8,2) NULL,
    env_humidity DECIMAL(8,2) NULL,
    test_date DATE NULL,
    complete_date DATE NULL,
    tester NVARCHAR(50) NULL,
    reviewer NVARCHAR(50) NULL,
    remarks NVARCHAR(500) NULL,
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechRptMain_created_at DEFAULT GETDATE(),
    updated_at DATETIME NOT NULL CONSTRAINT DF_labMechRptMain_updated_at DEFAULT GETDATE()
);
GO

-- 規格主檔
CREATE TABLE dbo.labMechSpec (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    product_key NVARCHAR(100) NOT NULL,
    test_code NVARCHAR(50) NOT NULL,      -- core_hardness, surface_hardness, decarb...
    spec_name NVARCHAR(100) NOT NULL,
    method_code NVARCHAR(100) NULL,
    unit NVARCHAR(30) NULL,
    spec_min DECIMAL(18,4) NULL,
    spec_max DECIMAL(18,4) NULL,
    spec_text NVARCHAR(300) NULL,
    judge_mode NVARCHAR(30) NOT NULL,     -- numeric_range / ok_ng / decarb / salt_spray / hydrogen / custom
    default_sample_count INT NULL,
    is_active BIT NOT NULL CONSTRAINT DF_labMechSpec_is_active DEFAULT 1,
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechSpec_created_at DEFAULT GETDATE()
);
GO

-- 測試項目主表
CREATE TABLE dbo.labMechRptItem (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    report_id INT NOT NULL,
    test_code NVARCHAR(50) NOT NULL,
    test_name NVARCHAR(100) NOT NULL,
    method_code NVARCHAR(100) NULL,
    unit NVARCHAR(30) NULL,
    sample_count INT NULL,
    spec_min DECIMAL(18,4) NULL,
    spec_max DECIMAL(18,4) NULL,
    spec_text NVARCHAR(300) NULL,
    judge_mode NVARCHAR(30) NOT NULL,
    instrument_no NVARCHAR(50) NULL,
    pass_count INT NOT NULL CONSTRAINT DF_labMechRptItem_pass_count DEFAULT 0,
    fail_count INT NOT NULL CONSTRAINT DF_labMechRptItem_fail_count DEFAULT 0,
    result NVARCHAR(10) NULL,             -- PASS / FAIL
    sort_no INT NOT NULL CONSTRAINT DF_labMechRptItem_sort_no DEFAULT 0,
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechRptItem_created_at DEFAULT GETDATE(),
    updated_at DATETIME NOT NULL CONSTRAINT DF_labMechRptItem_updated_at DEFAULT GETDATE(),
    CONSTRAINT FK_labMechRptItem_report
        FOREIGN KEY (report_id) REFERENCES dbo.labMechRptMain(id)
);
GO

-- 數值型明細
CREATE TABLE dbo.labMechTestValues (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    report_test_id INT NOT NULL,
    sample_no INT NOT NULL,
    reading_no INT NOT NULL CONSTRAINT DF_labMechTestValues_reading_no DEFAULT 1,
    value_num DECIMAL(18,4) NULL,
    avg_value DECIMAL(18,4) NULL,
    judge_value DECIMAL(18,4) NULL,
    result NVARCHAR(10) NULL,
    is_out_of_spec BIT NOT NULL CONSTRAINT DF_labMechTestValues_is_out_of_spec DEFAULT 0,
    remark NVARCHAR(200) NULL,
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechTestValues_created_at DEFAULT GETDATE(),
    CONSTRAINT FK_labMechTestValues_item
        FOREIGN KEY (report_test_id) REFERENCES dbo.labMechRptItem(id)
);
GO

-- OK/NG 型明細
CREATE TABLE dbo.labMechTestStatus (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    report_test_id INT NOT NULL,
    sample_no INT NOT NULL,
    result_status NVARCHAR(10) NOT NULL,  -- OK / NG
    is_out_of_spec BIT NOT NULL CONSTRAINT DF_labMechTestStatus_is_out_of_spec DEFAULT 0,
    remark NVARCHAR(200) NULL,
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechTestStatus_created_at DEFAULT GETDATE(),
    CONSTRAINT FK_labMechTestStatus_item
        FOREIGN KEY (report_test_id) REFERENCES dbo.labMechRptItem(id)
);
GO

-- 脫碳層明細
CREATE TABLE dbo.labMechTestDecarb (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    report_test_id INT NOT NULL,
    sample_no INT NOT NULL,
    hv1 DECIMAL(18,4) NOT NULL,
    hv2 DECIMAL(18,4) NOT NULL,
    hv3 DECIMAL(18,4) NOT NULL,
    result NVARCHAR(10) NULL,
    hv2_ok BIT NOT NULL CONSTRAINT DF_labMechTestDecarb_hv2_ok DEFAULT 0,
    hv3_ok BIT NOT NULL CONSTRAINT DF_labMechTestDecarb_hv3_ok DEFAULT 0,
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechTestDecarb_created_at DEFAULT GETDATE(),
    CONSTRAINT FK_labMechTestDecarb_item
        FOREIGN KEY (report_test_id) REFERENCES dbo.labMechRptItem(id)
);
GO

-- 鹽霧測試
CREATE TABLE dbo.labMechSaltSpray (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    report_test_id INT NOT NULL,
    spec_rust_type NVARCHAR(20) NOT NULL, -- white / red
    spec_hours INT NOT NULL,
    start_at DATETIME NULL,
    end_at DATETIME NULL,
    actual_hours DECIMAL(18,2) NULL,
    no_rust_pcs INT NOT NULL CONSTRAINT DF_labMechSaltSpray_no_rust_pcs DEFAULT 0,
    white_rust_pcs INT NOT NULL CONSTRAINT DF_labMechSaltSpray_white_rust_pcs DEFAULT 0,
    red_rust_pcs INT NOT NULL CONSTRAINT DF_labMechSaltSpray_red_rust_pcs DEFAULT 0,
    result NVARCHAR(10) NULL,
    angle_ok BIT NOT NULL CONSTRAINT DF_labMechSaltSpray_angle_ok DEFAULT 1,
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechSaltSpray_created_at DEFAULT GETDATE(),
    CONSTRAINT FK_labMechSaltSpray_item
        FOREIGN KEY (report_test_id) REFERENCES dbo.labMechRptItem(id)
);
GO

-- 氫脆測試
CREATE TABLE dbo.labMechHydrogen (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    report_test_id INT NOT NULL,
    plate_thickness DECIMAL(18,4) NULL,
    hole_diameter DECIMAL(18,4) NULL,
    plate_hardness DECIMAL(18,4) NULL,
    tighter_torque DECIMAL(18,4) NULL,
    no_failures_after_hours INT NULL,
    sample_count INT NULL,
    pass_count INT NOT NULL CONSTRAINT DF_labMechHydrogen_pass_count DEFAULT 0,
    fail_count INT NOT NULL CONSTRAINT DF_labMechHydrogen_fail_count DEFAULT 0,
    result NVARCHAR(10) NULL,
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechHydrogen_created_at DEFAULT GETDATE(),
    CONSTRAINT FK_labMechHydrogen_item
        FOREIGN KEY (report_test_id) REFERENCES dbo.labMechRptItem(id)
);
GO

-- 氫脆測試明細
CREATE TABLE dbo.labMechHydrogenData (
    id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    hydrogen_id INT NOT NULL,
    sample_no INT NOT NULL,
    tighten_at DATETIME NULL,
    remove_at DATETIME NULL,
    result_status NVARCHAR(10) NOT NULL,  -- OK / NG
    created_at DATETIME NOT NULL CONSTRAINT DF_labMechHydrogenData_created_at DEFAULT GETDATE(),
    CONSTRAINT FK_labMechHydrogenData_main
        FOREIGN KEY (hydrogen_id) REFERENCES dbo.labMechHydrogen(id)
);
GO

/* =========================================================
   3. INDEX
   ========================================================= */

CREATE UNIQUE INDEX UX_labMechRptMain_report_no
ON dbo.labMechRptMain(report_no);
GO

CREATE INDEX IX_labMechRptItem_report_id
ON dbo.labMechRptItem(report_id);
GO

CREATE INDEX IX_labMechRptItem_test_code
ON dbo.labMechRptItem(test_code);
GO

CREATE INDEX IX_labMechTestValues_report_test_id
ON dbo.labMechTestValues(report_test_id);
GO

CREATE INDEX IX_labMechTestValues_sample_no
ON dbo.labMechTestValues(sample_no);
GO

CREATE INDEX IX_labMechTestStatus_report_test_id
ON dbo.labMechTestStatus(report_test_id);
GO

CREATE INDEX IX_labMechTestStatus_sample_no
ON dbo.labMechTestStatus(sample_no);
GO

CREATE INDEX IX_labMechTestDecarb_report_test_id
ON dbo.labMechTestDecarb(report_test_id);
GO

CREATE INDEX IX_labMechSaltSpray_report_test_id
ON dbo.labMechSaltSpray(report_test_id);
GO

CREATE INDEX IX_labMechHydrogen_report_test_id
ON dbo.labMechHydrogen(report_test_id);
GO

CREATE INDEX IX_labMechHydrogenData_hydrogen_id
ON dbo.labMechHydrogenData(hydrogen_id);
GO

CREATE INDEX IX_labMechSpec_product_key_test_code_is_active
ON dbo.labMechSpec(product_key, test_code, is_active);
GO