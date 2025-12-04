#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
采购系统全面测试脚本
"""
import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:5001/api/v1"
TEST_REPORT = []

def log(category, message, status="INFO"):
    """记录测试日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "category": category,
        "message": message,
        "status": status
    }
    TEST_REPORT.append(entry)
    symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
    print(f"{symbol} [{timestamp}] [{category}] {message}")

def api_call(method, endpoint, data=None, token=None, desc=""):
    """统一的API调用函数"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 禁用代理
    proxies = {
        'http': None,
        'https': None
    }

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        elif method == "POST":
            resp = requests.post(url, json=data, headers=headers, proxies=proxies, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, json=data, headers=headers, proxies=proxies, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, proxies=proxies, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")

        log("API", f"{method} {endpoint} - {desc} - Status: {resp.status_code}",
            "PASS" if 200 <= resp.status_code < 300 else "FAIL")

        return resp
    except Exception as e:
        log("API", f"{method} {endpoint} - {desc} - Error: {str(e)}", "FAIL")
        return None

# ============================================================
# 阶段 1: 准备测试账户
# ============================================================
def stage1_prepare_accounts():
    """创建测试账户"""
    log("STAGE1", "===== 开始准备测试账户 =====")

    # 1.1 创建测试员工
    employees = [
        {"username": "test_user1", "password": "123456", "role": "user", "department": "生产部"},
        {"username": "test_buyer", "password": "123456", "role": "user", "department": "采购部"},
        {"username": "test_manager", "password": "123456", "role": "admin", "department": "管理部"}
    ]

    for emp in employees:
        # 注意：需要使用实际的注册接口
        log("STAGE1", f"创建员工账户: {emp['username']}")

    # 1.2 创建测试供应商
    suppliers = [
        {
            "company_name": "测试供应商A-刀具专家",
            "email": f"supplier_a_{int(time.time())}@test.com",
            "password": "123456",
            "contact_name": "张三",
            "contact_phone": "13800138001",
            "contact_email": "zhangsan@test.com",
            "tax_id": "91110000MA001A2B3C"
        },
        {
            "company_name": "测试供应商B-材料供应",
            "email": f"supplier_b_{int(time.time())}@test.com",
            "password": "123456",
            "contact_name": "李四",
            "contact_phone": "13800138002",
            "contact_email": "lisi@test.com",
            "tax_id": "91110000MA001A2B3D"
        },
        {
            "company_name": "测试供应商C-综合供应",
            "email": f"supplier_c_{int(time.time())}@test.com",
            "password": "123456",
            "contact_name": "王五",
            "contact_phone": "13800138003",
            "contact_email": "wangwu@test.com",
            "tax_id": "91110000MA001A2B3E"
        }
    ]

    created_suppliers = []
    for sup in suppliers:
        resp = api_call("POST", "/suppliers/public/register", sup, desc=f"注册供应商: {sup['company_name']}")
        if resp and resp.status_code in [200, 201]:
            try:
                data = resp.json()
                created_suppliers.append(data)
                log("STAGE1", f"供应商注册成功: {sup['company_name']}", "PASS")
            except:
                log("STAGE1", f"供应商注册响应解析失败: {sup['company_name']}", "FAIL")
        else:
            log("STAGE1", f"供应商注册失败: {sup['company_name']}", "FAIL")

    log("STAGE1", f"===== 阶段1完成: 创建了 {len(created_suppliers)} 个供应商 =====")
    return created_suppliers

# ============================================================
# 阶段 2: 测试PR创建和审批
# ============================================================
def stage2_pr_creation_and_approval():
    """测试PR创建和审批流程"""
    log("STAGE2", "===== 开始测试PR创建和审批 =====")

    # 2.1 使用现有管理员登录
    login_resp = api_call("POST", "/auth/login", {
        "username": "周鹏",
        "password": "123456"
    }, desc="管理员登录")

    if not login_resp or login_resp.status_code != 200:
        log("STAGE2", "管理员登录失败，跳过PR测试", "FAIL")
        return None

    try:
        token = login_resp.json().get("access_token")
        user_id = login_resp.json().get("user", {}).get("id")
        log("STAGE2", f"管理员登录成功, user_id={user_id}", "PASS")
    except:
        log("STAGE2", "登录响应解析失败", "FAIL")
        return None

    # 2.2 创建PR (包含多个物料)
    pr_data = {
        "title": f"测试采购申请-{int(time.time())}",
        "urgency": "high",
        "expected_delivery_date": "2025-12-31",
        "remark": "系统自动化测试创建的采购申请",
        "items": [
            {
                "item_name": "镗刀",
                "item_spec": "直径10mm",
                "quantity": 100,
                "unit": "支",
                "category": "刀具",
                "remark": "用于CNC加工"
            },
            {
                "item_name": "铣刀",
                "item_spec": "直径8mm",
                "quantity": 50,
                "unit": "支",
                "category": "刀具",
                "remark": "用于铣削加工"
            },
            {
                "item_name": "钻头",
                "item_spec": "直径5mm",
                "quantity": 200,
                "unit": "支",
                "category": "刀具",
                "remark": "用于钻孔"
            },
            {
                "item_name": "304不锈钢板",
                "item_spec": "1000x2000x3mm",
                "quantity": 20,
                "unit": "张",
                "category": "金属材料",
                "remark": "用于机箱制造"
            }
        ]
    }

    create_resp = api_call("POST", "/pr", pr_data, token, desc="创建包含4个物料的PR")

    if not create_resp or create_resp.status_code not in [200, 201]:
        log("STAGE2", "PR创建失败", "FAIL")
        return None

    try:
        pr = create_resp.json()
        pr_id = pr.get("id")
        log("STAGE2", f"PR创建成功, PR ID={pr_id}, 包含 {len(pr.get('items', []))} 个物料", "PASS")
    except:
        log("STAGE2", "PR创建响应解析失败", "FAIL")
        return None

    # 2.3 查看PR详情
    time.sleep(0.5)
    detail_resp = api_call("GET", f"/pr/{pr_id}", token=token, desc="查看PR详情")
    if detail_resp and detail_resp.status_code == 200:
        log("STAGE2", "PR详情查询成功", "PASS")

    # 2.4 审批PR
    time.sleep(0.5)
    approve_resp = api_call("POST", f"/pr/{pr_id}/approve", {
        "approved": True,
        "comment": "测试审批通过"
    }, token, desc="审批PR")

    if not approve_resp or approve_resp.status_code != 200:
        log("STAGE2", "PR审批失败", "FAIL")
        return None

    try:
        approve_result = approve_resp.json()
        rfq_id = approve_result.get("rfq_id")
        log("STAGE2", f"PR审批成功, 自动创建RFQ ID={rfq_id}", "PASS")
    except:
        log("STAGE2", "PR审批响应解析失败", "FAIL")
        return None

    log("STAGE2", "===== 阶段2完成: PR创建和审批流程测试完成 =====")
    return {"pr_id": pr_id, "rfq_id": rfq_id, "token": token}

# ============================================================
# 阶段 3: 测试RFQ多物料批量插入
# ============================================================
def stage3_rfq_batch_insert(stage2_result):
    """测试RFQ自动生成和多物料批量插入"""
    log("STAGE3", "===== 开始测试RFQ批量插入 =====")

    if not stage2_result:
        log("STAGE3", "阶段2数据缺失，跳过", "FAIL")
        return None

    rfq_id = stage2_result["rfq_id"]
    token = stage2_result["token"]

    # 3.1 查看RFQ详情，验证物料数量
    detail_resp = api_call("GET", f"/rfqs/{rfq_id}", token=token, desc="查看RFQ详情")

    if not detail_resp or detail_resp.status_code != 200:
        log("STAGE3", "RFQ详情查询失败", "FAIL")
        return None

    try:
        rfq_data = detail_resp.json()
        items = rfq_data.get("items", [])
        item_count = len(items)

        if item_count == 4:
            log("STAGE3", f"✅ RFQ包含正确的物料数量: {item_count}个", "PASS")
            for idx, item in enumerate(items, 1):
                log("STAGE3", f"  物料{idx}: {item.get('item_name')} - {item.get('quantity')}{item.get('unit')}", "INFO")
        else:
            log("STAGE3", f"❌ RFQ物料数量错误: 期望4个, 实际{item_count}个", "FAIL")
    except Exception as e:
        log("STAGE3", f"RFQ详情解析失败: {str(e)}", "FAIL")
        return None

    log("STAGE3", "===== 阶段3完成: 批量插入测试完成 =====")
    return stage2_result

# ============================================================
# 阶段 4: 测试RFQ删除和PR失效
# ============================================================
def stage4_rfq_deletion(stage3_result):
    """测试RFQ删除和PR失效功能"""
    log("STAGE4", "===== 开始测试RFQ删除功能 =====")

    if not stage3_result:
        log("STAGE4", "阶段3数据缺失，跳过", "FAIL")
        return None

    # 4.1 先创建一个新的PR和RFQ用于删除测试
    token = stage3_result["token"]

    pr_data = {
        "title": f"待删除测试PR-{int(time.time())}",
        "urgency": "low",
        "expected_delivery_date": "2025-12-31",
        "remark": "用于测试删除功能",
        "items": [
            {
                "item_name": "测试物料",
                "item_spec": "测试规格",
                "quantity": 10,
                "unit": "个",
                "category": "测试类别"
            }
        ]
    }

    create_resp = api_call("POST", "/pr", pr_data, token, desc="创建待删除的PR")
    if not create_resp or create_resp.status_code not in [200, 201]:
        log("STAGE4", "待删除PR创建失败", "FAIL")
        return stage3_result

    try:
        pr = create_resp.json()
        test_pr_id = pr.get("id")
    except:
        log("STAGE4", "PR响应解析失败", "FAIL")
        return stage3_result

    # 审批创建RFQ
    time.sleep(0.5)
    approve_resp = api_call("POST", f"/pr/{test_pr_id}/approve", {
        "approved": True,
        "comment": "测试审批"
    }, token, desc="审批待删除的PR")

    if not approve_resp or approve_resp.status_code != 200:
        log("STAGE4", "待删除PR审批失败", "FAIL")
        return stage3_result

    try:
        test_rfq_id = approve_resp.json().get("rfq_id")
        log("STAGE4", f"创建待删除RFQ ID={test_rfq_id}", "PASS")
    except:
        log("STAGE4", "审批响应解析失败", "FAIL")
        return stage3_result

    # 4.2 删除RFQ
    time.sleep(0.5)
    delete_resp = api_call("DELETE", f"/rfqs/{test_rfq_id}", token=token, desc="删除RFQ")

    if not delete_resp or delete_resp.status_code != 200:
        log("STAGE4", "RFQ删除失败", "FAIL")
        return stage3_result

    try:
        delete_result = delete_resp.json()
        if delete_result.get("success") and delete_result.get("pr_status") == "cancelled":
            log("STAGE4", f"✅ RFQ删除成功, PR状态已更新为: {delete_result.get('pr_status')}", "PASS")
        else:
            log("STAGE4", "RFQ删除后PR状态更新失败", "FAIL")
    except:
        log("STAGE4", "删除响应解析失败", "FAIL")

    # 4.3 验证PR状态
    time.sleep(0.5)
    pr_detail_resp = api_call("GET", f"/pr/{test_pr_id}", token=token, desc="验证PR状态")
    if pr_detail_resp and pr_detail_resp.status_code == 200:
        try:
            pr_data = pr_detail_resp.json()
            if pr_data.get("status") == "cancelled":
                log("STAGE4", "✅ PR状态已正确更新为: cancelled", "PASS")
            else:
                log("STAGE4", f"❌ PR状态异常: {pr_data.get('status')}", "FAIL")
        except:
            log("STAGE4", "PR状态验证失败", "FAIL")

    log("STAGE4", "===== 阶段4完成: RFQ删除测试完成 =====")
    return stage3_result

# ============================================================
# 阶段 5: 测试供应商报价流程
# ============================================================
def stage5_supplier_quotation(stage4_result, suppliers):
    """测试供应商报价流程"""
    log("STAGE5", "===== 开始测试供应商报价 =====")

    if not stage4_result or not suppliers:
        log("STAGE5", "数据缺失，跳过", "FAIL")
        return None

    rfq_id = stage4_result["rfq_id"]

    # 5.1 供应商登录并查看RFQ
    for idx, sup in enumerate(suppliers[:2], 1):  # 测试前2个供应商
        log("STAGE5", f"--- 供应商{idx}: {sup.get('company_name', 'Unknown')} ---")

        # 登录供应商账户 (假设email作为用户名)
        # 注意：需要根据实际的供应商登录接口调整
        # login_resp = api_call("POST", "/suppliers/login", {
        #     "email": sup.get("email"),
        #     "password": "123456"
        # }, desc=f"供应商{idx}登录")
        #
        # if not login_resp or login_resp.status_code != 200:
        #     log("STAGE5", f"供应商{idx}登录失败", "FAIL")
        #     continue

        # ... 报价逻辑 (需要实际的API)
        log("STAGE5", f"供应商{idx}报价功能待实现API后测试", "INFO")

    log("STAGE5", "===== 阶段5完成: 供应商报价测试 (部分功能待API完善) =====")
    return stage4_result

# ============================================================
# 生成测试报告
# ============================================================
def generate_report():
    """生成测试报告"""
    log("REPORT", "===== 生成测试报告 =====")

    total = len(TEST_REPORT)
    passed = len([r for r in TEST_REPORT if r["status"] == "PASS"])
    failed = len([r for r in TEST_REPORT if r["status"] == "FAIL"])

    print("\n")
    print("=" * 80)
    print(" " * 25 + "采购系统测试报告")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总测试项: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"信息: {total - passed - failed} ℹ️")
    print(f"通过率: {passed/total*100:.1f}%" if total > 0 else "N/A")
    print("=" * 80)
    print("\n详细日志:")
    for entry in TEST_REPORT:
        symbol = "✅" if entry["status"] == "PASS" else "❌" if entry["status"] == "FAIL" else "ℹ️"
        print(f"{symbol} [{entry['timestamp']}] [{entry['category']}] {entry['message']}")
    print("=" * 80)

# ============================================================
# 主测试流程
# ============================================================
def main():
    """主测试流程"""
    print("\n" + "=" * 80)
    print(" " * 20 + "采购系统全面测试开始")
    print("=" * 80 + "\n")

    try:
        # 阶段1: 准备账户
        suppliers = stage1_prepare_accounts()

        # 阶段2: PR创建和审批
        stage2_result = stage2_pr_creation_and_approval()

        # 阶段3: RFQ批量插入验证
        stage3_result = stage3_rfq_batch_insert(stage2_result)

        # 阶段4: RFQ删除测试
        stage4_result = stage4_rfq_deletion(stage3_result)

        # 阶段5: 供应商报价
        stage5_result = stage5_supplier_quotation(stage4_result, suppliers)

    except Exception as e:
        log("SYSTEM", f"测试过程发生异常: {str(e)}", "FAIL")
    finally:
        # 生成报告
        generate_report()

if __name__ == "__main__":
    main()
