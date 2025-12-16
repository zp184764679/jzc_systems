from flask import Blueprint, request, jsonify
from app import db
from app.models import Task, ProductionPlan
from app.models.task import PRIORITY_ORDER
from datetime import datetime, timedelta, date
from sqlalchemy import and_, or_

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('', methods=['GET'])
def get_tasks():
    """获取待办事项列表"""
    status = request.args.get('status')
    priority = request.args.get('priority')
    assigned_to = request.args.get('assigned_to', type=int)
    department = request.args.get('department')
    due_date = request.args.get('due_date')  # today, week, overdue
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Task.query

    # 过滤条件
    if status:
        query = query.filter(Task.status == status)
    else:
        # 默认不显示已完成和已取消
        query = query.filter(Task.status.notin_(['completed', 'cancelled']))

    if priority:
        query = query.filter(Task.priority == priority)

    if assigned_to:
        query = query.filter(Task.assigned_to_user_id == assigned_to)

    if department:
        query = query.filter(Task.assigned_to_dept == department)

    if due_date:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        if due_date == 'today':
            query = query.filter(Task.due_date.between(today_start, today_end))
        elif due_date == 'week':
            week_end = datetime.combine(today + timedelta(days=7), datetime.max.time())
            query = query.filter(Task.due_date.between(today_start, week_end))
        elif due_date == 'overdue':
            query = query.filter(Task.due_date < today_start)

    if search:
        search_term = f'%{search}%'
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.task_no.ilike(search_term),
                Task.order_no.ilike(search_term)
            )
        )

    # 排序：优先级 > 截止日期
    query = query.order_by(
        db.case(
            (Task.priority == 'urgent', 1),
            (Task.priority == 'high', 2),
            (Task.priority == 'normal', 3),
            (Task.priority == 'low', 4),
            else_=5
        ),
        Task.due_date.asc()
    )

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'tasks': [t.to_dict() for t in pagination.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取单个待办事项"""
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict())


@tasks_bp.route('', methods=['POST'])
def create_task():
    """创建待办事项"""
    data = request.get_json()

    # 生成任务编号
    today = date.today()
    count = Task.query.filter(
        Task.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    task_no = f'TASK-{today.strftime("%Y%m%d")}-{count + 1:03d}'

    task = Task(
        task_no=task_no,
        title=data.get('title'),
        description=data.get('description'),
        task_type=data.get('task_type'),
        order_id=data.get('order_id'),
        order_no=data.get('order_no'),
        plan_id=data.get('plan_id'),
        step_id=data.get('step_id'),
        due_date=datetime.fromisoformat(data.get('due_date')) if data.get('due_date') else None,
        remind_before_hours=data.get('remind_before_hours', 24),
        assigned_to_user_id=data.get('assigned_to_user_id'),
        assigned_to_name=data.get('assigned_to_name'),
        assigned_to_dept=data.get('assigned_to_dept'),
        created_by_user_id=data.get('created_by_user_id'),
        created_by_name=data.get('created_by_name'),
        priority=data.get('priority', 'normal')
    )

    db.session.add(task)
    db.session.commit()

    return jsonify(task.to_dict()), 201


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新待办事项"""
    task = Task.query.get_or_404(task_id)
    data = request.get_json()

    # 更新字段
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'task_type' in data:
        task.task_type = data['task_type']
    if 'due_date' in data:
        task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
    if 'remind_before_hours' in data:
        task.remind_before_hours = data['remind_before_hours']
    if 'assigned_to_user_id' in data:
        task.assigned_to_user_id = data['assigned_to_user_id']
    if 'assigned_to_name' in data:
        task.assigned_to_name = data['assigned_to_name']
    if 'assigned_to_dept' in data:
        task.assigned_to_dept = data['assigned_to_dept']
    if 'priority' in data:
        task.priority = data['priority']

    # 状态变更处理
    if 'status' in data:
        new_status = data['status']
        if new_status == 'in_progress' and task.status == 'pending':
            task.started_at = datetime.now()
        elif new_status == 'completed':
            task.completed_at = datetime.now()
        task.status = new_status

    db.session.commit()

    return jsonify(task.to_dict())


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除待办事项"""
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()

    return jsonify({'message': 'Task deleted successfully'})


@tasks_bp.route('/batch-status', methods=['PUT'])
def batch_update_status():
    """批量更新任务状态"""
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    new_status = data.get('status')

    if not task_ids or not new_status:
        return jsonify({'error': 'task_ids and status are required'}), 400

    tasks = Task.query.filter(Task.id.in_(task_ids)).all()

    for task in tasks:
        if new_status == 'in_progress' and task.status == 'pending':
            task.started_at = datetime.now()
        elif new_status == 'completed':
            task.completed_at = datetime.now()
        task.status = new_status

    db.session.commit()

    return jsonify({
        'message': f'Updated {len(tasks)} tasks',
        'updated_ids': [t.id for t in tasks]
    })


@tasks_bp.route('/calendar', methods=['GET'])
def get_calendar_tasks():
    """获取日历视图的任务数据"""
    year = request.args.get('year', date.today().year, type=int)
    month = request.args.get('month', date.today().month, type=int)

    # 获取月份的开始和结束
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)

    tasks = Task.query.filter(
        Task.due_date.between(start_date, end_date)
    ).order_by(Task.due_date).all()

    # 按日期分组
    calendar_data = {}
    for task in tasks:
        day = task.due_date.day
        if day not in calendar_data:
            calendar_data[day] = []
        calendar_data[day].append({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'priority': task.priority,
            'is_overdue': task.is_overdue
        })

    return jsonify({
        'year': year,
        'month': month,
        'data': calendar_data
    })


@tasks_bp.route('/stats', methods=['GET'])
def get_task_stats():
    """获取任务统计"""
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    # 各状态统计
    status_stats = db.session.query(
        Task.status,
        db.func.count(Task.id)
    ).group_by(Task.status).all()

    # 今日到期
    due_today = Task.query.filter(
        Task.due_date.between(today_start, today_end),
        Task.status.notin_(['completed', 'cancelled'])
    ).count()

    # 已逾期
    overdue = Task.query.filter(
        Task.due_date < today_start,
        Task.status.notin_(['completed', 'cancelled'])
    ).count()

    # 本周完成
    week_start = today - timedelta(days=today.weekday())
    completed_this_week = Task.query.filter(
        Task.status == 'completed',
        Task.completed_at >= datetime.combine(week_start, datetime.min.time())
    ).count()

    return jsonify({
        'status_distribution': {s: c for s, c in status_stats},
        'due_today': due_today,
        'overdue': overdue,
        'completed_this_week': completed_this_week
    })
