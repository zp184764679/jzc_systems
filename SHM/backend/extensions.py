# Flask extensions - 独立定义以避免循环导入
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
