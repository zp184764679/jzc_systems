import requests
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
        response = requests.get(
            f"{Config.CRM_API_BASE_URL}/api/customers",
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
            f"{Config.CRM_API_BASE_URL}/api/customers/{customer_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'CRM系统连接失败: {str(e)}'
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
        response = requests.post(
            f"{Config.CRM_API_BASE_URL}/api/customers/search",
            json={
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


def check_crm_health():
    """检查CRM服务是否可用"""
    try:
        response = requests.get(
            f"{Config.CRM_API_BASE_URL}/api/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
