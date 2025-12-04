"""
调试工序API响应
"""
from config.database import SessionLocal
from models.process import Process
from api.schemas import ProcessResponse
import json

db = SessionLocal()

try:
    # 获取第一条记录
    process = db.query(Process).first()

    if process:
        print("=" * 60)
        print("SQLAlchemy对象属性:")
        print("=" * 60)
        print(f"process_code: {process.process_code}")
        print(f"process_name: {process.process_name}")
        print(f"daily_fee: {process.daily_fee}")
        print(f"icon: {process.icon}")
        print(f"hourly_rate: {process.hourly_rate}")

        print("\n" + "=" * 60)
        print("ProcessResponse.model_validate()结果:")
        print("=" * 60)
        response = ProcessResponse.model_validate(process)
        print(f"response object: {response}")

        print("\n" + "=" * 60)
        print("response.model_dump()结果:")
        print("=" * 60)
        data = response.model_dump()
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

        print("\n" + "=" * 60)
        print("response.model_dump_json()结果:")
        print("=" * 60)
        json_str = response.model_dump_json()
        print(json_str)

finally:
    db.close()
