"""
P1-10: 分页参数验证工具
提供统一的分页参数验证，防止恶意参数攻击

使用方式:
    from shared.pagination import get_pagination_params, validate_pagination

    # 方式1：直接获取验证后的参数
    page, per_page = get_pagination_params()

    # 方式2：验证已有参数
    page = validate_pagination(page, per_page)
"""

from flask import request


# 默认配置
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MIN_PAGE = 1
MIN_PER_PAGE = 1
MAX_PER_PAGE = 1000  # 防止单次请求返回过多数据


def get_pagination_params(
    default_page: int = DEFAULT_PAGE,
    default_per_page: int = DEFAULT_PER_PAGE,
    max_per_page: int = MAX_PER_PAGE,
    page_param: str = 'page',
    per_page_param: str = None  # 如果为 None，自动检测常见参数名
) -> tuple:
    """
    从 Flask request.args 获取并验证分页参数

    Args:
        default_page: 默认页码
        default_per_page: 默认每页数量
        max_per_page: 最大每页数量限制
        page_param: 页码参数名
        per_page_param: 每页数量参数名（自动检测: per_page, page_size, pageSize）

    Returns:
        tuple: (page, per_page) 验证后的分页参数

    Example:
        page, per_page = get_pagination_params()
        query.offset((page - 1) * per_page).limit(per_page)
    """
    # 获取 page 参数
    try:
        page = int(request.args.get(page_param, default_page))
    except (ValueError, TypeError):
        page = default_page

    # 自动检测 per_page 参数名
    if per_page_param is None:
        for param_name in ['per_page', 'page_size', 'pageSize']:
            val = request.args.get(param_name)
            if val is not None:
                per_page_param = param_name
                break
        if per_page_param is None:
            per_page_param = 'per_page'

    # 获取 per_page 参数
    try:
        per_page = int(request.args.get(per_page_param, default_per_page))
    except (ValueError, TypeError):
        per_page = default_per_page

    # 验证边界
    page = max(MIN_PAGE, page)
    per_page = max(MIN_PER_PAGE, min(per_page, max_per_page))

    return page, per_page


def validate_pagination(
    page: int,
    per_page: int,
    max_per_page: int = MAX_PER_PAGE
) -> tuple:
    """
    验证已有的分页参数

    Args:
        page: 页码
        per_page: 每页数量
        max_per_page: 最大每页数量限制

    Returns:
        tuple: (page, per_page) 验证后的分页参数
    """
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = DEFAULT_PAGE

    try:
        per_page = int(per_page)
    except (ValueError, TypeError):
        per_page = DEFAULT_PER_PAGE

    # 验证边界
    page = max(MIN_PAGE, page)
    per_page = max(MIN_PER_PAGE, min(per_page, max_per_page))

    return page, per_page


def paginate_query(query, page: int, per_page: int):
    """
    对 SQLAlchemy 查询应用分页

    Args:
        query: SQLAlchemy Query 对象
        page: 页码 (已验证)
        per_page: 每页数量 (已验证)

    Returns:
        分页后的查询结果
    """
    return query.offset((page - 1) * per_page).limit(per_page)


def make_pagination_response(items, total: int, page: int, per_page: int) -> dict:
    """
    生成标准的分页响应格式

    Args:
        items: 当前页数据列表
        total: 总记录数
        page: 当前页码
        per_page: 每页数量

    Returns:
        dict: 包含分页信息的响应字典
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
    }
