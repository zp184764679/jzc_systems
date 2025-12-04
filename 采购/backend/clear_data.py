"""清空采购系统数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text

db_uri = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    "mysql+pymysql://zhoupeng:ZPexak472008@127.0.0.1:3307/caigou?charset=utf8mb4"
)
engine = create_engine(db_uri)

with engine.connect() as conn:
    conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
    conn.execute(text('TRUNCATE TABLE pr_item'))
    conn.execute(text('TRUNCATE TABLE pr'))
    conn.execute(text('TRUNCATE TABLE price_history'))
    conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
    conn.commit()
    print('✅ 数据已清空: pr, pr_item, price_history')
