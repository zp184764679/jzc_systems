-- 添加中国发票完整字段
-- 执行时间: 2025-11-03
-- 说明: 为invoices表添加中国发票的完整信息字段，包括发票代码、购买方/销售方信息、金额明细等

USE caigou;

-- 添加发票代码字段
ALTER TABLE invoices ADD COLUMN invoice_code VARCHAR(50) DEFAULT NULL COMMENT '发票代码（10-12位）' AFTER id;

-- 添加购买方信息字段
ALTER TABLE invoices ADD COLUMN buyer_name VARCHAR(255) DEFAULT NULL COMMENT '购买方名称' AFTER invoice_date;
ALTER TABLE invoices ADD COLUMN buyer_tax_id VARCHAR(50) DEFAULT NULL COMMENT '购买方纳税人识别号/统一社会信用代码' AFTER buyer_name;

-- 添加销售方信息字段
ALTER TABLE invoices ADD COLUMN seller_name VARCHAR(255) DEFAULT NULL COMMENT '销售方名称（供应商）' AFTER buyer_tax_id;
ALTER TABLE invoices ADD COLUMN seller_tax_id VARCHAR(50) DEFAULT NULL COMMENT '销售方纳税人识别号' AFTER seller_name;

-- 添加金额明细字段
ALTER TABLE invoices ADD COLUMN amount_before_tax DECIMAL(12,2) DEFAULT NULL COMMENT '金额合计（不含税）' AFTER seller_tax_id;
ALTER TABLE invoices ADD COLUMN total_amount DECIMAL(12,2) DEFAULT NULL COMMENT '价税合计' AFTER tax_amount;

-- 添加备注字段（中国发票格式）
ALTER TABLE invoices ADD COLUMN remark TEXT DEFAULT NULL COMMENT '备注说明（中国发票格式）' AFTER description;

-- 更新现有记录，将amount值复制到total_amount
UPDATE invoices SET total_amount = amount WHERE total_amount IS NULL;

-- 添加索引以优化查询
CREATE INDEX idx_invoices_invoice_code ON invoices(invoice_code);
CREATE INDEX idx_invoices_buyer_tax_id ON invoices(buyer_tax_id);
CREATE INDEX idx_invoices_seller_tax_id ON invoices(seller_tax_id);

-- 完成
SELECT 'Migration completed successfully!' AS status;
