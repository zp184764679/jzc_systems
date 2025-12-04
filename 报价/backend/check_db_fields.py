"""检查数据库字段"""
import sqlite3

conn = sqlite3.connect('quote_system.db')
cursor = conn.cursor()

# 检查表结构
cursor.execute('PRAGMA table_info(processes)')
columns = cursor.fetchall()
print("processes表字段:")
for col in columns:
    print(f"  {col[1]}: {col[2]}")

# 检查数据
cursor.execute('SELECT process_code, daily_fee, icon FROM processes LIMIT 3')
print("\n前3条记录:")
print("Code | Daily Fee | Icon")
print("-" * 50)
for row in cursor.fetchall():
    print(f"{row[0]:20} | {row[1]} | {row[2]}")

conn.close()
