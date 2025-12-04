import requests

print("测试负数limit参数修复...")
try:
    r = requests.get('http://localhost:8001/api/drawings?limit=-1')
    print(f"状态码: {r.status_code}")
    if r.status_code == 422:
        print("✅ 修复成功！正确返回422验证错误")
        print(f"响应: {r.json()}")
    elif r.status_code == 500:
        print("❌ 修复失败！仍然返回500错误")
        print(f"错误详情: {r.text[:500]}")
    else:
        print(f"⚠️  返回了意外的状态码: {r.status_code}")
        print(f"响应: {r.text[:200]}")
except Exception as e:
    print(f"❌ 测试失败: {e}")
