"""
客户数据导入脚本
从 客户清单250902.xlsx 导入客户到 CRM 数据库
使用 Flask-SQLAlchemy 上下文
"""
import sys
import os

# 确保能找到 app 模块
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from datetime import datetime

# Excel 文件路径
EXCEL_PATH = os.path.join(os.path.dirname(__file__), '..', '客户清单250902.xlsx')

def normalize_currency(val):
    """统一币种格式"""
    if pd.isna(val) or not val:
        return None
    val = str(val).strip().upper()
    if val in ['RMB', '人民币', 'CNH']:
        return 'CNY'
    if val in ['USD', '美元']:
        return 'USD'
    if val in ['EUR', '欧元']:
        return 'EUR'
    if val in ['HKD', '港币']:
        return 'HKD'
    return val

def safe_int(val, default=None):
    """安全转换为整数"""
    if pd.isna(val):
        return default
    try:
        return int(float(val))
    except:
        return default

def safe_str(val):
    """安全转换为字符串"""
    if pd.isna(val):
        return None
    return str(val).strip() if val else None

def import_customers():
    """导入客户数据"""
    from app import create_app, db
    from app.models.customer import Customer

    app = create_app()

    with app.app_context():
        print(f"读取 Excel 文件: {EXCEL_PATH}")

        # 读取 Excel，跳过第一行标题
        df = pd.read_excel(EXCEL_PATH, header=1)

        # 重命名列
        df.columns = ['序号', '客户代码', '客户简称', '客户全称', '默认币种', '含税点数',
                      '结算周期', '结算方式', '对账日期', '公司地址']

        print(f"共读取 {len(df)} 条客户记录")

        # 获取现有客户代码
        existing_customers = Customer.query.filter(Customer.code.isnot(None)).all()
        existing = set(c.code for c in existing_customers)

        print(f"数据库中已有 {len(existing)} 个客户")

        imported = 0
        skipped = 0
        errors = 0

        for idx, row in df.iterrows():
            code = safe_str(row['客户代码'])
            if not code:
                continue

            # 检查是否已存在
            if code in existing:
                skipped += 1
                continue

            try:
                seq_no = safe_int(row['序号'])
                customer = Customer(
                    seq_no=seq_no,
                    code=code,
                    short_name=safe_str(row['客户简称']),
                    name=safe_str(row['客户全称']),
                    currency_default=normalize_currency(row['默认币种']),
                    tax_points=safe_int(row['含税点数']),
                    settlement_cycle_days=safe_int(row['结算周期']),
                    settlement_method=safe_str(row['结算方式']),
                    statement_day=safe_int(row['对账日期']),
                    address=safe_str(row['公司地址']),
                    contacts=[],  # 空联系人列表
                )

                db.session.add(customer)
                imported += 1

                # 每20条提交一次
                if imported % 20 == 0:
                    db.session.commit()
                    print(f"  已导入 {imported} 条...")

            except Exception as e:
                errors += 1
                print(f"  导入 {code} 失败: {e}")
                db.session.rollback()

        # 提交剩余的
        db.session.commit()

        print(f"\n导入完成!")
        print(f"  - 成功导入: {imported} 条")
        print(f"  - 跳过(已存在): {skipped} 条")
        print(f"  - 失败: {errors} 条")

        # 显示总数
        total = Customer.query.count()
        print(f"  - 数据库总客户数: {total}")

if __name__ == '__main__':
    import_customers()
