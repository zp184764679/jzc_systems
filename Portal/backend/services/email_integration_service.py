"""
Email Integration Service - 邮件集成服务
提供与供应商邮件翻译系统的数据交互，获取邮件列表和预提取的任务信息
"""
import os
import re
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

from models import SessionLocal
from models.project import Project
from services.integration_service import integration_service


class EmailIntegrationService:
    """邮件集成服务"""

    def __init__(self):
        # 邮件翻译系统 API URL
        self.email_api_url = os.getenv('EMAIL_TRANSLATE_API_URL', 'http://localhost:2000')
        # Ollama LLM URL（备用现场提取）
        self.ollama_url = os.getenv('LLM_BASE', 'http://localhost:11434')
        self.ollama_model = os.getenv('LLM_MODEL', 'qwen2.5:7b')
        self.timeout = 30
        # 本地请求禁用代理
        self.no_proxy = {'http': None, 'https': None}
        # Portal 服务令牌（用于与邮件系统的服务间通信）
        self.portal_service_token = os.getenv('PORTAL_SERVICE_TOKEN', 'jzc-portal-integration-token-2025')

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """构建请求头"""
        headers = {
            'Content-Type': 'application/json',
        }
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def _get_portal_headers(self) -> Dict[str, str]:
        """构建 Portal 服务令牌请求头"""
        return {
            'Content-Type': 'application/json',
            'X-Portal-Token': self.portal_service_token
        }

    # ==================== 邮件列表接口 ====================

    def get_emails(
        self,
        keyword: str = "",
        page: int = 1,
        page_size: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        translation_status: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取邮件列表（使用 Portal 服务令牌认证）

        Args:
            keyword: 搜索关键词（主题、发件人）
            page: 页码
            page_size: 每页数量
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            translation_status: 翻译状态筛选 (none/translating/completed/failed)
            token: 邮件系统认证 token（已废弃，使用服务令牌）

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
            # 使用 Portal 专用接口，通过服务令牌认证
            url = f"{self.email_api_url}/api/task-extractions/portal/emails"
            params = {
                'keyword': keyword,
                'page': page,
                'page_size': page_size
            }
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            if translation_status:
                params['translation_status'] = translation_status

            response = requests.get(
                url,
                params=params,
                headers=self._get_portal_headers(),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                data = response.json()
                # 标准化返回格式
                if isinstance(data, dict):
                    items = data.get('items') or data.get('emails') or []
                    total = data.get('total') or len(items)
                    return {
                        'success': True,
                        'data': {
                            'items': items,
                            'total': total,
                            'page': data.get('page', page),
                            'page_size': data.get('page_size', page_size)
                        }
                    }
                elif isinstance(data, list):
                    return {
                        'success': True,
                        'data': {
                            'items': data,
                            'total': len(data),
                            'page': page,
                            'page_size': page_size
                        }
                    }
                return {'success': True, 'data': data}
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': '服务令牌无效，请检查配置',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'error': f'邮件系统返回错误: {response.status_code}',
                    'data': None
                }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': '邮件系统连接失败，请检查服务是否启动',
                'data': None
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': '邮件系统请求超时',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'邮件系统请求失败: {str(e)}',
                'data': None
            }

    def get_email(self, email_id: int, token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取邮件详情

        Args:
            email_id: 邮件 ID
            token: 邮件系统认证 token（已废弃）

        Returns:
            邮件详情
        """
        try:
            # 使用 Portal 专用接口
            url = f"{self.email_api_url}/api/task-extractions/portal/emails/{email_id}"
            response = requests.get(
                url,
                headers=self._get_portal_headers(),
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
                    'error': '邮件不存在',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'error': f'邮件系统返回错误: {response.status_code}',
                    'data': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取邮件失败: {str(e)}',
                'data': None
            }

    # ==================== 任务提取接口 ====================

    def get_task_extraction(self, email_id: int, token: Optional[str] = None) -> Dict[str, Any]:
        """
        获取邮件的预提取任务信息

        Args:
            email_id: 邮件 ID
            token: 邮件系统认证 token（已废弃）

        Returns:
            预提取结果
        """
        try:
            # 使用 Portal 专用接口
            url = f"{self.email_api_url}/api/task-extractions/portal/emails/{email_id}/extraction"
            response = requests.get(
                url,
                headers=self._get_portal_headers(),
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
                    'error': '邮件不存在',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'error': f'获取提取结果失败: {response.status_code}',
                    'data': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取提取结果失败: {str(e)}',
                'data': None
            }

    def trigger_extraction(self, email_id: int, force: bool = False, token: Optional[str] = None) -> Dict[str, Any]:
        """
        触发任务提取（如果预提取失败或未完成）

        Args:
            email_id: 邮件 ID
            force: 是否强制重新提取
            token: 邮件系统认证 token（已废弃）

        Returns:
            触发结果
        """
        try:
            # 使用 Portal 专用接口
            url = f"{self.email_api_url}/api/task-extractions/portal/emails/{email_id}/extract"
            response = requests.post(
                url,
                params={'force': force},
                headers=self._get_portal_headers(),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'触发提取失败: {response.status_code}',
                    'data': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'触发提取失败: {str(e)}',
                'data': None
            }

    # ==================== 智能匹配接口 ====================

    def match_project_by_part_number(self, part_number: str) -> Optional[Dict[str, Any]]:
        """
        根据品番号匹配 Portal 项目

        Args:
            part_number: 品番号/部件号

        Returns:
            匹配的项目信息，或 None
        """
        if not part_number:
            return None

        db = SessionLocal()
        try:
            # 使用模糊匹配查询项目
            project = db.query(Project).filter(
                Project.part_number.ilike(f'%{part_number}%')
            ).first()

            if project:
                return {
                    'id': project.id,
                    'project_no': project.project_no,
                    'name': project.name,
                    'part_number': project.part_number,
                    'status': project.status.value if project.status else None
                }

            return None
        except Exception as e:
            print(f"[EmailIntegration] 项目匹配失败: {e}")
            return None
        finally:
            db.close()

    def match_employee_by_name(self, name: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        根据姓名匹配 HR 员工

        Args:
            name: 员工姓名
            token: 认证 token

        Returns:
            匹配的员工信息，或 None
        """
        if not name:
            return None

        try:
            # 调用 HR 系统搜索员工
            result = integration_service.get_employees(
                search=name,
                page=1,
                page_size=5,
                token=token
            )

            if result.get('success') and result.get('data'):
                items = result['data'].get('items', [])
                # 精确匹配姓名
                for emp in items:
                    emp_name = emp.get('name') or emp.get('full_name') or ''
                    if emp_name == name:
                        return {
                            'id': emp.get('id'),
                            'name': emp_name,
                            'emp_no': emp.get('emp_no'),
                            'department': emp.get('department_name') or emp.get('department')
                        }
                # 没有精确匹配，返回第一个（模糊匹配）
                if items:
                    emp = items[0]
                    return {
                        'id': emp.get('id'),
                        'name': emp.get('name') or emp.get('full_name'),
                        'emp_no': emp.get('emp_no'),
                        'department': emp.get('department_name') or emp.get('department'),
                        'fuzzy': True  # 标记为模糊匹配
                    }

            return None
        except Exception as e:
            print(f"[EmailIntegration] 员工匹配失败: {e}")
            return None

    # ==================== 完整提取流程 ====================

    def extract_task_from_email(
        self,
        email_id: int,
        token: Optional[str] = None,
        portal_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从邮件提取任务信息（完整流程）

        1. 先查询预提取结果
        2. 如果有结果，进行项目/员工匹配
        3. 返回完整的任务数据

        Args:
            email_id: 邮件 ID
            token: 邮件系统认证 token
            portal_token: Portal 认证 token（用于 HR 匹配）

        Returns:
            {
                'success': True,
                'data': {
                    'extraction': { ... 提取的原始数据 },
                    'matched_project': { ... 匹配的项目 },
                    'matched_employee': { ... 匹配的员工 },
                    'task_data': { ... 可直接用于创建任务的数据 }
                }
            }
        """
        # 1. 获取预提取结果
        extraction_result = self.get_task_extraction(email_id, token)

        if not extraction_result.get('success'):
            return extraction_result

        extraction_data = extraction_result.get('data', {})
        status = extraction_data.get('status')

        if status == 'none':
            # 尚未提取，触发提取
            trigger_result = self.trigger_extraction(email_id, token=token)
            return {
                'success': True,
                'data': {
                    'status': 'triggered',
                    'message': '已触发任务提取，请稍后查询',
                    'extraction': None,
                    'matched_project': None,
                    'matched_employee': None,
                    'task_data': None
                }
            }

        if status == 'processing':
            return {
                'success': True,
                'data': {
                    'status': 'processing',
                    'message': '任务提取正在进行中，请稍后查询',
                    'extraction': None,
                    'matched_project': None,
                    'matched_employee': None,
                    'task_data': None
                }
            }

        if status == 'failed':
            return {
                'success': False,
                'error': extraction_data.get('error_message', '提取失败'),
                'data': {
                    'status': 'failed',
                    'error_message': extraction_data.get('error_message'),
                    'extraction': extraction_data.get('data'),
                    'matched_project': None,
                    'matched_employee': None,
                    'task_data': None
                }
            }

        # 2. 提取完成，获取数据
        extracted = extraction_data.get('data', {})

        # 3. 智能匹配项目
        matched_project = None
        part_number = extracted.get('part_number')
        if part_number:
            matched_project = self.match_project_by_part_number(part_number)

        # 4. 智能匹配员工
        matched_employee = None
        assignee_name = extracted.get('assignee_name')
        if assignee_name:
            matched_employee = self.match_employee_by_name(assignee_name, portal_token)

        # 5. 构建可直接用于创建任务的数据
        task_data = {
            'title': extracted.get('title', ''),
            'description': extracted.get('description', ''),
            'task_type': extracted.get('task_type', 'general'),
            'priority': extracted.get('priority', 'normal'),
            'due_date': extracted.get('due_date'),
            'start_date': extracted.get('start_date'),
            'action_items': extracted.get('action_items', []),
            # 匹配结果
            'project_id': matched_project.get('id') if matched_project else None,
            'assigned_to_id': matched_employee.get('id') if matched_employee else None,
            # 来源追踪
            'source_email_id': email_id
        }

        # 6. 构建可直接用于创建项目的数据
        project_data = {
            'name': extracted.get('project_name', ''),
            'description': extracted.get('description', ''),
            'customer_name': extracted.get('customer_name', ''),
            'order_no': extracted.get('order_no', ''),
            'part_number': extracted.get('part_number', ''),
            'priority': extracted.get('priority', 'normal'),
            'planned_start_date': extracted.get('start_date'),
            'planned_end_date': extracted.get('due_date'),
            # 来源追踪
            'source_email_id': email_id
        }

        return {
            'success': True,
            'data': {
                'status': 'completed',
                'extraction': extracted,
                'matched_project': matched_project,
                'matched_employee': matched_employee,
                'task_data': task_data,
                'project_data': project_data,
                'confidence': extracted.get('confidence', {})
            }
        }

    # ==================== 健康检查 ====================

    def check_health(self) -> Dict[str, Any]:
        """检查邮件系统健康状态"""
        try:
            response = requests.get(
                f"{self.email_api_url}/health",
                timeout=5,
                proxies=self.no_proxy
            )
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'url': self.email_api_url,
                'response_code': response.status_code
            }
        except Exception as e:
            return {
                'status': 'unreachable',
                'url': self.email_api_url,
                'error': str(e)
            }


# 创建单例实例
email_integration_service = EmailIntegrationService()
