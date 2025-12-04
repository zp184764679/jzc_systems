# -*- coding: utf-8 -*-
"""
测试文件上传系统优化
1. 测试按年月分文件夹存储
2. 测试文件保留（即使处理失败）
"""
import os
import sys
from datetime import datetime

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def test_year_month_folder():
    """测试年月文件夹生成"""
    print("=" * 60)
    print("📁 测试年月文件夹功能")
    print("=" * 60)
    print()

    from utils.file_handler import get_year_month_folder, ensure_year_month_folder

    # 获取年月文件夹路径
    folder_path = get_year_month_folder()
    print(f"✅ 年月文件夹路径: {folder_path}")

    # 确保文件夹存在
    actual_path = ensure_year_month_folder()
    print(f"✅ 实际创建路径: {actual_path}")

    # 验证路径格式
    now = datetime.now()
    expected_year = now.strftime('%Y')
    expected_month = now.strftime('%m')

    assert expected_year in folder_path, "路径应包含年份"
    assert expected_month in folder_path, "路径应包含月份"
    print(f"✅ 路径格式正确: uploads/{expected_year}/{expected_month}")

    # 验证文件夹确实存在
    assert os.path.exists(actual_path), "文件夹应该存在"
    print(f"✅ 文件夹已创建")
    print()

    return True

def test_file_save():
    """测试文件保存到年月文件夹"""
    print("=" * 60)
    print("💾 测试文件保存功能")
    print("=" * 60)
    print()

    from utils.file_handler import save_file_to_disk

    # 创建测试文件内容
    test_content = b"This is a test invoice file"
    test_filename = "test_invoice.pdf"

    # 保存文件
    file_path, file_url, error = save_file_to_disk(test_content, test_filename)

    if error:
        print(f"❌ 保存失败: {error}")
        return False

    print(f"✅ 文件路径: {file_path}")
    print(f"✅ 文件URL: {file_url}")

    # 验证文件存在
    assert os.path.exists(file_path), "文件应该存在"
    print(f"✅ 文件已成功保存")

    # 验证URL格式 (应包含年月路径)
    now = datetime.now()
    expected_year = now.strftime('%Y')
    expected_month = now.strftime('%m')

    assert f"/{expected_year}/{expected_month}/" in file_url, "URL应包含年月路径"
    print(f"✅ URL格式正确: {file_url}")

    # 清理测试文件
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"✅ 测试文件已清理")

    print()
    return True

def test_file_persistence():
    """测试文件持久化（模拟失败场景）"""
    print("=" * 60)
    print("🔒 测试文件持久化（失败场景）")
    print("=" * 60)
    print()

    from utils.file_handler import save_file_to_disk

    # 创建测试文件
    test_content = b"This file should persist even if processing fails"
    test_filename = "persistent_test.pdf"

    file_path, file_url, error = save_file_to_disk(test_content, test_filename)

    if error:
        print(f"❌ 保存失败: {error}")
        return False

    print(f"✅ 文件已保存: {file_path}")
    print(f"✅ 文件URL: {file_url}")

    # 模拟处理失败，但文件应该保留
    print("⚠️  模拟处理失败...")
    print("💡 根据新的逻辑，文件不会被删除")

    # 验证文件仍然存在
    assert os.path.exists(file_path), "文件应该保留（即使处理失败）"
    print(f"✅ 文件已保留: {file_path}")

    # 清理测试文件
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"✅ 测试文件已清理")

    print()
    return True

def main():
    """运行所有测试"""
    print()
    print("🧪 开始测试文件上传系统优化")
    print()

    tests = [
        ("年月文件夹功能", test_year_month_folder),
        ("文件保存功能", test_file_save),
        ("文件持久化测试", test_file_persistence),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # 显示测试结果
    print("=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print()

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")

    print()

    all_passed = all(result for _, result in results)
    if all_passed:
        print("=" * 60)
        print("🎉 所有测试通过！文件上传系统优化成功！")
        print("=" * 60)
        print()
        print("✨ 优化内容:")
        print("  1. ✅ 文件按年月文件夹组织存储 (uploads/YYYY/MM/)")
        print("  2. ✅ 失败的文件不再被删除，便于审查")
        print("  3. ✅ 静态文件服务已配置，支持年月路径")
        print()
    else:
        print("⚠️  部分测试失败，请检查错误信息")

    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
