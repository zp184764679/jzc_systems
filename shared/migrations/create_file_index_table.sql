-- 文件中心统一索引表
-- 用于跨系统文件的中心化管理和多维度查询

CREATE TABLE IF NOT EXISTS file_index (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    file_uuid VARCHAR(32) NOT NULL UNIQUE COMMENT '文件唯一标识',

    -- 来源信息
    source_system VARCHAR(32) NOT NULL COMMENT '来源系统: portal/caigou/quotation/hr/crm/scm/shm/eam/mes',
    source_table VARCHAR(64) NOT NULL COMMENT '来源表名',
    source_id BIGINT NOT NULL COMMENT '来源记录ID',

    -- 基本信息
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '存储路径',
    file_url VARCHAR(500) COMMENT '访问URL',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    file_type VARCHAR(128) COMMENT 'MIME类型',
    file_extension VARCHAR(16) COMMENT '文件扩展名',
    md5_hash VARCHAR(32) COMMENT 'MD5哈希值',

    -- 分类
    file_category VARCHAR(64) NOT NULL COMMENT '文件分类: specification/drawing/contract/invoice/qc_report/delivery_note/certificate/photo/other',

    -- 业务关联（多维索引）
    order_no VARCHAR(100) COMMENT '订单号',
    project_id INT COMMENT '项目ID',
    project_no VARCHAR(50) COMMENT '项目编号',
    part_number VARCHAR(100) COMMENT '品番号',
    supplier_id BIGINT COMMENT '供应商ID',
    supplier_name VARCHAR(200) COMMENT '供应商名称',
    customer_id INT COMMENT '客户ID',
    customer_name VARCHAR(200) COMMENT '客户名称',
    po_number VARCHAR(50) COMMENT '采购订单号',

    -- 版本控制
    version VARCHAR(16) DEFAULT '1.0' COMMENT '版本号',
    is_latest_version TINYINT(1) DEFAULT 1 COMMENT '是否最新版本',
    parent_file_id BIGINT COMMENT '父版本文件ID',

    -- 状态
    status ENUM('active', 'archived', 'deleted') DEFAULT 'active' COMMENT '状态',

    -- 审计信息
    uploaded_by INT COMMENT '上传者用户ID',
    uploaded_by_name VARCHAR(100) COMMENT '上传者姓名',
    uploaded_at DATETIME COMMENT '上传时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引
    INDEX idx_file_uuid (file_uuid),
    INDEX idx_source (source_system, source_table, source_id),
    INDEX idx_order (order_no),
    INDEX idx_project (project_id),
    INDEX idx_project_no (project_no),
    INDEX idx_supplier (supplier_id),
    INDEX idx_customer (customer_id),
    INDEX idx_category (file_category),
    INDEX idx_part (part_number),
    INDEX idx_po (po_number),
    INDEX idx_status (status),
    INDEX idx_uploaded_at (uploaded_at),
    INDEX idx_created_at (created_at),
    FULLTEXT idx_search (file_name, supplier_name, customer_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件中心统一索引表';

-- 文件分类字典表（可选，用于管理分类）
CREATE TABLE IF NOT EXISTS file_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(32) NOT NULL UNIQUE COMMENT '分类代码',
    name_zh VARCHAR(64) NOT NULL COMMENT '中文名称',
    name_ja VARCHAR(64) COMMENT '日文名称',
    name_en VARCHAR(64) COMMENT '英文名称',
    icon VARCHAR(64) COMMENT '图标',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件分类字典';

-- 初始化文件分类
INSERT INTO file_categories (code, name_zh, name_ja, name_en, icon, sort_order) VALUES
('specification', '采购式样书', '購買仕様書', 'Specification', 'FileTextOutlined', 1),
('drawing', '图纸', '設計図面', 'Drawing', 'FileImageOutlined', 2),
('contract', '合同', '契約書', 'Contract', 'FileProtectOutlined', 3),
('invoice', '发票', '請求書', 'Invoice', 'FileDoneOutlined', 4),
('qc_report', '质检报告', '品質報告', 'QC Report', 'FileSearchOutlined', 5),
('delivery_note', '送货单', '納品書', 'Delivery Note', 'FileSyncOutlined', 6),
('certificate', '证书', '証明書', 'Certificate', 'SafetyCertificateOutlined', 7),
('photo', '照片', '写真', 'Photo', 'PictureOutlined', 8),
('other', '其他', 'その他', 'Other', 'FileOutlined', 99)
ON DUPLICATE KEY UPDATE name_zh = VALUES(name_zh);
