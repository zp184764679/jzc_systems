-- 任务导向项目管理 - 数据库迁移脚本
-- 为 tasks 表添加阶段关联、权重和完成百分比字段

-- 检查并添加 phase_id 字段
SET @dbname = 'cncplan';
SET @tablename = 'tasks';
SET @columnname = 'phase_id';
SET @preparedStatement = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
    'SELECT "phase_id column already exists"',
    'ALTER TABLE tasks ADD COLUMN phase_id INT NULL COMMENT "所属阶段ID"'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 检查并添加 weight 字段
SET @columnname = 'weight';
SET @preparedStatement = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
    'SELECT "weight column already exists"',
    'ALTER TABLE tasks ADD COLUMN weight INT DEFAULT 1 COMMENT "任务权重(1-10)"'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 检查并添加 completion_percentage 字段
SET @columnname = 'completion_percentage';
SET @preparedStatement = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = @dbname AND TABLE_NAME = @tablename AND COLUMN_NAME = @columnname) > 0,
    'SELECT "completion_percentage column already exists"',
    'ALTER TABLE tasks ADD COLUMN completion_percentage INT DEFAULT 0 COMMENT "完成百分比(0-100)"'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- 添加外键约束 (如果不存在)
-- 注意: 如果 project_phases 表不存在，此语句会失败，需要先创建该表
-- ALTER TABLE tasks ADD CONSTRAINT fk_task_phase FOREIGN KEY (phase_id) REFERENCES project_phases(id) ON DELETE SET NULL;

-- 添加索引
CREATE INDEX IF NOT EXISTS idx_tasks_phase_id ON tasks(phase_id);
CREATE INDEX IF NOT EXISTS idx_tasks_completion ON tasks(completion_percentage);

-- 显示完成信息
SELECT '任务字段迁移完成!' AS message;
SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'cncplan' AND TABLE_NAME = 'tasks'
AND COLUMN_NAME IN ('phase_id', 'weight', 'completion_percentage');
