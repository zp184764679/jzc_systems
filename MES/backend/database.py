# 数据库配置 - 独立模块避免循环导入
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
