#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

# Test login API
url = "http://localhost:5001/api/v1/login"
data = {
    "email": "admin@test.com",
    "password": "admin123"
}

try:
    response = requests.post(url, json=data, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")

    if response.status_code == 500:
        print("\n❌ Got 500 error - checking backend logs...")

except Exception as e:
    print(f"Error: {e}")
