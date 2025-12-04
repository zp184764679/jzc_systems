# scripts/init_data.py
"""
初始化基础数据
包括：材料库、工艺库、切削参数等
"""
import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import SessionLocal, init_db
from models.material import Material
from models.process import Process, CuttingParameter


def init_materials():
    """初始化材料库"""
    print("📦 初始化材料库...")

    materials_data = [
        # 不锈钢系列
        {
            "material_code": "SUS303",
            "material_name": "303不锈钢",
            "category": "不锈钢",
            "density": 7.93,
            "hardness": "HB187",
            "tensile_strength": 515,
            "price_per_kg": 35.0,
            "remark": "易切削不锈钢，常用于自动车床件"
        },
        {
            "material_code": "SUS304",
            "material_name": "304不锈钢",
            "category": "不锈钢",
            "density": 7.93,
            "hardness": "HB187",
            "tensile_strength": 520,
            "price_per_kg": 32.0,
            "remark": "通用不锈钢，耐腐蚀性好"
        },
        {
            "material_code": "SUS316",
            "material_name": "316不锈钢",
            "category": "不锈钢",
            "density": 7.98,
            "hardness": "HB187",
            "tensile_strength": 520,
            "price_per_kg": 45.0,
            "remark": "高耐腐蚀不锈钢，含钼"
        },
        {
            "material_code": "SUS420",
            "material_name": "420不锈钢",
            "category": "不锈钢",
            "density": 7.75,
            "hardness": "HRC52",
            "tensile_strength": 660,
            "price_per_kg": 28.0,
            "remark": "马氏体不锈钢，可热处理"
        },

        # 铝合金系列
        {
            "material_code": "6061",
            "material_name": "6061铝合金",
            "category": "铝合金",
            "density": 2.70,
            "hardness": "HB95",
            "tensile_strength": 310,
            "price_per_kg": 22.0,
            "remark": "综合性能好，应用广泛"
        },
        {
            "material_code": "7075",
            "material_name": "7075铝合金",
            "category": "铝合金",
            "density": 2.81,
            "hardness": "HB150",
            "tensile_strength": 572,
            "price_per_kg": 38.0,
            "remark": "超硬铝合金，强度高"
        },
        {
            "material_code": "2024",
            "material_name": "2024铝合金",
            "category": "铝合金",
            "density": 2.78,
            "hardness": "HB120",
            "tensile_strength": 470,
            "price_per_kg": 28.0,
            "remark": "高强度铝合金"
        },

        # 碳钢系列
        {
            "material_code": "45#",
            "material_name": "45号钢",
            "category": "碳钢",
            "density": 7.85,
            "hardness": "HB197",
            "tensile_strength": 600,
            "price_per_kg": 8.0,
            "remark": "优质碳素结构钢"
        },
        {
            "material_code": "Q235",
            "material_name": "Q235碳钢",
            "category": "碳钢",
            "density": 7.85,
            "hardness": "HB120",
            "tensile_strength": 370,
            "price_per_kg": 5.5,
            "remark": "普通碳素结构钢"
        },

        # 铜合金系列
        {
            "material_code": "C3604",
            "material_name": "易切削黄铜",
            "category": "铜合金",
            "density": 8.50,
            "hardness": "HB80",
            "tensile_strength": 340,
            "price_per_kg": 58.0,
            "remark": "易切削黄铜，自动车床件"
        },
    ]

    db = SessionLocal()
    try:
        for data in materials_data:
            # 检查是否已存在
            existing = db.query(Material).filter(
                Material.material_code == data["material_code"]
            ).first()

            if not existing:
                material = Material(**data)
                db.add(material)
                print(f"  ✅ 添加材料: {data['material_code']} - {data['material_name']}")

        db.commit()
        print(f"✅ 材料库初始化完成，共 {len(materials_data)} 种材料")
    except Exception as e:
        print(f"❌ 材料库初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


def init_processes():
    """初始化工艺库"""
    print("\n🔧 初始化工艺库...")

    processes_data = [
        {
            "process_code": "CNC_TURNING",
            "process_name": "CNC车削",
            "category": "车削",
            "machine_type": "CNC车床",
            "hourly_rate": 55.0,
            "setup_time": 0.125,
            "daily_output": 500,
            "defect_rate": 0.01,
            "description": "CNC车床加工，适用于回转体零件"
        },
        {
            "process_code": "CNC_MILLING",
            "process_name": "CNC铣削",
            "category": "铣削",
            "machine_type": "CNC铣床/加工中心",
            "hourly_rate": 80.0,
            "setup_time": 0.25,
            "daily_output": 200,
            "defect_rate": 0.015,
            "description": "CNC铣床/加工中心，适用于复杂轮廓"
        },
        {
            "process_code": "GRINDING",
            "process_name": "磨削",
            "category": "磨削",
            "machine_type": "磨床",
            "hourly_rate": 65.0,
            "setup_time": 0.20,
            "daily_output": 300,
            "defect_rate": 0.01,
            "description": "高精度表面加工"
        },
        {
            "process_code": "CENTERLESS_GRINDING",
            "process_name": "无芯磨削",
            "category": "磨削",
            "machine_type": "无心磨床",
            "hourly_rate": 70.0,
            "setup_time": 0.15,
            "daily_output": 800,
            "defect_rate": 0.008,
            "description": "高效率圆柱面磨削"
        },
        {
            "process_code": "DRILLING",
            "process_name": "钻孔",
            "category": "钻削",
            "machine_type": "钻床",
            "hourly_rate": 40.0,
            "setup_time": 0.10,
            "daily_output": 1000,
            "defect_rate": 0.005,
            "description": "孔加工"
        },
        {
            "process_code": "TAPPING",
            "process_name": "攻丝",
            "category": "螺纹",
            "machine_type": "攻丝机",
            "hourly_rate": 45.0,
            "setup_time": 0.10,
            "daily_output": 800,
            "defect_rate": 0.02,
            "description": "内螺纹加工"
        },
        {
            "process_code": "DEBURRING",
            "process_name": "去毛刺",
            "category": "辅助",
            "machine_type": "去毛刺机/手工",
            "hourly_rate": 25.0,
            "setup_time": 0.05,
            "daily_output": 2000,
            "defect_rate": 0,
            "description": "去除加工毛刺"
        },
        {
            "process_code": "HEAT_TREATMENT",
            "process_name": "热处理",
            "category": "热处理",
            "machine_type": "热处理炉",
            "hourly_rate": 15.0,
            "setup_time": 0,
            "daily_output": 5000,
            "defect_rate": 0.001,
            "description": "提高硬度和强度"
        },
        {
            "process_code": "PLATING",
            "process_name": "电镀",
            "category": "表面处理",
            "machine_type": "电镀线",
            "hourly_rate": 20.0,
            "setup_time": 0,
            "daily_output": 3000,
            "defect_rate": 0.005,
            "description": "表面电镀处理"
        },
        {
            "process_code": "INSPECTION",
            "process_name": "检验",
            "category": "质检",
            "machine_type": "检测设备",
            "hourly_rate": 35.0,
            "setup_time": 0.05,
            "daily_output": 3000,
            "defect_rate": 0,
            "description": "质量检验"
        },
    ]

    db = SessionLocal()
    try:
        for data in processes_data:
            existing = db.query(Process).filter(
                Process.process_code == data["process_code"]
            ).first()

            if not existing:
                process = Process(**data)
                db.add(process)
                print(f"  ✅ 添加工艺: {data['process_code']} - {data['process_name']}")

        db.commit()
        print(f"✅ 工艺库初始化完成，共 {len(processes_data)} 种工艺")
    except Exception as e:
        print(f"❌ 工艺库初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


def init_cutting_parameters():
    """初始化切削参数库"""
    print("\n⚙️  初始化切削参数库...")

    cutting_params_data = [
        # 不锈钢切削参数
        {
            "material_category": "不锈钢",
            "process_type": "车削",
            "cutting_speed": 80.0,
            "feed_rate": 0.15,
            "depth_of_cut": 2.0,
            "spindle_speed": 800,
            "tool_type": "硬质合金",
            "tool_life": 60,
            "remark": "303/304不锈钢车削参数"
        },
        {
            "material_category": "不锈钢",
            "process_type": "铣削",
            "cutting_speed": 60.0,
            "feed_rate": 0.10,
            "depth_of_cut": 1.5,
            "spindle_speed": 600,
            "tool_type": "硬质合金",
            "tool_life": 45,
            "remark": "不锈钢铣削参数"
        },

        # 铝合金切削参数
        {
            "material_category": "铝合金",
            "process_type": "车削",
            "cutting_speed": 250.0,
            "feed_rate": 0.25,
            "depth_of_cut": 3.0,
            "spindle_speed": 2500,
            "tool_type": "硬质合金",
            "tool_life": 120,
            "remark": "6061铝合金车削参数"
        },
        {
            "material_category": "铝合金",
            "process_type": "铣削",
            "cutting_speed": 300.0,
            "feed_rate": 0.20,
            "depth_of_cut": 2.5,
            "spindle_speed": 3000,
            "tool_type": "硬质合金",
            "tool_life": 100,
            "remark": "铝合金铣削参数"
        },

        # 碳钢切削参数
        {
            "material_category": "碳钢",
            "process_type": "车削",
            "cutting_speed": 120.0,
            "feed_rate": 0.20,
            "depth_of_cut": 2.5,
            "spindle_speed": 1200,
            "tool_type": "硬质合金",
            "tool_life": 80,
            "remark": "45号钢车削参数"
        },
        {
            "material_category": "碳钢",
            "process_type": "铣削",
            "cutting_speed": 100.0,
            "feed_rate": 0.15,
            "depth_of_cut": 2.0,
            "spindle_speed": 1000,
            "tool_type": "硬质合金",
            "tool_life": 60,
            "remark": "碳钢铣削参数"
        },
    ]

    db = SessionLocal()
    try:
        for data in cutting_params_data:
            param = CuttingParameter(**data)
            db.add(param)
            print(f"  ✅ 添加参数: {data['material_category']} - {data['process_type']}")

        db.commit()
        print(f"✅ 切削参数库初始化完成，共 {len(cutting_params_data)} 组参数")
    except Exception as e:
        print(f"❌ 切削参数库初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 开始初始化数据库")
    print("=" * 60)

    # 初始化数据库表结构
    init_db()

    # 初始化基础数据
    init_materials()
    init_processes()
    init_cutting_parameters()

    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成！")
    print("=" * 60)
    print("\n📊 数据统计:")
    db = SessionLocal()
    try:
        material_count = db.query(Material).count()
        process_count = db.query(Process).count()
        cutting_param_count = db.query(CuttingParameter).count()

        print(f"  - 材料库: {material_count} 种材料")
        print(f"  - 工艺库: {process_count} 种工艺")
        print(f"  - 切削参数: {cutting_param_count} 组参数")
    finally:
        db.close()


if __name__ == "__main__":
    main()
