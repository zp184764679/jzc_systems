# utils/file_handler.py
# -*- coding: utf-8 -*-
"""
文件处理工具 - 报价系统
使用共享文件存储工具
"""
import os
import sys
import uuid
import logging
from typing import Optional, Tuple, Dict, Any
from fastapi import UploadFile, HTTPException
from config.settings import settings

logger = logging.getLogger(__name__)

# 添加shared目录到路径
# __file__ 在 C:\Users\Admin\Desktop\报价\backend\utils\file_handler.py
# 需要往上3级到 Desktop，然后进入 shared
from pathlib import Path as _Path
_desktop_path = _Path(__file__).resolve().parent.parent.parent.parent  # Desktop
shared_path = str(_desktop_path / "shared")
storage_base_path = str(_desktop_path / "storage")

if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# 导入共享文件存储工具
try:
    from file_storage import FileStorage
    _shared_storage = FileStorage(
        base_path=storage_base_path,
        url_prefix="/storage"
    )
    USE_SHARED_STORAGE = True
    logger.info(f"共享存储模块已加载，存储路径: {storage_base_path}")
except ImportError as e:
    USE_SHARED_STORAGE = False
    _shared_storage = None
    logger.warning(f"共享存储模块未找到，使用本地存储。错误: {e}")


def validate_file_extension(filename: str) -> bool:
    """
    验证文件扩展名

    Args:
        filename: 文件名

    Returns:
        是否为允许的文件类型
    """
    ext = filename.split('.')[-1].lower()
    return ext in settings.ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """
    验证文件大小

    Args:
        file_size: 文件大小（字节）

    Returns:
        是否在允许的大小范围内
    """
    max_size_bytes = settings.MAX_UPLOAD_SIZE * 1024 * 1024  # MB转字节
    return file_size <= max_size_bytes


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一文件名

    Args:
        original_filename: 原始文件名

    Returns:
        唯一文件名
    """
    ext = original_filename.split('.')[-1].lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}"


async def save_upload_file(
    upload_file: UploadFile,
    subdir: str = "drawings"
) -> Tuple[str, str, int]:
    """
    保存上传的文件

    Args:
        upload_file: FastAPI UploadFile对象
        subdir: 子目录名称（drawings, quotes, exports）

    Returns:
        (文件路径, 原始文件名, 文件大小)

    Raises:
        HTTPException: 文件验证失败
    """
    # 验证文件扩展名
    if not validate_file_extension(upload_file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。允许的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # 读取文件内容
    contents = await upload_file.read()
    file_size = len(contents)

    # 验证文件大小
    if not validate_file_size(file_size):
        raise HTTPException(
            status_code=400,
            detail=f"文件太大。最大允许: {settings.MAX_UPLOAD_SIZE}MB"
        )

    if USE_SHARED_STORAGE and _shared_storage:
        # 使用共享存储
        result = _shared_storage.save_file(
            file_bytes=contents,
            original_filename=upload_file.filename,
            system="quotation",
            file_type=subdir
        )

        if result["success"]:
            logger.info(f"文件已保存: {result['path']} -> {result['url']}")
            return result["path"], upload_file.filename, file_size
        else:
            raise HTTPException(
                status_code=500,
                detail=f"文件保存失败: {result['error']}"
            )
    else:
        # 使用本地存储（兼容旧代码）
        return await _save_file_local(contents, upload_file.filename, subdir)


async def _save_file_local(
    contents: bytes,
    original_filename: str,
    subdir: str
) -> Tuple[str, str, int]:
    """本地存储（兼容旧代码）"""
    # 生成唯一文件名
    unique_filename = generate_unique_filename(original_filename)

    # 确保子目录存在
    save_dir = os.path.join(settings.UPLOAD_DIR, subdir)
    os.makedirs(save_dir, exist_ok=True)

    # 保存文件
    file_path = os.path.join(save_dir, unique_filename)

    try:
        with open(file_path, "wb") as f:
            f.write(contents)

        return file_path, original_filename, len(contents)

    except Exception as e:
        # 如果保存失败，清理可能创建的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"文件保存失败: {str(e)}"
        )


def save_file_sync(
    file_bytes: bytes,
    original_filename: str,
    file_type: str = "drawings"
) -> Dict[str, Any]:
    """
    同步保存文件（用于非异步场景）

    Args:
        file_bytes: 文件字节内容
        original_filename: 原始文件名
        file_type: 文件类型（drawings, quotes, exports）

    Returns:
        {
            "success": True/False,
            "path": 文件路径,
            "url": 访问URL,
            "error": 错误信息
        }
    """
    if USE_SHARED_STORAGE and _shared_storage:
        return _shared_storage.save_file(
            file_bytes=file_bytes,
            original_filename=original_filename,
            system="quotation",
            file_type=file_type
        )
    else:
        # 本地存储
        try:
            unique_filename = generate_unique_filename(original_filename)
            save_dir = os.path.join(settings.UPLOAD_DIR, file_type)
            os.makedirs(save_dir, exist_ok=True)

            file_path = os.path.join(save_dir, unique_filename)

            with open(file_path, "wb") as f:
                f.write(file_bytes)

            return {
                "success": True,
                "path": file_path,
                "url": f"/uploads/{file_type}/{unique_filename}",
                "filename": unique_filename
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def delete_file(file_path: str) -> bool:
    """
    删除文件

    Args:
        file_path: 文件路径

    Returns:
        是否删除成功
    """
    if USE_SHARED_STORAGE and _shared_storage:
        return _shared_storage.delete_file(file_path)
    else:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False


def get_file_type(filename: str) -> str:
    """
    获取文件类型

    Args:
        filename: 文件名

    Returns:
        文件类型
    """
    ext = filename.split('.')[-1].lower()

    if ext == 'pdf':
        return 'pdf'
    elif ext in ['png', 'jpg', 'jpeg']:
        return 'image'
    else:
        return 'unknown'


def get_storage_stats() -> Dict[str, Any]:
    """
    获取存储统计信息

    Returns:
        统计信息字典
    """
    if USE_SHARED_STORAGE and _shared_storage:
        return _shared_storage.get_storage_stats()
    else:
        return {"message": "使用本地存储，暂无统计功能"}
