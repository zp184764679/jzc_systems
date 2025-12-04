#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
安全审计脚本 - 检查代码中的潜在安全问题
"""
import os
import re
from pathlib import Path

# 安全检查规则
SECURITY_PATTERNS = {
    "硬编码密码/密钥": [
        r"password\s*=\s*['\"](?!.*{|.*%s)[\w@#$%^&*()]+['\"]",
        r"secret\s*=\s*['\"](?!.*{|.*%s)[\w@#$%^&*()]+['\"]",
        r"api_key\s*=\s*['\"](?!.*{|.*%s)[\w@#$%^&*()]+['\"]",
    ],
    "SQL注入风险": [
        r"execute\s*\(\s*['\"].*%s.*['\"]",
        r"execute\s*\(\s*f['\"].*{.*}.*['\"]",
        r"\.raw\s*\(",
    ],
    "命令注入风险": [
        r"os\.system\s*\(",
        r"subprocess\.call\s*\(.+shell\s*=\s*True",
        r"eval\s*\(",
        r"exec\s*\(",
    ],
    "路径遍历风险": [
        r"open\s*\(.+\+.+\)",
        r"os\.path\.join\s*\(.+request\.",
    ],
    "敏感信息泄露": [
        r"print\s*\(.*(password|secret|token|key)",
        r"logger\.(info|debug|warning)\s*\(.*(password|secret|token|key)",
    ],
    "不安全的随机数": [
        r"random\.random\(",
        r"random\.randint\(",
    ],
    "调试模式": [
        r"DEBUG\s*=\s*True",
        r"debug\s*=\s*True",
    ],
}

# 需要检查的文件扩展名
CHECK_EXTENSIONS = ['.py']

# 排除目录
EXCLUDE_DIRS = ['venv', 'node_modules', '__pycache__', '.git', 'migrations']


def scan_file(file_path):
    """扫描单个文件"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')

        for category, patterns in SECURITY_PATTERNS.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    # 跳过注释行
                    if line.strip().startswith('#'):
                        continue

                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append({
                            'file': str(file_path),
                            'line': line_num,
                            'category': category,
                            'code': line.strip(),
                            'severity': get_severity(category)
                        })

    except Exception as e:
        print(f"⚠️  无法读取文件 {file_path}: {e}")

    return issues


def get_severity(category):
    """获取严重级别"""
    high_risk = ["SQL注入风险", "命令注入风险", "硬编码密码/密钥"]
    medium_risk = ["路径遍历风险", "敏感信息泄露"]

    if category in high_risk:
        return "🔴 高危"
    elif category in medium_risk:
        return "🟡 中危"
    else:
        return "🟢 低危"


def scan_directory(directory):
    """扫描目录"""
    all_issues = []

    for root, dirs, files in os.walk(directory):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if any(file.endswith(ext) for ext in CHECK_EXTENSIONS):
                file_path = Path(root) / file
                issues = scan_file(file_path)
                all_issues.extend(issues)

    return all_issues


def generate_report(issues):
    """生成报告"""
    if not issues:
        print("\n✅ 未发现明显的安全问题！")
        return

    print(f"\n⚠️  发现 {len(issues)} 个潜在安全问题:\n")

    # 按严重程度分组
    by_severity = {}
    for issue in issues:
        severity = issue['severity']
        if severity not in by_severity:
            by_severity[severity] = []
        by_severity[severity].append(issue)

    # 按严重程度输出
    for severity in ["🔴 高危", "🟡 中危", "🟢 低危"]:
        if severity in by_severity:
            print(f"\n{severity} 问题 ({len(by_severity[severity])} 个):")
            print("=" * 80)

            for issue in by_severity[severity]:
                rel_path = os.path.relpath(issue['file'], start=os.getcwd())
                print(f"\n📁 {rel_path}:{issue['line']}")
                print(f"   类别: {issue['category']}")
                print(f"   代码: {issue['code'][:100]}")


def main():
    """主函数"""
    print("🔍 开始安全审计...")
    print(f"📂 扫描目录: {os.getcwd()}")

    # 扫描当前目录
    issues = scan_directory(".")

    # 生成报告
    generate_report(issues)

    # 输出统计信息
    print("\n" + "=" * 80)
    print(f"\n📊 统计信息:")
    print(f"   总问题数: {len(issues)}")

    by_category = {}
    for issue in issues:
        cat = issue['category']
        by_category[cat] = by_category.get(cat, 0) + 1

    for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"   - {category}: {count}")

    print("\n💡 建议:")
    print("   1. 审查所有高危和中危问题")
    print("   2. 确认是否为误报")
    print("   3. 对于真实问题，立即修复")
    print("   4. 考虑添加代码安全扫描到CI/CD流程")


if __name__ == "__main__":
    main()
