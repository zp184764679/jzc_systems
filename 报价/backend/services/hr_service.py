# services/hr_service.py
"""
HR人力资源系统客户端服务
用于从HR系统获取员工数据（如销售人员）
"""
import httpx
from typing import Dict, Any
from config.settings import settings


class HRService:
    """HR系统API客户端"""

    def __init__(self):
        self.base_url = settings.HR_API_BASE_URL
        self.timeout = 10.0

    def _get_client(self):
        """获取HTTP客户端"""
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get_sales_staff(self, search: str = "", page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """
        获取销售人员列表

        Args:
            search: 搜索关键词
            page: 页码
            per_page: 每页数量

        Returns:
            销售人员列表数据
        """
        try:
            with self._get_client() as client:
                params = {
                    "search": search,
                    "employment_status": "Active",
                    "page": page,
                    "per_page": per_page
                }
                response = client.get("/api/employees", params=params)
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
        except httpx.HTTPError as e:
            return {
                'success': False,
                'error': f'HR API请求失败: {str(e)}',
                'data': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HR服务异常: {str(e)}',
                'data': []
            }

    def get_employee(self, employee_id: int) -> Dict[str, Any]:
        """
        获取员工详情

        Args:
            employee_id: 员工ID

        Returns:
            员工详情数据
        """
        try:
            with self._get_client() as client:
                response = client.get(f"/api/employees/{employee_id}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                'success': False,
                'error': f'HR API请求失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HR服务异常: {str(e)}'
            }

    def health_check(self) -> bool:
        """检查HR服务是否可用"""
        try:
            with self._get_client() as client:
                response = client.get("/api/employees/stats")
                return response.status_code == 200
        except Exception:
            return False


# 全局单例
hr_service = HRService()
