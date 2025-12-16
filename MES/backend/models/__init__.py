# MES Models
from .work_order import WorkOrder
from .production_record import ProductionRecord
from .quality_inspection import QualityInspection
from .base_data import (
    WorkOrderStatus, SourceType, InspectionType, InspectionResult,
    DispositionType, ProductionLine, WorkCenter
)
from .process import (
    ProcessDefinition, ProcessRoute, ProcessRouteStep, WorkOrderProcess,
    ProcessType, ProcessStatus,
    generate_route_code,
    PROCESS_STATUS_TRANSITIONS,
    PROCESS_TYPE_LABELS, PROCESS_STATUS_LABELS, ROUTE_STATUS_LABELS
)
from .quality import (
    InspectionStandard, DefectType, QualityInspectionOrder, DefectRecord,
    NonConformanceReport,
    InspectionStage, InspectionMethod, QualityResult, DispositionAction, DefectSeverity,
    generate_inspection_no, generate_ncr_no,
    INSPECTION_STATUS_TRANSITIONS, NCR_STATUS_TRANSITIONS,
    INSPECTION_STAGE_LABELS, INSPECTION_METHOD_LABELS, QUALITY_RESULT_LABELS,
    DISPOSITION_LABELS, DEFECT_SEVERITY_LABELS, NCR_STATUS_LABELS
)
from .schedule import (
    ProductionSchedule, ScheduleTask, MachineCapacity,
    ScheduleStatus, TaskStatus,
    generate_schedule_code,
    SCHEDULE_STATUS_LABELS, TASK_STATUS_LABELS
)
from .traceability import (
    MaterialLot, ProductLot, MaterialConsumption, TraceRecord,
    MaterialLotStatus, ProductLotStatus,
    generate_material_lot_no, generate_product_lot_no,
    MATERIAL_LOT_STATUS_LABELS, PRODUCT_LOT_STATUS_LABELS
)

__all__ = [
    # 工单
    'WorkOrder',
    # 生产记录
    'ProductionRecord',
    # 质量检验 (旧)
    'QualityInspection',
    # 基础数据
    'WorkOrderStatus', 'SourceType', 'InspectionType', 'InspectionResult',
    'DispositionType', 'ProductionLine', 'WorkCenter',
    # 工序管理
    'ProcessDefinition', 'ProcessRoute', 'ProcessRouteStep', 'WorkOrderProcess',
    'ProcessType', 'ProcessStatus',
    'generate_route_code',
    'PROCESS_STATUS_TRANSITIONS',
    'PROCESS_TYPE_LABELS', 'PROCESS_STATUS_LABELS', 'ROUTE_STATUS_LABELS',
    # 质量管理 (新)
    'InspectionStandard', 'DefectType', 'QualityInspectionOrder', 'DefectRecord',
    'NonConformanceReport',
    'InspectionStage', 'InspectionMethod', 'QualityResult', 'DispositionAction', 'DefectSeverity',
    'generate_inspection_no', 'generate_ncr_no',
    'INSPECTION_STATUS_TRANSITIONS', 'NCR_STATUS_TRANSITIONS',
    'INSPECTION_STAGE_LABELS', 'INSPECTION_METHOD_LABELS', 'QUALITY_RESULT_LABELS',
    'DISPOSITION_LABELS', 'DEFECT_SEVERITY_LABELS', 'NCR_STATUS_LABELS',
    # 生产排程
    'ProductionSchedule', 'ScheduleTask', 'MachineCapacity',
    'ScheduleStatus', 'TaskStatus',
    'generate_schedule_code',
    'SCHEDULE_STATUS_LABELS', 'TASK_STATUS_LABELS',
    # 物料追溯
    'MaterialLot', 'ProductLot', 'MaterialConsumption', 'TraceRecord',
    'MaterialLotStatus', 'ProductLotStatus',
    'generate_material_lot_no', 'generate_product_lot_no',
    'MATERIAL_LOT_STATUS_LABELS', 'PRODUCT_LOT_STATUS_LABELS',
]
