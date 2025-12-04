# tasks/notify_rfq.py
# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from extensions import celery, db
from models.rfq_notification_task import RFQNotificationTask
from models.rfq import RFQ
from models.supplier import Supplier
from models.supplier_quote import SupplierQuote

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.send_rfq_notification")
def send_rfq_notification(self, task_id: int):
    """
    发送RFQ通知任务（改进版）

    说明：
    - SupplierQuote 已在 rfq_service.create_supplier_quotes_for_routes() 中按品类创建
    - 本任务只负责：验证数据存在 + 标记任务状态 + （可选）发送邮件通知
    """
    task = RFQNotificationTask.query.get(task_id)
    if not task:
        logger.error(f"[send_rfq_notification] 任务不存在: {task_id}")
        return

    try:
        rfq = RFQ.query.get(task.rfq_id)
        supplier = Supplier.query.get(task.supplier_id)
        if not rfq or not supplier:
            task.status = 'failed'
            task.error_message = "RFQ或Supplier不存在"
            db.session.commit()
            return

        # 验证该供应商对应品类的报价是否已创建
        category = task.category  # 任务关联的品类
        quote = SupplierQuote.query.filter_by(
            rfq_id=rfq.id,
            supplier_id=supplier.id,
            category=category
        ).first()

        if not quote:
            task.status = 'failed'
            task.error_message = f"未找到报价邀请（品类: {category}）"
            db.session.commit()
            logger.warning(f"[send_rfq_notification] 未找到报价: RFQ#{rfq.id} × S#{supplier.id} × {category}")
            return

        # TODO: 这里可以添加邮件通知逻辑
        # send_email_to_supplier(supplier.contact_email, rfq, quote)

        # 标记任务完成
        task.status = 'sent'
        task.sent_at = datetime.utcnow()
        task.error_message = None
        db.session.commit()

        logger.info(f"✅ RFQ#{rfq.id} → Supplier#{supplier.id} ({category}) 通知完成")

    except Exception as e:
        db.session.rollback()
        try:
            task = RFQNotificationTask.query.get(task_id)
            if task:
                task.status = 'failed'
                task.error_message = str(e)[:500]
                task.failed_at = datetime.utcnow()
                db.session.commit()
        except Exception:
            db.session.rollback()
        logger.exception(f"[send_rfq_notification] 异常 task={task_id}: {e}")
        raise self.retry(exc=e)
