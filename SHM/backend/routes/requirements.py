"""
SHM 交货要求管理路由
安全修复：添加认证装饰器
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models.shipment import DeliveryRequirement
from middleware.jwt_auth import jwt_required

requirements_bp = Blueprint('requirements', __name__)


@requirements_bp.route('/requirements', methods=['GET'])
def get_requirements():
    """获取交货要求列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    customer_name = request.args.get('customer_name')
    customer_id = request.args.get('customer_id')

    query = DeliveryRequirement.query

    if customer_name:
        query = query.filter(DeliveryRequirement.customer_name.like(f'%{customer_name}%'))
    if customer_id:
        query = query.filter(DeliveryRequirement.customer_id == customer_id)

    query = query.order_by(DeliveryRequirement.created_at.desc())

    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        'success': True,
        'data': [req.to_dict() for req in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size
    })


@requirements_bp.route('/requirements', methods=['POST'])
@jwt_required
def create_requirement():
    """创建交货要求 - 需要认证"""
    data = request.get_json()

    requirement = DeliveryRequirement(
        customer_id=data.get('customer_id'),
        customer_name=data.get('customer_name'),
        packaging_type=data.get('packaging_type'),
        packaging_material=data.get('packaging_material'),
        labeling_requirement=data.get('labeling_requirement'),
        delivery_time_window=data.get('delivery_time_window'),
        special_instructions=data.get('special_instructions'),
        quality_cert_required=data.get('quality_cert_required', False),
        packing_list_format=data.get('packing_list_format'),
        invoice_requirement=data.get('invoice_requirement'),
        remark=data.get('remark')
    )

    db.session.add(requirement)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '交货要求创建成功',
        'data': requirement.to_dict()
    })


@requirements_bp.route('/requirements/customer/<customer_id>', methods=['GET'])
def get_customer_requirements(customer_id):
    """获取客户的交货要求"""
    requirement = DeliveryRequirement.query.filter_by(
        customer_id=customer_id
    ).order_by(DeliveryRequirement.updated_at.desc()).first()

    if requirement:
        return jsonify({
            'success': True,
            'data': requirement.to_dict()
        })
    else:
        return jsonify({
            'success': True,
            'data': None
        })


@requirements_bp.route('/requirements/<int:id>', methods=['GET'])
def get_requirement(id):
    """获取交货要求详情"""
    requirement = DeliveryRequirement.query.get_or_404(id)
    return jsonify({
        'success': True,
        'data': requirement.to_dict()
    })


@requirements_bp.route('/requirements/<int:id>', methods=['PUT'])
@jwt_required
def update_requirement(id):
    """更新交货要求 - 需要认证"""
    requirement = DeliveryRequirement.query.get_or_404(id)
    data = request.get_json()

    if 'customer_id' in data:
        requirement.customer_id = data['customer_id']
    if 'customer_name' in data:
        requirement.customer_name = data['customer_name']
    if 'packaging_type' in data:
        requirement.packaging_type = data['packaging_type']
    if 'packaging_material' in data:
        requirement.packaging_material = data['packaging_material']
    if 'labeling_requirement' in data:
        requirement.labeling_requirement = data['labeling_requirement']
    if 'delivery_time_window' in data:
        requirement.delivery_time_window = data['delivery_time_window']
    if 'special_instructions' in data:
        requirement.special_instructions = data['special_instructions']
    if 'quality_cert_required' in data:
        requirement.quality_cert_required = data['quality_cert_required']
    if 'packing_list_format' in data:
        requirement.packing_list_format = data['packing_list_format']
    if 'invoice_requirement' in data:
        requirement.invoice_requirement = data['invoice_requirement']
    if 'remark' in data:
        requirement.remark = data['remark']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '交货要求更新成功',
        'data': requirement.to_dict()
    })


@requirements_bp.route('/requirements/<int:id>', methods=['DELETE'])
@jwt_required
def delete_requirement(id):
    """删除交货要求 - 需要认证"""
    requirement = DeliveryRequirement.query.get_or_404(id)

    db.session.delete(requirement)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '交货要求删除成功'
    })
