# -*- coding: utf-8 -*-
"""新建订单（OrderNew）—— 仅负责 POST /api/orders"""
from __future__ import annotations

from .orders import (
    bp, db, Order, OrderLine,
    _err, _json_ready, _order_to_dict,
    _pick, _num, _set_if_has,
    request, jsonify
)

# 兼容 /api/orders 和 /api/orders/
@bp.post("")
@bp.post("/")
def create_order():
    try:
        data = request.get_json(silent=True) or {}

        # 兼容键名：把 request_date 同步为 due_date；把 stock_finished_qty 同步到 finished_in_stock
        if "request_date" in data and "due_date" not in data:
            data["due_date"] = data["request_date"]
        if "stock_finished_qty" in data and "finished_in_stock" not in data:
            data["finished_in_stock"] = data["stock_finished_qty"]

        # --- 主表 ---
        o = Order()
        for name in (
            "produce_no","order_no","product","qty_total","stock_qty",
            "route_id","batch_no","unit_price","customer_id","customer_code",
            "order_date","currency","remark","status","process_content","delivered_qty","delivery_date",
            "container_code","default_small_bag","department","poid",
            "order_qty","deficit_qty","finished_in_stock","packing_req","default_box_num","biz_dept","cn_name",
            "forecast_qty","stock_location","due_date",
        ):
            if name in data:
                try:
                    setattr(o, name, data.get(name))
                except Exception:
                    pass

        # 别名兜底写入
        _set_if_has(o, data, "container_code", "container", "containerNo", "柜号", "货柜编号")
        _set_if_has(o, data, "remark", "comments", "note", "备注")
        _set_if_has(o, data, "finished_in_stock", "stock_finished_qty", "finishedStock", "成品在库")
        _set_if_has(o, data, "default_box_num", "default_outer_box", "默认外包装", "outer_box_default", "default_outer_pack")
        _set_if_has(o, data, "forecast_qty", "fc", "forecast", "forecast_quantity", "forecastQty", "预测数量")
        _set_if_has(o, data, "stock_location", "location", "stock_place", "warehouse_location", "库存所在地")

        # 默认值兜底
        if getattr(o, "currency", None) is None:
            setattr(o, "currency", "CNY")
        if getattr(o, "status", None) is None:
            setattr(o, "status", "draft")

        # 若携带明细，预处理总量/金额与顶层字段兜底
        rows = data.get("lines") or data.get("order_lines") or data.get("items") or []
        if isinstance(rows, list) and rows:
            first = rows[0]
            sum_qty = sum(_num(_pick(r, "qty", "quantity", default=0)) for r in rows)
            sum_amt = 0.0
            for r in rows:
                amt = _pick(r, "amount", "line_total", "lineTotal", "total")
                sum_amt += _num(amt) if amt not in (None, "") else (
                    _num(_pick(r, "qty", "quantity", default=0)) * _num(_pick(r, "unit_price", "price", "unitPrice", default=0))
                )

            if not getattr(o, "product", None):
                setattr(o, "product", _pick(first, "product_text", "product"))
            if not getattr(o, "produce_no", None):
                setattr(o, "produce_no", _pick(first, "product_text", "product"))

            if not getattr(o, "qty_total", None):
                setattr(o, "qty_total", sum_qty or None)
            if not getattr(o, "order_qty", None):
                setattr(o, "order_qty", sum_qty or None)
            if not getattr(o, "unit_price", None) and len(rows) == 1:
                setattr(o, "unit_price", _num(_pick(first, "unit_price", "price", "unitPrice", default=0)))

            # 若模型存在 amount_total 字段，则赋值
            if hasattr(o, "amount_total"):
                try:
                    setattr(o, "amount_total", sum_amt)
                except Exception:
                    pass

        db.session.add(o)
        db.session.flush()  # 获取 o.id

        # --- 明细 ---
        lines = data.get("lines") or data.get("order_lines") or data.get("items") or []
        if isinstance(lines, list) and lines:
            for i, row in enumerate(lines, start=1):
                item = OrderLine(
                    order_id=o.id,
                    line_no=row.get("line_no") or i,
                    product_text=_pick(row, "product_text", "product", default=""),
                    spec=_pick(row, "spec", "specification", "specs", "model", "standard", default=""),
                    material_code=_pick(row, "material_code", "materialCode", "part_code", "partCode", "code", default=""),
                    material=_pick(row, "material", "material_name", "materialName", default=""),
                    qty=int(_num(_pick(row, "qty", "quantity", default=0))),
                    currency_code=_pick(row, "currency_code", "unit", "uom", "currency", "currencyCode", default="CNY") or "CNY",
                    tax_rate=_num(_pick(row, "tax_rate", "vat_rate", "vatRate", default=0)),
                    unit_price=_num(_pick(row, "unit_price", "price", "unitPrice", default=0)),
                )
                # 库存所在地 / FC 兜底
                item.stock_location = _pick(
                    row, "stock_location", "location", "stock_place", "warehouse_location",
                    default=data.get("stock_location")
                ) or None
                fq = _pick(
                    row, "forecast_qty", "fc", "forecast", "forecast_quantity", "forecastQty",
                    default=data.get("forecast_qty")
                )
                if fq not in (None, ""):
                    item.forecast_qty = _num(fq)

                amt = _pick(row, "amount", "line_total", "lineTotal", "total")
                if amt not in (None, ""):
                    item.amount = _num(amt)
                else:
                    item.amount = float(item.qty) * float(item.unit_price)

                db.session.add(item)

        db.session.commit()
        # 返回新建后的结构（含序列化）
        return jsonify(_json_ready({"id": o.id, "order": _order_to_dict(o)})), 201

    except Exception as e:
        db.session.rollback()
        return _err(e, {"stage": "create_order"})
