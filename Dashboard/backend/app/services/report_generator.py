"""
Report Generator Service - 报表生成服务
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app import db
from app.models import ProductionPlan, ProductionStep, Task


class ReportGenerator:
    """报表生成服务"""

    def generate_production_report(self, date_range, filters=None):
        """
        生成生产报表数据
        统计：计划数、完成数、完成率、延期数、各状态分布
        """
        filters = filters or {}
        start_date, end_date = self._parse_date_range(date_range)

        # 基础查询
        query = ProductionPlan.query.filter(
            and_(
                ProductionPlan.plan_start_date >= start_date,
                ProductionPlan.plan_start_date <= end_date
            )
        )

        # 应用筛选条件
        if filters.get('status'):
            if isinstance(filters['status'], list):
                query = query.filter(ProductionPlan.status.in_(filters['status']))
            else:
                query = query.filter(ProductionPlan.status == filters['status'])

        if filters.get('department'):
            query = query.filter(ProductionPlan.department == filters['department'])

        if filters.get('customer_id'):
            query = query.filter(ProductionPlan.customer_id == filters['customer_id'])

        plans = query.all()

        # 统计数据
        total_count = len(plans)
        completed_count = len([p for p in plans if p.status == 'completed'])
        in_progress_count = len([p for p in plans if p.status == 'in_progress'])
        delayed_count = len([p for p in plans if p.is_delayed])
        pending_count = len([p for p in plans if p.status == 'pending'])
        cancelled_count = len([p for p in plans if p.status == 'cancelled'])

        # 完成率
        completion_rate = round((completed_count / total_count * 100), 2) if total_count > 0 else 0

        # 数量统计
        total_plan_qty = sum(p.plan_quantity or 0 for p in plans)
        total_completed_qty = sum(p.completed_quantity or 0 for p in plans)
        total_defect_qty = sum(p.defect_quantity or 0 for p in plans)
        defect_rate = round((total_defect_qty / total_completed_qty * 100), 2) if total_completed_qty > 0 else 0

        # 按部门统计
        department_stats = {}
        for p in plans:
            dept = p.department or '未分配'
            if dept not in department_stats:
                department_stats[dept] = {'total': 0, 'completed': 0, 'delayed': 0}
            department_stats[dept]['total'] += 1
            if p.status == 'completed':
                department_stats[dept]['completed'] += 1
            if p.is_delayed:
                department_stats[dept]['delayed'] += 1

        # 状态分布
        status_distribution = [
            {'status': 'pending', 'label': '待开始', 'count': pending_count},
            {'status': 'in_progress', 'label': '进行中', 'count': in_progress_count},
            {'status': 'completed', 'label': '已完成', 'count': completed_count},
            {'status': 'delayed', 'label': '已延期', 'count': delayed_count},
            {'status': 'cancelled', 'label': '已取消', 'count': cancelled_count},
        ]

        # 明细数据
        details = [{
            'plan_no': p.plan_no,
            'order_no': p.order_no,
            'product_name': p.product_name,
            'department': p.department,
            'status': p.status,
            'plan_quantity': p.plan_quantity,
            'completed_quantity': p.completed_quantity,
            'defect_quantity': p.defect_quantity,
            'progress': p.progress_percentage,
            'plan_start_date': p.plan_start_date.isoformat() if p.plan_start_date else None,
            'plan_end_date': p.plan_end_date.isoformat() if p.plan_end_date else None,
            'is_delayed': p.is_delayed,
            'days_remaining': p.days_remaining,
        } for p in plans]

        return {
            'report_type': 'production',
            'report_name': '生产报表',
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_plans': total_count,
                'completed_plans': completed_count,
                'in_progress_plans': in_progress_count,
                'delayed_plans': delayed_count,
                'completion_rate': completion_rate,
                'total_plan_quantity': total_plan_qty,
                'total_completed_quantity': total_completed_qty,
                'total_defect_quantity': total_defect_qty,
                'defect_rate': defect_rate,
            },
            'status_distribution': status_distribution,
            'department_stats': [
                {'department': k, **v} for k, v in department_stats.items()
            ],
            'details': details
        }

    def generate_order_report(self, date_range, filters=None):
        """
        生成订单报表数据
        统计：订单数、客户分布、状态分布、交付趋势
        """
        filters = filters or {}
        start_date, end_date = self._parse_date_range(date_range)

        # 基础查询
        query = ProductionPlan.query.filter(
            and_(
                ProductionPlan.plan_start_date >= start_date,
                ProductionPlan.plan_start_date <= end_date
            )
        )

        if filters.get('customer_id'):
            query = query.filter(ProductionPlan.customer_id == filters['customer_id'])

        plans = query.all()

        # 按客户统计
        customer_stats = {}
        for p in plans:
            cid = p.customer_id or 0
            cname = p.customer_name or '未知客户'
            if cid not in customer_stats:
                customer_stats[cid] = {
                    'customer_id': cid,
                    'customer_name': cname,
                    'order_count': 0,
                    'total_quantity': 0,
                    'completed_quantity': 0,
                }
            customer_stats[cid]['order_count'] += 1
            customer_stats[cid]['total_quantity'] += p.plan_quantity or 0
            customer_stats[cid]['completed_quantity'] += p.completed_quantity or 0

        # 按日期统计交付趋势
        delivery_trend = {}
        for p in plans:
            if p.plan_end_date:
                date_key = p.plan_end_date.strftime('%Y-%m-%d')
                if date_key not in delivery_trend:
                    delivery_trend[date_key] = {'planned': 0, 'actual': 0}
                delivery_trend[date_key]['planned'] += 1
                if p.status == 'completed' and p.actual_end_date:
                    if p.actual_end_date <= p.plan_end_date:
                        delivery_trend[date_key]['actual'] += 1

        # 状态统计
        status_counts = {}
        for p in plans:
            status = p.status or 'unknown'
            status_counts[status] = status_counts.get(status, 0) + 1

        # 按日期排序交付趋势
        sorted_trend = sorted(delivery_trend.items(), key=lambda x: x[0])

        return {
            'report_type': 'order',
            'report_name': '订单报表',
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_orders': len(plans),
                'total_customers': len(customer_stats),
                'total_quantity': sum(p.plan_quantity or 0 for p in plans),
                'completed_quantity': sum(p.completed_quantity or 0 for p in plans),
            },
            'customer_ranking': sorted(
                customer_stats.values(),
                key=lambda x: x['order_count'],
                reverse=True
            )[:10],
            'status_distribution': [
                {'status': k, 'count': v} for k, v in status_counts.items()
            ],
            'delivery_trend': [
                {'date': k, 'planned': v['planned'], 'actual': v['actual']}
                for k, v in sorted_trend
            ]
        }

    def generate_task_report(self, date_range, filters=None):
        """
        生成任务报表数据
        统计：任务数、完成率、逾期率、部门/人员分布
        """
        filters = filters or {}
        start_date, end_date = self._parse_date_range(date_range)

        # 基础查询
        query = Task.query.filter(
            and_(
                Task.created_at >= start_date,
                Task.created_at <= end_date
            )
        )

        if filters.get('status'):
            if isinstance(filters['status'], list):
                query = query.filter(Task.status.in_(filters['status']))
            else:
                query = query.filter(Task.status == filters['status'])

        if filters.get('assigned_to'):
            query = query.filter(Task.assigned_to_user_id == filters['assigned_to'])

        if filters.get('department'):
            query = query.filter(Task.assigned_to_dept == filters['department'])

        tasks = query.all()

        # 统计
        total_count = len(tasks)
        completed_count = len([t for t in tasks if t.status == 'completed'])
        overdue_count = len([t for t in tasks if t.is_overdue])
        in_progress_count = len([t for t in tasks if t.status == 'in_progress'])
        pending_count = len([t for t in tasks if t.status == 'pending'])

        completion_rate = round((completed_count / total_count * 100), 2) if total_count > 0 else 0
        overdue_rate = round((overdue_count / total_count * 100), 2) if total_count > 0 else 0

        # 按部门统计
        dept_stats = {}
        for t in tasks:
            dept = t.assigned_to_dept or '未分配'
            if dept not in dept_stats:
                dept_stats[dept] = {'total': 0, 'completed': 0, 'overdue': 0}
            dept_stats[dept]['total'] += 1
            if t.status == 'completed':
                dept_stats[dept]['completed'] += 1
            if t.is_overdue:
                dept_stats[dept]['overdue'] += 1

        # 按人员统计
        assignee_stats = {}
        for t in tasks:
            aid = t.assigned_to_user_id or 0
            aname = t.assigned_to_name or '未分配'
            if aid not in assignee_stats:
                assignee_stats[aid] = {
                    'user_id': aid,
                    'name': aname,
                    'total': 0,
                    'completed': 0,
                    'overdue': 0
                }
            assignee_stats[aid]['total'] += 1
            if t.status == 'completed':
                assignee_stats[aid]['completed'] += 1
            if t.is_overdue:
                assignee_stats[aid]['overdue'] += 1

        # 按优先级统计
        priority_stats = {}
        for t in tasks:
            prio = t.priority or 'normal'
            priority_stats[prio] = priority_stats.get(prio, 0) + 1

        # 按类型统计
        type_stats = {}
        for t in tasks:
            ttype = t.task_type or 'other'
            type_stats[ttype] = type_stats.get(ttype, 0) + 1

        # 明细数据
        details = [{
            'task_no': t.task_no,
            'title': t.title,
            'task_type': t.task_type,
            'status': t.status,
            'priority': t.priority,
            'assigned_to': t.assigned_to_name,
            'department': t.assigned_to_dept,
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'is_overdue': t.is_overdue,
            'created_at': t.created_at.isoformat() if t.created_at else None,
        } for t in tasks]

        return {
            'report_type': 'task',
            'report_name': '任务报表',
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_tasks': total_count,
                'completed_tasks': completed_count,
                'in_progress_tasks': in_progress_count,
                'pending_tasks': pending_count,
                'overdue_tasks': overdue_count,
                'completion_rate': completion_rate,
                'overdue_rate': overdue_rate,
            },
            'department_stats': [
                {'department': k, **v} for k, v in dept_stats.items()
            ],
            'assignee_ranking': sorted(
                assignee_stats.values(),
                key=lambda x: x['completed'],
                reverse=True
            )[:10],
            'priority_distribution': [
                {'priority': k, 'count': v} for k, v in priority_stats.items()
            ],
            'type_distribution': [
                {'type': k, 'count': v} for k, v in type_stats.items()
            ],
            'details': details
        }

    def generate_kpi_report(self, date_range, metrics=None):
        """
        生成 KPI 综合报表数据
        汇总多维度 KPI 指标
        """
        metrics = metrics or ['completion_rate', 'on_time_delivery', 'defect_rate', 'task_efficiency']
        start_date, end_date = self._parse_date_range(date_range)

        kpi_data = {}

        # 生产相关 KPI
        plans = ProductionPlan.query.filter(
            and_(
                ProductionPlan.plan_start_date >= start_date,
                ProductionPlan.plan_start_date <= end_date
            )
        ).all()

        total_plans = len(plans)
        completed_plans = len([p for p in plans if p.status == 'completed'])
        delayed_plans = len([p for p in plans if p.is_delayed])
        total_qty = sum(p.plan_quantity or 0 for p in plans)
        completed_qty = sum(p.completed_quantity or 0 for p in plans)
        defect_qty = sum(p.defect_quantity or 0 for p in plans)

        # 准时交付统计
        on_time_count = 0
        for p in plans:
            if p.status == 'completed' and p.actual_end_date and p.plan_end_date:
                if p.actual_end_date <= p.plan_end_date:
                    on_time_count += 1

        if 'completion_rate' in metrics:
            kpi_data['completion_rate'] = {
                'name': '计划完成率',
                'value': round((completed_plans / total_plans * 100), 2) if total_plans > 0 else 0,
                'unit': '%',
                'trend': 'up',
                'target': 90,
            }

        if 'on_time_delivery' in metrics:
            kpi_data['on_time_delivery'] = {
                'name': '准时交付率',
                'value': round((on_time_count / completed_plans * 100), 2) if completed_plans > 0 else 0,
                'unit': '%',
                'trend': 'up',
                'target': 95,
            }

        if 'defect_rate' in metrics:
            kpi_data['defect_rate'] = {
                'name': '不良率',
                'value': round((defect_qty / completed_qty * 100), 2) if completed_qty > 0 else 0,
                'unit': '%',
                'trend': 'down',
                'target': 2,
            }

        if 'production_efficiency' in metrics:
            kpi_data['production_efficiency'] = {
                'name': '产能利用率',
                'value': round((completed_qty / total_qty * 100), 2) if total_qty > 0 else 0,
                'unit': '%',
                'trend': 'up',
                'target': 85,
            }

        # 任务相关 KPI
        tasks = Task.query.filter(
            and_(
                Task.created_at >= start_date,
                Task.created_at <= end_date
            )
        ).all()

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        overdue_tasks = len([t for t in tasks if t.is_overdue])

        if 'task_efficiency' in metrics:
            kpi_data['task_efficiency'] = {
                'name': '任务完成率',
                'value': round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0,
                'unit': '%',
                'trend': 'up',
                'target': 95,
            }

        if 'task_overdue_rate' in metrics:
            kpi_data['task_overdue_rate'] = {
                'name': '任务逾期率',
                'value': round((overdue_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0,
                'unit': '%',
                'trend': 'down',
                'target': 5,
            }

        return {
            'report_type': 'kpi',
            'report_name': 'KPI综合报表',
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_production_plans': total_plans,
                'total_tasks': total_tasks,
                'data_coverage_days': (end_date - start_date).days + 1,
            },
            'kpi_metrics': kpi_data,
            'overall_score': self._calculate_overall_score(kpi_data)
        }

    def _parse_date_range(self, date_range):
        """解析日期范围"""
        if isinstance(date_range, list) and len(date_range) == 2:
            start = datetime.strptime(date_range[0], '%Y-%m-%d').date() if isinstance(date_range[0], str) else date_range[0]
            end = datetime.strptime(date_range[1], '%Y-%m-%d').date() if isinstance(date_range[1], str) else date_range[1]
            return start, end
        elif isinstance(date_range, dict):
            start = datetime.strptime(date_range['start'], '%Y-%m-%d').date()
            end = datetime.strptime(date_range['end'], '%Y-%m-%d').date()
            return start, end
        else:
            # 默认最近30天
            end = datetime.now().date()
            start = end - timedelta(days=30)
            return start, end

    def _calculate_overall_score(self, kpi_data):
        """计算综合得分"""
        if not kpi_data:
            return 0

        scores = []
        for key, kpi in kpi_data.items():
            value = kpi.get('value', 0)
            target = kpi.get('target', 100)
            trend = kpi.get('trend', 'up')

            if trend == 'up':
                # 越高越好
                score = min(100, (value / target * 100)) if target > 0 else 0
            else:
                # 越低越好
                if value <= target:
                    score = 100
                else:
                    score = max(0, 100 - ((value - target) / target * 100))

            scores.append(score)

        return round(sum(scores) / len(scores), 1) if scores else 0
