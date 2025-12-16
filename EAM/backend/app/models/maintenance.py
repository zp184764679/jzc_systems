# -*- coding: utf-8 -*-
"""
EAM 维护保养模型
包含：保养标准、保养计划、保养工单、保养记录
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import enum
from .. import db


class MaintenanceType(enum.Enum):
    """保养类型"""
    PREVENTIVE = "preventive"      # 预防性保养
    CORRECTIVE = "corrective"      # 纠正性维修
    PREDICTIVE = "predictive"      # 预测性维护
    INSPECTION = "inspection"      # 点检
    OVERHAUL = "overhaul"          # 大修


class MaintenanceCycle(enum.Enum):
    """保养周期"""
    DAILY = "daily"                # 每日
    WEEKLY = "weekly"              # 每周
    BIWEEKLY = "biweekly"          # 每两周
    MONTHLY = "monthly"            # 每月
    QUARTERLY = "quarterly"        # 每季度
    SEMIANNUAL = "semiannual"      # 每半年
    ANNUAL = "annual"              # 每年
    CUSTOM = "custom"              # 自定义天数


class OrderStatus(enum.Enum):
    """工单状态"""
    PENDING = "pending"            # 待执行
    IN_PROGRESS = "in_progress"    # 执行中
    COMPLETED = "completed"        # 已完成
    CANCELLED = "cancelled"        # 已取消
    OVERDUE = "overdue"            # 已逾期


class MaintenanceStandard(db.Model):
    """
    保养标准
    定义设备的保养项目、周期、方法等标准
    """
    __tablename__ = "maintenance_standards"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    code = db.Column(db.String(64), unique=True, nullable=False, comment="标准编码")
    name = db.Column(db.String(128), nullable=False, comment="标准名称")
    description = db.Column(db.Text, comment="标准描述")

    # 适用设备
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), comment="适用设备ID(空=通用)")
    machine_model = db.Column(db.String(128), comment="适用设备型号(模糊匹配)")
    equipment_group = db.Column(db.String(64), comment="适用设备组")

    # 保养类型和周期
    maintenance_type = db.Column(db.String(32), default="preventive", comment="保养类型")
    cycle = db.Column(db.String(32), default="monthly", comment="保养周期")
    cycle_days = db.Column(db.Integer, comment="自定义周期天数")
    estimated_hours = db.Column(db.Float, default=1.0, comment="预计工时(小时)")

    # 保养内容 (JSON格式)
    check_items = db.Column(db.JSON, comment="检查项目列表")
    # 示例: [{"item": "检查润滑油", "method": "目视", "standard": "油位正常"}, ...]

    tools_required = db.Column(db.JSON, comment="所需工具")
    spare_parts = db.Column(db.JSON, comment="所需备件")
    safety_notes = db.Column(db.Text, comment="安全注意事项")

    # 状态
    is_active = db.Column(db.Boolean, default=True, comment="是否启用")
    sort_order = db.Column(db.Integer, default=0, comment="排序")

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, comment="创建人ID")
    created_by_name = db.Column(db.String(50), comment="创建人姓名")

    # 关联
    machine = db.relationship("Machine", backref="maintenance_standards", lazy="joined")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "machine_id": self.machine_id,
            "machine_name": self.machine.name if self.machine else None,
            "machine_model": self.machine_model,
            "equipment_group": self.equipment_group,
            "maintenance_type": self.maintenance_type,
            "cycle": self.cycle,
            "cycle_days": self.cycle_days,
            "estimated_hours": self.estimated_hours,
            "check_items": self.check_items or [],
            "tools_required": self.tools_required or [],
            "spare_parts": self.spare_parts or [],
            "safety_notes": self.safety_notes,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
        }


class MaintenancePlan(db.Model):
    """
    保养计划
    为设备生成周期性保养计划
    """
    __tablename__ = "maintenance_plans"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    code = db.Column(db.String(64), unique=True, nullable=False, comment="计划编码")
    name = db.Column(db.String(128), nullable=False, comment="计划名称")
    description = db.Column(db.Text, comment="计划描述")

    # 关联设备和标准
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False, comment="设备ID")
    standard_id = db.Column(db.Integer, db.ForeignKey("maintenance_standards.id"), comment="保养标准ID")

    # 计划周期
    cycle = db.Column(db.String(32), default="monthly", comment="执行周期")
    cycle_days = db.Column(db.Integer, comment="自定义周期天数")

    # 计划时间
    start_date = db.Column(db.Date, nullable=False, comment="开始日期")
    end_date = db.Column(db.Date, comment="结束日期(空=永久)")
    next_due_date = db.Column(db.Date, comment="下次执行日期")
    last_executed_date = db.Column(db.Date, comment="上次执行日期")

    # 提前提醒
    advance_days = db.Column(db.Integer, default=3, comment="提前提醒天数")

    # 负责人
    responsible_id = db.Column(db.Integer, comment="负责人ID")
    responsible_name = db.Column(db.String(50), comment="负责人姓名")

    # 状态
    is_active = db.Column(db.Boolean, default=True, comment="是否启用")

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, comment="创建人ID")
    created_by_name = db.Column(db.String(50), comment="创建人姓名")

    # 关联
    machine = db.relationship("Machine", backref="maintenance_plans", lazy="joined")
    standard = db.relationship("MaintenanceStandard", backref="plans", lazy="joined")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "machine_id": self.machine_id,
            "machine_code": self.machine.machine_code if self.machine else None,
            "machine_name": self.machine.name if self.machine else None,
            "standard_id": self.standard_id,
            "standard_name": self.standard.name if self.standard else None,
            "cycle": self.cycle,
            "cycle_days": self.cycle_days,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "last_executed_date": self.last_executed_date.isoformat() if self.last_executed_date else None,
            "advance_days": self.advance_days,
            "responsible_id": self.responsible_id,
            "responsible_name": self.responsible_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
        }

    def calculate_next_due_date(self) -> Optional[date]:
        """计算下次执行日期"""
        from datetime import timedelta

        base_date = self.last_executed_date or self.start_date
        if not base_date:
            return None

        cycle_map = {
            "daily": 1,
            "weekly": 7,
            "biweekly": 14,
            "monthly": 30,
            "quarterly": 90,
            "semiannual": 180,
            "annual": 365,
        }

        days = self.cycle_days if self.cycle == "custom" else cycle_map.get(self.cycle, 30)
        return base_date + timedelta(days=days)


class MaintenanceOrder(db.Model):
    """
    保养工单
    从保养计划生成或手动创建的具体工单
    """
    __tablename__ = "maintenance_orders"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    order_no = db.Column(db.String(64), unique=True, nullable=False, comment="工单编号")
    title = db.Column(db.String(200), nullable=False, comment="工单标题")
    description = db.Column(db.Text, comment="工单描述")

    # 关联
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False, comment="设备ID")
    plan_id = db.Column(db.Integer, db.ForeignKey("maintenance_plans.id"), comment="来源计划ID")
    standard_id = db.Column(db.Integer, db.ForeignKey("maintenance_standards.id"), comment="保养标准ID")

    # 类型
    maintenance_type = db.Column(db.String(32), default="preventive", comment="保养类型")
    source = db.Column(db.String(32), default="manual", comment="来源:manual/plan/fault")

    # 时间安排
    planned_date = db.Column(db.Date, nullable=False, comment="计划执行日期")
    due_date = db.Column(db.Date, comment="截止日期")
    started_at = db.Column(db.DateTime, comment="实际开始时间")
    completed_at = db.Column(db.DateTime, comment="实际完成时间")

    # 预计工时
    estimated_hours = db.Column(db.Float, comment="预计工时(小时)")
    actual_hours = db.Column(db.Float, comment="实际工时(小时)")

    # 执行人
    assigned_to_id = db.Column(db.Integer, comment="指派人ID")
    assigned_to_name = db.Column(db.String(50), comment="指派人姓名")
    executor_id = db.Column(db.Integer, comment="执行人ID")
    executor_name = db.Column(db.String(50), comment="执行人姓名")

    # 状态
    status = db.Column(db.String(32), default="pending", comment="状态")
    priority = db.Column(db.String(16), default="normal", comment="优先级:low/normal/high/urgent")

    # 检查项目结果 (JSON格式)
    check_results = db.Column(db.JSON, comment="检查结果")
    # 示例: [{"item": "检查润滑油", "result": "正常", "remark": ""}]

    # 使用备件
    spare_parts_used = db.Column(db.JSON, comment="使用的备件")
    cost = db.Column(db.Float, default=0, comment="维护费用")

    # 备注
    remark = db.Column(db.Text, comment="备注")

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, comment="创建人ID")
    created_by_name = db.Column(db.String(50), comment="创建人姓名")

    # 关联
    machine = db.relationship("Machine", backref="maintenance_orders", lazy="joined")
    plan = db.relationship("MaintenancePlan", backref="orders", lazy="joined")
    standard = db.relationship("MaintenanceStandard", backref="orders", lazy="joined")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_no": self.order_no,
            "title": self.title,
            "description": self.description,
            "machine_id": self.machine_id,
            "machine_code": self.machine.machine_code if self.machine else None,
            "machine_name": self.machine.name if self.machine else None,
            "plan_id": self.plan_id,
            "plan_name": self.plan.name if self.plan else None,
            "standard_id": self.standard_id,
            "standard_name": self.standard.name if self.standard else None,
            "maintenance_type": self.maintenance_type,
            "source": self.source,
            "planned_date": self.planned_date.isoformat() if self.planned_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "assigned_to_id": self.assigned_to_id,
            "assigned_to_name": self.assigned_to_name,
            "executor_id": self.executor_id,
            "executor_name": self.executor_name,
            "status": self.status,
            "priority": self.priority,
            "check_results": self.check_results or [],
            "spare_parts_used": self.spare_parts_used or [],
            "cost": self.cost,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "created_by_name": self.created_by_name,
        }


class FaultReport(db.Model):
    """
    故障报修
    设备故障登记和处理
    """
    __tablename__ = "fault_reports"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    report_no = db.Column(db.String(64), unique=True, nullable=False, comment="报修单号")
    title = db.Column(db.String(200), nullable=False, comment="故障标题")
    description = db.Column(db.Text, nullable=False, comment="故障描述")

    # 关联设备
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False, comment="设备ID")

    # 故障信息
    fault_type = db.Column(db.String(32), comment="故障类型:mechanical/electrical/software/other")
    severity = db.Column(db.String(16), default="normal", comment="严重程度:minor/normal/major/critical")
    fault_time = db.Column(db.DateTime, comment="故障发生时间")

    # 报修人
    reporter_id = db.Column(db.Integer, comment="报修人ID")
    reporter_name = db.Column(db.String(50), comment="报修人姓名")
    reporter_phone = db.Column(db.String(20), comment="报修人电话")

    # 处理人
    handler_id = db.Column(db.Integer, comment="处理人ID")
    handler_name = db.Column(db.String(50), comment="处理人姓名")

    # 状态
    status = db.Column(db.String(32), default="reported", comment="状态:reported/assigned/in_progress/completed/closed")

    # 处理信息
    diagnosis = db.Column(db.Text, comment="故障诊断")
    solution = db.Column(db.Text, comment="解决方案")
    spare_parts_used = db.Column(db.JSON, comment="使用的备件")
    cost = db.Column(db.Float, default=0, comment="维修费用")

    # 时间
    assigned_at = db.Column(db.DateTime, comment="指派时间")
    started_at = db.Column(db.DateTime, comment="开始处理时间")
    completed_at = db.Column(db.DateTime, comment="完成时间")
    closed_at = db.Column(db.DateTime, comment="关闭时间")
    downtime_hours = db.Column(db.Float, comment="停机时长(小时)")

    # 关联工单
    order_id = db.Column(db.Integer, db.ForeignKey("maintenance_orders.id"), comment="关联维修工单ID")

    # 图片附件
    images = db.Column(db.JSON, comment="故障图片")

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    machine = db.relationship("Machine", backref="fault_reports", lazy="joined")
    order = db.relationship("MaintenanceOrder", backref="fault_report", lazy="joined")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "report_no": self.report_no,
            "title": self.title,
            "description": self.description,
            "machine_id": self.machine_id,
            "machine_code": self.machine.machine_code if self.machine else None,
            "machine_name": self.machine.name if self.machine else None,
            "fault_type": self.fault_type,
            "severity": self.severity,
            "fault_time": self.fault_time.isoformat() if self.fault_time else None,
            "reporter_id": self.reporter_id,
            "reporter_name": self.reporter_name,
            "reporter_phone": self.reporter_phone,
            "handler_id": self.handler_id,
            "handler_name": self.handler_name,
            "status": self.status,
            "diagnosis": self.diagnosis,
            "solution": self.solution,
            "spare_parts_used": self.spare_parts_used or [],
            "cost": self.cost,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "downtime_hours": self.downtime_hours,
            "order_id": self.order_id,
            "images": self.images or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class InspectionRecord(db.Model):
    """
    点检记录
    日常设备点检
    """
    __tablename__ = "inspection_records"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)

    # 基本信息
    record_no = db.Column(db.String(64), unique=True, nullable=False, comment="点检单号")

    # 关联设备
    machine_id = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False, comment="设备ID")
    standard_id = db.Column(db.Integer, db.ForeignKey("maintenance_standards.id"), comment="点检标准ID")

    # 点检信息
    inspection_date = db.Column(db.Date, nullable=False, comment="点检日期")
    shift = db.Column(db.String(16), comment="班次:morning/afternoon/night")

    # 点检人
    inspector_id = db.Column(db.Integer, comment="点检人ID")
    inspector_name = db.Column(db.String(50), comment="点检人姓名")

    # 点检结果
    result = db.Column(db.String(16), default="normal", comment="结果:normal/abnormal")
    check_items = db.Column(db.JSON, comment="点检项目结果")
    # 示例: [{"item": "外观", "status": "normal", "remark": ""}]

    abnormal_items = db.Column(db.JSON, comment="异常项")
    remark = db.Column(db.Text, comment="备注")

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    machine = db.relationship("Machine", backref="inspection_records", lazy="joined")
    standard = db.relationship("MaintenanceStandard", backref="inspections", lazy="joined")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "record_no": self.record_no,
            "machine_id": self.machine_id,
            "machine_code": self.machine.machine_code if self.machine else None,
            "machine_name": self.machine.name if self.machine else None,
            "standard_id": self.standard_id,
            "standard_name": self.standard.name if self.standard else None,
            "inspection_date": self.inspection_date.isoformat() if self.inspection_date else None,
            "shift": self.shift,
            "inspector_id": self.inspector_id,
            "inspector_name": self.inspector_name,
            "result": self.result,
            "check_items": self.check_items or [],
            "abnormal_items": self.abnormal_items or [],
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# 辅助函数
def generate_order_no(prefix: str = "MO") -> str:
    """生成工单编号"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = str(random.randint(100, 999))
    return f"{prefix}{timestamp}{random_suffix}"


def generate_report_no() -> str:
    """生成报修单号"""
    return generate_order_no("FR")


def generate_inspection_no() -> str:
    """生成点检单号"""
    return generate_order_no("IR")


# 周期映射
CYCLE_DAYS_MAP = {
    "daily": 1,
    "weekly": 7,
    "biweekly": 14,
    "monthly": 30,
    "quarterly": 90,
    "semiannual": 180,
    "annual": 365,
}


# 状态流转
ORDER_STATUS_TRANSITIONS = {
    "pending": ["in_progress", "cancelled"],
    "in_progress": ["completed", "pending"],
    "completed": [],
    "cancelled": ["pending"],
    "overdue": ["in_progress", "cancelled"],
}

FAULT_STATUS_TRANSITIONS = {
    "reported": ["assigned", "closed"],
    "assigned": ["in_progress", "reported"],
    "in_progress": ["completed", "assigned"],
    "completed": ["closed"],
    "closed": [],
}
