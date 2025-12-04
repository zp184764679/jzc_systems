from flask import Blueprint, request, jsonify
from app import db
from app.models.employee import Employee
from app.models.base_data import Department, Position, Team, Factory
from datetime import datetime
from sqlalchemy import or_, and_
from app.routes.auth import require_auth

employees_bp = Blueprint('employees', __name__, url_prefix='/api')

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
    - per_page: items per page (default: 10)
    - search: search term for empNo, name, department, title
    - department: filter by department
    - employment_status: filter by employment status
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10000, type=int)  # Increased to handle all employees
        search = request.args.get('search', '').strip()
        department_filter = request.args.get('department', '').strip()
        status_filter = request.args.get('employment_status', '').strip()
        factory_filter = request.args.get('factory_id', '').strip()

        # Build query
        query = Employee.query

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
            'message': f'Error fetching employees: {str(e)}'
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
                'message': 'Employee not found'
            }), 404

        return jsonify({
            'success': True,
            'data': employee.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching employee: {str(e)}'
        }), 500

@employees_bp.route('/employees', methods=['POST'])
@require_auth
def create_employee(user):
    """Create new employee"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        # Validate required fields
        if not data.get('empNo'):
            return jsonify({
                'success': False,
                'message': 'Employee number (empNo) is required'
            }), 400

        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Employee name is required'
            }), 400

        # Check if empNo already exists
        existing = Employee.query.filter_by(empNo=data['empNo']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': f'Employee number {data["empNo"]} already exists'
            }), 400

        # Check if id_card already exists (if provided)
        if data.get('id_card'):
            existing_id = Employee.query.filter_by(id_card=data['id_card']).first()
            if existing_id:
                return jsonify({
                    'success': False,
                    'message': f'ID card number already exists'
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

        return jsonify({
            'success': True,
            'message': 'Employee created successfully',
            'data': employee.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating employee: {str(e)}'
        }), 500

@employees_bp.route('/employees/<int:id>', methods=['PUT'])
@require_auth
def update_employee(id, user):
    """Update employee by ID"""
    try:
        employee = Employee.query.get(id)

        if not employee:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404

        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        # Check if empNo is being changed and if it conflicts
        if 'empNo' in data and data['empNo'] != employee.empNo:
            existing = Employee.query.filter_by(empNo=data['empNo']).first()
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'Employee number {data["empNo"]} already exists'
                }), 400

        # Check if id_card is being changed and if it conflicts
        if 'id_card' in data and data['id_card'] and data['id_card'] != employee.id_card:
            existing_id = Employee.query.filter_by(id_card=data['id_card']).first()
            if existing_id:
                return jsonify({
                    'success': False,
                    'message': f'ID card number already exists'
                }), 400

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

        return jsonify({
            'success': True,
            'message': 'Employee updated successfully',
            'data': employee.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating employee: {str(e)}'
        }), 500

@employees_bp.route('/employees/<int:id>', methods=['DELETE'])
@require_auth
def delete_employee(id, user):
    """Delete employee by ID"""
    try:
        employee = Employee.query.get(id)

        if not employee:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404

        # Store employee data before deletion
        employee_data = employee.to_dict()

        db.session.delete(employee)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Employee deleted successfully',
            'data': employee_data
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting employee: {str(e)}'
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
        search = data.get('search', '').strip()
        department_filter = data.get('department', '').strip()
        status_filter = data.get('employment_status', '').strip()

        # Build query
        query = Employee.query

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
            'message': f'Error fetching employees: {str(e)}'
        }), 500

@employees_bp.route('/employees/stats', methods=['GET'])
@require_auth
def get_employee_stats(user):
    """Get employee statistics"""
    try:
        total_employees = Employee.query.count()
        active_employees = Employee.query.filter_by(employment_status='Active').count()
        resigned_employees = Employee.query.filter_by(employment_status='Resigned').count()

        # Department statistics
        departments = db.session.query(
            Employee.department,
            db.func.count(Employee.id).label('count')
        ).filter(
            Employee.department.isnot(None)
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
            'message': f'Error fetching statistics: {str(e)}'
        }), 500
