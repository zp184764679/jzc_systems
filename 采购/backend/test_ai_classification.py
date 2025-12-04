# -*- coding: utf-8 -*-
"""
测试 Qwen3:8b AI 分类功能
"""
import os
import sys

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 加载.env文件
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, '.env'))

def test_ai_classification():
    """测试AI分类功能"""
    print("=" * 60)
    print("🤖 测试 Qwen3:8b AI 分类功能")
    print("=" * 60)
    print()

    try:
        # 导入分类服务
        print("[1/3] 初始化AI分类服务...")
        from services.ai_classifier import LocalClassifier
        classifier = LocalClassifier()

        # 验证配置
        print(f"✅ LLM模型: {os.getenv('LLM_MODEL', 'unknown')}")
        print(f"✅ LLM基础URL: {os.getenv('LLM_BASE', 'unknown')}")
        print()

        # 测试物料列表
        test_materials = [
            "硬质合金镗刀 Φ50mm",
            "不锈钢螺栓 M12×50",
            "液压油 68号 20L",
            "防护手套 耐磨型",
            "数控铣刀 Φ16mm R0.5",
        ]

        print("[2/3] 测试物料分类...")
        print()

        results = []
        for i, material_name in enumerate(test_materials, 1):
            print(f"[{i}/5] 分类物料: {material_name}")
            print("   ⏳ 调用 Qwen3:8b 分类中...")

            result = classifier.classify(material_name)
            results.append(result)

            if result:
                major_cat = result.get('major_category', '未知')
                minor_cat = result.get('minor_category', '未知')
                confidence = result.get('confidence', 0)
                method = result.get('method', 'unknown')

                print(f"   ✅ 大类: {major_cat}")
                print(f"   ✅ 小类: {minor_cat}")
                print(f"   ✅ 置信度: {confidence}")
                print(f"   ✅ 方法: {method}")
            else:
                print(f"   ❌ 分类失败")
            print()

        # 统计结果
        print("[3/3] 分类结果统计:")
        print("-" * 60)

        success_count = sum(1 for r in results if r)
        ai_count = sum(1 for r in results if r and r.get('method') == 'ai')

        print(f"总物料数: {len(test_materials)}")
        print(f"成功分类: {success_count}/{len(test_materials)} ({success_count/len(test_materials)*100:.1f}%)")
        print(f"AI分类: {ai_count}/{len(test_materials)} ({ai_count/len(test_materials)*100:.1f}%)")

        if ai_count > 0:
            avg_confidence = sum(r.get('confidence', 0) for r in results if r and r.get('method') == 'ai') / ai_count
            print(f"平均置信度: {avg_confidence:.2f}")

        print("-" * 60)
        print()
        print("=" * 60)
        print("✅ AI 分类测试完成")
        print("=" * 60)

        return success_count == len(test_materials)

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_ai_classification()
    sys.exit(0 if success else 1)
