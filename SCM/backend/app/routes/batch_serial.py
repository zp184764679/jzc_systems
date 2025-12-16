# -*- coding: utf-8 -*-
"""
批次和序列号管理路由
"""
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, request, jsonify, g

from app import db
from app.models import (
    BatchMaster, SerialNumber, BatchTransaction, SerialTransaction,
    Material, Warehouse, StorageBin,
    BatchStatus, QualityStatus, SerialStatus,
    BATCH_STATUS_MAP, QUALITY_STATUS_MAP, SERIAL_STATUS_MAP,
    BATCH_TX_TYPE_MAP, SERIAL_TX_TYPE_MAP
)

bp = Blueprint('batch_serial', __name__, url_prefix='/api/batch-serial')


# ==================== 批次管理 ====================

@bp.get('/batches')
def get_batches():
    """获取批次列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    material_id = request.args.get('material_id', type=int)
    status = request.args.get('status')
    quality_status = request.args.get('quality_status')
    supplier_id = request.args.get('supplier_id', type=int)
    expiring_days = request.args.get('expiring_days', type=int)

    query = BatchMaster.query

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            db.or_(
                BatchMaster.batch_no.ilike(like),
                BatchMaster.material_code.ilike(like),
                BatchMaster.material_name.ilike(like),
                BatchMaster.supplier_batch_no.ilike(like)
            )
        )

    if material_id:
        query = query.filter(BatchMaster.material_id == material_id)

    if status:
        query = query.filter(BatchMaster.status == status)

    if quality_status:
        query = query.filter(BatchMaster.quality_status == quality_status)

    if supplier_id:
        query = query.filter(BatchMaster.supplier_id == supplier_id)

    # 即将过期筛选
    if expiring_days:
        future_date = date.today()
        from datetime import timedelta
        future_date = future_date + timedelta(days=expiring_days)
        query = query.filter(
            BatchMaster.expiry_date.isnot(None),
            BatchMaster.expiry_date <= future_date,
            BatchMaster.expiry_date >= date.today()
        )

    # 排序
    query = query.order_by(BatchMaster.created_at.desc())

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'success': True,
        'items': [item.to_dict() for item in items],
        'total': total,
        'page': page,
        'page_size': page_size,
        'pages': (total + page_size - 1) // page_size
    })


@bp.get('/batches/<int:batch_id>')
def get_batch(batch_id):
    """获取批次详情"""
    batch = BatchMaster.query.get_or_404(batch_id)
    data = batch.to_dict(include_material=True)

    # 获取序列号列表
    serial_numbers = batch.serial_numbers.limit(100).all()
    data['serial_numbers'] = [sn.to_dict() for sn in serial_numbers]
    data['serial_count'] = batch.serial_numbers.count()

    # 获取最近交易记录
    transactions = BatchTransaction.query.filter_by(
        batch_id=batch_id
    ).order_by(BatchTransaction.transaction_date.desc()).limit(20).all()
    data['transactions'] = [tx.to_dict() for tx in transactions]

    return jsonify({
        'success': True,
        'data': data
    })


@bp.post('/batches')
def create_batch():
    """创建批次"""
    data = request.get_json() or {}

    material_id = data.get('material_id')
    if not material_id:
        return jsonify({'success': False, 'error': '物料ID不能为空'}), 400

    material = Material.query.get(material_id)
    if not material:
        return jsonify({'success': False, 'error': '物料不存在'}), 404

    # 检查物料是否启用批次管理
    if not material.is_batch_managed:
        return jsonify({'success': False, 'error': '该物料未启用批次管理'}), 400

    # 生成或使用提供的批次号
    batch_no = data.get('batch_no')
    if not batch_no:
        batch_no = BatchMaster.generate_batch_no(material.code)

    # 检查批次号是否重复
    existing = BatchMaster.query.filter_by(
        material_id=material_id,
        batch_no=batch_no
    ).first()
    if existing:
        return jsonify({'success': False, 'error': f'批次号 {batch_no} 已存在'}), 400

    # 处理日期
    production_date = None
    expiry_date = None
    if data.get('production_date'):
        production_date = datetime.strptime(data['production_date'], '%Y-%m-%d').date()
    if data.get('expiry_date'):
        expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
    elif production_date and material.shelf_life_days:
        from datetime import timedelta
        expiry_date = production_date + timedelta(days=material.shelf_life_days)

    batch = BatchMaster(
        batch_no=batch_no,
        material_id=material_id,
        material_code=material.code,
        material_name=material.name,
        production_date=production_date,
        expiry_date=expiry_date,
        shelf_life_days=data.get('shelf_life_days') or material.shelf_life_days,
        supplier_id=data.get('supplier_id'),
        supplier_name=data.get('supplier_name'),
        supplier_batch_no=data.get('supplier_batch_no'),
        manufacturer=data.get('manufacturer'),
        origin_country=data.get('origin_country'),
        po_no=data.get('po_no'),
        inbound_order_no=data.get('inbound_order_no'),
        initial_qty=Decimal(str(data.get('initial_qty', 0))),
        current_qty=Decimal(str(data.get('initial_qty', 0))),
        uom=data.get('uom') or material.base_uom,
        quality_status=data.get('quality_status', QualityStatus.PENDING.value),
        certificate_no=data.get('certificate_no'),
        lot_no=data.get('lot_no'),
        heat_no=data.get('heat_no'),
        remark=data.get('remark'),
        created_by=getattr(g, 'current_user', {}).get('user_id'),
        created_by_name=getattr(g, 'current_user', {}).get('full_name'),
    )

    db.session.add(batch)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '批次创建成功',
        'data': batch.to_dict()
    }), 201


@bp.put('/batches/<int:batch_id>')
def update_batch(batch_id):
    """更新批次"""
    batch = BatchMaster.query.get_or_404(batch_id)
    data = request.get_json() or {}

    # 更新允许的字段
    updatable_fields = [
        'supplier_name', 'supplier_batch_no', 'manufacturer', 'origin_country',
        'quality_status', 'inspection_date', 'inspection_no', 'inspection_result',
        'certificate_no', 'certificate_url', 'lot_no', 'heat_no', 'customs_no',
        'attributes', 'remark'
    ]

    for field in updatable_fields:
        if field in data:
            if field == 'inspection_date' and data[field]:
                setattr(batch, field, datetime.strptime(data[field], '%Y-%m-%d').date())
            else:
                setattr(batch, field, data[field])

    # 更新日期字段
    if 'production_date' in data and data['production_date']:
        batch.production_date = datetime.strptime(data['production_date'], '%Y-%m-%d').date()
    if 'expiry_date' in data and data['expiry_date']:
        batch.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()

    batch.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '批次更新成功',
        'data': batch.to_dict()
    })


@bp.post('/batches/<int:batch_id>/block')
def block_batch(batch_id):
    """冻结批次"""
    batch = BatchMaster.query.get_or_404(batch_id)
    data = request.get_json() or {}

    batch.status = BatchStatus.BLOCKED.value
    batch.block_reason = data.get('reason', '')
    batch.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '批次已冻结'
    })


@bp.post('/batches/<int:batch_id>/unblock')
def unblock_batch(batch_id):
    """解冻批次"""
    batch = BatchMaster.query.get_or_404(batch_id)

    if batch.is_expired:
        batch.status = BatchStatus.EXPIRED.value
    elif batch.current_qty <= 0:
        batch.status = BatchStatus.DEPLETED.value
    else:
        batch.status = BatchStatus.ACTIVE.value

    batch.block_reason = None
    batch.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '批次已解冻'
    })


@bp.post('/batches/<int:batch_id>/quality-check')
def batch_quality_check(batch_id):
    """批次质检"""
    batch = BatchMaster.query.get_or_404(batch_id)
    data = request.get_json() or {}

    quality_status = data.get('quality_status')
    if quality_status not in [s.value for s in QualityStatus]:
        return jsonify({'success': False, 'error': '无效的质量状态'}), 400

    batch.quality_status = quality_status
    batch.inspection_date = date.today()
    batch.inspection_no = data.get('inspection_no')
    batch.inspection_result = data.get('inspection_result')
    batch.certificate_no = data.get('certificate_no')

    # 不合格则隔离
    if quality_status == QualityStatus.FAILED.value:
        batch.status = BatchStatus.QUARANTINE.value

    batch.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '质检结果已更新',
        'data': batch.to_dict()
    })


@bp.get('/batches/<int:batch_id>/trace')
def trace_batch(batch_id):
    """批次追溯"""
    batch = BatchMaster.query.get_or_404(batch_id)

    # 获取所有交易记录
    transactions = BatchTransaction.query.filter_by(
        batch_id=batch_id
    ).order_by(BatchTransaction.transaction_date.asc()).all()

    # 获取关联的序列号
    serial_numbers = batch.serial_numbers.all()

    return jsonify({
        'success': True,
        'data': {
            'batch': batch.to_dict(),
            'transactions': [tx.to_dict() for tx in transactions],
            'serial_numbers': [sn.to_dict() for sn in serial_numbers]
        }
    })


@bp.get('/batches/expiring')
def get_expiring_batches():
    """获取即将过期的批次"""
    days = request.args.get('days', 30, type=int)
    from datetime import timedelta
    future_date = date.today() + timedelta(days=days)

    batches = BatchMaster.query.filter(
        BatchMaster.expiry_date.isnot(None),
        BatchMaster.expiry_date <= future_date,
        BatchMaster.expiry_date >= date.today(),
        BatchMaster.status == BatchStatus.ACTIVE.value,
        BatchMaster.current_qty > 0
    ).order_by(BatchMaster.expiry_date.asc()).all()

    return jsonify({
        'success': True,
        'items': [b.to_dict() for b in batches],
        'total': len(batches)
    })


@bp.get('/batches/statistics')
def get_batch_statistics():
    """获取批次统计"""
    # 按状态统计
    status_stats = db.session.query(
        BatchMaster.status,
        db.func.count(BatchMaster.id)
    ).group_by(BatchMaster.status).all()

    # 按质量状态统计
    quality_stats = db.session.query(
        BatchMaster.quality_status,
        db.func.count(BatchMaster.id)
    ).group_by(BatchMaster.quality_status).all()

    # 即将过期统计
    from datetime import timedelta
    today = date.today()
    expiring_7d = BatchMaster.query.filter(
        BatchMaster.expiry_date.isnot(None),
        BatchMaster.expiry_date <= today + timedelta(days=7),
        BatchMaster.expiry_date >= today,
        BatchMaster.status == BatchStatus.ACTIVE.value
    ).count()

    expiring_30d = BatchMaster.query.filter(
        BatchMaster.expiry_date.isnot(None),
        BatchMaster.expiry_date <= today + timedelta(days=30),
        BatchMaster.expiry_date >= today,
        BatchMaster.status == BatchStatus.ACTIVE.value
    ).count()

    expired = BatchMaster.query.filter(
        BatchMaster.expiry_date.isnot(None),
        BatchMaster.expiry_date < today,
        BatchMaster.current_qty > 0
    ).count()

    return jsonify({
        'success': True,
        'data': {
            'by_status': {s: c for s, c in status_stats},
            'by_quality': {q: c for q, c in quality_stats},
            'expiring_7d': expiring_7d,
            'expiring_30d': expiring_30d,
            'expired': expired,
            'total': BatchMaster.query.count()
        }
    })


# ==================== 序列号管理 ====================

@bp.get('/serials')
def get_serials():
    """获取序列号列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    material_id = request.args.get('material_id', type=int)
    batch_id = request.args.get('batch_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status')

    query = SerialNumber.query

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            db.or_(
                SerialNumber.serial_no.ilike(like),
                SerialNumber.material_code.ilike(like),
                SerialNumber.material_name.ilike(like),
                SerialNumber.supplier_serial_no.ilike(like)
            )
        )

    if material_id:
        query = query.filter(SerialNumber.material_id == material_id)

    if batch_id:
        query = query.filter(SerialNumber.batch_id == batch_id)

    if warehouse_id:
        query = query.filter(SerialNumber.warehouse_id == warehouse_id)

    if status:
        query = query.filter(SerialNumber.status == status)

    # 排序
    query = query.order_by(SerialNumber.created_at.desc())

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({
        'success': True,
        'items': [item.to_dict() for item in items],
        'total': total,
        'page': page,
        'page_size': page_size,
        'pages': (total + page_size - 1) // page_size
    })


@bp.get('/serials/<int:serial_id>')
def get_serial(serial_id):
    """获取序列号详情"""
    serial = SerialNumber.query.get_or_404(serial_id)
    data = serial.to_dict(include_material=True, include_batch=True)

    # 获取流转记录
    transactions = SerialTransaction.query.filter_by(
        serial_id=serial_id
    ).order_by(SerialTransaction.transaction_date.desc()).all()
    data['transactions'] = [tx.to_dict() for tx in transactions]

    return jsonify({
        'success': True,
        'data': data
    })


@bp.post('/serials')
def create_serial():
    """创建序列号"""
    data = request.get_json() or {}

    material_id = data.get('material_id')
    if not material_id:
        return jsonify({'success': False, 'error': '物料ID不能为空'}), 400

    material = Material.query.get(material_id)
    if not material:
        return jsonify({'success': False, 'error': '物料不存在'}), 404

    # 检查物料是否启用序列号管理
    if not material.is_serial_managed:
        return jsonify({'success': False, 'error': '该物料未启用序列号管理'}), 400

    serial_no = data.get('serial_no')
    if not serial_no:
        return jsonify({'success': False, 'error': '序列号不能为空'}), 400

    # 检查序列号是否重复
    existing = SerialNumber.query.filter_by(
        material_id=material_id,
        serial_no=serial_no
    ).first()
    if existing:
        return jsonify({'success': False, 'error': f'序列号 {serial_no} 已存在'}), 400

    # 处理批次关联
    batch_id = data.get('batch_id')
    batch_no = data.get('batch_no')
    if batch_id:
        batch = BatchMaster.query.get(batch_id)
        if batch:
            batch_no = batch.batch_no

    # 处理仓库/库位
    warehouse_id = data.get('warehouse_id')
    warehouse_name = None
    bin_id = data.get('bin_id')
    bin_code = None

    if warehouse_id:
        warehouse = Warehouse.query.get(warehouse_id)
        if warehouse:
            warehouse_name = warehouse.name

    if bin_id:
        bin = StorageBin.query.get(bin_id)
        if bin:
            bin_code = bin.code

    serial = SerialNumber(
        serial_no=serial_no,
        material_id=material_id,
        material_code=material.code,
        material_name=material.name,
        batch_id=batch_id,
        batch_no=batch_no,
        warehouse_id=warehouse_id,
        warehouse_name=warehouse_name,
        bin_id=bin_id,
        bin_code=bin_code,
        supplier_id=data.get('supplier_id'),
        supplier_name=data.get('supplier_name'),
        supplier_serial_no=data.get('supplier_serial_no'),
        manufacturer=data.get('manufacturer'),
        manufacturer_serial_no=data.get('manufacturer_serial_no'),
        po_no=data.get('po_no'),
        inbound_order_no=data.get('inbound_order_no'),
        quality_status=data.get('quality_status', QualityStatus.PENDING.value),
        status=data.get('status', SerialStatus.IN_STOCK.value),
        remark=data.get('remark'),
        created_by=getattr(g, 'current_user', {}).get('user_id'),
        created_by_name=getattr(g, 'current_user', {}).get('full_name'),
    )

    # 处理保修信息
    if data.get('warranty_months'):
        serial.warranty_months = data['warranty_months']
        serial.warranty_start_date = date.today()
        from datetime import timedelta
        serial.warranty_end_date = date.today() + timedelta(days=data['warranty_months'] * 30)

    db.session.add(serial)

    # 记录入库交易
    tx = SerialTransaction(
        serial_id=serial.id,
        serial_no=serial.serial_no,
        material_id=material_id,
        material_code=material.code,
        material_name=material.name,
        transaction_type='receipt',
        to_warehouse_id=warehouse_id,
        to_warehouse_name=warehouse_name,
        to_bin_id=bin_id,
        to_bin_code=bin_code,
        to_status=serial.status,
        reference_type=data.get('reference_type'),
        reference_no=data.get('reference_no'),
        partner_type='supplier',
        partner_id=data.get('supplier_id'),
        partner_name=data.get('supplier_name'),
        created_by=getattr(g, 'current_user', {}).get('user_id'),
        created_by_name=getattr(g, 'current_user', {}).get('full_name'),
    )
    db.session.add(tx)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': '序列号创建成功',
        'data': serial.to_dict()
    }), 201


@bp.post('/serials/batch-create')
def batch_create_serials():
    """批量创建序列号"""
    data = request.get_json() or {}

    material_id = data.get('material_id')
    serial_nos = data.get('serial_nos', [])

    if not material_id:
        return jsonify({'success': False, 'error': '物料ID不能为空'}), 400

    if not serial_nos:
        return jsonify({'success': False, 'error': '序列号列表不能为空'}), 400

    material = Material.query.get(material_id)
    if not material:
        return jsonify({'success': False, 'error': '物料不存在'}), 404

    if not material.is_serial_managed:
        return jsonify({'success': False, 'error': '该物料未启用序列号管理'}), 400

    # 检查重复
    existing = SerialNumber.query.filter(
        SerialNumber.material_id == material_id,
        SerialNumber.serial_no.in_(serial_nos)
    ).all()

    if existing:
        existing_nos = [s.serial_no for s in existing]
        return jsonify({
            'success': False,
            'error': f'以下序列号已存在: {", ".join(existing_nos)}'
        }), 400

    created = []
    user_id = getattr(g, 'current_user', {}).get('user_id')
    user_name = getattr(g, 'current_user', {}).get('full_name')

    for serial_no in serial_nos:
        serial = SerialNumber(
            serial_no=serial_no,
            material_id=material_id,
            material_code=material.code,
            material_name=material.name,
            batch_id=data.get('batch_id'),
            batch_no=data.get('batch_no'),
            warehouse_id=data.get('warehouse_id'),
            warehouse_name=data.get('warehouse_name'),
            bin_id=data.get('bin_id'),
            bin_code=data.get('bin_code'),
            supplier_id=data.get('supplier_id'),
            supplier_name=data.get('supplier_name'),
            status=SerialStatus.IN_STOCK.value,
            created_by=user_id,
            created_by_name=user_name,
        )
        db.session.add(serial)
        created.append(serial)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'成功创建 {len(created)} 个序列号',
        'data': [s.to_dict() for s in created]
    }), 201


@bp.put('/serials/<int:serial_id>')
def update_serial(serial_id):
    """更新序列号"""
    serial = SerialNumber.query.get_or_404(serial_id)
    data = request.get_json() or {}

    # 更新允许的字段
    updatable_fields = [
        'supplier_serial_no', 'manufacturer', 'manufacturer_serial_no',
        'quality_status', 'inspection_date', 'inspection_no',
        'warranty_start_date', 'warranty_end_date', 'warranty_months',
        'attributes', 'remark'
    ]

    for field in updatable_fields:
        if field in data:
            if field in ['inspection_date', 'warranty_start_date', 'warranty_end_date'] and data[field]:
                setattr(serial, field, datetime.strptime(data[field], '%Y-%m-%d').date())
            else:
                setattr(serial, field, data[field])

    serial.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '序列号更新成功',
        'data': serial.to_dict()
    })


@bp.post('/serials/<int:serial_id>/status')
def update_serial_status(serial_id):
    """更新序列号状态"""
    serial = SerialNumber.query.get_or_404(serial_id)
    data = request.get_json() or {}

    new_status = data.get('status')
    if new_status not in [s.value for s in SerialStatus]:
        return jsonify({'success': False, 'error': '无效的状态'}), 400

    old_status = serial.status
    user_id = getattr(g, 'current_user', {}).get('user_id')
    user_name = getattr(g, 'current_user', {}).get('full_name')

    serial.update_status(new_status, user_id)

    # 记录状态变更
    tx = SerialTransaction(
        serial_id=serial_id,
        serial_no=serial.serial_no,
        material_id=serial.material_id,
        material_code=serial.material_code,
        material_name=serial.material_name,
        transaction_type='status_change',
        from_status=old_status,
        to_status=new_status,
        remark=data.get('remark'),
        created_by=user_id,
        created_by_name=user_name,
    )
    db.session.add(tx)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '状态更新成功',
        'data': serial.to_dict()
    })


@bp.get('/serials/<int:serial_id>/trace')
def trace_serial(serial_id):
    """序列号追溯"""
    serial = SerialNumber.query.get_or_404(serial_id)

    # 获取所有流转记录
    transactions = SerialTransaction.query.filter_by(
        serial_id=serial_id
    ).order_by(SerialTransaction.transaction_date.asc()).all()

    return jsonify({
        'success': True,
        'data': {
            'serial': serial.to_dict(include_material=True, include_batch=True),
            'transactions': [tx.to_dict() for tx in transactions]
        }
    })


@bp.get('/serials/by-serial-no/<serial_no>')
def get_serial_by_no(serial_no):
    """通过序列号查询"""
    serials = SerialNumber.query.filter(
        SerialNumber.serial_no.ilike(f"%{serial_no}%")
    ).limit(50).all()

    return jsonify({
        'success': True,
        'items': [s.to_dict() for s in serials]
    })


@bp.get('/serials/statistics')
def get_serial_statistics():
    """获取序列号统计"""
    # 按状态统计
    status_stats = db.session.query(
        SerialNumber.status,
        db.func.count(SerialNumber.id)
    ).group_by(SerialNumber.status).all()

    # 按仓库统计
    warehouse_stats = db.session.query(
        SerialNumber.warehouse_name,
        db.func.count(SerialNumber.id)
    ).filter(
        SerialNumber.warehouse_id.isnot(None)
    ).group_by(SerialNumber.warehouse_name).all()

    return jsonify({
        'success': True,
        'data': {
            'by_status': {s: c for s, c in status_stats},
            'by_warehouse': {w or '未分配': c for w, c in warehouse_stats},
            'total': SerialNumber.query.count()
        }
    })


# ==================== 枚举值 ====================

@bp.get('/enums')
def get_enums():
    """获取枚举值"""
    return jsonify({
        'success': True,
        'data': {
            'batch_status': BATCH_STATUS_MAP,
            'quality_status': QUALITY_STATUS_MAP,
            'serial_status': SERIAL_STATUS_MAP,
            'batch_tx_type': BATCH_TX_TYPE_MAP,
            'serial_tx_type': SERIAL_TX_TYPE_MAP
        }
    })
