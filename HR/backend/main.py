# CRITICAL: Load .env BEFORE any other imports that may use shared.auth
# This ensures JWT_SECRET_KEY is available when jwt_utils.py is imported
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

from app import create_app

# Create Flask application
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8003))
    # 安全修复：从环境变量读取 debug 模式，默认关闭
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"HR Backend starting on port {port}, debug={debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
