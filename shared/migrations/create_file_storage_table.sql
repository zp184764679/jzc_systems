-- ============================================================
-- 企业级文件存储表结构
-- 创建时间: 2025-12-18
-- 适用数据库: MySQL 8.0+
-- ============================================================

-- 删除旧表（如果存在）
-- DROP TABLE IF EXISTS file_storage_tags;
-- DROP TABLE IF EXISTS file_storage;

-- ============================================================
-- 1. 主文件存储表
-- ============================================================
CREATE TABLE IF NOT EXISTS file_storage (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',

    -- 唯一标识
    file_id VARCHAR(32) NOT NULL COMMENT '唯一文件ID (8位UUID)',

    -- 基本信息
    original_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    stored_name VARCHAR(255) NOT NULL COMMENT '存储文件名',
    storage_path VARCHAR(500) NOT NULL COMMENT '相对存储路径',
    file_url VARCHAR(500) NOT NULL COMMENT '访问URL',

    -- 分类信息
    system_code VARCHAR(32) NOT NULL COMMENT '系统代码: portal/caigou/quotation/hr/crm/scm/shm/eam/mes/account',
    entity_type VARCHAR(64) NOT NULL COMMENT '实体类型: projects/suppliers/quotes/employees',
    entity_id VARCHAR(64) NOT NULL COMMENT '实体ID: PRJ-2025-0001',
    category VARCHAR(64) NOT NULL DEFAULT 'documents' COMMENT '文件分类: documents/drawings/contracts/invoices/photos/certificates/reports/exports/attachments',

    -- 文件属性
    file_size BIGINT NOT NULL DEFAULT 0 COMMENT '文件大小(字节)',
    mime_type VARCHAR(128) COMMENT 'MIME类型',
    file_extension VARCHAR(16) COMMENT '文件扩展名',
    md5_hash VARCHAR(32) COMMENT 'MD5校验值',
    sha256_hash VARCHAR(64) COMMENT 'SHA256校验值',

    -- 版本控制
    version VARCHAR(16) DEFAULT '1.0' COMMENT '版本号',
    parent_version_id BIGINT COMMENT '父版本ID (外键指向自身)',
    is_latest_version TINYINT(1) DEFAULT 1 COMMENT '是否最新版本: 0=否, 1=是',
    version_note TEXT COMMENT '版本说明',

    -- 多语言支持
    language VARCHAR(8) COMMENT '文件语言: zh/en/ja',
    translation_of_id BIGINT COMMENT '翻译自哪个文件ID',

    -- 访问控制
    access_level ENUM('public', 'internal', 'confidential', 'secret') DEFAULT 'internal' COMMENT '访问级别',
    owner_id INT COMMENT '文件所有者用户ID',
    department_id INT COMMENT '所属部门ID',

    -- 状态管理
    status ENUM('active', 'archived', 'deleted', 'quarantine') DEFAULT 'active' COMMENT '文件状态',
    archived_at DATETIME COMMENT '归档时间',
    deleted_at DATETIME COMMENT '删除时间',
    delete_reason VARCHAR(255) COMMENT '删除原因',

    -- 审计信息
    created_by INT COMMENT '创建者用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_by INT COMMENT '更新者用户ID',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 统计信息
    download_count INT DEFAULT 0 COMMENT '下载次数',
    view_count INT DEFAULT 0 COMMENT '查看次数',
    last_accessed_at DATETIME COMMENT '最后访问时间',
    last_accessed_by INT COMMENT '最后访问者用户ID',

    -- 扩展信息
    description TEXT COMMENT '文件描述',
    metadata JSON COMMENT '扩展元数据 (JSON)',

    -- 唯一约束
    UNIQUE KEY uk_file_id (file_id),

    -- 索引
    INDEX idx_system_entity (system_code, entity_type, entity_id),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_md5 (md5_hash),
    INDEX idx_owner (owner_id),
    INDEX idx_department (department_id),
    INDEX idx_version (parent_version_id, version),
    INDEX idx_translation (translation_of_id)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业级文件存储表';

-- ============================================================
-- 2. 文件标签关联表
-- ============================================================
CREATE TABLE IF NOT EXISTS file_storage_tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    file_id VARCHAR(32) NOT NULL COMMENT '文件ID',
    tag_name VARCHAR(64) NOT NULL COMMENT '标签名称',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_file_tag (file_id, tag_name),
    INDEX idx_tag_name (tag_name),

    FOREIGN KEY (file_id) REFERENCES file_storage(file_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件标签关联表';

-- ============================================================
-- 3. 文件访问日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS file_access_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    file_id VARCHAR(32) NOT NULL COMMENT '文件ID',
    user_id INT COMMENT '用户ID',
    action_type ENUM('view', 'download', 'upload', 'update', 'delete', 'archive', 'restore') NOT NULL COMMENT '操作类型',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent VARCHAR(500) COMMENT '用户代理',
    action_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    details JSON COMMENT '详细信息',

    INDEX idx_file_id (file_id),
    INDEX idx_user_id (user_id),
    INDEX idx_action_time (action_time),
    INDEX idx_action_type (action_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件访问日志表';

-- ============================================================
-- 4. 文件共享链接表
-- ============================================================
CREATE TABLE IF NOT EXISTS file_share_links (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    file_id VARCHAR(32) NOT NULL COMMENT '文件ID',
    share_code VARCHAR(64) NOT NULL COMMENT '分享码',
    share_password VARCHAR(32) COMMENT '分享密码 (可选)',

    -- 权限设置
    allow_download TINYINT(1) DEFAULT 1 COMMENT '允许下载',
    allow_preview TINYINT(1) DEFAULT 1 COMMENT '允许预览',

    -- 有效期
    expire_at DATETIME COMMENT '过期时间 (NULL=永不过期)',
    max_downloads INT COMMENT '最大下载次数 (NULL=无限制)',
    download_count INT DEFAULT 0 COMMENT '已下载次数',

    -- 审计
    created_by INT NOT NULL COMMENT '创建者用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    last_accessed_at DATETIME COMMENT '最后访问时间',

    -- 状态
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否有效',

    UNIQUE KEY uk_share_code (share_code),
    INDEX idx_file_id (file_id),
    INDEX idx_expire_at (expire_at),

    FOREIGN KEY (file_id) REFERENCES file_storage(file_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件共享链接表';

-- ============================================================
-- 5. 存储配额表 (按部门/用户)
-- ============================================================
CREATE TABLE IF NOT EXISTS storage_quota (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',

    -- 配额对象
    quota_type ENUM('user', 'department', 'system') NOT NULL COMMENT '配额类型',
    target_id INT NOT NULL COMMENT '目标ID (用户ID/部门ID)',
    system_code VARCHAR(32) COMMENT '系统代码 (可选，用于系统级配额)',

    -- 配额设置
    max_storage_bytes BIGINT NOT NULL DEFAULT 10737418240 COMMENT '最大存储空间 (默认10GB)',
    max_file_count INT DEFAULT 10000 COMMENT '最大文件数量',
    max_single_file_bytes BIGINT DEFAULT 104857600 COMMENT '单文件最大大小 (默认100MB)',

    -- 当前使用
    used_storage_bytes BIGINT DEFAULT 0 COMMENT '已用存储空间',
    used_file_count INT DEFAULT 0 COMMENT '已用文件数量',

    -- 审计
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_quota_target (quota_type, target_id, system_code),
    INDEX idx_target (quota_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储配额表';

-- ============================================================
-- 6. 插入默认系统配额
-- ============================================================
INSERT INTO storage_quota (quota_type, target_id, system_code, max_storage_bytes, max_file_count, max_single_file_bytes)
VALUES
    ('system', 0, 'portal', 107374182400, 100000, 104857600),      -- Portal: 100GB
    ('system', 0, 'caigou', 107374182400, 100000, 104857600),      -- 采购: 100GB
    ('system', 0, 'quotation', 53687091200, 50000, 52428800),      -- 报价: 50GB
    ('system', 0, 'hr', 21474836480, 20000, 52428800),             -- HR: 20GB
    ('system', 0, 'crm', 21474836480, 20000, 52428800),            -- CRM: 20GB
    ('system', 0, 'scm', 53687091200, 50000, 104857600),           -- SCM: 50GB
    ('system', 0, 'shm', 53687091200, 50000, 104857600),           -- SHM: 50GB
    ('system', 0, 'eam', 21474836480, 20000, 52428800),            -- EAM: 20GB
    ('system', 0, 'mes', 21474836480, 20000, 52428800),            -- MES: 20GB
    ('system', 0, 'account', 5368709120, 5000, 10485760)           -- Account: 5GB
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- ============================================================
-- 7. 创建视图：文件统计
-- ============================================================
CREATE OR REPLACE VIEW v_file_storage_stats AS
SELECT
    system_code,
    entity_type,
    status,
    COUNT(*) as file_count,
    SUM(file_size) as total_size,
    AVG(file_size) as avg_size,
    MAX(file_size) as max_size,
    MIN(created_at) as first_upload,
    MAX(created_at) as last_upload
FROM file_storage
GROUP BY system_code, entity_type, status;

-- ============================================================
-- 8. 创建视图：按月统计
-- ============================================================
CREATE OR REPLACE VIEW v_file_storage_monthly AS
SELECT
    system_code,
    DATE_FORMAT(created_at, '%Y-%m') as month,
    COUNT(*) as file_count,
    SUM(file_size) as total_size,
    COUNT(DISTINCT entity_id) as entity_count,
    COUNT(DISTINCT created_by) as uploader_count
FROM file_storage
WHERE status = 'active'
GROUP BY system_code, DATE_FORMAT(created_at, '%Y-%m')
ORDER BY month DESC;

-- ============================================================
-- 完成
-- ============================================================
SELECT '文件存储表结构创建完成!' as message;
