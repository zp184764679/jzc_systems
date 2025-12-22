# backend/app/models/__init__.py
from .customer import Customer
from .supplier import Supplier, SUPPLIER_STATUS
from .sales import (
    SalesOpportunity, OpportunityStageHistory, FollowUpRecord,
    OpportunityStage, OpportunityPriority, FollowUpType,
    STAGE_PROBABILITY_MAP, STAGE_NAME_MAP, FOLLOW_UP_TYPE_MAP, PRIORITY_NAME_MAP
)
from .contract import (
    Contract, ContractItem, ContractApproval,
    ContractStatus, ContractType, ApprovalStatus,
    CONTRACT_TYPE_MAP, CONTRACT_STATUS_MAP, APPROVAL_STATUS_MAP
)
from .core import (
    Order, OrderLine, OrderApproval, InventoryTx,
    OrderStatus, ApprovalAction,
    ORDER_STATUS_TRANSITIONS, can_transition, get_next_status
)

__all__ = [
    'Customer',
    'Supplier', 'SUPPLIER_STATUS',
    'SalesOpportunity', 'OpportunityStageHistory', 'FollowUpRecord',
    'OpportunityStage', 'OpportunityPriority', 'FollowUpType',
    'STAGE_PROBABILITY_MAP', 'STAGE_NAME_MAP', 'FOLLOW_UP_TYPE_MAP', 'PRIORITY_NAME_MAP',
    'Contract', 'ContractItem', 'ContractApproval',
    'ContractStatus', 'ContractType', 'ApprovalStatus',
    'CONTRACT_TYPE_MAP', 'CONTRACT_STATUS_MAP', 'APPROVAL_STATUS_MAP',
    # 订单相关
    'Order', 'OrderLine', 'OrderApproval', 'InventoryTx',
    'OrderStatus', 'ApprovalAction',
    'ORDER_STATUS_TRANSITIONS', 'can_transition', 'get_next_status'
]
