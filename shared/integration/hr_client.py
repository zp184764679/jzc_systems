"""
HR 系统统一客户端

提供员工、部门、职位相关的 API 调用。
替代各系统各自实现的 hr_service.py。
"""

import os
from typing import Optional, Dict, Any, List
from .base_client import BaseIntegrationClient


class HRClient(BaseIntegrationClient):
    """
    HR 系统客户端

    提供以下功能：
    - 员工列表查询
    - 员工详情获取
    - 按角色/部门筛选员工
    - 部门列表
    - 职位列表

    使用示例:
        hr = HRClient()

        # 获取销售人员
        sales = hr.get_employees_by_role("sales")

        # 获取员工详情
        employee = hr.get_employee(123)

        # 获取部门列表
        departments = hr.get_departments()
    """

    SERVICE_NAME = "HR"
    ENV_URL_KEY = "HR_API_URL"
    DEFAULT_URL = "http://localhost:8003"

    # 角色到部门/职位的映射
    ROLE_FILTERS = {
        "sales": {"department": "销售", "position_keywords": ["销售", "业务"]},
        "procurement": {"department": "采购", "position_keywords": ["采购"]},
        "logistics": {"department": "物流", "position_keywords": ["物流", "仓管"]},
        "production": {"department": "生产", "position_keywords": ["生产", "制造"]},
        "quality": {"department": "品质", "position_keywords": ["品质", "QC", "QA"]},
        "manager": {"position_keywords": ["经理", "主管", "总监"]},
    }

    # ============ 员工相关 API ============

    def get_employees(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 100,
        department: Optional[str] = None,
        status: str = "Active"
    ) -> Dict[str, Any]:
        """
        获取员工列表

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页条数
            department: 部门筛选
            status: 在职状态筛选

        Returns:
            {
                "items": [...],
                "total": 100,
                "page": 1,
                "page_size": 100
            }
        """
        params = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "employment_status": status
        }
        if department:
            params["department"] = department

        return self._safe_get("/api/employees", default={"items": [], "total": 0}, params=params)

    def search_employees(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        搜索员工（用于下拉选择器）

        Args:
            keyword: 搜索关键词
            limit: 返回条数上限

        Returns:
            员工列表 [{"id": 1, "name": "...", "empNo": "..."}]
        """
        result = self.get_employees(keyword=keyword, page_size=limit)
        return result.get("items", [])

    def get_employee(self, employee_id: int) -> Optional[Dict]:
        """
        获取员工详情

        Args:
            employee_id: 员工 ID

        Returns:
            员工详情或 None
        """
        return self._safe_get(f"/api/employees/{employee_id}")

    def get_employees_by_role(self, role: str, keyword: str = "") -> List[Dict]:
        """
        按角色获取员工列表

        Args:
            role: 角色类型（sales/procurement/logistics/production/quality/manager）
            keyword: 额外的搜索关键词

        Returns:
            员工列表
        """
        role_config = self.ROLE_FILTERS.get(role.lower(), {})
        department = role_config.get("department")

        result = self.get_employees(keyword=keyword, department=department)
        employees = result.get("items", [])

        # 如果有职位关键词，进一步过滤
        position_keywords = role_config.get("position_keywords", [])
        if position_keywords:
            filtered = []
            for emp in employees:
                position = emp.get("position", "") or emp.get("title", "") or ""
                if any(kw in position for kw in position_keywords):
                    filtered.append(emp)
            return filtered

        return employees

    def get_sales_staff(self, keyword: str = "") -> List[Dict]:
        """获取销售人员列表"""
        return self.get_employees_by_role("sales", keyword)

    def get_procurement_staff(self, keyword: str = "") -> List[Dict]:
        """获取采购人员列表"""
        return self.get_employees_by_role("procurement", keyword)

    # ============ 部门相关 API ============

    def get_departments(self) -> List[Dict]:
        """
        获取部门列表

        Returns:
            部门列表 [{"id": 1, "name": "..."}]
        """
        result = self._safe_get("/api/departments", default={"items": []})
        return result.get("items", []) if isinstance(result, dict) else result

    def get_department(self, department_id: int) -> Optional[Dict]:
        """
        获取部门详情

        Args:
            department_id: 部门 ID

        Returns:
            部门详情或 None
        """
        return self._safe_get(f"/api/departments/{department_id}")

    # ============ 职位相关 API ============

    def get_positions(self) -> List[Dict]:
        """
        获取职位列表

        Returns:
            职位列表 [{"id": 1, "name": "..."}]
        """
        result = self._safe_get("/api/positions", default={"items": []})
        return result.get("items", []) if isinstance(result, dict) else result

    # ============ 工具方法 ============

    def get_employee_options(self, keyword: str = "", role: Optional[str] = None) -> List[Dict]:
        """
        获取员工选项列表（用于前端 Select 组件）

        Args:
            keyword: 搜索关键词
            role: 角色筛选

        Returns:
            [{"value": 1, "label": "姓名", "extra": {...}}]
        """
        if role:
            employees = self.get_employees_by_role(role, keyword)
        else:
            employees = self.search_employees(keyword)

        return [
            {
                "value": e.get("id"),
                "label": e.get("name"),
                "extra": {
                    "empNo": e.get("empNo") or e.get("emp_no"),
                    "department": e.get("department"),
                    "position": e.get("position") or e.get("title"),
                    "phone": e.get("phone"),
                    "email": e.get("email")
                }
            }
            for e in employees
        ]

    def get_department_options(self) -> List[Dict]:
        """
        获取部门选项列表（用于前端 Select 组件）

        Returns:
            [{"value": 1, "label": "部门名称"}]
        """
        departments = self.get_departments()
        return [
            {"value": d.get("id"), "label": d.get("name")}
            for d in departments
        ]
