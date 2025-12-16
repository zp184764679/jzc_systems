"""
Tasks API Routes - 任务管理API
"""
from flask import Blueprint, request, jsonify
from models import SessionLocal
from models.task import Task, TaskStatus
from models.project import Project
from datetime import datetime
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


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


@tasks_bp.route('/project/<int:project_id>', methods=['GET'])
def get_project_tasks(project_id):
    """获取项目的所有任务"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Check project exists
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # Get tasks
        query = session.query(Task).filter_by(project_id=project_id)

        # Apply filters
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)

        assigned_to = request.args.get('assigned_to')
        if assigned_to:
            query = query.filter_by(assigned_to_id=int(assigned_to))

        priority = request.args.get('priority')
        if priority:
            query = query.filter_by(priority=priority)

        tasks = query.order_by(Task.created_at.desc()).all()

        return jsonify({
            'tasks': [t.to_dict() for t in tasks],
            'total': len(tasks)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        return jsonify(task.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('', methods=['POST'])
def create_task():
    """创建任务"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'project_id' not in data or 'title' not in data:
        return jsonify({'error': '缺少必要字段'}), 400

    session = SessionLocal()
    try:
        # Check project exists
        project = session.query(Project).filter_by(id=data['project_id']).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # Generate task number
        task_no = f"TASK{datetime.now().strftime('%Y%m%d%H%M%S')}"

        task = Task(
            project_id=data['project_id'],
            task_no=task_no,
            title=data['title'],
            description=data.get('description'),
            task_type=data.get('task_type', 'other'),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'normal'),
            assigned_to_id=data.get('assigned_to_id'),
            created_by_id=user.get('user_id') or user.get('id'),
            depends_on_task_id=data.get('depends_on_task_id'),
            is_milestone=data.get('is_milestone', False),
        )

        session.add(task)
        session.commit()
        session.refresh(task)

        return jsonify(task.to_dict()), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # Update fields
        updateable_fields = [
            'title', 'description', 'task_type', 'status', 'priority',
            'assigned_to_id', 'depends_on_task_id', 'is_milestone',
            'reminder_enabled', 'reminder_days_before'
        ]

        for key in updateable_fields:
            if key in data:
                setattr(task, key, data[key])

        # Handle dates
        if 'start_date' in data:
            task.start_date = datetime.fromisoformat(data['start_date']) if data['start_date'] else None
        if 'due_date' in data:
            task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None

        session.commit()
        session.refresh(task)

        return jsonify(task.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/assign', methods=['POST'])
def assign_task(task_id):
    """分配任务"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'assigned_to_id' not in data:
        return jsonify({'error': '缺少分配用户ID'}), 400

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        task.assigned_to_id = data['assigned_to_id']

        # TODO: 发送任务分配通知

        session.commit()
        session.refresh(task)

        return jsonify(task.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """完成任务"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        # TODO: 发送任务完成通知
        # TODO: 更新项目进度

        session.commit()
        session.refresh(task)

        return jsonify(task.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/batch-update', methods=['POST'])
def batch_update_tasks():
    """批量更新任务"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'task_ids' not in data or 'updates' not in data:
        return jsonify({'error': '缺少必要字段'}), 400

    session = SessionLocal()
    try:
        task_ids = data['task_ids']
        updates = data['updates']

        tasks = session.query(Task).filter(Task.id.in_(task_ids)).all()

        for task in tasks:
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)

        session.commit()

        return jsonify({
            'message': f'成功更新 {len(tasks)} 个任务',
            'updated_count': len(tasks)
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # TODO: 检查用户是否有删除权限

        session.delete(task)
        session.commit()

        return jsonify({'message': '任务已删除'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
