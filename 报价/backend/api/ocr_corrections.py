# api/ocr_corrections.py
"""
OCR修正和学习API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from config.database import get_db
from services.ocr_learning_service import get_ocr_learning_service
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class CorrectionRequest(BaseModel):
    """修正请求"""
    drawing_id: int
    field_name: str
    ocr_value: Optional[str] = None
    corrected_value: str


class CorrectionStatsResponse(BaseModel):
    """修正统计响应"""
    total: int
    by_field: dict
    by_type: dict
    avg_similarity: float
    recent_corrections: list


class LearningInsightsResponse(BaseModel):
    """学习洞察响应"""
    status: str
    message: Optional[str] = None
    stats: Optional[dict] = None
    suggestions: list


@router.post("/corrections")
def record_correction(
    request: CorrectionRequest,
    db: Session = Depends(get_db)
):
    """
    记录人工修正

    - 保存修正记录用于AI学习
    - 自动分析修正类型和相似度
    """
    logger.info(f"📝 记录修正: drawing_id={request.drawing_id}, field={request.field_name}")

    try:
        learning_service = get_ocr_learning_service(db)

        correction = learning_service.record_correction(
            drawing_id=request.drawing_id,
            field_name=request.field_name,
            ocr_value=request.ocr_value,
            corrected_value=request.corrected_value
        )

        return {
            "success": True,
            "correction_id": correction.id,
            "correction_type": correction.correction_type,
            "similarity_score": correction.similarity_score,
            "message": "修正记录已保存"
        }
    except Exception as e:
        logger.error(f"❌ 记录修正失败: {e}")
        raise HTTPException(status_code=500, detail=f"记录修正失败: {str(e)}")


@router.get("/corrections/stats", response_model=CorrectionStatsResponse)
def get_correction_stats(
    field_name: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取修正统计数据

    - 支持按字段筛选
    - 返回修正分布和趋势
    """
    logger.info(f"📊 获取修正统计: field_name={field_name}, limit={limit}")

    try:
        learning_service = get_ocr_learning_service(db)
        stats = learning_service.get_correction_stats(
            field_name=field_name,
            limit=limit
        )

        return CorrectionStatsResponse(**stats)
    except Exception as e:
        logger.error(f"❌ 获取统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/corrections/patterns")
def get_field_patterns(
    field_name: str,
    min_count: int = 3,
    db: Session = Depends(get_db)
):
    """
    获取字段的常见修正模式

    - 分析高频修正规律
    - 用于生成智能规则
    """
    logger.info(f"🔍 获取修正模式: field_name={field_name}")

    try:
        learning_service = get_ocr_learning_service(db)
        patterns = learning_service.get_field_patterns(
            field_name=field_name,
            min_count=min_count
        )

        return {
            "success": True,
            "field_name": field_name,
            "patterns": patterns,
            "pattern_count": len(patterns)
        }
    except Exception as e:
        logger.error(f"❌ 获取模式失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模式失败: {str(e)}")


@router.get("/learning/insights", response_model=LearningInsightsResponse)
def get_learning_insights(db: Session = Depends(get_db)):
    """
    获取AI学习洞察

    - 分析修正数据
    - 生成优化建议
    - 用于持续改进OCR准确性
    """
    logger.info("🧠 生成AI学习洞察...")

    try:
        learning_service = get_ocr_learning_service(db)
        insights = learning_service.learn_from_corrections()

        return LearningInsightsResponse(**insights)
    except Exception as e:
        logger.error(f"❌ 生成洞察失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成洞察失败: {str(e)}")


@router.get("/health")
def health_check():
    """OCR学习服务健康检查"""
    return {
        "status": "healthy",
        "service": "ocr_learning"
    }
