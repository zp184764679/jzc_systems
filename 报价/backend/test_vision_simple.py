#!/usr/bin/env python
"""简单测试 - 检查Ollama Vision是否能看到图片"""
import sys
sys.path.insert(0, '.')

import requests
import base64
from pathlib import Path
import fitz

# 使用第一个PDF
test_pdf = Path("uploads/drawings/1c76c8ca-f905-4fca-8294-82b43965ca6b.pdf")

print("=" * 60)
print("  简单Vision测试 - 检查模型是否能看到图片")
print("=" * 60)
print()

# 转换PDF为图片
print("1️⃣ 转换PDF...")
doc = fitz.open(test_pdf)
page = doc[0]
pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))  # 降低分辨率
temp_image = test_pdf.with_suffix('.test.png')
pix.save(temp_image)
doc.close()
print(f"   ✅ 已转换: {temp_image}")
print(f"   图片大小: {temp_image.stat().st_size} bytes")
print()

# 编码图片
print("2️⃣ 编码图片...")
with open(temp_image, 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')
print(f"   Base64长度: {len(image_data)}")
print()

# 测试1: 最简单的prompt
print("3️⃣ 测试1: 简单描述图片")
print("   Prompt: '请描述这张图片'")
print("   正在请求...")

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen3-vl:8b-instruct",
        "prompt": "请描述这张图片",
        "images": [image_data],
        "stream": False
    },
    timeout=120
)

result = response.json()
response_text = result.get('response', '').strip()

print(f"   响应: {response_text[:200] if response_text else '(空)'}")
print()

# 测试2: 询问图纸类型
print("4️⃣ 测试2: 询问是否是工程图纸")
print("   Prompt: '这是什么类型的图片？是工程图纸吗？'")
print("   正在请求...")

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen3-vl:8b-instruct",
        "prompt": "这是什么类型的图片？是工程图纸吗？",
        "images": [image_data],
        "stream": False
    },
    timeout=120
)

result = response.json()
response_text = result.get('response', '').strip()

print(f"   响应: {response_text[:200] if response_text else '(空)'}")
print()

# 测试3: 请求提取文本
print("5️⃣ 测试3: 请求提取图中文字")
print("   Prompt: '请提取图片中的所有文字'")
print("   正在请求...")

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen3-vl:8b-instruct",
        "prompt": "请提取图片中的所有文字",
        "images": [image_data],
        "stream": False
    },
    timeout=120
)

result = response.json()
response_text = result.get('response', '').strip()

print(f"   响应长度: {len(response_text)}")
if response_text:
    print(f"   响应前200字: {response_text[:200]}")
else:
    print("   响应: (空)")

print()

# 清理
temp_image.unlink()

print("=" * 60)
print()

if not response_text or len(response_text) < 10:
    print("❌ 问题确认: Ollama Vision无法正常处理图片")
    print()
    print("可能的原因:")
    print("1. 模型配置问题")
    print("2. 图片格式或大小不兼容")
    print("3. Ollama版本问题")
    print()
    print("建议:")
    print("- 检查Ollama版本是否支持vision功能")
    print("- 尝试重新拉取模型: ollama pull qwen3-vl:8b-instruct")
    print("- 检查Ollama日志看是否有错误")
else:
    print("✅ Ollama Vision工作正常")
    print("   问题可能在prompt设计或JSON格式要求")
