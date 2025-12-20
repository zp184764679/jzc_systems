"""
TDM 数据模型
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入所有模型
from .product_master import ProductMaster
from .technical_spec import TechnicalSpec
from .inspection_criteria import InspectionCriteria
from .process_document import ProcessDocument
from .product_file_link import ProductFileLink

# 共享数据模型（与报价系统共享）
from .shared_material import Material
from .shared_process import Process
from .shared_drawing import Drawing

__all__ = [
    'db',
    'ProductMaster',
    'TechnicalSpec',
    'InspectionCriteria',
    'ProcessDocument',
    'ProductFileLink',
    'Material',
    'Process',
    'Drawing'
]
