"""
考勤管理数据模型
包含: 考勤规则、排班、考勤记录、加班申请
"""
from app import db
from datetime import datetime, time, date
from sqlalchemy import String, Integer, Float, Date, DateTime, Time, Text, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum


class ShiftType(enum.Enum):
    """班次类型"""
    REGULAR = 'regular'          # 正常班
    MORNING = 'morning'          # 早班
    AFTERNOON = 'afternoon'      # 中班
    NIGHT = 'night'              # 晚班
    FLEXIBLE = 'flexible'        # 弹性工作制
    REST = 'rest'                # 休息日


class AttendanceStatus(enum.Enum):
    """考勤状态"""
    NORMAL = 'normal'            # 正常
    LATE = 'late'                # 迟到
    EARLY_LEAVE = 'early_leave'  # 早退
    ABSENT = 'absent'            # 缺勤
    LEAVE = 'leave'              # 请假
    OVERTIME = 'overtime'        # 加班
    BUSINESS_TRIP = 'business_trip'  # 出差
    REST = 'rest'                # 休息


class OvertimeType(enum.Enum):
    """加班类型"""
    WORKDAY = 'workday'          # 工作日加班
    WEEKEND = 'weekend'          # 周末加班
    HOLIDAY = 'holiday'          # 节假日加班


class OvertimeStatus(enum.Enum):
    """加班申请状态"""
    PENDING = 'pending'          # 待审批
    APPROVED = 'approved'        # 已批准
    REJECTED = 'rejected'        # 已拒绝
    CANCELLED = 'cancelled'      # 已取消


class AttendanceRule(db.Model):
    """考勤规则表"""
    __tablename__ = 'attendance_rules'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='规则名称')
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='规则编码')
    factory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('factories.id'), comment='适用工厂')
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('departments.id'), comment='适用部门')

    # 工作时间设置
    work_start_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 30), comment='上班时间')
    work_end_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(17, 30), comment='下班时间')
    break_start_time: Mapped[Optional[time]] = mapped_column(Time, comment='午休开始时间')
    break_end_time: Mapped[Optional[time]] = mapped_column(Time, comment='午休结束时间')

    # 弹性时间
    flexible_minutes: Mapped[int] = mapped_column(Integer, default=0, comment='弹性时间(分钟)')

    # 迟到早退规则
    late_threshold_minutes: Mapped[int] = mapped_column(Integer, default=0, comment='迟到阈值(分钟)')
    early_leave_threshold_minutes: Mapped[int] = mapped_column(Integer, default=0, comment='早退阈值(分钟)')
    absent_threshold_minutes: Mapped[int] = mapped_column(Integer, default=240, comment='缺勤阈值(分钟)')

    # 加班规则
    min_overtime_minutes: Mapped[int] = mapped_column(Integer, default=30, comment='最小加班时长(分钟)')
    require_overtime_approval: Mapped[bool] = mapped_column(Boolean, default=True, comment='加班是否需要审批')

    # 工作日配置 (JSON格式，如 {"monday": true, "tuesday": true, ...})
    work_days: Mapped[Optional[str]] = mapped_column(JSON, comment='工作日配置')

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否默认规则')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='规则描述')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')

    # 关系
    factory = relationship('Factory', backref='attendance_rules')
    department = relationship('Department', backref='attendance_rules')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'factory_id': self.factory_id,
            'factory_name': self.factory.name if self.factory else None,
            'department_id': self.department_id,
            'department_name': self.department.name if self.department else None,
            'work_start_time': self.work_start_time.strftime('%H:%M') if self.work_start_time else None,
            'work_end_time': self.work_end_time.strftime('%H:%M') if self.work_end_time else None,
            'break_start_time': self.break_start_time.strftime('%H:%M') if self.break_start_time else None,
            'break_end_time': self.break_end_time.strftime('%H:%M') if self.break_end_time else None,
            'flexible_minutes': self.flexible_minutes,
            'late_threshold_minutes': self.late_threshold_minutes,
            'early_leave_threshold_minutes': self.early_leave_threshold_minutes,
            'absent_threshold_minutes': self.absent_threshold_minutes,
            'min_overtime_minutes': self.min_overtime_minutes,
            'require_overtime_approval': self.require_overtime_approval,
            'work_days': self.work_days,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Shift(db.Model):
    """班次/排班表"""
    __tablename__ = 'shifts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='班次名称')
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='班次编码')
    shift_type: Mapped[str] = mapped_column(String(20), default='regular', comment='班次类型')

    # 时间设置
    start_time: Mapped[time] = mapped_column(Time, nullable=False, comment='开始时间')
    end_time: Mapped[time] = mapped_column(Time, nullable=False, comment='结束时间')
    cross_day: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否跨天')

    # 工时计算
    work_hours: Mapped[float] = mapped_column(Float, default=8.0, comment='标准工时(小时)')
    break_hours: Mapped[float] = mapped_column(Float, default=1.0, comment='休息时长(小时)')

    # 颜色标识(用于日历显示)
    color: Mapped[Optional[str]] = mapped_column(String(20), comment='显示颜色')

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    factory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('factories.id'), comment='适用工厂')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    factory = relationship('Factory', backref='shifts')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'shift_type': self.shift_type,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'cross_day': self.cross_day,
            'work_hours': self.work_hours,
            'break_hours': self.break_hours,
            'color': self.color,
            'is_active': self.is_active,
            'factory_id': self.factory_id,
            'factory_name': self.factory.name if self.factory else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Schedule(db.Model):
    """排班计划表 - 员工某天的排班安排"""
    __tablename__ = 'schedules'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    shift_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('shifts.id'), comment='班次ID')
    schedule_date: Mapped[date] = mapped_column(Date, nullable=False, comment='排班日期')

    # 排班状态
    is_rest: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否休息日')
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否节假日')

    # 自定义时间(覆盖班次默认时间)
    custom_start_time: Mapped[Optional[time]] = mapped_column(Time, comment='自定义上班时间')
    custom_end_time: Mapped[Optional[time]] = mapped_column(Time, comment='自定义下班时间')

    # 备注
    remark: Mapped[Optional[str]] = mapped_column(Text, comment='排班备注')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')

    # 关系
    employee = relationship('Employee', backref='schedules')
    shift = relationship('Shift', backref='schedules')

    # 唯一约束: 一个员工同一天只能有一个排班
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'schedule_date', name='uq_employee_schedule_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'shift_id': self.shift_id,
            'shift_name': self.shift.name if self.shift else None,
            'schedule_date': self.schedule_date.strftime('%Y-%m-%d') if self.schedule_date else None,
            'is_rest': self.is_rest,
            'is_holiday': self.is_holiday,
            'custom_start_time': self.custom_start_time.strftime('%H:%M') if self.custom_start_time else None,
            'custom_end_time': self.custom_end_time.strftime('%H:%M') if self.custom_end_time else None,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class AttendanceRecord(db.Model):
    """考勤记录表 - 每日打卡记录"""
    __tablename__ = 'attendance_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, comment='考勤日期')

    # 打卡时间
    check_in_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='上班打卡时间')
    check_out_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='下班打卡时间')

    # 打卡位置(支持GPS定位)
    check_in_location: Mapped[Optional[str]] = mapped_column(String(255), comment='上班打卡位置')
    check_out_location: Mapped[Optional[str]] = mapped_column(String(255), comment='下班打卡位置')
    check_in_ip: Mapped[Optional[str]] = mapped_column(String(50), comment='上班打卡IP')
    check_out_ip: Mapped[Optional[str]] = mapped_column(String(50), comment='下班打卡IP')

    # 打卡方式
    check_in_method: Mapped[Optional[str]] = mapped_column(String(20), comment='上班打卡方式(app/web/device/manual)')
    check_out_method: Mapped[Optional[str]] = mapped_column(String(20), comment='下班打卡方式')

    # 考勤状态
    status: Mapped[str] = mapped_column(String(20), default='normal', comment='考勤状态')
    is_late: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否迟到')
    late_minutes: Mapped[int] = mapped_column(Integer, default=0, comment='迟到分钟数')
    is_early_leave: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否早退')
    early_leave_minutes: Mapped[int] = mapped_column(Integer, default=0, comment='早退分钟数')
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否缺勤')

    # 工时统计
    work_hours: Mapped[float] = mapped_column(Float, default=0, comment='实际工时(小时)')
    overtime_hours: Mapped[float] = mapped_column(Float, default=0, comment='加班时长(小时)')

    # 关联排班
    schedule_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('schedules.id'), comment='排班ID')

    # 异常处理
    is_exception: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否异常')
    exception_reason: Mapped[Optional[str]] = mapped_column(Text, comment='异常原因')
    is_corrected: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否已补卡')
    correction_reason: Mapped[Optional[str]] = mapped_column(Text, comment='补卡原因')
    corrected_by: Mapped[Optional[int]] = mapped_column(Integer, comment='补卡操作人ID')
    corrected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='补卡时间')

    # 备注
    remark: Mapped[Optional[str]] = mapped_column(Text, comment='备注')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    employee = relationship('Employee', backref='attendance_records')
    schedule = relationship('Schedule', backref='attendance_records')

    # 唯一约束: 一个员工同一天只能有一条考勤记录
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'attendance_date', name='uq_employee_attendance_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'department': self.employee.department if self.employee else None,
            'attendance_date': self.attendance_date.strftime('%Y-%m-%d') if self.attendance_date else None,
            'check_in_time': self.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if self.check_in_time else None,
            'check_out_time': self.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if self.check_out_time else None,
            'check_in_location': self.check_in_location,
            'check_out_location': self.check_out_location,
            'check_in_method': self.check_in_method,
            'check_out_method': self.check_out_method,
            'status': self.status,
            'is_late': self.is_late,
            'late_minutes': self.late_minutes,
            'is_early_leave': self.is_early_leave,
            'early_leave_minutes': self.early_leave_minutes,
            'is_absent': self.is_absent,
            'work_hours': self.work_hours,
            'overtime_hours': self.overtime_hours,
            'schedule_id': self.schedule_id,
            'is_exception': self.is_exception,
            'exception_reason': self.exception_reason,
            'is_corrected': self.is_corrected,
            'correction_reason': self.correction_reason,
            'remark': self.remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class OvertimeRequest(db.Model):
    """加班申请表"""
    __tablename__ = 'overtime_requests'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')

    # 加班信息
    overtime_date: Mapped[date] = mapped_column(Date, nullable=False, comment='加班日期')
    overtime_type: Mapped[str] = mapped_column(String(20), default='workday', comment='加班类型')
    start_time: Mapped[time] = mapped_column(Time, nullable=False, comment='加班开始时间')
    end_time: Mapped[time] = mapped_column(Time, nullable=False, comment='加班结束时间')
    planned_hours: Mapped[float] = mapped_column(Float, nullable=False, comment='计划加班时长(小时)')
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, comment='实际加班时长(小时)')

    # 申请原因
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment='加班原因')
    work_content: Mapped[Optional[str]] = mapped_column(Text, comment='工作内容')

    # 审批信息
    status: Mapped[str] = mapped_column(String(20), default='pending', comment='审批状态')
    approver_id: Mapped[Optional[int]] = mapped_column(Integer, comment='审批人ID')
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='审批时间')
    approval_remark: Mapped[Optional[str]] = mapped_column(Text, comment='审批备注')

    # 多级审批支持
    approval_flow: Mapped[Optional[str]] = mapped_column(JSON, comment='审批流程记录')
    current_approver_level: Mapped[int] = mapped_column(Integer, default=1, comment='当前审批级别')

    # 补偿方式
    compensation_type: Mapped[Optional[str]] = mapped_column(String(20), comment='补偿方式(pay/leave)')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    employee = relationship('Employee', backref='overtime_requests')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'department': self.employee.department if self.employee else None,
            'overtime_date': self.overtime_date.strftime('%Y-%m-%d') if self.overtime_date else None,
            'overtime_type': self.overtime_type,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'planned_hours': self.planned_hours,
            'actual_hours': self.actual_hours,
            'reason': self.reason,
            'work_content': self.work_content,
            'status': self.status,
            'approver_id': self.approver_id,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'approval_remark': self.approval_remark,
            'compensation_type': self.compensation_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class AttendanceCorrection(db.Model):
    """补卡申请表"""
    __tablename__ = 'attendance_corrections'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    attendance_record_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('attendance_records.id'), comment='关联考勤记录')

    # 补卡信息
    correction_date: Mapped[date] = mapped_column(Date, nullable=False, comment='补卡日期')
    correction_type: Mapped[str] = mapped_column(String(20), nullable=False, comment='补卡类型(check_in/check_out)')
    correction_time: Mapped[time] = mapped_column(Time, nullable=False, comment='补卡时间')

    # 申请原因
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment='补卡原因')
    attachment: Mapped[Optional[str]] = mapped_column(String(255), comment='附件(证明材料)')

    # 审批信息
    status: Mapped[str] = mapped_column(String(20), default='pending', comment='审批状态')
    approver_id: Mapped[Optional[int]] = mapped_column(Integer, comment='审批人ID')
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='审批时间')
    approval_remark: Mapped[Optional[str]] = mapped_column(Text, comment='审批备注')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    employee = relationship('Employee', backref='attendance_corrections')
    attendance_record = relationship('AttendanceRecord', backref='corrections')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'attendance_record_id': self.attendance_record_id,
            'correction_date': self.correction_date.strftime('%Y-%m-%d') if self.correction_date else None,
            'correction_type': self.correction_type,
            'correction_time': self.correction_time.strftime('%H:%M') if self.correction_time else None,
            'reason': self.reason,
            'attachment': self.attachment,
            'status': self.status,
            'approver_id': self.approver_id,
            'approved_at': self.approved_at.strftime('%Y-%m-%d %H:%M:%S') if self.approved_at else None,
            'approval_remark': self.approval_remark,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class MonthlyAttendanceSummary(db.Model):
    """月度考勤汇总表"""
    __tablename__ = 'monthly_attendance_summaries'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment='年份')
    month: Mapped[int] = mapped_column(Integer, nullable=False, comment='月份')

    # 统计数据
    work_days: Mapped[int] = mapped_column(Integer, default=0, comment='应出勤天数')
    actual_work_days: Mapped[float] = mapped_column(Float, default=0, comment='实际出勤天数')
    late_count: Mapped[int] = mapped_column(Integer, default=0, comment='迟到次数')
    late_minutes_total: Mapped[int] = mapped_column(Integer, default=0, comment='迟到总分钟数')
    early_leave_count: Mapped[int] = mapped_column(Integer, default=0, comment='早退次数')
    early_leave_minutes_total: Mapped[int] = mapped_column(Integer, default=0, comment='早退总分钟数')
    absent_days: Mapped[float] = mapped_column(Float, default=0, comment='缺勤天数')
    leave_days: Mapped[float] = mapped_column(Float, default=0, comment='请假天数')

    # 工时统计
    standard_hours: Mapped[float] = mapped_column(Float, default=0, comment='标准工时')
    actual_hours: Mapped[float] = mapped_column(Float, default=0, comment='实际工时')
    overtime_hours: Mapped[float] = mapped_column(Float, default=0, comment='加班工时')
    workday_overtime_hours: Mapped[float] = mapped_column(Float, default=0, comment='工作日加班')
    weekend_overtime_hours: Mapped[float] = mapped_column(Float, default=0, comment='周末加班')
    holiday_overtime_hours: Mapped[float] = mapped_column(Float, default=0, comment='节假日加班')

    # 状态
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否锁定(用于薪资计算)')
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='锁定时间')
    locked_by: Mapped[Optional[int]] = mapped_column(Integer, comment='锁定人ID')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    employee = relationship('Employee', backref='monthly_summaries')

    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'year', 'month', name='uq_employee_year_month'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'department': self.employee.department if self.employee else None,
            'year': self.year,
            'month': self.month,
            'work_days': self.work_days,
            'actual_work_days': self.actual_work_days,
            'late_count': self.late_count,
            'late_minutes_total': self.late_minutes_total,
            'early_leave_count': self.early_leave_count,
            'early_leave_minutes_total': self.early_leave_minutes_total,
            'absent_days': self.absent_days,
            'leave_days': self.leave_days,
            'standard_hours': self.standard_hours,
            'actual_hours': self.actual_hours,
            'overtime_hours': self.overtime_hours,
            'workday_overtime_hours': self.workday_overtime_hours,
            'weekend_overtime_hours': self.weekend_overtime_hours,
            'holiday_overtime_hours': self.holiday_overtime_hours,
            'is_locked': self.is_locked,
            'locked_at': self.locked_at.strftime('%Y-%m-%d %H:%M:%S') if self.locked_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
