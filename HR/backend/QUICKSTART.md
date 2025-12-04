# HR System Backend - Quick Start Guide

## 5-Minute Setup

### Prerequisites Check
- [ ] Python 3.8+ installed
- [ ] MySQL 5.7+ installed and running
- [ ] Git installed (optional)

### Step 1: Database Setup (1 minute)
Open MySQL and run:
```sql
CREATE DATABASE cncplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 2: Install Dependencies (2 minutes)
Double-click or run:
```bash
install.bat
```

This will:
- Create virtual environment
- Install all dependencies
- Set up the environment

### Step 3: Configure (30 seconds)
The `.env` file is already configured with default values:
```env
DB_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=cncplan
PORT=8003
```

**IMPORTANT**: If your MySQL password is different, edit `.env` and change `MYSQL_PASSWORD`.

### Step 4: Start Server (30 seconds)
Double-click or run:
```bash
run.bat
```

### Step 5: Test (1 minute)
Open browser and visit:
- http://localhost:8003 - Should show API status
- http://localhost:8003/health - Should show healthy status

Or use curl:
```bash
curl http://localhost:8003/health
```

## First API Call

### Create Your First Employee
```bash
curl -X POST http://localhost:8003/api/employees \
  -H "Content-Type: application/json" \
  -d "{\"empNo\":\"EMP001\",\"name\":\"John Doe\",\"department\":\"IT\",\"title\":\"Software Engineer\",\"employment_status\":\"Active\"}"
```

### Get All Employees
```bash
curl http://localhost:8003/api/employees
```

### Success Response
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "empNo": "EMP001",
      "name": "John Doe",
      "department": "IT",
      "title": "Software Engineer",
      ...
    }
  ],
  "pagination": {
    "total": 1,
    "page": 1,
    "per_page": 10,
    "pages": 1
  }
}
```

## Common Issues

### Issue: "MySQL connection refused"
**Solution**:
1. Check if MySQL is running
2. Verify credentials in `.env` file
3. Make sure database `cncplan` exists

### Issue: "Port 8003 already in use"
**Solution**:
1. Change PORT in `.env` to another port (e.g., 8004)
2. Or kill the process using port 8003:
   ```bash
   netstat -ano | findstr :8003
   taskkill /PID <process_id> /F
   ```

### Issue: "Module not found"
**Solution**:
1. Activate virtual environment: `venv\Scripts\activate`
2. Reinstall: `pip install -r requirements.txt`

## Next Steps

1. **Explore API**: Read `API_EXAMPLES.md` for more examples
2. **Review Documentation**: Check `README.md` for detailed API docs
3. **Deploy**: See `DEPLOYMENT.md` for production deployment
4. **Test**: Run tests with `pytest tests/`

## Project Structure

```
backend/
├── app/                    # Application code
│   ├── models/            # Database models
│   │   └── employee.py    # Employee model
│   └── routes/            # API routes
│       └── employees.py   # Employee endpoints
├── tests/                 # Test files
├── .env                   # Configuration (edit this!)
├── main.py               # Entry point (run this!)
├── requirements.txt      # Dependencies
└── README.md            # Full documentation
```

## Useful Commands

### Start Server
```bash
run.bat
# or
venv\Scripts\activate
python main.py
```

### Stop Server
- Press `Ctrl+C` in terminal

### View Logs
- Logs appear in the terminal where you ran `run.bat`

### Backup Database
```bash
mysqldump -u root -p cncplan > backup.sql
```

### Restore Database
```bash
mysql -u root -p cncplan < backup.sql
```

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/employees` | List all employees |
| GET | `/api/employees/{id}` | Get single employee |
| POST | `/api/employees` | Create employee |
| PUT | `/api/employees/{id}` | Update employee |
| DELETE | `/api/employees/{id}` | Delete employee |
| GET | `/api/employees/stats` | Get statistics |
| GET | `/health` | Health check |

## Testing with Postman

1. Download Postman: https://www.postman.com/downloads/
2. Create new request
3. Set URL: `http://localhost:8003/api/employees`
4. Set method: GET
5. Click Send

## Need Help?

- Read `README.md` for detailed documentation
- Check `API_EXAMPLES.md` for code examples
- See `DEPLOYMENT.md` for deployment help
- Review `PROJECT_SUMMARY.md` for project overview

## Development Workflow

1. **Make changes** to code
2. **Save files**
3. **Flask auto-reloads** (in debug mode)
4. **Test changes** via API calls

## Production Checklist

Before going to production:
- [ ] Change `MYSQL_PASSWORD` in `.env`
- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Set `DEBUG=False` in code
- [ ] Use Gunicorn or uWSGI
- [ ] Set up database backups
- [ ] Configure firewall
- [ ] Enable HTTPS

## Support

For issues or questions:
1. Check documentation files
2. Review error messages in terminal
3. Check database connection
4. Verify environment configuration

---

**You're all set! Happy coding! 🚀**
