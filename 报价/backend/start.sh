#!/bin/bash
cd /home/admin/quotation/backend
mkdir -p uploads
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
