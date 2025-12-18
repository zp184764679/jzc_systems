# shared/file_storage_v2.py
# -*- coding: utf-8 -*-
"""
企业级文件存储管理器 v2.0

存储结构:
    storage/
    ├── active/                           # 活跃文件
    │   └── {system}/{YYYY}/{MM}/{entity_type}/{entity_id}/
    │       ├── _meta.json                # 元数据索引
    │       ├── documents/
    │       ├── drawings/
    │       ├── contracts/
    │       └── versions/{file_id}/v1.0/
    ├── archive/                          # 归档文件
    │   └── {YYYY}/{system}/{entity_type}/{entity_id}.tar.gz
    ├── temp/                             # 临时文件
    │   └── {date}/{session_id}/
    └── quarantine/                       # 隔离区
        └── {date}/

特性:
    - 按实体组织文件（项目、供应商、员工等）
    - 完整版本控制
    - 元数据索引（_meta.json）
    - 自动归档
    - 临时文件管理
    - 访问控制级别
    - MD5/SHA256 校验
"""

import base64
import os
import uuid
import json
import logging
import hashlib
import shutil
import tarfile
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


# ============== 枚举定义 ==============

class AccessLevel(Enum):
    """访问控制级别"""
    PUBLIC = "public"           # 公开
    INTERNAL = "internal"       # 内部
    CONFIDENTIAL = "confidential"  # 机密
    SECRET = "secret"           # 绝密


class FileStatus(Enum):
    """文件状态"""
    ACTIVE = "active"           # 活跃
    ARCHIVED = "archived"       # 已归档
    DELETED = "deleted"         # 已删除
    QUARANTINE = "quarantine"   # 隔离中


class SystemCode(Enum):
    """系统代码"""
    PORTAL = "portal"
    CAIGOU = "caigou"
    QUOTATION = "quotation"
    HR = "hr"
    CRM = "crm"
    SCM = "scm"
    SHM = "shm"
    EAM = "eam"
    MES = "mes"
    ACCOUNT = "account"
    SHARED = "shared"


# ============== 配置定义 ==============

# 默认配置
DEFAULT_STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
URL_PREFIX = "/storage"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
TEMP_FILE_EXPIRE_DAYS = 7
QUARANTINE_EXPIRE_DAYS = 30

# 允许的文件扩展名（按类别）
ALLOWED_EXTENSIONS = {
    "documents": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv", "rtf"},
    "drawings": {"dwg", "dxf", "pdf", "png", "jpg", "jpeg", "svg", "ai", "psd"},
    "images": {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico"},
    "archives": {"zip", "rar", "7z", "tar", "gz"},
    "all": {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv",
            "jpg", "jpeg", "png", "gif", "bmp", "webp", "svg",
            "dwg", "dxf", "ai", "psd",
            "zip", "rar", "7z", "tar", "gz",
            "json", "xml", "html", "css", "js"}
}

# 实体类型定义
ENTITY_TYPES = {
    "portal": ["projects", "announcements", "documents"],
    "caigou": ["suppliers", "purchase_orders", "rfq", "contracts", "invoices"],
    "quotation": ["quotes", "drawings", "customers"],
    "hr": ["employees", "contracts", "training", "performance"],
    "crm": ["customers", "contacts", "opportunities"],
    "scm": ["inventory", "warehouses", "shipments"],
    "shm": ["shipments", "deliveries", "returns"],
    "eam": ["equipment", "maintenance", "inspections"],
    "mes": ["work_orders", "production", "quality"],
    "account": ["users", "roles", "settings"],
    "shared": ["templates", "logos", "exports"]
}

# 文件分类定义
FILE_CATEGORIES = [
    "documents",      # 文档
    "drawings",       # 图纸
    "contracts",      # 合同
    "invoices",       # 发票
    "photos",         # 照片
    "certificates",   # 证书/资质
    "reports",        # 报告
    "exports",        # 导出文件
    "attachments",    # 附件
    "versions"        # 历史版本
]


# ============== 数据类 ==============

@dataclass
class FileInfo:
    """文件信息"""
    id: str
    name: str
    stored_name: str
    path: str
    url: str
    category: str
    size: int
    mime_type: str
    md5: str
    sha256: str = None
    version: str = "1.0"
    is_latest: bool = True
    language: str = None
    translation_of_id: str = None
    access_level: str = "internal"
    tags: List[str] = None
    description: str = None
    uploaded_by: str = None
    uploaded_at: str = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EntityMeta:
    """实体元数据"""
    entity_id: str
    entity_type: str
    system: str
    created_at: str
    updated_at: str
    created_by: str = None
    total_files: int = 0
    total_size_bytes: int = 0
    files: List[Dict] = None
    version_history: Dict = None
    access_history: List[Dict] = None  # 文件操作历史

    def to_dict(self) -> Dict:
        data = asdict(self)
        if data['files'] is None:
            data['files'] = []
        if data['version_history'] is None:
            data['version_history'] = {}
        if data['access_history'] is None:
            data['access_history'] = []
        return data


# ============== 主类 ==============

class EnterpriseFileStorage:
    """企业级文件存储管理器"""

    def __init__(self, base_path: str = None, url_prefix: str = URL_PREFIX):
        """
        初始化存储管理器

        Args:
            base_path: 存储根目录
            url_prefix: URL 前缀
        """
        self.base_path = base_path or DEFAULT_STORAGE_PATH
        self.url_prefix = url_prefix
        self._init_storage_structure()

    def _init_storage_structure(self):
        """初始化存储目录结构"""
        dirs = [
            os.path.join(self.base_path, "active"),
            os.path.join(self.base_path, "archive"),
            os.path.join(self.base_path, "temp"),
            os.path.join(self.base_path, "quarantine")
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)

    # ============== 路径生成 ==============

    def _get_entity_path(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int = None,
        month: int = None
    ) -> str:
        """
        获取实体存储路径

        格式: active/{system}/{YYYY}/{MM}/{entity_type}/{entity_id}/
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        return os.path.join(
            self.base_path,
            "active",
            system,
            str(year),
            f"{month:02d}",
            entity_type,
            self._sanitize_entity_id(entity_id)
        )

    def _get_file_path(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        category: str,
        filename: str,
        year: int = None,
        month: int = None
    ) -> str:
        """获取文件完整路径"""
        entity_path = self._get_entity_path(system, entity_type, entity_id, year, month)
        return os.path.join(entity_path, category, filename)

    def _get_version_path(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        file_id: str,
        version: str,
        year: int = None,
        month: int = None
    ) -> str:
        """获取版本存储路径"""
        entity_path = self._get_entity_path(system, entity_type, entity_id, year, month)
        return os.path.join(entity_path, "versions", file_id, version)

    def _get_temp_path(self, session_id: str = None) -> str:
        """获取临时文件路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        session_id = session_id or uuid.uuid4().hex[:8]
        return os.path.join(self.base_path, "temp", date_str, session_id)

    def _get_quarantine_path(self) -> str:
        """获取隔离区路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.base_path, "quarantine", date_str)

    def _get_archive_path(self, system: str, entity_type: str, entity_id: str, year: int) -> str:
        """获取归档路径"""
        return os.path.join(
            self.base_path,
            "archive",
            str(year),
            system,
            entity_type,
            f"{self._sanitize_entity_id(entity_id)}.tar.gz"
        )

    # ============== 工具方法 ==============

    @staticmethod
    def _sanitize_entity_id(entity_id: str) -> str:
        """清理实体ID，移除不安全字符"""
        # 保留字母、数字、连字符、下划线
        return re.sub(r'[^a-zA-Z0-9\-_]', '_', str(entity_id))

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名"""
        # 移除路径分隔符和特殊字符
        name = os.path.basename(filename)
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        return name

    @staticmethod
    def _get_extension(filename: str) -> str:
        """获取文件扩展名"""
        if '.' in filename:
            return filename.rsplit('.', 1)[1].lower()
        return ''

    @staticmethod
    def _get_mime_type(filename: str) -> str:
        """获取 MIME 类型"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

    @staticmethod
    def _calculate_hash(file_bytes: bytes, algorithm: str = 'md5') -> str:
        """计算文件哈希"""
        if algorithm == 'md5':
            return hashlib.md5(file_bytes).hexdigest()
        elif algorithm == 'sha256':
            return hashlib.sha256(file_bytes).hexdigest()
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    def _generate_file_id(self) -> str:
        """生成文件唯一ID"""
        return uuid.uuid4().hex[:8]

    def _generate_stored_name(self, original_name: str, file_id: str = None) -> str:
        """
        生成存储文件名
        格式: {YYYYMMDD}_{file_id}_{original_name}.{ext}
        """
        file_id = file_id or self._generate_file_id()
        date_str = datetime.now().strftime("%Y%m%d")
        safe_name = self._sanitize_filename(original_name)

        # 分离扩展名
        if '.' in safe_name:
            name_part, ext = safe_name.rsplit('.', 1)
            # 限制文件名长度
            if len(name_part) > 50:
                name_part = name_part[:50]
            return f"{date_str}_{file_id}_{name_part}.{ext}"
        else:
            if len(safe_name) > 50:
                safe_name = safe_name[:50]
            return f"{date_str}_{file_id}_{safe_name}"

    def _validate_file(
        self,
        file_bytes: bytes,
        filename: str,
        category: str = None,
        max_size: int = None
    ) -> Tuple[bool, str]:
        """
        验证文件

        Returns:
            (is_valid, error_message)
        """
        # 检查文件大小
        file_size = len(file_bytes)
        max_size = max_size or MAX_FILE_SIZE

        if file_size == 0:
            return False, "文件内容为空"

        if file_size > max_size:
            return False, f"文件大小超过限制 ({max_size / 1024 / 1024:.1f}MB)"

        # 检查扩展名
        ext = self._get_extension(filename)
        if category and category in ALLOWED_EXTENSIONS:
            allowed = ALLOWED_EXTENSIONS[category]
        else:
            allowed = ALLOWED_EXTENSIONS['all']

        if ext and ext not in allowed:
            return False, f"不支持的文件类型: .{ext}"

        return True, ""

    # ============== 元数据管理 ==============

    def _get_meta_path(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int = None,
        month: int = None
    ) -> str:
        """获取元数据文件路径"""
        entity_path = self._get_entity_path(system, entity_type, entity_id, year, month)
        return os.path.join(entity_path, "_meta.json")

    def _load_meta(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int = None,
        month: int = None
    ) -> EntityMeta:
        """加载实体元数据"""
        meta_path = self._get_meta_path(system, entity_type, entity_id, year, month)

        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return EntityMeta(**data)
            except Exception as e:
                logger.warning(f"Failed to load meta: {e}")

        # 创建新的元数据
        now = datetime.now().isoformat()
        return EntityMeta(
            entity_id=entity_id,
            entity_type=entity_type,
            system=system,
            created_at=now,
            updated_at=now,
            files=[],
            version_history={}
        )

    def _save_meta(
        self,
        meta: EntityMeta,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int = None,
        month: int = None
    ):
        """保存实体元数据"""
        entity_path = self._get_entity_path(system, entity_type, entity_id, year, month)
        Path(entity_path).mkdir(parents=True, exist_ok=True)

        meta_path = os.path.join(entity_path, "_meta.json")
        meta.updated_at = datetime.now().isoformat()

        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta.to_dict(), f, ensure_ascii=False, indent=2)

    def _add_file_to_meta(
        self,
        meta: EntityMeta,
        file_info: FileInfo
    ) -> EntityMeta:
        """添加文件到元数据"""
        if meta.files is None:
            meta.files = []

        meta.files.append(file_info.to_dict())
        meta.total_files = len(meta.files)
        meta.total_size_bytes = sum(f.get('size', 0) for f in meta.files)

        return meta

    def _update_version_history(
        self,
        meta: EntityMeta,
        file_id: str,
        version: str
    ) -> EntityMeta:
        """更新版本历史"""
        if meta.version_history is None:
            meta.version_history = {}

        if file_id not in meta.version_history:
            meta.version_history[file_id] = {
                "current": version,
                "versions": [version]
            }
        else:
            meta.version_history[file_id]["current"] = version
            if version not in meta.version_history[file_id]["versions"]:
                meta.version_history[file_id]["versions"].append(version)

        return meta

    # ============== 核心操作 ==============

    def save_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        system: str,
        entity_type: str,
        entity_id: str,
        category: str = "documents",
        version: str = "1.0",
        language: str = None,
        access_level: str = "internal",
        tags: List[str] = None,
        description: str = None,
        uploaded_by: str = None,
        year: int = None,
        month: int = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        保存文件到存储系统

        Args:
            file_bytes: 文件字节内容
            original_filename: 原始文件名
            system: 系统代码 (portal, caigou, quotation, etc.)
            entity_type: 实体类型 (projects, suppliers, quotes, etc.)
            entity_id: 实体ID (PRJ-2025-0001, SUP-001, etc.)
            category: 文件分类 (documents, drawings, contracts, etc.)
            version: 版本号
            language: 语言 (zh, en, ja)
            access_level: 访问级别
            tags: 标签列表
            description: 文件描述
            uploaded_by: 上传者ID
            year: 指定年份（默认当前年）
            month: 指定月份（默认当前月）
            validate: 是否验证文件

        Returns:
            {
                "success": True/False,
                "file_id": "唯一文件ID",
                "path": "完整存储路径",
                "url": "访问URL",
                "stored_name": "存储文件名",
                "size": 文件大小,
                "md5": "MD5哈希",
                "error": "错误信息（如果有）"
            }
        """
        try:
            # 验证文件
            if validate:
                is_valid, error = self._validate_file(file_bytes, original_filename, category)
                if not is_valid:
                    return {"success": False, "error": error}

            # 生成文件信息
            file_id = self._generate_file_id()
            stored_name = self._generate_stored_name(original_filename, file_id)

            # 确定存储路径
            now = datetime.now()
            year = year or now.year
            month = month or now.month

            entity_path = self._get_entity_path(system, entity_type, entity_id, year, month)
            category_path = os.path.join(entity_path, category)
            Path(category_path).mkdir(parents=True, exist_ok=True)

            file_path = os.path.join(category_path, stored_name)

            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_bytes)

            # 计算哈希
            md5_hash = self._calculate_hash(file_bytes, 'md5')
            sha256_hash = self._calculate_hash(file_bytes, 'sha256')

            # 生成URL
            relative_path = os.path.relpath(file_path, os.path.join(self.base_path, "active"))
            file_url = f"{self.url_prefix}/active/{relative_path.replace(os.sep, '/')}"

            # 创建文件信息
            file_info = FileInfo(
                id=file_id,
                name=original_filename,
                stored_name=stored_name,
                path=f"{category}/{stored_name}",
                url=file_url,
                category=category,
                size=len(file_bytes),
                mime_type=self._get_mime_type(original_filename),
                md5=md5_hash,
                sha256=sha256_hash,
                version=version,
                is_latest=True,
                language=language,
                access_level=access_level,
                tags=tags or [],
                description=description,
                uploaded_by=uploaded_by,
                uploaded_at=now.isoformat()
            )

            # 更新元数据
            meta = self._load_meta(system, entity_type, entity_id, year, month)
            meta = self._add_file_to_meta(meta, file_info)
            self._save_meta(meta, system, entity_type, entity_id, year, month)

            logger.info(f"File saved: {file_path} ({len(file_bytes)} bytes)")

            return {
                "success": True,
                "file_id": file_id,
                "path": file_path,
                "url": file_url,
                "stored_name": stored_name,
                "original_name": original_filename,
                "size": len(file_bytes),
                "md5": md5_hash,
                "sha256": sha256_hash,
                "category": category,
                "entity_id": entity_id,
                "entity_type": entity_type,
                "system": system
            }

        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return {"success": False, "error": str(e)}

    def save_file_version(
        self,
        file_bytes: bytes,
        original_filename: str,
        system: str,
        entity_type: str,
        entity_id: str,
        file_id: str,
        new_version: str,
        version_note: str = None,
        uploaded_by: str = None,
        year: int = None,
        month: int = None
    ) -> Dict[str, Any]:
        """
        保存文件新版本

        Args:
            file_id: 原文件ID
            new_version: 新版本号 (如 "1.1", "2.0")
            version_note: 版本说明
        """
        try:
            now = datetime.now()
            year = year or now.year
            month = month or now.month

            # 获取版本存储路径
            version_path = self._get_version_path(
                system, entity_type, entity_id, file_id, new_version, year, month
            )
            Path(version_path).mkdir(parents=True, exist_ok=True)

            # 生成文件名
            stored_name = self._generate_stored_name(original_filename, file_id)
            file_path = os.path.join(version_path, stored_name)

            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_bytes)

            # 计算哈希
            md5_hash = self._calculate_hash(file_bytes, 'md5')

            # 生成URL
            relative_path = os.path.relpath(file_path, os.path.join(self.base_path, "active"))
            file_url = f"{self.url_prefix}/active/{relative_path.replace(os.sep, '/')}"

            # 更新元数据
            meta = self._load_meta(system, entity_type, entity_id, year, month)
            meta = self._update_version_history(meta, file_id, new_version)

            # 标记旧版本为非最新
            for f in meta.files:
                if f.get('id') == file_id:
                    f['is_latest'] = False

            # 添加新版本文件信息
            file_info = FileInfo(
                id=f"{file_id}_v{new_version}",
                name=original_filename,
                stored_name=stored_name,
                path=f"versions/{file_id}/{new_version}/{stored_name}",
                url=file_url,
                category="versions",
                size=len(file_bytes),
                mime_type=self._get_mime_type(original_filename),
                md5=md5_hash,
                version=new_version,
                is_latest=True,
                description=version_note,
                uploaded_by=uploaded_by,
                uploaded_at=now.isoformat()
            )
            meta = self._add_file_to_meta(meta, file_info)
            self._save_meta(meta, system, entity_type, entity_id, year, month)

            logger.info(f"File version saved: {file_path} (v{new_version})")

            return {
                "success": True,
                "file_id": file_id,
                "version": new_version,
                "path": file_path,
                "url": file_url,
                "md5": md5_hash
            }

        except Exception as e:
            logger.error(f"Failed to save file version: {e}")
            return {"success": False, "error": str(e)}

    def save_base64_file(
        self,
        base64_string: str,
        original_filename: str,
        **kwargs
    ) -> Dict[str, Any]:
        """保存 Base64 编码的文件"""
        try:
            # 移除 data: 前缀
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]

            file_bytes = base64.b64decode(base64_string)
            return self.save_file(file_bytes, original_filename, **kwargs)

        except Exception as e:
            logger.error(f"Failed to decode base64: {e}")
            return {"success": False, "error": f"Base64 解码失败: {e}"}

    def delete_file(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        file_id: str,
        soft_delete: bool = True,
        year: int = None,
        month: int = None
    ) -> Dict[str, Any]:
        """
        删除文件

        Args:
            soft_delete: 软删除（移动到隔离区）还是物理删除
        """
        try:
            meta = self._load_meta(system, entity_type, entity_id, year, month)

            # 查找文件
            file_info = None
            for f in meta.files or []:
                if f.get('id') == file_id:
                    file_info = f
                    break

            if not file_info:
                return {"success": False, "error": "文件不存在"}

            # 获取文件路径
            entity_path = self._get_entity_path(system, entity_type, entity_id, year, month)
            file_path = os.path.join(entity_path, file_info['path'])

            if not os.path.exists(file_path):
                return {"success": False, "error": "文件已被删除"}

            if soft_delete:
                # 移动到隔离区
                quarantine_path = self._get_quarantine_path()
                Path(quarantine_path).mkdir(parents=True, exist_ok=True)

                dest_path = os.path.join(quarantine_path, f"{file_id}_{os.path.basename(file_path)}")
                shutil.move(file_path, dest_path)
                logger.info(f"File moved to quarantine: {dest_path}")
            else:
                # 物理删除
                os.remove(file_path)
                logger.info(f"File deleted: {file_path}")

            # 从元数据中移除
            meta.files = [f for f in meta.files if f.get('id') != file_id]
            meta.total_files = len(meta.files)
            meta.total_size_bytes = sum(f.get('size', 0) for f in meta.files)
            self._save_meta(meta, system, entity_type, entity_id, year, month)

            return {"success": True, "file_id": file_id}

        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return {"success": False, "error": str(e)}

    def get_file(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        file_id: str,
        year: int = None,
        month: int = None
    ) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        meta = self._load_meta(system, entity_type, entity_id, year, month)

        for f in meta.files or []:
            if f.get('id') == file_id:
                entity_path = self._get_entity_path(system, entity_type, entity_id, year, month)
                full_path = os.path.join(entity_path, f['path'])

                return {
                    **f,
                    "full_path": full_path,
                    "exists": os.path.exists(full_path)
                }

        return None

    def list_files(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        category: str = None,
        year: int = None,
        month: int = None
    ) -> List[Dict[str, Any]]:
        """列出实体的所有文件"""
        meta = self._load_meta(system, entity_type, entity_id, year, month)

        files = meta.files or []

        if category:
            files = [f for f in files if f.get('category') == category]

        return files

    def get_entity_meta(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int = None,
        month: int = None
    ) -> Dict[str, Any]:
        """获取实体元数据"""
        meta = self._load_meta(system, entity_type, entity_id, year, month)
        return meta.to_dict()

    # ============== 归档操作 ==============

    def archive_entity(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int,
        month: int = None
    ) -> Dict[str, Any]:
        """
        归档实体的所有文件

        将实体目录压缩为 tar.gz 并移动到 archive 目录
        """
        try:
            entity_path = self._get_entity_path(system, entity_type, entity_id, year, month)

            if not os.path.exists(entity_path):
                return {"success": False, "error": "实体目录不存在"}

            # 创建归档路径
            archive_path = self._get_archive_path(system, entity_type, entity_id, year)
            Path(os.path.dirname(archive_path)).mkdir(parents=True, exist_ok=True)

            # 创建压缩包
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(entity_path, arcname=os.path.basename(entity_path))

            # 删除原目录
            shutil.rmtree(entity_path)

            logger.info(f"Entity archived: {archive_path}")

            return {
                "success": True,
                "archive_path": archive_path,
                "archive_size": os.path.getsize(archive_path)
            }

        except Exception as e:
            logger.error(f"Failed to archive entity: {e}")
            return {"success": False, "error": str(e)}

    def restore_archive(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int
    ) -> Dict[str, Any]:
        """从归档恢复实体文件"""
        try:
            archive_path = self._get_archive_path(system, entity_type, entity_id, year)

            if not os.path.exists(archive_path):
                return {"success": False, "error": "归档文件不存在"}

            # 确定恢复路径
            restore_base = os.path.join(
                self.base_path,
                "active",
                system,
                str(year)
            )
            Path(restore_base).mkdir(parents=True, exist_ok=True)

            # 解压
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(restore_base)

            logger.info(f"Archive restored: {archive_path}")

            return {"success": True, "restored_path": restore_base}

        except Exception as e:
            logger.error(f"Failed to restore archive: {e}")
            return {"success": False, "error": str(e)}

    # ============== 清理操作 ==============

    def cleanup_temp_files(self, days: int = TEMP_FILE_EXPIRE_DAYS) -> Dict[str, Any]:
        """清理过期的临时文件"""
        temp_base = os.path.join(self.base_path, "temp")
        cutoff_date = datetime.now() - timedelta(days=days)

        deleted_count = 0
        deleted_size = 0

        if os.path.exists(temp_base):
            for date_dir in os.listdir(temp_base):
                date_path = os.path.join(temp_base, date_dir)

                try:
                    dir_date = datetime.strptime(date_dir, "%Y-%m-%d")
                    if dir_date < cutoff_date:
                        # 计算大小
                        for root, dirs, files in os.walk(date_path):
                            for f in files:
                                deleted_size += os.path.getsize(os.path.join(root, f))
                                deleted_count += 1

                        # 删除目录
                        shutil.rmtree(date_path)
                        logger.info(f"Deleted temp directory: {date_path}")

                except ValueError:
                    continue

        return {
            "deleted_files": deleted_count,
            "deleted_size": deleted_size
        }

    def cleanup_quarantine(self, days: int = QUARANTINE_EXPIRE_DAYS) -> Dict[str, Any]:
        """清理过期的隔离文件"""
        quarantine_base = os.path.join(self.base_path, "quarantine")
        cutoff_date = datetime.now() - timedelta(days=days)

        deleted_count = 0
        deleted_size = 0

        if os.path.exists(quarantine_base):
            for date_dir in os.listdir(quarantine_base):
                date_path = os.path.join(quarantine_base, date_dir)

                try:
                    dir_date = datetime.strptime(date_dir, "%Y-%m-%d")
                    if dir_date < cutoff_date:
                        for root, dirs, files in os.walk(date_path):
                            for f in files:
                                deleted_size += os.path.getsize(os.path.join(root, f))
                                deleted_count += 1

                        shutil.rmtree(date_path)
                        logger.info(f"Deleted quarantine directory: {date_path}")

                except ValueError:
                    continue

        return {
            "deleted_files": deleted_count,
            "deleted_size": deleted_size
        }

    # ============== 统计信息 ==============

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "by_system": {},
            "by_status": {
                "active": {"files": 0, "size": 0},
                "archived": {"files": 0, "size": 0},
                "temp": {"files": 0, "size": 0},
                "quarantine": {"files": 0, "size": 0}
            }
        }

        for status in ["active", "archive", "temp", "quarantine"]:
            status_path = os.path.join(self.base_path, status)
            if os.path.exists(status_path):
                for root, dirs, files in os.walk(status_path):
                    for f in files:
                        if f == "_meta.json":
                            continue

                        file_path = os.path.join(root, f)
                        file_size = os.path.getsize(file_path)

                        stats["total_files"] += 1
                        stats["total_size"] += file_size
                        stats["by_status"][status]["files"] += 1
                        stats["by_status"][status]["size"] += file_size

                        # 按系统统计
                        if status == "active":
                            parts = root.replace(status_path, "").strip(os.sep).split(os.sep)
                            if parts:
                                system = parts[0]
                                if system not in stats["by_system"]:
                                    stats["by_system"][system] = {"files": 0, "size": 0}
                                stats["by_system"][system]["files"] += 1
                                stats["by_system"][system]["size"] += file_size

        return stats


# ============== 全局实例 ==============

enterprise_storage = EnterpriseFileStorage()


# ============== 便捷函数 ==============

def save_file(
    file_bytes: bytes,
    original_filename: str,
    system: str,
    entity_type: str,
    entity_id: str,
    **kwargs
) -> Dict[str, Any]:
    """便捷函数：保存文件"""
    return enterprise_storage.save_file(
        file_bytes, original_filename, system, entity_type, entity_id, **kwargs
    )


def save_base64_file(
    base64_string: str,
    original_filename: str,
    system: str,
    entity_type: str,
    entity_id: str,
    **kwargs
) -> Dict[str, Any]:
    """便捷函数：保存 Base64 文件"""
    return enterprise_storage.save_base64_file(
        base64_string, original_filename,
        system=system, entity_type=entity_type, entity_id=entity_id, **kwargs
    )


def delete_file(
    system: str,
    entity_type: str,
    entity_id: str,
    file_id: str,
    **kwargs
) -> Dict[str, Any]:
    """便捷函数：删除文件"""
    return enterprise_storage.delete_file(system, entity_type, entity_id, file_id, **kwargs)


def get_file(
    system: str,
    entity_type: str,
    entity_id: str,
    file_id: str,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """便捷函数：获取文件"""
    return enterprise_storage.get_file(system, entity_type, entity_id, file_id, **kwargs)


def list_files(
    system: str,
    entity_type: str,
    entity_id: str,
    **kwargs
) -> List[Dict[str, Any]]:
    """便捷函数：列出文件"""
    return enterprise_storage.list_files(system, entity_type, entity_id, **kwargs)


# ============================================================
# 文件操作日志管理
# ============================================================

class FileActionType(Enum):
    """文件操作类型"""
    UPLOAD = "upload"           # 上传
    DOWNLOAD = "download"       # 下载
    VIEW = "view"               # 预览
    UPDATE = "update"           # 更新
    DELETE = "delete"           # 删除
    RESTORE = "restore"         # 恢复
    SHARE = "share"             # 分享
    ARCHIVE = "archive"         # 归档
    VERSION = "version"         # 新版本
    RENAME = "rename"           # 重命名
    MOVE = "move"               # 移动


@dataclass
class FileAccessRecord:
    """文件访问记录"""
    id: str
    file_id: str
    action_type: str
    user_id: int = None
    username: str = None
    ip_address: str = None
    user_agent: str = None
    action_time: str = None
    details: Dict = None

    def to_dict(self) -> Dict:
        return asdict(self)


class FileAccessLogger:
    """
    文件操作日志记录器

    日志存储在两个位置:
    1. 实体的 _meta.json 文件中 (access_history 字段)
    2. 数据库 file_access_log 表 (如果有数据库连接)
    """

    def __init__(self, storage: EnterpriseFileStorage, db_session=None):
        """
        初始化日志记录器

        Args:
            storage: 企业级存储管理器实例
            db_session: 数据库会话 (可选)
        """
        self.storage = storage
        self.db_session = db_session

    def log_action(
        self,
        file_id: str,
        action_type: str,
        system: str = None,
        entity_type: str = None,
        entity_id: str = None,
        user_id: int = None,
        username: str = None,
        ip_address: str = None,
        user_agent: str = None,
        details: Dict = None,
        year: int = None,
        month: int = None
    ) -> Dict[str, Any]:
        """
        记录文件操作日志

        Args:
            file_id: 文件ID
            action_type: 操作类型 (upload/download/view/update/delete/restore/share/archive/version)
            system: 系统代码
            entity_type: 实体类型
            entity_id: 实体ID
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            user_agent: 用户代理
            details: 详细信息 (如版本变更)
            year: 年份
            month: 月份

        Returns:
            {"success": True, "record_id": "xxx"}
        """
        try:
            record_id = uuid.uuid4().hex[:12]
            action_time = datetime.now().isoformat()

            record = FileAccessRecord(
                id=record_id,
                file_id=file_id,
                action_type=action_type,
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                action_time=action_time,
                details=details or {}
            )

            # 1. 写入实体的 _meta.json
            if system and entity_type and entity_id:
                self._log_to_meta(record, system, entity_type, entity_id, year, month)

            # 2. 写入数据库 (如果有)
            if self.db_session:
                self._log_to_database(record)

            logger.info(f"File action logged: {action_type} on {file_id} by {username or user_id}")

            return {"success": True, "record_id": record_id}

        except Exception as e:
            logger.error(f"Failed to log file action: {e}")
            return {"success": False, "error": str(e)}

    def _log_to_meta(
        self,
        record: FileAccessRecord,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int = None,
        month: int = None
    ):
        """写入实体元数据文件"""
        meta = self.storage._load_meta(system, entity_type, entity_id, year, month)

        # 初始化 access_history
        if not hasattr(meta, 'access_history') or meta.access_history is None:
            meta.access_history = []

        # 添加记录 (保留最近 100 条)
        meta.access_history.insert(0, record.to_dict())
        if len(meta.access_history) > 100:
            meta.access_history = meta.access_history[:100]

        # 保存
        self.storage._save_meta(meta, system, entity_type, entity_id, year, month)

    def _log_to_database(self, record: FileAccessRecord):
        """写入数据库表"""
        try:
            # 需要 file_access_log 表
            # INSERT INTO file_access_log (file_id, action_type, user_id, ip_address, ...)
            # 这里依赖外部数据库模型
            pass
        except Exception as e:
            logger.warning(f"Failed to log to database: {e}")

    def get_file_history(
        self,
        file_id: str,
        system: str = None,
        entity_type: str = None,
        entity_id: str = None,
        year: int = None,
        month: int = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取文件操作历史

        Args:
            file_id: 文件ID
            system: 系统代码
            entity_type: 实体类型
            entity_id: 实体ID
            limit: 返回记录数量限制

        Returns:
            操作记录列表
        """
        try:
            if not (system and entity_type and entity_id):
                return []

            meta = self.storage._load_meta(system, entity_type, entity_id, year, month)
            access_history = getattr(meta, 'access_history', []) or []

            # 过滤指定文件的记录
            file_records = [
                r for r in access_history
                if r.get('file_id') == file_id
            ]

            return file_records[:limit]

        except Exception as e:
            logger.error(f"Failed to get file history: {e}")
            return []

    def get_entity_history(
        self,
        system: str,
        entity_type: str,
        entity_id: str,
        year: int = None,
        month: int = None,
        action_type: str = None,
        user_id: int = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取实体下所有文件的操作历史

        Args:
            system: 系统代码
            entity_type: 实体类型
            entity_id: 实体ID
            action_type: 过滤操作类型
            user_id: 过滤用户ID
            limit: 返回记录数量限制

        Returns:
            操作记录列表
        """
        try:
            meta = self.storage._load_meta(system, entity_type, entity_id, year, month)
            access_history = getattr(meta, 'access_history', []) or []

            # 过滤
            records = access_history
            if action_type:
                records = [r for r in records if r.get('action_type') == action_type]
            if user_id:
                records = [r for r in records if r.get('user_id') == user_id]

            return records[:limit]

        except Exception as e:
            logger.error(f"Failed to get entity history: {e}")
            return []


# 创建全局日志记录器实例
file_access_logger = FileAccessLogger(enterprise_storage)


def log_file_action(
    file_id: str,
    action_type: str,
    **kwargs
) -> Dict[str, Any]:
    """便捷函数：记录文件操作"""
    return file_access_logger.log_action(file_id, action_type, **kwargs)


def get_file_history(
    file_id: str,
    **kwargs
) -> List[Dict]:
    """便捷函数：获取文件历史"""
    return file_access_logger.get_file_history(file_id, **kwargs)
