"""
Projects API Routes - 项目管理API
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
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

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
    """获取项目列表（支持分页和筛选）"""
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

        # 构建查询
        query = session.query(Project)

        # 应用筛选
        if status:
            query = query.filter(Project.status == status)
        if priority:
            query = query.filter(Project.priority == priority)
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Project.name.ilike(search_pattern)) |
                (Project.customer.ilike(search_pattern)) |
                (Project.order_no.ilike(search_pattern))
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
            'order_no', 'status', 'priority', 'progress_percentage', 'manager_id'
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
    """删除项目（包含级联删除）"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 检查删除权限（需要 owner 或 manager 角色）
        has_permission, role = check_project_permission(session, project_id, user, 'manager')
        if not has_permission:
            return jsonify({'error': '没有删除权限'}), 403

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

        # 删除文件记录（物理文件保留，可手动清理）
        files = session.query(ProjectFile).filter_by(project_id=project_id).all()
        for file in files:
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
        session.delete(project)
        session.commit()

        return jsonify({
            'message': '项目已删除',
            'deleted': deleted_counts
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
