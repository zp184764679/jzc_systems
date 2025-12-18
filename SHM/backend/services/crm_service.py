# P2-18: 添加跨系统服务调用重试机制
import sys
import os

# 添加 shared 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.http_client import get_with_retry, post_with_retry, RETRYABLE_EXCEPTIONS
from config import Config


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
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{Config.CRM_API_BASE_URL}/api/customers",
            params={
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            },
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {
            'success': False,
            'error': f'CRM系统连接失败: {str(e)} (已重试)',
            'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'CRM系统调用异常: {str(e)}',
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
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{Config.CRM_API_BASE_URL}/api/customers/{customer_id}",
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {
            'success': False,
            'error': f'CRM系统连接失败: {str(e)} (已重试)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'CRM系统调用异常: {str(e)}'
        }


def search_customers(keyword, page=1, page_size=20):
    """
    搜索客户

    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量

    Returns:
        dict: 搜索结果
    """
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = post_with_retry(
            f"{Config.CRM_API_BASE_URL}/api/customers/search",
            json={
                "keyword": keyword,
                "page": page,
                "page_size": page_size
            },
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {
            'success': False,
            'error': f'CRM系统连接失败: {str(e)} (已重试)',
            'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'CRM系统调用异常: {str(e)}',
            'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
        }


def check_crm_health():
    """检查CRM服务是否可用"""
    try:
        # P2-18: 健康检查只重试1次
        response = get_with_retry(
            f"{Config.CRM_API_BASE_URL}/api/health",
            max_retries=1,
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
