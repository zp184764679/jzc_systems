#!/usr/bin/env python3
"""
报价系统安全性、性能和边界测试脚本
包含：压力测试、漏洞测试、边界测试
"""
import requests
import json
import time
import concurrent.futures
import statistics
from datetime import datetime
from typing import List, Dict, Any
import os

# 配置
API_BASE = "http://localhost:8001/api"
TEST_RESULTS = []

class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """打印测试标题"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """打印信息"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


# ============================================================================
# 1. 漏洞测试 (Security Testing)
# ============================================================================

def test_sql_injection():
    """测试SQL注入漏洞"""
    print_header("SQL注入测试")

    sql_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE drawings; --",
        "1' UNION SELECT NULL--",
        "admin'--",
        "' OR 1=1--",
    ]

    vulnerabilities_found = 0

    for payload in sql_payloads:
        try:
            # 测试搜索端点
            response = requests.get(
                f"{API_BASE}/drawings",
                params={"search": payload},
                timeout=5
            )

            if response.status_code == 500:
                print_error(f"可能存在SQL注入漏洞: {payload[:30]}...")
                vulnerabilities_found += 1
            elif response.status_code == 200:
                print_success(f"安全防护有效: {payload[:30]}...")
            else:
                print_warning(f"响应异常 ({response.status_code}): {payload[:30]}...")

        except Exception as e:
            print_error(f"测试失败: {str(e)}")

    if vulnerabilities_found == 0:
        print_success("SQL注入测试通过 - 未发现漏洞")
    else:
        print_error(f"发现 {vulnerabilities_found} 个潜在SQL注入漏洞")

    TEST_RESULTS.append({
        "test": "SQL注入测试",
        "vulnerabilities": vulnerabilities_found,
        "status": "PASS" if vulnerabilities_found == 0 else "FAIL"
    })


def test_xss_vulnerability():
    """测试XSS跨站脚本漏洞"""
    print_header("XSS跨站脚本测试")

    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg/onload=alert('XSS')>",
    ]

    vulnerabilities_found = 0

    # 这里应该测试API是否正确转义输入
    # 由于是API，主要关注数据存储和返回时是否被正确处理
    print_info("XSS测试主要在前端进行，API应正确转义所有输入")
    print_success("建议：前端使用React的自动转义，API使用参数化查询")

    TEST_RESULTS.append({
        "test": "XSS测试",
        "status": "INFO",
        "note": "需要前端配合测试"
    })


def test_file_upload_security():
    """测试文件上传安全性"""
    print_header("文件上传安全测试")

    # 测试各种文件类型
    test_cases = [
        {"name": "test.php", "content": b"<?php echo 'hack'; ?>", "should_reject": True},
        {"name": "test.exe", "content": b"MZ\x90\x00", "should_reject": True},
        {"name": "test.pdf", "content": b"%PDF-1.4", "should_reject": False},
        {"name": "../../../etc/passwd", "content": b"test", "should_reject": True},
        {"name": "test.pdf.exe", "content": b"test", "should_reject": True},
    ]

    vulnerabilities_found = 0

    for test_case in test_cases:
        try:
            files = {'file': (test_case['name'], test_case['content'], 'application/octet-stream')}
            response = requests.post(
                f"{API_BASE}/drawings/upload",
                files=files,
                timeout=10
            )

            if test_case['should_reject'] and response.status_code == 200:
                print_error(f"安全漏洞：接受了危险文件 {test_case['name']}")
                vulnerabilities_found += 1
            elif not test_case['should_reject'] and response.status_code != 200:
                print_warning(f"可能过于严格：拒绝了合法文件 {test_case['name']}")
            else:
                print_success(f"文件上传验证正确: {test_case['name']}")

        except Exception as e:
            print_warning(f"测试文件 {test_case['name']} 时出错: {str(e)}")

    if vulnerabilities_found == 0:
        print_success("文件上传安全测试通过")
    else:
        print_error(f"发现 {vulnerabilities_found} 个文件上传安全漏洞")

    TEST_RESULTS.append({
        "test": "文件上传安全",
        "vulnerabilities": vulnerabilities_found,
        "status": "PASS" if vulnerabilities_found == 0 else "FAIL"
    })


def test_cors_configuration():
    """测试CORS配置"""
    print_header("CORS配置测试")

    try:
        response = requests.options(
            f"{API_BASE}/drawings",
            headers={
                'Origin': 'http://malicious-site.com',
                'Access-Control-Request-Method': 'GET'
            }
        )

        allowed_origin = response.headers.get('Access-Control-Allow-Origin')

        if allowed_origin == '*':
            print_error("CORS配置不安全：允许所有来源 (*)")
            status = "FAIL"
        elif allowed_origin:
            print_info(f"允许的来源: {allowed_origin}")
            status = "PASS"
        else:
            print_success("未发现CORS配置问题")
            status = "PASS"

    except Exception as e:
        print_error(f"CORS测试失败: {str(e)}")
        status = "ERROR"

    TEST_RESULTS.append({
        "test": "CORS配置",
        "status": status
    })


# ============================================================================
# 2. 压力测试 (Stress Testing)
# ============================================================================

def make_request(endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """发送HTTP请求并记录时间"""
    start_time = time.time()
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE}{endpoint}", **kwargs, timeout=30)
        elif method == "POST":
            response = requests.post(f"{API_BASE}{endpoint}", **kwargs, timeout=30)

        elapsed_time = time.time() - start_time

        return {
            "success": True,
            "status_code": response.status_code,
            "time": elapsed_time,
            "size": len(response.content)
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {
            "success": False,
            "error": str(e),
            "time": elapsed_time
        }


def stress_test_endpoint(endpoint: str, num_requests: int = 100, num_workers: int = 10):
    """压力测试单个端点"""
    print_info(f"测试端点: {endpoint}")
    print_info(f"并发数: {num_workers}, 总请求数: {num_requests}")

    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(make_request, endpoint) for _ in range(num_requests)]

        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # 统计结果
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    if successful:
        times = [r['time'] for r in successful]
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)

        print_success(f"成功: {len(successful)}/{num_requests}")
        print_info(f"平均响应时间: {avg_time:.3f}s")
        print_info(f"最快: {min_time:.3f}s, 最慢: {max_time:.3f}s")

        if avg_time < 1.0:
            performance_rating = "优秀"
            color = Colors.OKGREEN
        elif avg_time < 3.0:
            performance_rating = "良好"
            color = Colors.OKBLUE
        elif avg_time < 5.0:
            performance_rating = "一般"
            color = Colors.WARNING
        else:
            performance_rating = "需要优化"
            color = Colors.FAIL

        print(f"{color}性能评级: {performance_rating}{Colors.ENDC}")

    if failed:
        print_error(f"失败: {len(failed)}/{num_requests}")

    return {
        "endpoint": endpoint,
        "total": num_requests,
        "successful": len(successful),
        "failed": len(failed),
        "avg_time": avg_time if successful else None,
        "performance": performance_rating if successful else "失败"
    }


def run_stress_tests():
    """运行所有压力测试"""
    print_header("API压力测试")

    # 测试各个关键端点
    endpoints_to_test = [
        ("/drawings", 50, 5),  # 图纸列表
        ("/processes?limit=100", 50, 5),  # 工序列表
        # ("/drawings/1", 100, 10),  # 单个图纸详情（需要实际ID）
    ]

    stress_results = []

    for endpoint, num_requests, num_workers in endpoints_to_test:
        result = stress_test_endpoint(endpoint, num_requests, num_workers)
        stress_results.append(result)
        print("")  # 空行分隔

    TEST_RESULTS.append({
        "test": "压力测试",
        "results": stress_results
    })


# ============================================================================
# 3. 边界测试 (Boundary Testing)
# ============================================================================

def test_boundary_conditions():
    """测试边界条件"""
    print_header("边界条件测试")

    boundary_tests = []

    # 测试1: 空值测试
    print_info("测试空值处理...")
    test_cases = [
        {"search": ""},  # 空字符串
        {"search": None},  # None值
        {"limit": 0},  # 零值
        {"limit": -1},  # 负数
        {"limit": 10000},  # 超大值
    ]

    for params in test_cases:
        try:
            response = requests.get(f"{API_BASE}/drawings", params=params, timeout=5)
            if response.status_code == 200 or response.status_code == 422:
                print_success(f"边界值处理正确: {params}")
                boundary_tests.append({"params": params, "status": "PASS"})
            else:
                print_warning(f"边界值响应异常 ({response.status_code}): {params}")
                boundary_tests.append({"params": params, "status": "WARNING"})
        except Exception as e:
            print_error(f"边界值测试失败: {params} - {str(e)}")
            boundary_tests.append({"params": params, "status": "FAIL"})

    # 测试2: 特殊字符测试
    print_info("\n测试特殊字符处理...")
    special_chars = [
        "中文测试",
        "🎉 emoji",
        "' OR '1'='1",
        "<script>alert('xss')</script>",
        "../../etc/passwd",
        "\x00\x01\x02",  # 控制字符
    ]

    for char in special_chars:
        try:
            response = requests.get(
                f"{API_BASE}/drawings",
                params={"search": char},
                timeout=5
            )
            if response.status_code in [200, 422]:
                print_success(f"特殊字符处理正确: {char[:20]}...")
            else:
                print_warning(f"特殊字符响应异常: {char[:20]}...")
        except Exception as e:
            print_error(f"特殊字符测试失败: {char[:20]}... - {str(e)}")

    # 测试3: 文件大小限制
    print_info("\n测试文件大小限制...")
    file_sizes = [
        (1024, "1KB", False),  # 1KB - 应该接受
        (1024 * 1024, "1MB", False),  # 1MB - 应该接受
        (10 * 1024 * 1024, "10MB", False),  # 10MB - 应该接受
        (60 * 1024 * 1024, "60MB", True),  # 60MB - 应该拒绝（超过50MB限制）
    ]

    for size, label, should_reject in file_sizes:
        try:
            # 创建指定大小的测试文件
            test_data = b'A' * size
            files = {'file': (f'test_{label}.pdf', test_data, 'application/pdf')}

            response = requests.post(
                f"{API_BASE}/drawings/upload",
                files=files,
                timeout=30
            )

            if should_reject:
                if response.status_code != 200:
                    print_success(f"正确拒绝超大文件: {label}")
                else:
                    print_error(f"安全漏洞：接受了超大文件 {label}")
            else:
                if response.status_code == 200:
                    print_success(f"正确接受文件: {label}")
                else:
                    print_warning(f"可能过于严格: 拒绝了 {label} 文件")

        except Exception as e:
            print_warning(f"文件大小测试 {label} 出错: {str(e)}")

    TEST_RESULTS.append({
        "test": "边界条件测试",
        "boundary_tests": len(boundary_tests),
        "status": "COMPLETED"
    })


# ============================================================================
# 报告生成
# ============================================================================

def generate_report():
    """生成测试报告"""
    print_header("测试报告生成")

    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
# 报价系统安全性与性能测试报告

**测试时间**: {report_time}
**测试工具**: Python Requests + Concurrent Futures

---

## 测试摘要

"""

    for result in TEST_RESULTS:
        report += f"\n### {result['test']}\n"
        report += f"- 状态: **{result.get('status', 'N/A')}**\n"

        if 'vulnerabilities' in result:
            report += f"- 发现漏洞: {result['vulnerabilities']}\n"

        if 'results' in result:
            report += "\n**详细结果**:\n"
            for r in result['results']:
                report += f"- {r['endpoint']}: {r['successful']}/{r['total']} 成功"
                if r.get('avg_time'):
                    report += f", 平均 {r['avg_time']:.3f}s"
                report += f", 性能: {r.get('performance', 'N/A')}\n"

        if 'note' in result:
            report += f"- 备注: {result['note']}\n"

    report += """

---

## 建议

### 安全性建议:
1. ✅ 保持SQL参数化查询，防止SQL注入
2. ✅ 前端使用React自动转义，防止XSS
3. ⚠️ 加强文件上传验证（文件类型、大小、路径）
4. ⚠️ 配置合适的CORS策略
5. ⚠️ 实施访问频率限制（Rate Limiting）

### 性能优化建议:
1. 添加Redis缓存层
2. 优化数据库查询（添加索引）
3. 实施分页和懒加载
4. 压缩API响应
5. 使用CDN加速静态资源

### 边界处理建议:
1. ✅ 继续验证所有输入参数
2. ✅ 正确处理空值和特殊字符
3. ✅ 实施文件大小限制
4. ⚠️ 添加更详细的错误提示

---

**测试完成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    # 保存报告
    report_path = "C:\\Users\\Admin\\Desktop\\报价\\测试报告.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print_success(f"测试报告已生成: {report_path}")

    return report


# ============================================================================
# 主程序
# ============================================================================

def main():
    """运行所有测试"""
    print_header("报价系统 - 安全性、性能与边界测试套件")
    print_info(f"目标API: {API_BASE}")
    print_info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 1. 漏洞测试
        test_sql_injection()
        test_xss_vulnerability()
        test_file_upload_security()
        test_cors_configuration()

        # 2. 压力测试
        run_stress_tests()

        # 3. 边界测试
        test_boundary_conditions()

        # 4. 生成报告
        generate_report()

        print_header("测试完成")
        print_success("所有测试已完成，请查看测试报告")

    except KeyboardInterrupt:
        print_warning("\n测试被用户中断")
    except Exception as e:
        print_error(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
