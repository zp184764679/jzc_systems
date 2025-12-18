-- CRM 数据库迁移脚本
-- 日期: 2025-12-18
-- 说明: 重命名表（添加 crm_ 前缀）+ 添加客户分级字段

-- ============================================
-- 1. 重命名表（添加 crm_ 前缀）
-- ============================================
-- 注意: order 是 MySQL 保留字，需要用反引号
RENAME TABLE `order` TO crm_orders;
RENAME TABLE order_line TO crm_order_lines;
RENAME TABLE plan TO crm_plans;
RENAME TABLE record TO crm_records;
RENAME TABLE route TO crm_routes;
RENAME TABLE step TO crm_steps;
RENAME TABLE employees TO crm_employees;
RENAME TABLE inventory_tx TO crm_inventory_tx;
RENAME TABLE settlement_methods TO crm_settlement_methods;
RENAME TABLE shipping_methods TO crm_shipping_methods;
RENAME TABLE order_methods TO crm_order_methods;
RENAME TABLE currencies TO crm_currencies;
RENAME TABLE order_statuses TO crm_order_statuses;
RENAME TABLE process_types TO crm_process_types;
RENAME TABLE warehouses TO crm_warehouses;
RENAME TABLE customers TO crm_customers;

-- ============================================
-- 2. 添加客户分级相关字段
-- ============================================
ALTER TABLE crm_customers ADD COLUMN grade VARCHAR(10) DEFAULT NULL COMMENT '客户等级: S/A/B/C/regular';
ALTER TABLE crm_customers ADD COLUMN grade_score INT DEFAULT 0 COMMENT '客户评分';
ALTER TABLE crm_customers ADD COLUMN grade_updated_at DATETIME DEFAULT NULL COMMENT '等级更新时间';
ALTER TABLE crm_customers ADD COLUMN is_key_account TINYINT(1) DEFAULT 0 COMMENT '是否重点客户';
ALTER TABLE crm_customers ADD COLUMN owner_id INT DEFAULT NULL COMMENT '负责人ID';
ALTER TABLE crm_customers ADD COLUMN owner_name VARCHAR(100) DEFAULT NULL COMMENT '负责人姓名';
ALTER TABLE crm_customers ADD COLUMN department_id INT DEFAULT NULL COMMENT '所属部门ID';
ALTER TABLE crm_customers ADD COLUMN department_name VARCHAR(100) DEFAULT NULL COMMENT '所属部门名称';
ALTER TABLE crm_customers ADD COLUMN created_by VARCHAR(100) DEFAULT NULL COMMENT '创建人';

-- ============================================
-- 验证
-- ============================================
-- SHOW TABLES;
-- DESCRIBE crm_customers;
