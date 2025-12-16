"""
招聘管理数据模型
包含: 职位发布、应聘申请、面试安排、面试评价
"""
from app import db
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Date, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum


class JobStatus(enum.Enum):
    """职位状态"""
    DRAFT = 'draft'          # 草稿
    OPEN = 'open'            # 开放招聘
    PAUSED = 'paused'        # 暂停招聘
    CLOSED = 'closed'        # 已关闭
    FILLED = 'filled'        # 已招满


class ApplicationStatus(enum.Enum):
    """应聘状态"""
    PENDING = 'pending'           # 待筛选
    SCREENING = 'screening'       # 筛选中
    INTERVIEW = 'interview'       # 面试中
    OFFER = 'offer'               # 已发offer
    HIRED = 'hired'               # 已录用
    REJECTED = 'rejected'         # 已拒绝
    WITHDRAWN = 'withdrawn'       # 已撤回


class InterviewStatus(enum.Enum):
    """面试状态"""
    SCHEDULED = 'scheduled'       # 已安排
    CONFIRMED = 'confirmed'       # 已确认
    IN_PROGRESS = 'in_progress'   # 进行中
    COMPLETED = 'completed'       # 已完成
    CANCELLED = 'cancelled'       # 已取消
    NO_SHOW = 'no_show'           # 未到场


class InterviewType(enum.Enum):
    """面试类型"""
    PHONE = 'phone'              # 电话面试
    VIDEO = 'video'              # 视频面试
    ONSITE = 'onsite'            # 现场面试
    TECHNICAL = 'technical'      # 技术面试
    HR = 'hr'                    # HR面试
    FINAL = 'final'              # 终面


class JobPosting(db.Model):
    """职位发布表"""
    __tablename__ = 'job_postings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='职位编码')
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment='职位名称')

    # 关联字段
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('departments.id'), comment='招聘部门')
    position_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('positions.id'), comment='关联职位')
    factory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('factories.id'), comment='工作地点(工厂)')

    # 招聘信息
    headcount: Mapped[int] = mapped_column(Integer, default=1, comment='招聘人数')
    hired_count: Mapped[int] = mapped_column(Integer, default=0, comment='已录用人数')
    urgency: Mapped[str] = mapped_column(String(20), default='normal', comment='紧急程度(urgent/normal/low)')
    job_type: Mapped[str] = mapped_column(String(20), default='full_time', comment='工作类型(full_time/part_time/intern/contract)')

    # 要求条件
    education_requirement: Mapped[Optional[str]] = mapped_column(String(50), comment='学历要求')
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, comment='经验年限要求')
    age_min: Mapped[Optional[int]] = mapped_column(Integer, comment='最小年龄')
    age_max: Mapped[Optional[int]] = mapped_column(Integer, comment='最大年龄')
    gender_requirement: Mapped[Optional[str]] = mapped_column(String(10), comment='性别要求(male/female/null=不限)')
    skills: Mapped[Optional[str]] = mapped_column(JSON, comment='技能要求(JSON数组)')

    # 薪资信息
    salary_min: Mapped[Optional[float]] = mapped_column(Float, comment='薪资下限')
    salary_max: Mapped[Optional[float]] = mapped_column(Float, comment='薪资上限')
    salary_type: Mapped[str] = mapped_column(String(20), default='monthly', comment='薪资类型(hourly/daily/monthly)')
    salary_negotiable: Mapped[bool] = mapped_column(Boolean, default=True, comment='薪资面议')

    # 职位描述
    description: Mapped[Optional[str]] = mapped_column(Text, comment='职位描述')
    requirements: Mapped[Optional[str]] = mapped_column(Text, comment='任职要求')
    benefits: Mapped[Optional[str]] = mapped_column(Text, comment='福利待遇')

    # 状态和时间
    status: Mapped[str] = mapped_column(String(20), default='draft', comment='状态')
    publish_date: Mapped[Optional[date]] = mapped_column(Date, comment='发布日期')
    expire_date: Mapped[Optional[date]] = mapped_column(Date, comment='截止日期')

    # 招聘负责人
    recruiter_id: Mapped[Optional[int]] = mapped_column(Integer, comment='招聘负责人ID(员工ID)')
    hiring_manager_id: Mapped[Optional[int]] = mapped_column(Integer, comment='用人经理ID(员工ID)')

    # 统计
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment='浏览次数')
    apply_count: Mapped[int] = mapped_column(Integer, default=0, comment='申请次数')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')

    # 关系
    applications = relationship('JobApplication', back_populates='job_posting', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'job_code': self.job_code,
            'title': self.title,
            'department_id': self.department_id,
            'position_id': self.position_id,
            'factory_id': self.factory_id,
            'headcount': self.headcount,
            'hired_count': self.hired_count,
            'urgency': self.urgency,
            'job_type': self.job_type,
            'education_requirement': self.education_requirement,
            'experience_years': self.experience_years,
            'age_min': self.age_min,
            'age_max': self.age_max,
            'gender_requirement': self.gender_requirement,
            'skills': self.skills,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'salary_type': self.salary_type,
            'salary_negotiable': self.salary_negotiable,
            'description': self.description,
            'requirements': self.requirements,
            'benefits': self.benefits,
            'status': self.status,
            'publish_date': self.publish_date.strftime('%Y-%m-%d') if self.publish_date else None,
            'expire_date': self.expire_date.strftime('%Y-%m-%d') if self.expire_date else None,
            'recruiter_id': self.recruiter_id,
            'hiring_manager_id': self.hiring_manager_id,
            'view_count': self.view_count,
            'apply_count': self.apply_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'created_by': self.created_by
        }


class JobApplication(db.Model):
    """应聘申请表"""
    __tablename__ = 'job_applications'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment='申请编号')

    # 关联职位
    job_posting_id: Mapped[int] = mapped_column(Integer, ForeignKey('job_postings.id'), nullable=False, comment='职位ID')

    # 候选人基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='姓名')
    gender: Mapped[Optional[str]] = mapped_column(String(10), comment='性别')
    birth_date: Mapped[Optional[date]] = mapped_column(Date, comment='出生日期')
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment='手机号码')
    email: Mapped[Optional[str]] = mapped_column(String(100), comment='邮箱')
    id_card: Mapped[Optional[str]] = mapped_column(String(50), comment='身份证号')

    # 学历和工作经验
    education: Mapped[Optional[str]] = mapped_column(String(50), comment='最高学历')
    major: Mapped[Optional[str]] = mapped_column(String(100), comment='专业')
    school: Mapped[Optional[str]] = mapped_column(String(200), comment='毕业院校')
    graduation_date: Mapped[Optional[date]] = mapped_column(Date, comment='毕业日期')
    work_experience_years: Mapped[Optional[int]] = mapped_column(Integer, comment='工作年限')
    current_company: Mapped[Optional[str]] = mapped_column(String(200), comment='当前公司')
    current_position: Mapped[Optional[str]] = mapped_column(String(100), comment='当前职位')

    # 期望信息
    expected_salary: Mapped[Optional[float]] = mapped_column(Float, comment='期望薪资')
    available_date: Mapped[Optional[date]] = mapped_column(Date, comment='可入职日期')

    # 简历和附件
    resume_url: Mapped[Optional[str]] = mapped_column(String(500), comment='简历文件URL')
    resume_text: Mapped[Optional[str]] = mapped_column(Text, comment='简历文本内容')
    attachments: Mapped[Optional[str]] = mapped_column(JSON, comment='其他附件(JSON)')

    # 来源
    source: Mapped[str] = mapped_column(String(50), default='direct', comment='来源(direct/referral/job_site/campus)')
    referrer_id: Mapped[Optional[int]] = mapped_column(Integer, comment='推荐人ID(员工ID)')
    referrer_name: Mapped[Optional[str]] = mapped_column(String(100), comment='推荐人姓名')

    # 状态
    status: Mapped[str] = mapped_column(String(20), default='pending', comment='状态')
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, comment='拒绝原因')

    # 评分和评语
    screening_score: Mapped[Optional[int]] = mapped_column(Integer, comment='筛选评分(1-100)')
    screening_notes: Mapped[Optional[str]] = mapped_column(Text, comment='筛选备注')
    overall_score: Mapped[Optional[int]] = mapped_column(Integer, comment='综合评分(1-100)')

    # Offer信息
    offer_salary: Mapped[Optional[float]] = mapped_column(Float, comment='Offer薪资')
    offer_date: Mapped[Optional[date]] = mapped_column(Date, comment='发Offer日期')
    offer_expire_date: Mapped[Optional[date]] = mapped_column(Date, comment='Offer有效期')
    offer_accepted_date: Mapped[Optional[date]] = mapped_column(Date, comment='接受Offer日期')

    # 入职信息
    hire_date: Mapped[Optional[date]] = mapped_column(Date, comment='入职日期')
    employee_id: Mapped[Optional[int]] = mapped_column(Integer, comment='转正后员工ID')

    # 时间戳
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='申请时间')
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    job_posting = relationship('JobPosting', back_populates='applications')
    interviews = relationship('Interview', back_populates='application', lazy='dynamic')

    def to_dict(self, include_job=False):
        result = {
            'id': self.id,
            'application_no': self.application_no,
            'job_posting_id': self.job_posting_id,
            'name': self.name,
            'gender': self.gender,
            'birth_date': self.birth_date.strftime('%Y-%m-%d') if self.birth_date else None,
            'phone': self.phone,
            'email': self.email,
            'id_card': self.id_card,
            'education': self.education,
            'major': self.major,
            'school': self.school,
            'graduation_date': self.graduation_date.strftime('%Y-%m-%d') if self.graduation_date else None,
            'work_experience_years': self.work_experience_years,
            'current_company': self.current_company,
            'current_position': self.current_position,
            'expected_salary': self.expected_salary,
            'available_date': self.available_date.strftime('%Y-%m-%d') if self.available_date else None,
            'resume_url': self.resume_url,
            'source': self.source,
            'referrer_id': self.referrer_id,
            'referrer_name': self.referrer_name,
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'screening_score': self.screening_score,
            'screening_notes': self.screening_notes,
            'overall_score': self.overall_score,
            'offer_salary': self.offer_salary,
            'offer_date': self.offer_date.strftime('%Y-%m-%d') if self.offer_date else None,
            'offer_expire_date': self.offer_expire_date.strftime('%Y-%m-%d') if self.offer_expire_date else None,
            'offer_accepted_date': self.offer_accepted_date.strftime('%Y-%m-%d') if self.offer_accepted_date else None,
            'hire_date': self.hire_date.strftime('%Y-%m-%d') if self.hire_date else None,
            'employee_id': self.employee_id,
            'applied_at': self.applied_at.strftime('%Y-%m-%d %H:%M:%S') if self.applied_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        if include_job and self.job_posting:
            result['job_posting'] = self.job_posting.to_dict()
        return result


class Interview(db.Model):
    """面试安排表"""
    __tablename__ = 'interviews'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey('job_applications.id'), nullable=False, comment='申请ID')

    # 面试信息
    interview_round: Mapped[int] = mapped_column(Integer, default=1, comment='面试轮次')
    interview_type: Mapped[str] = mapped_column(String(20), default='onsite', comment='面试类型')

    # 时间和地点
    scheduled_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment='预约时间')
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, comment='预计时长(分钟)')
    location: Mapped[Optional[str]] = mapped_column(String(200), comment='面试地点')
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), comment='视频会议链接')

    # 面试官
    interviewer_ids: Mapped[Optional[str]] = mapped_column(JSON, comment='面试官ID列表(JSON)')
    interviewer_names: Mapped[Optional[str]] = mapped_column(String(500), comment='面试官姓名(逗号分隔)')

    # 状态
    status: Mapped[str] = mapped_column(String(20), default='scheduled', comment='状态')
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='实际开始时间')
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, comment='实际结束时间')

    # 通知
    candidate_notified: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否已通知候选人')
    candidate_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, comment='候选人是否确认')
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否已发提醒')

    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='面试备注')
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, comment='取消原因')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')

    # 关系
    application = relationship('JobApplication', back_populates='interviews')
    evaluations = relationship('InterviewEvaluation', back_populates='interview', lazy='dynamic')

    def to_dict(self, include_application=False):
        result = {
            'id': self.id,
            'application_id': self.application_id,
            'interview_round': self.interview_round,
            'interview_type': self.interview_type,
            'scheduled_time': self.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if self.scheduled_time else None,
            'duration_minutes': self.duration_minutes,
            'location': self.location,
            'meeting_link': self.meeting_link,
            'interviewer_ids': self.interviewer_ids,
            'interviewer_names': self.interviewer_names,
            'status': self.status,
            'actual_start_time': self.actual_start_time.strftime('%Y-%m-%d %H:%M:%S') if self.actual_start_time else None,
            'actual_end_time': self.actual_end_time.strftime('%Y-%m-%d %H:%M:%S') if self.actual_end_time else None,
            'candidate_notified': self.candidate_notified,
            'candidate_confirmed': self.candidate_confirmed,
            'reminder_sent': self.reminder_sent,
            'notes': self.notes,
            'cancel_reason': self.cancel_reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'created_by': self.created_by
        }
        if include_application and self.application:
            result['application'] = self.application.to_dict()
        return result


class InterviewEvaluation(db.Model):
    """面试评价表"""
    __tablename__ = 'interview_evaluations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联
    interview_id: Mapped[int] = mapped_column(Integer, ForeignKey('interviews.id'), nullable=False, comment='面试ID')
    evaluator_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='评价人ID(员工ID)')
    evaluator_name: Mapped[str] = mapped_column(String(100), nullable=False, comment='评价人姓名')

    # 评分项 (1-5分)
    technical_score: Mapped[Optional[int]] = mapped_column(Integer, comment='技术能力评分')
    communication_score: Mapped[Optional[int]] = mapped_column(Integer, comment='沟通能力评分')
    teamwork_score: Mapped[Optional[int]] = mapped_column(Integer, comment='团队协作评分')
    problem_solving_score: Mapped[Optional[int]] = mapped_column(Integer, comment='问题解决能力评分')
    culture_fit_score: Mapped[Optional[int]] = mapped_column(Integer, comment='文化匹配度评分')
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False, comment='综合评分(1-5)')

    # 评价内容
    strengths: Mapped[Optional[str]] = mapped_column(Text, comment='优点')
    weaknesses: Mapped[Optional[str]] = mapped_column(Text, comment='不足')
    questions_asked: Mapped[Optional[str]] = mapped_column(Text, comment='提问内容')
    candidate_answers: Mapped[Optional[str]] = mapped_column(Text, comment='候选人回答要点')

    # 推荐意见
    recommendation: Mapped[str] = mapped_column(String(20), default='pending', comment='推荐意见(strong_yes/yes/neutral/no/strong_no)')
    recommendation_reason: Mapped[Optional[str]] = mapped_column(Text, comment='推荐理由')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    interview = relationship('Interview', back_populates='evaluations')

    def to_dict(self):
        return {
            'id': self.id,
            'interview_id': self.interview_id,
            'evaluator_id': self.evaluator_id,
            'evaluator_name': self.evaluator_name,
            'technical_score': self.technical_score,
            'communication_score': self.communication_score,
            'teamwork_score': self.teamwork_score,
            'problem_solving_score': self.problem_solving_score,
            'culture_fit_score': self.culture_fit_score,
            'overall_score': self.overall_score,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'questions_asked': self.questions_asked,
            'candidate_answers': self.candidate_answers,
            'recommendation': self.recommendation,
            'recommendation_reason': self.recommendation_reason,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class TalentPool(db.Model):
    """人才库表"""
    __tablename__ = 'talent_pool'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 来源
    application_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('job_applications.id'), comment='原申请ID')

    # 候选人信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='姓名')
    phone: Mapped[str] = mapped_column(String(20), nullable=False, comment='手机号码')
    email: Mapped[Optional[str]] = mapped_column(String(100), comment='邮箱')
    education: Mapped[Optional[str]] = mapped_column(String(50), comment='学历')
    work_experience_years: Mapped[Optional[int]] = mapped_column(Integer, comment='工作年限')
    skills: Mapped[Optional[str]] = mapped_column(JSON, comment='技能标签(JSON)')

    # 期望
    expected_positions: Mapped[Optional[str]] = mapped_column(JSON, comment='期望职位(JSON)')
    expected_salary_min: Mapped[Optional[float]] = mapped_column(Float, comment='期望薪资下限')
    expected_salary_max: Mapped[Optional[float]] = mapped_column(Float, comment='期望薪资上限')

    # 简历
    resume_url: Mapped[Optional[str]] = mapped_column(String(500), comment='简历URL')
    resume_text: Mapped[Optional[str]] = mapped_column(Text, comment='简历文本')

    # 评估
    talent_level: Mapped[str] = mapped_column(String(20), default='normal', comment='人才等级(excellent/good/normal)')
    tags: Mapped[Optional[str]] = mapped_column(JSON, comment='标签(JSON)')
    notes: Mapped[Optional[str]] = mapped_column(Text, comment='备注')

    # 状态
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, comment='是否可联系')
    last_contact_date: Mapped[Optional[date]] = mapped_column(Date, comment='最近联系日期')

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, comment='创建人ID')

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'education': self.education,
            'work_experience_years': self.work_experience_years,
            'skills': self.skills,
            'expected_positions': self.expected_positions,
            'expected_salary_min': self.expected_salary_min,
            'expected_salary_max': self.expected_salary_max,
            'resume_url': self.resume_url,
            'talent_level': self.talent_level,
            'tags': self.tags,
            'notes': self.notes,
            'is_available': self.is_available,
            'last_contact_date': self.last_contact_date.strftime('%Y-%m-%d') if self.last_contact_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'created_by': self.created_by
        }
