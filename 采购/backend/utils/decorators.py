# suppliers/utils/decorators.py
# 装饰器：数据库操作、错误处理、认证
# -*- coding: utf-8 -*-
from functools import wraps
from flask import request
from extensions import db
from utils.response import error_response
import logging
import traceback

logger = logging.getLogger(__name__)


def handle_db_operation(operation_name):
    """装饰器：处理数据库操作的异常"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                db.session.rollback()
                logger.error(f"❌ {operation_name} 错误: {str(e)}\n{traceback.format_exc()}")
                return error_response("服务器内部错误", 500)
        return wrapper
    return decorator


def require_supplier_id(func):
    """装饰器：验证 Supplier-ID 请求头"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        supplier_id = request.headers.get('Supplier-ID')
        if not supplier_id:
            return error_response("缺少 Supplier-ID 请求头", 401)
        
        try:
            supplier_id = int(supplier_id)
        except (ValueError, TypeError):
            return error_response("无效的供应商ID", 400)
        
        return func(*args, **kwargs)
    return wrapper