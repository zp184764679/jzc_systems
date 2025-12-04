# HR System Backend - Deployment Guide

## Quick Start (Development)

### Prerequisites
- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

### Installation Steps

1. **Navigate to project directory**
   ```bash
   cd C:\Users\Admin\Desktop\HR\backend
   ```

2. **Run installation script**
   ```bash
   install.bat
   ```
   This will:
   - Create virtual environment
   - Install all dependencies
   - Set up the environment

3. **Configure database**
   - Open MySQL and create database:
     ```sql
     CREATE DATABASE cncplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     ```
   - Or run the SQL script:
     ```bash
     mysql -u root -p < setup_database.sql
     ```

4. **Update environment variables**
   - Edit `.env` file with your credentials
   - Default values are already set for local development

5. **Start the server**
   ```bash
   run.bat
   ```
   Or manually:
   ```bash
   venv\Scripts\activate
   python main.py
   ```

6. **Verify installation**
   - Open browser: http://localhost:8003
   - Check health: http://localhost:8003/health

## Manual Installation

### Step 1: Create Virtual Environment

```bash
python -m venv venv
```

### Step 2: Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

Create `.env` file:
```env
DB_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=cncplan
PORT=8003
```

### Step 5: Setup Database

```sql
CREATE DATABASE cncplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 6: Run Application

```bash
python main.py
```

## Production Deployment

### Option 1: Using Gunicorn (Recommended)

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Create Gunicorn configuration** (`gunicorn_config.py`)
   ```python
   bind = "0.0.0.0:8003"
   workers = 4
   worker_class = "sync"
   worker_connections = 1000
   timeout = 30
   keepalive = 2

   # Logging
   accesslog = "logs/access.log"
   errorlog = "logs/error.log"
   loglevel = "info"

   # Process naming
   proc_name = "hr-system-backend"

   # Server mechanics
   daemon = False
   pidfile = "hr-system.pid"
   ```

3. **Create logs directory**
   ```bash
   mkdir logs
   ```

4. **Run with Gunicorn**
   ```bash
   gunicorn -c gunicorn_config.py main:app
   ```

### Option 2: Using uWSGI

1. **Install uWSGI**
   ```bash
   pip install uwsgi
   ```

2. **Create uWSGI configuration** (`uwsgi.ini`)
   ```ini
   [uwsgi]
   module = main:app
   master = true
   processes = 4
   threads = 2
   socket = 0.0.0.0:8003
   protocol = http
   vacuum = true
   die-on-term = true
   ```

3. **Run with uWSGI**
   ```bash
   uwsgi --ini uwsgi.ini
   ```

### Option 3: Windows Service

1. **Install NSSM (Non-Sucking Service Manager)**
   - Download from: https://nssm.cc/download

2. **Install as service**
   ```bash
   nssm install HRSystemBackend "C:\Users\Admin\Desktop\HR\backend\venv\Scripts\python.exe" "C:\Users\Admin\Desktop\HR\backend\main.py"
   ```

3. **Start service**
   ```bash
   nssm start HRSystemBackend
   ```

## Nginx Configuration (Reverse Proxy)

Create nginx configuration file:

```nginx
server {
    listen 80;
    server_name hr-system.example.com;

    location / {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Optional: Increase timeout for long requests
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;
}
```

## Environment-Specific Configuration

### Development
```env
FLASK_ENV=development
DEBUG=True
DB_HOST=localhost
PORT=8003
```

### Production
```env
FLASK_ENV=production
DEBUG=False
DB_HOST=production-db-server
PORT=8003
SECRET_KEY=your-secret-key-here
```

## Database Migration

### Using Flask-Migrate

1. **Initialize migrations**
   ```bash
   flask db init
   ```

2. **Create migration**
   ```bash
   flask db migrate -m "Initial migration"
   ```

3. **Apply migration**
   ```bash
   flask db upgrade
   ```

4. **Rollback migration**
   ```bash
   flask db downgrade
   ```

## Performance Optimization

### 1. Database Connection Pool
Already configured in `app/__init__.py`:
```python
'pool_size': 10,
'max_overflow': 20,
'pool_pre_ping': True,
'pool_recycle': 3600
```

### 2. Caching (Optional)
Install Redis and Flask-Caching:
```bash
pip install flask-caching redis
```

### 3. Gzip Compression
Install Flask-Compress:
```bash
pip install flask-compress
```

## Monitoring and Logging

### Application Logging

Add to `app/__init__.py`:
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/hr-system.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('HR System startup')
```

### Database Query Logging

In `.env`:
```env
SQLALCHEMY_ECHO=True  # Development only
```

## Security Best Practices

### 1. Environment Variables
- Never commit `.env` file to version control
- Use strong passwords
- Rotate secrets regularly

### 2. Database Security
- Use least privilege principle
- Enable SSL for database connections
- Regular backups

### 3. API Security
- Implement rate limiting
- Add authentication/authorization
- Use HTTPS in production

### 4. Input Validation
Already implemented in routes:
- Required field validation
- Unique constraint validation
- Date parsing with error handling

## Backup Strategy

### Database Backup

**Daily backup script** (`backup_db.bat`):
```batch
@echo off
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
mysqldump -u root -p cncplan > backups\cncplan_%TIMESTAMP%.sql
echo Backup completed: cncplan_%TIMESTAMP%.sql
```

### Automated Backups (Windows Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 2 AM)
4. Action: Start a program
5. Program: `C:\Users\Admin\Desktop\HR\backend\backup_db.bat`

## Troubleshooting

### Issue: Port already in use
```bash
# Find process using port 8003
netstat -ano | findstr :8003

# Kill process
taskkill /PID <process_id> /F
```

### Issue: Database connection failed
- Check MySQL is running
- Verify credentials in `.env`
- Check firewall settings
- Test connection: `mysql -u root -p`

### Issue: Module not found
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Permission denied
- Run as administrator
- Check file permissions
- Check antivirus settings

## Health Checks

### Manual Health Check
```bash
curl http://localhost:8003/health
```

### Automated Monitoring
Use tools like:
- Prometheus + Grafana
- Datadog
- New Relic
- Uptime Robot

## Scaling Strategies

### Horizontal Scaling
- Deploy multiple instances
- Use load balancer (Nginx, HAProxy)
- Share session data (Redis)

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Add database indexes

### Database Scaling
- Read replicas
- Connection pooling
- Query optimization
- Partitioning

## Update Procedure

1. **Backup database**
   ```bash
   mysqldump -u root -p cncplan > backup.sql
   ```

2. **Pull latest code**
   ```bash
   git pull origin main
   ```

3. **Update dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

4. **Run migrations**
   ```bash
   flask db upgrade
   ```

5. **Restart service**
   ```bash
   nssm restart HRSystemBackend
   # or
   systemctl restart hr-system
   ```

## Performance Benchmarking

### Using Apache Bench
```bash
ab -n 1000 -c 10 http://localhost:8003/api/employees
```

### Using wrk
```bash
wrk -t12 -c400 -d30s http://localhost:8003/api/employees
```

## Checklist for Production

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Implement rate limiting
- [ ] Add authentication
- [ ] Review CORS settings
- [ ] Configure firewall
- [ ] Set up error tracking (Sentry)
- [ ] Document API endpoints
- [ ] Create runbooks
- [ ] Set up CI/CD pipeline

## Support and Maintenance

### Regular Maintenance Tasks
- Weekly database backups verification
- Monthly dependency updates
- Quarterly security audits
- Regular log review
- Performance monitoring

### Useful Commands
```bash
# Check Python version
python --version

# Check pip packages
pip list

# Check database connection
mysql -u root -p -e "SELECT 1"

# Check application logs
tail -f logs/hr-system.log

# Check system resources
top  # Linux
tasklist  # Windows
```

## Additional Resources

- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- MySQL Documentation: https://dev.mysql.com/doc/
- Python Best Practices: https://docs.python-guide.org/

## License and Support

For technical support, contact the development team.
