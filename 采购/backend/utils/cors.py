# -*- coding: utf-8 -*-
"""
CORS跨域处理工具
统一管理CORS相关功能
"""
from functools import wraps
from flask import request


def handle_cors(f):
    """
    处理CORS预检请求的装饰器

    用法:
        @bp.before_request
        @handle_cors
        def before_request_func():
            pass

    或者:
        @bp.route("/api/endpoint", methods=["GET", "POST"])
        @handle_cors
        def my_endpoint():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 处理OPTIONS预检请求
        if request.method == "OPTIONS":
            return "", 200
        return f(*args, **kwargs)

    return decorated_function


def add_cors_headers(response):
    """
    为响应添加CORS头
    通常在after_request中使用

    用法:
        @bp.after_request
        def after_request(response):
            return add_cors_headers(response)

    参数:
        response: Flask响应对象

    返回:
        添加了CORS头的响应对象
    """
    # 允许所有来源（生产环境应该限制）
    response.headers["Access-Control-Allow-Origin"] = "*"

    # 允许的HTTP方法
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"

    # 允许的请求头
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, Authorization, User-ID, User-Role, Supplier-ID, "
        "X-Requested-With, Accept, Origin"
    )

    # 允许携带凭证
    response.headers["Access-Control-Allow-Credentials"] = "true"

    # 预检请求的缓存时间（秒）
    response.headers["Access-Control-Max-Age"] = "3600"

    return response


def register_cors_handlers(blueprint):
    """
    为Blueprint注册CORS处理器

    用法:
        bp = Blueprint("my_blueprint", __name__)
        register_cors_handlers(bp)

    参数:
        blueprint: Flask Blueprint对象
    """
    @blueprint.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            return "", 200

    @blueprint.after_request
    def add_cors(response):
        return add_cors_headers(response)
