"""
Email Integration Service - 邮件集成服务
提供与供应商邮件翻译系统的数据交互，获取邮件列表和预提取的任务信息
"""
import os
import re
import json
import time
import requests
from functools import wraps
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

from models import SessionLocal
from models.project import Project
from services.integration_service import integration_service


# P1-2: 请求重试装饰器
def with_retry(max_retries: int = 3, initial_delay: float = 0.5, backoff: float = 2.0,
               retry_exceptions: tuple = (requests.exceptions.ConnectionError,
                                          requests.exceptions.Timeout)):
    """
    带指数退避的重试装饰器

    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        backoff: 退避因子
        retry_exceptions: 触发重试的异常类型

    Usage:
        @with_retry(max_retries=3)
        def my_function():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                        delay *= backoff
                        continue
                    raise

            # 如果所有重试都失败，抛出最后一个异常
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


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
        # P0-3: 移除硬编码默认值，生产环境必须配置
        self.portal_service_token = os.getenv('PORTAL_SERVICE_TOKEN')
        if not self.portal_service_token:
            import warnings
            warnings.warn(
                'PORTAL_SERVICE_TOKEN 环境变量未配置，邮件集成功能将不可用。'
                '请在 .env 文件中设置 PORTAL_SERVICE_TOKEN',
                RuntimeWarning
            )

        # P1-1: 服务降级策略 - 健康检查缓存
        self._service_available = None
        self._last_health_check = None
        self._health_check_interval = 60  # 缓存60秒

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
        if not self.portal_service_token:
            raise ValueError('PORTAL_SERVICE_TOKEN 未配置，无法访问邮件系统')
        return {
            'Content-Type': 'application/json',
            'X-Portal-Token': self.portal_service_token
        }

    def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = 3,
        **kwargs
    ) -> requests.Response:
        """
        带重试的 HTTP 请求

        P1-2: 请求重试机制 - 对网络错误和超时进行自动重试

        Args:
            method: HTTP 方法 (get/post/put/delete)
            url: 请求 URL
            max_retries: 最大重试次数
            **kwargs: 传递给 requests 的其他参数

        Returns:
            requests.Response
        """
        delay = 0.5
        last_exception = None
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('proxies', self.no_proxy)

        for attempt in range(max_retries + 1):
            try:
                response = getattr(requests, method.lower())(url, **kwargs)
                return response
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= 2  # 指数退避
                    continue
                raise

        if last_exception:
            raise last_exception

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

    # ==================== 邮件同步接口 ====================

    def sync_emails(self, since_days: int = 7) -> Dict[str, Any]:
        """
        触发邮件系统同步最新邮件

        从 IMAP 服务器拉取最新邮件到邮件翻译系统数据库

        Args:
            since_days: 同步最近多少天的邮件（默认7天）

        Returns:
            {
                'success': True,
                'message': '已触发 X 个邮箱账户的同步',
                'synced_accounts': X,
                'since_days': 7
            }
        """
        try:
            url = f"{self.email_api_url}/api/task-extractions/portal/sync"
            response = requests.post(
                url,
                params={'since_days': since_days},
                headers=self._get_portal_headers(),
                timeout=self.timeout,
                proxies=self.no_proxy
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    **response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'同步请求失败: {response.status_code}',
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
                'error': '同步请求超时',
                'data': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'同步请求失败: {str(e)}',
                'data': None
            }

    # ==================== 导入历史管理 (P0-2) ====================

    def check_duplicate_import(self, email_id: int) -> Dict[str, Any]:
        """
        检查邮件是否已经被导入过

        Args:
            email_id: 邮件翻译系统的邮件ID

        Returns:
            {
                'is_duplicate': bool,
                'existing_imports': [...],  # 已存在的导入记录
                'message': str
            }
        """
        try:
            from models.email_import_history import EmailImportHistory
            from models.task import Task

            db = SessionLocal()
            try:
                # 查询该邮件的导入历史
                existing_imports = db.query(EmailImportHistory).filter(
                    EmailImportHistory.email_id == email_id
                ).order_by(EmailImportHistory.imported_at.desc()).all()

                if not existing_imports:
                    return {
                        'is_duplicate': False,
                        'existing_imports': [],
                        'message': '该邮件未被导入过'
                    }

                # 构建已导入记录信息
                import_records = []
                for imp in existing_imports:
                    record = {
                        'id': imp.id,
                        'imported_at': imp.imported_at.isoformat() if imp.imported_at else None,
                        'imported_by_name': imp.imported_by_name,
                        'import_mode': imp.import_mode.value if imp.import_mode else 'task',
                        'task_id': imp.task_id,
                        'project_id': imp.project_id,
                    }
                    # 如果有关联任务，获取任务信息
                    if imp.task_id:
                        task = db.query(Task).filter(Task.id == imp.task_id).first()
                        if task:
                            record['task_title'] = task.title
                            record['task_no'] = task.task_no
                    import_records.append(record)

                return {
                    'is_duplicate': True,
                    'existing_imports': import_records,
                    'message': f'该邮件已被导入过 {len(import_records)} 次'
                }
            finally:
                db.close()
        except Exception as e:
            return {
                'is_duplicate': False,
                'existing_imports': [],
                'message': f'检查重复导入时出错: {str(e)}',
                'error': str(e)
            }

    def record_import(
        self,
        email_id: int,
        task_id: Optional[int],
        project_id: Optional[int],
        user_id: int,
        user_name: str,
        email_data: Optional[Dict] = None,
        extraction_data: Optional[Dict] = None,
        matched_project_id: Optional[int] = None,
        matched_employee_id: Optional[int] = None,
        import_mode: str = 'task'
    ) -> Dict[str, Any]:
        """
        记录邮件导入历史

        Args:
            email_id: 邮件翻译系统的邮件ID
            task_id: 创建的任务ID（如果有）
            project_id: 创建/关联的项目ID（如果有）
            user_id: 导入用户ID
            user_name: 导入用户姓名
            email_data: 邮件信息（subject, from, message_id等）
            extraction_data: AI提取的数据快照
            matched_project_id: 智能匹配的项目ID
            matched_employee_id: 智能匹配的员工ID
            import_mode: 导入模式 (task/project/task_and_project)

        Returns:
            {'success': bool, 'import_history_id': int, 'error': str}
        """
        try:
            from models.email_import_history import EmailImportHistory, ImportMode

            db = SessionLocal()
            try:
                # 创建导入历史记录
                history = EmailImportHistory(
                    email_id=email_id,
                    email_message_id=email_data.get('message_id') if email_data else None,
                    email_subject=email_data.get('subject_translated') or email_data.get('subject_original') if email_data else None,
                    email_from=email_data.get('sender') or email_data.get('from') if email_data else None,
                    email_received_at=email_data.get('received_at') if email_data else None,
                    task_id=task_id,
                    project_id=project_id,
                    import_mode=ImportMode(import_mode) if import_mode in ['task', 'project', 'task_and_project'] else ImportMode.TASK,
                    imported_by=user_id,
                    imported_by_name=user_name,
                    extraction_data=extraction_data,
                    matched_project_id=matched_project_id,
                    matched_employee_id=matched_employee_id,
                )

                db.add(history)
                db.commit()
                db.refresh(history)

                return {
                    'success': True,
                    'import_history_id': history.id,
                    'message': '导入记录已保存'
                }
            finally:
                db.close()
        except Exception as e:
            return {
                'success': False,
                'import_history_id': None,
                'error': f'记录导入历史时出错: {str(e)}'
            }

    def get_import_history(
        self,
        email_id: Optional[int] = None,
        task_id: Optional[int] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        查询导入历史

        Args:
            email_id: 按邮件ID筛选
            task_id: 按任务ID筛选
            user_id: 按导入用户筛选
            page: 页码
            page_size: 每页数量

        Returns:
            {'success': bool, 'data': {...}, 'error': str}
        """
        try:
            from models.email_import_history import EmailImportHistory

            db = SessionLocal()
            try:
                query = db.query(EmailImportHistory)

                if email_id:
                    query = query.filter(EmailImportHistory.email_id == email_id)
                if task_id:
                    query = query.filter(EmailImportHistory.task_id == task_id)
                if user_id:
                    query = query.filter(EmailImportHistory.imported_by == user_id)

                # 统计总数
                total = query.count()

                # 分页
                query = query.order_by(EmailImportHistory.imported_at.desc())
                query = query.offset((page - 1) * page_size).limit(page_size)

                items = [item.to_dict() for item in query.all()]

                return {
                    'success': True,
                    'data': {
                        'items': items,
                        'total': total,
                        'page': page,
                        'page_size': page_size
                    }
                }
            finally:
                db.close()
        except Exception as e:
            return {
                'success': False,
                'error': f'查询导入历史时出错: {str(e)}',
                'data': None
            }

    # ==================== 任务创建接口 ====================

    def create_project_from_email(
        self,
        email_id: int,
        project_data: Dict[str, Any],
        user_id: int,
        user_name: str
    ) -> Dict[str, Any]:
        """
        从邮件创建项目

        Args:
            email_id: 邮件翻译系统的邮件ID
            project_data: 项目数据 (name, description, customer_name, order_no, part_number, etc.)
            user_id: 创建用户ID
            user_name: 创建用户姓名

        Returns:
            {'success': bool, 'project': {...}, 'error': str}
        """
        try:
            from models.project import Project, ProjectStatus
            from models import SessionLocal

            db = SessionLocal()
            try:
                # 创建项目
                project = Project(
                    name=project_data.get('name', f'邮件项目-{email_id}'),
                    description=project_data.get('description'),
                    customer_name=project_data.get('customer_name'),
                    order_no=project_data.get('order_no'),
                    part_number=project_data.get('part_number'),
                    priority=project_data.get('priority', 'normal'),
                    status=ProjectStatus.ACTIVE,
                    created_by=user_id,
                    source_email_id=email_id,
                )

                # 设置日期
                if project_data.get('planned_start_date'):
                    from datetime import datetime
                    try:
                        project.planned_start_date = datetime.fromisoformat(
                            project_data['planned_start_date'].replace('Z', '+00:00')
                        )
                    except:
                        pass

                if project_data.get('planned_end_date'):
                    from datetime import datetime
                    try:
                        project.planned_end_date = datetime.fromisoformat(
                            project_data['planned_end_date'].replace('Z', '+00:00')
                        )
                    except:
                        pass

                db.add(project)
                db.commit()
                db.refresh(project)

                return {
                    'success': True,
                    'project': project.to_dict() if hasattr(project, 'to_dict') else {
                        'id': project.id,
                        'name': project.name,
                        'project_no': getattr(project, 'project_no', None),
                    }
                }
            finally:
                db.close()
        except Exception as e:
            print(f"[EmailIntegration] 创建项目失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'创建项目失败: {str(e)}',
                'project': None
            }

    def create_task_from_email(
        self,
        email_id: int,
        project_id: int,
        task_data: Dict[str, Any],
        email_data: Dict[str, Any],
        user_id: int,
        user_name: str,
        create_project: bool = False,
        project_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从邮件创建任务

        Args:
            email_id: 邮件翻译系统的邮件ID
            project_id: 关联的项目ID（如果已有）
            task_data: 任务数据
            email_data: 邮件数据（用于记录导入历史）
            user_id: 创建用户ID
            user_name: 创建用户姓名
            create_project: 是否需要创建新项目
            project_data: 新项目数据（create_project=True时必需）

        Returns:
            {
                'success': bool,
                'project': {...},
                'task': {...},
                'created_project': bool,
                'error': str
            }
        """
        try:
            from models.task import Task, TaskStatus, TaskPriority
            from models import SessionLocal

            db = SessionLocal()
            created_project = None

            try:
                # 1. 如果需要创建项目
                if create_project and project_data:
                    project_result = self.create_project_from_email(
                        email_id=email_id,
                        project_data=project_data,
                        user_id=user_id,
                        user_name=user_name
                    )
                    if not project_result.get('success'):
                        return project_result
                    created_project = project_result['project']
                    project_id = created_project['id']

                # 2. 验证项目存在
                if not project_id:
                    return {
                        'success': False,
                        'error': '未指定项目ID'
                    }

                # 3. 创建任务
                # 转换优先级
                priority_map = {
                    'low': TaskPriority.LOW,
                    'normal': TaskPriority.MEDIUM,
                    'high': TaskPriority.HIGH,
                    'urgent': TaskPriority.URGENT
                }
                priority = priority_map.get(task_data.get('priority', 'normal'), TaskPriority.MEDIUM)

                task = Task(
                    title=task_data.get('title', f'邮件任务-{email_id}'),
                    description=task_data.get('description'),
                    project_id=project_id,
                    priority=priority,
                    status=TaskStatus.TODO,
                    created_by=user_id,
                    assigned_to=task_data.get('assigned_to_id'),
                    source_email_id=email_id,
                    source_email_subject=email_data.get('subject_translated') or email_data.get('subject_original'),
                )

                # 设置日期
                if task_data.get('due_date'):
                    from datetime import datetime
                    try:
                        task.due_date = datetime.fromisoformat(
                            task_data['due_date'].replace('Z', '+00:00')
                        )
                    except:
                        pass

                if task_data.get('start_date'):
                    from datetime import datetime
                    try:
                        task.start_date = datetime.fromisoformat(
                            task_data['start_date'].replace('Z', '+00:00')
                        )
                    except:
                        pass

                db.add(task)
                db.commit()
                db.refresh(task)

                # 4. 如果有待办事项，创建 checklist
                action_items = task_data.get('action_items', [])
                if action_items and hasattr(task, 'checklist'):
                    from models.task import TaskChecklistItem
                    for item in action_items:
                        if item and isinstance(item, str):
                            checklist_item = TaskChecklistItem(
                                task_id=task.id,
                                content=item,
                                is_done=False
                            )
                            db.add(checklist_item)
                    db.commit()

                # 5. 记录导入历史
                self.record_import(
                    email_id=email_id,
                    task_id=task.id,
                    project_id=project_id,
                    user_id=user_id,
                    user_name=user_name,
                    email_data=email_data,
                    extraction_data=task_data,
                    import_mode='task_and_project' if create_project else 'task'
                )

                return {
                    'success': True,
                    'project': created_project,
                    'task': task.to_dict() if hasattr(task, 'to_dict') else {
                        'id': task.id,
                        'title': task.title,
                        'task_no': getattr(task, 'task_no', None),
                    },
                    'project_id': project_id,
                    'created_project': create_project
                }
            finally:
                db.close()
        except Exception as e:
            print(f"[EmailIntegration] 创建任务失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'创建任务失败: {str(e)}',
                'project': created_project if 'created_project' in dir() else None,
                'task': None
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
            is_healthy = response.status_code == 200
            # 更新缓存
            self._service_available = is_healthy
            self._last_health_check = datetime.now()
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'url': self.email_api_url,
                'response_code': response.status_code
            }
        except Exception as e:
            # 更新缓存
            self._service_available = False
            self._last_health_check = datetime.now()
            return {
                'status': 'unreachable',
                'url': self.email_api_url,
                'error': str(e)
            }

    def is_service_available(self) -> bool:
        """
        检查邮件系统是否可用（带缓存）

        P1-1: 服务降级策略 - 缓存健康检查结果避免频繁请求

        Returns:
            bool: 服务是否可用
        """
        now = datetime.now()

        # 如果有缓存且未过期，直接返回
        if (self._last_health_check and
            self._service_available is not None and
            (now - self._last_health_check).seconds < self._health_check_interval):
            return self._service_available

        # 执行健康检查并更新缓存
        result = self.check_health()
        return result.get('status') == 'healthy'

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态信息（含缓存状态）

        Returns:
            服务状态详情
        """
        is_available = self.is_service_available()
        return {
            'available': is_available,
            'url': self.email_api_url,
            'cached': self._last_health_check is not None,
            'last_check': self._last_health_check.isoformat() if self._last_health_check else None,
            'next_check_in': max(0, self._health_check_interval - (datetime.now() - self._last_health_check).seconds) if self._last_health_check else 0,
            'token_configured': bool(self.portal_service_token)
        }


# 创建单例实例
email_integration_service = EmailIntegrationService()
