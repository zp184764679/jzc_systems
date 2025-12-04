from flask import Blueprint, jsonify, request
from app import db
from app.models.base_data import EquipmentStatus, FactoryLocation, EquipmentGroup, Brand, StoragePlace
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
    for attr in ['address', 'color', 'country', 'factory_location_id', 'building', 'floor', 'area']:
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
    for attr in ['name', 'description', 'is_active', 'sort_order', 'address', 'color', 'country',
                 'factory_location_id', 'building', 'floor', 'area']:
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


# Equipment Statuses
@bp.route('/equipment-statuses', methods=['GET'])
def get_equipment_statuses():
    return get_list(EquipmentStatus, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/equipment-statuses', methods=['POST'])
def create_equipment_status():
    return create_item(EquipmentStatus, '设备状态')

@bp.route('/equipment-statuses/<int:item_id>', methods=['PUT'])
def update_equipment_status(item_id):
    return update_item(EquipmentStatus, item_id, '设备状态')

@bp.route('/equipment-statuses/<int:item_id>', methods=['DELETE'])
def delete_equipment_status(item_id):
    return delete_item(EquipmentStatus, item_id, '设备状态')


# Factory Locations
@bp.route('/factory-locations', methods=['GET'])
def get_factory_locations():
    return get_list(FactoryLocation, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/factory-locations', methods=['POST'])
def create_factory_location():
    return create_item(FactoryLocation, '工厂位置')

@bp.route('/factory-locations/<int:item_id>', methods=['PUT'])
def update_factory_location(item_id):
    return update_item(FactoryLocation, item_id, '工厂位置')

@bp.route('/factory-locations/<int:item_id>', methods=['DELETE'])
def delete_factory_location(item_id):
    return delete_item(FactoryLocation, item_id, '工厂位置')


# Equipment Groups
@bp.route('/equipment-groups', methods=['GET'])
def get_equipment_groups():
    return get_list(EquipmentGroup, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/equipment-groups', methods=['POST'])
def create_equipment_group():
    return create_item(EquipmentGroup, '设备组')

@bp.route('/equipment-groups/<int:item_id>', methods=['PUT'])
def update_equipment_group(item_id):
    return update_item(EquipmentGroup, item_id, '设备组')

@bp.route('/equipment-groups/<int:item_id>', methods=['DELETE'])
def delete_equipment_group(item_id):
    return delete_item(EquipmentGroup, item_id, '设备组')


# Brands
@bp.route('/brands', methods=['GET'])
def get_brands():
    return get_list(Brand, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/brands', methods=['POST'])
def create_brand():
    return create_item(Brand, '品牌')

@bp.route('/brands/<int:item_id>', methods=['PUT'])
def update_brand(item_id):
    return update_item(Brand, item_id, '品牌')

@bp.route('/brands/<int:item_id>', methods=['DELETE'])
def delete_brand(item_id):
    return delete_item(Brand, item_id, '品牌')


# Storage Places
@bp.route('/storage-places', methods=['GET'])
def get_storage_places():
    return get_list(StoragePlace, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/storage-places', methods=['POST'])
def create_storage_place():
    return create_item(StoragePlace, '存放位置')

@bp.route('/storage-places/<int:item_id>', methods=['PUT'])
def update_storage_place(item_id):
    return update_item(StoragePlace, item_id, '存放位置')

@bp.route('/storage-places/<int:item_id>', methods=['DELETE'])
def delete_storage_place(item_id):
    return delete_item(StoragePlace, item_id, '存放位置')
