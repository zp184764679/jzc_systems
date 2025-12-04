# -*- coding: utf-8 -*-
"""
企业微信消息模板
WeWork Message Templates
"""
import os
from typing import Dict, List
from datetime import datetime


class WeWorkMessageBuilder:
    """企业微信消息构建器"""

    @staticmethod
    def get_h5_domain() -> str:
        """获取H5页面域名"""
        return os.getenv('WEWORK_H5_DOMAIN', 'http://localhost:3000')

    @staticmethod
    def build_pr_approval_notification(pr, approver_name: str = "") -> Dict:
        """
        构建PR审批通知消息

        Args:
            pr: PR对象
            approver_name: 审批人姓名（可选）

        Returns:
            消息数据字典
        """
        # 计算总金额（如果有）
        total_amount = 0
        item_count = len(pr.items) if hasattr(pr, 'items') else 0

        # 如果有关联的RFQ，可以从RFQ获取报价金额
        # 这里简化处理

        # 构建描述文本
        description = f"""
<div class="gray">申请人：{pr.owner_name or '未知'}</div>
<div class="gray">部门：{pr.owner_department or '未知'}</div>
<div class="gray">申请时间：{pr.created_at.strftime('%Y-%m-%d %H:%M') if pr.created_at else '-'}</div>
<div class="normal">物料数量：{item_count} 项</div>
<div class="highlight">状态：待审批</div>
"""

        # H5审批页面URL
        h5_url = f"{WeWorkMessageBuilder.get_h5_domain()}/mobile/approval/pr/{pr.id}"

        return {
            'type': 'textcard',
            'title': f'【待审批】采购申请 {pr.pr_number}',
            'description': description,
            'url': h5_url,
            'btntxt': '立即审批'
        }

    @staticmethod
    def build_pr_approval_markdown(pr) -> str:
        """
        构建PR审批通知（Markdown格式）

        Args:
            pr: PR对象

        Returns:
            Markdown内容
        """
        item_count = len(pr.items) if hasattr(pr, 'items') else 0

        # 物料列表（最多显示5项）
        items_text = ""
        if hasattr(pr, 'items') and pr.items:
            for i, item in enumerate(pr.items[:5]):
                items_text += f"\n> {i+1}. {item.name} x {item.qty}"
            if len(pr.items) > 5:
                items_text += f"\n> ... 还有{len(pr.items)-5}项"

        owner_name = pr.owner.username if hasattr(pr, 'owner') and pr.owner else '未知'
        owner_department = pr.owner.department if hasattr(pr, 'owner') and pr.owner else '未知'

        markdown = f"""## 【待审批】采购申请

**申请单号**: {pr.pr_number}
**申请人**: {owner_name}
**部门**: {owner_department}
**申请时间**: {pr.created_at.strftime('%Y-%m-%d %H:%M') if pr.created_at else '-'}
**物料数量**: {item_count} 项

**物料清单**:{items_text}

> **状态**: <font color="warning">待审批</font>
>
> [点击查看详情并审批]({WeWorkMessageBuilder.get_h5_domain()}/mobile/approval/pr/{pr.id})
"""
        return markdown

    @staticmethod
    def build_pr_approved_notification(pr) -> Dict:
        """构建PR审批通过通知"""
        description = f"""
<div class="normal">您的采购申请已审批通过</div>
<div class="gray">申请单号：{pr.pr_number}</div>
<div class="gray">审批时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
<div class="highlight">系统将自动创建询价单</div>
"""

        return {
            'type': 'textcard',
            'title': f'【审批通过】{pr.pr_number}',
            'description': description,
            'url': f"{WeWorkMessageBuilder.get_h5_domain()}/pr/{pr.id}",
            'btntxt': '查看详情'
        }

    @staticmethod
    def build_pr_rejected_notification(pr, reason: str = "") -> Dict:
        """构建PR驳回通知"""
        description = f"""
<div class="normal">您的采购申请已被驳回</div>
<div class="gray">申请单号：{pr.pr_number}</div>
<div class="gray">驳回时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
"""
        if reason:
            description += f'<div class="highlight">驳回原因：{reason}</div>'

        return {
            'type': 'textcard',
            'title': f'【已驳回】{pr.pr_number}',
            'description': description,
            'url': f"{WeWorkMessageBuilder.get_h5_domain()}/pr/{pr.id}",
            'btntxt': '查看详情'
        }

    @staticmethod
    def build_po_created_notification(po, supplier_name: str = "") -> Dict:
        """
        构建采购订单创建通知

        Args:
            po: PurchaseOrder对象
            supplier_name: 供应商名称

        Returns:
            消息数据字典
        """
        # 计算剩余天数
        days_remaining = 7
        if po.invoice_due_date:
            delta = po.invoice_due_date - datetime.now()
            days_remaining = max(0, delta.days)

        description = f"""
<div class="normal">您有新的采购订单</div>
<div class="gray">订单号：{po.po_number}</div>
<div class="gray">订单金额：¥{po.total_price:,.2f}</div>
<div class="gray">交货期：{po.lead_time} 天</div>
<div class="highlight">请在 {days_remaining} 天内上传发票</div>
"""

        # 供应商H5页面URL（如果供应商也使用企业微信）
        h5_url = f"{WeWorkMessageBuilder.get_h5_domain()}/mobile/po/{po.id}"

        return {
            'type': 'textcard',
            'title': f'【新订单】{po.po_number}',
            'description': description,
            'url': h5_url,
            'btntxt': '查看详情'
        }

    @staticmethod
    def build_invoice_approved_notification(invoice) -> Dict:
        """构建发票审批通过通知"""
        description = f"""
<div class="normal">您的发票已审批通过</div>
<div class="gray">发票号：{invoice.invoice_number}</div>
<div class="gray">发票金额：¥{invoice.amount:,.2f}</div>
<div class="gray">审批时间：{invoice.approved_at.strftime('%Y-%m-%d %H:%M') if invoice.approved_at else '-'}</div>
<div class="highlight">财务将按付款条件处理</div>
"""

        return {
            'type': 'textcard',
            'title': f'【发票已批准】{invoice.invoice_number}',
            'description': description,
            'url': f"{WeWorkMessageBuilder.get_h5_domain()}/mobile/invoice/{invoice.id}",
            'btntxt': '查看详情'
        }

    @staticmethod
    def build_invoice_rejected_notification(invoice, reason: str = "") -> Dict:
        """构建发票驳回通知"""
        description = f"""
<div class="normal">您的发票审批未通过</div>
<div class="gray">发票号：{invoice.invoice_number}</div>
<div class="gray">发票金额：¥{invoice.amount:,.2f}</div>
"""
        if reason:
            description += f'<div class="highlight">驳回原因：{reason}</div>'

        return {
            'type': 'textcard',
            'title': f'【发票已驳回】{invoice.invoice_number}',
            'description': description,
            'url': f"{WeWorkMessageBuilder.get_h5_domain()}/mobile/invoice/{invoice.id}",
            'btntxt': '查看详情'
        }

    @staticmethod
    def build_template_card_pr_approval(pr) -> Dict:
        """
        构建PR审批模板卡片（更丰富的交互）

        Args:
            pr: PR对象

        Returns:
            模板卡片数据
        """
        item_count = len(pr.items) if hasattr(pr, 'items') else 0

        # 构建主要信息字段
        main_title = {
            "title": "采购申请待审批",
            "desc": pr.pr_number
        }

        # 强调内容
        emphasis_content = {
            "title": f"{item_count} 项物料",
            "desc": f"申请人：{pr.owner_name or '未知'}"
        }

        # 关键数据
        horizontal_content_list = [
            {
                "keyname": "申请部门",
                "value": pr.owner_department or '未知'
            },
            {
                "keyname": "申请时间",
                "value": pr.created_at.strftime('%m-%d %H:%M') if pr.created_at else '-'
            }
        ]

        # 按钮（跳转到H5页面）
        jump_list = [
            {
                "type": 1,  # 跳转类型
                "title": "立即审批",
                "url": f"{WeWorkMessageBuilder.get_h5_domain()}/mobile/approval/pr/{pr.id}"
            }
        ]

        # 完整的模板卡片数据
        card_data = {
            "card_type": "text_notice",  # 文本通知型
            "source": {
                "icon_url": "https://example.com/icon.png",  # 可选：应用图标
                "desc": "采购系统"
            },
            "main_title": main_title,
            "emphasis_content": emphasis_content,
            "horizontal_content_list": horizontal_content_list,
            "jump_list": jump_list,
            "card_action": {
                "type": 1,
                "url": f"{WeWorkMessageBuilder.get_h5_domain()}/mobile/approval/pr/{pr.id}"
            }
        }

        return card_data


# 便捷方法
def build_pr_approval_card(pr, approver_name: str = "") -> Dict:
    """构建PR审批通知卡片（快捷方法）"""
    return WeWorkMessageBuilder.build_pr_approval_notification(pr, approver_name)


def build_pr_approval_markdown(pr) -> str:
    """构建PR审批Markdown消息（快捷方法）"""
    return WeWorkMessageBuilder.build_pr_approval_markdown(pr)


def build_po_created_card(po, supplier_name: str = "") -> Dict:
    """构建采购订单通知卡片（快捷方法）"""
    return WeWorkMessageBuilder.build_po_created_notification(po, supplier_name)
