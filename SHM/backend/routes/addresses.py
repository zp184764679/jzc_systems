"""
SHM 客户地址管理路由
安全修复：添加认证装饰器
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models.shipment import CustomerAddress
from middleware.jwt_auth import jwt_required

addresses_bp = Blueprint('addresses', __name__)


@addresses_bp.route('/addresses', methods=['GET'])
def get_addresses():
    """获取地址列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    customer_name = request.args.get('customer_name')
    customer_id = request.args.get('customer_id')

    query = CustomerAddress.query

    if customer_name:
        query = query.filter(CustomerAddress.customer_name.like(f'%{customer_name}%'))
    if customer_id:
        query = query.filter(CustomerAddress.customer_id == customer_id)

    query = query.order_by(CustomerAddress.is_default.desc(), CustomerAddress.created_at.desc())

    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        'success': True,
        'data': [addr.to_dict() for addr in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size
    })


@addresses_bp.route('/addresses', methods=['POST'])
@jwt_required
def create_address():
    """创建地址 - 需要认证"""
    data = request.get_json()

    # 如果设为默认，取消其他默认地址
    if data.get('is_default'):
        CustomerAddress.query.filter_by(
            customer_id=data.get('customer_id'),
            is_default=True
        ).update({'is_default': False})

    address = CustomerAddress(
        customer_id=data.get('customer_id'),
        customer_name=data.get('customer_name'),
        contact_person=data.get('contact_person'),
        contact_phone=data.get('contact_phone'),
        province=data.get('province'),
        city=data.get('city'),
        district=data.get('district'),
        address=data.get('address'),
        postal_code=data.get('postal_code'),
        is_default=data.get('is_default', False),
        remark=data.get('remark')
    )

    db.session.add(address)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '地址创建成功',
        'data': address.to_dict()
    })


@addresses_bp.route('/addresses/customer/<customer_id>', methods=['GET'])
def get_customer_addresses(customer_id):
    """获取客户的所有地址"""
    addresses = CustomerAddress.query.filter_by(
        customer_id=customer_id
    ).order_by(CustomerAddress.is_default.desc()).all()

    return jsonify({
        'success': True,
        'data': [addr.to_dict() for addr in addresses]
    })


@addresses_bp.route('/addresses/<int:id>', methods=['GET'])
def get_address(id):
    """获取地址详情"""
    address = CustomerAddress.query.get_or_404(id)
    return jsonify({
        'success': True,
        'data': address.to_dict()
    })


@addresses_bp.route('/addresses/<int:id>', methods=['PUT'])
@jwt_required
def update_address(id):
    """更新地址 - 需要认证"""
    address = CustomerAddress.query.get_or_404(id)
    data = request.get_json()

    # 如果设为默认，取消其他默认地址
    if data.get('is_default') and not address.is_default:
        CustomerAddress.query.filter_by(
            customer_id=address.customer_id,
            is_default=True
        ).update({'is_default': False})

    if 'customer_id' in data:
        address.customer_id = data['customer_id']
    if 'customer_name' in data:
        address.customer_name = data['customer_name']
    if 'contact_person' in data:
        address.contact_person = data['contact_person']
    if 'contact_phone' in data:
        address.contact_phone = data['contact_phone']
    if 'province' in data:
        address.province = data['province']
    if 'city' in data:
        address.city = data['city']
    if 'district' in data:
        address.district = data['district']
    if 'address' in data:
        address.address = data['address']
    if 'postal_code' in data:
        address.postal_code = data['postal_code']
    if 'is_default' in data:
        address.is_default = data['is_default']
    if 'remark' in data:
        address.remark = data['remark']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '地址更新成功',
        'data': address.to_dict()
    })


@addresses_bp.route('/addresses/<int:id>', methods=['DELETE'])
@jwt_required
def delete_address(id):
    """删除地址 - 需要认证"""
    address = CustomerAddress.query.get_or_404(id)

    db.session.delete(address)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '地址删除成功'
    })
