"""
Integration Service - 子系统集成服务
提供与 CRM、HR 等子系统的数据交互
"""
import os
import requests
from typing import Optional, List, Dict, Any


class IntegrationService:
    """子系统集成服务"""

    def __init__(self):
        # 从环境变量读取子系统 URL，默认本地开发端口
        self.crm_base_url = os.getenv('CRM_API_BASE_URL', 'http://localhost:8002')
        self.hr_base_url = os.getenv('HR_API_BASE_URL', 'http://localhost:8003')
        self.quotation_base_url = os.getenv('QUOTATION_API_BASE_URL', 'http://localhost:8001')
        self.scm_base_url = os.getenv('SCM_API_BASE_URL', 'http://localhost:8005')
        self.timeout = 10  # 请求超时时间
        # 本地请求禁用代理，避免其他功能的代理配置影响子系统调用
        self.no_proxy = {'http': None, 'https': None}

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """构建请求头，包含认证 token"""
        headers = {
            'Content-Type': 'application/json',
        }
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    # ==================== CRM 客户接口 ====================

    def get_customers(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取客户列表（从 CRM 系统）

        Args:
            keyword: 搜索关键词（客户名称、简称、编号）
            page: 页码
            page_size: 每页数量
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': {
                    'items': [...],
                    'total': 100,
                    'page': 1,
                    'page_size': 20
                }
            }
        """
        try:
            url = f"{self.crm_base_url}/api/customers"
            params = {
                'keyword': keyword,
                'page': page,
                'page_size': page_size
            }
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                data = response.json()
                # CRM 返回格式: {"success": True, "data": {"items": [...], "total": N}}
                # 或直接: {"items": [...], "total": N} 或列表 [...]

                # 处理 {"success": True, "data": {...}} 格式
                if isinstance(data, dict) and 'success' in data and 'data' in data:
                    data = data.get('data') or {}

                if isinstance(data, list):
                    return {
                        'success': True,
                        'data': {
                            'items': data,
                            'total': len(data),
                            'page': page,
                            'page_size': page_size
                        }
                    }
                elif isinstance(data, dict):
                    # 标准化返回格式
                    items = data.get('items') or data.get('customers') or []
                    total = data.get('total') or data.get('count') or len(items)
                    return {
                        'success': True,
                        'data': {
                            'items': items,
                            'total': total,
                            'page': data.get('page', page),
                            'page_size': data.get('page_size', page_size)
                        }
                    }
                return {'success': True, 'data': data}
            else:
                return {
                    'success': False,
                    'error': f'CRM 服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'CRM 服务连接失败，请检查服务是否启动',
                'data': None
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'CRM 服务请求超时',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'CRM 服务请求失败: {str(e)}',
                'data': None
            }

    def get_customer(self, customer_id: int, token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取客户详情（从 CRM 系统）

        Args:
            customer_id: 客户 ID
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': { 客户详情 }
            }
        """
        try:
            url = f"{self.crm_base_url}/api/customers/{customer_id}"
            response = requests.get(
                url,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': '客户不存在',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'error': f'CRM 服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'CRM 服务连接失败',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'CRM 服务请求失败: {str(e)}',
                'data': None
            }

    # ==================== CRM 供应商接口 ====================

    def get_suppliers(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取供应商列表（从 CRM 系统）

        Args:
            keyword: 搜索关键词（供应商名称、简称、编号）
            page: 页码
            page_size: 每页数量
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': {
                    'items': [...],
                    'total': 100,
                    'page': 1,
                    'page_size': 20
                }
            }
        """
        try:
            url = f"{self.crm_base_url}/api/suppliers"
            params = {
                'keyword': keyword,
                'page': page,
                'page_size': page_size
            }
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                data = response.json()
                # CRM 返回格式处理
                if isinstance(data, dict) and 'success' in data and 'data' in data:
                    data = data.get('data') or {}

                if isinstance(data, list):
                    return {
                        'success': True,
                        'data': {
                            'items': data,
                            'total': len(data),
                            'page': page,
                            'page_size': page_size
                        }
                    }
                elif isinstance(data, dict):
                    items = data.get('items') or data.get('suppliers') or []
                    total = data.get('total') or data.get('count') or len(items)
                    return {
                        'success': True,
                        'data': {
                            'items': items,
                            'total': total,
                            'page': data.get('page', page),
                            'page_size': data.get('page_size', page_size)
                        }
                    }
                return {'success': True, 'data': data}
            else:
                return {
                    'success': False,
                    'error': f'CRM 服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'CRM 服务连接失败，请检查服务是否启动',
                'data': None
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'CRM 服务请求超时',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'CRM 服务请求失败: {str(e)}',
                'data': None
            }

    def get_supplier(self, supplier_id: int, token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取供应商详情（从 CRM 系统）

        Args:
            supplier_id: 供应商 ID
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': { 供应商详情 }
            }
        """
        try:
            url = f"{self.crm_base_url}/api/suppliers/{supplier_id}"
            response = requests.get(
                url,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': '供应商不存在',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'error': f'CRM 服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'CRM 服务连接失败',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'CRM 服务请求失败: {str(e)}',
                'data': None
            }

    # ==================== HR 员工接口 ====================

    def get_employees(
        self,
        search: str = "",
        department: str = "",
        page: int = 1,
        page_size: int = 50,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取员工列表（从 HR 系统）

        Args:
            search: 搜索关键词（姓名、工号）
            department: 部门筛选
            page: 页码
            page_size: 每页数量
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': {
                    'items': [...],
                    'total': 100
                }
            }
        """
        try:
            url = f"{self.hr_base_url}/api/employees"
            params = {
                'search': search,
                'page': page,
                'page_size': page_size
            }
            if department:
                params['department'] = department

            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                data = response.json()
                # HR 返回格式: {"success": True, "data": {"items": [...], "total": N}}
                # 或直接: {"items": [...], "total": N} 或列表 [...]

                # 处理 {"success": True, "data": {...}} 格式
                if isinstance(data, dict) and 'success' in data and 'data' in data:
                    data = data.get('data') or {}

                if isinstance(data, list):
                    return {
                        'success': True,
                        'data': {
                            'items': data,
                            'total': len(data),
                            'page': page,
                            'page_size': page_size
                        }
                    }
                elif isinstance(data, dict):
                    items = data.get('items') or data.get('employees') or []
                    total = data.get('total') or data.get('count') or len(items)
                    return {
                        'success': True,
                        'data': {
                            'items': items,
                            'total': total,
                            'page': data.get('page', page),
                            'page_size': data.get('page_size', page_size)
                        }
                    }
                return {'success': True, 'data': data}
            else:
                return {
                    'success': False,
                    'error': f'HR 服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'HR 服务连接失败，请检查服务是否启动',
                'data': None
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'HR 服务请求超时',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HR 服务请求失败: {str(e)}',
                'data': None
            }

    def get_employee(self, employee_id: int, token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取员工详情（从 HR 系统）

        Args:
            employee_id: 员工 ID
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': { 员工详情 }
            }
        """
        try:
            url = f"{self.hr_base_url}/api/employees/{employee_id}"
            response = requests.get(
                url,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': '员工不存在',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'error': f'HR 服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'HR 服务连接失败',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HR 服务请求失败: {str(e)}',
                'data': None
            }

    def get_departments(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取部门列表（从 HR 系统）

        Args:
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': [{ 部门列表 }]
            }
        """
        try:
            url = f"{self.hr_base_url}/api/departments"
            response = requests.get(
                url,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                data = response.json()
                # 标准化返回
                if isinstance(data, list):
                    return {
                        'success': True,
                        'data': data
                    }
                elif isinstance(data, dict):
                    items = data.get('items') or data.get('departments') or data.get('data') or []
                    return {
                        'success': True,
                        'data': items
                    }
                return {'success': True, 'data': data}
            else:
                return {
                    'success': False,
                    'error': f'HR 服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'HR 服务连接失败，请检查服务是否启动',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HR 服务请求失败: {str(e)}',
                'data': None
            }

    def get_positions(self, token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取职位列表（从 HR 系统）

        Args:
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': [{ 职位列表 }]
            }
        """
        try:
            url = f"{self.hr_base_url}/api/positions"
            response = requests.get(
                url,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return {
                        'success': True,
                        'data': data
                    }
                elif isinstance(data, dict):
                    items = data.get('items') or data.get('positions') or data.get('data') or []
                    return {
                        'success': True,
                        'data': items
                    }
                return {'success': True, 'data': data}
            else:
                return {
                    'success': False,
                    'error': f'HR 服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'HR 服务连接失败',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'HR 服务请求失败: {str(e)}',
                'data': None
            }

    # ==================== 报价系统产品接口 ====================

    def get_products(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取产品/品番号列表（从报价系统）

        Args:
            keyword: 搜索关键词（品番号、产品名称）
            page: 页码
            page_size: 每页数量
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': {
                    'items': [...],
                    'total': 100,
                    'page': 1,
                    'page_size': 20
                }
            }
        """
        try:
            url = f"{self.quotation_base_url}/api/products"
            # 报价系统使用 search/skip/limit 参数
            skip = (page - 1) * page_size
            params = {
                'search': keyword,
                'skip': skip,
                'limit': page_size
            }
            response = requests.get(
                url,
                params=params,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                data = response.json()
                # 报价系统返回格式处理
                if isinstance(data, dict) and 'success' in data and 'data' in data:
                    data = data.get('data') or {}

                if isinstance(data, list):
                    return {
                        'success': True,
                        'data': {
                            'items': data,
                            'total': len(data),
                            'page': page,
                            'page_size': page_size
                        }
                    }
                elif isinstance(data, dict):
                    items = data.get('items') or data.get('products') or []
                    total = data.get('total') or data.get('count') or len(items)
                    return {
                        'success': True,
                        'data': {
                            'items': items,
                            'total': total,
                            'page': data.get('page', page),
                            'page_size': data.get('page_size', page_size)
                        }
                    }
                return {'success': True, 'data': data}
            else:
                return {
                    'success': False,
                    'error': f'报价服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': '报价服务连接失败，请检查服务是否启动',
                'data': None
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': '报价服务请求超时',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'报价服务请求失败: {str(e)}',
                'data': None
            }

    def get_product(self, product_code: str, token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取产品详情（从报价系统）

        Args:
            product_code: 产品品番号
            token: 认证 token

        Returns:
            {
                'success': True,
                'data': { 产品详情 }
            }
        """
        try:
            # 报价系统使用 /products/code/{product_code} 路径
            url = f"{self.quotation_base_url}/api/products/code/{product_code}"
            response = requests.get(
                url,
                headers=self._get_headers(token),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'error': '产品不存在',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'error': f'报价服务返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': '报价服务连接失败',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'报价服务请求失败: {str(e)}',
                'data': None
            }

    # ==================== 健康检查 ====================

    def check_health(self) -> Dict[str, Any]:
        """
        检查所有子系统的健康状态

        Returns:
            {
                'crm': {'status': 'healthy', 'url': '...'},
                'hr': {'status': 'healthy', 'url': '...'}
            }
        """
        result = {}

        # 检查 CRM
        try:
            response = requests.get(
                f"{self.crm_base_url}/health",
                timeout=5,
                proxies=self.no_proxy
            )
            result['crm'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'url': self.crm_base_url,
                'response_code': response.status_code
            }
        except Exception as e:
            result['crm'] = {
                'status': 'unreachable',
                'url': self.crm_base_url,
                'error': str(e)
            }

        # 检查 HR
        try:
            response = requests.get(
                f"{self.hr_base_url}/health",
                timeout=5,
                proxies=self.no_proxy
            )
            result['hr'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'url': self.hr_base_url,
                'response_code': response.status_code
            }
        except Exception as e:
            result['hr'] = {
                'status': 'unreachable',
                'url': self.hr_base_url,
                'error': str(e)
            }

        # 检查报价系统
        try:
            response = requests.get(
                f"{self.quotation_base_url}/health",
                timeout=5,
                proxies=self.no_proxy
            )
            result['quotation'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'url': self.quotation_base_url,
                'response_code': response.status_code
            }
        except Exception as e:
            result['quotation'] = {
                'status': 'unreachable',
                'url': self.quotation_base_url,
                'error': str(e)
            }

        return result


# 创建单例实例
integration_service = IntegrationService()
