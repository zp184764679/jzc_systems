# suppliers/utils/serializers.py
# 序列化函数：将ORM对象转为字典
# -*- coding: utf-8 -*-
from models.supplier import Supplier
from models.supplier_quote import SupplierQuote
import json
import logging

logger = logging.getLogger(__name__)


def supplier_to_dict(s: Supplier):
    """序列化供应商对象"""
    if not s:
        return None
    
    try:
        return {
            "id": s.id,
            "code": s.code,
            "company_name": s.company_name,
            "email": s.email,
            "tax_id": s.tax_id,
            "contact_name": s.contact_name,
            "contact_phone": s.contact_phone,
            "contact_email": s.contact_email,
            "business_scope": s.business_scope,
            "province": s.province or '',
            "city": s.city or '',
            "district": s.district or '',
            "address": s.address or '',
            "status": s.status,
            "business_license_url": s.business_license_url if s.business_license_url else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "last_login_at": s.last_login_at.isoformat() if s.last_login_at else None,
        }
    except AttributeError as e:
        logger.error(f"❌ supplier_to_dict 序列化失败: {str(e)}")
        return None


def supplier_quote_to_dict(sq: SupplierQuote):
    """序列化供应商报价对象"""
    if not sq:
        return None
    
    # 解析 JSON 报价内容
    quote_data = {}
    if sq.quote_json:
        try:
            quote_data = json.loads(sq.quote_json) if isinstance(sq.quote_json, str) else sq.quote_json
        except (json.JSONDecodeError, TypeError):
            quote_data = {}
    
    return {
        "id": sq.id,
        "rfq_id": sq.rfq_id,
        "supplier_id": sq.supplier_id,
        "status": sq.status,
        "quote_data": quote_data,
        "created_at": sq.created_at.isoformat() if sq.created_at else None,
        "responded_at": sq.responded_at.isoformat() if sq.responded_at else None,
        "expired_at": sq.expired_at.isoformat() if sq.expired_at else None,
    }


def invoice_to_dict(inv):
    """序列化发票对象"""
    if not inv:
        return None
    
    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "amount": str(inv.amount),
        "currency": inv.currency,
        "status": inv.status,
        "approval_notes": inv.approval_notes,
        "file_url": inv.file_url,
        "file_name": inv.file_name,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "approved_at": inv.approved_at.isoformat() if inv.approved_at else None,
    }