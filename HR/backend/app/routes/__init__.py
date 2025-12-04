from app.routes.employees import employees_bp
from app.routes.base_data import bp as base_data_bp
from app.routes.auth import auth_bp

__all__ = ['employees_bp', 'base_data_bp', 'auth_bp']
