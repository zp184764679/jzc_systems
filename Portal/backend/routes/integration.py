"""
Integration Routes - 子系统集成 API 路由
代理 CRM 和 HR 系统的接口，提供给项目管理使用
"""
from flask import Blueprint, request, jsonify
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.integration_service import integration_service

integration_bp = Blueprint('integration', __name__, url_prefix='/api/integration')


def get_token_from_request():
    """从请求头中提取 token"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        parts = auth_header.split(' ')
        if len(parts) == 2:
            return parts[1]
    return None


# ==================== CRM 客户接口 ====================

@integration_bp.route('/customers', methods=['GET'])
def get_customers():
    """
    获取客户列表
    Query params:
    - keyword: 搜索关键词
    - page: 页码（默认1）
    - page_size: 每页数量（默认20）
    """
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    token = get_token_from_request()

    result = integration_service.get_customers(
        keyword=keyword,
        page=page,
        page_size=page_size,
        token=token
    )

    if result['success']:
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['error']}), 503


@integration_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """获取客户详情"""
    token = get_token_from_request()
    result = integration_service.get_customer(customer_id, token=token)

    if result['success']:
        return jsonify(result['data']), 200
    elif result['error'] == '客户不存在':
        return jsonify({'error': result['error']}), 404
    else:
        return jsonify({'error': result['error']}), 503


# ==================== CRM 供应商接口 ====================

@integration_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    """
    获取供应商列表
    Query params:
    - keyword: 搜索关键词
    - page: 页码（默认1）
    - page_size: 每页数量（默认20）
    """
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    token = get_token_from_request()

    result = integration_service.get_suppliers(
        keyword=keyword,
        page=page,
        page_size=page_size,
        token=token
    )

    if result['success']:
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['error']}), 503


@integration_bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """获取供应商详情"""
    token = get_token_from_request()
    result = integration_service.get_supplier(supplier_id, token=token)

    if result['success']:
        return jsonify(result['data']), 200
    elif result['error'] == '供应商不存在':
        return jsonify({'error': result['error']}), 404
    else:
        return jsonify({'error': result['error']}), 503


@integration_bp.route('/suppliers/search', methods=['GET'])
def search_suppliers():
    """搜索供应商（用于下拉选择）"""
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', 10, type=int)
    token = get_token_from_request()

    result = integration_service.get_suppliers(
        keyword=keyword,
        page=1,
        page_size=limit,
        token=token
    )

    if result['success']:
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['error']}), 503


# ==================== 报价系统产品接口 ====================

@integration_bp.route('/products', methods=['GET'])
def get_products():
    """
    获取产品/品番号列表
    Query params:
    - keyword: 搜索关键词
    - page: 页码（默认1）
    - page_size: 每页数量（默认20）
    """
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    token = get_token_from_request()

    result = integration_service.get_products(
        keyword=keyword,
        page=page,
        page_size=page_size,
        token=token
    )

    if result['success']:
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['error']}), 503


@integration_bp.route('/products/<path:product_code>', methods=['GET'])
def get_product(product_code):
    """获取产品详情"""
    token = get_token_from_request()
    result = integration_service.get_product(product_code, token=token)

    if result['success']:
        return jsonify(result['data']), 200
    elif result['error'] == '产品不存在':
        return jsonify({'error': result['error']}), 404
    else:
        return jsonify({'error': result['error']}), 503


@integration_bp.route('/products/search', methods=['GET'])
def search_products():
    """搜索产品/品番号（用于下拉选择）"""
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', 10, type=int)
    token = get_token_from_request()

    result = integration_service.get_products(
        keyword=keyword,
        page=1,
        page_size=limit,
        token=token
    )

    if result['success']:
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['error']}), 503


# ==================== HR 员工接口 ====================

@integration_bp.route('/employees', methods=['GET'])
def get_employees():
    """
    获取员工列表
    Query params:
    - search: 搜索关键词（姓名、工号）
    - department: 部门筛选
    - page: 页码（默认1）
    - page_size: 每页数量（默认50）
    """
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    token = get_token_from_request()

    result = integration_service.get_employees(
        search=search,
        department=department,
        page=page,
        page_size=page_size,
        token=token
    )

    if result['success']:
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['error']}), 503


@integration_bp.route('/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """获取员工详情"""
    token = get_token_from_request()
    result = integration_service.get_employee(employee_id, token=token)

    if result['success']:
        return jsonify(result['data']), 200
    elif result['error'] == '员工不存在':
        return jsonify({'error': result['error']}), 404
    else:
        return jsonify({'error': result['error']}), 503


@integration_bp.route('/departments', methods=['GET'])
def get_departments():
    """获取部门列表"""
    token = get_token_from_request()
    result = integration_service.get_departments(token=token)

    if result['success']:
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['error']}), 503


@integration_bp.route('/positions', methods=['GET'])
def get_positions():
    """获取职位列表"""
    token = get_token_from_request()
    result = integration_service.get_positions(token=token)

    if result['success']:
        return jsonify(result['data']), 200
    else:
        return jsonify({'error': result['error']}), 503


# ==================== 健康检查 ====================

@integration_bp.route('/health', methods=['GET'])
def check_health():
    """检查所有子系统的健康状态"""
    result = integration_service.check_health()
    return jsonify(result), 200
