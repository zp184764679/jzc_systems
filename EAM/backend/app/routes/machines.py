# -*- coding: utf-8 -*-
# app/routes/machines.py
from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import date
import re

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from sqlalchemy import or_, desc, asc

from .. import db
from ..models.machine import Machine

bp = Blueprint("machines", __name__, url_prefix="/api/machines")


# ==========================
# 工具函数
# ==========================
def _json() -> Dict[str, Any]:
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:
        return {}

def _trim(s: Optional[str]) -> Optional[str]:
    return s.strip() if isinstance(s, str) else s

def _as_bool(v: Any) -> Optional[bool]:
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    s = str(v).lower()
    if s in ("1", "true", "t", "yes", "y", "on"):
        return True
    if s in ("0", "false", "f", "no", "n", "off"):
        return False
    return None

def _as_int(v: Any) -> Optional[int]:
    try:
        return int(v) if v not in (None, "") else None
    except Exception:
        return None

def _as_date(s: Any) -> Optional[date]:
    """支持 YYYY-MM-DD 或包含时间戳前 10 位的字符串。"""
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None

_slug_re = re.compile(r"[^A-Za-z0-9]+")
def _derive_code(name: str) -> str:
    """根据名称简单派生一个 code（仅兜底，真实情况建议前端填写）。"""
    name = name or "MC"
    base = _slug_re.sub("-", name).strip("-").upper()[:12] or "MC"
    return f"{base}"

def _apply_updates(m: Machine, data: Dict[str, Any]) -> None:
    """将 data 写入模型实例；只在有值时更新，避免无意覆盖。"""
    fields = {
        "machine_code": _trim(data.get("machine_code") or data.get("code")),
        "name":         _trim(data.get("name")),
        "model":        _trim(data.get("model")),
        "group":        _trim(data.get("group")),
        "dept_name":    _trim(data.get("dept_name")),
        "sub_dept_name":_trim(data.get("sub_dept_name")),
        "is_active":    _as_bool(data.get("is_active")),

        # 扩展
        "factory_location": _trim(data.get("factory_location") or data.get("factoryLocation") or data.get("factory_loc") or data.get("location")),
        "brand":            _trim(data.get("brand") or data.get("brand_name") or data.get("brandName")),
        "serial_no":        _trim(data.get("serial_no") or data.get("serialNo") or data.get("sn") or data.get("factory_serial")),
        "manufacture_date": _as_date(data.get("manufacture_date") or data.get("mfg_date") or data.get("production_date") or data.get("factory_date")),
        "purchase_date":    _as_date(data.get("purchase_date") or data.get("buy_date") or data.get("procure_date")),
        "place":            _trim(data.get("place") or data.get("location_place") or data.get("store_place") or data.get("storage_place") or data.get("site")),
        "manufacturer":     _trim(data.get("manufacturer") or data.get("maker") or data.get("vendor") or data.get("producer")),
        "capacity":         _as_int(data.get("capacity")),
        "status":           _trim(data.get("status")),
    }
    for k, v in fields.items():
        if v is None:
            continue
        setattr(m, k, v)

def _dto(m: Machine) -> Dict[str, Any]:
    """统一返回别名，兼容前端读取 r.code。"""
    d = m.to_dict()
    d.setdefault("code", d.get("machine_code"))
    return d


# ==========================
# 路由：列表 / 详情 / 新增 / 修改 / 删除
# ==========================

@bp.route("", methods=["GET"], strict_slashes=False)
@bp.route("/", methods=["GET"], strict_slashes=False)
@cross_origin()
def list_machines_get():
    """
    支持：
    - 单条探测：?id=xx 或 ?code=MC-001
    - 关键字：?q=xxx / ?keyword=xxx / ?code=xxx / ?name=xxx
    - 分类筛选：?dept_name=数控
    - 分页：?page=1&page_size=10
    - 排序：?sort_by=created_at|name|machine_code 等，?order=asc|desc
    """
    args = request.args or {}

    # 单条探测优先
    mid_raw = _trim(args.get("id"))
    code_eq = _trim(args.get("code"))
    if (mid_raw and mid_raw.isdigit()) or code_eq:
        m = None
        if mid_raw and mid_raw.isdigit():
            m = Machine.query.get(int(mid_raw))
        elif code_eq:
            m = Machine.query.filter(Machine.machine_code == code_eq).first()
        if not m:
            return jsonify({"error": "not found"}), 404
        return jsonify(_dto(m))

    # 读取参数
    page      = _as_int(args.get("page")) or _as_int(args.get("p")) or 1
    page_size = _as_int(args.get("page_size")) or _as_int(args.get("ps")) or 10

    # 统一兼容的关键字
    q_all  = _trim(args.get("q") or args.get("keyword"))
    code_kw = _trim(args.get("code"))
    name_kw = _trim(args.get("name"))
    dept    = _trim(args.get("dept_name"))

    sort_by = args.get("sort_by") or "created_at"
    order   = (args.get("order") or "desc").lower()

    # 组装查询
    query = Machine.query

    # 全局关键字（多字段模糊）
    if q_all:
        like = f"%{q_all}%"
        query = query.filter(
            or_(
                Machine.name.ilike(like),
                Machine.machine_code.ilike(like),
                Machine.model.ilike(like),
                Machine.brand.ilike(like),
                Machine.serial_no.ilike(like),
                Machine.place.ilike(like),
                Machine.manufacturer.ilike(like),
            )
        )

    # 单字段模糊
    if code_kw:
        query = query.filter(Machine.machine_code.ilike(f"%{code_kw}%"))
    if name_kw:
        query = query.filter(Machine.name.ilike(f"%{name_kw}%"))

    # 部门分类筛选
    if dept:
        query = query.filter(Machine.dept_name == dept)

    # 排序
    sortable = {
        "created_at":   Machine.created_at,
        "updated_at":   Machine.updated_at,
        "name":         Machine.name,
        "machine_code": Machine.machine_code,
        "model":        Machine.model,
        "status":       Machine.status,
        "dept_name":    Machine.dept_name,
    }
    col = sortable.get(sort_by, Machine.created_at)
    query = query.order_by(asc(col) if order == "asc" else desc(col))

    # 分页
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    data = [_dto(m) for m in items]

    return jsonify({
        "page": page,
        "page_size": page_size,
        "total": total,
        "list": data,
        "items": data,
    })


@bp.route("", methods=["POST"], strict_slashes=False)
@bp.route("/", methods=["POST"], strict_slashes=False)
@cross_origin()
def create_machine():
    """
    新增：
    - 至少需要 name
    - code/machine_code 二选一，不给则从 name 派生
    """
    data = _json()
    name = _trim(data.get("name") or "")
    if not name:
        return jsonify({"error": "name is required"}), 400

    machine_code = _trim(data.get("machine_code") or data.get("code")) or _derive_code(name)

    # 唯一性检查
    if Machine.query.filter(Machine.machine_code == machine_code).first():
        return jsonify({"error": "machine_code duplicated"}), 409

    m = Machine(machine_code=machine_code, name=name)
    _apply_updates(m, data)

    try:
        db.session.add(m)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "db error", "detail": str(e)}), 500

    return jsonify(_dto(m)), 201


@bp.get("/<int:mid>")
@cross_origin()
def get_machine(mid: int):
    m = Machine.query.get_or_404(mid)
    return jsonify(_dto(m))


@bp.put("/<int:mid>")
@cross_origin()
def update_machine(mid: int):
    """
    更新：
    - 支持修改 machine_code（保证唯一）
    - 支持修改 dept_name（部门分类）
    """
    m = Machine.query.get_or_404(mid)
    data = _json()

    # machine_code 可改（若传了）
    code = _trim(data.get("machine_code") or data.get("code"))
    if code and code != m.machine_code:
        if Machine.query.filter(Machine.machine_code == code, Machine.id != mid).first():
            return jsonify({"error": "machine_code duplicated"}), 409
        m.machine_code = code

    _apply_updates(m, data)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "db error", "detail": str(e)}), 500

    return jsonify(_dto(m))


@bp.delete("/<int:mid>")
@cross_origin()
def delete_machine(mid: int):
    m = Machine.query.get_or_404(mid)
    try:
        db.session.delete(m)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "db error", "detail": str(e)}), 500
    return jsonify({"ok": True, "id": mid})


# 兼容：有的前端会用 POST 来做列表查询
@bp.post("/list")
@bp.post("/query")
@bp.post("/search")
@cross_origin()
def list_machines_post_alias():
    body = _json()
    # 将 body 映射为 querystring 形式调用同一逻辑
    with bp.test_request_context(
        query_string={
            k: v
            for k, v in {
                "q": body.get("q") or body.get("keyword"),
                "page": body.get("page"),
                "page_size": body.get("page_size"),
                "sort_by": body.get("sort_by"),
                "order": body.get("order"),
                "id": body.get("id"),
                "code": body.get("code"),
                "name": body.get("name"),
                "dept_name": body.get("dept_name"),
            }.items()
            if v is not None and v != ""
        }
    ):
        return list_machines_get()
