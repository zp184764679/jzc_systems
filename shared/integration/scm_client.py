"""
SCM 仓库系统统一客户端

提供库存、仓库、库位相关的 API 调用。
"""

import os
from typing import Optional, Dict, Any, List
from .base_client import BaseIntegrationClient


class SCMClient(BaseIntegrationClient):
    """
    SCM 仓库系统客户端

    提供以下功能：
    - 库存查询
    - 仓库列表
    - 库位列表
    - 库存锁定/释放

    使用示例:
        scm = SCMClient()

        # 查询产品库存
        stock = scm.get_inventory_by_code("ABC-001")

        # 获取仓库列表
        warehouses = scm.get_warehouses()
    """

    SERVICE_NAME = "SCM"
    ENV_URL_KEY = "SCM_API_URL"
    DEFAULT_URL = "http://localhost:8005"

    # ============ 库存相关 API ============

    def get_inventory(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        warehouse_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取库存列表

        Args:
            keyword: 搜索关键词（产品编码/名称）
            page: 页码
            page_size: 每页条数
            warehouse_id: 仓库筛选

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
        if warehouse_id:
            params["warehouse_id"] = warehouse_id

        return self._safe_get("/api/inventory", default={"items": [], "total": 0}, params=params)

    def search_inventory(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜索库存产品（用于下拉选择器）

        Args:
            keyword: 搜索关键词
            limit: 返回条数上限

        Returns:
            库存列表 [{"product_code": "...", "product_name": "...", "quantity": 100}]
        """
        result = self.get_inventory(keyword=keyword, page_size=limit)
        return result.get("items", [])

    def get_inventory_by_code(self, product_code: str) -> Optional[Dict]:
        """
        按产品编码查询库存

        Args:
            product_code: 产品编码

        Returns:
            库存详情或 None
        """
        return self._safe_get(f"/api/inventory/by-code/{product_code}")

    def check_stock_availability(self, product_code: str, quantity: int) -> Dict:
        """
        检查库存可用性

        Args:
            product_code: 产品编码
            quantity: 需求数量

        Returns:
            {
                "available": True/False,
                "current_stock": 100,
                "requested": 50
            }
        """
        inventory = self.get_inventory_by_code(product_code)
        if not inventory:
            return {
                "available": False,
                "current_stock": 0,
                "requested": quantity,
                "message": "产品不存在"
            }

        current_stock = inventory.get("quantity", 0)
        return {
            "available": current_stock >= quantity,
            "current_stock": current_stock,
            "requested": quantity
        }

    # ============ 仓库相关 API ============

    def get_warehouses(self, status: str = "active") -> List[Dict]:
        """
        获取仓库列表

        Args:
            status: 状态筛选（active/inactive/all）

        Returns:
            仓库列表 [{"id": 1, "name": "...", "address": "..."}]
        """
        params = {}
        if status != "all":
            params["status"] = status

        result = self._safe_get("/api/warehouses", default={"items": []}, params=params)
        return result.get("items", []) if isinstance(result, dict) else result

    def get_warehouse(self, warehouse_id: int) -> Optional[Dict]:
        """
        获取仓库详情

        Args:
            warehouse_id: 仓库 ID

        Returns:
            仓库详情或 None
        """
        return self._safe_get(f"/api/warehouses/{warehouse_id}")

    # ============ 库位相关 API ============

    def get_locations(self, warehouse_id: Optional[int] = None) -> List[Dict]:
        """
        获取库位列表

        Args:
            warehouse_id: 仓库筛选

        Returns:
            库位列表 [{"id": 1, "code": "...", "warehouse_id": 1}]
        """
        params = {}
        if warehouse_id:
            params["warehouse_id"] = warehouse_id

        result = self._safe_get("/api/inventory/locations", default={"items": []}, params=params)
        return result.get("items", []) if isinstance(result, dict) else result

    # ============ 库存操作 API ============

    def deduct_stock(self, product_code: str, quantity: int, reason: str = "") -> Dict:
        """
        扣减库存（出货时调用）

        Args:
            product_code: 产品编码
            quantity: 扣减数量
            reason: 扣减原因

        Returns:
            操作结果
        """
        data = {
            "product_code": product_code,
            "quantity": quantity,
            "reason": reason
        }
        try:
            return self._post("/api/inventory/out", data=data)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def add_stock(self, product_code: str, quantity: int, reason: str = "") -> Dict:
        """
        增加库存（入库时调用）

        Args:
            product_code: 产品编码
            quantity: 增加数量
            reason: 入库原因

        Returns:
            操作结果
        """
        data = {
            "product_code": product_code,
            "quantity": quantity,
            "reason": reason
        }
        try:
            return self._post("/api/inventory/in", data=data)
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============ 工具方法 ============

    def get_warehouse_options(self) -> List[Dict]:
        """
        获取仓库选项列表（用于前端 Select 组件）

        Returns:
            [{"value": 1, "label": "仓库名称", "extra": {...}}]
        """
        warehouses = self.get_warehouses()
        return [
            {
                "value": w.get("id"),
                "label": w.get("name"),
                "extra": {
                    "code": w.get("code"),
                    "address": w.get("address")
                }
            }
            for w in warehouses
        ]

    def get_product_options(self, keyword: str = "") -> List[Dict]:
        """
        获取库存产品选项列表（用于前端 Select 组件）

        Returns:
            [{"value": "product_code", "label": "产品名称", "extra": {...}}]
        """
        items = self.search_inventory(keyword)
        return [
            {
                "value": i.get("product_code"),
                "label": f"{i.get('product_code')} - {i.get('product_name', '')}",
                "extra": {
                    "product_name": i.get("product_name"),
                    "quantity": i.get("quantity"),
                    "warehouse": i.get("warehouse_name")
                }
            }
            for i in items
        ]
