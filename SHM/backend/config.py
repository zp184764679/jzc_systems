import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', '')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', os.getenv('MYSQL_ROOT_PASSWORD', ''))
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'cncplan')
    PORT = int(os.getenv('PORT', 8006))

    # Database configuration - Use MySQL if configured, otherwise SQLite
    if MYSQL_USER and MYSQL_PASSWORD:
        # MySQL configuration
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{DB_HOST}/{MYSQL_DATABASE}?charset=utf8mb4"
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
        }
    else:
        # SQLite configuration (fallback)
        import os.path
        db_path = os.path.join(os.path.dirname(__file__), 'shm.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        SQLALCHEMY_ENGINE_OPTIONS = {}

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # 跨系统API配置
    SCM_API_BASE_URL = os.getenv('SCM_API_BASE_URL', '')
    PDM_API_BASE_URL = os.getenv('PDM_API_BASE_URL', '')
    CRM_API_BASE_URL = os.getenv('CRM_API_BASE_URL', '')
    HR_API_BASE_URL = os.getenv('HR_API_BASE_URL', '')
