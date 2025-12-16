-- Dashboard 可视化追踪系统 - 数据库表创建脚本
-- 数据库: cncplan
-- 创建日期: 2024-12-13

USE cncplan;

-- 1. 生产计划表
CREATE TABLE IF NOT EXISTS dashboard_production_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- 关联信息
    order_id INT NOT NULL COMMENT '关联订单ID',
    order_no VARCHAR(50) COMMENT '订单号',
    customer_id INT COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',

    -- 计划信息
    plan_no VARCHAR(50) UNIQUE NOT NULL COMMENT '计划编号',
    product_code VARCHAR(100) COMMENT '产品代码',
    product_name VARCHAR(200) COMMENT '产品名称',

    -- 时间规划
    plan_start_date DATE NOT NULL COMMENT '计划开始日期',
    plan_end_date DATE NOT NULL COMMENT '计划结束日期',
    actual_start_date DATE COMMENT '实际开始日期',
    actual_end_date DATE COMMENT '实际结束日期',

    -- 数量
    plan_quantity INT NOT NULL DEFAULT 0 COMMENT '计划数量',
    completed_quantity INT DEFAULT 0 COMMENT '完成数量',
    defect_quantity INT DEFAULT 0 COMMENT '不良数量',

    -- 状态和优先级
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/in_progress/completed/delayed/cancelled',
    priority INT DEFAULT 3 COMMENT '优先级: 1-5, 1最高',

    -- 负责人
    department VARCHAR(64) COMMENT '部门',
    responsible_person VARCHAR(100) COMMENT '负责人',
    responsible_user_id INT COMMENT '负责人用户ID',

    -- 备注
    remark TEXT COMMENT '备注',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,

    -- 索引
    INDEX idx_order_id (order_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_status (status),
    INDEX idx_plan_dates (plan_start_date, plan_end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产计划表';


-- 2. 生产工序步骤表
CREATE TABLE IF NOT EXISTS dashboard_production_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plan_id INT NOT NULL COMMENT '关联生产计划ID',

    -- 工序信息
    step_name VARCHAR(100) NOT NULL COMMENT '工序名称',
    step_code VARCHAR(50) COMMENT '工序代码',
    step_sequence INT NOT NULL DEFAULT 1 COMMENT '工序顺序',

    -- 时间
    plan_start DATETIME NOT NULL COMMENT '计划开始时间',
    plan_end DATETIME NOT NULL COMMENT '计划结束时间',
    actual_start DATETIME COMMENT '实际开始时间',
    actual_end DATETIME COMMENT '实际结束时间',

    -- 设备和人员
    machine_id INT COMMENT '设备ID',
    machine_name VARCHAR(100) COMMENT '设备名称',
    operator_id INT COMMENT '操作员ID',
    operator_name VARCHAR(100) COMMENT '操作员姓名',

    -- 数量
    plan_quantity INT DEFAULT 0 COMMENT '计划数量',
    completed_quantity INT DEFAULT 0 COMMENT '完成数量',

    -- 状态
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态',
    completion_rate DECIMAL(5,2) DEFAULT 0 COMMENT '完成率 0-100',

    -- 质量
    defect_count INT DEFAULT 0 COMMENT '不良数量',
    defect_rate DECIMAL(5,2) DEFAULT 0 COMMENT '不良率',

    -- 依赖关系
    depends_on_step_id INT COMMENT '依赖的工序ID',

    -- 备注
    remark TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,

    -- 外键和索引
    FOREIGN KEY (plan_id) REFERENCES dashboard_production_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_step_id) REFERENCES dashboard_production_steps(id) ON DELETE SET NULL,
    INDEX idx_plan_id (plan_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生产工序步骤表';


-- 3. 待办事项表
CREATE TABLE IF NOT EXISTS dashboard_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- 关联
    order_id INT COMMENT '订单ID',
    order_no VARCHAR(50) COMMENT '订单号',
    plan_id INT COMMENT '生产计划ID',
    step_id INT COMMENT '工序ID',

    -- 任务信息
    task_no VARCHAR(50) UNIQUE COMMENT '任务编号',
    title VARCHAR(200) NOT NULL COMMENT '任务标题',
    description TEXT COMMENT '任务描述',
    task_type VARCHAR(50) COMMENT '任务类型: quote_review/production_start/quality_check/shipment/procurement',

    -- 时间
    due_date DATETIME NOT NULL COMMENT '截止日期',
    remind_before_hours INT DEFAULT 24 COMMENT '提前提醒小时数',
    reminded_at DATETIME COMMENT '提醒时间',

    -- 负责人
    assigned_to_user_id INT COMMENT '负责人用户ID',
    assigned_to_name VARCHAR(100) COMMENT '负责人姓名',
    assigned_to_dept VARCHAR(64) COMMENT '负责部门',

    -- 创建者
    created_by_user_id INT COMMENT '创建者用户ID',
    created_by_name VARCHAR(100) COMMENT '创建者姓名',

    -- 状态和优先级
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/in_progress/completed/cancelled',
    priority VARCHAR(20) DEFAULT 'normal' COMMENT '优先级: low/normal/high/urgent',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,

    -- 外键和索引
    FOREIGN KEY (plan_id) REFERENCES dashboard_production_plans(id) ON DELETE SET NULL,
    FOREIGN KEY (step_id) REFERENCES dashboard_production_steps(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_due_date (due_date),
    INDEX idx_assigned_to (assigned_to_user_id),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='待办事项表';


-- 4. 客户访问令牌表
CREATE TABLE IF NOT EXISTS dashboard_customer_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- 客户信息
    customer_id INT NOT NULL COMMENT '客户ID',
    customer_code VARCHAR(64) COMMENT '客户编码',
    customer_name VARCHAR(200) COMMENT '客户名称',
    contact_name VARCHAR(100) COMMENT '联系人姓名',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    contact_email VARCHAR(100) COMMENT '联系邮箱',

    -- 令牌
    token VARCHAR(255) UNIQUE NOT NULL COMMENT '访问令牌',

    -- 权限范围
    order_ids JSON COMMENT '可访问的订单ID列表',
    permissions JSON COMMENT '权限配置',

    -- 有效期
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL COMMENT '过期时间',
    last_accessed_at DATETIME COMMENT '最后访问时间',

    -- 状态
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否有效',
    revoked_at DATETIME COMMENT '撤销时间',
    revoked_reason VARCHAR(200) COMMENT '撤销原因',

    -- 创建者
    created_by_user_id INT COMMENT '创建者用户ID',
    created_by_name VARCHAR(100) COMMENT '创建者姓名',

    -- 索引
    INDEX idx_customer_id (customer_id),
    INDEX idx_token (token),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客户访问令牌表';


-- 插入示例数据（可选）
-- 在生产环境中请注释掉这部分

-- 示例生产计划
INSERT INTO dashboard_production_plans (plan_no, order_id, order_no, customer_id, customer_name, product_code, product_name, plan_start_date, plan_end_date, plan_quantity, completed_quantity, status, priority, department, responsible_person) VALUES
('PP-20241201-001', 1, 'ORD-2024-001', 1, '深圳精密科技有限公司', 'PART-A001', 'CNC精密轴套', DATE_SUB(CURDATE(), INTERVAL 10 DAY), DATE_ADD(CURDATE(), INTERVAL 5 DAY), 5000, 3500, 'in_progress', 2, '生产部', '张工'),
('PP-20241202-001', 2, 'ORD-2024-002', 2, '东莞机械制造厂', 'PART-B002', '精密齿轮', DATE_SUB(CURDATE(), INTERVAL 5 DAY), DATE_ADD(CURDATE(), INTERVAL 10 DAY), 2000, 800, 'in_progress', 3, '生产部', '李工'),
('PP-20241203-001', 3, 'ORD-2024-003', 1, '深圳精密科技有限公司', 'PART-C003', '连接器外壳', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 15 DAY), 10000, 0, 'pending', 3, '生产部', '王工');

-- 示例工序
INSERT INTO dashboard_production_steps (plan_id, step_name, step_sequence, plan_start, plan_end, status, completion_rate) VALUES
(1, 'CNC车削', 1, DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 8 DAY), 'completed', 100),
(1, '铣扁', 2, DATE_SUB(NOW(), INTERVAL 8 DAY), DATE_SUB(NOW(), INTERVAL 7 DAY), 'completed', 100),
(1, '电镀', 3, DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), 'in_progress', 70),
(1, '质检', 4, DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_SUB(NOW(), INTERVAL 4 DAY), 'pending', 0),
(1, '包装', 5, DATE_SUB(NOW(), INTERVAL 4 DAY), DATE_ADD(NOW(), INTERVAL 5 DAY), 'pending', 0);

-- 示例任务
INSERT INTO dashboard_tasks (task_no, title, task_type, order_no, due_date, assigned_to_name, assigned_to_dept, priority) VALUES
('TASK-20241213-001', '检查订单ORD-2024-001的CNC车削工序', 'quality_check', 'ORD-2024-001', DATE_ADD(NOW(), INTERVAL 4 HOUR), '质检员小李', '质检部', 'high'),
('TASK-20241213-002', '确认订单ORD-2024-003的原材料到货', 'procurement', 'ORD-2024-003', DATE_ADD(NOW(), INTERVAL 1 DAY), '采购员小王', '采购部', 'normal'),
('TASK-20241213-003', '安排订单ORD-2024-002的电镀外协', 'production_start', 'ORD-2024-002', DATE_ADD(NOW(), INTERVAL 3 DAY), '计划员小张', '生产部', 'normal');

SELECT 'Dashboard tables created successfully!' AS Result;
