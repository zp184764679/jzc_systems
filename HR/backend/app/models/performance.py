"""
绩效管理数据模型
包含: 考核周期、KPI模板、绩效目标、绩效评估
"""
from app import db
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Date, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum


class PerformancePeriodType(enum.Enum):
    """考核周期类型"""
    MONTHLY = 'monthly'        # 月度
    QUARTERLY = 'quarterly'    # 季度
    SEMI_ANNUAL = 'semi_annual'  # 半年
    ANNUAL = 'annual'          # 年度


class PerformanceStatus(enum.Enum):
    """绩效状态"""
    NOT_STARTED = 'not_started'  # 未开始
    IN_PROGRESS = 'in_progress'  # 进行中
    SELF_EVALUATION = 'self_evaluation'  # 自评阶段
    MANAGER_EVALUATION = 'manager_evaluation'  # 主管评估
    CALIBRATION = 'calibration'  # 校准阶段
    COMPLETED = 'completed'    # 已完成
    ARCHIVED = 'archived'      # 已归档


class GoalStatus(enum.Enum):
    """目标状态"""
    PENDING = 'pending'        # 待确认
    CONFIRMED = 'confirmed'    # 已确认
    IN_PROGRESS = 'in_progress'  # 进行中
    COMPLETED = 'completed'    # 已完成
    CANCELLED = 'cancelled'    # 已取消


class PerformancePeriod(db.Model):
    """考核周期表"""
    __tablename__ = 'performance_periods'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='周期名称')
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='周期编码')
    period_type: Mapped[str] = mapped_column(String(20), nullable=False, comment='周期类型')
    year: Mapped[int] = mapped_column(Integer, nullable=False, comment='年份')

    # 时间范围
    start_date: Mapped[date] = mapped_column(Date, nullable=False, comment='开始日期')
    end_date: Mapped[date] = mapped_column(Date, nullable=False, comment='结束日期')

    # 各阶段时间
    goal_setting_start: Mapped[Optional[date]] = mapped_column(Date, comment='目标设定开始')
    goal_setting_end: Mapped[Optional[date]] = mapped_column(Date, comment='目标设定结束')
    self_evaluation_start: Mapped[Optional[date]] = mapped_column(Date, comment='自评开始')
    self_evaluation_end: Mapped[Optional[date]] = mapped_column(Date, comment='自评结束')
    manager_evaluation_start: Mapped[Optional[date]] = mapped_column(Date, comment='主管评估开始')
    manager_evaluation_end: Mapped[Optional[date]] = mapped_column(Date, comment='主管评估结束')
    calibration_start: Mapped[Optional[date]] = mapped_column(Date, comment='校准开始')
    calibration_end: Mapped[Optional[date]] = mapped_column(Date, comment='校准结束')

    # 状态
    status: Mapped[str] = mapped_column(String(20), default='not_started', comment='状态')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')

    # 适用范围
    department_ids: Mapped[Optional[str]] = mapped_column(JSON, comment='适用部门IDs')
    factory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('factories.id'), comment='适用工厂')

    # 备注
    description: Mapped[Optional[str]] = mapped_column(Text, comment='描述')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人')

    # 关系
    factory = relationship('Factory', backref='performance_periods')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'period_type': self.period_type,
            'year': self.year,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'goal_setting_start': self.goal_setting_start.strftime('%Y-%m-%d') if self.goal_setting_start else None,
            'goal_setting_end': self.goal_setting_end.strftime('%Y-%m-%d') if self.goal_setting_end else None,
            'self_evaluation_start': self.self_evaluation_start.strftime('%Y-%m-%d') if self.self_evaluation_start else None,
            'self_evaluation_end': self.self_evaluation_end.strftime('%Y-%m-%d') if self.self_evaluation_end else None,
            'manager_evaluation_start': self.manager_evaluation_start.strftime('%Y-%m-%d') if self.manager_evaluation_start else None,
            'manager_evaluation_end': self.manager_evaluation_end.strftime('%Y-%m-%d') if self.manager_evaluation_end else None,
            'calibration_start': self.calibration_start.strftime('%Y-%m-%d') if self.calibration_start else None,
            'calibration_end': self.calibration_end.strftime('%Y-%m-%d') if self.calibration_end else None,
            'status': self.status,
            'is_active': self.is_active,
            'department_ids': self.department_ids,
            'factory_id': self.factory_id,
            'factory_name': self.factory.name if self.factory else None,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class KPITemplate(db.Model):
    """KPI模板表"""
    __tablename__ = 'kpi_templates'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='模板编码')
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment='KPI名称')
    category: Mapped[str] = mapped_column(String(50), default='work', comment='分类(work/behavior/growth)')

    # 权重和评分
    default_weight: Mapped[float] = mapped_column(Float, default=0, comment='默认权重(%)')
    max_score: Mapped[float] = mapped_column(Float, default=100, comment='最高分')
    min_score: Mapped[float] = mapped_column(Float, default=0, comment='最低分')

    # 评分标准
    scoring_criteria: Mapped[Optional[str]] = mapped_column(JSON, comment='评分标准')
    # 格式: [{"score": 100, "description": "超额完成"}, {"score": 80, "description": "完成"}]

    # 适用范围
    applicable_positions: Mapped[Optional[str]] = mapped_column(JSON, comment='适用职位IDs')
    applicable_departments: Mapped[Optional[str]] = mapped_column(JSON, comment='适用部门IDs')

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment='排序')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='描述')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'category': self.category,
            'default_weight': self.default_weight,
            'max_score': self.max_score,
            'min_score': self.min_score,
            'scoring_criteria': self.scoring_criteria,
            'applicable_positions': self.applicable_positions,
            'applicable_departments': self.applicable_departments,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class PerformanceGoal(db.Model):
    """绩效目标表"""
    __tablename__ = 'performance_goals'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    period_id: Mapped[int] = mapped_column(Integer, ForeignKey('performance_periods.id'), nullable=False, comment='考核周期ID')
    kpi_template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('kpi_templates.id'), comment='KPI模板ID')

    # 目标信息
    goal_name: Mapped[str] = mapped_column(String(200), nullable=False, comment='目标名称')
    goal_description: Mapped[Optional[str]] = mapped_column(Text, comment='目标描述')
    category: Mapped[str] = mapped_column(String(50), default='work', comment='分类')

    # 目标值
    target_value: Mapped[Optional[str]] = mapped_column(String(200), comment='目标值')
    target_unit: Mapped[Optional[str]] = mapped_column(String(50), comment='目标单位')
    actual_value: Mapped[Optional[str]] = mapped_column(String(200), comment='实际完成值')

    # 权重和评分
    weight: Mapped[float] = mapped_column(Float, default=0, comment='权重(%)')
    max_score: Mapped[float] = mapped_column(Float, default=100, comment='满分')

    # 自评
    self_score: Mapped[Optional[float]] = mapped_column(Float, comment='自评分数')
    self_comment: Mapped[Optional[str]] = mapped_column(Text, comment='自评说明')
    self_evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='自评时间')

    # 主管评分
    manager_score: Mapped[Optional[float]] = mapped_column(Float, comment='主管评分')
    manager_comment: Mapped[Optional[str]] = mapped_column(Text, comment='主管评语')
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, comment='评估主管ID')
    manager_evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='主管评估时间')

    # 最终评分
    final_score: Mapped[Optional[float]] = mapped_column(Float, comment='最终得分')
    weighted_score: Mapped[Optional[float]] = mapped_column(Float, comment='加权得分')

    # 状态
    status: Mapped[str] = mapped_column(String(20), default='pending', comment='目标状态')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    employee = relationship('Employee', backref='performance_goals')
    period = relationship('PerformancePeriod', backref='goals')
    kpi_template = relationship('KPITemplate', backref='goals')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'period_id': self.period_id,
            'period_name': self.period.name if self.period else None,
            'kpi_template_id': self.kpi_template_id,
            'kpi_template_name': self.kpi_template.name if self.kpi_template else None,
            'goal_name': self.goal_name,
            'goal_description': self.goal_description,
            'category': self.category,
            'target_value': self.target_value,
            'target_unit': self.target_unit,
            'actual_value': self.actual_value,
            'weight': self.weight,
            'max_score': self.max_score,
            'self_score': self.self_score,
            'self_comment': self.self_comment,
            'self_evaluated_at': self.self_evaluated_at.strftime('%Y-%m-%d %H:%M:%S') if self.self_evaluated_at else None,
            'manager_score': self.manager_score,
            'manager_comment': self.manager_comment,
            'manager_id': self.manager_id,
            'manager_evaluated_at': self.manager_evaluated_at.strftime('%Y-%m-%d %H:%M:%S') if self.manager_evaluated_at else None,
            'final_score': self.final_score,
            'weighted_score': self.weighted_score,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class PerformanceEvaluation(db.Model):
    """绩效评估表 - 员工周期总评"""
    __tablename__ = 'performance_evaluations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    period_id: Mapped[int] = mapped_column(Integer, ForeignKey('performance_periods.id'), nullable=False, comment='考核周期ID')

    # 总评分
    total_weight: Mapped[float] = mapped_column(Float, default=0, comment='总权重')
    self_total_score: Mapped[Optional[float]] = mapped_column(Float, comment='自评总分')
    manager_total_score: Mapped[Optional[float]] = mapped_column(Float, comment='主管评估总分')
    final_total_score: Mapped[Optional[float]] = mapped_column(Float, comment='最终总分')

    # 等级评定
    grade: Mapped[Optional[str]] = mapped_column(String(20), comment='绩效等级(A/B/C/D/E)')
    grade_description: Mapped[Optional[str]] = mapped_column(String(100), comment='等级描述')

    # 排名
    department_rank: Mapped[Optional[int]] = mapped_column(Integer, comment='部门排名')
    company_rank: Mapped[Optional[int]] = mapped_column(Integer, comment='公司排名')

    # 评语
    self_summary: Mapped[Optional[str]] = mapped_column(Text, comment='自评总结')
    manager_summary: Mapped[Optional[str]] = mapped_column(Text, comment='主管总评')
    improvement_suggestions: Mapped[Optional[str]] = mapped_column(Text, comment='改进建议')
    development_plan: Mapped[Optional[str]] = mapped_column(Text, comment='发展计划')

    # 评估人
    evaluator_id: Mapped[Optional[int]] = mapped_column(Integer, comment='评估人ID')
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='评估时间')

    # 校准
    is_calibrated: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否已校准')
    calibrated_by: Mapped[Optional[int]] = mapped_column(Integer, comment='校准人')
    calibrated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='校准时间')
    calibration_reason: Mapped[Optional[str]] = mapped_column(Text, comment='校准原因')
    score_before_calibration: Mapped[Optional[float]] = mapped_column(Float, comment='校准前分数')

    # 状态
    status: Mapped[str] = mapped_column(String(20), default='not_started', comment='评估状态')
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否锁定')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    employee = relationship('Employee', backref='performance_evaluations')
    period = relationship('PerformancePeriod', backref='evaluations')

    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'period_id', name='uq_employee_period'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'employee_no': self.employee.empNo if self.employee else None,
            'department': self.employee.department if self.employee else None,
            'period_id': self.period_id,
            'period_name': self.period.name if self.period else None,
            'total_weight': self.total_weight,
            'self_total_score': self.self_total_score,
            'manager_total_score': self.manager_total_score,
            'final_total_score': self.final_total_score,
            'grade': self.grade,
            'grade_description': self.grade_description,
            'department_rank': self.department_rank,
            'company_rank': self.company_rank,
            'self_summary': self.self_summary,
            'manager_summary': self.manager_summary,
            'improvement_suggestions': self.improvement_suggestions,
            'development_plan': self.development_plan,
            'evaluator_id': self.evaluator_id,
            'evaluated_at': self.evaluated_at.strftime('%Y-%m-%d %H:%M:%S') if self.evaluated_at else None,
            'is_calibrated': self.is_calibrated,
            'calibrated_at': self.calibrated_at.strftime('%Y-%m-%d %H:%M:%S') if self.calibrated_at else None,
            'calibration_reason': self.calibration_reason,
            'score_before_calibration': self.score_before_calibration,
            'status': self.status,
            'is_locked': self.is_locked,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class PerformanceGradeConfig(db.Model):
    """绩效等级配置表"""
    __tablename__ = 'performance_grade_configs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grade: Mapped[str] = mapped_column(String(20), nullable=False, comment='等级')
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment='等级名称')
    min_score: Mapped[float] = mapped_column(Float, nullable=False, comment='最低分')
    max_score: Mapped[float] = mapped_column(Float, nullable=False, comment='最高分')

    # 比例控制
    target_percentage: Mapped[Optional[float]] = mapped_column(Float, comment='目标比例(%)')
    max_percentage: Mapped[Optional[float]] = mapped_column(Float, comment='最大比例(%)')

    # 奖金系数
    bonus_coefficient: Mapped[float] = mapped_column(Float, default=1.0, comment='奖金系数')

    # 排序
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment='排序')
    color: Mapped[Optional[str]] = mapped_column(String(20), comment='显示颜色')
    description: Mapped[Optional[str]] = mapped_column(Text, comment='等级描述')

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否启用')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'grade': self.grade,
            'name': self.name,
            'min_score': self.min_score,
            'max_score': self.max_score,
            'target_percentage': self.target_percentage,
            'max_percentage': self.max_percentage,
            'bonus_coefficient': self.bonus_coefficient,
            'sort_order': self.sort_order,
            'color': self.color,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class PerformanceFeedback(db.Model):
    """绩效反馈记录表"""
    __tablename__ = 'performance_feedbacks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    period_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('performance_periods.id'), comment='考核周期ID')
    goal_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('performance_goals.id'), comment='关联目标ID')

    # 反馈信息
    feedback_type: Mapped[str] = mapped_column(String(20), default='general', comment='反馈类型(praise/improvement/general)')
    content: Mapped[str] = mapped_column(Text, nullable=False, comment='反馈内容')

    # 反馈人
    feedback_by: Mapped[int] = mapped_column(Integer, nullable=False, comment='反馈人ID')
    feedback_by_name: Mapped[Optional[str]] = mapped_column(String(100), comment='反馈人姓名')

    # 可见性
    is_visible_to_employee: Mapped[bool] = mapped_column(Boolean, default=True, comment='员工可见')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    employee = relationship('Employee', backref='performance_feedbacks')
    period = relationship('PerformancePeriod', backref='feedbacks')
    goal = relationship('PerformanceGoal', backref='feedbacks')

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'employee_name': self.employee.name if self.employee else None,
            'period_id': self.period_id,
            'period_name': self.period.name if self.period else None,
            'goal_id': self.goal_id,
            'goal_name': self.goal.goal_name if self.goal else None,
            'feedback_type': self.feedback_type,
            'content': self.content,
            'feedback_by': self.feedback_by,
            'feedback_by_name': self.feedback_by_name,
            'is_visible_to_employee': self.is_visible_to_employee,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


def init_default_grade_configs():
    """初始化默认绩效等级配置"""
    default_grades = [
        {'grade': 'A', 'name': '卓越', 'min_score': 90, 'max_score': 100, 'target_percentage': 10, 'bonus_coefficient': 1.5, 'sort_order': 1, 'color': '#52c41a'},
        {'grade': 'B', 'name': '优秀', 'min_score': 80, 'max_score': 89.99, 'target_percentage': 25, 'bonus_coefficient': 1.2, 'sort_order': 2, 'color': '#1890ff'},
        {'grade': 'C', 'name': '称职', 'min_score': 70, 'max_score': 79.99, 'target_percentage': 50, 'bonus_coefficient': 1.0, 'sort_order': 3, 'color': '#faad14'},
        {'grade': 'D', 'name': '待改进', 'min_score': 60, 'max_score': 69.99, 'target_percentage': 10, 'bonus_coefficient': 0.8, 'sort_order': 4, 'color': '#fa8c16'},
        {'grade': 'E', 'name': '不合格', 'min_score': 0, 'max_score': 59.99, 'target_percentage': 5, 'bonus_coefficient': 0, 'sort_order': 5, 'color': '#f5222d'},
    ]

    for grade_data in default_grades:
        existing = PerformanceGradeConfig.query.filter_by(grade=grade_data['grade']).first()
        if not existing:
            grade = PerformanceGradeConfig(**grade_data)
            db.session.add(grade)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"初始化绩效等级配置失败: {e}")


def init_default_kpi_templates():
    """初始化默认KPI模板"""
    default_templates = [
        {'code': 'work_quality', 'name': '工作质量', 'category': 'work', 'default_weight': 20, 'description': '工作成果的准确性、完整性和专业度'},
        {'code': 'work_efficiency', 'name': '工作效率', 'category': 'work', 'default_weight': 15, 'description': '完成工作的速度和资源利用效率'},
        {'code': 'task_completion', 'name': '任务完成率', 'category': 'work', 'default_weight': 20, 'description': '按时完成分配任务的比例'},
        {'code': 'innovation', 'name': '创新能力', 'category': 'work', 'default_weight': 10, 'description': '提出新想法和改进建议的能力'},
        {'code': 'teamwork', 'name': '团队协作', 'category': 'behavior', 'default_weight': 15, 'description': '与同事合作的能力和态度'},
        {'code': 'communication', 'name': '沟通能力', 'category': 'behavior', 'default_weight': 10, 'description': '有效沟通和表达的能力'},
        {'code': 'attendance', 'name': '出勤纪律', 'category': 'behavior', 'default_weight': 5, 'description': '遵守工作时间和公司规定'},
        {'code': 'learning', 'name': '学习成长', 'category': 'growth', 'default_weight': 5, 'description': '主动学习和自我提升'},
    ]

    for template_data in default_templates:
        existing = KPITemplate.query.filter_by(code=template_data['code']).first()
        if not existing:
            template = KPITemplate(**template_data)
            db.session.add(template)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"初始化KPI模板失败: {e}")
