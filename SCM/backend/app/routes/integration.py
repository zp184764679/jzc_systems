# app/routes/integration.py
"""
跨系统集成路由
"""
from flask import Blueprint, request, jsonify
from ..services import pdm_service, hr_service

bp = Blueprint('integration', __name__, url_prefix='/api/integration')


# ========== PDM产品数据集成 ==========

@bp.route('/products', methods=['GET'])
def get_pdm_products():
    """从PDM系统获取产品列表"""
    keyword = request.args.get('keyword', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    result = pdm_service.get_products(keyword=keyword, page=page, page_size=page_size)
    return jsonify(result)


@bp.route('/products/<int:product_id>', methods=['GET'])
def get_pdm_product_detail(product_id):
    """从PDM系统获取产品详情"""
    result = pdm_service.get_product_by_id(product_id)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


@bp.route('/products/by-code/<product_code>', methods=['GET'])
def get_pdm_product_by_code(product_code):
    """根据产品编码获取产品信息"""
    result = pdm_service.get_product_by_code(product_code)
    if not result.get('success', False):
        return jsonify(result), 404
    return jsonify(result)


# ========== HR员工数据集成 ==========

@bp.route('/hr/procurement-staff', methods=['GET'])
def get_procurement_staff():
    """获取采购人员列表（来自HR系统）"""
    search = request.args.get('search', '')
    result = hr_service.get_procurement_staff(search=search)
    return jsonify(result)


@bp.route('/hr/employees/<int:employee_id>', methods=['GET'])
def get_employee_detail(employee_id):
    """获取员工详情"""
    result = hr_service.get_employee(employee_id)
    return jsonify(result)


# ========== 健康检查 ==========

@bp.route('/health', methods=['GET'])
def check_integrations_health():
    """检查所有跨系统集成的健康状态"""
    pdm_healthy = pdm_service.check_pdm_health()
    hr_healthy = hr_service.check_hr_health()

    return jsonify({
        'success': True,
        'data': {
            'integrations': {
                'pdm': {
                    'status': 'healthy' if pdm_healthy else 'unavailable',
                },
                'hr': {
                    'status': 'healthy' if hr_healthy else 'unavailable',
                }
            }
        }
    })
