"""
回收站管理 API
提供统一的回收站功能，管理已删除的项目和文件
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, or_
import logging
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

from models import SessionLocal
from models.project import Project
from models.project_file import ProjectFile

logger = logging.getLogger(__name__)


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

recycle_bin_bp = Blueprint('recycle_bin', __name__, url_prefix='/api/recycle-bin')


def is_admin(user):
    """检查用户是否是管理员"""
    role = user.get('role', '')
    return role in ['admin', 'super_admin', '管理员', '超级管理员']


def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes is None:
        return '0 B'

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def calculate_days_remaining(deleted_at, retention_days=30):
    """计算距离永久删除的剩余天数"""
    if deleted_at is None:
        return None

    expire_date = deleted_at + timedelta(days=retention_days)
    remaining = (expire_date - datetime.now()).days
    return max(0, remaining)


# ============================================================
# 回收站列表 API
# ============================================================

@recycle_bin_bp.route('/items', methods=['GET'])
def get_recycle_bin_items():
    """获取回收站所有项目（项目 + 文件）

    Query参数:
        - type: 类型筛选 (all/project/file)
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认20)
        - search: 搜索关键词
        - sort: 排序字段 (deleted_at/name/size)
        - order: 排序方向 (asc/desc)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # 解析参数
        item_type = request.args.get('type', 'all')
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'deleted_at')
        order = request.args.get('order', 'desc')

        user_id = user.get('user_id') or user.get('id')
        is_admin_user = is_admin(user)

        items = []
        total_projects = 0
        total_files = 0

        # 查询已删除项目
        if item_type in ['all', 'project']:
            project_query = session.query(Project).filter(Project.deleted_at != None)

            # 非管理员只能看自己删除的或创建的项目
            if not is_admin_user:
                project_query = project_query.filter(
                    or_(
                        Project.deleted_by_id == user_id,
                        Project.created_by_id == user_id
                    )
                )

            # 搜索
            if search:
                project_query = project_query.filter(
                    or_(
                        Project.name.ilike(f'%{search}%'),
                        Project.project_no.ilike(f'%{search}%')
                    )
                )

            total_projects = project_query.count()

            projects = project_query.order_by(Project.deleted_at.desc()).all()

            for p in projects:
                # 获取关联的已删除文件数
                deleted_files_count = session.query(func.count(ProjectFile.id)).filter(
                    ProjectFile.project_id == p.id,
                    ProjectFile.deleted_at != None
                ).scalar() or 0

                # 计算项目文件总大小
                total_size = session.query(func.sum(ProjectFile.file_size)).filter(
                    ProjectFile.project_id == p.id
                ).scalar() or 0

                items.append({
                    'type': 'project',
                    'id': p.id,
                    'name': p.name,
                    'project_no': p.project_no,
                    'deleted_at': p.deleted_at.isoformat() if p.deleted_at else None,
                    'delete_reason': p.delete_reason,
                    'deleted_by_id': p.deleted_by_id,
                    'days_remaining': calculate_days_remaining(p.deleted_at),
                    'can_restore': True,
                    'size_bytes': total_size,
                    'size_formatted': format_file_size(total_size),
                    'related_files_count': deleted_files_count
                })

        # 查询已删除文件（不属于已删除项目的独立文件）
        if item_type in ['all', 'file']:
            file_query = session.query(ProjectFile).filter(
                ProjectFile.deleted_at != None
            )

            # 排除已删除项目的文件（避免重复）
            deleted_project_ids = session.query(Project.id).filter(
                Project.deleted_at != None
            ).subquery()

            file_query = file_query.filter(
                ~ProjectFile.project_id.in_(deleted_project_ids)
            )

            # 非管理员只能看自己删除或上传的文件
            if not is_admin_user:
                file_query = file_query.filter(
                    or_(
                        ProjectFile.deleted_by_id == user_id,
                        ProjectFile.uploaded_by_id == user_id
                    )
                )

            # 搜索
            if search:
                file_query = file_query.filter(
                    ProjectFile.file_name.ilike(f'%{search}%')
                )

            total_files = file_query.count()

            files = file_query.order_by(ProjectFile.deleted_at.desc()).all()

            for f in files:
                # 获取所属项目名称
                project = session.query(Project).filter_by(id=f.project_id).first()
                project_name = project.name if project else '未知项目'

                items.append({
                    'type': 'file',
                    'id': f.id,
                    'name': f.file_name,
                    'file_size': f.file_size,
                    'size_formatted': format_file_size(f.file_size),
                    'file_type': f.file_type,
                    'project_id': f.project_id,
                    'project_name': project_name,
                    'deleted_at': f.deleted_at.isoformat() if f.deleted_at else None,
                    'delete_reason': f.delete_reason,
                    'deleted_by_id': f.deleted_by_id,
                    'days_remaining': calculate_days_remaining(f.deleted_at),
                    'can_restore': True
                })

        # 排序
        if sort_by == 'deleted_at':
            items.sort(key=lambda x: x.get('deleted_at') or '', reverse=(order == 'desc'))
        elif sort_by == 'name':
            items.sort(key=lambda x: x.get('name', ''), reverse=(order == 'desc'))
        elif sort_by == 'size':
            items.sort(key=lambda x: x.get('size_bytes') or x.get('file_size') or 0, reverse=(order == 'desc'))

        # 分页
        total = len(items)
        offset = (page - 1) * page_size
        paginated_items = items[offset:offset + page_size]

        return jsonify({
            'items': paginated_items,
            'total': total,
            'total_projects': total_projects,
            'total_files': total_files,
            'page': page,
            'page_size': page_size
        }), 200

    except Exception as e:
        logger.error(f"Get recycle bin items failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@recycle_bin_bp.route('/stats', methods=['GET'])
def get_recycle_bin_stats():
    """获取回收站统计信息"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')
        is_admin_user = is_admin(user)

        # 项目统计
        project_query = session.query(Project).filter(Project.deleted_at != None)
        if not is_admin_user:
            project_query = project_query.filter(
                or_(
                    Project.deleted_by_id == user_id,
                    Project.created_by_id == user_id
                )
            )
        total_projects = project_query.count()

        # 文件统计
        file_query = session.query(ProjectFile).filter(ProjectFile.deleted_at != None)
        if not is_admin_user:
            file_query = file_query.filter(
                or_(
                    ProjectFile.deleted_by_id == user_id,
                    ProjectFile.uploaded_by_id == user_id
                )
            )
        total_files = file_query.count()

        # 存储空间
        if is_admin_user:
            total_size = session.query(func.sum(ProjectFile.file_size)).filter(
                ProjectFile.deleted_at != None
            ).scalar() or 0
        else:
            total_size = session.query(func.sum(ProjectFile.file_size)).filter(
                ProjectFile.deleted_at != None,
                or_(
                    ProjectFile.deleted_by_id == user_id,
                    ProjectFile.uploaded_by_id == user_id
                )
            ).scalar() or 0

        # 即将过期（7天内）
        expire_threshold = datetime.now() - timedelta(days=23)  # 30 - 7 = 23
        expiring_soon = session.query(func.count(Project.id)).filter(
            Project.deleted_at != None,
            Project.deleted_at < expire_threshold
        ).scalar() or 0

        # 最旧项目
        oldest_item = session.query(func.min(Project.deleted_at)).filter(
            Project.deleted_at != None
        ).scalar()
        oldest_days = 0
        if oldest_item:
            oldest_days = (datetime.now() - oldest_item).days

        return jsonify({
            'total_items': total_projects + total_files,
            'total_projects': total_projects,
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_formatted': format_file_size(total_size),
            'expiring_soon': expiring_soon,
            'oldest_item_days': oldest_days,
            'retention_days': 30
        }), 200

    except Exception as e:
        logger.error(f"Get recycle bin stats failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 恢复 API
# ============================================================

@recycle_bin_bp.route('/batch-restore', methods=['POST'])
def batch_restore():
    """批量恢复项目和文件

    Request Body:
        {
            "items": [
                {"type": "project", "id": 1},
                {"type": "file", "id": 2}
            ]
        }
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'error': '请提供要恢复的项目列表'}), 400

    items = data.get('items', [])
    if not items:
        return jsonify({'error': '项目列表为空'}), 400

    session = SessionLocal()
    try:
        user_id = user.get('user_id') or user.get('id')
        is_admin_user = is_admin(user)

        restored = {'projects': 0, 'files': 0}
        errors = []

        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')

            if not item_type or not item_id:
                errors.append(f"无效的项目: {item}")
                continue

            try:
                if item_type == 'project':
                    project = session.query(Project).filter_by(id=item_id).first()
                    if not project:
                        errors.append(f"项目 {item_id} 不存在")
                        continue

                    if project.deleted_at is None:
                        errors.append(f"项目 {item_id} 未被删除")
                        continue

                    # 检查权限
                    can_restore = is_admin_user or project.deleted_by_id == user_id or project.created_by_id == user_id
                    if not can_restore:
                        errors.append(f"无权恢复项目 {item_id}")
                        continue

                    # 恢复项目及其文件
                    project.deleted_at = None
                    project.delete_reason = None
                    project.deleted_by_id = None

                    # 恢复项目下的所有文件
                    session.query(ProjectFile).filter(
                        ProjectFile.project_id == item_id,
                        ProjectFile.deleted_at != None
                    ).update({
                        'deleted_at': None,
                        'delete_reason': None,
                        'deleted_by_id': None
                    })

                    restored['projects'] += 1

                elif item_type == 'file':
                    file = session.query(ProjectFile).filter_by(id=item_id).first()
                    if not file:
                        errors.append(f"文件 {item_id} 不存在")
                        continue

                    if file.deleted_at is None:
                        errors.append(f"文件 {item_id} 未被删除")
                        continue

                    # 检查权限
                    can_restore = is_admin_user or file.deleted_by_id == user_id or file.uploaded_by_id == user_id
                    if not can_restore:
                        errors.append(f"无权恢复文件 {item_id}")
                        continue

                    # 恢复文件
                    file.deleted_at = None
                    file.delete_reason = None
                    file.deleted_by_id = None

                    restored['files'] += 1

            except Exception as e:
                errors.append(f"{item_type} {item_id}: {str(e)}")

        session.commit()

        username = user.get('username', 'unknown')
        logger.info(f"Batch restore by {username}: {restored}")

        return jsonify({
            'message': '恢复完成',
            'restored': restored,
            'errors': errors if errors else None
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Batch restore failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@recycle_bin_bp.route('/files/<int:file_id>/restore', methods=['POST'])
def restore_file(file_id):
    """恢复单个文件"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        if file.deleted_at is None:
            return jsonify({'error': '文件未被删除'}), 400

        # 检查权限
        user_id = user.get('user_id') or user.get('id')
        can_restore = is_admin(user) or file.deleted_by_id == user_id or file.uploaded_by_id == user_id
        if not can_restore:
            return jsonify({'error': '没有恢复权限'}), 403

        # 恢复文件
        file.deleted_at = None
        file.delete_reason = None
        file.deleted_by_id = None

        session.commit()

        return jsonify({
            'message': '文件已恢复',
            'file': {
                'id': file.id,
                'file_name': file.file_name
            }
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Restore file failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 永久删除 API (仅管理员)
# ============================================================

@recycle_bin_bp.route('/batch-delete', methods=['POST'])
def batch_permanent_delete():
    """批量永久删除项目和文件（仅管理员）

    Request Body:
        {
            "items": [
                {"type": "project", "id": 1},
                {"type": "file", "id": 2}
            ],
            "confirm": "PERMANENT-DELETE"
        }
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    if not is_admin(user):
        return jsonify({'error': '仅管理员可执行永久删除'}), 403

    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'error': '请提供要删除的项目列表'}), 400

    # 安全确认
    if data.get('confirm') != 'PERMANENT-DELETE':
        return jsonify({'error': '请确认永久删除操作（confirm: "PERMANENT-DELETE"）'}), 400

    items = data.get('items', [])
    if not items:
        return jsonify({'error': '项目列表为空'}), 400

    session = SessionLocal()
    try:
        deleted = {'projects': 0, 'files': 0}
        errors = []

        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')

            if not item_type or not item_id:
                errors.append(f"无效的项目: {item}")
                continue

            try:
                if item_type == 'project':
                    project = session.query(Project).filter_by(id=item_id).first()
                    if not project:
                        errors.append(f"项目 {item_id} 不存在")
                        continue

                    # 删除项目下的所有文件
                    session.query(ProjectFile).filter_by(project_id=item_id).delete()

                    # 删除项目
                    session.delete(project)
                    deleted['projects'] += 1

                elif item_type == 'file':
                    file = session.query(ProjectFile).filter_by(id=item_id).first()
                    if not file:
                        errors.append(f"文件 {item_id} 不存在")
                        continue

                    # 删除文件记录
                    session.delete(file)
                    deleted['files'] += 1

            except Exception as e:
                errors.append(f"{item_type} {item_id}: {str(e)}")

        session.commit()

        username = user.get('username', 'unknown')
        logger.warning(f"Permanent delete by admin {username}: {deleted}")

        return jsonify({
            'message': '永久删除完成',
            'deleted': deleted,
            'errors': errors if errors else None
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Batch permanent delete failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@recycle_bin_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def permanent_delete_project(project_id):
    """永久删除单个项目（仅管理员）"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    if not is_admin(user):
        return jsonify({'error': '仅管理员可执行永久删除'}), 403

    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        project_no = project.project_no

        # 删除项目下的所有文件
        files_deleted = session.query(ProjectFile).filter_by(project_id=project_id).delete()

        # 删除项目
        session.delete(project)
        session.commit()

        username = user.get('username', 'unknown')
        logger.warning(f"Project permanently deleted: {project_no} by {username}")

        return jsonify({
            'message': '项目已永久删除',
            'project_no': project_no,
            'files_deleted': files_deleted
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Permanent delete project failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@recycle_bin_bp.route('/files/<int:file_id>', methods=['DELETE'])
def permanent_delete_file(file_id):
    """永久删除单个文件（仅管理员）"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    if not is_admin(user):
        return jsonify({'error': '仅管理员可执行永久删除'}), 403

    session = SessionLocal()
    try:
        file = session.query(ProjectFile).filter_by(id=file_id).first()
        if not file:
            return jsonify({'error': '文件不存在'}), 404

        file_name = file.file_name

        # 删除文件记录
        session.delete(file)
        session.commit()

        username = user.get('username', 'unknown')
        logger.warning(f"File permanently deleted: {file_name} by {username}")

        return jsonify({
            'message': '文件已永久删除',
            'file_name': file_name
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Permanent delete file failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 清理 API (仅超级管理员)
# ============================================================

@recycle_bin_bp.route('/purge', methods=['DELETE'])
def purge_expired():
    """清理所有过期项目（仅超级管理员）

    删除所有超过30天的已删除项目和文件
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    role = user.get('role', '')
    if role not in ['super_admin', '超级管理员']:
        return jsonify({'error': '仅超级管理员可执行清理操作'}), 403

    session = SessionLocal()
    try:
        # 计算过期时间点
        expire_date = datetime.now() - timedelta(days=30)

        # 查找过期的项目
        expired_projects = session.query(Project).filter(
            Project.deleted_at != None,
            Project.deleted_at < expire_date
        ).all()

        projects_deleted = 0
        files_deleted = 0

        for project in expired_projects:
            # 删除项目文件
            count = session.query(ProjectFile).filter_by(project_id=project.id).delete()
            files_deleted += count

            # 删除项目
            session.delete(project)
            projects_deleted += 1

        # 查找过期的独立文件
        expired_files = session.query(ProjectFile).filter(
            ProjectFile.deleted_at != None,
            ProjectFile.deleted_at < expire_date
        ).all()

        for file in expired_files:
            session.delete(file)
            files_deleted += 1

        session.commit()

        username = user.get('username', 'unknown')
        logger.info(f"Purge expired by {username}: {projects_deleted} projects, {files_deleted} files")

        return jsonify({
            'message': '清理完成',
            'projects_deleted': projects_deleted,
            'files_deleted': files_deleted
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Purge expired failed: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
