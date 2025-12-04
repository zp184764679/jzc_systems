# seed_processes.py
"""
种子数据 - 工艺库
"""
import sys
sys.path.insert(0, 'C:/Users/Admin/Desktop/报价/backend')

from config.database import SessionLocal
from models.process import Process

# 常用机加工工艺数据
PROCESSES_DATA = [
    # 车削类
    {
        "process_code": "CNC-TURN-01",
        "process_name": "CNC车削",
        "category": "车削",
        "machine_type": "数控车床",
        "machine_model": "CK6140",
        "hourly_rate": 80.00,
        "setup_time": 0.5,
        "daily_fee": 640.00,
        "daily_output": 500,
        "defect_rate": 0.005,
        "icon": "🔄",
        "description": "CNC数控车床加工，适用于轴类、盘类零件",
        "is_active": True
    },
    {
        "process_code": "TURN-AUTO-01",
        "process_name": "自动车",
        "category": "车削",
        "machine_type": "自动车床",
        "machine_model": "B0205",
        "hourly_rate": 60.00,
        "setup_time": 1.0,
        "daily_fee": 480.00,
        "daily_output": 2000,
        "defect_rate": 0.008,
        "icon": "⚙️",
        "description": "自动车床批量加工，适用于小型轴类零件",
        "is_active": True
    },
    {
        "process_code": "TURN-SWISS-01",
        "process_name": "走心机",
        "category": "车削",
        "machine_type": "走心式车床",
        "machine_model": "Citizen L20",
        "hourly_rate": 120.00,
        "setup_time": 1.0,
        "daily_fee": 960.00,
        "daily_output": 800,
        "defect_rate": 0.003,
        "icon": "🎯",
        "description": "走心式数控车床，高精度小零件加工",
        "is_active": True
    },
    # 铣削类
    {
        "process_code": "CNC-MILL-01",
        "process_name": "CNC铣削",
        "category": "铣削",
        "machine_type": "立式加工中心",
        "machine_model": "VMC850",
        "hourly_rate": 100.00,
        "setup_time": 0.5,
        "daily_fee": 800.00,
        "daily_output": 200,
        "defect_rate": 0.005,
        "icon": "🔧",
        "description": "CNC立式加工中心，适用于箱体、板类零件",
        "is_active": True
    },
    {
        "process_code": "CNC-MILL-5X",
        "process_name": "五轴加工",
        "category": "铣削",
        "machine_type": "五轴加工中心",
        "machine_model": "DMG DMU50",
        "hourly_rate": 200.00,
        "setup_time": 1.0,
        "daily_fee": 1600.00,
        "daily_output": 50,
        "defect_rate": 0.002,
        "icon": "⭐",
        "description": "五轴联动加工中心，复杂曲面零件",
        "is_active": True
    },
    # 磨削类
    {
        "process_code": "GRIND-CYL-01",
        "process_name": "外圆磨",
        "category": "磨削",
        "machine_type": "外圆磨床",
        "machine_model": "M1432",
        "hourly_rate": 70.00,
        "setup_time": 0.5,
        "daily_fee": 560.00,
        "daily_output": 300,
        "defect_rate": 0.003,
        "icon": "💫",
        "description": "外圆磨床精加工，轴类零件精磨",
        "is_active": True
    },
    {
        "process_code": "GRIND-SUR-01",
        "process_name": "平面磨",
        "category": "磨削",
        "machine_type": "平面磨床",
        "machine_model": "M7130",
        "hourly_rate": 60.00,
        "setup_time": 0.3,
        "daily_fee": 480.00,
        "daily_output": 400,
        "defect_rate": 0.003,
        "icon": "📐",
        "description": "平面磨床精加工，平面精度保证",
        "is_active": True
    },
    {
        "process_code": "GRIND-INT-01",
        "process_name": "内圆磨",
        "category": "磨削",
        "machine_type": "内圆磨床",
        "machine_model": "M2110",
        "hourly_rate": 80.00,
        "setup_time": 0.5,
        "daily_fee": 640.00,
        "daily_output": 200,
        "defect_rate": 0.003,
        "icon": "🔘",
        "description": "内圆磨床精加工，孔类精磨",
        "is_active": True
    },
    # 钻孔类
    {
        "process_code": "DRILL-01",
        "process_name": "钻孔",
        "category": "钻削",
        "machine_type": "钻床",
        "machine_model": "Z3050",
        "hourly_rate": 40.00,
        "setup_time": 0.2,
        "daily_fee": 320.00,
        "daily_output": 1000,
        "defect_rate": 0.005,
        "icon": "🔩",
        "description": "普通钻床钻孔加工",
        "is_active": True
    },
    {
        "process_code": "TAP-01",
        "process_name": "攻牙",
        "category": "钻削",
        "machine_type": "攻丝机",
        "machine_model": "S4012",
        "hourly_rate": 50.00,
        "setup_time": 0.2,
        "daily_fee": 400.00,
        "daily_output": 800,
        "defect_rate": 0.008,
        "icon": "🔗",
        "description": "螺纹攻丝加工",
        "is_active": True
    },
    # 特种加工
    {
        "process_code": "EDM-WIRE-01",
        "process_name": "线切割",
        "category": "特种加工",
        "machine_type": "线切割机",
        "machine_model": "DK7740",
        "hourly_rate": 50.00,
        "setup_time": 0.5,
        "daily_fee": 400.00,
        "daily_output": 100,
        "defect_rate": 0.002,
        "icon": "⚡",
        "description": "电火花线切割加工，适用于模具、复杂轮廓",
        "is_active": True
    },
    {
        "process_code": "EDM-SINK-01",
        "process_name": "电火花",
        "category": "特种加工",
        "machine_type": "电火花成型机",
        "machine_model": "D7140",
        "hourly_rate": 60.00,
        "setup_time": 1.0,
        "daily_fee": 480.00,
        "daily_output": 50,
        "defect_rate": 0.002,
        "icon": "🔥",
        "description": "电火花成型加工，模具型腔加工",
        "is_active": True
    },
    # 表面处理
    {
        "process_code": "POLISH-01",
        "process_name": "抛光",
        "category": "表面处理",
        "machine_type": "抛光机",
        "machine_model": "PG-01",
        "hourly_rate": 40.00,
        "setup_time": 0.1,
        "daily_fee": 320.00,
        "daily_output": 500,
        "defect_rate": 0.005,
        "icon": "✨",
        "description": "表面抛光处理",
        "is_active": True
    },
    {
        "process_code": "DEBURR-01",
        "process_name": "去毛刺",
        "category": "表面处理",
        "machine_type": "去毛刺机",
        "machine_model": "DB-01",
        "hourly_rate": 30.00,
        "setup_time": 0.1,
        "daily_fee": 240.00,
        "daily_output": 1000,
        "defect_rate": 0.002,
        "icon": "🧹",
        "description": "零件去毛刺处理",
        "is_active": True
    },
    # 热处理
    {
        "process_code": "HEAT-QUENCH-01",
        "process_name": "淬火",
        "category": "热处理",
        "machine_type": "淬火炉",
        "machine_model": "RQ-01",
        "hourly_rate": 30.00,
        "setup_time": 0.5,
        "daily_fee": 240.00,
        "daily_output": 500,
        "defect_rate": 0.01,
        "icon": "🔥",
        "description": "零件淬火热处理",
        "is_active": True
    },
    {
        "process_code": "HEAT-TEMPER-01",
        "process_name": "回火",
        "category": "热处理",
        "machine_type": "回火炉",
        "machine_model": "RT-01",
        "hourly_rate": 25.00,
        "setup_time": 0.5,
        "daily_fee": 200.00,
        "daily_output": 500,
        "defect_rate": 0.005,
        "icon": "🌡️",
        "description": "零件回火热处理",
        "is_active": True
    },
    # 检验
    {
        "process_code": "QC-01",
        "process_name": "检验",
        "category": "检验",
        "machine_type": "三坐标测量机",
        "machine_model": "CMM",
        "hourly_rate": 100.00,
        "setup_time": 0.2,
        "daily_fee": 800.00,
        "daily_output": 200,
        "defect_rate": 0,
        "icon": "🔍",
        "description": "三坐标精密测量检验",
        "is_active": True
    },
    # 其他
    {
        "process_code": "ASSEM-01",
        "process_name": "组装",
        "category": "其他",
        "machine_type": "组装工位",
        "machine_model": "手工",
        "hourly_rate": 35.00,
        "setup_time": 0.1,
        "daily_fee": 280.00,
        "daily_output": 300,
        "defect_rate": 0.005,
        "icon": "🔨",
        "description": "零件组装工序",
        "is_active": True
    },
    {
        "process_code": "PACK-01",
        "process_name": "包装",
        "category": "其他",
        "machine_type": "包装工位",
        "machine_model": "手工",
        "hourly_rate": 25.00,
        "setup_time": 0.1,
        "daily_fee": 200.00,
        "daily_output": 1000,
        "defect_rate": 0,
        "icon": "📦",
        "description": "成品包装工序",
        "is_active": True
    },
]


def seed_processes():
    """填充工艺库种子数据"""
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing_count = db.query(Process).count()
        if existing_count > 0:
            print(f"工艺库已有 {existing_count} 条数据，跳过种子数据填充")
            return

        # 添加种子数据
        for data in PROCESSES_DATA:
            process = Process(**data)
            db.add(process)

        db.commit()
        print(f"✅ 成功添加 {len(PROCESSES_DATA)} 条工艺数据")

        # 验证
        count = db.query(Process).count()
        print(f"工艺库现有 {count} 条数据")

    except Exception as e:
        db.rollback()
        print(f"❌ 添加工艺数据失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_processes()
