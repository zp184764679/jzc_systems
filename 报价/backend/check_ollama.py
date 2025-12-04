#!/usr/bin/env python
"""检查Ollama服务状态和模型"""
import sys
import requests
from config.settings import settings

print("=" * 60)
print("  Ollama Vision 服务检查")
print("=" * 60)
print()

# 检查配置
print("📋 配置信息:")
print(f"  Ollama地址: {settings.OLLAMA_BASE_URL}")
print(f"  模型名称: {settings.OLLAMA_VISION_MODEL}")
print()

# 检查Ollama服务
print("🔍 检查Ollama服务...")
try:
    response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
    if response.status_code == 200:
        print("  ✅ Ollama服务正常运行")
        print()

        # 列出可用模型
        data = response.json()
        models = data.get('models', [])

        print(f"📦 已安装的模型 ({len(models)}个):")
        if models:
            for model in models:
                name = model.get('name', 'unknown')
                size = model.get('size', 0) / (1024**3)  # 转换为GB
                print(f"  • {name} ({size:.2f} GB)")
        else:
            print("  ⚠️  没有已安装的模型")
        print()

        # 检查目标模型
        print(f"🎯 检查目标模型: {settings.OLLAMA_VISION_MODEL}")
        model_names = [m['name'] for m in models]

        # 精确匹配
        if settings.OLLAMA_VISION_MODEL in model_names:
            print(f"  ✅ 模型已安装: {settings.OLLAMA_VISION_MODEL}")
        else:
            # 模糊匹配
            matching = [m for m in model_names if 'qwen3-vl' in m.lower() or 'qwen2-vl' in m.lower() or 'llava' in m.lower()]

            if matching:
                print(f"  ⚠️  未找到精确匹配的模型: {settings.OLLAMA_VISION_MODEL}")
                print(f"  💡 但找到了类似的视觉模型:")
                for m in matching:
                    print(f"     • {m}")
                print()
                print(f"  💡 建议修改配置文件中的 OLLAMA_VISION_MODEL 为: {matching[0]}")
            else:
                print(f"  ❌ 未找到模型: {settings.OLLAMA_VISION_MODEL}")
                print()
                print("  📥 安装模型的方法:")
                print(f"     ollama pull {settings.OLLAMA_VISION_MODEL}")
                print()
                print("  💡 推荐的视觉模型:")
                print("     • qwen2-vl:7b  (推荐，中文支持好)")
                print("     • llava:7b     (备选，性能不错)")
                print("     • llava:13b    (更强大，需要更多内存)")
    else:
        print(f"  ❌ Ollama服务响应异常: {response.status_code}")
        print("  💡 请检查Ollama是否正确启动")

except requests.exceptions.ConnectionError:
    print("  ❌ 无法连接到Ollama服务")
    print(f"  💡 请确保Ollama正在运行: {settings.OLLAMA_BASE_URL}")
    print()
    print("  📥 安装Ollama:")
    print("     Windows: 下载并安装 https://ollama.com/download")
    print("     启动后会自动运行在 http://localhost:11434")

except Exception as e:
    print(f"  ❌ 检查失败: {str(e)}")

print()
print("=" * 60)
print()

# 提供解决方案
print("🛠️  解决方案:")
print()
print("1. 确保Ollama已安装并运行")
print("   • 下载: https://ollama.com/download")
print("   • Windows会自动启动服务")
print()
print("2. 安装视觉模型 (任选其一)")
print("   • ollama pull qwen2-vl:7b")
print("   • ollama pull llava:7b")
print()
print("3. 修改配置文件 backend/.env (如果需要)")
print("   OLLAMA_BASE_URL=http://localhost:11434")
print("   OLLAMA_VISION_MODEL=qwen2-vl:7b")
print()
print("=" * 60)
