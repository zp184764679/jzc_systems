# -*- coding: utf-8 -*-
"""
企业微信功能测试脚本
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from services.wework_service import get_wework_service


def test_config():
    """测试配置"""
    print("=" * 60)
    print("1. 测试企业微信配置")
    print("=" * 60)

    wework = get_wework_service()

    print(f"CorpID: {wework.corp_id}")
    print(f"AgentID: {wework.agent_id or '❌ 未配置'}")
    print(f"Secret: {wework.secret[:15]}..." if wework.secret else "❌ 未配置")
    print(f"服务状态: {'✅ 已启用' if wework.is_enabled() else '❌ 未启用'}")
    print()


def test_access_token():
    """测试Access Token获取"""
    print("=" * 60)
    print("2. 测试Access Token获取")
    print("=" * 60)

    wework = get_wework_service()

    if not wework.is_enabled():
        print("❌ 企业微信服务未启用，请先配置WEWORK_AGENT_ID")
        return False

    token = wework.get_access_token()

    if token:
        print(f"✅ Access Token获取成功")
        print(f"   Token: {token[:30]}...")
        print(f"   过期时间: {wework._token_expires_at}")
        return True
    else:
        print("❌ Access Token获取失败")
        print("   请检查：")
        print("   1. CorpID是否正确")
        print("   2. Secret是否正确")
        print("   3. 应用是否已启用")
        return False


def test_send_text_message():
    """测试发送文本消息"""
    print("\n" + "=" * 60)
    print("3. 测试发送文本消息")
    print("=" * 60)

    wework = get_wework_service()

    if not wework.is_enabled():
        print("❌ 企业微信服务未启用")
        return False

    # 输入测试用户ID
    user_id = input("请输入测试用户的企业微信UserID (例如: ZhangSan): ").strip()

    if not user_id:
        print("❌ UserID不能为空")
        return False

    print(f"\n正在向 {user_id} 发送测试消息...")

    success = wework.send_text_message(
        user_ids=[user_id],
        content="🎉 这是来自采购系统的测试消息\n\n如果你看到这条消息，说明企业微信集成配置成功！"
    )

    if success:
        print("✅ 测试消息发送成功！")
        print("   请打开企业微信，在'采购系统'应用中查看消息")
        return True
    else:
        print("❌ 测试消息发送失败")
        print("   请检查：")
        print("   1. UserID是否正确")
        print("   2. 用户是否在应用可见范围内")
        print("   3. 用户是否已激活企业微信")
        return False


def test_send_card_message():
    """测试发送卡片消息"""
    print("\n" + "=" * 60)
    print("4. 测试发送卡片消息")
    print("=" * 60)

    wework = get_wework_service()

    if not wework.is_enabled():
        print("❌ 企业微信服务未启用")
        return False

    user_id = input("请输入测试用户的企业微信UserID (例如: ZhangSan): ").strip()

    if not user_id:
        print("❌ UserID不能为空")
        return False

    print(f"\n正在向 {user_id} 发送测试卡片...")

    success = wework.send_textcard_message(
        user_ids=[user_id],
        title="【测试】采购申请待审批",
        description="""<div class="normal">这是一条测试卡片消息</div>
<div class="gray">申请单号：PR-TEST-001</div>
<div class="gray">申请人：测试用户</div>
<div class="highlight">点击按钮查看详情</div>""",
        url="http://localhost:3000",
        btntxt="查看详情"
    )

    if success:
        print("✅ 测试卡片发送成功！")
        print("   请打开企业微信，在'采购系统'应用中查看卡片消息")
        return True
    else:
        print("❌ 测试卡片发送失败")
        return False


def test_user_binding():
    """测试用户绑定状态"""
    print("\n" + "=" * 60)
    print("5. 测试用户企业微信绑定状态")
    print("=" * 60)

    with app.app_context():
        from models.user import User

        users = User.query.all()

        print(f"系统中共有 {len(users)} 个用户\n")

        bound_count = 0
        for user in users:
            if hasattr(user, 'wework_user_id') and user.wework_user_id:
                print(f"✅ {user.username} → {user.wework_user_id}")
                bound_count += 1
            else:
                print(f"⚠️  {user.username} → 未绑定")

        print(f"\n已绑定: {bound_count}/{len(users)} 人")

        if bound_count == 0:
            print("\n💡 提示：请使用以下SQL为用户配置企业微信UserID：")
            print("   UPDATE users SET wework_user_id = '你的UserID' WHERE username = 'xxx';")


def interactive_menu():
    """交互式菜单"""
    while True:
        print("\n" + "=" * 60)
        print("企业微信功能测试菜单")
        print("=" * 60)
        print("1. 测试配置")
        print("2. 测试Access Token")
        print("3. 测试发送文本消息")
        print("4. 测试发送卡片消息")
        print("5. 查看用户绑定状态")
        print("6. 运行完整测试")
        print("0. 退出")
        print("=" * 60)

        choice = input("请选择 (0-6): ").strip()

        if choice == '1':
            test_config()
        elif choice == '2':
            test_access_token()
        elif choice == '3':
            test_send_text_message()
        elif choice == '4':
            test_send_card_message()
        elif choice == '5':
            test_user_binding()
        elif choice == '6':
            test_config()
            if test_access_token():
                test_send_text_message()
                test_send_card_message()
            test_user_binding()
        elif choice == '0':
            print("\n👋 再见！")
            break
        else:
            print("❌ 无效选择")


if __name__ == "__main__":
    interactive_menu()
