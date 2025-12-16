"""
考勤管理 API 路由
包含: 打卡、排班、加班申请、补卡申请、月度汇总
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models.attendance import (
    AttendanceRule, Shift, Schedule, AttendanceRecord,
    OvertimeRequest, AttendanceCorrection, MonthlyAttendanceSummary
)
from app.models.employee import Employee
from datetime import datetime, date, time, timedelta
from sqlalchemy import or_, and_, func
from app.routes.auth import require_auth

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')


def parse_date(date_string):
    """Parse date string to date object"""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None


def parse_time(time_string):
    """Parse time string to time object"""
    if not time_string:
        return None
    try:
        return datetime.strptime(time_string, '%H:%M').time()
    except ValueError:
        try:
            return datetime.strptime(time_string, '%H:%M:%S').time()
        except ValueError:
            return None


def parse_datetime(datetime_string):
    """Parse datetime string to datetime object"""
    if not datetime_string:
        return None
    try:
        return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            return None


def calculate_late_minutes(check_in_time, work_start_time, flexible_minutes=0):
    """计算迟到分钟数"""
    if not check_in_time or not work_start_time:
        return 0

    work_start = datetime.combine(date.today(), work_start_time)
    work_start += timedelta(minutes=flexible_minutes)
    check_in = datetime.combine(date.today(), check_in_time.time() if isinstance(check_in_time, datetime) else check_in_time)

    diff = (check_in - work_start).total_seconds() / 60
    return max(0, int(diff))


def calculate_early_leave_minutes(check_out_time, work_end_time):
    """计算早退分钟数"""
    if not check_out_time or not work_end_time:
        return 0

    work_end = datetime.combine(date.today(), work_end_time)
    check_out = datetime.combine(date.today(), check_out_time.time() if isinstance(check_out_time, datetime) else check_out_time)

    diff = (work_end - check_out).total_seconds() / 60
    return max(0, int(diff))


def calculate_work_hours(check_in_time, check_out_time, break_hours=1.0):
    """计算实际工时"""
    if not check_in_time or not check_out_time:
        return 0

    diff = (check_out_time - check_in_time).total_seconds() / 3600
    return max(0, diff - break_hours)


# ==================== 打卡 API ====================

@attendance_bp.route('/check-in', methods=['POST'])
@require_auth
def check_in(user):
    """上班打卡"""
    try:
        data = request.get_json() or {}
        employee_id = data.get('employee_id')

        # 如果没有提供 employee_id，尝试从当前用户获取
        if not employee_id:
            # 通过用户名查找员工
            employee = Employee.query.filter_by(empNo=user.get('username')).first()
            if not employee:
                return jsonify({
                    'success': False,
                    'message': '未找到关联的员工信息'
                }), 400
            employee_id = employee.id
        else:
            employee = Employee.query.get(employee_id)
            if not employee:
                return jsonify({
                    'success': False,
                    'message': '员工不存在'
                }), 404

        today = date.today()
        now = datetime.now()

        # 检查今天是否已有考勤记录
        existing_record = AttendanceRecord.query.filter_by(
            employee_id=employee_id,
            attendance_date=today
        ).first()

        if existing_record and existing_record.check_in_time:
            return jsonify({
                'success': False,
                'message': '今日已打过上班卡',
                'data': existing_record.to_dict()
            }), 400

        # 获取适用的考勤规则
        rule = AttendanceRule.query.filter(
            and_(
                AttendanceRule.is_active == True,
                or_(
                    AttendanceRule.department_id == employee.department_id,
                    AttendanceRule.department_id.is_(None)
                ),
                or_(
                    AttendanceRule.factory_id == employee.factory_id,
                    AttendanceRule.factory_id.is_(None)
                )
            )
        ).order_by(AttendanceRule.is_default.desc()).first()

        # 计算迟到
        is_late = False
        late_minutes = 0
        if rule:
            late_minutes = calculate_late_minutes(now, rule.work_start_time, rule.flexible_minutes)
            is_late = late_minutes > rule.late_threshold_minutes

        if existing_record:
            # 更新现有记录
            existing_record.check_in_time = now
            existing_record.check_in_location = data.get('location')
            existing_record.check_in_ip = request.remote_addr
            existing_record.check_in_method = data.get('method', 'web')
            existing_record.is_late = is_late
            existing_record.late_minutes = late_minutes
            existing_record.updated_at = now
            record = existing_record
        else:
            # 创建新记录
            record = AttendanceRecord(
                employee_id=employee_id,
                attendance_date=today,
                check_in_time=now,
                check_in_location=data.get('location'),
                check_in_ip=request.remote_addr,
                check_in_method=data.get('method', 'web'),
                is_late=is_late,
                late_minutes=late_minutes,
                status='normal' if not is_late else 'late'
            )
            db.session.add(record)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '上班打卡成功' + (f'，迟到 {late_minutes} 分钟' if is_late else ''),
            'data': record.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'打卡失败: {str(e)}'
        }), 500


@attendance_bp.route('/check-out', methods=['POST'])
@require_auth
def check_out(user):
    """下班打卡"""
    try:
        data = request.get_json() or {}
        employee_id = data.get('employee_id')

        if not employee_id:
            employee = Employee.query.filter_by(empNo=user.get('username')).first()
            if not employee:
                return jsonify({
                    'success': False,
                    'message': '未找到关联的员工信息'
                }), 400
            employee_id = employee.id
        else:
            employee = Employee.query.get(employee_id)
            if not employee:
                return jsonify({
                    'success': False,
                    'message': '员工不存在'
                }), 404

        today = date.today()
        now = datetime.now()

        # 查找今天的考勤记录
        record = AttendanceRecord.query.filter_by(
            employee_id=employee_id,
            attendance_date=today
        ).first()

        if not record:
            return jsonify({
                'success': False,
                'message': '今日未打上班卡，请先打上班卡'
            }), 400

        if record.check_out_time:
            return jsonify({
                'success': False,
                'message': '今日已打过下班卡',
                'data': record.to_dict()
            }), 400

        # 获取考勤规则
        rule = AttendanceRule.query.filter(
            and_(
                AttendanceRule.is_active == True,
                or_(
                    AttendanceRule.department_id == employee.department_id,
                    AttendanceRule.department_id.is_(None)
                ),
                or_(
                    AttendanceRule.factory_id == employee.factory_id,
                    AttendanceRule.factory_id.is_(None)
                )
            )
        ).order_by(AttendanceRule.is_default.desc()).first()

        # 计算早退
        is_early_leave = False
        early_leave_minutes = 0
        if rule:
            early_leave_minutes = calculate_early_leave_minutes(now, rule.work_end_time)
            is_early_leave = early_leave_minutes > rule.early_leave_threshold_minutes

        # 计算工时
        work_hours = calculate_work_hours(record.check_in_time, now)

        # 计算加班时长
        overtime_hours = 0
        if rule and work_hours > 8:
            overtime_hours = work_hours - 8

        # 更新记录
        record.check_out_time = now
        record.check_out_location = data.get('location')
        record.check_out_ip = request.remote_addr
        record.check_out_method = data.get('method', 'web')
        record.is_early_leave = is_early_leave
        record.early_leave_minutes = early_leave_minutes
        record.work_hours = round(work_hours, 2)
        record.overtime_hours = round(overtime_hours, 2)
        record.updated_at = now

        # 更新状态
        if record.is_late and is_early_leave:
            record.status = 'late_and_early_leave'
        elif is_early_leave:
            record.status = 'early_leave'

        db.session.commit()

        message = '下班打卡成功'
        if is_early_leave:
            message += f'，早退 {early_leave_minutes} 分钟'
        if overtime_hours > 0:
            message += f'，加班 {round(overtime_hours, 1)} 小时'

        return jsonify({
            'success': True,
            'message': message,
            'data': record.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'打卡失败: {str(e)}'
        }), 500


@attendance_bp.route('/today', methods=['GET'])
@require_auth
def get_today_record(user):
    """获取今日考勤状态"""
    try:
        employee_id = request.args.get('employee_id')

        if not employee_id:
            employee = Employee.query.filter_by(empNo=user.get('username')).first()
            if employee:
                employee_id = employee.id

        if not employee_id:
            return jsonify({
                'success': False,
                'message': '未找到关联的员工信息'
            }), 400

        today = date.today()
        record = AttendanceRecord.query.filter_by(
            employee_id=employee_id,
            attendance_date=today
        ).first()

        return jsonify({
            'success': True,
            'data': record.to_dict() if record else None
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


# ==================== 考勤记录查询 API ====================

@attendance_bp.route('/records', methods=['GET'])
@require_auth
def get_attendance_records(user):
    """获取考勤记录列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        department_id = request.args.get('department_id', type=int)
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))
        status = request.args.get('status')

        query = AttendanceRecord.query

        if employee_id:
            query = query.filter(AttendanceRecord.employee_id == employee_id)

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        if start_date:
            query = query.filter(AttendanceRecord.attendance_date >= start_date)

        if end_date:
            query = query.filter(AttendanceRecord.attendance_date <= end_date)

        if status:
            if status == 'late':
                query = query.filter(AttendanceRecord.is_late == True)
            elif status == 'early_leave':
                query = query.filter(AttendanceRecord.is_early_leave == True)
            elif status == 'absent':
                query = query.filter(AttendanceRecord.is_absent == True)
            elif status == 'normal':
                query = query.filter(
                    and_(
                        AttendanceRecord.is_late == False,
                        AttendanceRecord.is_early_leave == False,
                        AttendanceRecord.is_absent == False
                    )
                )

        query = query.order_by(AttendanceRecord.attendance_date.desc(), AttendanceRecord.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in pagination.items],
            'pagination': {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@attendance_bp.route('/my-records', methods=['GET'])
@require_auth
def get_my_attendance_records(user):
    """获取我的考勤记录"""
    try:
        employee = Employee.query.filter_by(empNo=user.get('username')).first()
        if not employee:
            return jsonify({
                'success': False,
                'message': '未找到关联的员工信息'
            }), 400

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        month = request.args.get('month')  # 格式: 2025-12

        query = AttendanceRecord.query.filter_by(employee_id=employee.id)

        if month:
            try:
                year, mon = map(int, month.split('-'))
                start_date = date(year, mon, 1)
                if mon == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, mon + 1, 1) - timedelta(days=1)
                query = query.filter(
                    and_(
                        AttendanceRecord.attendance_date >= start_date,
                        AttendanceRecord.attendance_date <= end_date
                    )
                )
            except:
                pass

        query = query.order_by(AttendanceRecord.attendance_date.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in pagination.items],
            'pagination': {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


# ==================== 考勤规则 API ====================

@attendance_bp.route('/rules', methods=['GET'])
@require_auth
def get_attendance_rules(user):
    """获取考勤规则列表"""
    try:
        rules = AttendanceRule.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [rule.to_dict() for rule in rules]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@attendance_bp.route('/rules', methods=['POST'])
@require_auth
def create_attendance_rule(user):
    """创建考勤规则"""
    try:
        data = request.get_json()

        if not data.get('name') or not data.get('code'):
            return jsonify({
                'success': False,
                'message': '规则名称和编码不能为空'
            }), 400

        # 检查编码是否重复
        existing = AttendanceRule.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': f'规则编码 {data["code"]} 已存在'
            }), 400

        rule = AttendanceRule(
            name=data['name'],
            code=data['code'],
            factory_id=data.get('factory_id'),
            department_id=data.get('department_id'),
            work_start_time=parse_time(data.get('work_start_time', '08:30')),
            work_end_time=parse_time(data.get('work_end_time', '17:30')),
            break_start_time=parse_time(data.get('break_start_time')),
            break_end_time=parse_time(data.get('break_end_time')),
            flexible_minutes=data.get('flexible_minutes', 0),
            late_threshold_minutes=data.get('late_threshold_minutes', 0),
            early_leave_threshold_minutes=data.get('early_leave_threshold_minutes', 0),
            absent_threshold_minutes=data.get('absent_threshold_minutes', 240),
            min_overtime_minutes=data.get('min_overtime_minutes', 30),
            require_overtime_approval=data.get('require_overtime_approval', True),
            work_days=data.get('work_days'),
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
            description=data.get('description'),
            created_by=user.get('id')
        )

        db.session.add(rule)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '考勤规则创建成功',
            'data': rule.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@attendance_bp.route('/rules/<int:id>', methods=['PUT'])
@require_auth
def update_attendance_rule(id, user):
    """更新考勤规则"""
    try:
        rule = AttendanceRule.query.get(id)
        if not rule:
            return jsonify({
                'success': False,
                'message': '规则不存在'
            }), 404

        data = request.get_json()

        if 'name' in data:
            rule.name = data['name']
        if 'factory_id' in data:
            rule.factory_id = data['factory_id']
        if 'department_id' in data:
            rule.department_id = data['department_id']
        if 'work_start_time' in data:
            rule.work_start_time = parse_time(data['work_start_time'])
        if 'work_end_time' in data:
            rule.work_end_time = parse_time(data['work_end_time'])
        if 'break_start_time' in data:
            rule.break_start_time = parse_time(data['break_start_time'])
        if 'break_end_time' in data:
            rule.break_end_time = parse_time(data['break_end_time'])
        if 'flexible_minutes' in data:
            rule.flexible_minutes = data['flexible_minutes']
        if 'late_threshold_minutes' in data:
            rule.late_threshold_minutes = data['late_threshold_minutes']
        if 'early_leave_threshold_minutes' in data:
            rule.early_leave_threshold_minutes = data['early_leave_threshold_minutes']
        if 'min_overtime_minutes' in data:
            rule.min_overtime_minutes = data['min_overtime_minutes']
        if 'require_overtime_approval' in data:
            rule.require_overtime_approval = data['require_overtime_approval']
        if 'work_days' in data:
            rule.work_days = data['work_days']
        if 'is_active' in data:
            rule.is_active = data['is_active']
        if 'is_default' in data:
            rule.is_default = data['is_default']
        if 'description' in data:
            rule.description = data['description']

        rule.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '考勤规则更新成功',
            'data': rule.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@attendance_bp.route('/rules/<int:id>', methods=['DELETE'])
@require_auth
def delete_attendance_rule(id, user):
    """删除考勤规则"""
    try:
        rule = AttendanceRule.query.get(id)
        if not rule:
            return jsonify({
                'success': False,
                'message': '规则不存在'
            }), 404

        db.session.delete(rule)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '考勤规则删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


# ==================== 班次管理 API ====================

@attendance_bp.route('/shifts', methods=['GET'])
@require_auth
def get_shifts(user):
    """获取班次列表"""
    try:
        factory_id = request.args.get('factory_id', type=int)

        query = Shift.query.filter_by(is_active=True)
        if factory_id:
            query = query.filter(
                or_(Shift.factory_id == factory_id, Shift.factory_id.is_(None))
            )

        shifts = query.all()
        return jsonify({
            'success': True,
            'data': [shift.to_dict() for shift in shifts]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@attendance_bp.route('/shifts', methods=['POST'])
@require_auth
def create_shift(user):
    """创建班次"""
    try:
        data = request.get_json()

        if not data.get('name') or not data.get('code'):
            return jsonify({
                'success': False,
                'message': '班次名称和编码不能为空'
            }), 400

        existing = Shift.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': f'班次编码 {data["code"]} 已存在'
            }), 400

        shift = Shift(
            name=data['name'],
            code=data['code'],
            shift_type=data.get('shift_type', 'regular'),
            start_time=parse_time(data.get('start_time', '08:30')),
            end_time=parse_time(data.get('end_time', '17:30')),
            cross_day=data.get('cross_day', False),
            work_hours=data.get('work_hours', 8.0),
            break_hours=data.get('break_hours', 1.0),
            color=data.get('color'),
            is_active=data.get('is_active', True),
            factory_id=data.get('factory_id')
        )

        db.session.add(shift)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '班次创建成功',
            'data': shift.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@attendance_bp.route('/shifts/<int:id>', methods=['PUT'])
@require_auth
def update_shift(id, user):
    """更新班次"""
    try:
        shift = Shift.query.get(id)
        if not shift:
            return jsonify({
                'success': False,
                'message': '班次不存在'
            }), 404

        data = request.get_json()

        if 'name' in data:
            shift.name = data['name']
        if 'shift_type' in data:
            shift.shift_type = data['shift_type']
        if 'start_time' in data:
            shift.start_time = parse_time(data['start_time'])
        if 'end_time' in data:
            shift.end_time = parse_time(data['end_time'])
        if 'cross_day' in data:
            shift.cross_day = data['cross_day']
        if 'work_hours' in data:
            shift.work_hours = data['work_hours']
        if 'break_hours' in data:
            shift.break_hours = data['break_hours']
        if 'color' in data:
            shift.color = data['color']
        if 'is_active' in data:
            shift.is_active = data['is_active']
        if 'factory_id' in data:
            shift.factory_id = data['factory_id']

        shift.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '班次更新成功',
            'data': shift.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@attendance_bp.route('/shifts/<int:id>', methods=['DELETE'])
@require_auth
def delete_shift(id, user):
    """删除班次"""
    try:
        shift = Shift.query.get(id)
        if not shift:
            return jsonify({
                'success': False,
                'message': '班次不存在'
            }), 404

        db.session.delete(shift)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '班次删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


# ==================== 排班管理 API ====================

@attendance_bp.route('/schedules', methods=['GET'])
@require_auth
def get_schedules(user):
    """获取排班列表"""
    try:
        employee_id = request.args.get('employee_id', type=int)
        department_id = request.args.get('department_id', type=int)
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))

        query = Schedule.query

        if employee_id:
            query = query.filter(Schedule.employee_id == employee_id)

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        if start_date:
            query = query.filter(Schedule.schedule_date >= start_date)

        if end_date:
            query = query.filter(Schedule.schedule_date <= end_date)

        schedules = query.order_by(Schedule.schedule_date.asc()).all()

        return jsonify({
            'success': True,
            'data': [schedule.to_dict() for schedule in schedules]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@attendance_bp.route('/schedules', methods=['POST'])
@require_auth
def create_schedule(user):
    """创建排班"""
    try:
        data = request.get_json()

        if not data.get('employee_id') or not data.get('schedule_date'):
            return jsonify({
                'success': False,
                'message': '员工ID和排班日期不能为空'
            }), 400

        employee = Employee.query.get(data['employee_id'])
        if not employee:
            return jsonify({
                'success': False,
                'message': '员工不存在'
            }), 404

        schedule_date = parse_date(data['schedule_date'])

        # 检查是否已有排班
        existing = Schedule.query.filter_by(
            employee_id=data['employee_id'],
            schedule_date=schedule_date
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'message': '该员工当日已有排班'
            }), 400

        schedule = Schedule(
            employee_id=data['employee_id'],
            shift_id=data.get('shift_id'),
            schedule_date=schedule_date,
            is_rest=data.get('is_rest', False),
            is_holiday=data.get('is_holiday', False),
            custom_start_time=parse_time(data.get('custom_start_time')),
            custom_end_time=parse_time(data.get('custom_end_time')),
            remark=data.get('remark'),
            created_by=user.get('id')
        )

        db.session.add(schedule)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '排班创建成功',
            'data': schedule.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@attendance_bp.route('/schedules/batch', methods=['POST'])
@require_auth
def create_batch_schedules(user):
    """批量创建排班"""
    try:
        data = request.get_json()

        employee_ids = data.get('employee_ids', [])
        shift_id = data.get('shift_id')
        start_date = parse_date(data.get('start_date'))
        end_date = parse_date(data.get('end_date'))
        rest_days = data.get('rest_days', [])  # 休息日，格式: ['2025-12-20', '2025-12-21']

        if not employee_ids or not start_date or not end_date:
            return jsonify({
                'success': False,
                'message': '员工列表、开始日期和结束日期不能为空'
            }), 400

        created_count = 0
        skipped_count = 0
        current_date = start_date

        while current_date <= end_date:
            is_rest = current_date.strftime('%Y-%m-%d') in rest_days or current_date.weekday() >= 5

            for emp_id in employee_ids:
                existing = Schedule.query.filter_by(
                    employee_id=emp_id,
                    schedule_date=current_date
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                schedule = Schedule(
                    employee_id=emp_id,
                    shift_id=shift_id if not is_rest else None,
                    schedule_date=current_date,
                    is_rest=is_rest,
                    created_by=user.get('id')
                )
                db.session.add(schedule)
                created_count += 1

            current_date += timedelta(days=1)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'批量排班完成，创建 {created_count} 条，跳过 {skipped_count} 条'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@attendance_bp.route('/schedules/<int:id>', methods=['PUT'])
@require_auth
def update_schedule(id, user):
    """更新排班"""
    try:
        schedule = Schedule.query.get(id)
        if not schedule:
            return jsonify({
                'success': False,
                'message': '排班不存在'
            }), 404

        data = request.get_json()

        if 'shift_id' in data:
            schedule.shift_id = data['shift_id']
        if 'is_rest' in data:
            schedule.is_rest = data['is_rest']
        if 'is_holiday' in data:
            schedule.is_holiday = data['is_holiday']
        if 'custom_start_time' in data:
            schedule.custom_start_time = parse_time(data['custom_start_time'])
        if 'custom_end_time' in data:
            schedule.custom_end_time = parse_time(data['custom_end_time'])
        if 'remark' in data:
            schedule.remark = data['remark']

        schedule.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '排班更新成功',
            'data': schedule.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@attendance_bp.route('/schedules/<int:id>', methods=['DELETE'])
@require_auth
def delete_schedule(id, user):
    """删除排班"""
    try:
        schedule = Schedule.query.get(id)
        if not schedule:
            return jsonify({
                'success': False,
                'message': '排班不存在'
            }), 404

        db.session.delete(schedule)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '排班删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


# ==================== 加班申请 API ====================

@attendance_bp.route('/overtime', methods=['GET'])
@require_auth
def get_overtime_requests(user):
    """获取加班申请列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        status = request.args.get('status')
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))

        query = OvertimeRequest.query

        if employee_id:
            query = query.filter(OvertimeRequest.employee_id == employee_id)

        if status:
            query = query.filter(OvertimeRequest.status == status)

        if start_date:
            query = query.filter(OvertimeRequest.overtime_date >= start_date)

        if end_date:
            query = query.filter(OvertimeRequest.overtime_date <= end_date)

        query = query.order_by(OvertimeRequest.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [req.to_dict() for req in pagination.items],
            'pagination': {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@attendance_bp.route('/overtime', methods=['POST'])
@require_auth
def create_overtime_request(user):
    """创建加班申请"""
    try:
        data = request.get_json()

        employee_id = data.get('employee_id')
        if not employee_id:
            employee = Employee.query.filter_by(empNo=user.get('username')).first()
            if not employee:
                return jsonify({
                    'success': False,
                    'message': '未找到关联的员工信息'
                }), 400
            employee_id = employee.id

        if not data.get('overtime_date') or not data.get('start_time') or not data.get('end_time'):
            return jsonify({
                'success': False,
                'message': '加班日期和时间不能为空'
            }), 400

        overtime_date = parse_date(data['overtime_date'])
        start_time = parse_time(data['start_time'])
        end_time = parse_time(data['end_time'])

        # 计算计划加班时长
        start_dt = datetime.combine(overtime_date, start_time)
        end_dt = datetime.combine(overtime_date, end_time)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        planned_hours = (end_dt - start_dt).total_seconds() / 3600

        overtime = OvertimeRequest(
            employee_id=employee_id,
            overtime_date=overtime_date,
            overtime_type=data.get('overtime_type', 'workday'),
            start_time=start_time,
            end_time=end_time,
            planned_hours=round(planned_hours, 2),
            reason=data.get('reason', ''),
            work_content=data.get('work_content'),
            status='pending',
            compensation_type=data.get('compensation_type')
        )

        db.session.add(overtime)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '加班申请提交成功',
            'data': overtime.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }), 500


@attendance_bp.route('/overtime/<int:id>/approve', methods=['POST'])
@require_auth
def approve_overtime(id, user):
    """审批加班申请"""
    try:
        overtime = OvertimeRequest.query.get(id)
        if not overtime:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        if overtime.status != 'pending':
            return jsonify({
                'success': False,
                'message': '该申请已处理'
            }), 400

        data = request.get_json()
        action = data.get('action')  # 'approve' or 'reject'

        if action not in ['approve', 'reject']:
            return jsonify({
                'success': False,
                'message': '无效的操作'
            }), 400

        overtime.status = 'approved' if action == 'approve' else 'rejected'
        overtime.approver_id = user.get('id')
        overtime.approved_at = datetime.utcnow()
        overtime.approval_remark = data.get('remark')

        if action == 'approve' and data.get('actual_hours'):
            overtime.actual_hours = data['actual_hours']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '审批成功',
            'data': overtime.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'审批失败: {str(e)}'
        }), 500


# ==================== 补卡申请 API ====================

@attendance_bp.route('/corrections', methods=['GET'])
@require_auth
def get_corrections(user):
    """获取补卡申请列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        status = request.args.get('status')

        query = AttendanceCorrection.query

        if employee_id:
            query = query.filter(AttendanceCorrection.employee_id == employee_id)

        if status:
            query = query.filter(AttendanceCorrection.status == status)

        query = query.order_by(AttendanceCorrection.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [req.to_dict() for req in pagination.items],
            'pagination': {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@attendance_bp.route('/corrections', methods=['POST'])
@require_auth
def create_correction(user):
    """创建补卡申请"""
    try:
        data = request.get_json()

        employee_id = data.get('employee_id')
        if not employee_id:
            employee = Employee.query.filter_by(empNo=user.get('username')).first()
            if not employee:
                return jsonify({
                    'success': False,
                    'message': '未找到关联的员工信息'
                }), 400
            employee_id = employee.id

        if not data.get('correction_date') or not data.get('correction_type') or not data.get('correction_time'):
            return jsonify({
                'success': False,
                'message': '补卡日期、类型和时间不能为空'
            }), 400

        correction = AttendanceCorrection(
            employee_id=employee_id,
            attendance_record_id=data.get('attendance_record_id'),
            correction_date=parse_date(data['correction_date']),
            correction_type=data['correction_type'],
            correction_time=parse_time(data['correction_time']),
            reason=data.get('reason', ''),
            attachment=data.get('attachment'),
            status='pending'
        )

        db.session.add(correction)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '补卡申请提交成功',
            'data': correction.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }), 500


@attendance_bp.route('/corrections/<int:id>/approve', methods=['POST'])
@require_auth
def approve_correction(id, user):
    """审批补卡申请"""
    try:
        correction = AttendanceCorrection.query.get(id)
        if not correction:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        if correction.status != 'pending':
            return jsonify({
                'success': False,
                'message': '该申请已处理'
            }), 400

        data = request.get_json()
        action = data.get('action')

        if action not in ['approve', 'reject']:
            return jsonify({
                'success': False,
                'message': '无效的操作'
            }), 400

        correction.status = 'approved' if action == 'approve' else 'rejected'
        correction.approver_id = user.get('id')
        correction.approved_at = datetime.utcnow()
        correction.approval_remark = data.get('remark')

        # 如果批准，更新考勤记录
        if action == 'approve':
            record = AttendanceRecord.query.filter_by(
                employee_id=correction.employee_id,
                attendance_date=correction.correction_date
            ).first()

            correction_datetime = datetime.combine(correction.correction_date, correction.correction_time)

            if record:
                if correction.correction_type == 'check_in':
                    record.check_in_time = correction_datetime
                    record.is_corrected = True
                    record.correction_reason = correction.reason
                    record.corrected_by = user.get('id')
                    record.corrected_at = datetime.utcnow()
                elif correction.correction_type == 'check_out':
                    record.check_out_time = correction_datetime
                    record.is_corrected = True
                    record.correction_reason = correction.reason
                    record.corrected_by = user.get('id')
                    record.corrected_at = datetime.utcnow()
            else:
                # 创建新的考勤记录
                new_record = AttendanceRecord(
                    employee_id=correction.employee_id,
                    attendance_date=correction.correction_date,
                    is_corrected=True,
                    correction_reason=correction.reason,
                    corrected_by=user.get('id'),
                    corrected_at=datetime.utcnow()
                )
                if correction.correction_type == 'check_in':
                    new_record.check_in_time = correction_datetime
                elif correction.correction_type == 'check_out':
                    new_record.check_out_time = correction_datetime
                db.session.add(new_record)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '审批成功',
            'data': correction.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'审批失败: {str(e)}'
        }), 500


# ==================== 月度汇总 API ====================

@attendance_bp.route('/monthly-summary', methods=['GET'])
@require_auth
def get_monthly_summary(user):
    """获取月度考勤汇总"""
    try:
        year = request.args.get('year', type=int, default=date.today().year)
        month = request.args.get('month', type=int, default=date.today().month)
        employee_id = request.args.get('employee_id', type=int)
        department_id = request.args.get('department_id', type=int)

        query = MonthlyAttendanceSummary.query.filter_by(year=year, month=month)

        if employee_id:
            query = query.filter(MonthlyAttendanceSummary.employee_id == employee_id)

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        summaries = query.all()

        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in summaries]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@attendance_bp.route('/monthly-summary/generate', methods=['POST'])
@require_auth
def generate_monthly_summary(user):
    """生成月度考勤汇总"""
    try:
        data = request.get_json()
        year = data.get('year', date.today().year)
        month = data.get('month', date.today().month)
        employee_ids = data.get('employee_ids')  # 如果为空则生成所有员工

        # 确定日期范围
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # 获取员工列表
        if employee_ids:
            employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
        else:
            employees = Employee.query.filter_by(employment_status='Active').all()

        generated_count = 0

        for emp in employees:
            # 检查是否已有汇总
            existing = MonthlyAttendanceSummary.query.filter_by(
                employee_id=emp.id,
                year=year,
                month=month
            ).first()

            if existing and existing.is_locked:
                continue  # 跳过已锁定的汇总

            # 获取该员工当月的考勤记录
            records = AttendanceRecord.query.filter(
                and_(
                    AttendanceRecord.employee_id == emp.id,
                    AttendanceRecord.attendance_date >= start_date,
                    AttendanceRecord.attendance_date <= end_date
                )
            ).all()

            # 统计数据
            actual_work_days = len([r for r in records if r.check_in_time and r.check_out_time])
            late_records = [r for r in records if r.is_late]
            early_leave_records = [r for r in records if r.is_early_leave]
            absent_records = [r for r in records if r.is_absent]

            total_work_hours = sum(r.work_hours or 0 for r in records)
            total_overtime_hours = sum(r.overtime_hours or 0 for r in records)

            # 获取加班记录
            overtime_requests = OvertimeRequest.query.filter(
                and_(
                    OvertimeRequest.employee_id == emp.id,
                    OvertimeRequest.overtime_date >= start_date,
                    OvertimeRequest.overtime_date <= end_date,
                    OvertimeRequest.status == 'approved'
                )
            ).all()

            workday_ot = sum(o.actual_hours or o.planned_hours for o in overtime_requests if o.overtime_type == 'workday')
            weekend_ot = sum(o.actual_hours or o.planned_hours for o in overtime_requests if o.overtime_type == 'weekend')
            holiday_ot = sum(o.actual_hours or o.planned_hours for o in overtime_requests if o.overtime_type == 'holiday')

            if existing:
                # 更新现有汇总
                existing.actual_work_days = actual_work_days
                existing.late_count = len(late_records)
                existing.late_minutes_total = sum(r.late_minutes for r in late_records)
                existing.early_leave_count = len(early_leave_records)
                existing.early_leave_minutes_total = sum(r.early_leave_minutes for r in early_leave_records)
                existing.absent_days = len(absent_records)
                existing.actual_hours = round(total_work_hours, 2)
                existing.overtime_hours = round(total_overtime_hours, 2)
                existing.workday_overtime_hours = round(workday_ot, 2)
                existing.weekend_overtime_hours = round(weekend_ot, 2)
                existing.holiday_overtime_hours = round(holiday_ot, 2)
                existing.updated_at = datetime.utcnow()
            else:
                # 创建新汇总
                summary = MonthlyAttendanceSummary(
                    employee_id=emp.id,
                    year=year,
                    month=month,
                    work_days=22,  # 默认工作日，可根据实际情况调整
                    actual_work_days=actual_work_days,
                    late_count=len(late_records),
                    late_minutes_total=sum(r.late_minutes for r in late_records),
                    early_leave_count=len(early_leave_records),
                    early_leave_minutes_total=sum(r.early_leave_minutes for r in early_leave_records),
                    absent_days=len(absent_records),
                    standard_hours=176,  # 默认标准工时
                    actual_hours=round(total_work_hours, 2),
                    overtime_hours=round(total_overtime_hours, 2),
                    workday_overtime_hours=round(workday_ot, 2),
                    weekend_overtime_hours=round(weekend_ot, 2),
                    holiday_overtime_hours=round(holiday_ot, 2)
                )
                db.session.add(summary)

            generated_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已生成 {generated_count} 条月度汇总'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'生成失败: {str(e)}'
        }), 500


@attendance_bp.route('/monthly-summary/<int:id>/lock', methods=['POST'])
@require_auth
def lock_monthly_summary(id, user):
    """锁定月度汇总（用于薪资计算）"""
    try:
        summary = MonthlyAttendanceSummary.query.get(id)
        if not summary:
            return jsonify({
                'success': False,
                'message': '汇总不存在'
            }), 404

        summary.is_locked = True
        summary.locked_at = datetime.utcnow()
        summary.locked_by = user.get('id')

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '月度汇总已锁定',
            'data': summary.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'锁定失败: {str(e)}'
        }), 500


# ==================== 统计 API ====================

@attendance_bp.route('/stats/daily', methods=['GET'])
@require_auth
def get_daily_stats(user):
    """获取每日考勤统计"""
    try:
        target_date = parse_date(request.args.get('date')) or date.today()
        department_id = request.args.get('department_id', type=int)
        factory_id = request.args.get('factory_id', type=int)

        query = AttendanceRecord.query.filter_by(attendance_date=target_date)

        if department_id or factory_id:
            query = query.join(Employee)
            if department_id:
                query = query.filter(Employee.department_id == department_id)
            if factory_id:
                query = query.filter(Employee.factory_id == factory_id)

        records = query.all()

        total = len(records)
        checked_in = len([r for r in records if r.check_in_time])
        checked_out = len([r for r in records if r.check_out_time])
        late = len([r for r in records if r.is_late])
        early_leave = len([r for r in records if r.is_early_leave])
        absent = len([r for r in records if r.is_absent])

        return jsonify({
            'success': True,
            'data': {
                'date': target_date.strftime('%Y-%m-%d'),
                'total_records': total,
                'checked_in': checked_in,
                'checked_out': checked_out,
                'late': late,
                'early_leave': early_leave,
                'absent': absent,
                'late_rate': round(late / total * 100, 2) if total > 0 else 0,
                'absent_rate': round(absent / total * 100, 2) if total > 0 else 0
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'统计失败: {str(e)}'
        }), 500
