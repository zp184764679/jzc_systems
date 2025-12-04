# routes/pr/common.py
# PR模块公共工具函数

_STATUS_MAP_ZH = {
    "submitted": "待主管审批",
    "supervisor_approved": "待填写价格",
    "price_filled": "待厂长审批",
    "admin_approved": "厂长已批准",  # 兼容旧状态
    "pending_super_admin": "待总经理审批",
    "super_admin_approved": "总经理已批准",  # 兼容旧状态
    "completed": "已完成",
    "approved": "已批准",
    "rejected": "已驳回",
    "draft": "草稿",
    "cancelled": "已失效",
}

_URGENCY_MAP_ZH = {
    "high": "高",
    "medium": "中",
    "low": "低",
    "normal": "中",
}

def zh_status(s):
    """将英文状态转为中文"""
    return _STATUS_MAP_ZH.get(s, s or "-")

def zh_urgency(u):
    """将英文紧急程度转为中文"""
    return _URGENCY_MAP_ZH.get(u, u or "-")

def iso(dt):
    """将datetime转为ISO格式字符串"""
    return dt.isoformat(timespec='seconds') if dt else None

def _normalize_urgency_input(u: str) -> str:
    """
    入库前的容错：支持中文传参（高/中/低），以及 high/medium/low/normal。
    存库仍用英文，前端展示走 zh_urgency。
    """
    if not u:
        return "medium"
    u = str(u).strip().lower()
    cn_map = {"高": "high", "中": "medium", "低": "low", "正常": "medium"}
    if u in ("high", "medium", "low", "normal"):
        return u
    return cn_map.get(u, "medium")


# =========================
# 用户信息缓存 (避免重复查询)
# =========================
_user_cache = {}

def get_owner_info(owner_id):
    """
    获取申请人信息（从统一数据源 account.users）
    带简单缓存，避免重复查询

    返回: {"username": ..., "department": ..., "full_name": ...} 或 None
    """
    if not owner_id:
        return None

    # 检查缓存
    if owner_id in _user_cache:
        return _user_cache[owner_id]

    try:
        from utils.auth import get_user_by_id
        user = get_user_by_id(owner_id)
        if user:
            info = {
                "username": user.username,
                "full_name": user.full_name or user.username,
                "department": user.department_name or "",
            }
            _user_cache[owner_id] = info
            return info
    except Exception as e:
        print(f"获取用户信息失败: {e}")

    return None


def clear_user_cache():
    """清除用户缓存"""
    global _user_cache
    _user_cache = {}