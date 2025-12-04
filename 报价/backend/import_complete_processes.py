"""
导入完整的工序数据
包含36个常见机加工工序
"""
from config.database import SessionLocal
from models.process import Process
from datetime import datetime
import json
import os

def import_processes():
    """导入完整工序数据"""
    json_path = os.path.join(os.path.dirname(__file__), 'migrations', 'complete_process_data.json')

    if not os.path.exists(json_path):
        print(f"❌ 找不到数据文件: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        processes_data = json.load(f)

    db = SessionLocal()

    try:
        imported = 0
        updated = 0
        skipped = 0

        for data in processes_data:
            # 检查是否已存在
            existing = db.query(Process).filter(
                Process.process_code == data['process_code']
            ).first()

            if existing:
                # 更新现有工序
                for key, value in data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
                print(f"🔄 更新工序: {data['process_code']} - {data['process_name']}")
                updated += 1
            else:
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
                imported += 1

        db.commit()

        print("\n" + "=" * 60)
        print(f"✅ 成功导入 {imported} 条新工序")
        print(f"🔄 更新 {updated} 条现有工序")
        print(f"总计工序数: {imported + updated}")
        print("=" * 60)

        # 显示分类统计
        print("\n工序分类统计:")
        categories = db.query(Process.category).filter(Process.is_active == True).distinct().all()
        for cat in categories:
            if cat[0]:
                count = db.query(Process).filter(
                    Process.category == cat[0],
                    Process.is_active == True
                ).count()
                print(f"  - {cat[0]}: {count}个")

    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("开始导入完整工序数据...")
    print("=" * 60)
    import_processes()
