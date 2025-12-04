# -*- coding: utf-8 -*-
"""
企业微信OAuth2扫码登录
挂载到 /api/v1/auth/wework
"""
from flask import Blueprint, request, jsonify, redirect
from models.user import User
from extensions import db
from services.wework_user_sync import sync_user_from_wework, sync_user_to_wework
from services.wework_service import get_wework_service
import os
import secrets
import logging

logger = logging.getLogger(__name__)

URL_PREFIX = '/api/v1/auth/wework'

bp_wework_oauth = Blueprint('wework_oauth', __name__)


def generate_jwt_token(user):
    """生成JWT Token（简化版，实际应使用你们现有的JWT逻辑）"""
    import jwt
    import datetime

    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }

    secret_key = os.getenv('APP_SECRET', 'your_secret_key')
    token = jwt.encode(payload, secret_key, algorithm='HS256')

    return token


@bp_wework_oauth.route('/authorize', methods=['GET'])
def authorize():
    """
    生成企业微信授权URL（移动端）

    GET /api/v1/auth/wework/authorize

    Returns:
        {
            "auth_url": "https://open.weixin.qq.com/connect/oauth2/authorize?..."
        }
    """
    try:
        wework = get_wework_service()

        if not wework.is_enabled():
            return jsonify({
                'error': '企业微信服务未启用',
                'code': 'WEWORK_DISABLED'
            }), 400

        # 授权回调地址（需要在企业微信后台配置可信域名）
        h5_domain = os.getenv('WEWORK_H5_DOMAIN', 'http://61.145.212.28:3000')
        redirect_uri = f"{h5_domain}/auth/wework/callback"

        # 生成state防止CSRF攻击
        state = secrets.token_urlsafe(16)

        # 构建授权URL
        corp_id = wework.corp_id
        agent_id = wework.agent_id

        # 企业微信网页授权URL（移动端）
        auth_url = f"https://open.weixin.qq.com/connect/oauth2/authorize"
        params = (
            f"?appid={corp_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=snsapi_base"  # 静默授权，获取UserID
            f"&state={state}"
            f"&agentid={agent_id}"
            f"#wechat_redirect"
        )

        full_auth_url = auth_url + params

        logger.info(f"生成企业微信授权URL（移动端）: {full_auth_url}")

        return jsonify({
            'auth_url': full_auth_url,
            'state': state
        })

    except Exception as e:
        logger.error(f"❌ 生成授权URL失败: {e}")
        return jsonify({'error': str(e)}), 500


@bp_wework_oauth.route('/qr-authorize', methods=['GET'])
def qr_authorize():
    """
    生成企业微信Web端扫码登录URL

    GET /api/v1/auth/wework/qr-authorize

    Returns:
        {
            "qr_url": "https://open.work.weixin.qq.com/wwopen/sso/qrConnect?..."
        }
    """
    try:
        wework = get_wework_service()

        if not wework.is_enabled():
            return jsonify({
                'error': '企业微信服务未启用',
                'code': 'WEWORK_DISABLED'
            }), 400

        # 获取后端地址用于回调
        backend_domain = os.getenv('BACKEND_DOMAIN', 'http://61.145.212.28:5001')
        redirect_uri = f"{backend_domain}/api/v1/auth/wework/callback"

        # 生成state防止CSRF攻击
        state = secrets.token_urlsafe(16)

        # 构建扫码登录URL
        corp_id = wework.corp_id
        agent_id = wework.agent_id

        # URL编码redirect_uri
        import urllib.parse
        encoded_redirect_uri = urllib.parse.quote(redirect_uri, safe='')

        # 企业微信Web端扫码登录URL
        qr_url = (
            f"https://open.work.weixin.qq.com/wwopen/sso/qrConnect"
            f"?appid={corp_id}"
            f"&agentid={agent_id}"
            f"&redirect_uri={encoded_redirect_uri}"
            f"&state={state}"
        )

        logger.info(f"生成企业微信扫码登录URL: {qr_url}")

        return jsonify({
            'qr_url': qr_url,
            'state': state
        })

    except Exception as e:
        logger.error(f"❌ 生成扫码URL失败: {e}")
        return jsonify({'error': str(e)}), 500


@bp_wework_oauth.route('/callback', methods=['GET'])
def callback():
    """
    企业微信授权回调

    GET /api/v1/auth/wework/callback?code=xxx&state=xxx

    流程：
    1. 用code换取UserID
    2. 查询系统是否已有此用户
    3. 如果有，直接登录
    4. 如果没有，获取详细信息，跳转到确认页面
    """
    try:
        code = request.args.get('code')
        state = request.args.get('state')

        if not code:
            return jsonify({'error': '缺少授权code'}), 400

        # 1. 通过code获取UserID
        wework = get_wework_service()
        user_info = get_user_info_by_code(wework, code)

        if not user_info or 'UserId' not in user_info:
            logger.error(f"❌ 获取UserID失败: {user_info}")
            return jsonify({'error': '获取用户信息失败'}), 400

        wework_user_id = user_info['UserId']
        logger.info(f"✅ 获取到UserID: {wework_user_id}")

        # 2. 查询系统中是否已有此用户
        user = User.query.filter_by(wework_user_id=wework_user_id).first()

        if user:
            # 已有账号，直接登录
            logger.info(f"✅ 用户已存在，直接登录: {user.username}")
            token = generate_jwt_token(user)

            # 重定向到前端，带上token
            h5_domain = os.getenv('WEWORK_H5_DOMAIN', 'http://61.145.212.28:3000')
            return redirect(f"{h5_domain}/auth/success?token={token}")

        else:
            # 3. 新用户，获取详细信息
            logger.info(f"🆕 新用户，获取详细信息: {wework_user_id}")
            detail = sync_user_from_wework(wework_user_id)

            if not detail:
                return jsonify({'error': '获取用户详细信息失败'}), 400

            # 4. 跳转到确认页面，让用户确认/修改部门
            h5_domain = os.getenv('WEWORK_H5_DOMAIN', 'http://61.145.212.28:3000')

            # 将用户信息传递到前端确认页面
            import urllib.parse
            params = urllib.parse.urlencode({
                'wework_user_id': detail['wework_user_id'],
                'username': detail['username'],
                'department': detail.get('department', ''),
                'phone': detail.get('phone', ''),
                'email': detail.get('email', ''),
                'is_new': 'true'
            })

            return redirect(f"{h5_domain}/auth/confirm?{params}")

    except Exception as e:
        logger.error(f"❌ 授权回调处理失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp_wework_oauth.route('/confirm', methods=['POST'])
def confirm_register():
    """
    确认注册/绑定

    POST /api/v1/auth/wework/confirm
    {
        "wework_user_id": "ZhouPeng",
        "username": "周鹏",
        "department": "研发部",  // 用户可能已修改
        "phone": "13800138000",
        "email": "zp@company.com",
        "sync_to_wework": true  // 是否同步部门到企业微信
    }

    Returns:
        {
            "token": "xxx",
            "user": {...}
        }
    """
    try:
        data = request.get_json()

        wework_user_id = data.get('wework_user_id')
        username = data.get('username')
        department = data.get('department', '')
        phone = data.get('phone', '')
        email = data.get('email', '')
        sync_to_wework_flag = data.get('sync_to_wework', False)

        if not wework_user_id or not username:
            return jsonify({'error': '缺少必要参数'}), 400

        # 检查是否已存在
        existing_user = User.query.filter_by(wework_user_id=wework_user_id).first()
        if existing_user:
            return jsonify({'error': '用户已存在'}), 400

        # 创建新用户
        user = User(
            username=username,
            email=email or f"{wework_user_id}@company.com",
            department=department,
            phone=phone,
            wework_user_id=wework_user_id,
            status='approved',  # 企业微信用户自动审核通过
            role='user'
        )

        # 设置随机密码（用户以后可以修改）
        random_password = secrets.token_urlsafe(16)
        user.set_password(random_password)

        db.session.add(user)
        db.session.commit()

        logger.info(f"✅ 新用户注册成功: {username} ({wework_user_id})")

        # 如果用户选择同步部门到企业微信
        if sync_to_wework_flag and department:
            success = sync_user_to_wework(wework_user_id, department)
            if success:
                logger.info(f"✅ 部门已同步到企业微信: {department}")
            else:
                logger.warning(f"⚠️  部门同步到企业微信失败（不影响注册）")

        # 生成Token
        token = generate_jwt_token(user)

        return jsonify({
            'token': token,
            'user': user.to_dict(),
            'is_new': True,
            'message': '注册成功'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 确认注册失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp_wework_oauth.route('/bind', methods=['POST'])
def bind_wework():
    """
    已有账号绑定企业微信

    POST /api/v1/auth/wework/bind
    Headers: Authorization: Bearer <token>
    Body: {
        "code": "xxx"  // 企业微信授权code
    }

    Returns:
        {
            "success": true,
            "wework_user_id": "ZhouPeng"
        }
    """
    try:
        # 获取当前登录用户（需要从JWT中解析）
        # 这里简化处理，实际应使用你们的JWT中间件
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': '未登录'}), 401

        # 解析JWT获取user_id（简化版）
        import jwt
        secret_key = os.getenv('APP_SECRET', 'your_secret_key')
        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
        except:
            return jsonify({'error': 'Token无效'}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 获取企业微信授权code
        code = request.json.get('code')
        if not code:
            return jsonify({'error': '缺少授权code'}), 400

        # 通过code获取UserID
        wework = get_wework_service()
        user_info = get_user_info_by_code(wework, code)

        if not user_info or 'UserId' not in user_info:
            return jsonify({'error': '获取用户信息失败'}), 400

        wework_user_id = user_info['UserId']

        # 检查此UserID是否已被其他账号绑定
        existing = User.query.filter_by(wework_user_id=wework_user_id).first()
        if existing and existing.id != user.id:
            return jsonify({'error': '此企业微信账号已被其他用户绑定'}), 400

        # 绑定
        user.wework_user_id = wework_user_id
        db.session.commit()

        logger.info(f"✅ 用户绑定企业微信成功: {user.username} -> {wework_user_id}")

        return jsonify({
            'success': True,
            'wework_user_id': wework_user_id,
            'message': '绑定成功'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ 绑定企业微信失败: {e}")
        return jsonify({'error': str(e)}), 500


def get_user_info_by_code(wework, code: str):
    """通过code获取用户信息"""
    try:
        import requests

        url = "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo"
        params = {
            'access_token': wework.get_access_token(),
            'code': code
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get('errcode') == 0:
            return data
        else:
            logger.error(f"❌ 获取用户信息失败: {data.get('errmsg')}")
            return None

    except Exception as e:
        logger.error(f"❌ 获取用户信息异常: {e}")
        return None


# 导出蓝图供app.py自动注册
BLUEPRINTS = [(bp_wework_oauth, URL_PREFIX)]
