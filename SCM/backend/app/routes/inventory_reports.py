# -*- coding: utf-8 -*-
"""
库存报表 API - Inventory Reports
提供库存相关的统计报表接口
"""
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc, and_, or_, case

from app import db
from app.models.material import Material, MaterialCategory, Warehouse, StorageBin, Inventory, MaterialType, MATERIAL_TYPE_MAP
from app.models.inventory import InventoryTx

inventory_reports_bp = Blueprint('inventory_reports', __name__, url_prefix='/api/inventory/reports')


@inventory_reports_bp.route('/summary', methods=['GET'])
def get_inventory_summary():
    """
    库存汇总报表
    返回总体库存概况：总SKU数、总数量、总金额、仓库分布等
    """
    try:
        # 总库存记录数（有库存的SKU）
        total_sku = db.session.query(func.count(func.distinct(Inventory.material_id))).filter(
            Inventory.quantity > 0
        ).scalar() or 0

        # 总库存数量
        total_qty = db.session.query(func.sum(Inventory.quantity)).filter(
            Inventory.quantity > 0
        ).scalar() or Decimal(0)

        # 总预留数量
        total_reserved = db.session.query(func.sum(Inventory.reserved_qty)).filter(
            Inventory.reserved_qty > 0
        ).scalar() or Decimal(0)

        # 总可用数量
        total_available = db.session.query(func.sum(Inventory.available_qty)).filter(
            Inventory.available_qty > 0
        ).scalar() or Decimal(0)

        # 库存金额（库存 * 参考成本）
        total_value = db.session.query(
            func.sum(Inventory.quantity * Material.reference_cost)
        ).join(Material, Inventory.material_id == Material.id).filter(
            Inventory.quantity > 0,
            Material.reference_cost.isnot(None)
        ).scalar() or Decimal(0)

        # 按仓库统计
        warehouse_stats = db.session.query(
            Warehouse.id,
            Warehouse.code,
            Warehouse.name,
            func.count(func.distinct(Inventory.material_id)).label('sku_count'),
            func.sum(Inventory.quantity).label('total_qty'),
            func.sum(Inventory.quantity * Material.reference_cost).label('total_value')
        ).join(
            Inventory, Inventory.warehouse_id == Warehouse.id
        ).join(
            Material, Material.id == Inventory.material_id
        ).filter(
            Inventory.quantity > 0
        ).group_by(Warehouse.id).all()

        warehouse_distribution = [{
            'warehouse_id': ws.id,
            'warehouse_code': ws.code,
            'warehouse_name': ws.name,
            'sku_count': ws.sku_count or 0,
            'total_qty': float(ws.total_qty or 0),
            'total_value': float(ws.total_value or 0),
        } for ws in warehouse_stats]

        # 按物料类型统计
        type_stats = db.session.query(
            Material.material_type,
            func.count(func.distinct(Inventory.material_id)).label('sku_count'),
            func.sum(Inventory.quantity).label('total_qty')
        ).join(
            Inventory, Inventory.material_id == Material.id
        ).filter(
            Inventory.quantity > 0
        ).group_by(Material.material_type).all()

        type_distribution = [{
            'material_type': ts.material_type,
            'type_label': MATERIAL_TYPE_MAP.get(ts.material_type, ts.material_type),
            'sku_count': ts.sku_count or 0,
            'total_qty': float(ts.total_qty or 0),
        } for ts in type_stats]

        return jsonify({
            'total_sku': total_sku,
            'total_quantity': float(total_qty),
            'total_reserved': float(total_reserved),
            'total_available': float(total_available),
            'total_value': float(total_value),
            'warehouse_distribution': warehouse_distribution,
            'type_distribution': type_distribution,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_reports_bp.route('/by-warehouse', methods=['GET'])
def get_inventory_by_warehouse():
    """
    按仓库的库存报表
    支持筛选：warehouse_id, material_type, category_id
    """
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        material_type = request.args.get('material_type')
        category_id = request.args.get('category_id', type=int)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # 基础查询
        query = db.session.query(
            Inventory.warehouse_id,
            Warehouse.code.label('warehouse_code'),
            Warehouse.name.label('warehouse_name'),
            Inventory.material_id,
            Material.code.label('material_code'),
            Material.name.label('material_name'),
            Material.material_type,
            Material.specification,
            Material.base_uom,
            func.sum(Inventory.quantity).label('quantity'),
            func.sum(Inventory.reserved_qty).label('reserved_qty'),
            func.sum(Inventory.available_qty).label('available_qty'),
            Material.reference_cost,
            Material.safety_stock,
            Material.min_stock,
        ).join(
            Warehouse, Inventory.warehouse_id == Warehouse.id
        ).join(
            Material, Inventory.material_id == Material.id
        ).filter(
            Inventory.quantity > 0
        )

        # 筛选条件
        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)
        if material_type:
            query = query.filter(Material.material_type == material_type)
        if category_id:
            query = query.filter(Material.category_id == category_id)

        # 分组
        query = query.group_by(
            Inventory.warehouse_id, Inventory.material_id
        ).order_by(Warehouse.code, Material.code)

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        result = []
        for item in items:
            qty = float(item.quantity or 0)
            cost = float(item.reference_cost or 0)
            safety = float(item.safety_stock or 0)

            result.append({
                'warehouse_id': item.warehouse_id,
                'warehouse_code': item.warehouse_code,
                'warehouse_name': item.warehouse_name,
                'material_id': item.material_id,
                'material_code': item.material_code,
                'material_name': item.material_name,
                'material_type': item.material_type,
                'specification': item.specification,
                'uom': item.base_uom,
                'quantity': qty,
                'reserved_qty': float(item.reserved_qty or 0),
                'available_qty': float(item.available_qty or 0),
                'unit_cost': cost,
                'value': qty * cost,
                'safety_stock': safety,
                'is_low_stock': qty < safety if safety > 0 else False,
            })

        return jsonify({
            'items': result,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 1,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_reports_bp.route('/by-category', methods=['GET'])
def get_inventory_by_category():
    """
    按物料分类的库存报表
    返回各分类的库存数量和金额
    """
    try:
        # 按分类统计
        stats = db.session.query(
            MaterialCategory.id,
            MaterialCategory.code,
            MaterialCategory.name,
            MaterialCategory.level,
            MaterialCategory.parent_id,
            func.count(func.distinct(Inventory.material_id)).label('sku_count'),
            func.sum(Inventory.quantity).label('total_qty'),
            func.sum(Inventory.quantity * Material.reference_cost).label('total_value')
        ).join(
            Material, Material.category_id == MaterialCategory.id
        ).join(
            Inventory, Inventory.material_id == Material.id
        ).filter(
            Inventory.quantity > 0,
            MaterialCategory.is_active == True
        ).group_by(MaterialCategory.id).order_by(MaterialCategory.level, MaterialCategory.sort_order).all()

        result = [{
            'category_id': s.id,
            'category_code': s.code,
            'category_name': s.name,
            'level': s.level,
            'parent_id': s.parent_id,
            'sku_count': s.sku_count or 0,
            'total_qty': float(s.total_qty or 0),
            'total_value': float(s.total_value or 0),
        } for s in stats]

        return jsonify({
            'items': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_reports_bp.route('/low-stock', methods=['GET'])
def get_low_stock_report():
    """
    低库存预警报表
    返回库存低于安全库存的物料
    """
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # 汇总每个物料的总库存
        subquery = db.session.query(
            Inventory.material_id,
            func.sum(Inventory.quantity).label('total_qty'),
            func.sum(Inventory.available_qty).label('available_qty')
        )

        if warehouse_id:
            subquery = subquery.filter(Inventory.warehouse_id == warehouse_id)

        subquery = subquery.group_by(Inventory.material_id).subquery()

        # 查询低库存物料
        query = db.session.query(
            Material.id,
            Material.code,
            Material.name,
            Material.specification,
            Material.base_uom,
            Material.safety_stock,
            Material.min_stock,
            Material.reorder_point,
            Material.reorder_qty,
            Material.material_type,
            subquery.c.total_qty,
            subquery.c.available_qty,
        ).outerjoin(
            subquery, Material.id == subquery.c.material_id
        ).filter(
            Material.status == 'active',
            Material.safety_stock > 0,
            or_(
                subquery.c.total_qty < Material.safety_stock,
                subquery.c.total_qty.is_(None)
            )
        ).order_by(
            case(
                (subquery.c.total_qty.is_(None), 0),
                else_=subquery.c.total_qty
            ).asc()
        )

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        result = []
        for item in items:
            qty = float(item.total_qty or 0)
            safety = float(item.safety_stock or 0)
            shortage = max(0, safety - qty)

            result.append({
                'material_id': item.id,
                'material_code': item.code,
                'material_name': item.name,
                'specification': item.specification,
                'uom': item.base_uom,
                'material_type': item.material_type,
                'current_qty': qty,
                'available_qty': float(item.available_qty or 0),
                'safety_stock': safety,
                'min_stock': float(item.min_stock or 0),
                'reorder_point': float(item.reorder_point or 0),
                'reorder_qty': float(item.reorder_qty or 0),
                'shortage': shortage,
                'shortage_rate': round((shortage / safety * 100) if safety > 0 else 100, 1),
            })

        return jsonify({
            'items': result,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 1,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_reports_bp.route('/turnover', methods=['GET'])
def get_turnover_report():
    """
    库存周转率报表
    根据出入库流水计算周转率
    """
    try:
        days = request.args.get('days', 30, type=int)  # 统计天数
        warehouse_id = request.args.get('warehouse_id', type=int)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        start_date = datetime.utcnow() - timedelta(days=days)

        # 计算期间内的出库量
        outbound_subq = db.session.query(
            InventoryTx.product_text,
            func.sum(func.abs(InventoryTx.qty_delta)).label('outbound_qty')
        ).filter(
            InventoryTx.tx_type.in_(['出库', 'out', 'delivery']),
            InventoryTx.occurred_at >= start_date,
            InventoryTx.qty_delta < 0
        ).group_by(InventoryTx.product_text).subquery()

        # 汇总当前库存
        inventory_subq = db.session.query(
            Material.code.label('material_code'),
            func.sum(Inventory.quantity).label('current_qty'),
            func.sum(Inventory.quantity * Material.reference_cost).label('current_value')
        ).join(
            Inventory, Inventory.material_id == Material.id
        )

        if warehouse_id:
            inventory_subq = inventory_subq.filter(Inventory.warehouse_id == warehouse_id)

        inventory_subq = inventory_subq.group_by(Material.code).subquery()

        # 组合查询
        query = db.session.query(
            Material.id,
            Material.code,
            Material.name,
            Material.specification,
            Material.base_uom,
            Material.reference_cost,
            inventory_subq.c.current_qty,
            inventory_subq.c.current_value,
            outbound_subq.c.outbound_qty,
        ).outerjoin(
            inventory_subq, Material.code == inventory_subq.c.material_code
        ).outerjoin(
            outbound_subq, Material.code == outbound_subq.c.product_text
        ).filter(
            or_(
                inventory_subq.c.current_qty > 0,
                outbound_subq.c.outbound_qty > 0
            )
        ).order_by(desc(outbound_subq.c.outbound_qty))

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        result = []
        for item in items:
            current_qty = float(item.current_qty or 0)
            outbound_qty = float(item.outbound_qty or 0)
            current_value = float(item.current_value or 0)

            # 平均库存 = (期初 + 期末) / 2，简化为当前库存
            avg_inventory = current_qty if current_qty > 0 else 1

            # 周转率 = 出库量 / 平均库存
            turnover_rate = round(outbound_qty / avg_inventory, 2) if avg_inventory > 0 else 0

            # 周转天数 = 统计天数 / 周转率
            turnover_days = round(days / turnover_rate, 1) if turnover_rate > 0 else 999

            result.append({
                'material_id': item.id,
                'material_code': item.code,
                'material_name': item.name,
                'specification': item.specification,
                'uom': item.base_uom,
                'current_qty': current_qty,
                'current_value': current_value,
                'outbound_qty': outbound_qty,
                'turnover_rate': turnover_rate,
                'turnover_days': turnover_days,
                'days_in_period': days,
            })

        return jsonify({
            'items': result,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 1,
            'period_days': days,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_reports_bp.route('/aging', methods=['GET'])
def get_aging_report():
    """
    库龄分析报表
    分析库存的存放时间分布
    """
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        now = datetime.utcnow()

        # 定义库龄分段
        age_30 = now - timedelta(days=30)
        age_60 = now - timedelta(days=60)
        age_90 = now - timedelta(days=90)
        age_180 = now - timedelta(days=180)

        # 查询库存及其最后入库时间
        query = db.session.query(
            Material.id,
            Material.code,
            Material.name,
            Material.specification,
            Material.base_uom,
            Material.reference_cost,
            Inventory.warehouse_id,
            Warehouse.name.label('warehouse_name'),
            func.sum(Inventory.quantity).label('quantity'),
            func.max(Inventory.last_in_date).label('last_in_date'),
            func.min(Inventory.created_at).label('first_in_date'),
        ).join(
            Material, Inventory.material_id == Material.id
        ).join(
            Warehouse, Inventory.warehouse_id == Warehouse.id
        ).filter(
            Inventory.quantity > 0
        )

        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)

        query = query.group_by(
            Material.id, Inventory.warehouse_id
        ).order_by(Inventory.warehouse_id, Material.code)

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        result = []
        for item in items:
            qty = float(item.quantity or 0)
            cost = float(item.reference_cost or 0)
            value = qty * cost

            # 计算库龄（基于最早入库时间）
            first_in = item.first_in_date or item.last_in_date or now
            age_days = (now - first_in).days if first_in else 0

            # 库龄分段
            if age_days <= 30:
                age_range = '0-30天'
                age_level = 1
            elif age_days <= 60:
                age_range = '31-60天'
                age_level = 2
            elif age_days <= 90:
                age_range = '61-90天'
                age_level = 3
            elif age_days <= 180:
                age_range = '91-180天'
                age_level = 4
            else:
                age_range = '180天以上'
                age_level = 5

            result.append({
                'material_id': item.id,
                'material_code': item.code,
                'material_name': item.name,
                'specification': item.specification,
                'uom': item.base_uom,
                'warehouse_id': item.warehouse_id,
                'warehouse_name': item.warehouse_name,
                'quantity': qty,
                'unit_cost': cost,
                'value': value,
                'first_in_date': first_in.isoformat() if first_in else None,
                'last_in_date': item.last_in_date.isoformat() if item.last_in_date else None,
                'age_days': age_days,
                'age_range': age_range,
                'age_level': age_level,
            })

        # 计算库龄分布汇总
        age_summary = {}
        for r in result:
            age_range = r['age_range']
            if age_range not in age_summary:
                age_summary[age_range] = {'count': 0, 'quantity': 0, 'value': 0}
            age_summary[age_range]['count'] += 1
            age_summary[age_range]['quantity'] += r['quantity']
            age_summary[age_range]['value'] += r['value']

        return jsonify({
            'items': result,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 1,
            'age_summary': age_summary,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_reports_bp.route('/movement', methods=['GET'])
def get_movement_report():
    """
    库存变动报表
    统计指定时间段内的出入库情况
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        warehouse_id = request.args.get('warehouse_id', type=int)
        material_code = request.args.get('material_code')
        tx_type = request.args.get('tx_type')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 50, type=int)

        # 默认最近30天
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

        # 查询流水
        query = InventoryTx.query.filter(
            InventoryTx.occurred_at >= start_date,
            InventoryTx.occurred_at <= f"{end_date} 23:59:59"
        )

        if material_code:
            query = query.filter(InventoryTx.product_text.ilike(f'%{material_code}%'))
        if tx_type:
            query = query.filter(InventoryTx.tx_type == tx_type)
        if warehouse_id:
            # 需要关联仓库，这里简化处理
            pass

        query = query.order_by(desc(InventoryTx.occurred_at))

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        result = [tx.to_dict() for tx in items]

        # 统计汇总
        inbound_qty = db.session.query(func.sum(InventoryTx.qty_delta)).filter(
            InventoryTx.occurred_at >= start_date,
            InventoryTx.occurred_at <= f"{end_date} 23:59:59",
            InventoryTx.qty_delta > 0
        ).scalar() or 0

        outbound_qty = db.session.query(func.sum(func.abs(InventoryTx.qty_delta))).filter(
            InventoryTx.occurred_at >= start_date,
            InventoryTx.occurred_at <= f"{end_date} 23:59:59",
            InventoryTx.qty_delta < 0
        ).scalar() or 0

        return jsonify({
            'items': result,
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size if page_size else 1,
            'start_date': start_date,
            'end_date': end_date,
            'summary': {
                'inbound_qty': float(inbound_qty),
                'outbound_qty': float(outbound_qty),
                'net_change': float(inbound_qty - outbound_qty),
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@inventory_reports_bp.route('/value', methods=['GET'])
def get_inventory_value_report():
    """
    库存价值报表
    按仓库和物料类型汇总库存价值
    """
    try:
        warehouse_id = request.args.get('warehouse_id', type=int)

        # 总价值
        total_query = db.session.query(
            func.sum(Inventory.quantity * Material.reference_cost).label('total_value'),
            func.sum(Inventory.quantity).label('total_qty'),
            func.count(func.distinct(Inventory.material_id)).label('sku_count')
        ).join(
            Material, Inventory.material_id == Material.id
        ).filter(
            Inventory.quantity > 0,
            Material.reference_cost.isnot(None)
        )

        if warehouse_id:
            total_query = total_query.filter(Inventory.warehouse_id == warehouse_id)

        total_result = total_query.first()

        total_value = float(total_result.total_value or 0)
        total_qty = float(total_result.total_qty or 0)
        total_sku = total_result.sku_count or 0

        # 按仓库分组
        warehouse_query = db.session.query(
            Warehouse.id,
            Warehouse.code,
            Warehouse.name,
            func.sum(Inventory.quantity * Material.reference_cost).label('value'),
            func.sum(Inventory.quantity).label('quantity'),
            func.count(func.distinct(Inventory.material_id)).label('sku_count')
        ).join(
            Inventory, Inventory.warehouse_id == Warehouse.id
        ).join(
            Material, Material.id == Inventory.material_id
        ).filter(
            Inventory.quantity > 0,
            Material.reference_cost.isnot(None)
        )

        if warehouse_id:
            warehouse_query = warehouse_query.filter(Warehouse.id == warehouse_id)

        warehouse_query = warehouse_query.group_by(Warehouse.id).order_by(desc('value'))

        warehouse_data = [{
            'warehouse_id': w.id,
            'warehouse_code': w.code,
            'warehouse_name': w.name,
            'value': float(w.value or 0),
            'quantity': float(w.quantity or 0),
            'sku_count': w.sku_count or 0,
            'percentage': round(float(w.value or 0) / total_value * 100, 1) if total_value > 0 else 0,
        } for w in warehouse_query.all()]

        # 按物料类型分组
        type_query = db.session.query(
            Material.material_type,
            func.sum(Inventory.quantity * Material.reference_cost).label('value'),
            func.sum(Inventory.quantity).label('quantity'),
            func.count(func.distinct(Inventory.material_id)).label('sku_count')
        ).join(
            Inventory, Inventory.material_id == Material.id
        ).filter(
            Inventory.quantity > 0,
            Material.reference_cost.isnot(None)
        )

        if warehouse_id:
            type_query = type_query.join(
                Warehouse, Inventory.warehouse_id == Warehouse.id
            ).filter(Warehouse.id == warehouse_id)

        type_query = type_query.group_by(Material.material_type).order_by(desc('value'))

        type_data = [{
            'material_type': t.material_type,
            'type_label': MATERIAL_TYPE_MAP.get(t.material_type, t.material_type),
            'value': float(t.value or 0),
            'quantity': float(t.quantity or 0),
            'sku_count': t.sku_count or 0,
            'percentage': round(float(t.value or 0) / total_value * 100, 1) if total_value > 0 else 0,
        } for t in type_query.all()]

        return jsonify({
            'total_value': total_value,
            'total_quantity': total_qty,
            'total_sku': total_sku,
            'by_warehouse': warehouse_data,
            'by_material_type': type_data,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
