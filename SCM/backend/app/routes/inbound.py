# backend/app/routes/inbound.py
"""
入库管理 API 路由
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import or_, func
from app import db
from app.models.inbound import (
    InboundOrder, InboundOrderItem, InboundReceiveLog,
    InboundStatus, InboundType,
    INBOUND_STATUS_MAP, INBOUND_TYPE_MAP
)
from app.models.material import Material, Warehouse, StorageBin, Inventory
from app.models.inventory import InventoryTx

inbound_bp = Blueprint('inbound', __name__, url_prefix='/api/inbound')


# ============== 入库单 API ==============

@inbound_bp.route('', methods=['GET'])
def get_inbound_orders():
    """获取入库单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '').strip()
        status = request.args.get('status', '')
        inbound_type = request.args.get('inbound_type', '')
        warehouse_id = request.args.get('warehouse_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        query = InboundOrder.query

        # 关键字搜索
        if keyword:
            query = query.filter(or_(
                InboundOrder.order_no.ilike(f'%{keyword}%'),
                InboundOrder.source_no.ilike(f'%{keyword}%'),
                InboundOrder.supplier_name.ilike(f'%{keyword}%'),
            ))

        # 状态筛选
        if status:
            try:
                query = query.filter(InboundOrder.status == InboundStatus(status))
            except ValueError:
                pass

        # 类型筛选
        if inbound_type:
            try:
                query = query.filter(InboundOrder.inbound_type == InboundType(inbound_type))
            except ValueError:
                pass

        # 仓库筛选
        if warehouse_id:
            query = query.filter(InboundOrder.warehouse_id == warehouse_id)

        # 日期筛选
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(InboundOrder.created_at >= start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(InboundOrder.created_at < end)
            except ValueError:
                pass

        # 排序
        query = query.order_by(InboundOrder.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return jsonify({
            "success": True,
            "data": {
                "items": [order.to_dict() for order in pagination.items],
                "total": pagination.total,
                "page": page,
                "page_size": page_size,
                "pages": pagination.pages
            }
        })
    except Exception as e:
        current_app.logger.exception("获取入库单列表失败")
        return jsonify({"success": False, "error": str(e)}), 500


@inbound_bp.route('/<int:id>', methods=['GET'])
def get_inbound_order(id):
    """获取入库单详情"""
    try:
        order = InboundOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "入库单不存在"}), 404

        return jsonify({
            "success": True,
            "data": order.to_dict(include_items=True)
        })
    except Exception as e:
        current_app.logger.exception("获取入库单详情失败")
        return jsonify({"success": False, "error": str(e)}), 500


@inbound_bp.route('', methods=['POST'])
def create_inbound_order():
    """创建入库单"""
    try:
        data = request.get_json()

        # 获取入库类型
        inbound_type = data.get('inbound_type', 'purchase')

        # 验证仓库
        warehouse_id = data.get('warehouse_id')
        if not warehouse_id:
            return jsonify({"success": False, "error": "请选择目标仓库"}), 400

        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return jsonify({"success": False, "error": "仓库不存在"}), 400

        # 创建入库单
        order = InboundOrder(
            order_no=InboundOrder.generate_order_no(inbound_type),
            inbound_type=InboundType(inbound_type),
            status=InboundStatus.DRAFT,
            source_no=data.get('source_no'),
            source_system=data.get('source_system'),
            supplier_id=data.get('supplier_id'),
            supplier_name=data.get('supplier_name'),
            warehouse_id=warehouse_id,
            warehouse_name=warehouse.name,
            planned_date=datetime.strptime(data['planned_date'], '%Y-%m-%d').date() if data.get('planned_date') else None,
            remark=data.get('remark'),
            created_by=data.get('created_by'),
            created_by_name=data.get('created_by_name'),
        )

        db.session.add(order)
        db.session.flush()  # 获取 order.id

        # 创建明细
        items = data.get('items', [])
        total_planned_qty = 0

        for idx, item_data in enumerate(items, start=1):
            material_id = item_data.get('material_id')
            material = Material.query.get(material_id) if material_id else None

            planned_qty = float(item_data.get('planned_qty', 0))
            total_planned_qty += planned_qty

            item = InboundOrderItem(
                order_id=order.id,
                line_no=idx,
                material_id=material_id,
                material_code=item_data.get('material_code') or (material.code if material else ''),
                material_name=item_data.get('material_name') or (material.name if material else ''),
                specification=item_data.get('specification') or (material.specification if material else ''),
                planned_qty=planned_qty,
                uom=item_data.get('uom') or (material.base_uom if material else 'pcs'),
                bin_id=item_data.get('bin_id'),
                bin_code=item_data.get('bin_code'),
                batch_no=item_data.get('batch_no'),
                production_date=datetime.strptime(item_data['production_date'], '%Y-%m-%d').date() if item_data.get('production_date') else None,
                expiry_date=datetime.strptime(item_data['expiry_date'], '%Y-%m-%d').date() if item_data.get('expiry_date') else None,
                unit_price=item_data.get('unit_price'),
                source_line_no=item_data.get('source_line_no'),
                source_item_id=item_data.get('source_item_id'),
                remark=item_data.get('remark'),
            )

            # 计算金额
            if item.unit_price and item.planned_qty:
                item.amount = float(item.unit_price) * float(item.planned_qty)

            db.session.add(item)

        # 更新总数量
        order.total_planned_qty = total_planned_qty

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "入库单创建成功",
            "data": order.to_dict(include_items=True)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("创建入库单失败")
        return jsonify({"success": False, "error": str(e)}), 500


@inbound_bp.route('/<int:id>', methods=['PUT'])
def update_inbound_order(id):
    """更新入库单（仅草稿状态可编辑）"""
    try:
        order = InboundOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "入库单不存在"}), 404

        if order.status != InboundStatus.DRAFT:
            return jsonify({"success": False, "error": "只有草稿状态的入库单可以编辑"}), 400

        data = request.get_json()

        # 更新仓库
        if 'warehouse_id' in data:
            warehouse = Warehouse.query.get(data['warehouse_id'])
            if warehouse:
                order.warehouse_id = warehouse.id
                order.warehouse_name = warehouse.name

        # 更新其他字段
        if 'source_no' in data:
            order.source_no = data['source_no']
        if 'supplier_id' in data:
            order.supplier_id = data['supplier_id']
        if 'supplier_name' in data:
            order.supplier_name = data['supplier_name']
        if 'planned_date' in data and data['planned_date']:
            order.planned_date = datetime.strptime(data['planned_date'], '%Y-%m-%d').date()
        if 'remark' in data:
            order.remark = data['remark']

        # 更新明细
        if 'items' in data:
            # 删除原有明细
            InboundOrderItem.query.filter_by(order_id=order.id).delete()

            # 创建新明细
            total_planned_qty = 0
            for idx, item_data in enumerate(data['items'], start=1):
                material_id = item_data.get('material_id')
                material = Material.query.get(material_id) if material_id else None

                planned_qty = float(item_data.get('planned_qty', 0))
                total_planned_qty += planned_qty

                item = InboundOrderItem(
                    order_id=order.id,
                    line_no=idx,
                    material_id=material_id,
                    material_code=item_data.get('material_code') or (material.code if material else ''),
                    material_name=item_data.get('material_name') or (material.name if material else ''),
                    specification=item_data.get('specification') or (material.specification if material else ''),
                    planned_qty=planned_qty,
                    uom=item_data.get('uom') or (material.base_uom if material else 'pcs'),
                    bin_id=item_data.get('bin_id'),
                    bin_code=item_data.get('bin_code'),
                    batch_no=item_data.get('batch_no'),
                    production_date=datetime.strptime(item_data['production_date'], '%Y-%m-%d').date() if item_data.get('production_date') else None,
                    expiry_date=datetime.strptime(item_data['expiry_date'], '%Y-%m-%d').date() if item_data.get('expiry_date') else None,
                    unit_price=item_data.get('unit_price'),
                    source_line_no=item_data.get('source_line_no'),
                    source_item_id=item_data.get('source_item_id'),
                    remark=item_data.get('remark'),
                )

                if item.unit_price and item.planned_qty:
                    item.amount = float(item.unit_price) * float(item.planned_qty)

                db.session.add(item)

            order.total_planned_qty = total_planned_qty

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "入库单更新成功",
            "data": order.to_dict(include_items=True)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("更新入库单失败")
        return jsonify({"success": False, "error": str(e)}), 500


@inbound_bp.route('/<int:id>', methods=['DELETE'])
def delete_inbound_order(id):
    """删除入库单（仅草稿状态可删除）"""
    try:
        order = InboundOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "入库单不存在"}), 404

        if order.status != InboundStatus.DRAFT:
            return jsonify({"success": False, "error": "只有草稿状态的入库单可以删除"}), 400

        db.session.delete(order)
        db.session.commit()

        return jsonify({"success": True, "message": "入库单已删除"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("删除入库单失败")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 状态流转 API ==============

@inbound_bp.route('/<int:id>/submit', methods=['POST'])
def submit_inbound_order(id):
    """提交入库单（草稿 -> 待入库）"""
    try:
        order = InboundOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "入库单不存在"}), 404

        if order.status != InboundStatus.DRAFT:
            return jsonify({"success": False, "error": "只有草稿状态的入库单可以提交"}), 400

        # 检查是否有明细
        if order.items.count() == 0:
            return jsonify({"success": False, "error": "入库单没有明细，无法提交"}), 400

        order.status = InboundStatus.PENDING
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "入库单已提交",
            "data": order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("提交入库单失败")
        return jsonify({"success": False, "error": str(e)}), 500


@inbound_bp.route('/<int:id>/cancel', methods=['POST'])
def cancel_inbound_order(id):
    """取消入库单"""
    try:
        order = InboundOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "入库单不存在"}), 404

        if order.status == InboundStatus.COMPLETED:
            return jsonify({"success": False, "error": "已完成的入库单无法取消"}), 400

        if order.status == InboundStatus.CANCELLED:
            return jsonify({"success": False, "error": "入库单已取消"}), 400

        # 检查是否有已收货的记录
        if float(order.total_received_qty or 0) > 0:
            return jsonify({"success": False, "error": "已有收货记录，无法取消"}), 400

        order.status = InboundStatus.CANCELLED
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "入库单已取消",
            "data": order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("取消入库单失败")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 收货 API ==============

@inbound_bp.route('/<int:id>/receive', methods=['POST'])
def receive_inbound_order(id):
    """执行入库收货"""
    try:
        order = InboundOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "入库单不存在"}), 404

        if order.status not in [InboundStatus.PENDING, InboundStatus.PARTIAL]:
            return jsonify({"success": False, "error": "入库单状态不允许收货"}), 400

        data = request.get_json()
        items_data = data.get('items', [])
        received_by = data.get('received_by')
        received_by_name = data.get('received_by_name')

        if not items_data:
            return jsonify({"success": False, "error": "请提供收货明细"}), 400

        total_received_this_time = 0

        for item_data in items_data:
            item_id = item_data.get('item_id')
            received_qty = float(item_data.get('received_qty', 0))
            rejected_qty = float(item_data.get('rejected_qty', 0))

            if received_qty <= 0 and rejected_qty <= 0:
                continue

            item = InboundOrderItem.query.get(item_id)
            if not item or item.order_id != order.id:
                continue

            # 更新明细收货数量
            item.received_qty = float(item.received_qty or 0) + received_qty
            item.rejected_qty = float(item.rejected_qty or 0) + rejected_qty

            # 更新库位信息
            if item_data.get('bin_id'):
                item.bin_id = item_data['bin_id']
                bin_obj = StorageBin.query.get(item_data['bin_id'])
                if bin_obj:
                    item.bin_code = bin_obj.code

            if item_data.get('batch_no'):
                item.batch_no = item_data['batch_no']

            total_received_this_time += received_qty

            # 创建收货记录
            log = InboundReceiveLog(
                order_id=order.id,
                item_id=item.id,
                received_qty=received_qty,
                rejected_qty=rejected_qty,
                bin_id=item.bin_id,
                bin_code=item.bin_code,
                batch_no=item.batch_no,
                received_by=received_by,
                received_by_name=received_by_name,
            )
            db.session.add(log)

            # 更新库存汇总表
            if received_qty > 0:
                inventory = Inventory.query.filter_by(
                    material_id=item.material_id,
                    warehouse_id=order.warehouse_id,
                    bin_id=item.bin_id,
                    batch_no=item.batch_no or ''
                ).first()

                if inventory:
                    inventory.quantity = float(inventory.quantity or 0) + received_qty
                    inventory.available_qty = float(inventory.available_qty or 0) + received_qty
                    inventory.last_in_date = datetime.utcnow()
                else:
                    inventory = Inventory(
                        material_id=item.material_id,
                        warehouse_id=order.warehouse_id,
                        bin_id=item.bin_id,
                        batch_no=item.batch_no or '',
                        quantity=received_qty,
                        available_qty=received_qty,
                        uom=item.uom,
                        production_date=item.production_date,
                        expiry_date=item.expiry_date,
                        last_in_date=datetime.utcnow(),
                    )
                    db.session.add(inventory)

                # 创建库存流水
                tx = InventoryTx(
                    product_text=item.material_code,
                    qty_delta=received_qty,
                    tx_type='入库',
                    order_no=order.order_no,
                    bin_code=item.bin_code,
                    uom=item.uom,
                    ref=f"入库单明细#{item.id}",
                    remark=f"入库单 {order.order_no} 收货",
                )
                db.session.add(tx)
                db.session.flush()

                # 记录流水ID
                log.inventory_tx_id = tx.id

        # 更新入库单总数量
        order.total_received_qty = float(order.total_received_qty or 0) + total_received_this_time

        # 更新状态
        if float(order.total_received_qty) >= float(order.total_planned_qty):
            order.status = InboundStatus.COMPLETED
            order.actual_date = datetime.utcnow().date()
        else:
            order.status = InboundStatus.PARTIAL

        # 更新收货人
        order.received_by = received_by
        order.received_by_name = received_by_name

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "收货成功",
            "data": order.to_dict(include_items=True)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("收货失败")
        return jsonify({"success": False, "error": str(e)}), 500


@inbound_bp.route('/<int:id>/receive-logs', methods=['GET'])
def get_receive_logs(id):
    """获取入库单收货记录"""
    try:
        order = InboundOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "入库单不存在"}), 404

        logs = InboundReceiveLog.query.filter_by(order_id=id).order_by(InboundReceiveLog.received_at.desc()).all()

        return jsonify({
            "success": True,
            "data": [log.to_dict() for log in logs]
        })
    except Exception as e:
        current_app.logger.exception("获取收货记录失败")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 辅助 API ==============

@inbound_bp.route('/types', methods=['GET'])
def get_inbound_types():
    """获取入库类型列表"""
    return jsonify({
        "success": True,
        "data": [
            {"value": key, "label": value}
            for key, value in INBOUND_TYPE_MAP.items()
        ]
    })


@inbound_bp.route('/statuses', methods=['GET'])
def get_inbound_statuses():
    """获取入库单状态列表"""
    return jsonify({
        "success": True,
        "data": [
            {"value": key, "label": value}
            for key, value in INBOUND_STATUS_MAP.items()
        ]
    })


@inbound_bp.route('/statistics', methods=['GET'])
def get_inbound_statistics():
    """获取入库统计"""
    try:
        # 今日入库
        today = datetime.utcnow().date()
        today_count = InboundOrder.query.filter(
            func.DATE(InboundOrder.created_at) == today
        ).count()

        # 待入库
        pending_count = InboundOrder.query.filter(
            InboundOrder.status == InboundStatus.PENDING
        ).count()

        # 部分入库
        partial_count = InboundOrder.query.filter(
            InboundOrder.status == InboundStatus.PARTIAL
        ).count()

        # 本月入库
        from datetime import timedelta
        month_start = today.replace(day=1)
        month_count = InboundOrder.query.filter(
            InboundOrder.status == InboundStatus.COMPLETED,
            InboundOrder.actual_date >= month_start
        ).count()

        return jsonify({
            "success": True,
            "data": {
                "today_count": today_count,
                "pending_count": pending_count,
                "partial_count": partial_count,
                "month_completed_count": month_count,
            }
        })
    except Exception as e:
        current_app.logger.exception("获取入库统计失败")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 采购入库关联 API ==============

@inbound_bp.route('/from-po', methods=['POST'])
def create_from_purchase_order():
    """从采购订单创建入库单"""
    try:
        data = request.get_json()

        po_number = data.get('po_number')
        if not po_number:
            return jsonify({"success": False, "error": "请提供采购订单号"}), 400

        # 检查是否已有该 PO 的入库单
        existing = InboundOrder.query.filter_by(
            source_no=po_number,
            source_system='采购'
        ).filter(InboundOrder.status != InboundStatus.CANCELLED).first()

        if existing:
            return jsonify({
                "success": False,
                "error": f"采购订单 {po_number} 已有入库单 {existing.order_no}"
            }), 400

        # 验证仓库
        warehouse_id = data.get('warehouse_id')
        if not warehouse_id:
            return jsonify({"success": False, "error": "请选择目标仓库"}), 400

        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return jsonify({"success": False, "error": "仓库不存在"}), 400

        # 创建入库单
        order = InboundOrder(
            order_no=InboundOrder.generate_order_no('purchase'),
            inbound_type=InboundType.PURCHASE,
            status=InboundStatus.DRAFT,
            source_no=po_number,
            source_system='采购',
            supplier_id=data.get('supplier_id'),
            supplier_name=data.get('supplier_name'),
            warehouse_id=warehouse_id,
            warehouse_name=warehouse.name,
            planned_date=datetime.strptime(data['planned_date'], '%Y-%m-%d').date() if data.get('planned_date') else None,
            remark=data.get('remark'),
            created_by=data.get('created_by'),
            created_by_name=data.get('created_by_name'),
        )

        db.session.add(order)
        db.session.flush()

        # 创建明细
        items = data.get('items', [])
        total_planned_qty = 0

        for idx, item_data in enumerate(items, start=1):
            # 尝试根据物料编码查找物料
            material_code = item_data.get('material_code', '')
            material = Material.query.filter_by(code=material_code).first() if material_code else None

            planned_qty = float(item_data.get('quantity', 0))
            total_planned_qty += planned_qty

            item = InboundOrderItem(
                order_id=order.id,
                line_no=idx,
                material_id=material.id if material else None,
                material_code=material_code,
                material_name=item_data.get('material_name', ''),
                specification=item_data.get('specification', ''),
                planned_qty=planned_qty,
                uom=item_data.get('uom', 'pcs'),
                unit_price=item_data.get('unit_price'),
                source_line_no=item_data.get('line_no'),
                source_item_id=item_data.get('item_id'),
                remark=item_data.get('remark'),
            )

            if item.unit_price and item.planned_qty:
                item.amount = float(item.unit_price) * float(item.planned_qty)

            db.session.add(item)

        order.total_planned_qty = total_planned_qty

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"已从采购订单 {po_number} 创建入库单",
            "data": order.to_dict(include_items=True)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("从采购订单创建入库单失败")
        return jsonify({"success": False, "error": str(e)}), 500


@inbound_bp.route('/pending-po', methods=['GET'])
def get_pending_purchase_orders():
    """获取待入库的采购订单列表

    此 API 返回模拟数据，实际使用时应该调用采购系统的 API
    """
    try:
        # 获取已创建入库单的 PO 号
        existing_pos = db.session.query(InboundOrder.source_no).filter(
            InboundOrder.source_system == '采购',
            InboundOrder.status != InboundStatus.CANCELLED
        ).all()
        existing_po_numbers = [po[0] for po in existing_pos if po[0]]

        # 返回示例数据 - 实际应调用采购系统API
        # TODO: 集成采购系统 API
        sample_data = [
            {
                "id": 1,
                "po_number": "PO-20251215-00001",
                "supplier_name": "供应商A",
                "total_price": 10000.00,
                "status": "confirmed",
                "confirmed_at": "2025-12-15T10:00:00",
                "items": [
                    {"line_no": 1, "material_code": "MAT001", "material_name": "物料A", "quantity": 100, "uom": "pcs"},
                    {"line_no": 2, "material_code": "MAT002", "material_name": "物料B", "quantity": 50, "uom": "pcs"},
                ]
            }
        ]

        # 过滤掉已创建入库单的
        result = [po for po in sample_data if po['po_number'] not in existing_po_numbers]

        return jsonify({
            "success": True,
            "data": result,
            "message": "注意：此为示例数据，实际应集成采购系统API"
        })
    except Exception as e:
        current_app.logger.exception("获取待入库采购订单失败")
        return jsonify({"success": False, "error": str(e)}), 500
