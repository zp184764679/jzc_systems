# routes/supplier_admin/supplier_routes.py
# 供应商管理系统 - 供应商路由模块
# -*- coding: utf-8 -*-
from flask import Blueprint, request
from datetime import datetime
from extensions import db
from models.supplier import Supplier
from sqlalchemy import or_, desc
import logging
import traceback

from .utils import (
    make_response, error_response, success_response,
    handle_db_operation, validate_json_data, check_admin_permission
)
from .serializers import supplier_to_dict

logger = logging.getLogger(__name__)

bp_supplier = Blueprint(
    "supplier_admin_supplier",
    __name__,
    url_prefix="/api/v1/suppliers/admin"
)


# ==============================
# OPTIONS 预检处理
# ==============================
@bp_supplier.route("/", methods=["OPTIONS"])
@bp_supplier.route("/list", methods=["OPTIONS"])
@bp_supplier.route("/pending", methods=["OPTIONS"])
@bp_supplier.route("/<int:supplier_id>", methods=["OPTIONS"])
@bp_supplier.route("/<int:supplier_id>/approve", methods=["OPTIONS"])
@bp_supplier.route("/<int:supplier_id>/reject", methods=["OPTIONS"])
@bp_supplier.route("/<int:supplier_id>/freeze", methods=["OPTIONS"])
@bp_supplier.route("/<int:supplier_id>/rating", methods=["OPTIONS"])
@bp_supplier.route("/ratings/update-all", methods=["OPTIONS"])
@bp_supplier.route("/ratings/top", methods=["OPTIONS"])
def handle_options():
    """处理 CORS 预检请求"""
    resp = make_response()
    return resp, 204


# ==============================
# 供应商管理 API
# ==============================
@bp_supplier.route('/list', methods=['GET'])
@handle_db_operation("获取供应商列表")
def get_suppliers():
    """
    GET /api/v1/suppliers/admin/list?status=approved&page=1&per_page=10
    获取供应商列表（可按状态筛选）
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    try:
        status = request.args.get('status', None)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Supplier.query
        
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(desc(Supplier.created_at))
        paginated = query.paginate(page=page, per_page=per_page)
        
        suppliers = [supplier_to_dict(s) for s in paginated.items if s]
        
        return success_response({
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": per_page,
            "items": suppliers
        })
    
    except Exception as e:
        logger.error(f"❌ 获取供应商列表错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("获取供应商列表失败", 500)


@bp_supplier.route('/pending', methods=['GET'])
@handle_db_operation("获取待审批供应商")
def get_pending_suppliers():
    """
    GET /api/v1/suppliers/admin/pending?q=keyword
    获取待审批的供应商列表
    
    查询参数：
    - q: 关键词（搜索公司名、税号、联系人、电话、邮箱）
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    try:
        keyword = request.args.get('q', '', type=str).strip()
        
        query = Supplier.query.filter_by(status='pending')
        
        # 按关键词搜索
        if keyword:
            kw = f"%{keyword}%"
            query = query.filter(or_(
                Supplier.company_name.ilike(kw),
                Supplier.tax_id.ilike(kw),
                Supplier.contact_name.ilike(kw),
                Supplier.contact_phone.ilike(kw),
                Supplier.contact_email.ilike(kw),
                Supplier.email.ilike(kw)
            ))
        
        suppliers = query.order_by(desc(Supplier.created_at)).all()
        
        result = [supplier_to_dict(s) for s in suppliers if s]
        
        logger.info(f"✅ 获取待审批供应商: 共 {len(result)} 家（关键词: '{keyword}'）")
        
        return success_response(result)
    
    except Exception as e:
        logger.error(f"❌ 获取待审批供应商错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("获取待审批供应商失败", 500)


@bp_supplier.route('/<int:supplier_id>', methods=['GET'])
@handle_db_operation("获取供应商详情")
def get_supplier(supplier_id):
    """
    GET /api/v1/suppliers/admin/{supplier_id}
    获取指定供应商的详细信息
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return error_response("供应商不存在", 404)
        
        return success_response(supplier_to_dict(supplier))
    
    except Exception as e:
        logger.error(f"❌ 获取供应商详情错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("获取供应商详情失败", 500)


@bp_supplier.route('/<int:supplier_id>', methods=['PUT'])
@handle_db_operation("修改供应商信息")
def update_supplier(supplier_id):
    """
    PUT /api/v1/suppliers/admin/{supplier_id}
    修改供应商信息（管理员用）
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    data, err = validate_json_data()
    if err:
        return err
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return error_response("供应商不存在", 404)
        
        # 允许更新的字段（所有扩展字段）
        updateable_fields = [
            # 原有字段
            'company_name', 'contact_name', 'contact_phone', 'contact_email',
            'business_scope', 'address', 'province', 'city', 'district', 'tax_id',

            # 🏢 基本信息扩展字段
            'credit_code', 'tax_number', 'legal_representative', 'registered_capital',
            'registered_address', 'established_date', 'company_type', 'business_status',

            # 📞 联系方式扩展字段
            'company_phone', 'fax', 'website', 'office_address', 'postal_code',

            # 💼 业务信息扩展字段
            'company_description', 'description', 'main_products', 'annual_revenue',
            'employee_count', 'factory_area', 'production_capacity', 'quality_certifications',

            # 💰 财务信息扩展字段
            'bank_name', 'bank_account', 'bank_branch', 'swift_code',
            'payment_terms', 'credit_rating', 'tax_registration_number', 'invoice_type'
        ]

        for field in updateable_fields:
            if field in data:
                setattr(supplier, field, data[field])
        
        supplier.updated_at = datetime.now()
        db.session.commit()
        
        return success_response(supplier_to_dict(supplier), message="供应商信息更新成功")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 修改供应商信息错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("修改供应商信息失败", 500)


@bp_supplier.route('/<int:supplier_id>/approve', methods=['PUT'])
@handle_db_operation("批准供应商")
def approve_supplier(supplier_id):
    """
    PUT /api/v1/suppliers/admin/{supplier_id}/approve
    批准供应商注册
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return error_response("供应商不存在", 404)
        
        if supplier.status == 'approved':
            return error_response("该供应商已被批准", 400)
        
        supplier.status = 'approved'
        supplier.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"✅ 供应商 {supplier.company_name} 已被批准")
        
        return success_response(supplier_to_dict(supplier), message="供应商已被批准")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 批准供应商错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("批准供应商失败", 500)


@bp_supplier.route('/<int:supplier_id>/reject', methods=['PUT'])
@handle_db_operation("拒绝供应商")
def reject_supplier(supplier_id):
    """
    PUT /api/v1/suppliers/admin/{supplier_id}/reject
    拒绝供应商注册
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    data, err = validate_json_data()
    if err:
        return err
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return error_response("供应商不存在", 404)
        
        if supplier.status == 'rejected':
            return error_response("该供应商已被拒绝", 400)
        
        supplier.status = 'rejected'
        supplier.reason = data.get('reason', '')
        supplier.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"❌ 供应商 {supplier.company_name} 已被拒绝")
        
        return success_response(supplier_to_dict(supplier), message="供应商已被拒绝")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 拒绝供应商错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("拒绝供应商失败", 500)


@bp_supplier.route('/<int:supplier_id>', methods=['DELETE'])
@handle_db_operation("删除供应商")
def delete_supplier(supplier_id):
    """
    DELETE /api/v1/suppliers/admin/{supplier_id}
    删除供应商（管理员用）
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return error_response("供应商不存在", 404)
        
        supplier_name = supplier.company_name
        db.session.delete(supplier)
        db.session.commit()
        
        logger.info(f"✅ 供应商 {supplier_name} 已被删除")
        
        return success_response(message=f"供应商 {supplier_name} 已被删除")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 删除供应商错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("删除供应商失败", 500)


# ==============================
# 供应商评分 API
# ==============================
@bp_supplier.route('/<int:supplier_id>/rating', methods=['PUT'])
@handle_db_operation("更新供应商评分")
def update_supplier_rating_endpoint(supplier_id):
    """
    PUT /api/v1/suppliers/admin/{supplier_id}/rating
    更新指定供应商的评分（基于订单数据自动计算）
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err

    try:
        from services.supplier_rating_service import update_supplier_rating

        result = update_supplier_rating(supplier_id)

        if result.get('success'):
            return success_response(result, message=f"供应商评分已更新: {result['rating']}/5.0")
        else:
            return error_response(result.get('error', '评分更新失败'), 500)

    except Exception as e:
        logger.error(f"❌ 更新供应商评分错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("更新供应商评分失败", 500)


@bp_supplier.route('/ratings/update-all', methods=['POST'])
@handle_db_operation("批量更新所有供应商评分")
def batch_update_ratings_endpoint():
    """
    POST /api/v1/suppliers/admin/ratings/update-all
    批量更新所有已批准供应商的评分
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err

    try:
        from services.supplier_rating_service import batch_update_all_ratings

        result = batch_update_all_ratings()

        return success_response(result, message=f"批量评分更新完成: 成功 {result['success']}/{result['total']}")

    except Exception as e:
        logger.error(f"❌ 批量更新评分错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("批量更新评分失败", 500)


@bp_supplier.route('/ratings/top', methods=['GET'])
@handle_db_operation("获取评分最高的供应商")
def get_top_suppliers_endpoint():
    """
    GET /api/v1/suppliers/admin/ratings/top?limit=10
    获取评分最高的供应商列表
    """
    # 权限检查
    is_admin, err = check_admin_permission()
    if err:
        return err

    try:
        from services.supplier_rating_service import get_top_suppliers

        limit = request.args.get('limit', 10, type=int)
        result = get_top_suppliers(limit=limit)

        return success_response(result, message=f"获取前 {len(result)} 名供应商")

    except Exception as e:
        logger.error(f"❌ 获取评分排名错误: {str(e)}\n{traceback.format_exc()}")
        return error_response("获取评分排名失败", 500)