# -*- coding: utf-8 -*-
from app import app

with app.test_client() as client:
    # 测试invoice stats endpoint
    response = client.get('/api/v1/invoices/stats')
    print(f"Status: {response.status_code}")
    print(f"Data: {response.get_json()}")
    print(f"Headers: {dict(response.headers)}")
