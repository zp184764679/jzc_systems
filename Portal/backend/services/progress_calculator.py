"""
进度计算服务 - 任务驱动的项目进度管理

计算公式:
- 阶段进度 = Σ(任务完成% × 任务权重) / Σ(任务权重)
- 项目进度 = 各阶段完成度的平均值（无阶段时直接从任务计算）
"""
import logging

logger = logging.getLogger(__name__)


class ProgressCalculator:
    """进度计算器"""

    @staticmethod
    def calculate_phase_progress(session, phase_id):
        """
        计算阶段进度

        公式：阶段进度 = Σ(任务完成百分比 × 任务权重) / Σ(任务权重)

        Args:
            session: SQLAlchemy session
            phase_id: 阶段ID

        Returns:
            int: 完成百分比 (0-100)
        """
        from models.task import Task

        tasks = session.query(Task).filter_by(phase_id=phase_id).all()

        if not tasks:
            return 0

        total_weight = sum((t.weight or 1) for t in tasks)
        weighted_progress = sum(
            (t.completion_percentage or 0) * (t.weight or 1)
            for t in tasks
        )

        return round(weighted_progress / total_weight) if total_weight > 0 else 0

    @staticmethod
    def calculate_project_progress(session, project_id):
        """
        计算项目进度

        方案：基于阶段平均 - 所有阶段完成度的平均值
        备选：无阶段时直接从任务计算

        Args:
            session: SQLAlchemy session
            project_id: 项目ID

        Returns:
            int: 完成百分比 (0-100)
        """
        from models.project_phase import ProjectPhase

        phases = session.query(ProjectPhase).filter_by(project_id=project_id).all()

        if not phases:
            # 无阶段时直接从任务计算
            return ProgressCalculator._calculate_from_tasks(session, project_id)

        # 阶段加权平均
        total_phases = len(phases)
        phase_progress_sum = sum(p.completion_percentage or 0 for p in phases)

        return round(phase_progress_sum / total_phases) if total_phases > 0 else 0

    @staticmethod
    def _calculate_from_tasks(session, project_id):
        """
        直接从任务计算项目进度（无阶段时的备选方案）

        Args:
            session: SQLAlchemy session
            project_id: 项目ID

        Returns:
            int: 完成百分比 (0-100)
        """
        from models.task import Task

        tasks = session.query(Task).filter_by(project_id=project_id).all()

        if not tasks:
            return 0

        total_weight = sum((t.weight or 1) for t in tasks)
        weighted_progress = sum(
            (t.completion_percentage or 0) * (t.weight or 1)
            for t in tasks
        )

        return round(weighted_progress / total_weight) if total_weight > 0 else 0

    @staticmethod
    def update_all_progress(session, project_id):
        """
        更新项目及其所有阶段的进度

        触发时机：任务完成/进度更新时调用

        Args:
            session: SQLAlchemy session
            project_id: 项目ID
        """
        from models.project import Project
        from models.project_phase import ProjectPhase

        try:
            # 1. 更新所有阶段的进度
            phases = session.query(ProjectPhase).filter_by(project_id=project_id).all()
            for phase in phases:
                phase.completion_percentage = ProgressCalculator.calculate_phase_progress(
                    session, phase.id
                )

            # 2. 更新项目总进度
            project = session.query(Project).filter_by(id=project_id).first()
            if project:
                old_progress = project.progress_percentage
                project.progress_percentage = ProgressCalculator.calculate_project_progress(
                    session, project_id
                )

                # 3. 自动更新项目状态
                if project.progress_percentage == 100:
                    if project.status.value != 'completed':
                        project.status = 'completed'
                        logger.info(f"Project {project_id} auto-completed (progress=100%)")
                elif project.progress_percentage > 0 and project.status.value == 'planning':
                    project.status = 'in_progress'
                    logger.info(f"Project {project_id} auto-started (progress>0%)")

                logger.debug(f"Project {project_id} progress updated: {old_progress}% -> {project.progress_percentage}%")

        except Exception as e:
            logger.error(f"Failed to update progress for project {project_id}: {e}")
            raise

    @staticmethod
    def get_progress_detail(session, project_id):
        """
        获取项目进度详情

        Args:
            session: SQLAlchemy session
            project_id: 项目ID

        Returns:
            dict: 包含项目、阶段、任务进度的详细信息
        """
        from models.project import Project
        from models.project_phase import ProjectPhase
        from models.task import Task

        project = session.query(Project).filter_by(id=project_id).first()
        if not project:
            return None

        phases = session.query(ProjectPhase).filter_by(project_id=project_id).order_by(
            ProjectPhase.phase_order
        ).all()

        tasks = session.query(Task).filter_by(project_id=project_id).all()

        # 按阶段分组任务
        tasks_by_phase = {}
        unassigned_tasks = []

        for task in tasks:
            if task.phase_id:
                if task.phase_id not in tasks_by_phase:
                    tasks_by_phase[task.phase_id] = []
                tasks_by_phase[task.phase_id].append(task.to_dict())
            else:
                unassigned_tasks.append(task.to_dict())

        # 构建阶段详情
        phase_details = []
        for phase in phases:
            phase_tasks = tasks_by_phase.get(phase.id, [])
            phase_details.append({
                'id': phase.id,
                'name': phase.name,
                'phase_type': phase.phase_type.value if hasattr(phase.phase_type, 'value') else str(phase.phase_type),
                'phase_order': phase.phase_order,
                'status': phase.status.value if hasattr(phase.status, 'value') else str(phase.status),
                'completion_percentage': phase.completion_percentage or 0,
                'tasks': phase_tasks,
                'task_count': len(phase_tasks)
            })

        # 任务统计
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status.value == 'completed' if hasattr(t.status, 'value') else str(t.status) == 'completed')
        in_progress_tasks = sum(1 for t in tasks if t.status.value == 'in_progress' if hasattr(t.status, 'value') else str(t.status) == 'in_progress')
        blocked_tasks = sum(1 for t in tasks if t.status.value == 'blocked' if hasattr(t.status, 'value') else str(t.status) == 'blocked')

        return {
            'project': {
                'id': project.id,
                'name': project.name,
                'progress_percentage': project.progress_percentage or 0,
                'status': project.status.value if hasattr(project.status, 'value') else str(project.status)
            },
            'phases': phase_details,
            'unassigned_tasks': unassigned_tasks,
            'stats': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'blocked_tasks': blocked_tasks,
                'pending_tasks': total_tasks - completed_tasks - in_progress_tasks - blocked_tasks
            }
        }
