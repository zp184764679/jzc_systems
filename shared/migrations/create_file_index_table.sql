-- 文件中心统一索引表
-- 用于跨系统文件的中心化管理和多维度查询
-- 日本制造业完整业务流程覆盖

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

    -- 分类 (完整的日本制造业文件类型)
    file_category VARCHAR(64) NOT NULL COMMENT '文件分类代码',

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

-- 文件分类分组表
CREATE TABLE IF NOT EXISTS file_category_groups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(32) NOT NULL UNIQUE COMMENT '分组代码',
    name_zh VARCHAR(64) NOT NULL COMMENT '中文名称',
    name_ja VARCHAR(64) COMMENT '日文名称',
    name_en VARCHAR(64) COMMENT '英文名称',
    icon VARCHAR(64) COMMENT '图标',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件分类分组';

-- 文件分类字典表
CREATE TABLE IF NOT EXISTS file_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(32) NOT NULL UNIQUE COMMENT '分类代码',
    group_code VARCHAR(32) NOT NULL COMMENT '所属分组',
    name_zh VARCHAR(64) NOT NULL COMMENT '中文名称',
    name_ja VARCHAR(64) COMMENT '日文名称',
    name_en VARCHAR(64) COMMENT '英文名称',
    icon VARCHAR(64) COMMENT '图标',
    sort_order INT DEFAULT 0 COMMENT '排序',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_group (group_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件分类字典';

-- 初始化分组数据
INSERT INTO file_category_groups (code, name_zh, name_ja, name_en, icon, sort_order) VALUES
('sales', '营业/询价', '営業/見積', 'Sales/Inquiry', 'ShopOutlined', 1),
('engineering', '技术/设计', '技術/設計', 'Engineering', 'ToolOutlined', 2),
('procurement', '采购/发注', '購買/発注', 'Procurement', 'ShoppingCartOutlined', 3),
('manufacturing', '生产', '製造', 'Manufacturing', 'BuildOutlined', 4),
('quality', '品质管理', '品質管理', 'Quality', 'SafetyOutlined', 5),
('logistics', '物流/出货', '物流/出荷', 'Logistics', 'CarOutlined', 6),
('finance', '财务/结算', '財務/決済', 'Finance', 'AccountBookOutlined', 7),
('contract', '合同/契约', '契約', 'Contract', 'FileProtectOutlined', 8),
('certification', '认证/合规', '認証/コンプライアンス', 'Certification', 'SafetyCertificateOutlined', 9),
('other', '其他', 'その他', 'Other', 'FolderOutlined', 99)
ON DUPLICATE KEY UPDATE name_zh = VALUES(name_zh), name_ja = VALUES(name_ja), name_en = VALUES(name_en);

-- 初始化文件分类数据 - 日本制造业完整业务流程
INSERT INTO file_categories (code, group_code, name_zh, name_ja, name_en, icon, sort_order) VALUES
-- 1. 营业/询价 (Sales/Inquiry)
('rfq', 'sales', '询价单', '見積依頼書', 'RFQ', 'QuestionCircleOutlined', 101),
('quotation', 'sales', '报价单', '見積書', 'Quotation', 'DollarOutlined', 102),

-- 2. 技术/设计 (Engineering/Design)
('specification', 'engineering', '技术规格书', '仕様書', 'Specification', 'FileTextOutlined', 201),
('purchase_spec', 'engineering', '采购仕样书', '購買仕様書', 'Purchase Spec', 'ProfileOutlined', 202),
('drawing', 'engineering', '图纸', '図面', 'Drawing', 'FileImageOutlined', 203),
('approval_drawing', 'engineering', '承认图', '承認図', 'Approval Drawing', 'CheckSquareOutlined', 204),
('bom', 'engineering', '物料清单', '部品表', 'BOM', 'UnorderedListOutlined', 205),
('work_instruction', 'engineering', '作业标准书', '作業標準書', 'Work Instruction', 'SolutionOutlined', 206),

-- 3. 采购/发注 (Procurement)
('purchase_order', 'procurement', '采购订单', '注文書', 'Purchase Order', 'ShoppingCartOutlined', 301),
('order_ack', 'procurement', '订单确认书', '注文請書', 'Order Ack', 'CheckCircleOutlined', 302),

-- 4. 生产 (Manufacturing)
('manufacturing_order', 'manufacturing', '制造指示书', '製造指示書', 'MO', 'ToolOutlined', 401),
('process_sheet', 'manufacturing', '工程表', '工程表', 'Process Sheet', 'NodeIndexOutlined', 402),

-- 5. 品质管理 (Quality)
('inspection_standard', 'quality', '检查基准书', '検査基準書', 'Inspection Std', 'AuditOutlined', 501),
('inspection_report', 'quality', '检查成绩书', '検査成績書', 'Inspection Report', 'FileSearchOutlined', 502),
('mill_cert', 'quality', '材质证明', 'ミルシート', 'Mill Cert', 'ExperimentOutlined', 503),
('first_article', 'quality', '初物检查', '初物検査報告', 'FAI', 'FlagOutlined', 504),
('ncr', 'quality', '不良报告', '不良報告書', 'NCR', 'WarningOutlined', 505),
('ppap', 'quality', 'PPAP文档', 'PPAP文書', 'PPAP', 'FileProtectOutlined', 506),

-- 6. 物流/出货 (Logistics/Shipping)
('delivery_note', 'logistics', '送货单', '納品書', 'Delivery Note', 'FileSyncOutlined', 601),
('packing_list', 'logistics', '装箱单', '梱包明細', 'Packing List', 'InboxOutlined', 602),
('shipping_inspection', 'logistics', '出货检查表', '出荷検査表', 'Ship Inspection', 'CarOutlined', 603),
('waybill', 'logistics', '运单', '送り状', 'Waybill', 'SendOutlined', 604),

-- 7. 财务/结算 (Finance)
('invoice', 'finance', '发票/请款单', '請求書', 'Invoice', 'FileDoneOutlined', 701),
('receipt', 'finance', '收据', '領収書', 'Receipt', 'WalletOutlined', 702),
('debit_note', 'finance', '借项通知', '借方票', 'Debit Note', 'MinusCircleOutlined', 703),
('credit_note', 'finance', '贷项通知', '貸方票', 'Credit Note', 'PlusCircleOutlined', 704),

-- 8. 合同/契约 (Contract)
('contract', 'contract', '合同', '契約書', 'Contract', 'FileProtectOutlined', 801),
('master_agreement', 'contract', '基本合同', '基本契約書', 'Master Agreement', 'BookOutlined', 802),
('nda', 'contract', '保密协议', '機密保持契約', 'NDA', 'LockOutlined', 803),
('quality_agreement', 'contract', '品质保证协议', '品質保証契約', 'QA Agreement', 'SafetyOutlined', 804),

-- 9. 认证/合规 (Certification/Compliance)
('certificate', 'certification', '证书', '証明書', 'Certificate', 'SafetyCertificateOutlined', 901),
('iso_cert', 'certification', 'ISO认证', 'ISO認証', 'ISO Cert', 'TrophyOutlined', 902),
('rohs_cert', 'certification', 'RoHS证明', 'RoHS適合証明', 'RoHS Cert', 'GlobalOutlined', 903),
('sds', 'certification', '安全数据表', 'SDS', 'SDS/MSDS', 'AlertOutlined', 904),
('coc', 'certification', '符合性证明', '適合証明書', 'CoC', 'VerifiedOutlined', 905),

-- 10. 其他 (Others)
('photo', 'other', '照片', '写真', 'Photo', 'PictureOutlined', 1001),
('correspondence', 'other', '往来文件', '連絡文書', 'Correspondence', 'MailOutlined', 1002),
('meeting_minutes', 'other', '会议记录', '議事録', 'Meeting Minutes', 'TeamOutlined', 1003),
('other', 'other', '其他', 'その他', 'Other', 'FileOutlined', 9999)
ON DUPLICATE KEY UPDATE
    group_code = VALUES(group_code),
    name_zh = VALUES(name_zh),
    name_ja = VALUES(name_ja),
    name_en = VALUES(name_en),
    icon = VALUES(icon),
    sort_order = VALUES(sort_order);
