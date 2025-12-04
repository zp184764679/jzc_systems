# suppliers/utils/response.py
# 统一响应处理 + CORS
# -*- coding: utf-8 -*-
from flask import jsonify

def cors_headers():
    """返回 CORS 响应头"""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, Supplier-ID",
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


def options_response():
    """OPTIONS 预检响应"""
    from flask import make_response as flask_make_response
    resp = flask_make_response()
    resp.status_code = 204
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Supplier-ID'
    resp.headers['Access-Control-Max-Age'] = '86400'
    resp.headers['Content-Length'] = '0'
    return resp