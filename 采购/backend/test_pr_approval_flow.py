# -*- coding: utf-8 -*-
"""
测试完整PR审批通知流程
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models.user import User
from models.pr import PR
from models.pr_item import PRItem
from services.notification_service import NotificationService
from extensions import db
import datetime


def test_pr_approval_flow():
    """测试PR审批通知流程"""

    with app.app_context():
        # 获取用户
        owner = User.query.get(4)  # 周鹏
        approver = User.query.get(1)  # Admin作为审批人

        if not owner:
            print('❌ 申请人不存在 (ID: 4)')
            return

        if not approver:
            print('❌ 审批人不存在 (ID: 1)')
            return

        print("=" * 60)
        print("     测试PR审批通知流程")
        print("=" * 60)
        print()

        # 创建测试PR
        print("📝 步骤1: 创建测试PR")
        print("-" * 60)

        pr = PR(
            pr_number=f'PR-TEST-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}',
            title='测试PR审批通知',
            description='这是一个测试PR，用于验证企业微信审批通知功能',
            urgency='normal',
            owner_id=owner.id,
            created_by=owner.username,
            status='submitted'  # 初始状态为submitted，待审批
        )
        db.session.add(pr)
        db.session.flush()

        # 添加测试物料
        items = [
            PRItem(
                pr_id=pr.id,
                name='铣刀',
                spec='Φ12',
                qty=10,
                unit='个',
                classification='刀具/铣削刀具',
                status='pending'
            ),
            PRItem(
                pr_id=pr.id,
                name='钻头',
                spec='Φ8',
                qty=20,
                unit='个',
                classification='刀具/钻削刀具',
                status='pending'
            ),
            PRItem(
                pr_id=pr.id,
                name='铝板',
                spec='6061 200x300x10mm',
                qty=5,
                unit='块',
                classification='原材料/金属材料',
                status='pending'
            )
        ]

        for item in items:
            db.session.add(item)

        db.session.commit()

        print(f'✅ PR创建成功')
        print(f'   PR编号: {pr.pr_number}')
        print(f'   申请人: {owner.username} (ID: {owner.id})')
        print(f'   审批人: {approver.username} (ID: {approver.id})')
        print(f'   物料数量: {len(items)}项')
        print()

        # 显示物料清单
        print("📦 物料清单:")
        for idx, item in enumerate(items, 1):
            print(f'   {idx}. {item.name} {item.spec} x{item.qty}{item.unit}')
        print()

        # 发送审批通知
        print("📱 步骤2: 发送审批通知")
        print("-" * 60)

        try:
            NotificationService.notify_pr_pending_approval(pr, approver.id)
            print('✅ 审批通知已发送！')
            print()

            # 检查审批人企业微信配置
            if approver.wework_user_id:
                print(f'📲 企业微信通知:')
                print(f'   发送到: {approver.username} ({approver.wework_user_id})')
                print()
                print('💡 请在以下位置查看通知:')
                print('   1️⃣  企业微信APP → 采购系统应用')
                print('   2️⃣  个人微信 → 企业微信对话（如果已开启消息同步）')
            else:
                print(f'⚠️  审批人未配置企业微信UserID')
                print(f'   仅发送站内通知')

            print()
            print("📧 站内通知:")
            print(f'   已创建站内通知记录')
            print()

        except Exception as e:
            print(f'❌ 发送通知失败: {e}')
            import traceback
            traceback.print_exc()
            return

        # 下一步指引
        print("=" * 60)
        print("     测试结果")
        print("=" * 60)
        print()
        print("✅ 测试PR创建成功")
        print("✅ 审批通知已发送")
        print()
        print("🎯 下一步测试（可选）:")
        print()
        print("1️⃣  测试审批通过通知:")
        print(f"   运行: python test_approve_pr.py {pr.id}")
        print()
        print("2️⃣  测试审批驳回通知:")
        print(f"   运行: python test_reject_pr.py {pr.id}")
        print()
        print("3️⃣  在系统中手动审批:")
        print("   - 登录系统")
        print("   - 进入PR审批页面")
        print(f"   - 找到 {pr.pr_number}")
        print("   - 点击通过/驳回")
        print("   - 查看企业微信是否收到结果通知")
        print()


if __name__ == "__main__":
    try:
        test_pr_approval_flow()
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
