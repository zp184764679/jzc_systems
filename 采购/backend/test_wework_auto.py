# -*- coding: utf-8 -*-
"""
企业微信自动化测试 - 发送测试消息到ZhouPeng
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from services.wework_service import get_wework_service

def main():
    print("=" * 60)
    print("企业微信自动化测试")
    print("=" * 60)

    # 检查配置
    service = get_wework_service()

    print(f"\n配置信息:")
    print(f"  CorpID: {service.corp_id}")
    print(f"  AgentID: {service.agent_id}")
    print(f"  配置状态: {'✅ 启用' if service.is_enabled() else '❌ 未启用'}")

    # 获取Access Token
    print(f"\n获取Access Token...")
    token = service.get_access_token()

    if not token:
        print("❌ 无法获取Access Token，测试终止")
        return

    print(f"✅ Access Token获取成功: {token[:20]}...")

    # 发送测试消息到 ZhouPeng
    user_id = 'ZhouPeng'
    print(f"\n发送测试消息到: {user_id}")

    # 测试1: 文本消息
    print("\n[测试1] 发送文本消息...")
    text_content = """【企业微信测试】

您好！这是来自采购系统的测试消息。

如果您收到这条消息，说明：
✅ 企业微信配置正确
✅ Access Token获取成功
✅ 消息推送功能正常

测试时间: 2025-11-05
系统: 采购管理系统
测试人: Claude"""

    success = service.send_text_message([user_id], text_content)
    print(f"{'✅ 成功' if success else '❌ 失败'}")

    # 测试2: 文本卡片消息
    print("\n[测试2] 发送文本卡片消息...")
    success = service.send_textcard_message(
        user_ids=[user_id],
        title="【测试】采购申请通知",
        description="""
<div class="gray">申请人：周鹏</div>
<div class="gray">部门：研发部</div>
<div class="gray">申请时间：2025-11-05 22:10</div>
<div class="normal">物料数量：5 项</div>
<div class="highlight">状态：待审批</div>
""",
        url="http://61.145.212.28:3000",
        btntxt="立即查看"
    )
    print(f"{'✅ 成功' if success else '❌ 失败'}")

    # 测试3: Markdown消息
    print("\n[测试3] 发送Markdown消息...")
    markdown_content = """## 【测试】采购申请通知

**申请单号**: PR20251105001
**申请人**: 周鹏
**部门**: 研发部
**申请时间**: 2025-11-05 22:10
**物料数量**: 5 项

**物料清单**:
> 1. 螺丝 M3x10 x 100个
> 2. 螺母 M3 x 100个
> 3. 垫片 M3 x 50个

> **状态**: <font color="warning">待审批</font>
>
> [点击查看详情并审批](http://61.145.212.28:3000/pr/test)
"""

    success = service.send_markdown_message([user_id], markdown_content)
    print(f"{'✅ 成功' if success else '❌ 失败'}")

    print("\n" + "=" * 60)
    print("测试完成！请检查企业微信是否收到3条测试消息")
    print("=" * 60)

if __name__ == '__main__':
    main()
