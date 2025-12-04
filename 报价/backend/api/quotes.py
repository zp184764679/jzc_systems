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
from models.drawing import Drawing
from models.material import Material
from models.process import Process
from api.schemas import QuoteResponse, QuoteList, QuoteCreate, MessageResponse
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

        # 处理多个小数点的情况：只保留第一个小数点
        parts = cleaned.split('.')
        if len(parts) > 2:
            # 重新组装：第一部分 + '.' + 其余部分拼接（去掉小数点）
            cleaned = parts[0] + '.' + ''.join(parts[1:])

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
