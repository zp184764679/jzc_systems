# HR人力资源系统集成服务 - EAM使用
# P2-18: 添加跨系统服务调用重试机制
import os
import sys
from dotenv import load_dotenv

# 添加 shared 模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.http_client import get_with_retry, RETRYABLE_EXCEPTIONS

load_dotenv()


def get_hr_base_url():
    return os.getenv('HR_API_BASE_URL', 'http://localhost:8003')


def get_maintenance_staff(search="", page=1, per_page=100):
    """获取维护人员列表"""
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_hr_base_url()}/api/employees",
            params={
                "search": search,
                "employment_status": "Active",
                "page": page,
                "per_page": per_page
            },
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()

        if result.get('success'):
            staff = []
            for emp in result.get('data', []):
                staff.append({
                    'id': emp.get('id'),
                    'empNo': emp.get('empNo'),
                    'name': emp.get('name'),
                    'department': emp.get('department'),
                    'title': emp.get('title'),
                    'phone': emp.get('phone'),
                    'email': emp.get('email')
                })
            return {
                'success': True,
                'data': staff,
                'total': len(staff)
            }
        return result
    except RETRYABLE_EXCEPTIONS as e:
        return {
            'success': False,
            'error': f'HR系统连接失败: {str(e)} (已重试)',
            'data': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'HR系统调用异常: {str(e)}',
            'data': []
        }


def get_employee(employee_id):
    """获取员工详情"""
    try:
        # P2-18: 使用带重试的 HTTP 客户端
        response = get_with_retry(
            f"{get_hr_base_url()}/api/employees/{employee_id}",
            max_retries=3,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except RETRYABLE_EXCEPTIONS as e:
        return {'success': False, 'error': f'HR系统连接失败: {str(e)} (已重试)'}
    except Exception as e:
        return {'success': False, 'error': f'HR系统调用异常: {str(e)}'}


def check_hr_health():
    """检查HR系统健康状态"""
    try:
        # P2-18: 健康检查只重试1次
        response = get_with_retry(
            f"{get_hr_base_url()}/api/employees/stats",
            max_retries=1,
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False
