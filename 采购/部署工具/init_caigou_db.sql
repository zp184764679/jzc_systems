-- =====================================================
-- 采购系统数据库初始化脚本
-- 数据库: caigou
-- 用户: exzzz / exak472008
-- =====================================================

-- 1. 创建数据库
DROP DATABASE IF EXISTS caigou;
CREATE DATABASE caigou
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE caigou;

-- 2. 创建用户并授权
-- 删除旧用户
DROP USER IF EXISTS 'exzzz'@'localhost';
DROP USER IF EXISTS 'exzzz'@'%';
DROP USER IF EXISTS 'exzzz'@'192.168.0.%';
DROP USER IF EXISTS 'exzzz'@'172.%';

-- 创建新用户
CREATE USER 'exzzz'@'localhost' IDENTIFIED BY 'exak472008';
CREATE USER 'exzzz'@'%' IDENTIFIED BY 'exak472008';
CREATE USER 'exzzz'@'192.168.0.%' IDENTIFIED BY 'exak472008';
CREATE USER 'exzzz'@'172.%' IDENTIFIED BY 'exak472008';

-- 授权
GRANT ALL PRIVILEGES ON caigou.* TO 'exzzz'@'localhost';
GRANT ALL PRIVILEGES ON caigou.* TO 'exzzz'@'%';
GRANT ALL PRIVILEGES ON caigou.* TO 'exzzz'@'192.168.0.%';
GRANT ALL PRIVILEGES ON caigou.* TO 'exzzz'@'172.%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证用户
SELECT '✅ 数据库创建成功: caigou' AS STATUS;
SELECT User, Host FROM mysql.user WHERE User = 'exzzz';
