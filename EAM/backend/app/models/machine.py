# -*- coding: utf-8 -*-
# app/models/machine.py
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlalchemy import UniqueConstraint
from .. import db


class Machine(db.Model):
    __tablename__ = "machines"
    __table_args__ = (
        db.UniqueConstraint("machine_code", name="uq_machines_machine_code"),
        {"extend_existing": True},
    )
    id = db.Column(db.Integer, primary_key=True)

    # 核心字段
    machine_code   = db.Column(db.String(64),  nullable=False)   # 设备编码（唯一）
    name           = db.Column(db.String(128), nullable=False)   # 设备名称
    model          = db.Column(db.String(128))                   # 型号
    group          = db.Column(db.String(64))                    # 设备分组/产线
    dept_name      = db.Column(db.String(64))                    # 部门
    sub_dept_name  = db.Column(db.String(64))                    # 子部门/班组
    is_active      = db.Column(db.Boolean, default=True)         # 是否在用

    # 扩展信息
    factory_location = db.Column(db.String(16))                  # 工厂所在地：深圳/东莞
    brand            = db.Column(db.String(64))                  # 品牌
    serial_no        = db.Column(db.String(64))                  # 出厂编号/序列号
    manufacture_date = db.Column(db.Date)                        # 出厂日期
    purchase_date    = db.Column(db.Date)                        # 购入日期
    place            = db.Column(db.String(128))                 # 放置场所
    manufacturer     = db.Column(db.String(128))                 # 生产厂商/制造商
    capacity         = db.Column(db.Integer)                     # 产能（件/天）
    status           = db.Column(db.String(16))                  # 在用/停用/维修等

    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 序列化
    @staticmethod
    def _date_to_str(d: Optional[date]) -> Optional[str]:
        return d.isoformat() if d else None

    def to_dict(self) -> Dict[str, Any]:
        """统一的返回结构；含常见别名，方便前端兼容显示。"""
        return {
            "id": self.id,

            # 主键/编码
            "machine_code": self.machine_code,
            "code": self.machine_code,   # 别名

            # 基本信息
            "name": self.name,
            "model": self.model,
            "group": self.group,
            "dept_name": self.dept_name,
            "sub_dept_name": self.sub_dept_name,
            "is_active": bool(self.is_active),

            # 扩展信息（含部分别名）
            "factory_location": self.factory_location,
            "factory_loc": self.factory_location,
            "brand": self.brand,
            "brand_name": self.brand,
            "brandName": self.brand,
            "serial_no": self.serial_no,
            "serialNo": self.serial_no,
            "sn": self.serial_no,
            "manufacture_date": self._date_to_str(self.manufacture_date),
            "mfg_date": self._date_to_str(self.manufacture_date),
            "purchase_date": self._date_to_str(self.purchase_date),
            "buy_date": self._date_to_str(self.purchase_date),
            "place": self.place,
            "manufacturer": self.manufacturer,
            "capacity": self.capacity,
            "status": self.status,

            # 时间戳
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
