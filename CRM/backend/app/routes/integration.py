# 跨系统集成路由 - CRM
from flask import Blueprint, jsonify, request
from app.services import hr_service

bp = Blueprint('integration', __name__, url_prefix='/api/integration')


@bp.route('/hr/sales-staff', methods=['GET'])
def get_sales_staff():
    """获取销售人员列表（来自HR系统）"""
    search = request.args.get('search', '')
    result = hr_service.get_sales_staff(search=search)
    return jsonify(result)


@bp.route('/hr/employees/<int:employee_id>', methods=['GET'])
def get_employee_detail(employee_id):
    """获取员工详情"""
    result = hr_service.get_employee(employee_id)
    return jsonify(result)


@bp.route('/health', methods=['GET'])
def check_integrations():
    """检查集成服务健康状态"""
    return jsonify({
        'success': True,
        'data': {
            'hr': hr_service.check_hr_health()
        }
    })
