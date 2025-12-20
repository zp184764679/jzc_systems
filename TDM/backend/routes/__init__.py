"""
TDM API 路由
"""
from .products import products_bp
from .technical_specs import technical_specs_bp
from .inspection import inspection_bp
from .process_docs import process_docs_bp
from .files import files_bp

__all__ = [
    'products_bp',
    'technical_specs_bp',
    'inspection_bp',
    'process_docs_bp',
    'files_bp'
]
