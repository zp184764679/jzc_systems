from flask import Blueprint, jsonify, request
from extensions import db
from models.base_data import ShipmentStatus, ShippingMethod, PackagingType, PackagingMaterial, Warehouse, UnitOfMeasure
from sqlalchemy import or_

bp = Blueprint('base_data', __name__, url_prefix='/api/base')


def get_list(model, search='', active_only=True):
    query = model.query
    if active_only:
        query = query.filter(model.is_active == True)
    if search:
        query = query.filter(or_(model.code.ilike(f'%{search}%'), model.name.ilike(f'%{search}%')))
    items = query.order_by(model.sort_order, model.code).all()
    return jsonify({'success': True, 'data': [item.to_dict() for item in items], 'total': len(items)})


def create_item(model, model_name):
    data = request.get_json()
    if not data or not data.get('code') or not data.get('name'):
        return jsonify({'success': False, 'error': '编码和名称不能为空'}), 400
    if model.query.filter_by(code=data['code']).first():
        return jsonify({'success': False, 'error': '编码已存在'}), 400
    item = model(code=data['code'], name=data['name'], description=data.get('description', ''),
                 is_active=data.get('is_active', True), sort_order=data.get('sort_order', 0))
    for attr in ['color', 'symbol', 'address']:
        if hasattr(item, attr) and attr in data:
            setattr(item, attr, data[attr])
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'data': item.to_dict(), 'message': f'{model_name}创建成功'}), 201


def update_item(model, item_id, model_name):
    item = model.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'error': f'{model_name}不存在'}), 404
    data = request.get_json()
    if 'code' in data and data['code'] != item.code:
        if model.query.filter_by(code=data['code']).first():
            return jsonify({'success': False, 'error': '编码已存在'}), 400
        item.code = data['code']
    for attr in ['name', 'description', 'is_active', 'sort_order', 'color', 'symbol', 'address']:
        if attr in data:
            setattr(item, attr, data[attr])
    db.session.commit()
    return jsonify({'success': True, 'data': item.to_dict(), 'message': f'{model_name}更新成功'})


def delete_item(model, item_id, model_name):
    item = model.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'error': f'{model_name}不存在'}), 404
    item.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': f'{model_name}已禁用'})


# Shipment Statuses
@bp.route('/shipment-statuses', methods=['GET'])
def get_shipment_statuses():
    return get_list(ShipmentStatus, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/shipment-statuses', methods=['POST'])
def create_shipment_status():
    return create_item(ShipmentStatus, '出货状态')

@bp.route('/shipment-statuses/<int:item_id>', methods=['PUT'])
def update_shipment_status(item_id):
    return update_item(ShipmentStatus, item_id, '出货状态')

@bp.route('/shipment-statuses/<int:item_id>', methods=['DELETE'])
def delete_shipment_status(item_id):
    return delete_item(ShipmentStatus, item_id, '出货状态')


# Shipping Methods
@bp.route('/shipping-methods', methods=['GET'])
def get_shipping_methods():
    return get_list(ShippingMethod, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/shipping-methods', methods=['POST'])
def create_shipping_method():
    return create_item(ShippingMethod, '运输方式')

@bp.route('/shipping-methods/<int:item_id>', methods=['PUT'])
def update_shipping_method(item_id):
    return update_item(ShippingMethod, item_id, '运输方式')

@bp.route('/shipping-methods/<int:item_id>', methods=['DELETE'])
def delete_shipping_method(item_id):
    return delete_item(ShippingMethod, item_id, '运输方式')


# Packaging Types
@bp.route('/packaging-types', methods=['GET'])
def get_packaging_types():
    return get_list(PackagingType, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/packaging-types', methods=['POST'])
def create_packaging_type():
    return create_item(PackagingType, '包装类型')

@bp.route('/packaging-types/<int:item_id>', methods=['PUT'])
def update_packaging_type(item_id):
    return update_item(PackagingType, item_id, '包装类型')

@bp.route('/packaging-types/<int:item_id>', methods=['DELETE'])
def delete_packaging_type(item_id):
    return delete_item(PackagingType, item_id, '包装类型')


# Packaging Materials
@bp.route('/packaging-materials', methods=['GET'])
def get_packaging_materials():
    return get_list(PackagingMaterial, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/packaging-materials', methods=['POST'])
def create_packaging_material():
    return create_item(PackagingMaterial, '包装材料')

@bp.route('/packaging-materials/<int:item_id>', methods=['PUT'])
def update_packaging_material(item_id):
    return update_item(PackagingMaterial, item_id, '包装材料')

@bp.route('/packaging-materials/<int:item_id>', methods=['DELETE'])
def delete_packaging_material(item_id):
    return delete_item(PackagingMaterial, item_id, '包装材料')


# Warehouses
@bp.route('/warehouses', methods=['GET'])
def get_warehouses():
    return get_list(Warehouse, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/warehouses', methods=['POST'])
def create_warehouse():
    return create_item(Warehouse, '仓库')

@bp.route('/warehouses/<int:item_id>', methods=['PUT'])
def update_warehouse(item_id):
    return update_item(Warehouse, item_id, '仓库')

@bp.route('/warehouses/<int:item_id>', methods=['DELETE'])
def delete_warehouse(item_id):
    return delete_item(Warehouse, item_id, '仓库')


# Units of Measure
@bp.route('/units-of-measure', methods=['GET'])
def get_units_of_measure():
    return get_list(UnitOfMeasure, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/units-of-measure', methods=['POST'])
def create_unit_of_measure():
    return create_item(UnitOfMeasure, '计量单位')

@bp.route('/units-of-measure/<int:item_id>', methods=['PUT'])
def update_unit_of_measure(item_id):
    return update_item(UnitOfMeasure, item_id, '计量单位')

@bp.route('/units-of-measure/<int:item_id>', methods=['DELETE'])
def delete_unit_of_measure(item_id):
    return delete_item(UnitOfMeasure, item_id, '计量单位')
