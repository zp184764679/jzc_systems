"""
根据Excel更新现有客户的公司地址
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from app import create_app, db
from app.models.customer import Customer

EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', '客户清单250902.xlsx')

def safe_str(val):
    if pd.isna(val):
        return None
    return str(val).strip() if val else None

def update_addresses():
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
            address = safe_str(row['公司地址'])

            if not code:
                continue

            # 按客户代码查找
            customer = Customer.query.filter_by(code=code).first()
            if customer:
                if address and address != customer.address:
                    print(f"  更新 {code}: {customer.address} -> {address}")
                    customer.address = address
                    updated += 1
            else:
                not_found += 1
                print(f"  未找到客户: {code}")

        db.session.commit()
        print(f"\n更新完成!")
        print(f"  - 已更新地址: {updated} 条")
        print(f"  - 未找到: {not_found} 条")

if __name__ == '__main__':
    update_addresses()
