# routes/integration_routes.py
"""
跨系统集成路由
提供对PDM、CRM、SCM等子系统的数据访问
"""
from flask import Blueprint, request, jsonify
from services import pdm_service, crm_service, scm_service
import sys
import os

# Add shared module to path for JWT verification
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', '..'))
from shared.auth import verify_token

integration_bp = Blueprint('integration', __name__)


@integration_bp.before_request
def check_auth():
    """JWT认证检查（排除健康检查路由）"""
    if request.method == 'OPTIONS':
        return None

    # 健康检查路由不需要认证
    if request.path.endswith('/health'):
        return None

    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        if payload:
            request.current_user_id = payload.get('user_id')
            request.current_user_role = payload.get('role')
            return None

    # 回退检查 User-ID header
    user_id = request.headers.get('User-ID')
    if user_id:
        request.current_user_id = user_id
        request.current_user_role = request.headers.get('User-Role')
        return None

    return jsonify({"error": "未授权：请先登录"}), 401


# ========== PDM产品数据集成 ==========

@integration_bp.route('/products', methods=['GET'])
def get_pdm_products():
    """从PDM系统获取产品列表"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    result = pdm_service.get_products(keyword=keyword, page=page, page_size=page_size)
    return jsonify(result)


@integration_bp.route('/products/<int:product_id>', methods=['GET'])
def get_pdm_product_detail(product_id):
    """从PDM系统获取产品详情"""
    result = pdm_service.get_product_by_id(product_id)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


@integration_bp.route('/products/by-code/<product_code>', methods=['GET'])
def get_pdm_product_by_code(product_code):
    """根据产品编码获取产品信息"""
    result = pdm_service.get_product_by_code(product_code)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


@integration_bp.route('/products/<int:product_id>/bom', methods=['GET'])
def get_product_bom(product_id):
    """获取产品BOM物料清单"""
    result = pdm_service.get_product_bom(product_id)
    return jsonify(result)


# ========== CRM客户数据集成 ==========

@integration_bp.route('/customers', methods=['GET'])
def get_crm_customers():
    """从CRM系统获取客户列表"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    result = crm_service.get_customers(keyword=keyword, page=page, page_size=page_size)
    return jsonify(result)


@integration_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_crm_customer_detail(customer_id):
    """从CRM系统获取客户详情"""
    result = crm_service.get_customer_by_id(customer_id)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


@integration_bp.route('/customers/<int:customer_id>/contacts', methods=['GET'])
def get_customer_contacts(customer_id):
    """获取客户联系人列表"""
    result = crm_service.get_customer_contacts(customer_id)
    return jsonify(result)


# ========== SCM库存数据集成 ==========

@integration_bp.route('/inventory', methods=['GET'])
def get_scm_inventory():
    """从SCM系统获取库存物料列表"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    result = scm_service.get_inventory_items(keyword=keyword, page=page, page_size=page_size)
    return jsonify(result)


@integration_bp.route('/inventory/by-code/<material_code>', methods=['GET'])
def get_inventory_by_code(material_code):
    """根据物料编码获取库存信息"""
    result = scm_service.get_inventory_by_material_code(material_code)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


@integration_bp.route('/inventory/check-stock', methods=['GET'])
def check_stock_availability():
    """检查物料库存是否充足"""
    material_code = request.args.get('material_code', '')
    quantity = float(request.args.get('quantity', 0))

    if not material_code or quantity <= 0:
        return jsonify({
            'success': False,
            'error': '请提供物料编码和有效数量'
        }), 400

    result = scm_service.check_stock_availability(material_code, quantity)
    return jsonify(result)


@integration_bp.route('/inventory/requests', methods=['POST'])
def create_stock_request():
    """创建库存请求"""
    data = request.get_json() or {}
    material_code = data.get('material_code', '')
    quantity = data.get('quantity', 0)
    requester = data.get('requester', '')
    reason = data.get('reason', '采购需求')

    if not material_code or not quantity or not requester:
        return jsonify({
            'success': False,
            'error': '请提供完整的请求信息'
        }), 400

    result = scm_service.create_stock_request(material_code, quantity, requester, reason)
    return jsonify(result)


# ========== 健康检查 ==========

@integration_bp.route('/health', methods=['GET'])
def check_integrations_health():
    """检查所有跨系统集成的健康状态"""
    pdm_healthy = pdm_service.check_pdm_health()
    crm_healthy = crm_service.check_crm_health()
    scm_healthy = scm_service.check_scm_health()

    return jsonify({
        'success': True,
        'data': {
            'integrations': {
                'pdm': {
                    'status': 'healthy' if pdm_healthy else 'unavailable',
                    'url': pdm_service.get_pdm_base_url()
                },
                'crm': {
                    'status': 'healthy' if crm_healthy else 'unavailable',
                    'url': crm_service.get_crm_base_url()
                },
                'scm': {
                    'status': 'healthy' if scm_healthy else 'unavailable',
                    'url': scm_service.get_scm_base_url()
                }
            }
        }
    })


# 蓝图列表（供自动注册使用）
BLUEPRINTS = [integration_bp]
URL_PREFIX = '/api/v1/integration'
