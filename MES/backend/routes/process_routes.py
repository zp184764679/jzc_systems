# MES 工序管理路由
# Process Management Routes

from flask import Blueprint, request, jsonify
from database import db
from models.process import (
    ProcessDefinition, ProcessRoute, ProcessRouteStep, WorkOrderProcess,
    generate_route_code, PROCESS_STATUS_TRANSITIONS,
    PROCESS_TYPE_LABELS, PROCESS_STATUS_LABELS, ROUTE_STATUS_LABELS
)
from models.work_order import WorkOrder
from datetime import datetime
from sqlalchemy import or_, and_

process_bp = Blueprint('process', __name__)


# ==================== 工序定义 API ====================

@process_bp.route('/definitions', methods=['GET'])
def list_process_definitions():
    """获取工序定义列表"""
    try:
        # 查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '')
        process_type = request.args.get('process_type', '')
        work_center_id = request.args.get('work_center_id', type=int)
        is_active = request.args.get('is_active', '')

        # 构建查询
        query = ProcessDefinition.query

        if keyword:
            query = query.filter(or_(
                ProcessDefinition.code.like(f'%{keyword}%'),
                ProcessDefinition.name.like(f'%{keyword}%')
            ))
        if process_type:
            query = query.filter(ProcessDefinition.process_type == process_type)
        if work_center_id:
            query = query.filter(ProcessDefinition.work_center_id == work_center_id)
        if is_active != '':
            query = query.filter(ProcessDefinition.is_active == (is_active.lower() == 'true'))

        # 排序
        query = query.order_by(ProcessDefinition.code)

        # 分页
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return jsonify({
            'success': True,
            'data': [item.to_simple_dict() for item in items],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            },
            'type_labels': PROCESS_TYPE_LABELS
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/definitions/<int:id>', methods=['GET'])
def get_process_definition(id):
    """获取工序定义详情"""
    try:
        item = ProcessDefinition.query.get_or_404(id)
        return jsonify({'success': True, 'data': item.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/definitions', methods=['POST'])
def create_process_definition():
    """创建工序定义"""
    try:
        data = request.get_json()

        # 检查编码唯一性
        if ProcessDefinition.query.filter_by(code=data['code']).first():
            return jsonify({'success': False, 'message': f"工序编码 {data['code']} 已存在"}), 400

        item = ProcessDefinition(
            code=data['code'],
            name=data['name'],
            process_type=data.get('process_type', 'other'),
            description=data.get('description'),
            work_instructions=data.get('work_instructions'),
            work_center_id=data.get('work_center_id'),
            default_machine_id=data.get('default_machine_id'),
            default_machine_name=data.get('default_machine_name'),
            setup_time=data.get('setup_time', 0),
            standard_time=data.get('standard_time', 0),
            move_time=data.get('move_time', 0),
            min_batch_size=data.get('min_batch_size', 1),
            max_batch_size=data.get('max_batch_size'),
            daily_capacity=data.get('daily_capacity'),
            required_skill_level=data.get('required_skill_level'),
            min_operators=data.get('min_operators', 1),
            max_operators=data.get('max_operators'),
            inspection_required=data.get('inspection_required', False),
            inspection_type=data.get('inspection_type'),
            quality_standards=data.get('quality_standards'),
            required_tools=data.get('required_tools'),
            required_materials=data.get('required_materials'),
            safety_notes=data.get('safety_notes'),
            is_active=data.get('is_active', True),
            created_by=data.get('created_by')
        )

        db.session.add(item)
        db.session.commit()

        return jsonify({'success': True, 'data': item.to_dict(), 'message': '创建成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/definitions/<int:id>', methods=['PUT'])
def update_process_definition(id):
    """更新工序定义"""
    try:
        item = ProcessDefinition.query.get_or_404(id)
        data = request.get_json()

        # 检查编码唯一性
        if data.get('code') and data['code'] != item.code:
            if ProcessDefinition.query.filter_by(code=data['code']).first():
                return jsonify({'success': False, 'message': f"工序编码 {data['code']} 已存在"}), 400

        # 更新字段
        for field in ['code', 'name', 'process_type', 'description', 'work_instructions',
                     'work_center_id', 'default_machine_id', 'default_machine_name',
                     'setup_time', 'standard_time', 'move_time',
                     'min_batch_size', 'max_batch_size', 'daily_capacity',
                     'required_skill_level', 'min_operators', 'max_operators',
                     'inspection_required', 'inspection_type', 'quality_standards',
                     'required_tools', 'required_materials', 'safety_notes', 'is_active']:
            if field in data:
                setattr(item, field, data[field])

        item.updated_by = data.get('updated_by')
        item.version = (item.version or 1) + 1

        db.session.commit()

        return jsonify({'success': True, 'data': item.to_dict(), 'message': '更新成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/definitions/<int:id>', methods=['DELETE'])
def delete_process_definition(id):
    """删除工序定义"""
    try:
        item = ProcessDefinition.query.get_or_404(id)

        # 检查是否有关联的工艺路线步骤
        if ProcessRouteStep.query.filter_by(process_id=id).first():
            return jsonify({'success': False, 'message': '该工序已被工艺路线引用，无法删除'}), 400

        db.session.delete(item)
        db.session.commit()

        return jsonify({'success': True, 'message': '删除成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/definitions/options', methods=['GET'])
def get_process_options():
    """获取工序选项（用于下拉选择）"""
    try:
        items = ProcessDefinition.query.filter_by(is_active=True).order_by(ProcessDefinition.code).all()
        return jsonify({
            'success': True,
            'data': [{'id': item.id, 'code': item.code, 'name': item.name,
                     'process_type': item.process_type, 'standard_time': item.standard_time}
                    for item in items]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 工艺路线 API ====================

@process_bp.route('/routes', methods=['GET'])
def list_process_routes():
    """获取工艺路线列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '')
        product_id = request.args.get('product_id', type=int)
        status = request.args.get('status', '')
        is_active = request.args.get('is_active', '')

        query = ProcessRoute.query

        if keyword:
            query = query.filter(or_(
                ProcessRoute.route_code.like(f'%{keyword}%'),
                ProcessRoute.name.like(f'%{keyword}%'),
                ProcessRoute.product_code.like(f'%{keyword}%'),
                ProcessRoute.product_name.like(f'%{keyword}%')
            ))
        if product_id:
            query = query.filter(ProcessRoute.product_id == product_id)
        if status:
            query = query.filter(ProcessRoute.status == status)
        if is_active != '':
            query = query.filter(ProcessRoute.is_active == (is_active.lower() == 'true'))

        query = query.order_by(ProcessRoute.created_at.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return jsonify({
            'success': True,
            'data': [item.to_simple_dict() for item in items],
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            },
            'status_labels': ROUTE_STATUS_LABELS
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/routes/<int:id>', methods=['GET'])
def get_process_route(id):
    """获取工艺路线详情（含工序步骤）"""
    try:
        item = ProcessRoute.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': item.to_dict(include_steps=True),
            'status_labels': ROUTE_STATUS_LABELS
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/routes', methods=['POST'])
def create_process_route():
    """创建工艺路线"""
    try:
        data = request.get_json()

        # 自动生成编码
        route_code = data.get('route_code') or generate_route_code()

        # 检查编码唯一性
        if ProcessRoute.query.filter_by(route_code=route_code).first():
            return jsonify({'success': False, 'message': f"路线编码 {route_code} 已存在"}), 400

        route = ProcessRoute(
            route_code=route_code,
            name=data['name'],
            product_id=data.get('product_id'),
            product_code=data.get('product_code'),
            product_name=data.get('product_name'),
            version=data.get('version', '1.0'),
            is_default=data.get('is_default', False),
            description=data.get('description'),
            status='draft',
            is_active=True,
            effective_date=datetime.strptime(data['effective_date'], '%Y-%m-%d').date() if data.get('effective_date') else None,
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            created_by=data.get('created_by')
        )

        db.session.add(route)
        db.session.flush()  # 获取ID

        # 如果设为默认，取消同产品其他默认路线
        if route.is_default and route.product_id:
            ProcessRoute.query.filter(
                ProcessRoute.product_id == route.product_id,
                ProcessRoute.id != route.id
            ).update({'is_default': False})

        # 添加工序步骤
        steps_data = data.get('steps', [])
        for step_data in steps_data:
            step = ProcessRouteStep(
                route_id=route.id,
                process_id=step_data['process_id'],
                step_no=step_data['step_no'],
                step_name=step_data.get('step_name'),
                work_center_id=step_data.get('work_center_id'),
                machine_id=step_data.get('machine_id'),
                machine_name=step_data.get('machine_name'),
                setup_time=step_data.get('setup_time'),
                standard_time=step_data.get('standard_time'),
                move_time=step_data.get('move_time'),
                min_batch_size=step_data.get('min_batch_size'),
                max_batch_size=step_data.get('max_batch_size'),
                inspection_required=step_data.get('inspection_required'),
                inspection_type=step_data.get('inspection_type'),
                is_optional=step_data.get('is_optional', False),
                is_parallel=step_data.get('is_parallel', False),
                predecessor_steps=step_data.get('predecessor_steps'),
                notes=step_data.get('notes'),
                is_active=True
            )
            db.session.add(step)

        # 计算汇总
        route.recalculate_totals()

        db.session.commit()

        return jsonify({'success': True, 'data': route.to_dict(), 'message': '创建成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/routes/<int:id>', methods=['PUT'])
def update_process_route(id):
    """更新工艺路线"""
    try:
        route = ProcessRoute.query.get_or_404(id)
        data = request.get_json()

        # 只有草稿状态可以修改
        if route.status != 'draft' and not data.get('force'):
            return jsonify({'success': False, 'message': '只有草稿状态的工艺路线可以修改'}), 400

        # 更新基本信息
        for field in ['name', 'product_id', 'product_code', 'product_name',
                     'version', 'is_default', 'description']:
            if field in data:
                setattr(route, field, data[field])

        if data.get('effective_date'):
            route.effective_date = datetime.strptime(data['effective_date'], '%Y-%m-%d').date()
        if data.get('expiry_date'):
            route.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()

        route.updated_by = data.get('updated_by')

        # 如果设为默认，取消同产品其他默认路线
        if route.is_default and route.product_id:
            ProcessRoute.query.filter(
                ProcessRoute.product_id == route.product_id,
                ProcessRoute.id != route.id
            ).update({'is_default': False})

        # 更新工序步骤（如果提供）
        if 'steps' in data:
            # 删除旧步骤
            ProcessRouteStep.query.filter_by(route_id=route.id).delete()

            # 添加新步骤
            for step_data in data['steps']:
                step = ProcessRouteStep(
                    route_id=route.id,
                    process_id=step_data['process_id'],
                    step_no=step_data['step_no'],
                    step_name=step_data.get('step_name'),
                    work_center_id=step_data.get('work_center_id'),
                    machine_id=step_data.get('machine_id'),
                    machine_name=step_data.get('machine_name'),
                    setup_time=step_data.get('setup_time'),
                    standard_time=step_data.get('standard_time'),
                    move_time=step_data.get('move_time'),
                    min_batch_size=step_data.get('min_batch_size'),
                    max_batch_size=step_data.get('max_batch_size'),
                    inspection_required=step_data.get('inspection_required'),
                    inspection_type=step_data.get('inspection_type'),
                    is_optional=step_data.get('is_optional', False),
                    is_parallel=step_data.get('is_parallel', False),
                    predecessor_steps=step_data.get('predecessor_steps'),
                    notes=step_data.get('notes'),
                    is_active=True
                )
                db.session.add(step)

            # 重新计算汇总
            route.recalculate_totals()

        db.session.commit()

        return jsonify({'success': True, 'data': route.to_dict(), 'message': '更新成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/routes/<int:id>', methods=['DELETE'])
def delete_process_route(id):
    """删除工艺路线"""
    try:
        route = ProcessRoute.query.get_or_404(id)

        # 只有草稿状态可以删除
        if route.status != 'draft':
            return jsonify({'success': False, 'message': '只有草稿状态的工艺路线可以删除'}), 400

        # 检查是否被工单引用
        if WorkOrder.query.filter_by(process_route_id=route.id).first():
            return jsonify({'success': False, 'message': '该工艺路线已被工单引用，无法删除'}), 400

        db.session.delete(route)
        db.session.commit()

        return jsonify({'success': True, 'message': '删除成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/routes/<int:id>/activate', methods=['POST'])
def activate_process_route(id):
    """激活工艺路线"""
    try:
        route = ProcessRoute.query.get_or_404(id)
        data = request.get_json() or {}

        if route.status != 'draft':
            return jsonify({'success': False, 'message': '只有草稿状态的工艺路线可以激活'}), 400

        if route.total_steps == 0:
            return jsonify({'success': False, 'message': '工艺路线没有工序步骤，无法激活'}), 400

        route.status = 'active'
        route.approved_by = data.get('approved_by')
        route.approved_at = datetime.utcnow()

        if not route.effective_date:
            route.effective_date = datetime.utcnow().date()

        db.session.commit()

        return jsonify({'success': True, 'data': route.to_dict(), 'message': '激活成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/routes/<int:id>/obsolete', methods=['POST'])
def obsolete_process_route(id):
    """废弃工艺路线"""
    try:
        route = ProcessRoute.query.get_or_404(id)

        if route.status not in ['draft', 'active']:
            return jsonify({'success': False, 'message': '该工艺路线已废弃'}), 400

        route.status = 'obsolete'
        route.is_active = False
        route.expiry_date = datetime.utcnow().date()

        db.session.commit()

        return jsonify({'success': True, 'data': route.to_dict(), 'message': '已废弃'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/routes/<int:id>/copy', methods=['POST'])
def copy_process_route(id):
    """复制工艺路线（创建新版本）"""
    try:
        original = ProcessRoute.query.get_or_404(id)
        data = request.get_json() or {}

        # 生成新编码
        new_code = generate_route_code()

        # 计算新版本号
        if data.get('new_version'):
            new_version = data['new_version']
        else:
            try:
                ver_parts = original.version.split('.')
                new_version = f"{ver_parts[0]}.{int(ver_parts[1]) + 1}"
            except:
                new_version = f"{original.version}.1"

        # 创建新路线
        new_route = ProcessRoute(
            route_code=new_code,
            name=data.get('name', f"{original.name} (复制)"),
            product_id=original.product_id,
            product_code=original.product_code,
            product_name=original.product_name,
            version=new_version,
            is_default=False,
            description=original.description,
            status='draft',
            is_active=True,
            created_by=data.get('created_by')
        )

        db.session.add(new_route)
        db.session.flush()

        # 复制工序步骤
        for step in original.steps:
            new_step = ProcessRouteStep(
                route_id=new_route.id,
                process_id=step.process_id,
                step_no=step.step_no,
                step_name=step.step_name,
                work_center_id=step.work_center_id,
                machine_id=step.machine_id,
                machine_name=step.machine_name,
                setup_time=step.setup_time,
                standard_time=step.standard_time,
                move_time=step.move_time,
                min_batch_size=step.min_batch_size,
                max_batch_size=step.max_batch_size,
                inspection_required=step.inspection_required,
                inspection_type=step.inspection_type,
                is_optional=step.is_optional,
                is_parallel=step.is_parallel,
                predecessor_steps=step.predecessor_steps,
                notes=step.notes,
                is_active=True
            )
            db.session.add(new_step)

        new_route.recalculate_totals()
        db.session.commit()

        return jsonify({'success': True, 'data': new_route.to_dict(), 'message': '复制成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/routes/options', methods=['GET'])
def get_route_options():
    """获取工艺路线选项（用于工单选择）"""
    try:
        product_id = request.args.get('product_id', type=int)

        query = ProcessRoute.query.filter_by(status='active', is_active=True)
        if product_id:
            query = query.filter_by(product_id=product_id)

        items = query.order_by(ProcessRoute.is_default.desc(), ProcessRoute.route_code).all()

        return jsonify({
            'success': True,
            'data': [{'id': item.id, 'route_code': item.route_code, 'name': item.name,
                     'version': item.version, 'is_default': item.is_default,
                     'total_steps': item.total_steps, 'total_standard_time': item.total_standard_time}
                    for item in items]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 工单工序 API ====================

@process_bp.route('/work-order/<int:work_order_id>/processes', methods=['GET'])
def list_work_order_processes(work_order_id):
    """获取工单的所有工序"""
    try:
        work_order = WorkOrder.query.get_or_404(work_order_id)

        processes = WorkOrderProcess.query.filter_by(
            work_order_id=work_order_id
        ).order_by(WorkOrderProcess.step_no).all()

        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in processes],
            'work_order': work_order.to_dict(),
            'status_labels': PROCESS_STATUS_LABELS
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/work-order/<int:work_order_id>/generate-processes', methods=['POST'])
def generate_work_order_processes(work_order_id):
    """根据工艺路线为工单生成工序列表"""
    try:
        work_order = WorkOrder.query.get_or_404(work_order_id)
        data = request.get_json() or {}

        route_id = data.get('route_id') or work_order.process_route_id
        if not route_id:
            return jsonify({'success': False, 'message': '请指定工艺路线'}), 400

        route = ProcessRoute.query.get_or_404(route_id)

        # 检查是否已有工序
        existing = WorkOrderProcess.query.filter_by(work_order_id=work_order_id).first()
        if existing and not data.get('force'):
            return jsonify({'success': False, 'message': '工单已有工序，如需重新生成请设置 force=true'}), 400

        # 删除现有工序
        WorkOrderProcess.query.filter_by(work_order_id=work_order_id).delete()

        # 根据工艺路线步骤生成工单工序
        steps = route.steps.filter_by(is_active=True).order_by(ProcessRouteStep.step_no).all()

        for i, step in enumerate(steps):
            process = step.process

            # 计算计划工时
            setup_time = step.setup_time if step.setup_time is not None else (process.setup_time if process else 0)
            standard_time = step.standard_time if step.standard_time is not None else (process.standard_time if process else 0)
            planned_hours = (setup_time + standard_time * work_order.planned_quantity) / 60

            wo_process = WorkOrderProcess(
                work_order_id=work_order_id,
                route_step_id=step.id,
                process_id=step.process_id,
                step_no=step.step_no,
                process_code=process.code if process else None,
                process_name=step.step_name or (process.name if process else f'工序{step.step_no}'),
                process_type=process.process_type if process else 'other',
                planned_quantity=work_order.planned_quantity,
                work_center_id=step.work_center_id or (process.work_center_id if process else None),
                work_center_name=step.work_center.name if step.work_center else (process.work_center.name if process and process.work_center else None),
                machine_id=step.machine_id or (process.default_machine_id if process else None),
                machine_name=step.machine_name or (process.default_machine_name if process else None),
                setup_time=setup_time,
                standard_time=standard_time,
                planned_hours=planned_hours,
                inspection_required=step.inspection_required if step.inspection_required is not None else (process.inspection_required if process else False),
                status='pending',
                is_current=(i == 0)  # 第一个工序为当前工序
            )
            db.session.add(wo_process)

        # 更新工单的工艺路线ID和当前步骤
        work_order.process_route_id = route_id
        work_order.current_step = 1 if steps else 0

        db.session.commit()

        # 返回生成的工序列表
        processes = WorkOrderProcess.query.filter_by(
            work_order_id=work_order_id
        ).order_by(WorkOrderProcess.step_no).all()

        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in processes],
            'message': f'成功生成 {len(processes)} 个工序'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/work-order-process/<int:id>/start', methods=['POST'])
def start_work_order_process(id):
    """开始执行工序"""
    try:
        process = WorkOrderProcess.query.get_or_404(id)
        data = request.get_json() or {}

        if not process.can_transition_to('in_progress'):
            return jsonify({'success': False, 'message': f'当前状态 {process.status} 不能开始执行'}), 400

        process.status = 'in_progress'
        process.actual_start = datetime.utcnow()
        process.operator_id = data.get('operator_id')
        process.operator_name = data.get('operator_name')
        process.machine_id = data.get('machine_id') or process.machine_id
        process.machine_name = data.get('machine_name') or process.machine_name

        # 标记为当前工序
        WorkOrderProcess.query.filter_by(work_order_id=process.work_order_id).update({'is_current': False})
        process.is_current = True

        # 更新工单状态和当前步骤
        work_order = process.work_order
        if work_order.status == 'pending':
            work_order.status = 'in_progress'
            work_order.actual_start = datetime.utcnow()
        work_order.current_step = process.step_no

        db.session.commit()

        return jsonify({'success': True, 'data': process.to_dict(), 'message': '开始执行'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/work-order-process/<int:id>/complete', methods=['POST'])
def complete_work_order_process(id):
    """完成工序"""
    try:
        process = WorkOrderProcess.query.get_or_404(id)
        data = request.get_json() or {}

        if not process.can_transition_to('completed'):
            return jsonify({'success': False, 'message': f'当前状态 {process.status} 不能完成'}), 400

        # 更新完成信息
        process.status = 'completed'
        process.actual_end = datetime.utcnow()
        process.completed_quantity = data.get('completed_quantity', process.planned_quantity)
        process.defect_quantity = data.get('defect_quantity', 0)
        process.completion_notes = data.get('completion_notes')

        # 计算实际工时
        if process.actual_start:
            diff = process.actual_end - process.actual_start
            process.actual_hours = diff.total_seconds() / 3600

        # 如果需要检验，更新检验状态
        if process.inspection_required:
            process.inspection_status = data.get('inspection_status', 'pending')
            process.inspection_result = data.get('inspection_result')

        process.is_current = False

        # 找到下一个待执行的工序
        next_process = WorkOrderProcess.query.filter(
            WorkOrderProcess.work_order_id == process.work_order_id,
            WorkOrderProcess.step_no > process.step_no,
            WorkOrderProcess.status == 'pending'
        ).order_by(WorkOrderProcess.step_no).first()

        if next_process:
            next_process.is_current = True

        # 检查工单是否完成
        work_order = process.work_order
        remaining = WorkOrderProcess.query.filter(
            WorkOrderProcess.work_order_id == process.work_order_id,
            WorkOrderProcess.status.notin_(['completed', 'skipped'])
        ).count()

        if remaining == 0:
            work_order.status = 'completed'
            work_order.actual_end = datetime.utcnow()

            # 汇总完成数量
            total_completed = db.session.query(
                db.func.min(WorkOrderProcess.completed_quantity)
            ).filter(
                WorkOrderProcess.work_order_id == work_order.id,
                WorkOrderProcess.status == 'completed'
            ).scalar() or 0

            total_defect = db.session.query(
                db.func.sum(WorkOrderProcess.defect_quantity)
            ).filter(
                WorkOrderProcess.work_order_id == work_order.id
            ).scalar() or 0

            work_order.completed_quantity = total_completed
            work_order.defect_quantity = total_defect

        db.session.commit()

        return jsonify({'success': True, 'data': process.to_dict(), 'message': '工序完成'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/work-order-process/<int:id>/pause', methods=['POST'])
def pause_work_order_process(id):
    """暂停工序"""
    try:
        process = WorkOrderProcess.query.get_or_404(id)
        data = request.get_json() or {}

        if not process.can_transition_to('paused'):
            return jsonify({'success': False, 'message': f'当前状态 {process.status} 不能暂停'}), 400

        process.status = 'paused'
        process.notes = data.get('notes', process.notes)

        db.session.commit()

        return jsonify({'success': True, 'data': process.to_dict(), 'message': '已暂停'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/work-order-process/<int:id>/skip', methods=['POST'])
def skip_work_order_process(id):
    """跳过工序"""
    try:
        process = WorkOrderProcess.query.get_or_404(id)
        data = request.get_json() or {}

        if not process.can_transition_to('skipped'):
            return jsonify({'success': False, 'message': f'当前状态 {process.status} 不能跳过'}), 400

        process.status = 'skipped'
        process.notes = data.get('reason', '已跳过')
        process.is_current = False

        # 找到下一个工序
        next_process = WorkOrderProcess.query.filter(
            WorkOrderProcess.work_order_id == process.work_order_id,
            WorkOrderProcess.step_no > process.step_no,
            WorkOrderProcess.status == 'pending'
        ).order_by(WorkOrderProcess.step_no).first()

        if next_process:
            next_process.is_current = True

        db.session.commit()

        return jsonify({'success': True, 'data': process.to_dict(), 'message': '已跳过'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/work-order-process/<int:id>/assign', methods=['POST'])
def assign_work_order_process(id):
    """派工 - 为工序指派操作员和设备"""
    try:
        process = WorkOrderProcess.query.get_or_404(id)
        data = request.get_json()

        if process.status not in ['pending', 'waiting']:
            return jsonify({'success': False, 'message': '只能对待开始或等待中的工序派工'}), 400

        process.operator_id = data.get('operator_id')
        process.operator_name = data.get('operator_name')
        process.machine_id = data.get('machine_id')
        process.machine_name = data.get('machine_name')
        process.work_center_id = data.get('work_center_id') or process.work_center_id
        process.work_center_name = data.get('work_center_name') or process.work_center_name
        process.planned_start = datetime.strptime(data['planned_start'], '%Y-%m-%d %H:%M:%S') if data.get('planned_start') else None
        process.planned_end = datetime.strptime(data['planned_end'], '%Y-%m-%d %H:%M:%S') if data.get('planned_end') else None
        process.assigned_by = data.get('assigned_by')
        process.assigned_at = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'data': process.to_dict(), 'message': '派工成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== 统计与报表 API ====================

@process_bp.route('/statistics/process-types', methods=['GET'])
def get_process_type_statistics():
    """按工序类型统计"""
    try:
        stats = db.session.query(
            ProcessDefinition.process_type,
            db.func.count(ProcessDefinition.id).label('count')
        ).group_by(ProcessDefinition.process_type).all()

        return jsonify({
            'success': True,
            'data': [{'type': s[0], 'label': PROCESS_TYPE_LABELS.get(s[0], s[0]), 'count': s[1]} for s in stats]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/statistics/route-status', methods=['GET'])
def get_route_status_statistics():
    """按工艺路线状态统计"""
    try:
        stats = db.session.query(
            ProcessRoute.status,
            db.func.count(ProcessRoute.id).label('count')
        ).group_by(ProcessRoute.status).all()

        return jsonify({
            'success': True,
            'data': [{'status': s[0], 'label': ROUTE_STATUS_LABELS.get(s[0], s[0]), 'count': s[1]} for s in stats]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@process_bp.route('/statistics/work-order-progress/<int:work_order_id>', methods=['GET'])
def get_work_order_progress(work_order_id):
    """获取工单工序进度统计"""
    try:
        work_order = WorkOrder.query.get_or_404(work_order_id)

        # 统计各状态工序数
        status_counts = db.session.query(
            WorkOrderProcess.status,
            db.func.count(WorkOrderProcess.id).label('count')
        ).filter(
            WorkOrderProcess.work_order_id == work_order_id
        ).group_by(WorkOrderProcess.status).all()

        status_dict = {s[0]: s[1] for s in status_counts}
        total = sum(s[1] for s in status_counts)
        completed = status_dict.get('completed', 0) + status_dict.get('skipped', 0)

        # 获取当前工序
        current = WorkOrderProcess.query.filter_by(
            work_order_id=work_order_id,
            is_current=True
        ).first()

        return jsonify({
            'success': True,
            'data': {
                'work_order_id': work_order_id,
                'work_order_no': work_order.order_no,
                'total_processes': total,
                'completed_processes': completed,
                'progress_rate': round(completed / total * 100, 2) if total > 0 else 0,
                'status_breakdown': status_dict,
                'current_process': current.to_dict() if current else None
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
