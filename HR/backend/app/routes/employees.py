from flask import Blueprint, request, jsonify
from app import db
from app.models.employee import Employee
from app.models.base_data import Department, Position, Team, Factory
from datetime import datetime
from sqlalchemy import or_, and_
from app.routes.auth import require_auth, require_admin
from functools import wraps
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Add shared module to path for AuditService
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '../..', '..'))
from shared.auth import is_admin, has_system_permission
from shared.auth.audit_service import AuditService

employees_bp = Blueprint('employees', __name__, url_prefix='/api')

# Constants
MAX_PAGE_SIZE = 100  # P1-9: Maximum pagination limit
VALID_EMPLOYMENT_STATUS = ['Active', 'Resigned', 'Terminated', 'On Leave']

# P2-14: Error message sanitization
def safe_error_message(operation: str, error: Exception) -> str:
    """
    Return a safe error message that doesn't expose system internals.
    In production, returns generic message; in development, includes details.
    """
    is_dev = os.getenv('FLASK_DEBUG', '').lower() == 'true' or os.getenv('FLASK_ENV') == 'development'
    if is_dev:
        return f'{operation}失败: {str(error)}'
    # Production: log the error but return generic message
    logger.error(f'{operation} error: {str(error)}')
    return f'{operation}失败，请稍后重试或联系管理员'


def require_hr_admin(f):
    """
    Decorator to require HR admin role for write operations.
    Only admin/super_admin roles can create, update, or delete employees.
    """
    @wraps(f)
    def decorated_function(user, *args, **kwargs):
        if not is_admin(user.role):
            return jsonify({
                'success': False,
                'message': '需要 HR 管理员权限才能执行此操作'
            }), 403
        return f(user=user, *args, **kwargs)
    return decorated_function


def validate_dates(data):
    """
    P1-7: Validate date logic
    Returns (is_valid, error_message)
    """
    errors = []

    hire_date = parse_date(data.get('hire_date'))
    contract_start = parse_date(data.get('contract_start_date'))
    contract_end = parse_date(data.get('contract_end_date'))
    resignation_date = parse_date(data.get('resignation_date'))

    # Contract dates should be in order
    if contract_start and contract_end and contract_start > contract_end:
        errors.append('合同开始日期不能晚于合同结束日期')

    # Resignation date should be after hire date
    if hire_date and resignation_date and resignation_date < hire_date:
        errors.append('离职日期不能早于入职日期')

    # Hire date should be before or equal to contract start
    if hire_date and contract_start and hire_date > contract_start:
        errors.append('入职日期不能晚于合同开始日期')

    return (len(errors) == 0, '; '.join(errors))


def validate_salary(data):
    """
    P1-8: Validate salary fields (must be non-negative if provided)
    Returns (is_valid, error_message)
    """
    errors = []
    salary_fields = ['base_salary', 'performance_salary', 'total_salary']

    for field in salary_fields:
        value = parse_float(data.get(field))
        if value is not None and value < 0:
            field_name = {'base_salary': '基本工资', 'performance_salary': '绩效工资', 'total_salary': '总工资'}
            errors.append(f'{field_name.get(field, field)} 不能为负数')

    return (len(errors) == 0, '; '.join(errors))

def parse_date(date_string):
    """Parse date string to date object"""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None

def parse_float(value):
    """Parse float value safely"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def resolve_base_data(data):
    """Resolve base data IDs to names and vice versa"""
    result = {}

    # Factory
    if data.get('factory_id'):
        factory = Factory.query.get(data['factory_id'])
        if factory:
            result['factory_id'] = factory.id
            result['factory_name'] = factory.name

    # Department
    if data.get('department_id'):
        dept = Department.query.get(data['department_id'])
        if dept:
            result['department_id'] = dept.id
            result['department'] = dept.name

    # Position
    if data.get('position_id'):
        pos = Position.query.get(data['position_id'])
        if pos:
            result['position_id'] = pos.id
            result['title'] = pos.name

    # Team
    if data.get('team_id'):
        team = Team.query.get(data['team_id'])
        if team:
            result['team_id'] = team.id
            result['team'] = team.name

    return result

@employees_bp.route('/employees', methods=['GET'])
@require_auth
def get_employees(user):
    """
    Get all employees with pagination and search
    Query params:
    - page: page number (default: 1)
    - per_page: items per page (default: 10, max: 100)
    - search: search term for empNo, name, department, title
    - department: filter by department
    - employment_status: filter by employment status
    - include_deleted: include soft-deleted records (admin only)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        # P1-9: Enforce pagination limit
        per_page = min(per_page, MAX_PAGE_SIZE)

        search = request.args.get('search', '').strip()
        department_filter = request.args.get('department', '').strip()
        status_filter = request.args.get('employment_status', '').strip()
        factory_filter = request.args.get('factory_id', '').strip()
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'

        # Build query - exclude soft-deleted by default
        query = Employee.query
        if not (include_deleted and is_admin(user.role)):
            query = query.filter(Employee.deleted_at.is_(None))

        # Apply search filter
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    Employee.empNo.like(search_term),
                    Employee.name.like(search_term),
                    Employee.department.like(search_term),
                    Employee.title.like(search_term),
                    Employee.email.like(search_term),
                    Employee.phone.like(search_term)
                )
            )

        # Apply department filter
        if department_filter:
            query = query.filter(Employee.department == department_filter)

        # Apply employment status filter
        if status_filter:
            query = query.filter(Employee.employment_status == status_filter)

        # Apply factory filter
        if factory_filter:
            try:
                factory_id = int(factory_filter)
                query = query.filter(Employee.factory_id == factory_id)
            except ValueError:
                pass  # Ignore invalid factory_id

        # Order by created_at descending
        query = query.order_by(Employee.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [emp.to_dict() for emp in pagination.items],
            'pagination': {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': safe_error_message('获取员工列表', e)
        }), 500

@employees_bp.route('/employees/<int:id>', methods=['GET'])
@require_auth
def get_employee(id, user):
    """Get single employee by ID"""
    try:
        employee = Employee.query.get(id)

        if not employee:
            return jsonify({
                'success': False,
                'message': '员工不存在'
            }), 404

        # Check if soft-deleted (only admin can view)
        if employee.deleted_at and not is_admin(user.role):
            return jsonify({
                'success': False,
                'message': '员工不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': employee.to_dict()
        }), 200

    except Exception as e:
        logger.error(f'Error fetching employee {id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': '获取员工信息失败'
        }), 500

@employees_bp.route('/employees', methods=['POST'])
@require_auth
@require_hr_admin
def create_employee(user):
    """Create new employee (Admin only)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': '请提供员工数据'
            }), 400

        # Validate required fields
        if not data.get('empNo'):
            return jsonify({
                'success': False,
                'message': '员工编号 (empNo) 为必填项'
            }), 400

        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': '员工姓名为必填项'
            }), 400

        # P1-7: Validate date logic
        date_valid, date_error = validate_dates(data)
        if not date_valid:
            return jsonify({
                'success': False,
                'message': date_error
            }), 400

        # P1-8: Validate salary fields
        salary_valid, salary_error = validate_salary(data)
        if not salary_valid:
            return jsonify({
                'success': False,
                'message': salary_error
            }), 400

        # Check if empNo already exists (including soft-deleted)
        existing = Employee.query.filter_by(empNo=data['empNo']).first()
        if existing:
            if existing.deleted_at:
                return jsonify({
                    'success': False,
                    'message': f'员工编号 {data["empNo"]} 已存在（已删除员工），请使用其他编号或恢复该员工'
                }), 400
            return jsonify({
                'success': False,
                'message': f'员工编号 {data["empNo"]} 已存在'
            }), 400

        # Check if id_card already exists (if provided)
        if data.get('id_card'):
            existing_id = Employee.query.filter(
                Employee.id_card == data['id_card'],
                Employee.deleted_at.is_(None)
            ).first()
            if existing_id:
                return jsonify({
                    'success': False,
                    'message': '身份证号已存在'
                }), 400

        # Resolve base data IDs to names
        base_data = resolve_base_data(data)

        # Create new employee
        employee = Employee(
            # Basic Information
            empNo=data['empNo'],
            name=data['name'],
            gender=data.get('gender'),
            birth_date=parse_date(data.get('birth_date')),
            id_card=data.get('id_card'),
            phone=data.get('phone'),
            email=data.get('email'),
            # Work Information - use resolved data or original
            factory_id=base_data.get('factory_id', data.get('factory_id')),
            department=base_data.get('department', data.get('department')),
            department_id=base_data.get('department_id', data.get('department_id')),
            title=base_data.get('title', data.get('title')),
            position_id=base_data.get('position_id', data.get('position_id')),
            team=base_data.get('team', data.get('team')),
            team_id=base_data.get('team_id', data.get('team_id')),
            hire_date=parse_date(data.get('hire_date')),
            employment_status=data.get('employment_status', 'Active'),
            resignation_date=parse_date(data.get('resignation_date')),
            # Contract Information
            contract_type=data.get('contract_type'),
            contract_start_date=parse_date(data.get('contract_start_date')),
            contract_end_date=parse_date(data.get('contract_end_date')),
            # Salary Information
            base_salary=parse_float(data.get('base_salary')),
            performance_salary=parse_float(data.get('performance_salary')),
            total_salary=parse_float(data.get('total_salary')),
            # Address and Emergency Contact
            home_address=data.get('home_address'),
            emergency_contact=data.get('emergency_contact'),
            emergency_phone=data.get('emergency_phone'),
            # Blacklist Information
            is_blacklisted=data.get('is_blacklisted', False),
            blacklist_reason=data.get('blacklist_reason'),
            blacklist_date=parse_date(data.get('blacklist_date')),
            # Other Information
            remark=data.get('remark')
        )

        db.session.add(employee)
        db.session.commit()

        # P0-5: Audit logging for employee creation
        AuditService.log(
            action_type=AuditService.ACTION_DATA_CREATE,
            user_id=user.id,
            username=user.username,
            resource_type='employee',
            resource_id=str(employee.id),
            description=f'创建员工: {employee.name} (工号: {employee.empNo})',
            status='success',
            module='hr'
        )

        return jsonify({
            'success': True,
            'message': '员工创建成功',
            'data': employee.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error creating employee: {str(e)}')
        return jsonify({
            'success': False,
            'message': '创建员工失败，请稍后重试'
        }), 500

@employees_bp.route('/employees/<int:id>', methods=['PUT'])
@require_auth
@require_hr_admin
def update_employee(id, user):
    """Update employee by ID (Admin only)"""
    try:
        employee = Employee.query.get(id)

        if not employee:
            return jsonify({
                'success': False,
                'message': '员工不存在'
            }), 404

        # Don't allow updating soft-deleted employees
        if employee.deleted_at:
            return jsonify({
                'success': False,
                'message': '无法修改已删除的员工，请先恢复该员工'
            }), 400

        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': '请提供更新数据'
            }), 400

        # P1-7: Validate date logic (merge with existing data)
        merged_data = {
            'hire_date': data.get('hire_date', employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else None),
            'contract_start_date': data.get('contract_start_date', employee.contract_start_date.strftime('%Y-%m-%d') if employee.contract_start_date else None),
            'contract_end_date': data.get('contract_end_date', employee.contract_end_date.strftime('%Y-%m-%d') if employee.contract_end_date else None),
            'resignation_date': data.get('resignation_date', employee.resignation_date.strftime('%Y-%m-%d') if employee.resignation_date else None),
        }
        date_valid, date_error = validate_dates(merged_data)
        if not date_valid:
            return jsonify({
                'success': False,
                'message': date_error
            }), 400

        # P1-8: Validate salary fields
        salary_valid, salary_error = validate_salary(data)
        if not salary_valid:
            return jsonify({
                'success': False,
                'message': salary_error
            }), 400

        # Check if empNo is being changed and if it conflicts
        if 'empNo' in data and data['empNo'] != employee.empNo:
            existing = Employee.query.filter(
                Employee.empNo == data['empNo'],
                Employee.id != id
            ).first()
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'员工编号 {data["empNo"]} 已存在'
                }), 400

        # Check if id_card is being changed and if it conflicts
        if 'id_card' in data and data['id_card'] and data['id_card'] != employee.id_card:
            existing_id = Employee.query.filter(
                Employee.id_card == data['id_card'],
                Employee.id != id,
                Employee.deleted_at.is_(None)
            ).first()
            if existing_id:
                return jsonify({
                    'success': False,
                    'message': '身份证号已存在'
                }), 400

        # Store old values for audit log
        old_values = {
            'name': employee.name,
            'empNo': employee.empNo,
            'base_salary': employee.base_salary,
            'is_blacklisted': employee.is_blacklisted
        }

        # Resolve base data IDs to names
        base_data = resolve_base_data(data)

        # Update fields
        # Basic Information
        if 'empNo' in data:
            employee.empNo = data['empNo']
        if 'name' in data:
            employee.name = data['name']
        if 'gender' in data:
            employee.gender = data['gender']
        if 'birth_date' in data:
            employee.birth_date = parse_date(data['birth_date'])
        if 'id_card' in data:
            employee.id_card = data['id_card']
        if 'phone' in data:
            employee.phone = data['phone']
        if 'email' in data:
            employee.email = data['email']

        # Work Information - handle both ID and name fields
        if 'factory_id' in data:
            employee.factory_id = base_data.get('factory_id', data.get('factory_id'))
        if 'department_id' in data:
            employee.department_id = base_data.get('department_id', data.get('department_id'))
            if 'department' in base_data:
                employee.department = base_data['department']
        if 'department' in data and 'department_id' not in data:
            employee.department = data['department']
        if 'position_id' in data:
            employee.position_id = base_data.get('position_id', data.get('position_id'))
            if 'title' in base_data:
                employee.title = base_data['title']
        if 'title' in data and 'position_id' not in data:
            employee.title = data['title']
        if 'team_id' in data:
            employee.team_id = base_data.get('team_id', data.get('team_id'))
            if 'team' in base_data:
                employee.team = base_data['team']
        if 'team' in data and 'team_id' not in data:
            employee.team = data['team']
        if 'hire_date' in data:
            employee.hire_date = parse_date(data['hire_date'])
        if 'employment_status' in data:
            employee.employment_status = data['employment_status']
        if 'resignation_date' in data:
            employee.resignation_date = parse_date(data['resignation_date'])

        # Contract Information
        if 'contract_type' in data:
            employee.contract_type = data['contract_type']
        if 'contract_start_date' in data:
            employee.contract_start_date = parse_date(data['contract_start_date'])
        if 'contract_end_date' in data:
            employee.contract_end_date = parse_date(data['contract_end_date'])

        # Salary Information
        if 'base_salary' in data:
            employee.base_salary = parse_float(data['base_salary'])
        if 'performance_salary' in data:
            employee.performance_salary = parse_float(data['performance_salary'])
        if 'total_salary' in data:
            employee.total_salary = parse_float(data['total_salary'])

        # Address and Emergency Contact
        if 'home_address' in data:
            employee.home_address = data['home_address']
        if 'emergency_contact' in data:
            employee.emergency_contact = data['emergency_contact']
        if 'emergency_phone' in data:
            employee.emergency_phone = data['emergency_phone']

        # Blacklist Information
        if 'is_blacklisted' in data:
            employee.is_blacklisted = data['is_blacklisted']
        if 'blacklist_reason' in data:
            employee.blacklist_reason = data['blacklist_reason']
        if 'blacklist_date' in data:
            employee.blacklist_date = parse_date(data['blacklist_date'])

        # Other Information
        if 'remark' in data:
            employee.remark = data['remark']

        # Update timestamp
        employee.updated_at = datetime.utcnow()

        db.session.commit()

        # P0-5: Audit logging for employee update
        # Detect significant changes
        changes = []
        if old_values['name'] != employee.name:
            changes.append(f'姓名: {old_values["name"]} -> {employee.name}')
        if old_values['base_salary'] != employee.base_salary:
            changes.append(f'薪资变更')
        if old_values['is_blacklisted'] != employee.is_blacklisted:
            changes.append(f'黑名单状态: {"加入" if employee.is_blacklisted else "移除"}')

        AuditService.log(
            action_type=AuditService.ACTION_DATA_UPDATE,
            user_id=user.id,
            username=user.username,
            resource_type='employee',
            resource_id=str(employee.id),
            description=f'更新员工: {employee.name} (工号: {employee.empNo})' + (f' - {"; ".join(changes)}' if changes else ''),
            status='success',
            module='hr'
        )

        return jsonify({
            'success': True,
            'message': '员工信息更新成功',
            'data': employee.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error updating employee {id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': '更新员工信息失败，请稍后重试'
        }), 500

@employees_bp.route('/employees/<int:id>', methods=['DELETE'])
@require_auth
@require_hr_admin
def delete_employee(id, user):
    """Soft delete employee by ID (Admin only)"""
    try:
        employee = Employee.query.get(id)

        if not employee:
            return jsonify({
                'success': False,
                'message': '员工不存在'
            }), 404

        # Already deleted?
        if employee.deleted_at:
            return jsonify({
                'success': False,
                'message': '该员工已被删除'
            }), 400

        # Store employee data before deletion
        employee_data = employee.to_dict()

        # P1-10: Soft delete instead of hard delete
        employee.deleted_at = datetime.utcnow()
        employee.deleted_by = user.id
        db.session.commit()

        # P0-5: Audit logging for employee deletion
        AuditService.log(
            action_type=AuditService.ACTION_DATA_DELETE,
            user_id=user.id,
            username=user.username,
            resource_type='employee',
            resource_id=str(employee.id),
            description=f'删除员工: {employee.name} (工号: {employee.empNo})',
            status='success',
            module='hr'
        )

        return jsonify({
            'success': True,
            'message': '员工删除成功',
            'data': employee_data
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error deleting employee {id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': '删除员工失败，请稍后重试'
        }), 500


@employees_bp.route('/employees/<int:id>/restore', methods=['POST'])
@require_auth
@require_hr_admin
def restore_employee(id, user):
    """Restore soft-deleted employee (Admin only)"""
    try:
        employee = Employee.query.get(id)

        if not employee:
            return jsonify({
                'success': False,
                'message': '员工不存在'
            }), 404

        if not employee.deleted_at:
            return jsonify({
                'success': False,
                'message': '该员工未被删除，无需恢复'
            }), 400

        # Restore employee
        employee.deleted_at = None
        employee.deleted_by = None
        employee.updated_at = datetime.utcnow()
        db.session.commit()

        # Audit logging
        AuditService.log(
            action_type=AuditService.ACTION_DATA_UPDATE,
            user_id=user.id,
            username=user.username,
            resource_type='employee',
            resource_id=str(employee.id),
            description=f'恢复已删除员工: {employee.name} (工号: {employee.empNo})',
            status='success',
            module='hr'
        )

        return jsonify({
            'success': True,
            'message': '员工恢复成功',
            'data': employee.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error restoring employee {id}: {str(e)}')
        return jsonify({
            'success': False,
            'message': '恢复员工失败，请稍后重试'
        }), 500

@employees_bp.route('/employees/list', methods=['POST'])
@require_auth
def list_employees(user):
    """
    Legacy support: Get employees list with POST method
    Accepts JSON body with optional filters
    """
    try:
        data = request.get_json() or {}

        page = data.get('page', 1)
        per_page = data.get('per_page', 10)
        # P1-9: Enforce pagination limit
        per_page = min(per_page, MAX_PAGE_SIZE)

        search = data.get('search', '').strip()
        department_filter = data.get('department', '').strip()
        status_filter = data.get('employment_status', '').strip()

        # Build query - exclude soft-deleted
        query = Employee.query.filter(Employee.deleted_at.is_(None))

        # Apply search filter
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    Employee.empNo.like(search_term),
                    Employee.name.like(search_term),
                    Employee.department.like(search_term),
                    Employee.title.like(search_term),
                    Employee.email.like(search_term),
                    Employee.phone.like(search_term)
                )
            )

        # Apply department filter
        if department_filter:
            query = query.filter(Employee.department == department_filter)

        # Apply employment status filter
        if status_filter:
            query = query.filter(Employee.employment_status == status_filter)

        # Order by created_at descending
        query = query.order_by(Employee.created_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [emp.to_dict() for emp in pagination.items],
            'pagination': {
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': safe_error_message('获取员工列表', e)
        }), 500

@employees_bp.route('/employees/stats', methods=['GET'])
@require_auth
def get_employee_stats(user):
    """Get employee statistics (excludes soft-deleted employees)"""
    try:
        # Exclude soft-deleted employees from all counts
        base_query = Employee.query.filter(Employee.deleted_at.is_(None))

        total_employees = base_query.count()
        active_employees = base_query.filter_by(employment_status='Active').count()
        resigned_employees = base_query.filter_by(employment_status='Resigned').count()

        # Department statistics (exclude soft-deleted)
        departments = db.session.query(
            Employee.department,
            db.func.count(Employee.id).label('count')
        ).filter(
            Employee.department.isnot(None),
            Employee.deleted_at.is_(None)
        ).group_by(
            Employee.department
        ).all()

        department_stats = [{'department': dept, 'count': count} for dept, count in departments]

        return jsonify({
            'success': True,
            'data': {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'resigned_employees': resigned_employees,
                'department_distribution': department_stats
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': safe_error_message('获取统计数据', e)
        }), 500
