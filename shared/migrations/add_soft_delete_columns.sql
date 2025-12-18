-- 添加软删除字段到项目表和文件表
-- Migration: add_soft_delete_columns
-- Date: 2025-12-18
-- Description: 为 projects 和 project_files 表添加软删除支持

-- 1. 添加 projects 表软删除字段
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL COMMENT '删除时间（软删除）',
ADD COLUMN IF NOT EXISTS delete_reason VARCHAR(500) NULL COMMENT '删除原因',
ADD COLUMN IF NOT EXISTS deleted_by_id INT NULL COMMENT '删除者ID';

-- 2. 添加 project_files 表软删除字段
ALTER TABLE project_files
ADD COLUMN IF NOT EXISTS deleted_at DATETIME NULL COMMENT '删除时间（软删除）',
ADD COLUMN IF NOT EXISTS delete_reason VARCHAR(500) NULL COMMENT '删除原因',
ADD COLUMN IF NOT EXISTS deleted_by_id INT NULL COMMENT '删除者ID';

-- 3. 创建索引加速软删除查询
CREATE INDEX IF NOT EXISTS idx_projects_deleted_at ON projects(deleted_at);
CREATE INDEX IF NOT EXISTS idx_project_files_deleted_at ON project_files(deleted_at);

-- 4. 创建已删除项目视图（便于管理回收站）
CREATE OR REPLACE VIEW v_deleted_projects AS
SELECT
    p.*,
    (SELECT COUNT(*) FROM project_files pf WHERE pf.project_id = p.id AND pf.deleted_at IS NOT NULL) as deleted_files_count
FROM projects p
WHERE p.deleted_at IS NOT NULL
ORDER BY p.deleted_at DESC;

-- 5. 创建已删除文件视图
CREATE OR REPLACE VIEW v_deleted_files AS
SELECT
    pf.*,
    p.name as project_name,
    p.project_no
FROM project_files pf
JOIN projects p ON pf.project_id = p.id
WHERE pf.deleted_at IS NOT NULL
ORDER BY pf.deleted_at DESC;
