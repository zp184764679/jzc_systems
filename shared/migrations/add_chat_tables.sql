-- 项目聊天功能数据库迁移
-- 创建聊天消息表和已读状态表
-- 执行命令: mysql -u app -papp cncplan < add_chat_tables.sql

USE cncplan;

-- 聊天消息表
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
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目聊天消息表';

-- 消息已读状态表
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

-- 验证表创建
SELECT '聊天功能表创建完成!' AS status;
SHOW TABLES LIKE '%message%';
