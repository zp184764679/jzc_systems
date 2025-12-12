"""
SHM 系统集成路由
安全修复：添加认证装饰器
"""
from flask import Blueprint, request, jsonify
from services import crm_service, pdm_service, hr_service
from middleware.jwt_auth import jwt_required

integration_bp = Blueprint('integration', __name__)


# ========== CRM客户数据集成 ==========

@integration_bp.route('/integration/customers', methods=['GET'])
@jwt_required
def get_crm_customers():
    """从CRM系统获取客户列表 - 需要认证"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    result = crm_service.get_customers(keyword=keyword, page=page, page_size=page_size)
    return jsonify(result)


@integration_bp.route('/integration/customers/<int:customer_id>', methods=['GET'])
@jwt_required
def get_crm_customer_detail(customer_id):
    """从CRM系统获取客户详情 - 需要认证"""
    result = crm_service.get_customer_by_id(customer_id)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


@integration_bp.route('/integration/customers/search', methods=['POST'])
@jwt_required
def search_crm_customers():
    """搜索CRM客户 - 需要认证"""
    data = request.get_json() or {}
    keyword = data.get('keyword', '')
    page = data.get('page', 1)
    page_size = data.get('page_size', 20)

    result = crm_service.search_customers(keyword=keyword, page=page, page_size=page_size)
    return jsonify(result)


# ========== PDM产品数据集成 ==========

@integration_bp.route('/integration/products', methods=['GET'])
@jwt_required
def get_pdm_products():
    """从PDM系统获取产品列表 - 需要认证"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    result = pdm_service.get_products(keyword=keyword, page=page, page_size=page_size)
    return jsonify(result)


@integration_bp.route('/integration/products/<int:product_id>', methods=['GET'])
@jwt_required
def get_pdm_product_detail(product_id):
    """从PDM系统获取产品详情 - 需要认证"""
    result = pdm_service.get_product_by_id(product_id)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


@integration_bp.route('/integration/products/by-code/<product_code>', methods=['GET'])
@jwt_required
def get_pdm_product_by_code(product_code):
    """根据产品编码获取产品信息 - 需要认证"""
    result = pdm_service.get_product_by_code(product_code)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


# ========== HR人员数据集成 ==========

@integration_bp.route('/integration/hr/warehouse-staff', methods=['GET'])
@jwt_required
def get_hr_warehouse_staff():
    """获取仓库人员列表（来自HR系统） - 需要认证"""
    search = request.args.get('search', '')
    result = hr_service.get_warehouse_staff(search=search)
    return jsonify(result)


@integration_bp.route('/integration/hr/employees/<int:employee_id>', methods=['GET'])
@jwt_required
def get_hr_employee_detail(employee_id):
    """获取员工详情 - 需要认证"""
    result = hr_service.get_employee(employee_id)
    return jsonify(result)


# ========== 健康检查 ==========

@integration_bp.route('/integration/health', methods=['GET'])
def check_integrations_health():
    """检查所有跨系统集成的健康状态"""
    crm_healthy = crm_service.check_crm_health()
    pdm_healthy = pdm_service.check_pdm_health()
    hr_healthy = hr_service.check_hr_health()

    return jsonify({
        'success': True,
        'data': {
            'integrations': {
                'crm': {
                    'status': 'healthy' if crm_healthy else 'unavailable',
                },
                'pdm': {
                    'status': 'healthy' if pdm_healthy else 'unavailable',
                },
                'hr': {
                    'status': 'healthy' if hr_healthy else 'unavailable',
                }
            }
        }
    })
