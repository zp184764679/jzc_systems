# -*- coding: utf-8 -*-
# backend/app/routes/inventory.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from sqlalchemy import func, and_, or_, desc

from app import db
from app.models.inventory import InventoryTx

# 注意：变量名必须叫 bp（你的工厂会自动扫描并注册）
bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")

# ---------- 公共工具 ----------
def _g(name: str, default: Optional[str] = None) -> Optional[str]:
    v = request.args.get(name)
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default

def _json() -> dict:
    return request.get_json(silent=True) or {}

def _j(name: str, default=None):
    data = _json()
    return data[name] if name in data else default

def _num(v) -> Decimal:
    try:
        if v is None or v == "":
            return Decimal("0")
        return Decimal(str(v))
    except Exception:
        return Decimal("0")

def _ok(data=None, status=200):
    return (jsonify({"ok": True, "data": data}), status) if data is not None else (jsonify({"ok": True}), status)

def _err(msg, status=400):
    return jsonify({"ok": False, "error": msg}), status

# 优先选择 occurred_at，没有则回退 created_at
_OCC_TIME = getattr(InventoryTx, "occurred_at", getattr(InventoryTx, "created_at", None))

# 统一合法类型（如模型/业务允许更多类型，在这里加）
_VALID_TYPES = {"IN", "OUT", "DELIVERY", "ADJUST"}

# ---------- 预检（CORS） ----------
@bp.route("", methods=["OPTIONS"])
@bp.route("/tx", methods=["OPTIONS"])
@bp.route("/stock", methods=["OPTIONS"])
@bp.route("/delivery-verify", methods=["OPTIONS"])
@bp.route("/in", methods=["OPTIONS"])
@bp.route("/out", methods=["OPTIONS"])
@bp.route("/adjust", methods=["OPTIONS"])
@cross_origin()
def _preflight():
    return ("", 204)

# ---------- 健康检查 ----------
@bp.get("/ping")
@cross_origin()
def ping():
    return jsonify({"ok": True})

# ---------- 库存流水：查询 ----------
@bp.get("/tx")
@bp.get("/transactions")
@cross_origin()
def list_tx():
    """
    支持筛选：
      - product_text / internal_no（完全匹配）
      - order_no（完全匹配）
      - tx_type in {IN, OUT, DELIVERY, ADJUST}
      - location, bin_code（完全匹配）
      - 时间范围：occurred_from, occurred_to（字符串；若模型没有 occurred_at 会自动用 created_at）
      - keyword：对 product_text/order_no/bin_code/location/tx_type/ref/remark 模糊
    分页：
      - page, page_size（<=500）
    排序：按发生时间/创建时间倒序（_OCC_TIME）
    """
    product_text = _g("product_text") or _g("internal_no")
    order_no     = _g("order_no")
    tx_type      = _g("tx_type")
    location     = _g("location")
    bin_code     = _g("bin_code")
    occurred_from = _g("occurred_from")
    occurred_to   = _g("occurred_to")
    keyword      = _g("q") or _g("keyword")
    page         = int(_g("page", "1") or "1")
    page_size    = min(max(int(_g("page_size", "50") or "50"), 1), 500)

    q = db.session.query(InventoryTx)

    if product_text:
        q = q.filter(InventoryTx.product_text == product_text)
    if order_no:
        q = q.filter(InventoryTx.order_no == order_no)
    if tx_type in _VALID_TYPES:
        q = q.filter(InventoryTx.tx_type == tx_type)
    if location:
        q = q.filter(InventoryTx.location == location)
    if bin_code:
        q = q.filter(InventoryTx.bin_code == bin_code)

    if _OCC_TIME is not None:
        if occurred_from:
            q = q.filter(_OCC_TIME >= occurred_from)
        if occurred_to:
            q = q.filter(_OCC_TIME <= occurred_to)

    if keyword:
        like = f"%{keyword}%"
        conds = [InventoryTx.product_text.like(like)]
        if hasattr(InventoryTx, "order_no"):  conds.append(InventoryTx.order_no.like(like))
        if hasattr(InventoryTx, "bin_code"):  conds.append(InventoryTx.bin_code.like(like))
        if hasattr(InventoryTx, "location"):  conds.append(InventoryTx.location.like(like))
        if hasattr(InventoryTx, "tx_type"):   conds.append(InventoryTx.tx_type.like(like))
        if hasattr(InventoryTx, "ref"):       conds.append(InventoryTx.ref.like(like))
        if hasattr(InventoryTx, "remark"):    conds.append(InventoryTx.remark.like(like))
        q = q.filter(or_(*conds))

    # 排序
    if _OCC_TIME is not None:
        q = q.order_by(desc(_OCC_TIME))
    else:
        q = q.order_by(desc(InventoryTx.id))

    total = q.count()
    items = q.limit(page_size).offset((page - 1) * page_size).all()

    # 统一 to_dict
    def _to_dict(x):
        if hasattr(x, "to_dict"):
            return x.to_dict()
        d = {c.name: getattr(x, c.name) for c in x.__table__.columns}
        # 时间转字符串
        for k in ("occurred_at", "created_at", "updated_at"):
            if k in d and d[k] is not None:
                try:
                    d[k] = d[k].isoformat()
                except Exception:
                    pass
        return d

    return jsonify({
        "items": [_to_dict(x) for x in items],
        "total": total,
        "page": page,
        "page_size": page_size
    })

# ---------- 库存流水：创建（支持单条或批量） ----------
@bp.post("/tx")
@cross_origin()
def create_tx():
    """
    Body:
      - 单条：{ product_text, qty_delta, tx_type?, order_no?, uom?, location?, bin_code?, occurred_at?, ref?, remark? }
      - 批量：[ {...}, {...} ]
    仅对模型中存在的列赋值（通过 hasattr 判断），避免因列名差异报错。
    """
    data = _json()
    rows = data if isinstance(data, list) else [data]
    created, fail = [], 0

    for row in rows:
        try:
            if not row.get("product_text"):
                fail += 1; continue
            if "qty_delta" not in row:
                fail += 1; continue

            tx = InventoryTx()
            # 安全赋值（仅当模型有该属性时才设置）
            for k in ("product_text", "qty_delta", "tx_type", "order_no", "uom",
                      "location", "bin_code", "ref", "remark"):
                if hasattr(InventoryTx, k) and k in row:
                    setattr(tx, k, row[k])

            # 发生时间
            if hasattr(InventoryTx, "occurred_at") and row.get("occurred_at"):
                setattr(tx, "occurred_at", row["occurred_at"])

            db.session.add(tx)
            created.append(tx)
        except Exception:
            fail += 1

    db.session.commit()

    # 序列化
    out = []
    for x in created:
        if hasattr(x, "to_dict"):
            out.append(x.to_dict())
        else:
            d = {c.name: getattr(x, c.name) for c in x.__table__.columns}
            for k in ("occurred_at", "created_at", "updated_at"):
                if k in d and d[k] is not None:
                    try:
                        d[k] = d[k].isoformat()
                    except Exception:
                        pass
            out.append(d)

    status = 201 if created and not fail else (207 if created and fail else 400)
    return _ok({"ok": len(created), "fail": fail, "items": out}, status=status)

# ---------- 当前库存（聚合） ----------
@bp.get("/stock")
@cross_origin()
def stock_overview():
    """
    返回库存总览（按"内部图号"为唯一 key 聚合）
    支持筛选：keyword、location=深圳|东莞
    """
    keyword   = _g("keyword") or _g("q")
    location  = _g("location")
    page      = int(_g("page", "1") or "1")
    page_size = min(max(int(_g("page_size", "200") or "200"), 1), 1000)

    # 按内部图号聚合结存
    cols = [
        InventoryTx.product_text.label("internal_no"),
        func.sum(InventoryTx.qty_delta).label("qty"),
        func.max(getattr(InventoryTx, "order_no", None)).label("order_no") if hasattr(InventoryTx, "order_no") else None,
        func.max(getattr(InventoryTx, "uom", None)).label("uom") if hasattr(InventoryTx, "uom") else None,
        func.max(getattr(InventoryTx, "location", None)).label("location") if hasattr(InventoryTx, "location") else None,
        func.max(getattr(InventoryTx, "bin_code", None)).label("bin") if hasattr(InventoryTx, "bin_code") else None,
        func.max(_OCC_TIME).label("last_time") if _OCC_TIME is not None else func.max(InventoryTx.id).label("last_time"),
    ]
    # 过滤掉 None 列
    cols = [c for c in cols if c is not None]

    q_sum = db.session.query(*cols).group_by(InventoryTx.product_text)

    if location and hasattr(InventoryTx, "location"):
        q_sum = q_sum.filter(InventoryTx.location == location)

    if keyword:
        like = f"%{keyword}%"
        q_sum = q_sum.filter(InventoryTx.product_text.like(like))

    # 只显示非零库存
    q_sum = q_sum.having(func.sum(InventoryTx.qty_delta) != 0)

    total = q_sum.count()
    rows  = q_sum.order_by(desc("last_time")).limit(page_size).offset((page - 1) * page_size).all()

    items = []
    for r in rows:
        items.append({
            "orderNo": getattr(r, "order_no", None) or "-",
            "internalNo": r.internal_no,
            "spec": "-",
            "bin": getattr(r, "bin", None) or "-",
            "qty": float(getattr(r, "qty", 0) or 0),
            "uom": getattr(r, "uom", None) or "pcs",
            "place": getattr(r, "location", None) or "-",
        })

    return jsonify({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    })

# ---------- 入库 ----------
@bp.post("/in")
@cross_origin()
def do_in():
    """
    入库：qty>0
    body: {product_text, qty, uom?, location?, bin_code?, order_no?, note?, operator?}
    """
    product_text = _j("product_text")
    qty          = _num(_j("qty"))
    if not product_text or qty <= 0:
        return _err("product_text 必填且 qty>0")

    tx = InventoryTx()
    setattr(tx, "product_text", product_text)
    setattr(tx, "tx_type", "IN") if hasattr(InventoryTx, "tx_type") else None
    if hasattr(InventoryTx, "qty_delta"): tx.qty_delta = qty
    for k in ("uom", "location", "bin_code", "order_no", "ref", "remark"):
        v = _j(k)
        if v is not None and hasattr(InventoryTx, k):
            setattr(tx, k, v)
    if hasattr(InventoryTx, "uom") and not getattr(tx, "uom", None):
        tx.uom = "pcs"

    db.session.add(tx)
    db.session.commit()
    return _ok(getattr(tx, "to_dict")() if hasattr(tx, "to_dict") else None, status=201)

# ---------- 出库 ----------
@bp.post("/out")
@cross_origin()
def do_out():
    """
    出库：qty>0（实际记录为负数）
    body: {product_text, qty, uom?, location?, bin_code?, order_no?, note?, operator?, allow_negative?}
    """
    product_text = _j("product_text")
    qty          = _num(_j("qty"))
    if not product_text or qty <= 0:
        return _err("product_text 必填且 qty>0")

    allow_negative = bool(_j("allow_negative", False))

    # 校验当前结存
    qsum = db.session.query(func.sum(InventoryTx.qty_delta)).filter(InventoryTx.product_text == product_text)
    loc = _j("location")
    if loc and hasattr(InventoryTx, "location"):
        qsum = qsum.filter(InventoryTx.location == loc)
    cur = qsum.scalar() or 0
    if not allow_negative and Decimal(str(cur)) - qty < 0:
        return _err(f"库存不足：当前 {cur}，出库 {qty}")

    tx = InventoryTx()
    setattr(tx, "product_text", product_text)
    if hasattr(InventoryTx, "tx_type"): tx.tx_type = "OUT"
    if hasattr(InventoryTx, "qty_delta"): tx.qty_delta = -qty
    for k in ("uom", "location", "bin_code", "order_no", "ref", "remark"):
        v = _j(k)
        if v is not None and hasattr(InventoryTx, k):
            setattr(tx, k, v)
    if hasattr(InventoryTx, "uom") and not getattr(tx, "uom", None):
        tx.uom = "pcs"

    db.session.add(tx)
    db.session.commit()
    return _ok(getattr(tx, "to_dict")() if hasattr(tx, "to_dict") else None, status=201)

# ---------- 交货核销 ----------
@bp.post("/delivery-verify")
@bp.post("/delivery")
@cross_origin()
def do_delivery_verify():
    """
    交货核销：通常扣减库存
    body: {product_text, qty, order_no?, uom?, location?, bin_code?, note?, operator?}
    """
    product_text = _j("product_text")
    qty          = _num(_j("qty"))
    if not product_text or qty <= 0:
        return _err("product_text 必填且 qty>0")

    tx = InventoryTx()
    setattr(tx, "product_text", product_text)
    if hasattr(InventoryTx, "tx_type"): tx.tx_type = "DELIVERY"
    if hasattr(InventoryTx, "qty_delta"): tx.qty_delta = -qty
    for k in ("uom", "location", "bin_code", "order_no", "ref", "remark"):
        v = _j(k)
        if v is not None and hasattr(InventoryTx, k):
            setattr(tx, k, v)
    if hasattr(InventoryTx, "uom") and not getattr(tx, "uom", None):
        tx.uom = "pcs"

    db.session.add(tx)
    db.session.commit()
    return _ok(getattr(tx, "to_dict")() if hasattr(tx, "to_dict") else None, status=201)

# ---------- 调整/盘点 ----------
@bp.post("/adjust")
@cross_origin()
def do_adjust():
    """
    盘点/修正：qty_delta 可正可负
    body: {product_text, qty_delta, reason?/note?, ...}
    """
    product_text = _j("product_text")
    qty_delta    = _num(_j("qty_delta"))
    if not product_text:
        return _err("product_text 必填")

    tx = InventoryTx()
    setattr(tx, "product_text", product_text)
    if hasattr(InventoryTx, "tx_type"): tx.tx_type = "ADJUST"
    if hasattr(InventoryTx, "qty_delta"): tx.qty_delta = qty_delta
    for k in ("uom", "location", "bin_code", "order_no", "ref", "remark"):
        v = _j(k) if k != "remark" else (_j("remark") or _j("reason"))
        if v is not None and hasattr(InventoryTx, k):
            setattr(tx, k, v)
    if hasattr(InventoryTx, "uom") and not getattr(tx, "uom", None):
        tx.uom = "pcs"

    db.session.add(tx)
    db.session.commit()
    return _ok(getattr(tx, "to_dict")() if hasattr(tx, "to_dict") else None, status=201)
