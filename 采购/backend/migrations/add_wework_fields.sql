-- 企业微信集成 - 数据库迁移
-- 添加企业微信相关字段

-- 1. 为users表添加企业微信UserID字段
ALTER TABLE users
ADD COLUMN IF NOT EXISTS wework_user_id VARCHAR(100) UNIQUE COMMENT '企业微信UserID';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_wework_user_id ON users(wework_user_id);

-- 2. 为notifications表添加企业微信发送状态字段（可选）
ALTER TABLE notifications
ADD COLUMN IF NOT EXISTS wework_msg_id VARCHAR(100) COMMENT '企业微信消息ID',
ADD COLUMN IF NOT EXISTS wework_sent_at DATETIME COMMENT '企业微信发送时间',
ADD COLUMN IF NOT EXISTS wework_status VARCHAR(20) DEFAULT 'pending' COMMENT '企业微信发送状态: pending/sent/failed';

-- 3. 测试数据：为示例用户配置企业微信UserID（根据实际情况修改）
-- UPDATE users SET wework_user_id = 'ZhangSan' WHERE username = 'admin';
-- UPDATE users SET wework_user_id = 'LiSi' WHERE username = 'user1';

-- 查看结果
SELECT id, username, wework_user_id, role, status
FROM users
ORDER BY id;

-- 提示信息
SELECT '✅ 数据库迁移完成！' AS message;
SELECT '💡 请使用以下SQL为用户配置企业微信UserID：' AS tip;
SELECT 'UPDATE users SET wework_user_id = ''你的企业微信UserID'' WHERE username = ''用户名'';' AS example;
