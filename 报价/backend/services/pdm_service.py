# services/pdm_service.py
"""
PDM产品数据管理系统客户端服务
用于从PDM系统获取产品数据和成本信息
"""
import httpx
from typing import Dict, Any
from config.settings import settings


class PDMService:
    """PDM系统API客户端"""

    def __init__(self):
        self.base_url = settings.PDM_API_BASE_URL
        self.timeout = 10.0

    def _get_client(self):
        """获取HTTP客户端"""
        return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def get_products(self, keyword: str = "", page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        获取产品列表

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            产品列表数据
        """
        try:
            with self._get_client() as client:
                params = {
                    "keyword": keyword,
                    "page": page,
                    "page_size": page_size
                }
                response = client.get("/api/products", params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                'success': False,
                'error': f'PDM API请求失败: {str(e)}',
                'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'PDM服务异常: {str(e)}',
                'data': {'items': [], 'total': 0, 'page': page, 'page_size': page_size}
            }

    def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """
        根据ID获取产品详情

        Args:
            product_id: 产品ID

        Returns:
            产品详情数据
        """
        try:
            with self._get_client() as client:
                response = client.get(f"/api/products/{product_id}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                'success': False,
                'error': f'PDM API请求失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'PDM服务异常: {str(e)}'
            }

    def get_product_by_code(self, product_code: str) -> Dict[str, Any]:
        """
        根据产品编码获取产品信息

        Args:
            product_code: 产品编码

        Returns:
            产品详情数据
        """
        try:
            with self._get_client() as client:
                response = client.get(f"/api/products/by-code/{product_code}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                'success': False,
                'error': f'PDM API请求失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'PDM服务异常: {str(e)}'
            }

    def get_product_cost(self, product_id: int) -> Dict[str, Any]:
        """
        获取产品成本信息

        Args:
            product_id: 产品ID

        Returns:
            产品成本数据
        """
        try:
            with self._get_client() as client:
                response = client.get(f"/api/products/{product_id}/cost")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {
                'success': False,
                'error': f'PDM API请求失败: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'PDM服务异常: {str(e)}'
            }

    def health_check(self) -> bool:
        """检查PDM服务是否可用"""
        try:
            with self._get_client() as client:
                response = client.get("/api/health")
                return response.status_code == 200
        except Exception:
            return False


# 全局单例
pdm_service = PDMService()
