# -*- coding: utf-8 -*-
"""
合同管理 API
包含: 合同 CRUD、审批流程、统计
"""
from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_

from .. import db
from ..models import (
    Customer, SalesOpportunity,
    Contract, ContractItem, ContractApproval,
    ContractStatus, ContractType, ApprovalStatus,
    CONTRACT_TYPE_MAP, CONTRACT_STATUS_MAP, APPROVAL_STATUS_MAP
)

contracts_bp = Blueprint('contracts', __name__, url_prefix='/api/contracts')


@contracts_bp.route('', methods=['GET'])
def get_contracts():
    """获取合同列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', '')
        contract_type = request.args.get('contract_type', '')
        customer_id = request.args.get('customer_id', type=int)
        owner_id = request.args.get('owner_id', type=int)
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        expiring_days = request.args.get('expiring_days', type=int)

        query = Contract.query

        # 关键字搜索
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    Contract.name.ilike(like),
                    Contract.contract_no.ilike(like),
                    Contract.customer_name.ilike(like),
                )
            )

        # 状态筛选
        if status:
            query = query.filter(Contract.status == status)

        # 类型筛选
        if contract_type:
            query = query.filter(Contract.contract_type == contract_type)

        # 客户筛选
        if customer_id:
            query = query.filter(Contract.customer_id == customer_id)

        # 负责人筛选
        if owner_id:
            query = query.filter(Contract.owner_id == owner_id)

        # 日期范围
        if start_date:
            query = query.filter(Contract.created_at >= start_date)
        if end_date:
            query = query.filter(Contract.created_at <= end_date + ' 23:59:59')

        # 即将到期筛选
        if expiring_days:
            today = date.today()
            expire_date = today + timedelta(days=expiring_days)
            query = query.filter(
                Contract.status == ContractStatus.ACTIVE.value,
                Contract.end_date <= expire_date,
                Contract.end_date >= today
            )

        # 排序
        query = query.order_by(Contract.updated_at.desc())

        # 分页
        total = query.count()
        contracts = query.offset((page - 1) * page_size).limit(page_size).all()

        return jsonify({
            "contracts": [c.to_dict() for c in contracts],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/<int:id>', methods=['GET'])
def get_contract(id):
    """获取单个合同详情"""
    try:
        contract = Contract.query.get(id)
        if not contract:
            return jsonify({"error": "合同不存在"}), 404

        return jsonify(contract.to_dict(include_items=True, include_approvals=True))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('', methods=['POST'])
def create_contract():
    """创建合同"""
    try:
        data = request.get_json()

        # 必填验证
        if not data.get('name'):
            return jsonify({"error": "合同名称不能为空"}), 400
        if not data.get('customer_id'):
            return jsonify({"error": "客户不能为空"}), 400

        # 获取客户信息
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return jsonify({"error": "客户不存在"}), 404

        # 生成合同编号
        contract_no = Contract.generate_contract_no()

        contract = Contract(
            contract_no=contract_no,
            name=data['name'],
            contract_type=data.get('contract_type', ContractType.SALES.value),
            status=ContractStatus.DRAFT.value,
            customer_id=data['customer_id'],
            customer_name=customer.short_name or customer.name,
            opportunity_id=data.get('opportunity_id'),
            total_amount=data.get('total_amount', 0),
            currency=data.get('currency', 'CNY'),
            tax_rate=data.get('tax_rate', 13),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
            sign_date=datetime.strptime(data['sign_date'], '%Y-%m-%d').date() if data.get('sign_date') else None,
            our_signatory=data.get('our_signatory'),
            customer_signatory=data.get('customer_signatory'),
            payment_terms=data.get('payment_terms'),
            delivery_terms=data.get('delivery_terms'),
            special_terms=data.get('special_terms'),
            attachments=data.get('attachments', []),
            owner_id=data.get('owner_id'),
            owner_name=data.get('owner_name'),
            remark=data.get('remark'),
            created_by=data.get('created_by'),
        )

        db.session.add(contract)
        db.session.flush()  # 获取 contract.id

        # 处理合同明细
        items_data = data.get('items', [])
        for idx, item_data in enumerate(items_data):
            item = ContractItem(
                contract_id=contract.id,
                product_name=item_data.get('product_name', ''),
                specification=item_data.get('specification'),
                quantity=item_data.get('quantity', 1),
                unit=item_data.get('unit', '个'),
                unit_price=item_data.get('unit_price', 0),
                delivery_date=datetime.strptime(item_data['delivery_date'], '%Y-%m-%d').date() if item_data.get('delivery_date') else None,
                remark=item_data.get('remark'),
                sort_order=idx,
            )
            item.calculate_amount()
            db.session.add(item)

        # 重新计算总金额
        db.session.flush()
        contract.calculate_total()

        db.session.commit()

        return jsonify(contract.to_dict(include_items=True)), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/<int:id>', methods=['PUT'])
def update_contract(id):
    """更新合同"""
    try:
        contract = Contract.query.get(id)
        if not contract:
            return jsonify({"error": "合同不存在"}), 404

        # 只有草稿和已拒绝状态可以编辑
        if contract.status not in [ContractStatus.DRAFT.value]:
            return jsonify({"error": "当前状态不允许编辑"}), 400

        data = request.get_json()

        # 更新基本信息
        for field in ['name', 'contract_type', 'currency', 'tax_rate',
                      'our_signatory', 'customer_signatory',
                      'payment_terms', 'delivery_terms', 'special_terms',
                      'attachments', 'owner_id', 'owner_name', 'remark']:
            if field in data:
                setattr(contract, field, data[field])

        # 更新日期
        if 'start_date' in data:
            contract.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None
        if 'end_date' in data:
            contract.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
        if 'sign_date' in data:
            contract.sign_date = datetime.strptime(data['sign_date'], '%Y-%m-%d').date() if data['sign_date'] else None

        # 更新客户
        if 'customer_id' in data and data['customer_id'] != contract.customer_id:
            customer = Customer.query.get(data['customer_id'])
            if customer:
                contract.customer_id = customer.id
                contract.customer_name = customer.short_name or customer.name

        # 更新明细
        if 'items' in data:
            # 删除现有明细
            ContractItem.query.filter_by(contract_id=id).delete()

            # 添加新明细
            for idx, item_data in enumerate(data['items']):
                item = ContractItem(
                    contract_id=id,
                    product_name=item_data.get('product_name', ''),
                    specification=item_data.get('specification'),
                    quantity=item_data.get('quantity', 1),
                    unit=item_data.get('unit', '个'),
                    unit_price=item_data.get('unit_price', 0),
                    delivery_date=datetime.strptime(item_data['delivery_date'], '%Y-%m-%d').date() if item_data.get('delivery_date') else None,
                    remark=item_data.get('remark'),
                    sort_order=idx,
                )
                item.calculate_amount()
                db.session.add(item)

            # 重新计算总金额
            db.session.flush()
            contract.calculate_total()

        db.session.commit()

        return jsonify(contract.to_dict(include_items=True))

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/<int:id>', methods=['DELETE'])
def delete_contract(id):
    """删除合同"""
    try:
        contract = Contract.query.get(id)
        if not contract:
            return jsonify({"error": "合同不存在"}), 404

        # 只有草稿状态可以删除
        if contract.status != ContractStatus.DRAFT.value:
            return jsonify({"error": "只有草稿状态的合同可以删除"}), 400

        db.session.delete(contract)
        db.session.commit()

        return jsonify({"message": "删除成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/<int:id>/submit', methods=['POST'])
def submit_contract(id):
    """提交合同审批"""
    try:
        contract = Contract.query.get(id)
        if not contract:
            return jsonify({"error": "合同不存在"}), 404

        if contract.status != ContractStatus.DRAFT.value:
            return jsonify({"error": "只有草稿状态可以提交审批"}), 400

        data = request.get_json() or {}

        # 更新状态
        contract.status = ContractStatus.PENDING.value

        # 创建审批记录
        approval = ContractApproval(
            contract_id=id,
            approver_id=data.get('approver_id', 0),
            approver_name=data.get('approver_name', '待指定'),
            status=ApprovalStatus.PENDING.value,
        )
        db.session.add(approval)

        db.session.commit()

        return jsonify(contract.to_dict(include_approvals=True))

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/<int:id>/approve', methods=['POST'])
def approve_contract(id):
    """审批通过"""
    try:
        contract = Contract.query.get(id)
        if not contract:
            return jsonify({"error": "合同不存在"}), 404

        if contract.status != ContractStatus.PENDING.value:
            return jsonify({"error": "合同不在待审批状态"}), 400

        data = request.get_json() or {}

        # 更新合同状态
        contract.status = ContractStatus.APPROVED.value

        # 更新审批记录
        approval = ContractApproval.query.filter_by(
            contract_id=id,
            status=ApprovalStatus.PENDING.value
        ).first()

        if approval:
            approval.status = ApprovalStatus.APPROVED.value
            approval.comment = data.get('comment')
            approval.approver_id = data.get('approver_id', approval.approver_id)
            approval.approver_name = data.get('approver_name', approval.approver_name)
            approval.approved_at = datetime.utcnow()

        db.session.commit()

        return jsonify(contract.to_dict(include_approvals=True))

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/<int:id>/reject', methods=['POST'])
def reject_contract(id):
    """审批拒绝"""
    try:
        contract = Contract.query.get(id)
        if not contract:
            return jsonify({"error": "合同不存在"}), 404

        if contract.status != ContractStatus.PENDING.value:
            return jsonify({"error": "合同不在待审批状态"}), 400

        data = request.get_json() or {}

        # 更新合同状态（退回草稿）
        contract.status = ContractStatus.DRAFT.value

        # 更新审批记录
        approval = ContractApproval.query.filter_by(
            contract_id=id,
            status=ApprovalStatus.PENDING.value
        ).first()

        if approval:
            approval.status = ApprovalStatus.REJECTED.value
            approval.comment = data.get('comment', '审批拒绝')
            approval.approver_id = data.get('approver_id', approval.approver_id)
            approval.approver_name = data.get('approver_name', approval.approver_name)
            approval.approved_at = datetime.utcnow()

        db.session.commit()

        return jsonify(contract.to_dict(include_approvals=True))

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/<int:id>/activate', methods=['POST'])
def activate_contract(id):
    """激活合同（生效）"""
    try:
        contract = Contract.query.get(id)
        if not contract:
            return jsonify({"error": "合同不存在"}), 404

        if contract.status != ContractStatus.APPROVED.value:
            return jsonify({"error": "只有已批准的合同可以激活"}), 400

        contract.status = ContractStatus.ACTIVE.value

        db.session.commit()

        return jsonify(contract.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/<int:id>/terminate', methods=['POST'])
def terminate_contract(id):
    """终止合同"""
    try:
        contract = Contract.query.get(id)
        if not contract:
            return jsonify({"error": "合同不存在"}), 404

        if contract.status != ContractStatus.ACTIVE.value:
            return jsonify({"error": "只有生效中的合同可以终止"}), 400

        data = request.get_json() or {}

        contract.status = ContractStatus.TERMINATED.value
        if data.get('remark'):
            contract.remark = (contract.remark or '') + f"\n[终止原因] {data['remark']}"

        db.session.commit()

        return jsonify(contract.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/expiring', methods=['GET'])
def get_expiring_contracts():
    """获取即将到期的合同"""
    try:
        days = request.args.get('days', 30, type=int)
        owner_id = request.args.get('owner_id', type=int)

        today = date.today()
        expire_date = today + timedelta(days=days)

        query = Contract.query.filter(
            Contract.status == ContractStatus.ACTIVE.value,
            Contract.end_date <= expire_date,
            Contract.end_date >= today
        )

        if owner_id:
            query = query.filter(Contract.owner_id == owner_id)

        contracts = query.order_by(Contract.end_date.asc()).all()

        # 按到期时间分组
        expired = []
        expiring_7 = []
        expiring_30 = []

        for c in contracts:
            days_left = (c.end_date - today).days
            c_dict = c.to_dict()
            c_dict['days_left'] = days_left

            if days_left <= 0:
                expired.append(c_dict)
            elif days_left <= 7:
                expiring_7.append(c_dict)
            else:
                expiring_30.append(c_dict)

        return jsonify({
            "expired": expired,
            "expiring_7_days": expiring_7,
            "expiring_30_days": expiring_30,
            "total": len(contracts)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/statistics', methods=['GET'])
def get_contract_statistics():
    """获取合同统计"""
    try:
        owner_id = request.args.get('owner_id', type=int)
        year = request.args.get('year', type=int) or datetime.now().year

        # 基础查询
        base_query = Contract.query

        if owner_id:
            base_query = base_query.filter(Contract.owner_id == owner_id)

        # 年度筛选
        base_query = base_query.filter(func.year(Contract.created_at) == year)

        # 各状态统计
        total_count = base_query.count()

        status_stats = {}
        for status in ContractStatus:
            count = base_query.filter(Contract.status == status.value).count()
            status_stats[status.value] = {
                "count": count,
                "label": CONTRACT_STATUS_MAP.get(status.value, status.value)
            }

        # 金额统计
        total_amount = base_query.with_entities(
            func.coalesce(func.sum(Contract.total_amount), 0)
        ).scalar() or 0

        active_amount = base_query.filter(
            Contract.status == ContractStatus.ACTIVE.value
        ).with_entities(
            func.coalesce(func.sum(Contract.total_amount), 0)
        ).scalar() or 0

        # 类型分布
        type_stats = db.session.query(
            Contract.contract_type,
            func.count(Contract.id),
            func.coalesce(func.sum(Contract.total_amount), 0)
        ).filter(func.year(Contract.created_at) == year)

        if owner_id:
            type_stats = type_stats.filter(Contract.owner_id == owner_id)

        type_stats = type_stats.group_by(Contract.contract_type).all()

        type_distribution = {
            t: {"count": c, "amount": float(a), "label": CONTRACT_TYPE_MAP.get(t, t)}
            for t, c, a in type_stats
        }

        return jsonify({
            "total_count": total_count,
            "total_amount": float(total_amount),
            "active_amount": float(active_amount),
            "status_stats": status_stats,
            "type_distribution": type_distribution,
            "year": year,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/from-opportunity/<int:opportunity_id>', methods=['GET'])
def create_from_opportunity(opportunity_id):
    """从销售机会创建合同（获取预填数据）"""
    try:
        opportunity = SalesOpportunity.query.get(opportunity_id)
        if not opportunity:
            return jsonify({"error": "销售机会不存在"}), 404

        # 返回预填数据
        return jsonify({
            "name": f"{opportunity.customer_name} - {opportunity.name}",
            "customer_id": opportunity.customer_id,
            "customer_name": opportunity.customer_name,
            "opportunity_id": opportunity.id,
            "total_amount": float(opportunity.expected_amount or 0),
            "currency": opportunity.currency,
            "owner_id": opportunity.owner_id,
            "owner_name": opportunity.owner_name,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@contracts_bp.route('/types', methods=['GET'])
def get_contract_types():
    """获取合同类型和状态定义"""
    return jsonify({
        "types": [
            {"value": t.value, "label": CONTRACT_TYPE_MAP.get(t.value)}
            for t in ContractType
        ],
        "statuses": [
            {"value": s.value, "label": CONTRACT_STATUS_MAP.get(s.value)}
            for s in ContractStatus
        ],
    })
