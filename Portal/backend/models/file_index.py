"""
FileIndex Model - 文件中心统一索引模型
用于跨系统文件的中心化管理和多维度查询
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger, Enum as SQLEnum
from datetime import datetime
from models import Base
import enum
import uuid


class FileStatus(str, enum.Enum):
    """文件状态枚举"""
    ACTIVE = 'active'       # 活跃
    ARCHIVED = 'archived'   # 归档
    DELETED = 'deleted'     # 已删除


class FileCategoryEnum(str, enum.Enum):
    """
    文件分类枚举 - 日本制造业完整业务流程
    按流程阶段分组：营业→技术→采购→生产→品质→物流→财务→合同→认证
    """
    # === 1. 营业/询价阶段 (Sales/Inquiry) ===
    RFQ = 'rfq'                                   # 見積依頼書 - Request for Quotation
    QUOTATION = 'quotation'                       # 見積書 - Quotation

    # === 2. 技术/设计 (Engineering/Design) ===
    SPECIFICATION = 'specification'               # 仕様書 - Specification (技术规格)
    PURCHASE_SPEC = 'purchase_spec'               # 購買仕様書 - Purchase Specification
    DRAWING = 'drawing'                           # 図面 - Drawing (设计图纸)
    APPROVAL_DRAWING = 'approval_drawing'         # 承認図 - Approval Drawing
    BOM = 'bom'                                   # 部品表 - Bill of Materials
    WORK_INSTRUCTION = 'work_instruction'         # 作業標準書 - Work Instruction/SOP

    # === 3. 采购/发注 (Procurement) ===
    PURCHASE_ORDER = 'purchase_order'             # 注文書/発注書 - Purchase Order
    ORDER_ACK = 'order_ack'                       # 注文請書 - Order Acknowledgement

    # === 4. 生产 (Manufacturing) ===
    MANUFACTURING_ORDER = 'manufacturing_order'   # 製造指示書 - Manufacturing Order
    PROCESS_SHEET = 'process_sheet'               # 工程表 - Process Sheet/Routing

    # === 5. 品质管理 (Quality) ===
    INSPECTION_STANDARD = 'inspection_standard'   # 検査基準書 - Inspection Standard
    INSPECTION_REPORT = 'inspection_report'       # 検査成績書 - Inspection Report
    MILL_CERT = 'mill_cert'                       # ミルシート - Mill Certificate
    FIRST_ARTICLE = 'first_article'               # 初物検査報告 - First Article Inspection
    NCR = 'ncr'                                   # 不良報告書 - Non-conformance Report
    PPAP = 'ppap'                                 # PPAP文書 - Production Part Approval Process

    # === 6. 物流/出货 (Logistics/Shipping) ===
    DELIVERY_NOTE = 'delivery_note'               # 納品書 - Delivery Note
    PACKING_LIST = 'packing_list'                 # 梱包明細 - Packing List
    SHIPPING_INSPECTION = 'shipping_inspection'   # 出荷検査表 - Shipping Inspection
    WAYBILL = 'waybill'                           # 送り状 - Waybill/BOL

    # === 7. 财务/结算 (Finance) ===
    INVOICE = 'invoice'                           # 請求書 - Invoice
    RECEIPT = 'receipt'                           # 領収書 - Receipt
    DEBIT_NOTE = 'debit_note'                     # 借方票 - Debit Note
    CREDIT_NOTE = 'credit_note'                   # 貸方票 - Credit Note

    # === 8. 合同/契约 (Contract) ===
    CONTRACT = 'contract'                         # 契約書 - Contract (一般合同)
    MASTER_AGREEMENT = 'master_agreement'         # 基本契約書 - Master Agreement
    NDA = 'nda'                                   # 機密保持契約 - Non-Disclosure Agreement
    QUALITY_AGREEMENT = 'quality_agreement'       # 品質保証契約 - Quality Agreement

    # === 9. 认证/合规 (Certification/Compliance) ===
    CERTIFICATE = 'certificate'                   # 証明書 - Certificate (一般证书)
    ISO_CERT = 'iso_cert'                         # ISO認証 - ISO Certificate
    ROHS_CERT = 'rohs_cert'                       # RoHS適合証明 - RoHS Certificate
    SDS = 'sds'                                   # SDS/MSDS - Safety Data Sheet
    COC = 'coc'                                   # 適合証明書 - Certificate of Conformance

    # === 10. 其他 (Others) ===
    PHOTO = 'photo'                               # 写真 - Photo
    CORRESPONDENCE = 'correspondence'             # 連絡文書 - Correspondence
    MEETING_MINUTES = 'meeting_minutes'           # 議事録 - Meeting Minutes
    OTHER = 'other'                               # その他 - Other


class SourceSystem(str, enum.Enum):
    """来源系统枚举"""
    PORTAL = 'portal'
    CAIGOU = 'caigou'
    QUOTATION = 'quotation'
    HR = 'hr'
    CRM = 'crm'
    SCM = 'scm'
    SHM = 'shm'
    EAM = 'eam'
    MES = 'mes'


# 分类信息字典（用于前端显示）- 按日本制造业流程分组
FILE_CATEGORIES = {
    # === 1. 营业/询价阶段 (Sales/Inquiry) ===
    'rfq': {'zh': '询价单', 'ja': '見積依頼書', 'en': 'RFQ', 'icon': 'QuestionCircleOutlined', 'group': 'sales', 'sort': 101},
    'quotation': {'zh': '报价单', 'ja': '見積書', 'en': 'Quotation', 'icon': 'DollarOutlined', 'group': 'sales', 'sort': 102},

    # === 2. 技术/设计 (Engineering/Design) ===
    'specification': {'zh': '技术规格书', 'ja': '仕様書', 'en': 'Specification', 'icon': 'FileTextOutlined', 'group': 'engineering', 'sort': 201},
    'purchase_spec': {'zh': '采购仕样书', 'ja': '購買仕様書', 'en': 'Purchase Spec', 'icon': 'ProfileOutlined', 'group': 'engineering', 'sort': 202},
    'drawing': {'zh': '图纸', 'ja': '図面', 'en': 'Drawing', 'icon': 'FileImageOutlined', 'group': 'engineering', 'sort': 203},
    'approval_drawing': {'zh': '承认图', 'ja': '承認図', 'en': 'Approval Drawing', 'icon': 'CheckSquareOutlined', 'group': 'engineering', 'sort': 204},
    'bom': {'zh': '物料清单', 'ja': '部品表', 'en': 'BOM', 'icon': 'UnorderedListOutlined', 'group': 'engineering', 'sort': 205},
    'work_instruction': {'zh': '作业标准书', 'ja': '作業標準書', 'en': 'Work Instruction', 'icon': 'SolutionOutlined', 'group': 'engineering', 'sort': 206},

    # === 3. 采购/发注 (Procurement) ===
    'purchase_order': {'zh': '采购订单', 'ja': '注文書', 'en': 'Purchase Order', 'icon': 'ShoppingCartOutlined', 'group': 'procurement', 'sort': 301},
    'order_ack': {'zh': '订单确认书', 'ja': '注文請書', 'en': 'Order Ack', 'icon': 'CheckCircleOutlined', 'group': 'procurement', 'sort': 302},

    # === 4. 生产 (Manufacturing) ===
    'manufacturing_order': {'zh': '制造指示书', 'ja': '製造指示書', 'en': 'MO', 'icon': 'ToolOutlined', 'group': 'manufacturing', 'sort': 401},
    'process_sheet': {'zh': '工程表', 'ja': '工程表', 'en': 'Process Sheet', 'icon': 'NodeIndexOutlined', 'group': 'manufacturing', 'sort': 402},

    # === 5. 品质管理 (Quality) ===
    'inspection_standard': {'zh': '检查基准书', 'ja': '検査基準書', 'en': 'Inspection Std', 'icon': 'AuditOutlined', 'group': 'quality', 'sort': 501},
    'inspection_report': {'zh': '检查成绩书', 'ja': '検査成績書', 'en': 'Inspection Report', 'icon': 'FileSearchOutlined', 'group': 'quality', 'sort': 502},
    'mill_cert': {'zh': '材质证明', 'ja': 'ミルシート', 'en': 'Mill Cert', 'icon': 'ExperimentOutlined', 'group': 'quality', 'sort': 503},
    'first_article': {'zh': '初物检查', 'ja': '初物検査報告', 'en': 'FAI', 'icon': 'FlagOutlined', 'group': 'quality', 'sort': 504},
    'ncr': {'zh': '不良报告', 'ja': '不良報告書', 'en': 'NCR', 'icon': 'WarningOutlined', 'group': 'quality', 'sort': 505},
    'ppap': {'zh': 'PPAP文档', 'ja': 'PPAP文書', 'en': 'PPAP', 'icon': 'FileProtectOutlined', 'group': 'quality', 'sort': 506},

    # === 6. 物流/出货 (Logistics/Shipping) ===
    'delivery_note': {'zh': '送货单', 'ja': '納品書', 'en': 'Delivery Note', 'icon': 'FileSyncOutlined', 'group': 'logistics', 'sort': 601},
    'packing_list': {'zh': '装箱单', 'ja': '梱包明細', 'en': 'Packing List', 'icon': 'InboxOutlined', 'group': 'logistics', 'sort': 602},
    'shipping_inspection': {'zh': '出货检查表', 'ja': '出荷検査表', 'en': 'Ship Inspection', 'icon': 'CarOutlined', 'group': 'logistics', 'sort': 603},
    'waybill': {'zh': '运单', 'ja': '送り状', 'en': 'Waybill', 'icon': 'SendOutlined', 'group': 'logistics', 'sort': 604},

    # === 7. 财务/结算 (Finance) ===
    'invoice': {'zh': '发票/请款单', 'ja': '請求書', 'en': 'Invoice', 'icon': 'FileDoneOutlined', 'group': 'finance', 'sort': 701},
    'receipt': {'zh': '收据', 'ja': '領収書', 'en': 'Receipt', 'icon': 'WalletOutlined', 'group': 'finance', 'sort': 702},
    'debit_note': {'zh': '借项通知', 'ja': '借方票', 'en': 'Debit Note', 'icon': 'MinusCircleOutlined', 'group': 'finance', 'sort': 703},
    'credit_note': {'zh': '贷项通知', 'ja': '貸方票', 'en': 'Credit Note', 'icon': 'PlusCircleOutlined', 'group': 'finance', 'sort': 704},

    # === 8. 合同/契约 (Contract) ===
    'contract': {'zh': '合同', 'ja': '契約書', 'en': 'Contract', 'icon': 'FileProtectOutlined', 'group': 'contract', 'sort': 801},
    'master_agreement': {'zh': '基本合同', 'ja': '基本契約書', 'en': 'Master Agreement', 'icon': 'BookOutlined', 'group': 'contract', 'sort': 802},
    'nda': {'zh': '保密协议', 'ja': '機密保持契約', 'en': 'NDA', 'icon': 'LockOutlined', 'group': 'contract', 'sort': 803},
    'quality_agreement': {'zh': '品质保证协议', 'ja': '品質保証契約', 'en': 'QA Agreement', 'icon': 'SafetyOutlined', 'group': 'contract', 'sort': 804},

    # === 9. 认证/合规 (Certification/Compliance) ===
    'certificate': {'zh': '证书', 'ja': '証明書', 'en': 'Certificate', 'icon': 'SafetyCertificateOutlined', 'group': 'certification', 'sort': 901},
    'iso_cert': {'zh': 'ISO认证', 'ja': 'ISO認証', 'en': 'ISO Cert', 'icon': 'TrophyOutlined', 'group': 'certification', 'sort': 902},
    'rohs_cert': {'zh': 'RoHS证明', 'ja': 'RoHS適合証明', 'en': 'RoHS Cert', 'icon': 'GlobalOutlined', 'group': 'certification', 'sort': 903},
    'sds': {'zh': '安全数据表', 'ja': 'SDS', 'en': 'SDS/MSDS', 'icon': 'AlertOutlined', 'group': 'certification', 'sort': 904},
    'coc': {'zh': '符合性证明', 'ja': '適合証明書', 'en': 'CoC', 'icon': 'VerifiedOutlined', 'group': 'certification', 'sort': 905},

    # === 10. 其他 (Others) ===
    'photo': {'zh': '照片', 'ja': '写真', 'en': 'Photo', 'icon': 'PictureOutlined', 'group': 'other', 'sort': 1001},
    'correspondence': {'zh': '往来文件', 'ja': '連絡文書', 'en': 'Correspondence', 'icon': 'MailOutlined', 'group': 'other', 'sort': 1002},
    'meeting_minutes': {'zh': '会议记录', 'ja': '議事録', 'en': 'Meeting Minutes', 'icon': 'TeamOutlined', 'group': 'other', 'sort': 1003},
    'other': {'zh': '其他', 'ja': 'その他', 'en': 'Other', 'icon': 'FileOutlined', 'group': 'other', 'sort': 9999},
}

# 分类分组信息
FILE_CATEGORY_GROUPS = {
    'sales': {'zh': '营业/询价', 'ja': '営業/見積', 'en': 'Sales/Inquiry', 'icon': 'ShopOutlined', 'sort': 1},
    'engineering': {'zh': '技术/设计', 'ja': '技術/設計', 'en': 'Engineering', 'icon': 'ToolOutlined', 'sort': 2},
    'procurement': {'zh': '采购/发注', 'ja': '購買/発注', 'en': 'Procurement', 'icon': 'ShoppingCartOutlined', 'sort': 3},
    'manufacturing': {'zh': '生产', 'ja': '製造', 'en': 'Manufacturing', 'icon': 'BuildOutlined', 'sort': 4},
    'quality': {'zh': '品质管理', 'ja': '品質管理', 'en': 'Quality', 'icon': 'SafetyOutlined', 'sort': 5},
    'logistics': {'zh': '物流/出货', 'ja': '物流/出荷', 'en': 'Logistics', 'icon': 'CarOutlined', 'sort': 6},
    'finance': {'zh': '财务/结算', 'ja': '財務/決済', 'en': 'Finance', 'icon': 'AccountBookOutlined', 'sort': 7},
    'contract': {'zh': '合同/契约', 'ja': '契約', 'en': 'Contract', 'icon': 'FileProtectOutlined', 'sort': 8},
    'certification': {'zh': '认证/合规', 'ja': '認証/コンプライアンス', 'en': 'Certification', 'icon': 'SafetyCertificateOutlined', 'sort': 9},
    'other': {'zh': '其他', 'ja': 'その他', 'en': 'Other', 'icon': 'FolderOutlined', 'sort': 99},
}

# 来源系统信息
SOURCE_SYSTEMS = {
    'portal': {'zh': '门户系统', 'en': 'Portal'},
    'caigou': {'zh': '采购系统', 'en': 'Procurement'},
    'quotation': {'zh': '报价系统', 'en': 'Quotation'},
    'hr': {'zh': '人事系统', 'en': 'HR'},
    'crm': {'zh': 'CRM系统', 'en': 'CRM'},
    'scm': {'zh': '仓库系统', 'en': 'SCM'},
    'shm': {'zh': '出货系统', 'en': 'SHM'},
    'eam': {'zh': '设备系统', 'en': 'EAM'},
    'mes': {'zh': '生产系统', 'en': 'MES'},
}


def generate_file_uuid():
    """生成文件UUID"""
    return uuid.uuid4().hex


class FileIndex(Base):
    """文件中心统一索引表"""
    __tablename__ = 'file_index'

    # 主键
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_uuid = Column(String(32), unique=True, nullable=False, default=generate_file_uuid, comment='文件唯一标识')

    # 来源信息
    source_system = Column(String(32), nullable=False, index=True, comment='来源系统')
    source_table = Column(String(64), nullable=False, comment='来源表名')
    source_id = Column(BigInteger, nullable=False, comment='来源记录ID')

    # 基本信息
    file_name = Column(String(255), nullable=False, comment='文件名')
    file_path = Column(String(500), nullable=False, comment='存储路径')
    file_url = Column(String(500), comment='访问URL')
    file_size = Column(BigInteger, default=0, comment='文件大小(字节)')
    file_type = Column(String(128), comment='MIME类型')
    file_extension = Column(String(16), comment='文件扩展名')
    md5_hash = Column(String(32), comment='MD5哈希值')

    # 分类
    file_category = Column(String(64), nullable=False, default='other', index=True, comment='文件分类')

    # 业务关联（多维索引）
    order_no = Column(String(100), index=True, comment='订单号')
    project_id = Column(Integer, index=True, comment='项目ID')
    project_no = Column(String(50), index=True, comment='项目编号')
    part_number = Column(String(100), index=True, comment='品番号')
    supplier_id = Column(BigInteger, index=True, comment='供应商ID')
    supplier_name = Column(String(200), comment='供应商名称')
    customer_id = Column(Integer, index=True, comment='客户ID')
    customer_name = Column(String(200), comment='客户名称')
    po_number = Column(String(50), index=True, comment='采购订单号')

    # 版本控制
    version = Column(String(16), default='1.0', comment='版本号')
    is_latest_version = Column(Boolean, default=True, comment='是否最新版本')
    parent_file_id = Column(BigInteger, comment='父版本文件ID')

    # 状态
    status = Column(
        SQLEnum(FileStatus, values_callable=lambda x: [e.value for e in x]),
        default=FileStatus.ACTIVE,
        nullable=False,
        index=True,
        comment='状态'
    )

    # 审计信息
    uploaded_by = Column(Integer, comment='上传者用户ID')
    uploaded_by_name = Column(String(100), comment='上传者姓名')
    uploaded_at = Column(DateTime, comment='上传时间')
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def to_dict(self):
        """Convert to dictionary"""
        category_info = FILE_CATEGORIES.get(self.file_category, FILE_CATEGORIES['other'])
        source_info = SOURCE_SYSTEMS.get(self.source_system, {'zh': self.source_system, 'en': self.source_system})
        group_key = category_info.get('group', 'other')
        group_info = FILE_CATEGORY_GROUPS.get(group_key, FILE_CATEGORY_GROUPS['other'])

        return {
            'id': self.id,
            'file_uuid': self.file_uuid,
            # 来源
            'source_system': self.source_system,
            'source_system_name': source_info['zh'],
            'source_table': self.source_table,
            'source_id': self.source_id,
            # 基本信息
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'file_extension': self.file_extension,
            'md5_hash': self.md5_hash,
            # 分类
            'file_category': self.file_category,
            'file_category_name': category_info['zh'],
            'file_category_ja': category_info.get('ja', ''),
            'file_category_en': category_info.get('en', ''),
            'file_category_icon': category_info['icon'],
            'file_category_group': group_key,
            'file_category_group_name': group_info['zh'],
            # 业务关联
            'order_no': self.order_no,
            'project_id': self.project_id,
            'project_no': self.project_no,
            'part_number': self.part_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier_name,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'po_number': self.po_number,
            # 版本
            'version': self.version,
            'is_latest_version': self.is_latest_version,
            'parent_file_id': self.parent_file_id,
            # 状态
            'status': self.status.value if isinstance(self.status, FileStatus) else self.status,
            # 审计
            'uploaded_by': self.uploaded_by,
            'uploaded_by_name': self.uploaded_by_name,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<FileIndex {self.file_name} [{self.source_system}]>"
