"""
导入完整的材料库数据
包含47种常见工业材料
"""
from config.database import SessionLocal
from models.material import Material
from datetime import datetime
import json
import os


def import_materials():
    """导入完整材料库数据"""
    json_path = os.path.join(os.path.dirname(__file__), 'migrations', 'material_data.json')

    if not os.path.exists(json_path):
        print(f"❌ 找不到数据文件: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        materials_data = json.load(f)

    db = SessionLocal()

    try:
        imported = 0
        updated = 0
        skipped = 0

        for data in materials_data:
            # 检查是否已存在
            existing = db.query(Material).filter(
                Material.material_code == data['material_code']
            ).first()

            if existing:
                # 更新现有材料
                existing.material_name = data['material_name']
                existing.category = data.get('category')
                existing.density = data.get('density')
                existing.price_per_kg = data.get('typical_price')
                existing.price_currency = 'CNY'
                existing.remark = data.get('description')
                existing.is_active = True
                existing.updated_at = datetime.now()
                print(f"🔄 更新材料: {data['material_code']} - {data['material_name']}")
                updated += 1
            else:
                # 创建新材料
                material = Material(
                    material_code=data['material_code'],
                    material_name=data['material_name'],
                    category=data.get('category'),
                    density=data.get('density'),
                    price_per_kg=data.get('typical_price'),
                    price_currency='CNY',
                    remark=data.get('description'),
                    is_active=True,
                    created_at=datetime.now()
                )
                db.add(material)
                print(f"✅ 导入材料: {data['material_code']} - {data['material_name']}")
                imported += 1

        db.commit()

        print("\n" + "=" * 60)
        print(f"✅ 成功导入 {imported} 种新材料")
        print(f"🔄 更新 {updated} 种现有材料")
        print(f"总计材料数: {imported + updated}")
        print("=" * 60)

        # 显示分类统计
        print("\n材料分类统计:")
        categories = db.query(Material.category).filter(Material.is_active == True).distinct().all()
        for cat in categories:
            if cat[0]:
                count = db.query(Material).filter(
                    Material.category == cat[0],
                    Material.is_active == True
                ).count()
                print(f"  - {cat[0]}: {count}种")

        # 显示每个类别的材料列表
        print("\n材料详细信息:")
        for cat in categories:
            if cat[0]:
                print(f"\n【{cat[0]}】")
                materials = db.query(Material).filter(
                    Material.category == cat[0],
                    Material.is_active == True
                ).all()
                for mat in materials:
                    print(f"  • {mat.material_code:12} - {mat.material_name:20} "
                          f"(密度: {mat.density} g/cm³, 价格: ¥{mat.price_per_kg}/kg)")

    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("开始导入完整材料库数据...")
    print("=" * 60)
    import_materials()
