"""
导出 API 路由
"""
from flask import Blueprint, request, send_file, jsonify
from datetime import datetime
import io

from models.project import Project
from models.task import Task
from services.export_service import ExportService

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


def serialize_project(project):
    """序列化项目对象"""
    return {
        'id': project.id,
        'project_no': project.project_no,
        'name': project.name,
        'customer': project.customer,
        'part_number': project.part_number,
        'order_no': project.order_no,
        'status': project.status.value if hasattr(project.status, 'value') else project.status,
        'priority': project.priority.value if hasattr(project.priority, 'value') else project.priority,
        'progress_percentage': project.progress_percentage,
        'planned_start_date': project.planned_start_date,
        'planned_end_date': project.planned_end_date,
        'description': project.description,
        'created_at': project.created_at,
    }


def serialize_task(task):
    """序列化任务对象"""
    return {
        'id': task.id,
        'task_no': task.task_no,
        'title': task.title,
        'status': task.status.value if hasattr(task.status, 'value') else task.status,
        'priority': task.priority.value if hasattr(task.priority, 'value') else task.priority,
        'completion_percentage': task.completion_percentage,
        'assigned_to_id': task.assigned_to_id,
        'assigned_to_name': task.assigned_to_name,
        'due_date': task.due_date,
        'created_at': task.created_at,
    }


@export_bp.route('/projects/excel', methods=['GET'])
def export_projects_excel():
    """导出项目列表到 Excel"""
    try:
        # 获取筛选参数
        status = request.args.get('status')
        priority = request.args.get('priority')
        customer = request.args.get('customer')
        part_number = request.args.get('part_number')

        # 构建查询
        query = Project.query.filter(Project.deleted_at.is_(None))

        if status:
            query = query.filter(Project.status == status)
        if priority:
            query = query.filter(Project.priority == priority)
        if customer:
            query = query.filter(Project.customer.like(f'%{customer}%'))
        if part_number:
            query = query.filter(Project.part_number == part_number)

        projects = query.order_by(Project.created_at.desc()).all()

        # 序列化
        projects_data = [serialize_project(p) for p in projects]

        # 生成 Excel
        excel_data = ExportService.export_projects_to_excel(projects_data)

        # 生成文件名
        filename = f"项目列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return send_file(
            io.BytesIO(excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


@export_bp.route('/projects/pdf', methods=['GET'])
def export_projects_pdf():
    """导出项目汇总报告到 PDF"""
    try:
        # 获取筛选参数
        status = request.args.get('status')
        priority = request.args.get('priority')
        customer = request.args.get('customer')
        part_number = request.args.get('part_number')

        # 构建查询
        query = Project.query.filter(Project.deleted_at.is_(None))

        if status:
            query = query.filter(Project.status == status)
        if priority:
            query = query.filter(Project.priority == priority)
        if customer:
            query = query.filter(Project.customer.like(f'%{customer}%'))
        if part_number:
            query = query.filter(Project.part_number == part_number)

        projects = query.order_by(Project.created_at.desc()).all()

        # 序列化
        projects_data = [serialize_project(p) for p in projects]

        # 生成 PDF
        pdf_data = ExportService.export_projects_summary_to_pdf(projects_data)

        # 生成文件名
        filename = f"项目汇总报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


@export_bp.route('/project/<int:project_id>/pdf', methods=['GET'])
def export_project_report_pdf(project_id):
    """导出单个项目报告到 PDF"""
    try:
        # 获取项目
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 获取任务
        tasks = Task.query.filter(
            Task.project_id == project_id,
            Task.deleted_at.is_(None)
        ).order_by(Task.created_at.asc()).all()

        # 序列化
        project_data = serialize_project(project)
        tasks_data = [serialize_task(t) for t in tasks]

        # 生成 PDF
        pdf_data = ExportService.export_project_report_to_pdf(project_data, tasks_data)

        # 生成文件名
        filename = f"项目报告_{project.project_no}_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


@export_bp.route('/project/<int:project_id>/tasks/excel', methods=['GET'])
def export_project_tasks_excel(project_id):
    """导出项目任务列表到 Excel"""
    try:
        # 获取项目
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        # 获取任务
        tasks = Task.query.filter(
            Task.project_id == project_id,
            Task.deleted_at.is_(None)
        ).order_by(Task.created_at.asc()).all()

        # 序列化
        tasks_data = [serialize_task(t) for t in tasks]

        # 生成 Excel
        excel_data = ExportService.export_tasks_to_excel(tasks_data, project.name)

        # 生成文件名
        filename = f"任务列表_{project.project_no}_{datetime.now().strftime('%Y%m%d')}.xlsx"

        return send_file(
            io.BytesIO(excel_data),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'导出失败: {str(e)}'}), 500


@export_bp.route('/part/<path:part_number>/pdf', methods=['GET'])
def export_part_number_report_pdf(part_number):
    """导出部件番号汇总报告到 PDF"""
    try:
        from urllib.parse import unquote
        decoded_part_number = unquote(part_number)

        # 获取相同部件番号的所有项目
        projects = Project.query.filter(
            Project.part_number == decoded_part_number,
            Project.deleted_at.is_(None)
        ).order_by(Project.created_at.desc()).all()

        if not projects:
            return jsonify({'error': f'未找到部件番号 {decoded_part_number} 的项目'}), 404

        # 序列化
        projects_data = [serialize_project(p) for p in projects]

        # 生成 PDF
        pdf_data = ExportService.export_projects_summary_to_pdf(projects_data)

        # 生成文件名
        filename = f"部件番号报告_{decoded_part_number}_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'导出失败: {str(e)}'}), 500
