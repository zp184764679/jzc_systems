#!/usr/bin/env python
"""快速测试OCR服务"""
import sys
sys.path.insert(0, '.')

from services.drawing_ocr_service import get_ocr_service

print("=" * 60)
print("  测试OCR服务初始化")
print("=" * 60)
print()

try:
    ocr_service = get_ocr_service()
    print("✅ OCR服务初始化成功")
    print()

    print("📋 服务状态:")
    print(f"  • Ollama Vision: {'✅ 可用' if ocr_service.ollama_available else '❌ 不可用'}")
    if ocr_service.ollama_available:
        print(f"    模型: {ocr_service.ollama_vision_model}")

    if ocr_service.ocr_engine:
        print(f"  • 备用OCR引擎: ✅ {ocr_service.ocr_type}")
    else:
        print(f"  • 备用OCR引擎: ❌ 未初始化")

    print()
    print("=" * 60)

except Exception as e:
    print(f"❌ 初始化失败: {e}")
    import traceback
    traceback.print_exc()
