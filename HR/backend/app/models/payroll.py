"""
薪资管理数据模型
包含: 薪资结构、薪资项目、工资单、薪资调整
"""
from app import db
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Date, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum


class PayItemType(enum.Enum):
    """薪资项目类型"""
    EARNING = 'earning'      # 收入项
    DEDUCTION = 'deduction'  # 扣减项
    SUBSIDY = 'subsidy'      # 补贴项
    TAX = 'tax'              # 税费项


class PayrollStatus(enum.Enum):
    """工资单状态"""
    DRAFT = 'draft'          # 草稿
    CALCULATED = 'calculated'  # 已计算
    APPROVED = 'approved'    # 已审批
    PAID = 'paid'            # 已发放
    CANCELLED = 'cancelled'  # 已取消


class SalaryStructure(db.Model):
    """薪资结构表 - 定义薪资计算规则"""
    __tablename__ = 'salary_structures'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='结构编码')
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='结构名称')

    # 适用范围
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('departments.id'), comment='适用部门')
    position_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('positions.id'), comment='适用职位')
    factory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('factories.id'), comment='适用工厂')

    # 薪资组成配置 (JSON格式)
    # [{"item_id": 1, "formula": "base", "rate": 1.0}, ...]
    structure_items: Mapped[Optional[str]] = mapped_column(JSON, comment='薪资结构项配置')

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否默认')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='结构描述')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')

    # 关系
    department = relationship('Department', backref='salary_structures')
    position = relationship('Position', backref='salary_structures')
    factory = relationship('Factory', backref='salary_structures')

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'position_id': self.position_id,
            'position_name': self.position.name if self.position else None,
            'factory_id': self.factory_id,
            'factory_name': self.factory.name if self.factory else None,
            'structure_items': self.structure_items,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class PayItem(db.Model):
    """薪资项目表 - 定义各类薪资项"""
    __tablename__ = 'pay_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='项目编码')
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='项目名称')
    item_type: Mapped[str] = mapped_column(String(20), nullable=False, comment='项目类型')

    # 计算规则
    calculation_type: Mapped[str] = mapped_column(String(20), default='fixed', comment='计算方式(fixed/formula/percent)')
    formula: Mapped[Optional[str]] = mapped_column(Text, comment='计算公式')
    default_value: Mapped[float] = mapped_column(Float, default=0, comment='默认值')

    # 税务相关
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否计税')
    is_social_insurance_base: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否计入社保基数')

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment='排序顺序')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='项目描述')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'item_type': self.item_type,
            'calculation_type': self.calculation_type,
            'formula': self.formula,
            'default_value': self.default_value,
            'is_taxable': self.is_taxable,
            'is_social_insurance_base': self.is_social_insurance_base,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class EmployeeSalary(db.Model):
    """员工薪资档案表 - 记录员工当前薪资信息"""
    __tablename__ = 'employee_salaries'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    salary_structure_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('salary_structures.id'), comment='薪资结构ID')

    # 基本薪资
    base_salary: Mapped[float] = mapped_column(Float, default=0, comment='基本工资')
    position_salary: Mapped[float] = mapped_column(Float, default=0, comment='岗位工资')
    performance_salary: Mapped[float] = mapped_column(Float, default=0, comment='绩效工资')

    # 各类补贴
    housing_allowance: Mapped[float] = mapped_column(Float, default=0, comment='住房补贴')
    transport_allowance: Mapped[float] = mapped_column(Float, default=0, comment='交通补贴')
    meal_allowance: Mapped[float] = mapped_column(Float, default=0, comment='餐饮补贴')
    phone_allowance: Mapped[float] = mapped_column(Float, default=0, comment='通讯补贴')
    other_allowance: Mapped[float] = mapped_column(Float, default=0, comment='其他补贴')

    # 社保公积金（个人部分）
    social_insurance: Mapped[float] = mapped_column(Float, default=0, comment='社保个人')
    housing_fund: Mapped[float] = mapped_column(Float, default=0, comment='公积金个人')

    # 社保公积金基数
    insurance_base: Mapped[float] = mapped_column(Float, default=0, comment='社保基数')
    housing_fund_base: Mapped[float] = mapped_column(Float, default=0, comment='公积金基数')

    # 计算方式
    salary_type: Mapped[str] = mapped_column(String(20), default='monthly', comment='薪资类型(monthly/hourly/piece)')
    hourly_rate: Mapped[Optional[float]] = mapped_column(Float, comment='时薪')
    piece_rate: Mapped[Optional[float]] = mapped_column(Float, comment='计件单价')

    # 银行账户
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), comment='开户银行')
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), comment='银行账号')
    bank_branch: Mapped[Optional[str]] = mapped_column(String(200), comment='支行名称')

    # 生效日期
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, comment='生效日期')
    end_date: Mapped[Optional[date]] = mapped_column(Date, comment='结束日期')
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否当前生效')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')

    # 关系
    employee = relationship('Employee', backref='salary_records')
    salary_structure = relationship('SalaryStructure', backref='employee_salaries')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'salary_structure_id': self.salary_structure_id,
            'salary_structure_name': self.salary_structure.name if self.salary_structure else None,
            'base_salary': self.base_salary,
            'position_salary': self.position_salary,
            'performance_salary': self.performance_salary,
            'housing_allowance': self.housing_allowance,
            'transport_allowance': self.transport_allowance,
            'meal_allowance': self.meal_allowance,
            'phone_allowance': self.phone_allowance,
            'other_allowance': self.other_allowance,
            'social_insurance': self.social_insurance,
            'housing_fund': self.housing_fund,
            'insurance_base': self.insurance_base,
            'housing_fund_base': self.housing_fund_base,
            'salary_type': self.salary_type,
            'hourly_rate': self.hourly_rate,
            'piece_rate': self.piece_rate,
            'bank_name': self.bank_name,
            'bank_account': self.bank_account,
            'bank_branch': self.bank_branch,
            'effective_date': self.effective_date.strftime('%Y-%m-%d') if self.effective_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'is_current': self.is_current,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    @property
    def total_salary(self):
        """计算薪资总额"""
        return (self.base_salary + self.position_salary + self.performance_salary +
                self.housing_allowance + self.transport_allowance + self.meal_allowance +
                self.phone_allowance + self.other_allowance)


class Payroll(db.Model):
    """工资单表 - 月度工资记录"""
    __tablename__ = 'payrolls'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payroll_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='工资单号')
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment='年份')
    month: Mapped[int] = mapped_column(Integer, nullable=False, comment='月份')

    # 基本薪资
    base_salary: Mapped[float] = mapped_column(Float, default=0, comment='基本工资')
    position_salary: Mapped[float] = mapped_column(Float, default=0, comment='岗位工资')
    performance_salary: Mapped[float] = mapped_column(Float, default=0, comment='绩效工资')

    # 考勤相关
    work_days: Mapped[float] = mapped_column(Float, default=0, comment='应出勤天数')
    actual_work_days: Mapped[float] = mapped_column(Float, default=0, comment='实际出勤天数')
    overtime_hours: Mapped[float] = mapped_column(Float, default=0, comment='加班时长')
    overtime_pay: Mapped[float] = mapped_column(Float, default=0, comment='加班费')

    # 各类补贴
    allowances: Mapped[float] = mapped_column(Float, default=0, comment='补贴合计')
    housing_allowance: Mapped[float] = mapped_column(Float, default=0, comment='住房补贴')
    transport_allowance: Mapped[float] = mapped_column(Float, default=0, comment='交通补贴')
    meal_allowance: Mapped[float] = mapped_column(Float, default=0, comment='餐饮补贴')
    other_allowance: Mapped[float] = mapped_column(Float, default=0, comment='其他补贴')

    # 奖金
    bonus: Mapped[float] = mapped_column(Float, default=0, comment='奖金')
    performance_bonus: Mapped[float] = mapped_column(Float, default=0, comment='绩效奖金')

    # 扣款
    deductions: Mapped[float] = mapped_column(Float, default=0, comment='扣款合计')
    absence_deduction: Mapped[float] = mapped_column(Float, default=0, comment='缺勤扣款')
    late_deduction: Mapped[float] = mapped_column(Float, default=0, comment='迟到扣款')
    leave_deduction: Mapped[float] = mapped_column(Float, default=0, comment='请假扣款')
    other_deduction: Mapped[float] = mapped_column(Float, default=0, comment='其他扣款')

    # 社保公积金
    social_insurance: Mapped[float] = mapped_column(Float, default=0, comment='社保个人')
    housing_fund: Mapped[float] = mapped_column(Float, default=0, comment='公积金个人')

    # 税前税后
    gross_salary: Mapped[float] = mapped_column(Float, default=0, comment='应发工资')
    taxable_income: Mapped[float] = mapped_column(Float, default=0, comment='应税收入')
    tax: Mapped[float] = mapped_column(Float, default=0, comment='个人所得税')
    net_salary: Mapped[float] = mapped_column(Float, default=0, comment='实发工资')

    # 明细 (JSON格式，存储所有薪资项明细)
    pay_items_detail: Mapped[Optional[str]] = mapped_column(JSON, comment='薪资项明细')

    # 状态
    status: Mapped[str] = mapped_column(String(20), default='draft', comment='状态')
    calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='计算时间')
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='审批时间')
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, comment='审批人')
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='发放时间')
    paid_by: Mapped[Optional[int]] = mapped_column(Integer, comment='发放人')

    # 备注
    remark: Mapped[Optional[str]] = mapped_column(Text, comment='备注')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')

    # 关系
    employee = relationship('Employee', backref='payrolls')

    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'year', 'month', name='uq_employee_payroll_month'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'payroll_no': self.payroll_no,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'department': self.employee.department if self.employee else None,
            'year': self.year,
            'month': self.month,
            'base_salary': self.base_salary,
            'position_salary': self.position_salary,
            'performance_salary': self.performance_salary,
            'work_days': self.work_days,
            'actual_work_days': self.actual_work_days,
            'overtime_hours': self.overtime_hours,
            'overtime_pay': self.overtime_pay,
            'allowances': self.allowances,
            'housing_allowance': self.housing_allowance,
            'transport_allowance': self.transport_allowance,
            'meal_allowance': self.meal_allowance,
            'other_allowance': self.other_allowance,
            'bonus': self.bonus,
            'performance_bonus': self.performance_bonus,
            'deductions': self.deductions,
            'absence_deduction': self.absence_deduction,
            'late_deduction': self.late_deduction,
            'leave_deduction': self.leave_deduction,
            'other_deduction': self.other_deduction,
            'social_insurance': self.social_insurance,
            'housing_fund': self.housing_fund,
            'gross_salary': self.gross_salary,
            'taxable_income': self.taxable_income,
            'tax': self.tax,
            'net_salary': self.net_salary,
            'pay_items_detail': self.pay_items_detail,
            'status': self.status,
            'calculated_at': self.calculated_at.strftime('%Y-%m-%d %H:%M:%S') if self.calculated_at else None,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'paid_at': self.paid_at.strftime('%Y-%m-%d %H:%M:%S') if self.paid_at else None,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class SalaryAdjustment(db.Model):
    """薪资调整记录表"""
    __tablename__ = 'salary_adjustments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    adjustment_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='调整单号')
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')

    # 调整类型
    adjustment_type: Mapped[str] = mapped_column(String(20), nullable=False, comment='调整类型(promotion/annual/other)')
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment='调整原因')

    # 调整前后
    before_base_salary: Mapped[float] = mapped_column(Float, default=0, comment='调整前基本工资')
    after_base_salary: Mapped[float] = mapped_column(Float, default=0, comment='调整后基本工资')
    before_position_salary: Mapped[float] = mapped_column(Float, default=0, comment='调整前岗位工资')
    after_position_salary: Mapped[float] = mapped_column(Float, default=0, comment='调整后岗位工资')
    before_total: Mapped[float] = mapped_column(Float, default=0, comment='调整前总额')
    after_total: Mapped[float] = mapped_column(Float, default=0, comment='调整后总额')

    # 调整幅度
    adjustment_amount: Mapped[float] = mapped_column(Float, default=0, comment='调整金额')
    adjustment_rate: Mapped[float] = mapped_column(Float, default=0, comment='调整比例(%)')

    # 生效日期
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, comment='生效日期')

    # 审批
    status: Mapped[str] = mapped_column(String(20), default='pending', comment='状态')
    approver_id: Mapped[Optional[int]] = mapped_column(Integer, comment='审批人')
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='审批时间')
    approval_remark: Mapped[Optional[str]] = mapped_column(Text, comment='审批备注')

    # 附件
    attachment: Mapped[Optional[str]] = mapped_column(String(255), comment='附件')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人')

    # 关系
    employee = relationship('Employee', backref='salary_adjustments')

    def to_dict(self):
        return {
            'id': self.id,
            'adjustment_no': self.adjustment_no,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'department': self.employee.department if self.employee else None,
            'adjustment_type': self.adjustment_type,
            'reason': self.reason,
            'before_base_salary': self.before_base_salary,
            'after_base_salary': self.after_base_salary,
            'before_position_salary': self.before_position_salary,
            'after_position_salary': self.after_position_salary,
            'before_total': self.before_total,
            'after_total': self.after_total,
            'adjustment_amount': self.adjustment_amount,
            'adjustment_rate': self.adjustment_rate,
            'effective_date': self.effective_date.strftime('%Y-%m-%d') if self.effective_date else None,
            'status': self.status,
            'approver_id': self.approver_id,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'approval_remark': self.approval_remark,
            'attachment': self.attachment,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class TaxBracket(db.Model):
    """个税税率表"""
    __tablename__ = 'tax_brackets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='档次名称')
    min_income: Mapped[float] = mapped_column(Float, nullable=False, comment='起始收入')
    max_income: Mapped[Optional[float]] = mapped_column(Float, comment='截止收入(null=无上限)')
    tax_rate: Mapped[float] = mapped_column(Float, nullable=False, comment='税率(%)')
    quick_deduction: Mapped[float] = mapped_column(Float, default=0, comment='速算扣除数')

    # 生效日期
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, comment='生效日期')
    end_date: Mapped[Optional[date]] = mapped_column(Date, comment='结束日期')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'min_income': self.min_income,
            'max_income': self.max_income,
            'tax_rate': self.tax_rate,
            'quick_deduction': self.quick_deduction,
            'effective_date': self.effective_date.strftime('%Y-%m-%d') if self.effective_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class SocialInsuranceRate(db.Model):
    """社保公积金费率表"""
    __tablename__ = 'social_insurance_rates'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='险种名称')
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='险种编码')

    # 费率
    employee_rate: Mapped[float] = mapped_column(Float, default=0, comment='个人费率(%)')
    company_rate: Mapped[float] = mapped_column(Float, default=0, comment='公司费率(%)')

    # 基数上下限
    min_base: Mapped[float] = mapped_column(Float, default=0, comment='基数下限')
    max_base: Mapped[float] = mapped_column(Float, default=0, comment='基数上限')

    # 适用地区
    city: Mapped[Optional[str]] = mapped_column(String(100), comment='适用城市')
    factory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('factories.id'), comment='适用工厂')

    # 生效日期
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, comment='生效日期')
    end_date: Mapped[Optional[date]] = mapped_column(Date, comment='结束日期')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    factory = relationship('Factory', backref='insurance_rates')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'employee_rate': self.employee_rate,
            'company_rate': self.company_rate,
            'min_base': self.min_base,
            'max_base': self.max_base,
            'city': self.city,
            'factory_id': self.factory_id,
            'factory_name': self.factory.name if self.factory else None,
            'effective_date': self.effective_date.strftime('%Y-%m-%d') if self.effective_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


def init_default_pay_items():
    """初始化默认薪资项目"""
    default_items = [
        # 收入项
        {'code': 'base_salary', 'name': '基本工资', 'item_type': 'earning', 'is_taxable': True, 'is_social_insurance_base': True, 'sort_order': 1},
        {'code': 'position_salary', 'name': '岗位工资', 'item_type': 'earning', 'is_taxable': True, 'is_social_insurance_base': True, 'sort_order': 2},
        {'code': 'performance_salary', 'name': '绩效工资', 'item_type': 'earning', 'is_taxable': True, 'sort_order': 3},
        {'code': 'overtime_pay', 'name': '加班费', 'item_type': 'earning', 'is_taxable': True, 'sort_order': 4},
        {'code': 'bonus', 'name': '奖金', 'item_type': 'earning', 'is_taxable': True, 'sort_order': 5},
        # 补贴项
        {'code': 'housing_allowance', 'name': '住房补贴', 'item_type': 'subsidy', 'is_taxable': True, 'sort_order': 10},
        {'code': 'transport_allowance', 'name': '交通补贴', 'item_type': 'subsidy', 'is_taxable': True, 'sort_order': 11},
        {'code': 'meal_allowance', 'name': '餐饮补贴', 'item_type': 'subsidy', 'is_taxable': True, 'sort_order': 12},
        {'code': 'phone_allowance', 'name': '通讯补贴', 'item_type': 'subsidy', 'is_taxable': True, 'sort_order': 13},
        # 扣减项
        {'code': 'absence_deduction', 'name': '缺勤扣款', 'item_type': 'deduction', 'is_taxable': False, 'sort_order': 20},
        {'code': 'late_deduction', 'name': '迟到扣款', 'item_type': 'deduction', 'is_taxable': False, 'sort_order': 21},
        {'code': 'leave_deduction', 'name': '请假扣款', 'item_type': 'deduction', 'is_taxable': False, 'sort_order': 22},
        # 社保
        {'code': 'pension', 'name': '养老保险', 'item_type': 'deduction', 'is_taxable': False, 'sort_order': 30},
        {'code': 'medical', 'name': '医疗保险', 'item_type': 'deduction', 'is_taxable': False, 'sort_order': 31},
        {'code': 'unemployment', 'name': '失业保险', 'item_type': 'deduction', 'is_taxable': False, 'sort_order': 32},
        {'code': 'housing_fund', 'name': '住房公积金', 'item_type': 'deduction', 'is_taxable': False, 'sort_order': 33},
        # 税费
        {'code': 'income_tax', 'name': '个人所得税', 'item_type': 'tax', 'is_taxable': False, 'sort_order': 40},
    ]

    for item_data in default_items:
        existing = PayItem.query.filter_by(code=item_data['code']).first()
        if not existing:
            item = PayItem(**item_data)
            db.session.add(item)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"初始化薪资项目失败: {e}")


def init_default_tax_brackets():
    """初始化中国个税税率表（2019年新税法）"""
    tax_brackets = [
        {'name': '不超过36000元', 'min_income': 0, 'max_income': 36000, 'tax_rate': 3, 'quick_deduction': 0},
        {'name': '超过36000元至144000元', 'min_income': 36000, 'max_income': 144000, 'tax_rate': 10, 'quick_deduction': 2520},
        {'name': '超过144000元至300000元', 'min_income': 144000, 'max_income': 300000, 'tax_rate': 20, 'quick_deduction': 16920},
        {'name': '超过300000元至420000元', 'min_income': 300000, 'max_income': 420000, 'tax_rate': 25, 'quick_deduction': 31920},
        {'name': '超过420000元至660000元', 'min_income': 420000, 'max_income': 660000, 'tax_rate': 30, 'quick_deduction': 52920},
        {'name': '超过660000元至960000元', 'min_income': 660000, 'max_income': 960000, 'tax_rate': 35, 'quick_deduction': 85920},
        {'name': '超过960000元', 'min_income': 960000, 'max_income': None, 'tax_rate': 45, 'quick_deduction': 181920},
    ]

    effective_date = date(2019, 1, 1)

    for bracket_data in tax_brackets:
        existing = TaxBracket.query.filter_by(
            min_income=bracket_data['min_income'],
            effective_date=effective_date
        ).first()
        if not existing:
            bracket = TaxBracket(
                effective_date=effective_date,
                **bracket_data
            )
            db.session.add(bracket)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"初始化税率表失败: {e}")
