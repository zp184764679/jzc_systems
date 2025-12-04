# -*- coding: utf-8 -*-
"""
通知服务
Notification Service
"""
from datetime import datetime
import json
import logging
from models.notification import Notification
from extensions import db

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务 - 统一管理所有通知"""

    @staticmethod
    def create_notification(
        recipient_id,
        recipient_type,
        notification_type,
        title,
        message,
        related_type=None,
        related_id=None,
        data=None,
        send_method='in_app'
    ):
        """
        创建通知

        Args:
            recipient_id: 接收者ID
            recipient_type: 接收者类型 (supplier/user)
            notification_type: 通知类型 (po_created, invoice_approved, etc.)
            title: 通知标题
            message: 通知内容
            related_type: 关联对象类型 (purchase_order, invoice, etc.)
            related_id: 关联对象ID
            data: 额外数据 (dict)
            send_method: 发送方式 (in_app/email/sms)

        Returns:
            Notification: 创建的通知对象
        """
        try:
            notification = Notification(
                recipient_id=recipient_id,
                recipient_type=recipient_type,
                notification_type=notification_type,
                title=title,
                message=message,
                related_type=related_type,
                related_id=related_id,
                data=json.dumps(data) if data else None,
                send_method=send_method,
                is_sent=True,  # 站内消息直接标记为已发送
                sent_at=datetime.utcnow()
            )

            db.session.add(notification)
            db.session.commit()

            print(f"✅ 通知创建成功: {notification_type} -> {recipient_type}#{recipient_id}")
            return notification

        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建通知失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def notify_po_created(po, supplier):
        """
        通知供应商：采购订单已创建

        Args:
            po: PurchaseOrder对象
            supplier: Supplier对象
        """
        from datetime import timedelta

        # 计算剩余天数
        days_remaining = 7
        if po.invoice_due_date:
            delta = po.invoice_due_date - datetime.utcnow()
            days_remaining = max(0, delta.days)

        title = f"新采购订单 {po.po_number}"
        message = f"""您好 {supplier.company_name}，

您有一个新的采购订单待处理：

📋 订单号：{po.po_number}
💰 订单金额：¥{po.total_price:,.2f}
🚚 交货期：{po.lead_time} 天
📅 发票截止日期：{po.invoice_due_date.strftime('%Y-%m-%d') if po.invoice_due_date else '未设置'}

⚠️ 请在 {days_remaining} 天内上传发票，逾期将影响后续合作。

请登录系统查看详情并上传发票。
"""

        data = {
            'po_id': po.id,
            'po_number': po.po_number,
            'total_price': float(po.total_price) if po.total_price else 0,
            'lead_time': po.lead_time,
            'invoice_due_date': po.invoice_due_date.isoformat() if po.invoice_due_date else None,
            'days_remaining': days_remaining
        }

        return NotificationService.create_notification(
            recipient_id=supplier.id,
            recipient_type='supplier',
            notification_type='po_created',
            title=title,
            message=message,
            related_type='purchase_order',
            related_id=po.id,
            data=data
        )

    @staticmethod
    def notify_invoice_approved(invoice, supplier):
        """
        通知供应商：发票已审批通过

        Args:
            invoice: Invoice对象
            supplier: Supplier对象
        """
        title = f"发票 {invoice.invoice_number} 已批准"
        message = f"""您好 {supplier.company_name}，

您提交的发票已审批通过：

📄 发票号：{invoice.invoice_number}
💰 发票金额：¥{invoice.amount:,.2f}
📋 关联订单：{invoice.po.po_number if invoice.po else '-'}
✅ 审批状态：已批准
⏰ 审批时间：{invoice.approved_at.strftime('%Y-%m-%d %H:%M') if invoice.approved_at else '-'}

财务将按照合同约定的付款条件进行付款处理。
"""

        data = {
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'amount': float(invoice.amount) if invoice.amount else 0,
            'po_number': invoice.po.po_number if invoice.po else None,
            'approved_at': invoice.approved_at.isoformat() if invoice.approved_at else None
        }

        return NotificationService.create_notification(
            recipient_id=supplier.id,
            recipient_type='supplier',
            notification_type='invoice_approved',
            title=title,
            message=message,
            related_type='invoice',
            related_id=invoice.id,
            data=data
        )

    @staticmethod
    def notify_invoice_rejected(invoice, supplier, reason=""):
        """
        通知供应商：发票已被驳回

        Args:
            invoice: Invoice对象
            supplier: Supplier对象
            reason: 驳回原因
        """
        title = f"发票 {invoice.invoice_number} 已驳回"
        message = f"""您好 {supplier.company_name}，

您提交的发票审批未通过：

📄 发票号：{invoice.invoice_number}
💰 发票金额：¥{invoice.amount:,.2f}
📋 关联订单：{invoice.po.po_number if invoice.po else '-'}
❌ 审批状态：已驳回
📝 驳回原因：{reason if reason else '未提供'}

请根据驳回原因修正后重新提交。如有疑问，请联系采购部门。
"""

        data = {
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'amount': float(invoice.amount) if invoice.amount else 0,
            'po_number': invoice.po.po_number if invoice.po else None,
            'rejection_reason': reason
        }

        return NotificationService.create_notification(
            recipient_id=supplier.id,
            recipient_type='supplier',
            notification_type='invoice_rejected',
            title=title,
            message=message,
            related_type='invoice',
            related_id=invoice.id,
            data=data
        )

    @staticmethod
    def get_unread_notifications(recipient_id, recipient_type='supplier', limit=20):
        """
        获取未读通知

        Args:
            recipient_id: 接收者ID
            recipient_type: 接收者类型
            limit: 返回数量限制

        Returns:
            list: 未读通知列表
        """
        notifications = Notification.query.filter_by(
            recipient_id=recipient_id,
            recipient_type=recipient_type,
            is_read=False
        ).order_by(Notification.created_at.desc()).limit(limit).all()

        return [n.to_dict() for n in notifications]

    @staticmethod
    def get_all_notifications(recipient_id, recipient_type='supplier', page=1, per_page=20):
        """
        获取所有通知（分页）

        Args:
            recipient_id: 接收者ID
            recipient_type: 接收者类型
            page: 页码
            per_page: 每页数量

        Returns:
            dict: {items, total, page, per_page, pages}
        """
        query = Notification.query.filter_by(
            recipient_id=recipient_id,
            recipient_type=recipient_type
        ).order_by(Notification.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [n.to_dict() for n in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }

    @staticmethod
    def mark_as_read(notification_id, recipient_id):
        """
        标记通知为已读

        Args:
            notification_id: 通知ID
            recipient_id: 接收者ID（用于权限验证）

        Returns:
            bool: 是否成功
        """
        try:
            notification = Notification.query.filter_by(
                id=notification_id,
                recipient_id=recipient_id
            ).first()

            if not notification:
                return False

            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()

            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ 标记通知为已读失败: {str(e)}")
            return False

    @staticmethod
    def mark_all_as_read(recipient_id, recipient_type='supplier'):
        """
        标记所有通知为已读

        Args:
            recipient_id: 接收者ID
            recipient_type: 接收者类型

        Returns:
            int: 标记的数量
        """
        try:
            count = Notification.query.filter_by(
                recipient_id=recipient_id,
                recipient_type=recipient_type,
                is_read=False
            ).update({'is_read': True, 'read_at': datetime.utcnow()})

            db.session.commit()
            return count

        except Exception as e:
            db.session.rollback()
            print(f"❌ 批量标记通知为已读失败: {str(e)}")
            return 0

    @staticmethod
    def notify_pr_pending_approval(pr, approver_user_id: int):
        """
        通知审批人：有新的PR待审批（含企业微信通知）

        Args:
            pr: PR对象
            approver_user_id: 审批人用户ID
        """
        try:
            # 从统一数据源查询审批人信息
            from utils.auth import get_user_by_id
            approver = get_user_by_id(approver_user_id)
            if not approver:
                logger.warning(f"⚠️  审批人不存在: user_id={approver_user_id}")
                return None

            # 创建站内通知
            item_count = len(pr.items) if hasattr(pr, 'items') else 0
            owner_name = pr.owner.username if hasattr(pr, 'owner') and pr.owner else '未知'
            owner_department = pr.owner.department if hasattr(pr, 'owner') and pr.owner else '未知'

            title = f"【待审批】采购申请 {pr.pr_number}"
            message = f"""您有新的采购申请待审批：

📋 申请单号：{pr.pr_number}
👤 申请人：{owner_name}
🏢 部门：{owner_department}
📦 物料数量：{item_count} 项
📅 申请时间：{pr.created_at.strftime('%Y-%m-%d %H:%M') if pr.created_at else '-'}

请及时审批。"""

            data = {
                'pr_id': pr.id,
                'pr_number': pr.pr_number,
                'owner_name': owner_name,
                'owner_department': owner_department,
                'item_count': item_count
            }

            notification = NotificationService.create_notification(
                recipient_id=approver_user_id,
                recipient_type='user',
                notification_type='pr_pending_approval',
                title=title,
                message=message,
                related_type='pr',
                related_id=pr.id,
                data=data
            )

            # 发送企业微信通知
            if approver.wework_user_id:
                try:
                    from services.wework_service import get_wework_service
                    from services.wework_message import build_pr_approval_markdown

                    wework = get_wework_service()
                    if wework.is_enabled():
                        # 使用Markdown格式发送
                        markdown_content = build_pr_approval_markdown(pr)
                        success = wework.send_markdown_message(
                            user_ids=[approver.wework_user_id],
                            content=markdown_content
                        )

                        if success:
                            logger.info(f"✅ 企业微信通知已发送 - PR#{pr.id} -> {approver.username}")
                        else:
                            logger.warning(f"⚠️  企业微信通知发送失败 - PR#{pr.id}")
                    else:
                        logger.warning("⚠️  企业微信服务未启用")

                except Exception as e:
                    logger.error(f"❌ 发送企业微信通知失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                logger.info(f"ℹ️  用户{approver.username}未绑定企业微信，跳过企业微信通知")

            # 发送企业微信群机器人通知
            try:
                from services.wework_robot_service import get_robot_service
                robot = get_robot_service()
                if robot.is_enabled():
                    # 构建审批人列表用于@提醒
                    mentioned_list = []
                    if approver.wework_user_id:
                        mentioned_list.append(approver.wework_user_id)
                    
                    # 发送群机器人通知
                    robot.send_pr_approval_notification(pr, approver.username, mentioned_list)
                    logger.info(f"✅ 企业微信群机器人通知已发送 - PR#{pr.id}")
            except Exception as e:
                logger.error(f"❌ 发送企业微信群机器人通知失败: {e}")
                import traceback
                traceback.print_exc()

            return notification

        except Exception as e:
            logger.error(f"❌ 创建PR审批通知失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def notify_pr_approved_to_owner(pr):
        """
        通知申请人：PR已审批通过（含企业微信通知）

        Args:
            pr: PR对象
        """
        try:
            from utils.auth import get_user_by_id
            owner = get_user_by_id(pr.owner_id)
            if not owner:
                return None

            title = f"【审批通过】{pr.pr_number}"
            message = f"""您的采购申请已审批通过：

📋 申请单号：{pr.pr_number}
✅ 审批状态：已通过
📅 审批时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

系统将自动创建询价单。"""

            notification = NotificationService.create_notification(
                recipient_id=pr.owner_id,
                recipient_type='user',
                notification_type='pr_approved',
                title=title,
                message=message,
                related_type='pr',
                related_id=pr.id
            )

            # 发送企业微信通知
            if owner.wework_user_id:
                try:
                    from services.wework_service import get_wework_service
                    from services.wework_message import WeWorkMessageBuilder

                    wework = get_wework_service()
                    if wework.is_enabled():
                        card_data = WeWorkMessageBuilder.build_pr_approved_notification(pr)
                        success = wework.send_textcard_message(
                            user_ids=[owner.wework_user_id],
                            title=card_data['title'],
                            description=card_data['description'],
                            url=card_data['url'],
                            btntxt=card_data['btntxt']
                        )
                        if success:
                            logger.info(f"✅ 企业微信审批通过通知已发送 - PR#{pr.id}")
                except Exception as e:
                    logger.error(f"❌ 发送企业微信通知失败: {e}")

            return notification

        except Exception as e:
            logger.error(f"❌ 创建PR审批通过通知失败: {e}")
            return None
            
            # 发送企业微信群机器人通知
            try:
                from services.wework_robot_service import get_robot_service
                robot = get_robot_service()
                if robot.is_enabled():
                    robot.send_pr_approved_notification(pr)
                    logger.info(f"✅ 企业微信群机器人审批通过通知已发送 - PR#{pr.id}")
            except Exception as e:
                logger.error(f"❌ 发送企业微信群机器人通知失败: {e}")

    @staticmethod
    def notify_pr_rejected_to_owner(pr, reason: str = ""):
        """
        通知申请人：PR已驳回（含企业微信通知）

        Args:
            pr: PR对象
            reason: 驳回原因
        """
        try:
            from utils.auth import get_user_by_id
            owner = get_user_by_id(pr.owner_id)
            if not owner:
                return None

            title = f"【已驳回】{pr.pr_number}"
            message = f"""您的采购申请已被驳回：

📋 申请单号：{pr.pr_number}
❌ 审批状态：已驳回
📅 驳回时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"""

            if reason:
                message += f"\n📝 驳回原因：{reason}"

            notification = NotificationService.create_notification(
                recipient_id=pr.owner_id,
                recipient_type='user',
                notification_type='pr_rejected',
                title=title,
                message=message,
                related_type='pr',
                related_id=pr.id,
                data={'reason': reason}
            )

            # 发送企业微信通知
            if owner.wework_user_id:
                try:
                    from services.wework_service import get_wework_service
                    from services.wework_message import WeWorkMessageBuilder

                    wework = get_wework_service()
                    if wework.is_enabled():
                        card_data = WeWorkMessageBuilder.build_pr_rejected_notification(pr, reason)
                        success = wework.send_textcard_message(
                            user_ids=[owner.wework_user_id],
                            title=card_data['title'],
                            description=card_data['description'],
                            url=card_data['url'],
                            btntxt=card_data['btntxt']
                        )
                        if success:
                            logger.info(f"✅ 企业微信驳回通知已发送 - PR#{pr.id}")
                except Exception as e:
                    logger.error(f"❌ 发送企业微信通知失败: {e}")

            return notification

        except Exception as e:
            logger.error(f"❌ 创建PR驳回通知失败: {e}")
            return None
            
            # 发送企业微信群机器人通知
            try:
                from services.wework_robot_service import get_robot_service
                robot = get_robot_service()
                if robot.is_enabled():
                    robot.send_pr_rejected_notification(pr, reason)
                    logger.info(f"✅ 企业微信群机器人驳回通知已发送 - PR#{pr.id}")
            except Exception as e:
                logger.error(f"❌ 发送企业微信群机器人通知失败: {e}")
