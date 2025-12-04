# 跨系统集成路由
from flask import Blueprint, request, jsonify
from services import pdm_service, scm_service, eam_service, hr_service

integration_bp = Blueprint('integration', __name__)


@integration_bp.route('/pdm/products', methods=['GET'])
def get_pdm_products():
    """从PDM获取产品列表"""
    keyword = request.args.get('keyword', '')
    result = pdm_service.get_products(keyword)
    return jsonify(result)


@integration_bp.route('/pdm/products/<int:product_id>/bom', methods=['GET'])
def get_product_bom(product_id):
    """获取产品BOM"""
    result = pdm_service.get_product_bom(product_id)
    return jsonify(result)


@integration_bp.route('/scm/materials', methods=['GET'])
def get_scm_materials():
    """从SCM获取物料库存"""
    keyword = request.args.get('keyword', '')
    result = scm_service.get_inventory_items(keyword)
    return jsonify(result)


@integration_bp.route('/scm/consume', methods=['POST'])
def consume_material():
    """消耗物料（出库）"""
    data = request.get_json()
    result = scm_service.create_stock_request(
        material_code=data.get('material_code'),
        quantity=data.get('quantity'),
        requester='MES',
        reason=f"工单生产: {data.get('work_order_no', '')}"
    )
    return jsonify(result)


@integration_bp.route('/eam/equipment', methods=['GET'])
def get_equipment():
    """从EAM获取设备列表"""
    result = eam_service.get_equipment_list()
    return jsonify(result)


@integration_bp.route('/eam/equipment/<int:equipment_id>/status', methods=['GET'])
def get_equipment_status(equipment_id):
    """获取设备状态"""
    result = eam_service.get_equipment_status(equipment_id)
    return jsonify(result)


@integration_bp.route('/hr/employees', methods=['GET'])
def get_hr_employees():
    """从HR系统获取员工列表"""
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    result = hr_service.get_employees(search=search, department=department)
    return jsonify(result)


@integration_bp.route('/hr/operators', methods=['GET'])
def get_hr_operators():
    """获取操作员列表（用于生产报工）"""
    department = request.args.get('department', '')
    result = hr_service.get_operators(department=department)
    return jsonify(result)


@integration_bp.route('/hr/employees/<int:employee_id>', methods=['GET'])
def get_hr_employee_detail(employee_id):
    """获取员工详情"""
    result = hr_service.get_employee(employee_id)
    return jsonify(result)


@integration_bp.route('/hr/stats', methods=['GET'])
def get_hr_stats():
    """获取员工统计"""
    result = hr_service.get_employee_stats()
    return jsonify(result)


@integration_bp.route('/health', methods=['GET'])
def check_integrations():
    """检查集成服务健康状态"""
    return jsonify({
        'success': True,
        'data': {
            'pdm': pdm_service.check_pdm_health(),
            'scm': scm_service.check_scm_health(),
            'eam': eam_service.check_eam_health(),
            'hr': hr_service.check_hr_health()
        }
    })
