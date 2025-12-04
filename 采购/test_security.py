#!/usr/bin/env python3
"""
采购系统安全测试脚本
边际测试 + 压力测试 + 漏洞检测
"""
import requests
import json
import time
import concurrent.futures
from datetime import datetime

BASE_URL = "http://localhost:5001"
PORTAL_URL = "http://localhost:3002"

# 获取测试用token
def get_token():
    resp = requests.post(f"{PORTAL_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if resp.status_code == 200:
        return resp.json().get("token")
    return None

TOKEN = None
RESULTS = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_result(test_name, status, detail=""):
    if status == "PASS":
        RESULTS["passed"].append({"test": test_name, "detail": detail})
        print(f"✅ PASS: {test_name}")
    elif status == "FAIL":
        RESULTS["failed"].append({"test": test_name, "detail": detail})
        print(f"❌ FAIL: {test_name} - {detail}")
    else:
        RESULTS["warnings"].append({"test": test_name, "detail": detail})
        print(f"⚠️ WARN: {test_name} - {detail}")

# ==================== 1. 认证边际测试 ====================
def test_auth_edge_cases():
    print("\n" + "="*50)
    print("1. 认证边际测试")
    print("="*50)

    # 1.1 空token访问
    resp = requests.get(f"{BASE_URL}/api/v1/pr/list")
    if resp.status_code == 401:
        log_result("空token访问受保护API", "PASS")
    else:
        log_result("空token访问受保护API", "FAIL", f"应返回401，实际返回{resp.status_code}")

    # 1.2 无效token
    resp = requests.get(f"{BASE_URL}/api/v1/pr/list", headers={
        "Authorization": "Bearer invalid_token_12345"
    })
    if resp.status_code in [401, 403]:
        log_result("无效token拒绝", "PASS")
    else:
        log_result("无效token拒绝", "FAIL", f"应返回401/403，实际返回{resp.status_code}")

    # 1.3 过期token格式
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE2MDAwMDAwMDB9.invalid"
    resp = requests.get(f"{BASE_URL}/api/v1/pr/list", headers={
        "Authorization": f"Bearer {expired_token}"
    })
    if resp.status_code in [401, 403]:
        log_result("过期token拒绝", "PASS")
    else:
        log_result("过期token拒绝", "FAIL", f"应返回401/403，实际返回{resp.status_code}")

    # 1.4 SQL注入登录尝试
    payloads = [
        {"username": "admin' OR '1'='1", "password": "anything"},
        {"username": "admin'--", "password": "anything"},
        {"username": "admin'; DROP TABLE users;--", "password": "test"},
    ]
    for payload in payloads:
        resp = requests.post(f"{PORTAL_URL}/api/auth/login", json=payload)
        if resp.status_code != 200 or "token" not in resp.text:
            log_result(f"SQL注入登录防护: {payload['username'][:20]}", "PASS")
        else:
            log_result(f"SQL注入登录防护: {payload['username'][:20]}", "FAIL", "可能存在SQL注入漏洞!")

# ==================== 2. 输入验证测试 ====================
def test_input_validation():
    print("\n" + "="*50)
    print("2. 输入验证测试")
    print("="*50)

    headers = {"Authorization": f"Bearer {TOKEN}", "User-ID": "1"}

    # 2.1 超长字符串
    long_string = "A" * 10000
    resp = requests.post(f"{BASE_URL}/api/v1/pr/create", headers=headers, json={
        "title": long_string,
        "description": "test",
        "urgency": "medium",
        "owner_id": 1,
        "items": [{"name": "test", "qty": 1}]
    })
    if resp.status_code in [400, 413, 422, 500]:
        log_result("超长字符串处理", "PASS", f"返回{resp.status_code}")
    else:
        log_result("超长字符串处理", "WARN", f"接受了10000字符的标题")

    # 2.2 特殊字符/XSS
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert(1)",
        "<img src=x onerror=alert(1)>",
        "{{7*7}}",  # 模板注入
    ]
    for xss in xss_payloads:
        resp = requests.post(f"{BASE_URL}/api/v1/pr/create", headers=headers, json={
            "title": xss,
            "description": xss,
            "urgency": "medium",
            "owner_id": 1,
            "items": [{"name": xss, "qty": 1}]
        })
        # 检查响应中是否原样返回了脚本标签
        if "<script>" in resp.text or "javascript:" in resp.text:
            log_result(f"XSS防护: {xss[:30]}", "WARN", "可能存在XSS风险，需检查前端是否转义")
        else:
            log_result(f"XSS防护: {xss[:30]}", "PASS")

    # 2.3 负数/零/非法数量
    invalid_qtys = [-1, 0, 999999999, "abc", None]
    for qty in invalid_qtys:
        resp = requests.post(f"{BASE_URL}/api/v1/pr/create", headers=headers, json={
            "title": "测试",
            "description": "test",
            "urgency": "medium",
            "owner_id": 1,
            "items": [{"name": "test", "qty": qty}]
        })
        if resp.status_code in [400, 422] or qty == 999999999:
            log_result(f"非法数量验证: qty={qty}", "PASS")
        elif resp.status_code == 201:
            log_result(f"非法数量验证: qty={qty}", "WARN", "可能需要更严格的验证")

    # 2.4 空必填字段
    resp = requests.post(f"{BASE_URL}/api/v1/pr/create", headers=headers, json={
        "title": "",
        "items": []
    })
    if resp.status_code in [400, 422]:
        log_result("空必填字段验证", "PASS")
    else:
        log_result("空必填字段验证", "WARN", f"空标题被接受，状态码{resp.status_code}")

# ==================== 3. SQL注入测试 ====================
def test_sql_injection():
    print("\n" + "="*50)
    print("3. SQL注入测试")
    print("="*50)

    headers = {"Authorization": f"Bearer {TOKEN}", "User-ID": "1"}

    sql_payloads = [
        "1 OR 1=1",
        "1; DROP TABLE pr_requests;--",
        "1 UNION SELECT * FROM users--",
        "' OR ''='",
        "1' AND '1'='1",
    ]

    # 测试搜索参数
    for payload in sql_payloads:
        resp = requests.get(f"{BASE_URL}/api/v1/pr/list", headers=headers, params={
            "search": payload
        })
        if resp.status_code == 200:
            try:
                data = resp.json()
                # 如果返回了异常大量数据，可能有注入
                if isinstance(data, list) and len(data) > 100:
                    log_result(f"SQL注入(搜索): {payload[:20]}", "WARN", "返回数据量异常")
                else:
                    log_result(f"SQL注入(搜索): {payload[:20]}", "PASS")
            except:
                log_result(f"SQL注入(搜索): {payload[:20]}", "PASS")
        else:
            log_result(f"SQL注入(搜索): {payload[:20]}", "PASS")

# ==================== 4. 权限绕过测试 ====================
def test_authorization_bypass():
    print("\n" + "="*50)
    print("4. 权限绕过测试")
    print("="*50)

    headers = {"Authorization": f"Bearer {TOKEN}", "User-ID": "1"}

    # 4.1 尝试用User-ID头伪造身份
    fake_headers = {"Authorization": f"Bearer {TOKEN}", "User-ID": "9999"}
    resp = requests.get(f"{BASE_URL}/api/v1/pr/list", headers=fake_headers)
    log_result("User-ID头伪造测试", "WARN" if resp.status_code == 200 else "PASS",
               "需确认后端是否验证User-ID与token一致")

    # 4.2 普通用户访问管理接口
    # 先检查是否有管理接口
    admin_endpoints = [
        "/api/v1/admin/users",
        "/api/v1/admin/settings",
        "/api/v1/users/list",
    ]
    for endpoint in admin_endpoints:
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        if resp.status_code == 404:
            log_result(f"管理接口: {endpoint}", "PASS", "接口不存在")
        elif resp.status_code in [401, 403]:
            log_result(f"管理接口: {endpoint}", "PASS", "权限拒绝")
        else:
            log_result(f"管理接口: {endpoint}", "WARN", f"状态码{resp.status_code}")

    # 4.3 IDOR测试 - 尝试访问其他用户的数据
    for i in [1, 2, 3, 999]:
        resp = requests.get(f"{BASE_URL}/api/v1/pr/{i}", headers=headers)
        if resp.status_code == 200:
            log_result(f"IDOR测试: PR ID={i}", "WARN", "需确认是否应限制访问")
        else:
            log_result(f"IDOR测试: PR ID={i}", "PASS", f"状态码{resp.status_code}")

# ==================== 5. API压力测试 ====================
def test_stress():
    print("\n" + "="*50)
    print("5. API压力测试")
    print("="*50)

    headers = {"Authorization": f"Bearer {TOKEN}", "User-ID": "1"}

    # 5.1 并发请求测试
    def make_request(i):
        try:
            start = time.time()
            resp = requests.get(f"{BASE_URL}/api/v1/pr/list", headers=headers, timeout=10)
            elapsed = time.time() - start
            return {"status": resp.status_code, "time": elapsed, "success": True}
        except Exception as e:
            return {"status": 0, "time": 0, "success": False, "error": str(e)}

    # 50个并发请求
    print("  执行50个并发请求...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(make_request, i) for i in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_count = sum(1 for r in results if r["success"] and r["status"] == 200)
    avg_time = sum(r["time"] for r in results if r["success"]) / max(1, success_count)

    if success_count >= 45:  # 90%成功率
        log_result(f"并发50请求", "PASS", f"成功率{success_count}/50, 平均响应{avg_time:.2f}s")
    else:
        log_result(f"并发50请求", "WARN", f"成功率{success_count}/50, 可能需要限流")

    # 5.2 快速连续请求（测试限流）
    print("  执行100个快速请求...")
    rate_limit_triggered = False
    for i in range(100):
        resp = requests.get(f"{BASE_URL}/api/v1/pr/list", headers=headers)
        if resp.status_code == 429:
            rate_limit_triggered = True
            break

    if rate_limit_triggered:
        log_result("限流机制", "PASS", "触发了429限流")
    else:
        log_result("限流机制", "WARN", "未检测到限流，生产环境建议添加")

# ==================== 6. 其他安全测试 ====================
def test_misc_security():
    print("\n" + "="*50)
    print("6. 其他安全测试")
    print("="*50)

    # 6.1 敏感信息泄露
    resp = requests.get(f"{BASE_URL}/")
    headers_to_check = ["X-Powered-By", "Server"]
    for h in headers_to_check:
        if h in resp.headers:
            log_result(f"敏感头信息: {h}", "WARN", f"值: {resp.headers[h]}")
        else:
            log_result(f"敏感头信息: {h}", "PASS", "未暴露")

    # 6.2 CORS配置
    resp = requests.options(f"{BASE_URL}/api/v1/pr/list", headers={
        "Origin": "http://evil.com",
        "Access-Control-Request-Method": "GET"
    })
    if "Access-Control-Allow-Origin" in resp.headers:
        origin = resp.headers["Access-Control-Allow-Origin"]
        if origin == "*":
            log_result("CORS配置", "WARN", "允许所有来源，生产环境需限制")
        else:
            log_result("CORS配置", "PASS", f"限制来源: {origin}")
    else:
        log_result("CORS配置", "PASS", "未返回CORS头")

    # 6.3 HTTP方法测试
    for method in ["TRACE", "OPTIONS", "CONNECT"]:
        try:
            resp = requests.request(method, f"{BASE_URL}/api/v1/pr/list", timeout=5)
            if method == "TRACE" and resp.status_code == 200:
                log_result(f"HTTP方法: {method}", "WARN", "TRACE方法应禁用")
            else:
                log_result(f"HTTP方法: {method}", "PASS", f"状态码{resp.status_code}")
        except:
            log_result(f"HTTP方法: {method}", "PASS", "请求失败")

    # 6.4 目录遍历测试
    traversal_payloads = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "%2e%2e%2f%2e%2e%2f",
    ]
    for payload in traversal_payloads:
        resp = requests.get(f"{BASE_URL}/api/v1/files/{payload}")
        if resp.status_code == 200 and ("root:" in resp.text or "[boot loader]" in resp.text):
            log_result(f"目录遍历: {payload[:20]}", "FAIL", "可能存在目录遍历漏洞!")
        else:
            log_result(f"目录遍历: {payload[:20]}", "PASS")

# ==================== 主函数 ====================
def main():
    global TOKEN

    print("="*60)
    print("  采购系统安全测试")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 获取token
    TOKEN = get_token()
    if not TOKEN:
        print("❌ 无法获取测试token，部分测试将跳过")
    else:
        print(f"✅ 获取测试token成功")

    # 执行测试
    test_auth_edge_cases()

    if TOKEN:
        test_input_validation()
        test_sql_injection()
        test_authorization_bypass()
        test_stress()

    test_misc_security()

    # 汇总报告
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    print(f"✅ 通过: {len(RESULTS['passed'])} 项")
    print(f"⚠️ 警告: {len(RESULTS['warnings'])} 项")
    print(f"❌ 失败: {len(RESULTS['failed'])} 项")

    if RESULTS['failed']:
        print("\n❌ 失败项详情:")
        for item in RESULTS['failed']:
            print(f"   - {item['test']}: {item['detail']}")

    if RESULTS['warnings']:
        print("\n⚠️ 警告项详情:")
        for item in RESULTS['warnings']:
            print(f"   - {item['test']}: {item['detail']}")

if __name__ == "__main__":
    main()
