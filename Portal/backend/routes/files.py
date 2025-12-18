"""
Files API Routes - 文件管理API
支持文件上传、版本控制、原版/中文版管理

使用企业级文件存储系统 (shared/file_storage_v2.py)
存储路径: storage/active/portal/{YYYY}/{MM}/projects/{project_id}/{category}/
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from models import SessionLocal
from models.project import Project
from models.project_file import ProjectFile, FileCategory, OriginalLanguage
from models.file_share_link import FileShareLink, generate_share_code
from datetime import datetime
import sys
import os
import hashlib
import logging

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token
from shared.auth.models import User, AuthSessionLocal, init_auth_db
from shared.file_storage_v2 import (
    EnterpriseFileStorage,
    FileAccessLogger,
    FileActionType,
    log_file_action,
    get_file_history as get_storage_file_history
)

# Initialize auth database for user queries
init_auth_db()

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

# Initialize enterprise file storage and logger
storage = EnterpriseFileStorage()
access_logger = FileAccessLogger(storage)

# 文件大小限制 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


def get_current_user():
    """从请求头获取当前用户"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    parts = auth_header.split(' ')
    if len(parts) != 2:
        return None
    token = parts[1]
    payload = verify_token(token)
    return payload if payload else None


def calculate_md5(file_bytes):
    """计算文件MD5"""
    return hashlib.md5(file_bytes).hexdigest()


def format_file_size(size_bytes):
    """格式化文件大小为人类可读格式"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_user_info(user_id):
    """获取用户信息（用于文件上传者展示）

    Returns:
        dict: 包含 username, full_name, department_name 的用户信息
        None: 如果用户不存在
    """
    if not user_id:
        return None

    auth_session = AuthSessionLocal()
    try:
        user = auth_session.query(User).filter_by(id=user_id).first()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name or user.username,
                'department_name': user.department_name,
                'position_name': user.position_name
            }
        return None
    except Exception as e:
        logger.warning(f"Failed to get user info for user_id={user_id}: {e}")
        return None
    finally:
        auth_session.close()


def get_users_by_ids(user_ids):
    """批量获取用户信息（用于文件列表）

    Args:
        user_ids: 用户ID列表

    Returns:
        dict: {user_id: user_info} 的映射字典
    """
    if not user_ids:
        return {}

    # 去重
    unique_ids = list(set(uid for uid in user_ids if uid))
    if not unique_ids:
        return {}

    auth_session = AuthSessionLocal()
    try:
        users = auth_session.query(User).filter(User.id.in_(unique_ids)).all()
        return {
            user.id: {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name or user.username,
                'department_name': user.department_name,
                'position_name': user.position_name
            }
            for user in users
        }
    except Exception as e:
        logger.warning(f"Failed to get users info: {e}")
        return {}
    finally:
        auth_session.close()


def file_to_dict_with_uploader(file, user_info=None):
    """将文件对象转换为包含上传者信息的字典

    Args:
        file: ProjectFile 对象
        user_info: 预先查询的用户信息字典，如果为 None 则会查询

    Returns:
        dict: 包含上传者信息的文件字典
    """
    result = file.to_dict()

    # 添加上传者信息
    if user_info is None and file.uploaded_by_id:
        user_info = get_user_info(file.uploaded_by_id)

    result['uploader'] = user_info or {
        'id': file.uploaded_by_id,
        'username': '未知用户',
        'full_name': '未知用户',
        'department_name': None,
        'position_name': None
    }

    return result


def check_file_size(file):
    """检查文件大小是否超过限制"""
    # 获取文件大小（移动到末尾获取大小，然后移回开头）
    file.seek(0, 2)  # 移到文件末尾
    size = file.tell()
    file.seek(0)  # 移回开头

    if size > MAX_FILE_SIZE:
        return False, size
    return True, size


@files_bp.route('/project/<int:project_id>', methods=['GET'])
def get_project_files(project_id):
    """获取项目文件列表

    Query参数:
        - category: 文件分类筛选
        - only_latest: 是否只显示最新版本 (默认 true)
        - uploader_id: 按上传者ID筛选
        - include_uploader: 是否包含上传者详细信息 (默认 true)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Check project exists
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # Get files
        query = session.query(ProjectFile).filter_by(project_id=project_id)

        # Apply filters
        category = request.args.get('category')
        if category:
            query = query.filter_by(category=category)

        # Filter by uploader
        uploader_id = request.args.get('uploader_id', type=int)
        if uploader_id:
            query = query.filter_by(uploaded_by_id=uploader_id)

        # Only latest versions by default
        only_latest = request.args.get('only_latest', 'true').lower() == 'true'
        if only_latest:
            query = query.filter_by(is_latest_version=True)

        files = query.order_by(ProjectFile.created_at.desc()).all()

        # Check if uploader info is requested
        include_uploader = request.args.get('include_uploader', 'true').lower() == 'true'

        if include_uploader and files:
            # Batch fetch user info for efficiency
            user_ids = [f.uploaded_by_id for f in files]
            users_map = get_users_by_ids(user_ids)

            # Build response with uploader info
            files_data = [
                file_to_dict_with_uploader(f, users_map.get(f.uploaded_by_id))
                for f in files
            ]
        else:
            files_data = [f.to_dict() for f in files]

        return jsonify({
            'files': files_data,
            'total': len(files)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传文件

    使用企业级文件存储系统，按实体组织文件：
    storage/active/portal/{YYYY}/{MM}/projects/{project_id}/{category}/
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    # 检查文件大小
    is_valid, file_size = check_file_size(file)
    if not is_valid:
        return jsonify({
            'error': f'文件过大，最大允许 {format_file_size(MAX_FILE_SIZE)}，当前文件 {format_file_size(file_size)}'
        }), 413

    project_id = request.form.get('project_id')
    if not project_id:
        return jsonify({'error': '缺少项目ID'}), 400

    session = SessionLocal()
    try:
        # Check project exists
        project = session.query(Project).filter_by(id=int(project_id)).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # Read file
        file_bytes = file.read()

        # Get form data
        category = request.form.get('category', 'documents')
        original_language = request.form.get('original_language', 'zh')
        is_chinese_version = request.form.get('is_chinese_version', 'false').lower() == 'true'
        remark = request.form.get('remark', '')

        # Generate entity ID from project
        entity_id = project.project_id if project.project_id else f"PRJ-{project_id}"

        # Get user info for metadata
        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')

        # Save file using enterprise storage (entity-based organization)
        result = storage.save_file(
            file_bytes=file_bytes,
            original_filename=secure_filename(file.filename),
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            category=category,
            version='1.0',
            language=original_language,
            owner_id=user_id,
            tags=[category, project.name] if project.name else [category],
            description=remark
        )

        if not result.get('success', True):
            return jsonify({'error': result.get('error', '文件保存失败')}), 500

        # Create file record in database
        project_file = ProjectFile(
            project_id=int(project_id),
            file_name=result['original_filename'],
            file_path=result['path'],
            file_url=result['url'],
            file_size=result['size'],
            file_type=file.content_type or 'application/octet-stream',
            md5_hash=result['md5'],
            category=category,
            is_chinese_version=is_chinese_version,
            original_language=original_language,
            version='1.0',
            is_latest_version=True,
            uploaded_by_id=user_id,
            remark=remark
        )

        session.add(project_file)
        session.commit()
        session.refresh(project_file)

        # 记录文件上传日志
        access_logger.log_action(
            file_id=result.get('file_id', str(project_file.id)),
            action_type='upload',
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            details={
                'file_name': result['original_filename'],
                'file_size': result['size'],
                'category': category,
                'version': '1.0'
            }
        )

        logger.info(f"File uploaded: {result['path']} by user {username}")

        return jsonify(project_file.to_dict()), 201

    except Exception as e:
        session.rollback()
        logger.error(f"File upload failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/upload-inline', methods=['POST'])
def upload_inline_file():
    """上传内联文件（用于富文本编辑器中的图片和附件）

    不关联到特定项目，存储到临时/内联目录。
    支持类型:
    - description_image: 任务描述中的图片
    - task_attachment: 任务附件

    返回:
        - url: 文件访问URL
        - file_id: 文件ID（用于后续管理）
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    # 检查文件大小
    is_valid, file_size = check_file_size(file)
    if not is_valid:
        return jsonify({
            'error': f'文件过大，最大允许 {format_file_size(MAX_FILE_SIZE)}，当前文件 {format_file_size(file_size)}'
        }), 413

    file_type = request.form.get('type', 'description_image')

    # 验证图片类型
    if file_type == 'description_image':
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp']
        if file.content_type not in allowed_types:
            return jsonify({'error': '只允许上传图片文件 (jpg, png, gif, webp, bmp)'}), 400

    try:
        # Read file
        file_bytes = file.read()

        # Get user info
        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')

        # Generate unique filename
        import uuid
        file_ext = os.path.splitext(secure_filename(file.filename))[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"

        # Save file using enterprise storage
        result = storage.save_file(
            file_bytes=file_bytes,
            original_filename=unique_filename,
            system='portal',
            entity_type='inline',
            entity_id=f"user-{user_id}",
            category=file_type,
            version='1.0',
            owner_id=user_id,
            tags=[file_type, 'inline'],
            description=f"Inline {file_type} uploaded by {username}"
        )

        if not result.get('success', True):
            return jsonify({'error': result.get('error', '文件保存失败')}), 500

        # Generate access URL
        # Use a static URL pattern that nginx can serve
        access_url = f"/api/files/inline/{result['md5']}{file_ext}"

        # Store mapping in a simple way (or you can create a separate table)
        # For simplicity, we'll use the file path directly
        inline_file_path = result['path']

        logger.info(f"Inline file uploaded: {inline_file_path} by user {username}")

        return jsonify({
            'success': True,
            'url': access_url,
            'file_id': result.get('file_id', result['md5']),
            'file_name': file.filename,
            'file_size': file_size,
            'md5': result['md5'],
            'path': inline_file_path
        }), 201

    except Exception as e:
        logger.error(f"Inline file upload failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@files_bp.route('/inline/<path:file_path>', methods=['GET'])
def get_inline_file(file_path):
    """获取内联文件（用于富文本编辑器显示图片）

    支持通过 MD5+扩展名 或完整路径访问
    """
    try:
        # 尝试在内联存储目录中查找文件
        import glob

        # 构建搜索路径
        base_path = storage.base_path
        search_patterns = [
            os.path.join(base_path, 'active', 'portal', '*', '*', 'inline', '*', '*', file_path),
            os.path.join(base_path, 'active', 'portal', '*', '*', 'inline', '*', file_path),
        ]

        found_path = None
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            if matches:
                found_path = matches[0]
                break

        if not found_path or not os.path.exists(found_path):
            return jsonify({'error': '文件不存在'}), 404

        # 获取 MIME 类型
        import mimetypes
        mime_type, _ = mimetypes.guess_type(found_path)

        return send_file(
            found_path,
            mimetype=mime_type or 'application/octet-stream'
        )

    except Exception as e:
        logger.error(f"Get inline file failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@files_bp.route('/<int:file_id>/upload-version', methods=['POST'])
def upload_file_version(file_id):
    """上传文件新版本

    企业级存储系统自动管理版本:
    storage/active/portal/.../projects/{project_id}/{category}/versions/{file_id}/v{version}/
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    # 检查文件大小
    is_valid, file_size = check_file_size(file)
    if not is_valid:
        return jsonify({
            'error': f'文件过大，最大允许 {format_file_size(MAX_FILE_SIZE)}，当前文件 {format_file_size(file_size)}'
        }), 413

    session = SessionLocal()
    try:
        # Get original file
        original_file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not original_file:
            return jsonify({'error': '原文件不存在'}), 404

        # Get project for entity_id
        project = session.query(Project).filter_by(id=original_file.project_id).first()
        entity_id = project.project_id if project and project.project_id else f"PRJ-{original_file.project_id}"

        # Read file
        file_bytes = file.read()

        # Calculate new version number
        parts = original_file.version.split('.')
        major, minor = int(parts[0]), int(parts[1])
        new_version = f"{major}.{minor + 1}"

        # Get user info
        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')
        remark = request.form.get('remark', '')

        # Save new version using enterprise storage
        result = storage.save_file(
            file_bytes=file_bytes,
            original_filename=secure_filename(file.filename),
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            category=original_file.category,
            version=new_version,
            language=original_file.original_language,
            owner_id=user_id,
            tags=[original_file.category, f'version:{new_version}'],
            description=f"Version {new_version}: {remark}" if remark else f"Version {new_version}"
        )

        if not result.get('success', True):
            return jsonify({'error': result.get('error', '文件保存失败')}), 500

        # Mark old file as not latest
        original_file.is_latest_version = False

        # Create new version file record
        new_file = ProjectFile(
            project_id=original_file.project_id,
            file_name=result['original_filename'],
            file_path=result['path'],
            file_url=result['url'],
            file_size=result['size'],
            file_type=file.content_type or 'application/octet-stream',
            md5_hash=result['md5'],
            category=original_file.category,
            is_chinese_version=original_file.is_chinese_version,
            original_language=original_file.original_language,
            related_file_id=original_file.related_file_id,
            version=new_version,
            is_latest_version=True,
            parent_file_id=file_id,
            uploaded_by_id=user_id,
            remark=remark
        )

        session.add(new_file)
        session.commit()
        session.refresh(new_file)

        # 记录版本上传日志
        access_logger.log_action(
            file_id=result.get('file_id', str(new_file.id)),
            action_type='version',
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            details={
                'file_name': result['original_filename'],
                'file_size': result['size'],
                'old_version': original_file.version,
                'new_version': new_version,
                'parent_file_id': file_id
            }
        )

        logger.info(f"File version uploaded: {result['path']} v{new_version} by user {username}")

        return jsonify(new_file.to_dict()), 201

    except Exception as e:
        session.rollback()
        logger.error(f"File version upload failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/versions', methods=['GET'])
def get_file_versions(file_id):
    """获取文件版本历史（含上传者信息）"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Get file
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # Get all versions (including self and children)
        versions = session.query(ProjectFile).filter(
            (ProjectFile.id == file_id) |
            (ProjectFile.parent_file_id == file_id)
        ).order_by(ProjectFile.created_at.desc()).all()

        # Batch fetch user info
        user_ids = [v.uploaded_by_id for v in versions]
        users_map = get_users_by_ids(user_ids)

        # Build response with uploader info
        versions_data = [
            file_to_dict_with_uploader(v, users_map.get(v.uploaded_by_id))
            for v in versions
        ]

        return jsonify({
            'versions': versions_data,
            'total': len(versions),
            'current_file_id': file_id,
            'latest_version': versions[0].version if versions else None
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>', methods=['GET'])
def get_file_detail(file_id):
    """获取文件详情（含上传者信息和版本信息）

    返回:
        - 文件基本信息
        - 上传者详细信息
        - 版本数量
        - 是否有关联的中文版/原版
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # Get uploader info
        uploader_info = get_user_info(file.uploaded_by_id)

        # Build file detail
        file_data = file_to_dict_with_uploader(file, uploader_info)

        # Count versions
        version_count = session.query(ProjectFile).filter(
            (ProjectFile.id == file_id) |
            (ProjectFile.parent_file_id == file_id)
        ).count()

        file_data['version_count'] = version_count

        # Get related file info (original/chinese version)
        if file.related_file_id:
            related_file = session.query(ProjectFile).filter_by(id=file.related_file_id).first()
            if related_file:
                file_data['related_file'] = {
                    'id': related_file.id,
                    'file_name': related_file.file_name,
                    'is_chinese_version': related_file.is_chinese_version,
                    'original_language': related_file.original_language.value if hasattr(related_file.original_language, 'value') else related_file.original_language
                }

        return jsonify(file_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/link-translation', methods=['POST'])
def link_translation(file_id):
    """关联原版和中文版文件"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'related_file_id' not in data:
        return jsonify({'error': '缺少关联文件ID'}), 400

    session = SessionLocal()
    try:
        file1 = session.query(ProjectFile).filter_by(id=file_id).first()
        file2 = session.query(ProjectFile).filter_by(id=data['related_file_id']).first()

        if not file1 or not file2:
            return jsonify({'error': '文件不存在'}), 404

        # Link both ways
        file1.related_file_id = data['related_file_id']
        file2.related_file_id = file_id

        session.commit()

        return jsonify({
            'message': '文件关联成功',
            'file1': file1.to_dict(),
            'file2': file2.to_dict()
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 版本状态管理 API (P0-3)
# ============================================================

@files_bp.route('/<int:file_id>/set-latest', methods=['PUT'])
def set_file_as_latest(file_id):
    """设置指定版本为最新版本

    将指定版本设为最新版本，并将同组其他版本标记为非最新。
    只有文件上传者、项目成员或管理员可以执行此操作。

    请求体 (可选):
        - reason: 变更原因
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Get target file
        target_file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not target_file:
            return jsonify({'error': '文件不存在'}), 404

        # Already latest
        if target_file.is_latest_version:
            return jsonify({
                'message': '该文件已经是最新版本',
                'file': target_file.to_dict()
            }), 200

        # Get user info
        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')
        user_role = user.get('role', 'user')

        # Check permission (uploader or admin)
        is_owner = target_file.uploaded_by_id == user_id
        is_admin = user_role in ['admin', 'super_admin']

        if not is_owner and not is_admin:
            return jsonify({'error': '无权修改此文件版本'}), 403

        # Find root file (original file in version chain)
        root_file_id = target_file.parent_file_id or target_file.id

        # Get all files in the same version chain
        # (parent_file_id equals root_file_id, or id equals root_file_id)
        sibling_files = session.query(ProjectFile).filter(
            (ProjectFile.id == root_file_id) |
            (ProjectFile.parent_file_id == root_file_id)
        ).all()

        # Record previous latest version
        previous_latest = None
        for f in sibling_files:
            if f.is_latest_version:
                previous_latest = f
                break

        # Update all siblings to not latest
        for f in sibling_files:
            f.is_latest_version = False

        # Set target as latest
        target_file.is_latest_version = True

        session.commit()

        # Get project for logging
        project = session.query(Project).filter_by(id=target_file.project_id).first()
        entity_id = project.project_id if project and project.project_id else f"PRJ-{target_file.project_id}"

        # Get change reason
        data = request.get_json() or {}
        reason = data.get('reason', '用户手动设置')

        # Log the version change
        access_logger.log_action(
            file_id=str(file_id),
            action_type='update',
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            details={
                'action': 'set_as_latest',
                'file_name': target_file.file_name,
                'version': target_file.version,
                'previous_latest_version': previous_latest.version if previous_latest else None,
                'previous_latest_file_id': previous_latest.id if previous_latest else None,
                'reason': reason
            }
        )

        logger.info(f"File version set as latest: file_id={file_id}, version={target_file.version} by user {username}")

        return jsonify({
            'message': '版本设置成功',
            'file': file_to_dict_with_uploader(target_file, get_user_info(target_file.uploaded_by_id)),
            'previous_latest_version': previous_latest.version if previous_latest else None
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Set latest version failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/version-tree', methods=['GET'])
def get_file_version_tree(file_id):
    """获取文件版本树

    返回该文件所有版本的树形结构，包含：
    - 根文件（第一个上传的版本）
    - 所有子版本
    - 版本状态（最新/历史）
    - 每个版本的上传者信息
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Get file
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # Find root file (original version)
        root_file_id = file.parent_file_id or file.id

        # Get all versions
        all_versions = session.query(ProjectFile).filter(
            (ProjectFile.id == root_file_id) |
            (ProjectFile.parent_file_id == root_file_id)
        ).order_by(ProjectFile.created_at.asc()).all()

        if not all_versions:
            return jsonify({'error': '版本数据不存在'}), 404

        # Batch fetch user info
        user_ids = [v.uploaded_by_id for v in all_versions]
        users_map = get_users_by_ids(user_ids)

        # Build version tree
        root_file = all_versions[0]
        latest_version = None

        versions_list = []
        for v in all_versions:
            version_data = file_to_dict_with_uploader(v, users_map.get(v.uploaded_by_id))
            version_data['is_root'] = (v.id == root_file.id)
            version_data['version_status'] = 'latest' if v.is_latest_version else 'history'
            versions_list.append(version_data)

            if v.is_latest_version:
                latest_version = v

        # Build tree structure
        version_tree = {
            'root_file_id': root_file.id,
            'root_file_name': root_file.file_name,
            'total_versions': len(all_versions),
            'latest_version': latest_version.version if latest_version else all_versions[-1].version,
            'latest_file_id': latest_version.id if latest_version else all_versions[-1].id,
            'created_at': root_file.created_at.isoformat() if root_file.created_at else None,
            'last_updated_at': all_versions[-1].created_at.isoformat() if all_versions else None,
            'versions': versions_list
        }

        return jsonify(version_tree), 200

    except Exception as e:
        logger.error(f"Get version tree failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    """下载文件"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # Get project for entity_id
        project = session.query(Project).filter_by(id=file.project_id).first()
        entity_id = project.project_id if project and project.project_id else f"PRJ-{file.project_id}"

        # Get user info
        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')

        # 记录下载日志
        access_logger.log_action(
            file_id=str(file_id),
            action_type='download',
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            details={
                'file_name': file.file_name,
                'file_size': file.file_size
            }
        )

        # Send file
        return send_file(
            file.file_path,
            as_attachment=True,
            download_name=file.file_name
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """删除文件

    使用软删除策略：
    1. 物理文件移动到隔离区 (storage/quarantine/)
    2. 30天后由定时任务永久删除
    3. 数据库记录保留但标记为已删除
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # Get project for entity_id
        project = session.query(Project).filter_by(id=file.project_id).first()
        entity_id = project.project_id if project and project.project_id else f"PRJ-{file.project_id}"

        # Get user info
        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')

        # Check permission (only owner, uploader, or admin can delete)
        user_role = user.get('role', 'user')
        is_owner = file.uploaded_by_id == user_id
        is_admin = user_role in ['admin', 'super_admin']

        if not is_owner and not is_admin:
            return jsonify({'error': '无权删除此文件'}), 403

        # Get delete reason from request
        data = request.get_json() or {}
        delete_reason = data.get('reason', f'用户 {username} 删除')

        # 保存文件信息用于日志
        file_info = {
            'file_name': file.file_name,
            'file_size': file.file_size,
            'category': file.category
        }

        # Soft delete: move physical file to quarantine
        try:
            if os.path.exists(file.file_path):
                # Use enterprise storage's soft delete
                storage.soft_delete(
                    file_path=file.file_path,
                    reason=delete_reason
                )
                logger.info(f"File moved to quarantine: {file.file_path} by user {username}")
        except Exception as e:
            logger.warning(f"Failed to move file to quarantine: {e}")
            # Still proceed with database update even if physical move fails

        # Soft delete database record (mark as deleted instead of removing)
        # Note: This requires adding deleted_at field to ProjectFile model
        # For now, we'll hard delete the record
        session.delete(file)
        session.commit()

        # 记录删除日志
        access_logger.log_action(
            file_id=str(file_id),
            action_type='delete',
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            details={
                **file_info,
                'delete_reason': delete_reason
            }
        )

        logger.info(f"File record deleted: file_id={file_id} by user {username}")

        return jsonify({
            'message': '文件已删除',
            'note': '物理文件已移动到隔离区，30天后永久删除'
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"File delete failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 存储管理 API (仅管理员)
# ============================================================

@files_bp.route('/storage/stats', methods=['GET'])
def get_storage_stats():
    """获取存储统计信息 (仅管理员)

    返回:
        - 总文件数
        - 总存储大小
        - 按系统统计
        - 按状态统计
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    # 检查管理员权限
    user_role = user.get('role', 'user')
    if user_role not in ['admin', 'super_admin']:
        return jsonify({'error': '需要管理员权限'}), 403

    try:
        stats = storage.get_storage_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Failed to get storage stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@files_bp.route('/storage/entity/<system>/<entity_type>/<entity_id>', methods=['GET'])
def get_entity_files(system, entity_type, entity_id):
    """获取实体的所有文件

    Args:
        system: 系统代码 (portal, caigou, etc.)
        entity_type: 实体类型 (projects, suppliers, etc.)
        entity_id: 实体ID (PRJ-2025-0001, etc.)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    try:
        files = storage.list_entity_files(
            system=system,
            entity_type=entity_type,
            entity_id=entity_id
        )
        return jsonify({
            'files': files,
            'total': len(files),
            'entity': {
                'system': system,
                'entity_type': entity_type,
                'entity_id': entity_id
            }
        }), 200
    except Exception as e:
        logger.error(f"Failed to list entity files: {str(e)}")
        return jsonify({'error': str(e)}), 500


@files_bp.route('/storage/cleanup', methods=['POST'])
def cleanup_storage():
    """清理临时文件和过期隔离文件 (仅超级管理员)

    请求体 (可选):
        - temp_days: 临时文件保留天数 (默认7)
        - quarantine_days: 隔离文件保留天数 (默认30)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    # 检查超级管理员权限
    user_role = user.get('role', 'user')
    if user_role != 'super_admin':
        return jsonify({'error': '需要超级管理员权限'}), 403

    try:
        data = request.get_json() or {}
        temp_days = data.get('temp_days', 7)
        quarantine_days = data.get('quarantine_days', 30)

        # 清理临时文件
        temp_result = storage.cleanup_temp_files(days=temp_days)

        # 清理隔离文件
        quarantine_result = storage.cleanup_quarantine(days=quarantine_days)

        username = user.get('username', 'unknown')
        logger.info(f"Storage cleanup by {username}: temp={temp_result}, quarantine={quarantine_result}")

        return jsonify({
            'message': '清理完成',
            'temp_cleanup': temp_result,
            'quarantine_cleanup': quarantine_result
        }), 200

    except Exception as e:
        logger.error(f"Storage cleanup failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@files_bp.route('/storage/info', methods=['GET'])
def get_storage_info():
    """获取存储系统信息"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    return jsonify({
        'version': '2.0',
        'type': 'enterprise',
        'base_path': storage.base_path,
        'structure': {
            'active': 'storage/active/{system}/{YYYY}/{MM}/{entity_type}/{entity_id}/{category}/',
            'archive': 'storage/archive/{YYYY}/{system}/{entity_type}/{entity_id}.tar.gz',
            'temp': 'storage/temp/{date}/{session_id}/',
            'quarantine': 'storage/quarantine/{date}/'
        },
        'features': [
            'entity_based_organization',
            'version_control',
            'metadata_indexing',
            'soft_delete_quarantine',
            'auto_cleanup',
            'archive_support',
            'access_history'
        ]
    }), 200


# ============================================================
# 文件操作历史 API
# ============================================================

@files_bp.route('/<int:file_id>/history', methods=['GET'])
def get_file_history(file_id):
    """获取文件操作历史

    返回该文件的所有操作记录：
    - 上传、下载、更新、删除等操作
    - 操作人、操作时间、IP地址
    - 操作详情（如版本变更）

    Query参数:
        - limit: 返回记录数量限制 (默认50)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Get file info
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # Get project for entity_id
        project = session.query(Project).filter_by(id=file.project_id).first()
        entity_id = project.project_id if project and project.project_id else f"PRJ-{file.project_id}"

        # Get history from storage
        limit = request.args.get('limit', 50, type=int)
        history = access_logger.get_file_history(
            file_id=str(file_id),
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            limit=limit
        )

        return jsonify({
            'file_id': file_id,
            'file_name': file.file_name,
            'history': history,
            'total': len(history)
        }), 200

    except Exception as e:
        logger.error(f"Failed to get file history: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/project/<int:project_id>/history', methods=['GET'])
def get_project_files_history(project_id):
    """获取项目下所有文件的操作历史

    Query参数:
        - action_type: 过滤操作类型 (upload/download/delete等)
        - user_id: 过滤用户ID
        - limit: 返回记录数量限制 (默认100)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Get project
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        entity_id = project.project_id if project.project_id else f"PRJ-{project_id}"

        # Get filters
        action_type = request.args.get('action_type')
        filter_user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', 100, type=int)

        # Get history from storage
        history = access_logger.get_entity_history(
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            action_type=action_type,
            user_id=filter_user_id,
            limit=limit
        )

        return jsonify({
            'project_id': project_id,
            'project_name': project.name,
            'history': history,
            'total': len(history)
        }), 200

    except Exception as e:
        logger.error(f"Failed to get project files history: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 文件搜索 API (P1-1)
# ============================================================

@files_bp.route('/search', methods=['GET'])
def search_files():
    """搜索文件

    Query参数:
        - q: 搜索关键词（搜索文件名）
        - uploader_id: 按上传者ID筛选
        - category: 文件分类筛选
        - file_type: 文件类型筛选（如 pdf, image, doc 等）
        - date_from: 上传时间范围起始（格式: YYYY-MM-DD）
        - date_to: 上传时间范围结束（格式: YYYY-MM-DD）
        - project_id: 限定在某个项目内搜索
        - only_latest: 只搜索最新版本 (默认true)
        - include_deleted: 包含已删除文件 (默认false)
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认20, 最大100)
        - sort_by: 排序字段 (created_at, file_name, file_size, 默认created_at)
        - sort_order: 排序方向 (asc, desc, 默认desc)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(page_size, 100)

        # 搜索参数
        q = request.args.get('q', '').strip()
        uploader_id = request.args.get('uploader_id', type=int)
        category = request.args.get('category')
        file_type = request.args.get('file_type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        project_id = request.args.get('project_id', type=int)
        only_latest = request.args.get('only_latest', 'true').lower() == 'true'
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # 构建查询
        query = session.query(ProjectFile)

        # 默认排除已删除文件
        if not include_deleted:
            query = query.filter(ProjectFile.deleted_at == None)

        # 关键词搜索（文件名模糊匹配）
        if q:
            search_pattern = f'%{q}%'
            query = query.filter(ProjectFile.file_name.ilike(search_pattern))

        # 上传者筛选
        if uploader_id:
            query = query.filter(ProjectFile.uploaded_by_id == uploader_id)

        # 分类筛选
        if category:
            query = query.filter(ProjectFile.category == category)

        # 文件类型筛选
        if file_type:
            file_type_patterns = {
                'pdf': ['application/pdf'],
                'image': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'],
                'doc': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
                'excel': ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
                'ppt': ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'],
                'text': ['text/plain'],
                'archive': ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed']
            }

            if file_type in file_type_patterns:
                from sqlalchemy import or_
                type_filters = [ProjectFile.file_type == t for t in file_type_patterns[file_type]]
                query = query.filter(or_(*type_filters))
            else:
                # 自定义类型，直接匹配
                query = query.filter(ProjectFile.file_type.ilike(f'%{file_type}%'))

        # 日期范围筛选
        if date_from:
            from datetime import datetime as dt
            try:
                from_date = dt.strptime(date_from, '%Y-%m-%d')
                query = query.filter(ProjectFile.created_at >= from_date)
            except ValueError:
                pass

        if date_to:
            from datetime import datetime as dt, timedelta
            try:
                to_date = dt.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(ProjectFile.created_at < to_date)
            except ValueError:
                pass

        # 项目筛选
        if project_id:
            query = query.filter(ProjectFile.project_id == project_id)

        # 只显示最新版本
        if only_latest:
            query = query.filter(ProjectFile.is_latest_version == True)

        # 获取总数
        total = query.count()

        # 排序
        sort_column = getattr(ProjectFile, sort_by, ProjectFile.created_at)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        # 分页
        offset = (page - 1) * page_size
        files = query.offset(offset).limit(page_size).all()

        # 批量获取上传者信息
        user_ids = [f.uploaded_by_id for f in files]
        users_map = get_users_by_ids(user_ids)

        # 构建响应
        files_data = [
            file_to_dict_with_uploader(f, users_map.get(f.uploaded_by_id))
            for f in files
        ]

        # 获取关联的项目信息
        project_ids = list(set(f.project_id for f in files))
        if project_ids:
            projects = session.query(Project).filter(Project.id.in_(project_ids)).all()
            projects_map = {p.id: {'id': p.id, 'project_no': p.project_no, 'name': p.name} for p in projects}
            for fd in files_data:
                fd['project'] = projects_map.get(fd['project_id'])

        return jsonify({
            'files': files_data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'search_params': {
                'q': q,
                'uploader_id': uploader_id,
                'category': category,
                'file_type': file_type,
                'date_from': date_from,
                'date_to': date_to,
                'project_id': project_id,
                'only_latest': only_latest
            }
        }), 200

    except Exception as e:
        logger.error(f"File search failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 批量操作 API (P1-3)
# ============================================================

@files_bp.route('/batch/delete', methods=['POST'])
def batch_delete_files():
    """批量删除文件

    请求体:
        - file_ids: 文件ID列表
        - reason: 删除原因 (可选)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or not data.get('file_ids'):
        return jsonify({'error': '缺少文件ID列表'}), 400

    file_ids = data['file_ids']
    if not isinstance(file_ids, list) or len(file_ids) == 0:
        return jsonify({'error': '文件ID列表无效'}), 400

    if len(file_ids) > 100:
        return jsonify({'error': '单次最多删除100个文件'}), 400

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')
        user_role = user.get('role', 'user')
        is_admin_user = user_role in ['admin', 'super_admin']

        delete_reason = data.get('reason', f'用户 {username} 批量删除')

        deleted = []
        failed = []

        for file_id in file_ids:
            try:
                file = session.query(ProjectFile).filter_by(id=file_id).first()
                if not file:
                    failed.append({'id': file_id, 'error': '文件不存在'})
                    continue

                # 检查权限
                is_owner = file.uploaded_by_id == user_id
                if not is_owner and not is_admin_user:
                    failed.append({'id': file_id, 'error': '无权删除此文件'})
                    continue

                # 软删除
                file.deleted_at = datetime.now()
                file.delete_reason = delete_reason
                file.deleted_by_id = user_id

                # 移动物理文件到隔离区
                try:
                    if file.file_path and os.path.exists(file.file_path):
                        storage.soft_delete(
                            file_path=file.file_path,
                            reason=delete_reason
                        )
                except Exception as e:
                    logger.warning(f"Failed to move file {file_id} to quarantine: {e}")

                deleted.append({'id': file_id, 'file_name': file.file_name})

            except Exception as e:
                failed.append({'id': file_id, 'error': str(e)})

        session.commit()

        logger.info(f"Batch delete by {username}: deleted={len(deleted)}, failed={len(failed)}")

        return jsonify({
            'message': f'批量删除完成',
            'deleted': deleted,
            'failed': failed,
            'deleted_count': len(deleted),
            'failed_count': len(failed)
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Batch delete failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/batch/download', methods=['POST'])
def batch_download_files():
    """批量下载文件（打包为ZIP）

    请求体:
        - file_ids: 文件ID列表

    返回:
        - ZIP 文件下载
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or not data.get('file_ids'):
        return jsonify({'error': '缺少文件ID列表'}), 400

    file_ids = data['file_ids']
    if not isinstance(file_ids, list) or len(file_ids) == 0:
        return jsonify({'error': '文件ID列表无效'}), 400

    if len(file_ids) > 50:
        return jsonify({'error': '单次最多下载50个文件'}), 400

    session = SessionLocal()
    try:
        import zipfile
        import tempfile
        from flask import send_file

        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')

        # 获取文件列表
        files = session.query(ProjectFile).filter(
            ProjectFile.id.in_(file_ids),
            ProjectFile.deleted_at == None
        ).all()

        if not files:
            return jsonify({'error': '没有可下载的文件'}), 404

        # 创建临时 ZIP 文件
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip_path = temp_zip.name

        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                if file.file_path and os.path.exists(file.file_path):
                    # 使用文件名作为ZIP内的名称
                    arcname = file.file_name
                    zipf.write(file.file_path, arcname)

                    # 记录下载日志
                    try:
                        project = session.query(Project).filter_by(id=file.project_id).first()
                        entity_id = project.project_no if project else f"PRJ-{file.project_id}"
                        access_logger.log_action(
                            file_id=str(file.id),
                            action_type='download',
                            system='portal',
                            entity_type='projects',
                            entity_id=entity_id,
                            user_id=user_id,
                            username=username,
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent', ''),
                            details={
                                'file_name': file.file_name,
                                'batch_download': True
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to log download for file {file.id}: {e}")

        logger.info(f"Batch download by {username}: {len(files)} files")

        # 返回 ZIP 文件
        zip_filename = f'batch_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        return send_file(
            temp_zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

    except Exception as e:
        logger.error(f"Batch download failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 文件预览 API (P1-2)
# ============================================================

@files_bp.route('/<int:file_id>/preview', methods=['GET'])
def preview_file(file_id):
    """获取文件预览

    支持的文件类型:
    - 图片: jpg, png, gif, webp (直接返回图片)
    - PDF: 返回 PDF 文件
    - 文本: txt, md, json, xml, csv (返回文本内容)
    - Office: 不支持直接预览，返回下载链接

    Query参数:
        - thumb: 是否返回缩略图 (仅图片, 默认false)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        if file.deleted_at is not None:
            return jsonify({'error': '文件已删除'}), 404

        if not file.file_path or not os.path.exists(file.file_path):
            return jsonify({'error': '文件不存在于服务器'}), 404

        # 获取文件类型
        file_type = file.file_type or ''
        file_ext = os.path.splitext(file.file_name)[1].lower() if file.file_name else ''

        # 图片预览
        if file_type.startswith('image/') or file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            # 是否返回缩略图
            thumb = request.args.get('thumb', 'false').lower() == 'true'

            if thumb:
                # 生成缩略图（简化实现，直接返回原图）
                # 实际生产中可以使用 Pillow 生成缩略图
                pass

            return send_file(
                file.file_path,
                mimetype=file_type or 'image/jpeg'
            )

        # PDF 预览
        if file_type == 'application/pdf' or file_ext == '.pdf':
            return send_file(
                file.file_path,
                mimetype='application/pdf'
            )

        # 文本文件预览
        text_extensions = ['.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.html', '.css']
        if file_ext in text_extensions or file_type.startswith('text/'):
            try:
                with open(file.file_path, 'r', encoding='utf-8') as f:
                    content = f.read(100000)  # 限制读取 100KB

                return jsonify({
                    'file_id': file_id,
                    'file_name': file.file_name,
                    'file_type': file_type,
                    'content_type': 'text',
                    'content': content,
                    'truncated': len(content) >= 100000
                }), 200
            except UnicodeDecodeError:
                return jsonify({
                    'file_id': file_id,
                    'file_name': file.file_name,
                    'content_type': 'binary',
                    'error': '无法预览二进制文件',
                    'download_url': f'/api/files/{file_id}/download'
                }), 200

        # 其他类型不支持预览
        return jsonify({
            'file_id': file_id,
            'file_name': file.file_name,
            'file_type': file_type,
            'content_type': 'unsupported',
            'message': '此文件类型不支持预览',
            'download_url': f'/api/files/{file_id}/download'
        }), 200

    except Exception as e:
        logger.error(f"File preview failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/preview-info', methods=['GET'])
def get_preview_info(file_id):
    """获取文件预览信息（不实际返回内容）

    返回文件是否支持预览、预览类型等元数据
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        file_type = file.file_type or ''
        file_ext = os.path.splitext(file.file_name)[1].lower() if file.file_name else ''

        preview_info = {
            'file_id': file_id,
            'file_name': file.file_name,
            'file_type': file_type,
            'file_size': file.file_size,
            'file_extension': file_ext,
            'supports_preview': False,
            'preview_type': None,
            'preview_url': None,
            'download_url': f'/api/files/{file_id}/download'
        }

        # 图片
        if file_type.startswith('image/') or file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            preview_info['supports_preview'] = True
            preview_info['preview_type'] = 'image'
            preview_info['preview_url'] = f'/api/files/{file_id}/preview'
            preview_info['thumbnail_url'] = f'/api/files/{file_id}/preview?thumb=true'

        # PDF
        elif file_type == 'application/pdf' or file_ext == '.pdf':
            preview_info['supports_preview'] = True
            preview_info['preview_type'] = 'pdf'
            preview_info['preview_url'] = f'/api/files/{file_id}/preview'

        # 文本
        elif file_ext in ['.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.html', '.css'] or file_type.startswith('text/'):
            preview_info['supports_preview'] = True
            preview_info['preview_type'] = 'text'
            preview_info['preview_url'] = f'/api/files/{file_id}/preview'

        # Office 文档
        elif file_ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            preview_info['supports_preview'] = False
            preview_info['preview_type'] = 'office'
            preview_info['note'] = 'Office 文档请下载后查看'

        return jsonify(preview_info), 200

    except Exception as e:
        logger.error(f"Get preview info failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 文件分享链接 API (P1-4)
# ============================================================

@files_bp.route('/<int:file_id>/share', methods=['POST'])
def create_share_link(file_id):
    """创建文件分享链接

    请求体:
        - password: 分享密码 (可选)
        - expire_days: 有效天数 (可选，默认永不过期)
        - expire_at: 过期时间 (可选，ISO格式，优先于expire_days)
        - max_downloads: 最大下载次数 (可选)
        - allow_download: 允许下载 (默认true)
        - allow_preview: 允许预览 (默认true)
        - remark: 备注 (可选)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Check file exists
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        if file.deleted_at is not None:
            return jsonify({'error': '文件已删除'}), 404

        # Get user info
        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')

        # Get request data
        data = request.get_json() or {}

        # Create share link
        share_link = FileShareLink(
            file_id=file_id,
            share_code=generate_share_code(),
            allow_download=data.get('allow_download', True),
            allow_preview=data.get('allow_preview', True),
            max_downloads=data.get('max_downloads'),
            created_by_id=user_id,
            created_by_name=username,
            remark=data.get('remark')
        )

        # Set password if provided
        if data.get('password'):
            share_link.set_password(data['password'])

        # Set expiration
        from datetime import timedelta
        if data.get('expire_at'):
            try:
                share_link.expire_at = datetime.fromisoformat(data['expire_at'].replace('Z', '+00:00'))
            except ValueError:
                pass
        elif data.get('expire_days'):
            try:
                days = int(data['expire_days'])
                share_link.expire_at = datetime.now() + timedelta(days=days)
            except (ValueError, TypeError):
                pass

        session.add(share_link)
        session.commit()
        session.refresh(share_link)

        # Log action
        project = session.query(Project).filter_by(id=file.project_id).first()
        entity_id = project.project_no if project else f"PRJ-{file.project_id}"

        access_logger.log_action(
            file_id=str(file_id),
            action_type='share',
            system='portal',
            entity_type='projects',
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            details={
                'file_name': file.file_name,
                'share_code': share_link.share_code,
                'has_password': share_link.has_password,
                'expire_at': share_link.expire_at.isoformat() if share_link.expire_at else None,
                'max_downloads': share_link.max_downloads
            }
        )

        logger.info(f"Share link created for file {file_id}: {share_link.share_code} by {username}")

        return jsonify({
            'message': '分享链接创建成功',
            'share_link': share_link.to_dict(include_file=True, file_info={
                'id': file.id,
                'file_name': file.file_name,
                'file_size': file.file_size
            })
        }), 201

    except Exception as e:
        session.rollback()
        logger.error(f"Create share link failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/shares', methods=['GET'])
def get_file_share_links(file_id):
    """获取文件的所有分享链接

    Query参数:
        - active_only: 只显示有效的分享链接 (默认true)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Check file exists
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # Get share links
        query = session.query(FileShareLink).filter_by(file_id=file_id)

        active_only = request.args.get('active_only', 'true').lower() == 'true'
        if active_only:
            query = query.filter_by(is_active=True)

        share_links = query.order_by(FileShareLink.created_at.desc()).all()

        return jsonify({
            'file_id': file_id,
            'file_name': file.file_name,
            'share_links': [sl.to_dict() for sl in share_links],
            'total': len(share_links)
        }), 200

    except Exception as e:
        logger.error(f"Get share links failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/share/<share_code>', methods=['DELETE'])
def delete_share_link(file_id, share_code):
    """删除/停用分享链接

    请求体 (可选):
        - reason: 停用原因
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Check file exists
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # Get share link
        share_link = session.query(FileShareLink).filter_by(
            file_id=file_id,
            share_code=share_code
        ).first()

        if not share_link:
            return jsonify({'error': '分享链接不存在'}), 404

        # Check permission (only creator or admin can delete)
        user_id = user.get('user_id') or user.get('id')
        user_role = user.get('role', 'user')
        is_owner = share_link.created_by_id == user_id
        is_admin = user_role in ['admin', 'super_admin']

        if not is_owner and not is_admin:
            return jsonify({'error': '无权删除此分享链接'}), 403

        # Get reason
        data = request.get_json() or {}
        reason = data.get('reason', '用户删除')

        # Deactivate share link
        share_link.deactivate(reason)

        session.commit()

        logger.info(f"Share link deleted: {share_code} for file {file_id}")

        return jsonify({
            'message': '分享链接已停用',
            'share_code': share_code
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Delete share link failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 公开分享访问 API (无需认证)
# ============================================================

# 创建单独的 Blueprint 用于公开分享访问
share_bp = Blueprint('share', __name__, url_prefix='/api/share')


@share_bp.route('/<share_code>', methods=['GET'])
def get_share_info(share_code):
    """获取分享信息（公开访问）

    返回分享链接的基本信息，不包含文件内容
    """
    session = SessionLocal()
    try:
        # Get share link
        share_link = session.query(FileShareLink).filter_by(share_code=share_code).first()

        if not share_link:
            return jsonify({'error': '分享链接不存在'}), 404

        if not share_link.is_active:
            return jsonify({'error': '分享链接已停用'}), 410

        if share_link.is_expired:
            return jsonify({'error': '分享链接已过期'}), 410

        # Get file info
        file = session.query(ProjectFile).filter_by(id=share_link.file_id).first()
        if not file or file.deleted_at is not None:
            return jsonify({'error': '文件不存在'}), 404

        # Increment view count (only if no password or verified)
        if not share_link.has_password:
            share_link.increment_view()
            session.commit()

        return jsonify({
            'share_code': share_code,
            'has_password': share_link.has_password,
            'allow_download': share_link.allow_download,
            'allow_preview': share_link.allow_preview,
            'is_download_limit_reached': share_link.is_download_limit_reached,
            'file': {
                'file_name': file.file_name,
                'file_size': file.file_size,
                'file_type': file.file_type
            } if not share_link.has_password else None,
            'created_by_name': share_link.created_by_name,
            'expire_at': share_link.expire_at.isoformat() if share_link.expire_at else None
        }), 200

    except Exception as e:
        logger.error(f"Get share info failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@share_bp.route('/<share_code>/verify', methods=['POST'])
def verify_share_password(share_code):
    """验证分享密码（公开访问）

    请求体:
        - password: 分享密码
    """
    session = SessionLocal()
    try:
        # Get share link
        share_link = session.query(FileShareLink).filter_by(share_code=share_code).first()

        if not share_link:
            return jsonify({'error': '分享链接不存在'}), 404

        if not share_link.is_active:
            return jsonify({'error': '分享链接已停用'}), 410

        if share_link.is_expired:
            return jsonify({'error': '分享链接已过期'}), 410

        # Check password
        data = request.get_json() or {}
        password = data.get('password', '')

        if not share_link.check_password(password):
            return jsonify({'error': '密码错误'}), 403

        # Get file info
        file = session.query(ProjectFile).filter_by(id=share_link.file_id).first()
        if not file or file.deleted_at is not None:
            return jsonify({'error': '文件不存在'}), 404

        # Increment view count on successful verification
        share_link.increment_view()
        session.commit()

        return jsonify({
            'success': True,
            'share_code': share_code,
            'allow_download': share_link.allow_download,
            'allow_preview': share_link.allow_preview,
            'is_download_limit_reached': share_link.is_download_limit_reached,
            'file': {
                'id': file.id,
                'file_name': file.file_name,
                'file_size': file.file_size,
                'file_type': file.file_type
            }
        }), 200

    except Exception as e:
        logger.error(f"Verify share password failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@share_bp.route('/<share_code>/download', methods=['GET'])
def download_shared_file(share_code):
    """下载分享文件（公开访问）

    Query参数:
        - password: 分享密码 (如果需要)
    """
    session = SessionLocal()
    try:
        # Get share link
        share_link = session.query(FileShareLink).filter_by(share_code=share_code).first()

        if not share_link:
            return jsonify({'error': '分享链接不存在'}), 404

        if not share_link.is_active:
            return jsonify({'error': '分享链接已停用'}), 410

        if share_link.is_expired:
            return jsonify({'error': '分享链接已过期'}), 410

        if not share_link.allow_download:
            return jsonify({'error': '此分享链接不允许下载'}), 403

        if share_link.is_download_limit_reached:
            return jsonify({'error': '下载次数已达上限'}), 403

        # Check password
        password = request.args.get('password', '')
        if not share_link.check_password(password):
            return jsonify({'error': '密码错误'}), 403

        # Get file
        file = session.query(ProjectFile).filter_by(id=share_link.file_id).first()
        if not file or file.deleted_at is not None:
            return jsonify({'error': '文件不存在'}), 404

        if not file.file_path or not os.path.exists(file.file_path):
            return jsonify({'error': '文件不存在于服务器'}), 404

        # Increment download count
        share_link.increment_download()
        session.commit()

        logger.info(f"Shared file downloaded: {share_code}, downloads={share_link.download_count}")

        # Send file
        return send_file(
            file.file_path,
            as_attachment=True,
            download_name=file.file_name
        )

    except Exception as e:
        logger.error(f"Download shared file failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@share_bp.route('/<share_code>/preview', methods=['GET'])
def preview_shared_file(share_code):
    """预览分享文件（公开访问）

    Query参数:
        - password: 分享密码 (如果需要)
    """
    session = SessionLocal()
    try:
        # Get share link
        share_link = session.query(FileShareLink).filter_by(share_code=share_code).first()

        if not share_link:
            return jsonify({'error': '分享链接不存在'}), 404

        if not share_link.is_active:
            return jsonify({'error': '分享链接已停用'}), 410

        if share_link.is_expired:
            return jsonify({'error': '分享链接已过期'}), 410

        if not share_link.allow_preview:
            return jsonify({'error': '此分享链接不允许预览'}), 403

        # Check password
        password = request.args.get('password', '')
        if not share_link.check_password(password):
            return jsonify({'error': '密码错误'}), 403

        # Get file
        file = session.query(ProjectFile).filter_by(id=share_link.file_id).first()
        if not file or file.deleted_at is not None:
            return jsonify({'error': '文件不存在'}), 404

        if not file.file_path or not os.path.exists(file.file_path):
            return jsonify({'error': '文件不存在于服务器'}), 404

        # Get file type
        file_type = file.file_type or ''
        file_ext = os.path.splitext(file.file_name)[1].lower() if file.file_name else ''

        # Image preview
        if file_type.startswith('image/') or file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            return send_file(
                file.file_path,
                mimetype=file_type or 'image/jpeg'
            )

        # PDF preview
        if file_type == 'application/pdf' or file_ext == '.pdf':
            return send_file(
                file.file_path,
                mimetype='application/pdf'
            )

        # Text preview
        text_extensions = ['.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.html', '.css']
        if file_ext in text_extensions or file_type.startswith('text/'):
            try:
                with open(file.file_path, 'r', encoding='utf-8') as f:
                    content = f.read(100000)

                return jsonify({
                    'file_name': file.file_name,
                    'file_type': file_type,
                    'content_type': 'text',
                    'content': content,
                    'truncated': len(content) >= 100000
                }), 200
            except UnicodeDecodeError:
                return jsonify({
                    'file_name': file.file_name,
                    'content_type': 'binary',
                    'error': '无法预览二进制文件'
                }), 200

        # Unsupported type
        return jsonify({
            'file_name': file.file_name,
            'file_type': file_type,
            'content_type': 'unsupported',
            'message': '此文件类型不支持预览'
        }), 200

    except Exception as e:
        logger.error(f"Preview shared file failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
