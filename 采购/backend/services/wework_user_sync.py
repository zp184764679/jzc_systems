# -*- coding: utf-8 -*-
"""
企业微信用户信息同步服务
支持双向同步：系统 ↔ 企业微信
"""
import logging
from typing import Dict, Optional, List
from services.wework_service import get_wework_service

logger = logging.getLogger(__name__)


class WeWorkUserSyncService:
    """企业微信用户信息同步服务"""

    def __init__(self):
        self.wework = get_wework_service()

    def get_user_detail(self, user_id: str) -> Optional[Dict]:
        """
        从企业微信获取用户详细信息

        Args:
            user_id: 企业微信UserID

        Returns:
            {
                'userid': 'zhangsan',
                'name': '张三',
                'department': [1, 2],  # 部门ID列表
                'main_department': 1,  # 主部门ID
                'mobile': '13800138000',
                'email': 'zhangsan@company.com',
                'position': '产品经理',
                'avatar': 'http://...'
            }
        """
        if not self.wework.is_enabled():
            logger.warning("⚠️  企业微信服务未启用")
            return None

        try:
            import requests

            url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
            params = {
                'access_token': self.wework.get_access_token(),
                'userid': user_id
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                logger.info(f"✅ 获取企业微信用户信息成功: {user_id}")
                return {
                    'userid': data.get('userid'),
                    'name': data.get('name'),
                    'department': data.get('department', []),
                    'main_department': data.get('main_department'),
                    'mobile': data.get('mobile', ''),
                    'email': data.get('email', ''),
                    'position': data.get('position', ''),
                    'avatar': data.get('avatar', ''),
                    'status': data.get('status', 1)  # 1=激活, 2=禁用, 4=未激活
                }
            else:
                logger.error(f"❌ 获取企业微信用户信息失败: {data.get('errmsg')}")
                return None

        except Exception as e:
            logger.error(f"❌ 获取企业微信用户信息异常: {e}")
            return None

    def get_department_list(self) -> List[Dict]:
        """
        获取企业微信部门列表

        Returns:
            [
                {
                    'id': 1,
                    'name': '研发部',
                    'parentid': 0,
                    'order': 1
                }
            ]
        """
        if not self.wework.is_enabled():
            return []

        try:
            import requests

            url = "https://qyapi.weixin.qq.com/cgi-bin/department/list"
            params = {
                'access_token': self.wework.get_access_token()
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('errcode') == 0:
                logger.info(f"✅ 获取企业微信部门列表成功，共{len(data.get('department', []))}个部门")
                return data.get('department', [])
            else:
                logger.error(f"❌ 获取企业微信部门列表失败: {data.get('errmsg')}")
                return []

        except Exception as e:
            logger.error(f"❌ 获取企业微信部门列表异常: {e}")
            return []

    def update_user_department_to_wework(self, user_id: str, department_name: str) -> bool:
        """
        将系统中的部门信息同步到企业微信

        Args:
            user_id: 企业微信UserID
            department_name: 系统中的部门名称（如："研发部"）

        Returns:
            是否同步成功
        """
        if not self.wework.is_enabled():
            logger.warning("⚠️  企业微信服务未启用，跳过同步")
            return False

        try:
            # 1. 获取企业微信部门列表
            departments = self.get_department_list()
            if not departments:
                logger.warning("⚠️  无法获取企业微信部门列表")
                return False

            # 2. 查找匹配的部门ID
            department_id = None
            for dept in departments:
                if dept['name'] == department_name:
                    department_id = dept['id']
                    break

            if not department_id:
                logger.warning(f"⚠️  企业微信中未找到部门: {department_name}")
                logger.info(f"💡 可选的部门: {[d['name'] for d in departments]}")
                return False

            # 3. 更新用户部门
            import requests

            url = "https://qyapi.weixin.qq.com/cgi-bin/user/update"
            data = {
                'access_token': self.wework.get_access_token()
            }
            body = {
                'userid': user_id,
                'department': [department_id],
                'main_department': department_id
            }

            response = requests.post(url, params=data, json=body, timeout=10)
            result = response.json()

            if result.get('errcode') == 0:
                logger.info(f"✅ 同步部门到企业微信成功: {user_id} -> {department_name}")
                return True
            else:
                error_msg = result.get('errmsg')
                logger.error(f"❌ 同步部门到企业微信失败: {error_msg}")

                # 权限不足提示
                if result.get('errcode') == 60011:
                    logger.warning("⚠️  权限不足：应用需要开启'通讯录管理'权限")

                return False

        except Exception as e:
            logger.error(f"❌ 同步部门到企业微信异常: {e}")
            return False

    def get_department_mapping(self) -> Dict[str, int]:
        """
        获取系统部门到企业微信部门的映射

        Returns:
            {
                '研发部': 1,
                '采购部': 2,
                ...
            }
        """
        departments = self.get_department_list()
        return {dept['name']: dept['id'] for dept in departments}


def sync_user_from_wework(wework_user_id: str) -> Optional[Dict]:
    """
    从企业微信同步用户信息（用于扫码登录）

    Args:
        wework_user_id: 企业微信UserID

    Returns:
        用户信息字典，供系统创建/更新账号使用
    """
    service = WeWorkUserSyncService()
    user_detail = service.get_user_detail(wework_user_id)

    if not user_detail:
        return None

    # 获取部门名称（默认取主部门）
    department_name = "未知"
    if user_detail.get('main_department'):
        departments = service.get_department_list()
        for dept in departments:
            if dept['id'] == user_detail['main_department']:
                department_name = dept['name']
                break

    return {
        'wework_user_id': user_detail['userid'],
        'username': user_detail['name'],
        'department': department_name,
        'phone': user_detail.get('mobile', ''),
        'email': user_detail.get('email', ''),
        'position': user_detail.get('position', ''),
        'avatar': user_detail.get('avatar', ''),
        'status': user_detail.get('status', 1)
    }


def sync_user_to_wework(user_id: str, department_name: str) -> bool:
    """
    将系统用户信息同步到企业微信

    Args:
        user_id: 企业微信UserID
        department_name: 系统中的部门名称

    Returns:
        是否同步成功
    """
    service = WeWorkUserSyncService()
    return service.update_user_department_to_wework(user_id, department_name)


# 使用示例
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from app import app

    with app.app_context():
        # 示例1：从企业微信获取用户信息
        print("\n=== 测试1：从企业微信获取用户信息 ===")
        user_info = sync_user_from_wework('ZhouPeng')
        if user_info:
            print(f"✅ 获取成功:")
            for key, value in user_info.items():
                print(f"   {key}: {value}")
        else:
            print("❌ 获取失败")

        # 示例2：同步部门到企业微信
        print("\n=== 测试2：同步部门到企业微信 ===")
        success = sync_user_to_wework('ZhouPeng', '研发部')
        if success:
            print("✅ 同步成功")
        else:
            print("❌ 同步失败")

        # 示例3：获取部门映射
        print("\n=== 测试3：获取部门映射 ===")
        service = WeWorkUserSyncService()
        mapping = service.get_department_mapping()
        print(f"企业微信部门列表:")
        for name, dept_id in mapping.items():
            print(f"   {name} (ID: {dept_id})")
