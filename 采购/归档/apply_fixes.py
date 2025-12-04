#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动应用供应商界面修复补丁
运行方法: python apply_fixes.py
"""

import os
import sys

def apply_fix_to_quote_library():
    """修复前端报价库文件"""
    file_path = r"frontend\src\pages\supplier\SupplierQuoteLibrary.jsx"

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False

    print(f"📝 正在修复: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修改1: 添加导入
    old_import = 'import useSupplierQuotes from "../../hooks/useSupplierQuotes";'
    new_import = '''import useSupplierQuotes from "../../hooks/useSupplierQuotes";
import QuoteParticipateModal from "../../components/supplier/QuoteParticipateModal";'''

    if old_import in content and 'QuoteParticipateModal' not in content:
        content = content.replace(old_import, new_import)
        print("  ✅ 添加了 QuoteParticipateModal 导入")
    else:
        print("  ⏭️  导入已存在或文件结构不匹配")

    # 修改2: 添加状态
    old_state = '  const [detail, setDetail] = useState(null);'
    new_state = '''  const [detail, setDetail] = useState(null);
  const [participateQuote, setParticipateQuote] = useState(null);'''

    if old_state in content and 'participateQuote' not in content:
        content = content.replace(old_state, new_state)
        print("  ✅ 添加了 participateQuote 状态")
    else:
        print("  ⏭️  状态已存在或文件结构不匹配")

    # 修改3: 修改操作列
    old_button = '''                <td className="px-3 py-2">
                  <button
                    className="px-2 py-1 border rounded"
                    onClick={() => setDetail(q)}
                  >
                    详情
                  </button>
                </td>'''

    new_button = '''                <td className="px-3 py-2">
                  <div className="flex gap-2">
                    {/* 报价按钮 - 仅待报价状态显示 */}
                    {q.status === 'pending' && (
                      <button
                        className="px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                        onClick={() => setParticipateQuote(q)}
                      >
                        报价
                      </button>
                    )}
                    <button
                      className="px-2 py-1 border rounded hover:bg-gray-50"
                      onClick={() => setDetail(q)}
                    >
                      详情
                    </button>
                  </div>
                </td>'''

    if old_button in content:
        content = content.replace(old_button, new_button)
        print("  ✅ 修改了操作列，添加报价按钮")
    else:
        print("  ⏭️  操作列已修改或文件结构不匹配")

    # 修改4: 添加报价弹窗
    old_end = '''      )}
    </div>
  );
}'''

    new_end = '''      )}

      {/* 报价弹窗 */}
      {participateQuote && (
        <QuoteParticipateModal
          quote={participateQuote}
          onClose={() => setParticipateQuote(null)}
          onSuccess={(updatedQuote) => {
            // 刷新列表
            reload();
            setParticipateQuote(null);
          }}
        />
      )}
    </div>
  );
}'''

    if old_end in content and 'QuoteParticipateModal' not in content.split('详情抽屉/弹窗')[1]:
        content = content.replace(old_end, new_end)
        print("  ✅ 添加了报价弹窗组件")
    else:
        print("  ⏭️  报价弹窗已存在或文件结构不匹配")

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {file_path} 修复完成\n")
    return True


def apply_fix_to_supplier_routes():
    """修复后端供应商路由文件"""
    file_path = r"backend\routes\supplier_self_routes.py"

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False

    print(f"📝 正在修复: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修改1: 添加 joinedload 导入
    old_import = 'from sqlalchemy import or_, desc'
    new_import = '''from sqlalchemy import or_, desc
from sqlalchemy.orm import joinedload'''

    if old_import in content and 'joinedload' not in content:
        content = content.replace(old_import, new_import)
        print("  ✅ 添加了 joinedload 导入")
    else:
        print("  ⏭️  导入已存在或文件结构不匹配")

    # 修改2: 添加预加载
    old_query = '    # 3) 构建查询\n    q = SupplierQuote.query.filter(SupplierQuote.supplier_id == supplier_id)'
    new_query = '    # 3) 构建查询 - 预加载 supplier 关联，确保 display_no 能正确生成\n    q = SupplierQuote.query.options(joinedload(SupplierQuote.supplier)).filter(SupplierQuote.supplier_id == supplier_id)'

    if old_query in content:
        content = content.replace(old_query, new_query)
        print("  ✅ 添加了 supplier 关联预加载")
    else:
        # 尝试另一种格式
        old_query2 = '    q = SupplierQuote.query.filter(SupplierQuote.supplier_id == supplier_id)'
        new_query2 = '    q = SupplierQuote.query.options(joinedload(SupplierQuote.supplier)).filter(SupplierQuote.supplier_id == supplier_id)'
        if old_query2 in content and 'joinedload(SupplierQuote.supplier)' not in content:
            content = content.replace(old_query2, new_query2)
            print("  ✅ 添加了 supplier 关联预加载（备用方案）")
        else:
            print("  ⏭️  预加载已存在或文件结构不匹配")

    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ {file_path} 修复完成\n")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("🔧 供应商界面修复脚本")
    print("=" * 60)
    print()

    # 检查是否在项目根目录
    if not os.path.exists('frontend') or not os.path.exists('backend'):
        print("❌ 请在项目根目录（采购文件夹）下运行此脚本")
        print("   当前目录:", os.getcwd())
        sys.exit(1)

    success_count = 0
    total_count = 2

    # 应用修复
    if apply_fix_to_quote_library():
        success_count += 1

    if apply_fix_to_supplier_routes():
        success_count += 1

    print("=" * 60)
    if success_count == total_count:
        print(f"✅ 所有修复已成功应用! ({success_count}/{total_count})")
        print()
        print("📋 后续步骤:")
        print("   1. 检查两个文件的修改是否正确")
        print("   2. 启动后端服务: cd backend && python app.py")
        print("   3. 启动前端服务: cd frontend && npm run dev")
        print("   4. 测试报价功能")
    else:
        print(f"⚠️  部分修复完成 ({success_count}/{total_count})")
        print("   请查看上面的输出，手动完成未成功的修复")
    print("=" * 60)


if __name__ == '__main__':
    main()
