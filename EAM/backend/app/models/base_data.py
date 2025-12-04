from app import db
from datetime import datetime


class EquipmentStatus(db.Model):
    """设备状态"""
    __tablename__ = 'equipment_statuses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class FactoryLocation(db.Model):
    """工厂位置"""
    __tablename__ = 'factory_locations'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'address': self.address,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class EquipmentGroup(db.Model):
    """设备组/生产线"""
    __tablename__ = 'equipment_groups'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class Brand(db.Model):
    """品牌"""
    __tablename__ = 'brands'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'country': self.country,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }


class StoragePlace(db.Model):
    """存放位置"""
    __tablename__ = 'storage_places'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    factory_location_id = db.Column(db.Integer, db.ForeignKey('factory_locations.id'))
    building = db.Column(db.String(50))
    floor = db.Column(db.String(20))
    area = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    factory_location = db.relationship('FactoryLocation', backref='storage_places')

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'factory_location_id': self.factory_location_id,
            'factory_location_name': self.factory_location.name if self.factory_location else None,
            'building': self.building,
            'floor': self.floor,
            'area': self.area,
            'description': self.description,
            'is_active': self.is_active,
            'sort_order': self.sort_order
        }
