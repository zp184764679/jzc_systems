"""
ProductFileLink 产品-文件关联模型
"""
from datetime import datetime
from . import db


class ProductFileLink(db.Model):
    """产品-文件关联表"""
    __tablename__ = 'tdm_product_file_links'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    product_id = db.Column(db.BigInteger, db.ForeignKey('tdm_product_master.id'), nullable=False, index=True)
    part_number = db.Column(db.String(100), nullable=False, index=True, comment='品番号(冗余)')

    # 文件关联 (FileIndex)
    file_index_id = db.Column(db.BigInteger, nullable=False, index=True, comment='FileIndex表ID')
    file_uuid = db.Column(db.String(32), comment='FileIndex UUID(冗余)')

    # 文件分类
    file_type = db.Column(
        db.Enum('drawing', 'specification', 'inspection_standard',
                'work_instruction', 'process_sheet', 'photo', 'certificate',
                'report', 'contract', 'other', name='file_type'),
        nullable=False,
        index=True,
        comment='文件类型'
    )

    # 文件信息 (冗余，便于显示)
    file_name = db.Column(db.String(255), comment='文件名')
    file_category = db.Column(db.String(64), comment='FileIndex分类')

    # 显示控制
    is_primary = db.Column(db.Boolean, default=False, comment='是否主文件')
    display_order = db.Column(db.Integer, default=0, comment='显示顺序')
    description = db.Column(db.String(500), comment='文件描述')

    # 审计字段
    linked_by = db.Column(db.Integer, comment='关联人ID')
    linked_by_name = db.Column(db.String(100), comment='关联人姓名')
    linked_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    # 文件类型显示名称
    FILE_TYPE_NAMES = {
        'drawing': {'zh': '图纸', 'ja': '図面', 'en': 'Drawing'},
        'specification': {'zh': '规格书', 'ja': '仕様書', 'en': 'Specification'},
        'inspection_standard': {'zh': '检验标准', 'ja': '検査基準書', 'en': 'Inspection Standard'},
        'work_instruction': {'zh': '作业指导书', 'ja': '作業標準書', 'en': 'Work Instruction'},
        'process_sheet': {'zh': '工程表', 'ja': '工程表', 'en': 'Process Sheet'},
        'photo': {'zh': '照片', 'ja': '写真', 'en': 'Photo'},
        'certificate': {'zh': '证书', 'ja': '証明書', 'en': 'Certificate'},
        'report': {'zh': '报告', 'ja': 'レポート', 'en': 'Report'},
        'contract': {'zh': '合同', 'ja': '契約書', 'en': 'Contract'},
        'other': {'zh': '其他', 'ja': 'その他', 'en': 'Other'},
    }

    def to_dict(self):
        """转换为字典"""
        type_info = self.FILE_TYPE_NAMES.get(self.file_type, {})
        return {
            'id': self.id,
            'product_id': self.product_id,
            'part_number': self.part_number,
            'file_index_id': self.file_index_id,
            'file_uuid': self.file_uuid,
            'file_type': self.file_type,
            'file_type_name': type_info.get('zh', self.file_type),
            'file_type_ja': type_info.get('ja', ''),
            'file_name': self.file_name,
            'file_category': self.file_category,
            'is_primary': self.is_primary,
            'display_order': self.display_order,
            'description': self.description,
            'linked_by': self.linked_by,
            'linked_by_name': self.linked_by_name,
            'linked_at': self.linked_at.isoformat() if self.linked_at else None,
        }

    def __repr__(self):
        return f'<ProductFileLink {self.part_number} -> {self.file_index_id}>'
