# -*- coding: utf-8 -*-
"""
微信服务号消息回调接口
用于接收微信服务器的消息推送和验证服务器配置
"""
from flask import Blueprint, request
import hashlib
import os
import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

URL_PREFIX = '/api/v1/wechat'

bp_wechat_callback = Blueprint('wechat_callback', __name__)


def verify_signature(signature: str, timestamp: str, nonce: str) -> bool:
    """
    验证微信服务器签名

    Args:
        signature: 微信加密签名
        timestamp: 时间戳
        nonce: 随机数

    Returns:
        签名是否正确
    """
    token = os.getenv('WECHAT_TOKEN', 'caigou_wechat_2025')

    # 1. 将token、timestamp、nonce三个参数进行字典序排序
    tmp_list = [token, timestamp, nonce]
    tmp_list.sort()

    # 2. 将三个参数字符串拼接成一个字符串进行sha1加密
    tmp_str = ''.join(tmp_list)
    tmp_signature = hashlib.sha1(tmp_str.encode('utf-8')).hexdigest()

    # 3. 比较加密后的字符串与signature是否相等
    return tmp_signature == signature


@bp_wechat_callback.route('/callback', methods=['GET', 'POST'])
def wechat_callback():
    """
    微信服务号消息回调

    GET: 验证服务器配置
    POST: 接收用户消息和事件
    """
    # GET请求：验证服务器配置
    if request.method == 'GET':
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')
        echostr = request.args.get('echostr', '')

        logger.info(f"收到微信服务器验证请求 - timestamp: {timestamp}, nonce: {nonce}")

        # 验证签名
        if verify_signature(signature, timestamp, nonce):
            logger.info("✅ 微信服务器验证成功")
            return echostr
        else:
            logger.error("❌ 微信服务器验证失败：签名不匹配")
            return 'error', 403

    # POST请求：接收消息
    elif request.method == 'POST':
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')

        # 验证签名
        if not verify_signature(signature, timestamp, nonce):
            logger.error("❌ 微信消息签名验证失败")
            return 'error', 403

        # 解析XML消息
        try:
            xml_data = request.data
            root = ET.fromstring(xml_data)

            msg_type = root.find('MsgType').text
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text

            logger.info(f"收到微信消息 - 类型: {msg_type}, FromUser: {from_user[:10]}...")

            # 处理不同类型的消息
            if msg_type == 'event':
                return handle_event(root, from_user, to_user)
            elif msg_type == 'text':
                return handle_text_message(root, from_user, to_user)
            else:
                logger.info(f"未处理的消息类型: {msg_type}")
                return 'success'

        except Exception as e:
            logger.error(f"❌ 处理微信消息异常: {e}")
            import traceback
            traceback.print_exc()
            return 'error', 500

    # 其他HTTP方法(HEAD, OPTIONS等)
    else:
        logger.warning(f"⚠️  收到不支持的HTTP方法: {request.method}")
        return 'Method Not Allowed', 405


def handle_event(root, from_user: str, to_user: str) -> str:
    """
    处理事件消息

    Args:
        root: XML根节点
        from_user: 发送者OpenID
        to_user: 公众号原始ID

    Returns:
        响应XML
    """
    event = root.find('Event').text

    if event == 'subscribe':
        # 用户关注事件
        logger.info(f"✅ 用户关注公众号 - OpenID: {from_user[:10]}...")
        return handle_subscribe(from_user, to_user)

    elif event == 'unsubscribe':
        # 用户取消关注事件
        logger.info(f"⚠️  用户取消关注公众号 - OpenID: {from_user[:10]}...")
        return handle_unsubscribe(from_user)

    elif event == 'CLICK':
        # 菜单点击事件
        event_key = root.find('EventKey').text
        logger.info(f"用户点击菜单 - EventKey: {event_key}")
        return 'success'

    else:
        logger.info(f"未处理的事件类型: {event}")
        return 'success'


def handle_subscribe(openid: str, to_user: str) -> str:
    """
    处理用户关注事件

    Args:
        openid: 用户OpenID
        to_user: 公众号原始ID

    Returns:
        响应XML
    """
    try:
        # 保存用户OpenID到数据库（如果是供应商）
        from app import app
        from models.supplier import Supplier
        from extensions import db

        with app.app_context():
            # 检查是否是已注册的供应商（通过某种方式识别，如手机号）
            # 这里先简单记录日志，后续完善绑定逻辑
            logger.info(f"新用户关注，OpenID: {openid}")

            # TODO: 实现供应商OpenID绑定逻辑
            # 1. 显示绑定引导消息
            # 2. 用户输入手机号验证
            # 3. 绑定OpenID到供应商账号

        # 返回欢迎消息
        import time
        welcome_msg = """欢迎关注精之成精密五金！

您可以通过本公众号：
✅ 接收询价通知
✅ 查看询价详情
✅ 在线提交报价

如需绑定供应商账号，请回复您的手机号进行验证。"""

        return build_text_response(to_user, openid, welcome_msg, int(time.time()))

    except Exception as e:
        logger.error(f"❌ 处理关注事件异常: {e}")
        return 'success'


def handle_unsubscribe(openid: str) -> str:
    """
    处理用户取消关注事件

    Args:
        openid: 用户OpenID

    Returns:
        'success'
    """
    try:
        # 更新数据库中的订阅状态
        from app import app
        from models.supplier import Supplier
        from extensions import db

        with app.app_context():
            supplier = Supplier.query.filter_by(wechat_openid=openid).first()
            if supplier:
                supplier.is_subscribed = False
                db.session.commit()
                logger.info(f"✅ 更新供应商取消关注状态 - {supplier.company_name}")

        return 'success'

    except Exception as e:
        logger.error(f"❌ 处理取消关注事件异常: {e}")
        return 'success'


def handle_text_message(root, from_user: str, to_user: str) -> str:
    """
    处理文本消息

    Args:
        root: XML根节点
        from_user: 发送者OpenID
        to_user: 公众号原始ID

    Returns:
        响应XML
    """
    content = root.find('Content').text
    create_time = root.find('CreateTime').text

    logger.info(f"收到文本消息: {content}")

    # 判断是否是手机号（用于绑定供应商账号）
    if content.isdigit() and len(content) == 11:
        return handle_phone_bind(from_user, to_user, content, int(create_time))

    # 默认回复
    reply_msg = f"""您发送的内容是：{content}

如需帮助，请访问：http://61.145.212.28:3000"""

    return build_text_response(to_user, from_user, reply_msg, int(create_time))


def handle_phone_bind(openid: str, to_user: str, phone: str, create_time: int) -> str:
    """
    处理手机号绑定

    Args:
        openid: 用户OpenID
        to_user: 公众号原始ID
        phone: 手机号
        create_time: 消息创建时间

    Returns:
        响应XML
    """
    try:
        from app import app
        from models.supplier import Supplier
        from extensions import db

        with app.app_context():
            # 查找手机号对应的供应商
            supplier = Supplier.query.filter_by(contact_phone=phone).first()

            if supplier:
                # 绑定OpenID
                supplier.wechat_openid = openid
                supplier.is_subscribed = True
                db.session.commit()

                reply_msg = f"""✅ 绑定成功！

公司名称：{supplier.company_name}
联系人：{supplier.contact_person}

您现在可以接收询价通知了！"""

                logger.info(f"✅ 供应商绑定成功 - {supplier.company_name}")
            else:
                reply_msg = """❌ 未找到该手机号对应的供应商账号

请确认：
1. 手机号是否正确
2. 是否已在系统中注册

如有疑问，请联系采购部门。"""

                logger.warning(f"⚠️  未找到手机号对应的供应商: {phone}")

            return build_text_response(to_user, openid, reply_msg, create_time)

    except Exception as e:
        logger.error(f"❌ 处理手机号绑定异常: {e}")
        reply_msg = "系统繁忙，请稍后再试。"
        return build_text_response(to_user, openid, reply_msg, create_time)


def build_text_response(from_user: str, to_user: str, content: str, timestamp: int) -> str:
    """
    构建文本消息响应XML

    Args:
        from_user: 发送方（公众号）
        to_user: 接收方（用户）
        content: 文本内容
        timestamp: 时间戳

    Returns:
        XML字符串
    """
    import time
    xml_template = """<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{create_time}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""

    return xml_template.format(
        to_user=to_user,
        from_user=from_user,
        create_time=int(time.time()),
        content=content
    )


# 导出蓝图供app.py自动注册
BLUEPRINTS = [(bp_wechat_callback, URL_PREFIX)]
