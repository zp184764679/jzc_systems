# services/crm_service.py
"""
CRM客户关系管理系统集成服务
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_crm_base_url():
    """获取CRM API基础URL"""
    return os.getenv('CRM_API_BASE_URL', 'http://localhost:8002')


def get_customers(keyword="", page=1, page_size=20):
    """
    从CRM系统获取客户列表

    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量

    Returns:
        dict: 客户列表数据
    """
    try:
        response = requests.get(
            f"{get_crm_base_url()}/api/customers",
            params={
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'CRM系统连接失败: {str(e)}',
            'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
        }


def get_customer_by_id(customer_id):
    """
    根据ID获取客户详情

    Args:
        customer_id: 客户ID

    Returns:
        dict: 客户详情
    """
    try:
        response = requests.get(
            f"{get_crm_base_url()}/api/customers/{customer_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'CRM系统连接失败: {str(e)}'
        }


def get_customer_contacts(customer_id):
    """
    获取客户联系人列表

    Args:
        customer_id: 客户ID

    Returns:
        dict: 联系人列表
    """
    try:
        response = requests.get(
            f"{get_crm_base_url()}/api/customers/{customer_id}/contacts",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'CRM系统连接失败: {str(e)}'
        }


def check_crm_health():
    """检查CRM服务是否可用"""
    try:
        response = requests.get(
            f"{get_crm_base_url()}/api/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
