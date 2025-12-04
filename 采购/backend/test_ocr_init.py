# -*- coding: utf-8 -*-
"""
测试OCR服务初始化
"""
import os
import sys

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def test_ocr_service():
    """测试OCR服务初始化"""
    print("=" * 60)
    print("🧪 测试 OCR 服务初始化")
    print("=" * 60)
    print()

    try:
        from services.invoice_ocr_service import get_ocr_service

        print("[1/3] 导入OCR服务模块...")
        print("✅ 模块导入成功")
        print()

        print("[2/3] 初始化OCR服务...")
        service = get_ocr_service()
        print("✅ OCR服务初始化成功")
        print()

        print("[3/3] 检查OCR配置...")
        print(f"   - OCR类型: {service.ocr_type}")
        print(f"   - 使用云API: {service.use_cloud_api}")
        print(f"   - 使用Ollama Vision: {service.use_ollama_vision}")
        print(f"   - Ollama可用: {service.ollama_available}")

        if service.ocr_engine:
            print(f"   - OCR引擎: ✅ 已加载")
        else:
            print(f"   - OCR引擎: ⚠️  未加载（将使用Fallback）")

        print()
        print("=" * 60)
        print("✅ OCR服务测试完成")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ocr_service()
    sys.exit(0 if success else 1)
