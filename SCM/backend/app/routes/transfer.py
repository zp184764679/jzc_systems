# SCM 库存转移路由
# Transfer Order API Routes

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func, or_, and_
from app import db
from app.models.transfer import (
    TransferOrder, TransferOrderItem, TransferLog,
    TransferStatus, TransferType,
    TRANSFER_STATUS_MAP, TRANSFER_TYPE_MAP
)
from app.models.material import Material, Warehouse, StorageBin, Inventory
from app.models.inventory import InventoryTx

transfer_bp = Blueprint('transfer', __name__, url_prefix='/api/transfer')


def generate_order_no():
    """生成转移单号 TR-YYYYMMDD-XXXX"""
    today = datetime.now().strftime('%Y%m%d')
    prefix = f'TR-{today}-'

    # 查找今天最大的单号
    last_order = TransferOrder.query.filter(
        TransferOrder.order_no.like(f'{prefix}%')
    ).order_by(TransferOrder.order_no.desc()).first()

    if last_order:
        try:
            last_num = int(last_order.order_no.split('-')[-1])
            next_num = last_num + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1

    return f'{prefix}{next_num:04d}'


# ==================== 转移单 CRUD ====================

@transfer_bp.route('', methods=['GET'])
def get_transfer_orders():
    """获取转移单列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    transfer_type = request.args.get('transfer_type')
    keyword = request.args.get('keyword')
    source_warehouse_id = request.args.get('source_warehouse_id', type=int)
    target_warehouse_id = request.args.get('target_warehouse_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = TransferOrder.query

    # 筛选条件
    if status:
        try:
            query = query.filter(TransferOrder.status == TransferStatus(status))
        except ValueError:
            pass
    if transfer_type:
        try:
            query = query.filter(TransferOrder.transfer_type == TransferType(transfer_type))
        except ValueError:
            pass
    if source_warehouse_id:
        query = query.filter(TransferOrder.source_warehouse_id == source_warehouse_id)
    if target_warehouse_id:
        query = query.filter(TransferOrder.target_warehouse_id == target_warehouse_id)
    if keyword:
        query = query.filter(or_(
            TransferOrder.order_no.ilike(f'%{keyword}%'),
            TransferOrder.reason.ilike(f'%{keyword}%'),
        ))
    if start_date:
        try:
            d = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(TransferOrder.planned_date >= d)
        except ValueError:
            pass
    if end_date:
        try:
            d = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(TransferOrder.planned_date <= d)
        except ValueError:
            pass

    # 排序：最新在前
    query = query.order_by(TransferOrder.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'items': [order.to_dict() for order in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    })


@transfer_bp.route('/<int:order_id>', methods=['GET'])
def get_transfer_order(order_id):
    """获取转移单详情"""
    order = TransferOrder.query.get_or_404(order_id)
    return jsonify(order.to_dict(include_items=True))


@transfer_bp.route('', methods=['POST'])
def create_transfer_order():
    """创建转移单"""
    data = request.get_json()

    # 验证必填字段
    required = ['source_warehouse_id', 'target_warehouse_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'缺少必填字段: {field}'}), 400

    # 验证源和目标不能相同（同仓库同库位）
    source_wh = data.get('source_warehouse_id')
    target_wh = data.get('target_warehouse_id')
    source_bin = data.get('source_bin_id')
    target_bin = data.get('target_bin_id')

    if source_wh == target_wh and source_bin == target_bin:
        return jsonify({'error': '源位置和目标位置不能相同'}), 400

    # 获取仓库信息
    source_warehouse = Warehouse.query.get(source_wh)
    target_warehouse = Warehouse.query.get(target_wh)
    if not source_warehouse:
        return jsonify({'error': '源仓库不存在'}), 400
    if not target_warehouse:
        return jsonify({'error': '目标仓库不存在'}), 400

    # 确定转移类型
    if source_wh == target_wh:
        transfer_type = TransferType.BIN
    elif source_bin or target_bin:
        transfer_type = TransferType.CROSS
    else:
        transfer_type = TransferType.WAREHOUSE

    # 创建转移单
    order = TransferOrder(
        order_no=generate_order_no(),
        transfer_type=transfer_type,
        status=TransferStatus.DRAFT,
        source_warehouse_id=source_wh,
        source_warehouse_name=source_warehouse.name,
        target_warehouse_id=target_wh,
        target_warehouse_name=target_warehouse.name,
        reason=data.get('reason'),
        remark=data.get('remark'),
        created_by=request.headers.get('User-ID'),
        created_by_name=data.get('created_by_name'),
    )

    # 源库位
    if source_bin:
        source_bin_obj = StorageBin.query.get(source_bin)
        if source_bin_obj:
            order.source_bin_id = source_bin
            order.source_bin_code = source_bin_obj.code

    # 目标库位
    if target_bin:
        target_bin_obj = StorageBin.query.get(target_bin)
        if target_bin_obj:
            order.target_bin_id = target_bin
            order.target_bin_code = target_bin_obj.code

    # 计划日期
    if data.get('planned_date'):
        try:
            order.planned_date = datetime.strptime(data['planned_date'], '%Y-%m-%d').date()
        except ValueError:
            pass

    db.session.add(order)
    db.session.flush()

    # 添加明细
    items_data = data.get('items', [])
    for i, item_data in enumerate(items_data, 1):
        material_id = item_data.get('material_id')
        if not material_id:
            continue

        material = Material.query.get(material_id)
        if not material:
            continue

        item = TransferOrderItem(
            order_id=order.id,
            line_no=i,
            material_id=material_id,
            material_code=material.code,
            material_name=material.name,
            specification=material.specification,
            planned_qty=Decimal(str(item_data.get('planned_qty', 0))),
            uom=item_data.get('uom') or material.base_uom or 'pcs',
            batch_no=item_data.get('batch_no'),
            serial_no=item_data.get('serial_no'),
            remark=item_data.get('remark'),
        )

        # 明细级别的源/目标库位
        if item_data.get('source_bin_id'):
            bin_obj = StorageBin.query.get(item_data['source_bin_id'])
            if bin_obj:
                item.source_bin_id = bin_obj.id
                item.source_bin_code = bin_obj.code
        if item_data.get('target_bin_id'):
            bin_obj = StorageBin.query.get(item_data['target_bin_id'])
            if bin_obj:
                item.target_bin_id = bin_obj.id
                item.target_bin_code = bin_obj.code

        db.session.add(item)

    # 更新统计
    order.update_totals()

    db.session.commit()

    return jsonify({
        'message': '转移单创建成功',
        'data': order.to_dict(include_items=True)
    }), 201


@transfer_bp.route('/<int:order_id>', methods=['PUT'])
def update_transfer_order(order_id):
    """更新转移单（仅草稿状态）"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status != TransferStatus.DRAFT:
        return jsonify({'error': '只能修改草稿状态的转移单'}), 400

    data = request.get_json()

    # 更新仓库信息
    if data.get('source_warehouse_id'):
        wh = Warehouse.query.get(data['source_warehouse_id'])
        if wh:
            order.source_warehouse_id = wh.id
            order.source_warehouse_name = wh.name
    if data.get('target_warehouse_id'):
        wh = Warehouse.query.get(data['target_warehouse_id'])
        if wh:
            order.target_warehouse_id = wh.id
            order.target_warehouse_name = wh.name

    # 更新库位信息
    if 'source_bin_id' in data:
        if data['source_bin_id']:
            bin_obj = StorageBin.query.get(data['source_bin_id'])
            if bin_obj:
                order.source_bin_id = bin_obj.id
                order.source_bin_code = bin_obj.code
        else:
            order.source_bin_id = None
            order.source_bin_code = None

    if 'target_bin_id' in data:
        if data['target_bin_id']:
            bin_obj = StorageBin.query.get(data['target_bin_id'])
            if bin_obj:
                order.target_bin_id = bin_obj.id
                order.target_bin_code = bin_obj.code
        else:
            order.target_bin_id = None
            order.target_bin_code = None

    # 更新其他字段
    if 'planned_date' in data:
        try:
            order.planned_date = datetime.strptime(data['planned_date'], '%Y-%m-%d').date() if data['planned_date'] else None
        except ValueError:
            pass
    if 'reason' in data:
        order.reason = data['reason']
    if 'remark' in data:
        order.remark = data['remark']

    # 重新确定转移类型
    if order.source_warehouse_id == order.target_warehouse_id:
        order.transfer_type = TransferType.BIN
    elif order.source_bin_id or order.target_bin_id:
        order.transfer_type = TransferType.CROSS
    else:
        order.transfer_type = TransferType.WAREHOUSE

    db.session.commit()

    return jsonify({
        'message': '转移单更新成功',
        'data': order.to_dict(include_items=True)
    })


@transfer_bp.route('/<int:order_id>', methods=['DELETE'])
def delete_transfer_order(order_id):
    """删除转移单（仅草稿/已取消状态）"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status not in [TransferStatus.DRAFT, TransferStatus.CANCELLED]:
        return jsonify({'error': '只能删除草稿或已取消的转移单'}), 400

    db.session.delete(order)
    db.session.commit()

    return jsonify({'message': '转移单删除成功'})


# ==================== 转移单状态操作 ====================

@transfer_bp.route('/<int:order_id>/submit', methods=['POST'])
def submit_transfer_order(order_id):
    """提交转移单"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status != TransferStatus.DRAFT:
        return jsonify({'error': '只能提交草稿状态的转移单'}), 400

    # 验证是否有明细
    if order.items.count() == 0:
        return jsonify({'error': '转移单必须包含至少一条明细'}), 400

    data = request.get_json() or {}

    order.status = TransferStatus.PENDING
    order.submitted_by = request.headers.get('User-ID')
    order.submitted_by_name = data.get('submitted_by_name')
    order.submitted_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'message': '转移单已提交',
        'data': order.to_dict()
    })


@transfer_bp.route('/<int:order_id>/cancel', methods=['POST'])
def cancel_transfer_order(order_id):
    """取消转移单"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status not in [TransferStatus.DRAFT, TransferStatus.PENDING]:
        return jsonify({'error': '只能取消草稿或待执行的转移单'}), 400

    order.status = TransferStatus.CANCELLED

    db.session.commit()

    return jsonify({
        'message': '转移单已取消',
        'data': order.to_dict()
    })


@transfer_bp.route('/<int:order_id>/execute', methods=['POST'])
def execute_transfer(order_id):
    """执行转移（支持部分转移）"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status not in [TransferStatus.PENDING, TransferStatus.IN_PROGRESS]:
        return jsonify({'error': '转移单状态不允许执行转移'}), 400

    data = request.get_json()
    items_to_transfer = data.get('items', [])

    if not items_to_transfer:
        return jsonify({'error': '请指定要转移的明细'}), 400

    operator_id = request.headers.get('User-ID')
    operator_name = data.get('executed_by_name', '')
    errors = []
    transferred_count = 0

    for item_data in items_to_transfer:
        item_id = item_data.get('item_id')
        transfer_qty = Decimal(str(item_data.get('transfer_qty', 0)))

        if not item_id or transfer_qty <= 0:
            continue

        item = TransferOrderItem.query.get(item_id)
        if not item or item.order_id != order.id:
            errors.append(f'明细 {item_id} 不存在')
            continue

        # 检查可转移数量
        remaining = (item.planned_qty or Decimal('0')) - (item.transferred_qty or Decimal('0'))
        if transfer_qty > remaining:
            errors.append(f'物料 {item.material_code} 转移数量超出剩余可转移数量')
            continue

        # 确定源位置
        source_wh_id = order.source_warehouse_id
        source_bin_id = item.source_bin_id or order.source_bin_id

        # 检查源库存
        inv_query = Inventory.query.filter(
            Inventory.material_id == item.material_id,
            Inventory.warehouse_id == source_wh_id
        )
        if source_bin_id:
            inv_query = inv_query.filter(Inventory.bin_id == source_bin_id)
        if item.batch_no:
            inv_query = inv_query.filter(Inventory.batch_no == item.batch_no)

        source_inventory = inv_query.first()
        if not source_inventory:
            errors.append(f'物料 {item.material_code} 在源位置无库存')
            continue

        available_qty = (source_inventory.available_qty or Decimal('0'))
        if transfer_qty > available_qty:
            errors.append(f'物料 {item.material_code} 可用库存不足 (可用: {available_qty})')
            continue

        # 确定目标位置
        target_wh_id = order.target_warehouse_id
        target_bin_id = item.target_bin_id or order.target_bin_id

        # 执行转移：1. 减少源库存
        source_inventory.quantity = (source_inventory.quantity or Decimal('0')) - transfer_qty
        source_inventory.available_qty = (source_inventory.available_qty or Decimal('0')) - transfer_qty
        source_inventory.last_out_date = datetime.utcnow()

        # 创建出库流水
        out_tx = InventoryTx(
            product_code=item.material_code,
            product_name=item.material_name,
            tx_type='transfer_out',
            tx_date=datetime.utcnow(),
            quantity=-float(transfer_qty),
            unit=item.uom,
            warehouse_id=source_wh_id,
            bin_id=source_bin_id,
            batch_no=item.batch_no,
            reference_no=order.order_no,
            reference_type='transfer',
            operator_name=operator_name,
            remark=f'转移出库 -> {order.target_warehouse_name}',
        )
        db.session.add(out_tx)
        db.session.flush()

        # 2. 增加目标库存
        target_inventory = Inventory.query.filter(
            Inventory.material_id == item.material_id,
            Inventory.warehouse_id == target_wh_id,
            Inventory.bin_id == target_bin_id if target_bin_id else True,
            Inventory.batch_no == item.batch_no if item.batch_no else True
        ).first()

        if target_inventory:
            target_inventory.quantity = (target_inventory.quantity or Decimal('0')) + transfer_qty
            target_inventory.available_qty = (target_inventory.available_qty or Decimal('0')) + transfer_qty
            target_inventory.last_in_date = datetime.utcnow()
        else:
            # 创建新的库存记录
            target_warehouse = Warehouse.query.get(target_wh_id)
            target_inventory = Inventory(
                material_id=item.material_id,
                material_code=item.material_code,
                warehouse_id=target_wh_id,
                bin_id=target_bin_id,
                batch_no=item.batch_no,
                serial_no=item.serial_no,
                quantity=transfer_qty,
                reserved_qty=Decimal('0'),
                available_qty=transfer_qty,
                uom=item.uom,
                last_in_date=datetime.utcnow(),
            )
            db.session.add(target_inventory)

        # 创建入库流水
        in_tx = InventoryTx(
            product_code=item.material_code,
            product_name=item.material_name,
            tx_type='transfer_in',
            tx_date=datetime.utcnow(),
            quantity=float(transfer_qty),
            unit=item.uom,
            warehouse_id=target_wh_id,
            bin_id=target_bin_id,
            batch_no=item.batch_no,
            reference_no=order.order_no,
            reference_type='transfer',
            operator_name=operator_name,
            remark=f'转移入库 <- {order.source_warehouse_name}',
        )
        db.session.add(in_tx)
        db.session.flush()

        # 3. 更新明细
        item.transferred_qty = (item.transferred_qty or Decimal('0')) + transfer_qty
        item.transferred_at = datetime.utcnow()
        item.transferred_by = operator_id
        item.transferred_by_name = operator_name
        item.update_status()

        # 4. 记录转移日志
        log = TransferLog(
            order_id=order.id,
            item_id=item.id,
            material_code=item.material_code,
            material_name=item.material_name,
            transfer_qty=transfer_qty,
            uom=item.uom,
            batch_no=item.batch_no,
            source_warehouse_name=order.source_warehouse_name,
            source_bin_code=item.source_bin_code or order.source_bin_code,
            target_warehouse_name=order.target_warehouse_name,
            target_bin_code=item.target_bin_code or order.target_bin_code,
            executed_by=operator_id,
            executed_by_name=operator_name,
            executed_at=datetime.utcnow(),
            inventory_tx_out_id=out_tx.id,
            inventory_tx_in_id=in_tx.id,
        )
        db.session.add(log)

        transferred_count += 1

    # 更新转移单状态
    order.update_totals()
    order.executed_by = operator_id
    order.executed_by_name = operator_name
    order.actual_date = date.today()

    # 检查是否全部完成
    if order.check_completion():
        pass  # 状态已在方法中更新
    elif order.status == TransferStatus.PENDING:
        order.status = TransferStatus.IN_PROGRESS

    db.session.commit()

    result = {
        'message': f'成功转移 {transferred_count} 条明细',
        'data': order.to_dict(include_items=True),
    }
    if errors:
        result['errors'] = errors

    return jsonify(result)


@transfer_bp.route('/<int:order_id>/complete', methods=['POST'])
def complete_transfer_order(order_id):
    """强制完成转移单"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status not in [TransferStatus.IN_PROGRESS, TransferStatus.PENDING]:
        return jsonify({'error': '转移单状态不允许完成'}), 400

    order.status = TransferStatus.COMPLETED
    order.completed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'message': '转移单已完成',
        'data': order.to_dict()
    })


# ==================== 转移单明细操作 ====================

@transfer_bp.route('/<int:order_id>/items', methods=['GET'])
def get_transfer_items(order_id):
    """获取转移单明细列表"""
    order = TransferOrder.query.get_or_404(order_id)
    items = order.items.order_by(TransferOrderItem.line_no).all()
    return jsonify([item.to_dict() for item in items])


@transfer_bp.route('/<int:order_id>/items', methods=['POST'])
def add_transfer_item(order_id):
    """添加转移单明细"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status != TransferStatus.DRAFT:
        return jsonify({'error': '只能修改草稿状态的转移单'}), 400

    data = request.get_json()

    material_id = data.get('material_id')
    if not material_id:
        return jsonify({'error': '请指定物料'}), 400

    material = Material.query.get(material_id)
    if not material:
        return jsonify({'error': '物料不存在'}), 400

    # 获取下一个行号
    max_line = db.session.query(func.max(TransferOrderItem.line_no)).filter(
        TransferOrderItem.order_id == order_id
    ).scalar() or 0

    item = TransferOrderItem(
        order_id=order.id,
        line_no=max_line + 1,
        material_id=material_id,
        material_code=material.code,
        material_name=material.name,
        specification=material.specification,
        planned_qty=Decimal(str(data.get('planned_qty', 0))),
        uom=data.get('uom') or material.base_uom or 'pcs',
        batch_no=data.get('batch_no'),
        serial_no=data.get('serial_no'),
        remark=data.get('remark'),
    )

    # 明细级别的库位
    if data.get('source_bin_id'):
        bin_obj = StorageBin.query.get(data['source_bin_id'])
        if bin_obj:
            item.source_bin_id = bin_obj.id
            item.source_bin_code = bin_obj.code
    if data.get('target_bin_id'):
        bin_obj = StorageBin.query.get(data['target_bin_id'])
        if bin_obj:
            item.target_bin_id = bin_obj.id
            item.target_bin_code = bin_obj.code

    db.session.add(item)
    order.update_totals()
    db.session.commit()

    return jsonify({
        'message': '明细添加成功',
        'data': item.to_dict()
    }), 201


@transfer_bp.route('/<int:order_id>/items/<int:item_id>', methods=['PUT'])
def update_transfer_item(order_id, item_id):
    """更新转移单明细"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status != TransferStatus.DRAFT:
        return jsonify({'error': '只能修改草稿状态的转移单'}), 400

    item = TransferOrderItem.query.filter_by(id=item_id, order_id=order_id).first()
    if not item:
        return jsonify({'error': '明细不存在'}), 404

    data = request.get_json()

    if 'planned_qty' in data:
        item.planned_qty = Decimal(str(data['planned_qty']))
    if 'uom' in data:
        item.uom = data['uom']
    if 'batch_no' in data:
        item.batch_no = data['batch_no']
    if 'serial_no' in data:
        item.serial_no = data['serial_no']
    if 'remark' in data:
        item.remark = data['remark']

    # 更新库位
    if 'source_bin_id' in data:
        if data['source_bin_id']:
            bin_obj = StorageBin.query.get(data['source_bin_id'])
            if bin_obj:
                item.source_bin_id = bin_obj.id
                item.source_bin_code = bin_obj.code
        else:
            item.source_bin_id = None
            item.source_bin_code = None

    if 'target_bin_id' in data:
        if data['target_bin_id']:
            bin_obj = StorageBin.query.get(data['target_bin_id'])
            if bin_obj:
                item.target_bin_id = bin_obj.id
                item.target_bin_code = bin_obj.code
        else:
            item.target_bin_id = None
            item.target_bin_code = None

    order.update_totals()
    db.session.commit()

    return jsonify({
        'message': '明细更新成功',
        'data': item.to_dict()
    })


@transfer_bp.route('/<int:order_id>/items/<int:item_id>', methods=['DELETE'])
def delete_transfer_item(order_id, item_id):
    """删除转移单明细"""
    order = TransferOrder.query.get_or_404(order_id)

    if order.status != TransferStatus.DRAFT:
        return jsonify({'error': '只能修改草稿状态的转移单'}), 400

    item = TransferOrderItem.query.filter_by(id=item_id, order_id=order_id).first()
    if not item:
        return jsonify({'error': '明细不存在'}), 404

    db.session.delete(item)
    order.update_totals()
    db.session.commit()

    return jsonify({'message': '明细删除成功'})


# ==================== 转移日志 ====================

@transfer_bp.route('/<int:order_id>/logs', methods=['GET'])
def get_transfer_logs(order_id):
    """获取转移执行日志"""
    order = TransferOrder.query.get_or_404(order_id)
    logs = TransferLog.query.filter_by(order_id=order_id).order_by(TransferLog.executed_at.desc()).all()
    return jsonify([log.to_dict() for log in logs])


# ==================== 统计和枚举 ====================

@transfer_bp.route('/types', methods=['GET'])
def get_transfer_types():
    """获取转移类型枚举"""
    return jsonify([
        {'value': t.value, 'label': TRANSFER_TYPE_MAP.get(t.value, t.value)}
        for t in TransferType
    ])


@transfer_bp.route('/statuses', methods=['GET'])
def get_transfer_statuses():
    """获取转移状态枚举"""
    return jsonify([
        {'value': s.value, 'label': TRANSFER_STATUS_MAP.get(s.value, s.value)}
        for s in TransferStatus
    ])


@transfer_bp.route('/statistics', methods=['GET'])
def get_transfer_statistics():
    """获取转移统计"""
    # 按状态统计
    status_stats = db.session.query(
        TransferOrder.status,
        func.count(TransferOrder.id).label('count')
    ).group_by(TransferOrder.status).all()

    by_status = {
        s.value: {'count': 0, 'label': TRANSFER_STATUS_MAP.get(s.value, s.value)}
        for s in TransferStatus
    }
    for stat in status_stats:
        if stat.status:
            by_status[stat.status.value]['count'] = stat.count

    # 本月统计
    today = date.today()
    first_day = today.replace(day=1)

    this_month_count = TransferOrder.query.filter(
        TransferOrder.created_at >= datetime(first_day.year, first_day.month, first_day.day)
    ).count()

    completed_this_month = TransferOrder.query.filter(
        TransferOrder.status == TransferStatus.COMPLETED,
        TransferOrder.completed_at >= datetime(first_day.year, first_day.month, first_day.day)
    ).count()

    # 待处理
    pending_count = TransferOrder.query.filter(
        TransferOrder.status.in_([TransferStatus.PENDING, TransferStatus.IN_PROGRESS])
    ).count()

    return jsonify({
        'by_status': by_status,
        'total': sum(s['count'] for s in by_status.values()),
        'this_month': this_month_count,
        'completed_this_month': completed_this_month,
        'pending': pending_count,
    })


# ==================== 快速转移 ====================

@transfer_bp.route('/quick', methods=['POST'])
def quick_transfer():
    """快速转移（创建并立即执行）"""
    data = request.get_json()

    required = ['source_warehouse_id', 'target_warehouse_id', 'items']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'缺少必填字段: {field}'}), 400

    # 验证源和目标
    source_wh = data.get('source_warehouse_id')
    target_wh = data.get('target_warehouse_id')
    source_bin = data.get('source_bin_id')
    target_bin = data.get('target_bin_id')

    if source_wh == target_wh and source_bin == target_bin:
        return jsonify({'error': '源位置和目标位置不能相同'}), 400

    source_warehouse = Warehouse.query.get(source_wh)
    target_warehouse = Warehouse.query.get(target_wh)
    if not source_warehouse:
        return jsonify({'error': '源仓库不存在'}), 400
    if not target_warehouse:
        return jsonify({'error': '目标仓库不存在'}), 400

    # 确定转移类型
    if source_wh == target_wh:
        transfer_type = TransferType.BIN
    elif source_bin or target_bin:
        transfer_type = TransferType.CROSS
    else:
        transfer_type = TransferType.WAREHOUSE

    operator_id = request.headers.get('User-ID')
    operator_name = data.get('executed_by_name', '')

    # 创建转移单
    order = TransferOrder(
        order_no=generate_order_no(),
        transfer_type=transfer_type,
        status=TransferStatus.PENDING,
        source_warehouse_id=source_wh,
        source_warehouse_name=source_warehouse.name,
        target_warehouse_id=target_wh,
        target_warehouse_name=target_warehouse.name,
        reason=data.get('reason'),
        remark=data.get('remark'),
        created_by=operator_id,
        created_by_name=operator_name,
        submitted_by=operator_id,
        submitted_by_name=operator_name,
        submitted_at=datetime.utcnow(),
        planned_date=date.today(),
    )

    if source_bin:
        bin_obj = StorageBin.query.get(source_bin)
        if bin_obj:
            order.source_bin_id = source_bin
            order.source_bin_code = bin_obj.code
    if target_bin:
        bin_obj = StorageBin.query.get(target_bin)
        if bin_obj:
            order.target_bin_id = target_bin
            order.target_bin_code = bin_obj.code

    db.session.add(order)
    db.session.flush()

    # 添加明细并直接执行
    items_data = data.get('items', [])
    errors = []
    transferred_count = 0

    for i, item_data in enumerate(items_data, 1):
        material_id = item_data.get('material_id')
        transfer_qty = Decimal(str(item_data.get('qty', 0)))

        if not material_id or transfer_qty <= 0:
            continue

        material = Material.query.get(material_id)
        if not material:
            errors.append(f'物料 ID {material_id} 不存在')
            continue

        # 确定源库位
        item_source_bin_id = item_data.get('source_bin_id') or source_bin
        item_target_bin_id = item_data.get('target_bin_id') or target_bin
        batch_no = item_data.get('batch_no')

        # 检查源库存
        inv_query = Inventory.query.filter(
            Inventory.material_id == material_id,
            Inventory.warehouse_id == source_wh
        )
        if item_source_bin_id:
            inv_query = inv_query.filter(Inventory.bin_id == item_source_bin_id)
        if batch_no:
            inv_query = inv_query.filter(Inventory.batch_no == batch_no)

        source_inventory = inv_query.first()
        if not source_inventory:
            errors.append(f'物料 {material.code} 在源位置无库存')
            continue

        available_qty = (source_inventory.available_qty or Decimal('0'))
        if transfer_qty > available_qty:
            errors.append(f'物料 {material.code} 可用库存不足')
            continue

        # 创建明细
        item = TransferOrderItem(
            order_id=order.id,
            line_no=i,
            material_id=material_id,
            material_code=material.code,
            material_name=material.name,
            specification=material.specification,
            planned_qty=transfer_qty,
            transferred_qty=transfer_qty,
            uom=item_data.get('uom') or material.base_uom or 'pcs',
            batch_no=batch_no,
            item_status='completed',
            transferred_at=datetime.utcnow(),
            transferred_by=operator_id,
            transferred_by_name=operator_name,
        )

        if item_source_bin_id:
            bin_obj = StorageBin.query.get(item_source_bin_id)
            if bin_obj:
                item.source_bin_id = bin_obj.id
                item.source_bin_code = bin_obj.code
        if item_target_bin_id:
            bin_obj = StorageBin.query.get(item_target_bin_id)
            if bin_obj:
                item.target_bin_id = bin_obj.id
                item.target_bin_code = bin_obj.code

        db.session.add(item)
        db.session.flush()

        # 执行转移
        # 1. 减少源库存
        source_inventory.quantity = (source_inventory.quantity or Decimal('0')) - transfer_qty
        source_inventory.available_qty = (source_inventory.available_qty or Decimal('0')) - transfer_qty
        source_inventory.last_out_date = datetime.utcnow()

        # 创建出库流水
        out_tx = InventoryTx(
            product_code=material.code,
            product_name=material.name,
            tx_type='transfer_out',
            tx_date=datetime.utcnow(),
            quantity=-float(transfer_qty),
            unit=item.uom,
            warehouse_id=source_wh,
            bin_id=item_source_bin_id,
            batch_no=batch_no,
            reference_no=order.order_no,
            reference_type='transfer',
            operator_name=operator_name,
            remark=f'快速转移出库 -> {target_warehouse.name}',
        )
        db.session.add(out_tx)
        db.session.flush()

        # 2. 增加目标库存
        target_inventory = Inventory.query.filter(
            Inventory.material_id == material_id,
            Inventory.warehouse_id == target_wh,
            Inventory.bin_id == item_target_bin_id if item_target_bin_id else True,
            Inventory.batch_no == batch_no if batch_no else True
        ).first()

        if target_inventory:
            target_inventory.quantity = (target_inventory.quantity or Decimal('0')) + transfer_qty
            target_inventory.available_qty = (target_inventory.available_qty or Decimal('0')) + transfer_qty
            target_inventory.last_in_date = datetime.utcnow()
        else:
            target_inventory = Inventory(
                material_id=material_id,
                material_code=material.code,
                warehouse_id=target_wh,
                bin_id=item_target_bin_id,
                batch_no=batch_no,
                quantity=transfer_qty,
                reserved_qty=Decimal('0'),
                available_qty=transfer_qty,
                uom=item.uom,
                last_in_date=datetime.utcnow(),
            )
            db.session.add(target_inventory)

        # 创建入库流水
        in_tx = InventoryTx(
            product_code=material.code,
            product_name=material.name,
            tx_type='transfer_in',
            tx_date=datetime.utcnow(),
            quantity=float(transfer_qty),
            unit=item.uom,
            warehouse_id=target_wh,
            bin_id=item_target_bin_id,
            batch_no=batch_no,
            reference_no=order.order_no,
            reference_type='transfer',
            operator_name=operator_name,
            remark=f'快速转移入库 <- {source_warehouse.name}',
        )
        db.session.add(in_tx)
        db.session.flush()

        # 记录日志
        log = TransferLog(
            order_id=order.id,
            item_id=item.id,
            material_code=material.code,
            material_name=material.name,
            transfer_qty=transfer_qty,
            uom=item.uom,
            batch_no=batch_no,
            source_warehouse_name=source_warehouse.name,
            source_bin_code=item.source_bin_code,
            target_warehouse_name=target_warehouse.name,
            target_bin_code=item.target_bin_code,
            executed_by=operator_id,
            executed_by_name=operator_name,
            executed_at=datetime.utcnow(),
            inventory_tx_out_id=out_tx.id,
            inventory_tx_in_id=in_tx.id,
        )
        db.session.add(log)

        transferred_count += 1

    # 更新转移单
    order.update_totals()
    order.executed_by = operator_id
    order.executed_by_name = operator_name
    order.actual_date = date.today()

    if transferred_count > 0:
        order.status = TransferStatus.COMPLETED
        order.completed_at = datetime.utcnow()
    else:
        order.status = TransferStatus.CANCELLED

    db.session.commit()

    result = {
        'message': f'快速转移完成，成功转移 {transferred_count} 项',
        'data': order.to_dict(include_items=True),
    }
    if errors:
        result['errors'] = errors

    return jsonify(result), 201 if transferred_count > 0 else 400
