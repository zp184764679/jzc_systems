"""
Portal Backend API - 统一认证服务
提供员工和供应商登录，生成JWT token用于SSO
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from shared.auth import (
    User, init_auth_db,
    create_token_from_user, verify_password
)
import shared.auth.models as auth_models
from routes.system import system_bp
from routes.translate import translate_bp
from routes.doc_translate import doc_translate_bp

app = Flask(__name__)

# Configure CORS - 允许所有子系统前端访问
cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Initialize auth database
init_auth_db()

# Register blueprints
app.register_blueprint(system_bp)
app.register_blueprint(translate_bp)
app.register_blueprint(doc_translate_bp)


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Employee login endpoint"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '请提供用户名和密码'}), 400
    
    username = data['username']
    password = data['password']
    
    session = auth_models.AuthSessionLocal()
    try:
        # Find user by username
        user = session.query(User).filter_by(username=username).first()
        
        if not user:
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'error': '账户已被禁用，请联系管理员'}), 403
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # Only allow employees to login here
        if user.user_type != 'employee':
            return jsonify({'error': '请使用供应商登录入口'}), 403
        
        # Generate JWT token
        user_dict = user.to_dict()
        token = create_token_from_user(user_dict)
        
        return jsonify({
            'message': '登录成功',
            'token': token,
            'user': user_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'登录失败: {str(e)}'}), 500
    finally:
        session.close()


@app.route('/api/auth/supplier-login', methods=['POST'])
def supplier_login():
    """Supplier login endpoint"""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': '请提供用户名和密码'}), 400
    
    username = data['username']
    password = data['password']
    
    session = auth_models.AuthSessionLocal()
    try:
        # Find user by username
        user = session.query(User).filter_by(username=username).first()
        
        if not user:
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'error': '账户已被禁用，请联系管理员'}), 403
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # Only allow suppliers to login here
        if user.user_type != 'supplier':
            return jsonify({'error': '请使用员工登录入口'}), 403
        
        # Generate JWT token
        user_dict = user.to_dict()
        token = create_token_from_user(user_dict)
        
        return jsonify({
            'message': '登录成功',
            'token': token,
            'user': user_dict
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'登录失败: {str(e)}'}), 500
    finally:
        session.close()


@app.route('/api/auth/verify', methods=['POST'])
def verify_token_endpoint():
    """Verify JWT token"""
    from shared.auth import verify_token
    
    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({'error': '缺少token'}), 400
    
    token = data['token']
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Token无效或已过期'}), 401
    
    return jsonify({
        'valid': True,
        'user': payload
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'portal-backend'}), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'Portal Backend API',
        'version': '1.0.0',
        'endpoints': {
            'employee_login': '/api/auth/login',
            'supplier_login': '/api/auth/supplier-login',
            'verify_token': '/api/auth/verify',
            'health': '/health'
        }
    }), 200


if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 3002))
    print(f"🚀 Portal Backend API starting on port {port}")
    print(f"📍 Employee Login: http://localhost:{port}/api/auth/login")
    print(f"📍 Supplier Login: http://localhost:{port}/api/auth/supplier-login")
    app.run(host='0.0.0.0', port=port, debug=True)
