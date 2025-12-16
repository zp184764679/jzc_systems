"""
招聘管理 API 路由
包含: 职位发布、应聘申请、面试安排、面试评价、人才库
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models.recruitment import (
    JobPosting, JobApplication, Interview, InterviewEvaluation, TalentPool,
    JobStatus, ApplicationStatus, InterviewStatus, InterviewType
)
from app.models.base_data import Department, Position, Factory
from app.models.employee import Employee
from datetime import datetime, date
from sqlalchemy import or_, and_, func
from app.routes.auth import require_auth
import uuid

recruitment_bp = Blueprint('recruitment', __name__, url_prefix='/api/recruitment')


def parse_date(date_string):
    """Parse date string to date object"""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None


def parse_datetime(datetime_string):
    """Parse datetime string to datetime object"""
    if not datetime_string:
        return None
    try:
        return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            try:
                return datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M')
            except ValueError:
                return None


def generate_job_code():
    """生成职位编码"""
    now = datetime.now()
    return f"JOB{now.strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"


def generate_application_no():
    """生成申请编号"""
    now = datetime.now()
    return f"APP{now.strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"


# ==================== 职位发布 API ====================

@recruitment_bp.route('/jobs', methods=['GET'])
@require_auth
def get_job_postings(user):
    """获取职位发布列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        department_id = request.args.get('department_id', type=int)
        factory_id = request.args.get('factory_id', type=int)
        search = request.args.get('search', '')

        query = JobPosting.query

        if status:
            query = query.filter(JobPosting.status == status)
        if department_id:
            query = query.filter(JobPosting.department_id == department_id)
        if factory_id:
            query = query.filter(JobPosting.factory_id == factory_id)
        if search:
            query = query.filter(or_(
                JobPosting.title.like(f'%{search}%'),
                JobPosting.job_code.like(f'%{search}%')
            ))

        query = query.order_by(JobPosting.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        jobs = []
        for job in pagination.items:
            job_dict = job.to_dict()
            # 添加部门和工厂名称
            if job.department_id:
                dept = Department.query.get(job.department_id)
                job_dict['department_name'] = dept.name if dept else None
            if job.factory_id:
                factory = Factory.query.get(job.factory_id)
                job_dict['factory_name'] = factory.name if factory else None
            if job.position_id:
                position = Position.query.get(job.position_id)
                job_dict['position_name'] = position.name if position else None
            jobs.append(job_dict)

        return jsonify({
            'success': True,
            'data': {
                'items': jobs,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@recruitment_bp.route('/jobs/<int:job_id>', methods=['GET'])
@require_auth
def get_job_posting(user, job_id):
    """获取单个职位详情"""
    try:
        job = JobPosting.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': '职位不存在'
            }), 404

        job_dict = job.to_dict()
        # 添加关联名称
        if job.department_id:
            dept = Department.query.get(job.department_id)
            job_dict['department_name'] = dept.name if dept else None
        if job.factory_id:
            factory = Factory.query.get(job.factory_id)
            job_dict['factory_name'] = factory.name if factory else None
        if job.position_id:
            position = Position.query.get(job.position_id)
            job_dict['position_name'] = position.name if position else None

        # 增加浏览次数
        job.view_count += 1
        db.session.commit()

        return jsonify({
            'success': True,
            'data': job_dict
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@recruitment_bp.route('/jobs', methods=['POST'])
@require_auth
def create_job_posting(user):
    """创建职位发布"""
    try:
        data = request.get_json()

        job = JobPosting(
            job_code=data.get('job_code') or generate_job_code(),
            title=data.get('title'),
            department_id=data.get('department_id'),
            position_id=data.get('position_id'),
            factory_id=data.get('factory_id'),
            headcount=data.get('headcount', 1),
            urgency=data.get('urgency', 'normal'),
            job_type=data.get('job_type', 'full_time'),
            education_requirement=data.get('education_requirement'),
            experience_years=data.get('experience_years'),
            age_min=data.get('age_min'),
            age_max=data.get('age_max'),
            gender_requirement=data.get('gender_requirement'),
            skills=data.get('skills'),
            salary_min=data.get('salary_min'),
            salary_max=data.get('salary_max'),
            salary_type=data.get('salary_type', 'monthly'),
            salary_negotiable=data.get('salary_negotiable', True),
            description=data.get('description'),
            requirements=data.get('requirements'),
            benefits=data.get('benefits'),
            status=data.get('status', 'draft'),
            publish_date=parse_date(data.get('publish_date')),
            expire_date=parse_date(data.get('expire_date')),
            recruiter_id=data.get('recruiter_id'),
            hiring_manager_id=data.get('hiring_manager_id'),
            created_by=user.get('id')
        )

        db.session.add(job)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': job.to_dict(),
            'message': '职位创建成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@recruitment_bp.route('/jobs/<int:job_id>', methods=['PUT'])
@require_auth
def update_job_posting(user, job_id):
    """更新职位发布"""
    try:
        job = JobPosting.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': '职位不存在'
            }), 404

        data = request.get_json()

        for field in ['title', 'department_id', 'position_id', 'factory_id',
                      'headcount', 'urgency', 'job_type', 'education_requirement',
                      'experience_years', 'age_min', 'age_max', 'gender_requirement',
                      'skills', 'salary_min', 'salary_max', 'salary_type',
                      'salary_negotiable', 'description', 'requirements', 'benefits',
                      'status', 'recruiter_id', 'hiring_manager_id']:
            if field in data:
                setattr(job, field, data[field])

        if 'publish_date' in data:
            job.publish_date = parse_date(data['publish_date'])
        if 'expire_date' in data:
            job.expire_date = parse_date(data['expire_date'])

        db.session.commit()

        return jsonify({
            'success': True,
            'data': job.to_dict(),
            'message': '职位更新成功'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@recruitment_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@require_auth
def delete_job_posting(user, job_id):
    """删除职位发布"""
    try:
        job = JobPosting.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': '职位不存在'
            }), 404

        # 检查是否有关联的申请
        if job.applications.count() > 0:
            return jsonify({
                'success': False,
                'message': '该职位有关联的应聘申请，无法删除'
            }), 400

        db.session.delete(job)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '职位删除成功'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@recruitment_bp.route('/jobs/<int:job_id>/publish', methods=['POST'])
@require_auth
def publish_job(user, job_id):
    """发布职位"""
    try:
        job = JobPosting.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': '职位不存在'
            }), 404

        job.status = 'open'
        job.publish_date = date.today()
        db.session.commit()

        return jsonify({
            'success': True,
            'data': job.to_dict(),
            'message': '职位已发布'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'发布失败: {str(e)}'
        }), 500


@recruitment_bp.route('/jobs/<int:job_id>/close', methods=['POST'])
@require_auth
def close_job(user, job_id):
    """关闭职位"""
    try:
        job = JobPosting.query.get(job_id)
        if not job:
            return jsonify({
                'success': False,
                'message': '职位不存在'
            }), 404

        job.status = 'closed'
        db.session.commit()

        return jsonify({
            'success': True,
            'data': job.to_dict(),
            'message': '职位已关闭'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'关闭失败: {str(e)}'
        }), 500


# ==================== 应聘申请 API ====================

@recruitment_bp.route('/applications', methods=['GET'])
@require_auth
def get_applications(user):
    """获取应聘申请列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        job_id = request.args.get('job_id', type=int)
        status = request.args.get('status')
        search = request.args.get('search', '')

        query = JobApplication.query

        if job_id:
            query = query.filter(JobApplication.job_posting_id == job_id)
        if status:
            query = query.filter(JobApplication.status == status)
        if search:
            query = query.filter(or_(
                JobApplication.name.like(f'%{search}%'),
                JobApplication.phone.like(f'%{search}%'),
                JobApplication.application_no.like(f'%{search}%')
            ))

        query = query.order_by(JobApplication.applied_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        applications = []
        for app in pagination.items:
            app_dict = app.to_dict(include_job=True)
            applications.append(app_dict)

        return jsonify({
            'success': True,
            'data': {
                'items': applications,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@recruitment_bp.route('/applications/<int:app_id>', methods=['GET'])
@require_auth
def get_application(user, app_id):
    """获取单个应聘申请详情"""
    try:
        app = JobApplication.query.get(app_id)
        if not app:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        app_dict = app.to_dict(include_job=True)
        # 添加面试列表
        app_dict['interviews'] = [i.to_dict() for i in app.interviews.all()]

        return jsonify({
            'success': True,
            'data': app_dict
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@recruitment_bp.route('/applications', methods=['POST'])
@require_auth
def create_application(user):
    """创建应聘申请"""
    try:
        data = request.get_json()

        # 检查职位是否存在且开放
        job = JobPosting.query.get(data.get('job_posting_id'))
        if not job:
            return jsonify({
                'success': False,
                'message': '职位不存在'
            }), 404

        if job.status != 'open':
            return jsonify({
                'success': False,
                'message': '该职位暂不接受申请'
            }), 400

        app = JobApplication(
            application_no=generate_application_no(),
            job_posting_id=data.get('job_posting_id'),
            name=data.get('name'),
            gender=data.get('gender'),
            birth_date=parse_date(data.get('birth_date')),
            phone=data.get('phone'),
            email=data.get('email'),
            id_card=data.get('id_card'),
            education=data.get('education'),
            major=data.get('major'),
            school=data.get('school'),
            graduation_date=parse_date(data.get('graduation_date')),
            work_experience_years=data.get('work_experience_years'),
            current_company=data.get('current_company'),
            current_position=data.get('current_position'),
            expected_salary=data.get('expected_salary'),
            available_date=parse_date(data.get('available_date')),
            resume_url=data.get('resume_url'),
            resume_text=data.get('resume_text'),
            attachments=data.get('attachments'),
            source=data.get('source', 'direct'),
            referrer_id=data.get('referrer_id'),
            referrer_name=data.get('referrer_name'),
            status='pending'
        )

        # 更新职位申请次数
        job.apply_count += 1

        db.session.add(app)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': app.to_dict(),
            'message': '申请提交成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }), 500


@recruitment_bp.route('/applications/<int:app_id>', methods=['PUT'])
@require_auth
def update_application(user, app_id):
    """更新应聘申请"""
    try:
        app = JobApplication.query.get(app_id)
        if not app:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        data = request.get_json()

        for field in ['name', 'gender', 'phone', 'email', 'id_card',
                      'education', 'major', 'school', 'work_experience_years',
                      'current_company', 'current_position', 'expected_salary',
                      'resume_url', 'resume_text', 'attachments', 'source',
                      'referrer_id', 'referrer_name', 'status', 'rejection_reason',
                      'screening_score', 'screening_notes', 'overall_score',
                      'offer_salary', 'employee_id']:
            if field in data:
                setattr(app, field, data[field])

        for date_field in ['birth_date', 'graduation_date', 'available_date',
                           'offer_date', 'offer_expire_date', 'offer_accepted_date', 'hire_date']:
            if date_field in data:
                setattr(app, date_field, parse_date(data[date_field]))

        db.session.commit()

        return jsonify({
            'success': True,
            'data': app.to_dict(),
            'message': '申请更新成功'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@recruitment_bp.route('/applications/<int:app_id>/status', methods=['PUT'])
@require_auth
def update_application_status(user, app_id):
    """更新申请状态"""
    try:
        app = JobApplication.query.get(app_id)
        if not app:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        data = request.get_json()
        new_status = data.get('status')

        if new_status not in ['pending', 'screening', 'interview', 'offer', 'hired', 'rejected', 'withdrawn']:
            return jsonify({
                'success': False,
                'message': '无效的状态'
            }), 400

        app.status = new_status

        if new_status == 'rejected':
            app.rejection_reason = data.get('rejection_reason')
        elif new_status == 'offer':
            app.offer_salary = data.get('offer_salary')
            app.offer_date = date.today()
            app.offer_expire_date = parse_date(data.get('offer_expire_date'))
        elif new_status == 'hired':
            app.hire_date = parse_date(data.get('hire_date')) or date.today()
            # 更新职位已录用人数
            job = app.job_posting
            job.hired_count += 1
            if job.hired_count >= job.headcount:
                job.status = 'filled'

        db.session.commit()

        return jsonify({
            'success': True,
            'data': app.to_dict(),
            'message': '状态更新成功'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


# ==================== 面试安排 API ====================

@recruitment_bp.route('/interviews', methods=['GET'])
@require_auth
def get_interviews(user):
    """获取面试安排列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        application_id = request.args.get('application_id', type=int)
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        query = Interview.query

        if application_id:
            query = query.filter(Interview.application_id == application_id)
        if status:
            query = query.filter(Interview.status == status)
        if date_from:
            query = query.filter(Interview.scheduled_time >= parse_datetime(date_from + ' 00:00:00'))
        if date_to:
            query = query.filter(Interview.scheduled_time <= parse_datetime(date_to + ' 23:59:59'))

        query = query.order_by(Interview.scheduled_time.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        interviews = []
        for interview in pagination.items:
            interview_dict = interview.to_dict(include_application=True)
            interviews.append(interview_dict)

        return jsonify({
            'success': True,
            'data': {
                'items': interviews,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@recruitment_bp.route('/interviews', methods=['POST'])
@require_auth
def create_interview(user):
    """创建面试安排"""
    try:
        data = request.get_json()

        # 检查申请是否存在
        app = JobApplication.query.get(data.get('application_id'))
        if not app:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        # 计算面试轮次
        existing_count = Interview.query.filter_by(application_id=app.id).count()

        interview = Interview(
            application_id=app.id,
            interview_round=existing_count + 1,
            interview_type=data.get('interview_type', 'onsite'),
            scheduled_time=parse_datetime(data.get('scheduled_time')),
            duration_minutes=data.get('duration_minutes', 60),
            location=data.get('location'),
            meeting_link=data.get('meeting_link'),
            interviewer_ids=data.get('interviewer_ids'),
            interviewer_names=data.get('interviewer_names'),
            status='scheduled',
            notes=data.get('notes'),
            created_by=user.get('id')
        )

        # 更新申请状态为面试中
        if app.status == 'screening' or app.status == 'pending':
            app.status = 'interview'

        db.session.add(interview)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': interview.to_dict(),
            'message': '面试安排成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@recruitment_bp.route('/interviews/<int:interview_id>', methods=['PUT'])
@require_auth
def update_interview(user, interview_id):
    """更新面试安排"""
    try:
        interview = Interview.query.get(interview_id)
        if not interview:
            return jsonify({
                'success': False,
                'message': '面试不存在'
            }), 404

        data = request.get_json()

        for field in ['interview_type', 'duration_minutes', 'location',
                      'meeting_link', 'interviewer_ids', 'interviewer_names',
                      'status', 'candidate_notified', 'candidate_confirmed',
                      'reminder_sent', 'notes', 'cancel_reason']:
            if field in data:
                setattr(interview, field, data[field])

        if 'scheduled_time' in data:
            interview.scheduled_time = parse_datetime(data['scheduled_time'])
        if 'actual_start_time' in data:
            interview.actual_start_time = parse_datetime(data['actual_start_time'])
        if 'actual_end_time' in data:
            interview.actual_end_time = parse_datetime(data['actual_end_time'])

        db.session.commit()

        return jsonify({
            'success': True,
            'data': interview.to_dict(),
            'message': '面试更新成功'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@recruitment_bp.route('/interviews/<int:interview_id>/cancel', methods=['POST'])
@require_auth
def cancel_interview(user, interview_id):
    """取消面试"""
    try:
        interview = Interview.query.get(interview_id)
        if not interview:
            return jsonify({
                'success': False,
                'message': '面试不存在'
            }), 404

        data = request.get_json()

        interview.status = 'cancelled'
        interview.cancel_reason = data.get('reason')

        db.session.commit()

        return jsonify({
            'success': True,
            'data': interview.to_dict(),
            'message': '面试已取消'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'取消失败: {str(e)}'
        }), 500


# ==================== 面试评价 API ====================

@recruitment_bp.route('/interviews/<int:interview_id>/evaluations', methods=['GET'])
@require_auth
def get_interview_evaluations(user, interview_id):
    """获取面试评价列表"""
    try:
        interview = Interview.query.get(interview_id)
        if not interview:
            return jsonify({
                'success': False,
                'message': '面试不存在'
            }), 404

        evaluations = interview.evaluations.all()

        return jsonify({
            'success': True,
            'data': [e.to_dict() for e in evaluations]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@recruitment_bp.route('/interviews/<int:interview_id>/evaluations', methods=['POST'])
@require_auth
def create_interview_evaluation(user, interview_id):
    """创建面试评价"""
    try:
        interview = Interview.query.get(interview_id)
        if not interview:
            return jsonify({
                'success': False,
                'message': '面试不存在'
            }), 404

        data = request.get_json()

        evaluation = InterviewEvaluation(
            interview_id=interview_id,
            evaluator_id=data.get('evaluator_id') or user.get('id'),
            evaluator_name=data.get('evaluator_name') or user.get('full_name', user.get('username')),
            technical_score=data.get('technical_score'),
            communication_score=data.get('communication_score'),
            teamwork_score=data.get('teamwork_score'),
            problem_solving_score=data.get('problem_solving_score'),
            culture_fit_score=data.get('culture_fit_score'),
            overall_score=data.get('overall_score'),
            strengths=data.get('strengths'),
            weaknesses=data.get('weaknesses'),
            questions_asked=data.get('questions_asked'),
            candidate_answers=data.get('candidate_answers'),
            recommendation=data.get('recommendation', 'pending'),
            recommendation_reason=data.get('recommendation_reason')
        )

        # 更新面试状态
        if interview.status == 'scheduled' or interview.status == 'confirmed':
            interview.status = 'completed'

        db.session.add(evaluation)
        db.session.commit()

        # 更新应聘申请的综合评分
        app = interview.application
        all_evaluations = InterviewEvaluation.query.join(Interview).filter(
            Interview.application_id == app.id
        ).all()
        if all_evaluations:
            avg_score = sum(e.overall_score for e in all_evaluations) / len(all_evaluations)
            app.overall_score = int(avg_score * 20)  # 转换为百分制
            db.session.commit()

        return jsonify({
            'success': True,
            'data': evaluation.to_dict(),
            'message': '评价提交成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }), 500


# ==================== 人才库 API ====================

@recruitment_bp.route('/talent-pool', methods=['GET'])
@require_auth
def get_talent_pool(user):
    """获取人才库列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        talent_level = request.args.get('talent_level')

        query = TalentPool.query

        if search:
            query = query.filter(or_(
                TalentPool.name.like(f'%{search}%'),
                TalentPool.phone.like(f'%{search}%')
            ))
        if talent_level:
            query = query.filter(TalentPool.talent_level == talent_level)

        query = query.order_by(TalentPool.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': {
                'items': [t.to_dict() for t in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500


@recruitment_bp.route('/talent-pool', methods=['POST'])
@require_auth
def create_talent(user):
    """添加到人才库"""
    try:
        data = request.get_json()

        talent = TalentPool(
            application_id=data.get('application_id'),
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            education=data.get('education'),
            work_experience_years=data.get('work_experience_years'),
            skills=data.get('skills'),
            expected_positions=data.get('expected_positions'),
            expected_salary_min=data.get('expected_salary_min'),
            expected_salary_max=data.get('expected_salary_max'),
            resume_url=data.get('resume_url'),
            resume_text=data.get('resume_text'),
            talent_level=data.get('talent_level', 'normal'),
            tags=data.get('tags'),
            notes=data.get('notes'),
            created_by=user.get('id')
        )

        db.session.add(talent)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': talent.to_dict(),
            'message': '人才添加成功'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'添加失败: {str(e)}'
        }), 500


@recruitment_bp.route('/talent-pool/from-application/<int:app_id>', methods=['POST'])
@require_auth
def add_to_talent_pool_from_application(user, app_id):
    """从应聘申请添加到人才库"""
    try:
        app = JobApplication.query.get(app_id)
        if not app:
            return jsonify({
                'success': False,
                'message': '申请不存在'
            }), 404

        # 检查是否已存在
        existing = TalentPool.query.filter_by(application_id=app_id).first()
        if existing:
            return jsonify({
                'success': False,
                'message': '该候选人已在人才库中'
            }), 400

        data = request.get_json() or {}

        talent = TalentPool(
            application_id=app_id,
            name=app.name,
            phone=app.phone,
            email=app.email,
            education=app.education,
            work_experience_years=app.work_experience_years,
            resume_url=app.resume_url,
            resume_text=app.resume_text,
            expected_salary_min=app.expected_salary,
            talent_level=data.get('talent_level', 'normal'),
            tags=data.get('tags'),
            notes=data.get('notes'),
            created_by=user.get('id')
        )

        db.session.add(talent)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': talent.to_dict(),
            'message': '已添加到人才库'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'添加失败: {str(e)}'
        }), 500


# ==================== 统计 API ====================

@recruitment_bp.route('/stats', methods=['GET'])
@require_auth
def get_recruitment_stats(user):
    """获取招聘统计数据"""
    try:
        # 职位统计
        job_stats = {
            'total': JobPosting.query.count(),
            'open': JobPosting.query.filter_by(status='open').count(),
            'closed': JobPosting.query.filter_by(status='closed').count(),
            'filled': JobPosting.query.filter_by(status='filled').count()
        }

        # 申请统计
        application_stats = {
            'total': JobApplication.query.count(),
            'pending': JobApplication.query.filter_by(status='pending').count(),
            'interview': JobApplication.query.filter_by(status='interview').count(),
            'offer': JobApplication.query.filter_by(status='offer').count(),
            'hired': JobApplication.query.filter_by(status='hired').count(),
            'rejected': JobApplication.query.filter_by(status='rejected').count()
        }

        # 面试统计
        interview_stats = {
            'total': Interview.query.count(),
            'scheduled': Interview.query.filter_by(status='scheduled').count(),
            'completed': Interview.query.filter_by(status='completed').count(),
            'cancelled': Interview.query.filter_by(status='cancelled').count()
        }

        # 人才库统计
        talent_stats = {
            'total': TalentPool.query.count(),
            'excellent': TalentPool.query.filter_by(talent_level='excellent').count(),
            'good': TalentPool.query.filter_by(talent_level='good').count()
        }

        return jsonify({
            'success': True,
            'data': {
                'jobs': job_stats,
                'applications': application_stats,
                'interviews': interview_stats,
                'talent_pool': talent_stats
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'统计失败: {str(e)}'
        }), 500
