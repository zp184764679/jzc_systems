#!/usr/bin/env python
"""测试改进后的prompt"""
import sys
sys.path.insert(0, '.')

import requests
import base64
import json
from pathlib import Path
import fitz

test_pdf = Path("uploads/drawings/1c76c8ca-f905-4fca-8294-82b43965ca6b.pdf")

print("=" * 60)
print("  测试改进后的Prompt")
print("=" * 60)
print()

# 转换PDF
print("1️⃣ 转换PDF为图片...")
doc = fitz.open(test_pdf)
page = doc[0]
pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
temp_image = test_pdf.with_suffix('.test2.png')
pix.save(temp_image)
doc.close()
print(f"   ✅ 已转换")
print()

# 编码
with open(temp_image, 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# 使用改进的prompt
print("2️⃣ 使用改进的Prompt识别...")
prompt = """请分析这张机加工图纸，提取关键信息。

请识别以下信息（如果图纸中有的话）：
- 图号/物料代码（通常在右下角标题栏）
- 材质规格（如SUS303、304、45钢、铝合金等）
- 产品名称
- 外径尺寸（Φ标注）
- 总长度

请用JSON格式返回，格式如下：
```json
{
  "drawing_number": "图号或物料代码",
  "material": "材质",
  "product_name": "产品名称",
  "outer_diameter": "外径",
  "length": "长度"
}
```"""

print(f"   Prompt长度: {len(prompt)} 字符")
print("   正在请求Ollama...")
print()

try:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen3-vl:8b-instruct",
            "prompt": prompt,
            "images": [image_data],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 500,
                "num_ctx": 2048,
                "num_thread": 4,
            }
        },
        timeout=180
    )

    result = response.json()
    response_text = result.get('response', '').strip()

    print("3️⃣ 原始响应:")
    print("-" * 60)
    print(response_text)
    print("-" * 60)
    print()

    # 尝试解析JSON
    print("4️⃣ 解析JSON...")

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

    # 提取JSON
    if "{" in clean_text and "}" in clean_text:
        start = clean_text.find("{")
        end = clean_text.rfind("}") + 1
        json_str = clean_text[start:end]

        try:
            drawing_data = json.loads(json_str)
            print("   ✅ JSON解析成功！")
            print()
            print("5️⃣ 提取的信息:")
            print("-" * 60)
            for key, value in drawing_data.items():
                print(f"   {key}: {value}")
            print("-" * 60)
            print()
            print("✅ 成功！改进的Prompt工作正常")

        except json.JSONDecodeError as e:
            print(f"   ❌ JSON解析失败: {e}")
            print(f"   提取的内容: {json_str[:300]}...")
    else:
        print("   ❌ 未找到JSON内容")
        print(f"   响应: {clean_text[:300]}...")

except requests.Timeout:
    print("   ❌ 超时（180秒）")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 清理
temp_image.unlink()

print()
print("=" * 60)
