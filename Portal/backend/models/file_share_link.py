"""
FileShareLink Model - 文件分享链接模型
支持密码保护、有效期、下载次数限制
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from datetime import datetime
from models import Base
import secrets
import hashlib


def generate_share_code(length=16):
    """生成唯一的分享码"""
    return secrets.token_urlsafe(length)[:length]


def hash_password(password):
    """对分享密码进行哈希"""
    if not password:
        return None
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    """验证分享密码"""
    if not hashed:
        return True  # 无密码保护
    if not password:
        return False
    return hashlib.sha256(password.encode()).hexdigest() == hashed


class FileShareLink(Base):
    """文件分享链接表"""
    __tablename__ = 'file_share_links'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 关联文件 (project_files)
    file_id = Column(Integer, ForeignKey('project_files.id'), nullable=False, index=True, comment='关联的文件ID')

    # 分享码
    share_code = Column(String(64), nullable=False, unique=True, index=True, comment='分享码')

    # 安全设置
    share_password_hash = Column(String(64), nullable=True, comment='分享密码哈希 (SHA256)')
    has_password = Column(Boolean, default=False, comment='是否有密码保护')

    # 权限设置
    allow_download = Column(Boolean, default=True, comment='允许下载')
    allow_preview = Column(Boolean, default=True, comment='允许预览')

    # 有效期
    expire_at = Column(DateTime, nullable=True, comment='过期时间 (NULL=永不过期)')

    # 下载限制
    max_downloads = Column(Integer, nullable=True, comment='最大下载次数 (NULL=无限制)')
    download_count = Column(Integer, default=0, comment='已下载次数')
    view_count = Column(Integer, default=0, comment='已查看次数')

    # 创建者
    created_by_id = Column(Integer, nullable=False, comment='创建者用户ID')
    created_by_name = Column(String(100), nullable=True, comment='创建者用户名')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否有效')
    deactivated_at = Column(DateTime, nullable=True, comment='停用时间')
    deactivate_reason = Column(String(255), nullable=True, comment='停用原因')

    # 备注
    remark = Column(Text, nullable=True, comment='分享备注')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True, comment='最后访问时间')

    @property
    def is_expired(self):
        """检查分享链接是否已过期"""
        if not self.expire_at:
            return False
        return datetime.now() > self.expire_at

    @property
    def is_download_limit_reached(self):
        """检查是否已达到下载限制"""
        if self.max_downloads is None:
            return False
        return self.download_count >= self.max_downloads

    @property
    def is_valid(self):
        """检查分享链接是否有效"""
        if not self.is_active:
            return False
        if self.is_expired:
            return False
        return True

    def set_password(self, password):
        """设置分享密码"""
        if password:
            self.share_password_hash = hash_password(password)
            self.has_password = True
        else:
            self.share_password_hash = None
            self.has_password = False

    def check_password(self, password):
        """验证分享密码"""
        return verify_password(password, self.share_password_hash)

    def increment_download(self):
        """增加下载计数"""
        self.download_count += 1
        self.last_accessed_at = datetime.now()

    def increment_view(self):
        """增加查看计数"""
        self.view_count += 1
        self.last_accessed_at = datetime.now()

    def deactivate(self, reason=None):
        """停用分享链接"""
        self.is_active = False
        self.deactivated_at = datetime.now()
        self.deactivate_reason = reason

    def to_dict(self, include_file=False, file_info=None):
        """Convert to dictionary

        Args:
            include_file: 是否包含文件信息
            file_info: 预先查询的文件信息
        """
        result = {
            'id': self.id,
            'file_id': self.file_id,
            'share_code': self.share_code,
            'share_url': f'/share/{self.share_code}',
            'has_password': self.has_password,
            'allow_download': self.allow_download,
            'allow_preview': self.allow_preview,
            'expire_at': self.expire_at.isoformat() if self.expire_at else None,
            'max_downloads': self.max_downloads,
            'download_count': self.download_count,
            'view_count': self.view_count,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'is_download_limit_reached': self.is_download_limit_reached,
            'is_valid': self.is_valid,
            'created_by_id': self.created_by_id,
            'created_by_name': self.created_by_name,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
        }

        if include_file and file_info:
            result['file'] = file_info

        return result

    def to_public_dict(self):
        """转换为公开字典（不包含敏感信息）"""
        return {
            'share_code': self.share_code,
            'has_password': self.has_password,
            'allow_download': self.allow_download,
            'allow_preview': self.allow_preview,
            'is_valid': self.is_valid,
            'is_expired': self.is_expired,
            'is_download_limit_reached': self.is_download_limit_reached,
        }

    def __repr__(self):
        return f"<FileShareLink {self.share_code} (file_id={self.file_id})>"
