"""
材料库管理 API - 与报价系统共享数据
"""
from flask import Blueprint, request, jsonify
from models import db
from models.shared_material import Material

materials_bp = Blueprint('materials', __name__)


@materials_bp.route('/materials', methods=['GET'])
def list_materials():
    """获取材料列表"""
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # 筛选参数
    category = request.args.get('category', '')
    search = request.args.get('search', '')

    # 构建查询
    query = Material.query.filter(Material.is_active == True)

    if category:
        query = query.filter(Material.category == category)

    if search:
        query = query.filter(
            db.or_(
                Material.material_code.contains(search),
                Material.material_name.contains(search)
            )
        )

    # 排序
    query = query.order_by(Material.material_code)

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data': [m.to_dict() for m in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })


@materials_bp.route('/materials/categories', methods=['GET'])
def list_categories():
    """获取材料类别列表"""
    categories = db.session.query(Material.category).filter(
        Material.is_active == True,
        Material.category.isnot(None)
    ).distinct().all()

    return jsonify({
        'success': True,
        'data': [cat[0] for cat in categories if cat[0]]
    })


@materials_bp.route('/materials/<int:material_id>', methods=['GET'])
def get_material(material_id):
    """获取材料详情"""
    material = Material.query.filter(
        Material.id == material_id,
        Material.is_active == True
    ).first()

    if not material:
        return jsonify({'success': False, 'error': '材料不存在'}), 404

    return jsonify({
        'success': True,
        'data': material.to_dict()
    })


@materials_bp.route('/materials/code/<material_code>', methods=['GET'])
def get_material_by_code(material_code):
    """通过材料代码获取材料"""
    material = Material.query.filter(
        Material.material_code == material_code,
        Material.is_active == True
    ).first()

    if not material:
        return jsonify({'success': False, 'error': f'材料代码 {material_code} 不存在'}), 404

    return jsonify({
        'success': True,
        'data': material.to_dict()
    })


@materials_bp.route('/materials', methods=['POST'])
def create_material():
    """创建材料"""
    data = request.get_json()

    # 检查必填字段
    if not data.get('material_code'):
        return jsonify({'success': False, 'error': '材料代码不能为空'}), 400
    if not data.get('material_name'):
        return jsonify({'success': False, 'error': '材料名称不能为空'}), 400

    # 检查材料代码是否已存在
    existing = Material.query.filter(Material.material_code == data['material_code']).first()
    if existing:
        return jsonify({'success': False, 'error': f'材料代码 {data["material_code"]} 已存在'}), 400

    # 创建材料
    material = Material(
        material_code=data['material_code'],
        material_name=data['material_name'],
        category=data.get('category'),
        density=data.get('density'),
        hardness=data.get('hardness'),
        tensile_strength=data.get('tensile_strength'),
        price_per_kg=data.get('price_per_kg'),
        price_currency=data.get('price_currency', 'CNY'),
        supplier=data.get('supplier'),
        supplier_code=data.get('supplier_code'),
        remark=data.get('remark'),
        is_active=True
    )

    db.session.add(material)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': material.to_dict()
    }), 201


@materials_bp.route('/materials/<int:material_id>', methods=['PUT'])
def update_material(material_id):
    """更新材料"""
    material = Material.query.get(material_id)

    if not material:
        return jsonify({'success': False, 'error': '材料不存在'}), 404

    data = request.get_json()

    # 检查材料代码是否与其他材料冲突
    if data.get('material_code') and data['material_code'] != material.material_code:
        existing = Material.query.filter(
            Material.material_code == data['material_code'],
            Material.id != material_id
        ).first()
        if existing:
            return jsonify({'success': False, 'error': f'材料代码 {data["material_code"]} 已被使用'}), 400

    # 更新字段
    for field in ['material_code', 'material_name', 'category', 'density', 'hardness',
                  'tensile_strength', 'price_per_kg', 'price_currency', 'supplier',
                  'supplier_code', 'remark', 'is_active']:
        if field in data:
            setattr(material, field, data[field])

    db.session.commit()

    return jsonify({
        'success': True,
        'data': material.to_dict()
    })


@materials_bp.route('/materials/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    """删除材料（软删除）"""
    material = Material.query.get(material_id)

    if not material:
        return jsonify({'success': False, 'error': '材料不存在'}), 404

    # 软删除
    material.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'材料 {material.material_name} 已删除'
    })


@materials_bp.route('/materials/search', methods=['GET'])
def search_materials():
    """搜索材料"""
    keyword = request.args.get('keyword', '')
    limit = request.args.get('limit', 20, type=int)

    if not keyword:
        return jsonify({'success': True, 'data': []})

    materials = Material.query.filter(
        Material.is_active == True,
        db.or_(
            Material.material_code.contains(keyword),
            Material.material_name.contains(keyword)
        )
    ).limit(limit).all()

    return jsonify({
        'success': True,
        'data': [m.to_dict() for m in materials]
    })
