"""
假期管理数据模型
包含: 假期类型、假期余额、请假申请、审批流程
"""
from app import db
from datetime import datetime, date, time
from sqlalchemy import String, Integer, Float, Date, DateTime, Time, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum


class LeaveCategory(enum.Enum):
    """假期类别"""
    STATUTORY = 'statutory'      # 法定假期（年假、婚假、产假等）
    PERSONAL = 'personal'        # 个人事假
    SICK = 'sick'                # 病假
    COMPENSATION = 'compensation'  # 调休假（加班补偿）
    OTHER = 'other'              # 其他


class LeaveRequestStatus(enum.Enum):
    """请假申请状态"""
    DRAFT = 'draft'              # 草稿
    PENDING = 'pending'          # 待审批
    APPROVED = 'approved'        # 已批准
    REJECTED = 'rejected'        # 已拒绝
    CANCELLED = 'cancelled'      # 已取消
    COMPLETED = 'completed'      # 已销假


class LeaveType(db.Model):
    """假期类型表"""
    __tablename__ = 'leave_types'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='假期编码')
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='假期名称')
    category: Mapped[str] = mapped_column(String(20), default='personal', comment='假期类别')

    # 假期规则
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否带薪')
    pay_rate: Mapped[float] = mapped_column(Float, default=1.0, comment='薪资比例(1.0=全薪)')
    min_days: Mapped[float] = mapped_column(Float, default=0.5, comment='最小请假天数')
    max_days: Mapped[Optional[float]] = mapped_column(Float, comment='最大请假天数(null=无限制)')
    unit: Mapped[str] = mapped_column(String(10), default='day', comment='计算单位(day/hour)')

    # 额度规则
    has_quota: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否有额度限制')
    default_quota: Mapped[float] = mapped_column(Float, default=0, comment='默认年度额度')
    quota_unit: Mapped[str] = mapped_column(String(10), default='day', comment='额度单位')
    can_carry_over: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否可结转')
    max_carry_over: Mapped[float] = mapped_column(Float, default=0, comment='最大结转额度')

    # 审批规则
    require_approval: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否需要审批')
    require_attachment: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否需要附件')
    advance_days: Mapped[int] = mapped_column(Integer, default=0, comment='需提前申请天数')

    # 适用范围
    applicable_gender: Mapped[Optional[str]] = mapped_column(String(10), comment='适用性别(male/female/null=全部)')
    min_service_months: Mapped[int] = mapped_column(Integer, default=0, comment='最低服务月数')

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment='排序顺序')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='假期说明')
    color: Mapped[Optional[str]] = mapped_column(String(20), comment='显示颜色')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category,
            'is_paid': self.is_paid,
            'pay_rate': self.pay_rate,
            'min_days': self.min_days,
            'max_days': self.max_days,
            'unit': self.unit,
            'has_quota': self.has_quota,
            'default_quota': self.default_quota,
            'quota_unit': self.quota_unit,
            'can_carry_over': self.can_carry_over,
            'max_carry_over': self.max_carry_over,
            'require_approval': self.require_approval,
            'require_attachment': self.require_attachment,
            'advance_days': self.advance_days,
            'applicable_gender': self.applicable_gender,
            'min_service_months': self.min_service_months,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'description': self.description,
            'color': self.color,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class LeaveBalance(db.Model):
    """假期余额表"""
    __tablename__ = 'leave_balances'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    leave_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('leave_types.id'), nullable=False, comment='假期类型ID')
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment='年度')

    # 额度信息
    initial_balance: Mapped[float] = mapped_column(Float, default=0, comment='初始额度')
    carry_over: Mapped[float] = mapped_column(Float, default=0, comment='结转额度')
    adjustment: Mapped[float] = mapped_column(Float, default=0, comment='调整额度')
    total_balance: Mapped[float] = mapped_column(Float, default=0, comment='总额度')

    # 使用情况
    used: Mapped[float] = mapped_column(Float, default=0, comment='已使用')
    pending: Mapped[float] = mapped_column(Float, default=0, comment='审批中')
    remaining: Mapped[float] = mapped_column(Float, default=0, comment='剩余额度')

    # 备注
    remark: Mapped[Optional[str]] = mapped_column(Text, comment='备注')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    employee = relationship('Employee', backref='leave_balances')
    leave_type = relationship('LeaveType', backref='balances')

    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'leave_type_id', 'year', name='uq_employee_leave_year'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name if self.leave_type else None,
            'year': self.year,
            'initial_balance': self.initial_balance,
            'carry_over': self.carry_over,
            'adjustment': self.adjustment,
            'total_balance': self.total_balance,
            'used': self.used,
            'pending': self.pending,
            'remaining': self.remaining,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def update_remaining(self):
        """更新剩余额度"""
        self.remaining = self.total_balance - self.used - self.pending


class LeaveRequest(db.Model):
    """请假申请表"""
    __tablename__ = 'leave_requests'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='申请单号')
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    leave_type_id: Mapped[int] = mapped_column(Integer, ForeignKey('leave_types.id'), nullable=False, comment='假期类型ID')

    # 请假时间
    start_date: Mapped[date] = mapped_column(Date, nullable=False, comment='开始日期')
    end_date: Mapped[date] = mapped_column(Date, nullable=False, comment='结束日期')
    start_time: Mapped[Optional[time]] = mapped_column(Time, comment='开始时间(用于半天假)')
    end_time: Mapped[Optional[time]] = mapped_column(Time, comment='结束时间(用于半天假)')
    duration: Mapped[float] = mapped_column(Float, nullable=False, comment='请假时长')
    duration_unit: Mapped[str] = mapped_column(String(10), default='day', comment='时长单位')

    # 申请原因
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment='请假原因')
    attachment: Mapped[Optional[str]] = mapped_column(String(255), comment='附件路径')

    # 状态
    status: Mapped[str] = mapped_column(String(20), default='pending', comment='申请状态')

    # 审批信息
    approver_id: Mapped[Optional[int]] = mapped_column(Integer, comment='审批人ID')
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='审批时间')
    approval_remark: Mapped[Optional[str]] = mapped_column(Text, comment='审批备注')

    # 多级审批
    approval_flow: Mapped[Optional[str]] = mapped_column(JSON, comment='审批流程记录')
    current_approver_level: Mapped[int] = mapped_column(Integer, default=1, comment='当前审批级别')

    # 销假信息
    actual_return_date: Mapped[Optional[date]] = mapped_column(Date, comment='实际返回日期')
    actual_duration: Mapped[Optional[float]] = mapped_column(Float, comment='实际请假天数')
    return_remark: Mapped[Optional[str]] = mapped_column(Text, comment='销假备注')

    # 代理人
    proxy_employee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('employees.id'), comment='工作代理人ID')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    employee = relationship('Employee', foreign_keys=[employee_id], backref='leave_requests')
    leave_type = relationship('LeaveType', backref='requests')
    proxy_employee = relationship('Employee', foreign_keys=[proxy_employee_id])

    def to_dict(self):
        return {
            'id': self.id,
            'request_no': self.request_no,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'department': self.employee.department if self.employee else None,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name if self.leave_type else None,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'duration': self.duration,
            'duration_unit': self.duration_unit,
            'reason': self.reason,
            'attachment': self.attachment,
            'status': self.status,
            'approver_id': self.approver_id,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'approval_remark': self.approval_remark,
            'actual_return_date': self.actual_return_date.strftime('%Y-%m-%d') if self.actual_return_date else None,
            'actual_duration': self.actual_duration,
            'return_remark': self.return_remark,
            'proxy_employee_id': self.proxy_employee_id,
            'proxy_employee_name': self.proxy_employee.name if self.proxy_employee else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class LeaveApprovalFlow(db.Model):
    """请假审批流程表"""
    __tablename__ = 'leave_approval_flows'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='流程名称')
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='流程编码')

    # 适用范围
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('departments.id'), comment='适用部门')
    leave_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('leave_types.id'), comment='适用假期类型')
    min_days: Mapped[float] = mapped_column(Float, default=0, comment='最小请假天数(触发此流程)')
    max_days: Mapped[Optional[float]] = mapped_column(Float, comment='最大请假天数')

    # 审批级别配置 (JSON格式)
    # [{"level": 1, "approver_type": "direct_manager", "approver_id": null},
    #  {"level": 2, "approver_type": "specific", "approver_id": 123}]
    approval_levels: Mapped[Optional[str]] = mapped_column(JSON, comment='审批级别配置')

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    priority: Mapped[int] = mapped_column(Integer, default=0, comment='优先级(数值越大优先级越高)')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='流程描述')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    department = relationship('Department', backref='leave_approval_flows')
    leave_type = relationship('LeaveType', backref='approval_flows')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name if self.leave_type else None,
            'min_days': self.min_days,
            'max_days': self.max_days,
            'approval_levels': self.approval_levels,
            'is_active': self.is_active,
            'priority': self.priority,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Holiday(db.Model):
    """公共假日表"""
    __tablename__ = 'holidays'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='假日名称')
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False, comment='假日日期')
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment='年份')

    # 假日类型
    holiday_type: Mapped[str] = mapped_column(String(20), default='holiday', comment='类型(holiday=假日/workday=调休上班)')

    # 适用工厂
    factory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('factories.id'), comment='适用工厂(null=全部)')

    # 备注
    description: Mapped[Optional[str]] = mapped_column(Text, comment='假日说明')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    factory = relationship('Factory', backref='holidays')

    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('holiday_date', 'factory_id', name='uq_holiday_date_factory'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'holiday_date': self.holiday_date.strftime('%Y-%m-%d') if self.holiday_date else None,
            'year': self.year,
            'holiday_type': self.holiday_type,
            'factory_id': self.factory_id,
            'factory_name': self.factory.name if self.factory else None,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class LeaveBalanceAdjustment(db.Model):
    """假期额度调整记录表"""
    __tablename__ = 'leave_balance_adjustments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    leave_balance_id: Mapped[int] = mapped_column(Integer, ForeignKey('leave_balances.id'), nullable=False, comment='余额记录ID')
    adjustment_type: Mapped[str] = mapped_column(String(20), nullable=False, comment='调整类型(add/deduct/reset)')
    amount: Mapped[float] = mapped_column(Float, nullable=False, comment='调整数量')
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment='调整原因')

    # 操作人
    operator_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='操作人ID')

    # 调整前后
    balance_before: Mapped[float] = mapped_column(Float, nullable=False, comment='调整前余额')
    balance_after: Mapped[float] = mapped_column(Float, nullable=False, comment='调整后余额')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    leave_balance = relationship('LeaveBalance', backref='adjustments')

    def to_dict(self):
        return {
            'id': self.id,
            'leave_balance_id': self.leave_balance_id,
            'adjustment_type': self.adjustment_type,
            'amount': self.amount,
            'reason': self.reason,
            'operator_id': self.operator_id,
            'balance_before': self.balance_before,
            'balance_after': self.balance_after,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


def init_default_leave_types():
    """初始化默认假期类型"""
    default_types = [
        {
            'code': 'annual',
            'name': '年假',
            'category': 'statutory',
            'is_paid': True,
            'has_quota': True,
            'default_quota': 5,
            'can_carry_over': True,
            'max_carry_over': 5,
            'require_approval': True,
            'advance_days': 3,
            'description': '根据工龄享有的带薪年休假'
        },
        {
            'code': 'sick',
            'name': '病假',
            'category': 'sick',
            'is_paid': True,
            'pay_rate': 0.6,
            'has_quota': False,
            'require_approval': True,
            'require_attachment': True,
            'description': '因病需要休息的假期，需提供医院证明'
        },
        {
            'code': 'personal',
            'name': '事假',
            'category': 'personal',
            'is_paid': False,
            'has_quota': False,
            'require_approval': True,
            'description': '因个人事务需要请的假期，不带薪'
        },
        {
            'code': 'marriage',
            'name': '婚假',
            'category': 'statutory',
            'is_paid': True,
            'has_quota': True,
            'default_quota': 3,
            'require_approval': True,
            'require_attachment': True,
            'description': '员工结婚享有的带薪假期'
        },
        {
            'code': 'maternity',
            'name': '产假',
            'category': 'statutory',
            'is_paid': True,
            'has_quota': True,
            'default_quota': 98,
            'require_approval': True,
            'require_attachment': True,
            'applicable_gender': 'female',
            'description': '女员工生育享有的带薪假期'
        },
        {
            'code': 'paternity',
            'name': '陪产假',
            'category': 'statutory',
            'is_paid': True,
            'has_quota': True,
            'default_quota': 15,
            'require_approval': True,
            'require_attachment': True,
            'applicable_gender': 'male',
            'description': '男员工配偶生育享有的带薪假期'
        },
        {
            'code': 'bereavement',
            'name': '丧假',
            'category': 'statutory',
            'is_paid': True,
            'has_quota': True,
            'default_quota': 3,
            'require_approval': True,
            'description': '直系亲属去世享有的带薪假期'
        },
        {
            'code': 'compensation',
            'name': '调休假',
            'category': 'compensation',
            'is_paid': True,
            'has_quota': True,
            'default_quota': 0,
            'require_approval': True,
            'description': '加班后用于调休的假期'
        },
    ]

    for lt_data in default_types:
        existing = LeaveType.query.filter_by(code=lt_data['code']).first()
        if not existing:
            leave_type = LeaveType(**lt_data)
            db.session.add(leave_type)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"初始化假期类型失败: {e}")
