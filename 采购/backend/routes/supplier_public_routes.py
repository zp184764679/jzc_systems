# routes/supplier_public_routes.py
# ✅ 供应商公开系统 - Base64文件上传、批量处理（对外API）
# -*- coding: utf-8 -*-
import os
from flask import Blueprint, request, jsonify
from extensions import db
from models.supplier import Supplier
from models.invoice import Invoice
import logging

# 导入工具函数
from utils.response import error_response, success_response, options_response
from utils.decorators import handle_db_operation
from utils.validators import validate_json_data
from utils.serializers import invoice_to_dict
from utils.file_handler import process_base64_file

logger = logging.getLogger(__name__)

URL_PREFIX = "/api/v1/suppliers/public"
bp_public = Blueprint(
    "supplier_public",
    __name__,
    url_prefix="/api/v1/suppliers/public"
)


# ==============================
# OPTIONS 预检处理
# ==============================
@bp_public.route("/upload-invoice", methods=["OPTIONS"])
@bp_public.route("/batch-upload-invoices", methods=["OPTIONS"])
@bp_public.route("/file-status/<int:invoice_id>", methods=["OPTIONS"])
@bp_public.route("/upload-file", methods=["OPTIONS"])

@bp_public.route('/ocr-status', methods=['GET', 'OPTIONS'])
def get_ocr_status():
    """获取OCR服务状态"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    try:
        from services.invoice_ocr_service import get_ocr_service
        ocr_service = get_ocr_service()

        return jsonify({
            "ocr_type": ocr_service.ocr_type,
            "ollama_available": ocr_service.ollama_available,
            "ocr_engine_loaded": ocr_service.ocr_engine is not None,
            "use_cloud_api": ocr_service.use_cloud_api,
            "vision_model": getattr(ocr_service, 'ollama_vision_model', 'N/A'),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@bp_public.route('/test-vision', methods=['GET', 'OPTIONS'])
def test_vision_ocr():
    """测试 Ollama Vision OCR"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    try:
        from services.invoice_ocr_service import get_ocr_service
        import os, requests, base64

        ocr_service = get_ocr_service()

        # Use an existing PDF file
        test_pdf = "/home/admin/caigou-prod/backend/uploads/2025/11/f97e4ef122144fbfa25a96cc93dc0344.pdf"
        if not os.path.exists(test_pdf):
            return jsonify({"error": f"Test file not found: {test_pdf}"}), 404

        # Convert PDF to image
        temp_image = ocr_service._convert_pdf_to_image(test_pdf)
        if not temp_image:
            return jsonify({"error": "PDF conversion failed"}), 500

        image_size = os.path.getsize(temp_image)

        # Read image and encode
        with open(temp_image, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # Direct API call to Ollama
        api_url = f"{ocr_service.ollama_base}/api/generate"
        model = ocr_service.ollama_vision_model

        try:
            resp = requests.post(api_url, json={
                "model": model,
                "prompt": "识别这张发票的发票号码，返回JSON格式: {invoice_number: xxx}",
                "images": [image_data],
                "stream": False
            }, timeout=60)

            api_status = resp.status_code
            api_response = resp.text[:500] if resp.text else "Empty"
        except Exception as api_err:
            api_status = "ERROR"
            api_response = str(api_err)

        # Cleanup
        if os.path.exists(temp_image):
            os.remove(temp_image)

        return jsonify({
            "ocr_type": ocr_service.ocr_type,
            "ollama_available": ocr_service.ollama_available,
            "ollama_base": ocr_service.ollama_base,
            "model": model,
            "image_size": image_size,
            "image_data_size": len(image_data),
            "api_url": api_url,
            "api_status": api_status,
            "api_response": api_response
        }), 200

    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@bp_public.route("/ocr-invoice", methods=["OPTIONS"])
def options_handler():
    """OPTIONS 预检处理"""
    return options_response()


# ==============================
# 文件上传接口
# ==============================

@bp_public.route('/upload-file', methods=['POST'])
def upload_file_only():
    """
    POST /api/v1/suppliers/public/upload-file
    纯文件上传接口 - 只上传文件并返回URL，不涉及数据库

    请求体：
    {
        "file_data": "data:image/png;base64,iVBOR...",
        "file_name": "invoice.pdf"
    }

    返回：
    {
        "success": true,
        "file_url": "/uploads/xxx.pdf",
        "file_name": "invoice.pdf"
    }
    """
    from flask import request, jsonify

    try:
        data = request.get_json() or {}

        # 验证必填字段
        if not data.get('file_data'):
            return jsonify({'success': False, 'error': '缺少文件数据'}), 400
        if not data.get('file_name'):
            return jsonify({'success': False, 'error': '缺少文件名'}), 400

        # 处理Base64文件
        file_url, error = process_base64_file(data['file_data'], data['file_name'])

        if error:
            return jsonify({'success': False, 'error': error}), 400

        return jsonify({
            'success': True,
            'file_url': file_url,
            'file_name': data['file_name']
        }), 200

    except Exception as e:
        logger.error(f"❌ 文件上传失败: {str(e)}")
        return jsonify({'success': False, 'error': f'文件上传失败: {str(e)}'}), 500


@bp_public.route('/ocr-invoice', methods=['POST'])
def ocr_invoice():
    """
    POST /api/v1/suppliers/public/ocr-invoice
    OCR识别发票信息

    请求体：
    {
        "file_data": "data:image/png;base64,iVBOR...",
        "file_name": "invoice.pdf"
    }

    返回：
    {
        "success": true,
        "invoice_number": "12345678",
        "amount": 1000.00,
        "date": "2025-01-01",
        "confidence": 0.95,
        "raw_text": "识别的原始文本..."
    }
    """
    from flask import request, jsonify
    from services.invoice_ocr_service import get_ocr_service
    import tempfile

    file_path = None  # 用于追踪上传的文件路径

    try:
        data = request.get_json() or {}

        # 验证必填字段
        if not data.get('file_data'):
            return jsonify({'success': False, 'error': '缺少文件数据'}), 400
        if not data.get('file_name'):
            return jsonify({'success': False, 'error': '缺少文件名'}), 400

        # 先保存文件到临时位置
        file_url, error = process_base64_file(data['file_data'], data['file_name'])

        if error:
            return jsonify({'success': False, 'error': error}), 400

        # 构建完整文件路径
        file_path = os.path.join(os.getcwd(), file_url.lstrip('/'))

        # 执行OCR识别
        ocr_service = get_ocr_service()
        print(f"[OCR DEBUG] ocr_type={ocr_service.ocr_type}, ollama_available={ocr_service.ollama_available}, engine={ocr_service.ocr_engine is not None}")
        print(f"[OCR DEBUG] File path: {file_path}")
        result = ocr_service.extract_invoice_info(file_path)
        print(f"[OCR DEBUG] Result success={result.get('success')}, method={result.get('ocr_method', 'unknown')}")

        # 添加文件URL到结果
        result['file_url'] = file_url

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"❌ OCR识别失败: {str(e)}")

        # 清理失败的文件（OCR失败说明文件无效，需要清理）
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"✅ 已清理OCR失败的文件: {file_path}")
            except Exception as cleanup_error:
                logger.error(f"❌ 清理文件失败: {str(cleanup_error)}")

        return jsonify({
            'success': False,
            'error': f'OCR识别失败: {str(e)}',
            'invoice_number': '',
            'amount': 0.0,
            'date': '',
            'confidence': 0.0
        }), 500


@bp_public.route('/upload-invoice', methods=['POST'])
@handle_db_operation("Base64发票上传")
def upload_invoice_base64():
    """
    POST /api/v1/suppliers/public/upload-invoice
    Base64 → 文件 → URL → 数据库

    请求体：
    {
        "supplier_id": 1,
        "invoice_number": "INV-202501-001",
        "amount": 1000.00,
        "currency": "CNY",
        "file_base64": "base64_encoded_string",
        "file_name": "invoice.pdf",
        "description": "发票描述"
    }
    """
    data, err = validate_json_data(required_fields=[
        'supplier_id', 'invoice_number', 'amount', 'file_base64', 'file_name'
    ])
    if err:
        return err

    file_url = None  # 用于追踪上传的文件URL

    try:
        # 验证供应商
        supplier_id = data.get('supplier_id')
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return error_response("供应商不存在", 404)

        # 检查发票号是否已存在
        existing = Invoice.query.filter_by(
            supplier_id=supplier_id,
            invoice_number=data.get('invoice_number')
        ).first()
        if existing:
            return error_response("该发票号已存在", 400)

        # 处理Base64文件
        file_name = data.get('file_name', 'invoice.pdf')
        file_base64 = data.get('file_base64')

        file_url, process_err = process_base64_file(file_base64, file_name)
        if process_err:
            return error_response(process_err, 400)

        # 创建发票记录
        invoice = Invoice(
            supplier_id=supplier_id,
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

        logger.info(f"✅ 发票 {data.get('invoice_number')} 已上传，URL: {file_url}")

        return success_response(invoice_to_dict(invoice), status_code=201, message="发票上传成功")

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 发票上传失败: {str(e)}")

        # 清理失败的文件
        if file_url:
            file_path = os.path.join(os.getcwd(), file_url.lstrip('/'))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"✅ 已清理失败的上传文件: {file_path}")
                except Exception as cleanup_error:
                    logger.error(f"❌ 清理文件失败: {str(cleanup_error)}")

        return error_response("发票上传失败", 500)


# ==============================
# 批量上传接口
# ==============================

@bp_public.route('/batch-upload-invoices', methods=['POST'])
@handle_db_operation("批量Base64发票上传")
def batch_upload_invoices():
    """
    POST /api/v1/suppliers/public/batch-upload-invoices
    批量上传发票
    
    请求体：
    {
        "supplier_id": 1,
        "invoices": [
            {
                "invoice_number": "INV-001",
                "amount": 1000.00,
                "currency": "CNY",
                "file_base64": "base64_string",
                "file_name": "inv1.pdf"
            },
            ...
        ]
    }
    """
    data, err = validate_json_data(required_fields=['supplier_id', 'invoices'])
    if err:
        return err
    
    try:
        supplier_id = data.get('supplier_id')
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return error_response("供应商不存在", 404)
        
        invoices_data = data.get('invoices', [])
        if not isinstance(invoices_data, list):
            return error_response("invoices 必须是数组", 400)
        
        results = []
        success_count = 0
        failed_count = 0
        
        for invoice_data in invoices_data:
            file_url = None  # 追踪文件URL以便清理
            try:
                invoice_number = invoice_data.get('invoice_number')
                if not invoice_number:
                    results.append({
                        "invoice_number": "未知",
                        "status": "failed",
                        "error": "缺少发票号"
                    })
                    failed_count += 1
                    continue

                # 检查重复
                existing = Invoice.query.filter_by(
                    supplier_id=supplier_id,
                    invoice_number=invoice_number
                ).first()
                if existing:
                    results.append({
                        "invoice_number": invoice_number,
                        "status": "failed",
                        "error": "发票号已存在"
                    })
                    failed_count += 1
                    continue

                # 处理Base64文件
                file_name = invoice_data.get('file_name', f'{invoice_number}.pdf')
                file_base64 = invoice_data.get('file_base64')

                file_url, process_err = process_base64_file(file_base64, file_name)
                if process_err:
                    results.append({
                        "invoice_number": invoice_number,
                        "status": "failed",
                        "error": process_err
                    })
                    failed_count += 1
                    continue

                # 创建发票记录
                invoice = Invoice(
                    supplier_id=supplier_id,
                    invoice_number=invoice_number,
                    quote_id=invoice_data.get('quote_id'),
                    amount=float(invoice_data.get('amount', 0)),
                    currency=invoice_data.get('currency', 'CNY'),
                    file_url=file_url,
                    file_name=file_name,
                    description=invoice_data.get('description', ''),
                    status='pending'
                )

                db.session.add(invoice)
                db.session.flush()

                results.append({
                    "invoice_number": invoice_number,
                    "status": "success",
                    "file_url": file_url,
                    "id": invoice.id
                })
                success_count += 1

            except Exception as e:
                logger.error(f"❌ 批量上传单个失败: {str(e)}")

                # 清理失败的文件
                if file_url:
                    file_path = os.path.join(os.getcwd(), file_url.lstrip('/'))
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logger.info(f"✅ 已清理失败的批量上传文件: {file_path}")
                        except Exception as cleanup_error:
                            logger.error(f"❌ 清理文件失败: {str(cleanup_error)}")

                results.append({
                    "invoice_number": invoice_data.get('invoice_number', '未知'),
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        db.session.commit()
        
        logger.info(f"✅ 批量上传完成: 成功 {success_count}, 失败 {failed_count}")
        
        return success_response({
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(invoices_data),
            "results": results
        }, message="批量上传完成")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 批量上传失败: {str(e)}")
        return error_response("批量上传失败", 500)


# ==============================
# 文件查询接口
# ==============================

@bp_public.route('/file-status/<int:invoice_id>', methods=['GET'])
@handle_db_operation("查询文件状态")
def get_file_status(invoice_id):
    """
    GET /api/v1/suppliers/public/file-status/<invoice_id>
    查询发票文件状态和URL
    """
    try:
        invoice = Invoice.query.get(invoice_id)
        if not invoice:
            return error_response("发票不存在", 404)
        
        return success_response(invoice_to_dict(invoice))
    
    except Exception as e:
        logger.error(f"❌ 查询文件状态失败: {str(e)}")
        return error_response("查询失败", 500)


# ==============================
# 导出蓝图
# ==============================
BLUEPRINTS = [bp_public]