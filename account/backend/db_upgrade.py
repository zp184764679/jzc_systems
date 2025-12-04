"""
Database upgrade script - automatically adds missing columns to registration_requests table
This script will be run on application startup to ensure database schema is up to date
"""
from sqlalchemy import create_engine, inspect, text
import os

def upgrade_database():
    """Check and upgrade database schema"""
    # Database configuration
    DB_USER = os.getenv('MYSQL_USER', 'app')
    DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'app')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('MYSQL_DATABASE', 'account')
    DATABASE_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'

    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    # Check if registration_requests table exists
    if 'registration_requests' not in inspector.get_table_names():
        print("Table registration_requests does not exist, will be created by init_db()")
        return

    # Get existing columns
    existing_columns = {col['name'] for col in inspector.get_columns('registration_requests')}

    # Define required columns and their definitions
    required_columns = {
        'username': "VARCHAR(50) AFTER full_name",
        'hashed_password': "VARCHAR(255) AFTER username"
    }

    # Add missing columns
    with engine.connect() as conn:
        for column_name, column_def in required_columns.items():
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE registration_requests ADD COLUMN {column_name} {column_def}"
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"❌ Error adding column {column_name}: {e}")
                    conn.rollback()
            else:
                print(f"✓ Column {column_name} already exists")

    print("Database schema upgrade completed")

if __name__ == '__main__':
    upgrade_database()
