"""
导入东莞厂离职员工到HR数据库
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

# 读取Excel - 离职人员sheet, 第3行是表头(index=2)
excel_file = r'C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls'
df = pd.read_excel(excel_file, sheet_name='离职人员', header=2)

print("列名:", df.columns.tolist())
print(f"总行数: {len(df)}")
print("\n前5行数据:")
print(df.head())

# 手动设置列名
df.columns = ['序号', '工号', '姓名', '性别', '民族', '学历', '入厂时间', '职位',
              '离职时间', '离职原因', '籍贯', '出生年月', '联系电话', '紧急联系人姓名',
              '紧急联络人电话', '身份证地址', '身份证号码', '银行卡', '备注',
              'col19', 'col20', 'col21', 'col22']

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
    phone = re.sub(r'[^\d]', '', phone)
    if len(phone) >= 11:
        return phone[:11]
    return phone if phone else None

def clean_id_card(val):
    """清理身份证号码"""
    if pd.isna(val):
        return None
    id_card = str(val).strip().replace(' ', '')
    if len(id_card) >= 15:
        return id_card
    return None

def clean_bank_card(val):
    """清理银行卡号"""
    if pd.isna(val):
        return None
    bank = str(val).strip().replace(' ', '')
    if len(bank) >= 10:
        return bank
    return None

# 连接数据库
conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

try:
    # 获取工厂ID
    cursor.execute("SELECT id FROM factories WHERE name = '东莞厂'")
    factory = cursor.fetchone()
    factory_id = factory[0] if factory else 1

    # 获取岗位ID映射
    cursor.execute("SELECT id, name FROM positions")
    position_ids = {row[1]: row[0] for row in cursor.fetchall()}

    # 统计
    imported = 0
    skipped = 0
    new_positions = set()

    for idx, row in df.iterrows():
        # 跳过空行
        if pd.isna(row['姓名']) or str(row['姓名']).strip() == '':
            continue

        name = str(row['姓名']).strip()
        emp_no = str(row['工号']).strip() if not pd.isna(row['工号']) else f'DG_R{idx+1:04d}'

        # 跳过已存在的工号
        cursor.execute("SELECT id FROM employees WHERE empNo = %s", (emp_no,))
        if cursor.fetchone():
            skipped += 1
            continue

        # 获取其他字段
        gender = str(row['性别']).strip() if not pd.isna(row['性别']) else None
        education = str(row['学历']).strip() if not pd.isna(row['学历']) else None
        hire_date = parse_date(row['入厂时间'])
        position = str(row['职位']).strip() if not pd.isna(row['职位']) else None
        resign_date = parse_date(row['离职时间'])
        resign_reason = str(row['离职原因']).strip() if not pd.isna(row['离职原因']) else None
        native_place = str(row['籍贯']).strip() if not pd.isna(row['籍贯']) else None
        birth_date = parse_date(row['出生年月'])
        phone = clean_phone(row['联系电话'])
        emergency_contact = str(row['紧急联系人姓名']).strip() if not pd.isna(row['紧急联系人姓名']) else None
        emergency_phone = clean_phone(row['紧急联络人电话'])
        id_address = str(row['身份证地址']).strip() if not pd.isna(row['身份证地址']) else None
        id_card = clean_id_card(row['身份证号码'])
        bank_card = clean_bank_card(row['银行卡'])

        if position and position not in position_ids:
            new_positions.add(position)

        cursor.execute("""
            INSERT INTO employees (
                empNo, name, gender, education, native_place,
                title, position_id,
                factory_id, hire_date, birth_date,
                phone, emergency_contact, emergency_phone,
                home_address, id_card, bank_card,
                resignation_date, remark,
                employment_status, is_blacklisted, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                'Resigned', 0, NOW(), NOW()
            )
        """, (
            emp_no, name, gender, education, native_place,
            position, position_ids.get(position),
            factory_id, hire_date, birth_date,
            phone, emergency_contact, emergency_phone,
            id_address, id_card, bank_card,
            resign_date, resign_reason
        ))
        imported += 1

        if imported % 100 == 0:
            print(f"  已导入 {imported} 条...")

    # 创建新发现的岗位
    for pos_idx, pos in enumerate(new_positions):
        if pos:
            cursor.execute("""
                INSERT IGNORE INTO positions (name, code, is_active, sort_order, created_at, updated_at)
                VALUES (%s, %s, 1, 99, NOW(), NOW())
            """, (pos, f'NEW_R{pos_idx+1}'))
            print(f"创建新岗位: {pos}")

    conn.commit()

    # 统计结果
    cursor.execute("SELECT COUNT(*) FROM employees WHERE employment_status = 'Active'")
    active_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM employees WHERE employment_status = 'Resigned'")
    resigned_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM employees")
    total_count = cursor.fetchone()[0]

    print(f"\n✅ 导入完成！")
    print(f"   新导入离职员工: {imported}名")
    print(f"   跳过已存在: {skipped}名")
    print(f"   在职员工总数: {active_count}名")
    print(f"   离职员工总数: {resigned_count}名")
    print(f"   员工总数: {total_count}名")

except Exception as e:
    conn.rollback()
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
