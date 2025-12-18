# SCM库存集成服务
# P2-18: 添加跨系统服务调用重试机制
import os
import sys
from dotenv import load_dotenv

# 添加 shared 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.http_client import get_with_retry, post_with_retry, RETRYABLE_EXCEPTIONS

load_dotenv()


def get_scm_base_url():
    return os.getenv('SCM_API_BASE_URL', '')


def get_inventory_items(keyword="", page=1, page_size=20):
    """获取库存物料"""
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_scm_base_url()}/api/inventory",
            params={"keyword": keyword, "page": page, "page_size": page_size},
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {'success': False, 'error': f'SCM系统连接失败: {str(e)} (已重试)', 'data': {'items': []}}
    except Exception as e:
        return {'success': False, 'error': f'SCM系统调用异常: {str(e)}', 'data': {'items': []}}


def create_stock_request(material_code, quantity, requester, reason):
    """创建出库请求"""
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = post_with_retry(
            f"{get_scm_base_url()}/api/inventory/requests",
            json={
                "material_code": material_code,
                "quantity": quantity,
                "requester": requester,
                "reason": reason,
                "source": "MES"
            },
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {'success': False, 'error': f'SCM系统连接失败: {str(e)} (已重试)'}
    except Exception as e:
        return {'success': False, 'error': f'SCM系统调用异常: {str(e)}'}


def check_scm_health():
    """检查SCM系统健康状态"""
    try:
        # P2-18: 健康检查只重试1次
        response = get_with_retry(
            f"{get_scm_base_url()}/api/health",
            max_retries=1,
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
