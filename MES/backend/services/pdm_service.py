# PDM产品数据集成服务
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_pdm_base_url():
    return os.getenv('PDM_API_BASE_URL', '')


def get_products(keyword="", page=1, page_size=20):
    """获取产品列表"""
    try:
        response = requests.get(
            f"{get_pdm_base_url()}/api/products",
            params={"keyword": keyword, "page": page, "page_size": page_size},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'PDM连接失败: {str(e)}', 'data': {'items': []}}


def get_product_bom(product_id):
    """获取产品BOM"""
    try:
        response = requests.get(f"{get_pdm_base_url()}/api/products/{product_id}/bom", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'PDM连接失败: {str(e)}'}


def get_process_route(product_id):
    """获取产品工艺路线"""
    try:
        response = requests.get(f"{get_pdm_base_url()}/api/products/{product_id}/process-route", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'PDM连接失败: {str(e)}'}


def check_pdm_health():
    try:
        response = requests.get(f"{get_pdm_base_url()}/api/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
