"""
SSO 认证配置 - 所有子系统必须使用相同的配置

JZC 系统使用 SSO 单点登录架构：
- Portal 签发 JWT Token
- 所有子系统使用相同的 JWT_SECRET_KEY 验证 Token
- 认证数据库统一使用 cncplan

配置不一致会导致：
- Token 验证失败 (401/503)
- 用户无法跨系统访问
"""
import os
import warnings


# 生产环境 JWT 密钥（必须在所有系统中一致）
PRODUCTION_JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

# 开发环境默认密钥 - 仅用于本地开发
DEV_JWT_SECRET_KEY = 'jzc-dev-shared-secret-key-2025'

# 认证数据库配置 - 必须统一使用 cncplan
AUTH_DB_CONFIG = {
    'user': os.getenv('AUTH_DB_USER', 'app'),
    'password': os.getenv('AUTH_DB_PASSWORD', 'app'),
    'host': os.getenv('AUTH_DB_HOST', 'localhost'),
    'database': os.getenv('AUTH_DB_NAME', 'cncplan'),  # 必须是 cncplan
}

# 支持的子系统列表
SUBSYSTEMS = [
    'Portal',      # SSO 认证中心
    'HR',          # 人力资源
    'account',     # 账户管理
    '报价',        # 报价系统
    '采购',        # 采购系统
    'SHM',         # 出货管理
    'CRM',         # 客户关系
    'SCM',         # 仓库管理
    'EAM',         # 设备资产
    'MES',         # 制造执行
    'Dashboard',   # 可视化
]


def get_jwt_secret_key():
    """
    获取 JWT 密钥

    生产环境: 使用 JWT_SECRET_KEY 环境变量
    开发环境: 使用默认开发密钥
    """
    flask_env = os.getenv('FLASK_ENV', 'development')

    if flask_env == 'production':
        if not PRODUCTION_JWT_SECRET_KEY:
            raise RuntimeError(
                "生产环境必须设置 JWT_SECRET_KEY 环境变量。\n"
                "请确保 JWT_SECRET_KEY 与 Portal 系统一致。"
            )
        return PRODUCTION_JWT_SECRET_KEY

    # 开发环境
    if PRODUCTION_JWT_SECRET_KEY:
        return PRODUCTION_JWT_SECRET_KEY

    warnings.warn(
        "使用开发环境默认 JWT 密钥。生产环境请设置 JWT_SECRET_KEY 环境变量。",
        UserWarning
    )
    return DEV_JWT_SECRET_KEY


def validate_sso_config(raise_on_error=True):
    """
    验证 SSO 配置一致性

    Args:
        raise_on_error: 是否在错误时抛出异常 (默认 True)

    Returns:
        dict: {
            'valid': bool,
            'errors': list[str],
            'warnings': list[str]
        }
    """
    errors = []
    warnings_list = []

    flask_env = os.getenv('FLASK_ENV', 'development')

    # 1. 检查 AUTH_DB_NAME 必须是 cncplan
    auth_db_name = AUTH_DB_CONFIG['database']
    if auth_db_name != 'cncplan':
        errors.append(
            f"AUTH_DB_NAME 必须是 'cncplan'，当前是 '{auth_db_name}'。\n"
            "认证数据库必须统一使用 cncplan，否则用户数据不一致。"
        )

    # 2. 生产环境必须设置 JWT_SECRET_KEY
    if flask_env == 'production':
        if not PRODUCTION_JWT_SECRET_KEY:
            errors.append(
                "生产环境必须设置 JWT_SECRET_KEY 环境变量。\n"
                "请从 Portal 系统的 .env 文件复制 JWT_SECRET_KEY。"
            )
    else:
        # 开发环境警告
        if not PRODUCTION_JWT_SECRET_KEY:
            warnings_list.append(
                "开发环境未设置 JWT_SECRET_KEY，使用默认开发密钥。\n"
                "如果需要与其他本地服务通信，请确保所有系统使用相同的密钥。"
            )

    # 3. 检查 SECRET_KEY 是否与 JWT_SECRET_KEY 一致
    secret_key = os.getenv('SECRET_KEY')
    if secret_key and PRODUCTION_JWT_SECRET_KEY:
        if secret_key != PRODUCTION_JWT_SECRET_KEY:
            warnings_list.append(
                "SECRET_KEY 与 JWT_SECRET_KEY 不一致。\n"
                "建议使用相同的值以避免混淆。"
            )

    result = {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings_list,
        'environment': flask_env,
        'auth_db': auth_db_name,
        'jwt_key_set': bool(PRODUCTION_JWT_SECRET_KEY),
    }

    if raise_on_error and errors:
        error_msg = "SSO 配置错误:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)

    return result


def print_config_status():
    """打印当前配置状态（用于调试）"""
    result = validate_sso_config(raise_on_error=False)

    print("=" * 50)
    print("JZC SSO 配置状态")
    print("=" * 50)
    print(f"环境: {result['environment']}")
    print(f"认证数据库: {result['auth_db']}")
    print(f"JWT密钥已设置: {'是' if result['jwt_key_set'] else '否'}")
    print()

    if result['valid']:
        print("✅ 配置验证通过")
    else:
        print("❌ 配置验证失败:")
        for error in result['errors']:
            print(f"  - {error}")

    if result['warnings']:
        print("\n⚠️ 警告:")
        for warning in result['warnings']:
            print(f"  - {warning}")

    print("=" * 50)
    return result['valid']


if __name__ == '__main__':
    # 直接运行时打印配置状态
    import sys
    valid = print_config_status()
    sys.exit(0 if valid else 1)
