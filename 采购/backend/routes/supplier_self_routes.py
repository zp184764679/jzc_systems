# routes/supplier_self_routes.py
# ✅ 供应商自助系统 - 供应商使用（登录、查看报价、上传发票等）
# ✅ 精简版：调用 utils + helpers
# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
from extensions import db
from models.supplier import Supplier, SUPPLIER_STATUS
from models.supplier_category import SupplierCategory
from models.supplier_quote import SupplierQuote
from models.invoice import Invoice
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from sqlalchemy import or_, desc
from sqlalchemy.orm import joinedload

# 导入工具函数
from utils.response import error_response, success_response, options_response
from utils.decorators import handle_db_operation
from utils.validators import validate_json_data, validate_field, get_supplier_or_error
from utils.serializers import supplier_to_dict, supplier_quote_to_dict, invoice_to_dict
from utils.file_handler import process_base64_file

logger = logging.getLogger(__name__)

URL_PREFIX = "/api/v1/suppliers"
bp_self = Blueprint(
    "supplier_self",
    __name__,
    url_prefix="/api/v1/suppliers"
)


# ==============================
# OPTIONS 预检处理
# ==============================
@bp_self.route("/register", methods=["OPTIONS"])
@bp_self.route("/login", methods=["OPTIONS"])
@bp_self.route("/me", methods=["OPTIONS"])
@bp_self.route("/me/statistics", methods=["OPTIONS"])
@bp_self.route("/me/quotes", methods=["OPTIONS"])
@bp_self.route("/me/invoices", methods=["OPTIONS"])
def _to_int(v, default=None):
    try:
        if v is None:
            return default
        return int(str(v).strip())
    except Exception:
        return default
    
def options_handler():
    """OPTIONS 预检处理"""
    return options_response()


# ==============================
# 供应商认证接口
# ==============================

@bp_self.route('/register', methods=['POST'])
@handle_db_operation("供应商注册")
def register_supplier():
    """
    POST /api/v1/suppliers/register
    供应商注册
    """
    data, err = validate_json_data(required_fields=['company_name', 'email', 'password', 'contact_name'])
    if err:
        return err
    
    try:
        company_name, _ = validate_field(data, 'company_name')
        email, _ = validate_field(data, 'email')
        password, _ = validate_field(data, 'password')
        contact_name, _ = validate_field(data, 'contact_name')
        
        # 检查邮箱是否已存在
        if Supplier.query.filter_by(email=email).first():
            return error_response("该邮箱已被注册", 400)
        
        # 创建供应商
        supplier = Supplier(
            company_name=company_name,
            email=email,
            password_hash=generate_password_hash(password),
            contact_name=contact_name,
            contact_phone=data.get('contact_phone', ''),
            contact_email=data.get('contact_email', ''),
            business_scope=data.get('business_scope', ''),
            tax_id=data.get('tax_id', ''),
            province=data.get('province', ''),
            city=data.get('city', ''),
            district=data.get('district', ''),
            address=data.get('address', ''),
            status=SUPPLIER_STATUS['PENDING']
        )
        
        db.session.add(supplier)
        db.session.flush()
        
        # 从经营范围提取出大类（如 “刀具”）
        scope = data.get('business_scope', 'General')
        major = scope.split('/')[0] if '/' in scope else scope

        category = SupplierCategory(
            supplier_id=supplier.id,
            category=scope,           # 完整路径，如 “刀具/铣削刀具”
            major_category=major,     # 主类，用于匹配
            minor_category=''         # 可选，可保留空
        )

        
        db.session.add(category)
        db.session.commit()
        
        logger.info(f"✅ 供应商 {company_name} 注册成功")
        
        return success_response(supplier_to_dict(supplier), status_code=201, message="注册成功")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 注册失败: {str(e)}")
        return error_response("注册失败", 500)


@bp_self.route('/login', methods=['POST'])
@handle_db_operation("供应商登录")
def login_supplier():
    """
    POST /api/v1/suppliers/login
    供应商登录
    """
    data, err = validate_json_data(required_fields=['email', 'password'])
    if err:
        return err
    
    try:
        email = data.get('email')
        password = data.get('password')
        
        supplier = Supplier.query.filter_by(email=email).first()
        if not supplier or not check_password_hash(supplier.password_hash, password):
            return error_response("邮箱或密码错误", 401)
        
        # 更新最后登录时间
        supplier.last_login_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ 供应商 {email} 登录成功")
        
        return success_response({
            "supplier": supplier_to_dict(supplier),
            "token": f"supplier_{supplier.id}"
        }, message="登录成功")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 登录失败: {str(e)}")
        return error_response("登录失败", 500)


# ==============================
# 供应商信息接口
# ==============================

@bp_self.route('/me', methods=['GET'])
@handle_db_operation("获取我的信息")
def get_my_info():
    """
    GET /api/v1/suppliers/me
    获取当前供应商的完整信息
    """
    supplier, err = get_supplier_or_error()
    if err:
        return err
    
    return success_response(supplier_to_dict(supplier))


@bp_self.route('/me', methods=['PUT'])
@handle_db_operation("更新我的信息")
def update_my_info():
    """
    PUT /api/v1/suppliers/me
    更新供应商信息
    """
    supplier, err = get_supplier_or_error()
    if err:
        return err
    
    data, err = validate_json_data()
    if err:
        return err
    
    try:
        # 允许更新的字段
        updateable_fields = [
            'company_name', 'contact_name', 'contact_phone', 'contact_email',
            'business_scope', 'tax_id', 'province', 'city', 'district', 'address'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(supplier, field, data[field])
        
        supplier.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"✅ 供应商信息已更新")
        
        return success_response(supplier_to_dict(supplier), message="更新成功")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 更新信息失败: {str(e)}")
        return error_response("更新信息失败", 500)


# ==============================
# 统计接口
# ==============================

@bp_self.route('/me/statistics', methods=['GET'])
@handle_db_operation("获取我的统计信息")
def get_my_statistics():
    """
    GET /api/v1/suppliers/me/statistics
    获取我的统计数据
    """
    supplier, err = get_supplier_or_error()
    if err:
        return err
    
    try:
        total_quotes = SupplierQuote.query.filter_by(supplier_id=supplier.id).count()
        participated_quotes = SupplierQuote.query.filter_by(
            supplier_id=supplier.id,
            status='participated'
        ).count()
        won_quotes = SupplierQuote.query.filter_by(
            supplier_id=supplier.id,
            status='won'
        ).count()
        
        success_rate = round((won_quotes / total_quotes * 100), 2) if total_quotes > 0 else 0
        
        pending_invoices = Invoice.query.filter_by(
            supplier_id=supplier.id,
            status='pending'
        ).count()
        
        return success_response({
            "total_quotes": total_quotes,
            "participated_quotes": participated_quotes,
            "won_quotes": won_quotes,
            "success_rate": success_rate,
            "pending_invoices": pending_invoices
        })
    
    except Exception as e:
        logger.error(f"❌ 获取统计信息错误: {str(e)}")
        return error_response("获取统计信息失败", 500)


# ==============================
# 报价管理接口
# ==============================

# 供应商：我的报价列表
@bp_self.route("/me/quotes", methods=["GET", "OPTIONS"])
def list_my_quotes():
    """
    供应商报价库列表（供应商端）
    读取请求头 Supplier-ID 来识别当前供应商。
    支持分页/状态筛选/关键字搜索。
    返回字段来自 SupplierQuote.to_dict()，包含 display_no（YYMMDD-SSSS-QQQ）
    """
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # 1) 读取 Supplier-ID（前端 useSupplierQuotes 已注入）
    supplier_id = request.headers.get("Supplier-ID") or request.headers.get("Supplier-Id") or request.headers.get("supplier-id")
    supplier_id = _to_int(supplier_id)
    if not supplier_id:
        return jsonify({"error": "缺少 Supplier-ID 请求头"}), 400

    # 2) 基本参数
    page = _to_int(request.args.get("page"), 1) or 1
    per_page = min(max(_to_int(request.args.get("per_page"), 10) or 10, 1), 100)
    status = (request.args.get("status") or "").strip()     # pending/received/expired/...
    keyword = (request.args.get("keyword") or "").strip()

    # 3) 构建查询 - 预加载 supplier 关联，确保 display_no 能正确生成
    q = SupplierQuote.query.options(joinedload(SupplierQuote.supplier)).filter(SupplierQuote.supplier_id == supplier_id)

    if status:
        q = q.filter(SupplierQuote.status == status)

    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            or_(
                SupplierQuote.item_name.ilike(like),
                SupplierQuote.item_description.ilike(like),
                SupplierQuote.supplier_name.ilike(like),
            )
        )

    q = q.order_by(desc(SupplierQuote.created_at), desc(SupplierQuote.id))

    # 4) 分页
    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()
    pages = (total + per_page - 1) // per_page

    # 5) 序列化
    result = []
    for row in items:
        try:
            d = row.to_dict()  # ✅ 不再访问不存在的 quote_number
            # 兼容：确保有 display_no（如果模型已实现就有；否则这里兜底）
            if "display_no" not in d or not d["display_no"]:
                # 兜底为旧格式 Q{rfq_id}-{id}；你也可以按需改为 YYMMDD-SSSS-QQQ
                d["display_no"] = f"Q{row.rfq_id}-{row.id}"
            result.append(d)
        except Exception as e:
            logger.error("序列化报价行失败 id=%s: %s", getattr(row, "id", None), e, exc_info=True)

    return jsonify({
        "quotes": result,
        "page": page,
        "pages": pages,
        "total": total,
    }), 200


# ==============================
# 发票管理接口
# ==============================

@bp_self.route('/me/invoices', methods=['GET'])
@handle_db_operation("获取我的发票")
def get_my_invoices():
    """
    GET /api/v1/suppliers/me/invoices
    获取我的所有发票
    """
    supplier, err = get_supplier_or_error()
    if err:
        return err
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', None)
        
        query = Invoice.query.filter_by(supplier_id=supplier.id)
        
        if status:
            query = query.filter_by(status=status)
        
        query = query.order_by(desc(Invoice.created_at))
        paginated = query.paginate(page=page, per_page=per_page)
        
        return success_response({
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": page,
            "per_page": per_page,
            "invoices": [invoice_to_dict(inv) for inv in paginated.items]
        })
    
    except Exception as e:
        logger.error(f"❌ 获取发票列表错误: {str(e)}")
        return error_response("获取发票列表失败", 500)


@bp_self.route('/me/invoices', methods=['POST'])
@handle_db_operation("上传发票")
def upload_invoice():
    """
    POST /api/v1/suppliers/me/invoices
    上传新发票（支持Base64）
    
    请求体：
    {
        "invoice_number": "INV-202501-001",
        "quote_id": 1,
        "amount": 1000.00,
        "currency": "CNY",
        "file_base64": "base64_string",  # 可选
        "file_url": "https://...",       # 或提供现成URL
        "file_name": "invoice.pdf",
        "description": "发票描述"
    }
    """
    supplier, err = get_supplier_or_error()
    if err:
        return err
    
    data, err = validate_json_data(required_fields=['invoice_number', 'amount'])
    if err:
        return err
    
    try:
        # 检查发票号是否已存在
        existing = Invoice.query.filter_by(
            supplier_id=supplier.id,
            invoice_number=data.get('invoice_number')
        ).first()
        
        if existing:
            return error_response("该发票号已存在", 400)
        
        # 处理文件URL
        file_url = data.get('file_url', '')
        file_name = data.get('file_name', '')
        
        # 如果提供了Base64，优先处理Base64
        if data.get('file_base64') and file_name:
            file_url, process_err = process_base64_file(
                data.get('file_base64'),
                file_name
            )
            if process_err:
                return error_response(process_err, 400)
        
        # 创建发票
        invoice = Invoice(
            supplier_id=supplier.id,
            invoice_number=data.get('invoice_number'),
            quote_id=data.get('quote_id'),
            amount=float(data.get('amount')),
            currency=data.get('currency', 'CNY'),
            file_url=file_url,
            file_name=file_name,
            description=data.get('description', ''),
            status='pending'
        )
        
        db.session.add(invoice)
        db.session.commit()
        
        logger.info(f"✅ 发票 {data.get('invoice_number')} 已上传")
        
        return success_response(invoice_to_dict(invoice), status_code=201, message="发票上传成功")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 上传发票错误: {str(e)}")
        return error_response("上传发票失败", 500)


# ==============================
# 导出蓝图
# ==============================
BLUEPRINTS = [bp_self]