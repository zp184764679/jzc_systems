# -*- coding: utf-8 -*-
"""
RFQ Items 分类异步任务
用于在后台运行 AI 分类，避免阻塞用户请求
"""
import logging
import json
from datetime import datetime
from sqlalchemy import text

logger = logging.getLogger(__name__)


from extensions import db, celery
from models.rfq import RFQ
from models.rfq_item import RFQItem
from services.ai_classifier import LocalClassifier
from constants.categories import get_major_category


@celery.task(bind=True, max_retries=3, default_retry_delay=10, name="tasks.classify_rfq_items")
def classify_rfq_items(self, rfq_id: int):
    """
    异步分类 RFQ 中的所有物料项

    Args:
        rfq_id: RFQ ID

    Returns:
        dict: 分类结果统计
    """
    from app import app

    with app.app_context():
        try:
            logger.info(f"开始分类 RFQ {rfq_id} 的物料项...")

            # 获取 RFQ
            rfq = RFQ.query.get(rfq_id)
            if not rfq:
                logger.error(f"RFQ {rfq_id} 不存在")
                return {"error": "RFQ不存在"}

            # 获取所有待分类的items
            items = RFQItem.query.filter_by(rfq_id=rfq_id).all()
            if not items:
                logger.warning(f"RFQ {rfq_id} 没有物料项")
                return {"error": "没有物料项"}

            # 初始化分类器
            classifier = LocalClassifier()

            success_count = 0
            error_count = 0

            for item in items:
                try:
                    # 执行分类
                    result = classifier.classify(
                        name=item.item_name or "",
                        spec=item.item_spec or "",
                        remark=""  # RFQItem 没有 remark字段，可以从pr_item获取
                    ) or {}

                    category = result.get('category', '未分类')
                    major_category = result.get('major_category', get_major_category(category) or "")
                    minor_category = result.get('minor_category', '')
                    source = result.get('source', 'vector')
                    scores = result.get('scores', {}) or {}

                    # 只保存 top-3 评分
                    top_3_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3])

                    # 更新item分类信息
                    update_sql = text("""
                        UPDATE rfq_items
                        SET category = :category,
                            major_category = :major_category,
                            minor_category = :minor_category,
                            classification_source = :classification_source,
                            classification_score = :classification_score
                        WHERE id = :item_id
                    """)

                    db.session.execute(update_sql, {
                        'category': category,
                        'major_category': major_category or '',
                        'minor_category': minor_category or '',
                        'classification_source': source,
                        'classification_score': json.dumps(top_3_scores, ensure_ascii=False),
                        'item_id': item.id
                    })

                    success_count += 1
                    logger.info(f"物料项 {item.id} 分类成功: {category} (来源: {source})")

                except Exception as e:
                    error_count += 1
                    logger.error(f"物料项 {item.id} 分类失败: {str(e)}")

            # 提交所有更新
            db.session.commit()

            # 更新RFQ状态为已分类
            rfq.classification_status = 'completed'
            rfq.classification_completed_at = datetime.utcnow()
            db.session.commit()

            result = {
                "rfq_id": rfq_id,
                "total_items": len(items),
                "success": success_count,
                "errors": error_count,
                "status": "completed"
            }

            logger.info(f"RFQ {rfq_id} 分类完成: {result}")
            return result

        except Exception as e:
            logger.error(f"分类任务失败: {str(e)}")
            db.session.rollback()

            # 重试机制
            try:
                raise self.retry(exc=e)
            except self.MaxRetriesExceededError:
                # 更新RFQ状态为失败
                try:
                    rfq = RFQ.query.get(rfq_id)
                    if rfq:
                        rfq.classification_status = 'failed'
                        db.session.commit()
                except:
                    pass
                return {"error": str(e), "status": "failed"}
