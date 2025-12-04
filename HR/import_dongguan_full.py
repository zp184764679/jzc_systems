"""
导入东莞厂完整人事资料到HR数据库
包含：入厂时间、出生年月、联系电话、紧急联系人、身份证、银行卡等
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

# 读取Excel - 总人数sheet包含完整信息
excel_file = r'C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls'
df = pd.read_excel(excel_file, sheet_name='总人数', header=1)  # 第2行是表头

print("列名:", df.columns.tolist())
print(f"总行数: {len(df)}")

# 清理列名
df.columns = ['序号', '工号', '姓名', '性别', '民族', '学历', '入厂时间', '部门', '职位',
              '制卡', '薪资制', '住宿情况', '籍贯', '出生年月', '联系电话', '紧急联系人姓名',
              '紧急联络人电话', '身份证地址', '身份证号码', '银行卡', '备注',
              'col21', 'col22', 'col23', 'col24', 'col25']

# 部门映射（统一部门名称）
dept_mapping = {
    '加工中心': '加工中心',
    '走芯机': '走芯机',
    '数控': '数控',
    '磨床': '磨床',
    '铣床': '铣床',
    '铣床？': '铣床',
    '品质部': '全检组',
    '生管组': '生管',
    '行政部': '办公室',
    '/': '办公室',  # 司机、厂长等
}

def parse_date(val):
    """解析日期"""
    if pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val.date()
    val_str = str(val).strip()
    if not val_str or val_str == 'NaN':
        return None
    # 尝试解析各种格式
    try:
        if '/' in val_str:
            # 处理 "2013/3/27深圳\n2024/7/1东莞" 这种格式
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
    # 清空现有数据
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute("DELETE FROM employees")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    print("已清空现有员工数据")

    # 获取工厂ID
    cursor.execute("SELECT id FROM factories WHERE name = '东莞厂'")
    factory = cursor.fetchone()
    factory_id = factory[0] if factory else 1

    # 获取部门ID映射
    cursor.execute("SELECT id, name FROM departments")
    dept_ids = {row[1]: row[0] for row in cursor.fetchall()}

    # 获取岗位ID映射
    cursor.execute("SELECT id, name FROM positions")
    position_ids = {row[1]: row[0] for row in cursor.fetchall()}

    # 统计
    imported = 0
    skipped = 0
    new_positions = set()
    new_depts = set()

    for idx, row in df.iterrows():
        # 跳过空行
        if pd.isna(row['姓名']) or str(row['姓名']).strip() == '':
            continue

        name = str(row['姓名']).strip()
        emp_no = str(row['工号']).strip() if not pd.isna(row['工号']) else f'DG{idx+1:04d}'

        # 部门处理
        dept_raw = str(row['部门']).strip() if not pd.isna(row['部门']) else ''
        department = dept_mapping.get(dept_raw, dept_raw)
        if department and department not in dept_ids:
            new_depts.add(department)

        # 岗位处理
        position = str(row['职位']).strip() if not pd.isna(row['职位']) else ''
        if position and position not in position_ids:
            new_positions.add(position)

        # 解析日期
        hire_date = parse_date(row['入厂时间'])
        birth_date = parse_date(row['出生年月'])

        # 其他字段
        gender = str(row['性别']).strip() if not pd.isna(row['性别']) else None
        education = str(row['学历']).strip() if not pd.isna(row['学历']) else None
        native_place = str(row['籍贯']).strip() if not pd.isna(row['籍贯']) else None
        phone = clean_phone(row['联系电话'])
        emergency_contact = str(row['紧急联系人姓名']).strip() if not pd.isna(row['紧急联系人姓名']) else None
        emergency_phone = clean_phone(row['紧急联络人电话'])
        id_address = str(row['身份证地址']).strip() if not pd.isna(row['身份证地址']) else None
        id_card = clean_id_card(row['身份证号码'])
        bank_card = clean_bank_card(row['银行卡'])
        salary_type = str(row['薪资制']).strip() if not pd.isna(row['薪资制']) else None
        accommodation = str(row['住宿情况']).strip() if not pd.isna(row['住宿情况']) else None

        print(f"  {emp_no}: {name} - {department} - {position}")

        cursor.execute("""
            INSERT INTO employees (
                empNo, name, gender, education, native_place,
                department, department_id, title, position_id,
                factory_id, hire_date, birth_date,
                phone, emergency_contact, emergency_phone,
                home_address, id_card, bank_card,
                salary_type, accommodation,
                employment_status, is_blacklisted, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                'Active', 0, NOW(), NOW()
            )
        """, (
            emp_no, name, gender, education, native_place,
            department, dept_ids.get(department), position, position_ids.get(position),
            factory_id, hire_date, birth_date,
            phone, emergency_contact, emergency_phone,
            id_address, id_card, bank_card,
            salary_type, accommodation
        ))
        imported += 1

    # 创建新发现的部门
    for idx, dept in enumerate(new_depts):
        if dept:
            cursor.execute("""
                INSERT IGNORE INTO departments (name, code, is_active, sort_order, created_at, updated_at)
                VALUES (%s, %s, 1, 99, NOW(), NOW())
            """, (dept, f'NEW_D{idx+1}'))
            print(f"创建新部门: {dept}")

    # 创建新发现的岗位
    for idx, pos in enumerate(new_positions):
        if pos:
            cursor.execute("""
                INSERT IGNORE INTO positions (name, code, is_active, sort_order, created_at, updated_at)
                VALUES (%s, %s, 1, 99, NOW(), NOW())
            """, (pos, f'NEW_P{idx+1}'))
            print(f"创建新岗位: {pos}")

    conn.commit()

    # 统计结果
    cursor.execute("SELECT COUNT(*) FROM employees WHERE employment_status = 'Active'")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM departments WHERE is_active = 1")
    dept_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM positions WHERE is_active = 1")
    pos_count = cursor.fetchone()[0]

    print(f"\n✅ 导入完成！")
    print(f"   在职员工: {total}名")
    print(f"   部门: {dept_count}个")
    print(f"   岗位: {pos_count}个")

except Exception as e:
    conn.rollback()
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
