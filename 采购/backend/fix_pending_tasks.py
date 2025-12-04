#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复待处理的RFQ通知任务"""
import sys
sys.path.insert(0, '.')

from app import app, db
from models.rfq_notification_task import RFQNotificationTask
from models.rfq import RFQ
from models.supplier import Supplier
from models.supplier_quote import SupplierQuote
from datetime import datetime

with app.app_context():
    # 查找所有pending任务
    pending_tasks = RFQNotificationTask.query.filter_by(status='pending').all()
    print(f"找到 {len(pending_tasks)} 个待处理任务")

    for task in pending_tasks:
        print(f"\n处理任务 #{task.id}: RFQ#{task.rfq_id} → S#{task.supplier_id} ({task.category})")

        rfq = RFQ.query.get(task.rfq_id)
        supplier = Supplier.query.get(task.supplier_id)

        if not rfq or not supplier:
            task.status = 'failed'
            task.error_reason = "RFQ或Supplier不存在"
            db.session.commit()
            print(f"  ❌ 失败: RFQ或Supplier不存在")
            continue

        # 查找报价记录
        quote = SupplierQuote.query.filter_by(
            rfq_id=rfq.id,
            supplier_id=supplier.id
        ).first()

        if not quote:
            # 没有找到报价记录，但这不是错误，只是供应商还没报价
            pass

        # 标记任务完成
        task.status = 'sent'
        task.sent_at = datetime.utcnow()
        task.error_reason = None
        db.session.commit()
        print(f"  ✅ 已标记为sent")

    print(f"\n处理完成")
