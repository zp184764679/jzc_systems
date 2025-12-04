import requests
import io

print("测试PDF文件上传...")

# 创建一个简单的PDF文件内容（模拟）
pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n196\n%%EOF"

# 测试不同文件大小
test_cases = [
    ("test_small.pdf", pdf_content, "小文件（<1KB）"),
    ("test_medium.pdf", pdf_content * 100, "中等文件（约20KB）"),
]

for filename, content, description in test_cases:
    print(f"\n测试 {description}: {filename}")

    files = {
        'file': (filename, io.BytesIO(content), 'application/pdf')
    }

    try:
        response = requests.post('http://localhost:9001/api/drawings/upload', files=files)

        if response.status_code == 201:
            print(f"  ✅ 上传成功")
            data = response.json()
            print(f"  - ID: {data.get('id')}")
            print(f"  - 图号: {data.get('drawing_number')}")
            print(f"  - 文件大小: {data.get('file_size')} bytes")
        else:
            print(f"  ❌ 上传失败: {response.status_code}")
            print(f"  - 错误: {response.text[:200]}")

    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

# 测试非PDF文件
print(f"\n测试非允许的文件类型: test.txt")
files = {
    'file': ('test.txt', io.BytesIO(b"test content"), 'text/plain')
}

try:
    response = requests.post('http://localhost:9001/api/drawings/upload', files=files)

    if response.status_code == 400:
        print(f"  ✅ 正确拒绝了非法文件类型")
        print(f"  - 响应: {response.json()}")
    else:
        print(f"  ⚠️ 未正确拒绝: {response.status_code}")

except Exception as e:
    print(f"  ❌ 请求失败: {e}")

# 测试超大文件（51MB，超过限制）
print(f"\n测试超大文件（51MB）")
large_content = b"X" * (51 * 1024 * 1024)  # 51MB
files = {
    'file': ('test_large.pdf', io.BytesIO(large_content), 'application/pdf')
}

try:
    response = requests.post('http://localhost:9001/api/drawings/upload', files=files, timeout=10)

    if response.status_code == 400:
        print(f"  ✅ 正确拒绝了超大文件")
        print(f"  - 响应: {response.json()}")
    else:
        print(f"  ⚠️ 未正确拒绝: {response.status_code}")

except requests.exceptions.Timeout:
    print(f"  ⚠️ 请求超时（文件太大）")
except Exception as e:
    print(f"  ❌ 请求失败: {e}")

print("\n测试完成！")
