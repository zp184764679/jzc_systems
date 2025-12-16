# -*- coding: utf-8 -*-
"""
采购合同管理路由
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import os
from werkzeug.utils import secure_filename

from extensions import db
from models.contract import (
    Contract, ContractItem,
    CONTRACT_STATUS_LABELS, CONTRACT_TYPE_LABELS
)
from models.supplier import Supplier
from models.purchase_order import PurchaseOrder

logger = logging.getLogger(__name__)

contract_bp = Blueprint('contracts', __name__)
URL_PREFIX = '/api/v1'

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== 合同 CRUD ====================

@contract_bp.route('/contracts', methods=['GET'])
def get_contracts():
    """获取合同列表"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # 筛选参数
        status = request.args.get('status')
        contract_type = request.args.get('contract_type')
        supplier_id = request.args.get('supplier_id', type=int)
        search = request.args.get('search', '').strip()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = Contract.query

        if status:
            query = query.filter(Contract.status == status)
        if contract_type:
            query = query.filter(Contract.contract_type == contract_type)
        if supplier_id:
            query = query.filter(Contract.supplier_id == supplier_id)
        if search:
            query = query.filter(
                db.or_(
                    Contract.contract_number.ilike(f'%{search}%'),
                    Contract.title.ilike(f'%{search}%'),
                    Contract.supplier_name.ilike(f'%{search}%')
                )
            )
        if start_date:
            query = query.filter(Contract.start_date >= start_date)
        if end_date:
            query = query.filter(Contract.end_date <= end_date)

        # 排序
        query = query.order_by(Contract.created_at.desc())

        # 分页
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'items': [c.to_dict() for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })

    except Exception as e:
        logger.error(f"获取合同列表失败: {e}")
        return jsonify({'error': '获取合同列表失败'}), 500


@contract_bp.route('/contracts/<int:contract_id>', methods=['GET'])
def get_contract(contract_id):
    """获取合同详情"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        return jsonify(contract.to_dict(include_items=True))

    except Exception as e:
        logger.error(f"获取合同详情失败: {e}")
        return jsonify({'error': '获取合同详情失败'}), 500


@contract_bp.route('/contracts', methods=['POST'])
def create_contract():
    """创建合同"""
    try:
        data = request.get_json() or {}

        # 验证必填字段
        required_fields = ['title', 'supplier_id', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 获取供应商信息
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({'error': '供应商不存在'}), 404

        # 生成合同编号
        contract_number = Contract.generate_contract_number()

        # 创建合同
        contract = Contract(
            contract_number=contract_number,
            title=data['title'],
            contract_type=data.get('contract_type', 'single'),
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            total_amount=data.get('total_amount', 0),
            currency=data.get('currency', 'CNY'),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date(),
            po_id=data.get('po_id'),
            payment_terms=data.get('payment_terms'),
            delivery_terms=data.get('delivery_terms'),
            warranty_terms=data.get('warranty_terms'),
            penalty_clause=data.get('penalty_clause'),
            other_terms=data.get('other_terms'),
            remarks=data.get('remarks'),
            status='draft',
            created_by=data.get('created_by'),
        )

        db.session.add(contract)

        # 添加合同明细
        items = data.get('items', [])
        total_amount = 0
        for item_data in items:
            quantity = float(item_data.get('quantity', 0))
            unit_price = float(item_data.get('unit_price', 0))
            amount = quantity * unit_price
            total_amount += amount

            item = ContractItem(
                contract=contract,
                material_code=item_data.get('material_code'),
                material_name=item_data.get('material_name', ''),
                specification=item_data.get('specification'),
                unit=item_data.get('unit'),
                quantity=quantity,
                unit_price=unit_price,
                amount=amount,
                remarks=item_data.get('remarks'),
            )
            db.session.add(item)

        # 更新合同总金额
        if items:
            contract.total_amount = total_amount

        db.session.commit()

        return jsonify({
            'message': '合同创建成功',
            'contract': contract.to_dict(include_items=True)
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建合同失败: {e}")
        return jsonify({'error': f'创建合同失败: {str(e)}'}), 500


@contract_bp.route('/contracts/<int:contract_id>', methods=['PUT'])
def update_contract(contract_id):
    """更新合同"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status not in ['draft', 'pending_approval']:
            return jsonify({'error': '只能修改草稿或待审批状态的合同'}), 400

        data = request.get_json() or {}

        # 更新基本信息
        if 'title' in data:
            contract.title = data['title']
        if 'contract_type' in data:
            contract.contract_type = data['contract_type']
        if 'supplier_id' in data:
            supplier = Supplier.query.get(data['supplier_id'])
            if supplier:
                contract.supplier_id = supplier.id
                contract.supplier_name = supplier.name
        if 'total_amount' in data:
            contract.total_amount = data['total_amount']
        if 'currency' in data:
            contract.currency = data['currency']
        if 'start_date' in data:
            contract.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            contract.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if 'po_id' in data:
            contract.po_id = data['po_id']
        if 'payment_terms' in data:
            contract.payment_terms = data['payment_terms']
        if 'delivery_terms' in data:
            contract.delivery_terms = data['delivery_terms']
        if 'warranty_terms' in data:
            contract.warranty_terms = data['warranty_terms']
        if 'penalty_clause' in data:
            contract.penalty_clause = data['penalty_clause']
        if 'other_terms' in data:
            contract.other_terms = data['other_terms']
        if 'remarks' in data:
            contract.remarks = data['remarks']

        # 更新合同明细
        if 'items' in data:
            # 删除现有明细
            ContractItem.query.filter_by(contract_id=contract.id).delete()

            # 添加新明细
            total_amount = 0
            for item_data in data['items']:
                quantity = float(item_data.get('quantity', 0))
                unit_price = float(item_data.get('unit_price', 0))
                amount = quantity * unit_price
                total_amount += amount

                item = ContractItem(
                    contract_id=contract.id,
                    material_code=item_data.get('material_code'),
                    material_name=item_data.get('material_name', ''),
                    specification=item_data.get('specification'),
                    unit=item_data.get('unit'),
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                    remarks=item_data.get('remarks'),
                )
                db.session.add(item)

            contract.total_amount = total_amount

        db.session.commit()

        return jsonify({
            'message': '合同更新成功',
            'contract': contract.to_dict(include_items=True)
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新合同失败: {e}")
        return jsonify({'error': f'更新合同失败: {str(e)}'}), 500


@contract_bp.route('/contracts/<int:contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    """删除合同"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status not in ['draft', 'cancelled']:
            return jsonify({'error': '只能删除草稿或已取消的合同'}), 400

        db.session.delete(contract)
        db.session.commit()

        return jsonify({'message': '合同删除成功'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除合同失败: {e}")
        return jsonify({'error': '删除合同失败'}), 500


# ==================== 合同审批 ====================

@contract_bp.route('/contracts/<int:contract_id>/submit', methods=['POST'])
def submit_contract(contract_id):
    """提交合同审批"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status != 'draft':
            return jsonify({'error': '只能提交草稿状态的合同'}), 400

        data = request.get_json() or {}

        contract.status = 'pending_approval'
        contract.submitted_by = data.get('submitted_by')
        contract.submitted_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'message': '合同已提交审批',
            'contract': contract.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"提交合同审批失败: {e}")
        return jsonify({'error': '提交合同审批失败'}), 500


@contract_bp.route('/contracts/<int:contract_id>/approve', methods=['POST'])
def approve_contract(contract_id):
    """审批通过合同"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status != 'pending_approval':
            return jsonify({'error': '只能审批待审批状态的合同'}), 400

        data = request.get_json() or {}

        contract.status = 'approved'
        contract.approved_by = data.get('approved_by')
        contract.approved_at = datetime.utcnow()
        contract.approval_note = data.get('approval_note')

        db.session.commit()

        return jsonify({
            'message': '合同审批通过',
            'contract': contract.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"审批合同失败: {e}")
        return jsonify({'error': '审批合同失败'}), 500


@contract_bp.route('/contracts/<int:contract_id>/reject', methods=['POST'])
def reject_contract(contract_id):
    """拒绝合同"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status != 'pending_approval':
            return jsonify({'error': '只能拒绝待审批状态的合同'}), 400

        data = request.get_json() or {}

        contract.status = 'draft'  # 退回草稿状态
        contract.approval_note = data.get('rejection_reason', '审批未通过')

        db.session.commit()

        return jsonify({
            'message': '合同已退回',
            'contract': contract.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"拒绝合同失败: {e}")
        return jsonify({'error': '拒绝合同失败'}), 500


@contract_bp.route('/contracts/<int:contract_id>/activate', methods=['POST'])
def activate_contract(contract_id):
    """激活合同（开始执行）"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status != 'approved':
            return jsonify({'error': '只能激活已批准的合同'}), 400

        contract.status = 'active'
        db.session.commit()

        return jsonify({
            'message': '合同已激活',
            'contract': contract.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"激活合同失败: {e}")
        return jsonify({'error': '激活合同失败'}), 500


@contract_bp.route('/contracts/<int:contract_id>/complete', methods=['POST'])
def complete_contract(contract_id):
    """完成合同"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status != 'active':
            return jsonify({'error': '只能完成执行中的合同'}), 400

        contract.status = 'completed'
        db.session.commit()

        return jsonify({
            'message': '合同已完成',
            'contract': contract.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"完成合同失败: {e}")
        return jsonify({'error': '完成合同失败'}), 500


@contract_bp.route('/contracts/<int:contract_id>/cancel', methods=['POST'])
def cancel_contract(contract_id):
    """取消合同"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status in ['completed', 'cancelled']:
            return jsonify({'error': '已完成或已取消的合同不能再取消'}), 400

        data = request.get_json() or {}

        contract.status = 'cancelled'
        contract.remarks = data.get('cancel_reason', contract.remarks)

        db.session.commit()

        return jsonify({
            'message': '合同已取消',
            'contract': contract.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"取消合同失败: {e}")
        return jsonify({'error': '取消合同失败'}), 500


# ==================== 合同执行 ====================

@contract_bp.route('/contracts/<int:contract_id>/execute', methods=['POST'])
def execute_contract(contract_id):
    """登记合同执行"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if contract.status != 'active':
            return jsonify({'error': '只能登记执行中的合同'}), 400

        data = request.get_json() or {}
        executions = data.get('executions', [])

        for exec_data in executions:
            item_id = exec_data.get('item_id')
            quantity = float(exec_data.get('quantity', 0))

            item = ContractItem.query.get(item_id)
            if item and item.contract_id == contract.id:
                # 检查是否超出合同数量
                if item.executed_quantity + quantity > item.quantity:
                    return jsonify({
                        'error': f'物料 {item.material_name} 执行数量超出合同数量'
                    }), 400

                item.executed_quantity += quantity

        # 更新合同已执行金额
        total_executed = sum(
            float(item.executed_quantity) * float(item.unit_price)
            for item in contract.items
        )
        contract.executed_amount = total_executed

        # 检查是否全部执行完成
        all_completed = all(
            item.executed_quantity >= item.quantity
            for item in contract.items
        )
        if all_completed:
            contract.status = 'completed'

        db.session.commit()

        return jsonify({
            'message': '执行记录已登记',
            'contract': contract.to_dict(include_items=True)
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"登记合同执行失败: {e}")
        return jsonify({'error': '登记合同执行失败'}), 500


# ==================== 合同附件 ====================

@contract_bp.route('/contracts/<int:contract_id>/attachment', methods=['POST'])
def upload_attachment(contract_id):
    """上传合同附件"""
    try:
        contract = Contract.query.get(contract_id)
        if not contract:
            return jsonify({'error': '合同不存在'}), 404

        if 'file' not in request.files:
            return jsonify({'error': '未提供文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '不支持的文件类型'}), 400

        # 保存文件
        filename = secure_filename(file.filename)
        year_month = datetime.utcnow().strftime('%Y/%m')
        upload_folder = os.path.join('uploads', 'contracts', year_month)
        os.makedirs(upload_folder, exist_ok=True)

        # 添加时间戳避免重名
        timestamp = datetime.utcnow().strftime('%H%M%S')
        filename = f"{contract.contract_number}_{timestamp}_{filename}"
        filepath = os.path.join(upload_folder, filename)

        file.save(filepath)

        # 更新合同附件路径
        contract.attachment_path = filepath
        db.session.commit()

        return jsonify({
            'message': '附件上传成功',
            'attachment_path': filepath
        })

    except Exception as e:
        logger.error(f"上传附件失败: {e}")
        return jsonify({'error': '上传附件失败'}), 500


# ==================== 统计和查询 ====================

@contract_bp.route('/contracts/statistics', methods=['GET'])
def get_contract_statistics():
    """获取合同统计"""
    try:
        today = datetime.utcnow().date()

        # 各状态合同数量
        status_counts = {}
        for status in CONTRACT_STATUS_LABELS.keys():
            count = Contract.query.filter(Contract.status == status).count()
            status_counts[status] = count

        # 即将到期的合同（30天内）
        from datetime import timedelta
        expiring_count = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date <= today + timedelta(days=30),
            Contract.end_date >= today
        ).count()

        # 已过期但未完成的合同
        expired_count = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date < today
        ).count()

        # 本月新增合同
        from sqlalchemy import extract
        current_month = today.month
        current_year = today.year
        monthly_count = Contract.query.filter(
            extract('month', Contract.created_at) == current_month,
            extract('year', Contract.created_at) == current_year
        ).count()

        # 总金额统计
        from sqlalchemy import func
        total_amount = db.session.query(
            func.sum(Contract.total_amount)
        ).filter(Contract.status.in_(['active', 'completed'])).scalar() or 0

        executed_amount = db.session.query(
            func.sum(Contract.executed_amount)
        ).filter(Contract.status.in_(['active', 'completed'])).scalar() or 0

        return jsonify({
            'status_counts': status_counts,
            'expiring_count': expiring_count,
            'expired_count': expired_count,
            'monthly_count': monthly_count,
            'total_amount': float(total_amount),
            'executed_amount': float(executed_amount),
            'execution_rate': round(float(executed_amount) / float(total_amount) * 100, 2) if total_amount > 0 else 0
        })

    except Exception as e:
        logger.error(f"获取合同统计失败: {e}")
        return jsonify({'error': '获取合同统计失败'}), 500


@contract_bp.route('/contracts/expiring', methods=['GET'])
def get_expiring_contracts():
    """获取即将到期的合同"""
    try:
        days = request.args.get('days', 30, type=int)
        today = datetime.utcnow().date()

        from datetime import timedelta
        contracts = Contract.query.filter(
            Contract.status == 'active',
            Contract.end_date <= today + timedelta(days=days),
            Contract.end_date >= today
        ).order_by(Contract.end_date).all()

        return jsonify({
            'items': [c.to_dict() for c in contracts],
            'total': len(contracts)
        })

    except Exception as e:
        logger.error(f"获取即将到期合同失败: {e}")
        return jsonify({'error': '获取即将到期合同失败'}), 500


@contract_bp.route('/contracts/by-supplier/<int:supplier_id>', methods=['GET'])
def get_supplier_contracts(supplier_id):
    """获取供应商的所有合同"""
    try:
        contracts = Contract.query.filter(
            Contract.supplier_id == supplier_id
        ).order_by(Contract.created_at.desc()).all()

        return jsonify({
            'items': [c.to_dict() for c in contracts],
            'total': len(contracts)
        })

    except Exception as e:
        logger.error(f"获取供应商合同失败: {e}")
        return jsonify({'error': '获取供应商合同失败'}), 500


@contract_bp.route('/contracts/enums', methods=['GET'])
def get_contract_enums():
    """获取合同枚举值"""
    return jsonify({
        'statuses': CONTRACT_STATUS_LABELS,
        'types': CONTRACT_TYPE_LABELS
    })


# 蓝图列表（用于自动注册）
BLUEPRINTS = [contract_bp]
