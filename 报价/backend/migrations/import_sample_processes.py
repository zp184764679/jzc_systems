"""
导入示例工序数据
执行时间: 2025-11-14
"""
import json
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.database import SessionLocal
from models.process import Process
from datetime import datetime

def import_processes():
    # 读取示例数据
    json_path = os.path.join(os.path.dirname(__file__), 'process_sample_data.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        processes_data = json.load(f)

    db = SessionLocal()

    try:
        print(f"准备导入 {len(processes_data)} 条工序数据...")

        for data in processes_data:
            # 检查工序是否已存在
            existing = db.query(Process).filter(
                Process.process_code == data['process_code']
            ).first()

            if existing:
                print(f"⚠️  工序 {data['process_code']} 已存在，跳过")
                continue

            # 创建新工序
            process = Process(
                process_code=data['process_code'],
                process_name=data['process_name'],
                category=data.get('category'),
                icon=data.get('icon'),
                defect_rate=data.get('defect_rate', 0),
                daily_output=data.get('daily_output', 1000),
                setup_time=data.get('setup_time', 0.125),
                daily_fee=data.get('daily_fee', 0),
                hourly_rate=data.get('hourly_rate', 0),
                description=data.get('description'),
                is_active=True,
                created_at=datetime.now()
            )

            db.add(process)
            print(f"✅ 导入工序: {data['process_code']} - {data['process_name']}")

        db.commit()

        # 查询总数
        total = db.query(Process).count()
        print(f"\n✅ 导入完成！数据库中现有 {total} 条工序")

        # 显示所有工序
        print("\n当前所有工序:")
        processes = db.query(Process).all()
        for i, p in enumerate(processes, 1):
            print(f"  {i}. {p.process_code}: {p.process_name} {p.icon or ''} "
                  f"(日产:{p.daily_output}, 工事费:{p.daily_fee})")

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_processes()
