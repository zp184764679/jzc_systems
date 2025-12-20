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

__all__ = [
    'db',
    'ProductMaster',
    'TechnicalSpec',
    'InspectionCriteria',
    'ProcessDocument',
    'ProductFileLink'
]
