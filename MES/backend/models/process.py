# MES 工序管理模型
# Process Management Models for MES

from database import db
from datetime import datetime
import enum


class ProcessType(enum.Enum):
    """工序类型"""
    MACHINING = "machining"         # 机加工
    ASSEMBLY = "assembly"           # 装配
    WELDING = "welding"             # 焊接
    PAINTING = "painting"           # 喷涂
    TESTING = "testing"             # 测试
    INSPECTION = "inspection"       # 检验
    PACKAGING = "packaging"         # 包装
    HEAT_TREATMENT = "heat_treatment"  # 热处理
    SURFACE_TREATMENT = "surface_treatment"  # 表面处理
    OTHER = "other"                 # 其他


class ProcessStatus(enum.Enum):
    """工序执行状态"""
    PENDING = "pending"             # 待开始
    WAITING = "waiting"             # 等待中（等待物料/设备）
    IN_PROGRESS = "in_progress"     # 进行中
    PAUSED = "paused"               # 暂停
    COMPLETED = "completed"         # 已完成
    SKIPPED = "skipped"             # 已跳过


# 工序状态流转规则
PROCESS_STATUS_TRANSITIONS = {
    "pending": ["waiting", "in_progress", "skipped"],
    "waiting": ["in_progress", "skipped"],
    "in_progress": ["paused", "completed"],
    "paused": ["in_progress", "skipped"],
    "completed": [],
    "skipped": [],
}


def generate_route_code():
    """生成工艺路线编号: RT + 年月日 + 4位序号"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"RT{today}"

    last_route = ProcessRoute.query.filter(
        ProcessRoute.route_code.like(f"{prefix}%")
    ).order_by(ProcessRoute.route_code.desc()).first()

    if last_route:
        try:
            seq = int(last_route.route_code[-4:]) + 1
        except:
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


class ProcessDefinition(db.Model):
    """
    工序定义 - 定义标准工序模板
    每个工序定义了生产过程中的一个标准操作步骤
    """
    __tablename__ = 'mes_process_definitions'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, comment='工序编码')
    name = db.Column(db.String(200), nullable=False, comment='工序名称')
    process_type = db.Column(db.String(32), default='other', comment='工序类型')

    # 工序详情
    description = db.Column(db.Text, comment='工序描述')
    work_instructions = db.Column(db.Text, comment='作业指导书')

    # 工作中心/设备
    work_center_id = db.Column(db.Integer, db.ForeignKey('mes_work_centers.id'), comment='默认工作中心')
    default_machine_id = db.Column(db.Integer, comment='默认设备ID（EAM）')
    default_machine_name = db.Column(db.String(200), comment='默认设备名称')

    # 标准工时
    setup_time = db.Column(db.Float, default=0, comment='准备时间（分钟）')
    standard_time = db.Column(db.Float, default=0, comment='标准工时（分钟/件）')
    move_time = db.Column(db.Float, default=0, comment='移动时间（分钟）')

    # 产能参数
    min_batch_size = db.Column(db.Integer, default=1, comment='最小批量')
    max_batch_size = db.Column(db.Integer, comment='最大批量')
    daily_capacity = db.Column(db.Integer, comment='日产能')

    # 人员要求
    required_skill_level = db.Column(db.String(50), comment='所需技能等级')
    min_operators = db.Column(db.Integer, default=1, comment='最少操作人数')
    max_operators = db.Column(db.Integer, comment='最多操作人数')

    # 质量要求
    inspection_required = db.Column(db.Boolean, default=False, comment='是否需要检验')
    inspection_type = db.Column(db.String(50), comment='检验类型')
    quality_standards = db.Column(db.JSON, comment='质量标准（JSON）')

    # 物料/工具
    required_tools = db.Column(db.JSON, comment='所需工具（JSON列表）')
    required_materials = db.Column(db.JSON, comment='所需物料（JSON列表）')

    # 安全/注意事项
    safety_notes = db.Column(db.Text, comment='安全注意事项')

    # 状态
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    version = db.Column(db.Integer, default=1, comment='版本号')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(50), comment='创建人')
    updated_by = db.Column(db.String(50), comment='更新人')

    # 关系
    work_center = db.relationship('WorkCenter', backref='process_definitions')

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'process_type': self.process_type,
            'description': self.description,
            'work_instructions': self.work_instructions,
            'work_center_id': self.work_center_id,
            'work_center_name': self.work_center.name if self.work_center else None,
            'default_machine_id': self.default_machine_id,
            'default_machine_name': self.default_machine_name,
            'setup_time': self.setup_time,
            'standard_time': self.standard_time,
            'move_time': self.move_time,
            'min_batch_size': self.min_batch_size,
            'max_batch_size': self.max_batch_size,
            'daily_capacity': self.daily_capacity,
            'required_skill_level': self.required_skill_level,
            'min_operators': self.min_operators,
            'max_operators': self.max_operators,
            'inspection_required': self.inspection_required,
            'inspection_type': self.inspection_type,
            'quality_standards': self.quality_standards,
            'required_tools': self.required_tools,
            'required_materials': self.required_materials,
            'safety_notes': self.safety_notes,
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
        }

    def to_simple_dict(self):
        """简化版，用于列表展示"""
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'process_type': self.process_type,
            'standard_time': self.standard_time,
            'work_center_name': self.work_center.name if self.work_center else None,
            'inspection_required': self.inspection_required,
            'is_active': self.is_active,
        }


class ProcessRoute(db.Model):
    """
    工艺路线 - 定义产品的完整生产工艺流程
    一个产品可以有多个工艺路线版本
    """
    __tablename__ = 'mes_process_routes'

    id = db.Column(db.Integer, primary_key=True)
    route_code = db.Column(db.String(64), unique=True, nullable=False, comment='路线编码')
    name = db.Column(db.String(200), nullable=False, comment='路线名称')

    # 产品信息（关联PDM或手动输入）
    product_id = db.Column(db.Integer, comment='产品ID（PDM）')
    product_code = db.Column(db.String(100), comment='产品编码')
    product_name = db.Column(db.String(200), comment='产品名称')

    # 版本管理
    version = db.Column(db.String(20), default='1.0', comment='版本号')
    is_default = db.Column(db.Boolean, default=False, comment='是否默认路线')

    # 描述
    description = db.Column(db.Text, comment='路线描述')

    # 汇总信息（由工序步骤计算）
    total_steps = db.Column(db.Integer, default=0, comment='总工序数')
    total_standard_time = db.Column(db.Float, default=0, comment='总标准工时（分钟）')
    total_setup_time = db.Column(db.Float, default=0, comment='总准备时间（分钟）')

    # 状态
    status = db.Column(db.String(20), default='draft', comment='状态: draft/active/obsolete')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    # 审批
    approved_by = db.Column(db.String(50), comment='审批人')
    approved_at = db.Column(db.DateTime, comment='审批时间')

    # 生效日期
    effective_date = db.Column(db.Date, comment='生效日期')
    expiry_date = db.Column(db.Date, comment='失效日期')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(50), comment='创建人')
    updated_by = db.Column(db.String(50), comment='更新人')

    # 关系
    steps = db.relationship('ProcessRouteStep', backref='route', lazy='dynamic',
                           order_by='ProcessRouteStep.step_no',
                           cascade='all, delete-orphan')

    def to_dict(self, include_steps=True):
        result = {
            'id': self.id,
            'route_code': self.route_code,
            'name': self.name,
            'product_id': self.product_id,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'version': self.version,
            'is_default': self.is_default,
            'description': self.description,
            'total_steps': self.total_steps,
            'total_standard_time': self.total_standard_time,
            'total_setup_time': self.total_setup_time,
            'status': self.status,
            'is_active': self.is_active,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
        }

        if include_steps:
            result['steps'] = [step.to_dict() for step in self.steps.order_by(ProcessRouteStep.step_no)]

        return result

    def to_simple_dict(self):
        """简化版，用于列表和选择器"""
        return {
            'id': self.id,
            'route_code': self.route_code,
            'name': self.name,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'version': self.version,
            'is_default': self.is_default,
            'total_steps': self.total_steps,
            'total_standard_time': self.total_standard_time,
            'status': self.status,
            'is_active': self.is_active,
        }

    def recalculate_totals(self):
        """重新计算汇总数据"""
        steps = self.steps.all()
        self.total_steps = len(steps)
        self.total_standard_time = sum(s.standard_time or 0 for s in steps)
        self.total_setup_time = sum(s.setup_time or 0 for s in steps)


class ProcessRouteStep(db.Model):
    """
    工艺路线步骤 - 工艺路线中的单个工序步骤
    """
    __tablename__ = 'mes_process_route_steps'

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('mes_process_routes.id', ondelete='CASCADE'),
                        nullable=False, comment='工艺路线ID')
    process_id = db.Column(db.Integer, db.ForeignKey('mes_process_definitions.id'),
                          nullable=False, comment='工序定义ID')

    # 步骤序号
    step_no = db.Column(db.Integer, nullable=False, comment='步骤序号')
    step_name = db.Column(db.String(200), comment='步骤名称（可覆盖工序名称）')

    # 工序参数（可覆盖工序定义的默认值）
    work_center_id = db.Column(db.Integer, db.ForeignKey('mes_work_centers.id'), comment='工作中心')
    machine_id = db.Column(db.Integer, comment='指定设备ID（EAM）')
    machine_name = db.Column(db.String(200), comment='指定设备名称')

    # 工时参数（可覆盖）
    setup_time = db.Column(db.Float, comment='准备时间（分钟）')
    standard_time = db.Column(db.Float, comment='标准工时（分钟/件）')
    move_time = db.Column(db.Float, comment='移动时间（分钟）')

    # 批量参数（可覆盖）
    min_batch_size = db.Column(db.Integer, comment='最小批量')
    max_batch_size = db.Column(db.Integer, comment='最大批量')

    # 质量参数（可覆盖）
    inspection_required = db.Column(db.Boolean, comment='是否需要检验')
    inspection_type = db.Column(db.String(50), comment='检验类型')

    # 流程控制
    is_optional = db.Column(db.Boolean, default=False, comment='是否可选步骤')
    is_parallel = db.Column(db.Boolean, default=False, comment='是否可并行执行')
    predecessor_steps = db.Column(db.JSON, comment='前置步骤（JSON数组）')

    # 备注
    notes = db.Column(db.Text, comment='备注')

    # 状态
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    process = db.relationship('ProcessDefinition', backref='route_steps')
    work_center = db.relationship('WorkCenter', backref='route_steps')

    def to_dict(self):
        # 获取工序定义的默认值
        process = self.process

        return {
            'id': self.id,
            'route_id': self.route_id,
            'process_id': self.process_id,
            'process_code': process.code if process else None,
            'process_name': process.name if process else None,
            'process_type': process.process_type if process else None,
            'step_no': self.step_no,
            'step_name': self.step_name or (process.name if process else None),
            'work_center_id': self.work_center_id or (process.work_center_id if process else None),
            'work_center_name': self.work_center.name if self.work_center else (process.work_center.name if process and process.work_center else None),
            'machine_id': self.machine_id or (process.default_machine_id if process else None),
            'machine_name': self.machine_name or (process.default_machine_name if process else None),
            'setup_time': self.setup_time if self.setup_time is not None else (process.setup_time if process else 0),
            'standard_time': self.standard_time if self.standard_time is not None else (process.standard_time if process else 0),
            'move_time': self.move_time if self.move_time is not None else (process.move_time if process else 0),
            'min_batch_size': self.min_batch_size or (process.min_batch_size if process else 1),
            'max_batch_size': self.max_batch_size or (process.max_batch_size if process else None),
            'inspection_required': self.inspection_required if self.inspection_required is not None else (process.inspection_required if process else False),
            'inspection_type': self.inspection_type or (process.inspection_type if process else None),
            'is_optional': self.is_optional,
            'is_parallel': self.is_parallel,
            'predecessor_steps': self.predecessor_steps,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class WorkOrderProcess(db.Model):
    """
    工单工序 - 工单关联的具体工序执行记录
    当工单创建时，根据工艺路线生成工单工序列表
    """
    __tablename__ = 'mes_work_order_processes'

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey('mes_work_orders.id', ondelete='CASCADE'),
                             nullable=False, comment='工单ID')
    route_step_id = db.Column(db.Integer, db.ForeignKey('mes_process_route_steps.id'),
                             comment='工艺路线步骤ID')
    process_id = db.Column(db.Integer, db.ForeignKey('mes_process_definitions.id'),
                          comment='工序定义ID')

    # 步骤信息
    step_no = db.Column(db.Integer, nullable=False, comment='步骤序号')
    process_code = db.Column(db.String(50), comment='工序编码')
    process_name = db.Column(db.String(200), nullable=False, comment='工序名称')
    process_type = db.Column(db.String(32), comment='工序类型')

    # 计划信息
    planned_quantity = db.Column(db.Integer, nullable=False, comment='计划数量')
    planned_start = db.Column(db.DateTime, comment='计划开始时间')
    planned_end = db.Column(db.DateTime, comment='计划结束时间')

    # 执行信息
    work_center_id = db.Column(db.Integer, comment='工作中心ID')
    work_center_name = db.Column(db.String(100), comment='工作中心名称')
    machine_id = db.Column(db.Integer, comment='设备ID（EAM）')
    machine_name = db.Column(db.String(200), comment='设备名称')

    # 操作人员
    operator_id = db.Column(db.Integer, comment='操作员ID')
    operator_name = db.Column(db.String(100), comment='操作员姓名')
    assigned_by = db.Column(db.String(100), comment='派工人')
    assigned_at = db.Column(db.DateTime, comment='派工时间')

    # 工时信息
    setup_time = db.Column(db.Float, default=0, comment='准备时间（分钟）')
    standard_time = db.Column(db.Float, default=0, comment='标准工时（分钟/件）')
    planned_hours = db.Column(db.Float, comment='计划工时')
    actual_hours = db.Column(db.Float, comment='实际工时')

    # 实际执行
    actual_start = db.Column(db.DateTime, comment='实际开始时间')
    actual_end = db.Column(db.DateTime, comment='实际结束时间')
    completed_quantity = db.Column(db.Integer, default=0, comment='完成数量')
    defect_quantity = db.Column(db.Integer, default=0, comment='不良数量')

    # 状态
    status = db.Column(db.String(20), default='pending', comment='状态')
    is_current = db.Column(db.Boolean, default=False, comment='是否当前工序')

    # 质量
    inspection_required = db.Column(db.Boolean, default=False, comment='是否需要检验')
    inspection_status = db.Column(db.String(20), comment='检验状态: pending/passed/failed')
    inspection_result = db.Column(db.JSON, comment='检验结果')

    # 物料消耗
    material_consumed = db.Column(db.JSON, comment='物料消耗（JSON）')

    # 备注
    notes = db.Column(db.Text, comment='备注')
    completion_notes = db.Column(db.Text, comment='完成备注')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    work_order = db.relationship('WorkOrder', backref=db.backref('processes', lazy='dynamic',
                                cascade='all, delete-orphan'))
    route_step = db.relationship('ProcessRouteStep', backref='work_order_processes')
    process = db.relationship('ProcessDefinition', backref='work_order_processes')

    def to_dict(self):
        return {
            'id': self.id,
            'work_order_id': self.work_order_id,
            'work_order_no': self.work_order.order_no if self.work_order else None,
            'route_step_id': self.route_step_id,
            'process_id': self.process_id,
            'step_no': self.step_no,
            'process_code': self.process_code,
            'process_name': self.process_name,
            'process_type': self.process_type,
            'planned_quantity': self.planned_quantity,
            'planned_start': self.planned_start.isoformat() if self.planned_start else None,
            'planned_end': self.planned_end.isoformat() if self.planned_end else None,
            'work_center_id': self.work_center_id,
            'work_center_name': self.work_center_name,
            'machine_id': self.machine_id,
            'machine_name': self.machine_name,
            'operator_id': self.operator_id,
            'operator_name': self.operator_name,
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'setup_time': self.setup_time,
            'standard_time': self.standard_time,
            'planned_hours': self.planned_hours,
            'actual_hours': self.actual_hours,
            'actual_start': self.actual_start.isoformat() if self.actual_start else None,
            'actual_end': self.actual_end.isoformat() if self.actual_end else None,
            'completed_quantity': self.completed_quantity,
            'defect_quantity': self.defect_quantity,
            'status': self.status,
            'is_current': self.is_current,
            'inspection_required': self.inspection_required,
            'inspection_status': self.inspection_status,
            'inspection_result': self.inspection_result,
            'material_consumed': self.material_consumed,
            'notes': self.notes,
            'completion_notes': self.completion_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # 计算字段
            'completion_rate': round(self.completed_quantity / self.planned_quantity * 100, 2) if self.planned_quantity > 0 else 0,
            'defect_rate': round(self.defect_quantity / (self.completed_quantity + self.defect_quantity) * 100, 2) if (self.completed_quantity + self.defect_quantity) > 0 else 0,
        }

    def can_transition_to(self, new_status):
        """检查是否可以转换到新状态"""
        allowed = PROCESS_STATUS_TRANSITIONS.get(self.status, [])
        return new_status in allowed


# 工序类型中文映射
PROCESS_TYPE_LABELS = {
    'machining': '机加工',
    'assembly': '装配',
    'welding': '焊接',
    'painting': '喷涂',
    'testing': '测试',
    'inspection': '检验',
    'packaging': '包装',
    'heat_treatment': '热处理',
    'surface_treatment': '表面处理',
    'other': '其他',
}

# 工序状态中文映射
PROCESS_STATUS_LABELS = {
    'pending': '待开始',
    'waiting': '等待中',
    'in_progress': '进行中',
    'paused': '暂停',
    'completed': '已完成',
    'skipped': '已跳过',
}

# 工艺路线状态中文映射
ROUTE_STATUS_LABELS = {
    'draft': '草稿',
    'active': '生效',
    'obsolete': '废弃',
}
