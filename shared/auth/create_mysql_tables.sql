-- Create users table for shared authentication
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    emp_no VARCHAR(50),
    user_type VARCHAR(20) NOT NULL DEFAULT 'employee',
    role VARCHAR(20) DEFAULT 'user',
    permissions TEXT,
    supplier_id INT NULL,
    department_id INT NULL,
    department_name VARCHAR(100) NULL,
    position_id INT NULL,
    position_name VARCHAR(100) NULL,
    team_id INT NULL,
    team_name VARCHAR(100) NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_emp_no (emp_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ⚠️  安全警告：以下语句仅供开发环境初始化使用
-- ⚠️  生产环境请勿使用已知密码，应通过 Python 脚本生成随机密码
-- ⚠️  此 SQL 文件已弃用，请使用 shared/auth/models.py 中的 init_auth_db() 函数初始化
--
-- 如确需手动创建管理员，请使用以下命令生成安全的密码哈希：
-- python -c "from shared.auth.password_utils import hash_password; import secrets; p=secrets.token_urlsafe(16); print(f'Password: {p}'); print(f'Hash: {hash_password(p)}')"

-- [DEPRECATED] Create default admin user - DO NOT USE IN PRODUCTION
-- INSERT INTO users (username, email, hashed_password, full_name, role, permissions, is_active, is_admin)
-- SELECT 'admin', 'admin@jzchardware.cn', '<generated_hash>', '系统管理员', 'super_admin', '["hr", "quotation", "采购", "account"]', TRUE, TRUE
-- WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');
