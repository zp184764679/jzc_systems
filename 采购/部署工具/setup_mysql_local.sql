-- =====================================================
-- MySQL本地数据库初始化脚本
-- 用于Windows本机部署 + Ubuntu远程访问
-- =====================================================

-- 1. 创建数据库
DROP DATABASE IF EXISTS caigou_local;
CREATE DATABASE caigou_local
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE caigou_local;

-- 2. 创建本地用户（localhost访问）
DROP USER IF EXISTS 'exzzz'@'localhost';
CREATE USER 'exzzz'@'localhost' IDENTIFIED BY 'exak472008';
GRANT ALL PRIVILEGES ON caigou_local.* TO 'exzzz'@'localhost';

-- 3. 创建局域网用户（192.168.0.%）
DROP USER IF EXISTS 'exzzz'@'192.168.0.%';
CREATE USER 'exzzz'@'192.168.0.%' IDENTIFIED BY 'exak472008';
GRANT ALL PRIVILEGES ON caigou_local.* TO 'exzzz'@'192.168.0.%';

-- 4. 创建WSL2用户（172.%）
DROP USER IF EXISTS 'exzzz'@'172.%';
CREATE USER 'exzzz'@'172.%' IDENTIFIED BY 'exak472008';
GRANT ALL PRIVILEGES ON caigou_local.* TO 'exzzz'@'172.%';

-- 5. 创建任意IP用户（用于外网和Ubuntu访问）
DROP USER IF EXISTS 'exzzz'@'%';
CREATE USER 'exzzz'@'%' IDENTIFIED BY 'exak472008';
GRANT ALL PRIVILEGES ON caigou_local.* TO 'exzzz'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 查看创建的用户
SELECT User, Host FROM mysql.user WHERE User = 'exzzz';

-- 显示数据库
SHOW DATABASES;

SELECT '✅ MySQL数据库创建成功!' AS STATUS;
SELECT '📊 数据库名: caigou_local' AS INFO;
SELECT '👤 用户名: exzzz' AS INFO;
SELECT '🔑 密码: exak472008' AS INFO;
