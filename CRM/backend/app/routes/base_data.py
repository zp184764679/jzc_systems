from flask import Blueprint, jsonify, request
from app import db
from app.models.base_data import (
    SettlementMethod, ShippingMethod, OrderMethod,
    Currency, OrderStatus, ProcessType, Warehouse
)
from sqlalchemy import or_

bp = Blueprint('base_data', __name__, url_prefix='/api/base')


# ========== 通用CRUD函数 ==========

def get_list(model, search='', active_only=True):
    """通用获取列表"""
    query = model.query
    if active_only:
        query = query.filter(model.is_active == True)
    if search:
        query = query.filter(or_(
            model.code.ilike(f'%{search}%'),
            model.name.ilike(f'%{search}%')
        ))
    items = query.order_by(model.sort_order, model.code).all()
    return jsonify({
        'success': True,
        'data': [item.to_dict() for item in items],
        'total': len(items)
    })


def create_item(model, model_name):
    """通用创建"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code or not name:
        return jsonify({'success': False, 'error': '编码和名称不能为空'}), 400

    existing = model.query.filter_by(code=code).first()
    if existing:
        return jsonify({'success': False, 'error': f'编码 {code} 已存在'}), 400

    item = model(
        code=code,
        name=name,
        description=data.get('description', ''),
        is_active=data.get('is_active', True),
        sort_order=data.get('sort_order', 0)
    )

    # Handle model-specific fields
    if hasattr(item, 'symbol') and 'symbol' in data:
        item.symbol = data['symbol']
    if hasattr(item, 'exchange_rate') and 'exchange_rate' in data:
        item.exchange_rate = data['exchange_rate']
    if hasattr(item, 'color') and 'color' in data:
        item.color = data['color']
    if hasattr(item, 'address') and 'address' in data:
        item.address = data['address']

    db.session.add(item)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': item.to_dict(),
        'message': f'{model_name}创建成功'
    }), 201


def update_item(model, item_id, model_name):
    """通用更新"""
    item = model.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'error': f'{model_name}不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '无效的请求数据'}), 400

    if 'code' in data and data['code'] != item.code:
        existing = model.query.filter_by(code=data['code']).first()
        if existing:
            return jsonify({'success': False, 'error': f'编码 {data["code"]} 已存在'}), 400
        item.code = data['code']

    if 'name' in data:
        item.name = data['name']
    if 'description' in data:
        item.description = data['description']
    if 'is_active' in data:
        item.is_active = data['is_active']
    if 'sort_order' in data:
        item.sort_order = data['sort_order']

    # Handle model-specific fields
    if hasattr(item, 'symbol') and 'symbol' in data:
        item.symbol = data['symbol']
    if hasattr(item, 'exchange_rate') and 'exchange_rate' in data:
        item.exchange_rate = data['exchange_rate']
    if hasattr(item, 'color') and 'color' in data:
        item.color = data['color']
    if hasattr(item, 'address') and 'address' in data:
        item.address = data['address']

    db.session.commit()
    return jsonify({
        'success': True,
        'data': item.to_dict(),
        'message': f'{model_name}更新成功'
    })


def delete_item(model, item_id, model_name):
    """通用软删除"""
    item = model.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'error': f'{model_name}不存在'}), 404

    item.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': f'{model_name}已禁用'})


# ========== 结算方式 ==========

@bp.route('/settlement-methods', methods=['GET'])
def get_settlement_methods():
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    return get_list(SettlementMethod, search, active_only)


@bp.route('/settlement-methods', methods=['POST'])
def create_settlement_method():
    return create_item(SettlementMethod, '结算方式')


@bp.route('/settlement-methods/<int:item_id>', methods=['PUT'])
def update_settlement_method(item_id):
    return update_item(SettlementMethod, item_id, '结算方式')


@bp.route('/settlement-methods/<int:item_id>', methods=['DELETE'])
def delete_settlement_method(item_id):
    return delete_item(SettlementMethod, item_id, '结算方式')


# ========== 出货方式 ==========

@bp.route('/shipping-methods', methods=['GET'])
def get_shipping_methods():
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    return get_list(ShippingMethod, search, active_only)


@bp.route('/shipping-methods', methods=['POST'])
def create_shipping_method():
    return create_item(ShippingMethod, '出货方式')


@bp.route('/shipping-methods/<int:item_id>', methods=['PUT'])
def update_shipping_method(item_id):
    return update_item(ShippingMethod, item_id, '出货方式')


@bp.route('/shipping-methods/<int:item_id>', methods=['DELETE'])
def delete_shipping_method(item_id):
    return delete_item(ShippingMethod, item_id, '出货方式')


# ========== 接单方式 ==========

@bp.route('/order-methods', methods=['GET'])
def get_order_methods():
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    return get_list(OrderMethod, search, active_only)


@bp.route('/order-methods', methods=['POST'])
def create_order_method():
    return create_item(OrderMethod, '接单方式')


@bp.route('/order-methods/<int:item_id>', methods=['PUT'])
def update_order_method(item_id):
    return update_item(OrderMethod, item_id, '接单方式')


@bp.route('/order-methods/<int:item_id>', methods=['DELETE'])
def delete_order_method(item_id):
    return delete_item(OrderMethod, item_id, '接单方式')


# ========== 币种 ==========

@bp.route('/currencies', methods=['GET'])
def get_currencies():
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    return get_list(Currency, search, active_only)


@bp.route('/currencies', methods=['POST'])
def create_currency():
    return create_item(Currency, '币种')


@bp.route('/currencies/<int:item_id>', methods=['PUT'])
def update_currency(item_id):
    return update_item(Currency, item_id, '币种')


@bp.route('/currencies/<int:item_id>', methods=['DELETE'])
def delete_currency(item_id):
    return delete_item(Currency, item_id, '币种')


# ========== 订单状态 ==========

@bp.route('/order-statuses', methods=['GET'])
def get_order_statuses():
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    return get_list(OrderStatus, search, active_only)


@bp.route('/order-statuses', methods=['POST'])
def create_order_status():
    return create_item(OrderStatus, '订单状态')


@bp.route('/order-statuses/<int:item_id>', methods=['PUT'])
def update_order_status(item_id):
    return update_item(OrderStatus, item_id, '订单状态')


@bp.route('/order-statuses/<int:item_id>', methods=['DELETE'])
def delete_order_status(item_id):
    return delete_item(OrderStatus, item_id, '订单状态')


# ========== 加工类型 ==========

@bp.route('/process-types', methods=['GET'])
def get_process_types():
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    return get_list(ProcessType, search, active_only)


@bp.route('/process-types', methods=['POST'])
def create_process_type():
    return create_item(ProcessType, '加工类型')


@bp.route('/process-types/<int:item_id>', methods=['PUT'])
def update_process_type(item_id):
    return update_item(ProcessType, item_id, '加工类型')


@bp.route('/process-types/<int:item_id>', methods=['DELETE'])
def delete_process_type(item_id):
    return delete_item(ProcessType, item_id, '加工类型')


# ========== 仓库 ==========

@bp.route('/warehouses', methods=['GET'])
def get_warehouses():
    search = request.args.get('search', '')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    return get_list(Warehouse, search, active_only)


@bp.route('/warehouses', methods=['POST'])
def create_warehouse():
    return create_item(Warehouse, '仓库')


@bp.route('/warehouses/<int:item_id>', methods=['PUT'])
def update_warehouse(item_id):
    return update_item(Warehouse, item_id, '仓库')


@bp.route('/warehouses/<int:item_id>', methods=['DELETE'])
def delete_warehouse(item_id):
    return delete_item(Warehouse, item_id, '仓库')
