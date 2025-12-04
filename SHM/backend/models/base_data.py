from extensions import db
from datetime import datetime


class ShipmentStatus(db.Model):
    """出货状态"""
    __tablename__ = 'shm_shipment_statuses'

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


class ShippingMethod(db.Model):
    """运输方式"""
    __tablename__ = 'shm_shipping_methods'

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


class PackagingType(db.Model):
    """包装类型"""
    __tablename__ = 'shm_packaging_types'

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


class PackagingMaterial(db.Model):
    """包装材料"""
    __tablename__ = 'shm_packaging_materials'

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


class Warehouse(db.Model):
    """仓库"""
    __tablename__ = 'shm_warehouses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'address': self.address, 'description': self.description,
            'is_active': self.is_active, 'sort_order': self.sort_order
        }


class UnitOfMeasure(db.Model):
    """计量单位"""
    __tablename__ = 'shm_units_of_measure'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name,
            'symbol': self.symbol, 'description': self.description,
            'is_active': self.is_active, 'sort_order': self.sort_order
        }
