# routes/supplier_admin/serializers.py
# 供应商管理系统 - 序列化器模块
# -*- coding: utf-8 -*-
import logging
from models.supplier import Supplier

logger = logging.getLogger(__name__)


def _safe_str(value, default=''):
    """安全将值转换为字符串，None 或空值默认为空串"""
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip() if value else default
    return str(value)


def supplier_to_dict(s: Supplier):
    """
    序列化供应商对象 - 与前端字段对齐
    
    ✅ 修复内容：
    1. 返回 'name' 字段（前端表格用 s.name）
    2. 返回 'categories' 列表（品类数据）- 简化为 [{id, name}] 格式
    3. 返回 'tags' 列表（暂为空，可扩展）
    4. 明确区分 email（登录邮箱）和 contact_email（联系人邮箱）
    5. ✅ 修复 categories 序列化 - 优先用 category 字段，否则由 major/minor 拼接
    6. ✅ 新增：所有 None 统一兜底为空串，避免前端拿到 null
    """
    if not s:
        return None
    
    try:
        # ✅ 处理 categories 列表 - 简化格式
        categories_list = []
        if s.categories:
            for c in s.categories:
                # ✅ 修复：优先用 category 字段，否则由 major/minor 拼接
                category_name = _safe_str(c.category)  # 优先用 category
                
                if not category_name and c.major_category:
                    # 如果 category 为空，则由 major/minor 拼接
                    minor = _safe_str(c.minor_category)
                    if minor:
                        category_name = f"{c.major_category}/{minor}"
                    else:
                        category_name = c.major_category
                
                # 仍然无法得到类别名称，则使用 ID 作为后备
                if not category_name:
                    category_name = f"Category {c.id}"
                
                category_dict = {
                    "id": c.id,
                    "name": category_name
                }
                categories_list.append(category_dict)
        
        return {
            "id": s.id,
            # ✅ 新增：name 字段（前端表格用 s.name）
            "name": _safe_str(s.company_name),
            # ✅ 保留：company_name（前端详情页用）
            "company_name": _safe_str(s.company_name),
            "code": _safe_str(s.code),
            "tax_id": _safe_str(s.tax_id),
            "contact_name": _safe_str(s.contact_name),
            "contact_phone": _safe_str(s.contact_phone),
            "contact_email": _safe_str(s.contact_email),
            "email": _safe_str(s.email),  # 企业登录邮箱
            "business_scope": _safe_str(s.business_scope),
            "province": _safe_str(s.province),
            "city": _safe_str(s.city),
            "district": _safe_str(s.district),
            "address": _safe_str(s.address),
            # ✅ 新增：categories 列表 - 简化格式 [{id, name}]
            "categories": categories_list,
            # ✅ 新增：tags（暂为空数组）
            "tags": [],
            "status": _safe_str(s.status),
            "reason": _safe_str(s.reason),
            "business_license_url": _safe_str(s.business_license_url) if s.business_license_url else '',
            "created_at": s.created_at.isoformat() if s.created_at else '',
            "updated_at": s.updated_at.isoformat() if s.updated_at else '',
            "last_login_at": s.last_login_at.isoformat() if s.last_login_at else '',
        }
    except AttributeError as e:
        logger.error(f"❌ supplier_to_dict 序列化失败: {str(e)}")
        return None