import sqlite3

conn = sqlite3.connect('C:/home/admin/shared/auth/users.db')
cursor = conn.cursor()
result = cursor.execute('SELECT id, username, full_name, role, is_admin, permissions FROM users WHERE username=?', ('jzchardware',)).fetchall()
print(result)
conn.close()
