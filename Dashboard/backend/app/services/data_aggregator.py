"""
数据聚合服务
从各个子系统收集和整合数据，为时间轴提供统一的数据源
"""

from datetime import datetime, timedelta
from sqlalchemy import text
from app import db


class DataAggregator:
    """数据聚合器 - 从各模块收集数据"""

    def __init__(self):
        # 跨系统API配置（如果需要通过API获取）
        self.api_urls = {
            'quotation': 'http://localhost:8001',
            'crm': 'http://localhost:8002',
            'hr': 'http://localhost:8003',
            'caigou': 'http://localhost:5001',
            'shm': 'http://localhost:8006'
        }

    def get_order_full_lifecycle(self, order_no):
        """
        获取订单完整生命周期数据
        整合报价、订单、生产、出货等各阶段数据
        """
        lifecycle = {
            'order_no': order_no,
            'stages': [],
            'timeline_items': []
        }

        # 1. 尝试获取报价数据
        quote_data = self._get_quote_data(order_no)
        if quote_data:
            lifecycle['stages'].append({
                'stage': 'quote',
                'name': '报价阶段',
                'data': quote_data,
                'status': quote_data.get('status', 'completed')
            })
            lifecycle['timeline_items'].append(self._convert_to_timeline_item(
                'quote', quote_data, order_no
            ))

        # 2. 获取订单数据（CRM）
        order_data = self._get_order_data(order_no)
        if order_data:
            lifecycle['stages'].append({
                'stage': 'order',
                'name': '订单确认',
                'data': order_data,
                'status': order_data.get('status', 'confirmed')
            })
            lifecycle['timeline_items'].append(self._convert_to_timeline_item(
                'order', order_data, order_no
            ))

        # 3. 获取采购数据
        procurement_data = self._get_procurement_data(order_no)
        if procurement_data:
            for pr in procurement_data:
                lifecycle['stages'].append({
                    'stage': 'procurement',
                    'name': f'采购 - {pr.get("pr_number")}',
                    'data': pr,
                    'status': pr.get('status', 'pending')
                })
                lifecycle['timeline_items'].append(self._convert_to_timeline_item(
                    'procurement', pr, order_no
                ))

        # 4. 获取生产数据
        production_data = self._get_production_data(order_no)
        if production_data:
            lifecycle['stages'].append({
                'stage': 'production',
                'name': '生产制造',
                'data': production_data,
                'status': production_data.get('status', 'in_progress')
            })
            lifecycle['timeline_items'].extend(
                self._convert_production_to_timeline(production_data, order_no)
            )

        # 5. 获取出货数据
        shipment_data = self._get_shipment_data(order_no)
        if shipment_data:
            for shipment in shipment_data:
                lifecycle['stages'].append({
                    'stage': 'shipment',
                    'name': f'出货 - {shipment.get("shipment_no")}',
                    'data': shipment,
                    'status': shipment.get('status', 'pending')
                })
                lifecycle['timeline_items'].append(self._convert_to_timeline_item(
                    'shipment', shipment, order_no
                ))

        return lifecycle

    def _get_quote_data(self, order_no):
        """从报价系统获取报价数据"""
        try:
            # 直接查询数据库（假设报价表存在）
            result = db.session.execute(text("""
                SELECT id, quote_number, customer_name, product_name,
                       created_at, updated_at, status
                FROM quotes
                WHERE order_no = :order_no OR quote_number LIKE :pattern
                LIMIT 1
            """), {'order_no': order_no, 'pattern': f'%{order_no}%'})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
        except Exception as e:
            print(f"获取报价数据失败: {e}")
        return None

    def _get_order_data(self, order_no):
        """从CRM获取订单数据"""
        try:
            result = db.session.execute(text("""
                SELECT id, order_no, customer_name, product,
                       order_date, delivery_date, status, order_qty
                FROM `order`
                WHERE order_no = :order_no
                LIMIT 1
            """), {'order_no': order_no})
            row = result.fetchone()
            if row:
                return dict(row._mapping)
        except Exception as e:
            print(f"获取订单数据失败: {e}")
        return None

    def _get_procurement_data(self, order_no):
        """从采购系统获取采购数据"""
        try:
            result = db.session.execute(text("""
                SELECT id, pr_number, description, status,
                       created_at, total_amount
                FROM purchase_requests
                WHERE description LIKE :pattern
            """), {'pattern': f'%{order_no}%'})
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            print(f"获取采购数据失败: {e}")
        return []

    def _get_production_data(self, order_no):
        """从Dashboard本身获取生产数据"""
        from app.models import ProductionPlan, ProductionStep

        plan = ProductionPlan.query.filter_by(order_no=order_no).first()
        if plan:
            steps = ProductionStep.query.filter_by(plan_id=plan.id).order_by(
                ProductionStep.step_sequence
            ).all()
            return {
                'plan': plan.to_dict(),
                'steps': [s.to_dict() for s in steps]
            }
        return None

    def _get_shipment_data(self, order_no):
        """从SHM获取出货数据"""
        try:
            result = db.session.execute(text("""
                SELECT id, shipment_no, customer_name, status,
                       delivery_date, created_at
                FROM shipments
                WHERE order_no = :order_no
            """), {'order_no': order_no})
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            print(f"获取出货数据失败: {e}")
        return []

    def _convert_to_timeline_item(self, stage_type, data, order_no):
        """将各阶段数据转换为统一的时间轴格式"""
        now = datetime.now()

        type_config = {
            'quote': {
                'color': '#722ed1',
                'icon': 'FileTextOutlined',
                'duration_days': 3
            },
            'order': {
                'color': '#1890ff',
                'icon': 'ShoppingCartOutlined',
                'duration_days': 1
            },
            'procurement': {
                'color': '#fa8c16',
                'icon': 'ShoppingOutlined',
                'duration_days': 7
            },
            'production': {
                'color': '#52c41a',
                'icon': 'ToolOutlined',
                'duration_days': 14
            },
            'shipment': {
                'color': '#13c2c2',
                'icon': 'CarOutlined',
                'duration_days': 2
            }
        }

        config = type_config.get(stage_type, {})

        # 确定时间
        start_time = data.get('created_at') or data.get('order_date') or now
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

        end_time = data.get('delivery_date') or data.get('updated_at') or (
            start_time + timedelta(days=config.get('duration_days', 1))
        )
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

        return {
            'id': f'{stage_type}-{data.get("id", 0)}',
            'group': f'order-{order_no}',
            'title': self._get_stage_title(stage_type, data),
            'start_time': int(start_time.timestamp() * 1000),
            'end_time': int(end_time.timestamp() * 1000),
            'type': stage_type,
            'status': data.get('status', 'pending'),
            'color': config.get('color'),
            'metadata': data
        }

    def _get_stage_title(self, stage_type, data):
        """获取阶段标题"""
        titles = {
            'quote': f"报价 {data.get('quote_number', '')}",
            'order': f"订单 {data.get('order_no', '')}",
            'procurement': f"采购 {data.get('pr_number', '')}",
            'production': f"生产 {data.get('plan', {}).get('plan_no', '')}",
            'shipment': f"出货 {data.get('shipment_no', '')}"
        }
        return titles.get(stage_type, stage_type)

    def _convert_production_to_timeline(self, production_data, order_no):
        """将生产数据（包含工序）转换为时间轴项目"""
        items = []

        plan = production_data.get('plan', {})
        steps = production_data.get('steps', [])

        # 添加生产计划整体
        if plan:
            items.append({
                'id': f"production-{plan.get('id')}",
                'group': f'order-{order_no}',
                'title': f"生产 - {plan.get('product_name', '')}",
                'start_time': int(datetime.fromisoformat(plan['plan_start_date']).timestamp() * 1000) if plan.get('plan_start_date') else None,
                'end_time': int(datetime.fromisoformat(plan['plan_end_date']).timestamp() * 1000) if plan.get('plan_end_date') else None,
                'type': 'production',
                'status': plan.get('status'),
                'progress': plan.get('progress_percentage', 0),
                'color': '#52c41a'
            })

        # 添加各工序
        for step in steps:
            items.append({
                'id': f"step-{step.get('id')}",
                'group': f'order-{order_no}',
                'title': step.get('step_name'),
                'start_time': int(datetime.fromisoformat(step['plan_start']).timestamp() * 1000) if step.get('plan_start') else None,
                'end_time': int(datetime.fromisoformat(step['plan_end']).timestamp() * 1000) if step.get('plan_end') else None,
                'type': 'step',
                'status': step.get('status'),
                'progress': step.get('completion_rate', 0),
                'sequence': step.get('step_sequence')
            })

        return items

    def aggregate_timeline_data(self, view_type, start_date, end_date, filters=None):
        """
        聚合时间轴数据（主入口方法）
        """
        from app.models import ProductionPlan

        # 获取生产计划数据
        query = ProductionPlan.query

        if start_date and end_date:
            query = query.filter(
                ProductionPlan.plan_start_date >= start_date,
                ProductionPlan.plan_end_date <= end_date
            )

        if filters:
            if filters.get('customer_id'):
                query = query.filter(ProductionPlan.customer_id == filters['customer_id'])
            if filters.get('status'):
                query = query.filter(ProductionPlan.status == filters['status'])
            if filters.get('department'):
                query = query.filter(ProductionPlan.department == filters['department'])

        plans = query.all()

        groups = []
        items = []
        group_set = set()

        for plan in plans:
            # 生成分组
            if view_type == 'customer':
                group_id = f'customer-{plan.customer_id}'
                group_title = plan.customer_name or f'客户 {plan.customer_id}'
            elif view_type == 'department':
                group_id = f'dept-{plan.department}' if plan.department else 'dept-unassigned'
                group_title = plan.department or '未分配'
            else:  # order
                group_id = f'order-{plan.order_id}'
                group_title = plan.order_no or f'订单 {plan.order_id}'

            if group_id not in group_set:
                group_set.add(group_id)
                groups.append({
                    'id': group_id,
                    'title': group_title,
                    'type': view_type
                })

            # 生成时间轴项目
            item = plan.to_timeline_item()
            item['group'] = group_id
            items.append(item)

        return {
            'groups': groups,
            'items': items,
            'meta': {
                'total': len(items),
                'view_type': view_type
            }
        }
