# routes/supplier_admin/utils.py
# 供应商管理系统 - 工具模块
# -*- coding: utf-8 -*-
from flask import request, jsonify
from functools import wraps
from extensions import db
import logging
import traceback

logger = logging.getLogger(__name__)


# ==============================
# CORS 和响应处理
# ==============================
def cors_headers():
    """返回 CORS 响应头"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, User-ID, User-Role",
        "Access-Control-Max-Age": "86400"
    }


def make_response(data=None, status_code=200, message=None, is_error=False):
    """统一响应处理函数"""
    if is_error:
        resp_data = {"error": message or "未知错误"}
        if data:
            resp_data.update(data)
        resp = jsonify(resp_data)
    else:
        if isinstance(data, dict):
            resp = jsonify(data)
        elif isinstance(data, list):
            resp = jsonify(data)
        else:
            resp_data = {"message": message or "成功"} if message else {"data": data}
            resp = jsonify(resp_data)
    
    resp.status_code = status_code
    for key, value in cors_headers().items():
        resp.headers[key] = value
    
    return resp


def error_response(message, status_code=400, data=None):
    """返回错误响应"""
    return make_response(data=data, status_code=status_code, message=message, is_error=True)


def success_response(data=None, status_code=200, message=None):
    """返回成功响应"""
    if message:
        if data:
            resp_data = {"message": message}
            if isinstance(data, dict):
                resp_data.update(data)
            else:
                resp_data["data"] = data
        else:
            resp_data = {"message": message}
    else:
        resp_data = data if data is not None else {"status": "success"}
    
    return make_response(data=resp_data, status_code=status_code)


# ==============================
# 装饰器
# ==============================
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


# ==============================
# 验证和认证辅助函数
# ==============================
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


def check_admin_permission():
    """✅ 修复：检查当前用户是否为管理员（admin 或 super_admin）"""
    from models.user import User
    
    user_role = request.headers.get('User-Role')
    
    # 方式1：前端直接传入角色（快速）
    if user_role in ['admin', 'super_admin']:  # ✅ 修改：允许 super_admin
        return True, None
    
    # 方式2：从用户ID查询角色（更安全）
    user_id = request.headers.get('User-ID')
    if not user_id:
        return False, error_response("未提供认证信息（需要 User-ID 或 User-Role 请求头）", 401)
    
    try:
        user = User.query.get(int(user_id))
        if not user:
            return False, error_response("用户不存在", 401)
        
        # ✅ 修改：支持 admin 和 super_admin
        if user.role not in ['admin', 'super_admin']:
            logger.warning(f"⚠️ 非管理员用户 (ID: {user_id}, Role: {user.role}) 尝试执行管理操作")
            return False, error_response("权限不足：只有管理员可以执行此操作", 403)
        
        return True, None
    
    except Exception as e:
        logger.error(f"❌ 权限检查失败: {str(e)}")
        return False, error_response("权限检查失败", 500)