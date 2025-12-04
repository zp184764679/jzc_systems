from flask import Blueprint, jsonify, request
from app import db
from app.models.base_data import TransactionType, Location, WarehouseBin, UnitOfMeasure
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
        return jsonify({'success': False, 'error': f'编码已存在'}), 400
    item = model(code=data['code'], name=data['name'], description=data.get('description', ''),
                 is_active=data.get('is_active', True), sort_order=data.get('sort_order', 0))
    for attr in ['address', 'symbol', 'location_id', 'zone']:
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
    for attr in ['name', 'description', 'is_active', 'sort_order', 'address', 'symbol', 'location_id', 'zone']:
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


# Transaction Types
@bp.route('/transaction-types', methods=['GET'])
def get_transaction_types():
    return get_list(TransactionType, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/transaction-types', methods=['POST'])
def create_transaction_type():
    return create_item(TransactionType, '交易类型')

@bp.route('/transaction-types/<int:item_id>', methods=['PUT'])
def update_transaction_type(item_id):
    return update_item(TransactionType, item_id, '交易类型')

@bp.route('/transaction-types/<int:item_id>', methods=['DELETE'])
def delete_transaction_type(item_id):
    return delete_item(TransactionType, item_id, '交易类型')


# Locations
@bp.route('/locations', methods=['GET'])
def get_locations():
    return get_list(Location, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/locations', methods=['POST'])
def create_location():
    return create_item(Location, '地点')

@bp.route('/locations/<int:item_id>', methods=['PUT'])
def update_location(item_id):
    return update_item(Location, item_id, '地点')

@bp.route('/locations/<int:item_id>', methods=['DELETE'])
def delete_location(item_id):
    return delete_item(Location, item_id, '地点')


# Warehouse Bins
@bp.route('/warehouse-bins', methods=['GET'])
def get_warehouse_bins():
    return get_list(WarehouseBin, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/warehouse-bins', methods=['POST'])
def create_warehouse_bin():
    return create_item(WarehouseBin, '仓位')

@bp.route('/warehouse-bins/<int:item_id>', methods=['PUT'])
def update_warehouse_bin(item_id):
    return update_item(WarehouseBin, item_id, '仓位')

@bp.route('/warehouse-bins/<int:item_id>', methods=['DELETE'])
def delete_warehouse_bin(item_id):
    return delete_item(WarehouseBin, item_id, '仓位')


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
