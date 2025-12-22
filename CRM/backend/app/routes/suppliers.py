# -*- coding: utf-8 -*-
"""
CRM 供应商路由

提供供应商主数据的 CRUD 和搜索 API。
"""

from __future__ import annotations

from typing import Any, Dict
import json

from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .. import db
from ..models.supplier import Supplier, SUPPLIER_STATUS
from ..services.data_permission import (
    crm_auth, crm_optional_auth, crm_admin_required,
    get_current_user, apply_data_permission_filter,
    can_access_record, can_edit_record, can_delete_record
)

bp = Blueprint("suppliers", __name__, url_prefix="/api/suppliers")


# ---------- helpers ----------
def _s(v) -> str:
    return str(v).strip() if v is not None else ""


def _i(v, default=None):
    try:
        if v is None or v == "":
            return default
        return int(v)
    except Exception:
        return default


def _parse_contacts(v):
    """contacts 可为 list / JSON 字符串，统一转成 list[dict]."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        try:
            j = json.loads(s)
            if isinstance(j, list):
                return j
        except Exception:
            pass
    return []


def _parse_tags(v):
    """tags 可为 list / JSON 字符串 / 逗号分割字符串."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        try:
            j = json.loads(s)
            if isinstance(j, list):
                return j
        except Exception:
            pass
        return [t.strip() for t in s.split(",") if t.strip()]
    return []


# ---------- 列表查询 ----------
@bp.route("", methods=["GET"])
@crm_optional_auth
def list_suppliers():
    """
    获取供应商列表

    Query params:
        keyword: 搜索关键词
        status: 状态筛选
        category: 分类筛选
        page: 页码
        page_size: 每页条数
    """
    keyword = request.args.get("keyword", "").strip()
    status = request.args.get("status", "").strip() or None
    category = request.args.get("category", "").strip() or None
    page = _i(request.args.get("page"), 1)
    page_size = _i(request.args.get("page_size"), 20)

    result = Supplier.search(
        keyword=keyword if keyword else None,
        status=status,
        category=category,
        page=page,
        page_size=page_size
    )

    return jsonify(result)


# ---------- 获取单个 ----------
@bp.route("/<int:supplier_id>", methods=["GET"])
@crm_optional_auth
def get_supplier(supplier_id: int):
    """获取供应商详情"""
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify({"error": "供应商不存在"}), 404

    return jsonify(supplier.to_dict())


# ---------- 创建 ----------
@bp.route("", methods=["POST"])
@crm_auth
def create_supplier():
    """创建供应商"""
    data = request.get_json() or {}

    # 必填字段校验
    name = _s(data.get("name"))
    if not name:
        return jsonify({"error": "供应商名称不能为空"}), 400

    # 检查重复
    code = _s(data.get("code"))
    if code:
        existing = Supplier.query.filter_by(code=code).first()
        if existing:
            return jsonify({"error": f"供应商代码 '{code}' 已存在"}), 400

    # 处理联系人和标签
    data["contacts"] = _parse_contacts(data.get("contacts"))
    data["tags"] = _parse_tags(data.get("tags"))

    try:
        supplier = Supplier.from_dict(data)

        # 设置创建人信息
        current_user = get_current_user()
        if current_user:
            supplier.created_by = current_user.get("user_id")
            supplier.owner_id = current_user.get("user_id")
            supplier.owner_name = current_user.get("username")

        db.session.add(supplier)
        db.session.commit()

        return jsonify({
            "message": "创建成功",
            "data": supplier.to_dict()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": f"数据重复: {str(e)}"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库错误: {str(e)}"}), 500


# ---------- 更新 ----------
@bp.route("/<int:supplier_id>", methods=["PUT"])
@crm_auth
def update_supplier(supplier_id: int):
    """更新供应商"""
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify({"error": "供应商不存在"}), 404

    data = request.get_json() or {}

    # 检查代码重复
    new_code = _s(data.get("code"))
    if new_code and new_code != supplier.code:
        existing = Supplier.query.filter_by(code=new_code).first()
        if existing:
            return jsonify({"error": f"供应商代码 '{new_code}' 已存在"}), 400

    # 处理联系人和标签
    if "contacts" in data:
        data["contacts"] = _parse_contacts(data.get("contacts"))
    if "tags" in data:
        data["tags"] = _parse_tags(data.get("tags"))

    try:
        supplier.update_from_dict(data)
        db.session.commit()

        return jsonify({
            "message": "更新成功",
            "data": supplier.to_dict()
        })

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库错误: {str(e)}"}), 500


# ---------- 删除 ----------
@bp.route("/<int:supplier_id>", methods=["DELETE"])
@crm_admin_required
def delete_supplier(supplier_id: int):
    """删除供应商（仅管理员）"""
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify({"error": "供应商不存在"}), 404

    try:
        db.session.delete(supplier)
        db.session.commit()

        return jsonify({"message": "删除成功"})

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"数据库错误: {str(e)}"}), 500


# ---------- 搜索（用于下拉选择器） ----------
@bp.route("/search", methods=["GET"])
@crm_optional_auth
def search_suppliers():
    """
    搜索供应商（用于下拉选择器）

    Query params:
        keyword: 搜索关键词
        limit: 返回条数上限（默认10）
    """
    keyword = request.args.get("keyword", "").strip()
    limit = _i(request.args.get("limit"), 10)

    result = Supplier.search(
        keyword=keyword if keyword else None,
        status="active",  # 只返回正常状态的供应商
        page=1,
        page_size=limit
    )

    # 简化返回格式
    options = [
        {
            "value": s["id"],
            "label": s["short_name"] or s["name"],
            "code": s["code"],
            "name": s["name"],
        }
        for s in result.get("items", [])
    ]

    return jsonify({
        "items": options,
        "total": result.get("total", 0)
    })


# ---------- 获取供应商联系人 ----------
@bp.route("/<int:supplier_id>/contacts", methods=["GET"])
@crm_optional_auth
def get_supplier_contacts(supplier_id: int):
    """获取供应商联系人列表"""
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify({"error": "供应商不存在"}), 404

    return jsonify({
        "items": supplier.contacts or [],
        "total": len(supplier.contacts or [])
    })


# ---------- 状态枚举 ----------
@bp.route("/statuses", methods=["GET"])
def get_statuses():
    """获取供应商状态枚举"""
    return jsonify(SUPPLIER_STATUS)


# ---------- 分类列表 ----------
@bp.route("/categories", methods=["GET"])
@crm_optional_auth
def get_categories():
    """获取供应商分类列表"""
    # 从数据库中获取已有的分类
    categories = db.session.query(Supplier.category).filter(
        Supplier.category.isnot(None),
        Supplier.category != ""
    ).distinct().all()

    return jsonify({
        "items": [c[0] for c in categories if c[0]]
    })
