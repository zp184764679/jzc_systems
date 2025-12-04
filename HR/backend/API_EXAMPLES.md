# HR System API Examples

This file contains practical examples for testing all API endpoints using curl, Postman, or any HTTP client.

## Base URL

```
http://localhost:8003
```

## 1. Health Check Endpoints

### Check Application Status
```bash
curl http://localhost:8003/
```

**Response:**
```json
{
  "message": "HR System Backend API",
  "status": "running"
}
```

### Check Database Health
```bash
curl http://localhost:8003/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## 2. Employee CRUD Operations

### 2.1 Create Employee

```bash
curl -X POST http://localhost:8003/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "empNo": "EMP001",
    "name": "John Doe",
    "gender": "Male",
    "birth_date": "1990-05-15",
    "id_card": "123456789012345678",
    "phone": "13800138000",
    "email": "john.doe@company.com",
    "department": "Information Technology",
    "title": "Senior Software Engineer",
    "team": "Backend Development",
    "hire_date": "2020-03-01",
    "employment_status": "Active",
    "contract_type": "Full-time",
    "contract_start_date": "2020-03-01",
    "contract_end_date": null,
    "base_salary": 15000.00,
    "performance_salary": 5000.00,
    "total_salary": 20000.00,
    "home_address": "Building 5, No. 123 Tech Street, Innovation District, City, Province",
    "emergency_contact": "Jane Doe",
    "emergency_phone": "13900139000",
    "remark": "Excellent technical skills, team leader"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Employee created successfully",
  "data": {
    "id": 1,
    "empNo": "EMP001",
    "name": "John Doe",
    ...
  }
}
```

### More Employee Creation Examples

#### Example 2: HR Department Employee
```bash
curl -X POST http://localhost:8003/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "empNo": "EMP002",
    "name": "Sarah Johnson",
    "gender": "Female",
    "birth_date": "1988-08-20",
    "id_card": "234567890123456789",
    "phone": "13800138001",
    "email": "sarah.johnson@company.com",
    "department": "Human Resources",
    "title": "HR Manager",
    "team": "Recruitment",
    "hire_date": "2018-06-15",
    "employment_status": "Active",
    "contract_type": "Full-time",
    "contract_start_date": "2018-06-15",
    "base_salary": 18000.00,
    "performance_salary": 6000.00,
    "total_salary": 24000.00,
    "home_address": "Apt 302, Tower 2, Garden Residence, City",
    "emergency_contact": "Michael Johnson",
    "emergency_phone": "13900139001"
  }'
```

#### Example 3: Intern
```bash
curl -X POST http://localhost:8003/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "empNo": "INT001",
    "name": "Mike Chen",
    "gender": "Male",
    "birth_date": "2001-03-10",
    "phone": "13800138002",
    "email": "mike.chen@company.com",
    "department": "Information Technology",
    "title": "Software Engineer Intern",
    "team": "Frontend Development",
    "hire_date": "2025-01-10",
    "employment_status": "Active",
    "contract_type": "Intern",
    "contract_start_date": "2025-01-10",
    "contract_end_date": "2025-07-10",
    "base_salary": 3000.00,
    "total_salary": 3000.00,
    "emergency_contact": "Lucy Chen",
    "emergency_phone": "13900139002",
    "remark": "Computer Science student, graduating in June 2025"
  }'
```

#### Example 4: Part-time Employee
```bash
curl -X POST http://localhost:8003/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "empNo": "PT001",
    "name": "Emily Wang",
    "gender": "Female",
    "birth_date": "1995-11-25",
    "phone": "13800138003",
    "email": "emily.wang@company.com",
    "department": "Marketing",
    "title": "Social Media Specialist",
    "team": "Digital Marketing",
    "hire_date": "2024-09-01",
    "employment_status": "Active",
    "contract_type": "Part-time",
    "contract_start_date": "2024-09-01",
    "base_salary": 6000.00,
    "total_salary": 6000.00,
    "remark": "Works 20 hours per week"
  }'
```

### 2.2 Get All Employees (with Pagination)

```bash
curl "http://localhost:8003/api/employees?page=1&per_page=10"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "empNo": "EMP001",
      "name": "John Doe",
      ...
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

### 2.3 Search Employees

#### Search by Name
```bash
curl "http://localhost:8003/api/employees?search=John"
```

#### Search by Department
```bash
curl "http://localhost:8003/api/employees?department=Information%20Technology"
```

#### Search by Employment Status
```bash
curl "http://localhost:8003/api/employees?employment_status=Active"
```

#### Combined Search
```bash
curl "http://localhost:8003/api/employees?search=John&department=IT&employment_status=Active&page=1&per_page=20"
```

### 2.4 Get Single Employee

```bash
curl http://localhost:8003/api/employees/1
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "empNo": "EMP001",
    "name": "John Doe",
    "gender": "Male",
    "birth_date": "1990-05-15",
    ...
  }
}
```

### 2.5 Update Employee

#### Update Basic Info
```bash
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138999",
    "email": "john.doe.new@company.com"
  }'
```

#### Update Work Info (Promotion)
```bash
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Lead Software Engineer",
    "base_salary": 18000.00,
    "performance_salary": 7000.00,
    "total_salary": 25000.00
  }'
```

#### Update Employment Status (Resignation)
```bash
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "employment_status": "Resigned",
    "resignation_date": "2025-02-28"
  }'
```

#### Transfer Department
```bash
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "department": "Research and Development",
    "team": "AI Lab",
    "title": "AI Research Engineer"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Employee updated successfully",
  "data": {
    "id": 1,
    "empNo": "EMP001",
    ...
  }
}
```

### 2.6 Delete Employee

```bash
curl -X DELETE http://localhost:8003/api/employees/1
```

**Response:**
```json
{
  "success": true,
  "message": "Employee deleted successfully",
  "data": {
    "id": 1,
    "empNo": "EMP001",
    "name": "John Doe",
    ...
  }
}
```

## 3. Legacy Endpoints

### POST /api/employees/list

```bash
curl -X POST http://localhost:8003/api/employees/list \
  -H "Content-Type: application/json" \
  -d '{
    "page": 1,
    "per_page": 10,
    "search": "John",
    "department": "IT",
    "employment_status": "Active"
  }'
```

## 4. Statistics Endpoint

### Get Employee Statistics

```bash
curl http://localhost:8003/api/employees/stats
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
      {"department": "Information Technology", "count": 30},
      {"department": "Human Resources", "count": 10},
      {"department": "Finance", "count": 20},
      {"department": "Marketing", "count": 15},
      {"department": "Operations", "count": 25}
    ]
  }
}
```

## 5. Error Responses

### 404 - Employee Not Found
```json
{
  "success": false,
  "message": "Employee not found"
}
```

### 400 - Validation Error
```json
{
  "success": false,
  "message": "Employee number (empNo) is required"
}
```

### 400 - Duplicate Employee Number
```json
{
  "success": false,
  "message": "Employee number EMP001 already exists"
}
```

### 500 - Server Error
```json
{
  "success": false,
  "message": "Error creating employee: [error details]"
}
```

## 6. Postman Collection

You can import these examples into Postman using the following structure:

1. Create a new Collection: "HR System API"
2. Add Environment Variables:
   - `base_url`: `http://localhost:8003`
3. Create folders:
   - Health Check
   - Employee Management
   - Statistics

## 7. Testing Scenarios

### Scenario 1: Complete Employee Lifecycle

```bash
# 1. Create employee
curl -X POST http://localhost:8003/api/employees \
  -H "Content-Type: application/json" \
  -d '{"empNo":"TEST001","name":"Test User","employment_status":"Active"}'

# 2. Get employee (assume ID is 1)
curl http://localhost:8003/api/employees/1

# 3. Update employee
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{"title":"Senior Developer"}'

# 4. Search for employee
curl "http://localhost:8003/api/employees?search=Test"

# 5. Delete employee
curl -X DELETE http://localhost:8003/api/employees/1
```

### Scenario 2: Bulk Data Testing

```bash
# Create multiple employees
for i in {1..10}; do
  curl -X POST http://localhost:8003/api/employees \
    -H "Content-Type: application/json" \
    -d "{\"empNo\":\"BULK$i\",\"name\":\"Employee $i\",\"department\":\"IT\"}"
done

# Get all with pagination
curl "http://localhost:8003/api/employees?page=1&per_page=5"
curl "http://localhost:8003/api/employees?page=2&per_page=5"
```

### Scenario 3: Advanced Search

```bash
# Search by multiple criteria
curl "http://localhost:8003/api/employees?department=IT&employment_status=Active&search=John"

# Get statistics
curl http://localhost:8003/api/employees/stats
```

## 8. JavaScript/Axios Examples

### Create Employee
```javascript
const axios = require('axios');

const createEmployee = async () => {
  try {
    const response = await axios.post('http://localhost:8003/api/employees', {
      empNo: 'EMP001',
      name: 'John Doe',
      gender: 'Male',
      department: 'IT',
      title: 'Software Engineer',
      employment_status: 'Active'
    });
    console.log('Employee created:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
};
```

### Get Employees with Pagination
```javascript
const getEmployees = async (page = 1, perPage = 10) => {
  try {
    const response = await axios.get('http://localhost:8003/api/employees', {
      params: { page, per_page: perPage }
    });
    console.log('Employees:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
};
```

### Update Employee
```javascript
const updateEmployee = async (id, updates) => {
  try {
    const response = await axios.put(`http://localhost:8003/api/employees/${id}`, updates);
    console.log('Employee updated:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
};
```

### Search Employees
```javascript
const searchEmployees = async (searchTerm, filters = {}) => {
  try {
    const response = await axios.get('http://localhost:8003/api/employees', {
      params: {
        search: searchTerm,
        ...filters
      }
    });
    console.log('Search results:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
};

// Usage
searchEmployees('John', { department: 'IT', employment_status: 'Active' });
```

## 9. Python/Requests Examples

### Create Employee
```python
import requests

def create_employee(employee_data):
    url = 'http://localhost:8003/api/employees'
    response = requests.post(url, json=employee_data)
    return response.json()

# Usage
employee = {
    'empNo': 'EMP001',
    'name': 'John Doe',
    'department': 'IT',
    'title': 'Software Engineer'
}
result = create_employee(employee)
print(result)
```

### Get Employees
```python
def get_employees(page=1, per_page=10, **filters):
    url = 'http://localhost:8003/api/employees'
    params = {'page': page, 'per_page': per_page, **filters}
    response = requests.get(url, params=params)
    return response.json()

# Usage
employees = get_employees(page=1, per_page=20, department='IT')
print(employees)
```

## 10. Common Use Cases

### Use Case 1: Onboarding New Employee
```bash
# Complete profile creation
curl -X POST http://localhost:8003/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "empNo": "NEW001",
    "name": "New Employee",
    "gender": "Male",
    "birth_date": "1995-01-01",
    "phone": "13800138000",
    "email": "new.employee@company.com",
    "department": "Engineering",
    "title": "Junior Developer",
    "team": "Web Development",
    "hire_date": "2025-01-15",
    "employment_status": "Active",
    "contract_type": "Full-time",
    "contract_start_date": "2025-01-15",
    "contract_end_date": "2027-01-14",
    "base_salary": 10000.00,
    "home_address": "Home Address Here",
    "emergency_contact": "Emergency Contact",
    "emergency_phone": "13900139000"
  }'
```

### Use Case 2: Employee Promotion
```bash
# Update salary and title
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Developer",
    "base_salary": 15000.00,
    "performance_salary": 5000.00,
    "total_salary": 20000.00,
    "remark": "Promoted due to excellent performance"
  }'
```

### Use Case 3: Department Transfer
```bash
# Transfer to new department
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "department": "Product Management",
    "team": "Product Strategy",
    "title": "Product Manager"
  }'
```

### Use Case 4: Contract Renewal
```bash
# Renew contract
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "contract_start_date": "2025-01-15",
    "contract_end_date": "2027-01-14",
    "remark": "Contract renewed for 2 years"
  }'
```

### Use Case 5: Employee Resignation
```bash
# Process resignation
curl -X PUT http://localhost:8003/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{
    "employment_status": "Resigned",
    "resignation_date": "2025-03-31",
    "remark": "Resigned for personal reasons"
  }'
```

## Notes

- All dates should be in `YYYY-MM-DD` format
- Salary fields accept decimal numbers
- `empNo` and `id_card` must be unique
- `empNo` and `name` are required fields
- All other fields are optional
- The API uses UTC timestamps for `created_at` and `updated_at`
