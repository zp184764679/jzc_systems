# MES 生产排程模型
# Production Scheduling Models for MES

from database import db
from datetime import datetime, date, timedelta
import enum


class ScheduleStatus(enum.Enum):
    """排程状态"""
    DRAFT = "draft"           # 草稿
    CONFIRMED = "confirmed"   # 已确认
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"   # 已完成
    CANCELLED = "cancelled"   # 已取消


class TaskStatus(enum.Enum):
    """任务状态"""
    PLANNED = "planned"       # 已计划
    SCHEDULED = "scheduled"   # 已排程
    IN_PROGRESS = "in_progress"  # 执行中
    COMPLETED = "completed"   # 已完成
    DELAYED = "delayed"       # 延迟
    CANCELLED = "cancelled"   # 已取消


SCHEDULE_STATUS_LABELS = {
    "draft": "草稿",
    "confirmed": "已确认",
    "in_progress": "执行中",
    "completed": "已完成",
    "cancelled": "已取消",
}

TASK_STATUS_LABELS = {
    "planned": "已计划",
    "scheduled": "已排程",
    "in_progress": "执行中",
    "completed": "已完成",
    "delayed": "延迟",
    "cancelled": "已取消",
}


def generate_schedule_code():
    """生成排程编号: SCH + 年月日 + 4位序号"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"SCH{today}"

    last = ProductionSchedule.query.filter(
        ProductionSchedule.schedule_code.like(f"{prefix}%")
    ).order_by(ProductionSchedule.schedule_code.desc()).first()

    if last:
        try:
            seq = int(last.schedule_code[-4:]) + 1
        except:
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


class ProductionSchedule(db.Model):
    """
    生产排程计划 - 主表
    每个排程计划包含一段时间内的所有生产任务安排
    """
    __tablename__ = 'mes_production_schedules'

    id = db.Column(db.Integer, primary_key=True)
    schedule_code = db.Column(db.String(50), unique=True, nullable=False, comment='排程编号')
    name = db.Column(db.String(200), nullable=False, comment='排程名称')
    description = db.Column(db.Text, comment='排程描述')

    # 排程周期
    start_date = db.Column(db.Date, nullable=False, comment='开始日期')
    end_date = db.Column(db.Date, nullable=False, comment='结束日期')

    # 排程状态
    status = db.Column(db.String(20), default='draft', comment='状态')
    version = db.Column(db.Integer, default=1, comment='版本号')

    # 排程参数
    work_hours_per_day = db.Column(db.Float, default=8, comment='每日工作小时')
    shifts_per_day = db.Column(db.Integer, default=1, comment='每日班次')
    consider_holidays = db.Column(db.Boolean, default=True, comment='考虑节假日')

    # 统计
    total_tasks = db.Column(db.Integer, default=0, comment='总任务数')
    completed_tasks = db.Column(db.Integer, default=0, comment='完成任务数')
    total_hours = db.Column(db.Float, default=0, comment='总计划工时')

    # 时间戳
    confirmed_at = db.Column(db.DateTime, comment='确认时间')
    confirmed_by = db.Column(db.String(50), comment='确认人')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(50), comment='创建人')

    # 关系
    tasks = db.relationship('ScheduleTask', backref='schedule', lazy='dynamic',
                           cascade='all, delete-orphan')

    @property
    def status_label(self):
        return SCHEDULE_STATUS_LABELS.get(self.status, self.status)

    @property
    def progress(self):
        if self.total_tasks == 0:
            return 0
        return round(self.completed_tasks / self.total_tasks * 100, 2)

    @property
    def days_count(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    def to_dict(self, include_tasks=False):
        data = {
            'id': self.id,
            'schedule_code': self.schedule_code,
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'status': self.status,
            'status_label': self.status_label,
            'version': self.version,
            'work_hours_per_day': self.work_hours_per_day,
            'shifts_per_day': self.shifts_per_day,
            'consider_holidays': self.consider_holidays,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'total_hours': self.total_hours,
            'progress': self.progress,
            'days_count': self.days_count,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by': self.confirmed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
        }
        if include_tasks:
            data['tasks'] = [t.to_dict() for t in self.tasks.order_by(ScheduleTask.planned_start).all()]
        return data


class ScheduleTask(db.Model):
    """
    排程任务 - 具体的生产任务安排
    每个任务对应一个工单的某个工序在特定设备上的执行
    """
    __tablename__ = 'mes_schedule_tasks'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('mes_production_schedules.id'), nullable=False)

    # 关联工单
    work_order_id = db.Column(db.Integer, nullable=False, comment='工单ID')
    work_order_no = db.Column(db.String(50), comment='工单编号')

    # 关联工序
    work_order_process_id = db.Column(db.Integer, comment='工单工序ID')
    process_id = db.Column(db.Integer, comment='工序定义ID')
    process_code = db.Column(db.String(50), comment='工序编码')
    process_name = db.Column(db.String(200), comment='工序名称')
    step_no = db.Column(db.Integer, default=1, comment='工序步骤号')

    # 产品信息
    product_code = db.Column(db.String(100), comment='产品编码')
    product_name = db.Column(db.String(200), comment='产品名称')

    # 设备安排
    machine_id = db.Column(db.Integer, comment='设备ID（EAM）')
    machine_code = db.Column(db.String(50), comment='设备编码')
    machine_name = db.Column(db.String(200), comment='设备名称')

    # 人员安排
    operator_id = db.Column(db.Integer, comment='操作员ID')
    operator_name = db.Column(db.String(100), comment='操作员姓名')

    # 计划时间
    planned_start = db.Column(db.DateTime, nullable=False, comment='计划开始时间')
    planned_end = db.Column(db.DateTime, nullable=False, comment='计划结束时间')
    planned_hours = db.Column(db.Float, default=0, comment='计划工时')

    # 实际时间
    actual_start = db.Column(db.DateTime, comment='实际开始时间')
    actual_end = db.Column(db.DateTime, comment='实际结束时间')
    actual_hours = db.Column(db.Float, comment='实际工时')

    # 数量
    planned_quantity = db.Column(db.Integer, default=0, comment='计划数量')
    completed_quantity = db.Column(db.Integer, default=0, comment='完成数量')

    # 状态
    status = db.Column(db.String(20), default='planned', comment='状态')
    priority = db.Column(db.Integer, default=3, comment='优先级 1-5')

    # 约束
    is_locked = db.Column(db.Boolean, default=False, comment='是否锁定（不允许自动调整）')
    dependencies = db.Column(db.JSON, comment='依赖任务ID列表')

    # 备注
    remark = db.Column(db.Text, comment='备注')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def status_label(self):
        return TASK_STATUS_LABELS.get(self.status, self.status)

    @property
    def duration_hours(self):
        """计划时长（小时）"""
        if self.planned_start and self.planned_end:
            delta = self.planned_end - self.planned_start
            return round(delta.total_seconds() / 3600, 2)
        return 0

    @property
    def is_delayed(self):
        """是否延迟"""
        if self.status in ['completed', 'cancelled']:
            return False
        if self.planned_end and datetime.utcnow() > self.planned_end:
            return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'work_order_id': self.work_order_id,
            'work_order_no': self.work_order_no,
            'work_order_process_id': self.work_order_process_id,
            'process_id': self.process_id,
            'process_code': self.process_code,
            'process_name': self.process_name,
            'step_no': self.step_no,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'machine_id': self.machine_id,
            'machine_code': self.machine_code,
            'machine_name': self.machine_name,
            'operator_id': self.operator_id,
            'operator_name': self.operator_name,
            'planned_start': self.planned_start.isoformat() if self.planned_start else None,
            'planned_end': self.planned_end.isoformat() if self.planned_end else None,
            'planned_hours': self.planned_hours,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'actual_hours': self.actual_hours,
            'planned_quantity': self.planned_quantity,
            'completed_quantity': self.completed_quantity,
            'status': self.status,
            'status_label': self.status_label,
            'priority': self.priority,
            'is_locked': self.is_locked,
            'is_delayed': self.is_delayed,
            'dependencies': self.dependencies,
            'duration_hours': self.duration_hours,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def to_gantt_item(self):
        """转换为甘特图数据格式"""
        return {
            'id': self.id,
            'task': f"{self.work_order_no} - {self.process_name}",
            'start': self.planned_start.isoformat() if self.planned_start else None,
            'end': self.planned_end.isoformat() if self.planned_end else None,
            'machine': self.machine_name,
            'machine_id': self.machine_id,
            'work_order_id': self.work_order_id,
            'work_order_no': self.work_order_no,
            'process_name': self.process_name,
            'product_name': self.product_name,
            'status': self.status,
            'priority': self.priority,
            'progress': round(self.completed_quantity / self.planned_quantity * 100, 2) if self.planned_quantity > 0 else 0,
        }


class MachineCapacity(db.Model):
    """
    设备产能配置 - 记录设备的可用时间和产能
    """
    __tablename__ = 'mes_machine_capacities'

    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, nullable=False, comment='设备ID（EAM）')
    machine_code = db.Column(db.String(50), comment='设备编码')
    machine_name = db.Column(db.String(200), comment='设备名称')

    # 日期
    date = db.Column(db.Date, nullable=False, comment='日期')

    # 可用时间
    available_hours = db.Column(db.Float, default=8, comment='可用小时数')
    scheduled_hours = db.Column(db.Float, default=0, comment='已排程小时数')

    # 班次设置
    shift_start = db.Column(db.Time, comment='班次开始时间')
    shift_end = db.Column(db.Time, comment='班次结束时间')

    # 状态
    is_available = db.Column(db.Boolean, default=True, comment='是否可用')
    unavailable_reason = db.Column(db.String(200), comment='不可用原因')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('machine_id', 'date', name='uq_machine_date'),
    )

    @property
    def remaining_hours(self):
        return max(0, self.available_hours - self.scheduled_hours)

    @property
    def utilization(self):
        if self.available_hours == 0:
            return 0
        return round(self.scheduled_hours / self.available_hours * 100, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'machine_code': self.machine_code,
            'machine_name': self.machine_name,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'available_hours': self.available_hours,
            'scheduled_hours': self.scheduled_hours,
            'remaining_hours': self.remaining_hours,
            'utilization': self.utilization,
            'shift_start': self.shift_start.strftime('%H:%M') if self.shift_start else None,
            'shift_end': self.shift_end.strftime('%H:%M') if self.shift_end else None,
            'is_available': self.is_available,
            'unavailable_reason': self.unavailable_reason,
        }
