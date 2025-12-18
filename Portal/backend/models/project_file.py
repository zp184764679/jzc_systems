"""
ProjectFile Model - 项目文件管理模型
包含文件版本控制和原版/中文版管理
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from models import Base
import enum


class FileCategory(str, enum.Enum):
    """文件分类枚举"""
    CONTRACT = 'contract'         # 合同
    QUOTE = 'quote'               # 报价单
    PO = 'po'                     # 采购订单
    QC_REPORT = 'qc_report'       # 质检报告
    DRAWING = 'drawing'           # 图纸
    PHOTO = 'photo'               # 照片
    OTHER = 'other'               # 其他


class OriginalLanguage(str, enum.Enum):
    """原文语言枚举"""
    CHINESE = 'zh'        # 中文
    ENGLISH = 'en'        # 英文
    JAPANESE = 'ja'       # 日文


class ProjectFile(Base):
    """项目文件表"""
    __tablename__ = 'project_files'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True, comment='所属项目ID')

    # 文件基本信息
    file_name = Column(String(255), nullable=False, comment='文件名')
    file_path = Column(String(500), nullable=False, comment='文件路径')
    file_url = Column(String(500), comment='文件访问URL')
    file_size = Column(BigInteger, comment='文件大小(字节)')
    file_type = Column(String(100), comment='文件类型(MIME type)')
    md5_hash = Column(String(32), comment='MD5哈希值')

    # 文件分类
    category = Column(
        Enum(FileCategory),
        default=FileCategory.OTHER,
        nullable=False,
        comment='文件分类'
    )

    # === 原版/中文版管理 ===
    is_chinese_version = Column(Boolean, default=False, comment='是否为中文版')
    original_language = Column(
        Enum(OriginalLanguage),
        default=OriginalLanguage.CHINESE,
        nullable=False,
        comment='原文语言'
    )
    related_file_id = Column(Integer, ForeignKey('project_files.id'), comment='关联的原版/中文版文件ID')

    # === 版本控制 ===
    version = Column(String(20), default='1.0', comment='版本号')
    is_latest_version = Column(Boolean, default=True, comment='是否为最新版本')
    parent_file_id = Column(Integer, ForeignKey('project_files.id'), comment='父版本文件ID')

    # 上传者和备注
    uploaded_by_id = Column(Integer, nullable=False, comment='上传者ID')
    remark = Column(Text, comment='备注')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 软删除字段
    deleted_at = Column(DateTime, nullable=True, comment='删除时间（软删除）')
    delete_reason = Column(String(500), nullable=True, comment='删除原因')
    deleted_by_id = Column(Integer, nullable=True, comment='删除者ID')

    # 关系
    # project = relationship('Project', back_populates='files')
    # related_file = relationship('ProjectFile', remote_side=[id], foreign_keys=[related_file_id])
    # parent_file = relationship('ProjectFile', remote_side=[id], foreign_keys=[parent_file_id])

    @property
    def is_deleted(self):
        """检查文件是否已删除"""
        return self.deleted_at is not None

    def to_dict(self, include_deleted_info=False):
        """Convert to dictionary

        Args:
            include_deleted_info: 是否包含删除相关信息
        """
        result = {
            'id': self.id,
            'project_id': self.project_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'md5_hash': self.md5_hash,
            'category': self.category.value if isinstance(self.category, FileCategory) else self.category,
            'is_chinese_version': self.is_chinese_version,
            'original_language': self.original_language.value if isinstance(self.original_language, OriginalLanguage) else self.original_language,
            'related_file_id': self.related_file_id,
            'version': self.version,
            'is_latest_version': self.is_latest_version,
            'parent_file_id': self.parent_file_id,
            'uploaded_by_id': self.uploaded_by_id,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
        }

        if include_deleted_info or self.is_deleted:
            result['deleted_at'] = self.deleted_at.isoformat() if self.deleted_at else None
            result['delete_reason'] = self.delete_reason
            result['deleted_by_id'] = self.deleted_by_id

        return result

    def __repr__(self):
        return f"<ProjectFile {self.file_name} (v{self.version})>"
