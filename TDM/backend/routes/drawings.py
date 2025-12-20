"""
图纸管理 API - 与报价系统共享数据
"""
from flask import Blueprint, request, jsonify
from models import db
from models.shared_drawing import Drawing

drawings_bp = Blueprint('drawings', __name__)


@drawings_bp.route('/drawings', methods=['GET'])
def list_drawings():
    """获取图纸列表"""
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 筛选参数
    customer_name = request.args.get('customer_name', '')
    material = request.args.get('material', '')
    ocr_status = request.args.get('ocr_status', '')
    search = request.args.get('search', '')

    # 构建查询
    query = Drawing.query

    if customer_name:
        query = query.filter(Drawing.customer_name.contains(customer_name))

    if material:
        query = query.filter(Drawing.material.contains(material))

    if ocr_status:
        query = query.filter(Drawing.ocr_status == ocr_status)

    if search:
        query = query.filter(
            db.or_(
                Drawing.drawing_number.contains(search),
                Drawing.product_name.contains(search),
                Drawing.customer_name.contains(search)
            )
        )

    # 排序（最新的在前）
    query = query.order_by(Drawing.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data': [d.to_dict() for d in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })


@drawings_bp.route('/drawings/<int:drawing_id>', methods=['GET'])
def get_drawing(drawing_id):
    """获取图纸详情"""
    drawing = Drawing.query.get(drawing_id)

    if not drawing:
        return jsonify({'success': False, 'error': '图纸不存在'}), 404

    return jsonify({
        'success': True,
        'data': drawing.to_dict()
    })


@drawings_bp.route('/drawings/number/<drawing_number>', methods=['GET'])
def get_drawing_by_number(drawing_number):
    """通过图号获取图纸"""
    drawing = Drawing.query.filter(Drawing.drawing_number == drawing_number).first()

    if not drawing:
        return jsonify({'success': False, 'error': f'图号 {drawing_number} 不存在'}), 404

    return jsonify({
        'success': True,
        'data': drawing.to_dict()
    })


@drawings_bp.route('/drawings/<int:drawing_id>', methods=['PUT'])
def update_drawing(drawing_id):
    """更新图纸信息"""
    drawing = Drawing.query.get(drawing_id)

    if not drawing:
        return jsonify({'success': False, 'error': '图纸不存在'}), 404

    data = request.get_json()

    # 检查图号是否与其他图纸冲突
    if data.get('drawing_number') and data['drawing_number'] != drawing.drawing_number:
        existing = Drawing.query.filter(
            Drawing.drawing_number == data['drawing_number'],
            Drawing.id != drawing_id
        ).first()
        if existing:
            return jsonify({'success': False, 'error': f'图号 {data["drawing_number"]} 已被使用'}), 400

    # 更新字段
    allowed_fields = [
        'drawing_number', 'customer_name', 'product_name', 'customer_part_number',
        'material', 'material_spec', 'outer_diameter', 'length', 'weight',
        'tolerance', 'surface_roughness', 'heat_treatment', 'surface_treatment',
        'special_requirements', 'notes', 'version'
    ]

    for field in allowed_fields:
        if field in data:
            setattr(drawing, field, data[field])

    db.session.commit()

    return jsonify({
        'success': True,
        'data': drawing.to_dict()
    })


@drawings_bp.route('/drawings/<int:drawing_id>', methods=['DELETE'])
def delete_drawing(drawing_id):
    """删除图纸"""
    drawing = Drawing.query.get(drawing_id)

    if not drawing:
        return jsonify({'success': False, 'error': '图纸不存在'}), 404

    drawing_number = drawing.drawing_number
    db.session.delete(drawing)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'图纸 {drawing_number} 已删除'
    })


@drawings_bp.route('/drawings/customers', methods=['GET'])
def list_customers():
    """获取客户列表（从图纸中提取）"""
    customers = db.session.query(Drawing.customer_name).filter(
        Drawing.customer_name.isnot(None)
    ).distinct().all()

    return jsonify({
        'success': True,
        'data': [c[0] for c in customers if c[0]]
    })


@drawings_bp.route('/drawings/materials', methods=['GET'])
def list_materials():
    """获取材质列表（从图纸中提取）"""
    materials = db.session.query(Drawing.material).filter(
        Drawing.material.isnot(None)
    ).distinct().all()

    return jsonify({
        'success': True,
        'data': [m[0] for m in materials if m[0]]
    })


@drawings_bp.route('/drawings/search', methods=['GET'])
def search_drawings():
    """搜索图纸"""
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', 20, type=int)

    if not keyword:
        return jsonify({'success': True, 'data': []})

    drawings = Drawing.query.filter(
        db.or_(
            Drawing.drawing_number.contains(keyword),
            Drawing.product_name.contains(keyword),
            Drawing.customer_name.contains(keyword)
        )
    ).limit(limit).all()

    return jsonify({
        'success': True,
        'data': [d.to_dict() for d in drawings]
    })


@drawings_bp.route('/drawings/statistics', methods=['GET'])
def get_statistics():
    """获取图纸统计"""
    total = Drawing.query.count()

    # 按OCR状态统计
    ocr_stats = db.session.query(
        Drawing.ocr_status,
        db.func.count(Drawing.id)
    ).group_by(Drawing.ocr_status).all()

    # 按客户统计（前10）
    customer_stats = db.session.query(
        Drawing.customer_name,
        db.func.count(Drawing.id)
    ).filter(
        Drawing.customer_name.isnot(None)
    ).group_by(Drawing.customer_name).order_by(
        db.func.count(Drawing.id).desc()
    ).limit(10).all()

    return jsonify({
        'success': True,
        'data': {
            'total': total,
            'by_ocr_status': {status: count for status, count in ocr_stats},
            'by_customer': [{'name': name, 'count': count} for name, count in customer_stats]
        }
    })
