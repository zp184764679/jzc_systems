-- 采购订单审批流程数据库迁移脚本
-- Migration Script for PO Approval Workflow
-- 日期: 2025-11-14

USE caigou;

-- 1. 修改 purchase_orders 表的 status 字段长度
ALTER TABLE purchase_orders 
MODIFY COLUMN status VARCHAR(50) NOT NULL DEFAULT 'created' 
COMMENT '状态：created/pending_admin_confirmation/pending_super_admin_confirmation/confirmed/received/completed/cancelled';

-- 2. 添加审批相关字段
ALTER TABLE purchase_orders
ADD COLUMN admin_confirmed_by BIGINT UNSIGNED NULL COMMENT '管理员确认人ID',
ADD COLUMN admin_confirmed_at DATETIME NULL COMMENT '管理员确认时间',
ADD COLUMN super_admin_confirmed_by BIGINT UNSIGNED NULL COMMENT '超级管理员确认人ID',
ADD COLUMN super_admin_confirmed_at DATETIME NULL COMMENT '超级管理员确认时间',
ADD COLUMN confirmation_note TEXT NULL COMMENT '确认备注';

-- 3. 添加外键约束
ALTER TABLE purchase_orders
ADD CONSTRAINT fk_po_admin_confirmed_by 
    FOREIGN KEY (admin_confirmed_by) REFERENCES users(id) ON DELETE SET NULL,
ADD CONSTRAINT fk_po_super_admin_confirmed_by 
    FOREIGN KEY (super_admin_confirmed_by) REFERENCES users(id) ON DELETE SET NULL;

-- 4. 添加索引以优化查询性能
CREATE INDEX idx_po_admin_confirmed_by ON purchase_orders(admin_confirmed_by);
CREATE INDEX idx_po_super_admin_confirmed_by ON purchase_orders(super_admin_confirmed_by);
CREATE INDEX idx_po_admin_confirmed_at ON purchase_orders(admin_confirmed_at);
CREATE INDEX idx_po_super_admin_confirmed_at ON purchase_orders(super_admin_confirmed_at);

-- 5. 数据迁移（可选）：将现有的 'created' 状态订单改为待管理员确认
-- 如果你希望现有订单也经过审批流程，取消下面的注释
-- UPDATE purchase_orders 
-- SET status = 'pending_admin_confirmation'
-- WHERE status = 'created';

-- 完成
SELECT '✓ 数据库迁移完成！已添加 PO 审批工作流字段和索引' AS message;
