"""
报价系统统一客户端

提供品番号、产品、工艺相关的 API 调用。
用于统一品番号主数据管理。
"""

import os
from typing import Optional, Dict, Any, List
from .base_client import BaseIntegrationClient


class QuotationClient(BaseIntegrationClient):
    """
    报价系统客户端

    提供以下功能：
    - 品番号/产品查询
    - 产品搜索
    - 工艺信息查询
    - BOM 查询

    使用示例:
        quotation = QuotationClient()

        # 搜索品番号
        products = quotation.search_products("2J1030")

        # 获取产品详情
        product = quotation.get_product("2J1030J")
    """

    SERVICE_NAME = "Quotation"
    ENV_URL_KEY = "QUOTATION_API_URL"
    DEFAULT_URL = "http://localhost:8001"

    # ============ 产品/品番号相关 API ============

    def get_products(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        customer_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取产品列表

        Args:
            keyword: 搜索关键词（品番号/产品名称）
            page: 页码
            page_size: 每页条数
            customer_id: 客户筛选

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
        if customer_id:
            params["customer_id"] = customer_id

        return self._safe_get("/api/products", default={"items": [], "total": 0}, params=params)

    def search_products(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜索产品/品番号（用于下拉选择器）

        Args:
            keyword: 搜索关键词
            limit: 返回条数上限

        Returns:
            产品列表 [{"code": "...", "name": "...", "customer_part_number": "..."}]
        """
        result = self.get_products(keyword=keyword, page_size=limit)
        return result.get("items", [])

    def get_product(self, product_code: str) -> Optional[Dict]:
        """
        按产品编码获取产品详情

        Args:
            product_code: 产品编码/品番号

        Returns:
            产品详情或 None
        """
        return self._safe_get(f"/api/products/{product_code}")

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        按 ID 获取产品详情

        Args:
            product_id: 产品 ID

        Returns:
            产品详情或 None
        """
        return self._safe_get(f"/api/products/id/{product_id}")

    # ============ 工艺相关 API ============

    def get_product_processes(self, product_code: str) -> List[Dict]:
        """
        获取产品工艺列表

        Args:
            product_code: 产品编码

        Returns:
            工艺列表
        """
        result = self._safe_get(f"/api/products/{product_code}/processes", default={"items": []})
        return result.get("items", []) if isinstance(result, dict) else result

    def get_product_materials(self, product_code: str) -> List[Dict]:
        """
        获取产品材料清单

        Args:
            product_code: 产品编码

        Returns:
            材料列表
        """
        result = self._safe_get(f"/api/products/{product_code}/materials", default={"items": []})
        return result.get("items", []) if isinstance(result, dict) else result

    # ============ 报价相关 API ============

    def get_quotes(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取报价列表

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页条数
            status: 状态筛选

        Returns:
            报价列表
        """
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size
        }
        if status:
            params["status"] = status

        return self._safe_get("/api/quotes", default={"items": [], "total": 0}, params=params)

    def get_quote(self, quote_id: int) -> Optional[Dict]:
        """
        获取报价详情

        Args:
            quote_id: 报价 ID

        Returns:
            报价详情或 None
        """
        return self._safe_get(f"/api/quotes/{quote_id}")

    # ============ 工具方法 ============

    def get_product_options(self, keyword: str = "") -> List[Dict]:
        """
        获取产品选项列表（用于前端 Select 组件）

        Returns:
            [{"value": "code", "label": "品番号 - 名称", "extra": {...}}]
        """
        products = self.search_products(keyword)
        return [
            {
                "value": p.get("code"),
                "label": f"{p.get('code')} - {p.get('name', '')}",
                "extra": {
                    "name": p.get("name"),
                    "customer_part_number": p.get("customer_part_number"),
                    "material": p.get("material"),
                    "version": p.get("version")
                }
            }
            for p in products
        ]

    def validate_part_number(self, part_number: str) -> Dict:
        """
        验证品番号是否存在

        Args:
            part_number: 品番号

        Returns:
            {
                "valid": True/False,
                "product": {...} or None,
                "message": "..."
            }
        """
        product = self.get_product(part_number)
        if product:
            return {
                "valid": True,
                "product": product,
                "message": "品番号有效"
            }
        else:
            return {
                "valid": False,
                "product": None,
                "message": f"品番号 '{part_number}' 不存在"
            }

    def search_part_numbers(self, keyword: str, limit: int = 10) -> List[str]:
        """
        搜索品番号（仅返回编码列表）

        Args:
            keyword: 搜索关键词
            limit: 返回条数上限

        Returns:
            品番号列表 ["2J1030J", "2J1051A", ...]
        """
        products = self.search_products(keyword, limit)
        return [p.get("code") for p in products if p.get("code")]
