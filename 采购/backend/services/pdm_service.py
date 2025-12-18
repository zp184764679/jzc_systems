# services/pdm_service.py
"""
PDM产品数据管理系统集成服务
P2-18: 添加跨系统服务调用重试机制
"""
import os
import sys
from dotenv import load_dotenv

# 添加 shared 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.http_client import get_with_retry, RETRYABLE_EXCEPTIONS

load_dotenv()


def get_pdm_base_url():
    """获取PDM API基础URL"""
    return os.getenv('PDM_API_BASE_URL', 'http://localhost:8001')


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
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_pdm_base_url()}/api/products",
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
            'error': f'PDM系统连接失败: {str(e)} (已重试)',
            'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'PDM系统调用异常: {str(e)}',
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
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_pdm_base_url()}/api/products/{product_id}",
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {
            'success': False,
            'error': f'PDM系统连接失败: {str(e)} (已重试)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'PDM系统调用异常: {str(e)}'
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
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_pdm_base_url()}/api/products",
            params={"keyword": product_code, "page_size": 1},
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data.get('success') and data.get('data', {}).get('items'):
            return {
                'success': True,
                'data': data['data']['items'][0]
            }
        return {
            'success': False,
            'error': f'产品 {product_code} 不存在'
        }
    except RETRYABLE_EXCEPTIONS as e:
        return {
            'success': False,
            'error': f'PDM系统连接失败: {str(e)} (已重试)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'PDM系统调用异常: {str(e)}'
        }


def get_product_bom(product_id):
    """
    获取产品BOM物料清单

    Args:
        product_id: 产品ID

    Returns:
        dict: BOM数据
    """
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_pdm_base_url()}/api/boms/{product_id}",
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {
            'success': False,
            'error': f'PDM系统连接失败: {str(e)} (已重试)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'PDM系统调用异常: {str(e)}'
        }


def check_pdm_health():
    """检查PDM服务是否可用"""
    try:
        # P2-18: 健康检查只重试1次
        response = get_with_retry(
            f"{get_pdm_base_url()}/ping",
            max_retries=1,
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
