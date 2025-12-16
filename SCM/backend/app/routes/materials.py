# -*- coding: utf-8 -*-
"""
物料管理 API 路由
包含: 物料分类、物料档案、仓库、库位
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func
from datetime import datetime

from app import db
from app.models.material import (
    MaterialCategory, Material, Warehouse, StorageBin, Inventory,
    MaterialStatus, MaterialType,
    MATERIAL_TYPE_MAP, MATERIAL_STATUS_MAP, WAREHOUSE_TYPE_MAP, BIN_TYPE_MAP
)
from app.models.base_data import Location

materials_bp = Blueprint('materials', __name__, url_prefix='/api/materials')
categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')
warehouses_bp = Blueprint('warehouses', __name__, url_prefix='/api/warehouses')


# ==================== 物料分类 API ====================

@categories_bp.get('')
def get_categories():
    """获取物料分类列表（支持树形结构）"""
    tree = request.args.get('tree', 'false').lower() == 'true'
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    query = MaterialCategory.query
    if active_only:
        query = query.filter(MaterialCategory.is_active == True)

    if tree:
        # 返回树形结构
        roots = query.filter(MaterialCategory.parent_id == None).order_by(MaterialCategory.sort_order).all()
        return jsonify({
            "categories": [c.to_dict(include_children=True) for c in roots]
        })
    else:
        # 返回平铺列表
        categories = query.order_by(MaterialCategory.level, MaterialCategory.sort_order).all()
        return jsonify({
            "categories": [c.to_dict() for c in categories]
        })


@categories_bp.get('/<int:category_id>')
def get_category(category_id):
    """获取分类详情"""
    category = MaterialCategory.query.get_or_404(category_id)
    return jsonify(category.to_dict(include_children=True))


@categories_bp.post('')
def create_category():
    """创建物料分类"""
    data = request.get_json()

    # 验证必填字段
    if not data.get('code') or not data.get('name'):
        return jsonify({"error": "分类编码和名称必填"}), 400

    # 检查编码是否已存在
    if MaterialCategory.query.filter_by(code=data['code']).first():
        return jsonify({"error": "分类编码已存在"}), 400

    category = MaterialCategory(
        code=data['code'],
        name=data['name'],
        parent_id=data.get('parent_id'),
        description=data.get('description'),
        default_uom=data.get('default_uom'),
        sort_order=data.get('sort_order', 0),
        created_by=request.headers.get('User-ID'),
    )

    db.session.add(category)
    db.session.flush()  # 获取 ID

    # 更新层级路径
    category.update_path()
    db.session.commit()

    return jsonify(category.to_dict()), 201


@categories_bp.put('/<int:category_id>')
def update_category(category_id):
    """更新物料分类"""
    category = MaterialCategory.query.get_or_404(category_id)
    data = request.get_json()

    # 检查编码唯一性
    if data.get('code') and data['code'] != category.code:
        if MaterialCategory.query.filter_by(code=data['code']).first():
            return jsonify({"error": "分类编码已存在"}), 400
        category.code = data['code']

    category.name = data.get('name', category.name)
    category.description = data.get('description', category.description)
    category.default_uom = data.get('default_uom', category.default_uom)
    category.sort_order = data.get('sort_order', category.sort_order)
    category.is_active = data.get('is_active', category.is_active)

    # 更新父级（需要更新路径）
    if 'parent_id' in data and data['parent_id'] != category.parent_id:
        category.parent_id = data['parent_id']
        category.update_path()

    db.session.commit()
    return jsonify(category.to_dict())


@categories_bp.delete('/<int:category_id>')
def delete_category(category_id):
    """删除物料分类（逻辑删除）"""
    category = MaterialCategory.query.get_or_404(category_id)

    # 检查是否有子分类
    if MaterialCategory.query.filter_by(parent_id=category_id, is_active=True).first():
        return jsonify({"error": "该分类下有子分类，无法删除"}), 400

    # 检查是否有物料
    if Material.query.filter_by(category_id=category_id).filter(Material.status != MaterialStatus.OBSOLETE.value).first():
        return jsonify({"error": "该分类下有物料，无法删除"}), 400

    category.is_active = False
    db.session.commit()
    return jsonify({"message": "删除成功"})


# ==================== 物料 API ====================

@materials_bp.get('')
def get_materials():
    """获取物料列表（分页筛选）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '').strip()
    category_id = request.args.get('category_id', type=int)
    material_type = request.args.get('material_type')
    status = request.args.get('status')

    query = Material.query

    # 关键字搜索
    if keyword:
        query = query.filter(or_(
            Material.code.ilike(f'%{keyword}%'),
            Material.name.ilike(f'%{keyword}%'),
            Material.barcode.ilike(f'%{keyword}%'),
            Material.specification.ilike(f'%{keyword}%'),
        ))

    # 分类筛选（包含子分类）
    if category_id:
        category = MaterialCategory.query.get(category_id)
        if category:
            # 查找该分类及其所有子分类的物料
            query = query.filter(or_(
                Material.category_id == category_id,
                Material.category.has(MaterialCategory.path.like(f'{category.path}/%'))
            ))

    # 类型筛选
    if material_type:
        query = query.filter(Material.material_type == material_type)

    # 状态筛选
    if status:
        query = query.filter(Material.status == status)
    else:
        # 默认不显示淘汰的
        query = query.filter(Material.status != MaterialStatus.OBSOLETE.value)

    # 排序
    query = query.order_by(Material.created_at.desc())

    # 分页
    total = query.count()
    materials = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        "materials": [m.to_dict() for m in materials],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@materials_bp.get('/search')
def search_materials():
    """快速搜索物料（供其他系统调用）"""
    keyword = request.args.get('keyword', '').strip()
    limit = request.args.get('limit', 20, type=int)

    if not keyword or len(keyword) < 2:
        return jsonify({"materials": []})

    materials = Material.query.filter(
        Material.status == MaterialStatus.ACTIVE.value,
        or_(
            Material.code.ilike(f'%{keyword}%'),
            Material.name.ilike(f'%{keyword}%'),
            Material.barcode.ilike(f'%{keyword}%'),
        )
    ).limit(limit).all()

    return jsonify({
        "materials": [{
            "id": m.id,
            "code": m.code,
            "name": m.name,
            "specification": m.specification,
            "base_uom": m.base_uom,
        } for m in materials]
    })


@materials_bp.get('/<int:material_id>')
def get_material(material_id):
    """获取物料详情"""
    material = Material.query.get_or_404(material_id)
    return jsonify(material.to_dict(include_category=True))


@materials_bp.post('')
def create_material():
    """创建物料"""
    data = request.get_json()

    # 验证必填字段
    if not data.get('name'):
        return jsonify({"error": "物料名称必填"}), 400

    # 生成或验证编码
    code = data.get('code')
    if not code:
        category = MaterialCategory.query.get(data.get('category_id')) if data.get('category_id') else None
        code = Material.generate_code(category.code if category else None)
    elif Material.query.filter_by(code=code).first():
        return jsonify({"error": "物料编码已存在"}), 400

    # 检查条形码唯一性
    if data.get('barcode') and Material.query.filter_by(barcode=data['barcode']).first():
        return jsonify({"error": "条形码已存在"}), 400

    material = Material(
        code=code,
        barcode=data.get('barcode'),
        customer_code=data.get('customer_code'),
        supplier_code=data.get('supplier_code'),
        name=data['name'],
        short_name=data.get('short_name'),
        english_name=data.get('english_name'),
        description=data.get('description'),
        category_id=data.get('category_id'),
        material_type=data.get('material_type', MaterialType.RAW.value),
        specification=data.get('specification'),
        model=data.get('model'),
        brand=data.get('brand'),
        color=data.get('color'),
        material=data.get('material'),
        base_uom=data.get('base_uom', 'pcs'),
        purchase_uom=data.get('purchase_uom'),
        sales_uom=data.get('sales_uom'),
        purchase_conversion=data.get('purchase_conversion', 1),
        sales_conversion=data.get('sales_conversion', 1),
        min_stock=data.get('min_stock', 0),
        max_stock=data.get('max_stock'),
        safety_stock=data.get('safety_stock', 0),
        reorder_point=data.get('reorder_point'),
        reorder_qty=data.get('reorder_qty'),
        default_warehouse_id=data.get('default_warehouse_id'),
        default_bin=data.get('default_bin'),
        shelf_life_days=data.get('shelf_life_days'),
        is_batch_managed=data.get('is_batch_managed', False),
        is_serial_managed=data.get('is_serial_managed', False),
        default_supplier_id=data.get('default_supplier_id'),
        lead_time_days=data.get('lead_time_days'),
        min_order_qty=data.get('min_order_qty'),
        reference_cost=data.get('reference_cost'),
        reference_price=data.get('reference_price'),
        currency=data.get('currency', 'CNY'),
        gross_weight=data.get('gross_weight'),
        net_weight=data.get('net_weight'),
        length=data.get('length'),
        width=data.get('width'),
        height=data.get('height'),
        volume=data.get('volume'),
        image_url=data.get('image_url'),
        drawing_url=data.get('drawing_url'),
        attachments=data.get('attachments', []),
        remark=data.get('remark'),
        created_by=request.headers.get('User-ID'),
    )

    db.session.add(material)
    db.session.commit()

    return jsonify(material.to_dict()), 201


@materials_bp.put('/<int:material_id>')
def update_material(material_id):
    """更新物料"""
    material = Material.query.get_or_404(material_id)
    data = request.get_json()

    # 检查编码唯一性
    if data.get('code') and data['code'] != material.code:
        if Material.query.filter_by(code=data['code']).first():
            return jsonify({"error": "物料编码已存在"}), 400
        material.code = data['code']

    # 检查条形码唯一性
    if data.get('barcode') and data['barcode'] != material.barcode:
        if Material.query.filter_by(barcode=data['barcode']).first():
            return jsonify({"error": "条形码已存在"}), 400
        material.barcode = data['barcode']

    # 更新字段
    updatable_fields = [
        'customer_code', 'supplier_code', 'name', 'short_name', 'english_name',
        'description', 'category_id', 'material_type', 'specification', 'model',
        'brand', 'color', 'material', 'base_uom', 'purchase_uom', 'sales_uom',
        'purchase_conversion', 'sales_conversion', 'min_stock', 'max_stock',
        'safety_stock', 'reorder_point', 'reorder_qty', 'default_warehouse_id',
        'default_bin', 'shelf_life_days', 'is_batch_managed', 'is_serial_managed',
        'default_supplier_id', 'lead_time_days', 'min_order_qty', 'reference_cost',
        'reference_price', 'currency', 'gross_weight', 'net_weight', 'length',
        'width', 'height', 'volume', 'image_url', 'drawing_url', 'attachments',
        'status', 'remark'
    ]

    for field in updatable_fields:
        if field in data:
            setattr(material, field, data[field])

    db.session.commit()
    return jsonify(material.to_dict())


@materials_bp.delete('/<int:material_id>')
def delete_material(material_id):
    """删除物料（标记为淘汰）"""
    material = Material.query.get_or_404(material_id)

    # 检查是否有库存
    inventory = Inventory.query.filter(
        Inventory.material_id == material_id,
        Inventory.quantity > 0
    ).first()
    if inventory:
        return jsonify({"error": "该物料有库存，无法删除"}), 400

    material.status = MaterialStatus.OBSOLETE.value
    db.session.commit()
    return jsonify({"message": "删除成功"})


@materials_bp.get('/types')
def get_material_types():
    """获取物料类型和状态定义"""
    return jsonify({
        "material_types": [{"value": k, "label": v} for k, v in MATERIAL_TYPE_MAP.items()],
        "material_statuses": [{"value": k, "label": v} for k, v in MATERIAL_STATUS_MAP.items()],
    })


@materials_bp.get('/low-stock')
def get_low_stock_materials():
    """获取低库存物料（库存预警）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)

    # 聚合每个物料的库存总量
    subquery = db.session.query(
        Inventory.material_id,
        func.sum(Inventory.quantity).label('total_qty')
    )
    if warehouse_id:
        subquery = subquery.filter(Inventory.warehouse_id == warehouse_id)
    subquery = subquery.group_by(Inventory.material_id).subquery()

    # 查找低于安全库存或最低库存的物料
    query = db.session.query(Material, subquery.c.total_qty).outerjoin(
        subquery, Material.id == subquery.c.material_id
    ).filter(
        Material.status == MaterialStatus.ACTIVE.value,
        or_(
            func.coalesce(subquery.c.total_qty, 0) <= Material.safety_stock,
            func.coalesce(subquery.c.total_qty, 0) <= Material.min_stock,
        ),
        Material.min_stock > 0  # 只检查设置了最低库存的物料
    )

    total = query.count()
    results = query.offset((page - 1) * page_size).limit(page_size).all()

    materials = []
    for material, total_qty in results:
        data = material.to_dict()
        data['current_stock'] = float(total_qty or 0)
        data['shortage'] = float(material.safety_stock or material.min_stock or 0) - float(total_qty or 0)
        materials.append(data)

    return jsonify({
        "materials": materials,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


# ==================== 仓库 API ====================

@warehouses_bp.get('')
def get_warehouses():
    """获取仓库列表"""
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    include_bins = request.args.get('include_bins', 'false').lower() == 'true'

    query = Warehouse.query
    if active_only:
        query = query.filter(Warehouse.is_active == True)

    warehouses = query.order_by(Warehouse.sort_order).all()

    return jsonify({
        "warehouses": [w.to_dict(include_bins=include_bins) for w in warehouses]
    })


@warehouses_bp.get('/<int:warehouse_id>')
def get_warehouse(warehouse_id):
    """获取仓库详情"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    return jsonify(warehouse.to_dict(include_bins=True))


@warehouses_bp.post('')
def create_warehouse():
    """创建仓库"""
    data = request.get_json()

    if not data.get('code') or not data.get('name'):
        return jsonify({"error": "仓库编码和名称必填"}), 400

    if Warehouse.query.filter_by(code=data['code']).first():
        return jsonify({"error": "仓库编码已存在"}), 400

    warehouse = Warehouse(
        code=data['code'],
        name=data['name'],
        short_name=data.get('short_name'),
        location_id=data.get('location_id'),
        address=data.get('address'),
        warehouse_type=data.get('warehouse_type', 'normal'),
        is_allow_negative=data.get('is_allow_negative', False),
        manager_id=data.get('manager_id'),
        manager_name=data.get('manager_name'),
        contact_phone=data.get('contact_phone'),
        description=data.get('description'),
        sort_order=data.get('sort_order', 0),
        created_by=request.headers.get('User-ID'),
    )

    db.session.add(warehouse)
    db.session.commit()

    return jsonify(warehouse.to_dict()), 201


@warehouses_bp.put('/<int:warehouse_id>')
def update_warehouse(warehouse_id):
    """更新仓库"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    data = request.get_json()

    if data.get('code') and data['code'] != warehouse.code:
        if Warehouse.query.filter_by(code=data['code']).first():
            return jsonify({"error": "仓库编码已存在"}), 400
        warehouse.code = data['code']

    updatable_fields = [
        'name', 'short_name', 'location_id', 'address', 'warehouse_type',
        'is_allow_negative', 'manager_id', 'manager_name', 'contact_phone',
        'description', 'is_active', 'sort_order'
    ]

    for field in updatable_fields:
        if field in data:
            setattr(warehouse, field, data[field])

    db.session.commit()
    return jsonify(warehouse.to_dict())


@warehouses_bp.delete('/<int:warehouse_id>')
def delete_warehouse(warehouse_id):
    """删除仓库（逻辑删除）"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)

    # 检查是否有库存
    if Inventory.query.filter(Inventory.warehouse_id == warehouse_id, Inventory.quantity > 0).first():
        return jsonify({"error": "该仓库有库存，无法删除"}), 400

    warehouse.is_active = False
    db.session.commit()
    return jsonify({"message": "删除成功"})


@warehouses_bp.get('/types')
def get_warehouse_types():
    """获取仓库类型和库位类型定义"""
    return jsonify({
        "warehouse_types": [{"value": k, "label": v} for k, v in WAREHOUSE_TYPE_MAP.items()],
        "bin_types": [{"value": k, "label": v} for k, v in BIN_TYPE_MAP.items()],
    })


# ==================== 库位 API ====================

@warehouses_bp.get('/<int:warehouse_id>/bins')
def get_warehouse_bins(warehouse_id):
    """获取仓库的库位列表"""
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    zone = request.args.get('zone')

    query = StorageBin.query.filter(StorageBin.warehouse_id == warehouse_id)
    if active_only:
        query = query.filter(StorageBin.is_active == True)
    if zone:
        query = query.filter(StorageBin.zone == zone)

    bins = query.order_by(StorageBin.sort_order, StorageBin.code).all()

    return jsonify({
        "bins": [b.to_dict() for b in bins]
    })


@warehouses_bp.post('/<int:warehouse_id>/bins')
def create_bin(warehouse_id):
    """创建库位"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    data = request.get_json()

    if not data.get('code'):
        return jsonify({"error": "库位编码必填"}), 400

    # 检查仓库内库位编码唯一性
    if StorageBin.query.filter_by(warehouse_id=warehouse_id, code=data['code']).first():
        return jsonify({"error": "该仓库已存在此库位编码"}), 400

    bin = StorageBin(
        code=data['code'],
        name=data.get('name'),
        warehouse_id=warehouse_id,
        zone=data.get('zone'),
        aisle=data.get('aisle'),
        rack=data.get('rack'),
        level=data.get('level'),
        position=data.get('position'),
        max_weight=data.get('max_weight'),
        max_volume=data.get('max_volume'),
        bin_type=data.get('bin_type', 'storage'),
        allowed_material_types=data.get('allowed_material_types', []),
        sort_order=data.get('sort_order', 0),
    )

    db.session.add(bin)
    db.session.commit()

    return jsonify(bin.to_dict()), 201


@warehouses_bp.put('/<int:warehouse_id>/bins/<int:bin_id>')
def update_bin(warehouse_id, bin_id):
    """更新库位"""
    bin = StorageBin.query.filter_by(id=bin_id, warehouse_id=warehouse_id).first_or_404()
    data = request.get_json()

    if data.get('code') and data['code'] != bin.code:
        if StorageBin.query.filter_by(warehouse_id=warehouse_id, code=data['code']).first():
            return jsonify({"error": "该仓库已存在此库位编码"}), 400
        bin.code = data['code']

    updatable_fields = [
        'name', 'zone', 'aisle', 'rack', 'level', 'position',
        'max_weight', 'max_volume', 'bin_type', 'allowed_material_types',
        'is_active', 'sort_order'
    ]

    for field in updatable_fields:
        if field in data:
            setattr(bin, field, data[field])

    db.session.commit()
    return jsonify(bin.to_dict())


@warehouses_bp.delete('/<int:warehouse_id>/bins/<int:bin_id>')
def delete_bin(warehouse_id, bin_id):
    """删除库位（逻辑删除）"""
    bin = StorageBin.query.filter_by(id=bin_id, warehouse_id=warehouse_id).first_or_404()

    # 检查是否有库存
    if Inventory.query.filter(Inventory.bin_id == bin_id, Inventory.quantity > 0).first():
        return jsonify({"error": "该库位有库存，无法删除"}), 400

    bin.is_active = False
    db.session.commit()
    return jsonify({"message": "删除成功"})


@warehouses_bp.post('/<int:warehouse_id>/bins/batch')
def batch_create_bins(warehouse_id):
    """批量创建库位"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    data = request.get_json()

    zone = data.get('zone', 'A')
    rows = data.get('rows', 1)           # 货架排数
    columns = data.get('columns', 1)     # 每排货架数
    levels = data.get('levels', 1)       # 层数

    created = []
    for r in range(1, rows + 1):
        for c in range(1, columns + 1):
            for l in range(1, levels + 1):
                code = f"{zone}-{r:02d}-{c:02d}-{l:02d}"

                # 跳过已存在的
                if StorageBin.query.filter_by(warehouse_id=warehouse_id, code=code).first():
                    continue

                bin = StorageBin(
                    code=code,
                    name=f"{zone}区{r}排{c}架{l}层",
                    warehouse_id=warehouse_id,
                    zone=zone,
                    rack=str(r),
                    aisle=str(c),
                    level=str(l),
                    bin_type='storage',
                )
                db.session.add(bin)
                created.append(code)

    db.session.commit()

    return jsonify({
        "message": f"成功创建 {len(created)} 个库位",
        "created": created
    }), 201
