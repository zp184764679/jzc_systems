#!/usr/bin/env python
"""测试Ollama Vision识别 - 详细调试版本"""
import sys
sys.path.insert(0, '.')

import requests
import base64
import json
from pathlib import Path

OLLAMA_BASE = "http://localhost:11434"
MODEL = "qwen3-vl:8b-instruct"

print("=" * 60)
print("  Ollama Vision识别调试测试")
print("=" * 60)
print()

# 1. 检查Ollama服务
print("1️⃣ 检查Ollama服务...")
try:
    response = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
    if response.status_code == 200:
        models = [m['name'] for m in response.json().get('models', [])]
        print(f"   ✅ Ollama服务正常")
        print(f"   可用模型: {', '.join(models)}")
        if MODEL in models:
            print(f"   ✅ 目标模型已安装: {MODEL}")
        else:
            print(f"   ❌ 目标模型未找到: {MODEL}")
            sys.exit(1)
    else:
        print(f"   ❌ Ollama服务异常: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ 无法连接Ollama: {e}")
    sys.exit(1)

print()

# 2. 查找测试图片
print("2️⃣ 查找测试图片...")
upload_dir = Path("uploads/drawings")
test_images = []
if upload_dir.exists():
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
        test_images.extend(upload_dir.glob(ext))

if not test_images:
    print("   ⚠️  未找到测试图片")
    print("   请先上传一张图纸到 uploads/drawings/ 目录")
    sys.exit(0)

test_image = test_images[0]
print(f"   ✅ 使用测试图片: {test_image.name}")
print()

# 如果是PDF，需要先转换成图片
temp_image = None
if test_image.suffix.lower() == '.pdf':
    print("   📄 PDF文件，正在转换为图片...")
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(test_image)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2倍分辨率
        temp_image = test_image.with_suffix('.png')
        pix.save(temp_image)
        doc.close()
        test_image = temp_image
        print(f"   ✅ PDF已转换: {test_image.name}")
    except Exception as e:
        print(f"   ❌ PDF转换失败: {e}")
        sys.exit(1)

print()

# 3. 读取并编码图片
print("3️⃣ 读取图片并编码...")
try:
    with open(test_image, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    print(f"   ✅ 图片已编码 (大小: {len(image_data)} bytes)")
except Exception as e:
    print(f"   ❌ 读取图片失败: {e}")
    sys.exit(1)

print()

# 4. 构建prompt
print("4️⃣ 构建识别prompt...")
prompt = """这是一张机加工图纸，请识别并提取关键信息，以JSON格式返回。

必须提取的字段：
1. drawing_number: 图号（常见位置：右下角标题栏）
2. material: 材质（如SUS303、304、45钢、铝合金等，常在标题栏）
3. product_name: 产品名称
4. outer_diameter: 外径（φ标注）
5. length: 总长度

可选字段（如果有）：
- customer_name: 客户名称
- tolerance: 公差（如±0.1、IT6等）
- surface_roughness: 表面粗糙度（Ra值）
- processes: 工艺要求数组

示例：
{
  "drawing_number": "ZQJ-123",
  "material": "SUS303",
  "product_name": "轴套",
  "outer_diameter": "φ6.05",
  "length": "240mm",
  "tolerance": "±0.1",
  "surface_roughness": "Ra3.2"
}

只返回JSON，不要任何解释。"""

print(f"   ✅ Prompt已准备 (长度: {len(prompt)} 字符)")
print()

# 5. 调用Ollama Vision API
print("5️⃣ 调用Ollama Vision API...")
print(f"   模型: {MODEL}")
print(f"   正在识别，请等待...")
print()

try:
    response = requests.post(
        f"{OLLAMA_BASE}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "images": [image_data],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 800,
                "num_ctx": 2048,
                "num_thread": 4,
            }
        },
        timeout=120  # 增加超时时间用于调试
    )

    print(f"   HTTP状态码: {response.status_code}")

    if response.status_code != 200:
        print(f"   ❌ API请求失败")
        print(f"   响应内容: {response.text}")
        sys.exit(1)

    result = response.json()
    print(f"   ✅ API调用成功")
    print()

    # 6. 查看原始响应
    print("6️⃣ 原始响应:")
    print("-" * 60)
    response_text = result.get('response', '').strip()
    print(response_text)
    print("-" * 60)
    print()

    # 7. 尝试解析JSON
    print("7️⃣ 解析JSON...")

    # 移除markdown代码块
    clean_text = response_text
    if "```" in clean_text:
        parts = clean_text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                clean_text = part[4:].strip()
                break
            elif "{" in part:
                clean_text = part
                break

    # 提取JSON部分
    if "{" in clean_text and "}" in clean_text:
        start = clean_text.find("{")
        end = clean_text.rfind("}") + 1
        json_str = clean_text[start:end]

        try:
            drawing_data = json.loads(json_str)
            print("   ✅ JSON解析成功！")
            print()
            print("8️⃣ 提取的信息:")
            print("-" * 60)
            for key, value in drawing_data.items():
                print(f"   {key}: {value}")
            print("-" * 60)
            print()
            print("✅ 测试成功！Ollama Vision工作正常")

        except json.JSONDecodeError as e:
            print(f"   ❌ JSON解析失败: {e}")
            print(f"   尝试解析的内容: {json_str[:200]}...")
            print()
            print("❌ 问题: 模型返回的不是有效JSON")

    else:
        print(f"   ❌ 响应中未找到JSON格式")
        print(f"   响应内容: {clean_text[:300]}...")
        print()
        print("❌ 问题: 模型没有返回JSON格式的数据")

except requests.Timeout:
    print(f"   ❌ 请求超时 (>120秒)")
    print()
    print("❌ 问题: Ollama响应太慢，可能是:")
    print("   - 模型在CPU上运行（未使用GPU）")
    print("   - 图片太大")
    print("   - 系统资源不足")

except Exception as e:
    print(f"   ❌ 识别失败: {type(e).__name__}: {e}")
    import traceback
    print()
    print("详细错误:")
    traceback.print_exc()

print()
print("=" * 60)

# 清理临时文件
if temp_image and temp_image.exists():
    try:
        temp_image.unlink()
        print(f"🗑️  已清理临时文件: {temp_image.name}")
    except:
        pass
