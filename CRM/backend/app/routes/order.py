# -*- coding: utf-8 -*-
"""订单主表相关路由：列表/查询/详情/更新/删除/诊断"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from .orders import (
    # blueprint & db & models
    bp, db, Order, OrderLine,
    # common helpers
    _err, _json_ready, _order_to_dict, _parse_date_like,
    _pick, _num, _set_if_has, _build_list_query, _paginate,
    # misc
    ORDER_BP_VERSION, request, jsonify, current_app, time, os,
)

# -------------------------------
# 列表核心
# -------------------------------
def _list_core(params: Dict[str, Any]):
    """
    支持两种形态：
    1) 若带 id/oid/order_id/no -> 返回单条
    2) 否则走分页列表
    """
    # 单条直取
    for key in ("id", "oid", "order_id", "no"):
        if params.get(key) not in (None, ""):
            try:
                if key in ("id", "oid", "order_id"):
                    oid = int(params.get(key))
                    obj = db.session.get(Order, oid)
                else:
                    obj = Order.query.filter(getattr(Order, "order_no") == params.get("no")).first()
                if not obj:
                    return jsonify({"error": "Not Found"}), 404
                return jsonify(_order_to_dict(obj))
            except Exception as e:
                return _err(e, {"stage": "single_probe"})

    # 分页参数
    try:
        page = max(1, int(params.get("page", 1)))
    except Exception:
        page = 1
    try:
        page_size = max(1, min(int(params.get("page_size", 20)), 200))
    except Exception:
        page_size = 20

    try:
        q = _build_list_query(params)
        items, total = _paginate(q, page, page_size)

        items_json, skipped = [], []
        for o in items:
            try:
                items_json.append(_order_to_dict(o))
            except Exception as e:
                skipped.append({"id": getattr(o, "id", None), "error": str(e)})

        payload: Dict[str, Any] = {
            "items": items_json,
            "page": page,
            "page_size": page_size,
            "total": total,
        }
        if (params.get("_debug") == "1") or (request.args.get("_debug") == "1"):
            payload["skipped"] = skipped
        return jsonify(_json_ready(payload))
    except Exception as e:
        return _err(e, {"stage": "list_core"})

# -------------------------------
# 列表（GET + POST 变体）
# -------------------------------
@bp.get("/")
# === ADD-ONLY === 兼容无尾斜杠：/api/orders
@bp.get("")  # 不改变原有 @bp.get("/")，仅新增一个无尾斜杠入口，避免 404
def list_orders_get():
    try:
        return _list_core(request.args or {})
    except Exception as e:
        return _err(e, {"stage": "list_orders_get"})

@bp.post("/query")
@bp.post("/search")
@bp.post("/list")
def list_orders_post_alias():
    try:
        body = request.get_json(silent=True) or {}
        # 让查询参数里的调试标志传入 body，行为更直观
        if "_debug" not in body and request.args.get("_debug"): body["_debug"] = request.args.get("_debug")
        if "_no_rel" not in body and request.args.get("_no_rel"): body["_no_rel"] = request.args.get("_no_rel")
        return _list_core(body)
    except Exception as e:
        return _err(e, {"stage": "list_orders_post_alias"})

# -------------------------------
# 详情
# -------------------------------
@bp.get("/<int:oid>")
def get_order(oid: int):
    try:
        o = db.session.get(Order, oid)
        if not o:
            return jsonify({"error": "Not Found"}), 404
        return jsonify(_order_to_dict(o))
    except Exception as e:
        return _err(e, {"stage": "get_order", "oid": oid})

# -------------------------------
# 更新（PUT / PATCH）
# -------------------------------
@bp.put("/<int:oid>")
@bp.patch("/<int:oid>")
def update_order(oid: int):
    try:
        o = db.session.get(Order, oid)
        if not o:
            return jsonify({"error": "Not Found"}), 404

        data = request.get_json(silent=True) or {}

        # 兼容键名：把 request_date 同步为 due_date；把 stock_finished_qty 同步到 finished_in_stock
        if "request_date" in data and "due_date" not in data:
            data["due_date"] = data["request_date"]
        if "stock_finished_qty" in data and "finished_in_stock" not in data:
            data["finished_in_stock"] = data["stock_finished_qty"]

        # 直写同名字段
        for name in (
            "produce_no","order_no","product","qty_total","stock_qty",
            "route_id","batch_no","unit_price","customer_id","customer_code",
            "order_date","currency","remark","status","process_content","delivered_qty","delivery_date",
            "container_code","default_small_bag","department","poid",
            "order_qty","deficit_qty","finished_in_stock","packing_req","default_box_num","biz_dept","cn_name",
            "forecast_qty","stock_location","due_date",
        ):
            if name in data:
                try: setattr(o, name, data.get(name))
                except Exception: pass

        # 别名兜底写入
        _set_if_has(o, data, "container_code", "container", "containerNo", "柜号", "货柜编号")
        _set_if_has(o, data, "remark", "comments", "note", "备注")
        _set_if_has(o, data, "finished_in_stock", "stock_finished_qty", "finishedStock", "成品在库")
        _set_if_has(o, data, "default_box_num", "default_outer_box", "默认外包装", "outer_box_default", "default_outer_pack")
        _set_if_has(o, data, "forecast_qty", "fc", "forecast", "forecast_quantity", "forecastQty", "预测数量")
        _set_if_has(o, data, "stock_location", "location", "stock_place", "warehouse_location", "库存所在地")

        db.session.flush()

        # 若本次未带行明细：把主表的 FC/库存所在地同步给第一行（该行为空时才填）
        if not any(k in data for k in ("lines", "order_lines", "items")) and (
            "stock_location" in data or "forecast_qty" in data or "fc" in data or "forecast" in data
        ):
            first = (
                db.session.query(OrderLine)
                .filter_by(order_id=o.id)
                .order_by(OrderLine.line_no.asc(), OrderLine.id.asc())
                .first()
            )
            if first:
                if "stock_location" in data and not getattr(first, "stock_location", None):
                    first.stock_location = data.get("stock_location")
                fc_val = _pick(data, "forecast_qty", "fc", "forecast", "forecast_quantity", "forecastQty")
                if fc_val not in (None, "") and (getattr(first, "forecast_qty", None) in (None, 0, 0.0)):
                    first.forecast_qty = _num(fc_val)

        # 如果带了行明细：重写全部行
        if any(k in data for k in ("lines", "order_lines", "items")):
            lines = data.get("lines") or data.get("order_lines") or data.get("items") or []
            db.session.query(OrderLine).filter(OrderLine.order_id == o.id).delete(synchronize_session=False)
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

# === 新增同步逻辑：如果行有 forecast_qty / stock_location，主表也跟着更新 ===
            if isinstance(lines, list) and lines:
                fc_from_line = next((r.get("forecast_qty") for r in lines if r.get("forecast_qty")), None)
                if fc_from_line is not None:
                    o.forecast_qty = _num(fc_from_line)
                loc_from_line = next((r.get("stock_location") for r in lines if r.get("stock_location")), None)
                if loc_from_line:
                    o.stock_location = loc_from_line

        db.session.commit()
        return jsonify(_order_to_dict(o))
    except Exception as e:
        db.session.rollback()
        return _err(e, {"stage": "update_order", "oid": oid})

# -------------------------------
# 删除
# -------------------------------
@bp.delete("/<int:oid>")
def delete_order(oid: int):
    try:
        o = db.session.get(Order, oid)
        if not o:
            return jsonify({"error": "Not Found"}), 404

        # 先删明细
        try:
            db.session.query(OrderLine).filter(OrderLine.order_id == o.id).delete(synchronize_session=False)
        except Exception:
            pass

        db.session.delete(o)
        db.session.commit()
        return ("", 204)
    except Exception as e:
        db.session.rollback()
        return _err(e, {"stage": "delete_order", "oid": oid})

# -------------------------------
# 自检 / 路由表 / 文件来源
# -------------------------------
@bp.get("/__diag")
def __diag():
    try:
        # 1) 基础数据库可用性
        try:
            any_id = db.session.query(Order.id).order_by(Order.id.desc()).limit(1).scalar()
        except Exception as e:
            return _err(e, {"ok": False, "stage": "db_or_table"})

        # 2) 简单查询可用性（带可选的关系预加载）
        try:
            q = Order.query
            _ = q.limit(1).first()
        except Exception as e:
            return jsonify({"ok": False, "stage": "simple_query", "detail": str(e)}), 500

        # 3) 列表查询构建函数可用性
        try:
            q2 = _build_list_query({})
            _ = q2.limit(1).first()
        except Exception as e:
            return jsonify({"ok": False, "stage": "build_list_query_or_exec", "detail": str(e)}), 500

        return jsonify({"ok": True, "sample_id": any_id, "version": ORDER_BP_VERSION, "file": __file__, "time": int(time.time())})
    except Exception as e:
        return _err(e, {"stage": "__diag"})

@bp.get("/__routes")
def __routes():
    try:
        rules = []
        prefix = bp.url_prefix or "/api/orders"
        for r in current_app.url_map.iter_rules():
            rule_str = str(r.rule)
            if rule_str.startswith(prefix):
                rules.append({
                    "rule": rule_str,
                    "endpoint": r.endpoint,
                    "methods": sorted([m for m in r.methods if m not in {"HEAD", "OPTIONS"}])
                })
        return jsonify({"url_prefix": prefix, "routes": rules, "count": len(rules)})
    except Exception as e:
        return _err(e, {"stage": "__routes"})

@bp.get("/__whoami")
def __whoami():
    try:
        return jsonify({"version": ORDER_BP_VERSION, "file": __file__, "pwd": os.getcwd(), "url_prefix": bp.url_prefix})
    except Exception as e:
        return _err(e, {"stage": "__whoami"})
