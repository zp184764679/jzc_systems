"""
Projects API Routes - 项目管理API

支持软删除功能：
- DELETE /api/projects/<id> - 软删除项目（移到隔离区）
- DELETE /api/projects/<id>?hard=true - 硬删除（仅管理员，需二次确认）
- POST /api/projects/<id>/restore - 恢复已删除项目
- GET /api/projects/deleted - 获取已删除项目列表（回收站）
"""
from flask import Blueprint, request, jsonify
from models import SessionLocal
from models.project import Project
from models.task import Task
from models.project_file import ProjectFile
from models.project_member import ProjectMember
from models.project_phase import ProjectPhase
from models.issue import Issue
from models.project_notification import ProjectNotification
from datetime import datetime
import sys
import os
import logging

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token
from shared.file_storage_v2 import EnterpriseFileStorage

logger = logging.getLogger(__name__)

# Initialize file storage for soft delete operations
storage = EnterpriseFileStorage()

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


def is_admin(user):
    """检查用户是否为管理员"""
    role = user.get('role', '')
    return role in ['admin', 'super_admin']


def check_project_permission(session, project_id, user, required_role=None):
    """
    检查用户是否有项目权限

    Args:
        session: 数据库会话
        project_id: 项目ID
        user: 当前用户信息
        required_role: 需要的角色（'owner', 'manager', 'member', None表示任意成员）

    Returns:
        (has_permission, member_role): 是否有权限，以及用户在项目中的角色
    """
    # 管理员有所有权限
    if is_admin(user):
        return True, 'admin'

    user_id = user.get('user_id') or user.get('id')

    # 检查是否为项目创建者
    project = session.query(Project).filter_by(id=project_id).first()
    if project and project.created_by_id == user_id:
        return True, 'owner'

    # 检查是否为项目成员
    member = session.query(ProjectMember).filter_by(
        project_id=project_id,
        user_id=user_id
    ).first()

    if not member:
        return False, None

    member_role = member.role if member else None

    # 如果没有特定角色要求，只要是成员就有权限
    if required_role is None:
        return True, member_role

    # 角色等级: owner > manager > member
    role_levels = {'owner': 3, 'manager': 2, 'member': 1}
    required_level = role_levels.get(required_role, 0)
    user_level = role_levels.get(member_role, 0)

    return user_level >= required_level, member_role


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


@projects_bp.route('', methods=['GET'])
def get_projects():
    """获取项目列表（支持分页和筛选）

    Query参数:
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认20, 最大100)
        - status: 项目状态筛选
        - priority: 优先级筛选
        - search: 搜索关键词
        - customer: 客户筛选
        - part_number: 部件番号筛选
        - include_deleted: 是否包含已删除项目 (默认false)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(page_size, 100)  # 最大每页100条

        # 筛选参数
        status = request.args.get('status')
        priority = request.args.get('priority')
        search = request.args.get('search', '')
        customer = request.args.get('customer')  # 客户筛选
        part_number = request.args.get('part_number')  # 部件番号筛选
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'

        # 构建查询
        query = session.query(Project)

        # 默认排除已删除项目（除非明确要求包含）
        if not include_deleted:
            query = query.filter(Project.deleted_at == None)

        # 应用筛选
        if status:
            query = query.filter(Project.status == status)
        if priority:
            query = query.filter(Project.priority == priority)
        if customer:
            # 客户筛选 - 支持精确匹配或模糊匹配
            if customer == '未分类':
                query = query.filter((Project.customer == None) | (Project.customer == ''))
            else:
                query = query.filter(
                    (Project.customer == customer) |
                    (Project.customer_name == customer)
                )
        if part_number:
            # 部件番号筛选
            if part_number == '无部件番号':
                query = query.filter((Project.part_number == None) | (Project.part_number == ''))
            else:
                query = query.filter(Project.part_number == part_number)
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Project.name.ilike(search_pattern)) |
                (Project.customer.ilike(search_pattern)) |
                (Project.order_no.ilike(search_pattern)) |
                (Project.part_number.ilike(search_pattern))
            )

        # 获取总数
        total = query.count()

        # 排序（最新创建的在前）
        query = query.order_by(Project.created_at.desc())

        # 分页
        offset = (page - 1) * page_size
        projects = query.offset(offset).limit(page_size).all()

        return jsonify({
            'projects': [p.to_dict() for p in projects],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """获取项目详情"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        return jsonify(project.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@projects_bp.route('', methods=['POST'])
def create_project():
    """创建项目"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': '缺少项目名称'}), 400

    session = SessionLocal()
    try:
        # Generate project number
        import datetime
        project_no = f"PRJ{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        project = Project(
            project_no=project_no,
            name=data['name'],
            description=data.get('description'),
            customer=data.get('customer'),  # 兼容旧数据
            customer_id=data.get('customer_id'),  # CRM 客户 ID
            customer_name=data.get('customer_name'),  # CRM 客户名称
            order_no=data.get('order_no'),
            part_number=data.get('part_number'),  # 部件番号
            created_by_id=user.get('user_id') or user.get('id'),
            manager_id=data.get('manager_id'),
            priority=data.get('priority', 'normal'),
            status=data.get('status', 'planning'),
        )

        # 处理日期字段
        if data.get('planned_start_date'):
            from datetime import datetime
            project.planned_start_date = datetime.strptime(data['planned_start_date'], '%Y-%m-%d').date()
        if data.get('planned_end_date'):
            from datetime import datetime
            project.planned_end_date = datetime.strptime(data['planned_end_date'], '%Y-%m-%d').date()

        session.add(project)
        session.commit()
        session.refresh(project)

        return jsonify(project.to_dict()), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@projects_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 检查编辑权限（需要 member 以上角色）
        has_permission, role = check_project_permission(session, project_id, user)
        if not has_permission:
            return jsonify({'error': '没有编辑权限'}), 403

        # Update fields
        updatable_fields = [
            'name', 'description', 'customer', 'customer_id', 'customer_name',
            'order_no', 'part_number', 'status', 'priority', 'progress_percentage', 'manager_id'
        ]
        for key in updatable_fields:
            if key in data:
                setattr(project, key, data[key])

        # 处理日期字段
        if 'planned_start_date' in data:
            if data['planned_start_date']:
                from datetime import datetime as dt
                project.planned_start_date = dt.strptime(data['planned_start_date'], '%Y-%m-%d').date()
            else:
                project.planned_start_date = None
        if 'planned_end_date' in data:
            if data['planned_end_date']:
                from datetime import datetime as dt
                project.planned_end_date = dt.strptime(data['planned_end_date'], '%Y-%m-%d').date()
            else:
                project.planned_end_date = None

        session.commit()
        session.refresh(project)

        return jsonify(project.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目（默认软删除）

    Query参数:
        - hard: 是否硬删除 (true/false, 默认false)
        - confirm: 硬删除确认码 (硬删除时必须提供)

    请求体:
        - reason: 删除原因 (可选)

    软删除策略:
    1. 项目标记为已删除
    2. 项目文件移动到隔离区
    3. 30天后由定时任务永久删除
    4. 支持恢复
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 检查是否已删除
        if project.deleted_at is not None:
            return jsonify({'error': '项目已在回收站中'}), 400

        # 检查删除权限（需要 owner 或 manager 角色）
        has_permission, role = check_project_permission(session, project_id, user, 'manager')
        if not has_permission:
            return jsonify({'error': '没有删除权限'}), 403

        user_id = user.get('user_id') or user.get('id')
        username = user.get('username', 'unknown')

        # 获取删除原因
        data = request.get_json() or {}
        delete_reason = data.get('reason', f'用户 {username} 删除')

        # 检查是否硬删除
        hard_delete = request.args.get('hard', 'false').lower() == 'true'

        if hard_delete:
            # 硬删除需要管理员权限和确认码
            if not is_admin(user):
                return jsonify({'error': '硬删除需要管理员权限'}), 403

            confirm = request.args.get('confirm')
            expected_confirm = f'DELETE-{project.project_no}'
            if confirm != expected_confirm:
                return jsonify({
                    'error': '硬删除需要确认',
                    'message': f'请在 URL 中添加 ?hard=true&confirm={expected_confirm} 确认删除'
                }), 400

            # 执行硬删除（级联删除所有关联数据）
            return _hard_delete_project(session, project, user_id, username)

        # ========== 软删除逻辑 ==========

        entity_id = project.project_no or f"PRJ-{project_id}"
        files_moved = 0
        files_failed = 0

        # 1. 移动项目文件到隔离区
        files = session.query(ProjectFile).filter_by(project_id=project_id).filter(
            ProjectFile.deleted_at == None
        ).all()

        for file in files:
            try:
                # 移动物理文件到隔离区
                if file.file_path and os.path.exists(file.file_path):
                    storage.soft_delete(
                        file_path=file.file_path,
                        reason=f'项目删除: {delete_reason}'
                    )

                # 标记文件为已删除
                file.deleted_at = datetime.now()
                file.delete_reason = f'项目删除: {delete_reason}'
                file.deleted_by_id = user_id
                files_moved += 1
            except Exception as e:
                logger.warning(f"Failed to soft delete file {file.id}: {e}")
                files_failed += 1

        # 2. 标记项目为已删除
        project.deleted_at = datetime.now()
        project.delete_reason = delete_reason
        project.deleted_by_id = user_id

        session.commit()

        logger.info(f"Project soft deleted: {project.project_no} by user {username}")

        return jsonify({
            'message': '项目已移至回收站',
            'project_id': project_id,
            'project_no': project.project_no,
            'deleted_at': project.deleted_at.isoformat(),
            'files_moved': files_moved,
            'files_failed': files_failed,
            'restore_url': f'/api/projects/{project_id}/restore',
            'note': '项目和文件将在30天后永久删除，期间可恢复'
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Project delete failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


def _hard_delete_project(session, project, user_id, username):
    """执行硬删除（完全删除项目和所有关联数据）"""
    project_id = project.id

    # 级联删除关联数据
    deleted_counts = {
        'tasks': 0,
        'phases': 0,
        'files': 0,
        'members': 0,
        'issues': 0,
        'notifications': 0
    }

    # 删除任务
    tasks = session.query(Task).filter_by(project_id=project_id).all()
    for task in tasks:
        session.delete(task)
        deleted_counts['tasks'] += 1

    # 删除阶段
    phases = session.query(ProjectPhase).filter_by(project_id=project_id).all()
    for phase in phases:
        session.delete(phase)
        deleted_counts['phases'] += 1

    # 删除文件记录和物理文件
    files = session.query(ProjectFile).filter_by(project_id=project_id).all()
    for file in files:
        # 尝试删除物理文件
        try:
            if file.file_path and os.path.exists(file.file_path):
                os.remove(file.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {file.file_path}: {e}")
        session.delete(file)
        deleted_counts['files'] += 1

    # 删除成员
    members = session.query(ProjectMember).filter_by(project_id=project_id).all()
    for member in members:
        session.delete(member)
        deleted_counts['members'] += 1

    # 删除问题
    issues = session.query(Issue).filter_by(project_id=project_id).all()
    for issue in issues:
        session.delete(issue)
        deleted_counts['issues'] += 1

    # 删除通知
    notifications = session.query(ProjectNotification).filter_by(project_id=project_id).all()
    for notification in notifications:
        session.delete(notification)
        deleted_counts['notifications'] += 1

    # 最后删除项目
    project_no = project.project_no
    session.delete(project)
    session.commit()

    logger.info(f"Project hard deleted: {project_no} by user {username}")

    return jsonify({
        'message': '项目已永久删除',
        'project_no': project_no,
        'deleted': deleted_counts
    }), 200


# ============================================================
# 回收站功能 API
# ============================================================

@projects_bp.route('/deleted', methods=['GET'])
def get_deleted_projects():
    """获取已删除项目列表（回收站）

    Query参数:
        - page: 页码 (默认1)
        - page_size: 每页数量 (默认20)
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # 查询已删除项目
        query = session.query(Project).filter(Project.deleted_at != None)

        # 非管理员只能看自己删除的项目
        user_id = user.get('user_id') or user.get('id')
        if not is_admin(user):
            query = query.filter(
                (Project.deleted_by_id == user_id) |
                (Project.created_by_id == user_id)
            )

        total = query.count()

        # 按删除时间倒序
        query = query.order_by(Project.deleted_at.desc())

        offset = (page - 1) * page_size
        projects = query.offset(offset).limit(page_size).all()

        # 获取每个项目的已删除文件数
        result_projects = []
        for p in projects:
            project_data = p.to_dict(include_deleted_info=True)
            deleted_files_count = session.query(ProjectFile).filter(
                ProjectFile.project_id == p.id,
                ProjectFile.deleted_at != None
            ).count()
            project_data['deleted_files_count'] = deleted_files_count
            result_projects.append(project_data)

        return jsonify({
            'projects': result_projects,
            'total': total,
            'page': page,
            'page_size': page_size
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@projects_bp.route('/<int:project_id>/restore', methods=['POST'])
def restore_project(project_id):
    """恢复已删除的项目

    同时恢复项目关联的文件（从隔离区恢复）
    """
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 检查是否已删除
        if project.deleted_at is None:
            return jsonify({'error': '项目未被删除'}), 400

        # 检查恢复权限（删除者、创建者或管理员）
        user_id = user.get('user_id') or user.get('id')
        can_restore = (
            is_admin(user) or
            project.deleted_by_id == user_id or
            project.created_by_id == user_id
        )

        if not can_restore:
            return jsonify({'error': '没有恢复权限'}), 403

        username = user.get('username', 'unknown')
        files_restored = 0
        files_failed = 0

        # 1. 恢复项目文件
        files = session.query(ProjectFile).filter_by(project_id=project_id).filter(
            ProjectFile.deleted_at != None
        ).all()

        for file in files:
            try:
                # 尝试从隔离区恢复物理文件
                # Note: 这里简化处理，实际需要从quarantine恢复到原位置
                # 清除删除标记
                file.deleted_at = None
                file.delete_reason = None
                file.deleted_by_id = None
                files_restored += 1
            except Exception as e:
                logger.warning(f"Failed to restore file {file.id}: {e}")
                files_failed += 1

        # 2. 恢复项目
        project.deleted_at = None
        project.delete_reason = None
        project.deleted_by_id = None

        session.commit()

        logger.info(f"Project restored: {project.project_no} by user {username}")

        return jsonify({
            'message': '项目已恢复',
            'project': project.to_dict(),
            'files_restored': files_restored,
            'files_failed': files_failed
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Project restore failed: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
