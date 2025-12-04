import requests
from config import Config


def get_products(keyword="", page=1, page_size=20):
    """
    从PDM系统获取产品列表

    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量

    Returns:
        dict: 产品列表数据
    """
    try:
        response = requests.get(
            f"{Config.PDM_API_BASE_URL}/api/products",
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
            'error': f'PDM系统连接失败: {str(e)}',
            'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
        }


def get_product_by_id(product_id):
    """
    根据ID获取产品详情

    Args:
        product_id: 产品ID

    Returns:
        dict: 产品详情
    """
    try:
        response = requests.get(
            f"{Config.PDM_API_BASE_URL}/api/products/{product_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'PDM系统连接失败: {str(e)}'
        }


def get_product_by_code(product_code):
    """
    根据产品编码获取产品信息

    Args:
        product_code: 产品编码

    Returns:
        dict: 产品信息
    """
    try:
        response = requests.get(
            f"{Config.PDM_API_BASE_URL}/api/products",
            params={"keyword": product_code, "page_size": 1},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data.get('success') and data.get('data', {}).get('items'):
            # 返回第一个匹配的产品
            return {
                'success': True,
                'data': data['data']['items'][0]
            }
        return {
            'success': False,
            'error': f'产品 {product_code} 不存在'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'PDM系统连接失败: {str(e)}'
        }


def check_pdm_health():
    """检查PDM服务是否可用"""
    try:
        response = requests.get(
            f"{Config.PDM_API_BASE_URL}/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
