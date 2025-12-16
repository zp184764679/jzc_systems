"""
Projects API Routes - 项目管理API
"""
from flask import Blueprint, request, jsonify
from models import SessionLocal
from models.project import Project
from models.task import Task
from models.project_file import ProjectFile
from models.project_member import ProjectMember
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


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
    """获取项目列表"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # TODO: 根据用户权限过滤项目
        projects = session.query(Project).all()
        return jsonify({
            'projects': [p.to_dict() for p in projects],
            'total': len(projects)
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

        # TODO: 检查用户是否有编辑权限

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
    """删除项目"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # TODO: 检查用户是否有删除权限
        # TODO: 删除关联的任务、文件、成员等

        session.delete(project)
        session.commit()

        return jsonify({'message': '项目已删除'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
