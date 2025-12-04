# -*- coding: utf-8 -*-
"""
企业微信服务
WeWork Service - 企业微信消息推送、OAuth认证等功能
"""
import os
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class WeWorkService:
    """企业微信服务类"""

    def __init__(self):
        self.corp_id = os.getenv('WEWORK_CORP_ID', 'ww7f7bb9e8fc040434')
        self.agent_id = os.getenv('WEWORK_AGENT_ID', '')  # 需要配置
        self.secret = os.getenv('WEWORK_SECRET', 'e6zeeDUO7Jp1BB-T8Nu-l0Kmn84lRcpHUgig8eff8uQ')

        # Access Token缓存
        self._access_token = None
        self._token_expires_at = None

        # 企业微信API基础URL
        self.base_url = 'https://qyapi.weixin.qq.com/cgi-bin'

        if not self.agent_id:
            logger.warning("⚠️  WEWORK_AGENT_ID未配置，企业微信功能不可用")

        logger.info(f"✅ WeWorkService初始化 - CorpID: {self.corp_id}")

    def is_enabled(self) -> bool:
        """检查企业微信服务是否已启用"""
        return bool(self.corp_id and self.agent_id and self.secret)

    def get_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        获取Access Token（自动缓存和刷新）

        Args:
            force_refresh: 强制刷新token

        Returns:
            access_token或None
        """
        # 如果token有效且未强制刷新，直接返回缓存
        if not force_refresh and self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token

        # 请求新token
        url = f"{self.base_url}/gettoken"
        params = {
            'corpid': self.corp_id,
            'corpsecret': self.secret
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                self._access_token = data['access_token']
                expires_in = data.get('expires_in', 7200)
                # 提前5分钟过期，避免边界问题
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

                logger.info(f"✅ 获取企业微信Access Token成功，有效期{expires_in}秒")
                return self._access_token
            else:
                logger.error(f"❌ 获取Access Token失败: {data.get('errmsg')}")
                return None

        except Exception as e:
            logger.error(f"❌ 获取Access Token异常: {e}")
            return None

    def send_text_message(self, user_ids: List[str], content: str,
                          safe: int = 0) -> bool:
        """
        发送文本消息

        Args:
            user_ids: 用户ID列表（企业微信UserID）
            content: 消息内容
            safe: 是否保密消息（0否1是）

        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            logger.warning("⚠️  企业微信服务未启用，跳过发送")
            return False

        access_token = self.get_access_token()
        if not access_token:
            return False

        url = f"{self.base_url}/message/send?access_token={access_token}"

        payload = {
            'touser': '|'.join(user_ids),
            'msgtype': 'text',
            'agentid': int(self.agent_id),
            'text': {
                'content': content
            },
            'safe': safe
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                logger.info(f"✅ 企业微信消息发送成功 -> {len(user_ids)}人")
                return True
            else:
                logger.error(f"❌ 企业微信消息发送失败: {data.get('errmsg')}")
                return False

        except Exception as e:
            logger.error(f"❌ 企业微信消息发送异常: {e}")
            return False

    def send_textcard_message(self, user_ids: List[str], title: str,
                              description: str, url: str,
                              btntxt: str = "详情") -> bool:
        """
        发送文本卡片消息

        Args:
            user_ids: 用户ID列表
            title: 卡片标题
            description: 卡片描述
            url: 点击跳转URL
            btntxt: 按钮文字

        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            logger.warning("⚠️  企业微信服务未启用，跳过发送")
            return False

        access_token = self.get_access_token()
        if not access_token:
            return False

        url_api = f"{self.base_url}/message/send?access_token={access_token}"

        payload = {
            'touser': '|'.join(user_ids),
            'msgtype': 'textcard',
            'agentid': int(self.agent_id),
            'textcard': {
                'title': title,
                'description': description,
                'url': url,
                'btntxt': btntxt
            }
        }

        try:
            response = requests.post(url_api, json=payload, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                logger.info(f"✅ 企业微信卡片消息发送成功 -> {len(user_ids)}人")
                return True
            else:
                logger.error(f"❌ 企业微信卡片消息发送失败: {data.get('errmsg')}")
                return False

        except Exception as e:
            logger.error(f"❌ 企业微信卡片消息发送异常: {e}")
            return False

    def send_markdown_message(self, user_ids: List[str], content: str) -> bool:
        """
        发送Markdown消息

        Args:
            user_ids: 用户ID列表
            content: Markdown内容

        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            logger.warning("⚠️  企业微信服务未启用，跳过发送")
            return False

        access_token = self.get_access_token()
        if not access_token:
            return False

        url = f"{self.base_url}/message/send?access_token={access_token}"

        payload = {
            'touser': '|'.join(user_ids),
            'msgtype': 'markdown',
            'agentid': int(self.agent_id),
            'markdown': {
                'content': content
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                logger.info(f"✅ 企业微信Markdown消息发送成功 -> {len(user_ids)}人")
                return True
            else:
                logger.error(f"❌ 企业微信Markdown消息发送失败: {data.get('errmsg')}")
                return False

        except Exception as e:
            logger.error(f"❌ 企业微信Markdown消息发送异常: {e}")
            return False

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        获取用户详细信息

        Args:
            user_id: 企业微信UserID

        Returns:
            用户信息字典或None
        """
        if not self.is_enabled():
            return None

        access_token = self.get_access_token()
        if not access_token:
            return None

        url = f"{self.base_url}/user/get"
        params = {
            'access_token': access_token,
            'userid': user_id
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                return data
            else:
                logger.error(f"❌ 获取用户信息失败: {data.get('errmsg')}")
                return None

        except Exception as e:
            logger.error(f"❌ 获取用户信息异常: {e}")
            return None

    def send_template_card(self, user_ids: List[str], card_data: Dict) -> bool:
        """
        发送模板卡片消息（更丰富的交互）

        Args:
            user_ids: 用户ID列表
            card_data: 卡片数据配置

        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            logger.warning("⚠️  企业微信服务未启用，跳过发送")
            return False

        access_token = self.get_access_token()
        if not access_token:
            return False

        url = f"{self.base_url}/message/send?access_token={access_token}"

        payload = {
            'touser': '|'.join(user_ids),
            'msgtype': 'template_card',
            'agentid': int(self.agent_id),
            'template_card': card_data
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                logger.info(f"✅ 企业微信模板卡片发送成功 -> {len(user_ids)}人")
                return True
            else:
                logger.error(f"❌ 企业微信模板卡片发送失败: {data.get('errmsg')}")
                return False

        except Exception as e:
            logger.error(f"❌ 企业微信模板卡片发送异常: {e}")
            return False


# 全局单例
_wework_service = None

def get_wework_service() -> WeWorkService:
    """获取企业微信服务单例"""
    global _wework_service
    if _wework_service is None:
        _wework_service = WeWorkService()
    return _wework_service
