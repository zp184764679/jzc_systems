# -*- coding: utf-8 -*-
"""
清空报价库脚本
"""
from extensions import db
from models.supplier_quote import SupplierQuote
from app import app

def clear_quotes():
    """清空所有报价数据"""
    with app.app_context():
        try:
            # 清空 supplier_quotes 表（RFQ系统的供应商报价）
            sq_count = SupplierQuote.query.count()
            SupplierQuote.query.delete()
            print(f"✅ 已删除 {sq_count} 条 supplier_quotes 记录")

            # 提交事务
            db.session.commit()
            print("\n🎉 报价库清空成功！")
            print(f"📊 总共删除了 {sq_count} 条报价记录")

        except Exception as e:
            db.session.rollback()
            print(f"❌ 清空失败: {str(e)}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("🗑️  报价库清空工具")
    print("=" * 60)

    # 确认操作
    confirm = input("\n⚠️  警告：此操作将删除所有报价数据，是否继续？(yes/no): ")

    if confirm.lower() == 'yes':
        clear_quotes()
    else:
        print("❌ 操作已取消")
