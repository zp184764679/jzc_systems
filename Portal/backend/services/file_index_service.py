"""
FileIndexService - 文件中心索引服务
提供文件索引、查询、统计等功能
"""
import os
import hashlib
from datetime import datetime
from sqlalchemy import func, or_, and_, desc
from sqlalchemy.orm import Session
from models.file_index import FileIndex, FileStatus, FILE_CATEGORIES, SOURCE_SYSTEMS


class FileIndexService:
    """文件索引服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 索引管理 ====================

    def index_file(
        self,
        source_system: str,
        source_table: str,
        source_id: int,
        file_name: str,
        file_path: str,
        file_category: str = 'other',
        **kwargs
    ) -> FileIndex:
        """
        将文件添加到索引

        Args:
            source_system: 来源系统 (portal/caigou/quotation/...)
            source_table: 来源表名
            source_id: 来源记录ID
            file_name: 文件名
            file_path: 文件路径
            file_category: 文件分类
            **kwargs: 其他可选参数 (order_no, project_id, supplier_id, etc.)
        """
        # 检查是否已存在
        existing = self.db.query(FileIndex).filter(
            FileIndex.source_system == source_system,
            FileIndex.source_table == source_table,
            FileIndex.source_id == source_id
        ).first()

        if existing:
            # 更新已存在的索引
            return self.update_index(source_system, source_table, source_id, **{
                'file_name': file_name,
                'file_path': file_path,
                'file_category': file_category,
                **kwargs
            })

        # 提取文件扩展名
        file_extension = os.path.splitext(file_name)[1].lower().lstrip('.')

        # 创建新索引
        file_index = FileIndex(
            source_system=source_system,
            source_table=source_table,
            source_id=source_id,
            file_name=file_name,
            file_path=file_path,
            file_extension=file_extension,
            file_category=file_category,
            uploaded_at=datetime.now(),
            **kwargs
        )

        self.db.add(file_index)
        self.db.commit()
        self.db.refresh(file_index)

        return file_index

    def update_index(
        self,
        source_system: str,
        source_table: str,
        source_id: int,
        **updates
    ) -> FileIndex:
        """更新索引"""
        file_index = self.db.query(FileIndex).filter(
            FileIndex.source_system == source_system,
            FileIndex.source_table == source_table,
            FileIndex.source_id == source_id
        ).first()

        if not file_index:
            return None

        for key, value in updates.items():
            if hasattr(file_index, key) and value is not None:
                setattr(file_index, key, value)

        self.db.commit()
        self.db.refresh(file_index)

        return file_index

    def remove_from_index(
        self,
        source_system: str,
        source_table: str,
        source_id: int,
        soft_delete: bool = True
    ) -> bool:
        """从索引中移除文件"""
        file_index = self.db.query(FileIndex).filter(
            FileIndex.source_system == source_system,
            FileIndex.source_table == source_table,
            FileIndex.source_id == source_id
        ).first()

        if not file_index:
            return False

        if soft_delete:
            file_index.status = FileStatus.DELETED
            self.db.commit()
        else:
            self.db.delete(file_index)
            self.db.commit()

        return True

    def get_by_id(self, file_id: int) -> FileIndex:
        """根据ID获取文件"""
        return self.db.query(FileIndex).filter(
            FileIndex.id == file_id,
            FileIndex.status == FileStatus.ACTIVE
        ).first()

    def get_by_uuid(self, file_uuid: str) -> FileIndex:
        """根据UUID获取文件"""
        return self.db.query(FileIndex).filter(
            FileIndex.file_uuid == file_uuid,
            FileIndex.status == FileStatus.ACTIVE
        ).first()

    # ==================== 查询功能 ====================

    def search(
        self,
        query: str = None,
        filters: dict = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> dict:
        """
        搜索文件

        Args:
            query: 搜索关键词
            filters: 筛选条件 {
                'source_system': 来源系统,
                'file_category': 文件分类,
                'order_no': 订单号,
                'project_id': 项目ID,
                'project_no': 项目编号,
                'supplier_id': 供应商ID,
                'customer_id': 客户ID,
                'part_number': 品番号,
                'po_number': PO号,
                'start_date': 开始日期,
                'end_date': 结束日期,
            }
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
        """
        filters = filters or {}

        # 基础查询
        base_query = self.db.query(FileIndex).filter(
            FileIndex.status == FileStatus.ACTIVE
        )

        # 关键词搜索
        if query:
            search_pattern = f"%{query}%"
            base_query = base_query.filter(
                or_(
                    FileIndex.file_name.like(search_pattern),
                    FileIndex.order_no.like(search_pattern),
                    FileIndex.project_no.like(search_pattern),
                    FileIndex.supplier_name.like(search_pattern),
                    FileIndex.customer_name.like(search_pattern),
                    FileIndex.part_number.like(search_pattern),
                    FileIndex.po_number.like(search_pattern),
                )
            )

        # 应用筛选条件
        if filters.get('source_system'):
            systems = filters['source_system']
            if isinstance(systems, str):
                systems = [systems]
            base_query = base_query.filter(FileIndex.source_system.in_(systems))

        if filters.get('file_category'):
            categories = filters['file_category']
            if isinstance(categories, str):
                categories = [categories]
            base_query = base_query.filter(FileIndex.file_category.in_(categories))

        if filters.get('order_no'):
            base_query = base_query.filter(FileIndex.order_no == filters['order_no'])

        if filters.get('project_id'):
            base_query = base_query.filter(FileIndex.project_id == filters['project_id'])

        if filters.get('project_no'):
            base_query = base_query.filter(FileIndex.project_no == filters['project_no'])

        if filters.get('supplier_id'):
            base_query = base_query.filter(FileIndex.supplier_id == filters['supplier_id'])

        if filters.get('customer_id'):
            base_query = base_query.filter(FileIndex.customer_id == filters['customer_id'])

        if filters.get('part_number'):
            base_query = base_query.filter(FileIndex.part_number.like(f"%{filters['part_number']}%"))

        if filters.get('po_number'):
            base_query = base_query.filter(FileIndex.po_number.like(f"%{filters['po_number']}%"))

        if filters.get('start_date'):
            base_query = base_query.filter(FileIndex.uploaded_at >= filters['start_date'])

        if filters.get('end_date'):
            base_query = base_query.filter(FileIndex.uploaded_at <= filters['end_date'])

        # 统计总数
        total = base_query.count()

        # 排序
        sort_column = getattr(FileIndex, sort_by, FileIndex.created_at)
        if sort_order == 'desc':
            base_query = base_query.order_by(desc(sort_column))
        else:
            base_query = base_query.order_by(sort_column)

        # 分页
        offset = (page - 1) * page_size
        items = base_query.offset(offset).limit(page_size).all()

        return {
            'items': [item.to_dict() for item in items],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }

    def get_by_order(self, order_no: str) -> list:
        """按订单号获取文件列表"""
        files = self.db.query(FileIndex).filter(
            FileIndex.order_no == order_no,
            FileIndex.status == FileStatus.ACTIVE
        ).order_by(desc(FileIndex.uploaded_at)).all()

        return [f.to_dict() for f in files]

    def get_by_project(self, project_no: str = None, project_id: int = None) -> list:
        """按项目获取文件列表"""
        query = self.db.query(FileIndex).filter(
            FileIndex.status == FileStatus.ACTIVE
        )

        if project_no:
            query = query.filter(FileIndex.project_no == project_no)
        elif project_id:
            query = query.filter(FileIndex.project_id == project_id)
        else:
            return []

        files = query.order_by(desc(FileIndex.uploaded_at)).all()
        return [f.to_dict() for f in files]

    def get_by_supplier(self, supplier_id: int) -> list:
        """按供应商获取文件列表"""
        files = self.db.query(FileIndex).filter(
            FileIndex.supplier_id == supplier_id,
            FileIndex.status == FileStatus.ACTIVE
        ).order_by(desc(FileIndex.uploaded_at)).all()

        return [f.to_dict() for f in files]

    def get_by_customer(self, customer_id: int) -> list:
        """按客户获取文件列表"""
        files = self.db.query(FileIndex).filter(
            FileIndex.customer_id == customer_id,
            FileIndex.status == FileStatus.ACTIVE
        ).order_by(desc(FileIndex.uploaded_at)).all()

        return [f.to_dict() for f in files]

    # ==================== 统计功能 ====================

    def get_statistics(self, filters: dict = None) -> dict:
        """获取文件统计信息"""
        filters = filters or {}

        base_query = self.db.query(FileIndex).filter(
            FileIndex.status == FileStatus.ACTIVE
        )

        # 应用筛选条件
        if filters.get('source_system'):
            base_query = base_query.filter(FileIndex.source_system == filters['source_system'])
        if filters.get('project_id'):
            base_query = base_query.filter(FileIndex.project_id == filters['project_id'])
        if filters.get('supplier_id'):
            base_query = base_query.filter(FileIndex.supplier_id == filters['supplier_id'])

        # 总文件数
        total_files = base_query.count()

        # 总文件大小
        total_size = base_query.with_entities(func.sum(FileIndex.file_size)).scalar() or 0

        # 按分类统计
        category_stats = self.db.query(
            FileIndex.file_category,
            func.count(FileIndex.id).label('count'),
            func.sum(FileIndex.file_size).label('size')
        ).filter(
            FileIndex.status == FileStatus.ACTIVE
        ).group_by(FileIndex.file_category).all()

        categories = {}
        for cat, count, size in category_stats:
            cat_info = FILE_CATEGORIES.get(cat, FILE_CATEGORIES['other'])
            categories[cat] = {
                'count': count,
                'size': size or 0,
                'name': cat_info['zh'],
                'icon': cat_info['icon']
            }

        # 按系统统计
        system_stats = self.db.query(
            FileIndex.source_system,
            func.count(FileIndex.id).label('count'),
            func.sum(FileIndex.file_size).label('size')
        ).filter(
            FileIndex.status == FileStatus.ACTIVE
        ).group_by(FileIndex.source_system).all()

        systems = {}
        for sys, count, size in system_stats:
            sys_info = SOURCE_SYSTEMS.get(sys, {'zh': sys, 'en': sys})
            systems[sys] = {
                'count': count,
                'size': size or 0,
                'name': sys_info['zh']
            }

        # 本月上传统计
        today = datetime.now()
        month_start = datetime(today.year, today.month, 1)
        month_uploads = self.db.query(func.count(FileIndex.id)).filter(
            FileIndex.status == FileStatus.ACTIVE,
            FileIndex.uploaded_at >= month_start
        ).scalar() or 0

        return {
            'total_files': total_files,
            'total_size': total_size,
            'month_uploads': month_uploads,
            'categories': categories,
            'systems': systems,
        }

    def get_categories(self) -> list:
        """获取所有文件分类"""
        return [
            {
                'code': code,
                'name_zh': info['zh'],
                'name_ja': info['ja'],
                'name_en': info['en'],
                'icon': info['icon']
            }
            for code, info in FILE_CATEGORIES.items()
        ]

    def get_source_systems(self) -> list:
        """获取所有来源系统"""
        return [
            {
                'code': code,
                'name_zh': info['zh'],
                'name_en': info['en']
            }
            for code, info in SOURCE_SYSTEMS.items()
        ]


# 便捷函数
def get_file_index_service(db: Session) -> FileIndexService:
    """获取文件索引服务实例"""
    return FileIndexService(db)
