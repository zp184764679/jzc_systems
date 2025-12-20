-- TDM 产品技术标准管理系统 - 数据库表创建脚本
-- 数据库: cncplan

USE cncplan;

-- 1. 产品主数据表
CREATE TABLE IF NOT EXISTS tdm_product_master (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    part_number VARCHAR(100) NOT NULL UNIQUE COMMENT '品番号',
    product_name VARCHAR(200) NOT NULL COMMENT '产品名称',
    product_name_en VARCHAR(200) COMMENT '英文名称',
    product_name_ja VARCHAR(200) COMMENT '日文名称',

    -- 客户信息
    customer_id INT COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    customer_part_number VARCHAR(100) COMMENT '客户料号',

    -- 分类
    category VARCHAR(50) COMMENT '产品分类',
    sub_category VARCHAR(50) COMMENT '子分类',

    -- 状态
    status ENUM('draft', 'active', 'discontinued', 'obsolete') DEFAULT 'draft' COMMENT '状态',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',

    -- 关联报价系统
    quotation_product_id INT COMMENT '报价系统产品ID',

    -- 版本控制
    current_version VARCHAR(20) DEFAULT '1.0' COMMENT '当前版本',

    -- 描述
    description TEXT COMMENT '产品描述',
    remarks TEXT COMMENT '备注',

    -- 审计字段
    created_by INT COMMENT '创建人ID',
    created_by_name VARCHAR(100) COMMENT '创建人姓名',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by INT COMMENT '更新人ID',
    updated_by_name VARCHAR(100) COMMENT '更新人姓名',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_part_number (part_number),
    INDEX idx_customer (customer_id),
    INDEX idx_category (category),
    INDEX idx_status (status),
    FULLTEXT idx_search (part_number, product_name, customer_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品主数据表';

-- 2. 技术规格表
CREATE TABLE IF NOT EXISTS tdm_technical_specs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT NOT NULL COMMENT '产品主数据ID',
    part_number VARCHAR(100) NOT NULL COMMENT '品番号(冗余)',

    -- 材料信息
    material_code VARCHAR(50) COMMENT '材料代码',
    material_name VARCHAR(100) COMMENT '材料名称',
    material_spec VARCHAR(200) COMMENT '材料规格',
    density DECIMAL(10,4) COMMENT '密度 g/cm3',
    hardness VARCHAR(50) COMMENT '硬度',
    tensile_strength DECIMAL(10,2) COMMENT '抗拉强度 MPa',

    -- 尺寸信息
    outer_diameter DECIMAL(10,4) COMMENT '外径 mm',
    inner_diameter DECIMAL(10,4) COMMENT '内径 mm',
    length DECIMAL(10,4) COMMENT '长度 mm',
    width DECIMAL(10,4) COMMENT '宽度 mm',
    height DECIMAL(10,4) COMMENT '高度 mm',
    weight DECIMAL(10,4) COMMENT '重量 kg',
    volume DECIMAL(10,4) COMMENT '体积 cm3',

    -- 精度要求
    tolerance_class VARCHAR(50) COMMENT '公差等级',
    surface_roughness VARCHAR(50) COMMENT '表面粗糙度 Ra',
    geometric_tolerance JSON COMMENT '几何公差 JSON',
    position_tolerance VARCHAR(100) COMMENT '位置公差',
    form_tolerance VARCHAR(100) COMMENT '形状公差',

    -- 热处理
    heat_treatment VARCHAR(200) COMMENT '热处理要求',
    hardness_spec VARCHAR(100) COMMENT '硬度要求',
    heat_treatment_temp VARCHAR(100) COMMENT '热处理温度',

    -- 表面处理
    surface_treatment VARCHAR(200) COMMENT '表面处理',
    coating_spec VARCHAR(200) COMMENT '涂层规格',
    coating_thickness VARCHAR(100) COMMENT '涂层厚度',
    color VARCHAR(50) COMMENT '颜色',

    -- 特殊要求
    special_requirements TEXT COMMENT '特殊要求',
    quality_requirements TEXT COMMENT '质量要求',
    packaging_requirements TEXT COMMENT '包装要求',

    -- 版本控制
    version VARCHAR(20) DEFAULT '1.0' COMMENT '版本号',
    is_current BOOLEAN DEFAULT TRUE COMMENT '是否当前版本',
    parent_version_id BIGINT COMMENT '上一版本ID',
    version_note TEXT COMMENT '版本说明',

    -- 审计字段
    created_by INT COMMENT '创建人ID',
    created_by_name VARCHAR(100) COMMENT '创建人姓名',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES tdm_product_master(id) ON DELETE CASCADE,
    INDEX idx_product (product_id),
    INDEX idx_part_number (part_number),
    INDEX idx_version (version),
    INDEX idx_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技术规格表';

-- 3. 检验标准表
CREATE TABLE IF NOT EXISTS tdm_inspection_criteria (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT NOT NULL COMMENT '产品主数据ID',
    part_number VARCHAR(100) NOT NULL COMMENT '品番号(冗余)',

    -- 标准基本信息
    criteria_code VARCHAR(50) NOT NULL COMMENT '检验标准编码',
    criteria_name VARCHAR(200) NOT NULL COMMENT '检验标准名称',

    -- 检验阶段
    inspection_stage ENUM('incoming', 'process', 'final', 'outgoing') COMMENT 'IQC/IPQC/FQC/OQC',

    -- 检验方式
    inspection_method ENUM('full', 'sampling', 'skip') DEFAULT 'sampling' COMMENT '检验方式',
    sampling_plan VARCHAR(100) COMMENT '抽样方案 如 AQL 1.0',
    sample_size_formula VARCHAR(200) COMMENT '抽样数量公式',

    -- 检验项目 (JSON数组)
    inspection_items JSON COMMENT '检验项目列表',

    -- AQL 标准
    aql_critical DECIMAL(5,2) COMMENT '致命缺陷AQL',
    aql_major DECIMAL(5,2) COMMENT '严重缺陷AQL',
    aql_minor DECIMAL(5,2) COMMENT '轻微缺陷AQL',

    -- 关联 MES 检验标准
    mes_standard_id INT COMMENT 'MES系统检验标准ID',

    -- 版本控制
    version VARCHAR(20) DEFAULT '1.0' COMMENT '版本号',
    is_current BOOLEAN DEFAULT TRUE COMMENT '是否当前版本',
    parent_version_id BIGINT COMMENT '上一版本ID',
    version_note TEXT COMMENT '版本说明',

    -- 生效日期
    effective_date DATE COMMENT '生效日期',
    expiry_date DATE COMMENT '失效日期',

    -- 状态
    status ENUM('draft', 'active', 'deprecated') DEFAULT 'draft' COMMENT '状态',

    -- 审批信息
    approved_by INT COMMENT '审批人ID',
    approved_by_name VARCHAR(100) COMMENT '审批人姓名',
    approved_at DATETIME COMMENT '审批时间',

    -- 审计字段
    created_by INT COMMENT '创建人ID',
    created_by_name VARCHAR(100) COMMENT '创建人姓名',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES tdm_product_master(id) ON DELETE CASCADE,
    UNIQUE KEY uk_criteria_version (criteria_code, version),
    INDEX idx_product (product_id),
    INDEX idx_part_number (part_number),
    INDEX idx_stage (inspection_stage),
    INDEX idx_status (status),
    INDEX idx_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检验标准表';

-- 4. 工艺文件表
CREATE TABLE IF NOT EXISTS tdm_process_documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT NOT NULL COMMENT '产品主数据ID',
    part_number VARCHAR(100) NOT NULL COMMENT '品番号(冗余)',

    -- 工艺信息
    process_code VARCHAR(50) COMMENT '工艺代码',
    process_name VARCHAR(100) COMMENT '工艺名称',
    process_category VARCHAR(50) COMMENT '工艺类别',
    process_sequence INT DEFAULT 0 COMMENT '工序顺序',

    -- 关联报价系统工艺
    quotation_process_id INT COMMENT '报价系统工艺ID',

    -- 工艺参数
    setup_time DECIMAL(10,4) COMMENT '准备时间(分钟)',
    cycle_time DECIMAL(10,4) COMMENT '加工周期(分钟)',
    daily_output INT COMMENT '日产量',
    defect_rate DECIMAL(5,4) COMMENT '不良率',

    -- 设备要求
    machine_type VARCHAR(100) COMMENT '设备类型',
    machine_model VARCHAR(100) COMMENT '设备型号',
    machine_specs TEXT COMMENT '设备规格要求',

    -- 工艺参数详情 (JSON)
    parameters JSON COMMENT '工艺参数',

    -- 作业标准
    work_instruction TEXT COMMENT '作业指导',
    safety_notes TEXT COMMENT '安全注意事项',
    quality_points TEXT COMMENT '质量要点',

    -- 文件关联 (通过 FileIndex)
    file_index_ids JSON COMMENT '关联的FileIndex ID列表',

    -- 版本控制
    version VARCHAR(20) DEFAULT '1.0' COMMENT '版本号',
    is_current BOOLEAN DEFAULT TRUE COMMENT '是否当前版本',
    parent_version_id BIGINT COMMENT '上一版本ID',
    version_note TEXT COMMENT '版本说明',

    -- 审计字段
    created_by INT COMMENT '创建人ID',
    created_by_name VARCHAR(100) COMMENT '创建人姓名',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES tdm_product_master(id) ON DELETE CASCADE,
    INDEX idx_product (product_id),
    INDEX idx_part_number (part_number),
    INDEX idx_process_code (process_code),
    INDEX idx_sequence (process_sequence),
    INDEX idx_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工艺文件表';

-- 5. 产品-文件关联表
CREATE TABLE IF NOT EXISTS tdm_product_file_links (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    product_id BIGINT NOT NULL COMMENT '产品主数据ID',
    part_number VARCHAR(100) NOT NULL COMMENT '品番号(冗余)',

    -- 文件关联 (FileIndex)
    file_index_id BIGINT NOT NULL COMMENT 'FileIndex表ID',
    file_uuid VARCHAR(32) COMMENT 'FileIndex UUID(冗余)',

    -- 文件分类
    file_type ENUM('drawing', 'specification', 'inspection_standard',
                   'work_instruction', 'process_sheet', 'photo', 'certificate',
                   'report', 'contract', 'other') NOT NULL COMMENT '文件类型',

    -- 文件信息 (冗余，便于显示)
    file_name VARCHAR(255) COMMENT '文件名',
    file_category VARCHAR(64) COMMENT 'FileIndex分类',

    -- 显示控制
    is_primary BOOLEAN DEFAULT FALSE COMMENT '是否主文件',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    description VARCHAR(500) COMMENT '文件描述',

    -- 审计字段
    linked_by INT COMMENT '关联人ID',
    linked_by_name VARCHAR(100) COMMENT '关联人姓名',
    linked_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (product_id) REFERENCES tdm_product_master(id) ON DELETE CASCADE,
    INDEX idx_product (product_id),
    INDEX idx_part_number (part_number),
    INDEX idx_file_index (file_index_id),
    INDEX idx_file_type (file_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品-文件关联表';

-- 创建视图：产品完整信息视图
CREATE OR REPLACE VIEW v_tdm_product_full AS
SELECT
    p.id,
    p.part_number,
    p.product_name,
    p.product_name_en,
    p.customer_id,
    p.customer_name,
    p.customer_part_number,
    p.category,
    p.sub_category,
    p.status,
    p.current_version,
    p.created_at,
    p.updated_at,
    -- 技术规格数量
    (SELECT COUNT(*) FROM tdm_technical_specs ts WHERE ts.product_id = p.id AND ts.is_current = TRUE) AS spec_count,
    -- 检验标准数量
    (SELECT COUNT(*) FROM tdm_inspection_criteria ic WHERE ic.product_id = p.id AND ic.is_current = TRUE) AS inspection_count,
    -- 工艺文件数量
    (SELECT COUNT(*) FROM tdm_process_documents pd WHERE pd.product_id = p.id AND pd.is_current = TRUE) AS process_count,
    -- 关联文件数量
    (SELECT COUNT(*) FROM tdm_product_file_links fl WHERE fl.product_id = p.id) AS file_count
FROM tdm_product_master p
WHERE p.is_active = TRUE;

-- 插入示例数据（可选）
-- INSERT INTO tdm_product_master (part_number, product_name, category, status, created_by_name)
-- VALUES ('SAMPLE-001', '示例产品', '机械零件', 'active', '系统初始化');
