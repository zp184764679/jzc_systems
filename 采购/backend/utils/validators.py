# suppliers/utils/validators.py
# 验证函数：JSON数据、字段验证
# -*- coding: utf-8 -*-
from flask import request
from utils.response import error_response
from models.supplier import Supplier


def validate_json_data(required_fields=None):
    """验证 JSON 请求数据"""
    data = request.get_json(silent=True) or {}
    
    if not data:
        return None, error_response("请求数据格式错误", 400)
    
    if required_fields:
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return None, error_response(f"缺少必填字段: {', '.join(missing)}", 400)
    
    return data, None


def validate_field(data, field_name, default=None, allow_empty=False):
    """提取和验证字段"""
    value = data.get(field_name, default)
    if isinstance(value, str):
        value = value.strip() if value else default
    
    if not allow_empty and not value:
        return None, f"{field_name} 不能为空"
    
    return value, None


def get_supplier_or_error():
    """获取当前供应商，若失败返回错误响应"""
    supplier_id = request.headers.get('Supplier-ID')
    if not supplier_id:
        return None, error_response("缺少 Supplier-ID 请求头", 401)
    
    try:
        supplier = Supplier.query.get(int(supplier_id))
        if not supplier:
            return None, error_response("供应商不存在", 404)
        return supplier, None
    except (ValueError, TypeError):
        return None, error_response("无效的供应商ID", 400)