"""
薪资管理 API 路由
包含: 薪资结构、薪资项、员工薪资、工资单、薪资调整、税率配置
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models import Employee
from app.models.payroll import (
    SalaryStructure, PayItem, EmployeeSalary, Payroll, SalaryAdjustment,
    TaxBracket, SocialInsuranceRate, PayItemType, PayrollStatus,
    init_default_pay_items, init_default_tax_brackets
)
from app.models.attendance import MonthlyAttendanceSummary
from datetime import datetime, date
from functools import wraps
import uuid

payroll_bp = Blueprint('payroll', __name__, url_prefix='/api/payroll')


# ============ 认证装饰器 ============
def require_auth(f):
    """验证 JWT Token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': '未提供认证信息'}), 401

        try:
            token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header
            # 简单验证 token 存在
            if not token:
                return jsonify({'error': 'Token 无效'}), 401
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': f'认证失败: {str(e)}'}), 401

    return decorated


# ============ 辅助函数 ============
def generate_payroll_no():
    """生成工资单号 GZ-YYYYMMDD-XXXX"""
    today = datetime.now().strftime('%Y%m%d')
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"GZ-{today}-{random_suffix}"


def generate_adjustment_no():
    """生成调整单号 TZ-YYYYMMDD-XXXX"""
    today = datetime.now().strftime('%Y%m%d')
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"TZ-{today}-{random_suffix}"


def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


def calculate_tax(taxable_income, year=None):
    """计算个人所得税（累计预扣法简化版）"""
    # 获取适用的税率表
    brackets = TaxBracket.query.filter(
        TaxBracket.is_active == True
    ).order_by(TaxBracket.min_income).all()

    if not brackets:
        return 0

    # 找到适用的税率档次
    for bracket in brackets:
        max_income = bracket.max_income if bracket.max_income else float('inf')
        if taxable_income <= max_income:
            tax = taxable_income * (bracket.tax_rate / 100) - bracket.quick_deduction
            return max(0, tax)

    # 超过最高档次
    last_bracket = brackets[-1]
    tax = taxable_income * (last_bracket.tax_rate / 100) - last_bracket.quick_deduction
    return max(0, tax)


# ============ 薪资结构 API ============
@payroll_bp.route('/structures', methods=['GET'])
@require_auth
def get_salary_structures():
    """获取薪资结构列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        is_active = request.args.get('is_active')
        department_id = request.args.get('department_id', type=int)
        factory_id = request.args.get('factory_id', type=int)

        query = SalaryStructure.query

        if is_active is not None:
            query = query.filter(SalaryStructure.is_active == (is_active.lower() == 'true'))
        if department_id:
            query = query.filter(SalaryStructure.department_id == department_id)
        if factory_id:
            query = query.filter(SalaryStructure.factory_id == factory_id)

        query = query.order_by(SalaryStructure.is_default.desc(), SalaryStructure.created_at.desc())
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


@payroll_bp.route('/structures', methods=['POST'])
@require_auth
def create_salary_structure():
    """创建薪资结构"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('code') or not data.get('name'):
            return jsonify({'error': '结构编码和名称为必填项'}), 400

        # 检查编码是否已存在
        existing = SalaryStructure.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'error': f'结构编码 {data["code"]} 已存在'}), 400

        structure = SalaryStructure(
            code=data['code'],
            name=data['name'],
            department_id=data.get('department_id'),
            position_id=data.get('position_id'),
            factory_id=data.get('factory_id'),
            structure_items=data.get('structure_items'),
            is_active=data.get('is_active', True),
            is_default=data.get('is_default', False),
            description=data.get('description')
        )

        # 如果设置为默认，取消其他默认
        if structure.is_default:
            SalaryStructure.query.filter(SalaryStructure.is_default == True).update({'is_default': False})

        db.session.add(structure)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': structure.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/structures/<int:id>', methods=['PUT'])
@require_auth
def update_salary_structure(id):
    """更新薪资结构"""
    try:
        structure = SalaryStructure.query.get_or_404(id)
        data = request.get_json()

        if data.get('code') and data['code'] != structure.code:
            existing = SalaryStructure.query.filter_by(code=data['code']).first()
            if existing:
                return jsonify({'error': f'结构编码 {data["code"]} 已存在'}), 400
            structure.code = data['code']

        if data.get('name'):
            structure.name = data['name']
        if 'department_id' in data:
            structure.department_id = data['department_id']
        if 'position_id' in data:
            structure.position_id = data['position_id']
        if 'factory_id' in data:
            structure.factory_id = data['factory_id']
        if 'structure_items' in data:
            structure.structure_items = data['structure_items']
        if 'is_active' in data:
            structure.is_active = data['is_active']
        if 'description' in data:
            structure.description = data['description']

        if data.get('is_default') and not structure.is_default:
            SalaryStructure.query.filter(SalaryStructure.is_default == True).update({'is_default': False})
            structure.is_default = True

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': structure.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/structures/<int:id>', methods=['DELETE'])
@require_auth
def delete_salary_structure(id):
    """删除薪资结构"""
    try:
        structure = SalaryStructure.query.get_or_404(id)

        # 检查是否有员工在使用
        using_count = EmployeeSalary.query.filter_by(salary_structure_id=id, is_current=True).count()
        if using_count > 0:
            return jsonify({'error': f'该薪资结构正在被 {using_count} 名员工使用，无法删除'}), 400

        db.session.delete(structure)
        db.session.commit()
        return jsonify({'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============ 薪资项目 API ============
@payroll_bp.route('/pay-items', methods=['GET'])
@require_auth
def get_pay_items():
    """获取薪资项目列表"""
    try:
        item_type = request.args.get('item_type')
        is_active = request.args.get('is_active')

        query = PayItem.query

        if item_type:
            query = query.filter(PayItem.item_type == item_type)
        if is_active is not None:
            query = query.filter(PayItem.is_active == (is_active.lower() == 'true'))

        items = query.order_by(PayItem.sort_order, PayItem.id).all()

        return jsonify({
            'items': [item.to_dict() for item in items],
            'total': len(items)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/pay-items', methods=['POST'])
@require_auth
def create_pay_item():
    """创建薪资项目"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('name') or not data.get('item_type'):
            return jsonify({'error': '项目编码、名称和类型为必填项'}), 400

        existing = PayItem.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'error': f'项目编码 {data["code"]} 已存在'}), 400

        item = PayItem(
            code=data['code'],
            name=data['name'],
            item_type=data['item_type'],
            calculation_type=data.get('calculation_type', 'fixed'),
            formula=data.get('formula'),
            default_value=data.get('default_value', 0),
            is_taxable=data.get('is_taxable', True),
            is_social_insurance_base=data.get('is_social_insurance_base', False),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0),
            description=data.get('description')
        )

        db.session.add(item)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': item.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/pay-items/<int:id>', methods=['PUT'])
@require_auth
def update_pay_item(id):
    """更新薪资项目"""
    try:
        item = PayItem.query.get_or_404(id)
        data = request.get_json()

        for field in ['name', 'item_type', 'calculation_type', 'formula', 'default_value',
                      'is_taxable', 'is_social_insurance_base', 'is_active', 'sort_order', 'description']:
            if field in data:
                setattr(item, field, data[field])

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': item.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/pay-items/init', methods=['POST'])
@require_auth
def init_pay_items():
    """初始化默认薪资项目"""
    try:
        init_default_pay_items()
        return jsonify({'message': '初始化成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ 员工薪资 API ============
@payroll_bp.route('/employee-salaries', methods=['GET'])
@require_auth
def get_employee_salaries():
    """获取员工薪资配置列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        department_id = request.args.get('department_id', type=int)
        factory_id = request.args.get('factory_id', type=int)
        is_current = request.args.get('is_current', 'true')

        query = EmployeeSalary.query

        if is_current.lower() == 'true':
            query = query.filter(EmployeeSalary.is_current == True)
        if employee_id:
            query = query.filter(EmployeeSalary.employee_id == employee_id)
        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)
        if factory_id:
            query = query.join(Employee).filter(Employee.factory_id == factory_id)

        query = query.order_by(EmployeeSalary.created_at.desc())
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


@payroll_bp.route('/employee-salaries', methods=['POST'])
@require_auth
def create_employee_salary():
    """配置员工薪资"""
    try:
        data = request.get_json()

        if not data.get('employee_id') or not data.get('effective_date'):
            return jsonify({'error': '员工ID和生效日期为必填项'}), 400

        # 验证员工存在
        employee = Employee.query.get(data['employee_id'])
        if not employee:
            return jsonify({'error': '员工不存在'}), 404

        # 将之前的记录标记为非当前
        EmployeeSalary.query.filter_by(
            employee_id=data['employee_id'],
            is_current=True
        ).update({'is_current': False, 'end_date': parse_date(data['effective_date'])})

        salary = EmployeeSalary(
            employee_id=data['employee_id'],
            salary_structure_id=data.get('salary_structure_id'),
            base_salary=data.get('base_salary', 0),
            position_salary=data.get('position_salary', 0),
            performance_salary=data.get('performance_salary', 0),
            housing_allowance=data.get('housing_allowance', 0),
            transport_allowance=data.get('transport_allowance', 0),
            meal_allowance=data.get('meal_allowance', 0),
            phone_allowance=data.get('phone_allowance', 0),
            other_allowance=data.get('other_allowance', 0),
            social_insurance=data.get('social_insurance', 0),
            housing_fund=data.get('housing_fund', 0),
            insurance_base=data.get('insurance_base', 0),
            housing_fund_base=data.get('housing_fund_base', 0),
            salary_type=data.get('salary_type', 'monthly'),
            hourly_rate=data.get('hourly_rate'),
            piece_rate=data.get('piece_rate'),
            bank_name=data.get('bank_name'),
            bank_account=data.get('bank_account'),
            bank_branch=data.get('bank_branch'),
            effective_date=parse_date(data['effective_date']),
            is_current=True
        )

        db.session.add(salary)
        db.session.commit()

        return jsonify({'message': '配置成功', 'data': salary.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/employee-salaries/<int:id>', methods=['PUT'])
@require_auth
def update_employee_salary(id):
    """更新员工薪资配置"""
    try:
        salary = EmployeeSalary.query.get_or_404(id)
        data = request.get_json()

        for field in ['salary_structure_id', 'base_salary', 'position_salary', 'performance_salary',
                      'housing_allowance', 'transport_allowance', 'meal_allowance', 'phone_allowance',
                      'other_allowance', 'social_insurance', 'housing_fund', 'insurance_base',
                      'housing_fund_base', 'salary_type', 'hourly_rate', 'piece_rate',
                      'bank_name', 'bank_account', 'bank_branch']:
            if field in data:
                setattr(salary, field, data[field])

        if 'effective_date' in data:
            salary.effective_date = parse_date(data['effective_date'])
        if 'end_date' in data:
            salary.end_date = parse_date(data['end_date'])

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': salary.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/employee-salaries/<int:employee_id>/current', methods=['GET'])
@require_auth
def get_current_employee_salary(employee_id):
    """获取员工当前薪资配置"""
    try:
        salary = EmployeeSalary.query.filter_by(
            employee_id=employee_id,
            is_current=True
        ).first()

        if not salary:
            return jsonify({'error': '未找到该员工的薪资配置'}), 404

        return jsonify({'data': salary.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ 税率配置 API ============
@payroll_bp.route('/tax-brackets', methods=['GET'])
@require_auth
def get_tax_brackets():
    """获取个税税率表"""
    try:
        is_active = request.args.get('is_active', 'true')

        query = TaxBracket.query

        if is_active.lower() == 'true':
            query = query.filter(TaxBracket.is_active == True)

        brackets = query.order_by(TaxBracket.min_income).all()

        return jsonify({
            'items': [b.to_dict() for b in brackets],
            'total': len(brackets)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/tax-brackets/init', methods=['POST'])
@require_auth
def init_tax_brackets():
    """初始化默认税率表"""
    try:
        init_default_tax_brackets()
        return jsonify({'message': '初始化成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ 社保费率 API ============
@payroll_bp.route('/social-insurance', methods=['GET'])
@require_auth
def get_social_insurance_rates():
    """获取社保公积金费率配置"""
    try:
        city = request.args.get('city')
        factory_id = request.args.get('factory_id', type=int)
        is_active = request.args.get('is_active', 'true')

        query = SocialInsuranceRate.query

        if is_active.lower() == 'true':
            query = query.filter(SocialInsuranceRate.is_active == True)
        if city:
            query = query.filter(SocialInsuranceRate.city == city)
        if factory_id:
            query = query.filter(SocialInsuranceRate.factory_id == factory_id)

        rates = query.order_by(SocialInsuranceRate.code).all()

        return jsonify({
            'items': [r.to_dict() for r in rates],
            'total': len(rates)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/social-insurance', methods=['POST'])
@require_auth
def create_social_insurance_rate():
    """创建社保费率配置"""
    try:
        data = request.get_json()

        if not data.get('code') or not data.get('name') or not data.get('effective_date'):
            return jsonify({'error': '险种编码、名称和生效日期为必填项'}), 400

        existing = SocialInsuranceRate.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'error': f'险种编码 {data["code"]} 已存在'}), 400

        rate = SocialInsuranceRate(
            code=data['code'],
            name=data['name'],
            employee_rate=data.get('employee_rate', 0),
            company_rate=data.get('company_rate', 0),
            min_base=data.get('min_base', 0),
            max_base=data.get('max_base', 0),
            city=data.get('city'),
            factory_id=data.get('factory_id'),
            effective_date=parse_date(data['effective_date']),
            end_date=parse_date(data.get('end_date')),
            is_active=data.get('is_active', True)
        )

        db.session.add(rate)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': rate.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/social-insurance/<int:id>', methods=['PUT'])
@require_auth
def update_social_insurance_rate(id):
    """更新社保费率配置"""
    try:
        rate = SocialInsuranceRate.query.get_or_404(id)
        data = request.get_json()

        for field in ['name', 'employee_rate', 'company_rate', 'min_base', 'max_base',
                      'city', 'factory_id', 'is_active']:
            if field in data:
                setattr(rate, field, data[field])

        if 'effective_date' in data:
            rate.effective_date = parse_date(data['effective_date'])
        if 'end_date' in data:
            rate.end_date = parse_date(data['end_date'])

        db.session.commit()
        return jsonify({'message': '更新成功', 'data': rate.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============ 工资单 API ============
@payroll_bp.route('/payrolls', methods=['GET'])
@require_auth
def get_payrolls():
    """获取工资单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        employee_id = request.args.get('employee_id', type=int)
        department_id = request.args.get('department_id', type=int)
        status = request.args.get('status')

        query = Payroll.query

        if year:
            query = query.filter(Payroll.year == year)
        if month:
            query = query.filter(Payroll.month == month)
        if employee_id:
            query = query.filter(Payroll.employee_id == employee_id)
        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)
        if status:
            query = query.filter(Payroll.status == status)

        query = query.order_by(Payroll.year.desc(), Payroll.month.desc(), Payroll.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [p.to_dict() for p in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/payrolls/<int:id>', methods=['GET'])
@require_auth
def get_payroll(id):
    """获取工资单详情"""
    try:
        payroll = Payroll.query.get_or_404(id)
        return jsonify({'data': payroll.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/calculate', methods=['POST'])
@require_auth
def calculate_payroll():
    """计算工资"""
    try:
        data = request.get_json()

        year = data.get('year')
        month = data.get('month')
        employee_ids = data.get('employee_ids', [])
        department_id = data.get('department_id')
        factory_id = data.get('factory_id')

        if not year or not month:
            return jsonify({'error': '年份和月份为必填项'}), 400

        # 获取要计算工资的员工列表
        query = Employee.query.filter(Employee.employment_status == 'Active')

        if employee_ids:
            query = query.filter(Employee.id.in_(employee_ids))
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        if factory_id:
            query = query.filter(Employee.factory_id == factory_id)

        employees = query.all()

        if not employees:
            return jsonify({'error': '未找到符合条件的员工'}), 404

        results = []
        errors = []

        for emp in employees:
            try:
                # 获取员工薪资配置
                salary_config = EmployeeSalary.query.filter_by(
                    employee_id=emp.id,
                    is_current=True
                ).first()

                if not salary_config:
                    errors.append(f'员工 {emp.name}({emp.empNo}) 未配置薪资信息')
                    continue

                # 检查是否已存在该月工资单
                existing = Payroll.query.filter_by(
                    employee_id=emp.id,
                    year=year,
                    month=month
                ).first()

                if existing:
                    payroll = existing
                else:
                    payroll = Payroll(
                        payroll_no=generate_payroll_no(),
                        employee_id=emp.id,
                        year=year,
                        month=month
                    )

                # 获取考勤汇总
                attendance = MonthlyAttendanceSummary.query.filter_by(
                    employee_id=emp.id,
                    year=year,
                    month=month
                ).first()

                # 计算基本薪资
                payroll.base_salary = salary_config.base_salary
                payroll.position_salary = salary_config.position_salary
                payroll.performance_salary = salary_config.performance_salary

                # 计算补贴
                payroll.housing_allowance = salary_config.housing_allowance
                payroll.transport_allowance = salary_config.transport_allowance
                payroll.meal_allowance = salary_config.meal_allowance
                payroll.other_allowance = (salary_config.phone_allowance +
                                           salary_config.other_allowance)
                payroll.allowances = (payroll.housing_allowance + payroll.transport_allowance +
                                      payroll.meal_allowance + payroll.other_allowance)

                # 处理考勤
                if attendance:
                    payroll.work_days = attendance.work_days
                    payroll.actual_work_days = attendance.actual_work_days
                    payroll.overtime_hours = attendance.overtime_hours

                    # 计算加班费 (假设加班费率为1.5倍)
                    daily_rate = salary_config.base_salary / 21.75  # 月计薪天数
                    hourly_rate = daily_rate / 8
                    payroll.overtime_pay = attendance.overtime_hours * hourly_rate * 1.5

                    # 计算缺勤扣款
                    absent_days = payroll.work_days - payroll.actual_work_days
                    if absent_days > 0:
                        payroll.absence_deduction = absent_days * daily_rate

                    # 迟到扣款
                    payroll.late_deduction = attendance.late_count * 20  # 假设每次迟到扣20元
                else:
                    payroll.work_days = 21.75
                    payroll.actual_work_days = 21.75
                    payroll.overtime_hours = 0
                    payroll.overtime_pay = 0
                    payroll.absence_deduction = 0
                    payroll.late_deduction = 0

                # 社保公积金
                payroll.social_insurance = salary_config.social_insurance
                payroll.housing_fund = salary_config.housing_fund

                # 汇总扣款
                payroll.deductions = (payroll.absence_deduction + payroll.late_deduction +
                                      payroll.leave_deduction + payroll.other_deduction)

                # 计算应发工资
                payroll.gross_salary = (payroll.base_salary + payroll.position_salary +
                                        payroll.performance_salary + payroll.overtime_pay +
                                        payroll.allowances + payroll.bonus +
                                        payroll.performance_bonus - payroll.deductions)

                # 计算应税收入 (扣除五险一金和起征点5000)
                payroll.taxable_income = max(0, payroll.gross_salary -
                                             payroll.social_insurance -
                                             payroll.housing_fund - 5000)

                # 计算个税
                payroll.tax = calculate_tax(payroll.taxable_income)

                # 计算实发工资
                payroll.net_salary = (payroll.gross_salary - payroll.social_insurance -
                                      payroll.housing_fund - payroll.tax)

                # 更新状态
                payroll.status = 'calculated'
                payroll.calculated_at = datetime.now()

                if not existing:
                    db.session.add(payroll)

                results.append(payroll.to_dict())

            except Exception as e:
                errors.append(f'员工 {emp.name}({emp.empNo}) 计算失败: {str(e)}')

        db.session.commit()

        return jsonify({
            'message': f'成功计算 {len(results)} 人工资',
            'results': results,
            'errors': errors
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/payrolls/<int:id>/approve', methods=['PUT'])
@require_auth
def approve_payroll(id):
    """审批工资单"""
    try:
        payroll = Payroll.query.get_or_404(id)
        data = request.get_json()

        if payroll.status not in ['calculated', 'draft']:
            return jsonify({'error': f'当前状态 {payroll.status} 无法审批'}), 400

        payroll.status = 'approved'
        payroll.approved_at = datetime.now()
        payroll.approved_by = data.get('approver_id')

        db.session.commit()
        return jsonify({'message': '审批成功', 'data': payroll.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/payrolls/batch-approve', methods=['PUT'])
@require_auth
def batch_approve_payrolls():
    """批量审批工资单"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        approver_id = data.get('approver_id')

        if not ids:
            return jsonify({'error': '请选择要审批的工资单'}), 400

        count = Payroll.query.filter(
            Payroll.id.in_(ids),
            Payroll.status.in_(['calculated', 'draft'])
        ).update({
            'status': 'approved',
            'approved_at': datetime.now(),
            'approved_by': approver_id
        }, synchronize_session=False)

        db.session.commit()
        return jsonify({'message': f'成功审批 {count} 条工资单'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/payrolls/<int:id>/pay', methods=['PUT'])
@require_auth
def mark_payroll_paid(id):
    """标记工资单已发放"""
    try:
        payroll = Payroll.query.get_or_404(id)
        data = request.get_json()

        if payroll.status != 'approved':
            return jsonify({'error': '只有已审批的工资单才能标记为已发放'}), 400

        payroll.status = 'paid'
        payroll.paid_at = datetime.now()
        payroll.paid_by = data.get('paid_by')

        db.session.commit()
        return jsonify({'message': '标记成功', 'data': payroll.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/my-payslips', methods=['GET'])
@require_auth
def get_my_payslips():
    """获取我的工资条"""
    try:
        employee_id = request.args.get('employee_id', type=int)
        year = request.args.get('year', type=int)

        if not employee_id:
            return jsonify({'error': '员工ID为必填项'}), 400

        query = Payroll.query.filter(
            Payroll.employee_id == employee_id,
            Payroll.status.in_(['approved', 'paid'])
        )

        if year:
            query = query.filter(Payroll.year == year)

        payslips = query.order_by(Payroll.year.desc(), Payroll.month.desc()).all()

        return jsonify({
            'items': [p.to_dict() for p in payslips],
            'total': len(payslips)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============ 薪资调整 API ============
@payroll_bp.route('/adjustments', methods=['GET'])
@require_auth
def get_salary_adjustments():
    """获取薪资调整记录列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        employee_id = request.args.get('employee_id', type=int)
        status = request.args.get('status')
        adjustment_type = request.args.get('adjustment_type')

        query = SalaryAdjustment.query

        if employee_id:
            query = query.filter(SalaryAdjustment.employee_id == employee_id)
        if status:
            query = query.filter(SalaryAdjustment.status == status)
        if adjustment_type:
            query = query.filter(SalaryAdjustment.adjustment_type == adjustment_type)

        query = query.order_by(SalaryAdjustment.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [a.to_dict() for a in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/adjustments', methods=['POST'])
@require_auth
def create_salary_adjustment():
    """创建薪资调整申请"""
    try:
        data = request.get_json()

        if not data.get('employee_id') or not data.get('adjustment_type') or not data.get('effective_date'):
            return jsonify({'error': '员工ID、调整类型和生效日期为必填项'}), 400

        # 获取员工当前薪资
        current_salary = EmployeeSalary.query.filter_by(
            employee_id=data['employee_id'],
            is_current=True
        ).first()

        if not current_salary:
            return jsonify({'error': '该员工未配置薪资信息'}), 404

        adjustment = SalaryAdjustment(
            adjustment_no=generate_adjustment_no(),
            employee_id=data['employee_id'],
            adjustment_type=data['adjustment_type'],
            reason=data.get('reason', ''),
            before_base_salary=current_salary.base_salary,
            after_base_salary=data.get('after_base_salary', current_salary.base_salary),
            before_position_salary=current_salary.position_salary,
            after_position_salary=data.get('after_position_salary', current_salary.position_salary),
            before_total=current_salary.total_salary,
            after_total=data.get('after_total', current_salary.total_salary),
            effective_date=parse_date(data['effective_date']),
            status='pending',
            attachment=data.get('attachment'),
            created_by=data.get('created_by')
        )

        # 计算调整金额和比例
        adjustment.adjustment_amount = adjustment.after_total - adjustment.before_total
        if adjustment.before_total > 0:
            adjustment.adjustment_rate = round((adjustment.adjustment_amount / adjustment.before_total) * 100, 2)

        db.session.add(adjustment)
        db.session.commit()

        return jsonify({'message': '创建成功', 'data': adjustment.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@payroll_bp.route('/adjustments/<int:id>/approve', methods=['PUT'])
@require_auth
def approve_salary_adjustment(id):
    """审批薪资调整"""
    try:
        adjustment = SalaryAdjustment.query.get_or_404(id)
        data = request.get_json()

        action = data.get('action')  # approve / reject

        if adjustment.status != 'pending':
            return jsonify({'error': '该调整申请已处理'}), 400

        if action == 'approve':
            adjustment.status = 'approved'

            # 创建新的薪资记录
            current_salary = EmployeeSalary.query.filter_by(
                employee_id=adjustment.employee_id,
                is_current=True
            ).first()

            if current_salary:
                # 结束当前薪资
                current_salary.is_current = False
                current_salary.end_date = adjustment.effective_date

                # 创建新薪资
                new_salary = EmployeeSalary(
                    employee_id=adjustment.employee_id,
                    salary_structure_id=current_salary.salary_structure_id,
                    base_salary=adjustment.after_base_salary,
                    position_salary=adjustment.after_position_salary,
                    performance_salary=current_salary.performance_salary,
                    housing_allowance=current_salary.housing_allowance,
                    transport_allowance=current_salary.transport_allowance,
                    meal_allowance=current_salary.meal_allowance,
                    phone_allowance=current_salary.phone_allowance,
                    other_allowance=current_salary.other_allowance,
                    social_insurance=current_salary.social_insurance,
                    housing_fund=current_salary.housing_fund,
                    insurance_base=current_salary.insurance_base,
                    housing_fund_base=current_salary.housing_fund_base,
                    salary_type=current_salary.salary_type,
                    hourly_rate=current_salary.hourly_rate,
                    piece_rate=current_salary.piece_rate,
                    bank_name=current_salary.bank_name,
                    bank_account=current_salary.bank_account,
                    bank_branch=current_salary.bank_branch,
                    effective_date=adjustment.effective_date,
                    is_current=True
                )
                db.session.add(new_salary)

        elif action == 'reject':
            adjustment.status = 'rejected'
        else:
            return jsonify({'error': '无效的操作类型'}), 400

        adjustment.approver_id = data.get('approver_id')
        adjustment.approved_at = datetime.now()
        adjustment.approval_remark = data.get('remark')

        db.session.commit()
        return jsonify({'message': '审批成功', 'data': adjustment.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ============ 统计报表 API ============
@payroll_bp.route('/statistics/summary', methods=['GET'])
@require_auth
def get_payroll_summary():
    """获取工资统计汇总"""
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        department_id = request.args.get('department_id', type=int)
        factory_id = request.args.get('factory_id', type=int)

        if not year or not month:
            return jsonify({'error': '年份和月份为必填项'}), 400

        query = Payroll.query.filter(
            Payroll.year == year,
            Payroll.month == month
        )

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)
        if factory_id:
            query = query.join(Employee).filter(Employee.factory_id == factory_id)

        payrolls = query.all()

        if not payrolls:
            return jsonify({
                'year': year,
                'month': month,
                'employee_count': 0,
                'total_gross': 0,
                'total_net': 0,
                'total_tax': 0,
                'total_insurance': 0,
                'avg_salary': 0
            })

        total_gross = sum(p.gross_salary for p in payrolls)
        total_net = sum(p.net_salary for p in payrolls)
        total_tax = sum(p.tax for p in payrolls)
        total_insurance = sum(p.social_insurance + p.housing_fund for p in payrolls)

        return jsonify({
            'year': year,
            'month': month,
            'employee_count': len(payrolls),
            'total_gross': round(total_gross, 2),
            'total_net': round(total_net, 2),
            'total_tax': round(total_tax, 2),
            'total_insurance': round(total_insurance, 2),
            'avg_salary': round(total_net / len(payrolls), 2) if payrolls else 0,
            'by_status': {
                'draft': len([p for p in payrolls if p.status == 'draft']),
                'calculated': len([p for p in payrolls if p.status == 'calculated']),
                'approved': len([p for p in payrolls if p.status == 'approved']),
                'paid': len([p for p in payrolls if p.status == 'paid'])
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
