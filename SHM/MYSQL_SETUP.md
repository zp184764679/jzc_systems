# SHM 系统 - MySQL 数据库配置指南

**重要**: SHM系统使用MySQL作为生产数据库。在部署前必须先创建MySQL数据库。

---

## 📋 前置要求

- MySQL Server 5.7+ 或 MySQL 8.0+
- 具有创建数据库权限的MySQL用户

---

## 🔧 数据库创建步骤

### 1. 登录MySQL

```bash
mysql -u root -p
```

### 2. 创建数据库

```sql
-- 创建SHM数据库（使用UTF-8编码）
CREATE DATABASE shm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 创建数据库用户

```sql
-- 创建应用用户
CREATE USER 'app'@'localhost' IDENTIFIED BY 'app';

-- 授予权限
GRANT ALL PRIVILEGES ON shm.* TO 'app'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 4. 验证数据库

```sql
-- 查看数据库
SHOW DATABASES;

-- 切换到shm数据库
USE shm;

-- 验证字符集
SHOW VARIABLES LIKE 'character%';
```

### 5. 退出MySQL

```sql
EXIT;
```

---

## ⚙️ 配置文件设置

数据库创建后，确保 `backend/.env` 配置正确：

```bash
# Database Configuration - MySQL (Production)
DB_HOST=localhost
MYSQL_USER=app
MYSQL_PASSWORD=app
MYSQL_DATABASE=shm
```

### 生产环境安全配置

**重要**: 生产环境请修改默认密码！

```sql
-- 修改用户密码
ALTER USER 'app'@'localhost' IDENTIFIED BY '强密码-请修改';
FLUSH PRIVILEGES;
```

然后更新 `.env` 文件：

```bash
MYSQL_PASSWORD=强密码-请修改
```

---

## 🚀 数据库初始化

部署脚本会自动创建表结构，但如果需要手动初始化：

### 方法一: 使用Flask-Migrate（推荐）

```bash
cd backend
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 初始化数据库
flask db upgrade
```

### 方法二: 使用Python脚本

```bash
cd backend
source venv/bin/activate

python -c "from app import app, db; \
with app.app_context(): \
    db.create_all(); \
    print('数据库表创建成功')"
```

---

## 🔍 验证配置

### 1. 测试数据库连接

```bash
cd backend
source venv/bin/activate

python -c "from app import app, db; \
with app.app_context(): \
    db.engine.connect(); \
    print('✅ MySQL连接成功')"
```

### 2. 查看表结构

```bash
mysql -u app -p shm

# 在MySQL中
SHOW TABLES;
DESCRIBE shipments;  # 查看出货单表结构
```

---

## 📊 数据库配置对比

| 配置项 | SQLite | MySQL (当前配置) |
|-------|--------|-----------------|
| 数据库类型 | 文件数据库 | 服务器数据库 |
| 连接字符串 | `sqlite:///shm.db` | `mysql+pymysql://app:app@localhost/shm` |
| 并发性能 | 低 | 高 |
| 适用场景 | 开发/测试 | 生产环境 |
| 数据完整性 | 一般 | 强 |

---

## 🛠️ 常见问题

### 问题1: 连接被拒绝

**错误**: `Can't connect to MySQL server on 'localhost'`

**解决**:
```bash
# 检查MySQL服务状态
# Windows
net start | findstr MySQL

# Linux
sudo systemctl status mysql

# 启动MySQL服务
# Windows
net start MySQL80

# Linux
sudo systemctl start mysql
```

### 问题2: 访问被拒绝

**错误**: `Access denied for user 'app'@'localhost'`

**解决**:
```sql
-- 重新设置用户权限
mysql -u root -p

GRANT ALL PRIVILEGES ON shm.* TO 'app'@'localhost';
FLUSH PRIVILEGES;
```

### 问题3: 字符集问题

**错误**: 中文显示乱码

**解决**:
```sql
-- 修改数据库字符集
ALTER DATABASE shm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修改表字符集（如果已创建表）
ALTER TABLE shipments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题4: 表不存在

**错误**: `Table 'shm.shipments' doesn't exist`

**解决**:
```bash
cd backend
source venv/bin/activate
flask db upgrade  # 运行数据库迁移
```

---

## 🔒 生产环境安全建议

1. **修改默认密码**
   ```sql
   ALTER USER 'app'@'localhost' IDENTIFIED BY '复杂密码';
   ```

2. **限制远程访问**
   ```sql
   -- 仅允许本地访问
   CREATE USER 'app'@'localhost' IDENTIFIED BY 'password';

   -- 或限制特定IP
   CREATE USER 'app'@'192.168.1.100' IDENTIFIED BY 'password';
   ```

3. **最小权限原则**
   ```sql
   -- 撤销不必要的权限
   REVOKE ALL PRIVILEGES ON *.* FROM 'app'@'localhost';

   -- 仅授予必要权限
   GRANT SELECT, INSERT, UPDATE, DELETE ON shm.* TO 'app'@'localhost';
   ```

4. **启用SSL连接**
   ```bash
   # .env 配置
   DATABASE_URL=mysql+pymysql://app:password@localhost/shm?ssl=true
   ```

5. **定期备份**
   ```bash
   # 备份数据库
   mysqldump -u app -p shm > shm_backup_$(date +%Y%m%d).sql

   # 恢复数据库
   mysql -u app -p shm < shm_backup_20251201.sql
   ```

---

## 📈 性能优化

### 1. 添加索引

```sql
USE shm;

-- 出货单常用查询索引
CREATE INDEX idx_shipment_status ON shipments(status);
CREATE INDEX idx_shipment_customer ON shipments(customer_name);
CREATE INDEX idx_shipment_date ON shipments(ship_date);
CREATE INDEX idx_shipment_created ON shipments(created_at);
```

### 2. 配置连接池

在 `config.py` 中已配置：

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,        # 连接池大小
    'pool_recycle': 3600,   # 连接回收时间（秒）
    'pool_pre_ping': True,  # 连接前检查
}
```

---

## 📞 支持信息

### 有用的命令

```bash
# 查看MySQL版本
mysql --version

# 查看数据库大小
mysql -u app -p -e "SELECT table_schema AS 'Database',
ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'shm';"

# 查看表大小
mysql -u app -p shm -e "SELECT table_name AS 'Table',
ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES
WHERE table_schema = 'shm'
ORDER BY (data_length + index_length) DESC;"
```

---

**配置完成后，继续执行部署脚本 `deploy.sh` 或 `deploy.bat`** 🚀
