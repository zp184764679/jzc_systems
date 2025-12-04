# -*- coding: utf-8 -*-
"""
清空所有采购数据脚本（报价、询价单、采购申请）
"""
from extensions import db
from models.supplier_quote import SupplierQuote
from models.rfq import RFQ
from models.rfq_item import RFQItem
from models.rfq_notification_task import RFQNotificationTask
from models.supplier_nudge import SupplierNudge
from models.pr import PR
from models.pr_item import PRItem
from models.purchase_order import PurchaseOrder
from app import app

def clear_all_data():
    """清空所有采购相关数据"""
    with app.app_context():
        try:
            total_count = 0

            # 1. 清空采购订单（PO）- 最上层，依赖RFQ
            try:
                po_count = PurchaseOrder.query.count()
                if po_count > 0:
                    PurchaseOrder.query.delete()
                    print(f"✅ 已删除 {po_count} 条采购订单（PO）")
                    total_count += po_count
                else:
                    print("ℹ️  采购订单（PO）表为空")
            except Exception as e:
                print(f"⚠️  采购订单表可能不存在或为空")

            # 2. 清空供应商报价 - 依赖RFQ
            sq_count = SupplierQuote.query.count()
            if sq_count > 0:
                SupplierQuote.query.delete()
                print(f"✅ 已删除 {sq_count} 条供应商报价")
                total_count += sq_count
            else:
                print("ℹ️  供应商报价表为空")

            # 3. 清空RFQ通知任务（RFQNotificationTask）- 依赖RFQ
            try:
                rfq_notif_count = RFQNotificationTask.query.count()
                if rfq_notif_count > 0:
                    RFQNotificationTask.query.delete()
                    print(f"✅ 已删除 {rfq_notif_count} 条RFQ通知任务")
                    total_count += rfq_notif_count
                else:
                    print("ℹ️  RFQ通知任务表为空")
            except Exception as e:
                print(f"⚠️  RFQ通知任务表可能不存在或为空")

            # 4. 清空供应商提醒（SupplierNudge）- 可能依赖RFQ
            try:
                nudge_count = SupplierNudge.query.count()
                if nudge_count > 0:
                    SupplierNudge.query.delete()
                    print(f"✅ 已删除 {nudge_count} 条供应商提醒")
                    total_count += nudge_count
                else:
                    print("ℹ️  供应商提醒表为空")
            except Exception as e:
                print(f"⚠️  供应商提醒表可能不存在或为空")

            # 5. 清空询价单物料明细（RFQItem）- 依赖RFQ
            rfq_item_count = RFQItem.query.count()
            if rfq_item_count > 0:
                RFQItem.query.delete()
                print(f"✅ 已删除 {rfq_item_count} 条询价单物料明细（RFQItem）")
                total_count += rfq_item_count
            else:
                print("ℹ️  询价单物料明细表为空")

            # 6. 清空询价单（RFQ）- 依赖PR
            rfq_count = RFQ.query.count()
            if rfq_count > 0:
                RFQ.query.delete()
                print(f"✅ 已删除 {rfq_count} 条询价单（RFQ）")
                total_count += rfq_count
            else:
                print("ℹ️  询价单（RFQ）表为空")

            # 7. 清空采购申请物料明细（PRItem）- 依赖PR，必须先删除
            pr_item_count = PRItem.query.count()
            if pr_item_count > 0:
                PRItem.query.delete()
                print(f"✅ 已删除 {pr_item_count} 条采购申请物料明细（PRItem）")
                total_count += pr_item_count
            else:
                print("ℹ️  采购申请物料明细表为空")

            # 8. 清空采购申请（PR）- 最底层
            pr_count = PR.query.count()
            if pr_count > 0:
                PR.query.delete()
                print(f"✅ 已删除 {pr_count} 条采购申请（PR）")
                total_count += pr_count
            else:
                print("ℹ️  采购申请（PR）表为空")

            # 提交事务
            db.session.commit()

            print("\n" + "=" * 60)
            print("🎉 所有采购数据清空成功！")
            print(f"📊 总共删除了 {total_count} 条记录")
            print("=" * 60)
            print("\n清空内容包括：")
            print("  ✓ 采购申请（PR）及物料明细")
            print("  ✓ 询价单（RFQ）及物料明细")
            print("  ✓ 供应商报价（Quotes）")
            print("  ✓ 采购订单（PO）")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 清空失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("🗑️  完整数据清空工具")
    print("=" * 60)
    print("\n⚠️  此操作将删除以下所有数据：")
    print("  • 采购申请（PR）及物料明细")
    print("  • 询价单（RFQ）及物料明细")
    print("  • 供应商报价（Quotes）")
    print("  • 采购订单（PO）")
    print("\n注意：用户、供应商、品类数据不会被删除")

    # 确认操作
    confirm = input("\n是否继续？(yes/no): ")

    if confirm.lower() == 'yes':
        print("\n开始清空数据...\n")
        clear_all_data()
    else:
        print("❌ 操作已取消")
