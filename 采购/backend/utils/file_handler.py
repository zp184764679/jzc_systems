# utils/file_handler.py
# -*- coding: utf-8 -*-
"""
文件处理工具 - 采购系统
使用共享文件存储工具
"""
import base64
import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加shared目录到路径
# __file__ 在 C:\Users\Admin\Desktop\采购\backend\utils\file_handler.py
# 需要往上3级到 Desktop，然后进入 shared
_desktop_path = Path(__file__).resolve().parent.parent.parent.parent  # Desktop
shared_path = str(_desktop_path / "shared")
storage_base_path = str(_desktop_path / "storage")

if shared_path not in sys.path:
    sys.path.insert(0, shared_path)

# 导入共享文件存储工具
try:
    from file_storage import FileStorage, ALLOWED_EXTENSIONS as SHARED_ALLOWED_EXTENSIONS
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

# 本地配置（兼容旧代码）
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def ensure_upload_folder():
    """确保上传文件夹存在"""
    Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """获取文件扩展名"""
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return 'bin'


def decode_base64_file(base64_string):
    """
    从Base64字符串解码文件

    返回: (bytes, 错误信息)
    """
    try:
        # 移除 data:image/png;base64, 等前缀
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        # 解码
        file_bytes = base64.b64decode(base64_string)

        # 检查文件大小
        if len(file_bytes) > MAX_FILE_SIZE:
            return None, f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024}MB)"

        if len(file_bytes) == 0:
            return None, "解码后的文件为空"

        return file_bytes, None

    except Exception as e:
        logger.error(f"Base64解码失败: {str(e)}")
        return None, f"Base64解码失败: {str(e)}"


def save_file(file_bytes, filename, file_type="attachments"):
    """
    保存文件到存储系统

    Args:
        file_bytes: 文件字节内容
        filename: 原始文件名
        file_type: 文件类型（invoices, contracts, attachments, rfq）

    返回: (文件路径, URL, 错误信息)
    """
    if USE_SHARED_STORAGE and _shared_storage:
        # 使用共享存储
        result = _shared_storage.save_file(
            file_bytes=file_bytes,
            original_filename=filename,
            system="caigou",
            file_type=file_type
        )

        if result["success"]:
            logger.info(f"文件已保存: {result['path']} -> {result['url']}")
            return result["path"], result["url"], None
        else:
            return None, None, result["error"]
    else:
        # 使用本地存储（兼容旧代码）
        return _save_file_local(file_bytes, filename)


def _save_file_local(file_bytes, filename):
    """本地存储（兼容旧代码）"""
    import uuid
    from datetime import datetime

    try:
        # 确保年月文件夹存在
        now = datetime.now()
        year = now.strftime('%Y')
        month = now.strftime('%m')
        folder_path = os.path.join(UPLOAD_FOLDER, year, month)
        Path(folder_path).mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        ext = get_file_extension(filename)
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(folder_path, unique_filename)

        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        # 生成URL
        file_url = f"/uploads/{year}/{month}/{unique_filename}"

        logger.info(f"文件已保存(本地): {file_path} -> {file_url}")
        return file_path, file_url, None

    except Exception as e:
        logger.error(f"文件保存失败: {str(e)}")
        return None, None, f"文件保存失败: {str(e)}"


def save_file_to_disk(file_bytes, filename):
    """
    兼容旧接口：将文件字节保存到磁盘

    返回: (文件路径, URL, 错误信息)
    """
    return save_file(file_bytes, filename, file_type="attachments")


def process_base64_file(base64_string, filename, file_type="attachments"):
    """
    一键处理：Base64 → 解码 → 保存 → 返回URL

    Args:
        base64_string: Base64编码的文件内容
        filename: 原始文件名
        file_type: 文件类型（invoices, contracts, attachments）

    返回: (file_url, 错误信息)
    """
    # 检查文件类型
    if not allowed_file(filename):
        return None, f"不支持的文件类型。允许: {', '.join(ALLOWED_EXTENSIONS)}"

    # 解码
    file_bytes, decode_err = decode_base64_file(base64_string)
    if decode_err:
        return None, decode_err

    # 保存
    file_path, file_url, save_err = save_file(file_bytes, filename, file_type)
    if save_err:
        return None, save_err

    return file_url, None


def delete_file(file_path):
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


def get_storage_stats():
    """
    获取存储统计信息

    Returns:
        统计信息字典
    """
    if USE_SHARED_STORAGE and _shared_storage:
        return _shared_storage.get_storage_stats()
    else:
        return {"message": "使用本地存储，暂无统计功能"}


# 兼容旧代码的函数别名
def get_year_month_folder():
    """获取当前年月文件夹路径（兼容旧代码）"""
    from datetime import datetime
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    return os.path.join(UPLOAD_FOLDER, year, month)


def ensure_year_month_folder():
    """确保年月文件夹存在（兼容旧代码）"""
    folder_path = get_year_month_folder()
    Path(folder_path).mkdir(parents=True, exist_ok=True)
    return folder_path


def generate_unique_filename(original_filename):
    """生成唯一的文件名（兼容旧代码）"""
    import uuid
    ext = get_file_extension(original_filename)
    return f"{uuid.uuid4().hex}.{ext}"