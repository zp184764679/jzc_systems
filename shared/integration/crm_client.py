"""
CRM 系统统一客户端

提供客户和供应商相关的 API 调用。
替代各系统各自实现的 crm_service.py。
"""

import os
from typing import Optional, Dict, Any, List
from .base_client import BaseIntegrationClient


class CRMClient(BaseIntegrationClient):
    """
    CRM 系统客户端

    提供以下功能：
    - 客户列表查询
    - 客户详情获取
    - 客户搜索
    - 供应商列表查询（新增）
    - 供应商详情获取（新增）

    使用示例:
        crm = CRMClient()

        # 搜索客户
        customers = crm.search_customers("ABC公司")

        # 获取客户详情
        customer = crm.get_customer(123)

        # 获取供应商列表
        suppliers = crm.get_suppliers()
    """

    SERVICE_NAME = "CRM"
    ENV_URL_KEY = "CRM_API_URL"
    DEFAULT_URL = "http://localhost:8002"

    # ============ 客户相关 API ============

    def get_customers(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        grade: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取客户列表

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页条数
            grade: 客户等级筛选

        Returns:
            {
                "items": [...],
                "total": 100,
                "page": 1,
                "page_size": 20
            }
        """
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size
        }
        if grade:
            params["grade"] = grade

        return self._safe_get("/api/customers", default={"items": [], "total": 0}, params=params)

    def search_customers(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜索客户（用于下拉选择器）

        Args:
            keyword: 搜索关键词
            limit: 返回条数上限

        Returns:
            客户列表 [{"id": 1, "name": "...", "short_name": "..."}]
        """
        result = self.get_customers(keyword=keyword, page_size=limit)
        return result.get("items", [])

    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """
        获取客户详情

        Args:
            customer_id: 客户 ID

        Returns:
            客户详情或 None
        """
        return self._safe_get(f"/api/customers/{customer_id}")

    def get_customer_contacts(self, customer_id: int) -> List[Dict]:
        """
        获取客户联系人列表

        Args:
            customer_id: 客户 ID

        Returns:
            联系人列表
        """
        result = self._safe_get(f"/api/customers/{customer_id}/contacts", default={"items": []})
        return result.get("items", [])

    # ============ 供应商相关 API ============

    def get_suppliers(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取供应商列表

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页条数
            status: 状态筛选（active/inactive）

        Returns:
            {
                "items": [...],
                "total": 100,
                "page": 1,
                "page_size": 20
            }
        """
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size
        }
        if status:
            params["status"] = status

        return self._safe_get("/api/suppliers", default={"items": [], "total": 0}, params=params)

    def search_suppliers(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜索供应商（用于下拉选择器）

        Args:
            keyword: 搜索关键词
            limit: 返回条数上限

        Returns:
            供应商列表 [{"id": 1, "name": "...", "code": "..."}]
        """
        result = self.get_suppliers(keyword=keyword, page_size=limit)
        return result.get("items", [])

    def get_supplier(self, supplier_id: int) -> Optional[Dict]:
        """
        获取供应商详情

        Args:
            supplier_id: 供应商 ID

        Returns:
            供应商详情或 None
        """
        return self._safe_get(f"/api/suppliers/{supplier_id}")

    def get_supplier_contacts(self, supplier_id: int) -> List[Dict]:
        """
        获取供应商联系人列表

        Args:
            supplier_id: 供应商 ID

        Returns:
            联系人列表
        """
        result = self._safe_get(f"/api/suppliers/{supplier_id}/contacts", default={"items": []})
        return result.get("items", [])

    # ============ 工具方法 ============

    def get_customer_options(self, keyword: str = "") -> List[Dict]:
        """
        获取客户选项列表（用于前端 Select 组件）

        Returns:
            [{"value": 1, "label": "客户名称", "extra": {...}}]
        """
        customers = self.search_customers(keyword)
        return [
            {
                "value": c.get("id"),
                "label": c.get("short_name") or c.get("name"),
                "extra": {
                    "full_name": c.get("name"),
                    "code": c.get("code")
                }
            }
            for c in customers
        ]

    def get_supplier_options(self, keyword: str = "") -> List[Dict]:
        """
        获取供应商选项列表（用于前端 Select 组件）

        Returns:
            [{"value": 1, "label": "供应商名称", "extra": {...}}]
        """
        suppliers = self.search_suppliers(keyword)
        return [
            {
                "value": s.get("id"),
                "label": s.get("company_name") or s.get("name"),
                "extra": {
                    "code": s.get("code"),
                    "email": s.get("email")
                }
            }
            for s in suppliers
        ]
