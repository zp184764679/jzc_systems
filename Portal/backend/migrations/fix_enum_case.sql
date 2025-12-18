-- Migration: Fix enum case to lowercase
-- Date: 2024-12-18
-- Description: 修复项目管理表的枚举值为小写

-- 修复 project_issues 表枚举值
ALTER TABLE project_issues
  MODIFY COLUMN issue_type ENUM('quality_issue','delay','cost_overrun','requirement_change','resource_shortage','communication','technical','other') NOT NULL DEFAULT 'other',
  MODIFY COLUMN severity ENUM('low','medium','high','critical') NOT NULL DEFAULT 'medium',
  MODIFY COLUMN status ENUM('open','in_progress','resolved','closed','reopened') NOT NULL DEFAULT 'open';

-- 修复 project_phases 表枚举值
ALTER TABLE project_phases
  MODIFY COLUMN phase_type ENUM('customer_order','quotation','procurement','production','qc','shipping','receipt') NOT NULL,
  MODIFY COLUMN status ENUM('pending','in_progress','completed','blocked') NOT NULL DEFAULT 'pending';

-- 修复 project_tasks 表枚举值（如果需要）
ALTER TABLE project_tasks
  MODIFY COLUMN task_type ENUM('general','design','development','review','testing','documentation','deployment','meeting','other') NOT NULL DEFAULT 'general',
  MODIFY COLUMN status ENUM('pending','in_progress','completed','blocked','cancelled') NOT NULL DEFAULT 'pending',
  MODIFY COLUMN priority ENUM('low','normal','high','urgent') NOT NULL DEFAULT 'normal';

-- 修复 project_files 表枚举值
ALTER TABLE project_files
  MODIFY COLUMN category ENUM('specification','drawing','contract','report','other') NOT NULL DEFAULT 'other',
  MODIFY COLUMN original_language ENUM('zh','en','ja','other') NOT NULL DEFAULT 'zh';
