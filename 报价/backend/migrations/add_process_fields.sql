-- 添加工艺库新字段
-- 执行时间: 2025-11-14

-- 添加 daily_fee 字段（工事费/日）
ALTER TABLE processes ADD COLUMN IF NOT EXISTS daily_fee DECIMAL(10, 2) DEFAULT 0 COMMENT '工事费/日 元/天';

-- 添加 icon 字段（图标emoji）
ALTER TABLE processes ADD COLUMN IF NOT EXISTS icon VARCHAR(10) COMMENT '图标emoji';

-- 更新 setup_time 注释（单位改为天）
ALTER TABLE processes MODIFY COLUMN setup_time DECIMAL(10, 4) DEFAULT 0 COMMENT '段取时间 天';

-- 更新 daily_output 注释和默认值
ALTER TABLE processes MODIFY COLUMN daily_output INT DEFAULT 1000 COMMENT '日产量（件/天）';

-- 更新 defect_rate 注释
ALTER TABLE processes MODIFY COLUMN defect_rate DECIMAL(5, 4) DEFAULT 0 COMMENT '不良率 %';
