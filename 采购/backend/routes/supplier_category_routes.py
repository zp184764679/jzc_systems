# routes/supplier_category_routes.py
# 供应商品类管理API路由
# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from extensions import db
from models.supplier_category import SupplierCategory
from models.supplier import Supplier
import logging

from utils.response import error_response, success_response
from utils.decorators import handle_db_operation
from utils.validators import validate_json_data, get_supplier_or_error

logger = logging.getLogger(__name__)

bp_supplier_category = Blueprint(
    "supplier_category",
    __name__
)

# 设置URL前缀，让app.py自动注册时使用
URL_PREFIX = "/api/v1/suppliers"


@bp_supplier_category.route('/categories/me', methods=['GET'])
@handle_db_operation("获取我的品类")
def get_my_categories():
    """
    GET /api/v1/suppliers/categories/me
    获取当前供应商的经营范围（大类）
    """
    supplier, err = get_supplier_or_error()
    if err:
        return err

    try:
        categories = SupplierCategory.query.filter_by(supplier_id=supplier.id).all()
        major_categories = list(set([cat.major_category for cat in categories if cat.major_category]))

        return success_response({
            "major_categories": major_categories,
            "categories": [{"category": cat.category, "major_category": cat.major_category} for cat in categories]
        })

    except Exception as e:
        logger.error(f"❌ 获取品类错误: {str(e)}")
        return error_response("获取品类失败", 500)


@bp_supplier_category.route('/categories/me', methods=['PUT'])
@handle_db_operation("更新我的品类")
def update_my_categories():
    """
    PUT /api/v1/suppliers/categories/me
    更新供应商经营范围（大类）

    请求体：
    {
        "major_categories": ["刀具", "测量工具", "机床附件"]
    }
    """
    supplier, err = get_supplier_or_error()
    if err:
        return err

    data, err = validate_json_data(required_fields=['major_categories'])
    if err:
        return err

    try:
        major_categories = data.get('major_categories', [])

        if not isinstance(major_categories, list):
            return error_response("major_categories 必须是数组", 400)

        if len(major_categories) == 0:
            return error_response("至少需要选择一个经营范围", 400)

        if len(major_categories) > 10:
            return error_response("最多只能选择10个经营范围", 400)

        # 删除现有品类
        SupplierCategory.query.filter_by(supplier_id=supplier.id).delete()

        # 添加新品类
        for major_cat in major_categories:
            category = SupplierCategory(
                supplier_id=supplier.id,
                category=major_cat,  # 这里只有大类，所以 category 和 major_category 相同
                major_category=major_cat,
                minor_category=''
            )
            db.session.add(category)

        db.session.commit()

        logger.info(f"✅ 供应商 {supplier.id} 的品类已更新")

        return success_response({
            "major_categories": major_categories
        }, message="品类更新成功")

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 更新品类错误: {str(e)}")
        return error_response("更新品类失败", 500)


BLUEPRINTS = [bp_supplier_category]
