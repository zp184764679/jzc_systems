# MES 质量管理模型
# Quality Management Models for MES

from database import db
from datetime import datetime
import enum


class InspectionStage(enum.Enum):
    """检验阶段"""
    INCOMING = "incoming"       # 来料检验 (IQC)
    PROCESS = "process"         # 过程检验 (IPQC)
    FINAL = "final"             # 最终检验 (FQC)
    OUTGOING = "outgoing"       # 出货检验 (OQC)


class InspectionMethod(enum.Enum):
    """检验方式"""
    FULL = "full"               # 全检
    SAMPLING = "sampling"       # 抽检
    SKIP = "skip"               # 免检


class QualityResult(enum.Enum):
    """检验结果"""
    PENDING = "pending"         # 待检验
    PASS = "pass"               # 合格
    FAIL = "fail"               # 不合格
    CONDITIONAL = "conditional" # 让步接收


class DispositionAction(enum.Enum):
    """处置动作"""
    ACCEPT = "accept"           # 接收
    REJECT = "reject"           # 拒收
    REWORK = "rework"           # 返工
    REPAIR = "repair"           # 返修
    SCRAP = "scrap"             # 报废
    CONCESSION = "concession"   # 让步放行
    DOWNGRADE = "downgrade"     # 降级使用


class DefectSeverity(enum.Enum):
    """缺陷严重程度"""
    CRITICAL = "critical"       # 致命缺陷
    MAJOR = "major"             # 严重缺陷
    MINOR = "minor"             # 轻微缺陷


def generate_inspection_no():
    """生成检验单号: QC + 年月日 + 4位序号"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"QC{today}"

    last = QualityInspectionOrder.query.filter(
        QualityInspectionOrder.inspection_no.like(f"{prefix}%")
    ).order_by(QualityInspectionOrder.inspection_no.desc()).first()

    if last:
        try:
            seq = int(last.inspection_no[-4:]) + 1
        except:
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


def generate_ncr_no():
    """生成不合格品报告单号: NCR + 年月日 + 4位序号"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"NCR{today}"

    last = NonConformanceReport.query.filter(
        NonConformanceReport.ncr_no.like(f"{prefix}%")
    ).order_by(NonConformanceReport.ncr_no.desc()).first()

    if last:
        try:
            seq = int(last.ncr_no[-4:]) + 1
        except:
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:04d}"


class InspectionStandard(db.Model):
    """
    检验标准 - 定义产品/工序的检验要求
    """
    __tablename__ = 'mes_inspection_standards'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, comment='标准编码')
    name = db.Column(db.String(200), nullable=False, comment='标准名称')

    # 适用范围
    product_id = db.Column(db.Integer, comment='适用产品ID')
    product_code = db.Column(db.String(100), comment='适用产品编码')
    product_name = db.Column(db.String(200), comment='适用产品名称')
    process_id = db.Column(db.Integer, comment='适用工序ID')
    process_name = db.Column(db.String(200), comment='适用工序名称')

    # 检验配置
    inspection_stage = db.Column(db.String(32), default='process', comment='检验阶段')
    inspection_method = db.Column(db.String(32), default='sampling', comment='检验方式')
    sample_plan = db.Column(db.String(100), comment='抽样方案（如AQL）')
    sample_size_formula = db.Column(db.String(200), comment='抽样数量公式')

    # 检验项目
    inspection_items = db.Column(db.JSON, comment='检验项目列表')
    # 格式: [{name, specification, method, tool, upper_limit, lower_limit, unit, critical}]

    # AQL 标准
    aql_critical = db.Column(db.Float, comment='致命缺陷AQL')
    aql_major = db.Column(db.Float, comment='严重缺陷AQL')
    aql_minor = db.Column(db.Float, comment='轻微缺陷AQL')

    # 版本
    version = db.Column(db.String(20), default='1.0', comment='版本号')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(50), comment='创建人')

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'product_id': self.product_id,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'process_id': self.process_id,
            'process_name': self.process_name,
            'inspection_stage': self.inspection_stage,
            'inspection_method': self.inspection_method,
            'sample_plan': self.sample_plan,
            'sample_size_formula': self.sample_size_formula,
            'inspection_items': self.inspection_items,
            'aql_critical': self.aql_critical,
            'aql_major': self.aql_major,
            'aql_minor': self.aql_minor,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
        }

    def to_simple_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'product_name': self.product_name,
            'process_name': self.process_name,
            'inspection_stage': self.inspection_stage,
            'inspection_method': self.inspection_method,
            'is_active': self.is_active,
        }


class DefectType(db.Model):
    """
    缺陷类型 - 缺陷分类目录
    """
    __tablename__ = 'mes_defect_types'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, comment='缺陷编码')
    name = db.Column(db.String(200), nullable=False, comment='缺陷名称')
    category = db.Column(db.String(100), comment='缺陷分类')
    severity = db.Column(db.String(32), default='minor', comment='严重程度')
    description = db.Column(db.Text, comment='缺陷描述')
    cause_analysis = db.Column(db.Text, comment='原因分析')
    corrective_action = db.Column(db.Text, comment='纠正措施')
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category,
            'severity': self.severity,
            'description': self.description,
            'cause_analysis': self.cause_analysis,
            'corrective_action': self.corrective_action,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
        }


class QualityInspectionOrder(db.Model):
    """
    质量检验单 - 检验执行记录
    """
    __tablename__ = 'mes_quality_inspection_orders'

    id = db.Column(db.Integer, primary_key=True)
    inspection_no = db.Column(db.String(64), unique=True, nullable=False, comment='检验单号')

    # 关联
    work_order_id = db.Column(db.Integer, db.ForeignKey('mes_work_orders.id'), comment='工单ID')
    work_order_process_id = db.Column(db.Integer, comment='工单工序ID')
    production_record_id = db.Column(db.Integer, comment='生产记录ID')
    standard_id = db.Column(db.Integer, db.ForeignKey('mes_inspection_standards.id'), comment='检验标准ID')

    # 检验信息
    inspection_stage = db.Column(db.String(32), default='process', comment='检验阶段')
    inspection_method = db.Column(db.String(32), default='sampling', comment='检验方式')

    # 产品信息
    product_code = db.Column(db.String(100), comment='产品编码')
    product_name = db.Column(db.String(200), comment='产品名称')
    process_name = db.Column(db.String(200), comment='工序名称')
    batch_no = db.Column(db.String(100), comment='批次号')

    # 数量
    lot_size = db.Column(db.Integer, comment='批量大小')
    sample_size = db.Column(db.Integer, comment='抽样数量')
    pass_quantity = db.Column(db.Integer, default=0, comment='合格数量')
    fail_quantity = db.Column(db.Integer, default=0, comment='不合格数量')

    # 检验结果
    result = db.Column(db.String(32), default='pending', comment='检验结果')
    pass_rate = db.Column(db.Float, comment='合格率')

    # 检验项结果
    item_results = db.Column(db.JSON, comment='检验项结果')
    # 格式: [{item_name, specification, actual_value, result, defect_type, notes}]

    # 检验人
    inspector_id = db.Column(db.Integer, comment='检验员ID')
    inspector_name = db.Column(db.String(100), comment='检验员姓名')
    inspected_at = db.Column(db.DateTime, comment='检验时间')

    # 复核
    reviewer_id = db.Column(db.Integer, comment='复核人ID')
    reviewer_name = db.Column(db.String(100), comment='复核人姓名')
    reviewed_at = db.Column(db.DateTime, comment='复核时间')

    # 处置
    disposition = db.Column(db.String(32), comment='处置方式')
    disposition_notes = db.Column(db.Text, comment='处置说明')
    disposed_by = db.Column(db.String(100), comment='处置人')
    disposed_at = db.Column(db.DateTime, comment='处置时间')

    # 状态
    status = db.Column(db.String(32), default='pending', comment='状态: pending/inspecting/completed/closed')

    # 备注
    notes = db.Column(db.Text, comment='备注')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(50))

    # 关系
    standard = db.relationship('InspectionStandard', backref='inspection_orders')
    work_order = db.relationship('WorkOrder', backref='quality_inspections')

    def to_dict(self):
        return {
            'id': self.id,
            'inspection_no': self.inspection_no,
            'work_order_id': self.work_order_id,
            'work_order_no': self.work_order.order_no if self.work_order else None,
            'work_order_process_id': self.work_order_process_id,
            'production_record_id': self.production_record_id,
            'standard_id': self.standard_id,
            'standard_name': self.standard.name if self.standard else None,
            'inspection_stage': self.inspection_stage,
            'inspection_method': self.inspection_method,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'process_name': self.process_name,
            'batch_no': self.batch_no,
            'lot_size': self.lot_size,
            'sample_size': self.sample_size,
            'pass_quantity': self.pass_quantity,
            'fail_quantity': self.fail_quantity,
            'result': self.result,
            'pass_rate': self.pass_rate,
            'item_results': self.item_results,
            'inspector_id': self.inspector_id,
            'inspector_name': self.inspector_name,
            'inspected_at': self.inspected_at.isoformat() if self.inspected_at else None,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer_name,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'disposition': self.disposition,
            'disposition_notes': self.disposition_notes,
            'disposed_by': self.disposed_by,
            'disposed_at': self.disposed_at.isoformat() if self.disposed_at else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
        }

    def to_simple_dict(self):
        return {
            'id': self.id,
            'inspection_no': self.inspection_no,
            'work_order_no': self.work_order.order_no if self.work_order else None,
            'product_name': self.product_name,
            'process_name': self.process_name,
            'inspection_stage': self.inspection_stage,
            'lot_size': self.lot_size,
            'sample_size': self.sample_size,
            'result': self.result,
            'pass_rate': self.pass_rate,
            'inspector_name': self.inspector_name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class DefectRecord(db.Model):
    """
    缺陷记录 - 检验发现的具体缺陷
    """
    __tablename__ = 'mes_defect_records'

    id = db.Column(db.Integer, primary_key=True)
    inspection_order_id = db.Column(db.Integer, db.ForeignKey('mes_quality_inspection_orders.id'),
                                   nullable=False, comment='检验单ID')
    defect_type_id = db.Column(db.Integer, db.ForeignKey('mes_defect_types.id'), comment='缺陷类型ID')

    # 缺陷信息
    defect_code = db.Column(db.String(50), comment='缺陷编码')
    defect_name = db.Column(db.String(200), nullable=False, comment='缺陷名称')
    severity = db.Column(db.String(32), default='minor', comment='严重程度')
    quantity = db.Column(db.Integer, default=1, comment='缺陷数量')

    # 检验项关联
    inspection_item = db.Column(db.String(200), comment='检验项')
    specification = db.Column(db.String(200), comment='规格要求')
    actual_value = db.Column(db.String(200), comment='实测值')

    # 详情
    description = db.Column(db.Text, comment='缺陷描述')
    location = db.Column(db.String(200), comment='缺陷位置')
    images = db.Column(db.JSON, comment='缺陷图片（URL列表）')

    # 原因分析
    root_cause = db.Column(db.Text, comment='根本原因')
    responsible_dept = db.Column(db.String(100), comment='责任部门')

    # 时间戳
    found_at = db.Column(db.DateTime, default=datetime.utcnow, comment='发现时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    inspection_order = db.relationship('QualityInspectionOrder',
                                       backref=db.backref('defect_records', lazy='dynamic'))
    defect_type = db.relationship('DefectType', backref='defect_records')

    def to_dict(self):
        return {
            'id': self.id,
            'inspection_order_id': self.inspection_order_id,
            'defect_type_id': self.defect_type_id,
            'defect_code': self.defect_code,
            'defect_name': self.defect_name,
            'severity': self.severity,
            'quantity': self.quantity,
            'inspection_item': self.inspection_item,
            'specification': self.specification,
            'actual_value': self.actual_value,
            'description': self.description,
            'location': self.location,
            'images': self.images,
            'root_cause': self.root_cause,
            'responsible_dept': self.responsible_dept,
            'found_at': self.found_at.isoformat() if self.found_at else None,
        }


class NonConformanceReport(db.Model):
    """
    不合格品报告 (NCR) - 不合格品处理流程
    """
    __tablename__ = 'mes_non_conformance_reports'

    id = db.Column(db.Integer, primary_key=True)
    ncr_no = db.Column(db.String(64), unique=True, nullable=False, comment='NCR编号')

    # 关联检验单
    inspection_order_id = db.Column(db.Integer, db.ForeignKey('mes_quality_inspection_orders.id'),
                                   comment='检验单ID')
    work_order_id = db.Column(db.Integer, comment='工单ID')

    # 产品信息
    product_code = db.Column(db.String(100), comment='产品编码')
    product_name = db.Column(db.String(200), comment='产品名称')
    batch_no = db.Column(db.String(100), comment='批次号')
    quantity = db.Column(db.Integer, comment='不合格数量')

    # 不合格描述
    nc_type = db.Column(db.String(100), comment='不合格类型')
    nc_description = db.Column(db.Text, comment='不合格描述')
    severity = db.Column(db.String(32), default='major', comment='严重程度')

    # 原因分析
    root_cause = db.Column(db.Text, comment='根本原因')
    cause_category = db.Column(db.String(100), comment='原因分类')

    # 处置决定
    disposition = db.Column(db.String(32), comment='处置方式')
    disposition_notes = db.Column(db.Text, comment='处置说明')
    disposition_by = db.Column(db.String(100), comment='处置决定人')
    disposition_at = db.Column(db.DateTime, comment='处置决定时间')

    # 纠正措施
    corrective_action = db.Column(db.Text, comment='纠正措施')
    preventive_action = db.Column(db.Text, comment='预防措施')
    action_due_date = db.Column(db.Date, comment='措施完成期限')
    action_completed_at = db.Column(db.DateTime, comment='措施完成时间')

    # 验证
    verified_by = db.Column(db.String(100), comment='验证人')
    verified_at = db.Column(db.DateTime, comment='验证时间')
    verification_result = db.Column(db.String(32), comment='验证结果')

    # 状态
    status = db.Column(db.String(32), default='open', comment='状态: open/reviewing/dispositioned/closed')

    # 责任
    responsible_dept = db.Column(db.String(100), comment='责任部门')
    responsible_person = db.Column(db.String(100), comment='责任人')

    # 发起人
    reporter_id = db.Column(db.Integer, comment='发起人ID')
    reporter_name = db.Column(db.String(100), comment='发起人姓名')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime, comment='关闭时间')

    # 关系
    inspection_order = db.relationship('QualityInspectionOrder', backref='ncr_reports')

    def to_dict(self):
        return {
            'id': self.id,
            'ncr_no': self.ncr_no,
            'inspection_order_id': self.inspection_order_id,
            'inspection_no': self.inspection_order.inspection_no if self.inspection_order else None,
            'work_order_id': self.work_order_id,
            'product_code': self.product_code,
            'product_name': self.product_name,
            'batch_no': self.batch_no,
            'quantity': self.quantity,
            'nc_type': self.nc_type,
            'nc_description': self.nc_description,
            'severity': self.severity,
            'root_cause': self.root_cause,
            'cause_category': self.cause_category,
            'disposition': self.disposition,
            'disposition_notes': self.disposition_notes,
            'disposition_by': self.disposition_by,
            'disposition_at': self.disposition_at.isoformat() if self.disposition_at else None,
            'corrective_action': self.corrective_action,
            'preventive_action': self.preventive_action,
            'action_due_date': self.action_due_date.isoformat() if self.action_due_date else None,
            'action_completed_at': self.action_completed_at.isoformat() if self.action_completed_at else None,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verification_result': self.verification_result,
            'status': self.status,
            'responsible_dept': self.responsible_dept,
            'responsible_person': self.responsible_person,
            'reporter_id': self.reporter_id,
            'reporter_name': self.reporter_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
        }

    def to_simple_dict(self):
        return {
            'id': self.id,
            'ncr_no': self.ncr_no,
            'product_name': self.product_name,
            'batch_no': self.batch_no,
            'quantity': self.quantity,
            'nc_type': self.nc_type,
            'severity': self.severity,
            'disposition': self.disposition,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# 检验单状态流转
INSPECTION_STATUS_TRANSITIONS = {
    'pending': ['inspecting'],
    'inspecting': ['completed'],
    'completed': ['closed'],
    'closed': [],
}

# NCR 状态流转
NCR_STATUS_TRANSITIONS = {
    'open': ['reviewing'],
    'reviewing': ['dispositioned'],
    'dispositioned': ['closed'],
    'closed': [],
}

# 标签映射
INSPECTION_STAGE_LABELS = {
    'incoming': '来料检验(IQC)',
    'process': '过程检验(IPQC)',
    'final': '最终检验(FQC)',
    'outgoing': '出货检验(OQC)',
}

INSPECTION_METHOD_LABELS = {
    'full': '全检',
    'sampling': '抽检',
    'skip': '免检',
}

QUALITY_RESULT_LABELS = {
    'pending': '待检验',
    'pass': '合格',
    'fail': '不合格',
    'conditional': '让步接收',
}

DISPOSITION_LABELS = {
    'accept': '接收',
    'reject': '拒收',
    'rework': '返工',
    'repair': '返修',
    'scrap': '报废',
    'concession': '让步放行',
    'downgrade': '降级使用',
}

DEFECT_SEVERITY_LABELS = {
    'critical': '致命缺陷',
    'major': '严重缺陷',
    'minor': '轻微缺陷',
}

NCR_STATUS_LABELS = {
    'open': '待处理',
    'reviewing': '审核中',
    'dispositioned': '已处置',
    'closed': '已关闭',
}
