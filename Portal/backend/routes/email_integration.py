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
