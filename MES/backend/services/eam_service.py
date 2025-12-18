# EAM设备资产集成服务
# P2-18: 添加跨系统服务调用重试机制
import os
import sys
from dotenv import load_dotenv

# 添加 shared 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.http_client import get_with_retry, post_with_retry, RETRYABLE_EXCEPTIONS

load_dotenv()


def get_eam_base_url():
    return os.getenv('EAM_API_BASE_URL', '')


def get_equipment_list(keyword=""):
    """获取设备列表"""
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_eam_base_url()}/api/equipment",
            params={"keyword": keyword},
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {'success': False, 'error': f'EAM系统连接失败: {str(e)} (已重试)', 'data': {'items': []}}
    except Exception as e:
        return {'success': False, 'error': f'EAM系统调用异常: {str(e)}', 'data': {'items': []}}


def get_equipment_status(equipment_id):
    """获取设备状态"""
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_eam_base_url()}/api/equipment/{equipment_id}/status",
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {'success': False, 'error': f'EAM系统连接失败: {str(e)} (已重试)'}
    except Exception as e:
        return {'success': False, 'error': f'EAM系统调用异常: {str(e)}'}


def report_equipment_usage(equipment_id, work_order_id, hours):
    """报告设备使用情况"""
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = post_with_retry(
            f"{get_eam_base_url()}/api/equipment/{equipment_id}/usage",
            json={"work_order_id": work_order_id, "hours": hours, "source": "MES"},
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {'success': False, 'error': f'EAM系统连接失败: {str(e)} (已重试)'}
    except Exception as e:
        return {'success': False, 'error': f'EAM系统调用异常: {str(e)}'}


def check_eam_health():
    """检查EAM系统健康状态"""
    try:
        # P2-18: 健康检查只重试1次
        response = get_with_retry(
            f"{get_eam_base_url()}/api/health",
            max_retries=1,
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
