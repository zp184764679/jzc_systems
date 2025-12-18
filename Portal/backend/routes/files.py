"""
Files API Routes - 文件管理API
支持文件上传、版本控制、原版/中文版管理
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from models import SessionLocal
from models.project import Project
from models.project_file import ProjectFile, FileCategory, OriginalLanguage
from datetime import datetime
import sys
import os
import hashlib

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token
from shared.file_storage import FileStorage

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

# Initialize file storage
storage = FileStorage()

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
    """获取项目文件列表"""
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

        # Only latest versions by default
        only_latest = request.args.get('only_latest', 'true').lower() == 'true'
        if only_latest:
            query = query.filter_by(is_latest_version=True)

        files = query.order_by(ProjectFile.created_at.desc()).all()

        return jsonify({
            'files': [f.to_dict() for f in files],
            'total': len(files)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/upload', methods=['POST'])
def upload_file():
    """上传文件"""
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

        # Save file using shared storage
        result = storage.save_file(
            file_bytes=file_bytes,
            original_filename=secure_filename(file.filename),
            system='portal',
            file_type='projects'
        )

        # Get form data
        category = request.form.get('category', 'other')
        original_language = request.form.get('original_language', 'zh')
        is_chinese_version = request.form.get('is_chinese_version', 'false').lower() == 'true'
        remark = request.form.get('remark', '')

        # Create file record
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
            uploaded_by_id=user.get('user_id') or user.get('id'),
            remark=remark
        )

        session.add(project_file)
        session.commit()
        session.refresh(project_file)

        return jsonify(project_file.to_dict()), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/upload-version', methods=['POST'])
def upload_file_version(file_id):
    """上传文件新版本"""
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

        # Read file
        file_bytes = file.read()

        # Save new version
        result = storage.save_file(
            file_bytes=file_bytes,
            original_filename=secure_filename(file.filename),
            system='portal',
            file_type='projects'
        )

        # Calculate new version number
        parts = original_file.version.split('.')
        major, minor = int(parts[0]), int(parts[1])
        new_version = f"{major}.{minor + 1}"

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
            uploaded_by_id=user.get('user_id') or user.get('id'),
            remark=request.form.get('remark', '')
        )

        session.add(new_file)
        session.commit()
        session.refresh(new_file)

        return jsonify(new_file.to_dict()), 201

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@files_bp.route('/<int:file_id>/versions', methods=['GET'])
def get_file_versions(file_id):
    """获取文件版本历史"""
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

        return jsonify({
            'versions': [v.to_dict() for v in versions],
            'total': len(versions)
        }), 200

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
    """删除文件"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        # TODO: Check permission (only owner or uploader can delete)

        # Delete physical file
        try:
            if os.path.exists(file.file_path):
                os.remove(file.file_path)
        except Exception as e:
            print(f"Failed to delete physical file: {e}")

        # Delete database record
        session.delete(file)
        session.commit()

        return jsonify({'message': '文件已删除'}), 200

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
