-- 微信服务号集成：为suppliers表添加OpenID和订阅状态字段
-- 执行方式：mysql -h 61.145.212.28 -u zhoupeng -pexak472008 caigou < add_wechat_fields_to_suppliers.sql

USE caigou;

-- 添加微信服务号OpenID字段（用于发送模板消息）
ALTER TABLE suppliers
ADD COLUMN wechat_openid VARCHAR(100) DEFAULT NULL COMMENT '微信服务号OpenID',
ADD UNIQUE KEY uk_wechat_openid (wechat_openid);

-- 添加订阅状态字段（是否关注公众号）
ALTER TABLE suppliers
ADD COLUMN is_subscribed TINYINT(1) DEFAULT 0 COMMENT '是否关注公众号';

-- 添加索引以提高查询性能
CREATE INDEX idx_suppliers_subscribed ON suppliers(is_subscribed);

-- 验证字段已添加
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'caigou'
AND TABLE_NAME = 'suppliers'
AND COLUMN_NAME IN ('wechat_openid', 'is_subscribed');

-- 显示当前suppliers表结构
DESCRIBE suppliers;
