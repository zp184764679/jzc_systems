# -*- coding: utf-8 -*-
"""
测试企业微信消息推送
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from services.wework_service import get_wework_service

def test_wework_configuration():
    """测试企业微信配置"""
    print("=" * 60)
    print("企业微信配置检查")
    print("=" * 60)

    corp_id = os.getenv('WEWORK_CORP_ID')
    agent_id = os.getenv('WEWORK_AGENT_ID')
    secret = os.getenv('WEWORK_SECRET')

    print(f"CorpID: {corp_id}")
    print(f"AgentID: {agent_id}")
    print(f"Secret: {secret[:10]}..." if secret else "未配置")
    print()

    if not all([corp_id, agent_id, secret]):
        print("❌ 企业微信配置不完整，请检查.env文件")
        return False

    print("✅ 企业微信配置完整")
    return True

def test_get_access_token():
    """测试获取Access Token"""
    print("\n" + "=" * 60)
    print("测试获取Access Token")
    print("=" * 60)

    service = get_wework_service()
    token = service.get_access_token()

    if token:
        print(f"✅ Access Token获取成功")
        print(f"Token: {token[:20]}...")
        return True
    else:
        print("❌ Access Token获取失败")
        return False

def test_send_text_message():
    """测试发送文本消息"""
    print("\n" + "=" * 60)
    print("测试发送文本消息")
    print("=" * 60)

    # 提示用户输入企业微信UserID
    print("\n请输入接收消息的企业微信UserID（如: ZhouPeng）:")
    print("（可在企业微信管理后台 -> 通讯录 中查看）")
    user_id = input("UserID: ").strip()

    if not user_id:
        print("❌ 未输入UserID，跳过测试")
        return False

    service = get_wework_service()

    content = """【测试消息】

这是来自采购系统的测试消息。

如果您收到这条消息，说明企业微信集成配置成功！

测试时间: 2025-11-05
系统: 采购管理系统"""

    success = service.send_text_message([user_id], content)

    if success:
        print(f"✅ 文本消息发送成功 -> {user_id}")
        return True
    else:
        print(f"❌ 文本消息发送失败")
        return False

def test_send_textcard_message():
    """测试发送文本卡片消息"""
    print("\n" + "=" * 60)
    print("测试发送文本卡片消息")
    print("=" * 60)

    print("\n请输入接收消息的企业微信UserID（如: ZhouPeng）:")
    user_id = input("UserID: ").strip()

    if not user_id:
        print("❌ 未输入UserID，跳过测试")
        return False

    service = get_wework_service()

    title = "【测试】采购申请通知"
    description = """
<div class="gray">申请人：周鹏</div>
<div class="gray">部门：研发部</div>
<div class="gray">申请时间：2025-11-05 10:30</div>
<div class="normal">物料数量：5 项</div>
<div class="highlight">状态：待审批</div>
"""
    url = "http://61.145.212.28:5000"

    success = service.send_textcard_message(
        [user_id],
        title=title,
        description=description,
        url=url,
        btntxt="查看详情"
    )

    if success:
        print(f"✅ 文本卡片消息发送成功 -> {user_id}")
        return True
    else:
        print(f"❌ 文本卡片消息发送失败")
        return False

def test_send_markdown_message():
    """测试发送Markdown消息"""
    print("\n" + "=" * 60)
    print("测试发送Markdown消息")
    print("=" * 60)

    print("\n请输入接收消息的企业微信UserID（如: ZhouPeng）:")
    user_id = input("UserID: ").strip()

    if not user_id:
        print("❌ 未输入UserID，跳过测试")
        return False

    service = get_wework_service()

    markdown_content = """## 【测试】采购申请通知

**申请单号**: PR20251105001
**申请人**: 周鹏
**部门**: 研发部
**申请时间**: 2025-11-05 10:30
**物料数量**: 5 项

**物料清单**:
> 1. 螺丝 x 100
> 2. 螺母 x 100
> 3. 垫片 x 50

> **状态**: <font color="warning">待审批</font>
>
> [点击查看详情](http://61.145.212.28:5000)
"""

    success = service.send_markdown_message([user_id], markdown_content)

    if success:
        print(f"✅ Markdown消息发送成功 -> {user_id}")
        return True
    else:
        print(f"❌ Markdown消息发送失败")
        return False

def main():
    """主测试函数"""
    print("\n")
    print("🔧 企业微信消息推送测试工具")
    print("=" * 60)
    print()

    # 1. 检查配置
    if not test_wework_configuration():
        print("\n测试终止：配置不完整")
        return

    # 2. 测试Access Token
    if not test_get_access_token():
        print("\n测试终止：无法获取Access Token")
        print("\n可能的原因：")
        print("1. CorpID或Secret配置错误")
        print("2. 网络连接问题")
        print("3. 企业微信API访问限制")
        return

    # 3. 选择测试项目
    print("\n" + "=" * 60)
    print("选择测试项目:")
    print("=" * 60)
    print("1. 发送文本消息")
    print("2. 发送文本卡片消息")
    print("3. 发送Markdown消息")
    print("4. 全部测试")
    print("0. 退出")
    print()

    choice = input("请选择 (0-4): ").strip()

    if choice == '1':
        test_send_text_message()
    elif choice == '2':
        test_send_textcard_message()
    elif choice == '3':
        test_send_markdown_message()
    elif choice == '4':
        test_send_text_message()
        test_send_textcard_message()
        test_send_markdown_message()
    elif choice == '0':
        print("退出测试")
    else:
        print("无效选择")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == '__main__':
    main()
