"""
Tasks API Routes - 任务管理API
"""
from flask import Blueprint, request, jsonify, send_file
from models import SessionLocal
from models.task import Task, TaskStatus
from models.project import Project
from datetime import datetime
from werkzeug.utils import secure_filename
import sys
import os
import json
import uuid

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.auth import verify_token

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

# 任务附件存储路径
TASK_ATTACHMENTS_DIR = os.path.join(os.path.dirname(__file__), '../../storage/task_attachments')
os.makedirs(TASK_ATTACHMENTS_DIR, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'rar'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


def safe_parse_date(date_str):
    """安全解析日期字符串，支持多种格式"""
    if not date_str:
        return None
    try:
        # 尝试 ISO 格式 (YYYY-MM-DDTHH:MM:SS)
        return datetime.fromisoformat(date_str)
    except ValueError:
        try:
            # 尝试简单日期格式 (YYYY-MM-DD)
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None


@tasks_bp.route('/all', methods=['GET'])
def get_all_tasks():
    """获取所有项目的任务，按项目分组返回"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # 获取所有活跃项目（排除已取消和已删除的）
        projects = session.query(Project).filter(
            Project.status.notin_(['cancelled', 'deleted']),
            Project.deleted_at.is_(None)
        ).order_by(Project.planned_start_date.asc().nullslast()).all()

        result = []
        for project in projects:
            # 获取项目的所有任务
            tasks = session.query(Task).filter_by(project_id=project.id).order_by(
                Task.start_date.asc().nullslast(),
                Task.due_date.asc().nullslast()
            ).all()

            if tasks:  # 只返回有任务的项目
                result.append({
                    'project': {
                        'id': project.id,
                        'name': project.name,
                        'project_no': project.project_no,
                        'part_number': project.part_number,
                        'customer': project.customer,
                        'status': project.status,
                        'priority': project.priority,
                        'planned_start_date': project.planned_start_date.isoformat() if project.planned_start_date else None,
                        'planned_end_date': project.planned_end_date.isoformat() if project.planned_end_date else None
                    },
                    'tasks': [t.to_dict() for t in tasks]
                })

        return jsonify({
            'data': result,
            'total_projects': len(result),
            'total_tasks': sum(len(p['tasks']) for p in result)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


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

        # 获取枚举值（保持小写，与数据库枚举匹配）
        task_type = data.get('task_type', 'general').lower()
        status = data.get('status', 'pending').lower()
        priority = data.get('priority', 'normal').lower()

        task = Task(
            project_id=data['project_id'],
            task_no=task_no,
            title=data['title'],
            description=data.get('description'),
            attachments=data.get('attachments'),
            task_type=task_type,
            start_date=safe_parse_date(data.get('start_date')),
            due_date=safe_parse_date(data.get('due_date')),
            status=status,
            priority=priority,
            assigned_to_id=data.get('assigned_to_id'),
            created_by_id=user.get('user_id') or user.get('id'),
            depends_on_task_id=data.get('depends_on_task_id'),
            is_milestone=data.get('is_milestone', False),
            weight=max(1, min(10, int(data.get('weight', 1)))),
            completion_percentage=max(0, min(100, int(data.get('completion_percentage', 0)))),
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
            'title', 'description', 'attachments', 'assigned_to_id', 'depends_on_task_id',
            'is_milestone', 'reminder_enabled', 'reminder_days_before'
        ]

        for key in updateable_fields:
            if key in data:
                setattr(task, key, data[key])

        # 处理枚举字段（保持小写）
        if 'task_type' in data:
            task.task_type = data['task_type'].lower() if data['task_type'] else 'general'
        if 'status' in data:
            task.status = data['status'].lower() if data['status'] else 'pending'
        if 'priority' in data:
            task.priority = data['priority'].lower() if data['priority'] else 'normal'

        # 处理日期字段（使用安全解析）
        if 'start_date' in data:
            task.start_date = safe_parse_date(data['start_date'])
        if 'due_date' in data:
            task.due_date = safe_parse_date(data['due_date'])

        # 处理任务权重和完成度
        if 'weight' in data:
            task.weight = max(1, min(10, int(data.get('weight', 1))))
        if 'completion_percentage' in data:
            task.completion_percentage = max(0, min(100, int(data.get('completion_percentage', 0))))
            # 如果完成度100%，自动设置为完成状态
            if task.completion_percentage == 100 and task.status != 'completed':
                task.status = 'completed'
                task.completed_at = datetime.now()

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

        task.status = 'completed'  # 使用小写字符串
        task.completed_at = datetime.now()

        # 更新项目进度
        project = session.query(Project).filter_by(id=task.project_id).first()
        if project:
            # 计算项目下所有任务的完成比例
            total_tasks = session.query(Task).filter_by(project_id=project.id).count()
            completed_tasks = session.query(Task).filter_by(
                project_id=project.id,
                status='completed'
            ).count()

            if total_tasks > 0:
                project.progress = int((completed_tasks / total_tasks) * 100)

                # 如果所有任务完成，自动更新项目状态
                if project.progress == 100:
                    project.status = 'completed'

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


# ============================================================
# 任务导向项目管理 API
# ============================================================

@tasks_bp.route('/project/<int:project_id>/kanban', methods=['GET'])
def get_kanban_tasks(project_id):
    """获取看板视图数据（按状态分组）"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        # Check project exists
        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        tasks = session.query(Task).filter_by(project_id=project_id).all()

        # 按状态分组
        kanban_data = {
            'pending': [],
            'in_progress': [],
            'blocked': [],
            'completed': [],
            'cancelled': []
        }

        for task in tasks:
            # 获取状态值
            if hasattr(task.status, 'value'):
                status = task.status.value
            else:
                status = str(task.status).lower()

            if status in kanban_data:
                kanban_data[status].append(task.to_dict())

        return jsonify({
            'columns': [
                {'key': 'pending', 'title': '待开始', 'tasks': kanban_data['pending'], 'count': len(kanban_data['pending'])},
                {'key': 'in_progress', 'title': '进行中', 'tasks': kanban_data['in_progress'], 'count': len(kanban_data['in_progress'])},
                {'key': 'blocked', 'title': '受阻', 'tasks': kanban_data['blocked'], 'count': len(kanban_data['blocked'])},
                {'key': 'completed', 'title': '已完成', 'tasks': kanban_data['completed'], 'count': len(kanban_data['completed'])},
            ],
            'total': len(tasks)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/progress', methods=['PUT'])
def update_task_progress(task_id):
    """更新任务完成百分比"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'completion_percentage' not in data:
        return jsonify({'error': '缺少完成百分比'}), 400

    progress = max(0, min(100, int(data.get('completion_percentage', 0))))

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        task.completion_percentage = progress

        # 如果达到100%，自动设置为完成状态
        if progress == 100:
            task.status = 'completed'
            task.completed_at = datetime.now()
        elif progress > 0 and task.status.value == 'pending':
            task.status = 'in_progress'

        # 更新阶段和项目进度
        from services.progress_calculator import ProgressCalculator
        ProgressCalculator.update_all_progress(session, task.project_id)

        session.commit()
        session.refresh(task)

        return jsonify(task.to_dict()), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/move-to-phase', methods=['POST'])
def move_task_to_phase(task_id):
    """移动任务到指定阶段"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    phase_id = data.get('phase_id')  # None 表示移出阶段

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # 验证阶段是否属于同一项目
        if phase_id:
            from models.project_phase import ProjectPhase
            phase = session.query(ProjectPhase).filter_by(id=phase_id).first()
            if not phase:
                return jsonify({'error': '阶段不存在'}), 404
            if phase.project_id != task.project_id:
                return jsonify({'error': '阶段不属于当前项目'}), 400

        old_phase_id = task.phase_id
        task.phase_id = phase_id

        # 更新进度
        from services.progress_calculator import ProgressCalculator
        ProgressCalculator.update_all_progress(session, task.project_id)

        session.commit()
        session.refresh(task)

        return jsonify({
            'message': '任务已移动',
            'task': task.to_dict(),
            'old_phase_id': old_phase_id,
            'new_phase_id': phase_id
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """更新任务状态（看板拖拽）"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': '缺少状态'}), 400

    new_status = data.get('status', '').lower()
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled', 'blocked']
    if new_status not in valid_statuses:
        return jsonify({'error': f'无效状态，有效值: {valid_statuses}'}), 400

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        old_status = task.status.value if hasattr(task.status, 'value') else str(task.status)
        task.status = new_status

        # 状态变化逻辑
        if new_status == 'completed':
            task.completed_at = datetime.now()
            task.completion_percentage = 100
        elif new_status == 'in_progress' and (task.completion_percentage or 0) == 0:
            task.completion_percentage = 10  # 开始时设置初始进度

        # 更新进度
        from services.progress_calculator import ProgressCalculator
        ProgressCalculator.update_all_progress(session, task.project_id)

        session.commit()
        session.refresh(task)

        return jsonify({
            'message': '状态已更新',
            'task': task.to_dict(),
            'old_status': old_status,
            'new_status': new_status
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


# ============================================================
# 任务附件管理 API
# ============================================================

@tasks_bp.route('/<int:task_id>/attachments', methods=['GET'])
def get_task_attachments(task_id):
    """获取任务附件列表"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # 解析附件 JSON
        attachments = []
        if task.attachments:
            try:
                attachments = json.loads(task.attachments) if isinstance(task.attachments, str) else task.attachments
            except:
                pass

        return jsonify({'attachments': attachments}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/attachments', methods=['POST'])
def upload_task_attachment(task_id):
    """上传任务附件"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'不支持的文件类型，允许: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # 生成唯一文件名
        original_filename = secure_filename(file.filename)
        # 保留中文文件名
        if not original_filename or original_filename == '_':
            original_filename = file.filename
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        unique_id = str(uuid.uuid4())[:8]
        stored_filename = f"{task_id}_{unique_id}.{file_ext}"

        # 保存文件
        file_path = os.path.join(TASK_ATTACHMENTS_DIR, stored_filename)
        file.save(file_path)

        # 获取文件大小
        file_size = os.path.getsize(file_path)

        # 更新任务附件列表
        attachments = []
        if task.attachments:
            try:
                attachments = json.loads(task.attachments) if isinstance(task.attachments, str) else task.attachments
            except:
                pass

        new_attachment = {
            'id': unique_id,
            'name': original_filename,
            'stored_name': stored_filename,
            'size': file_size,
            'type': file_ext,
            'url': f'/api/tasks/{task_id}/attachments/{unique_id}/download',
            'uploaded_at': datetime.now().isoformat(),
            'uploaded_by': user.get('username', 'unknown')
        }
        attachments.append(new_attachment)

        task.attachments = json.dumps(attachments, ensure_ascii=False)
        session.commit()

        return jsonify({
            'message': '上传成功',
            'attachment': new_attachment
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/attachments/<attachment_id>/download', methods=['GET'])
def download_task_attachment(task_id, attachment_id):
    """下载任务附件"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # 查找附件
        attachments = []
        if task.attachments:
            try:
                attachments = json.loads(task.attachments) if isinstance(task.attachments, str) else task.attachments
            except:
                pass

        attachment = next((a for a in attachments if a.get('id') == attachment_id), None)
        if not attachment:
            return jsonify({'error': '附件不存在'}), 404

        file_path = os.path.join(TASK_ATTACHMENTS_DIR, attachment['stored_name'])
        if not os.path.exists(file_path):
            return jsonify({'error': '文件不存在'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=attachment['name']
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/attachments/<attachment_id>', methods=['DELETE'])
def delete_task_attachment(task_id, attachment_id):
    """删除任务附件"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        # 查找并删除附件
        attachments = []
        if task.attachments:
            try:
                attachments = json.loads(task.attachments) if isinstance(task.attachments, str) else task.attachments
            except:
                pass

        attachment = next((a for a in attachments if a.get('id') == attachment_id), None)
        if not attachment:
            return jsonify({'error': '附件不存在'}), 404

        # 删除文件
        file_path = os.path.join(TASK_ATTACHMENTS_DIR, attachment['stored_name'])
        if os.path.exists(file_path):
            os.remove(file_path)

        # 更新附件列表
        attachments = [a for a in attachments if a.get('id') != attachment_id]
        task.attachments = json.dumps(attachments, ensure_ascii=False)
        session.commit()

        return jsonify({'message': '删除成功'}), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


@tasks_bp.route('/<int:task_id>/description', methods=['PUT'])
def update_task_description(task_id):
    """快速更新任务描述"""
    user = get_current_user()
    if not user:
        return jsonify({'error': '未授权'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': '缺少数据'}), 400

    session = SessionLocal()
    try:
        task = session.query(Task).filter_by(id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        task.description = data.get('description', '')
        session.commit()
        session.refresh(task)

        return jsonify({
            'message': '描述已更新',
            'task': task.to_dict()
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()
