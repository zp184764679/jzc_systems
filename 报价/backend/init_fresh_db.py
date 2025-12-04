"""
新数据库初始化脚本
创建所有表结构并导入示例数据
执行时间: 2025-11-14
"""
from sqlalchemy import create_engine
from config.settings import settings
from config.database import Base, SessionLocal
from models.drawing import Drawing
from models.material import Material
from models.process import Process
from models.quote import Quote
from datetime import datetime
import json
import os

def create_tables():
    """创建所有表结构"""
    print("=" * 60)
    print("开始创建数据库表结构...")
    print(f"数据库URL: {settings.DATABASE_URL}")
    print("=" * 60)

    engine = create_engine(settings.DATABASE_URL, echo=True)
    Base.metadata.create_all(bind=engine)

    print("\n✅ 所有表结构已创建成功！")

def import_processes():
    """导入工序示例数据"""
    print("\n" + "=" * 60)
    print("导入工序示例数据...")
    print("=" * 60)

    json_path = os.path.join(os.path.dirname(__file__), 'migrations', 'process_sample_data.json')

    if not os.path.exists(json_path):
        print(f"⚠️  警告: 找不到示例数据文件: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        processes_data = json.load(f)

    db = SessionLocal()

    try:
        imported = 0
        skipped = 0

        for data in processes_data:
            # 检查是否已存在
            existing = db.query(Process).filter(
                Process.process_code == data['process_code']
            ).first()

            if existing:
                print(f"⏭️  跳过已存在的工序: {data['process_code']}")
                skipped += 1
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
            imported += 1

        db.commit()
        print(f"\n✅ 成功导入 {imported} 条工序数据")
        if skipped > 0:
            print(f"⏭️  跳过 {skipped} 条已存在的数据")

    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def verify_data():
    """验证数据导入"""
    print("\n" + "=" * 60)
    print("验证数据...")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 检查工序数量
        process_count = db.query(Process).count()
        print(f"工序表记录数: {process_count}")

        if process_count > 0:
            # 显示前3条记录
            processes = db.query(Process).limit(3).all()
            print("\n前3条工序记录:")
            for p in processes:
                print(f"  - {p.process_code}: {p.process_name}")
                print(f"    类别: {p.category}, 图标: {p.icon}, 日费用: {p.daily_fee}")

        print("\n✅ 数据验证完成！")

    finally:
        db.close()

if __name__ == "__main__":
    try:
        # 创建表结构
        create_tables()

        # 导入工序数据
        import_processes()

        # 验证数据
        verify_data()

        print("\n" + "=" * 60)
        print("✅✅✅ 数据库初始化完成！✅✅✅")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
