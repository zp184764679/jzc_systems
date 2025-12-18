-- 添加文件分享链接表
-- Migration: add_file_share_links
-- Date: 2025-12-18
-- Description: 为 project_files 表创建分享链接功能

-- 1. 创建文件分享链接表
CREATE TABLE IF NOT EXISTS file_share_links (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',

    -- 关联文件
    file_id INT NOT NULL COMMENT '关联的文件ID',

    -- 分享码
    share_code VARCHAR(64) NOT NULL COMMENT '分享码',

    -- 安全设置
    share_password_hash VARCHAR(64) NULL COMMENT '分享密码哈希 (SHA256)',
    has_password TINYINT(1) DEFAULT 0 COMMENT '是否有密码保护',

    -- 权限设置
    allow_download TINYINT(1) DEFAULT 1 COMMENT '允许下载',
    allow_preview TINYINT(1) DEFAULT 1 COMMENT '允许预览',

    -- 有效期
    expire_at DATETIME NULL COMMENT '过期时间 (NULL=永不过期)',

    -- 下载限制
    max_downloads INT NULL COMMENT '最大下载次数 (NULL=无限制)',
    download_count INT DEFAULT 0 COMMENT '已下载次数',
    view_count INT DEFAULT 0 COMMENT '已查看次数',

    -- 创建者
    created_by_id INT NOT NULL COMMENT '创建者用户ID',
    created_by_name VARCHAR(100) NULL COMMENT '创建者用户名',

    -- 状态
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否有效',
    deactivated_at DATETIME NULL COMMENT '停用时间',
    deactivate_reason VARCHAR(255) NULL COMMENT '停用原因',

    -- 备注
    remark TEXT NULL COMMENT '分享备注',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_accessed_at DATETIME NULL COMMENT '最后访问时间',

    -- 唯一约束
    UNIQUE KEY uk_share_code (share_code),

    -- 索引
    INDEX idx_file_id (file_id),
    INDEX idx_expire_at (expire_at),
    INDEX idx_is_active (is_active),
    INDEX idx_created_by (created_by_id),

    -- 外键约束
    CONSTRAINT fk_share_file FOREIGN KEY (file_id) REFERENCES project_files(id) ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件分享链接表';

-- 2. 创建分享访问日志表（可选，用于追踪分享链接访问）
CREATE TABLE IF NOT EXISTS file_share_access_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    share_id INT NOT NULL COMMENT '分享链接ID',
    share_code VARCHAR(64) NOT NULL COMMENT '分享码',
    access_type ENUM('view', 'download', 'password_attempt') NOT NULL COMMENT '访问类型',
    is_success TINYINT(1) DEFAULT 1 COMMENT '是否成功',
    ip_address VARCHAR(45) NULL COMMENT 'IP地址',
    user_agent VARCHAR(500) NULL COMMENT '用户代理',
    referer VARCHAR(500) NULL COMMENT '来源页面',
    access_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '访问时间',

    INDEX idx_share_id (share_id),
    INDEX idx_share_code (share_code),
    INDEX idx_access_time (access_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分享链接访问日志表';

-- 完成
SELECT '文件分享链接表创建完成!' as message;
