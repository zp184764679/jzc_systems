# -*- coding: utf-8 -*-
"""
微信服务号API服务
用于给外部供应商发送普通微信消息
"""
import os
import time
import logging
import requests
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class WeChatOfficialService:
    """微信服务号API服务"""

    def __init__(self):
        self.app_id = os.getenv('WECHAT_APPID', '')
        self.app_secret = os.getenv('WECHAT_APPSECRET', '')
        self._access_token = None
        self._token_expires_at = 0

        if self.app_id and self.app_secret:
            logger.info(f"✅ 微信服务号初始化 - AppID: {self.app_id}")
        else:
            logger.warning("⚠️  微信服务号未配置 WECHAT_APPID 或 WECHAT_APPSECRET")

    def is_enabled(self) -> bool:
        """检查微信服务号是否已配置"""
        return bool(self.app_id and self.app_secret)

    def get_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        获取Access Token（带缓存）

        Args:
            force_refresh: 是否强制刷新

        Returns:
            Access Token字符串，失败返回None
        """
        # 检查缓存（提前5分钟刷新）
        if not force_refresh and self._access_token and time.time() < (self._token_expires_at - 300):
            return self._access_token

        try:
            url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {
                'grant_type': 'client_credential',
                'appid': self.app_id,
                'secret': self.app_secret
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'access_token' in data:
                self._access_token = data['access_token']
                expires_in = data.get('expires_in', 7200)
                self._token_expires_at = time.time() + expires_in

                logger.info(f"✅ 获取微信服务号Access Token成功，有效期{expires_in}秒")
                return self._access_token
            else:
                error_code = data.get('errcode')
                error_msg = data.get('errmsg')
                logger.error(f"❌ 获取微信服务号Access Token失败: [{error_code}] {error_msg}")
                return None

        except Exception as e:
            logger.error(f"❌ 获取微信服务号Access Token异常: {e}")
            return None

    def send_template_message(self, openid: str, template_id: str, data: Dict, url: str = "") -> bool:
        """
        发送模板消息

        Args:
            openid: 用户OpenID
            template_id: 模板ID
            data: 模板数据 {"first": {"value": "xx"}, "keyword1": {"value": "xx"}}
            url: 点击跳转链接

        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            logger.warning("⚠️  微信服务号未启用，跳过模板消息发送")
            return False

        try:
            access_token = self.get_access_token()
            if not access_token:
                return False

            api_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"

            payload = {
                "touser": openid,
                "template_id": template_id,
                "url": url,
                "data": data
            }

            response = requests.post(api_url, json=payload, timeout=10)
            result = response.json()

            if result.get('errcode') == 0:
                logger.info(f"✅ 微信模板消息发送成功 - OpenID: {openid[:10]}...")
                return True
            else:
                logger.error(f"❌ 微信模板消息发送失败: [{result.get('errcode')}] {result.get('errmsg')}")
                return False

        except Exception as e:
            logger.error(f"❌ 发送微信模板消息异常: {e}")
            return False

    def send_text_message(self, openid: str, content: str) -> bool:
        """
        发送文本消息（客服消息，需要用户48小时内互动过）

        Args:
            openid: 用户OpenID
            content: 文本内容

        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            logger.warning("⚠️  微信服务号未启用，跳过客服消息发送")
            return False

        try:
            access_token = self.get_access_token()
            if not access_token:
                return False

            api_url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"

            payload = {
                "touser": openid,
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }

            response = requests.post(api_url, json=payload, timeout=10)
            result = response.json()

            if result.get('errcode') == 0:
                logger.info(f"✅ 微信客服消息发送成功 - OpenID: {openid[:10]}...")
                return True
            else:
                logger.error(f"❌ 微信客服消息发送失败: [{result.get('errcode')}] {result.get('errmsg')}")
                return False

        except Exception as e:
            logger.error(f"❌ 发送微信客服消息异常: {e}")
            return False

    def get_user_info(self, openid: str) -> Optional[Dict]:
        """
        获取用户基本信息

        Args:
            openid: 用户OpenID

        Returns:
            用户信息字典，失败返回None
        """
        if not self.is_enabled():
            return None

        try:
            access_token = self.get_access_token()
            if not access_token:
                return None

            api_url = f"https://api.weixin.qq.com/cgi-bin/user/info"
            params = {
                'access_token': access_token,
                'openid': openid,
                'lang': 'zh_CN'
            }

            response = requests.get(api_url, params=params, timeout=10)
            result = response.json()

            if 'subscribe' in result:
                logger.info(f"✅ 获取微信用户信息成功 - {result.get('nickname', 'Unknown')}")
                return result
            else:
                logger.error(f"❌ 获取微信用户信息失败: {result.get('errmsg')}")
                return None

        except Exception as e:
            logger.error(f"❌ 获取微信用户信息异常: {e}")
            return None


# 全局单例
_wechat_official_service = None


def get_wechat_official_service() -> WeChatOfficialService:
    """获取微信服务号服务实例（单例）"""
    global _wechat_official_service
    if _wechat_official_service is None:
        _wechat_official_service = WeChatOfficialService()
    return _wechat_official_service


# 使用示例
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from app import app

    with app.app_context():
        service = get_wechat_official_service()

        # 测试1：获取Access Token
        print("\n=== 测试1：获取Access Token ===")
        token = service.get_access_token()
        if token:
            print(f"✅ Access Token: {token[:20]}...")
        else:
            print("❌ 获取失败")

        # 测试2：发送模板消息（需要有关注的用户OpenID）
        print("\n=== 测试2：发送模板消息 ===")
        # test_openid = "oXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # 替换为实际OpenID
        # test_template_id = "XXXXXXXXXXXXXXXXXXXXXXXXXXX"  # 替换为实际模板ID
        # success = service.send_template_message(
        #     openid=test_openid,
        #     template_id=test_template_id,
        #     data={
        #         "first": {"value": "您有新的询价单"},
        #         "keyword1": {"value": "RFQ-20250104-001"},
        #         "keyword2": {"value": "铣刀 Φ12"},
        #         "keyword3": {"value": "2025-01-10"},
        #         "remark": {"value": "请及时报价"}
        #     },
        #     url="http://61.145.212.28:3000/supplier/quotes"
        # )
        # print("✅ 发送成功" if success else "❌ 发送失败")
        print("⏳ 需要OpenID和模板ID才能测试")
