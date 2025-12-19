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
    """文件分类枚举"""
    SPECIFICATION = 'specification'   # 采购式样书
    DRAWING = 'drawing'               # 图纸
    CONTRACT = 'contract'             # 合同
    INVOICE = 'invoice'               # 发票
    QC_REPORT = 'qc_report'           # 质检报告
    DELIVERY_NOTE = 'delivery_note'   # 送货单
    CERTIFICATE = 'certificate'       # 证书
    PHOTO = 'photo'                   # 照片
    OTHER = 'other'                   # 其他


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


# 分类信息字典（用于前端显示）
FILE_CATEGORIES = {
    'specification': {'zh': '采购式样书', 'ja': '購買仕様書', 'en': 'Specification', 'icon': 'FileTextOutlined'},
    'drawing': {'zh': '图纸', 'ja': '設計図面', 'en': 'Drawing', 'icon': 'FileImageOutlined'},
    'contract': {'zh': '合同', 'ja': '契約書', 'en': 'Contract', 'icon': 'FileProtectOutlined'},
    'invoice': {'zh': '发票', 'ja': '請求書', 'en': 'Invoice', 'icon': 'FileDoneOutlined'},
    'qc_report': {'zh': '质检报告', 'ja': '品質報告', 'en': 'QC Report', 'icon': 'FileSearchOutlined'},
    'delivery_note': {'zh': '送货单', 'ja': '納品書', 'en': 'Delivery Note', 'icon': 'FileSyncOutlined'},
    'certificate': {'zh': '证书', 'ja': '証明書', 'en': 'Certificate', 'icon': 'SafetyCertificateOutlined'},
    'photo': {'zh': '照片', 'ja': '写真', 'en': 'Photo', 'icon': 'PictureOutlined'},
    'other': {'zh': '其他', 'ja': 'その他', 'en': 'Other', 'icon': 'FileOutlined'},
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
            'file_category_icon': category_info['icon'],
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
