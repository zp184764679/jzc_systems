"""
Unit tests for Employee API endpoints
Run with: pytest tests/test_employees.py -v
"""

import pytest
import json
from datetime import datetime


# Sample employee data for testing
SAMPLE_EMPLOYEE = {
    'empNo': 'TEST001',
    'name': 'Test Employee',
    'gender': 'Male',
    'birth_date': '1990-01-01',
    'phone': '13800138000',
    'email': 'test@company.com',
    'department': 'IT',
    'title': 'Software Engineer',
    'team': 'Development',
    'hire_date': '2020-01-01',
    'employment_status': 'Active',
    'contract_type': 'Full-time',
    'base_salary': 10000.00,
    'total_salary': 10000.00
}


class TestEmployeeAPI:
    """Test cases for Employee API endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_create_employee_success(self, client):
        """Test successful employee creation"""
        response = client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['empNo'] == SAMPLE_EMPLOYEE['empNo']
        assert data['data']['name'] == SAMPLE_EMPLOYEE['name']

    def test_create_employee_missing_required_field(self, client):
        """Test employee creation with missing required field"""
        invalid_data = {'name': 'Test'}  # Missing empNo
        response = client.post(
            '/api/employees',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_create_employee_duplicate_empno(self, client):
        """Test employee creation with duplicate empNo"""
        # Create first employee
        client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )
        # Try to create duplicate
        response = client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'already exists' in data['message']

    def test_get_employees(self, client):
        """Test get all employees with pagination"""
        # Create test employee
        client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )
        # Get employees
        response = client.get('/api/employees?page=1&per_page=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert 'pagination' in data

    def test_get_employee_by_id(self, client):
        """Test get single employee by ID"""
        # Create employee
        create_response = client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )
        employee_id = json.loads(create_response.data)['data']['id']

        # Get employee
        response = client.get(f'/api/employees/{employee_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['id'] == employee_id

    def test_get_employee_not_found(self, client):
        """Test get employee with non-existent ID"""
        response = client.get('/api/employees/99999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False

    def test_update_employee(self, client):
        """Test update employee"""
        # Create employee
        create_response = client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )
        employee_id = json.loads(create_response.data)['data']['id']

        # Update employee
        update_data = {
            'title': 'Senior Software Engineer',
            'base_salary': 15000.00
        }
        response = client.put(
            f'/api/employees/{employee_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['title'] == update_data['title']

    def test_delete_employee(self, client):
        """Test delete employee"""
        # Create employee
        create_response = client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )
        employee_id = json.loads(create_response.data)['data']['id']

        # Delete employee
        response = client.delete(f'/api/employees/{employee_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

        # Verify deletion
        get_response = client.get(f'/api/employees/{employee_id}')
        assert get_response.status_code == 404

    def test_search_employees(self, client):
        """Test search employees"""
        # Create employee
        client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )

        # Search by name
        response = client.get('/api/employees?search=Test')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['data']) > 0

    def test_filter_by_department(self, client):
        """Test filter employees by department"""
        # Create employee
        client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )

        # Filter by department
        response = client.get('/api/employees?department=IT')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_statistics(self, client):
        """Test get employee statistics"""
        # Create employee
        client.post(
            '/api/employees',
            data=json.dumps(SAMPLE_EMPLOYEE),
            content_type='application/json'
        )

        # Get stats
        response = client.get('/api/employees/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'total_employees' in data['data']
        assert 'active_employees' in data['data']


# Pytest fixtures
@pytest.fixture
def app():
    """Create application for testing"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True

    with app.app_context():
        from app import db
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()
