"""
Report Model - 报表记录模型
"""
import enum
from datetime import datetime
from app import db


class ReportType(enum.Enum):
    """报表类型"""
    PRODUCTION = "production"  # 生产报表
    ORDER = "order"           # 订单报表
    TASK = "task"             # 任务报表
    KPI = "kpi"               # KPI综合报表
    CUSTOM = "custom"         # 自定义报表


class ReportFormat(enum.Enum):
    """报表格式"""
    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"


class ReportStatus(enum.Enum):
    """报表状态"""
    PENDING = "pending"         # 待生成
    GENERATING = "generating"   # 生成中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 生成失败


class Report(db.Model):
    """报表记录表"""
    __tablename__ = 'dashboard_reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_no = db.Column(db.String(50), unique=True, nullable=False, comment='报表编号')
    report_type = db.Column(db.String(50), nullable=False, comment='报表类型')
    report_name = db.Column(db.String(200), nullable=False, comment='报表名称')

    # 数据范围
    date_range_start = db.Column(db.Date, nullable=True, comment='数据范围开始')
    date_range_end = db.Column(db.Date, nullable=True, comment='数据范围结束')

    # 筛选条件和数据快照
    filters = db.Column(db.JSON, nullable=True, comment='筛选条件')
    data_snapshot = db.Column(db.JSON, nullable=True, comment='数据快照')

    # 文件信息
    file_path = db.Column(db.String(500), nullable=True, comment='文件路径')
    file_format = db.Column(db.String(20), nullable=False, default='excel', comment='文件格式')
    file_size = db.Column(db.Integer, nullable=True, comment='文件大小(字节)')

    # 状态
    status = db.Column(db.String(20), nullable=False, default='pending', comment='状态')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')

    # 创建信息
    created_by = db.Column(db.Integer, nullable=True, comment='创建人ID')
    created_by_name = db.Column(db.String(100), nullable=True, comment='创建人姓名')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    completed_at = db.Column(db.DateTime, nullable=True, comment='完成时间')

    __table_args__ = (
        db.Index('idx_report_type', 'report_type'),
        db.Index('idx_report_status', 'status'),
        db.Index('idx_report_created_at', 'created_at'),
        db.Index('idx_report_created_by', 'created_by'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'report_no': self.report_no,
            'report_type': self.report_type,
            'report_name': self.report_name,
            'date_range_start': self.date_range_start.isoformat() if self.date_range_start else None,
            'date_range_end': self.date_range_end.isoformat() if self.date_range_end else None,
            'filters': self.filters,
            'file_path': self.file_path,
            'file_format': self.file_format,
            'file_size': self.file_size,
            'status': self.status,
            'error_message': self.error_message,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    @staticmethod
    def generate_report_no():
        """生成报表编号 RPT-YYYYMMDD-XXX"""
        today = datetime.now().strftime('%Y%m%d')
        prefix = f'RPT-{today}-'

        # 查询今天最大的编号
        last_report = Report.query.filter(
            Report.report_no.like(f'{prefix}%')
        ).order_by(Report.report_no.desc()).first()

        if last_report:
            try:
                last_num = int(last_report.report_no.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f'{prefix}{new_num:03d}'

    @staticmethod
    def get_report_type_label(report_type):
        """获取报表类型标签"""
        labels = {
            'production': '生产报表',
            'order': '订单报表',
            'task': '任务报表',
            'kpi': 'KPI综合报表',
            'custom': '自定义报表',
        }
        return labels.get(report_type, report_type)

    @staticmethod
    def get_format_label(file_format):
        """获取格式标签"""
        labels = {
            'excel': 'Excel (.xlsx)',
            'pdf': 'PDF',
            'csv': 'CSV',
        }
        return labels.get(file_format, file_format)
