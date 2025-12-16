# models/__init__.py
"""
数据库模型
"""
from .material import Material
from .process import Process, CuttingParameter
from .drawing import Drawing
from .product import Product
from .quote import Quote, QuoteItem, QuoteProcess
from .quote_approval import QuoteApproval, QuoteStatus, ApprovalAction, can_transition, QUOTE_STATUS_TRANSITIONS
from .process_route import ProcessRoute, ProcessRouteStep
from .ocr_correction import OCRCorrection
from .bom import BOM, BOMItem

__all__ = [
    "Material",
    "Process",
    "CuttingParameter",
    "Drawing",
    "Product",
    "Quote",
    "QuoteItem",
    "QuoteProcess",
    "QuoteApproval",
    "QuoteStatus",
    "ApprovalAction",
    "can_transition",
    "QUOTE_STATUS_TRANSITIONS",
    "ProcessRoute",
    "ProcessRouteStep",
    "OCRCorrection",
    "BOM",
    "BOMItem",
]
