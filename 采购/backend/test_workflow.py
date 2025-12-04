"""测试完整采购审批流程"""
import requests
import json

BASE_URL = "http://localhost:5001/api/v1"
PORTAL_URL = "http://localhost:3002"

def test_workflow():
    print("=" * 50)
    print("采购系统完整流程测试")
    print("=" * 50)

    # 1. 从门户获取token
    print("\n1. 获取登录Token...")
    login_resp = requests.post(f"{PORTAL_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if login_resp.status_code != 200:
        print(f"❌ 登录失败: {login_resp.text}")
        return

    token = login_resp.json()["token"]
    user = login_resp.json()["user"]
    print(f"✅ 登录成功: {user['full_name']} (ID: {user['id']}, Role: {user['role']})")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-ID": str(user["id"])
    }

    # 2. 创建采购申请
    print("\n2. 创建采购申请...")
    pr_data = {
        "title": "测试采购申请",
        "description": "这是一个测试申请",
        "urgency": "normal",
        "owner_id": user["id"],
        "applicant_name": user["full_name"],
        "applicant_dept": user.get("department_name", "测试部门"),
        "items": [
            {"name": "测试物料A", "spec": "规格A", "qty": 10, "unit": "个"},
            {"name": "测试物料B", "spec": "规格B", "qty": 5, "unit": "箱"}
        ]
    }

    create_resp = requests.post(f"{BASE_URL}/prs", json=pr_data, headers=headers)
    if create_resp.status_code not in [200, 201]:
        print(f"❌ 创建失败: {create_resp.text}")
        return

    pr = create_resp.json()
    pr_id = pr.get("id") or pr.get("data", {}).get("id")
    print(f"✅ 创建成功: PR#{pr.get('prNumber') or pr.get('data', {}).get('prNumber')} (ID: {pr_id})")

    # 3. 主管审批
    print("\n3. 主管审批...")
    approve_resp = requests.post(f"{BASE_URL}/pr/{pr_id}/supervisor-approve", headers=headers)
    if approve_resp.status_code != 200:
        print(f"❌ 主管审批失败: {approve_resp.text}")
        return
    print(f"✅ 主管审批通过")

    # 4. 填写价格
    print("\n4. 填写价格...")

    # 先获取PR详情拿到正确的item id
    detail_resp = requests.get(f"{BASE_URL}/pr/requests/{pr_id}", headers=headers)
    if detail_resp.status_code != 200:
        print(f"❌ 获取PR详情失败: {detail_resp.text}")
        return

    pr_detail = detail_resp.json()
    items = pr_detail.get("items", [])
    print(f"   物料数量: {len(items)}")

    # 构建价格数据 - 使用 id 字段
    # 测试超过2000元的情况：10个 * 300 = 3000, 5箱 * 200 = 1000, 总计 4000
    price_data = {
        "items": [
            {"id": items[0]["id"], "unit_price": 300},  # 10个 * 300 = 3000
            {"id": items[1]["id"], "unit_price": 200}   # 5箱 * 200 = 1000
        ]
    }
    print(f"   价格数据: {price_data}")

    price_resp = requests.post(f"{BASE_URL}/pr/{pr_id}/fill-price", json=price_data, headers=headers)
    if price_resp.status_code != 200:
        print(f"❌ 填写价格失败: {price_resp.text}")
        return

    price_result = price_resp.json()
    total = price_result.get("total_amount", 0)
    print(f"✅ 价格填写完成, 总金额: ¥{total}")

    # 5. 管理员审批
    print("\n5. 管理员审批...")
    admin_resp = requests.post(f"{BASE_URL}/pr/{pr_id}/admin-approve", headers=headers)
    if admin_resp.status_code != 200:
        print(f"❌ 管理员审批失败: {admin_resp.text}")
        return

    admin_result = admin_resp.json()
    print(f"   管理员审批结果: {admin_result}")
    if admin_result.get("auto_approved"):
        print(f"✅ 自动完成! 原因: {admin_result.get('auto_approve_reason')}")
    elif not admin_result.get("auto_approved") and admin_result.get("need_super_admin_reason"):
        print(f"⚠️ 需要超管审批, 原因: {admin_result.get('need_super_admin_reason')}")

        # 6. 超管审批
        print("\n6. 超管审批...")
        super_resp = requests.post(f"{BASE_URL}/pr/{pr_id}/super-admin-approve", headers=headers)
        if super_resp.status_code != 200:
            print(f"❌ 超管审批失败: {super_resp.text}")
            return
        print(f"✅ 超管审批完成")

    # 7. 验证最终状态
    print("\n7. 验证最终状态...")
    final_resp = requests.get(f"{BASE_URL}/pr/requests/{pr_id}", headers=headers)
    if final_resp.status_code == 200:
        final_pr = final_resp.json()
        status = final_pr.get("status") or final_pr.get("data", {}).get("status")
        status_code = final_pr.get("status_code") or final_pr.get("data", {}).get("status_code")
        print(f"✅ 最终状态: {status} ({status_code})")

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    test_workflow()
