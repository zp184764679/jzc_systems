# -*- coding: utf-8 -*-
"""
企业微信快速配置向导
帮助用户配置企业微信UserID并测试通知功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models.user import User
from services.wework_service import get_wework_service
from extensions import db
from sqlalchemy import text


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "=" * 60)
    print("     企业微信快速配置向导")
    print("=" * 60 + "\n")


def check_config():
    """检查企业微信配置"""
    print("📋 步骤1：检查企业微信配置")
    print("-" * 60)

    wework = get_wework_service()

    print(f"CorpID: {wework.corp_id}")
    print(f"AgentID: {wework.agent_id}")
    print(f"Secret: {wework.secret[:15]}...")

    if not wework.is_enabled():
        print("\n❌ 企业微信服务未启用")
        print("   请检查.env文件中的配置")
        return False

    print(f"状态: ✅ 已启用\n")

    # 测试Access Token
    print("测试Access Token...")
    token = wework.get_access_token()

    if token:
        print(f"✅ Access Token获取成功\n")
        return True
    else:
        print("❌ Access Token获取失败")
        print("   请检查CorpID、AgentID和Secret是否正确\n")
        return False


def list_users():
    """列出所有用户"""
    print("\n📋 步骤2：查看系统用户")
    print("-" * 60)

    with app.app_context():
        users = User.query.all()

        if not users:
            print("❌ 系统中没有用户")
            return []

        print(f"共有 {len(users)} 个用户:\n")

        for i, user in enumerate(users, 1):
            wework_status = f'✅ {user.wework_user_id}' if hasattr(user, 'wework_user_id') and user.wework_user_id else '⚠️  未绑定'
            print(f"  [{i}] ID: {user.id:2d} | 用户名: {user.username:15s} | 企业微信: {wework_status}")

        print()
        return users


def configure_user_wework_id():
    """配置用户的企业微信UserID"""
    print("\n📋 步骤3：配置企业微信UserID")
    print("-" * 60)

    with app.app_context():
        users = User.query.all()

        if not users:
            print("❌ 没有可配置的用户")
            return

        print("💡 如何获取企业微信UserID：")
        print("   1. 登录企业微信管理后台 https://work.weixin.qq.com/")
        print("   2. 通讯录 → 点击员工")
        print("   3. 查看\"账号\"字段（如：ZhangSan、001等）\n")

        # 选择用户
        while True:
            choice = input("请选择要配置的用户编号（输入0退出）: ").strip()

            if choice == '0':
                return

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(users):
                    user = users[idx]
                    break
                else:
                    print("❌ 无效的编号\n")
            except ValueError:
                print("❌ 请输入数字\n")

        print(f"\n选择的用户: {user.username}")

        # 输入UserID
        current_id = user.wework_user_id if hasattr(user, 'wework_user_id') else None
        if current_id:
            print(f"当前企业微信UserID: {current_id}")

        wework_id = input("请输入企业微信UserID（留空跳过）: ").strip()

        if not wework_id:
            print("❌ 已取消配置\n")
            return

        # 更新数据库
        try:
            user.wework_user_id = wework_id
            db.session.commit()
            print(f"✅ 用户 {user.username} 的企业微信UserID已设置为: {wework_id}\n")
            return user, wework_id
        except Exception as e:
            db.session.rollback()
            print(f"❌ 配置失败: {e}\n")
            return None, None


def send_test_message():
    """发送测试消息"""
    print("\n📋 步骤4：发送测试消息")
    print("-" * 60)

    with app.app_context():
        # 查询已配置UserID的用户
        users = User.query.filter(User.wework_user_id.isnot(None)).all()

        if not users:
            print("❌ 没有已配置企业微信UserID的用户")
            print("   请先完成步骤3配置用户\n")
            return

        print(f"已配置企业微信的用户:\n")
        for i, user in enumerate(users, 1):
            print(f"  [{i}] {user.username} → {user.wework_user_id}")

        print()

        # 选择用户
        while True:
            choice = input("请选择要发送测试消息的用户编号（输入0退出）: ").strip()

            if choice == '0':
                return

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(users):
                    user = users[idx]
                    break
                else:
                    print("❌ 无效的编号\n")
            except ValueError:
                print("❌ 请输入数字\n")

        print(f"\n正在向 {user.username} ({user.wework_user_id}) 发送测试消息...\n")

        wework = get_wework_service()

        # 发送文本消息
        success = wework.send_text_message(
            user_ids=[user.wework_user_id],
            content=f"""🎉 企业微信通知测试

你好 {user.username}，

这是来自采购系统的测试消息。
如果你看到这条消息，说明企业微信集成配置成功！

系统功能：
✅ PR审批通知
✅ 审批结果通知
✅ 采购订单通知

祝使用愉快！"""
        )

        if success:
            print("✅ 测试消息发送成功！")
            print(f"   请在企业微信\"采购系统\"应用中查看消息\n")
        else:
            print("❌ 测试消息发送失败")
            print("   可能的原因：")
            print("   1. UserID不正确")
            print("   2. 用户不在应用可见范围内")
            print("   3. 用户未激活企业微信\n")


def test_approval_notification():
    """测试审批通知"""
    print("\n📋 步骤5：测试PR审批通知（可选）")
    print("-" * 60)

    print("💡 这个功能会创建一个测试PR并发送审批通知\n")

    choice = input("是否继续？(y/n): ").strip().lower()

    if choice != 'y':
        print("已跳过\n")
        return

    with app.app_context():
        from models.pr import PR
        from models.pr_item import PRItem
        from services.notification_service import NotificationService
        import datetime

        # 查询已配置UserID的用户
        users = User.query.filter(User.wework_user_id.isnot(None)).all()

        if not users:
            print("❌ 没有已配置企业微信UserID的用户\n")
            return

        # 选择审批人
        print("请选择审批人:\n")
        for i, user in enumerate(users, 1):
            print(f"  [{i}] {user.username}")
        print()

        while True:
            choice = input("请输入编号: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(users):
                    approver = users[idx]
                    break
            except ValueError:
                pass
            print("❌ 无效的编号\n")

        # 创建测试PR
        try:
            pr = PR(
                pr_number=f"PR-TEST-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                owner_id=approver.id,
                owner_name=approver.username,
                owner_department="测试部门",
                status="pending_approval",
                pr_status_desc="待审批"
            )
            db.session.add(pr)
            db.session.flush()

            # 添加测试物料
            item = PRItem(
                pr_id=pr.id,
                item_name="测试物料-铣刀",
                item_spec="Φ12",
                quantity=10,
                unit="个",
                category="刀具/铣削刀具",
                status="pending_approval"
            )
            db.session.add(item)
            db.session.commit()

            print(f"\n✅ 测试PR创建成功: {pr.pr_number}")
            print("正在发送审批通知...\n")

            # 发送通知
            NotificationService.notify_pr_pending_approval(pr, approver.id)

            print("✅ 审批通知已发送！")
            print(f"   请在企业微信中查看 {approver.username} 是否收到审批通知\n")

        except Exception as e:
            db.session.rollback()
            print(f"❌ 测试失败: {e}\n")


def main():
    """主函数"""
    print_banner()

    # 步骤1：检查配置
    if not check_config():
        print("❌ 配置检查失败，请先完成企业微信配置")
        return

    # 步骤2：列出用户
    users = list_users()

    if not users:
        return

    # 步骤3：配置用户
    result = configure_user_wework_id()

    # 步骤4：发送测试消息
    send_test_message()

    # 步骤5：测试审批通知（可选）
    test_approval_notification()

    print("\n" + "=" * 60)
    print("     配置完成！")
    print("=" * 60)
    print("\n✅ 企业微信集成已配置完成")
    print("   系统将在以下场景自动发送通知：")
    print("   - PR审批：审批人收到待审批通知")
    print("   - 审批通过：申请人收到通过通知")
    print("   - 审批驳回：申请人收到驳回通知\n")
    print("💡 下一步：重启后端服务以应用最新代码")
    print("   通过启动器或手动重启Flask后端\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 配置已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
