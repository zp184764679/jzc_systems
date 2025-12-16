# api/quotes.py
"""
报价管理API
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from config.database import get_db
from models.quote import Quote, QuoteItem
from models.quote_approval import QuoteApproval, QuoteStatus, ApprovalAction, can_transition
from models.drawing import Drawing
from models.material import Material
from models.process import Process
from api.schemas import (
    QuoteResponse, QuoteList, QuoteCreate, MessageResponse,
    ApprovalRequest, RejectRequest, SendRequest,
    QuoteApprovalResponse, QuoteApprovalList, StatusInfo,
    CreateVersionRequest, QuoteVersionSummary, QuoteVersionList,
    VersionComparisonItem, QuoteCompareResponse
)
from services.quote_calculator import get_calculator
from services.quote_document_generator import get_document_generator
import logging
import uuid
import re

logger = logging.getLogger(__name__)

router = APIRouter()


def clean_numeric_value(value: any, default: str = "0") -> str:
    """
    清理数字字符串，移除无效字符并修复格式错误

    处理以下情况：
    - None/空值 -> 返回默认值
    - 已经是数字 -> 转换为字符串
    - 格式错误的数字（如 '101.80.10'） -> 只保留第一个小数点
    - 包含特殊字符（如 'Φ12.5'） -> 提取数字部分

    Args:
        value: 输入值
        default: 默认值（当输入无效时）

    Returns:
        清理后的数字字符串
    """
    if value is None or value == "":
        return default

    # 如果已经是数字类型，直接转换为字符串
    if isinstance(value, (int, float)):
        return str(value)

    # 如果是字符串，进行清理
    if isinstance(value, str):
        # 移除常见的非数字字符（保留数字、小数点、负号）
        cleaned = re.sub(r'[^\d.\-]', '', value)

        # 处理多个小数点的情况：只保留第一个小数点及其后的第一部分
        parts = cleaned.split('.')
        if len(parts) > 2:
            # 只保留整数部分和第一个小数部分，忽略后续错误的小数点
            cleaned = parts[0] + '.' + parts[1]

        # 验证是否是有效数字
        try:
            float(cleaned)
            return cleaned if cleaned else default
        except ValueError:
            logger.warning(f"无法转换为数字: {value} (清理后: {cleaned})，使用默认值: {default}")
            return default

    return default


@router.post("/calculate", response_model=dict)
async def calculate_quote(
    drawing_id: int,
    lot_size: int = 2000,
    process_codes: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    计算报价

    基于图纸信息、材料库和工艺库自动计算报价

    Args:
        drawing_id: 图纸ID
        lot_size: 批量大小
        process_codes: 工艺代码列表（可选，默认自动推荐）

    Returns:
        完整的报价计算结果
    """
    logger.info(f"开始计算报价: drawing_id={drawing_id}, lot_size={lot_size}")

    # 1. 查询图纸
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 2. 查询材料信息
    material = None
    if drawing.material:
        material = db.query(Material).filter(
            Material.material_code == drawing.material
        ).first()

        if not material:
            # 尝试模糊匹配
            material = db.query(Material).filter(
                Material.material_name.contains(drawing.material)
            ).first()

    if not material:
        raise HTTPException(
            status_code=400,
            detail=f"未找到材料信息: {drawing.material}. 请先在材料库中添加该材料"
        )

    # 3. 查询工艺信息
    if not process_codes:
        # 自动推荐工艺
        if "不锈钢" in material.category or "SUS" in drawing.material:
            process_codes = ["CNC_TURNING", "GRINDING", "DEBURRING", "INSPECTION"]
        elif "铝" in material.category:
            process_codes = ["CNC_TURNING", "CNC_MILLING", "DEBURRING", "INSPECTION"]
        else:
            process_codes = ["CNC_TURNING", "DEBURRING", "INSPECTION"]

    processes = db.query(Process).filter(
        Process.process_code.in_(process_codes),
        Process.is_active == True
    ).all()

    if not processes:
        raise HTTPException(status_code=400, detail="未找到有效的工艺信息")

    # 4. 准备计算数据（清理数值字段）
    drawing_info = {
        "drawing_number": drawing.drawing_number,
        "customer_name": drawing.customer_name,
        "product_name": drawing.product_name,
        "material": drawing.material,
        "outer_diameter": clean_numeric_value(drawing.outer_diameter, "6"),
        "length": clean_numeric_value(drawing.length, "100"),
    }

    material_info = {
        "material_code": material.material_code,
        "material_name": material.material_name,
        "density": float(material.density) if material.density else 7.93,
        "price_per_kg": float(material.price_per_kg) if material.price_per_kg else 35.0,
    }

    process_list = [
        {
            "process_code": p.process_code,
            "process_name": p.process_name,
            "category": p.category,
            "daily_output": p.daily_output or 1000,
            "setup_time": float(p.setup_time) if p.setup_time else 0.125,
            "hourly_rate": float(p.hourly_rate) if p.hourly_rate else 55,
            "defect_rate": float(p.defect_rate) if p.defect_rate else 0.01,
        }
        for p in processes
    ]

    # 5. 执行计算
    calculator = get_calculator()

    try:
        result = calculator.calculate_full_quote(
            drawing_info=drawing_info,
            material_info=material_info,
            processes=process_list,
            lot_size=lot_size
        )

        if result.get('success'):
            logger.info(f"报价计算成功: 总价={result['quote']['total_price']:.2f}元")
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', '计算失败'))

    except ValueError as e:
        logger.error(f"报价计算失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"报价计算异常: {e}")
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/save", response_model=QuoteResponse, status_code=201)
async def save_quote(
    drawing_id: int,
    calculation_result: dict,
    db: Session = Depends(get_db)
):
    """
    保存报价单

    将计算结果保存为正式报价单

    Args:
        drawing_id: 图纸ID
        calculation_result: 计算结果（来自calculate接口）
    """
    logger.info(f"保存报价: drawing_id={drawing_id}")

    # 查询图纸
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 生成报价单号
    quote_number = f"QT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    # 提取计算结果
    quote_data = calculation_result.get('quote', {})
    drawing_info = calculation_result.get('drawing_info', {})
    material_info = calculation_result.get('material', {})
    rates = quote_data.get('rates', {})

    # 创建报价单
    quote = Quote(
        quote_number=quote_number,
        drawing_id=drawing_id,
        customer_name=drawing.customer_name or "未知客户",
        product_name=drawing.product_name,
        lot_size=calculation_result.get('lot_size', 2000),
        # 材料信息
        material_name=drawing_info.get('material', ''),
        # 成本信息
        material_cost=quote_data.get('material_cost', 0),
        process_cost=quote_data.get('process_cost', 0),
        other_cost=quote_data.get('other_cost', 0),
        management_cost=quote_data.get('management_cost', 0),
        subtotal_cost=quote_data.get('subtotal', 0),
        profit_rate=rates.get('profit_rate', 0.15),
        profit_amount=quote_data.get('profit', 0),
        total_amount=quote_data.get('total_price', 0),
        # 其他信息
        currency="CNY",
        quantity=calculation_result.get('lot_size', 1),
        details=calculation_result,
        status="draft",
        valid_until=datetime.now().date() + timedelta(days=30)
    )

    db.add(quote)
    db.commit()
    db.refresh(quote)

    logger.info(f"报价单已保存: {quote_number}, 总额={quote.total_amount:.2f}元")

    return quote


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: int, db: Session = Depends(get_db)):
    """
    获取报价详情
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    return quote


@router.get("", response_model=QuoteList)
def list_quotes(
    skip: int = 0,
    limit: int = 20,
    customer: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取报价单列表

    - 支持分页
    - 支持按客户和状态筛选
    """
    query = db.query(Quote)

    # 筛选条件
    if customer:
        query = query.filter(Quote.customer_name.contains(customer))
    if status:
        query = query.filter(Quote.status == status)

    # 获取总数
    total = query.count()

    # 分页查询
    items = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()

    return QuoteList(total=total, items=items)


@router.put("/{quote_id}/status", response_model=QuoteResponse)
def update_quote_status(
    quote_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """
    更新报价单状态

    状态: draft(草稿), sent(已发送), approved(已批准), rejected(已拒绝)
    """
    valid_statuses = ["draft", "sent", "approved", "rejected"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"无效的状态。有效状态: {', '.join(valid_statuses)}"
        )

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    quote.status = status
    db.commit()
    db.refresh(quote)

    logger.info(f"报价单状态已更新: {quote.quote_number} -> {status}")

    return quote


@router.delete("/{quote_id}", response_model=MessageResponse)
def delete_quote(quote_id: int, db: Session = Depends(get_db)):
    """
    删除报价单
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    db.delete(quote)
    db.commit()

    logger.info(f"报价单已删除: {quote.quote_number}")

    return MessageResponse(message="报价单删除成功")


@router.get("/{quote_id}/export/excel")
async def export_quote_to_excel(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """
    导出报价单为Excel

    返回Excel文件下载
    """
    logger.info(f"导出Excel报价单: quote_id={quote_id}")

    # 查询报价单
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 准备数据
    quote_data = {
        "quote_number": quote.quote_number,
        "customer_name": quote.customer_name,
        "quote": {
            "material_cost": float(quote.material_cost),
            "process_cost": float(quote.process_cost),
            "other_cost": float(quote.other_cost),
            "management_cost": float(quote.management_cost),
            "profit": float(quote.profit_amount),
            "total_price": float(quote.total_amount),
            "rates": {
                "management_rate": float(quote.general_management_rate) if quote.general_management_rate else 0.045,
                "profit_rate": float(quote.profit_rate) if quote.profit_rate else 0.15
            }
        },
        "drawing_info": quote.details.get('drawing_info', {}) if quote.details else {},
        "material": quote.details.get('material', {}) if quote.details else {},
        "process": quote.details.get('process', {}) if quote.details else {},
        "lot_size": quote.quantity
    }

    try:
        # 生成Excel
        generator = get_document_generator()
        excel_file = generator.generate_excel(quote_data)

        # 返回文件
        from urllib.parse import quote as url_quote
        filename = f"报价单_{quote.quote_number}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        encoded_filename = url_quote(filename)

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )

    except Exception as e:
        logger.error(f"导出Excel失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/{quote_id}/export/pdf")
async def export_quote_to_pdf(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """
    导出报价单为PDF

    返回PDF文件下载
    """
    logger.info(f"导出PDF报价单: quote_id={quote_id}")

    # 查询报价单
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 准备数据
    quote_data = {
        "quote_number": quote.quote_number,
        "customer_name": quote.customer_name,
        "quote": {
            "material_cost": float(quote.material_cost),
            "process_cost": float(quote.process_cost),
            "other_cost": float(quote.other_cost),
            "management_cost": float(quote.management_cost),
            "profit": float(quote.profit_amount),
            "total_price": float(quote.total_amount),
            "rates": {
                "management_rate": float(quote.general_management_rate) if quote.general_management_rate else 0.045,
                "profit_rate": float(quote.profit_rate) if quote.profit_rate else 0.15
            }
        },
        "drawing_info": quote.details.get('drawing_info', {}) if quote.details else {},
        "material": quote.details.get('material', {}) if quote.details else {},
        "process": quote.details.get('process', {}) if quote.details else {},
        "lot_size": quote.quantity
    }

    try:
        # 生成PDF
        generator = get_document_generator()
        pdf_file = generator.generate_pdf(quote_data)

        # 返回文件
        from urllib.parse import quote as url_quote
        filename = f"报价单_{quote.quote_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
        encoded_filename = url_quote(filename)

        return StreamingResponse(
            pdf_file,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )

    except Exception as e:
        logger.error(f"导出PDF失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/export/chenlong-template")
async def export_chenlong_template(
    request_data: dict,
    db: Session = Depends(get_db)
):
    """
    使用晨龙精密报价单模板导出Excel

    支持导出多个产品的报价单

    Args:
        request_data: 导出请求数据
            - customer_info: 客户信息
                - customer_name: 客户名称
                - contact_person: 联系人
                - phone: 电话
                - fax: 传真
                - quote_number: 报价单号
            - drawing_ids: 图纸ID列表（可选）
            - items: 产品列表（可选，如果不提供drawing_ids）
                - 每个item包含: drawing_number, outer_diameter, length, material等

    Returns:
        Excel文件下载
    """
    logger.info(f"📤 导出晨龙精密报价单模板")

    try:
        customer_info = request_data.get('customer_info', {})
        drawing_ids = request_data.get('drawing_ids', [])
        items_data = request_data.get('items', [])

        # 准备产品列表
        items = []

        # 如果提供了drawing_ids，从数据库查询
        if drawing_ids:
            drawings = db.query(Drawing).filter(Drawing.id.in_(drawing_ids)).all()
            for drawing in drawings:
                item = {
                    'customer_part_number': drawing.customer_part_number or drawing.drawing_number,
                    'drawing_number': drawing.drawing_number,
                    'outer_diameter': drawing.outer_diameter,
                    'length': drawing.length,
                    'material': drawing.material,
                    'surface_treatment': drawing.surface_treatment,
                    'lot_size': customer_info.get('default_lot_size', 1000),
                    'notes': ''
                }

                # 如果有关联的报价，使用报价中的价格
                quote = db.query(Quote).filter(
                    Quote.drawing_id == drawing.id,
                    Quote.status.in_(['draft', 'sent', 'approved'])
                ).order_by(Quote.created_at.desc()).first()

                if quote:
                    unit_price = float(quote.total_amount) / quote.quantity if quote.quantity else float(quote.total_amount)
                    item['unit_price_before_tax'] = round(unit_price / 1.13, 4)
                    item['unit_price_with_tax'] = round(unit_price, 4)
                    item['lot_size'] = quote.quantity

                items.append(item)

        # 如果直接提供了items数据
        elif items_data:
            items = items_data

        else:
            raise HTTPException(status_code=400, detail="必须提供drawing_ids或items")

        if not items:
            raise HTTPException(status_code=400, detail="没有找到可导出的产品")

        # 生成Excel
        generator = get_document_generator()
        excel_file = generator.generate_chenlong_template(
            customer_info=customer_info,
            items=items
        )

        # 返回文件
        quote_number = customer_info.get('quote_number', datetime.now().strftime('%y%m%d'))
        filename = f"报价单_{quote_number}.xlsx"

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}".encode('utf-8').decode('latin1')
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 导出晨龙精密报价单失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


# ============ 审批相关 API ============

@router.get("/statuses", response_model=List[StatusInfo])
def get_quote_statuses():
    """
    获取报价单状态列表
    """
    statuses = [
        {"value": QuoteStatus.DRAFT, "label": "草稿", "color": "default"},
        {"value": QuoteStatus.PENDING_REVIEW, "label": "待审核", "color": "processing"},
        {"value": QuoteStatus.APPROVED, "label": "已批准", "color": "success"},
        {"value": QuoteStatus.REJECTED, "label": "已拒绝", "color": "error"},
        {"value": QuoteStatus.SENT, "label": "已发送", "color": "cyan"},
        {"value": QuoteStatus.EXPIRED, "label": "已过期", "color": "warning"},
    ]
    return statuses


@router.post("/{quote_id}/submit", response_model=QuoteResponse)
def submit_quote(
    quote_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    提交报价单审核

    状态流转: draft → pending_review
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 检查状态流转
    if not can_transition(quote.status, QuoteStatus.PENDING_REVIEW):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 [{QuoteStatus.get_display_name(quote.status)}] 不能提交审核"
        )

    # 更新状态
    old_status = quote.status
    quote.status = QuoteStatus.PENDING_REVIEW
    quote.submitted_at = datetime.now()
    quote.submitted_by = request.approver_id
    quote.submitted_by_name = request.approver_name

    # 记录审批历史
    approval = QuoteApproval(
        quote_id=quote_id,
        action=ApprovalAction.SUBMIT.value,
        from_status=old_status,
        to_status=QuoteStatus.PENDING_REVIEW,
        approver_id=request.approver_id,
        approver_name=request.approver_name,
        approver_role=request.approver_role,
        comment=request.comment
    )
    db.add(approval)

    db.commit()
    db.refresh(quote)

    logger.info(f"报价单已提交审核: {quote.quote_number}")

    return quote


@router.post("/{quote_id}/approve", response_model=QuoteResponse)
def approve_quote(
    quote_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    审批通过报价单

    状态流转: pending_review → approved
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 检查状态流转
    if not can_transition(quote.status, QuoteStatus.APPROVED):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 [{QuoteStatus.get_display_name(quote.status)}] 不能审批通过"
        )

    # 更新状态
    old_status = quote.status
    quote.status = QuoteStatus.APPROVED
    quote.approved_at = datetime.now()
    quote.approved_by = request.approver_id
    quote.approved_by_name = request.approver_name
    # 清除拒绝信息
    quote.rejected_at = None
    quote.rejected_by = None
    quote.rejected_by_name = None
    quote.reject_reason = None

    # 记录审批历史
    approval = QuoteApproval(
        quote_id=quote_id,
        action=ApprovalAction.APPROVE.value,
        from_status=old_status,
        to_status=QuoteStatus.APPROVED,
        approver_id=request.approver_id,
        approver_name=request.approver_name,
        approver_role=request.approver_role,
        comment=request.comment
    )
    db.add(approval)

    db.commit()
    db.refresh(quote)

    logger.info(f"报价单审批通过: {quote.quote_number}")

    return quote


@router.post("/{quote_id}/reject", response_model=QuoteResponse)
def reject_quote(
    quote_id: int,
    request: RejectRequest,
    db: Session = Depends(get_db)
):
    """
    拒绝报价单

    状态流转: pending_review → rejected
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 检查状态流转
    if not can_transition(quote.status, QuoteStatus.REJECTED):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 [{QuoteStatus.get_display_name(quote.status)}] 不能拒绝"
        )

    # 更新状态
    old_status = quote.status
    quote.status = QuoteStatus.REJECTED
    quote.rejected_at = datetime.now()
    quote.rejected_by = request.approver_id
    quote.rejected_by_name = request.approver_name
    quote.reject_reason = request.reason

    # 记录审批历史
    approval = QuoteApproval(
        quote_id=quote_id,
        action=ApprovalAction.REJECT.value,
        from_status=old_status,
        to_status=QuoteStatus.REJECTED,
        approver_id=request.approver_id,
        approver_name=request.approver_name,
        approver_role=request.approver_role,
        comment=request.reason
    )
    db.add(approval)

    db.commit()
    db.refresh(quote)

    logger.info(f"报价单已拒绝: {quote.quote_number}, 原因: {request.reason}")

    return quote


@router.post("/{quote_id}/revise", response_model=QuoteResponse)
def revise_quote(
    quote_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    退回修改报价单

    状态流转: pending_review/approved → draft
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 检查状态流转
    if not can_transition(quote.status, QuoteStatus.DRAFT):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 [{QuoteStatus.get_display_name(quote.status)}] 不能退回修改"
        )

    # 更新状态
    old_status = quote.status
    quote.status = QuoteStatus.DRAFT
    # 清除审批信息
    quote.submitted_at = None
    quote.submitted_by = None
    quote.submitted_by_name = None
    quote.approved_at = None
    quote.approved_by = None
    quote.approved_by_name = None
    quote.rejected_at = None
    quote.rejected_by = None
    quote.rejected_by_name = None
    quote.reject_reason = None

    # 记录审批历史
    approval = QuoteApproval(
        quote_id=quote_id,
        action=ApprovalAction.REVISE.value,
        from_status=old_status,
        to_status=QuoteStatus.DRAFT,
        approver_id=request.approver_id,
        approver_name=request.approver_name,
        approver_role=request.approver_role,
        comment=request.comment
    )
    db.add(approval)

    db.commit()
    db.refresh(quote)

    logger.info(f"报价单已退回修改: {quote.quote_number}")

    return quote


@router.post("/{quote_id}/send", response_model=QuoteResponse)
def send_quote(
    quote_id: int,
    request: SendRequest,
    db: Session = Depends(get_db)
):
    """
    发送报价单给客户

    状态流转: approved → sent
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 检查状态流转
    if not can_transition(quote.status, QuoteStatus.SENT):
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 [{QuoteStatus.get_display_name(quote.status)}] 不能发送给客户"
        )

    # 更新状态
    old_status = quote.status
    quote.status = QuoteStatus.SENT
    quote.sent_at = datetime.now()
    quote.sent_by = request.sender_id
    quote.sent_by_name = request.sender_name

    # 记录审批历史
    approval = QuoteApproval(
        quote_id=quote_id,
        action=ApprovalAction.SEND.value,
        from_status=old_status,
        to_status=QuoteStatus.SENT,
        approver_id=request.sender_id,
        approver_name=request.sender_name,
        comment=request.comment
    )
    db.add(approval)

    db.commit()
    db.refresh(quote)

    logger.info(f"报价单已发送给客户: {quote.quote_number}")

    return quote


@router.post("/{quote_id}/withdraw", response_model=QuoteResponse)
def withdraw_quote(
    quote_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    撤回报价单

    状态流转: pending_review → draft
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 只允许在待审核状态下撤回
    if quote.status != QuoteStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"当前状态 [{QuoteStatus.get_display_name(quote.status)}] 不能撤回"
        )

    # 更新状态
    old_status = quote.status
    quote.status = QuoteStatus.DRAFT
    quote.submitted_at = None
    quote.submitted_by = None
    quote.submitted_by_name = None

    # 记录审批历史
    approval = QuoteApproval(
        quote_id=quote_id,
        action=ApprovalAction.WITHDRAW.value,
        from_status=old_status,
        to_status=QuoteStatus.DRAFT,
        approver_id=request.approver_id,
        approver_name=request.approver_name,
        approver_role=request.approver_role,
        comment=request.comment
    )
    db.add(approval)

    db.commit()
    db.refresh(quote)

    logger.info(f"报价单已撤回: {quote.quote_number}")

    return quote


@router.get("/{quote_id}/approvals", response_model=QuoteApprovalList)
def get_quote_approvals(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """
    获取报价单审批历史
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    approvals = db.query(QuoteApproval).filter(
        QuoteApproval.quote_id == quote_id
    ).order_by(QuoteApproval.created_at.desc()).all()

    return QuoteApprovalList(total=len(approvals), items=approvals)


# ============ 版本管理 API ============

@router.post("/{quote_id}/create-version", response_model=QuoteResponse)
def create_quote_version(
    quote_id: int,
    request: CreateVersionRequest,
    db: Session = Depends(get_db)
):
    """
    创建报价单新版本

    从现有报价单复制并创建新版本，原版本的 is_current_version 设为 False

    Args:
        quote_id: 原报价单ID
        request: 版本创建请求（包含版本说明）

    Returns:
        新版本的报价单
    """
    # 查询原报价单
    original_quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not original_quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 确定根版本ID
    root_id = original_quote.root_quote_id or original_quote.id

    # 获取当前版本链中的最新版本号
    max_version = db.query(Quote).filter(
        (Quote.root_quote_id == root_id) | (Quote.id == root_id)
    ).with_entities(func.max(Quote.version)).scalar() or 1

    new_version = max_version + 1

    # 生成新的报价单号（保留原单号前缀，添加版本后缀）
    base_number = original_quote.quote_number.split('-V')[0]  # 移除旧版本号后缀
    new_quote_number = f"{base_number}-V{new_version}"

    # 创建新版本（复制所有关键字段）
    new_quote = Quote(
        quote_number=new_quote_number,
        drawing_id=original_quote.drawing_id,
        product_id=original_quote.product_id,
        customer_name=original_quote.customer_name,
        product_name=original_quote.product_name,
        lot_size=original_quote.lot_size,
        # 材料信息
        material_name=original_quote.material_name,
        material_spec=original_quote.material_spec,
        material_density=original_quote.material_density,
        outer_diameter=original_quote.outer_diameter,
        material_length=original_quote.material_length,
        product_length=original_quote.product_length,
        cut_width=original_quote.cut_width,
        remaining_material=original_quote.remaining_material,
        pieces_per_bar=original_quote.pieces_per_bar,
        part_weight=original_quote.part_weight,
        material_price_per_kg=original_quote.material_price_per_kg,
        total_defect_rate=original_quote.total_defect_rate,
        material_management_rate=original_quote.material_management_rate,
        material_cost=original_quote.material_cost,
        # 加工费
        process_cost=original_quote.process_cost,
        # 管理费
        general_management_rate=original_quote.general_management_rate,
        transportation_cost=original_quote.transportation_cost,
        management_cost=original_quote.management_cost,
        # 其他费用
        packaging_material_cost=original_quote.packaging_material_cost,
        consumables_cost=original_quote.consumables_cost,
        other_cost=original_quote.other_cost,
        # 成本汇总
        subtotal_cost=original_quote.subtotal_cost,
        profit_rate=original_quote.profit_rate,
        profit_amount=original_quote.profit_amount,
        unit_price=original_quote.unit_price,
        total_amount=original_quote.total_amount,
        # 其他信息
        currency=original_quote.currency,
        exchange_rate=original_quote.exchange_rate,
        quantity=original_quote.quantity,
        lead_time=original_quote.lead_time,
        calculation_details=original_quote.calculation_details,
        details=original_quote.details,
        # 版本管理
        version=new_version,
        parent_quote_id=original_quote.id,
        root_quote_id=root_id,
        is_current_version=True,
        version_note=request.version_note,
        # 状态重置为草稿
        status=QuoteStatus.DRAFT,
        valid_until=datetime.now().date() + timedelta(days=30),
        # 创建人
        created_by=request.created_by,
        created_by_name=request.created_by_name,
        notes=original_quote.notes
    )

    # 将原版本设为非当前版本
    original_quote.is_current_version = False

    # 同时将同一版本链的其他版本都设为非当前版本
    db.query(Quote).filter(
        (Quote.root_quote_id == root_id) | (Quote.id == root_id),
        Quote.id != original_quote.id
    ).update({'is_current_version': False})

    db.add(new_quote)
    db.commit()
    db.refresh(new_quote)

    logger.info(f"已创建报价单新版本: {new_quote_number} (V{new_version}), 基于: {original_quote.quote_number}")

    return new_quote


@router.get("/{quote_id}/versions", response_model=QuoteVersionList)
def get_quote_versions(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """
    获取报价单所有版本

    返回该报价单的所有版本列表（按版本号排序）

    Args:
        quote_id: 报价单ID（可以是任意版本的ID）

    Returns:
        版本列表
    """
    # 查询报价单
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 确定根版本ID
    root_id = quote.root_quote_id or quote.id

    # 查询所有版本
    versions = db.query(Quote).filter(
        (Quote.root_quote_id == root_id) | (Quote.id == root_id)
    ).order_by(Quote.version.desc()).all()

    # 找到当前版本
    current_version_id = None
    items = []
    for v in versions:
        if v.is_current_version:
            current_version_id = v.id
        items.append(QuoteVersionSummary(
            id=v.id,
            quote_number=v.quote_number,
            version=v.version,
            is_current_version=v.is_current_version,
            version_note=v.version_note,
            status=v.status,
            unit_price=float(v.unit_price) if v.unit_price else None,
            total_amount=float(v.total_amount) if v.total_amount else None,
            created_at=v.created_at,
            created_by_name=v.created_by_name
        ))

    return QuoteVersionList(
        total=len(versions),
        root_quote_id=root_id,
        current_version_id=current_version_id,
        items=items
    )


@router.post("/{quote_id}/set-current", response_model=QuoteResponse)
def set_current_version(
    quote_id: int,
    db: Session = Depends(get_db)
):
    """
    设置为当前版本

    将指定版本设置为当前版本，其他版本设为非当前

    Args:
        quote_id: 报价单ID

    Returns:
        更新后的报价单
    """
    # 查询报价单
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 确定根版本ID
    root_id = quote.root_quote_id or quote.id

    # 将同一版本链的所有版本设为非当前
    db.query(Quote).filter(
        (Quote.root_quote_id == root_id) | (Quote.id == root_id)
    ).update({'is_current_version': False})

    # 设置当前版本
    quote.is_current_version = True

    db.commit()
    db.refresh(quote)

    logger.info(f"已设置报价单当前版本: {quote.quote_number} (V{quote.version})")

    return quote


# ============ 有效期校验 API ============

@router.get("/expiring")
def get_expiring_quotes(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    获取即将过期的报价单

    Args:
        days: 查询未来多少天内过期的报价单，默认7天

    Returns:
        即将过期的报价单列表
    """
    from datetime import date
    today = date.today()
    future_date = today + timedelta(days=days)

    # 查询即将过期的报价单（排除草稿和已过期状态）
    quotes = db.query(Quote).filter(
        Quote.valid_until != None,
        Quote.valid_until >= today,
        Quote.valid_until <= future_date,
        Quote.status.notin_([QuoteStatus.DRAFT, QuoteStatus.EXPIRED])
    ).order_by(Quote.valid_until.asc()).all()

    return {
        "success": True,
        "data": [
            {
                "id": q.id,
                "quote_number": q.quote_number,
                "customer_name": q.customer_name,
                "product_name": q.product_name,
                "total_amount": float(q.total_amount) if q.total_amount else 0,
                "status": q.status,
                "valid_until": q.valid_until.isoformat() if q.valid_until else None,
                "days_remaining": (q.valid_until - today).days if q.valid_until else None
            }
            for q in quotes
        ],
        "total": len(quotes)
    }


@router.post("/check-expired")
def check_and_expire_quotes(
    db: Session = Depends(get_db)
):
    """
    检查并标记已过期的报价单

    将过期的报价单状态更新为 expired
    仅影响 pending_review 和 approved 状态的报价单

    Returns:
        处理结果统计
    """
    from datetime import date
    today = date.today()

    # 查询已过期的报价单
    expired_quotes = db.query(Quote).filter(
        Quote.valid_until != None,
        Quote.valid_until < today,
        Quote.status.in_([QuoteStatus.PENDING_REVIEW, QuoteStatus.APPROVED])
    ).all()

    expired_count = 0
    expired_list = []

    for quote in expired_quotes:
        old_status = quote.status
        quote.status = QuoteStatus.EXPIRED
        expired_count += 1
        expired_list.append({
            "id": quote.id,
            "quote_number": quote.quote_number,
            "customer_name": quote.customer_name,
            "old_status": old_status,
            "valid_until": quote.valid_until.isoformat()
        })

        # 记录审批历史
        approval = QuoteApproval(
            quote_id=quote.id,
            action="expire",
            from_status=old_status,
            to_status=QuoteStatus.EXPIRED,
            approver_name="系统",
            comment="报价单已超过有效期，系统自动标记为过期"
        )
        db.add(approval)

    db.commit()

    logger.info(f"已标记 {expired_count} 条报价单为过期状态")

    return {
        "success": True,
        "message": f"已检查并标记 {expired_count} 条报价单为过期状态",
        "data": {
            "expired_count": expired_count,
            "expired_quotes": expired_list
        }
    }


@router.put("/{quote_id}/extend-validity", response_model=QuoteResponse)
def extend_quote_validity(
    quote_id: int,
    days: int = 30,
    new_valid_until: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    延长报价单有效期

    Args:
        quote_id: 报价单ID
        days: 延长天数（从今天算起），默认30天
        new_valid_until: 新的有效期日期（YYYY-MM-DD），如果提供则忽略days参数

    Returns:
        更新后的报价单
    """
    from datetime import date

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价单不存在")

    # 已发送的报价单不能延长有效期
    if quote.status == QuoteStatus.SENT:
        raise HTTPException(status_code=400, detail="已发送的报价单不能延长有效期")

    # 计算新的有效期
    if new_valid_until:
        try:
            new_date = datetime.strptime(new_valid_until, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")

        if new_date <= date.today():
            raise HTTPException(status_code=400, detail="新有效期必须大于今天")
    else:
        new_date = date.today() + timedelta(days=days)

    old_valid_until = quote.valid_until
    quote.valid_until = new_date

    # 如果是过期状态，恢复为草稿状态
    if quote.status == QuoteStatus.EXPIRED:
        old_status = quote.status
        quote.status = QuoteStatus.DRAFT

        # 记录审批历史
        approval = QuoteApproval(
            quote_id=quote_id,
            action="reactivate",
            from_status=old_status,
            to_status=QuoteStatus.DRAFT,
            approver_name="系统",
            comment=f"延长有效期至 {new_date}，报价单已恢复为草稿状态"
        )
        db.add(approval)

    db.commit()
    db.refresh(quote)

    logger.info(f"报价单有效期已延长: {quote.quote_number}, {old_valid_until} -> {new_date}")

    return quote


@router.get("/validity-statistics")
def get_validity_statistics(
    db: Session = Depends(get_db)
):
    """
    获取报价单有效期统计

    Returns:
        有效期统计数据
    """
    from datetime import date
    from sqlalchemy import func

    today = date.today()

    # 统计各种状态
    total = db.query(Quote).count()

    # 已过期（valid_until < today 且 状态不是 expired/sent）
    overdue = db.query(Quote).filter(
        Quote.valid_until != None,
        Quote.valid_until < today,
        Quote.status.in_([QuoteStatus.PENDING_REVIEW, QuoteStatus.APPROVED])
    ).count()

    # 已标记过期
    marked_expired = db.query(Quote).filter(
        Quote.status == QuoteStatus.EXPIRED
    ).count()

    # 7天内过期
    expiring_7_days = db.query(Quote).filter(
        Quote.valid_until != None,
        Quote.valid_until >= today,
        Quote.valid_until <= today + timedelta(days=7),
        Quote.status.notin_([QuoteStatus.DRAFT, QuoteStatus.EXPIRED, QuoteStatus.SENT])
    ).count()

    # 30天内过期
    expiring_30_days = db.query(Quote).filter(
        Quote.valid_until != None,
        Quote.valid_until >= today,
        Quote.valid_until <= today + timedelta(days=30),
        Quote.status.notin_([QuoteStatus.DRAFT, QuoteStatus.EXPIRED, QuoteStatus.SENT])
    ).count()

    # 有效期内
    valid = db.query(Quote).filter(
        Quote.valid_until != None,
        Quote.valid_until > today,
        Quote.status.notin_([QuoteStatus.EXPIRED, QuoteStatus.SENT])
    ).count()

    return {
        "success": True,
        "data": {
            "total": total,
            "overdue": overdue,
            "marked_expired": marked_expired,
            "expiring_7_days": expiring_7_days,
            "expiring_30_days": expiring_30_days,
            "valid": valid,
            "today": today.isoformat()
        }
    }


@router.get("/{quote_id}/compare/{other_id}", response_model=QuoteCompareResponse)
def compare_quote_versions(
    quote_id: int,
    other_id: int,
    db: Session = Depends(get_db)
):
    """
    对比两个报价单版本

    对比两个报价单的主要字段差异

    Args:
        quote_id: 第一个报价单ID（通常是较旧版本）
        other_id: 第二个报价单ID（通常是较新版本）

    Returns:
        对比结果
    """
    # 查询两个报价单
    quote1 = db.query(Quote).filter(Quote.id == quote_id).first()
    quote2 = db.query(Quote).filter(Quote.id == other_id).first()

    if not quote1:
        raise HTTPException(status_code=404, detail=f"报价单 {quote_id} 不存在")
    if not quote2:
        raise HTTPException(status_code=404, detail=f"报价单 {other_id} 不存在")

    # 定义需要比较的字段
    compare_fields = [
        ("lot_size", "批量"),
        ("material_name", "材料名称"),
        ("material_cost", "材料费"),
        ("process_cost", "加工费"),
        ("management_cost", "管理费"),
        ("other_cost", "其他费用"),
        ("subtotal_cost", "小计"),
        ("profit_rate", "利润率"),
        ("profit_amount", "利润"),
        ("unit_price", "单价"),
        ("total_amount", "总价"),
        ("general_management_rate", "管理费率"),
        ("material_price_per_kg", "材料单价"),
        ("total_defect_rate", "总不良率"),
        ("lead_time", "交货周期"),
        ("notes", "备注"),
    ]

    differences = []
    changed_count = 0

    for field, label in compare_fields:
        val1 = getattr(quote1, field, None)
        val2 = getattr(quote2, field, None)

        # 处理 Decimal 类型
        if val1 is not None and hasattr(val1, '__float__'):
            val1 = float(val1)
        if val2 is not None and hasattr(val2, '__float__'):
            val2 = float(val2)

        changed = val1 != val2
        if changed:
            changed_count += 1

        differences.append(VersionComparisonItem(
            field=field,
            field_label=label,
            version1_value=val1,
            version2_value=val2,
            changed=changed
        ))

    # 创建摘要信息
    quote1_summary = QuoteVersionSummary(
        id=quote1.id,
        quote_number=quote1.quote_number,
        version=quote1.version,
        is_current_version=quote1.is_current_version,
        version_note=quote1.version_note,
        status=quote1.status,
        unit_price=float(quote1.unit_price) if quote1.unit_price else None,
        total_amount=float(quote1.total_amount) if quote1.total_amount else None,
        created_at=quote1.created_at,
        created_by_name=quote1.created_by_name
    )

    quote2_summary = QuoteVersionSummary(
        id=quote2.id,
        quote_number=quote2.quote_number,
        version=quote2.version,
        is_current_version=quote2.is_current_version,
        version_note=quote2.version_note,
        status=quote2.status,
        unit_price=float(quote2.unit_price) if quote2.unit_price else None,
        total_amount=float(quote2.total_amount) if quote2.total_amount else None,
        created_at=quote2.created_at,
        created_by_name=quote2.created_by_name
    )

    # 计算价格变化
    price_change = None
    price_change_pct = None
    if quote1.total_amount and quote2.total_amount:
        price_change = float(quote2.total_amount) - float(quote1.total_amount)
        if float(quote1.total_amount) != 0:
            price_change_pct = (price_change / float(quote1.total_amount)) * 100

    summary = {
        "total_fields": len(compare_fields),
        "changed_fields": changed_count,
        "unchanged_fields": len(compare_fields) - changed_count,
        "price_change": price_change,
        "price_change_pct": round(price_change_pct, 2) if price_change_pct else None
    }

    return QuoteCompareResponse(
        quote1=quote1_summary,
        quote2=quote2_summary,
        differences=differences,
        summary=summary
    )
