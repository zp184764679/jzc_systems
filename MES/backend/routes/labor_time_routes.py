# MES 工时统计路由
# Labor Time Statistics Routes

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy import func, extract, and_, or_, case
from database import db
from models.production_record import ProductionRecord
from models.process import WorkOrderProcess, ProcessDefinition, PROCESS_TYPE_LABELS
from models.work_order import WorkOrder

labor_time_bp = Blueprint('labor_time', __name__, url_prefix='/api/labor-time')


@labor_time_bp.route('/summary', methods=['GET'])
def get_summary():
    """获取工时统计汇总"""
    try:
        # 获取日期范围参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 默认本月
        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 从 ProductionRecord 统计实际工时
        record_stats = db.session.query(
            func.count(ProductionRecord.id).label('record_count'),
            func.sum(ProductionRecord.work_hours).label('total_work_hours'),
            func.sum(ProductionRecord.quantity).label('total_quantity'),
            func.sum(ProductionRecord.good_quantity).label('total_good_quantity'),
            func.sum(ProductionRecord.defect_quantity).label('total_defect_quantity'),
            func.count(func.distinct(ProductionRecord.operator_id)).label('operator_count'),
        ).filter(
            ProductionRecord.created_at >= start_dt,
            ProductionRecord.created_at < end_dt
        ).first()

        # 从 WorkOrderProcess 统计工时
        process_stats = db.session.query(
            func.count(WorkOrderProcess.id).label('process_count'),
            func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
            func.sum(WorkOrderProcess.planned_hours).label('planned_hours'),
            func.sum(
                case(
                    (WorkOrderProcess.planned_quantity > 0,
                     WorkOrderProcess.standard_time * WorkOrderProcess.planned_quantity / 60.0),
                    else_=0
                )
            ).label('standard_hours'),
            func.sum(WorkOrderProcess.completed_quantity).label('completed_quantity'),
        ).filter(
            WorkOrderProcess.status == 'completed',
            WorkOrderProcess.actual_end >= start_dt,
            WorkOrderProcess.actual_end < end_dt
        ).first()

        # 计算效率
        total_actual_hours = float(record_stats.total_work_hours or 0) + float(process_stats.actual_hours or 0)
        standard_hours = float(process_stats.standard_hours or 0)
        efficiency = round((standard_hours / total_actual_hours * 100), 2) if total_actual_hours > 0 else 0

        # 上期对比（上一个相同长度的时间段）
        period_days = (end_dt - start_dt).days
        prev_start_dt = start_dt - timedelta(days=period_days)
        prev_end_dt = start_dt

        prev_record_stats = db.session.query(
            func.sum(ProductionRecord.work_hours).label('total_work_hours'),
        ).filter(
            ProductionRecord.created_at >= prev_start_dt,
            ProductionRecord.created_at < prev_end_dt
        ).first()

        prev_hours = float(prev_record_stats.total_work_hours or 0)
        growth_rate = round((total_actual_hours - prev_hours) / prev_hours * 100, 2) if prev_hours > 0 else 0

        return jsonify({
            'success': True,
            'data': {
                'date_range': {'start': start_date, 'end': end_date},
                'total_work_hours': round(total_actual_hours, 2),
                'standard_hours': round(standard_hours, 2),
                'efficiency': efficiency,
                'record_count': record_stats.record_count or 0,
                'process_count': process_stats.process_count or 0,
                'operator_count': record_stats.operator_count or 0,
                'total_quantity': record_stats.total_quantity or 0,
                'total_good_quantity': record_stats.total_good_quantity or 0,
                'total_defect_quantity': record_stats.total_defect_quantity or 0,
                'completed_quantity': process_stats.completed_quantity or 0,
                'prev_period_hours': round(prev_hours, 2),
                'growth_rate': growth_rate,
                'avg_hours_per_operator': round(total_actual_hours / (record_stats.operator_count or 1), 2),
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@labor_time_bp.route('/by-operator', methods=['GET'])
def get_by_operator():
    """按操作员统计工时"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 从 ProductionRecord 统计
        record_by_operator = db.session.query(
            ProductionRecord.operator_id,
            ProductionRecord.operator_name,
            func.count(ProductionRecord.id).label('record_count'),
            func.sum(ProductionRecord.work_hours).label('work_hours'),
            func.sum(ProductionRecord.quantity).label('quantity'),
            func.sum(ProductionRecord.good_quantity).label('good_quantity'),
            func.sum(ProductionRecord.defect_quantity).label('defect_quantity'),
        ).filter(
            ProductionRecord.operator_id.isnot(None),
            ProductionRecord.created_at >= start_dt,
            ProductionRecord.created_at < end_dt
        ).group_by(
            ProductionRecord.operator_id,
            ProductionRecord.operator_name
        ).all()

        # 从 WorkOrderProcess 统计
        process_by_operator = db.session.query(
            WorkOrderProcess.operator_id,
            WorkOrderProcess.operator_name,
            func.count(WorkOrderProcess.id).label('process_count'),
            func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
            func.sum(WorkOrderProcess.planned_hours).label('planned_hours'),
            func.sum(WorkOrderProcess.completed_quantity).label('completed_quantity'),
        ).filter(
            WorkOrderProcess.operator_id.isnot(None),
            WorkOrderProcess.status == 'completed',
            WorkOrderProcess.actual_end >= start_dt,
            WorkOrderProcess.actual_end < end_dt
        ).group_by(
            WorkOrderProcess.operator_id,
            WorkOrderProcess.operator_name
        ).all()

        # 合并结果
        operator_map = {}

        for r in record_by_operator:
            key = r.operator_id
            if key not in operator_map:
                operator_map[key] = {
                    'operator_id': r.operator_id,
                    'operator_name': r.operator_name,
                    'record_count': 0,
                    'process_count': 0,
                    'work_hours': 0,
                    'actual_hours': 0,
                    'planned_hours': 0,
                    'quantity': 0,
                    'good_quantity': 0,
                    'defect_quantity': 0,
                    'completed_quantity': 0,
                }
            operator_map[key]['record_count'] = r.record_count or 0
            operator_map[key]['work_hours'] = float(r.work_hours or 0)
            operator_map[key]['quantity'] = r.quantity or 0
            operator_map[key]['good_quantity'] = r.good_quantity or 0
            operator_map[key]['defect_quantity'] = r.defect_quantity or 0

        for p in process_by_operator:
            key = p.operator_id
            if key not in operator_map:
                operator_map[key] = {
                    'operator_id': p.operator_id,
                    'operator_name': p.operator_name,
                    'record_count': 0,
                    'process_count': 0,
                    'work_hours': 0,
                    'actual_hours': 0,
                    'planned_hours': 0,
                    'quantity': 0,
                    'good_quantity': 0,
                    'defect_quantity': 0,
                    'completed_quantity': 0,
                }
            operator_map[key]['process_count'] = p.process_count or 0
            operator_map[key]['actual_hours'] = float(p.actual_hours or 0)
            operator_map[key]['planned_hours'] = float(p.planned_hours or 0)
            operator_map[key]['completed_quantity'] = p.completed_quantity or 0

        # 计算汇总
        result = []
        for op in operator_map.values():
            total_hours = op['work_hours'] + op['actual_hours']
            op['total_hours'] = round(total_hours, 2)
            op['work_hours'] = round(op['work_hours'], 2)
            op['actual_hours'] = round(op['actual_hours'], 2)
            op['planned_hours'] = round(op['planned_hours'], 2)
            op['efficiency'] = round(op['planned_hours'] / total_hours * 100, 2) if total_hours > 0 else 0
            op['yield_rate'] = round(op['good_quantity'] / op['quantity'] * 100, 2) if op['quantity'] > 0 else 100
            result.append(op)

        # 按总工时降序排序
        result.sort(key=lambda x: x['total_hours'], reverse=True)

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@labor_time_bp.route('/by-process-type', methods=['GET'])
def get_by_process_type():
    """按工序类型统计工时"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 从 WorkOrderProcess 按工序类型统计
        stats = db.session.query(
            WorkOrderProcess.process_type,
            func.count(WorkOrderProcess.id).label('count'),
            func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
            func.sum(WorkOrderProcess.planned_hours).label('planned_hours'),
            func.sum(WorkOrderProcess.completed_quantity).label('completed_quantity'),
            func.sum(WorkOrderProcess.defect_quantity).label('defect_quantity'),
        ).filter(
            WorkOrderProcess.status == 'completed',
            WorkOrderProcess.actual_end >= start_dt,
            WorkOrderProcess.actual_end < end_dt
        ).group_by(
            WorkOrderProcess.process_type
        ).all()

        result = []
        for s in stats:
            process_type = s.process_type or 'other'
            actual_hours = float(s.actual_hours or 0)
            planned_hours = float(s.planned_hours or 0)
            result.append({
                'process_type': process_type,
                'process_type_label': PROCESS_TYPE_LABELS.get(process_type, process_type),
                'count': s.count or 0,
                'actual_hours': round(actual_hours, 2),
                'planned_hours': round(planned_hours, 2),
                'completed_quantity': s.completed_quantity or 0,
                'defect_quantity': s.defect_quantity or 0,
                'efficiency': round(planned_hours / actual_hours * 100, 2) if actual_hours > 0 else 0,
            })

        # 按实际工时降序排序
        result.sort(key=lambda x: x['actual_hours'], reverse=True)

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@labor_time_bp.route('/trend', methods=['GET'])
def get_trend():
    """获取工时趋势（按日期）"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')  # day, week, month

        if not start_date:
            today = datetime.now()
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 根据分组方式选择日期格式
        if group_by == 'month':
            date_format = func.date_format(ProductionRecord.created_at, '%Y-%m')
            date_format2 = func.date_format(WorkOrderProcess.actual_end, '%Y-%m')
        elif group_by == 'week':
            date_format = func.date_format(ProductionRecord.created_at, '%Y-%u')
            date_format2 = func.date_format(WorkOrderProcess.actual_end, '%Y-%u')
        else:  # day
            date_format = func.date(ProductionRecord.created_at)
            date_format2 = func.date(WorkOrderProcess.actual_end)

        # 从 ProductionRecord 统计
        record_trend = db.session.query(
            date_format.label('date'),
            func.sum(ProductionRecord.work_hours).label('work_hours'),
            func.sum(ProductionRecord.quantity).label('quantity'),
            func.count(ProductionRecord.id).label('count'),
        ).filter(
            ProductionRecord.created_at >= start_dt,
            ProductionRecord.created_at < end_dt
        ).group_by(
            date_format
        ).all()

        # 从 WorkOrderProcess 统计
        process_trend = db.session.query(
            date_format2.label('date'),
            func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
            func.sum(WorkOrderProcess.planned_hours).label('planned_hours'),
            func.sum(WorkOrderProcess.completed_quantity).label('completed_quantity'),
        ).filter(
            WorkOrderProcess.status == 'completed',
            WorkOrderProcess.actual_end >= start_dt,
            WorkOrderProcess.actual_end < end_dt
        ).group_by(
            date_format2
        ).all()

        # 合并结果
        date_map = {}

        for r in record_trend:
            date_key = str(r.date)
            if date_key not in date_map:
                date_map[date_key] = {
                    'date': date_key,
                    'work_hours': 0,
                    'actual_hours': 0,
                    'planned_hours': 0,
                    'quantity': 0,
                    'completed_quantity': 0,
                    'record_count': 0,
                }
            date_map[date_key]['work_hours'] = float(r.work_hours or 0)
            date_map[date_key]['quantity'] = r.quantity or 0
            date_map[date_key]['record_count'] = r.count or 0

        for p in process_trend:
            date_key = str(p.date)
            if date_key not in date_map:
                date_map[date_key] = {
                    'date': date_key,
                    'work_hours': 0,
                    'actual_hours': 0,
                    'planned_hours': 0,
                    'quantity': 0,
                    'completed_quantity': 0,
                    'record_count': 0,
                }
            date_map[date_key]['actual_hours'] = float(p.actual_hours or 0)
            date_map[date_key]['planned_hours'] = float(p.planned_hours or 0)
            date_map[date_key]['completed_quantity'] = p.completed_quantity or 0

        # 计算总工时和效率
        result = []
        for d in date_map.values():
            total_hours = d['work_hours'] + d['actual_hours']
            d['total_hours'] = round(total_hours, 2)
            d['work_hours'] = round(d['work_hours'], 2)
            d['actual_hours'] = round(d['actual_hours'], 2)
            d['planned_hours'] = round(d['planned_hours'], 2)
            d['efficiency'] = round(d['planned_hours'] / total_hours * 100, 2) if total_hours > 0 else 0
            result.append(d)

        # 按日期排序
        result.sort(key=lambda x: x['date'])

        return jsonify({
            'success': True,
            'data': result,
            'group_by': group_by
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@labor_time_bp.route('/by-work-order', methods=['GET'])
def get_by_work_order():
    """按工单统计工时"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 统计每个工单的工时
        query = db.session.query(
            WorkOrder.id,
            WorkOrder.order_no,
            WorkOrder.product_code,
            WorkOrder.product_name,
            WorkOrder.planned_quantity,
            WorkOrder.completed_quantity,
            WorkOrder.status,
            func.count(WorkOrderProcess.id).label('process_count'),
            func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
            func.sum(WorkOrderProcess.planned_hours).label('planned_hours'),
            func.sum(
                case(
                    (WorkOrderProcess.planned_quantity > 0,
                     WorkOrderProcess.standard_time * WorkOrderProcess.planned_quantity / 60.0),
                    else_=0
                )
            ).label('standard_hours'),
        ).outerjoin(
            WorkOrderProcess, WorkOrder.id == WorkOrderProcess.work_order_id
        ).filter(
            or_(
                WorkOrder.created_at >= start_dt,
                WorkOrder.actual_start >= start_dt
            ),
            or_(
                WorkOrder.created_at < end_dt,
                WorkOrder.actual_start < end_dt
            )
        ).group_by(
            WorkOrder.id
        ).order_by(
            WorkOrder.id.desc()
        )

        # 分页
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        result = []
        for item in items:
            actual_hours = float(item.actual_hours or 0)
            planned_hours = float(item.planned_hours or 0)
            standard_hours = float(item.standard_hours or 0)
            result.append({
                'work_order_id': item.id,
                'order_no': item.order_no,
                'product_code': item.product_code,
                'product_name': item.product_name,
                'planned_quantity': item.planned_quantity or 0,
                'completed_quantity': item.completed_quantity or 0,
                'status': item.status,
                'process_count': item.process_count or 0,
                'actual_hours': round(actual_hours, 2),
                'planned_hours': round(planned_hours, 2),
                'standard_hours': round(standard_hours, 2),
                'efficiency': round(standard_hours / actual_hours * 100, 2) if actual_hours > 0 else 0,
            })

        return jsonify({
            'success': True,
            'data': result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@labor_time_bp.route('/by-equipment', methods=['GET'])
def get_by_equipment():
    """按设备统计工时"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 从 ProductionRecord 统计
        record_stats = db.session.query(
            ProductionRecord.equipment_id,
            ProductionRecord.equipment_code,
            ProductionRecord.equipment_name,
            func.count(ProductionRecord.id).label('record_count'),
            func.sum(ProductionRecord.work_hours).label('work_hours'),
            func.sum(ProductionRecord.quantity).label('quantity'),
            func.sum(ProductionRecord.good_quantity).label('good_quantity'),
        ).filter(
            ProductionRecord.equipment_id.isnot(None),
            ProductionRecord.created_at >= start_dt,
            ProductionRecord.created_at < end_dt
        ).group_by(
            ProductionRecord.equipment_id,
            ProductionRecord.equipment_code,
            ProductionRecord.equipment_name
        ).all()

        # 从 WorkOrderProcess 统计
        process_stats = db.session.query(
            WorkOrderProcess.machine_id,
            WorkOrderProcess.machine_name,
            func.count(WorkOrderProcess.id).label('process_count'),
            func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
            func.sum(WorkOrderProcess.completed_quantity).label('completed_quantity'),
        ).filter(
            WorkOrderProcess.machine_id.isnot(None),
            WorkOrderProcess.status == 'completed',
            WorkOrderProcess.actual_end >= start_dt,
            WorkOrderProcess.actual_end < end_dt
        ).group_by(
            WorkOrderProcess.machine_id,
            WorkOrderProcess.machine_name
        ).all()

        # 合并结果
        equipment_map = {}

        for r in record_stats:
            key = r.equipment_id
            if key and key not in equipment_map:
                equipment_map[key] = {
                    'equipment_id': r.equipment_id,
                    'equipment_code': r.equipment_code,
                    'equipment_name': r.equipment_name,
                    'record_count': 0,
                    'process_count': 0,
                    'work_hours': 0,
                    'actual_hours': 0,
                    'quantity': 0,
                    'good_quantity': 0,
                    'completed_quantity': 0,
                }
            if key:
                equipment_map[key]['record_count'] = r.record_count or 0
                equipment_map[key]['work_hours'] = float(r.work_hours or 0)
                equipment_map[key]['quantity'] = r.quantity or 0
                equipment_map[key]['good_quantity'] = r.good_quantity or 0

        for p in process_stats:
            key = p.machine_id
            if key and key not in equipment_map:
                equipment_map[key] = {
                    'equipment_id': p.machine_id,
                    'equipment_code': None,
                    'equipment_name': p.machine_name,
                    'record_count': 0,
                    'process_count': 0,
                    'work_hours': 0,
                    'actual_hours': 0,
                    'quantity': 0,
                    'good_quantity': 0,
                    'completed_quantity': 0,
                }
            if key:
                equipment_map[key]['process_count'] = p.process_count or 0
                equipment_map[key]['actual_hours'] = float(p.actual_hours or 0)
                equipment_map[key]['completed_quantity'] = p.completed_quantity or 0

        # 计算汇总
        result = []
        for eq in equipment_map.values():
            total_hours = eq['work_hours'] + eq['actual_hours']
            eq['total_hours'] = round(total_hours, 2)
            eq['work_hours'] = round(eq['work_hours'], 2)
            eq['actual_hours'] = round(eq['actual_hours'], 2)
            eq['utilization_rate'] = round(total_hours / 8 / 30 * 100, 2)  # 假设每天8小时，30天
            result.append(eq)

        # 按总工时降序排序
        result.sort(key=lambda x: x['total_hours'], reverse=True)

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@labor_time_bp.route('/overtime', methods=['GET'])
def get_overtime():
    """获取加班统计"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        standard_hours_per_day = request.args.get('standard_hours', 8, type=float)

        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        # 按操作员和日期统计工时
        daily_hours = db.session.query(
            ProductionRecord.operator_id,
            ProductionRecord.operator_name,
            func.date(ProductionRecord.created_at).label('work_date'),
            func.sum(ProductionRecord.work_hours).label('total_hours'),
        ).filter(
            ProductionRecord.operator_id.isnot(None),
            ProductionRecord.created_at >= start_dt,
            ProductionRecord.created_at < end_dt
        ).group_by(
            ProductionRecord.operator_id,
            ProductionRecord.operator_name,
            func.date(ProductionRecord.created_at)
        ).all()

        # 计算加班
        operator_overtime = {}

        for row in daily_hours:
            key = row.operator_id
            total_hours = float(row.total_hours or 0)
            overtime = max(0, total_hours - standard_hours_per_day)

            if key not in operator_overtime:
                operator_overtime[key] = {
                    'operator_id': row.operator_id,
                    'operator_name': row.operator_name,
                    'work_days': 0,
                    'total_hours': 0,
                    'standard_hours': 0,
                    'overtime_hours': 0,
                    'overtime_days': 0,
                }

            operator_overtime[key]['work_days'] += 1
            operator_overtime[key]['total_hours'] += total_hours
            operator_overtime[key]['standard_hours'] += min(total_hours, standard_hours_per_day)
            operator_overtime[key]['overtime_hours'] += overtime
            if overtime > 0:
                operator_overtime[key]['overtime_days'] += 1

        result = []
        for op in operator_overtime.values():
            op['total_hours'] = round(op['total_hours'], 2)
            op['standard_hours'] = round(op['standard_hours'], 2)
            op['overtime_hours'] = round(op['overtime_hours'], 2)
            op['overtime_rate'] = round(op['overtime_days'] / op['work_days'] * 100, 2) if op['work_days'] > 0 else 0
            result.append(op)

        # 按加班工时降序排序
        result.sort(key=lambda x: x['overtime_hours'], reverse=True)

        # 汇总
        summary = {
            'total_operators': len(result),
            'total_overtime_hours': sum(op['overtime_hours'] for op in result),
            'avg_overtime_hours': round(sum(op['overtime_hours'] for op in result) / len(result), 2) if result else 0,
            'operators_with_overtime': sum(1 for op in result if op['overtime_hours'] > 0),
        }

        return jsonify({
            'success': True,
            'data': result,
            'summary': summary,
            'standard_hours_per_day': standard_hours_per_day
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@labor_time_bp.route('/efficiency-ranking', methods=['GET'])
def get_efficiency_ranking():
    """获取效率排名"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        rank_by = request.args.get('rank_by', 'operator')  # operator, equipment, process_type
        top_n = request.args.get('top', 10, type=int)

        if not start_date:
            today = datetime.now()
            start_date = today.replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

        if rank_by == 'operator':
            # 按操作员排名
            stats = db.session.query(
                WorkOrderProcess.operator_id,
                WorkOrderProcess.operator_name,
                func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
                func.sum(WorkOrderProcess.planned_hours).label('planned_hours'),
                func.sum(WorkOrderProcess.completed_quantity).label('completed_quantity'),
                func.sum(WorkOrderProcess.defect_quantity).label('defect_quantity'),
                func.count(WorkOrderProcess.id).label('count'),
            ).filter(
                WorkOrderProcess.operator_id.isnot(None),
                WorkOrderProcess.status == 'completed',
                WorkOrderProcess.actual_end >= start_dt,
                WorkOrderProcess.actual_end < end_dt
            ).group_by(
                WorkOrderProcess.operator_id,
                WorkOrderProcess.operator_name
            ).all()

            result = []
            for s in stats:
                actual_hours = float(s.actual_hours or 0)
                planned_hours = float(s.planned_hours or 0)
                if actual_hours > 0:
                    efficiency = planned_hours / actual_hours * 100
                    total_qty = (s.completed_quantity or 0) + (s.defect_quantity or 0)
                    yield_rate = (s.completed_quantity or 0) / total_qty * 100 if total_qty > 0 else 100
                    result.append({
                        'id': s.operator_id,
                        'name': s.operator_name,
                        'actual_hours': round(actual_hours, 2),
                        'planned_hours': round(planned_hours, 2),
                        'efficiency': round(efficiency, 2),
                        'completed_quantity': s.completed_quantity or 0,
                        'defect_quantity': s.defect_quantity or 0,
                        'yield_rate': round(yield_rate, 2),
                        'count': s.count or 0,
                    })

        elif rank_by == 'equipment':
            # 按设备排名
            stats = db.session.query(
                WorkOrderProcess.machine_id,
                WorkOrderProcess.machine_name,
                func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
                func.sum(WorkOrderProcess.planned_hours).label('planned_hours'),
                func.sum(WorkOrderProcess.completed_quantity).label('completed_quantity'),
                func.count(WorkOrderProcess.id).label('count'),
            ).filter(
                WorkOrderProcess.machine_id.isnot(None),
                WorkOrderProcess.status == 'completed',
                WorkOrderProcess.actual_end >= start_dt,
                WorkOrderProcess.actual_end < end_dt
            ).group_by(
                WorkOrderProcess.machine_id,
                WorkOrderProcess.machine_name
            ).all()

            result = []
            for s in stats:
                actual_hours = float(s.actual_hours or 0)
                planned_hours = float(s.planned_hours or 0)
                if actual_hours > 0:
                    efficiency = planned_hours / actual_hours * 100
                    result.append({
                        'id': s.machine_id,
                        'name': s.machine_name,
                        'actual_hours': round(actual_hours, 2),
                        'planned_hours': round(planned_hours, 2),
                        'efficiency': round(efficiency, 2),
                        'completed_quantity': s.completed_quantity or 0,
                        'count': s.count or 0,
                    })

        else:  # process_type
            # 按工序类型排名
            stats = db.session.query(
                WorkOrderProcess.process_type,
                func.sum(WorkOrderProcess.actual_hours).label('actual_hours'),
                func.sum(WorkOrderProcess.planned_hours).label('planned_hours'),
                func.sum(WorkOrderProcess.completed_quantity).label('completed_quantity'),
                func.count(WorkOrderProcess.id).label('count'),
            ).filter(
                WorkOrderProcess.status == 'completed',
                WorkOrderProcess.actual_end >= start_dt,
                WorkOrderProcess.actual_end < end_dt
            ).group_by(
                WorkOrderProcess.process_type
            ).all()

            result = []
            for s in stats:
                actual_hours = float(s.actual_hours or 0)
                planned_hours = float(s.planned_hours or 0)
                if actual_hours > 0:
                    efficiency = planned_hours / actual_hours * 100
                    process_type = s.process_type or 'other'
                    result.append({
                        'id': process_type,
                        'name': PROCESS_TYPE_LABELS.get(process_type, process_type),
                        'actual_hours': round(actual_hours, 2),
                        'planned_hours': round(planned_hours, 2),
                        'efficiency': round(efficiency, 2),
                        'completed_quantity': s.completed_quantity or 0,
                        'count': s.count or 0,
                    })

        # 按效率排序
        result.sort(key=lambda x: x['efficiency'], reverse=True)

        # 添加排名
        for i, item in enumerate(result[:top_n], 1):
            item['rank'] = i

        return jsonify({
            'success': True,
            'data': result[:top_n],
            'rank_by': rank_by,
            'total': len(result)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
