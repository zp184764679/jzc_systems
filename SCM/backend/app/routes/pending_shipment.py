# -*- coding: utf-8 -*-
# backend/app/routes/pending_shipment.py
"""
待出货订单API
仓库人员用这个功能查看什么时候该出什么货
"""
from __future__ import annotations
from datetime import datetime, date, timedelta
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from sqlalchemy import func, and_, or_, desc

from app import db
from app.models.pending_shipment import PendingShipment
from app.models.inventory import InventoryTx

bp = Blueprint("pending_shipment", __name__, url_prefix="/api/pending-shipments")


def _g(name, default=None):
    v = request.args.get(name)
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _json():
    return request.get_json(silent=True) or {}


def _ok(data=None, status=200):
    return (jsonify({"ok": True, "data": data}), status) if data is not None else (jsonify({"ok": True}), status)


def _err(msg, status=400):
    return jsonify({"ok": False, "error": msg}), status


# ---------- 预检（CORS） ----------
@bp.route("", methods=["OPTIONS"])
@bp.route("/<int:id>", methods=["OPTIONS"])
@bp.route("/ship/<int:id>", methods=["OPTIONS"])
@bp.route("/stats", methods=["OPTIONS"])
@cross_origin()
def _preflight():
    return ("", 204)


# ---------- 获取待出货列表 ----------
@bp.get("")
@cross_origin()
def list_pending():
    """
    获取待出货订单列表
    筛选参数：
      - delivery_from, delivery_to: 交货日期范围
      - status: 状态筛选
      - location: 发货地点
      - priority: 优先级
      - keyword: 关键字搜索（订单号、客户名、产品）
      - overdue: true/false 只看逾期
      - days: 未来N天内需出货（如 days=7 表示未来7天）
    """
    delivery_from = _g("delivery_from")
    delivery_to = _g("delivery_to")
    status = _g("status")
    location = _g("location")
    priority = _g("priority")
    keyword = _g("keyword") or _g("q")
    overdue = _g("overdue")
    days = _g("days")
    page = int(_g("page", "1") or "1")
    page_size = min(max(int(_g("page_size", "50") or "50"), 1), 500)

    q = db.session.query(PendingShipment)

    # 默认只看未完成的
    if status:
        q = q.filter(PendingShipment.status == status)
    else:
        q = q.filter(PendingShipment.status.in_(['待出货', '部分出货']))

    # 日期范围
    if delivery_from:
        q = q.filter(PendingShipment.delivery_date >= delivery_from)
    if delivery_to:
        q = q.filter(PendingShipment.delivery_date <= delivery_to)

    # 未来N天
    if days:
        try:
            n = int(days)
            today = date.today()
            future = today + timedelta(days=n)
            q = q.filter(and_(
                PendingShipment.delivery_date >= today,
                PendingShipment.delivery_date <= future
            ))
        except ValueError:
            pass

    # 逾期筛选
    if overdue == 'true':
        today = date.today()
        q = q.filter(and_(
            PendingShipment.delivery_date < today,
            PendingShipment.status == '待出货'
        ))

    if location:
        q = q.filter(PendingShipment.location == location)

    if priority:
        try:
            q = q.filter(PendingShipment.priority == int(priority))
        except ValueError:
            pass

    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            PendingShipment.order_no.like(like),
            PendingShipment.customer_name.like(like),
            PendingShipment.product_text.like(like),
            PendingShipment.product_name.like(like),
        ))

    # 排序：优先级高的先、交货日期近的先
    q = q.order_by(desc(PendingShipment.priority), PendingShipment.delivery_date)

    total = q.count()
    items = q.limit(page_size).offset((page - 1) * page_size).all()

    # 获取每个产品的当前库存
    product_texts = list(set(item.product_text for item in items))
    stock_map = {}
    if product_texts:
        stock_q = db.session.query(
            InventoryTx.product_text,
            func.sum(InventoryTx.qty_delta).label("qty")
        ).filter(
            InventoryTx.product_text.in_(product_texts)
        ).group_by(InventoryTx.product_text).all()

        for row in stock_q:
            stock_map[row.product_text] = float(row.qty or 0)

    # 构建响应
    result_items = []
    for item in items:
        d = item.to_dict()
        d["current_stock"] = stock_map.get(item.product_text, 0)
        d["stock_sufficient"] = d["current_stock"] >= item.qty_remaining
        result_items.append(d)

    return jsonify({
        "items": result_items,
        "total": total,
        "page": page,
        "page_size": page_size
    })


# ---------- 创建待出货订单 ----------
@bp.post("")
@cross_origin()
def create_pending():
    """
    创建待出货订单
    通常由采购系统/CRM在订单确认后调用
    """
    data = _json()
    rows = data if isinstance(data, list) else [data]
    created = []
    errors = []

    for row in rows:
        try:
            order_no = row.get("order_no")
            product_text = row.get("product_text")
            delivery_date = row.get("delivery_date")
            qty = row.get("qty") or row.get("qty_ordered")

            if not order_no or not product_text or not delivery_date or not qty:
                errors.append({
                    "order_no": order_no,
                    "error": "缺少必填字段: order_no, product_text, delivery_date, qty"
                })
                continue

            # 解析日期
            if isinstance(delivery_date, str):
                delivery_date = datetime.strptime(delivery_date, "%Y-%m-%d").date()

            ps = PendingShipment(
                order_no=order_no,
                customer_name=row.get("customer_name"),
                customer_id=row.get("customer_id"),
                product_text=product_text,
                product_name=row.get("product_name"),
                qty_ordered=float(qty),
                uom=row.get("uom", "pcs"),
                delivery_date=delivery_date,
                priority=int(row.get("priority", 0)),
                location=row.get("location"),
                receiver_address=row.get("receiver_address"),
                receiver_contact=row.get("receiver_contact"),
                receiver_phone=row.get("receiver_phone"),
                remark=row.get("remark"),
                status="待出货"
            )
            db.session.add(ps)
            created.append(ps)

        except Exception as e:
            errors.append({
                "order_no": row.get("order_no"),
                "error": str(e)
            })

    db.session.commit()

    status = 201 if created and not errors else (207 if created and errors else 400)
    return jsonify({
        "ok": len(created) > 0,
        "created": len(created),
        "errors": errors,
        "items": [p.to_dict() for p in created]
    }), status


# ---------- 获取待出货订单详情 ----------
@bp.get("/<int:id>")
@cross_origin()
def get_pending(id):
    ps = PendingShipment.query.get(id)
    if not ps:
        return _err("订单不存在", 404)

    d = ps.to_dict()

    # 获取当前库存
    stock_q = db.session.query(
        func.sum(InventoryTx.qty_delta).label("qty")
    ).filter(InventoryTx.product_text == ps.product_text).scalar()
    d["current_stock"] = float(stock_q or 0)
    d["stock_sufficient"] = d["current_stock"] >= ps.qty_remaining

    return _ok(d)


# ---------- 更新待出货订单 ----------
@bp.put("/<int:id>")
@cross_origin()
def update_pending(id):
    ps = PendingShipment.query.get(id)
    if not ps:
        return _err("订单不存在", 404)

    data = _json()

    # 可更新的字段
    for field in ["customer_name", "product_name", "qty_ordered", "uom",
                  "priority", "location", "receiver_address", "receiver_contact",
                  "receiver_phone", "remark"]:
        if field in data:
            setattr(ps, field, data[field])

    if "delivery_date" in data:
        dd = data["delivery_date"]
        if isinstance(dd, str):
            ps.delivery_date = datetime.strptime(dd, "%Y-%m-%d").date()
        else:
            ps.delivery_date = dd

    db.session.commit()
    return _ok(ps.to_dict())


# ---------- 执行出货（扣库存） ----------
@bp.post("/ship/<int:id>")
@cross_origin()
def do_ship(id):
    """
    执行出货：
    1. 更新待出货记录的已出货数量
    2. 创建出库流水（扣减库存）
    """
    ps = PendingShipment.query.get(id)
    if not ps:
        return _err("订单不存在", 404)

    if ps.status in ['已完成', '已取消']:
        return _err(f"订单状态为{ps.status}，无法出货", 400)

    data = _json()
    ship_qty = float(data.get("qty", 0))

    if ship_qty <= 0:
        return _err("出货数量必须大于0", 400)

    if ship_qty > ps.qty_remaining:
        return _err(f"出货数量({ship_qty})超过剩余待出货数量({ps.qty_remaining})", 400)

    # 检查库存是否足够
    loc = data.get("location") or ps.location
    stock_q = db.session.query(
        func.sum(InventoryTx.qty_delta).label("qty")
    ).filter(InventoryTx.product_text == ps.product_text)
    if loc:
        stock_q = stock_q.filter(InventoryTx.location == loc)
    current_stock = float(stock_q.scalar() or 0)

    if current_stock < ship_qty:
        return _err(f"库存不足：当前库存{current_stock}，需出货{ship_qty}", 400)

    # 创建出库流水
    tx = InventoryTx(
        product_text=ps.product_text,
        qty_delta=-ship_qty,  # 负数表示出库
        tx_type="OUT",
        order_no=ps.order_no,
        location=loc,
        bin_code=data.get("bin_code"),
        uom=ps.uom,
        remark=f"待出货订单出库 - {ps.order_no}"
    )
    db.session.add(tx)

    # 更新待出货记录
    ps.qty_shipped = (ps.qty_shipped or 0) + ship_qty
    if ps.qty_shipped >= ps.qty_ordered:
        ps.status = "已完成"
    else:
        ps.status = "部分出货"

    db.session.commit()

    return _ok({
        "pending_shipment": ps.to_dict(),
        "inventory_tx": tx.to_dict()
    })


# ---------- 取消待出货订单 ----------
@bp.post("/cancel/<int:id>")
@cross_origin()
def cancel_pending(id):
    ps = PendingShipment.query.get(id)
    if not ps:
        return _err("订单不存在", 404)

    if ps.status == '已完成':
        return _err("已完成的订单无法取消", 400)

    ps.status = "已取消"
    db.session.commit()

    return _ok(ps.to_dict())


# ---------- 待出货统计 ----------
@bp.get("/stats")
@cross_origin()
def get_stats():
    """
    获取待出货统计
    """
    today = date.today()
    week_later = today + timedelta(days=7)

    # 总待出货
    total_pending = PendingShipment.query.filter(
        PendingShipment.status.in_(['待出货', '部分出货'])
    ).count()

    # 今日需出货
    today_due = PendingShipment.query.filter(
        and_(
            PendingShipment.delivery_date == today,
            PendingShipment.status.in_(['待出货', '部分出货'])
        )
    ).count()

    # 本周需出货
    week_due = PendingShipment.query.filter(
        and_(
            PendingShipment.delivery_date >= today,
            PendingShipment.delivery_date <= week_later,
            PendingShipment.status.in_(['待出货', '部分出货'])
        )
    ).count()

    # 逾期未出货
    overdue = PendingShipment.query.filter(
        and_(
            PendingShipment.delivery_date < today,
            PendingShipment.status == '待出货'
        )
    ).count()

    # 紧急订单
    urgent = PendingShipment.query.filter(
        and_(
            PendingShipment.priority >= 2,
            PendingShipment.status.in_(['待出货', '部分出货'])
        )
    ).count()

    return _ok({
        "total_pending": total_pending,
        "today_due": today_due,
        "week_due": week_due,
        "overdue": overdue,
        "urgent": urgent
    })
