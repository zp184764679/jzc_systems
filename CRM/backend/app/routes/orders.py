# -*- coding: utf-8 -*-
"""
Orders routes（Blueprint 根）
- 原说明保留：POST /api/orders (创建)、GET /api/orders/<int:oid> (按ID获取)
- 新增/兼容说明也保留：
  GET  /api/orders                           -> 分页列表
  POST /api/orders/query|search|list         -> 列表的 POST 变体（兼容前端）
  GET  /api/orders/__diag                    -> 自检端点
  GET  /api/orders/__routes                  -> 列出注册到应用的 routes（以 /api/orders 开头）
  GET  /api/orders/__whoami                  -> 返回当前加载文件路径版本信息
  可选参数：
    _debug=1   返回错误细节（不依赖全局 errorhandler）
    _no_rel=1  关闭关系预加载（定位 relationship 映射/N+1 问题）

说明：
- 本文件仅定义 Blueprint 与通用工具/序列化函数，不实现业务路由；
- 路由实现在同目录下的 order.py / ordernew.py 中，并挂载到同一个 bp。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from datetime import date, datetime
from decimal import Decimal
import traceback
import time
import os

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import or_, cast
from sqlalchemy.orm import selectinload
from sqlalchemy.types import String

from .. import db
from ..models.core import Order, OrderLine

bp = Blueprint("orders", __name__, url_prefix="/api/orders")
ORDER_BP_VERSION = "orders_bp v1.3"


# -------------------------------
# 工具 & 调试
# -------------------------------
def _debug_on() -> bool:
    """是否开启调试回显"""
    try:
        if request.args.get("_debug") == "1":
            return True
    except Exception:
        pass
    try:
        body = request.get_json(silent=True) or {}
        if str(body.get("_debug", "")).strip() == "1":
            return True
    except Exception:
        pass
    return request.headers.get("X-Debug") == "1"


def _err(e: Exception, extra: Dict[str, Any] | None = None, status: int = 500):
    """统一错误响应；在 _debug=1 时回显 traceback"""
    if _debug_on():
        payload = {
            "error": "Internal Server Error",
            "detail": str(e),
            "trace": traceback.format_exc().splitlines()[-30:],
        }
        if extra:
            payload.update(extra)
        return jsonify(payload), status
    return jsonify({"error": "Internal Server Error"}), status


def _g(obj: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


def _num(v) -> float:
    """宽松转数值：支持 '1,234.56' 字符串；无法解析返回 0"""
    try:
        if v is None or v == "":
            return 0.0
        if isinstance(v, (int, float, Decimal)):
            return float(v)
        s = str(v).replace(",", "")
        return float(s)
    except Exception:
        return 0.0


def _pick(d: dict, *names, default=None):
    """从 dict 中按别名顺序取第一个非空值"""
    for n in names:
        if n in d and d[n] not in (None, ""):
            return d[n]
    return default


def _set_if_has(obj, data: dict, target: str, *aliases: str):
    """如果模型上有 target 字段，则从 data 中按 (target, *aliases) 顺序取第一个出现的键写入。"""
    if not hasattr(obj, target):
        return
    keys = (target,) + aliases
    for k in keys:
        if k in data:
            try:
                setattr(obj, target, data[k])
            except Exception:
                pass
            return


def _get_if_has(obj, *names: str):
    """从 obj 上按顺序取第一个存在且非空的属性值。"""
    for n in names:
        if hasattr(obj, n):
            try:
                v = getattr(obj, n)
            except Exception:
                v = None
            if v not in (None, ""):
                return v
    return None


def _to_jsonable(v: Any):
    """把不能直接 JSON 的类型转换为可序列化的安全类型"""
    if v is None:
        return None
    if isinstance(v, (int, float, str, bool)):
        return v
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v  # 其它类型交给 _json_ready 递归处理


def _json_ready(x: Any):
    """递归把 dict/list/tuple 中的值变成可 JSON 序列化"""
    if isinstance(x, dict):
        return {k: _json_ready(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_ready(v) for v in x]
    return _to_jsonable(x)


def _parse_date_like(s: Optional[Union[str, int, float]]) -> Optional[Union[date, datetime]]:
    """尽量把字符串解析为 date/datetime；失败则返回 None（避免类型比较异常）"""
    if not s and s != 0:
        return None
    try:
        if isinstance(s, (int, float)):
            return datetime.fromtimestamp(float(s))
        ss = str(s).strip()
        # ISO 8601
        try:
            return datetime.fromisoformat(ss)
        except Exception:
            pass
        try:
            return date.fromisoformat(ss)
        except Exception:
            pass
        # 常见 'YYYY/MM/DD' 或 'YYYY.MM.DD'
        for sep in ("/", "."):
            if sep in ss:
                parts = ss.split(sep)
                if len(parts) == 3:
                    y, m, d = [int(x) for x in parts]
                    return date(y, m, d)
    except Exception:
        return None
    return None


# -------------------------------
# 序列化
# -------------------------------
def _order_to_dict(o: Order) -> Dict[str, Any]:
    """把 Order 实例序列化成字典（金额/别名兜底）"""
    d: Dict[str, Any] = {
        "id": _g(o, "id"),
        "order_no": _g(o, "order_no"),
        "produce_no": _g(o, "produce_no"),
        "product": _g(o, "product"),

        # 数量/金额类
        "qty_total": _to_jsonable(_g(o, "qty_total")),
        "stock_qty": _to_jsonable(_g(o, "stock_qty")),
        "order_qty": _to_jsonable(_g(o, "order_qty")),
        "delivered_qty": _to_jsonable(_g(o, "delivered_qty")),
        "deficit_qty": _to_jsonable(_g(o, "deficit_qty")),
        "finished_in_stock": _to_jsonable(_get_if_has(o, "finished_in_stock", "stock_finished_qty")),
        "unit_price": _to_jsonable(_g(o, "unit_price")),

        # 业务字段
        "currency": _g(o, "currency"),
        "status": _g(o, "status"),
        "remark": _g(o, "remark"),
        "process_content": _g(o, "process_content"),
        "packing_req": _g(o, "packing_req"),
        "default_small_bag": _g(o, "default_small_bag"),
        "default_box_num": _g(o, "default_box_num"),
        "container_code": _g(o, "container_code"),
        "department": _g(o, "department"),
        "biz_dept": _g(o, "biz_dept"),
        "poid": _g(o, "poid"),
        "cn_name": _g(o, "cn_name"),

        # 新增字段
        "forecast_qty": _to_jsonable(_g(o, "forecast_qty")),
        "stock_location": _g(o, "stock_location"),

        # 关联/外键/时间
        "customer_id": _to_jsonable(_g(o, "customer_id")),
        "customer_code": _g(o, "customer_code"),
        "route_id": _to_jsonable(_g(o, "route_id")),
        "batch_no": _g(o, "batch_no"),
        "due_date": _to_jsonable(_g(o, "due_date")),
        "order_date": _to_jsonable(_g(o, "order_date")),
        "delivery_date": _to_jsonable(_g(o, "delivery_date")),
    }

    # ------- 明细（优先 relationship；否则表查询兜底） -------
    lines: Optional[List[Any]] = None
    for rel_name in ("order_lines", "lines", "items"):
        if hasattr(o, rel_name):
            try:
                lines = list(getattr(o, rel_name) or [])
                break
            except Exception:
                lines = None

    if lines is None or len(lines) == 0:
        try:
            lines = (
                db.session.query(OrderLine)
                .filter(OrderLine.order_id == o.id)
                .order_by(OrderLine.line_no.asc(), OrderLine.id.asc())
                .all()
            )
        except Exception:
            lines = []

    def _line_dict(x: Any) -> Dict[str, Any]:
        def _get(*names):
            for n in names:
                v = _g(x, n)
                if v not in (None, ""):
                    return v
            return None

        return {
            "id": _to_jsonable(_g(x, "id")),
            "order_id": _to_jsonable(_g(x, "order_id")),
            "line_no": _to_jsonable(_g(x, "line_no")),
            "product_text": _get(
                "product_text", "product", "name",
                "internal_no", "inner_no", "drawing_no", "drawing",
                "part_no", "partNo", "part_code", "partCode", "sku"
            ),
            "spec": _get("spec", "specification", "specs", "model", "standard"),
            "material_code": _get("material_code", "materialCode", "part_code", "partCode", "code"),
            "material": _get("material", "material_name", "materialName"),

            # === 新增：客户图号 ===
            "customer_part_no": _get("customer_part_no", "customer_part", "cust_part_no", "customer_drawing_no", "drawing_no"),

            # === 关键两列 ===
            "stock_location": _get("stock_location", "location", "stock_place", "warehouse_location"),
            "forecast_qty": _to_jsonable(_get("forecast_qty", "fc", "forecast", "forecast_quantity", "forecastQty")),

            "qty": _to_jsonable(_get("qty", "quantity")),
            "currency_code": _get("currency_code", "unit", "uom", "currency", "currencyCode"),
            "tax_rate": _to_jsonable(_get("tax_rate", "vat_rate", "vatRate")),
            "unit_price": _to_jsonable(_get("unit_price", "price", "unitPrice")),
            "amount": _to_jsonable(_get("amount", "line_total", "lineTotal", "total")),
            "created_at": _to_jsonable(_g(x, "created_at")),
            "updated_at": _to_jsonable(_g(x, "updated_at")),
        }

    d["lines"] = [_line_dict(x) for x in (lines or [])]

    # 将第一条明细镜像到顶层，方便列表直接展示
    if d["lines"]:
        first = d["lines"][0]
        d.setdefault("spec", first.get("spec"))
        d.setdefault("material_code", first.get("material_code"))
        d.setdefault("material", first.get("material"))
        d.setdefault("product_text", first.get("product_text"))
        # === 新增两行镜像 ===
        d.setdefault("stock_location", first.get("stock_location"))
        d.setdefault("forecast_qty", first.get("forecast_qty"))
        d.setdefault("default_outer_pack", d.get("default_box_num") or d.get("default_outer_box") or d.get("outer_box_default"))
        # === 新增：把客户图号镜像到顶层，便于前端直接显示 ===
        if first.get("customer_part_no"):
            d.setdefault("customer_part_no", first.get("customer_part_no"))

    # 顶层"内部图号"兜底
    if not d.get("product_text"):
        for k in ("product_text", "produce_no", "product", "cn_name", "material_code", "batch_no"):
            v = d.get(k)
            if v:
                d["product_text"] = v
                break

    # 合计金额 amount_total 兜底
    for k in (
        "amount_total", "amountTotal", "grand_total", "grandTotal", "subtotal",
        "sub_total", "sum", "total_amount", "totalAmount", "total", "amount"
    ):
        v = d.get(k)
        if v not in (None, ""):
            d["amount_total"] = _num(v)
            break

    if d.get("amount_total") in (None, "") and d.get("lines"):
        total = 0.0
        try:
            for x in d["lines"]:
                cand = next((x.get(tk) for tk in ("amount", "line_total", "total") if x.get(tk) not in (None, "")), None)
                if cand is not None:
                    total += _num(cand)
                else:
                    total += _num(x.get("qty")) * _num(x.get("unit_price"))
            d["amount_total"] = total
        except Exception:
            pass

    if d.get("amount_total") in (None, ""):
        qty = _num(d.get("qty_total") or d.get("order_qty") or d.get("stock_qty"))
        price = _num(d.get("unit_price"))
        if qty > 0 and price > 0:
            d["amount_total"] = qty * price

    # "要求纳期"兼容键名
    if d.get("due_date") and not d.get("request_date"):
        d["request_date"] = d["due_date"]

    # 别名镜像
    d.setdefault("stock_finished_qty", d.get("finished_in_stock"))
    d.setdefault("container_no", d.get("container_code"))
    d.setdefault("containerNo", d.get("container_code"))

    # === 三项显示相关镜像（前端容易取到） ===
    d.setdefault("default_outer_box", d.get("default_box_num"))     # 默认外包装
    d.setdefault("outer_box_default", d.get("default_box_num"))
    d.setdefault("default_outer_pack", d.get("default_box_num"))

    d.setdefault("fc", d.get("forecast_qty"))                       # 预测数量(FC)
    d.setdefault("forecast", d.get("forecast_qty"))

    d.setdefault("location", d.get("stock_location"))               # 库存所在地
    d.setdefault("stock_place", d.get("stock_location"))
    d.setdefault("warehouse_location", d.get("stock_location"))

    return _json_ready(d)


# -------------------------------
# 查询构建 / 分页（供子模块调用）
# -------------------------------
def _build_list_query(params: Dict[str, Any]):
    q = Order.query

    # 允许 _no_rel=1 关闭预加载
    rel_name = next((rn for rn in ("order_lines", "lines", "items") if hasattr(Order, rn)), None)
    if str(params.get("_no_rel", "")).strip() != "1":
        if rel_name:
            try:
                q = q.options(selectinload(getattr(Order, rel_name)))
            except Exception:
                pass  # 预加载失败不要中断列表

    # 关键词匹配
    kw = (params.get("keyword") or params.get("q") or "").strip()
    if kw:
        like_exprs = []
        for col in ("order_no", "product", "cn_name", "customer_code", "batch_no", "produce_no"):
            c = getattr(Order, col, None)
            if c is not None:
                try:
                    like_exprs.append(cast(c, String).like(f"%{kw}%"))
                except Exception:
                    pass
        if like_exprs:
            q = q.filter(or_(*like_exprs))

    # 过滤：status
    status = (params.get("status") or "").strip()
    if status and hasattr(Order, "status"):
        q = q.filter(Order.status == status)

    # 过滤：customer_id
    cust_id = params.get("customer_id")
    if cust_id not in (None, "", []):
        try:
            if hasattr(Order, "customer_id"):
                q = q.filter(Order.customer_id == int(cust_id))
        except Exception:
            pass

    # 过滤：下单日期范围
    date_from = _parse_date_like(params.get("date_from"))
    if date_from and hasattr(Order, "order_date"):
        try:
            q = q.filter(Order.order_date >= date_from)
        except Exception:
            pass

    date_to = _parse_date_like(params.get("date_to"))
    if date_to and hasattr(Order, "order_date"):
        try:
            q = q.filter(Order.order_date <= date_to)
        except Exception:
            pass

    # 默认按 id 倒序
    q = q.order_by(Order.id.desc())
    return q


def _paginate(q, page: int, page_size: int):
    """Flask-SQLAlchemy 3.x paginate，失败时回退到手写分页"""
    try:
        paging = db.paginate(q, page=page, per_page=page_size, error_out=False)
        return paging.items, paging.total
    except Exception:
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items, total


# 供子模块复用的导出符号
__all__ = [
    "bp", "db", "Order", "OrderLine",
    "_debug_on", "_err", "_g", "_num", "_pick", "_set_if_has", "_get_if_has",
    "_to_jsonable", "_json_ready", "_parse_date_like",
    "_order_to_dict", "_build_list_query", "_paginate",
    "ORDER_BP_VERSION", "selectinload", "or_", "cast", "String",
    "current_app", "request", "time", "os", "jsonify"
]


# -------------------------------
# 统一在此处挂载子模块路由（保持只注册一次 bp）
# -------------------------------
# 注意：这两行导入必须放在文件末尾，避免导入时的循环引用
from . import order     # noqa: E402, F401
from . import ordernew  # noqa: E402, F401
