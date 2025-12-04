import pandas as pd
import pymysql

# 读取Excel
df = pd.read_excel(r'C:\Users\Admin\Desktop\HR\东莞厂人事资料-新2025.10.24xls.xls', sheet_name='总人数', header=2)

# 获取Excel中的所有员工
excel_employees = []
for idx, row in df.iterrows():
    name = row['姓名']
    emp_no = row['工号']
    if pd.notna(name) and str(name).strip():
        excel_employees.append({
            'name': str(name).strip(),
            'emp_no': str(emp_no).strip() if pd.notna(emp_no) else None
        })

print(f"Excel中在职员工数: {len(excel_employees)}")

# 从数据库获取在职员工
conn = pymysql.connect(host='localhost', user='app', password='app', database='hr_system', charset='utf8mb4')
cursor = conn.cursor()
cursor.execute("SELECT empNo, name FROM employees WHERE employment_status = 'Active'")
db_employees = {row[0]: row[1] for row in cursor.fetchall()}
cursor.close()
conn.close()

print(f"数据库中在职员工数: {len(db_employees)}")

# 比较
excel_emp_nos = set(e['emp_no'] for e in excel_employees if e['emp_no'])
db_emp_nos = set(db_employees.keys())

missing_in_db = excel_emp_nos - db_emp_nos
extra_in_db = db_emp_nos - excel_emp_nos

if missing_in_db:
    print(f"\nExcel中有但数据库中没有的员工:")
    for emp_no in missing_in_db:
        emp = next((e for e in excel_employees if e['emp_no'] == emp_no), None)
        print(f"  工号: {emp_no}, 姓名: {emp['name'] if emp else '未知'}")

if extra_in_db:
    print(f"\n数据库中有但Excel中没有的员工:")
    for emp_no in extra_in_db:
        print(f"  工号: {emp_no}, 姓名: {db_employees[emp_no]}")

# 显示Excel中所有员工
print(f"\nExcel中所有在职员工列表:")
for i, emp in enumerate(excel_employees, 1):
    in_db = "✓" if emp['emp_no'] in db_emp_nos else "✗"
    print(f"  {i}. {in_db} {emp['emp_no']}: {emp['name']}")
