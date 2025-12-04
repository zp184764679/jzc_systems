# HR System Backend - START HERE

## Welcome! 👋

This is a comprehensive Human Resources Management System backend built with Flask, SQLAlchemy, and MySQL.

## 🚀 Quick Start (5 Minutes)

### Step 1: Setup Database
Open MySQL and run:
```sql
CREATE DATABASE cncplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 2: Install
Double-click `install.bat` or run in terminal:
```bash
install.bat
```

### Step 3: Configure (Optional)
Edit `.env` if your MySQL password is not "root":
```env
MYSQL_PASSWORD=your_password_here
```

### Step 4: Run
Double-click `run.bat` or run in terminal:
```bash
run.bat
```

### Step 5: Test
Open browser: http://localhost:8003

Expected response:
```json
{
  "message": "HR System Backend API",
  "status": "running"
}
```

## ✅ You're Done! The system is running.

## 📚 What's Next?

### For First-Time Users
1. **[QUICKSTART.md](QUICKSTART.md)** - Complete quick start guide
2. **[API_EXAMPLES.md](API_EXAMPLES.md)** - Try some API calls
3. **[README.md](README.md)** - Full documentation

### For Developers
1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Understand the system design
2. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Feature overview
3. **Source code in `app/` directory**

### For DevOps
1. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
2. **[config.py](config.py)** - Configuration options
3. **[setup_database.sql](setup_database.sql)** - Database scripts

## 📖 Documentation Index

All documentation files are in the root directory:

| File | Purpose |
|------|---------|
| **START_HERE.md** | This file - Quick orientation |
| **QUICKSTART.md** | 5-minute setup guide |
| **README.md** | Complete documentation & API reference |
| **INDEX.md** | Complete documentation index |
| **API_EXAMPLES.md** | API usage examples (curl, JS, Python) |
| **ARCHITECTURE.md** | System architecture & design |
| **PROJECT_SUMMARY.md** | Project overview & features |
| **DEPLOYMENT.md** | Production deployment guide |
| **CHANGELOG.md** | Version history |

## 🎯 Common Tasks

### Create an Employee
```bash
curl -X POST http://localhost:8003/api/employees \
  -H "Content-Type: application/json" \
  -d "{\"empNo\":\"EMP001\",\"name\":\"John Doe\",\"department\":\"IT\"}"
```

### Get All Employees
```bash
curl http://localhost:8003/api/employees
```

### Search Employees
```bash
curl "http://localhost:8003/api/employees?search=John"
```

More examples in **[API_EXAMPLES.md](API_EXAMPLES.md)**

## 🏗️ Project Structure

```
backend/
├── 📁 app/                    # Application code
│   ├── __init__.py           # Flask app factory
│   ├── models/               # Database models
│   │   └── employee.py       # Employee model (26 fields)
│   └── routes/               # API endpoints
│       └── employees.py      # Employee CRUD API
│
├── 📁 tests/                  # Test suite
│   └── test_employees.py     # API tests
│
├── 📄 main.py                # Entry point
├── 📄 .env                   # Configuration
└── 📚 Documentation files    # All *.md files
```

## 🌟 Key Features

- **Comprehensive Employee Management**: 26 fields covering all aspects
- **RESTful API**: Complete CRUD operations
- **Advanced Search**: Full-text search and filtering
- **Pagination**: Handle large datasets efficiently
- **Statistics**: Employee analytics
- **Well-documented**: 8 documentation files
- **Production-ready**: Deployment guides and scripts
- **Tested**: Complete test suite

## 🔧 Technology Stack

- **Backend**: Python Flask 3.x
- **ORM**: SQLAlchemy 2.x with type hints
- **Database**: MySQL 5.7+
- **API**: RESTful JSON API
- **Port**: 8003

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/employees` | GET | List employees (paginated) |
| `/api/employees/{id}` | GET | Get single employee |
| `/api/employees` | POST | Create employee |
| `/api/employees/{id}` | PUT | Update employee |
| `/api/employees/{id}` | DELETE | Delete employee |
| `/api/employees/stats` | GET | Statistics |
| `/health` | GET | Health check |

Full API reference: **[README.md](README.md)**

## 🎓 Employee Model

26 fields organized into categories:

1. **Basic Info** (7): Name, gender, birth date, ID, contact
2. **Work Info** (6): Department, title, team, hire date, status
3. **Contract Info** (3): Type, start/end dates
4. **Salary Info** (3): Base, performance, total
5. **Contact Info** (3): Address, emergency contact
6. **Other** (4): Remarks, timestamps

See: **[ARCHITECTURE.md](ARCHITECTURE.md)** for full schema

## 🔒 Default Configuration

```env
DB_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=cncplan
PORT=8003
```

Change in `.env` file if needed.

## ❓ Troubleshooting

### Database connection failed
- Is MySQL running?
- Is password correct in `.env`?
- Does database `cncplan` exist?

### Port already in use
- Change PORT in `.env`
- Or kill process: `taskkill /F /PID <process_id>`

### Module not found
- Did you run `install.bat`?
- Activate environment: `venv\Scripts\activate`
- Reinstall: `pip install -r requirements.txt`

More help: **[QUICKSTART.md](QUICKSTART.md)** or **[DEPLOYMENT.md](DEPLOYMENT.md)**

## 📞 Need Help?

1. Check **[INDEX.md](INDEX.md)** - Find the right documentation
2. Check **[QUICKSTART.md](QUICKSTART.md)** - Common issues
3. Check **[DEPLOYMENT.md](DEPLOYMENT.md)** - Troubleshooting
4. Review error messages in terminal

## ✨ What Makes This Special?

Compared to typical PM (Project Management) systems:

- **More detailed**: 26 employee fields vs typical 10-15
- **Better organized**: Fields grouped into logical categories
- **More features**: Advanced search, statistics, filtering
- **Better documented**: 8+ documentation files
- **Production-ready**: Complete deployment guides
- **Well-tested**: Full test suite
- **Modern**: SQLAlchemy 2.x with type hints

## 🎯 Your Path Forward

### Path 1: I want to use the API
```
START_HERE.md → QUICKSTART.md → API_EXAMPLES.md → Start coding
```

### Path 2: I want to understand the code
```
START_HERE.md → ARCHITECTURE.md → PROJECT_SUMMARY.md → Read code
```

### Path 3: I want to deploy to production
```
START_HERE.md → README.md → DEPLOYMENT.md → Deploy
```

### Path 4: I want everything
```
START_HERE.md → INDEX.md → Read all docs → Master the system
```

## 📦 What's Included?

- ✅ Complete backend API
- ✅ Database models with 26 fields
- ✅ Full CRUD operations
- ✅ Search & filtering
- ✅ Pagination
- ✅ Statistics endpoint
- ✅ Health checks
- ✅ 8+ documentation files
- ✅ Installation scripts
- ✅ Test suite
- ✅ Deployment guides
- ✅ Database setup scripts
- ✅ Example API calls

## 🚀 Ready to Go?

The system is now running on http://localhost:8003

Try this in your browser:
- http://localhost:8003 - API status
- http://localhost:8003/health - Health check
- http://localhost:8003/api/employees - Employee list

Or try this in terminal:
```bash
curl http://localhost:8003/health
```

## 📝 Version

- **Version**: 1.0.0
- **Date**: November 15, 2025
- **Status**: Production Ready ✅

## 🎉 Congratulations!

You now have a fully functional HR system backend running locally.

**Next Step**: Read **[QUICKSTART.md](QUICKSTART.md)** to learn how to use it.

---

**Happy Coding! 🚀**

For detailed documentation, see **[INDEX.md](INDEX.md)**
