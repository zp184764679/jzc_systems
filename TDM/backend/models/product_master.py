"""
ProductMaster 产品主数据模型
"""
from datetime import datetime
from . import db


class ProductMaster(db.Model):
    """产品主数据表"""
    __tablename__ = 'tdm_product_master'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    part_number = db.Column(db.String(100), unique=True, nullable=False, index=True, comment='品番号')
    product_name = db.Column(db.String(200), nullable=False, comment='产品名称')
    product_name_en = db.Column(db.String(200), comment='英文名称')
    product_name_ja = db.Column(db.String(200), comment='日文名称')

    # 客户信息
    customer_id = db.Column(db.Integer, index=True, comment='客户ID')
    customer_name = db.Column(db.String(200), comment='客户名称')
    customer_part_number = db.Column(db.String(100), comment='客户料号')

    # 分类
    category = db.Column(db.String(50), index=True, comment='产品分类')
    sub_category = db.Column(db.String(50), comment='子分类')

    # 状态
    status = db.Column(
        db.Enum('draft', 'active', 'discontinued', 'obsolete', name='product_status'),
        default='draft',
        nullable=False,
        index=True,
        comment='状态'
    )
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')

    # 关联报价系统
    quotation_product_id = db.Column(db.Integer, comment='报价系统产品ID')

    # 版本控制
    current_version = db.Column(db.String(20), default='1.0', comment='当前版本')

    # 描述
    description = db.Column(db.Text, comment='产品描述')
    remarks = db.Column(db.Text, comment='备注')

    # 审计字段
    created_by = db.Column(db.Integer, comment='创建人ID')
    created_by_name = db.Column(db.String(100), comment='创建人姓名')
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_by = db.Column(db.Integer, comment='更新人ID')
    updated_by_name = db.Column(db.String(100), comment='更新人姓名')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # 关系
    technical_specs = db.relationship('TechnicalSpec', backref='product', lazy='dynamic',
                                       cascade='all, delete-orphan')
    inspection_criteria = db.relationship('InspectionCriteria', backref='product', lazy='dynamic',
                                           cascade='all, delete-orphan')
    process_documents = db.relationship('ProcessDocument', backref='product', lazy='dynamic',
                                         cascade='all, delete-orphan')
    file_links = db.relationship('ProductFileLink', backref='product', lazy='dynamic',
                                  cascade='all, delete-orphan')

    def to_dict(self, include_relations=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'part_number': self.part_number,
            'product_name': self.product_name,
            'product_name_en': self.product_name_en,
            'product_name_ja': self.product_name_ja,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'customer_part_number': self.customer_part_number,
            'category': self.category,
            'sub_category': self.sub_category,
            'status': self.status,
            'is_active': self.is_active,
            'quotation_product_id': self.quotation_product_id,
            'current_version': self.current_version,
            'description': self.description,
            'remarks': self.remarks,
            'created_by': self.created_by,
            'created_by_name': self.created_by_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_by': self.updated_by,
            'updated_by_name': self.updated_by_name,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_relations:
            # 获取当前版本的技术规格
            current_spec = self.technical_specs.filter_by(is_current=True).first()
            data['current_tech_spec'] = current_spec.to_dict() if current_spec else None

            # 获取当前版本的检验标准
            current_inspections = self.inspection_criteria.filter_by(is_current=True).all()
            data['current_inspections'] = [i.to_dict() for i in current_inspections]

            # 获取当前版本的工艺文件
            current_processes = self.process_documents.filter_by(is_current=True).order_by('process_sequence').all()
            data['current_processes'] = [p.to_dict() for p in current_processes]

            # 获取关联文件数量
            data['file_count'] = self.file_links.count()

        return data

    def __repr__(self):
        return f'<ProductMaster {self.part_number}: {self.product_name}>'
