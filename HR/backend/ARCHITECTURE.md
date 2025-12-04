# HR System Backend - Architecture Documentation

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                   (React/Vue/Angular)                        │
│                   http://localhost:6000                      │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
                     │ (CORS enabled)
┌────────────────────▼────────────────────────────────────────┐
│                    Flask Backend                             │
│                  http://localhost:8003                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Routes Layer                         │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  /api/employees (GET, POST)                  │   │  │
│  │  │  /api/employees/<id> (GET, PUT, DELETE)      │   │  │
│  │  │  /api/employees/list (POST)                  │   │  │
│  │  │  /api/employees/stats (GET)                  │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │           Business Logic Layer                        │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  - Input Validation                            │ │  │
│  │  │  - Data Processing                             │ │  │
│  │  │  - Error Handling                              │ │  │
│  │  │  - Search & Filter Logic                       │ │  │
│  │  │  - Pagination Logic                            │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │              ORM Layer (SQLAlchemy)                   │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  - Model Definitions                           │ │  │
│  │  │  - Query Building                              │ │  │
│  │  │  - Relationship Management                     │ │  │
│  │  │  - Connection Pooling                          │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────┬───────────────────────────────────┘  │
└────────────────────┬┘                                       │
                     │ SQL Queries
┌────────────────────▼────────────────────────────────────────┐
│                    MySQL Database                            │
│                    Database: cncplan                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              employees Table                          │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  - id (PK)                                     │ │  │
│  │  │  - empNo (UNIQUE)                              │ │  │
│  │  │  - name                                        │ │  │
│  │  │  - department, title, team                    │ │  │
│  │  │  - salary fields                              │ │  │
│  │  │  - contract fields                            │ │  │
│  │  │  - 26 total fields                            │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
C:\Users\Admin\Desktop\HR\backend\
│
├── 📁 app/                          # Application package
│   ├── 📄 __init__.py              # Flask app factory
│   │                                # - Creates Flask app
│   │                                # - Configures database
│   │                                # - Sets up CORS
│   │                                # - Registers blueprints
│   │                                # - Database cleanup handlers
│   │
│   ├── 📁 models/                   # Data models
│   │   ├── 📄 __init__.py          # Models package
│   │   └── 📄 employee.py          # Employee model
│   │                                # - 26 field definitions
│   │                                # - Type hints
│   │                                # - to_dict() method
│   │                                # - Constraints & indexes
│   │
│   └── 📁 routes/                   # API endpoints
│       ├── 📄 __init__.py          # Routes package
│       └── 📄 employees.py         # Employee routes
│                                    # - CRUD operations
│                                    # - Search & filter
│                                    # - Pagination
│                                    # - Statistics
│
├── 📁 tests/                        # Test suite
│   ├── 📄 __init__.py              # Tests package
│   ├── 📄 conftest.py              # Pytest config
│   └── 📄 test_employees.py        # Employee API tests
│
├── 📄 main.py                       # Entry point
│                                    # - Loads environment
│                                    # - Creates app
│                                    # - Runs server
│
├── 📄 config.py                     # Configuration module
│                                    # - Multi-environment
│                                    # - Database settings
│                                    # - App settings
│
├── 📄 .env                          # Environment variables
│                                    # - Database credentials
│                                    # - Port configuration
│                                    # - Secret keys
│
├── 📄 requirements.txt              # Production dependencies
├── 📄 requirements-dev.txt          # Development dependencies
│
├── 📄 .gitignore                    # Git ignore rules
│
├── 🔧 install.bat                   # Installation script
├── 🔧 run.bat                       # Run script
├── 🔧 setup_database.sql            # Database setup
│
└── 📚 Documentation/
    ├── 📄 README.md                 # Main documentation
    ├── 📄 QUICKSTART.md            # Quick start guide
    ├── 📄 API_EXAMPLES.md          # API examples
    ├── 📄 DEPLOYMENT.md            # Deployment guide
    ├── 📄 ARCHITECTURE.md          # This file
    ├── 📄 PROJECT_SUMMARY.md       # Project overview
    └── 📄 CHANGELOG.md             # Version history
```

## Data Flow

### 1. Create Employee Flow

```
Client Request (POST /api/employees)
    │
    ├─→ Flask Route Handler (employees.py)
    │       ├─→ Parse JSON data
    │       ├─→ Validate required fields (empNo, name)
    │       ├─→ Check for duplicates (empNo, id_card)
    │       └─→ Parse dates and numbers
    │
    ├─→ Create Employee Object
    │       ├─→ Employee(**data)
    │       └─→ Set all 26 fields
    │
    ├─→ Database Operations
    │       ├─→ db.session.add(employee)
    │       ├─→ db.session.commit()
    │       └─→ Handle errors with rollback
    │
    └─→ Return Response
            ├─→ Success: HTTP 201 + employee data
            └─→ Error: HTTP 400/500 + error message
```

### 2. Get Employees Flow (with Pagination)

```
Client Request (GET /api/employees?page=1&per_page=10&search=John)
    │
    ├─→ Flask Route Handler
    │       ├─→ Parse query parameters
    │       │   ├─→ page, per_page
    │       │   ├─→ search term
    │       │   └─→ filters (department, status)
    │
    ├─→ Build Query
    │       ├─→ Start with Employee.query
    │       ├─→ Apply search filter (OR across multiple fields)
    │       ├─→ Apply department filter
    │       ├─→ Apply status filter
    │       └─→ Order by created_at DESC
    │
    ├─→ Execute Pagination
    │       ├─→ query.paginate(page, per_page)
    │       └─→ Returns pagination object
    │
    └─→ Return Response
            ├─→ data: List of employee dicts
            └─→ pagination: Meta information
```

### 3. Update Employee Flow

```
Client Request (PUT /api/employees/1)
    │
    ├─→ Flask Route Handler
    │       ├─→ Get employee by ID
    │       ├─→ Check if exists (404 if not)
    │       ├─→ Parse JSON data
    │       └─→ Validate changes (check duplicates if changing empNo)
    │
    ├─→ Update Fields
    │       ├─→ Loop through provided fields
    │       ├─→ Update employee attributes
    │       └─→ Set updated_at = now()
    │
    ├─→ Save to Database
    │       ├─→ db.session.commit()
    │       └─→ Handle errors with rollback
    │
    └─→ Return Response
            ├─→ Success: HTTP 200 + updated employee
            └─→ Error: HTTP 404/400/500 + message
```

## Component Interaction

```
┌──────────────────────────────────────────────────────────────┐
│                         main.py                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. Load environment (.env)                            │ │
│  │  2. Import create_app from app                         │ │
│  │  3. Create Flask application                           │ │
│  │  4. Run on configured port (8003)                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────┬───────────────────────────────────────────┘
                   │ calls
┌──────────────────▼───────────────────────────────────────────┐
│                    app/__init__.py                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  create_app():                                         │ │
│  │    1. Create Flask instance                            │ │
│  │    2. Configure database connection                    │ │
│  │    3. Initialize extensions (db, migrate, cors)        │ │
│  │    4. Register blueprints                              │ │
│  │    5. Setup cleanup handlers                           │ │
│  │    6. Create database tables                           │ │
│  │    7. Define health/status routes                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────┬───────────────────────────────────────────┘
                   │ uses
┌──────────────────▼───────────────────────────────────────────┐
│               app/models/employee.py                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Employee(db.Model):                                   │ │
│  │    - Table name: employees                             │ │
│  │    - 26 fields with type hints                         │ │
│  │    - Constraints: UNIQUE, NOT NULL                     │ │
│  │    - Methods: to_dict(), __repr__()                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                   │ imported by
┌──────────────────▼───────────────────────────────────────────┐
│              app/routes/employees.py                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  employees_bp (Blueprint):                             │ │
│  │    - GET    /api/employees                             │ │
│  │    - GET    /api/employees/<id>                        │ │
│  │    - POST   /api/employees                             │ │
│  │    - PUT    /api/employees/<id>                        │ │
│  │    - DELETE /api/employees/<id>                        │ │
│  │    - POST   /api/employees/list                        │ │
│  │    - GET    /api/employees/stats                       │ │
│  │                                                         │ │
│  │  Helper functions:                                     │ │
│  │    - parse_date()                                      │ │
│  │    - parse_float()                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

```sql
CREATE TABLE employees (
    -- Primary Key
    id INT PRIMARY KEY AUTO_INCREMENT,

    -- Basic Information
    empNo VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(10),
    birth_date DATE,
    id_card VARCHAR(50) UNIQUE,
    phone VARCHAR(20),
    email VARCHAR(100),

    -- Work Information
    department VARCHAR(100),
    title VARCHAR(100),
    team VARCHAR(100),
    hire_date DATE,
    employment_status VARCHAR(20) NOT NULL DEFAULT 'Active',
    resignation_date DATE,

    -- Contract Information
    contract_type VARCHAR(50),
    contract_start_date DATE,
    contract_end_date DATE,

    -- Salary Information
    base_salary FLOAT,
    performance_salary FLOAT,
    total_salary FLOAT,

    -- Contact Information
    home_address TEXT,
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(20),

    -- Other
    remark TEXT,

    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_empNo (empNo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## API Request/Response Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Client Application                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP Request
                     │ (JSON payload)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Flask CORS Middleware                 │
│  - Check Origin                                          │
│  - Validate Headers                                      │
│  - Handle OPTIONS preflight                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Flask Request Handler                  │
│  - Parse request.get_json()                              │
│  - Extract query parameters                              │
│  - Route to appropriate endpoint                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Validation Layer                        │
│  - Check required fields                                 │
│  - Validate data types                                   │
│  - Check constraints                                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Business Logic                          │
│  - Process data                                          │
│  - Apply business rules                                  │
│  - Build database queries                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Database Operations                     │
│  - Execute queries                                       │
│  - Transaction management                                │
│  - Error handling                                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Response Builder                        │
│  - Convert objects to dict                               │
│  - Build JSON response                                   │
│  - Set HTTP status code                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP Response
                     │ (JSON payload)
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Client Application                    │
│  - Parse response                                        │
│  - Update UI                                             │
│  - Handle errors                                         │
└─────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
Try Block
    │
    ├─→ Database Operations
    │
    ├─→ Success Path
    │       └─→ Return 200/201 with data
    │
    └─→ Exception Caught
            │
            ├─→ Validation Error
            │       ├─→ db.session.rollback()
            │       └─→ Return 400 + error message
            │
            ├─→ Not Found Error
            │       └─→ Return 404 + error message
            │
            └─→ Server Error
                    ├─→ db.session.rollback()
                    ├─→ Log error
                    └─→ Return 500 + safe error message
```

## Security Layers

```
1. Network Layer
   └─→ CORS Configuration (only localhost:6000)

2. Application Layer
   ├─→ Input Validation
   ├─→ SQL Injection Prevention (ORM)
   └─→ Error Message Sanitization

3. Database Layer
   ├─→ Unique Constraints
   ├─→ Foreign Key Constraints
   └─→ Connection Pooling

4. Data Layer
   └─→ Type Hints & Validation
```

## Performance Optimization

```
1. Database Level
   ├─→ Connection Pooling (10 base, 20 overflow)
   ├─→ Connection Pre-ping
   ├─→ Connection Recycling (1 hour)
   └─→ Indexes on frequently queried fields

2. Query Level
   ├─→ Pagination (limit result sets)
   ├─→ Selective Field Loading
   └─→ Optimized Joins

3. Application Level
   ├─→ Efficient Data Serialization
   └─→ Proper Error Handling
```

## Scalability Considerations

```
Current Setup (Single Instance)
    │
    ├─→ Horizontal Scaling
    │   ├─→ Multiple Flask instances
    │   ├─→ Load balancer (Nginx/HAProxy)
    │   └─→ Shared database
    │
    ├─→ Database Scaling
    │   ├─→ Read replicas
    │   ├─→ Connection pooling
    │   └─→ Query optimization
    │
    └─→ Caching Layer
        ├─→ Redis for sessions
        ├─→ Query result caching
        └─→ API response caching
```

## Deployment Architecture

```
Development Environment
├─→ Local MySQL
├─→ Flask Development Server
└─→ Debug Mode ON

Production Environment
├─→ Production MySQL Server
├─→ Gunicorn/uWSGI
├─→ Nginx Reverse Proxy
├─→ SSL/TLS Certificates
└─→ Debug Mode OFF
```

## Technology Stack Dependencies

```
Flask Ecosystem
├─→ Flask (Core framework)
├─→ Flask-SQLAlchemy (ORM)
├─→ Flask-Migrate (Migrations)
└─→ Flask-CORS (CORS handling)

Database
├─→ MySQL (Data storage)
├─→ PyMySQL (Driver)
└─→ SQLAlchemy (ORM)

Utilities
├─→ python-dotenv (Environment)
└─→ cryptography (Security)
```

---

This architecture is designed to be:
- **Scalable**: Easy to add more features
- **Maintainable**: Clear separation of concerns
- **Testable**: Modular design
- **Performant**: Optimized database operations
- **Secure**: Multiple security layers
