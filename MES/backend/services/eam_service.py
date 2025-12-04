# EAM设备资产集成服务
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_eam_base_url():
    return os.getenv('EAM_API_BASE_URL', '')


def get_equipment_list(keyword=""):
    """获取设备列表"""
    try:
        response = requests.get(
            f"{get_eam_base_url()}/api/equipment",
            params={"keyword": keyword},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'EAM连接失败: {str(e)}', 'data': {'items': []}}


def get_equipment_status(equipment_id):
    """获取设备状态"""
    try:
        response = requests.get(f"{get_eam_base_url()}/api/equipment/{equipment_id}/status", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'EAM连接失败: {str(e)}'}


def report_equipment_usage(equipment_id, work_order_id, hours):
    """报告设备使用情况"""
    try:
        response = requests.post(
            f"{get_eam_base_url()}/api/equipment/{equipment_id}/usage",
            json={"work_order_id": work_order_id, "hours": hours, "source": "MES"},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'success': False, 'error': f'EAM连接失败: {str(e)}'}


def check_eam_health():
    try:
        response = requests.get(f"{get_eam_base_url()}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False
