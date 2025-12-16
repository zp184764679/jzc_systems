# -*- coding: utf-8 -*-
"""
销售机会 API
包含: 机会 CRUD、阶段推进、销售漏斗统计
"""
from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_

from .. import db
from ..models import (
    Customer, SalesOpportunity, OpportunityStageHistory, FollowUpRecord,
    OpportunityStage, STAGE_PROBABILITY_MAP, STAGE_NAME_MAP, PRIORITY_NAME_MAP
)

opportunities_bp = Blueprint('opportunities', __name__, url_prefix='/api/opportunities')


@opportunities_bp.route('', methods=['GET'])
def get_opportunities():
    """获取销售机会列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        keyword = request.args.get('keyword', '')
        stage = request.args.get('stage', '')
        owner_id = request.args.get('owner_id', type=int)
        customer_id = request.args.get('customer_id', type=int)
        priority = request.args.get('priority', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        query = SalesOpportunity.query

        # 关键字搜索
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    SalesOpportunity.name.ilike(like),
                    SalesOpportunity.opportunity_no.ilike(like),
                    SalesOpportunity.customer_name.ilike(like),
                )
            )

        # 阶段筛选
        if stage:
            query = query.filter(SalesOpportunity.stage == stage)

        # 负责人筛选
        if owner_id:
            query = query.filter(SalesOpportunity.owner_id == owner_id)

        # 客户筛选
        if customer_id:
            query = query.filter(SalesOpportunity.customer_id == customer_id)

        # 优先级筛选
        if priority:
            query = query.filter(SalesOpportunity.priority == priority)

        # 日期范围
        if start_date:
            query = query.filter(SalesOpportunity.created_at >= start_date)
        if end_date:
            query = query.filter(SalesOpportunity.created_at <= end_date + ' 23:59:59')

        # 排序: 优先级高的在前，然后按预计成交日期
        query = query.order_by(
            SalesOpportunity.updated_at.desc()
        )

        # 分页
        total = query.count()
        opportunities = query.offset((page - 1) * page_size).limit(page_size).all()

        return jsonify({
            "opportunities": [o.to_dict() for o in opportunities],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@opportunities_bp.route('/<int:id>', methods=['GET'])
def get_opportunity(id):
    """获取单个销售机会详情"""
    try:
        opportunity = SalesOpportunity.query.get(id)
        if not opportunity:
            return jsonify({"error": "机会不存在"}), 404

        # 获取阶段历史
        stage_history = OpportunityStageHistory.query.filter_by(
            opportunity_id=id
        ).order_by(OpportunityStageHistory.created_at.desc()).all()

        # 获取相关跟进记录
        follow_ups = FollowUpRecord.query.filter_by(
            opportunity_id=id
        ).order_by(FollowUpRecord.follow_up_date.desc()).limit(10).all()

        data = opportunity.to_dict()
        data["stage_history"] = [h.to_dict() for h in stage_history]
        data["recent_follow_ups"] = [f.to_dict() for f in follow_ups]

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@opportunities_bp.route('', methods=['POST'])
def create_opportunity():
    """创建销售机会"""
    try:
        data = request.get_json()

        # 必填验证
        if not data.get('name'):
            return jsonify({"error": "机会名称不能为空"}), 400
        if not data.get('customer_id'):
            return jsonify({"error": "客户不能为空"}), 400

        # 获取客户信息
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return jsonify({"error": "客户不存在"}), 404

        # 生成机会编号
        opportunity_no = SalesOpportunity.generate_opportunity_no()

        # 获取阶段对应的默认概率
        stage = data.get('stage', OpportunityStage.LEAD.value)
        probability = data.get('probability') or STAGE_PROBABILITY_MAP.get(stage, 10)

        opportunity = SalesOpportunity(
            opportunity_no=opportunity_no,
            name=data['name'],
            customer_id=data['customer_id'],
            customer_name=customer.short_name or customer.name,
            stage=stage,
            expected_amount=data.get('expected_amount', 0),
            currency=data.get('currency', 'CNY'),
            probability=probability,
            expected_close_date=datetime.strptime(data['expected_close_date'], '%Y-%m-%d').date() if data.get('expected_close_date') else None,
            owner_id=data.get('owner_id'),
            owner_name=data.get('owner_name'),
            priority=data.get('priority', 'medium'),
            source=data.get('source'),
            product_interest=data.get('product_interest'),
            competitors=data.get('competitors'),
            description=data.get('description'),
            next_follow_up_date=datetime.strptime(data['next_follow_up_date'], '%Y-%m-%d').date() if data.get('next_follow_up_date') else None,
            next_follow_up_note=data.get('next_follow_up_note'),
            created_by=data.get('created_by'),
        )

        # 计算加权金额
        opportunity.update_weighted_amount()

        db.session.add(opportunity)

        # 记录初始阶段
        history = OpportunityStageHistory(
            opportunity_id=opportunity.id,
            from_stage=None,
            to_stage=stage,
            changed_by=data.get('created_by'),
            changed_by_name=data.get('owner_name'),
            change_reason="创建机会"
        )
        db.session.add(history)

        db.session.commit()

        return jsonify(opportunity.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@opportunities_bp.route('/<int:id>', methods=['PUT'])
def update_opportunity(id):
    """更新销售机会"""
    try:
        opportunity = SalesOpportunity.query.get(id)
        if not opportunity:
            return jsonify({"error": "机会不存在"}), 404

        data = request.get_json()

        # 更新基本信息
        for field in ['name', 'priority', 'source', 'product_interest',
                      'competitors', 'description', 'currency',
                      'next_follow_up_note', 'owner_id', 'owner_name']:
            if field in data:
                setattr(opportunity, field, data[field])

        # 更新金额和概率
        if 'expected_amount' in data:
            opportunity.expected_amount = data['expected_amount']
        if 'probability' in data:
            opportunity.probability = data['probability']

        # 更新日期
        if 'expected_close_date' in data:
            opportunity.expected_close_date = datetime.strptime(data['expected_close_date'], '%Y-%m-%d').date() if data['expected_close_date'] else None
        if 'next_follow_up_date' in data:
            opportunity.next_follow_up_date = datetime.strptime(data['next_follow_up_date'], '%Y-%m-%d').date() if data['next_follow_up_date'] else None

        # 更新客户（如果变更）
        if 'customer_id' in data and data['customer_id'] != opportunity.customer_id:
            customer = Customer.query.get(data['customer_id'])
            if customer:
                opportunity.customer_id = customer.id
                opportunity.customer_name = customer.short_name or customer.name

        # 计算加权金额
        opportunity.update_weighted_amount()

        db.session.commit()

        return jsonify(opportunity.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@opportunities_bp.route('/<int:id>/stage', methods=['PUT'])
def update_stage(id):
    """更新销售阶段（阶段推进）"""
    try:
        opportunity = SalesOpportunity.query.get(id)
        if not opportunity:
            return jsonify({"error": "机会不存在"}), 404

        data = request.get_json()
        new_stage = data.get('stage')

        if not new_stage:
            return jsonify({"error": "阶段不能为空"}), 400

        old_stage = opportunity.stage

        if old_stage == new_stage:
            return jsonify({"error": "阶段未发生变化"}), 400

        # 更新阶段
        opportunity.stage = new_stage

        # 根据阶段更新概率
        if new_stage in STAGE_PROBABILITY_MAP:
            opportunity.probability = STAGE_PROBABILITY_MAP[new_stage]

        # 如果是成交或丢单，记录实际日期
        if new_stage == OpportunityStage.CLOSED_WON.value:
            opportunity.actual_close_date = date.today()
            opportunity.win_reason = data.get('reason')
        elif new_stage == OpportunityStage.CLOSED_LOST.value:
            opportunity.actual_close_date = date.today()
            opportunity.loss_reason = data.get('reason')

        # 更新加权金额
        opportunity.update_weighted_amount()

        # 记录阶段变更历史
        history = OpportunityStageHistory(
            opportunity_id=id,
            from_stage=old_stage,
            to_stage=new_stage,
            changed_by=data.get('changed_by'),
            changed_by_name=data.get('changed_by_name'),
            change_reason=data.get('reason')
        )
        db.session.add(history)

        db.session.commit()

        return jsonify(opportunity.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@opportunities_bp.route('/<int:id>', methods=['DELETE'])
def delete_opportunity(id):
    """删除销售机会"""
    try:
        opportunity = SalesOpportunity.query.get(id)
        if not opportunity:
            return jsonify({"error": "机会不存在"}), 404

        # 删除相关的阶段历史
        OpportunityStageHistory.query.filter_by(opportunity_id=id).delete()

        # 解除关联的跟进记录
        FollowUpRecord.query.filter_by(opportunity_id=id).update({'opportunity_id': None})

        db.session.delete(opportunity)
        db.session.commit()

        return jsonify({"message": "删除成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@opportunities_bp.route('/pipeline', methods=['GET'])
def get_pipeline():
    """获取销售漏斗数据"""
    try:
        owner_id = request.args.get('owner_id', type=int)

        query = SalesOpportunity.query.filter(
            ~SalesOpportunity.stage.in_([
                OpportunityStage.CLOSED_WON.value,
                OpportunityStage.CLOSED_LOST.value
            ])
        )

        if owner_id:
            query = query.filter(SalesOpportunity.owner_id == owner_id)

        # 按阶段分组统计
        stages_data = []
        for stage in [OpportunityStage.LEAD, OpportunityStage.QUALIFIED,
                      OpportunityStage.PROPOSAL, OpportunityStage.NEGOTIATION]:
            stage_query = query.filter(SalesOpportunity.stage == stage.value)
            count = stage_query.count()
            total_amount = db.session.query(
                func.coalesce(func.sum(SalesOpportunity.expected_amount), 0)
            ).filter(
                SalesOpportunity.stage == stage.value,
                ~SalesOpportunity.stage.in_([
                    OpportunityStage.CLOSED_WON.value,
                    OpportunityStage.CLOSED_LOST.value
                ])
            )
            if owner_id:
                total_amount = total_amount.filter(SalesOpportunity.owner_id == owner_id)
            total_amount = total_amount.scalar() or 0

            # 获取该阶段的机会列表
            opportunities = stage_query.order_by(
                SalesOpportunity.expected_amount.desc()
            ).limit(20).all()

            stages_data.append({
                "stage": stage.value,
                "stage_name": STAGE_NAME_MAP.get(stage.value, stage.value),
                "count": count,
                "total_amount": float(total_amount),
                "probability": STAGE_PROBABILITY_MAP.get(stage.value, 0),
                "opportunities": [o.to_dict() for o in opportunities]
            })

        return jsonify({
            "pipeline": stages_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@opportunities_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """获取销售统计数据"""
    try:
        owner_id = request.args.get('owner_id', type=int)
        year = request.args.get('year', type=int) or datetime.now().year
        month = request.args.get('month', type=int)

        # 基础查询
        base_query = SalesOpportunity.query

        if owner_id:
            base_query = base_query.filter(SalesOpportunity.owner_id == owner_id)

        # 时间筛选
        if year and month:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            base_query = base_query.filter(
                SalesOpportunity.created_at >= start_date,
                SalesOpportunity.created_at < end_date
            )
        elif year:
            base_query = base_query.filter(
                func.year(SalesOpportunity.created_at) == year
            )

        # 统计数据
        total_count = base_query.count()
        total_amount = base_query.with_entities(
            func.coalesce(func.sum(SalesOpportunity.expected_amount), 0)
        ).scalar() or 0

        # 成交统计
        won_query = base_query.filter(SalesOpportunity.stage == OpportunityStage.CLOSED_WON.value)
        won_count = won_query.count()
        won_amount = won_query.with_entities(
            func.coalesce(func.sum(SalesOpportunity.expected_amount), 0)
        ).scalar() or 0

        # 丢单统计
        lost_query = base_query.filter(SalesOpportunity.stage == OpportunityStage.CLOSED_LOST.value)
        lost_count = lost_query.count()

        # 进行中统计
        active_query = base_query.filter(
            ~SalesOpportunity.stage.in_([
                OpportunityStage.CLOSED_WON.value,
                OpportunityStage.CLOSED_LOST.value
            ])
        )
        active_count = active_query.count()
        active_amount = active_query.with_entities(
            func.coalesce(func.sum(SalesOpportunity.expected_amount), 0)
        ).scalar() or 0
        weighted_amount = active_query.with_entities(
            func.coalesce(func.sum(SalesOpportunity.weighted_amount), 0)
        ).scalar() or 0

        # 赢单率
        closed_count = won_count + lost_count
        win_rate = (won_count / closed_count * 100) if closed_count > 0 else 0

        return jsonify({
            "total_count": total_count,
            "total_amount": float(total_amount),
            "won_count": won_count,
            "won_amount": float(won_amount),
            "lost_count": lost_count,
            "active_count": active_count,
            "active_amount": float(active_amount),
            "weighted_amount": float(weighted_amount),
            "win_rate": round(win_rate, 1),
            "year": year,
            "month": month,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@opportunities_bp.route('/stages', methods=['GET'])
def get_stages():
    """获取所有阶段定义"""
    return jsonify({
        "stages": [
            {"value": s.value, "label": STAGE_NAME_MAP.get(s.value), "probability": STAGE_PROBABILITY_MAP.get(s.value)}
            for s in OpportunityStage
        ],
        "priorities": [
            {"value": k, "label": v} for k, v in PRIORITY_NAME_MAP.items()
        ]
    })
