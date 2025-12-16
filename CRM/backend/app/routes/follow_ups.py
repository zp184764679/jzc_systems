# -*- coding: utf-8 -*-
"""
客户跟进记录 API
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy import func, or_

from .. import db
from ..models import (
    Customer, SalesOpportunity, FollowUpRecord,
    FollowUpType, FOLLOW_UP_TYPE_MAP
)

follow_ups_bp = Blueprint('follow_ups', __name__, url_prefix='/api/follow-ups')


@follow_ups_bp.route('', methods=['GET'])
def get_follow_ups():
    """获取跟进记录列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        customer_id = request.args.get('customer_id', type=int)
        opportunity_id = request.args.get('opportunity_id', type=int)
        owner_id = request.args.get('owner_id', type=int)
        follow_up_type = request.args.get('type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        keyword = request.args.get('keyword', '')

        query = FollowUpRecord.query

        # 客户筛选
        if customer_id:
            query = query.filter(FollowUpRecord.customer_id == customer_id)

        # 机会筛选
        if opportunity_id:
            query = query.filter(FollowUpRecord.opportunity_id == opportunity_id)

        # 负责人筛选
        if owner_id:
            query = query.filter(FollowUpRecord.owner_id == owner_id)

        # 类型筛选
        if follow_up_type:
            query = query.filter(FollowUpRecord.follow_up_type == follow_up_type)

        # 日期范围
        if start_date:
            query = query.filter(FollowUpRecord.follow_up_date >= start_date)
        if end_date:
            query = query.filter(FollowUpRecord.follow_up_date <= end_date + ' 23:59:59')

        # 关键字搜索
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    FollowUpRecord.subject.ilike(like),
                    FollowUpRecord.content.ilike(like),
                    FollowUpRecord.customer_name.ilike(like),
                    FollowUpRecord.contact_name.ilike(like),
                )
            )

        # 排序
        query = query.order_by(FollowUpRecord.follow_up_date.desc())

        # 分页
        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()

        return jsonify({
            "records": [r.to_dict() for r in records],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@follow_ups_bp.route('/<int:id>', methods=['GET'])
def get_follow_up(id):
    """获取单个跟进记录"""
    try:
        record = FollowUpRecord.query.get(id)
        if not record:
            return jsonify({"error": "记录不存在"}), 404

        return jsonify(record.to_dict())

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@follow_ups_bp.route('', methods=['POST'])
def create_follow_up():
    """创建跟进记录"""
    try:
        data = request.get_json()

        # 验证必填
        if not data.get('customer_id'):
            return jsonify({"error": "客户不能为空"}), 400
        if not data.get('content'):
            return jsonify({"error": "跟进内容不能为空"}), 400

        # 获取客户信息
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return jsonify({"error": "客户不存在"}), 404

        record = FollowUpRecord(
            customer_id=data['customer_id'],
            customer_name=customer.short_name or customer.name,
            opportunity_id=data.get('opportunity_id'),
            follow_up_type=data.get('follow_up_type', FollowUpType.PHONE.value),
            follow_up_date=datetime.strptime(data['follow_up_date'], '%Y-%m-%d %H:%M:%S') if data.get('follow_up_date') else datetime.now(),
            subject=data.get('subject'),
            content=data['content'],
            result=data.get('result'),
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            contact_role=data.get('contact_role'),
            next_follow_up_date=datetime.strptime(data['next_follow_up_date'], '%Y-%m-%d').date() if data.get('next_follow_up_date') else None,
            next_follow_up_note=data.get('next_follow_up_note'),
            owner_id=data.get('owner_id'),
            owner_name=data.get('owner_name'),
            attachments=data.get('attachments', []),
        )

        db.session.add(record)

        # 如果关联了机会，更新机会的下次跟进信息
        if data.get('opportunity_id') and data.get('next_follow_up_date'):
            opportunity = SalesOpportunity.query.get(data['opportunity_id'])
            if opportunity:
                opportunity.next_follow_up_date = record.next_follow_up_date
                opportunity.next_follow_up_note = record.next_follow_up_note

        db.session.commit()

        return jsonify(record.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@follow_ups_bp.route('/<int:id>', methods=['PUT'])
def update_follow_up(id):
    """更新跟进记录"""
    try:
        record = FollowUpRecord.query.get(id)
        if not record:
            return jsonify({"error": "记录不存在"}), 404

        data = request.get_json()

        # 更新字段
        for field in ['follow_up_type', 'subject', 'content', 'result',
                      'contact_name', 'contact_phone', 'contact_role',
                      'next_follow_up_note', 'owner_id', 'owner_name', 'attachments']:
            if field in data:
                setattr(record, field, data[field])

        if 'follow_up_date' in data:
            record.follow_up_date = datetime.strptime(data['follow_up_date'], '%Y-%m-%d %H:%M:%S') if data['follow_up_date'] else None

        if 'next_follow_up_date' in data:
            record.next_follow_up_date = datetime.strptime(data['next_follow_up_date'], '%Y-%m-%d').date() if data['next_follow_up_date'] else None

        db.session.commit()

        return jsonify(record.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@follow_ups_bp.route('/<int:id>', methods=['DELETE'])
def delete_follow_up(id):
    """删除跟进记录"""
    try:
        record = FollowUpRecord.query.get(id)
        if not record:
            return jsonify({"error": "记录不存在"}), 404

        db.session.delete(record)
        db.session.commit()

        return jsonify({"message": "删除成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@follow_ups_bp.route('/customer/<int:customer_id>/timeline', methods=['GET'])
def get_customer_timeline(customer_id):
    """获取客户的跟进时间线"""
    try:
        limit = request.args.get('limit', 50, type=int)

        records = FollowUpRecord.query.filter_by(
            customer_id=customer_id
        ).order_by(FollowUpRecord.follow_up_date.desc()).limit(limit).all()

        return jsonify({
            "customer_id": customer_id,
            "timeline": [r.to_dict() for r in records]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@follow_ups_bp.route('/pending', methods=['GET'])
def get_pending_follow_ups():
    """获取待跟进列表（下次跟进日期在今天之前的）"""
    try:
        owner_id = request.args.get('owner_id', type=int)
        days = request.args.get('days', 7, type=int)

        from datetime import date, timedelta
        end_date = date.today() + timedelta(days=days)

        query = FollowUpRecord.query.filter(
            FollowUpRecord.next_follow_up_date <= end_date,
            FollowUpRecord.next_follow_up_date.isnot(None)
        )

        if owner_id:
            query = query.filter(FollowUpRecord.owner_id == owner_id)

        records = query.order_by(FollowUpRecord.next_follow_up_date.asc()).all()

        # 按日期分组
        overdue = []
        today_list = []
        upcoming = []
        today = date.today()

        for r in records:
            if r.next_follow_up_date < today:
                overdue.append(r.to_dict())
            elif r.next_follow_up_date == today:
                today_list.append(r.to_dict())
            else:
                upcoming.append(r.to_dict())

        return jsonify({
            "overdue": overdue,
            "today": today_list,
            "upcoming": upcoming,
            "total": len(records)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@follow_ups_bp.route('/statistics', methods=['GET'])
def get_follow_up_statistics():
    """获取跟进统计"""
    try:
        owner_id = request.args.get('owner_id', type=int)
        year = request.args.get('year', type=int) or datetime.now().year
        month = request.args.get('month', type=int)

        from datetime import date

        # 基础查询
        base_query = FollowUpRecord.query

        if owner_id:
            base_query = base_query.filter(FollowUpRecord.owner_id == owner_id)

        # 时间筛选
        if year and month:
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)
            base_query = base_query.filter(
                FollowUpRecord.follow_up_date >= datetime.combine(start_date, datetime.min.time()),
                FollowUpRecord.follow_up_date < datetime.combine(end_date, datetime.min.time())
            )
        elif year:
            base_query = base_query.filter(
                func.year(FollowUpRecord.follow_up_date) == year
            )

        # 总数
        total_count = base_query.count()

        # 按类型统计
        type_stats = db.session.query(
            FollowUpRecord.follow_up_type,
            func.count(FollowUpRecord.id)
        ).group_by(FollowUpRecord.follow_up_type).all()

        type_distribution = {
            t: {"count": c, "label": FOLLOW_UP_TYPE_MAP.get(t, t)}
            for t, c in type_stats
        }

        # 按客户统计（前10）
        customer_stats = db.session.query(
            FollowUpRecord.customer_id,
            FollowUpRecord.customer_name,
            func.count(FollowUpRecord.id).label('count')
        )
        if owner_id:
            customer_stats = customer_stats.filter(FollowUpRecord.owner_id == owner_id)
        if year:
            customer_stats = customer_stats.filter(func.year(FollowUpRecord.follow_up_date) == year)

        customer_stats = customer_stats.group_by(
            FollowUpRecord.customer_id,
            FollowUpRecord.customer_name
        ).order_by(func.count(FollowUpRecord.id).desc()).limit(10).all()

        top_customers = [
            {"customer_id": c[0], "customer_name": c[1], "count": c[2]}
            for c in customer_stats
        ]

        return jsonify({
            "total_count": total_count,
            "type_distribution": type_distribution,
            "top_customers": top_customers,
            "year": year,
            "month": month,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@follow_ups_bp.route('/types', methods=['GET'])
def get_follow_up_types():
    """获取所有跟进类型"""
    return jsonify({
        "types": [
            {"value": t.value, "label": FOLLOW_UP_TYPE_MAP.get(t.value)}
            for t in FollowUpType
        ]
    })
