IF OBJECT_ID(N'dbo.lab_test_item', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lab_test_item (
        id int IDENTITY(1,1) NOT NULL PRIMARY KEY,
        cate_key nvarchar(50) NOT NULL,
        item_name nvarchar(100) NOT NULL,
        sort_no int NOT NULL CONSTRAINT DF_lab_test_item_sort_no DEFAULT 0
    )
END
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_lab_test_item_cate_key_item_name'
      AND object_id = OBJECT_ID(N'dbo.lab_test_item')
)
BEGIN
    CREATE UNIQUE NONCLUSTERED INDEX UX_lab_test_item_cate_key_item_name
        ON dbo.lab_test_item(cate_key, item_name)
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'dimension' AND item_name = N'一般尺寸')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'dimension', N'一般尺寸', 10)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'dimension' AND item_name = N'外螺紋精度')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'dimension', N'外螺紋精度', 20)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'dimension' AND item_name = N'內螺紋精度')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'dimension', N'內螺紋精度', 30)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'mechanical' AND item_name = N'心部硬度')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'mechanical', N'心部硬度', 10)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'mechanical' AND item_name = N'表面硬度')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'mechanical', N'表面硬度', 20)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'mechanical' AND item_name = N'滲碳深度')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'mechanical', N'滲碳深度', 30)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'mechanical' AND item_name = N'脫碳測試')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'mechanical', N'脫碳測試', 40)
GO
IF EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'functional' AND item_name = N'功能測試')
BEGIN
    DELETE m
    FROM dbo.lab_test_method m
    INNER JOIN dbo.lab_test_item i ON i.id = m.item_id
    WHERE i.cate_key = N'functional'
      AND i.item_name = N'功能測試'

    DELETE FROM dbo.lab_test_item
    WHERE cate_key = N'functional'
      AND item_name = N'功能測試'
END
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'functional' AND item_name = N'延展性(鎚擊)')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'functional', N'延展性(鎚擊)', 20)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'functional' AND item_name = N'扭力')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'functional', N'扭力', 30)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'functional' AND item_name = N'氫脆化')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'functional', N'氫脆化', 40)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'functional' AND item_name = N'攻速')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'functional', N'攻速', 50)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'functional' AND item_name = N'旋入')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'functional', N'旋入', 60)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'surface' AND item_name = N'電鍍膜厚')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'surface', N'電鍍膜厚', 10)
GO
IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'surface' AND item_name = N'鹽水噴霧')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'surface', N'鹽水噴霧', 20)
GO
IF EXISTS (
    SELECT 1
    FROM dbo.lab_test_item
    WHERE cate_key = N'other' AND item_name = N'XXX'
)
AND NOT EXISTS (
    SELECT 1
    FROM dbo.lab_test_item
    WHERE cate_key = N'other' AND item_name = N'其他'
)
BEGIN
    UPDATE dbo.lab_test_item
    SET item_name = N'其他'
    WHERE cate_key = N'other' AND item_name = N'XXX'
END
GO

IF NOT EXISTS (SELECT 1 FROM dbo.lab_test_item WHERE cate_key = N'other' AND item_name = N'其他')
    INSERT INTO dbo.lab_test_item(cate_key, item_name, sort_no) VALUES (N'other', N'其他', 10)
GO

IF EXISTS (
    SELECT 1
    FROM dbo.lab_test_item
    WHERE cate_key = N'other' AND item_name = N'XXX'
)
AND EXISTS (
    SELECT 1
    FROM dbo.lab_test_item
    WHERE cate_key = N'other' AND item_name = N'其他'
)
BEGIN
    DECLARE @OtherItemId int
    DECLARE @XxxItemId int

    SELECT TOP 1 @OtherItemId = id
    FROM dbo.lab_test_item
    WHERE cate_key = N'other' AND item_name = N'其他'

    SELECT TOP 1 @XxxItemId = id
    FROM dbo.lab_test_item
    WHERE cate_key = N'other' AND item_name = N'XXX'

    IF @OtherItemId IS NOT NULL AND @XxxItemId IS NOT NULL
    BEGIN
        INSERT INTO dbo.lab_test_method(item_id, method_text, sort_no)
        SELECT @OtherItemId, src.method_text, src.sort_no
        FROM dbo.lab_test_method src
        WHERE src.item_id = @XxxItemId
          AND NOT EXISTS (
              SELECT 1
              FROM dbo.lab_test_method dst
              WHERE dst.item_id = @OtherItemId
                AND dst.method_text = src.method_text
          )

        DELETE FROM dbo.lab_test_method WHERE item_id = @XxxItemId
        DELETE FROM dbo.lab_test_item WHERE id = @XxxItemId
    END
END
GO
