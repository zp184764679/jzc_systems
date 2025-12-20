"""
共享工艺库模型 - 连接报价系统的 processes 表
"""
from datetime import datetime
from . import db


class Process(db.Model):
    """工艺库表 - 与报价系统共享"""
    __tablename__ = 'processes'

    id = db.Column(db.Integer, primary_key=True)
    process_code = db.Column(db.String(50), unique=True, index=True, nullable=False, comment='工艺代码')
    process_name = db.Column(db.String(100), nullable=False, comment='工艺名称')
    category = db.Column(db.String(50), index=True, comment='工艺类别')

    # 设备信息
    machine_type = db.Column(db.String(100), comment='设备类型')
    machine_model = db.Column(db.String(100), comment='设备型号')

    # 成本信息
    hourly_rate = db.Column(db.Numeric(10, 2), comment='工时费率 元/小时')
    setup_time = db.Column(db.Numeric(10, 4), default=0, comment='段取时间 天')
    daily_fee = db.Column(db.Numeric(10, 2), default=0, comment='工事费/日 元/天')

    # 生产效率
    daily_output = db.Column(db.Integer, default=1000, comment='日产量（件/天）')
    defect_rate = db.Column(db.Numeric(5, 4), default=0, comment='不良率 %')

    # UI展示
    icon = db.Column(db.String(10), comment='图标emoji')

    # 其他信息
    description = db.Column(db.Text, comment='工艺说明')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'process_code': self.process_code,
            'process_name': self.process_name,
            'category': self.category,
            'machine_type': self.machine_type,
            'machine_model': self.machine_model,
            'hourly_rate': float(self.hourly_rate) if self.hourly_rate else None,
            'setup_time': float(self.setup_time) if self.setup_time else None,
            'daily_fee': float(self.daily_fee) if self.daily_fee else None,
            'daily_output': self.daily_output,
            'defect_rate': float(self.defect_rate) if self.defect_rate else None,
            'icon': self.icon,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Process {self.process_code}: {self.process_name}>'
