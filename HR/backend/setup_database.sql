-- HR System Database Setup Script
-- This script creates the database and sets up initial configuration

-- Create database
CREATE DATABASE IF NOT EXISTS cncplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE cncplan;

-- Grant privileges (adjust username as needed)
GRANT ALL PRIVILEGES ON cncplan.* TO 'root'@'localhost';
GRANT ALL PRIVILEGES ON cncplan.* TO 'root'@'%';
FLUSH PRIVILEGES;

-- Show current databases
SHOW DATABASES;

-- Note: The Flask application will automatically create the employees table
-- when you run it for the first time using SQLAlchemy's db.create_all()

-- To manually check the table structure after running the app:
-- DESCRIBE employees;

-- To view all tables in the database:
-- SHOW TABLES;

-- Sample data insert (optional - uncomment to use)
/*
INSERT INTO employees (
    empNo, name, gender, birth_date, id_card, phone, email,
    department, title, team, hire_date, employment_status,
    contract_type, contract_start_date,
    base_salary, performance_salary, total_salary,
    home_address, emergency_contact, emergency_phone,
    remark, created_at, updated_at
) VALUES (
    'EMP001', 'John Doe', 'Male', '1990-05-15', '123456789012345678',
    '13800138000', 'john.doe@company.com',
    'Information Technology', 'Senior Software Engineer', 'Backend Development',
    '2020-03-01', 'Active',
    'Full-time', '2020-03-01',
    15000.00, 5000.00, 20000.00,
    'Building 5, No. 123 Tech Street, Innovation District',
    'Jane Doe', '13900139000',
    'Excellent technical skills, team leader',
    NOW(), NOW()
);

INSERT INTO employees (
    empNo, name, gender, birth_date, phone, email,
    department, title, team, hire_date, employment_status,
    contract_type, contract_start_date,
    base_salary, total_salary,
    emergency_contact, emergency_phone,
    created_at, updated_at
) VALUES (
    'EMP002', 'Sarah Johnson', 'Female', '1988-08-20',
    '13800138001', 'sarah.johnson@company.com',
    'Human Resources', 'HR Manager', 'Recruitment',
    '2018-06-15', 'Active',
    'Full-time', '2018-06-15',
    18000.00, 24000.00,
    'Michael Johnson', '13900139001',
    NOW(), NOW()
);

INSERT INTO employees (
    empNo, name, gender, birth_date, phone, email,
    department, title, team, hire_date, employment_status,
    contract_type, contract_start_date, contract_end_date,
    base_salary, total_salary,
    emergency_contact, emergency_phone,
    remark, created_at, updated_at
) VALUES (
    'INT001', 'Mike Chen', 'Male', '2001-03-10',
    '13800138002', 'mike.chen@company.com',
    'Information Technology', 'Software Engineer Intern', 'Frontend Development',
    '2025-01-10', 'Active',
    'Intern', '2025-01-10', '2025-07-10',
    3000.00, 3000.00,
    'Lucy Chen', '13900139002',
    'Computer Science student, graduating in June 2025',
    NOW(), NOW()
);
*/

-- Useful queries for HR management

-- Query 1: Get all active employees
-- SELECT * FROM employees WHERE employment_status = 'Active' ORDER BY hire_date DESC;

-- Query 2: Get employees by department
-- SELECT department, COUNT(*) as employee_count
-- FROM employees
-- WHERE employment_status = 'Active'
-- GROUP BY department
-- ORDER BY employee_count DESC;

-- Query 3: Get employees with expiring contracts (within 3 months)
-- SELECT empNo, name, department, title, contract_end_date
-- FROM employees
-- WHERE contract_end_date IS NOT NULL
--   AND contract_end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 MONTH)
--   AND employment_status = 'Active'
-- ORDER BY contract_end_date;

-- Query 4: Calculate average salary by department
-- SELECT department,
--        AVG(base_salary) as avg_base_salary,
--        AVG(total_salary) as avg_total_salary,
--        COUNT(*) as employee_count
-- FROM employees
-- WHERE employment_status = 'Active' AND total_salary IS NOT NULL
-- GROUP BY department;

-- Query 5: Get new hires (last 30 days)
-- SELECT empNo, name, department, title, hire_date
-- FROM employees
-- WHERE hire_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
-- ORDER BY hire_date DESC;

-- Query 6: Get employees without emergency contact
-- SELECT empNo, name, department, phone, email
-- FROM employees
-- WHERE (emergency_contact IS NULL OR emergency_phone IS NULL)
--   AND employment_status = 'Active';

-- Query 7: Employee tenure report
-- SELECT empNo, name, department, title, hire_date,
--        TIMESTAMPDIFF(YEAR, hire_date, CURDATE()) as years_of_service,
--        TIMESTAMPDIFF(MONTH, hire_date, CURDATE()) as months_of_service
-- FROM employees
-- WHERE employment_status = 'Active'
-- ORDER BY hire_date;

-- Query 8: Salary distribution
-- SELECT
--     CASE
--         WHEN total_salary < 5000 THEN 'Below 5K'
--         WHEN total_salary BETWEEN 5000 AND 10000 THEN '5K-10K'
--         WHEN total_salary BETWEEN 10000 AND 20000 THEN '10K-20K'
--         WHEN total_salary > 20000 THEN 'Above 20K'
--         ELSE 'Not Set'
--     END as salary_range,
--     COUNT(*) as employee_count
-- FROM employees
-- WHERE employment_status = 'Active'
-- GROUP BY salary_range;
