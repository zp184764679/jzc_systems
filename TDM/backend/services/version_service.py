"""
版本控制服务
"""
from models import db


class VersionService:
    """版本控制服务"""

    @staticmethod
    def increment_version(current_version: str) -> str:
        """
        增加版本号
        1.0 -> 1.1
        1.9 -> 1.10
        """
        try:
            parts = current_version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            return f"{major}.{minor + 1}"
        except:
            return "1.1"

    @staticmethod
    def increment_major_version(current_version: str) -> str:
        """
        增加主版本号
        1.5 -> 2.0
        """
        try:
            parts = current_version.split('.')
            major = int(parts[0])
            return f"{major + 1}.0"
        except:
            return "2.0"

    @staticmethod
    def compare_versions(v1: str, v2: str) -> int:
        """
        比较版本号
        返回: -1 (v1 < v2), 0 (v1 == v2), 1 (v1 > v2)
        """
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]

            # 补齐长度
            while len(parts1) < len(parts2):
                parts1.append(0)
            while len(parts2) < len(parts1):
                parts2.append(0)

            for p1, p2 in zip(parts1, parts2):
                if p1 < p2:
                    return -1
                elif p1 > p2:
                    return 1
            return 0
        except:
            return 0

    @staticmethod
    def get_version_history(model_class, product_id: int, identifier_field: str = None, identifier_value: str = None):
        """
        获取版本历史

        Args:
            model_class: 模型类 (TechnicalSpec, InspectionCriteria, ProcessDocument)
            product_id: 产品ID
            identifier_field: 标识字段名 (如 criteria_code, process_code)
            identifier_value: 标识字段值

        Returns:
            版本历史列表
        """
        query = model_class.query.filter_by(product_id=product_id)

        if identifier_field and identifier_value:
            query = query.filter(getattr(model_class, identifier_field) == identifier_value)

        versions = query.order_by(model_class.version.desc()).all()

        return [{
            'id': v.id,
            'version': v.version,
            'is_current': v.is_current,
            'version_note': getattr(v, 'version_note', None),
            'created_by_name': getattr(v, 'created_by_name', None),
            'created_at': v.created_at.isoformat() if v.created_at else None
        } for v in versions]

    @staticmethod
    def set_current_version(model_class, product_id: int, version_id: int, identifier_field: str = None, identifier_value: str = None):
        """
        设置当前版本

        Args:
            model_class: 模型类
            product_id: 产品ID
            version_id: 要设置为当前版本的记录ID
            identifier_field: 标识字段名
            identifier_value: 标识字段值
        """
        # 将所有版本标记为非当前
        query = model_class.query.filter_by(product_id=product_id)
        if identifier_field and identifier_value:
            query = query.filter(getattr(model_class, identifier_field) == identifier_value)
        query.update({'is_current': False})

        # 将指定版本设置为当前
        target = model_class.query.get(version_id)
        if target:
            target.is_current = True

        db.session.commit()

        return target
