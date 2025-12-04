# -*- coding: utf-8 -*-
"""
企业微信群机器人服务
WeWork Group Robot Service - 用于向企业微信群发送机器人消息
"""
import os
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class WeWorkRobotService:
    """企业微信群机器人服务 - 通过webhook发送消息到企业微信群"""

    def __init__(self):
        """初始化机器人服务"""
        self.webhook_url = os.getenv('WEWORK_ROBOT_WEBHOOK', '')
        self.enabled = bool(self.webhook_url and 'YOUR_KEY_HERE' not in self.webhook_url)

        if self.enabled:
            logger.info('✅ 企业微信群机器人服务已启用')
        else:
            logger.warning('⚠️  企业微信群机器人服务未配置或已禁用')

    def is_enabled(self) -> bool:
        """检查服务是否已启用"""
        return self.enabled

    def send_text_message(self, content: str, mentioned_list: Optional[list] = None,
                         mentioned_mobile_list: Optional[list] = None) -> bool:
        """
        发送文本消息

        Args:
            content: 消息内容
            mentioned_list: @的企业微信用户ID列表，@all表示提醒所有人
            mentioned_mobile_list: @的手机号列表

        Returns:
            bool: 是否发送成功
        """
        if not self.enabled:
            logger.warning('企业微信群机器人服务未启用，跳过发送')
            return False

        try:
            payload = {
                'msgtype': 'text',
                'text': {
                    'content': content
                }
            }

            # 添加@提醒
            if mentioned_list or mentioned_mobile_list:
                payload['text']['mentioned_list'] = mentioned_list or []
                payload['text']['mentioned_mobile_list'] = mentioned_mobile_list or []

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            result = response.json()
            if result.get('errcode') == 0:
                logger.info(f'✅ 企业微信群机器人消息发送成功')
                return True
            else:
                logger.error(f'❌ 企业微信群机器人消息发送失败: {result.get("errmsg")}')
                return False

        except Exception as e:
            logger.error(f'❌ 发送企业微信群机器人消息异常: {e}')
            return False

    def send_markdown_message(self, content: str) -> bool:
        """
        发送Markdown格式消息

        Args:
            content: Markdown格式的消息内容

        Returns:
            bool: 是否发送成功
        """
        if not self.enabled:
            logger.warning('企业微信群机器人服务未启用，跳过发送')
            return False

        try:
            payload = {
                'msgtype': 'markdown',
                'markdown': {
                    'content': content
                }
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            result = response.json()
            if result.get('errcode') == 0:
                logger.info(f'✅ 企业微信群机器人Markdown消息发送成功')
                return True
            else:
                logger.error(f'❌ 企业微信群机器人Markdown消息发送失败: {result.get("errmsg")}')
                return False

        except Exception as e:
            logger.error(f'❌ 发送企业微信群机器人Markdown消息异常: {e}')
            return False

    def send_pr_approval_notification(self, pr, approver_name: str,
                                     mentioned_list: Optional[list] = None) -> bool:
        """
        发送PR待审批通知

        Args:
            pr: PR对象
            approver_name: 审批人姓名
            mentioned_list: @的企业微信用户ID列表

        Returns:
            bool: 是否发送成功
        """
        # 构建消息内容
        owner_name = pr.owner.username if hasattr(pr, 'owner') and pr.owner else '未知'
        owner_department = pr.owner.department if hasattr(pr, 'owner') and pr.owner else '未知'
        item_count = len(pr.items) if hasattr(pr, 'items') else 0

        # 使用Markdown格式
        content = f"""## 📋 【待审批】采购申请通知

**申请单号：** {pr.pr_number}
**申请人：** {owner_name}
**部门：** {owner_department}
**物料数量：** {item_count} 项
**审批人：** {approver_name}

> 请及时登录系统审批

[点击查看详情](http://61.145.212.28:5000/pr/{pr.id})
"""

        return self.send_markdown_message(content)

    def send_pr_approved_notification(self, pr) -> bool:
        """
        发送PR审批通过通知

        Args:
            pr: PR对象

        Returns:
            bool: 是否发送成功
        """
        owner_name = pr.owner.username if hasattr(pr, 'owner') and pr.owner else '未知'

        content = f"""## ✅ 【审批通过】采购申请通知

**申请单号：** {pr.pr_number}
**申请人：** {owner_name}
**审批状态：** 已通过

> 系统将自动创建询价单

[查看详情](http://61.145.212.28:5000/pr/{pr.id})
"""

        # @申请人
        mentioned_list = []
        if hasattr(pr, 'owner') and pr.owner and pr.owner.wework_user_id:
            mentioned_list = [pr.owner.wework_user_id]

        if mentioned_list:
            # 如果有@用户，使用文本消息
            text_content = f"💬 采购申请审批通知\n\n"                           f"📋 申请单号：{pr.pr_number}\n"                           f"👤 申请人：{owner_name}\n"                           f"✅ 审批状态：已通过\n\n"                           f"系统将自动创建询价单\n"                           f"查看详情：http://61.145.212.28:5000/pr/{pr.id}"
            return self.send_text_message(text_content, mentioned_list=mentioned_list)
        else:
            return self.send_markdown_message(content)

    def send_pr_rejected_notification(self, pr, reason: str = '') -> bool:
        """
        发送PR驳回通知

        Args:
            pr: PR对象
            reason: 驳回原因

        Returns:
            bool: 是否发送成功
        """
        owner_name = pr.owner.username if hasattr(pr, 'owner') and pr.owner else '未知'

        reason_text = f"\n**驳回原因：** {reason}" if reason else ''

        content = f"""## ❌ 【已驳回】采购申请通知

**申请单号：** {pr.pr_number}
**申请人：** {owner_name}
**审批状态：** 已驳回{reason_text}

> 请根据驳回原因修改后重新提交

[查看详情](http://61.145.212.28:5000/pr/{pr.id})
"""

        # @申请人
        mentioned_list = []
        if hasattr(pr, 'owner') and pr.owner and pr.owner.wework_user_id:
            mentioned_list = [pr.owner.wework_user_id]

        if mentioned_list:
            # 如果有@用户，使用文本消息
            text_content = f"💬 采购申请审批通知\n\n"                           f"📋 申请单号：{pr.pr_number}\n"                           f"👤 申请人：{owner_name}\n"                           f"❌ 审批状态：已驳回\n"
            if reason:
                text_content += f"📝 驳回原因：{reason}\n"
            text_content += f"\n请修改后重新提交\n"                            f"查看详情：http://61.145.212.28:5000/pr/{pr.id}"
            return self.send_text_message(text_content, mentioned_list=mentioned_list)
        else:
            return self.send_markdown_message(content)


# 全局单例
_robot_service = None


def get_robot_service() -> WeWorkRobotService:
    """获取企业微信群机器人服务单例"""
    global _robot_service
    if _robot_service is None:
        _robot_service = WeWorkRobotService()
    return _robot_service
