# services/crm_service.py
"""
CRM系统客户端服务
用于从CRM系统获取客户数据
"""
import httpx
from typing import Optional, Dict, Any, List
from config.settings import settings


class CRMService:
    """CRM系统API客户端"""

    def __init__(self):
        self.base_url = settings.CRM_API_BASE_URL
        self.timeout = 10.0  # 10秒超时

    def _get_client(self):
        """获取HTTP客户端"""
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get_customers(self, keyword: str = "", page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取客户列表

        Args:
            keyword: 搜索关键词（可搜索客户代码、简称、全称）
            page: 页码
            page_size: 每页数量

        Returns:
            {
                "success": bool,
                "data": {
                    "items": [...],
                    "total": int,
                    "page": int,
                    "page_size": int
                }
            }
        """
        try:
            with self._get_client() as client:
                params = {
                    "keyword": keyword,
                    "page": page,
                    "page_size": page_size
                }
                response = client.get("/api/customers", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"CRM API请求失败: {str(e)}",
                "data": {"items": [], "total": 0, "page": page, "page_size": page_size}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"CRM服务异常: {str(e)}",
                "data": {"items": [], "total": 0, "page": page, "page_size": page_size}
            }

    def get_customer_by_id(self, customer_id: int) -> Dict[str, Any]:
        """
        根据ID获取客户详情

        Args:
            customer_id: 客户ID

        Returns:
            客户详情字典
        """
        try:
            with self._get_client() as client:
                response = client.get(f"/api/customers/{customer_id}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"CRM API请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"CRM服务异常: {str(e)}"
            }

    def search_customers(self, keyword: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        搜索客户

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            搜索结果
        """
        try:
            with self._get_client() as client:
                response = client.post(
                    "/api/customers/search",
                    json={
                        "keyword": keyword,
                        "page": page,
                        "page_size": page_size
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"CRM API请求失败: {str(e)}",
                "data": {"items": [], "total": 0, "page": page, "page_size": page_size}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"CRM服务异常: {str(e)}",
                "data": {"items": [], "total": 0, "page": page, "page_size": page_size}
            }

    def get_customer_count(self) -> int:
        """获取客户总数"""
        try:
            with self._get_client() as client:
                response = client.get("/api/customers/_count")
                response.raise_for_status()
                data = response.json()
                if data.get("success"):
                    return data.get("data", {}).get("count", 0)
                return 0
        except Exception:
            return 0

    def health_check(self) -> bool:
        """检查CRM服务是否可用"""
        try:
            with self._get_client() as client:
                response = client.get("/api/health")
                return response.status_code == 200
        except Exception:
            return False


# 全局单例
crm_service = CRMService()
