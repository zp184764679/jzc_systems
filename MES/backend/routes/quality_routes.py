# MES 质量管理路由
# Quality Management Routes

from flask import Blueprint, request, jsonify
from database import db
from datetime import datetime
from models.quality import (
    InspectionStandard, DefectType, QualityInspectionOrder, DefectRecord,
    NonConformanceReport,
    generate_inspection_no, generate_ncr_no,
    INSPECTION_STATUS_TRANSITIONS, NCR_STATUS_TRANSITIONS,
    INSPECTION_STAGE_LABELS, INSPECTION_METHOD_LABELS, QUALITY_RESULT_LABELS,
    DISPOSITION_LABELS, DEFECT_SEVERITY_LABELS, NCR_STATUS_LABELS
)
from models.work_order import WorkOrder

quality_bp = Blueprint('quality', __name__)


# ==================== 检验标准 API ====================

@quality_bp.route('/standards', methods=['GET'])
def get_standards():
    """获取检验标准列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        stage = request.args.get('inspection_stage', '')
        is_active = request.args.get('is_active', '')

        query = InspectionStandard.query

        if keyword:
            query = query.filter(
                db.or_(
                    InspectionStandard.code.like(f'%{keyword}%'),
                    InspectionStandard.name.like(f'%{keyword}%'),
                    InspectionStandard.product_name.like(f'%{keyword}%')
                )
            )

        if stage:
            query = query.filter(InspectionStandard.inspection_stage == stage)

        if is_active != '':
            query = query.filter(InspectionStandard.is_active == (is_active == 'true'))

        query = query.order_by(InspectionStandard.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/standards/<int:id>', methods=['GET'])
def get_standard(id):
    """获取检验标准详情"""
    try:
        standard = InspectionStandard.query.get_or_404(id)
        return jsonify({'success': True, 'data': standard.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/standards', methods=['POST'])
def create_standard():
    """创建检验标准"""
    try:
        data = request.get_json()

        # 检查编码唯一性
        if InspectionStandard.query.filter_by(code=data.get('code')).first():
            return jsonify({'success': False, 'message': '标准编码已存在'}), 400

        standard = InspectionStandard(
            code=data.get('code'),
            name=data.get('name'),
            product_id=data.get('product_id'),
            product_code=data.get('product_code'),
            product_name=data.get('product_name'),
            process_id=data.get('process_id'),
            process_name=data.get('process_name'),
            inspection_stage=data.get('inspection_stage', 'process'),
            inspection_method=data.get('inspection_method', 'sampling'),
            sample_plan=data.get('sample_plan'),
            sample_size_formula=data.get('sample_size_formula'),
            inspection_items=data.get('inspection_items', []),
            aql_critical=data.get('aql_critical'),
            aql_major=data.get('aql_major'),
            aql_minor=data.get('aql_minor'),
            version=data.get('version', '1.0'),
            is_active=data.get('is_active', True),
            created_by=data.get('created_by')
        )

        db.session.add(standard)
        db.session.commit()

        return jsonify({'success': True, 'data': standard.to_dict(), 'message': '创建成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/standards/<int:id>', methods=['PUT'])
def update_standard(id):
    """更新检验标准"""
    try:
        standard = InspectionStandard.query.get_or_404(id)
        data = request.get_json()

        # 检查编码唯一性
        if data.get('code') and data['code'] != standard.code:
            if InspectionStandard.query.filter_by(code=data['code']).first():
                return jsonify({'success': False, 'message': '标准编码已存在'}), 400
            standard.code = data['code']

        for field in ['name', 'product_id', 'product_code', 'product_name',
                      'process_id', 'process_name', 'inspection_stage',
                      'inspection_method', 'sample_plan', 'sample_size_formula',
                      'inspection_items', 'aql_critical', 'aql_major', 'aql_minor',
                      'version', 'is_active']:
            if field in data:
                setattr(standard, field, data[field])

        db.session.commit()
        return jsonify({'success': True, 'data': standard.to_dict(), 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/standards/<int:id>', methods=['DELETE'])
def delete_standard(id):
    """删除检验标准"""
    try:
        standard = InspectionStandard.query.get_or_404(id)

        # 检查是否有关联的检验单
        if QualityInspectionOrder.query.filter_by(standard_id=id).first():
            return jsonify({'success': False, 'message': '该标准已被使用，无法删除'}), 400

        db.session.delete(standard)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/standards/options', methods=['GET'])
def get_standard_options():
    """获取检验标准选项（下拉框）"""
    try:
        product_id = request.args.get('product_id', type=int)
        process_id = request.args.get('process_id', type=int)
        stage = request.args.get('inspection_stage', '')

        query = InspectionStandard.query.filter_by(is_active=True)

        if product_id:
            query = query.filter(
                db.or_(
                    InspectionStandard.product_id == product_id,
                    InspectionStandard.product_id.is_(None)
                )
            )

        if process_id:
            query = query.filter(
                db.or_(
                    InspectionStandard.process_id == process_id,
                    InspectionStandard.process_id.is_(None)
                )
            )

        if stage:
            query = query.filter(InspectionStandard.inspection_stage == stage)

        standards = query.order_by(InspectionStandard.name).all()

        return jsonify({
            'success': True,
            'data': [s.to_simple_dict() for s in standards]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 缺陷类型 API ====================

@quality_bp.route('/defect-types', methods=['GET'])
def get_defect_types():
    """获取缺陷类型列表"""
    try:
        category = request.args.get('category', '')
        severity = request.args.get('severity', '')
        is_active = request.args.get('is_active', '')

        query = DefectType.query

        if category:
            query = query.filter(DefectType.category == category)

        if severity:
            query = query.filter(DefectType.severity == severity)

        if is_active != '':
            query = query.filter(DefectType.is_active == (is_active == 'true'))

        defect_types = query.order_by(DefectType.sort_order, DefectType.code).all()

        return jsonify({
            'success': True,
            'data': [dt.to_dict() for dt in defect_types]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/defect-types', methods=['POST'])
def create_defect_type():
    """创建缺陷类型"""
    try:
        data = request.get_json()

        if DefectType.query.filter_by(code=data.get('code')).first():
            return jsonify({'success': False, 'message': '缺陷编码已存在'}), 400

        defect_type = DefectType(
            code=data.get('code'),
            name=data.get('name'),
            category=data.get('category'),
            severity=data.get('severity', 'minor'),
            description=data.get('description'),
            cause_analysis=data.get('cause_analysis'),
            corrective_action=data.get('corrective_action'),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0)
        )

        db.session.add(defect_type)
        db.session.commit()

        return jsonify({'success': True, 'data': defect_type.to_dict(), 'message': '创建成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/defect-types/<int:id>', methods=['PUT'])
def update_defect_type(id):
    """更新缺陷类型"""
    try:
        defect_type = DefectType.query.get_or_404(id)
        data = request.get_json()

        if data.get('code') and data['code'] != defect_type.code:
            if DefectType.query.filter_by(code=data['code']).first():
                return jsonify({'success': False, 'message': '缺陷编码已存在'}), 400
            defect_type.code = data['code']

        for field in ['name', 'category', 'severity', 'description',
                      'cause_analysis', 'corrective_action', 'is_active', 'sort_order']:
            if field in data:
                setattr(defect_type, field, data[field])

        db.session.commit()
        return jsonify({'success': True, 'data': defect_type.to_dict(), 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/defect-types/<int:id>', methods=['DELETE'])
def delete_defect_type(id):
    """删除缺陷类型"""
    try:
        defect_type = DefectType.query.get_or_404(id)

        if DefectRecord.query.filter_by(defect_type_id=id).first():
            return jsonify({'success': False, 'message': '该缺陷类型已被使用，无法删除'}), 400

        db.session.delete(defect_type)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/defect-types/categories', methods=['GET'])
def get_defect_categories():
    """获取缺陷分类列表"""
    try:
        categories = db.session.query(DefectType.category).distinct().filter(
            DefectType.category.isnot(None),
            DefectType.category != ''
        ).all()

        return jsonify({
            'success': True,
            'data': [c[0] for c in categories]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 质量检验单 API ====================

@quality_bp.route('/inspections', methods=['GET'])
def get_inspections():
    """获取质量检验单列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        stage = request.args.get('inspection_stage', '')
        result = request.args.get('result', '')
        status = request.args.get('status', '')
        work_order_id = request.args.get('work_order_id', type=int)

        query = QualityInspectionOrder.query

        if keyword:
            query = query.filter(
                db.or_(
                    QualityInspectionOrder.inspection_no.like(f'%{keyword}%'),
                    QualityInspectionOrder.product_name.like(f'%{keyword}%'),
                    QualityInspectionOrder.batch_no.like(f'%{keyword}%')
                )
            )

        if stage:
            query = query.filter(QualityInspectionOrder.inspection_stage == stage)

        if result:
            query = query.filter(QualityInspectionOrder.result == result)

        if status:
            query = query.filter(QualityInspectionOrder.status == status)

        if work_order_id:
            query = query.filter(QualityInspectionOrder.work_order_id == work_order_id)

        query = query.order_by(QualityInspectionOrder.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [i.to_simple_dict() for i in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/inspections/<int:id>', methods=['GET'])
def get_inspection(id):
    """获取检验单详情"""
    try:
        inspection = QualityInspectionOrder.query.get_or_404(id)
        data = inspection.to_dict()

        # 获取缺陷记录
        defects = DefectRecord.query.filter_by(inspection_order_id=id).all()
        data['defects'] = [d.to_dict() for d in defects]

        # 获取关联的 NCR
        ncrs = NonConformanceReport.query.filter_by(inspection_order_id=id).all()
        data['ncr_reports'] = [n.to_simple_dict() for n in ncrs]

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/inspections', methods=['POST'])
def create_inspection():
    """创建质量检验单"""
    try:
        data = request.get_json()

        # 生成检验单号
        inspection_no = generate_inspection_no()

        # 获取工单信息
        work_order = None
        if data.get('work_order_id'):
            work_order = WorkOrder.query.get(data['work_order_id'])

        # 获取检验标准
        standard = None
        if data.get('standard_id'):
            standard = InspectionStandard.query.get(data['standard_id'])

        inspection = QualityInspectionOrder(
            inspection_no=inspection_no,
            work_order_id=data.get('work_order_id'),
            work_order_process_id=data.get('work_order_process_id'),
            production_record_id=data.get('production_record_id'),
            standard_id=data.get('standard_id'),
            inspection_stage=data.get('inspection_stage', standard.inspection_stage if standard else 'process'),
            inspection_method=data.get('inspection_method', standard.inspection_method if standard else 'sampling'),
            product_code=data.get('product_code', work_order.product_code if work_order else None),
            product_name=data.get('product_name', work_order.product_name if work_order else None),
            process_name=data.get('process_name'),
            batch_no=data.get('batch_no'),
            lot_size=data.get('lot_size'),
            sample_size=data.get('sample_size'),
            item_results=standard.inspection_items if standard else data.get('item_results', []),
            status='pending',
            result='pending',
            created_by=data.get('created_by')
        )

        db.session.add(inspection)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': inspection.to_dict(),
            'message': f'检验单 {inspection_no} 创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/inspections/<int:id>/start', methods=['POST'])
def start_inspection(id):
    """开始检验"""
    try:
        inspection = QualityInspectionOrder.query.get_or_404(id)

        if inspection.status != 'pending':
            return jsonify({'success': False, 'message': '只有待检验状态可以开始'}), 400

        data = request.get_json()

        inspection.status = 'inspecting'
        inspection.inspector_id = data.get('inspector_id')
        inspection.inspector_name = data.get('inspector_name')

        db.session.commit()
        return jsonify({'success': True, 'data': inspection.to_dict(), 'message': '检验已开始'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/inspections/<int:id>/complete', methods=['POST'])
def complete_inspection(id):
    """完成检验"""
    try:
        inspection = QualityInspectionOrder.query.get_or_404(id)

        if inspection.status != 'inspecting':
            return jsonify({'success': False, 'message': '只有检验中状态可以完成'}), 400

        data = request.get_json()

        # 更新检验结果
        inspection.item_results = data.get('item_results', inspection.item_results)
        inspection.pass_quantity = data.get('pass_quantity', 0)
        inspection.fail_quantity = data.get('fail_quantity', 0)

        # 计算合格率
        total = inspection.pass_quantity + inspection.fail_quantity
        if total > 0:
            inspection.pass_rate = round(inspection.pass_quantity / total * 100, 2)

        # 判断检验结果
        if inspection.fail_quantity == 0:
            inspection.result = 'pass'
        else:
            inspection.result = 'fail'

        inspection.result = data.get('result', inspection.result)
        inspection.status = 'completed'
        inspection.inspected_at = datetime.utcnow()
        inspection.notes = data.get('notes')

        db.session.commit()
        return jsonify({'success': True, 'data': inspection.to_dict(), 'message': '检验已完成'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/inspections/<int:id>/review', methods=['POST'])
def review_inspection(id):
    """复核检验"""
    try:
        inspection = QualityInspectionOrder.query.get_or_404(id)

        if inspection.status != 'completed':
            return jsonify({'success': False, 'message': '只有已完成状态可以复核'}), 400

        data = request.get_json()

        inspection.reviewer_id = data.get('reviewer_id')
        inspection.reviewer_name = data.get('reviewer_name')
        inspection.reviewed_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'success': True, 'data': inspection.to_dict(), 'message': '复核完成'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/inspections/<int:id>/dispose', methods=['POST'])
def dispose_inspection(id):
    """处置检验结果"""
    try:
        inspection = QualityInspectionOrder.query.get_or_404(id)

        if inspection.status != 'completed':
            return jsonify({'success': False, 'message': '只有已完成状态可以处置'}), 400

        data = request.get_json()

        inspection.disposition = data.get('disposition')
        inspection.disposition_notes = data.get('disposition_notes')
        inspection.disposed_by = data.get('disposed_by')
        inspection.disposed_at = datetime.utcnow()

        # 如果是让步接收，更新结果
        if inspection.disposition == 'concession':
            inspection.result = 'conditional'

        inspection.status = 'closed'

        db.session.commit()

        # 如果需要创建 NCR
        if data.get('create_ncr') and inspection.result == 'fail':
            ncr = NonConformanceReport(
                ncr_no=generate_ncr_no(),
                inspection_order_id=inspection.id,
                work_order_id=inspection.work_order_id,
                product_code=inspection.product_code,
                product_name=inspection.product_name,
                batch_no=inspection.batch_no,
                quantity=inspection.fail_quantity,
                nc_type='检验不合格',
                nc_description=data.get('nc_description', ''),
                severity='major',
                reporter_id=data.get('reporter_id'),
                reporter_name=data.get('reporter_name'),
                status='open'
            )
            db.session.add(ncr)
            db.session.commit()

            return jsonify({
                'success': True,
                'data': inspection.to_dict(),
                'ncr': ncr.to_dict(),
                'message': f'处置完成，已创建NCR: {ncr.ncr_no}'
            })

        return jsonify({'success': True, 'data': inspection.to_dict(), 'message': '处置完成'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/inspections/<int:id>/defects', methods=['POST'])
def add_defect_record(id):
    """添加缺陷记录"""
    try:
        inspection = QualityInspectionOrder.query.get_or_404(id)
        data = request.get_json()

        # 获取缺陷类型信息
        defect_type = None
        if data.get('defect_type_id'):
            defect_type = DefectType.query.get(data['defect_type_id'])

        defect = DefectRecord(
            inspection_order_id=id,
            defect_type_id=data.get('defect_type_id'),
            defect_code=defect_type.code if defect_type else data.get('defect_code'),
            defect_name=defect_type.name if defect_type else data.get('defect_name'),
            severity=defect_type.severity if defect_type else data.get('severity', 'minor'),
            quantity=data.get('quantity', 1),
            inspection_item=data.get('inspection_item'),
            specification=data.get('specification'),
            actual_value=data.get('actual_value'),
            description=data.get('description'),
            location=data.get('location'),
            images=data.get('images'),
            root_cause=data.get('root_cause'),
            responsible_dept=data.get('responsible_dept')
        )

        db.session.add(defect)
        db.session.commit()

        return jsonify({'success': True, 'data': defect.to_dict(), 'message': '缺陷记录添加成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/inspections/<int:inspection_id>/defects/<int:defect_id>', methods=['DELETE'])
def delete_defect_record(inspection_id, defect_id):
    """删除缺陷记录"""
    try:
        defect = DefectRecord.query.filter_by(
            id=defect_id,
            inspection_order_id=inspection_id
        ).first_or_404()

        db.session.delete(defect)
        db.session.commit()

        return jsonify({'success': True, 'message': '缺陷记录删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 不合格品报告 (NCR) API ====================

@quality_bp.route('/ncr', methods=['GET'])
def get_ncr_list():
    """获取 NCR 列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')
        severity = request.args.get('severity', '')

        query = NonConformanceReport.query

        if keyword:
            query = query.filter(
                db.or_(
                    NonConformanceReport.ncr_no.like(f'%{keyword}%'),
                    NonConformanceReport.product_name.like(f'%{keyword}%'),
                    NonConformanceReport.batch_no.like(f'%{keyword}%')
                )
            )

        if status:
            query = query.filter(NonConformanceReport.status == status)

        if severity:
            query = query.filter(NonConformanceReport.severity == severity)

        query = query.order_by(NonConformanceReport.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'data': [n.to_simple_dict() for n in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/ncr/<int:id>', methods=['GET'])
def get_ncr(id):
    """获取 NCR 详情"""
    try:
        ncr = NonConformanceReport.query.get_or_404(id)
        return jsonify({'success': True, 'data': ncr.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/ncr', methods=['POST'])
def create_ncr():
    """创建 NCR"""
    try:
        data = request.get_json()

        ncr = NonConformanceReport(
            ncr_no=generate_ncr_no(),
            inspection_order_id=data.get('inspection_order_id'),
            work_order_id=data.get('work_order_id'),
            product_code=data.get('product_code'),
            product_name=data.get('product_name'),
            batch_no=data.get('batch_no'),
            quantity=data.get('quantity'),
            nc_type=data.get('nc_type'),
            nc_description=data.get('nc_description'),
            severity=data.get('severity', 'major'),
            reporter_id=data.get('reporter_id'),
            reporter_name=data.get('reporter_name'),
            responsible_dept=data.get('responsible_dept'),
            responsible_person=data.get('responsible_person'),
            status='open'
        )

        db.session.add(ncr)
        db.session.commit()

        return jsonify({
            'success': True,
            'data': ncr.to_dict(),
            'message': f'NCR {ncr.ncr_no} 创建成功'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/ncr/<int:id>', methods=['PUT'])
def update_ncr(id):
    """更新 NCR"""
    try:
        ncr = NonConformanceReport.query.get_or_404(id)
        data = request.get_json()

        for field in ['nc_type', 'nc_description', 'severity', 'root_cause',
                      'cause_category', 'corrective_action', 'preventive_action',
                      'action_due_date', 'responsible_dept', 'responsible_person']:
            if field in data:
                if field == 'action_due_date' and data[field]:
                    setattr(ncr, field, datetime.fromisoformat(data[field][:10]))
                else:
                    setattr(ncr, field, data[field])

        db.session.commit()
        return jsonify({'success': True, 'data': ncr.to_dict(), 'message': '更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/ncr/<int:id>/review', methods=['POST'])
def review_ncr(id):
    """审核 NCR"""
    try:
        ncr = NonConformanceReport.query.get_or_404(id)

        if ncr.status != 'open':
            return jsonify({'success': False, 'message': '只有待处理状态可以审核'}), 400

        data = request.get_json()

        ncr.root_cause = data.get('root_cause', ncr.root_cause)
        ncr.cause_category = data.get('cause_category', ncr.cause_category)
        ncr.status = 'reviewing'

        db.session.commit()
        return jsonify({'success': True, 'data': ncr.to_dict(), 'message': '已进入审核'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/ncr/<int:id>/dispose', methods=['POST'])
def dispose_ncr(id):
    """处置 NCR"""
    try:
        ncr = NonConformanceReport.query.get_or_404(id)

        if ncr.status != 'reviewing':
            return jsonify({'success': False, 'message': '只有审核中状态可以处置'}), 400

        data = request.get_json()

        ncr.disposition = data.get('disposition')
        ncr.disposition_notes = data.get('disposition_notes')
        ncr.disposition_by = data.get('disposition_by')
        ncr.disposition_at = datetime.utcnow()
        ncr.corrective_action = data.get('corrective_action')
        ncr.preventive_action = data.get('preventive_action')
        ncr.action_due_date = datetime.fromisoformat(data['action_due_date'][:10]) if data.get('action_due_date') else None
        ncr.status = 'dispositioned'

        db.session.commit()
        return jsonify({'success': True, 'data': ncr.to_dict(), 'message': '处置完成'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/ncr/<int:id>/close', methods=['POST'])
def close_ncr(id):
    """关闭 NCR"""
    try:
        ncr = NonConformanceReport.query.get_or_404(id)

        if ncr.status != 'dispositioned':
            return jsonify({'success': False, 'message': '只有已处置状态可以关闭'}), 400

        data = request.get_json()

        ncr.verified_by = data.get('verified_by')
        ncr.verified_at = datetime.utcnow()
        ncr.verification_result = data.get('verification_result', 'pass')
        ncr.action_completed_at = datetime.utcnow()
        ncr.status = 'closed'
        ncr.closed_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'success': True, 'data': ncr.to_dict(), 'message': 'NCR 已关闭'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 统计 API ====================

@quality_bp.route('/statistics/summary', methods=['GET'])
def get_quality_summary():
    """获取质量统计概览"""
    try:
        # 检验统计
        total_inspections = QualityInspectionOrder.query.count()
        pending_inspections = QualityInspectionOrder.query.filter_by(status='pending').count()
        pass_inspections = QualityInspectionOrder.query.filter_by(result='pass').count()
        fail_inspections = QualityInspectionOrder.query.filter_by(result='fail').count()

        # NCR 统计
        total_ncr = NonConformanceReport.query.count()
        open_ncr = NonConformanceReport.query.filter_by(status='open').count()
        reviewing_ncr = NonConformanceReport.query.filter_by(status='reviewing').count()

        # 缺陷统计
        total_defects = DefectRecord.query.count()
        critical_defects = DefectRecord.query.filter_by(severity='critical').count()
        major_defects = DefectRecord.query.filter_by(severity='major').count()

        # 合格率
        completed = QualityInspectionOrder.query.filter(
            QualityInspectionOrder.result.in_(['pass', 'fail', 'conditional'])
        ).all()

        if completed:
            total_pass = sum(i.pass_quantity or 0 for i in completed)
            total_inspected = sum((i.pass_quantity or 0) + (i.fail_quantity or 0) for i in completed)
            overall_pass_rate = round(total_pass / total_inspected * 100, 2) if total_inspected > 0 else 0
        else:
            overall_pass_rate = 0

        return jsonify({
            'success': True,
            'data': {
                'inspections': {
                    'total': total_inspections,
                    'pending': pending_inspections,
                    'pass': pass_inspections,
                    'fail': fail_inspections,
                },
                'ncr': {
                    'total': total_ncr,
                    'open': open_ncr,
                    'reviewing': reviewing_ncr,
                },
                'defects': {
                    'total': total_defects,
                    'critical': critical_defects,
                    'major': major_defects,
                },
                'overall_pass_rate': overall_pass_rate,
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/statistics/by-stage', methods=['GET'])
def get_stats_by_stage():
    """按检验阶段统计"""
    try:
        stats = db.session.query(
            QualityInspectionOrder.inspection_stage,
            db.func.count(QualityInspectionOrder.id).label('total'),
            db.func.sum(db.case((QualityInspectionOrder.result == 'pass', 1), else_=0)).label('pass_count'),
            db.func.sum(db.case((QualityInspectionOrder.result == 'fail', 1), else_=0)).label('fail_count'),
        ).group_by(QualityInspectionOrder.inspection_stage).all()

        return jsonify({
            'success': True,
            'data': [
                {
                    'stage': s.inspection_stage,
                    'stage_label': INSPECTION_STAGE_LABELS.get(s.inspection_stage, s.inspection_stage),
                    'total': s.total,
                    'pass_count': s.pass_count or 0,
                    'fail_count': s.fail_count or 0,
                    'pass_rate': round((s.pass_count or 0) / s.total * 100, 2) if s.total > 0 else 0,
                }
                for s in stats
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@quality_bp.route('/statistics/defect-analysis', methods=['GET'])
def get_defect_analysis():
    """缺陷分析统计"""
    try:
        # 按缺陷类型统计
        by_type = db.session.query(
            DefectRecord.defect_name,
            DefectRecord.severity,
            db.func.count(DefectRecord.id).label('count'),
            db.func.sum(DefectRecord.quantity).label('total_qty')
        ).group_by(DefectRecord.defect_name, DefectRecord.severity).order_by(
            db.desc('total_qty')
        ).limit(10).all()

        # 按严重程度统计
        by_severity = db.session.query(
            DefectRecord.severity,
            db.func.count(DefectRecord.id).label('count'),
            db.func.sum(DefectRecord.quantity).label('total_qty')
        ).group_by(DefectRecord.severity).all()

        return jsonify({
            'success': True,
            'data': {
                'by_type': [
                    {
                        'defect_name': t.defect_name,
                        'severity': t.severity,
                        'severity_label': DEFECT_SEVERITY_LABELS.get(t.severity, t.severity),
                        'count': t.count,
                        'total_qty': t.total_qty or 0,
                    }
                    for t in by_type
                ],
                'by_severity': [
                    {
                        'severity': s.severity,
                        'severity_label': DEFECT_SEVERITY_LABELS.get(s.severity, s.severity),
                        'count': s.count,
                        'total_qty': s.total_qty or 0,
                    }
                    for s in by_severity
                ]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 辅助 API ====================

@quality_bp.route('/enums', methods=['GET'])
def get_quality_enums():
    """获取质量管理枚举值"""
    return jsonify({
        'success': True,
        'data': {
            'inspection_stages': INSPECTION_STAGE_LABELS,
            'inspection_methods': INSPECTION_METHOD_LABELS,
            'quality_results': QUALITY_RESULT_LABELS,
            'dispositions': DISPOSITION_LABELS,
            'defect_severities': DEFECT_SEVERITY_LABELS,
            'ncr_statuses': NCR_STATUS_LABELS,
        }
    })
