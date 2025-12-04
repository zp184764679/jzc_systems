"""
导入东莞厂人事资料到HR数据库
- 工厂/地点：东莞厂
- 部门：办公室、生管、走芯机、数控、全检组、磨床、铣床、加工中心
"""
import pandas as pd
import pymysql
from datetime import datetime

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
df = pd.read_excel(excel_file, sheet_name='东莞精之成各组人员名单', header=None)

# 部门列位置映射（根据Excel结构）
departments_config = [
    {'name': '走芯机', 'start_col': 0},
    {'name': '数控', 'start_col': 4},
    {'name': '全检组', 'start_col': 8},
    {'name': '磨床', 'start_col': 15},
    {'name': '铣床', 'start_col': 19},
    {'name': '生管', 'start_col': 23},
    {'name': '办公室', 'start_col': 27},
    {'name': '加工中心', 'start_col': 31},
]

# 提取员工数据
employees = []
positions_set = set()

for dept in departments_config:
    dept_name = dept['name']
    start_col = dept['start_col']

    # 从第3行开始读取数据（第0行部门名，第1行空，第2行表头）
    for row_idx in range(3, 25):
        try:
            seq = df.iloc[row_idx, start_col]
            name = df.iloc[row_idx, start_col + 1]
            position = df.iloc[row_idx, start_col + 2]

            # 跳过空行和表头
            if pd.isna(name) or str(name).strip() == '' or str(name).strip() == '姓名':
                continue

            name = str(name).strip()
            position = str(position).strip() if not pd.isna(position) else ''

            # 跳过"岗位"这个表头
            if position == '岗位' or not position:
                continue

            employees.append({
                'name': name,
                'position': position,
                'department': dept_name,
                'factory': '东莞厂'
            })
            positions_set.add(position)
            print(f"  {dept_name}: {name} - {position}")
        except Exception as e:
            continue

print(f"\n总共提取 {len(employees)} 名员工")
print(f"岗位类型: {sorted(positions_set)}")

# 连接数据库并导入
conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

try:
    # 1. 创建工厂（地点）
    cursor.execute("SELECT id FROM factories WHERE name = '东莞厂'")
    factory = cursor.fetchone()
    if not factory:
        cursor.execute("""
            INSERT INTO factories (name, code, is_active, sort_order, created_at, updated_at)
            VALUES ('东莞厂', 'DG', 1, 1, NOW(), NOW())
        """)
        factory_id = cursor.lastrowid
        print(f"\n创建工厂: 东莞厂 (ID: {factory_id})")
    else:
        factory_id = factory[0]

    # 也创建深圳厂（预留）
    cursor.execute("SELECT id FROM factories WHERE name = '深圳厂'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO factories (name, code, is_active, sort_order, created_at, updated_at)
            VALUES ('深圳厂', 'SZ', 1, 2, NOW(), NOW())
        """)
        print(f"创建工厂: 深圳厂")

    # 2. 创建部门
    dept_ids = {}
    for idx, dept in enumerate(departments_config):
        dept_name = dept['name']
        cursor.execute("SELECT id FROM departments WHERE name = %s", (dept_name,))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute("""
                INSERT INTO departments (name, code, is_active, sort_order, created_at, updated_at)
                VALUES (%s, %s, 1, %s, NOW(), NOW())
            """, (dept_name, f'D{idx+1}', idx+1))
            dept_ids[dept_name] = cursor.lastrowid
            print(f"创建部门: {dept_name} (ID: {dept_ids[dept_name]})")
        else:
            dept_ids[dept_name] = existing[0]

    # 3. 创建岗位
    position_ids = {}
    for idx, pos_name in enumerate(sorted(positions_set)):
        cursor.execute("SELECT id FROM positions WHERE name = %s", (pos_name,))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute("""
                INSERT INTO positions (name, code, is_active, sort_order, created_at, updated_at)
                VALUES (%s, %s, 1, %s, NOW(), NOW())
            """, (pos_name, f'P{idx+1}', idx+1))
            position_ids[pos_name] = cursor.lastrowid
            print(f"创建岗位: {pos_name}")
        else:
            position_ids[pos_name] = existing[0]

    # 4. 导入员工
    imported_count = 0
    for idx, emp in enumerate(employees):
        emp_no = f'DG{str(idx+1).zfill(4)}'

        # 检查是否已存在
        cursor.execute("SELECT id FROM employees WHERE name = %s AND department = %s",
                      (emp['name'], emp['department']))
        if cursor.fetchone():
            continue

        dept_id = dept_ids.get(emp['department'])
        position_id = position_ids.get(emp['position'])

        cursor.execute("""
            INSERT INTO employees (
                empNo, name, department, department_id, title, position_id,
                factory_id, employment_status, is_blacklisted, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, 'Active', 0, NOW(), NOW()
            )
        """, (emp_no, emp['name'], emp['department'], dept_id, emp['position'],
              position_id, factory_id))
        imported_count += 1

    conn.commit()
    print(f"\n✅ 导入完成！")
    print(f"   工厂: 2个（东莞厂、深圳厂）")

    cursor.execute("SELECT COUNT(*) FROM departments WHERE is_active = 1")
    print(f"   部门: {cursor.fetchone()[0]}个")

    cursor.execute("SELECT COUNT(*) FROM positions WHERE is_active = 1")
    print(f"   岗位: {cursor.fetchone()[0]}个")

    cursor.execute("SELECT COUNT(*) FROM employees WHERE employment_status = 'Active'")
    print(f"   员工: {cursor.fetchone()[0]}名")

except Exception as e:
    conn.rollback()
    print(f"❌ 导入失败: {e}")
    raise
finally:
    cursor.close()
    conn.close()
