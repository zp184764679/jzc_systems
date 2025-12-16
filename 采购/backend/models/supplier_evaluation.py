# models/supplier_evaluation.py
# -*- coding: utf-8 -*-
"""
供应商评估模型
包含：评估模板、评估指标、评估记录、评估得分
"""

from sqlalchemy import String, DateTime, Text, Float, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from extensions import db


# ==================== 枚举定义 ====================

class EvaluationPeriodType(enum.Enum):
    """评估周期类型"""
    MONTHLY = "monthly"          # 月度评估
    QUARTERLY = "quarterly"      # 季度评估
    SEMI_ANNUAL = "semi_annual"  # 半年度评估
    ANNUAL = "annual"            # 年度评估
    PROJECT = "project"          # 项目评估
    AD_HOC = "ad_hoc"            # 临时评估


class EvaluationStatus(enum.Enum):
    """评估状态"""
    DRAFT = "draft"              # 草稿
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消


class SupplierGrade(enum.Enum):
    """供应商等级"""
    A = "A"      # 优秀 (90-100)
    B = "B"      # 良好 (75-89)
    C = "C"      # 合格 (60-74)
    D = "D"      # 待改进 (40-59)
    E = "E"      # 不合格 (<40)


# 状态标签
EVALUATION_STATUS_LABELS = {
    'draft': '草稿',
    'in_progress': '进行中',
    'completed': '已完成',
    'cancelled': '已取消',
}

PERIOD_TYPE_LABELS = {
    'monthly': '月度',
    'quarterly': '季度',
    'semi_annual': '半年度',
    'annual': '年度',
    'project': '项目',
    'ad_hoc': '临时',
}

GRADE_LABELS = {
    'A': '优秀',
    'B': '良好',
    'C': '合格',
    'D': '待改进',
    'E': '不合格',
}


# ==================== 评估模板 ====================

class EvaluationTemplate(db.Model):
    """
    评估模板 - 定义评估结构和指标权重
    """
    __tablename__ = 'evaluation_templates'
    __table_args__ = (
        db.Index('idx_template_code', 'code'),
        db.Index('idx_template_status', 'is_active'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 模板基本信息
    code = db.Column(String(50), unique=True, nullable=False)  # 模板编码
    name = db.Column(String(100), nullable=False)  # 模板名称
    description = db.Column(Text, nullable=True)  # 模板描述

    # 适用范围
    supplier_category = db.Column(String(100), nullable=True)  # 适用供应商类别（可为空表示通用）

    # 评估周期
    period_type = db.Column(String(20), default='quarterly')  # 评估周期类型

    # 模板版本控制
    version = db.Column(String(20), default='1.0')  # 版本号
    is_active = db.Column(Boolean, default=True)  # 是否启用
    is_default = db.Column(Boolean, default=False)  # 是否默认模板

    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(BIGINT(unsigned=True), nullable=True)  # 创建人ID

    # 关联关系
    criteria = relationship(
        'EvaluationCriteria',
        back_populates='template',
        cascade='all, delete-orphan',
        order_by='EvaluationCriteria.sort_order'
    )

    evaluations = relationship(
        'SupplierEvaluation',
        back_populates='template',
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<EvaluationTemplate {self.code}: {self.name}>'

    def to_dict(self, include_criteria=False):
        """序列化为字典"""
        result = {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'supplier_category': self.supplier_category,
            'period_type': self.period_type,
            'period_type_label': PERIOD_TYPE_LABELS.get(self.period_type, self.period_type),
            'version': self.version,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'criteria_count': len(self.criteria) if self.criteria else 0,
            'total_weight': sum(c.weight for c in self.criteria) if self.criteria else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_criteria:
            result['criteria'] = [c.to_dict() for c in self.criteria]
        return result


# ==================== 评估指标 ====================

class EvaluationCriteria(db.Model):
    """
    评估指标 - 定义具体的评分项目
    """
    __tablename__ = 'evaluation_criteria'
    __table_args__ = (
        db.Index('idx_criteria_template', 'template_id'),
        db.Index('idx_criteria_category', 'category'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 关联模板
    template_id = db.Column(BIGINT(unsigned=True), ForeignKey('evaluation_templates.id', ondelete='CASCADE'), nullable=False)

    # 指标基本信息
    code = db.Column(String(50), nullable=False)  # 指标编码（模板内唯一）
    name = db.Column(String(100), nullable=False)  # 指标名称
    description = db.Column(Text, nullable=True)  # 指标说明/评分标准

    # 分类（方便分组展示）
    category = db.Column(String(50), nullable=False, default='general')
    # 常用分类: quality(质量), delivery(交期), service(服务), price(价格), technology(技术)

    # 权重和评分规则
    weight = db.Column(Float, default=10.0)  # 权重（百分比，所有指标权重之和应为100）
    max_score = db.Column(Float, default=100.0)  # 最高分
    min_score = db.Column(Float, default=0.0)  # 最低分

    # 评分方式
    score_type = db.Column(String(20), default='numeric')  # numeric(数值)/select(选择)
    score_options = db.Column(Text, nullable=True)  # JSON格式的选项（用于select类型）

    # 排序
    sort_order = db.Column(Integer, default=0)

    # 是否必填
    is_required = db.Column(Boolean, default=True)

    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    template = relationship('EvaluationTemplate', back_populates='criteria')
    scores = relationship('EvaluationScore', back_populates='criteria', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<EvaluationCriteria {self.code}: {self.name}>'

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'weight': self.weight,
            'max_score': self.max_score,
            'min_score': self.min_score,
            'score_type': self.score_type,
            'score_options': self.score_options,
            'sort_order': self.sort_order,
            'is_required': self.is_required,
        }


# ==================== 供应商评估记录 ====================

class SupplierEvaluation(db.Model):
    """
    供应商评估记录 - 一次完整的评估实例
    """
    __tablename__ = 'supplier_evaluations'
    __table_args__ = (
        db.Index('idx_eval_supplier', 'supplier_id'),
        db.Index('idx_eval_template', 'template_id'),
        db.Index('idx_eval_status', 'status'),
        db.Index('idx_eval_period', 'evaluation_period'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 评估编号（自动生成）
    evaluation_no = db.Column(String(50), unique=True, nullable=False)

    # 关联供应商
    supplier_id = db.Column(BIGINT(unsigned=True), ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False)

    # 关联模板
    template_id = db.Column(BIGINT(unsigned=True), ForeignKey('evaluation_templates.id'), nullable=False)

    # 评估周期信息
    evaluation_period = db.Column(String(50), nullable=False)  # 如：2025-Q1, 2025-01, 2025
    period_type = db.Column(String(20), default='quarterly')
    period_start = db.Column(DateTime, nullable=True)  # 评估周期开始
    period_end = db.Column(DateTime, nullable=True)  # 评估周期结束

    # 评估状态
    status = db.Column(String(20), default='draft')

    # 评估结果
    total_score = db.Column(Float, nullable=True)  # 总分（加权计算）
    grade = db.Column(String(10), nullable=True)  # 等级（A/B/C/D/E）

    # 各维度得分（JSON存储，方便快速查看）
    dimension_scores = db.Column(Text, nullable=True)  # JSON: {"quality": 85, "delivery": 90, ...}

    # 评估备注
    summary = db.Column(Text, nullable=True)  # 评估总结
    strengths = db.Column(Text, nullable=True)  # 优势
    weaknesses = db.Column(Text, nullable=True)  # 不足
    improvement_plan = db.Column(Text, nullable=True)  # 改进建议

    # 评估人
    evaluator_id = db.Column(BIGINT(unsigned=True), nullable=True)
    evaluator_name = db.Column(String(100), nullable=True)

    # 审核人
    reviewer_id = db.Column(BIGINT(unsigned=True), nullable=True)
    reviewer_name = db.Column(String(100), nullable=True)
    reviewed_at = db.Column(DateTime, nullable=True)
    review_comment = db.Column(Text, nullable=True)

    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(DateTime, nullable=True)

    # 关联关系
    template = relationship('EvaluationTemplate', back_populates='evaluations')
    supplier = relationship('Supplier', backref='evaluations')
    scores = relationship(
        'EvaluationScore',
        back_populates='evaluation',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<SupplierEvaluation {self.evaluation_no}>'

    def calculate_total_score(self):
        """计算总分（加权平均）"""
        if not self.scores:
            return None

        total_weighted_score = 0
        total_weight = 0

        for score in self.scores:
            if score.score is not None and score.criteria:
                weighted = score.score * (score.criteria.weight / 100)
                total_weighted_score += weighted
                total_weight += score.criteria.weight

        if total_weight > 0:
            # 归一化到100分制
            self.total_score = round(total_weighted_score * (100 / total_weight), 2)
        else:
            self.total_score = 0

        # 计算等级
        self.grade = self._calculate_grade(self.total_score)

        return self.total_score

    def _calculate_grade(self, score):
        """根据分数计算等级"""
        if score is None:
            return None
        if score >= 90:
            return 'A'
        elif score >= 75:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 40:
            return 'D'
        else:
            return 'E'

    def to_dict(self, include_scores=False):
        """序列化为字典"""
        result = {
            'id': self.id,
            'evaluation_no': self.evaluation_no,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.company_name if self.supplier else None,
            'template_id': self.template_id,
            'template_name': self.template.name if self.template else None,
            'evaluation_period': self.evaluation_period,
            'period_type': self.period_type,
            'period_type_label': PERIOD_TYPE_LABELS.get(self.period_type, self.period_type),
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'status': self.status,
            'status_label': EVALUATION_STATUS_LABELS.get(self.status, self.status),
            'total_score': self.total_score,
            'grade': self.grade,
            'grade_label': GRADE_LABELS.get(self.grade) if self.grade else None,
            'dimension_scores': self.dimension_scores,
            'summary': self.summary,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'improvement_plan': self.improvement_plan,
            'evaluator_id': self.evaluator_id,
            'evaluator_name': self.evaluator_name,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer_name,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_comment': self.review_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
        if include_scores:
            result['scores'] = [s.to_dict() for s in self.scores]
        return result


# ==================== 评估得分 ====================

class EvaluationScore(db.Model):
    """
    评估得分 - 单个指标的评分记录
    """
    __tablename__ = 'evaluation_scores'
    __table_args__ = (
        db.Index('idx_score_evaluation', 'evaluation_id'),
        db.Index('idx_score_criteria', 'criteria_id'),
    )

    id = db.Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

    # 关联评估记录
    evaluation_id = db.Column(BIGINT(unsigned=True), ForeignKey('supplier_evaluations.id', ondelete='CASCADE'), nullable=False)

    # 关联评估指标
    criteria_id = db.Column(BIGINT(unsigned=True), ForeignKey('evaluation_criteria.id', ondelete='CASCADE'), nullable=False)

    # 得分
    score = db.Column(Float, nullable=True)  # 原始得分
    weighted_score = db.Column(Float, nullable=True)  # 加权后得分

    # 评分备注/依据
    comment = db.Column(Text, nullable=True)
    evidence = db.Column(Text, nullable=True)  # 评分依据/证据

    # 时间戳
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    evaluation = relationship('SupplierEvaluation', back_populates='scores')
    criteria = relationship('EvaluationCriteria', back_populates='scores')

    def __repr__(self):
        return f'<EvaluationScore eval={self.evaluation_id} criteria={self.criteria_id}>'

    def calculate_weighted_score(self):
        """计算加权得分"""
        if self.score is not None and self.criteria:
            self.weighted_score = round(self.score * (self.criteria.weight / 100), 2)
        return self.weighted_score

    def to_dict(self):
        """序列化为字典"""
        return {
            'id': self.id,
            'evaluation_id': self.evaluation_id,
            'criteria_id': self.criteria_id,
            'criteria_code': self.criteria.code if self.criteria else None,
            'criteria_name': self.criteria.name if self.criteria else None,
            'criteria_category': self.criteria.category if self.criteria else None,
            'criteria_weight': self.criteria.weight if self.criteria else None,
            'score': self.score,
            'weighted_score': self.weighted_score,
            'comment': self.comment,
            'evidence': self.evidence,
        }


# ==================== 辅助函数 ====================

def generate_evaluation_no():
    """生成评估编号：EVAL-YYYYMMDD-XXXX"""
    from datetime import datetime
    today = datetime.now().strftime('%Y%m%d')

    # 查询今日最大编号
    latest = SupplierEvaluation.query.filter(
        SupplierEvaluation.evaluation_no.like(f'EVAL-{today}-%')
    ).order_by(SupplierEvaluation.evaluation_no.desc()).first()

    if latest:
        try:
            seq = int(latest.evaluation_no.split('-')[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1

    return f'EVAL-{today}-{seq:04d}'


def init_default_template():
    """初始化默认评估模板"""
    # 检查是否已存在默认模板
    existing = EvaluationTemplate.query.filter_by(code='TPL-DEFAULT').first()
    if existing:
        return existing

    # 创建默认模板
    template = EvaluationTemplate(
        code='TPL-DEFAULT',
        name='标准供应商评估模板',
        description='适用于一般供应商的综合评估',
        period_type='quarterly',
        is_active=True,
        is_default=True
    )
    db.session.add(template)
    db.session.flush()  # 获取ID

    # 添加默认评估指标
    default_criteria = [
        # 质量维度 (40%)
        {'code': 'Q1', 'name': '产品合格率', 'category': 'quality', 'weight': 15, 'description': '交货产品的合格率，计算公式：合格数量/交货数量×100'},
        {'code': 'Q2', 'name': '质量问题响应', 'category': 'quality', 'weight': 10, 'description': '质量问题发生后的响应速度和处理效果'},
        {'code': 'Q3', 'name': '质量改进能力', 'category': 'quality', 'weight': 10, 'description': '质量问题的根本原因分析和预防措施实施'},
        {'code': 'Q4', 'name': '质量体系认证', 'category': 'quality', 'weight': 5, 'description': 'ISO9001等质量体系认证情况'},

        # 交期维度 (25%)
        {'code': 'D1', 'name': '准时交货率', 'category': 'delivery', 'weight': 15, 'description': '按时交货的订单比例'},
        {'code': 'D2', 'name': '交期变更沟通', 'category': 'delivery', 'weight': 5, 'description': '交期变更时的提前沟通和解决方案'},
        {'code': 'D3', 'name': '紧急需求响应', 'category': 'delivery', 'weight': 5, 'description': '应对紧急订单或需求变更的能力'},

        # 服务维度 (15%)
        {'code': 'S1', 'name': '沟通配合度', 'category': 'service', 'weight': 5, 'description': '日常沟通的及时性和有效性'},
        {'code': 'S2', 'name': '售后服务', 'category': 'service', 'weight': 5, 'description': '售后问题处理的响应速度和解决效果'},
        {'code': 'S3', 'name': '技术支持', 'category': 'service', 'weight': 5, 'description': '提供技术支持和解决方案的能力'},

        # 价格维度 (15%)
        {'code': 'P1', 'name': '价格竞争力', 'category': 'price', 'weight': 10, 'description': '与市场价格相比的竞争力'},
        {'code': 'P2', 'name': '成本控制配合', 'category': 'price', 'weight': 5, 'description': '配合成本优化和VA/VE活动'},

        # 综合维度 (5%)
        {'code': 'G1', 'name': '合规与风险', 'category': 'general', 'weight': 5, 'description': '合规经营、财务稳定性、供应风险'},
    ]

    for i, c in enumerate(default_criteria):
        criteria = EvaluationCriteria(
            template_id=template.id,
            code=c['code'],
            name=c['name'],
            category=c['category'],
            weight=c['weight'],
            description=c['description'],
            max_score=100,
            min_score=0,
            score_type='numeric',
            sort_order=i,
            is_required=True
        )
        db.session.add(criteria)

    db.session.commit()
    return template
