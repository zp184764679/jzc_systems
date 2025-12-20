"""
InspectionCriteria 检验标准模型
"""
from datetime import datetime
from . import db


class InspectionCriteria(db.Model):
    """检验标准表"""
    __tablename__ = 'tdm_inspection_criteria'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(db.BigInteger, db.ForeignKey('tdm_product_master.id'), nullable=False, index=True)
    part_number = db.Column(db.String(100), nullable=False, index=True, comment='品番号(冗余)')

    # 标准基本信息
    criteria_code = db.Column(db.String(50), nullable=False, comment='检验标准编码')
    criteria_name = db.Column(db.String(200), nullable=False, comment='检验标准名称')

    # 检验阶段
    inspection_stage = db.Column(
        db.Enum('incoming', 'process', 'final', 'outgoing', name='inspection_stage'),
        index=True,
        comment='检验阶段: IQC/IPQC/FQC/OQC'
    )

    # 检验方式
    inspection_method = db.Column(
        db.Enum('full', 'sampling', 'skip', name='inspection_method'),
        default='sampling',
        comment='检验方式: 全检/抽检/免检'
    )
    sampling_plan = db.Column(db.String(100), comment='抽样方案 如 AQL 1.0')
    sample_size_formula = db.Column(db.String(200), comment='抽样数量公式')

    # 检验项目 (JSON数组)
    inspection_items = db.Column(db.JSON, comment='检验项目列表')
    """
    格式:
    [
        {
            "item_no": "01",
            "item_name": "外径",
            "specification": "Φ10 ±0.02",
            "method": "游标卡尺",
            "tool": "0-150mm卡尺",
            "upper_limit": 10.02,
            "lower_limit": 9.98,
            "unit": "mm",
            "is_critical": true,
            "sample_size": 5
        }
    ]
    """

    # AQL 标准
    aql_critical = db.Column(db.Numeric(5, 2), comment='致命缺陷AQL')
    aql_major = db.Column(db.Numeric(5, 2), comment='严重缺陷AQL')
    aql_minor = db.Column(db.Numeric(5, 2), comment='轻微缺陷AQL')

    # 关联 MES 检验标准
    mes_standard_id = db.Column(db.Integer, comment='MES系统检验标准ID')

    # 版本控制
    version = db.Column(db.String(20), default='1.0', nullable=False, comment='版本号')
    is_current = db.Column(db.Boolean, default=True, index=True, comment='是否当前版本')
    parent_version_id = db.Column(db.BigInteger, comment='上一版本ID')
    version_note = db.Column(db.Text, comment='版本说明')

    # 生效日期
    effective_date = db.Column(db.Date, comment='生效日期')
    expiry_date = db.Column(db.Date, comment='失效日期')

    # 状态
    status = db.Column(
        db.Enum('draft', 'active', 'deprecated', name='criteria_status'),
        default='draft',
        index=True,
        comment='状态'
    )

    # 审批信息
    approved_by = db.Column(db.Integer, comment='审批人ID')
    approved_by_name = db.Column(db.String(100), comment='审批人姓名')
    approved_at = db.Column(db.DateTime, comment='审批时间')

    # 审计字段
    created_by = db.Column(db.Integer, comment='创建人ID')
    created_by_name = db.Column(db.String(100), comment='创建人姓名')
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('criteria_code', 'version', name='uk_criteria_version'),
    )

    # 检验阶段显示名称
    STAGE_NAMES = {
        'incoming': {'zh': '来料检验 (IQC)', 'en': 'Incoming Quality Control'},
        'process': {'zh': '过程检验 (IPQC)', 'en': 'In-Process Quality Control'},
        'final': {'zh': '最终检验 (FQC)', 'en': 'Final Quality Control'},
        'outgoing': {'zh': '出货检验 (OQC)', 'en': 'Outgoing Quality Control'},
    }

    def to_dict(self):
        """转换为字典"""
        stage_info = self.STAGE_NAMES.get(self.inspection_stage, {})
        return {
            'id': self.id,
            'product_id': self.product_id,
            'part_number': self.part_number,
            'criteria_code': self.criteria_code,
            'criteria_name': self.criteria_name,
            'inspection_stage': self.inspection_stage,
            'inspection_stage_name': stage_info.get('zh', self.inspection_stage),
            'inspection_method': self.inspection_method,
            'sampling_plan': self.sampling_plan,
            'sample_size_formula': self.sample_size_formula,
            'inspection_items': self.inspection_items or [],
            'aql_critical': float(self.aql_critical) if self.aql_critical else None,
            'aql_major': float(self.aql_major) if self.aql_major else None,
            'aql_minor': float(self.aql_minor) if self.aql_minor else None,
            'mes_standard_id': self.mes_standard_id,
            'version': self.version,
            'is_current': self.is_current,
            'parent_version_id': self.parent_version_id,
            'version_note': self.version_note,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_by_name': self.approved_by_name,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<InspectionCriteria {self.criteria_code} v{self.version}>'
