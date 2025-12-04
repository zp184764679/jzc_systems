# -*- coding: utf-8 -*-
"""
测试AI分类系统
验证知识库索引层、规则匹配、LLM分类的效果
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from services.ai_classifier import LocalClassifier

# 测试用例
TEST_CASES = [
    # 知识库精确匹配测试
    {"name": "车刀", "spec": "", "expected": "刀具/车削刀具"},
    {"name": "铣刀", "spec": "", "expected": "刀具/铣削刀具"},
    {"name": "钻头", "spec": "Φ10", "expected": "刀具/钻削刀具"},
    {"name": "丝锥", "spec": "M6", "expected": "刀具/丝锥铰刀镗刀"},
    {"name": "游标卡尺", "spec": "0-150mm", "expected": "测量工具/卡尺"},
    {"name": "千分尺", "spec": "0-25mm", "expected": "测量工具/千分尺"},

    # 知识库模糊匹配测试（同义词）
    {"name": "外圆车刀", "spec": "", "expected": "刀具/车削刀具"},
    {"name": "立铣刀", "spec": "Φ12", "expected": "刀具/铣削刀具"},
    {"name": "麻花钻", "spec": "Φ8", "expected": "刀具/钻削刀具"},
    {"name": "数显卡尺", "spec": "", "expected": "测量工具/卡尺"},

    # 知识库关键词匹配测试
    {"name": "刀片", "spec": "CNMG120408", "expected": "刀具/车削刀具"},
    {"name": "六角螺栓", "spec": "M8×20", "expected": "五金劳保/紧固件"},
    {"name": "劳保手套", "spec": "", "expected": "五金劳保/劳保防护"},
    {"name": "6200轴承", "spec": "", "expected": "机械零部件/轴承"},

    # 规则匹配测试
    {"name": "铣刀23", "spec": "", "expected": "刀具/铣削刀具"},
    {"name": "手套5", "spec": "", "expected": "五金劳保/劳保防护"},

    # 组合测试
    {"name": "高速钢钻头", "spec": "Φ6", "expected": "刀具/钻削刀具"},
    {"name": "硬质合金立铣刀", "spec": "Φ10×60", "expected": "刀具/铣削刀具"},
    {"name": "304不锈钢螺栓", "spec": "M10×30", "expected": "五金劳保/紧固件"},
]


def test_classification():
    """测试分类效果"""
    with app.app_context():
        print("=" * 80)
        print("AI分类系统测试")
        print("=" * 80)
        print()

        # 初始化分类器
        classifier = LocalClassifier(use_ollama=True, use_knowledge=True)

        passed = 0
        failed = 0

        for i, case in enumerate(TEST_CASES, 1):
            name = case["name"]
            spec = case["spec"]
            expected = case["expected"]

            # 执行分类
            result = classifier.classify(name, spec)

            category = result["category"]
            source = result["source"]

            # 判断是否匹配
            is_match = (category == expected)

            if is_match:
                status = "✅ PASS"
                passed += 1
            else:
                status = "❌ FAIL"
                failed += 1

            # 打印结果
            print(f"[{i:2d}] {status}")
            print(f"     输入: {name} {spec}")
            print(f"     预期: {expected}")
            print(f"     结果: {category}")
            print(f"     来源: {source}")

            if not is_match:
                print(f"     ⚠️  分类不匹配！")

            print()

        # 统计结果
        total = len(TEST_CASES)
        success_rate = (passed / total) * 100 if total > 0 else 0

        print("=" * 80)
        print(f"测试完成")
        print(f"总计: {total} 个用例")
        print(f"通过: {passed} 个 ✅")
        print(f"失败: {failed} 个 ❌")
        print(f"成功率: {success_rate:.1f}%")
        print("=" * 80)

        return success_rate


def test_cache_performance():
    """测试缓存性能"""
    with app.app_context():
        print("\n" + "=" * 80)
        print("缓存性能测试")
        print("=" * 80)
        print()

        classifier = LocalClassifier(use_ollama=True, use_knowledge=True)

        # 第一次分类（写入缓存）
        import time

        test_item = {"name": "铣刀", "spec": "Φ12"}

        print(f"测试物料: {test_item['name']} {test_item['spec']}")
        print()

        # 首次查询
        start = time.time()
        result1 = classifier.classify(test_item["name"], test_item["spec"])
        time1 = (time.time() - start) * 1000

        print(f"首次查询:")
        print(f"  结果: {result1['category']}")
        print(f"  来源: {result1['source']}")
        print(f"  耗时: {time1:.2f}ms")
        print()

        # 第二次查询（应该从缓存读取）
        start = time.time()
        result2 = classifier.classify(test_item["name"], test_item["spec"])
        time2 = (time.time() - start) * 1000

        print(f"二次查询（缓存）:")
        print(f"  结果: {result2['category']}")
        print(f"  来源: {result2['source']}")
        print(f"  耗时: {time2:.2f}ms")
        print()

        if time2 < time1:
            speedup = time1 / time2 if time2 > 0 else float('inf')
            print(f"✅ 缓存加速: {speedup:.1f}x 倍")
        else:
            print(f"⚠️  缓存未生效")

        print("=" * 80)


if __name__ == "__main__":
    # 运行分类测试
    success_rate = test_classification()

    # 运行缓存性能测试
    test_cache_performance()

    # 退出代码
    sys.exit(0 if success_rate == 100 else 1)
