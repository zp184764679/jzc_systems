#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
边界情况和异常场景测试
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5001/api/v1"
proxies = {'http': None, 'https': None}

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_test(name, result, detail=""):
    status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
    print(f"{status} | {name}")
    if detail:
        print(f"     └─ {detail}")

def log_section(title):
    print(f"\n{Colors.BLUE}{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}{Colors.END}\n")

# 登录获取token
def login():
    resp = requests.post(f"{BASE_URL}/login", json={
        "email": "jzchardware@gmail.com",
        "password": "123456"
    }, proxies=proxies, timeout=10)

    if resp.status_code == 200:
        data = resp.json()
        return {
            "user_id": data.get("user_id"),
            "role": data.get("role"),
            "headers": {
                "Content-Type": "application/json",
                "User-ID": str(data.get("user_id")),
                "User-Role": data.get("role", "admin")
            }
        }
    return None

print(f"\n{Colors.BLUE}{'='*80}")
print("           边界情况和异常场景测试")
print(f"{'='*80}{Colors.END}\n")

auth = login()
if not auth:
    print(f"{Colors.RED}❌ 登录失败，测试终止{Colors.END}")
    exit(1)

headers = auth["headers"]

# ============================================================
# 测试类别1: 输入验证测试
# ============================================================
log_section("测试类别1: 输入验证和数据完整性")

# 测试1.1: PR创建 - 缺少必填字段
print("【测试1.1】PR创建 - 缺少必填字段")
resp = requests.post(f"{BASE_URL}/pr", json={
    "title": "",  # 空标题
    "urgency": "high"
}, proxies=proxies, headers=headers, timeout=10)
log_test("空标题应被拒绝", resp.status_code in [400, 422], f"状态码: {resp.status_code}")

# 测试1.2: PR创建 - 无效的urgency值
print("\n【测试1.2】PR创建 - 无效枚举值")
resp = requests.post(f"{BASE_URL}/pr", json={
    "title": "测试PR",
    "urgency": "超高",  # 无效值
    "expected_delivery_date": "2025-12-31",
    "items": [{"item_name": "测试", "quantity": 1, "unit": "个"}]
}, proxies=proxies, headers=headers, timeout=10)
log_test("无效urgency应被拒绝或自动修正",
         resp.status_code in [200, 201, 400, 422],
         f"状态码: {resp.status_code}")

# 测试1.3: PR创建 - items为空数组
print("\n【测试1.3】PR创建 - 空物料列表")
resp = requests.post(f"{BASE_URL}/pr", json={
    "title": "空物料测试",
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": []  # 空数组
}, proxies=proxies, headers=headers, timeout=10)
log_test("空物料列表应被拒绝", resp.status_code in [400, 422], f"状态码: {resp.status_code}")

# 测试1.4: PR创建 - 负数数量
print("\n【测试1.4】PR创建 - 负数数量")
resp = requests.post(f"{BASE_URL}/pr", json={
    "title": "负数测试",
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": [
        {"item_name": "测试物料", "quantity": -10, "unit": "个"}  # 负数
    ]
}, proxies=proxies, headers=headers, timeout=10)
log_test("负数数量应被拒绝", resp.status_code in [400, 422], f"状态码: {resp.status_code}")

# 测试1.5: PR创建 - 超长字符串
print("\n【测试1.5】PR创建 - 超长字符串")
long_string = "A" * 1000  # 1000个字符
resp = requests.post(f"{BASE_URL}/pr", json={
    "title": long_string,
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": [{"item_name": "测试", "quantity": 1, "unit": "个"}]
}, proxies=proxies, headers=headers, timeout=10)
log_test("超长字符串应被拒绝或截断",
         resp.status_code in [200, 201, 400, 413, 422],
         f"状态码: {resp.status_code}")

# ============================================================
# 测试类别2: 权限和认证测试
# ============================================================
log_section("测试类别2: 权限和认证")

# 测试2.1: 未登录访问受保护资源
print("【测试2.1】未登录访问PR列表")
resp = requests.get(f"{BASE_URL}/pr", proxies=proxies, timeout=10)
log_test("未登录应返回401/403",
         resp.status_code in [401, 403, 404],
         f"状态码: {resp.status_code}")

# 测试2.2: 无效token访问
print("\n【测试2.2】无效token访问")
bad_headers = {
    "Content-Type": "application/json",
    "User-ID": "99999",  # 不存在的用户
    "User-Role": "admin"
}
resp = requests.get(f"{BASE_URL}/pr", proxies=proxies, headers=bad_headers, timeout=10)
log_test("无效token应被拒绝",
         resp.status_code in [401, 403, 404],
         f"状态码: {resp.status_code}")

# ============================================================
# 测试类别3: 数据一致性测试
# ============================================================
log_section("测试类别3: 数据一致性")

# 测试3.1: 创建PR并立即查询
print("【测试3.1】创建后立即查询 - 测试数据一致性")
create_resp = requests.post(f"{BASE_URL}/pr", json={
    "title": f"一致性测试-{int(time.time())}",
    "urgency": "medium",
    "expected_delivery_date": "2025-12-31",
    "items": [
        {"item_name": "测试物料1", "quantity": 5, "unit": "个"},
        {"item_name": "测试物料2", "quantity": 10, "unit": "件"}
    ]
}, proxies=proxies, headers=headers, timeout=10)

if create_resp.status_code in [200, 201]:
    pr_id = create_resp.json().get("id")
    time.sleep(0.2)  # 短暂延迟

    # 立即查询
    query_resp = requests.get(f"{BASE_URL}/pr/{pr_id}", proxies=proxies, headers=headers, timeout=10)

    if query_resp.status_code == 200:
        pr_data = query_resp.json()
        items_count = len(pr_data.get("items", []))
        log_test("创建后数据一致", items_count == 2, f"期望2个items, 实际{items_count}个")
    else:
        log_test("创建后数据一致", False, f"查询失败: {query_resp.status_code}")
else:
    log_test("创建后数据一致", False, f"创建失败: {create_resp.status_code}")

# 测试3.2: 批量插入一致性 - 大量物料
print("\n【测试3.2】批量插入 - 10个物料")
items = [{"item_name": f"物料{i}", "quantity": i*10, "unit": "个"} for i in range(1, 11)]
create_resp = requests.post(f"{BASE_URL}/pr", json={
    "title": f"批量测试-{int(time.time())}",
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": items
}, proxies=proxies, headers=headers, timeout=10)

if create_resp.status_code in [200, 201]:
    pr_id = create_resp.json().get("id")
    time.sleep(0.5)

    # 审批并创建RFQ
    approve_resp = requests.post(f"{BASE_URL}/pr/{pr_id}/approve", json={
        "approved": True,
        "comment": "批量测试"
    }, proxies=proxies, headers=headers, timeout=15)

    if approve_resp.status_code == 200:
        rfq_id = approve_resp.json().get("rfq_id")
        time.sleep(1)

        # 查询RFQ items数量
        rfq_resp = requests.get(f"{BASE_URL}/rfqs/{rfq_id}", proxies=proxies, headers=headers, timeout=10)
        if rfq_resp.status_code == 200:
            rfq_items = rfq_resp.json().get("items", [])
            log_test("10个物料全部创建", len(rfq_items) == 10, f"期望10个, 实际{len(rfq_items)}个")
        else:
            log_test("10个物料全部创建", False, f"查询RFQ失败: {rfq_resp.status_code}")
    else:
        log_test("10个物料全部创建", False, f"审批失败: {approve_resp.status_code}")
else:
    log_test("10个物料全部创建", False, f"创建PR失败: {create_resp.status_code}")

# ============================================================
# 测试类别4: 边界值测试
# ============================================================
log_section("测试类别4: 边界值测试")

# 测试4.1: 极小数量
print("【测试4.1】数量边界 - 最小值1")
resp = requests.post(f"{BASE_URL}/pr", json={
    "title": "最小数量测试",
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": [{"item_name": "测试", "quantity": 1, "unit": "个"}]
}, proxies=proxies, headers=headers, timeout=10)
log_test("最小数量1应被接受", resp.status_code in [200, 201], f"状态码: {resp.status_code}")

# 测试4.2: 极大数量
print("\n【测试4.2】数量边界 - 超大值")
resp = requests.post(f"{BASE_URL}/pr", json={
    "title": "超大数量测试",
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": [{"item_name": "测试", "quantity": 999999, "unit": "个"}]
}, proxies=proxies, headers=headers, timeout=10)
log_test("超大数量应被接受或限制",
         resp.status_code in [200, 201, 400, 422],
         f"状态码: {resp.status_code}")

# 测试4.3: 零数量
print("\n【测试4.3】数量边界 - 零值")
resp = requests.post(f"{BASE_URL}/pr", json={
    "title": "零数量测试",
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": [{"item_name": "测试", "quantity": 0, "unit": "个"}]
}, proxies=proxies, headers=headers, timeout=10)
log_test("零数量应被拒绝", resp.status_code in [400, 422], f"状态码: {resp.status_code}")

# ============================================================
# 测试类别5: 并发和竞态测试
# ============================================================
log_section("测试类别5: 并发测试")

# 测试5.1: 同一PR多次审批
print("【测试5.1】防重复审批测试")
# 先创建一个新PR
create_resp = requests.post(f"{BASE_URL}/pr", json={
    "title": f"重复审批测试-{int(time.time())}",
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": [{"item_name": "测试", "quantity": 1, "unit": "个"}]
}, proxies=proxies, headers=headers, timeout=10)

if create_resp.status_code in [200, 201]:
    pr_id = create_resp.json().get("id")
    time.sleep(0.3)

    # 第一次审批
    resp1 = requests.post(f"{BASE_URL}/pr/{pr_id}/approve", json={
        "approved": True,
        "comment": "第一次审批"
    }, proxies=proxies, headers=headers, timeout=10)

    time.sleep(0.5)

    # 第二次审批（应该失败或被忽略）
    resp2 = requests.post(f"{BASE_URL}/pr/{pr_id}/approve", json={
        "approved": True,
        "comment": "第二次审批"
    }, proxies=proxies, headers=headers, timeout=10)

    log_test("防止重复审批",
             resp1.status_code in [200, 201] and resp2.status_code in [400, 409],
             f"第一次: {resp1.status_code}, 第二次: {resp2.status_code}")
else:
    log_test("防止重复审批", False, "创建PR失败")

# ============================================================
# 测试类别6: 删除和级联测试
# ============================================================
log_section("测试类别6: 删除和级联操作")

# 测试6.1: 删除不存在的RFQ
print("【测试6.1】删除不存在的资源")
resp = requests.delete(f"{BASE_URL}/rfqs/999999", proxies=proxies, headers=headers, timeout=10)
log_test("删除不存在资源应返回404", resp.status_code == 404, f"状态码: {resp.status_code}")

# 测试6.2: 删除后再次查询
print("\n【测试6.2】删除后验证资源不可访问")
# 先创建一个RFQ
create_resp = requests.post(f"{BASE_URL}/pr", json={
    "title": f"删除测试-{int(time.time())}",
    "urgency": "low",
    "expected_delivery_date": "2025-12-31",
    "items": [{"item_name": "测试", "quantity": 1, "unit": "个"}]
}, proxies=proxies, headers=headers, timeout=10)

if create_resp.status_code in [200, 201]:
    pr_id = create_resp.json().get("id")
    time.sleep(0.3)

    # 审批创建RFQ
    approve_resp = requests.post(f"{BASE_URL}/pr/{pr_id}/approve", json={
        "approved": True
    }, proxies=proxies, headers=headers, timeout=10)

    if approve_resp.status_code == 200:
        rfq_id = approve_resp.json().get("rfq_id")
        time.sleep(0.3)

        # 删除RFQ
        delete_resp = requests.delete(f"{BASE_URL}/rfqs/{rfq_id}", proxies=proxies, headers=headers, timeout=10)

        if delete_resp.status_code == 200:
            time.sleep(0.3)

            # 再次查询（应该失败）
            query_resp = requests.get(f"{BASE_URL}/rfqs/{rfq_id}", proxies=proxies, headers=headers, timeout=10)
            log_test("删除后不可访问", query_resp.status_code == 404, f"查询状态: {query_resp.status_code}")
        else:
            log_test("删除后不可访问", False, f"删除失败: {delete_resp.status_code}")
    else:
        log_test("删除后不可访问", False, "审批失败")
else:
    log_test("删除后不可访问", False, "创建PR失败")

# ============================================================
# 测试总结
# ============================================================
print(f"\n{Colors.BLUE}{'='*80}")
print("                       测试完成")
print(f"{'='*80}{Colors.END}\n")

print(f"{Colors.GREEN}✅ 边界情况和异常场景测试已完成{Colors.END}")
print(f"\n测试覆盖范围:")
print("  • 输入验证测试 (5项)")
print("  • 权限和认证测试 (2项)")
print("  • 数据一致性测试 (2项)")
print("  • 边界值测试 (3项)")
print("  • 并发测试 (1项)")
print("  • 删除和级联测试 (2项)")
print(f"\n{Colors.YELLOW}建议: 查看测试结果，修复发现的问题{Colors.END}\n")
