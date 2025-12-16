"""
假期管理 API 路由
包含: 假期类型、假期余额、请假申请、审批、公共假日
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models.leave import (
    LeaveType, LeaveBalance, LeaveRequest, LeaveApprovalFlow,
    Holiday, LeaveBalanceAdjustment, init_default_leave_types
)
from app.models.employee import Employee
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, func
from app.routes.auth import require_auth
import uuid

leave_bp = Blueprint('leave', __name__, url_prefix='/api/leave')


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


def generate_request_no():
    """生成请假单号"""
    now = datetime.now()
    return f"LV{now.strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"


def calculate_leave_days(start_date, end_date, start_time=None, end_time=None):
    """计算请假天数"""
    if not start_date or not end_date:
        return 0

    days = (end_date - start_date).days + 1

    # 如果有具体时间，计算半天
    if start_time and end_time:
        # 简化计算：上午假或下午假算0.5天
        if days == 1:
            start_hour = start_time.hour
            end_hour = end_time.hour
            if start_hour >= 12 or end_hour <= 12:
                return 0.5

    return float(days)


# ==================== 假期类型 API ====================

@leave_bp.route('/types', methods=['GET'])
@require_auth
def get_leave_types(user):
    """获取假期类型列表"""
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        query = LeaveType.query
        if active_only:
            query = query.filter_by(is_active=True)

        types = query.order_by(LeaveType.sort_order.asc()).all()

        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in types]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@leave_bp.route('/types', methods=['POST'])
@require_auth
def create_leave_type(user):
    """创建假期类型"""
    try:
        data = request.get_json()

        if not data.get('name') or not data.get('code'):
            return jsonify({
                'success': False,
                'message': '假期名称和编码不能为空'
            }), 400

        existing = LeaveType.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': f'假期编码 {data["code"]} 已存在'
            }), 400

        leave_type = LeaveType(
            code=data['code'],
            name=data['name'],
            category=data.get('category', 'personal'),
            is_paid=data.get('is_paid', True),
            pay_rate=data.get('pay_rate', 1.0),
            min_days=data.get('min_days', 0.5),
            max_days=data.get('max_days'),
            unit=data.get('unit', 'day'),
            has_quota=data.get('has_quota', False),
            default_quota=data.get('default_quota', 0),
            quota_unit=data.get('quota_unit', 'day'),
            can_carry_over=data.get('can_carry_over', False),
            max_carry_over=data.get('max_carry_over', 0),
            require_approval=data.get('require_approval', True),
            require_attachment=data.get('require_attachment', False),
            advance_days=data.get('advance_days', 0),
            applicable_gender=data.get('applicable_gender'),
            min_service_months=data.get('min_service_months', 0),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0),
            description=data.get('description'),
            color=data.get('color')
        )

        db.session.add(leave_type)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '假期类型创建成功',
            'data': leave_type.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@leave_bp.route('/types/<int:id>', methods=['PUT'])
@require_auth
def update_leave_type(id, user):
    """更新假期类型"""
    try:
        leave_type = LeaveType.query.get(id)
        if not leave_type:
            return jsonify({
                'success': False,
                'message': '假期类型不存在'
            }), 404

        data = request.get_json()

        for field in ['name', 'category', 'is_paid', 'pay_rate', 'min_days', 'max_days',
                      'unit', 'has_quota', 'default_quota', 'quota_unit', 'can_carry_over',
                      'max_carry_over', 'require_approval', 'require_attachment', 'advance_days',
                      'applicable_gender', 'min_service_months', 'is_active', 'sort_order',
                      'description', 'color']:
            if field in data:
                setattr(leave_type, field, data[field])

        leave_type.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '假期类型更新成功',
            'data': leave_type.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@leave_bp.route('/types/<int:id>', methods=['DELETE'])
@require_auth
def delete_leave_type(id, user):
    """删除假期类型"""
    try:
        leave_type = LeaveType.query.get(id)
        if not leave_type:
            return jsonify({
                'success': False,
                'message': '假期类型不存在'
            }), 404

        # 检查是否有关联的请假记录
        if LeaveRequest.query.filter_by(leave_type_id=id).first():
            return jsonify({
                'success': False,
                'message': '该假期类型已有请假记录，无法删除'
            }), 400

        db.session.delete(leave_type)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '假期类型删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@leave_bp.route('/types/init', methods=['POST'])
@require_auth
def init_leave_types(user):
    """初始化默认假期类型"""
    try:
        init_default_leave_types()
        return jsonify({
            'success': True,
            'message': '默认假期类型初始化成功'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'初始化失败: {str(e)}'
        }), 500


# ==================== 假期余额 API ====================

@leave_bp.route('/balances', methods=['GET'])
@require_auth
def get_leave_balances(user):
    """获取假期余额列表"""
    try:
        employee_id = request.args.get('employee_id', type=int)
        year = request.args.get('year', type=int, default=date.today().year)
        leave_type_id = request.args.get('leave_type_id', type=int)

        query = LeaveBalance.query.filter_by(year=year)

        if employee_id:
            query = query.filter_by(employee_id=employee_id)

        if leave_type_id:
            query = query.filter_by(leave_type_id=leave_type_id)

        balances = query.all()

        return jsonify({
            'success': True,
            'data': [b.to_dict() for b in balances]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@leave_bp.route('/balances/my', methods=['GET'])
@require_auth
def get_my_balances(user):
    """获取我的假期余额"""
    try:
        employee = Employee.query.filter_by(empNo=user.get('username')).first()
        if not employee:
            return jsonify({
                'success': False,
                'message': '未找到关联的员工信息'
            }), 400

        year = request.args.get('year', type=int, default=date.today().year)

        balances = LeaveBalance.query.filter_by(
            employee_id=employee.id,
            year=year
        ).all()

        return jsonify({
            'success': True,
            'data': [b.to_dict() for b in balances]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@leave_bp.route('/balances/init', methods=['POST'])
@require_auth
def init_leave_balances(user):
    """初始化员工假期余额"""
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids')  # 为空则初始化所有在职员工
        year = data.get('year', date.today().year)

        # 获取所有有额度的假期类型
        leave_types = LeaveType.query.filter_by(is_active=True, has_quota=True).all()

        # 获取员工列表
        if employee_ids:
            employees = Employee.query.filter(Employee.id.in_(employee_ids)).all()
        else:
            employees = Employee.query.filter_by(employment_status='Active').all()

        created_count = 0

        for emp in employees:
            for lt in leave_types:
                # 检查性别限制
                if lt.applicable_gender:
                    if emp.gender and emp.gender.lower() != lt.applicable_gender.lower():
                        continue

                # 检查服务月数
                if lt.min_service_months > 0 and emp.hire_date:
                    service_months = (date.today() - emp.hire_date).days / 30
                    if service_months < lt.min_service_months:
                        continue

                # 检查是否已存在
                existing = LeaveBalance.query.filter_by(
                    employee_id=emp.id,
                    leave_type_id=lt.id,
                    year=year
                ).first()

                if existing:
                    continue

                # 计算结转额度
                carry_over = 0
                if lt.can_carry_over:
                    prev_balance = LeaveBalance.query.filter_by(
                        employee_id=emp.id,
                        leave_type_id=lt.id,
                        year=year - 1
                    ).first()
                    if prev_balance:
                        carry_over = min(prev_balance.remaining, lt.max_carry_over)

                # 计算年假额度（根据工龄）
                initial_balance = lt.default_quota
                if lt.code == 'annual' and emp.hire_date:
                    years_of_service = (date.today() - emp.hire_date).days / 365
                    if years_of_service >= 20:
                        initial_balance = 15
                    elif years_of_service >= 10:
                        initial_balance = 10
                    elif years_of_service >= 1:
                        initial_balance = 5
                    else:
                        initial_balance = 0

                balance = LeaveBalance(
                    employee_id=emp.id,
                    leave_type_id=lt.id,
                    year=year,
                    initial_balance=initial_balance,
                    carry_over=carry_over,
                    total_balance=initial_balance + carry_over,
                    remaining=initial_balance + carry_over
                )
                db.session.add(balance)
                created_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已初始化 {created_count} 条假期余额'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'初始化失败: {str(e)}'
        }), 500


@leave_bp.route('/balances/<int:id>/adjust', methods=['POST'])
@require_auth
def adjust_leave_balance(id, user):
    """调整假期余额"""
    try:
        balance = LeaveBalance.query.get(id)
        if not balance:
            return jsonify({
                'success': False,
                'message': '余额记录不存在'
            }), 404

        data = request.get_json()
        adjustment_type = data.get('type')  # 'add' or 'deduct'
        amount = data.get('amount', 0)
        reason = data.get('reason', '')

        if adjustment_type not in ['add', 'deduct']:
            return jsonify({
                'success': False,
                'message': '无效的调整类型'
            }), 400

        if amount <= 0:
            return jsonify({
                'success': False,
                'message': '调整数量必须大于0'
            }), 400

        balance_before = balance.remaining

        if adjustment_type == 'add':
            balance.adjustment += amount
            balance.total_balance += amount
            balance.remaining += amount
        else:
            if balance.remaining < amount:
                return jsonify({
                    'success': False,
                    'message': '扣减数量超过剩余额度'
                }), 400
            balance.adjustment -= amount
            balance.total_balance -= amount
            balance.remaining -= amount

        # 记录调整
        adjustment = LeaveBalanceAdjustment(
            leave_balance_id=balance.id,
            adjustment_type=adjustment_type,
            amount=amount,
            reason=reason,
            operator_id=user.get('id'),
            balance_before=balance_before,
            balance_after=balance.remaining
        )
        db.session.add(adjustment)

        balance.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '余额调整成功',
            'data': balance.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'调整失败: {str(e)}'
        }), 500


# ==================== 请假申请 API ====================

@leave_bp.route('/requests', methods=['GET'])
@require_auth
def get_leave_requests(user):
    """获取请假申请列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        department_id = request.args.get('department_id', type=int)
        leave_type_id = request.args.get('leave_type_id', type=int)
        status = request.args.get('status')
        start_date = parse_date(request.args.get('start_date'))
        end_date = parse_date(request.args.get('end_date'))

        query = LeaveRequest.query

        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        if leave_type_id:
            query = query.filter(LeaveRequest.leave_type_id == leave_type_id)

        if status:
            query = query.filter(LeaveRequest.status == status)

        if start_date:
            query = query.filter(LeaveRequest.start_date >= start_date)

        if end_date:
            query = query.filter(LeaveRequest.end_date <= end_date)

        query = query.order_by(LeaveRequest.created_at.desc())

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


@leave_bp.route('/requests/my', methods=['GET'])
@require_auth
def get_my_requests(user):
    """获取我的请假申请"""
    try:
        employee = Employee.query.filter_by(empNo=user.get('username')).first()
        if not employee:
            return jsonify({
                'success': False,
                'message': '未找到关联的员工信息'
            }), 400

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')

        query = LeaveRequest.query.filter_by(employee_id=employee.id)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(LeaveRequest.created_at.desc())

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


@leave_bp.route('/requests/pending', methods=['GET'])
@require_auth
def get_pending_requests(user):
    """获取待审批的请假申请"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        query = LeaveRequest.query.filter_by(status='pending')
        query = query.order_by(LeaveRequest.created_at.asc())

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


@leave_bp.route('/requests', methods=['POST'])
@require_auth
def create_leave_request(user):
    """创建请假申请"""
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
        else:
            employee = Employee.query.get(employee_id)
            if not employee:
                return jsonify({
                    'success': False,
                    'message': '员工不存在'
                }), 404

        if not data.get('leave_type_id') or not data.get('start_date') or not data.get('end_date'):
            return jsonify({
                'success': False,
                'message': '假期类型、开始日期和结束日期不能为空'
            }), 400

        leave_type = LeaveType.query.get(data['leave_type_id'])
        if not leave_type:
            return jsonify({
                'success': False,
                'message': '假期类型不存在'
            }), 404

        start_date = parse_date(data['start_date'])
        end_date = parse_date(data['end_date'])
        start_time = parse_time(data.get('start_time'))
        end_time = parse_time(data.get('end_time'))

        if end_date < start_date:
            return jsonify({
                'success': False,
                'message': '结束日期不能早于开始日期'
            }), 400

        # 计算请假天数
        duration = data.get('duration') or calculate_leave_days(start_date, end_date, start_time, end_time)

        # 检查假期余额
        if leave_type.has_quota:
            balance = LeaveBalance.query.filter_by(
                employee_id=employee_id,
                leave_type_id=leave_type.id,
                year=start_date.year
            ).first()

            if not balance or balance.remaining < duration:
                return jsonify({
                    'success': False,
                    'message': f'假期余额不足，当前剩余: {balance.remaining if balance else 0} 天'
                }), 400

        leave_request = LeaveRequest(
            request_no=generate_request_no(),
            employee_id=employee_id,
            leave_type_id=leave_type.id,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            duration_unit=leave_type.unit,
            reason=data.get('reason', ''),
            attachment=data.get('attachment'),
            status='pending' if leave_type.require_approval else 'approved',
            proxy_employee_id=data.get('proxy_employee_id')
        )

        db.session.add(leave_request)

        # 如果有额度限制，更新pending数
        if leave_type.has_quota and balance:
            balance.pending += duration
            balance.update_remaining()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '请假申请提交成功',
            'data': leave_request.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }), 500


@leave_bp.route('/requests/<int:id>', methods=['GET'])
@require_auth
def get_leave_request(id, user):
    """获取请假申请详情"""
    try:
        leave_request = LeaveRequest.query.get(id)
        if not leave_request:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': leave_request.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@leave_bp.route('/requests/<int:id>/approve', methods=['POST'])
@require_auth
def approve_leave_request(id, user):
    """审批请假申请"""
    try:
        leave_request = LeaveRequest.query.get(id)
        if not leave_request:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        if leave_request.status != 'pending':
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

        leave_request.status = 'approved' if action == 'approve' else 'rejected'
        leave_request.approver_id = user.get('id')
        leave_request.approved_at = datetime.utcnow()
        leave_request.approval_remark = data.get('remark')

        # 更新假期余额
        leave_type = leave_request.leave_type
        if leave_type.has_quota:
            balance = LeaveBalance.query.filter_by(
                employee_id=leave_request.employee_id,
                leave_type_id=leave_type.id,
                year=leave_request.start_date.year
            ).first()

            if balance:
                balance.pending -= leave_request.duration
                if action == 'approve':
                    balance.used += leave_request.duration
                balance.update_remaining()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '审批成功',
            'data': leave_request.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'审批失败: {str(e)}'
        }), 500


@leave_bp.route('/requests/<int:id>/cancel', methods=['POST'])
@require_auth
def cancel_leave_request(id, user):
    """取消请假申请"""
    try:
        leave_request = LeaveRequest.query.get(id)
        if not leave_request:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        if leave_request.status not in ['pending', 'approved']:
            return jsonify({
                'success': False,
                'message': '该申请状态无法取消'
            }), 400

        # 更新假期余额
        leave_type = leave_request.leave_type
        if leave_type.has_quota:
            balance = LeaveBalance.query.filter_by(
                employee_id=leave_request.employee_id,
                leave_type_id=leave_type.id,
                year=leave_request.start_date.year
            ).first()

            if balance:
                if leave_request.status == 'pending':
                    balance.pending -= leave_request.duration
                elif leave_request.status == 'approved':
                    balance.used -= leave_request.duration
                balance.update_remaining()

        leave_request.status = 'cancelled'
        leave_request.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '申请已取消',
            'data': leave_request.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'取消失败: {str(e)}'
        }), 500


@leave_bp.route('/requests/<int:id>/return', methods=['POST'])
@require_auth
def return_from_leave(id, user):
    """销假"""
    try:
        leave_request = LeaveRequest.query.get(id)
        if not leave_request:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        if leave_request.status != 'approved':
            return jsonify({
                'success': False,
                'message': '只有已批准的申请才能销假'
            }), 400

        data = request.get_json()
        actual_return_date = parse_date(data.get('actual_return_date')) or date.today()
        actual_duration = data.get('actual_duration')

        leave_request.actual_return_date = actual_return_date
        leave_request.return_remark = data.get('remark')
        leave_request.status = 'completed'

        # 如果实际天数不同，调整余额
        if actual_duration is not None and actual_duration != leave_request.duration:
            diff = leave_request.duration - actual_duration
            leave_request.actual_duration = actual_duration

            leave_type = leave_request.leave_type
            if leave_type.has_quota and diff != 0:
                balance = LeaveBalance.query.filter_by(
                    employee_id=leave_request.employee_id,
                    leave_type_id=leave_type.id,
                    year=leave_request.start_date.year
                ).first()

                if balance:
                    balance.used -= diff
                    balance.update_remaining()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '销假成功',
            'data': leave_request.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'销假失败: {str(e)}'
        }), 500


# ==================== 公共假日 API ====================

@leave_bp.route('/holidays', methods=['GET'])
@require_auth
def get_holidays(user):
    """获取公共假日列表"""
    try:
        year = request.args.get('year', type=int, default=date.today().year)
        factory_id = request.args.get('factory_id', type=int)

        query = Holiday.query.filter_by(year=year)

        if factory_id:
            query = query.filter(
                or_(Holiday.factory_id == factory_id, Holiday.factory_id.is_(None))
            )

        holidays = query.order_by(Holiday.holiday_date.asc()).all()

        return jsonify({
            'success': True,
            'data': [h.to_dict() for h in holidays]
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@leave_bp.route('/holidays', methods=['POST'])
@require_auth
def create_holiday(user):
    """创建公共假日"""
    try:
        data = request.get_json()

        if not data.get('name') or not data.get('holiday_date'):
            return jsonify({
                'success': False,
                'message': '假日名称和日期不能为空'
            }), 400

        holiday_date = parse_date(data['holiday_date'])

        holiday = Holiday(
            name=data['name'],
            holiday_date=holiday_date,
            year=holiday_date.year,
            holiday_type=data.get('holiday_type', 'holiday'),
            factory_id=data.get('factory_id'),
            description=data.get('description')
        )

        db.session.add(holiday)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '假日创建成功',
            'data': holiday.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@leave_bp.route('/holidays/batch', methods=['POST'])
@require_auth
def create_holidays_batch(user):
    """批量创建公共假日"""
    try:
        data = request.get_json()
        holidays_data = data.get('holidays', [])

        created_count = 0
        for hd in holidays_data:
            if not hd.get('name') or not hd.get('holiday_date'):
                continue

            holiday_date = parse_date(hd['holiday_date'])

            # 检查是否已存在
            existing = Holiday.query.filter_by(
                holiday_date=holiday_date,
                factory_id=hd.get('factory_id')
            ).first()

            if existing:
                continue

            holiday = Holiday(
                name=hd['name'],
                holiday_date=holiday_date,
                year=holiday_date.year,
                holiday_type=hd.get('holiday_type', 'holiday'),
                factory_id=hd.get('factory_id'),
                description=hd.get('description')
            )
            db.session.add(holiday)
            created_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'成功创建 {created_count} 条假日记录'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@leave_bp.route('/holidays/<int:id>', methods=['DELETE'])
@require_auth
def delete_holiday(id, user):
    """删除公共假日"""
    try:
        holiday = Holiday.query.get(id)
        if not holiday:
            return jsonify({
                'success': False,
                'message': '假日不存在'
            }), 404

        db.session.delete(holiday)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '假日删除成功'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


# ==================== 统计 API ====================

@leave_bp.route('/stats/summary', methods=['GET'])
@require_auth
def get_leave_stats(user):
    """获取请假统计"""
    try:
        year = request.args.get('year', type=int, default=date.today().year)
        department_id = request.args.get('department_id', type=int)

        # 统计各类型请假天数
        query = db.session.query(
            LeaveType.name,
            func.sum(LeaveRequest.duration).label('total_days')
        ).join(LeaveRequest).filter(
            LeaveRequest.status == 'approved',
            func.year(LeaveRequest.start_date) == year
        )

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        query = query.group_by(LeaveType.id)
        type_stats = query.all()

        # 统计各月请假人次
        monthly_query = db.session.query(
            func.month(LeaveRequest.start_date).label('month'),
            func.count(LeaveRequest.id).label('count')
        ).filter(
            LeaveRequest.status == 'approved',
            func.year(LeaveRequest.start_date) == year
        )

        if department_id:
            monthly_query = monthly_query.join(Employee).filter(Employee.department_id == department_id)

        monthly_query = monthly_query.group_by(func.month(LeaveRequest.start_date))
        monthly_stats = monthly_query.all()

        return jsonify({
            'success': True,
            'data': {
                'by_type': [{'type': name, 'days': float(days or 0)} for name, days in type_stats],
                'by_month': [{'month': m, 'count': c} for m, c in monthly_stats]
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'统计失败: {str(e)}'
        }), 500
