# backend/app/models/__init__.py
from .machine import Machine
from .base_data import (
    EquipmentStatus, FactoryLocation, EquipmentGroup, Brand, StoragePlace
)
from .maintenance import (
    MaintenanceStandard, MaintenancePlan, MaintenanceOrder,
    FaultReport, InspectionRecord,
    MaintenanceType, MaintenanceCycle, OrderStatus,
    generate_order_no, generate_report_no, generate_inspection_no,
    CYCLE_DAYS_MAP, ORDER_STATUS_TRANSITIONS, FAULT_STATUS_TRANSITIONS
)
from .spare_parts import (
    SparePartCategory, SparePart, SparePartTransaction,
    TransactionType, TRANSACTION_TYPE_LABELS,
    generate_spare_part_code, generate_transaction_no, generate_category_code
)
from .capacity import (
    CapacityConfig, CapacityAdjustment, CapacityLog,
    ShiftType, AdjustmentType, CapacityStatus,
    SHIFT_TYPE_LABELS, ADJUSTMENT_TYPE_LABELS, CAPACITY_STATUS_LABELS,
    generate_config_code, generate_adjustment_code
)

__all__ = [
    'Machine',
    'EquipmentStatus', 'FactoryLocation', 'EquipmentGroup', 'Brand', 'StoragePlace',
    'MaintenanceStandard', 'MaintenancePlan', 'MaintenanceOrder',
    'FaultReport', 'InspectionRecord',
    'MaintenanceType', 'MaintenanceCycle', 'OrderStatus',
    'generate_order_no', 'generate_report_no', 'generate_inspection_no',
    'CYCLE_DAYS_MAP', 'ORDER_STATUS_TRANSITIONS', 'FAULT_STATUS_TRANSITIONS',
    # 备件管理
    'SparePartCategory', 'SparePart', 'SparePartTransaction',
    'TransactionType', 'TRANSACTION_TYPE_LABELS',
    'generate_spare_part_code', 'generate_transaction_no', 'generate_category_code',
    # 产能配置
    'CapacityConfig', 'CapacityAdjustment', 'CapacityLog',
    'ShiftType', 'AdjustmentType', 'CapacityStatus',
    'SHIFT_TYPE_LABELS', 'ADJUSTMENT_TYPE_LABELS', 'CAPACITY_STATUS_LABELS',
    'generate_config_code', 'generate_adjustment_code'
]
