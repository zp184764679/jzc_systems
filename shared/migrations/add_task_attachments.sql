-- Migration: Add attachments field to tasks table
-- Description: Support rich text descriptions with inline images and file attachments
-- Date: 2024-12-18

USE cncplan;

-- Add attachments column if not exists
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS attachments TEXT COMMENT '附件列表(JSON格式)' AFTER description;

-- Verify the change
SHOW COLUMNS FROM tasks WHERE Field = 'attachments';

SELECT '任务附件字段添加完成!' AS message;
