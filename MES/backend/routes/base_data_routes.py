from flask import Blueprint, jsonify, request
from database import db
from models.base_data import WorkOrderStatus, SourceType, InspectionType, InspectionResult, DispositionType, ProductionLine, WorkCenter
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
    for attr in ['color', 'location', 'capacity', 'production_line_id']:
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
    for attr in ['name', 'description', 'is_active', 'sort_order', 'color', 'location', 'capacity', 'production_line_id']:
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


# Work Order Statuses
@bp.route('/work-order-statuses', methods=['GET'])
def get_work_order_statuses():
    return get_list(WorkOrderStatus, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/work-order-statuses', methods=['POST'])
def create_work_order_status():
    return create_item(WorkOrderStatus, '工单状态')

@bp.route('/work-order-statuses/<int:item_id>', methods=['PUT'])
def update_work_order_status(item_id):
    return update_item(WorkOrderStatus, item_id, '工单状态')

@bp.route('/work-order-statuses/<int:item_id>', methods=['DELETE'])
def delete_work_order_status(item_id):
    return delete_item(WorkOrderStatus, item_id, '工单状态')


# Source Types
@bp.route('/source-types', methods=['GET'])
def get_source_types():
    return get_list(SourceType, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/source-types', methods=['POST'])
def create_source_type():
    return create_item(SourceType, '来源类型')

@bp.route('/source-types/<int:item_id>', methods=['PUT'])
def update_source_type(item_id):
    return update_item(SourceType, item_id, '来源类型')

@bp.route('/source-types/<int:item_id>', methods=['DELETE'])
def delete_source_type(item_id):
    return delete_item(SourceType, item_id, '来源类型')


# Inspection Types
@bp.route('/inspection-types', methods=['GET'])
def get_inspection_types():
    return get_list(InspectionType, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/inspection-types', methods=['POST'])
def create_inspection_type():
    return create_item(InspectionType, '检验类型')

@bp.route('/inspection-types/<int:item_id>', methods=['PUT'])
def update_inspection_type(item_id):
    return update_item(InspectionType, item_id, '检验类型')

@bp.route('/inspection-types/<int:item_id>', methods=['DELETE'])
def delete_inspection_type(item_id):
    return delete_item(InspectionType, item_id, '检验类型')


# Inspection Results
@bp.route('/inspection-results', methods=['GET'])
def get_inspection_results():
    return get_list(InspectionResult, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/inspection-results', methods=['POST'])
def create_inspection_result():
    return create_item(InspectionResult, '检验结果')

@bp.route('/inspection-results/<int:item_id>', methods=['PUT'])
def update_inspection_result(item_id):
    return update_item(InspectionResult, item_id, '检验结果')

@bp.route('/inspection-results/<int:item_id>', methods=['DELETE'])
def delete_inspection_result(item_id):
    return delete_item(InspectionResult, item_id, '检验结果')


# Disposition Types
@bp.route('/disposition-types', methods=['GET'])
def get_disposition_types():
    return get_list(DispositionType, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/disposition-types', methods=['POST'])
def create_disposition_type():
    return create_item(DispositionType, '处置类型')

@bp.route('/disposition-types/<int:item_id>', methods=['PUT'])
def update_disposition_type(item_id):
    return update_item(DispositionType, item_id, '处置类型')

@bp.route('/disposition-types/<int:item_id>', methods=['DELETE'])
def delete_disposition_type(item_id):
    return delete_item(DispositionType, item_id, '处置类型')


# Production Lines
@bp.route('/production-lines', methods=['GET'])
def get_production_lines():
    return get_list(ProductionLine, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/production-lines', methods=['POST'])
def create_production_line():
    return create_item(ProductionLine, '生产线')

@bp.route('/production-lines/<int:item_id>', methods=['PUT'])
def update_production_line(item_id):
    return update_item(ProductionLine, item_id, '生产线')

@bp.route('/production-lines/<int:item_id>', methods=['DELETE'])
def delete_production_line(item_id):
    return delete_item(ProductionLine, item_id, '生产线')


# Work Centers
@bp.route('/work-centers', methods=['GET'])
def get_work_centers():
    return get_list(WorkCenter, request.args.get('search', ''), request.args.get('active_only', 'true').lower() == 'true')

@bp.route('/work-centers', methods=['POST'])
def create_work_center():
    return create_item(WorkCenter, '工作中心')

@bp.route('/work-centers/<int:item_id>', methods=['PUT'])
def update_work_center(item_id):
    return update_item(WorkCenter, item_id, '工作中心')

@bp.route('/work-centers/<int:item_id>', methods=['DELETE'])
def delete_work_center(item_id):
    return delete_item(WorkCenter, item_id, '工作中心')
