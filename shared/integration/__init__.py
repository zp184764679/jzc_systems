"""
JZC 系统统一集成模块

提供各子系统间跨系统调用的统一客户端。
所有子系统应使用此模块进行跨系统 API 调用，避免重复实现。

使用示例:
    from shared.integration import CRMClient, HRClient, SCMClient

    # 获取客户列表
    crm = CRMClient()
    customers = crm.get_customers(keyword="xxx")

    # 获取员工列表
    hr = HRClient()
    employees = hr.get_employees(role="sales")
"""

from .base_client import BaseIntegrationClient
from .crm_client import CRMClient
from .hr_client import HRClient
from .scm_client import SCMClient
from .quotation_client import QuotationClient

__all__ = [
    'BaseIntegrationClient',
    'CRMClient',
    'HRClient',
    'SCMClient',
    'QuotationClient',
]
