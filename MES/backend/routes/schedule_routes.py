# MES 生产排程 API
# Production Scheduling API for MES

from flask import Blueprint, request, jsonify
from database import db
from models import (
    ProductionSchedule, ScheduleTask, MachineCapacity,
    ScheduleStatus, TaskStatus,
    generate_schedule_code,
    SCHEDULE_STATUS_LABELS, TASK_STATUS_LABELS,
    WorkOrder, WorkOrderProcess
)
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_

bp = Blueprint('schedule', __name__, url_prefix='/api/schedule')


# ==================== 排程计划 API ====================

@bp.route('/schedules', methods=['GET'])
def list_schedules():
    """获取排程计划列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        search = request.args.get('search')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = ProductionSchedule.query

        if status:
            query = query.filter(ProductionSchedule.status == status)
        if search:
            query = query.filter(or_(
                ProductionSchedule.schedule_code.contains(search),
                ProductionSchedule.name.contains(search)
            ))
        if start_date:
            query = query.filter(ProductionSchedule.start_date >= start_date)
        if end_date:
            query = query.filter(ProductionSchedule.end_date <= end_date)

        query = query.order_by(ProductionSchedule.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [s.to_dict() for s in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """获取排程计划详情"""
    try:
        include_tasks = request.args.get('include_tasks', 'true').lower() == 'true'
        schedule = ProductionSchedule.query.get_or_404(schedule_id)
        return jsonify(schedule.to_dict(include_tasks=include_tasks))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules', methods=['POST'])
def create_schedule():
    """创建排程计划"""
    try:
        data = request.get_json()

        schedule = ProductionSchedule(
            schedule_code=generate_schedule_code(),
            name=data.get('name'),
            description=data.get('description'),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            status='draft',
            work_hours_per_day=data.get('work_hours_per_day', 8),
            shifts_per_day=data.get('shifts_per_day', 1),
            consider_holidays=data.get('consider_holidays', True),
            created_by=data.get('created_by')
        )

        db.session.add(schedule)
        db.session.commit()

        return jsonify(schedule.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """更新排程计划"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        if schedule.status not in ['draft']:
            return jsonify({'error': '只有草稿状态的排程可以编辑'}), 400

        data = request.get_json()

        if 'name' in data:
            schedule.name = data['name']
        if 'description' in data:
            schedule.description = data['description']
        if 'start_date' in data:
            schedule.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            schedule.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'work_hours_per_day' in data:
            schedule.work_hours_per_day = data['work_hours_per_day']
        if 'shifts_per_day' in data:
            schedule.shifts_per_day = data['shifts_per_day']
        if 'consider_holidays' in data:
            schedule.consider_holidays = data['consider_holidays']

        db.session.commit()
        return jsonify(schedule.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """删除排程计划"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        if schedule.status not in ['draft', 'cancelled']:
            return jsonify({'error': '只有草稿或已取消的排程可以删除'}), 400

        db.session.delete(schedule)
        db.session.commit()

        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>/confirm', methods=['POST'])
def confirm_schedule(schedule_id):
    """确认排程计划"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        if schedule.status != 'draft':
            return jsonify({'error': '只有草稿状态的排程可以确认'}), 400

        if schedule.total_tasks == 0:
            return jsonify({'error': '排程计划中没有任务，无法确认'}), 400

        data = request.get_json() or {}

        schedule.status = 'confirmed'
        schedule.confirmed_at = datetime.utcnow()
        schedule.confirmed_by = data.get('confirmed_by')

        # 更新所有任务状态为已排程
        ScheduleTask.query.filter_by(schedule_id=schedule_id).update({
            'status': 'scheduled'
        })

        db.session.commit()
        return jsonify(schedule.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>/start', methods=['POST'])
def start_schedule(schedule_id):
    """开始执行排程"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        if schedule.status != 'confirmed':
            return jsonify({'error': '只有已确认的排程可以开始执行'}), 400

        schedule.status = 'in_progress'
        db.session.commit()
        return jsonify(schedule.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>/complete', methods=['POST'])
def complete_schedule(schedule_id):
    """完成排程"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        if schedule.status != 'in_progress':
            return jsonify({'error': '只有执行中的排程可以完成'}), 400

        schedule.status = 'completed'
        db.session.commit()
        return jsonify(schedule.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>/cancel', methods=['POST'])
def cancel_schedule(schedule_id):
    """取消排程"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        if schedule.status in ['completed', 'cancelled']:
            return jsonify({'error': '已完成或已取消的排程无法取消'}), 400

        schedule.status = 'cancelled'

        # 取消所有未完成的任务
        ScheduleTask.query.filter(
            ScheduleTask.schedule_id == schedule_id,
            ScheduleTask.status.notin_(['completed', 'cancelled'])
        ).update({'status': 'cancelled'}, synchronize_session=False)

        db.session.commit()
        return jsonify(schedule.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 排程任务 API ====================

@bp.route('/schedules/<int:schedule_id>/tasks', methods=['GET'])
def list_schedule_tasks(schedule_id):
    """获取排程任务列表"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        status = request.args.get('status')
        machine_id = request.args.get('machine_id', type=int)

        query = ScheduleTask.query.filter_by(schedule_id=schedule_id)

        if status:
            query = query.filter(ScheduleTask.status == status)
        if machine_id:
            query = query.filter(ScheduleTask.machine_id == machine_id)

        tasks = query.order_by(ScheduleTask.planned_start).all()

        return jsonify({
            'items': [t.to_dict() for t in tasks],
            'total': len(tasks)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>/tasks', methods=['POST'])
def add_schedule_task(schedule_id):
    """添加排程任务"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        if schedule.status not in ['draft']:
            return jsonify({'error': '只有草稿状态的排程可以添加任务'}), 400

        data = request.get_json()

        task = ScheduleTask(
            schedule_id=schedule_id,
            work_order_id=data['work_order_id'],
            work_order_no=data.get('work_order_no'),
            work_order_process_id=data.get('work_order_process_id'),
            process_id=data.get('process_id'),
            process_code=data.get('process_code'),
            process_name=data.get('process_name'),
            step_no=data.get('step_no', 1),
            product_code=data.get('product_code'),
            product_name=data.get('product_name'),
            machine_id=data.get('machine_id'),
            machine_code=data.get('machine_code'),
            machine_name=data.get('machine_name'),
            operator_id=data.get('operator_id'),
            operator_name=data.get('operator_name'),
            planned_start=datetime.fromisoformat(data['planned_start']),
            planned_end=datetime.fromisoformat(data['planned_end']),
            planned_hours=data.get('planned_hours', 0),
            planned_quantity=data.get('planned_quantity', 0),
            priority=data.get('priority', 3),
            dependencies=data.get('dependencies'),
            remark=data.get('remark')
        )

        db.session.add(task)

        # 更新排程统计
        schedule.total_tasks += 1
        schedule.total_hours += task.planned_hours or 0

        db.session.commit()
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新排程任务"""
    try:
        task = ScheduleTask.query.get_or_404(task_id)
        schedule = ProductionSchedule.query.get(task.schedule_id)

        if schedule.status not in ['draft']:
            if task.is_locked:
                return jsonify({'error': '任务已锁定，无法修改'}), 400

        data = request.get_json()

        old_hours = task.planned_hours or 0

        if 'machine_id' in data:
            task.machine_id = data['machine_id']
            task.machine_code = data.get('machine_code')
            task.machine_name = data.get('machine_name')
        if 'operator_id' in data:
            task.operator_id = data['operator_id']
            task.operator_name = data.get('operator_name')
        if 'planned_start' in data:
            task.planned_start = datetime.fromisoformat(data['planned_start'])
        if 'planned_end' in data:
            task.planned_end = datetime.fromisoformat(data['planned_end'])
        if 'planned_hours' in data:
            task.planned_hours = data['planned_hours']
        if 'priority' in data:
            task.priority = data['priority']
        if 'is_locked' in data:
            task.is_locked = data['is_locked']
        if 'remark' in data:
            task.remark = data['remark']

        # 更新排程统计
        new_hours = task.planned_hours or 0
        schedule.total_hours += (new_hours - old_hours)

        db.session.commit()
        return jsonify(task.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除排程任务"""
    try:
        task = ScheduleTask.query.get_or_404(task_id)
        schedule = ProductionSchedule.query.get(task.schedule_id)

        if schedule.status not in ['draft']:
            return jsonify({'error': '只有草稿状态的排程可以删除任务'}), 400

        # 更新排程统计
        schedule.total_tasks -= 1
        schedule.total_hours -= (task.planned_hours or 0)

        db.session.delete(task)
        db.session.commit()

        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """开始执行任务"""
    try:
        task = ScheduleTask.query.get_or_404(task_id)

        if task.status not in ['planned', 'scheduled']:
            return jsonify({'error': '只有已计划或已排程的任务可以开始'}), 400

        data = request.get_json() or {}

        task.status = 'in_progress'
        task.actual_start = datetime.utcnow()

        if 'operator_id' in data:
            task.operator_id = data['operator_id']
            task.operator_name = data.get('operator_name')

        db.session.commit()
        return jsonify(task.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """完成任务"""
    try:
        task = ScheduleTask.query.get_or_404(task_id)
        schedule = ProductionSchedule.query.get(task.schedule_id)

        if task.status != 'in_progress':
            return jsonify({'error': '只有执行中的任务可以完成'}), 400

        data = request.get_json() or {}

        task.status = 'completed'
        task.actual_end = datetime.utcnow()
        task.completed_quantity = data.get('completed_quantity', task.planned_quantity)

        # 计算实际工时
        if task.actual_start:
            delta = task.actual_end - task.actual_start
            task.actual_hours = round(delta.total_seconds() / 3600, 2)

        # 更新排程完成数
        schedule.completed_tasks += 1

        db.session.commit()
        return jsonify(task.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 甘特图 API ====================

@bp.route('/schedules/<int:schedule_id>/gantt', methods=['GET'])
def get_gantt_data(schedule_id):
    """获取甘特图数据"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        group_by = request.args.get('group_by', 'machine')  # machine, work_order, date

        tasks = ScheduleTask.query.filter_by(schedule_id=schedule_id)\
            .order_by(ScheduleTask.planned_start).all()

        gantt_items = [t.to_gantt_item() for t in tasks]

        # 按分组方式组织数据
        if group_by == 'machine':
            # 按设备分组
            machines = {}
            for item in gantt_items:
                machine_key = item.get('machine_id') or 'unassigned'
                if machine_key not in machines:
                    machines[machine_key] = {
                        'id': machine_key,
                        'name': item.get('machine') or '未分配设备',
                        'tasks': []
                    }
                machines[machine_key]['tasks'].append(item)
            groups = list(machines.values())
        elif group_by == 'work_order':
            # 按工单分组
            work_orders = {}
            for item in gantt_items:
                wo_key = item.get('work_order_id')
                if wo_key not in work_orders:
                    work_orders[wo_key] = {
                        'id': wo_key,
                        'name': item.get('work_order_no'),
                        'tasks': []
                    }
                work_orders[wo_key]['tasks'].append(item)
            groups = list(work_orders.values())
        else:
            groups = [{'id': 'all', 'name': '所有任务', 'tasks': gantt_items}]

        return jsonify({
            'schedule': {
                'id': schedule.id,
                'name': schedule.name,
                'start_date': schedule.start_date.strftime('%Y-%m-%d'),
                'end_date': schedule.end_date.strftime('%Y-%m-%d'),
                'status': schedule.status
            },
            'groups': groups,
            'total_tasks': len(gantt_items)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 自动排程 API ====================

@bp.route('/schedules/<int:schedule_id>/auto-schedule', methods=['POST'])
def auto_schedule(schedule_id):
    """自动排程算法"""
    try:
        schedule = ProductionSchedule.query.get_or_404(schedule_id)

        if schedule.status not in ['draft']:
            return jsonify({'error': '只有草稿状态的排程可以执行自动排程'}), 400

        data = request.get_json() or {}

        # 获取要排程的工单列表
        work_order_ids = data.get('work_order_ids', [])
        if not work_order_ids:
            # 获取待排程的工单
            work_orders = WorkOrder.query.filter(
                WorkOrder.status.in_(['created', 'released']),
                WorkOrder.planned_start >= schedule.start_date,
                WorkOrder.planned_end <= schedule.end_date
            ).order_by(WorkOrder.priority.desc(), WorkOrder.planned_start).all()
            work_order_ids = [wo.id for wo in work_orders]

        if not work_order_ids:
            return jsonify({'error': '没有可排程的工单'}), 400

        # 获取设备列表（从EAM）
        machines = data.get('machines', [])

        # 清除现有任务
        ScheduleTask.query.filter_by(schedule_id=schedule_id).delete()
        schedule.total_tasks = 0
        schedule.total_hours = 0

        # 简单的排程算法：按优先级和计划开始时间顺序排程
        current_time = datetime.combine(schedule.start_date, datetime.min.time().replace(hour=8))
        work_hours = schedule.work_hours_per_day

        tasks_created = 0

        for wo_id in work_order_ids:
            work_order = WorkOrder.query.get(wo_id)
            if not work_order:
                continue

            # 获取工单的工序
            processes = WorkOrderProcess.query.filter_by(work_order_id=wo_id)\
                .order_by(WorkOrderProcess.step_no).all()

            if not processes:
                # 如果没有工序，创建一个整体任务
                duration_hours = 8  # 默认8小时
                task = ScheduleTask(
                    schedule_id=schedule_id,
                    work_order_id=wo_id,
                    work_order_no=work_order.order_no,
                    process_name='生产',
                    product_code=work_order.product_code,
                    product_name=work_order.product_name,
                    planned_start=current_time,
                    planned_end=current_time + timedelta(hours=duration_hours),
                    planned_hours=duration_hours,
                    planned_quantity=work_order.planned_quantity,
                    priority=work_order.priority or 3
                )
                db.session.add(task)
                tasks_created += 1
                current_time += timedelta(hours=duration_hours)
            else:
                # 按工序排程
                for proc in processes:
                    duration_hours = proc.planned_hours or 4  # 默认4小时

                    task = ScheduleTask(
                        schedule_id=schedule_id,
                        work_order_id=wo_id,
                        work_order_no=work_order.order_no,
                        work_order_process_id=proc.id,
                        process_id=proc.process_id,
                        process_name=proc.process_name,
                        step_no=proc.step_no,
                        product_code=work_order.product_code,
                        product_name=work_order.product_name,
                        machine_id=proc.machine_id,
                        planned_start=current_time,
                        planned_end=current_time + timedelta(hours=duration_hours),
                        planned_hours=duration_hours,
                        planned_quantity=work_order.planned_quantity,
                        priority=work_order.priority or 3
                    )
                    db.session.add(task)
                    tasks_created += 1
                    current_time += timedelta(hours=duration_hours)

        # 更新排程统计
        schedule.total_tasks = tasks_created

        db.session.commit()

        return jsonify({
            'message': f'自动排程完成，共创建 {tasks_created} 个任务',
            'tasks_created': tasks_created,
            'schedule': schedule.to_dict(include_tasks=True)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 设备产能 API ====================

@bp.route('/machine-capacities', methods=['GET'])
def list_machine_capacities():
    """获取设备产能列表"""
    try:
        machine_id = request.args.get('machine_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = MachineCapacity.query

        if machine_id:
            query = query.filter(MachineCapacity.machine_id == machine_id)
        if start_date:
            query = query.filter(MachineCapacity.date >= start_date)
        if end_date:
            query = query.filter(MachineCapacity.date <= end_date)

        capacities = query.order_by(MachineCapacity.date).all()

        return jsonify({
            'items': [c.to_dict() for c in capacities],
            'total': len(capacities)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/machine-capacities', methods=['POST'])
def create_machine_capacity():
    """创建/更新设备产能"""
    try:
        data = request.get_json()

        machine_id = data['machine_id']
        capacity_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

        # 查找是否已存在
        capacity = MachineCapacity.query.filter_by(
            machine_id=machine_id,
            date=capacity_date
        ).first()

        if capacity:
            # 更新
            capacity.available_hours = data.get('available_hours', capacity.available_hours)
            capacity.is_available = data.get('is_available', capacity.is_available)
            capacity.unavailable_reason = data.get('unavailable_reason')
        else:
            # 创建
            capacity = MachineCapacity(
                machine_id=machine_id,
                machine_code=data.get('machine_code'),
                machine_name=data.get('machine_name'),
                date=capacity_date,
                available_hours=data.get('available_hours', 8),
                is_available=data.get('is_available', True),
                unavailable_reason=data.get('unavailable_reason')
            )
            db.session.add(capacity)

        db.session.commit()
        return jsonify(capacity.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/machine-capacities/batch', methods=['POST'])
def batch_create_capacities():
    """批量创建设备产能（指定日期范围）"""
    try:
        data = request.get_json()

        machine_id = data['machine_id']
        machine_code = data.get('machine_code')
        machine_name = data.get('machine_name')
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        available_hours = data.get('available_hours', 8)

        created_count = 0
        current_date = start_date

        while current_date <= end_date:
            # 跳过已存在的
            existing = MachineCapacity.query.filter_by(
                machine_id=machine_id,
                date=current_date
            ).first()

            if not existing:
                capacity = MachineCapacity(
                    machine_id=machine_id,
                    machine_code=machine_code,
                    machine_name=machine_name,
                    date=current_date,
                    available_hours=available_hours,
                    is_available=True
                )
                db.session.add(capacity)
                created_count += 1

            current_date += timedelta(days=1)

        db.session.commit()

        return jsonify({
            'message': f'成功创建 {created_count} 条产能记录',
            'created_count': created_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== 统计 API ====================

@bp.route('/statistics/summary', methods=['GET'])
def schedule_statistics():
    """排程统计"""
    try:
        # 排程状态统计
        status_stats = db.session.query(
            ProductionSchedule.status,
            func.count(ProductionSchedule.id).label('count')
        ).group_by(ProductionSchedule.status).all()

        # 任务状态统计
        task_stats = db.session.query(
            ScheduleTask.status,
            func.count(ScheduleTask.id).label('count')
        ).group_by(ScheduleTask.status).all()

        # 本周排程
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        week_schedules = ProductionSchedule.query.filter(
            ProductionSchedule.start_date <= week_end,
            ProductionSchedule.end_date >= week_start
        ).count()

        # 延迟任务
        delayed_tasks = ScheduleTask.query.filter(
            ScheduleTask.status.notin_(['completed', 'cancelled']),
            ScheduleTask.planned_end < datetime.utcnow()
        ).count()

        return jsonify({
            'schedule_status': {s[0]: s[1] for s in status_stats},
            'task_status': {s[0]: s[1] for s in task_stats},
            'week_schedules': week_schedules,
            'delayed_tasks': delayed_tasks
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/statistics/machine-utilization', methods=['GET'])
def machine_utilization():
    """设备利用率统计"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date or not end_date:
            today = date.today()
            start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')

        # 查询设备产能和已排程时间
        capacities = MachineCapacity.query.filter(
            MachineCapacity.date >= start_date,
            MachineCapacity.date <= end_date
        ).all()

        # 按设备汇总
        machine_stats = {}
        for cap in capacities:
            if cap.machine_id not in machine_stats:
                machine_stats[cap.machine_id] = {
                    'machine_id': cap.machine_id,
                    'machine_code': cap.machine_code,
                    'machine_name': cap.machine_name,
                    'total_available': 0,
                    'total_scheduled': 0
                }
            machine_stats[cap.machine_id]['total_available'] += cap.available_hours
            machine_stats[cap.machine_id]['total_scheduled'] += cap.scheduled_hours

        # 计算利用率
        result = []
        for stats in machine_stats.values():
            if stats['total_available'] > 0:
                stats['utilization'] = round(
                    stats['total_scheduled'] / stats['total_available'] * 100, 2
                )
            else:
                stats['utilization'] = 0
            result.append(stats)

        return jsonify({
            'items': sorted(result, key=lambda x: x['utilization'], reverse=True),
            'period': {'start': start_date, 'end': end_date}
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 枚举 API ====================

@bp.route('/enums', methods=['GET'])
def get_enums():
    """获取排程相关枚举值"""
    return jsonify({
        'schedule_status': SCHEDULE_STATUS_LABELS,
        'task_status': TASK_STATUS_LABELS
    })
