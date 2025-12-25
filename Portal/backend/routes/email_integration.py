"""
Email Integration Routes - 邮件集成 API
提供邮件列表、任务提取等接口供前端调用
"""
from flask import Blueprint, request, jsonify
from functools import wraps
import os

from shared.auth import verify_token
from services.email_integration_service import email_integration_service

email_integration_bp = Blueprint('email_integration', __name__, url_prefix='/api/emails')


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '缺少认证信息'}), 401

        token = auth_header.split(' ')[1]
        payload = verify_token(token)

        if not payload:
            return jsonify({'error': 'Token无效或已过期'}), 401

        # 将用户信息和 token 存入 request 上下文
        request.current_user = payload
        request.portal_token = token
        return f(*args, **kwargs)
    return decorated


def get_email_token():
    """获取邮件系统认证 token（从请求头或环境变量）"""
    # 优先从自定义请求头获取
    email_token = request.headers.get('X-Email-Token')
    if email_token:
        return email_token

    # 尝试从环境变量获取服务账户 token
    service_token = os.getenv('EMAIL_SERVICE_TOKEN')
    if service_token:
        return service_token

    # 回退：使用 Portal token（如果邮件系统信任 Portal token）
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]

    return None


# ==================== 邮件列表接口 ====================

@email_integration_bp.route('', methods=['GET'])
@require_auth
def get_emails():
    """
    获取邮件列表

    Query Parameters:
        keyword: 搜索关键词
        page: 页码 (默认 1)
        page_size: 每页数量 (默认 20)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        translation_status: 翻译状态筛选

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
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    translation_status = request.args.get('translation_status')

    email_token = get_email_token()

    result = email_integration_service.get_emails(
        keyword=keyword,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
        translation_status=translation_status,
        token=email_token
    )

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 503


@email_integration_bp.route('/<int:email_id>', methods=['GET'])
@require_auth
def get_email(email_id: int):
    """
    获取邮件详情

    Path Parameters:
        email_id: 邮件 ID

    Returns:
        邮件详情
    """
    email_token = get_email_token()

    result = email_integration_service.get_email(email_id, token=email_token)

    if result.get('success'):
        return jsonify(result), 200
    elif result.get('error') == '邮件不存在':
        return jsonify(result), 404
    else:
        return jsonify(result), 503


# ==================== 任务提取接口 ====================

@email_integration_bp.route('/<int:email_id>/task-extraction', methods=['GET'])
@require_auth
def get_task_extraction(email_id: int):
    """
    获取邮件的预提取任务信息

    Path Parameters:
        email_id: 邮件 ID

    Returns:
        预提取结果
    """
    email_token = get_email_token()

    result = email_integration_service.get_task_extraction(email_id, token=email_token)

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 503


@email_integration_bp.route('/<int:email_id>/extract', methods=['POST'])
@require_auth
def extract_task_from_email(email_id: int):
    """
    从邮件提取任务信息（完整流程）

    包括：
    1. 获取预提取结果
    2. 智能匹配项目（根据品番号）
    3. 智能匹配负责人（根据姓名）
    4. 返回可直接创建任务的数据

    Path Parameters:
        email_id: 邮件 ID

    Returns:
        {
            'success': True,
            'data': {
                'status': 'completed',
                'extraction': { ... },
                'matched_project': { ... },
                'matched_employee': { ... },
                'task_data': { ... }
            }
        }
    """
    email_token = get_email_token()
    portal_token = request.portal_token

    result = email_integration_service.extract_task_from_email(
        email_id,
        token=email_token,
        portal_token=portal_token
    )

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 503


@email_integration_bp.route('/<int:email_id>/trigger-extraction', methods=['POST'])
@require_auth
def trigger_extraction(email_id: int):
    """
    手动触发任务提取

    用于未提取或提取失败的邮件

    Path Parameters:
        email_id: 邮件 ID

    Query Parameters:
        force: 是否强制重新提取 (默认 false)

    Returns:
        触发结果
    """
    email_token = get_email_token()
    force = request.args.get('force', 'false').lower() == 'true'

    result = email_integration_service.trigger_extraction(
        email_id,
        force=force,
        token=email_token
    )

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 503


# ==================== 邮件同步接口 ====================

@email_integration_bp.route('/sync', methods=['POST'])
@require_auth
def sync_emails():
    """
    触发邮件系统同步最新邮件

    从 IMAP 服务器拉取最新邮件到邮件翻译系统数据库

    Query Parameters:
        since_days: 同步最近多少天的邮件 (默认 7)

    Returns:
        {
            'success': True,
            'message': '已触发 X 个邮箱账户的同步',
            'synced_accounts': X
        }
    """
    since_days = request.args.get('since_days', 7, type=int)

    result = email_integration_service.sync_emails(since_days=since_days)

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 503


# ==================== 导入历史管理 (P0-2) ====================

@email_integration_bp.route('/<int:email_id>/check-duplicate', methods=['GET'])
@require_auth
def check_duplicate_import(email_id: int):
    """
    检查邮件是否已被导入过

    Path Parameters:
        email_id: 邮件 ID

    Returns:
        {
            'is_duplicate': True/False,
            'existing_imports': [...],
            'message': '...'
        }
    """
    result = email_integration_service.check_duplicate_import(email_id)
    return jsonify(result), 200


@email_integration_bp.route('/import-history', methods=['GET'])
@require_auth
def get_import_history():
    """
    查询导入历史

    Query Parameters:
        email_id: 按邮件ID筛选
        task_id: 按任务ID筛选
        user_id: 按导入用户筛选
        page: 页码 (默认 1)
        page_size: 每页数量 (默认 20)

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
    email_id = request.args.get('email_id', type=int)
    task_id = request.args.get('task_id', type=int)
    user_id = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    result = email_integration_service.get_import_history(
        email_id=email_id,
        task_id=task_id,
        user_id=user_id,
        page=page,
        page_size=page_size
    )

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 500


# ==================== 任务创建接口 ====================

@email_integration_bp.route('/<int:email_id>/create-task', methods=['POST'])
@require_auth
def create_task_from_email(email_id: int):
    """
    从邮件创建任务

    Path Parameters:
        email_id: 邮件 ID

    Request Body:
        {
            "project_id": 123,           # 可选，已有项目 ID
            "create_project": false,      # 是否创建新项目
            "project_data": {...},        # 新项目数据（create_project=true 时必需）
            "task_data": {...},           # 任务数据
            "email_data": {...}           # 邮件数据（用于记录）
        }

    Returns:
        {
            'success': True,
            'project': {...},    # 关联的项目
            'task': {...},       # 创建的任务
            'created_project': bool
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': '请求数据不能为空'}), 400

    user = request.current_user
    user_id = user.get('user_id') or user.get('id')
    user_name = user.get('name') or user.get('username') or '未知用户'

    project_id = data.get('project_id')
    create_project = data.get('create_project', False)
    project_data = data.get('project_data', {})
    task_data = data.get('task_data', {})
    email_data = data.get('email_data', {})

    # 验证必要参数
    if not project_id and not create_project:
        return jsonify({
            'success': False,
            'error': '必须指定 project_id 或设置 create_project=true'
        }), 400

    if create_project and not project_data.get('name'):
        return jsonify({
            'success': False,
            'error': '创建新项目时必须提供项目名称'
        }), 400

    result = email_integration_service.create_task_from_email(
        email_id=email_id,
        project_id=project_id,
        task_data=task_data,
        email_data=email_data,
        user_id=user_id,
        user_name=user_name,
        create_project=create_project,
        project_data=project_data
    )

    if result.get('success'):
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@email_integration_bp.route('/<int:email_id>/match-project', methods=['GET'])
@require_auth
def match_project(email_id: int):
    """
    根据邮件信息匹配项目

    Path Parameters:
        email_id: 邮件 ID

    Query Parameters:
        part_number: 品番号
        customer_name: 客户名称
        order_no: 订单号

    Returns:
        {
            'success': True,
            'matched_project': {...} 或 null
        }
    """
    part_number = request.args.get('part_number')
    customer_name = request.args.get('customer_name')
    order_no = request.args.get('order_no')

    matched_project = None

    # 尝试按品番号匹配
    if part_number:
        matched_project = email_integration_service.match_project_by_part_number(part_number)

    # TODO: 按客户名称和订单号匹配

    return jsonify({
        'success': True,
        'matched_project': matched_project
    }), 200


@email_integration_bp.route('/<int:email_id>/employees', methods=['GET'])
@require_auth
def get_employees(email_id: int):
    """
    获取可分配的员工列表（用于任务分配）

    Path Parameters:
        email_id: 邮件 ID（未使用，保持 API 一致性）

    Query Parameters:
        search: 搜索关键词
        page: 页码
        page_size: 每页数量

    Returns:
        员工列表
    """
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    portal_token = request.portal_token

    from services.integration_service import integration_service
    result = integration_service.get_employees(
        search=search,
        page=page,
        page_size=page_size,
        token=portal_token
    )

    if result.get('success'):
        return jsonify(result), 200
    else:
        return jsonify(result), 503


# ==================== 健康检查 ====================

@email_integration_bp.route('/health', methods=['GET'])
def check_email_system_health():
    """
    检查邮件系统健康状态

    Returns:
        {
            'status': 'healthy',
            'url': 'http://...',
            'response_code': 200
        }
    """
    result = email_integration_service.check_health()
    return jsonify(result), 200
