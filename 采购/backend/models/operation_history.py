# models/operation_history.py
# -*- coding: utf-8 -*-
"""
操作历史记录模型

用于记录所有业务操作，支持追溯审计。
"""

from datetime import datetime
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR, TEXT
from extensions import db


class OperationHistory(db.Model):
    """操作历史记录"""
    __tablename__ = "operation_history"

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 系统和模块
    system = db.Column(VARCHAR(50), nullable=False, index=True, comment='系统标识')
    module = db.Column(VARCHAR(100), nullable=False, index=True, comment='模块名称')
    action = db.Column(VARCHAR(100), nullable=False, index=True, comment='操作类型')

    # 操作目标
    target_type = db.Column(VARCHAR(100), nullable=True, comment='目标类型')
    target_id = db.Column(VARCHAR(100), nullable=True, index=True, comment='目标ID')
    target_name = db.Column(VARCHAR(255), nullable=True, comment='目标名称')

    # 操作人
    operator_id = db.Column(BIGINT(unsigned=True), nullable=True, index=True, comment='操作人ID')
    operator_name = db.Column(VARCHAR(100), nullable=True, comment='操作人姓名')
    operator_role = db.Column(VARCHAR(50), nullable=True, comment='操作人角色')
    ip_address = db.Column(VARCHAR(50), nullable=True, comment='IP地址')

    # 数据变更
    old_value = db.Column(TEXT, nullable=True, comment='旧值（JSON）')
    new_value = db.Column(TEXT, nullable=True, comment='新值（JSON）')

    # 描述
    description = db.Column(TEXT, nullable=True, comment='操作描述')
    extra_data = db.Column(TEXT, nullable=True, comment='附加数据（JSON）')

    # 时间戳
    created_at = db.Column(DATETIME, default=datetime.utcnow, index=True, comment='创建时间')

    # 复合索引
    __table_args__ = (
        db.Index('idx_target', 'target_type', 'target_id'),
        {'comment': '操作历史记录'}
    )

    def __repr__(self):
        return f'<OperationHistory {self.id}: {self.system}.{self.module}.{self.action}>'

    @classmethod
    def log(
        cls,
        system: str,
        module: str,
        action: str,
        target_type: str = None,
        target_id=None,
        target_name: str = None,
        operator_id: int = None,
        operator_name: str = None,
        operator_role: str = None,
        ip_address: str = None,
        old_value: str = None,
        new_value: str = None,
        description: str = None,
        extra_data: str = None,
        commit: bool = True
    ):
        """
        记录操作历史

        Args:
            system: 系统标识 (caigou, quotation, hr, etc.)
            module: 模块名称 (pr, rfq, supplier, etc.)
            action: 操作类型 (create, update, delete, approve, etc.)
            其他参数...
            commit: 是否立即提交

        Returns:
            OperationHistory实例
        """
        import json

        # 自动生成描述
        if not description:
            action_labels = {
                "create": "创建",
                "update": "修改",
                "delete": "删除",
                "view": "查看",
                "submit": "提交",
                "approve": "审批通过",
                "reject": "驳回",
                "withdraw": "撤回",
                "forward": "转发",
                "upload": "上传文件",
                "download": "下载文件",
                "export": "导出",
                "import": "导入",
            }
            action_label = action_labels.get(action, action)
            if target_name:
                description = f"{action_label} {target_type or ''} {target_name}"
            elif target_id:
                description = f"{action_label} {target_type or ''} #{target_id}"
            else:
                description = f"{action_label}"

        record = cls(
            system=system,
            module=module,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            target_name=target_name,
            operator_id=operator_id,
            operator_name=operator_name,
            operator_role=operator_role,
            ip_address=ip_address,
            old_value=json.dumps(old_value, ensure_ascii=False, default=str) if old_value else None,
            new_value=json.dumps(new_value, ensure_ascii=False, default=str) if new_value else None,
            description=description,
            extra_data=json.dumps(extra_data, ensure_ascii=False, default=str) if extra_data else None
        )

        db.session.add(record)

        if commit:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"记录操作历史失败: {str(e)}")
                return None

        return record

    @classmethod
    def get_target_history(cls, target_type: str, target_id, limit: int = 100):
        """
        获取目标的操作历史

        Args:
            target_type: 目标类型
            target_id: 目标ID
            limit: 最大返回数量

        Returns:
            历史记录列表
        """
        return cls.query.filter_by(
            target_type=target_type,
            target_id=str(target_id)
        ).order_by(cls.created_at.desc()).limit(limit).all()

    def to_dict(self):
        """转换为字典"""
        import json

        return {
            "id": self.id,
            "system": self.system,
            "module": self.module,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "operator_id": self.operator_id,
            "operator_name": self.operator_name,
            "operator_role": self.operator_role,
            "ip_address": self.ip_address,
            "old_value": json.loads(self.old_value) if self.old_value else None,
            "new_value": json.loads(self.new_value) if self.new_value else None,
            "description": self.description,
            "extra_data": json.loads(self.extra_data) if self.extra_data else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
