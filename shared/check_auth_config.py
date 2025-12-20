#!/usr/bin/env python3
"""
检查所有子系统的认证配置一致性

使用方法:
    python shared/check_auth_config.py          # 检查所有系统
    python shared/check_auth_config.py --fix    # 显示修复建议
    python shared/check_auth_config.py --json   # 输出 JSON 格式

返回码:
    0: 所有配置一致
    1: 发现配置不一致
    2: 脚本执行错误
"""
import os
import sys
import json
import argparse

# 需要检查的子系统
SYSTEMS = ['Portal', 'HR', 'account', '报价', '采购', 'SHM', 'CRM', 'SCM', 'EAM', 'MES', 'Dashboard']

# 必须一致的配置项
MUST_MATCH_KEYS = ['JWT_SECRET_KEY']

# 必须为特定值的配置项
REQUIRED_VALUES = {
    'AUTH_DB_NAME': 'cncplan',
}


def parse_env_file(env_path):
    """
    解析 .env 文件

    Args:
        env_path: .env 文件路径

    Returns:
        dict: 配置键值对
    """
    config = {}

    if not os.path.exists(env_path):
        return None

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                # 解析 KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # 去除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    config[key] = value

    except Exception as e:
        return {'_error': str(e)}

    return config


def check_all_systems(base_path):
    """
    检查所有子系统的配置

    Args:
        base_path: 项目根目录

    Returns:
        dict: 检查结果
    """
    results = {
        'systems': {},
        'errors': [],
        'warnings': [],
        'summary': {
            'total': 0,
            'found': 0,
            'valid': 0,
        }
    }

    # 收集所有系统的配置
    for system in SYSTEMS:
        system_path = os.path.join(base_path, system)
        env_path = os.path.join(system_path, 'backend', '.env')

        results['summary']['total'] += 1

        if not os.path.exists(system_path):
            results['systems'][system] = {
                'status': 'not_found',
                'message': '目录不存在',
            }
            continue

        config = parse_env_file(env_path)

        if config is None:
            results['systems'][system] = {
                'status': 'no_env',
                'message': '未找到 .env 文件',
            }
            continue

        if '_error' in config:
            results['systems'][system] = {
                'status': 'error',
                'message': config['_error'],
            }
            results['errors'].append(f"{system}: 读取 .env 失败 - {config['_error']}")
            continue

        results['summary']['found'] += 1
        results['systems'][system] = {
            'status': 'ok',
            'config': config,
        }

    # 比较 JWT_SECRET_KEY
    jwt_keys = {}
    for system, data in results['systems'].items():
        if data['status'] == 'ok':
            key = data['config'].get('JWT_SECRET_KEY', 'NOT_SET')
            jwt_keys[system] = key

    unique_keys = set(jwt_keys.values())
    if len(unique_keys) > 1:
        # 找出最常见的 key 作为"正确"的
        key_counts = {}
        for key in jwt_keys.values():
            key_counts[key] = key_counts.get(key, 0) + 1

        most_common_key = max(key_counts.keys(), key=lambda k: key_counts[k])

        for system, key in jwt_keys.items():
            if key != most_common_key:
                display_key = key[:20] + '...' if len(key) > 20 else key
                expected_key = most_common_key[:20] + '...' if len(most_common_key) > 20 else most_common_key
                results['errors'].append(
                    f"{system}: JWT_SECRET_KEY 不一致 (当前: {display_key}, 应为: {expected_key})"
                )
                results['systems'][system]['jwt_mismatch'] = True
    else:
        results['summary']['jwt_consistent'] = True

    # 检查 AUTH_DB_NAME
    for system, data in results['systems'].items():
        if data['status'] != 'ok':
            continue

        auth_db = data['config'].get('AUTH_DB_NAME', 'NOT_SET')
        expected = REQUIRED_VALUES.get('AUTH_DB_NAME', 'cncplan')

        if auth_db != expected and auth_db != 'NOT_SET':
            results['errors'].append(
                f"{system}: AUTH_DB_NAME 应为 '{expected}'，当前是 '{auth_db}'"
            )
            results['systems'][system]['auth_db_wrong'] = True

    # 计算有效系统数
    for system, data in results['systems'].items():
        if data['status'] == 'ok':
            if not data.get('jwt_mismatch') and not data.get('auth_db_wrong'):
                results['summary']['valid'] += 1

    return results


def print_results(results, show_fix=False):
    """
    打印检查结果

    Args:
        results: 检查结果
        show_fix: 是否显示修复建议
    """
    print("=" * 60)
    print("JZC 子系统认证配置一致性检查")
    print("=" * 60)
    print()

    # 系统状态概览
    print("系统状态:")
    for system, data in results['systems'].items():
        status = data['status']
        if status == 'ok':
            has_issues = data.get('jwt_mismatch') or data.get('auth_db_wrong')
            icon = "⚠️" if has_issues else "✅"
            msg = "配置异常" if has_issues else "正常"
        elif status == 'not_found':
            icon = "⏭️"
            msg = "目录不存在 (跳过)"
        elif status == 'no_env':
            icon = "📝"
            msg = "未找到 .env (可能未部署)"
        else:
            icon = "❌"
            msg = data.get('message', '错误')

        print(f"  {icon} {system}: {msg}")

    print()

    # 错误列表
    if results['errors']:
        print("❌ 发现以下问题:")
        for error in results['errors']:
            print(f"  - {error}")
        print()
    else:
        print("✅ 所有配置一致")
        print()

    # 警告列表
    if results['warnings']:
        print("⚠️ 警告:")
        for warning in results['warnings']:
            print(f"  - {warning}")
        print()

    # 统计
    summary = results['summary']
    print(f"统计: 检查 {summary['total']} 个系统, "
          f"找到 {summary['found']} 个 .env, "
          f"配置正确 {summary['valid']} 个")
    print()

    # 修复建议
    if show_fix and results['errors']:
        print("=" * 60)
        print("修复建议:")
        print("=" * 60)
        print()
        print("1. 确保所有系统的 JWT_SECRET_KEY 与 Portal 一致:")
        print("   - 打开 Portal/backend/.env")
        print("   - 复制 JWT_SECRET_KEY 的值")
        print("   - 粘贴到所有其他系统的 backend/.env 中")
        print()
        print("2. 确保所有系统的 AUTH_DB_NAME 为 'cncplan':")
        print("   AUTH_DB_NAME=cncplan")
        print()
        print("3. 重启所有后端服务:")
        print("   pm2 restart all")
        print()

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='检查 JZC 子系统认证配置一致性')
    parser.add_argument('--fix', action='store_true', help='显示修复建议')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    parser.add_argument('--path', type=str, help='项目根目录路径')

    args = parser.parse_args()

    # 确定项目根目录
    if args.path:
        base_path = args.path
    else:
        # 默认为脚本所在目录的上级
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(script_dir)

    if not os.path.exists(base_path):
        print(f"错误: 项目目录不存在: {base_path}")
        sys.exit(2)

    # 执行检查
    results = check_all_systems(base_path)

    # 输出结果
    if args.json:
        # JSON 格式输出时移除敏感配置
        safe_results = json.loads(json.dumps(results))
        for system, data in safe_results['systems'].items():
            if 'config' in data:
                # 只保留关键配置项的状态，不保留实际值
                config = data['config']
                data['config_status'] = {
                    'JWT_SECRET_KEY': 'set' if config.get('JWT_SECRET_KEY') else 'not_set',
                    'AUTH_DB_NAME': config.get('AUTH_DB_NAME', 'not_set'),
                }
                del data['config']

        print(json.dumps(safe_results, ensure_ascii=False, indent=2))
    else:
        print_results(results, show_fix=args.fix)

    # 返回码
    if results['errors']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
