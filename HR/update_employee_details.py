"""
更新员工详细信息（出生年月、联系电话、紧急联系人等）
"""
import pandas as pd
import pymysql
from datetime import datetime
import re

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'app',
    'password': 'app',
    'database': 'hr_system',
    'charset': 'utf8mb4'
}

# 读取Excel
excel_file = r'C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls'
df = pd.read_excel(excel_file, sheet_name='总人数', header=2)

print("列名:", df.columns.tolist())

def parse_date(val):
    """解析日期"""
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.date()
    val_str = str(val).strip()
    if not val_str or val_str == 'NaN' or val_str == 'nan':
        return None
    try:
        if '/' in val_str:
            match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', val_str)
            if match:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date()
        return pd.to_datetime(val).date()
    except:
        return None

def clean_phone(val):
    """清理电话号码"""
    if pd.isna(val):
        return None
    phone = str(val).strip()
    # 移除非数字字符
    phone = re.sub(r'[^\d]', '', phone)
    if len(phone) >= 11:
        return phone[:11]
    elif len(phone) >= 7:
        return phone
    return None

def clean_id_card(val):
    """清理身份证号码"""
    if pd.isna(val):
        return None
    id_card = str(val).strip().replace(' ', '').replace('\n', '')
    # 去除可能的小数点
    if '.' in id_card:
        id_card = id_card.split('.')[0]
    if len(id_card) >= 15:
        return id_card
    return None

def clean_bank_card(val):
    """清理银行卡号"""
    if pd.isna(val):
        return None
    bank = str(val).strip().replace(' ', '').replace('\n', '')
    # 去除可能的小数点
    if '.' in bank:
        bank = bank.split('.')[0]
    if len(bank) >= 10:
        return bank
    return None

def clean_string(val):
    """清理字符串"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == '' or s.lower() == 'nan':
        return None
    return s

# 连接数据库
conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

try:
    updated = 0
    not_found = 0

    for idx, row in df.iterrows():
        # 跳过空行
        if pd.isna(row['姓名']) or str(row['姓名']).strip() == '':
            continue

        emp_no = str(row['工号']).strip() if not pd.isna(row['工号']) else None
        if not emp_no:
            continue

        # 去除工号中可能的.0
        if '.' in emp_no:
            emp_no = emp_no.split('.')[0]

        # 解析字段
        birth_date = parse_date(row['出生年月'])
        phone = clean_phone(row['联系电话'])
        emergency_contact = clean_string(row['紧急联系人姓名'])
        emergency_phone = clean_phone(row['紧急联络人电话'])
        home_address = clean_string(row['身份证地址'])
        id_card = clean_id_card(row['身份证号码'])
        bank_card = clean_bank_card(row['银行卡'])

        # 其他字段
        nationality = clean_string(row['民族']) if '民族' in row else None
        education = clean_string(row['学历']) if '学历' in row else None
        native_place = clean_string(row['籍贯']) if '籍贯' in row else None

        # 处理特殊列名（带换行符）
        salary_type = None
        accommodation = None
        for col in df.columns:
            if '薪资' in col:
                salary_type = clean_string(row[col])
            if '住宿' in col:
                accommodation = clean_string(row[col])

        # 更新数据库
        cursor.execute("""
            UPDATE employees SET
                birth_date = COALESCE(%s, birth_date),
                phone = COALESCE(%s, phone),
                emergency_contact = COALESCE(%s, emergency_contact),
                emergency_phone = COALESCE(%s, emergency_phone),
                home_address = COALESCE(%s, home_address),
                id_card = COALESCE(%s, id_card),
                bank_card = COALESCE(%s, bank_card),
                nationality = COALESCE(%s, nationality),
                education = COALESCE(%s, education),
                native_place = COALESCE(%s, native_place),
                salary_type = COALESCE(%s, salary_type),
                accommodation = COALESCE(%s, accommodation),
                updated_at = NOW()
            WHERE empNo = %s
        """, (
            birth_date, phone, emergency_contact, emergency_phone,
            home_address, id_card, bank_card,
            nationality, education, native_place,
            salary_type, accommodation,
            emp_no
        ))

        if cursor.rowcount > 0:
            updated += 1
        else:
            not_found += 1
            print(f"  未找到员工: {emp_no}")

    conn.commit()

    # 统计结果
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN birth_date IS NOT NULL THEN 1 ELSE 0 END) as with_birth,
            SUM(CASE WHEN phone IS NOT NULL THEN 1 ELSE 0 END) as with_phone,
            SUM(CASE WHEN emergency_contact IS NOT NULL THEN 1 ELSE 0 END) as with_emergency_contact,
            SUM(CASE WHEN emergency_phone IS NOT NULL THEN 1 ELSE 0 END) as with_emergency_phone,
            SUM(CASE WHEN home_address IS NOT NULL THEN 1 ELSE 0 END) as with_address,
            SUM(CASE WHEN id_card IS NOT NULL THEN 1 ELSE 0 END) as with_id_card,
            SUM(CASE WHEN bank_card IS NOT NULL THEN 1 ELSE 0 END) as with_bank_card
        FROM employees WHERE employment_status = 'Active'
    """)
    result = cursor.fetchone()

    print(f"\n✅ 更新完成！")
    print(f"   更新记录: {updated}条")
    print(f"   未找到: {not_found}条")
    print(f"\n在职员工详细信息统计 (共{result[0]}人):")
    print(f"   出生年月: {result[1]}人")
    print(f"   联系电话: {result[2]}人")
    print(f"   紧急联系人: {result[3]}人")
    print(f"   紧急电话: {result[4]}人")
    print(f"   身份证地址: {result[5]}人")
    print(f"   身份证号码: {result[6]}人")
    print(f"   银行卡: {result[7]}人")

except Exception as e:
    conn.rollback()
    print(f"❌ 更新失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
