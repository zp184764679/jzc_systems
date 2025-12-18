-- 完整数据库表创建脚本
-- Portal 项目管理系统 + 认证系统

-- ================================================
-- 1. cncplan 数据库 - 项目管理表
-- ================================================
CREATE DATABASE IF NOT EXISTS cncplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cncplan;

-- 1.1 项目表 (基础表，无外键依赖)
CREATE TABLE IF NOT EXISTS projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_no VARCHAR(50) NOT NULL UNIQUE COMMENT '项目编号',
    name VARCHAR(200) NOT NULL COMMENT '项目名称',
    description TEXT COMMENT '项目描述',
    customer VARCHAR(200) COMMENT '客户名称（兼容旧数据）',
    customer_id INT COMMENT 'CRM客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称（从CRM同步）',
    order_no VARCHAR(100) COMMENT '订单号',
    part_number VARCHAR(100) COMMENT '部件番号',
    planned_start_date DATE COMMENT '计划开始日期',
    planned_end_date DATE COMMENT '计划结束日期',
    actual_start_date DATE COMMENT '实际开始日期',
    actual_end_date DATE COMMENT '实际结束日期',
    status ENUM('planning', 'in_progress', 'on_hold', 'completed', 'cancelled') DEFAULT 'planning' NOT NULL COMMENT '项目状态',
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal' NOT NULL COMMENT '优先级',
    progress_percentage INT DEFAULT 0 COMMENT '进度百分比(0-100)',
    created_by_id INT NOT NULL COMMENT '创建者ID',
    manager_id INT COMMENT '项目经理ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    deleted_at DATETIME COMMENT '删除时间（软删除）',
    delete_reason VARCHAR(500) COMMENT '删除原因',
    deleted_by_id INT COMMENT '删除者ID',
    INDEX idx_project_no (project_no),
    INDEX idx_customer_id (customer_id),
    INDEX idx_order_no (order_no),
    INDEX idx_part_number (part_number),
    INDEX idx_status (status),
    INDEX idx_created_by_id (created_by_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表';

-- 1.2 项目阶段表
CREATE TABLE IF NOT EXISTS project_phases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL COMMENT '所属项目ID',
    phase_type ENUM('customer_order', 'quotation', 'procurement', 'production', 'qc', 'shipping', 'receipt') NOT NULL COMMENT '阶段类型',
    phase_order INT NOT NULL COMMENT '阶段顺序(1-7)',
    name VARCHAR(100) NOT NULL COMMENT '阶段名称',
    description TEXT COMMENT '阶段描述',
    planned_start_date DATE COMMENT '计划开始日期',
    planned_end_date DATE COMMENT '计划结束日期',
    actual_start_date DATE COMMENT '实际开始日期',
    actual_end_date DATE COMMENT '实际结束日期',
    status ENUM('pending', 'in_progress', 'completed', 'blocked') DEFAULT 'pending' NOT NULL COMMENT '阶段状态',
    completion_percentage INT DEFAULT 0 COMMENT '完成百分比(0-100)',
    responsible_user_id INT COMMENT '负责人ID',
    department VARCHAR(100) COMMENT '负责部门',
    depends_on_phase_id INT COMMENT '依赖的前置阶段ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_phase_type (phase_type),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_phase_id) REFERENCES project_phases(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目阶段表';

-- 1.3 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL COMMENT '所属项目ID',
    task_no VARCHAR(50) NOT NULL UNIQUE COMMENT '任务编号',
    title VARCHAR(200) NOT NULL COMMENT '任务标题',
    description TEXT COMMENT '任务描述',
    task_type ENUM('general', 'design', 'development', 'testing', 'review', 'deployment', 'documentation', 'meeting', 'other') DEFAULT 'general' NOT NULL COMMENT '任务类型',
    start_date DATE COMMENT '开始日期',
    due_date DATE COMMENT '截止日期',
    completed_at DATETIME COMMENT '完成时间',
    status ENUM('pending', 'in_progress', 'completed', 'cancelled', 'blocked') DEFAULT 'pending' NOT NULL COMMENT '任务状态',
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal' NOT NULL COMMENT '优先级',
    assigned_to_id INT COMMENT '分配给(用户ID)',
    created_by_id INT NOT NULL COMMENT '创建者ID',
    depends_on_task_id INT COMMENT '依赖的任务ID',
    reminder_enabled BOOLEAN DEFAULT FALSE COMMENT '是否启用提醒',
    reminder_days_before INT DEFAULT 1 COMMENT '提前提醒天数',
    is_milestone BOOLEAN DEFAULT FALSE COMMENT '是否为里程碑',
    phase_id INT COMMENT '所属阶段ID',
    weight INT DEFAULT 1 COMMENT '任务权重(1-10)',
    completion_percentage INT DEFAULT 0 COMMENT '完成百分比(0-100)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_task_no (task_no),
    INDEX idx_status (status),
    INDEX idx_assigned_to_id (assigned_to_id),
    INDEX idx_phase_id (phase_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (phase_id) REFERENCES project_phases(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务表';

-- 1.4 项目成员表
CREATE TABLE IF NOT EXISTS project_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL COMMENT '项目ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role VARCHAR(50) DEFAULT 'member' COMMENT '角色: owner/manager/member/viewer',
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_project_user (project_id, user_id),
    INDEX idx_project_id (project_id),
    INDEX idx_user_id (user_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目成员表';

-- 1.5 项目文件表
CREATE TABLE IF NOT EXISTS project_files (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL COMMENT '所属项目ID',
    task_id INT COMMENT '关联任务ID',
    filename VARCHAR(255) NOT NULL COMMENT '文件名',
    original_filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    file_size BIGINT COMMENT '文件大小(字节)',
    file_type VARCHAR(100) COMMENT '文件类型/MIME',
    category VARCHAR(50) DEFAULT 'general' COMMENT '文件分类',
    description TEXT COMMENT '文件描述',
    version INT DEFAULT 1 COMMENT '版本号',
    is_latest BOOLEAN DEFAULT TRUE COMMENT '是否最新版本',
    parent_file_id INT COMMENT '父文件ID(版本链)',
    uploaded_by_id INT NOT NULL COMMENT '上传者ID',
    download_count INT DEFAULT 0 COMMENT '下载次数',
    view_count INT DEFAULT 0 COMMENT '预览次数',
    last_accessed_at DATETIME COMMENT '最后访问时间',
    last_accessed_by INT COMMENT '最后访问者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    deleted_at DATETIME COMMENT '删除时间（软删除）',
    deleted_by_id INT COMMENT '删除者ID',
    INDEX idx_project_id (project_id),
    INDEX idx_task_id (task_id),
    INDEX idx_category (category),
    INDEX idx_uploaded_by_id (uploaded_by_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_file_id) REFERENCES project_files(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目文件表';

-- 1.6 文件访问日志表
CREATE TABLE IF NOT EXISTS file_access_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    file_id INT NOT NULL COMMENT '文件ID',
    user_id INT NOT NULL COMMENT '用户ID',
    action VARCHAR(50) NOT NULL COMMENT '操作类型: upload/download/view/update/delete/restore/share',
    ip_address VARCHAR(50) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    details JSON COMMENT '操作详情',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_file_id (file_id),
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (file_id) REFERENCES project_files(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件访问日志表';

-- 1.7 文件分享链接表
CREATE TABLE IF NOT EXISTS file_share_links (
    id INT PRIMARY KEY AUTO_INCREMENT,
    file_id INT NOT NULL COMMENT '文件ID',
    share_code VARCHAR(50) NOT NULL UNIQUE COMMENT '分享码',
    created_by_id INT NOT NULL COMMENT '创建者ID',
    password_hash VARCHAR(255) COMMENT '密码哈希(可选)',
    expires_at DATETIME COMMENT '过期时间',
    max_downloads INT COMMENT '最大下载次数',
    download_count INT DEFAULT 0 COMMENT '已下载次数',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_share_code (share_code),
    INDEX idx_file_id (file_id),
    FOREIGN KEY (file_id) REFERENCES project_files(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件分享链接表';

-- 1.8 项目问题表
CREATE TABLE IF NOT EXISTS project_issues (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL COMMENT '所属项目ID',
    task_id INT COMMENT '关联任务ID',
    issue_no VARCHAR(50) NOT NULL UNIQUE COMMENT '问题编号',
    title VARCHAR(200) NOT NULL COMMENT '问题标题',
    description TEXT COMMENT '问题描述',
    issue_type ENUM('bug', 'feature', 'improvement', 'question', 'risk', 'other') DEFAULT 'bug' COMMENT '问题类型',
    severity ENUM('critical', 'major', 'minor', 'trivial') DEFAULT 'minor' COMMENT '严重程度',
    status ENUM('open', 'in_progress', 'resolved', 'closed', 'wont_fix') DEFAULT 'open' COMMENT '问题状态',
    priority ENUM('low', 'normal', 'high', 'urgent') DEFAULT 'normal' COMMENT '优先级',
    reported_by_id INT NOT NULL COMMENT '报告人ID',
    assigned_to_id INT COMMENT '分配给(用户ID)',
    resolved_at DATETIME COMMENT '解决时间',
    resolution TEXT COMMENT '解决方案',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_issue_no (issue_no),
    INDEX idx_status (status),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目问题表';

-- 1.9 项目通知表
CREATE TABLE IF NOT EXISTS project_notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '接收用户ID',
    project_id INT COMMENT '关联项目ID',
    task_id INT COMMENT '关联任务ID',
    notification_type VARCHAR(50) NOT NULL COMMENT '通知类型',
    title VARCHAR(200) NOT NULL COMMENT '通知标题',
    content TEXT COMMENT '通知内容',
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    read_at DATETIME COMMENT '阅读时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_project_id (project_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目通知表';

-- 1.10 项目聊天消息表
CREATE TABLE IF NOT EXISTS project_messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL COMMENT '所属项目ID',
    task_id INT DEFAULT NULL COMMENT '关联任务ID (NULL=项目聊天, 非NULL=任务评论)',
    sender_id INT NOT NULL COMMENT '发送者用户ID',
    sender_name VARCHAR(100) NOT NULL COMMENT '发送者姓名',
    content TEXT NOT NULL COMMENT '消息内容',
    message_type ENUM('text', 'system') DEFAULT 'text' COMMENT '消息类型',
    mentions JSON DEFAULT NULL COMMENT '@提醒的用户ID列表',
    is_edited BOOLEAN DEFAULT FALSE COMMENT '是否已编辑',
    is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否已删除(软删除)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_project_id (project_id),
    INDEX idx_task_id (task_id),
    INDEX idx_sender_id (sender_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目聊天消息表';

-- 1.11 消息已读状态表
CREATE TABLE IF NOT EXISTS message_read_status (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '用户ID',
    project_id INT NOT NULL COMMENT '项目ID',
    last_read_message_id INT DEFAULT NULL COMMENT '最后已读消息ID',
    last_read_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后已读时间',
    UNIQUE KEY unique_user_project (user_id, project_id),
    INDEX idx_user_id (user_id),
    INDEX idx_project_id (project_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息已读状态表';

-- ================================================
-- 2. account 数据库 - 补充缺失的表
-- ================================================
USE account;

-- 2.1 数据权限规则表 (RBAC)
CREATE TABLE IF NOT EXISTS data_permission_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL COMMENT '角色ID',
    resource_type VARCHAR(50) NOT NULL COMMENT '资源类型',
    field_name VARCHAR(50) NOT NULL COMMENT '字段名',
    operator VARCHAR(20) NOT NULL COMMENT '操作符: eq/ne/in/not_in/contains/range',
    value TEXT NOT NULL COMMENT '值(JSON格式)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_role_id (role_id),
    INDEX idx_resource_type (resource_type),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据权限规则表';

-- 2.2 用户角色关联表 (如果不存在)
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT NOT NULL COMMENT '用户ID',
    role_id INT NOT NULL COMMENT '角色ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT COMMENT '创建者ID',
    expires_at DATETIME COMMENT '过期时间',
    PRIMARY KEY (user_id, role_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- ================================================
-- 验证
-- ================================================
SELECT 'cncplan 数据库表:' AS info;
USE cncplan;
SHOW TABLES;

SELECT 'account 数据库表:' AS info;
USE account;
SHOW TABLES;

SELECT '所有表创建完成!' AS status;
