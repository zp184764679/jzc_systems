# routes/supplier_admin/__init__.py
# 供应商管理系统 - 蓝图初始化
# -*- coding: utf-8 -*-
"""
供应商管理系统模块
将原来的 supplier_admin_routes.py 分包成：
- utils.py: CORS、响应处理、认证等工具函数
- serializers.py: 数据序列化函数
- supplier_routes.py: 供应商管理路由
- invoice_routes.py: 发票管理路由
- __init__.py: 蓝图组织和导出
"""

from .supplier_routes import bp_supplier
from .invoice_routes import bp_invoice

# 导出所有蓝图列表，供 main app 注册
BLUEPRINTS = [bp_supplier, bp_invoice]

__all__ = ['BLUEPRINTS', 'bp_supplier', 'bp_invoice']