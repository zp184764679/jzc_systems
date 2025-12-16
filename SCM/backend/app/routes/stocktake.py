# backend/app/routes/stocktake.py
"""
库存盘点 API 路由
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import or_, func
from app import db
from app.models.stocktake import (
    StocktakeOrder, StocktakeOrderItem, StocktakeAdjustLog,
    StocktakeStatus, StocktakeType,
    STOCKTAKE_STATUS_MAP, STOCKTAKE_TYPE_MAP
)
from app.models.material import Material, Warehouse, StorageBin, Inventory, MaterialCategory
from app.models.inventory import InventoryTx

stocktake_bp = Blueprint('stocktake', __name__, url_prefix='/api/stocktake')


# ============== 盘点单 API ==============

@stocktake_bp.route('', methods=['GET'])
def get_stocktake_orders():
    """获取盘点单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '').strip()
        status = request.args.get('status', '')
        stocktake_type = request.args.get('stocktake_type', '')
        warehouse_id = request.args.get('warehouse_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        query = StocktakeOrder.query

        # 关键字搜索
        if keyword:
            query = query.filter(or_(
                StocktakeOrder.order_no.ilike(f'%{keyword}%'),
                StocktakeOrder.warehouse_name.ilike(f'%{keyword}%'),
            ))

        # 状态筛选
        if status:
            try:
                query = query.filter(StocktakeOrder.status == StocktakeStatus(status))
            except ValueError:
                pass

        # 类型筛选
        if stocktake_type:
            try:
                query = query.filter(StocktakeOrder.stocktake_type == StocktakeType(stocktake_type))
            except ValueError:
                pass

        # 仓库筛选
        if warehouse_id:
            query = query.filter(StocktakeOrder.warehouse_id == warehouse_id)

        # 日期筛选
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(StocktakeOrder.stocktake_date >= start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(StocktakeOrder.stocktake_date <= end)
            except ValueError:
                pass

        # 排序
        query = query.order_by(StocktakeOrder.created_at.desc())

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
        current_app.logger.exception("获取盘点单列表失败")
        return jsonify({"success": False, "error": str(e)}), 500


@stocktake_bp.route('/<int:id>', methods=['GET'])
def get_stocktake_order(id):
    """获取盘点单详情"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        return jsonify({
            "success": True,
            "data": order.to_dict(include_items=True)
        })
    except Exception as e:
        current_app.logger.exception("获取盘点单详情失败")
        return jsonify({"success": False, "error": str(e)}), 500


@stocktake_bp.route('', methods=['POST'])
def create_stocktake_order():
    """创建盘点单"""
    try:
        data = request.get_json()

        # 获取盘点类型
        stocktake_type = data.get('stocktake_type', 'full')

        # 验证仓库
        warehouse_id = data.get('warehouse_id')
        if not warehouse_id:
            return jsonify({"success": False, "error": "请选择盘点仓库"}), 400

        warehouse = Warehouse.query.get(warehouse_id)
        if not warehouse:
            return jsonify({"success": False, "error": "仓库不存在"}), 400

        # 验证盘点日期
        stocktake_date = data.get('stocktake_date')
        if not stocktake_date:
            return jsonify({"success": False, "error": "请选择盘点日期"}), 400

        # 获取物料分类（可选，用于抽盘）
        category_id = data.get('category_id')
        category_name = None
        if category_id:
            category = MaterialCategory.query.get(category_id)
            if category:
                category_name = category.name

        # 创建盘点单
        order = StocktakeOrder(
            order_no=StocktakeOrder.generate_order_no(stocktake_type),
            stocktake_type=StocktakeType(stocktake_type),
            status=StocktakeStatus.DRAFT,
            warehouse_id=warehouse_id,
            warehouse_name=warehouse.name,
            category_id=category_id,
            category_name=category_name,
            stocktake_date=datetime.strptime(stocktake_date, '%Y-%m-%d').date(),
            remark=data.get('remark'),
            created_by=data.get('created_by'),
            created_by_name=data.get('created_by_name'),
            stocktaker_id=data.get('stocktaker_id'),
            stocktaker_name=data.get('stocktaker_name'),
        )

        db.session.add(order)
        db.session.flush()

        # 生成盘点明细 - 根据仓库库存生成
        inventory_query = Inventory.query.filter_by(warehouse_id=warehouse_id)

        # 如果指定了物料分类，过滤物料
        if category_id:
            # 获取该分类及子分类的物料
            category = MaterialCategory.query.get(category_id)
            if category:
                material_ids = db.session.query(Material.id).filter(
                    Material.category_id.in_(
                        db.session.query(MaterialCategory.id).filter(
                            MaterialCategory.path.like(f'%/{category_id}/%')
                        )
                    )
                ).union(
                    db.session.query(Material.id).filter(Material.category_id == category_id)
                )
                inventory_query = inventory_query.filter(Inventory.material_id.in_(material_ids))

        inventories = inventory_query.all()

        total_book_qty = 0
        for idx, inv in enumerate(inventories, start=1):
            material = Material.query.get(inv.material_id)
            bin_obj = StorageBin.query.get(inv.bin_id) if inv.bin_id else None

            book_qty = float(inv.quantity or 0)
            unit_cost = float(material.reference_cost or 0) if material else 0
            book_amount = book_qty * unit_cost

            total_book_qty += book_qty

            item = StocktakeOrderItem(
                order_id=order.id,
                line_no=idx,
                material_id=inv.material_id,
                material_code=material.code if material else '',
                material_name=material.name if material else '',
                specification=material.specification if material else '',
                uom=inv.uom or (material.base_uom if material else 'pcs'),
                bin_id=inv.bin_id,
                bin_code=bin_obj.code if bin_obj else '',
                batch_no=inv.batch_no or '',
                book_qty=book_qty,
                unit_cost=unit_cost,
                book_amount=book_amount,
                count_status='pending',
                inventory_id=inv.id,
            )
            db.session.add(item)

        # 更新盘点单汇总
        order.total_items = len(inventories)
        order.total_book_qty = total_book_qty

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"盘点单创建成功，共 {len(inventories)} 项待盘点",
            "data": order.to_dict(include_items=True)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("创建盘点单失败")
        return jsonify({"success": False, "error": str(e)}), 500


@stocktake_bp.route('/<int:id>', methods=['DELETE'])
def delete_stocktake_order(id):
    """删除盘点单（仅草稿状态可删除）"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        if order.status != StocktakeStatus.DRAFT:
            return jsonify({"success": False, "error": "只有草稿状态的盘点单可以删除"}), 400

        db.session.delete(order)
        db.session.commit()

        return jsonify({"success": True, "message": "盘点单已删除"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("删除盘点单失败")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 状态流转 API ==============

@stocktake_bp.route('/<int:id>/start', methods=['POST'])
def start_stocktake(id):
    """开始盘点（草稿 -> 盘点中）"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        if order.status != StocktakeStatus.DRAFT:
            return jsonify({"success": False, "error": "只有草稿状态的盘点单可以开始"}), 400

        if order.total_items == 0:
            return jsonify({"success": False, "error": "盘点单没有明细，无法开始"}), 400

        order.status = StocktakeStatus.IN_PROGRESS
        order.start_time = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "盘点已开始",
            "data": order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("开始盘点失败")
        return jsonify({"success": False, "error": str(e)}), 500


@stocktake_bp.route('/<int:id>/submit', methods=['POST'])
def submit_stocktake(id):
    """提交审核（盘点中 -> 待审核）"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        if order.status != StocktakeStatus.IN_PROGRESS:
            return jsonify({"success": False, "error": "只有盘点中的盘点单可以提交"}), 400

        # 检查是否全部盘点完成
        pending_count = order.items.filter_by(count_status='pending').count()
        if pending_count > 0:
            return jsonify({"success": False, "error": f"还有 {pending_count} 项未盘点"}), 400

        order.status = StocktakeStatus.PENDING_REVIEW
        order.end_time = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "已提交审核",
            "data": order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("提交审核失败")
        return jsonify({"success": False, "error": str(e)}), 500


@stocktake_bp.route('/<int:id>/approve', methods=['POST'])
def approve_stocktake(id):
    """审核通过（待审核 -> 已审核）"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        if order.status != StocktakeStatus.PENDING_REVIEW:
            return jsonify({"success": False, "error": "只有待审核的盘点单可以审核"}), 400

        data = request.get_json() or {}

        order.status = StocktakeStatus.APPROVED
        order.reviewer_id = data.get('reviewer_id')
        order.reviewer_name = data.get('reviewer_name')
        order.reviewed_at = datetime.utcnow()
        order.review_remark = data.get('remark')

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "审核通过",
            "data": order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("审核失败")
        return jsonify({"success": False, "error": str(e)}), 500


@stocktake_bp.route('/<int:id>/reject', methods=['POST'])
def reject_stocktake(id):
    """审核拒绝（待审核 -> 盘点中，重新盘点）"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        if order.status != StocktakeStatus.PENDING_REVIEW:
            return jsonify({"success": False, "error": "只有待审核的盘点单可以拒绝"}), 400

        data = request.get_json() or {}

        order.status = StocktakeStatus.IN_PROGRESS
        order.review_remark = data.get('remark', '审核拒绝，请重新盘点')

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "审核拒绝，请重新盘点",
            "data": order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("拒绝审核失败")
        return jsonify({"success": False, "error": str(e)}), 500


@stocktake_bp.route('/<int:id>/cancel', methods=['POST'])
def cancel_stocktake(id):
    """取消盘点"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        if order.status in [StocktakeStatus.ADJUSTED, StocktakeStatus.CANCELLED]:
            return jsonify({"success": False, "error": "该状态的盘点单无法取消"}), 400

        order.status = StocktakeStatus.CANCELLED
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "盘点单已取消",
            "data": order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("取消盘点失败")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 盘点操作 API ==============

@stocktake_bp.route('/<int:id>/count', methods=['POST'])
def count_items(id):
    """录入盘点结果"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        if order.status != StocktakeStatus.IN_PROGRESS:
            return jsonify({"success": False, "error": "只有盘点中的盘点单可以录入"}), 400

        data = request.get_json()
        items_data = data.get('items', [])
        counted_by = data.get('counted_by')
        counted_by_name = data.get('counted_by_name')

        if not items_data:
            return jsonify({"success": False, "error": "请提供盘点数据"}), 400

        total_actual_qty = 0
        total_diff_qty = 0
        total_diff_amount = 0
        diff_count = 0
        counted_count = 0

        for item_data in items_data:
            item_id = item_data.get('item_id')
            actual_qty = item_data.get('actual_qty')

            if actual_qty is None:
                continue

            actual_qty = float(actual_qty)

            item = StocktakeOrderItem.query.get(item_id)
            if not item or item.order_id != order.id:
                continue

            # 计算差异
            book_qty = float(item.book_qty or 0)
            diff_qty = actual_qty - book_qty
            unit_cost = float(item.unit_cost or 0)
            actual_amount = actual_qty * unit_cost
            diff_amount = diff_qty * unit_cost

            # 更新明细
            item.actual_qty = actual_qty
            item.diff_qty = diff_qty
            item.actual_amount = actual_amount
            item.diff_amount = diff_amount
            item.count_status = 'counted'
            item.counted_at = datetime.utcnow()
            item.counted_by = counted_by
            item.counted_by_name = counted_by_name
            item.diff_reason = item_data.get('diff_reason')
            item.remark = item_data.get('remark')

            total_actual_qty += actual_qty
            total_diff_qty += diff_qty
            total_diff_amount += diff_amount
            counted_count += 1

            if abs(diff_qty) > 0.0001:
                diff_count += 1

        # 更新盘点单汇总
        # 重新计算所有项的汇总
        all_items = order.items.all()
        order.counted_items = sum(1 for i in all_items if i.count_status == 'counted')
        order.diff_items = sum(1 for i in all_items if i.count_status == 'counted' and abs(float(i.diff_qty or 0)) > 0.0001)
        order.total_actual_qty = sum(float(i.actual_qty or 0) for i in all_items if i.actual_qty is not None)
        order.total_diff_qty = sum(float(i.diff_qty or 0) for i in all_items)
        order.total_diff_amount = sum(float(i.diff_amount or 0) for i in all_items)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"已录入 {counted_count} 项盘点结果",
            "data": order.to_dict(include_items=True)
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("录入盘点失败")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 调整库存 API ==============

@stocktake_bp.route('/<int:id>/adjust', methods=['POST'])
def adjust_inventory(id):
    """执行库存调整（已审核 -> 已调整）"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        if order.status != StocktakeStatus.APPROVED:
            return jsonify({"success": False, "error": "只有已审核的盘点单可以调整库存"}), 400

        data = request.get_json() or {}
        adjusted_by = data.get('adjusted_by')
        adjusted_by_name = data.get('adjusted_by_name')

        adjust_count = 0

        # 遍历所有有差异的明细
        items = order.items.filter(StocktakeOrderItem.count_status == 'counted').all()

        for item in items:
            diff_qty = float(item.diff_qty or 0)
            if abs(diff_qty) < 0.0001:
                continue  # 无差异跳过

            # 更新库存
            inventory = Inventory.query.get(item.inventory_id)
            if inventory:
                old_qty = float(inventory.quantity or 0)
                new_qty = float(item.actual_qty or 0)
                inventory.quantity = new_qty
                inventory.available_qty = new_qty - float(inventory.reserved_qty or 0)

                # 创建库存流水
                tx = InventoryTx(
                    product_text=item.material_code,
                    qty_delta=diff_qty,
                    tx_type='盘点调整',
                    order_no=order.order_no,
                    bin_code=item.bin_code,
                    uom=item.uom,
                    ref=f"盘点单明细#{item.id}",
                    remark=f"盘点调整：账面{old_qty} -> 实际{new_qty}",
                )
                db.session.add(tx)
                db.session.flush()

                # 创建调整记录
                log = StocktakeAdjustLog(
                    order_id=order.id,
                    item_id=item.id,
                    material_code=item.material_code,
                    material_name=item.material_name,
                    book_qty=item.book_qty,
                    actual_qty=item.actual_qty,
                    adjust_qty=diff_qty,
                    adjust_type='increase' if diff_qty > 0 else 'decrease',
                    adjusted_by=adjusted_by,
                    adjusted_by_name=adjusted_by_name,
                    inventory_tx_id=tx.id,
                )
                db.session.add(log)

                item.adjust_status = 'approved'
                adjust_count += 1

        # 更新盘点单状态
        order.status = StocktakeStatus.ADJUSTED

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"库存调整完成，共调整 {adjust_count} 项",
            "data": order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("库存调整失败")
        return jsonify({"success": False, "error": str(e)}), 500


@stocktake_bp.route('/<int:id>/adjust-logs', methods=['GET'])
def get_adjust_logs(id):
    """获取盘点调整记录"""
    try:
        order = StocktakeOrder.query.get(id)
        if not order:
            return jsonify({"success": False, "error": "盘点单不存在"}), 404

        logs = StocktakeAdjustLog.query.filter_by(order_id=id).order_by(StocktakeAdjustLog.adjusted_at.desc()).all()

        return jsonify({
            "success": True,
            "data": [log.to_dict() for log in logs]
        })
    except Exception as e:
        current_app.logger.exception("获取调整记录失败")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 辅助 API ==============

@stocktake_bp.route('/types', methods=['GET'])
def get_stocktake_types():
    """获取盘点类型列表"""
    return jsonify({
        "success": True,
        "data": [
            {"value": key, "label": value}
            for key, value in STOCKTAKE_TYPE_MAP.items()
        ]
    })


@stocktake_bp.route('/statuses', methods=['GET'])
def get_stocktake_statuses():
    """获取盘点单状态列表"""
    return jsonify({
        "success": True,
        "data": [
            {"value": key, "label": value}
            for key, value in STOCKTAKE_STATUS_MAP.items()
        ]
    })


@stocktake_bp.route('/statistics', methods=['GET'])
def get_stocktake_statistics():
    """获取盘点统计"""
    try:
        # 本月盘点
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)

        month_count = StocktakeOrder.query.filter(
            StocktakeOrder.stocktake_date >= month_start
        ).count()

        # 进行中
        in_progress_count = StocktakeOrder.query.filter(
            StocktakeOrder.status == StocktakeStatus.IN_PROGRESS
        ).count()

        # 待审核
        pending_review_count = StocktakeOrder.query.filter(
            StocktakeOrder.status == StocktakeStatus.PENDING_REVIEW
        ).count()

        # 已完成
        completed_count = StocktakeOrder.query.filter(
            StocktakeOrder.status == StocktakeStatus.ADJUSTED,
            StocktakeOrder.stocktake_date >= month_start
        ).count()

        return jsonify({
            "success": True,
            "data": {
                "month_count": month_count,
                "in_progress_count": in_progress_count,
                "pending_review_count": pending_review_count,
                "completed_count": completed_count,
            }
        })
    except Exception as e:
        current_app.logger.exception("获取盘点统计失败")
        return jsonify({"success": False, "error": str(e)}), 500
