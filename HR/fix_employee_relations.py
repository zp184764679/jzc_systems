"""
修复员工的部门ID和职位ID关联
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'app',
    'password': 'app',
    'database': 'hr_system',
    'charset': 'utf8mb4'
}

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

try:
    # 获取部门映射
    cursor.execute("SELECT id, name FROM departments")
    dept_map = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"部门数: {len(dept_map)}")

    # 获取职位映射
    cursor.execute("SELECT id, name FROM positions")
    pos_map = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"职位数: {len(pos_map)}")

    # 获取工厂映射
    cursor.execute("SELECT id, name FROM factories")
    factory_map = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"工厂数: {len(factory_map)}")

    # 更新员工的department_id
    cursor.execute("SELECT id, department FROM employees WHERE department IS NOT NULL AND department != ''")
    employees_dept = cursor.fetchall()
    dept_updated = 0
    for emp_id, dept_name in employees_dept:
        if dept_name in dept_map:
            cursor.execute("UPDATE employees SET department_id = %s WHERE id = %s", (dept_map[dept_name], emp_id))
            dept_updated += 1
    print(f"更新department_id: {dept_updated}条")

    # 更新员工的position_id
    cursor.execute("SELECT id, title FROM employees WHERE title IS NOT NULL AND title != ''")
    employees_pos = cursor.fetchall()
    pos_updated = 0
    pos_not_found = set()
    for emp_id, title in employees_pos:
        if title in pos_map:
            cursor.execute("UPDATE employees SET position_id = %s WHERE id = %s", (pos_map[title], emp_id))
            pos_updated += 1
        else:
            pos_not_found.add(title)
    print(f"更新position_id: {pos_updated}条")

    if pos_not_found:
        print(f"\n以下职位名在positions表中不存在，需要添加:")
        # 添加缺失的职位
        for idx, pos_name in enumerate(sorted(pos_not_found)):
            code = f'AUTO_{idx+1:03d}'
            cursor.execute("""
                INSERT IGNORE INTO positions (code, name, is_active, sort_order, created_at, updated_at)
                VALUES (%s, %s, 1, 99, NOW(), NOW())
            """, (code, pos_name))
            print(f"  添加职位: {pos_name}")

        # 重新获取职位映射
        cursor.execute("SELECT id, name FROM positions")
        pos_map = {row[1]: row[0] for row in cursor.fetchall()}

        # 再次更新position_id
        for emp_id, title in employees_pos:
            if title in pos_map:
                cursor.execute("UPDATE employees SET position_id = %s WHERE id = %s", (pos_map[title], emp_id))

    # 设置所有东莞厂员工的factory_id
    dg_factory_id = factory_map.get('东莞厂', 1)
    cursor.execute("UPDATE employees SET factory_id = %s WHERE factory_id IS NULL", (dg_factory_id,))
    print(f"设置factory_id为东莞厂: {cursor.rowcount}条")

    conn.commit()

    # 统计结果
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN department_id IS NOT NULL THEN 1 ELSE 0 END) as with_dept_id,
            SUM(CASE WHEN position_id IS NOT NULL THEN 1 ELSE 0 END) as with_pos_id,
            SUM(CASE WHEN factory_id IS NOT NULL THEN 1 ELSE 0 END) as with_factory_id
        FROM employees WHERE employment_status = 'Active'
    """)
    result = cursor.fetchone()
    print(f"\n在职员工统计:")
    print(f"  总数: {result[0]}")
    print(f"  有department_id: {result[1]}")
    print(f"  有position_id: {result[2]}")
    print(f"  有factory_id: {result[3]}")

except Exception as e:
    conn.rollback()
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
