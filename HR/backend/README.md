# HR System Backend

A comprehensive Human Resources Management System backend built with Flask, SQLAlchemy, and MySQL.

## Features

- Complete employee lifecycle management (CRUD operations)
- Advanced search and filtering capabilities
- Pagination support for large datasets
- Comprehensive employee data tracking including:
  - Basic information (name, contact, demographics)
  - Work information (department, title, team, employment status)
  - Contract management (type, start/end dates)
  - Salary tracking (base, performance, total)
  - Emergency contacts and addresses
- RESTful API with JSON responses
- Database connection pooling and health checks
- CORS support for frontend integration
- Legacy API endpoint support

## Technology Stack

- **Framework**: Flask
- **Database**: MySQL with SQLAlchemy ORM
- **Migration**: Flask-Migrate
- **CORS**: Flask-CORS
- **Database Driver**: PyMySQL

## Project Structure

```
backend/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models/
│   │   ├── __init__.py
│   │   └── employee.py       # Employee model
│   └── routes/
│       ├── __init__.py
│       └── employees.py      # Employee API endpoints
├── .env                      # Environment configuration
├── .gitignore
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
└── README.md
```

## Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd C:\Users\Admin\Desktop\HR\backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**

   Update `.env` file with your database credentials:
   ```
   DB_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=root
   MYSQL_DATABASE=cncplan
   PORT=8003
   ```

6. **Create the database**
   ```sql
   CREATE DATABASE cncplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

7. **Run the application**
   ```bash
   python main.py
   ```

   The server will start on `http://localhost:8003`

## API Endpoints

### Employee Management

#### Get All Employees (with pagination & search)
```http
GET /api/employees?page=1&per_page=10&search=john&department=IT&employment_status=Active
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10)
- `search` (optional): Search term for empNo, name, department, title, email, phone
- `department` (optional): Filter by department
- `employment_status` (optional): Filter by employment status

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "empNo": "EMP001",
      "name": "John Doe",
      "gender": "Male",
      "birth_date": "1990-01-15",
      "id_card": "123456789",
      "phone": "1234567890",
      "email": "john.doe@example.com",
      "department": "IT",
      "title": "Software Engineer",
      "team": "Development",
      "hire_date": "2020-01-01",
      "employment_status": "Active",
      "resignation_date": null,
      "contract_type": "Full-time",
      "contract_start_date": "2020-01-01",
      "contract_end_date": null,
      "base_salary": 50000.00,
      "performance_salary": 10000.00,
      "total_salary": 60000.00,
      "home_address": "123 Main St",
      "emergency_contact": "Jane Doe",
      "emergency_phone": "0987654321",
      "remark": "Excellent performance",
      "created_at": "2025-01-15 10:30:00",
      "updated_at": "2025-01-15 10:30:00"
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "per_page": 10,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

#### Get Single Employee
```http
GET /api/employees/{id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "empNo": "EMP001",
    "name": "John Doe",
    ...
  }
}
```

#### Create Employee
```http
POST /api/employees
Content-Type: application/json

{
  "empNo": "EMP001",
  "name": "John Doe",
  "gender": "Male",
  "birth_date": "1990-01-15",
  "id_card": "123456789",
  "phone": "1234567890",
  "email": "john.doe@example.com",
  "department": "IT",
  "title": "Software Engineer",
  "team": "Development",
  "hire_date": "2020-01-01",
  "employment_status": "Active",
  "contract_type": "Full-time",
  "contract_start_date": "2020-01-01",
  "base_salary": 50000.00,
  "performance_salary": 10000.00,
  "total_salary": 60000.00,
  "home_address": "123 Main St",
  "emergency_contact": "Jane Doe",
  "emergency_phone": "0987654321",
  "remark": "New hire"
}
```

**Required Fields:**
- `empNo`: Employee number (must be unique)
- `name`: Employee name

**Response:**
```json
{
  "success": true,
  "message": "Employee created successfully",
  "data": {
    "id": 1,
    "empNo": "EMP001",
    ...
  }
}
```

#### Update Employee
```http
PUT /api/employees/{id}
Content-Type: application/json

{
  "name": "John Smith",
  "title": "Senior Software Engineer",
  "base_salary": 60000.00
}
```

**Response:**
```json
{
  "success": true,
  "message": "Employee updated successfully",
  "data": {
    "id": 1,
    "name": "John Smith",
    ...
  }
}
```

#### Delete Employee
```http
DELETE /api/employees/{id}
```

**Response:**
```json
{
  "success": true,
  "message": "Employee deleted successfully",
  "data": {
    "id": 1,
    "empNo": "EMP001",
    ...
  }
}
```

#### List Employees (POST - Legacy Support)
```http
POST /api/employees/list
Content-Type: application/json

{
  "page": 1,
  "per_page": 10,
  "search": "john",
  "department": "IT",
  "employment_status": "Active"
}
```

#### Get Employee Statistics
```http
GET /api/employees/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_employees": 100,
    "active_employees": 85,
    "resigned_employees": 15,
    "department_distribution": [
      {"department": "IT", "count": 30},
      {"department": "HR", "count": 10},
      {"department": "Finance", "count": 20}
    ]
  }
}
```

### Health Check

#### Application Health
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### Root Endpoint
```http
GET /
```

**Response:**
```json
{
  "message": "HR System Backend API",
  "status": "running"
}
```

## Employee Model Fields

### Basic Information
- `id`: Primary key (auto-increment)
- `empNo`: Employee number (unique, required)
- `name`: Full name (required)
- `gender`: Gender (Male/Female/Other)
- `birth_date`: Date of birth
- `id_card`: ID card number (unique)
- `phone`: Phone number
- `email`: Email address

### Work Information
- `department`: Department name
- `title`: Job title
- `team`: Team/Section name
- `hire_date`: Date of hiring
- `employment_status`: Active/Resigned/Terminated/On Leave (default: Active)
- `resignation_date`: Date of resignation

### Contract Information
- `contract_type`: Full-time/Part-time/Contract/Intern
- `contract_start_date`: Contract start date
- `contract_end_date`: Contract end date

### Salary Information
- `base_salary`: Base salary amount
- `performance_salary`: Performance/bonus salary
- `total_salary`: Total salary

### Address & Emergency Contact
- `home_address`: Residential address
- `emergency_contact`: Emergency contact person name
- `emergency_phone`: Emergency contact phone number

### Additional Information
- `remark`: Additional notes/remarks
- `created_at`: Record creation timestamp (auto-generated)
- `updated_at`: Last update timestamp (auto-updated)

## Database Schema

The application automatically creates the `employees` table with all necessary fields and indexes when first run.

### Key Features:
- Unique constraints on `empNo` and `id_card`
- Indexes for faster queries on `empNo`
- Comprehensive field comments for documentation
- Automatic timestamp management
- Support for NULL values on optional fields

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
DB_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=cncplan
PORT=8003
```

### CORS Configuration

The application is configured to accept requests from `http://localhost:6000`. To modify this, edit `app/__init__.py`:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:6000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

## Database Migration

To create and apply migrations:

1. **Initialize migrations** (first time only):
   ```bash
   flask db init
   ```

2. **Create a migration**:
   ```bash
   flask db migrate -m "Description of changes"
   ```

3. **Apply migrations**:
   ```bash
   flask db upgrade
   ```

## Error Handling

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "message": "Error description here"
}
```

HTTP Status Codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## Development

### Running in Debug Mode

The application runs in debug mode by default when using `python main.py`. For production, set `debug=False` in `main.py`.

### Testing the API

Use tools like:
- Postman
- curl
- Thunder Client (VS Code extension)
- Any HTTP client

Example curl command:
```bash
curl -X GET http://localhost:8003/api/employees?page=1&per_page=10
```

## Production Deployment

For production deployment:

1. Set `debug=False` in `main.py`
2. Use a production WSGI server (gunicorn, uWSGI)
3. Configure proper database credentials
4. Set up SSL/TLS certificates
5. Configure firewall rules
6. Set up proper logging
7. Use environment-specific configuration

Example with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8003 main:app
```

## Troubleshooting

### Database Connection Issues
- Verify MySQL is running
- Check database credentials in `.env`
- Ensure database exists: `CREATE DATABASE cncplan;`
- Check firewall settings

### Port Already in Use
- Change PORT in `.env` file
- Kill process using the port: `netstat -ano | findstr :8003`

### Import Errors
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

## License

This project is proprietary software for internal use.

## Support

For issues and questions, contact the development team.
