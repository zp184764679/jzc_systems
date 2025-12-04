# -*- coding: utf-8 -*-
"""
测试微信服务号回调接口
"""
import hashlib
import time
import requests

# 测试配置
BASE_URL = "http://127.0.0.1:5001"
TOKEN = "caigou_wechat_2025"

def generate_signature(token, timestamp, nonce):
    """生成微信签名"""
    tmp_list = [token, timestamp, nonce]
    tmp_list.sort()
    tmp_str = ''.join(tmp_list)
    return hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()

def test_server_verification():
    """测试服务器验证（GET请求）"""
    print("\n=== 测试1：服务器验证（GET请求）===")

    timestamp = str(int(time.time()))
    nonce = "test123456"
    echostr = "hello_wechat"

    signature = generate_signature(TOKEN, timestamp, nonce)

    url = f"{BASE_URL}/api/v1/wechat/callback"
    params = {
        'signature': signature,
        'timestamp': timestamp,
        'nonce': nonce,
        'echostr': echostr
    }

    print(f"请求URL: {url}")
    print(f"参数: {params}")
    print(f"生成的签名: {signature}")

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200 and response.text == echostr:
            print("✅ 服务器验证成功！")
            return True
        else:
            print("❌ 服务器验证失败！")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_message_callback():
    """测试消息回调（POST请求）"""
    print("\n=== 测试2：消息回调（POST请求）===")

    timestamp = str(int(time.time()))
    nonce = "test789"

    signature = generate_signature(TOKEN, timestamp, nonce)

    url = f"{BASE_URL}/api/v1/wechat/callback"
    params = {
        'signature': signature,
        'timestamp': timestamp,
        'nonce': nonce
    }

    # 模拟文本消息XML
    xml_data = f"""<xml>
<ToUserName><![CDATA[gh_test123456]]></ToUserName>
<FromUserName><![CDATA[oTest123456789]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[测试消息]]></Content>
<MsgId>1234567890</MsgId>
</xml>"""

    print(f"请求URL: {url}")
    print(f"参数: {params}")
    print(f"消息内容: 测试消息")

    try:
        response = requests.post(
            url,
            params=params,
            data=xml_data.encode('utf-8'),
            headers={'Content-Type': 'text/xml'},
            timeout=10
        )
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")

        if response.status_code == 200:
            print("✅ 消息回调处理成功！")
            return True
        else:
            print("❌ 消息回调处理失败！")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("微信服务号回调接口测试")
    print("=" * 60)

    # 测试1：服务器验证
    result1 = test_server_verification()

    # 测试2：消息回调
    result2 = test_message_callback()

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"服务器验证: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"消息回调: {'✅ 通过' if result2 else '❌ 失败'}")

    if result1 and result2:
        print("\n🎉 所有测试通过！可以在微信公众平台提交配置了。")
        print("\n配置信息：")
        print(f"服务器地址(URL): http://61.145.212.28/api/v1/wechat/callback")
        print(f"令牌(Token): {TOKEN}")
        print(f"消息加解密方式: 明文模式")
    else:
        print("\n⚠️  部分测试失败，请检查后端服务和配置。")
