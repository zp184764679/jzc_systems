from app.routes.employees import employees_bp
from app.routes.base_data import bp as base_data_bp
from app.routes.auth import auth_bp
from app.routes.attendance import attendance_bp
from app.routes.leave import leave_bp
from app.routes.payroll import payroll_bp
from app.routes.performance import performance_bp
from app.routes.recruitment import recruitment_bp

__all__ = ['employees_bp', 'base_data_bp', 'auth_bp', 'attendance_bp', 'leave_bp', 'payroll_bp', 'performance_bp', 'recruitment_bp']
