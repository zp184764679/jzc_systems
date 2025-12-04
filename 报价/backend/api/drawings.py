# api/drawings.py
"""
图纸管理API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from models.drawing import Drawing
from api.schemas import (
    DrawingResponse, DrawingList, DrawingUpdate,
    OCRResult, MessageResponse
)
from services.drawing_ocr_service import get_ocr_service
from services.ocr_learning_service import get_ocr_learning_service
from services.crm_match_service import enhance_ocr_result_with_crm
from utils.file_handler import save_upload_file, delete_file, get_file_type
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=DrawingResponse, status_code=201)
async def upload_drawing(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传图纸文件

    - 支持PDF、PNG、JPG、JPEG格式
    - 最大文件大小: 50MB
    - 自动生成唯一文件名
    """
    logger.info(f"📤 收到图纸上传请求: {file.filename}")

    try:
        # 保存文件
        file_path, original_filename, file_size = await save_upload_file(file, "drawings")
        logger.info(f"✅ 文件保存成功: {file_path}")

        # 生成唯一图号（使用时间戳和UUID确保唯一性）
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        drawing_number = f"DRAFT-{timestamp}-{unique_suffix}"

        # 创建图纸记录
        drawing = Drawing(
            drawing_number=drawing_number,
            file_path=file_path,
            file_name=original_filename,
            file_size=file_size,
            file_type=get_file_type(original_filename),
            ocr_status="pending"
        )

        db.add(drawing)
        db.commit()
        db.refresh(drawing)

        logger.info(f"✅ 图纸记录创建成功: ID={drawing.id}")

        return drawing

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 上传图纸失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/{drawing_id}/ocr", response_model=OCRResult)
async def recognize_drawing(
    drawing_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    触发OCR识别

    - 使用Ollama Vision识别图纸
    - 自动提取关键信息
    - 支持后台异步处理
    """
    logger.info(f"🔍 触发OCR识别: drawing_id={drawing_id}")

    # 查询图纸
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    if not drawing.file_path:
        raise HTTPException(status_code=400, detail="图纸文件不存在")

    # 更新状态为处理中
    drawing.ocr_status = "processing"
    db.commit()

    try:
        # 获取OCR服务和学习服务
        ocr_service = get_ocr_service()
        learning_service = get_ocr_learning_service(db)

        # 执行OCR识别
        logger.info(f"🤖 开始OCR识别: {drawing.file_path}")
        result = ocr_service.extract_drawing_info(drawing.file_path)

        if result.get('success'):
            # 应用智能规则进行自动修正
            corrected_result = learning_service.apply_smart_rules(result)
            auto_corrections = corrected_result.pop('_auto_corrections', [])

            if auto_corrections:
                logger.info(f"✨ 智能规则应用了{len(auto_corrections)}个自动修正")
                for correction in auto_corrections:
                    logger.info(f"  - {correction['field']}: {correction['original']} → {correction['corrected']}")

            result = corrected_result

            # CRM客户匹配 - 将OCR识别的客户名称与CRM数据库匹配
            try:
                result = enhance_ocr_result_with_crm(result)
                if result.get('crm_match', {}).get('matched'):
                    logger.info(f"🏢 CRM客户匹配成功: '{result.get('crm_match', {}).get('original_name')}' -> '{result.get('customer_name')}'")
            except Exception as crm_error:
                logger.warning(f"⚠️  CRM客户匹配失败: {str(crm_error)}")
            # 保存原始drawing_number以备回退
            original_drawing_number = drawing.drawing_number

            # 更新图纸信息
            drawing.drawing_number = result.get('drawing_number') or drawing.drawing_number
            drawing.customer_name = result.get('customer_name')
            drawing.product_name = result.get('product_name')
            drawing.customer_part_number = result.get('customer_part_number')
            drawing.material = result.get('material')
            drawing.outer_diameter = result.get('outer_diameter')
            drawing.length = result.get('length')
            drawing.weight = result.get('weight')
            drawing.tolerance = result.get('tolerance')
            drawing.surface_roughness = result.get('surface_roughness')
            drawing.heat_treatment = result.get('heat_treatment')
            drawing.surface_treatment = result.get('surface_treatment')
            drawing.special_requirements = result.get('special_requirements')
            drawing.ocr_data = result.get('raw_data', {})
            drawing.ocr_confidence = str(result.get('confidence', 0))
            drawing.ocr_status = "completed"

            try:
                db.commit()
                db.refresh(drawing)
            except Exception as commit_error:
                db.rollback()
                # 如果是图号重复错误，保留DRAFT图号但保存其他字段
                if "UNIQUE constraint" in str(commit_error) and "drawing_number" in str(commit_error):
                    logger.warning(f"⚠️  图号重复: {result.get('drawing_number')}，保留DRAFT图号: {original_drawing_number}")
                    # 重新获取drawing对象（rollback后需要重新获取）
                    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
                    # 恢复原始drawing_number，保存其他OCR字段
                    drawing.customer_name = result.get('customer_name')
                    drawing.product_name = result.get('product_name')
                    drawing.customer_part_number = result.get('customer_part_number')
                    drawing.material = result.get('material')
                    drawing.outer_diameter = result.get('outer_diameter')
                    drawing.length = result.get('length')
                    drawing.weight = result.get('weight')
                    drawing.tolerance = result.get('tolerance')
                    drawing.surface_roughness = result.get('surface_roughness')
                    drawing.heat_treatment = result.get('heat_treatment')
                    drawing.surface_treatment = result.get('surface_treatment')
                    drawing.special_requirements = result.get('special_requirements')
                    drawing.ocr_data = result.get('raw_data', {})
                    drawing.ocr_confidence = str(result.get('confidence', 0))
                    drawing.ocr_status = "completed"
                    db.commit()
                    db.refresh(drawing)
                else:
                    raise

            logger.info(f"✅ OCR识别成功: drawing_id={drawing_id}")

            return OCRResult(**result)
        else:
            # 识别失败
            drawing.ocr_status = "failed"
            db.commit()

            logger.error(f"❌ OCR识别失败: {result.get('error')}")

            return OCRResult(
                success=False,
                error=result.get('error', '识别失败')
            )

    except Exception as e:
        drawing.ocr_status = "failed"
        db.commit()

        logger.error(f"❌ OCR识别异常: {str(e)}")

        return OCRResult(
            success=False,
            error=f"识别失败: {str(e)}"
        )


@router.get("/{drawing_id}", response_model=DrawingResponse)
def get_drawing(drawing_id: int, db: Session = Depends(get_db)):
    """
    获取图纸详情
    """
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    return drawing


@router.put("/{drawing_id}", response_model=DrawingResponse)
def update_drawing(
    drawing_id: int,
    drawing_update: DrawingUpdate,
    db: Session = Depends(get_db)
):
    """
    更新图纸信息

    - 支持更新图号、客户、材质等信息
    - 用于人工校对OCR结果
    """
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 更新字段
    update_data = drawing_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(drawing, field, value)

    db.commit()
    db.refresh(drawing)

    logger.info(f"✅ 图纸信息已更新: drawing_id={drawing_id}")

    return drawing


@router.get("", response_model=DrawingList)
def list_drawings(
    skip: int = 0,
    limit: int = 20,
    customer: Optional[str] = None,
    material: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取图纸列表

    - 支持分页（skip>=0, limit: 1-1000）
    - 支持按客户和材质筛选
    """
    # 记录接收到的原始参数
    import sys
    print(f"FUNCTION CALLED: limit={limit}, type={type(limit)}", file=sys.stderr, flush=True)

    # 强制验证参数 - 在任何数据库操作之前
    if limit < 1:
        raise HTTPException(status_code=422, detail=f"limit参数无效: {limit}，必须 >= 1")
    if limit > 1000:
        raise HTTPException(status_code=422, detail=f"limit参数无效: {limit}，必须 <= 1000")
    if skip < 0:
        raise HTTPException(status_code=422, detail=f"skip参数无效: {skip}，必须 >= 0")

    query = db.query(Drawing)

    # 筛选条件
    if customer:
        query = query.filter(Drawing.customer_name.contains(customer))
    if material:
        query = query.filter(Drawing.material.contains(material))

    # 获取总数
    total = query.count()

    # 分页查询
    items = query.order_by(Drawing.created_at.desc()).offset(skip).limit(limit).all()

    return DrawingList(total=total, items=items)


@router.delete("/{drawing_id}", response_model=MessageResponse)
def delete_drawing(drawing_id: int, db: Session = Depends(get_db)):
    """
    删除图纸

    - 同时删除文件和数据库记录
    """
    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail="图纸不存在")

    # 删除文件
    if drawing.file_path:
        delete_file(drawing.file_path)

    # 删除数据库记录
    db.delete(drawing)
    db.commit()

    logger.info(f"✅ 图纸已删除: drawing_id={drawing_id}")

    return MessageResponse(message="图纸删除成功")
