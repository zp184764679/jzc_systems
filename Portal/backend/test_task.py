#!/usr/bin/env python
"""Test task model"""
from models import SessionLocal
from models.task import Task

session = SessionLocal()
try:
    tasks = session.query(Task).filter_by(project_id=1).all()
    print(f'Found {len(tasks)} tasks')
    for t in tasks:
        print(f'  - {t.task_no}: type={t.task_type}, status={t.status}')
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f'Error: {e}')
finally:
    session.close()
