"""
根据Excel更新现有客户的seq_no字段
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from app import create_app, db
from app.models.customer import Customer

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', '客户清单250902.xlsx')

def safe_int(val, default=None):
    if pd.isna(val):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default

def safe_str(val):
    if pd.isna(val):
        return None
    return str(val).strip() if val else None

def update_seq_no():
    app = create_app()
    with app.app_context():
        print(f"读取 Excel: {EXCEL_PATH}")
        df = pd.read_excel(EXCEL_PATH, header=1)
        df.columns = ['序号', '客户代码', '客户简称', '客户全称', '默认币种', '含税点数',
                      '结算周期', '结算方式', '对账日期', '公司地址']

        updated = 0
        not_found = 0

        for idx, row in df.iterrows():
            code = safe_str(row['客户代码'])
            seq_no = safe_int(row['序号'])

            if not code or seq_no is None:
                continue

            # 按客户代码查找
            customer = Customer.query.filter_by(code=code).first()
            if customer:
                customer.seq_no = seq_no
                updated += 1
            else:
                not_found += 1
                print(f"  未找到客户: {code}")

        db.session.commit()
        print(f"\n更新完成!")
        print(f"  - 已更新: {updated} 条")
        print(f"  - 未找到: {not_found} 条")

if __name__ == '__main__':
    update_seq_no()
