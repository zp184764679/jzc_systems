# HR System Backend - Documentation Index

Welcome to the HR System Backend documentation. This index will help you find the information you need quickly.

## Quick Navigation

### Getting Started
1. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
   - Installation steps
   - First API call
   - Common issues
   - Next steps

2. **[README.md](README.md)** - Complete documentation
   - Project overview
   - Installation guide
   - API reference
   - Configuration

### Development
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
   - System design
   - Data flow diagrams
   - Component interaction
   - Database schema

4. **[API_EXAMPLES.md](API_EXAMPLES.md)** - API usage examples
   - curl examples
   - JavaScript/Axios examples
   - Python examples
   - Postman collection

5. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project overview
   - Key features
   - Technology stack
   - Directory structure
   - Comparison with PM system

### Deployment & Operations
6. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide
   - Production deployment
   - Performance optimization
   - Monitoring & logging
   - Troubleshooting

7. **[CHANGELOG.md](CHANGELOG.md)** - Version history
   - Release notes
   - New features
   - Breaking changes
   - Future enhancements

### Database
8. **[setup_database.sql](setup_database.sql)** - Database setup
   - Database creation
   - Sample data
   - Useful queries
   - Management scripts

## Documentation by Role

### For Developers
Start here:
1. [QUICKSTART.md](QUICKSTART.md) - Get running in 5 minutes
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system
3. [API_EXAMPLES.md](API_EXAMPLES.md) - Learn the API
4. [README.md](README.md) - Reference documentation

### For DevOps/SysAdmins
Start here:
1. [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
2. [README.md](README.md) - Configuration
3. [setup_database.sql](setup_database.sql) - Database setup

### For Product Managers
Start here:
1. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Feature overview
2. [CHANGELOG.md](CHANGELOG.md) - Current status & roadmap
3. [API_EXAMPLES.md](API_EXAMPLES.md) - What it can do

### For QA/Testers
Start here:
1. [API_EXAMPLES.md](API_EXAMPLES.md) - Test scenarios
2. [README.md](README.md) - API endpoints
3. [tests/test_employees.py](tests/test_employees.py) - Test cases

## Documentation by Task

### I want to...

#### Install and Run
→ [QUICKSTART.md](QUICKSTART.md) - Quick installation
→ [install.bat](install.bat) - Installation script
→ [run.bat](run.bat) - Run script

#### Learn the API
→ [README.md](README.md) - API reference
→ [API_EXAMPLES.md](API_EXAMPLES.md) - Code examples
→ [tests/test_employees.py](tests/test_employees.py) - Test examples

#### Deploy to Production
→ [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
→ [config.py](config.py) - Configuration options
→ [.env](.env) - Environment variables

#### Understand the Code
→ [ARCHITECTURE.md](ARCHITECTURE.md) - System design
→ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Overview
→ [app/](app/) - Source code

#### Setup Database
→ [setup_database.sql](setup_database.sql) - SQL script
→ [README.md](README.md) - Database configuration
→ [DEPLOYMENT.md](DEPLOYMENT.md) - Database migration

#### Write Tests
→ [tests/test_employees.py](tests/test_employees.py) - Test examples
→ [tests/conftest.py](tests/conftest.py) - Test configuration
→ [requirements-dev.txt](requirements-dev.txt) - Test dependencies

#### Troubleshoot Issues
→ [QUICKSTART.md](QUICKSTART.md) - Common issues
→ [DEPLOYMENT.md](DEPLOYMENT.md) - Troubleshooting
→ [README.md](README.md) - Configuration

#### Extend the System
→ [ARCHITECTURE.md](ARCHITECTURE.md) - System design
→ [app/models/employee.py](app/models/employee.py) - Model example
→ [app/routes/employees.py](app/routes/employees.py) - Route example

## File Structure

```
Documentation Files (8)
├── INDEX.md                    # This file - Documentation index
├── QUICKSTART.md              # 5-minute quick start
├── README.md                  # Complete documentation
├── ARCHITECTURE.md            # System architecture
├── API_EXAMPLES.md            # API usage examples
├── PROJECT_SUMMARY.md         # Project overview
├── DEPLOYMENT.md              # Deployment guide
└── CHANGELOG.md               # Version history

Source Code Files (7)
├── main.py                    # Entry point
├── config.py                  # Configuration
├── app/__init__.py           # Flask app factory
├── app/models/__init__.py    # Models package
├── app/models/employee.py    # Employee model
├── app/routes/__init__.py    # Routes package
└── app/routes/employees.py   # Employee routes

Test Files (3)
├── tests/__init__.py         # Tests package
├── tests/conftest.py         # Pytest config
└── tests/test_employees.py   # Employee tests

Configuration Files (5)
├── .env                      # Environment variables
├── .gitignore               # Git ignore
├── requirements.txt         # Production deps
└── requirements-dev.txt     # Development deps

Database Files (1)
└── setup_database.sql       # Database setup

Utility Scripts (2)
├── install.bat             # Installation script
└── run.bat                 # Run script
```

## Key Concepts

### Employee Model
The core data model with 26 fields organized into:
- Basic Information (7 fields)
- Work Information (6 fields)
- Contract Information (3 fields)
- Salary Information (3 fields)
- Contact Information (3 fields)
- Other Information (4 fields)

See: [ARCHITECTURE.md](ARCHITECTURE.md) - Database Schema

### API Endpoints
8 main endpoints for complete CRUD operations:
- List employees (GET)
- Get single employee (GET)
- Create employee (POST)
- Update employee (PUT)
- Delete employee (DELETE)
- Legacy list (POST)
- Statistics (GET)
- Health check (GET)

See: [README.md](README.md) - API Endpoints

### Search & Filter
Advanced querying with:
- Full-text search
- Department filter
- Status filter
- Pagination
- Sorting

See: [API_EXAMPLES.md](API_EXAMPLES.md) - Search Examples

## Common Workflows

### 1. First-Time Setup
```
1. Read QUICKSTART.md
2. Run install.bat
3. Create database
4. Edit .env (if needed)
5. Run run.bat
6. Test with curl
```

### 2. Development Workflow
```
1. Read ARCHITECTURE.md
2. Make code changes
3. Test locally
4. Write tests
5. Update documentation
```

### 3. Deployment Workflow
```
1. Read DEPLOYMENT.md
2. Setup production environment
3. Configure .env for production
4. Run migrations
5. Deploy application
6. Monitor health
```

### 4. Testing Workflow
```
1. Read API_EXAMPLES.md
2. Install dev dependencies
3. Write tests
4. Run pytest
5. Check coverage
```

## API Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/employees` | GET | List all employees |
| `/api/employees/{id}` | GET | Get one employee |
| `/api/employees` | POST | Create employee |
| `/api/employees/{id}` | PUT | Update employee |
| `/api/employees/{id}` | DELETE | Delete employee |
| `/api/employees/list` | POST | Legacy list |
| `/api/employees/stats` | GET | Statistics |
| `/health` | GET | Health check |
| `/` | GET | API status |

Full reference: [README.md](README.md)

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Flask 3.x |
| ORM | SQLAlchemy 2.x |
| Database | MySQL 5.7+ |
| Driver | PyMySQL |
| Migration | Flask-Migrate |
| CORS | Flask-CORS |
| Testing | Pytest |

Details: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DB_HOST | localhost | Database host |
| MYSQL_USER | root | Database user |
| MYSQL_PASSWORD | root | Database password |
| MYSQL_DATABASE | cncplan | Database name |
| PORT | 8003 | Server port |
| FLASK_ENV | development | Environment |

Configuration: [.env](.env), [config.py](config.py)

## Dependencies

### Production
- Flask
- Flask-CORS
- Flask-SQLAlchemy
- Flask-Migrate
- PyMySQL
- python-dotenv
- cryptography
- SQLAlchemy>=2.0.36

See: [requirements.txt](requirements.txt)

### Development
All production dependencies plus:
- pytest
- pytest-cov
- pytest-flask
- flake8
- black
- mypy

See: [requirements-dev.txt](requirements-dev.txt)

## Support Resources

### Internal Documentation
- All documentation files are in this directory
- Code comments in source files
- Test cases as examples

### External Resources
- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- MySQL: https://dev.mysql.com/doc/
- Python: https://docs.python.org/

### Troubleshooting
1. Check [QUICKSTART.md](QUICKSTART.md) - Common Issues
2. Check [DEPLOYMENT.md](DEPLOYMENT.md) - Troubleshooting
3. Review error messages in terminal
4. Check database connection
5. Verify environment variables

## Version Information

- **Current Version**: 1.0.0
- **Release Date**: November 15, 2025
- **Status**: Production Ready

See: [CHANGELOG.md](CHANGELOG.md)

## Next Steps

### Just Starting?
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Install and run the system
3. Try the API examples
4. Explore the code

### Ready to Develop?
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Understand the code structure
3. Set up development environment
4. Write your first feature

### Ready to Deploy?
1. Read [DEPLOYMENT.md](DEPLOYMENT.md)
2. Prepare production environment
3. Configure security
4. Deploy and monitor

---

**Need help?** Start with [QUICKSTART.md](QUICKSTART.md) or search this index for your topic.

**Found an issue?** Check [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section.

**Want to contribute?** Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system.
