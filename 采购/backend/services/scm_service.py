# services/scm_service.py
"""
SCM库存管理系统集成服务
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_scm_base_url():
    """获取SCM API基础URL"""
    return os.getenv('SCM_API_BASE_URL', 'http://localhost:8004')


def get_inventory_items(keyword="", page=1, page_size=20):
    """
    从SCM系统获取库存物料列表

    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量

    Returns:
        dict: 库存物料列表数据
    """
    try:
        response = requests.get(
            f"{get_scm_base_url()}/api/inventory",
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
            'error': f'SCM系统连接失败: {str(e)}',
            'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
        }


def get_inventory_by_material_code(material_code):
    """
    根据物料编码获取库存信息

    Args:
        material_code: 物料编码

    Returns:
        dict: 库存信息
    """
    try:
        response = requests.get(
            f"{get_scm_base_url()}/api/inventory/by-code/{material_code}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'SCM系统连接失败: {str(e)}'
        }


def check_stock_availability(material_code, quantity):
    """
    检查物料库存是否充足

    Args:
        material_code: 物料编码
        quantity: 需求数量

    Returns:
        dict: 库存可用性信息
    """
    try:
        response = requests.get(
            f"{get_scm_base_url()}/api/inventory/check-stock",
            params={
                "material_code": material_code,
                "quantity": quantity
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'SCM系统连接失败: {str(e)}',
            'available': False
        }


def create_stock_request(material_code, quantity, requester, reason="采购需求"):
    """
    创建库存请求（入库/出库）

    Args:
        material_code: 物料编码
        quantity: 数量
        requester: 请求人
        reason: 请求原因

    Returns:
        dict: 请求结果
    """
    try:
        response = requests.post(
            f"{get_scm_base_url()}/api/inventory/requests",
            json={
                "material_code": material_code,
                "quantity": quantity,
                "requester": requester,
                "reason": reason,
                "source": "PROCUREMENT"
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'SCM系统连接失败: {str(e)}'
        }


def check_scm_health():
    """检查SCM服务是否可用"""
    try:
        response = requests.get(
            f"{get_scm_base_url()}/api/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
