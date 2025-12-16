# SCM库存集成服务
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_scm_base_url():
    return os.getenv('SCM_API_BASE_URL', '')


def get_inventory_items(keyword="", page=1, page_size=20):
    """获取库存物料"""
    try:
        response = requests.get(
            f"{get_scm_base_url()}/api/inventory",
            params={"keyword": keyword, "page": page, "page_size": page_size},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'SCM连接失败: {str(e)}', 'data': {'items': []}}


def create_stock_request(material_code, quantity, requester, reason):
    """创建出库请求"""
    try:
        response = requests.post(
            f"{get_scm_base_url()}/api/inventory/requests",
            json={
                "material_code": material_code,
                "quantity": quantity,
                "requester": requester,
                "reason": reason,
                "source": "MES"
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'SCM连接失败: {str(e)}'}


def check_scm_health():
    try:
        response = requests.get(f"{get_scm_base_url()}/api/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
