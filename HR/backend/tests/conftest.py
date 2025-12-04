"""
Pytest configuration and shared fixtures
"""

import pytest
import os


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'True'
