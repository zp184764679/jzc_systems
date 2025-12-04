from database import db
from datetime import datetime


class WorkOrderStatus(db.Model):
    """工单状态"""
    __tablename__ = 'mes_work_order_statuses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'color': self.color, 'description': self.description,
            'is_active': self.is_active, 'sort_order': self.sort_order
        }


class SourceType(db.Model):
    """来源类型"""
    __tablename__ = 'mes_source_types'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'description': self.description, 'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class InspectionType(db.Model):
    """检验类型"""
    __tablename__ = 'mes_inspection_types'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'description': self.description, 'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class InspectionResult(db.Model):
    """检验结果"""
    __tablename__ = 'mes_inspection_results'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'color': self.color, 'description': self.description,
            'is_active': self.is_active, 'sort_order': self.sort_order
        }


class DispositionType(db.Model):
    """处置类型"""
    __tablename__ = 'mes_disposition_types'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'description': self.description, 'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class ProductionLine(db.Model):
    """生产线"""
    __tablename__ = 'mes_production_lines'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'location': self.location, 'capacity': self.capacity,
            'description': self.description, 'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class WorkCenter(db.Model):
    """工作中心"""
    __tablename__ = 'mes_work_centers'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    production_line_id = db.Column(db.Integer, db.ForeignKey('mes_production_lines.id'))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    production_line = db.relationship('ProductionLine', backref='work_centers')

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'production_line_id': self.production_line_id,
            'production_line_name': self.production_line.name if self.production_line else None,
            'description': self.description, 'is_active': self.is_active,
            'sort_order': self.sort_order
        }
