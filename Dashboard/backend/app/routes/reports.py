"""
Reports API Routes - 报表 API 路由
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from datetime import datetime, date
import os
import traceback

from app import db
from app.models.report import Report, ReportType, ReportFormat, ReportStatus
from app.services.report_generator import ReportGenerator
from app.services.export_service import ExportService

reports_bp = Blueprint('reports', __name__)


def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


@reports_bp.route('', methods=['GET'])
def get_reports():
    """获取报表历史列表"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # 筛选参数
        report_type = request.args.get('report_type')
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # 构建查询
        query = Report.query

        if report_type:
            query = query.filter(Report.report_type == report_type)
        if status:
            query = query.filter(Report.status == status)
        if date_from:
            query = query.filter(Report.created_at >= parse_date(date_from))
        if date_to:
            query = query.filter(Report.created_at <= parse_date(date_to))

        # 排序和分页
        query = query.order_by(Report.created_at.desc())
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)

        return jsonify({
            'items': [r.to_dict() for r in pagination.items],
            'total': pagination.total,
            'page': page,
            'page_size': page_size,
            'pages': pagination.pages
        })

    except Exception as e:
        current_app.logger.error(f"获取报表列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """获取报表详情"""
    try:
        report = Report.query.get_or_404(report_id)
        result = report.to_dict()

        # 如果有数据快照，包含在结果中
        if report.data_snapshot:
            result['data'] = report.data_snapshot

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"获取报表详情失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/templates', methods=['GET'])
def get_templates():
    """获取报表模板"""
    templates = [
        {
            'type': 'production',
            'name': '生产报表',
            'description': '生产计划执行情况、完成率、延期分析',
            'icon': 'tool',
            'filters': ['status', 'department'],
        },
        {
            'type': 'order',
            'name': '订单报表',
            'description': '订单状态分布、客户订单统计、交付趋势',
            'icon': 'shopping-cart',
            'filters': ['customer', 'status'],
        },
        {
            'type': 'task',
            'name': '任务报表',
            'description': '任务完成情况、逾期分析、部门统计',
            'icon': 'check-square',
            'filters': ['assignee', 'priority', 'status'],
        },
        {
            'type': 'kpi',
            'name': 'KPI综合报表',
            'description': '多维度KPI汇总、综合评分、趋势分析',
            'icon': 'bar-chart',
            'filters': ['metrics'],
        },
    ]
    return jsonify(templates)


@reports_bp.route('/preview', methods=['POST'])
def preview_report():
    """预览报表数据（不保存）"""
    try:
        data = request.get_json()

        report_type = data.get('report_type')
        date_range_start = parse_date(data.get('date_range_start'))
        date_range_end = parse_date(data.get('date_range_end'))
        filters = data.get('filters', {})

        if not report_type:
            return jsonify({'error': '报表类型不能为空'}), 400

        # 生成报表数据
        generator = ReportGenerator()
        date_range = (date_range_start, date_range_end)

        if report_type == 'production':
            report_data = generator.generate_production_report(date_range, filters)
        elif report_type == 'order':
            report_data = generator.generate_order_report(date_range, filters)
        elif report_type == 'task':
            report_data = generator.generate_task_report(date_range, filters)
        elif report_type == 'kpi':
            metrics = data.get('metrics')
            report_data = generator.generate_kpi_report(date_range, metrics)
        else:
            return jsonify({'error': f'不支持的报表类型: {report_type}'}), 400

        return jsonify(report_data)

    except Exception as e:
        current_app.logger.error(f"预览报表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/generate', methods=['POST'])
def generate_report():
    """生成报表"""
    try:
        data = request.get_json()

        report_type = data.get('report_type')
        report_name = data.get('report_name')
        date_range_start = parse_date(data.get('date_range_start'))
        date_range_end = parse_date(data.get('date_range_end'))
        file_format = data.get('format', 'excel')
        filters = data.get('filters', {})
        metrics = data.get('metrics')

        # 验证
        if not report_type:
            return jsonify({'error': '报表类型不能为空'}), 400

        if file_format not in ['excel', 'pdf', 'csv']:
            return jsonify({'error': f'不支持的导出格式: {file_format}'}), 400

        # 生成报表名称
        if not report_name:
            type_labels = {
                'production': '生产报表',
                'order': '订单报表',
                'task': '任务报表',
                'kpi': 'KPI报表',
            }
            report_name = f"{type_labels.get(report_type, '报表')}_{datetime.now().strftime('%Y%m%d')}"

        # 创建报表记录
        report = Report(
            report_no=Report.generate_report_no(),
            report_type=report_type,
            report_name=report_name,
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            file_format=file_format,
            filters=filters,
            status='generating',
            created_by=data.get('created_by'),
            created_by_name=data.get('created_by_name'),
        )

        db.session.add(report)
        db.session.commit()

        try:
            # 生成报表数据
            generator = ReportGenerator()
            date_range = (date_range_start, date_range_end)

            if report_type == 'production':
                report_data = generator.generate_production_report(date_range, filters)
            elif report_type == 'order':
                report_data = generator.generate_order_report(date_range, filters)
            elif report_type == 'task':
                report_data = generator.generate_task_report(date_range, filters)
            elif report_type == 'kpi':
                report_data = generator.generate_kpi_report(date_range, metrics)
            else:
                raise ValueError(f'不支持的报表类型: {report_type}')

            # 保存数据快照
            report.data_snapshot = report_data

            # 导出文件
            export_service = ExportService()

            if file_format == 'excel':
                file_path = export_service.export_to_excel(report_data, report_type, report_name)
            elif file_format == 'pdf':
                file_path = export_service.export_to_pdf(report_data, report_type, report_name)
            elif file_format == 'csv':
                file_path = export_service.export_to_csv(report_data, report_type, report_name)

            # 更新报表记录
            report.file_path = file_path
            report.file_size = export_service.get_file_size(file_path)
            report.status = 'completed'
            report.completed_at = datetime.now()

            db.session.commit()

            return jsonify({
                'message': '报表生成成功',
                'report': report.to_dict()
            })

        except Exception as e:
            # 更新失败状态
            report.status = 'failed'
            report.error_message = str(e)
            db.session.commit()
            raise

    except Exception as e:
        current_app.logger.error(f"生成报表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/<int:report_id>/download', methods=['GET'])
def download_report(report_id):
    """下载报表文件"""
    try:
        report = Report.query.get_or_404(report_id)

        if report.status != 'completed':
            return jsonify({'error': '报表尚未生成完成'}), 400

        if not report.file_path or not os.path.exists(report.file_path):
            return jsonify({'error': '报表文件不存在'}), 404

        # 确定 MIME 类型
        mime_types = {
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf': 'application/pdf',
            'csv': 'text/csv',
        }
        mimetype = mime_types.get(report.file_format, 'application/octet-stream')

        # 构建下载文件名
        ext_map = {'excel': 'xlsx', 'pdf': 'pdf', 'csv': 'csv'}
        ext = ext_map.get(report.file_format, 'dat')
        download_name = f"{report.report_name}.{ext}"

        return send_file(
            report.file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        current_app.logger.error(f"下载报表失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """删除报表"""
    try:
        report = Report.query.get_or_404(report_id)

        # 删除文件
        if report.file_path and os.path.exists(report.file_path):
            try:
                os.remove(report.file_path)
            except OSError:
                pass  # 文件删除失败不影响数据库记录删除

        # 删除记录
        db.session.delete(report)
        db.session.commit()

        return jsonify({'message': '报表已删除'})

    except Exception as e:
        current_app.logger.error(f"删除报表失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取报表统计信息"""
    try:
        from sqlalchemy import func

        # 本月报表统计
        today = date.today()
        month_start = date(today.year, today.month, 1)

        total = Report.query.filter(Report.created_at >= month_start).count()
        pending = Report.query.filter(
            Report.created_at >= month_start,
            Report.status == 'pending'
        ).count()
        generating = Report.query.filter(
            Report.created_at >= month_start,
            Report.status == 'generating'
        ).count()
        completed = Report.query.filter(
            Report.created_at >= month_start,
            Report.status == 'completed'
        ).count()
        failed = Report.query.filter(
            Report.created_at >= month_start,
            Report.status == 'failed'
        ).count()

        # 存储空间统计
        total_size = db.session.query(func.sum(Report.file_size)).scalar() or 0

        # 按类型统计
        type_stats = db.session.query(
            Report.report_type,
            func.count(Report.id).label('count')
        ).filter(Report.created_at >= month_start).group_by(Report.report_type).all()

        return jsonify({
            'this_month': {
                'total': total,
                'pending': pending,
                'generating': generating,
                'completed': completed,
                'failed': failed,
            },
            'storage': {
                'total_size': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2) if total_size else 0,
            },
            'by_type': [
                {'type': t, 'count': c}
                for t, c in type_stats
            ]
        })

    except Exception as e:
        current_app.logger.error(f"获取报表统计失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/enums', methods=['GET'])
def get_enums():
    """获取枚举值"""
    return jsonify({
        'report_types': [
            {'value': 'production', 'label': '生产报表'},
            {'value': 'order', 'label': '订单报表'},
            {'value': 'task', 'label': '任务报表'},
            {'value': 'kpi', 'label': 'KPI报表'},
            {'value': 'custom', 'label': '自定义报表'},
        ],
        'formats': [
            {'value': 'excel', 'label': 'Excel (.xlsx)'},
            {'value': 'pdf', 'label': 'PDF'},
            {'value': 'csv', 'label': 'CSV'},
        ],
        'statuses': [
            {'value': 'pending', 'label': '待生成'},
            {'value': 'generating', 'label': '生成中'},
            {'value': 'completed', 'label': '已完成'},
            {'value': 'failed', 'label': '生成失败'},
        ]
    })
