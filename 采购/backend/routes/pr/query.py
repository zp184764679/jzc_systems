# routes/pr/query.py
# 查询采购申请相关接口

from flask import Blueprint, request, jsonify
from models.pr import PR
from models.rfq import RFQ
from extensions import db
import traceback
from .common import zh_status, zh_urgency, iso, get_owner_info

bp = Blueprint('pr_query', __name__)

@bp.route('/requests', methods=['GET', 'OPTIONS'])
def get_requests():
    """
    获取所有物料申请，可根据状态和用户筛选
    参数：
    - status: 状态筛选 (submitted/approved/rejected/draft)
    - user_id: 用户ID筛选
    """
    if request.method == 'OPTIONS':
        return "", 204
    
    try:
        status = request.args.get('status')
        user_id = request.args.get('user_id')
        current_user_id = request.headers.get('User-ID')
        current_user_role = request.headers.get('User-Role')

        query = PR.query
        
        # 普通员工（user）只能查看自己的 PR
        if current_user_role == 'user' and current_user_id:
            query = query.filter_by(owner_id=int(current_user_id))
        elif user_id:
            query = query.filter_by(owner_id=int(user_id))
        
        if status:
            query = query.filter_by(status=status)

        all_requests = query.order_by(PR.created_at.desc()).all()

        result = []
        for r in all_requests:
            approved_qty = sum(item.qty for item in r.items if item.status == "approved")
            pending_qty = sum(item.qty for item in r.items if item.status == "pending")
            owner = get_owner_info(r.owner_id)
            result.append({
                "id": r.id,
                "prNumber": r.pr_number,
                "title": r.title,
                "description": r.description,
                "approvedQty": approved_qty,
                "pendingQty": pending_qty,
                "status": zh_status(r.status),
                "status_code": r.status,
                "urgency": zh_urgency(r.urgency),
                "urgency_code": r.urgency,
                "created_at": iso(r.created_at),
                "owner_id": r.owner_id,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "total_amount": float(r.total_amount) if r.total_amount else None,
            })
        return jsonify(result), 200

    except Exception as e:
        print(f"获取申请列表错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500

@bp.route('/mine', methods=['GET', 'OPTIONS'])
def get_my_requests():
    """获取当前用户发起的物料申请；参数：user_id"""
    if request.method == 'OPTIONS':
        return "", 204
    
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "缺少用户ID"}), 400

        my_requests = PR.query.filter_by(owner_id=int(user_id)).order_by(PR.created_at.desc()).all()

        result = []
        for r in my_requests:
            owner = get_owner_info(r.owner_id)
            result.append({
                "id": r.id,
                "prNumber": r.pr_number,
                "title": r.title,
                "status": zh_status(r.status),
                "status_code": r.status,
                "urgency": zh_urgency(r.urgency),
                "urgency_code": r.urgency,
                "created_at": iso(r.created_at),
                "owner_id": r.owner_id,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "items": [{"name": it.name, "qty": it.qty, "unit": it.unit} for it in r.items]
            })
        return jsonify(result), 200

    except Exception as e:
        print(f"获取我的申请列表错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500

@bp.route('/todo', methods=['GET', 'OPTIONS'])
def get_todo_requests():
    """获取待审批的物料申请（状态为 submitted 的物料申请）"""
    if request.method == 'OPTIONS':
        return "", 204
    
    try:
        todo_requests = PR.query.filter_by(status="submitted").order_by(PR.created_at.desc()).all()

        result = []
        for r in todo_requests:
            owner = get_owner_info(r.owner_id)
            result.append({
                "id": r.id,
                "prNumber": r.pr_number,
                "title": r.title,
                "status": zh_status(r.status),
                "status_code": r.status,
                "urgency": zh_urgency(r.urgency),
                "urgency_code": r.urgency,
                "created_at": iso(r.created_at),
                "owner_id": r.owner_id,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "items": [{"name": it.name, "qty": it.qty, "unit": it.unit} for it in r.items]
            })
        return jsonify(result), 200

    except Exception as e:
        print(f"获取待审批列表错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500

@bp.route('/requests/<int:id>', methods=['GET', 'OPTIONS'])
def get_detail(id):
    """获取单个申请详情"""
    if request.method == 'OPTIONS':
        return "", 204
    
    try:
        pr = PR.query.get(id)
        if not pr:
            return jsonify({"error": "申请不存在"}), 404

        owner = get_owner_info(pr.owner_id)
        return jsonify({
            "id": pr.id,
            "prNumber": pr.pr_number,
            "title": pr.title,
            "description": pr.description,
            "status": zh_status(pr.status),
            "status_code": pr.status,
            "urgency": zh_urgency(pr.urgency),
            "urgency_code": pr.urgency,
            "created_at": iso(pr.created_at),
            "updated_at": iso(getattr(pr, 'updated_at', None)),
            "owner_id": pr.owner_id,
            "owner_name": owner["full_name"] if owner else None,
            "owner_department": owner["department"] if owner else None,
            "reject_reason": getattr(pr, 'reject_reason', None),
            "total_amount": float(pr.total_amount) if pr.total_amount else None,
            "needs_super_admin": getattr(pr, 'needs_super_admin', False),
            "auto_approve_reason": getattr(pr, 'auto_approve_reason', None),
            "items": [{
                "id": item.id,
                "name": item.name,
                "spec": item.spec,
                "qty": item.qty,
                "unit": item.unit,
                "remark": item.remark,
                "unit_price": float(item.unit_price) if item.unit_price else None,
                "total_price": float(item.total_price) if item.total_price else None,
                "status": zh_status(item.status),
                "status_code": item.status,
                "classification": getattr(item, 'classification', None),
                "reject_reason": getattr(item, 'reject_reason', None)
            } for item in pr.items]
        }), 200

    except Exception as e:
        print(f"获取申请详情错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500

@bp.route('/need-price', methods=['GET', 'OPTIONS'])
def get_need_price():
    """
    获取需要填写价格的PR列表（状态为 supervisor_approved）
    用于主管填写价格界面

    权限控制（新流程）：
    - 普通员工(user): 不能填写价格，只能看到自己的PR（仅查看）
    - 主管(supervisor): 可以看到所有待填价的PR并填写价格
    - 厂长(factory_manager)/管理员(admin): 可以看到所有PR
    - 总经理(general_manager)/超管(super_admin): 可以看到所有PR

    新审批流程：
    1. 员工提交 → 主管审批 → 主管填写价格 → 厂长审批 → [总经理审批] → 完成
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        current_user_id = getattr(request, 'current_user_id', None) or request.headers.get('User-ID')
        current_user_role = getattr(request, 'current_user_role', None) or request.headers.get('User-Role')

        # 转换 user_id 为整数
        try:
            current_user_id = int(current_user_id) if current_user_id else None
        except (ValueError, TypeError):
            current_user_id = None

        query = PR.query.filter_by(status="supervisor_approved")

        # 定义可以填写价格的角色（主管及以上）
        can_fill_price_roles = ['supervisor', 'factory_manager', 'admin', 'general_manager', 'super_admin']

        # 普通员工只能看到自己的PR（仅查看，不能填写）
        if current_user_role not in can_fill_price_roles:
            if current_user_id:
                query = query.filter_by(owner_id=current_user_id)
            else:
                # 没有用户ID，返回空列表
                return jsonify({"data": [], "total": 0, "can_view_all": False, "can_fill_price": False}), 200

        prs = query.order_by(PR.created_at.desc()).all()

        result = []
        for pr in prs:
            owner = get_owner_info(pr.owner_id)
            is_own = (pr.owner_id == current_user_id) if current_user_id else False
            result.append({
                "id": pr.id,
                "prNumber": pr.pr_number,
                "title": pr.title,
                "urgency": zh_urgency(pr.urgency),
                "urgency_code": pr.urgency,
                "owner_id": pr.owner_id,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "is_own": is_own,
                "items_count": len(pr.items),
                "created_at": iso(pr.created_at),
                "supervisor_approved_at": iso(pr.supervisor_approved_at) if pr.supervisor_approved_at else None,
                "items": [{
                    "id": item.id,
                    "name": item.name,
                    "spec": item.spec,
                    "qty": item.qty,
                    "unit": item.unit,
                    "unit_price": float(item.unit_price) if item.unit_price else None,
                } for item in pr.items]
            })

        can_view_all = current_user_role in can_fill_price_roles
        can_fill_price = current_user_role in can_fill_price_roles
        return jsonify({
            "data": result,
            "total": len(result),
            "can_view_all": can_view_all,
            "can_fill_price": can_fill_price,
            "current_user_id": current_user_id,
            "current_user_role": current_user_role
        }), 200

    except Exception as e:
        print(f"获取待填价列表错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


@bp.route('/price-history', methods=['GET', 'OPTIONS'])
def get_price_history():
    """
    获取填价历史记录 - 包括已填价、待填价、已审批等所有相关状态的PR
    支持多种筛选条件用于溯源查找

    参数：
    - status: 状态筛选 (all/need_price/price_filled/approved/rejected)
    - search: 搜索关键词（单号、标题、物料名称）
    - owner_id: 申请人ID
    - department: 部门筛选
    - urgency: 紧急程度
    - date_from: 开始日期
    - date_to: 结束日期
    - has_price: 是否已填价 (true/false)
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        from datetime import datetime, timedelta

        current_user_id = getattr(request, 'current_user_id', None) or request.headers.get('User-ID')
        current_user_role = getattr(request, 'current_user_role', None) or request.headers.get('User-Role')

        try:
            current_user_id = int(current_user_id) if current_user_id else None
        except (ValueError, TypeError):
            current_user_id = None

        # 获取筛选参数
        status_filter = request.args.get('status', 'all')
        search = request.args.get('search', '').strip()
        owner_filter = request.args.get('owner_id')
        department_filter = request.args.get('department')
        urgency_filter = request.args.get('urgency')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        has_price = request.args.get('has_price')

        # 定义与填价相关的状态
        price_related_statuses = [
            'supervisor_approved',  # 待填价
            'price_filled',         # 已填价待审批
            'pending_super_admin',  # 待超管审批
            'approved',             # 已批准
            'rejected',             # 已拒绝
        ]

        query = PR.query.filter(PR.status.in_(price_related_statuses))

        # 权限控制
        high_permission_roles = ['supervisor', 'admin', 'super_admin']
        if current_user_role not in high_permission_roles:
            if current_user_id:
                query = query.filter_by(owner_id=current_user_id)
            else:
                return jsonify({"data": [], "total": 0}), 200

        # 状态筛选
        if status_filter == 'need_price':
            query = query.filter_by(status='supervisor_approved')
        elif status_filter == 'price_filled':
            query = query.filter_by(status='price_filled')
        elif status_filter == 'approved':
            query = query.filter_by(status='approved')
        elif status_filter == 'rejected':
            query = query.filter_by(status='rejected')
        elif status_filter == 'pending':
            query = query.filter(PR.status.in_(['price_filled', 'pending_super_admin']))

        # 日期筛选
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(PR.created_at >= from_date)
            except ValueError:
                pass
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(PR.created_at < to_date)
            except ValueError:
                pass

        # 紧急程度筛选
        if urgency_filter and urgency_filter != 'all':
            query = query.filter_by(urgency=urgency_filter)

        # 申请人筛选
        if owner_filter:
            try:
                query = query.filter_by(owner_id=int(owner_filter))
            except ValueError:
                pass

        prs = query.order_by(PR.created_at.desc()).all()

        # 获取所有部门列表用于前端筛选
        all_departments = set()

        result = []
        for pr in prs:
            owner = get_owner_info(pr.owner_id)
            if owner and owner.get("department"):
                all_departments.add(owner["department"])

            # 部门筛选（在内存中进行）
            if department_filter and owner and owner.get("department") != department_filter:
                continue

            # 搜索过滤
            if search:
                search_lower = search.lower()
                match = False
                if pr.pr_number and search_lower in pr.pr_number.lower():
                    match = True
                elif pr.title and search_lower in pr.title.lower():
                    match = True
                elif owner and owner.get("full_name") and search_lower in owner["full_name"].lower():
                    match = True
                else:
                    for item in pr.items:
                        if item.name and search_lower in item.name.lower():
                            match = True
                            break
                        if item.spec and search_lower in item.spec.lower():
                            match = True
                            break
                if not match:
                    continue

            # 是否已填价筛选
            items_with_price = sum(1 for item in pr.items if item.unit_price and item.unit_price > 0)
            all_priced = items_with_price == len(pr.items) and len(pr.items) > 0

            if has_price == 'true' and not all_priced:
                continue
            if has_price == 'false' and all_priced:
                continue

            is_own = (pr.owner_id == current_user_id) if current_user_id else False

            # 状态中文映射
            status_text_map = {
                'supervisor_approved': '待填价',
                'price_filled': '已填价待审批',
                'pending_super_admin': '待超管审批',
                'approved': '已批准',
                'rejected': '已拒绝',
            }

            result.append({
                "id": pr.id,
                "prNumber": pr.pr_number,
                "title": pr.title,
                "status": status_text_map.get(pr.status, pr.status),
                "status_code": pr.status,
                "urgency": zh_urgency(pr.urgency),
                "urgency_code": pr.urgency,
                "owner_id": pr.owner_id,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "is_own": is_own,
                "items_count": len(pr.items),
                "items_with_price": items_with_price,
                "total_amount": float(pr.total_amount) if pr.total_amount else None,
                "created_at": iso(pr.created_at),
                "updated_at": iso(pr.updated_at) if hasattr(pr, 'updated_at') and pr.updated_at else None,
                "supervisor_approved_at": iso(pr.supervisor_approved_at) if pr.supervisor_approved_at else None,
                "price_filled_at": iso(pr.price_filled_at) if hasattr(pr, 'price_filled_at') and pr.price_filled_at else None,
                "items": [{
                    "id": item.id,
                    "name": item.name,
                    "spec": item.spec,
                    "qty": item.qty,
                    "unit": item.unit,
                    "unit_price": float(item.unit_price) if item.unit_price else None,
                    "total_price": float(item.total_price) if item.total_price else None,
                } for item in pr.items]
            })

        can_view_all = current_user_role in high_permission_roles
        return jsonify({
            "data": result,
            "total": len(result),
            "can_view_all": can_view_all,
            "departments": sorted(list(all_departments)),
        }), 200

    except Exception as e:
        print(f"获取填价历史错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


@bp.route('/need-admin-approve', methods=['GET', 'OPTIONS'])
def get_need_admin_approve():
    """
    获取需要管理员审批的PR列表（状态为 price_filled）
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        prs = PR.query.filter_by(status="price_filled").order_by(PR.created_at.desc()).all()

        result = []
        for pr in prs:
            owner = get_owner_info(pr.owner_id)
            result.append({
                "id": pr.id,
                "prNumber": pr.pr_number,
                "title": pr.title,
                "total_amount": float(pr.total_amount) if pr.total_amount else 0,
                "urgency": zh_urgency(pr.urgency),
                "urgency_code": pr.urgency,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "items_count": len(pr.items),
                "created_at": iso(pr.created_at),
            })
        return jsonify(result), 200

    except Exception as e:
        print(f"获取待管理员审批列表错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


@bp.route('/need-super-admin-approve', methods=['GET', 'OPTIONS'])
def get_need_super_admin_approve():
    """
    获取需要超管审批的PR列表（状态为 pending_super_admin）
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        prs = PR.query.filter_by(status="pending_super_admin").order_by(PR.created_at.desc()).all()

        result = []
        for pr in prs:
            owner = get_owner_info(pr.owner_id)
            result.append({
                "id": pr.id,
                "prNumber": pr.pr_number,
                "title": pr.title,
                "total_amount": float(pr.total_amount) if pr.total_amount else 0,
                "needs_super_admin": pr.needs_super_admin,
                "urgency": zh_urgency(pr.urgency),
                "urgency_code": pr.urgency,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "items_count": len(pr.items),
                "created_at": iso(pr.created_at),
            })
        return jsonify(result), 200

    except Exception as e:
        print(f"获取待超管审批列表错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


@bp.route('/approval-history', methods=['GET', 'OPTIONS'])
def get_approval_history():
    """
    获取审批历史记录 - 管理员审批中心使用
    包括已审批、待审批、已驳回等所有相关状态的PR
    支持多种筛选条件用于溯源查找

    参数：
    - status: 状态筛选 (all/price_filled/pending_super_admin/approved/rejected)
    - search: 搜索关键词（单号、标题、物料名称）
    - owner_id: 申请人ID
    - department: 部门筛选
    - urgency: 紧急程度
    - date_from: 开始日期
    - date_to: 结束日期
    - amount_min: 最小金额
    - amount_max: 最大金额
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        from datetime import datetime, timedelta

        # 获取筛选参数
        status_filter = request.args.get('status', 'all')
        search = request.args.get('search', '').strip()
        owner_filter = request.args.get('owner_id')
        department_filter = request.args.get('department')
        urgency_filter = request.args.get('urgency')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        amount_min = request.args.get('amount_min')
        amount_max = request.args.get('amount_max')

        # 定义审批相关的状态
        approval_related_statuses = [
            'price_filled',         # 待管理员审批
            'pending_super_admin',  # 待超管审批
            'approved',             # 已批准
            'rejected',             # 已拒绝
        ]

        query = PR.query.filter(PR.status.in_(approval_related_statuses))

        # 状态筛选
        if status_filter == 'price_filled':
            query = query.filter_by(status='price_filled')
        elif status_filter == 'pending_super_admin':
            query = query.filter_by(status='pending_super_admin')
        elif status_filter == 'approved':
            query = query.filter_by(status='approved')
        elif status_filter == 'rejected':
            query = query.filter_by(status='rejected')
        elif status_filter == 'pending':
            query = query.filter(PR.status.in_(['price_filled', 'pending_super_admin']))

        # 日期筛选
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(PR.created_at >= from_date)
            except ValueError:
                pass
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(PR.created_at < to_date)
            except ValueError:
                pass

        # 紧急程度筛选
        if urgency_filter and urgency_filter != 'all':
            query = query.filter_by(urgency=urgency_filter)

        # 申请人筛选
        if owner_filter:
            try:
                query = query.filter_by(owner_id=int(owner_filter))
            except ValueError:
                pass

        # 金额筛选
        if amount_min:
            try:
                query = query.filter(PR.total_amount >= float(amount_min))
            except ValueError:
                pass
        if amount_max:
            try:
                query = query.filter(PR.total_amount <= float(amount_max))
            except ValueError:
                pass

        prs = query.order_by(PR.created_at.desc()).all()

        # 获取所有部门和申请人列表用于前端筛选
        all_departments = set()
        all_owners = {}

        result = []
        for pr in prs:
            owner = get_owner_info(pr.owner_id)
            if owner:
                if owner.get("department"):
                    all_departments.add(owner["department"])
                all_owners[pr.owner_id] = owner["full_name"]

            # 部门筛选（在内存中进行）
            if department_filter and owner and owner.get("department") != department_filter:
                continue

            # 搜索过滤
            if search:
                search_lower = search.lower()
                match = False
                if pr.pr_number and search_lower in pr.pr_number.lower():
                    match = True
                elif pr.title and search_lower in pr.title.lower():
                    match = True
                elif owner and owner.get("full_name") and search_lower in owner["full_name"].lower():
                    match = True
                else:
                    for item in pr.items:
                        if item.name and search_lower in item.name.lower():
                            match = True
                            break
                        if item.spec and search_lower in item.spec.lower():
                            match = True
                            break
                if not match:
                    continue

            # 状态中文映射
            status_text_map = {
                'price_filled': '待管理员审批',
                'pending_super_admin': '待超管审批',
                'approved': '已批准',
                'rejected': '已拒绝',
            }

            result.append({
                "id": pr.id,
                "prNumber": pr.pr_number,
                "title": pr.title,
                "status": status_text_map.get(pr.status, pr.status),
                "status_code": pr.status,
                "urgency": zh_urgency(pr.urgency),
                "urgency_code": pr.urgency,
                "owner_id": pr.owner_id,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "items_count": len(pr.items),
                "total_amount": float(pr.total_amount) if pr.total_amount else 0,
                "reject_reason": pr.reject_reason if hasattr(pr, 'reject_reason') else None,
                "needs_super_admin": pr.needs_super_admin if hasattr(pr, 'needs_super_admin') else False,
                "created_at": iso(pr.created_at),
                "updated_at": iso(pr.updated_at) if hasattr(pr, 'updated_at') and pr.updated_at else None,
                "items": [{
                    "id": item.id,
                    "name": item.name,
                    "spec": item.spec,
                    "qty": item.qty,
                    "unit": item.unit,
                    "unit_price": float(item.unit_price) if item.unit_price else None,
                    "total_price": float(item.total_price) if item.total_price else None,
                } for item in pr.items]
            })

        # 统计信息
        stats = {
            "price_filled": sum(1 for r in result if r["status_code"] == "price_filled"),
            "pending_super_admin": sum(1 for r in result if r["status_code"] == "pending_super_admin"),
            "approved": sum(1 for r in result if r["status_code"] == "approved"),
            "rejected": sum(1 for r in result if r["status_code"] == "rejected"),
        }

        return jsonify({
            "data": result,
            "total": len(result),
            "stats": stats,
            "departments": sorted(list(all_departments)),
            "owners": [{"id": k, "name": v} for k, v in all_owners.items()],
        }), 200

    except Exception as e:
        print(f"获取审批历史错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500


@bp.route('/approved-not-sent', methods=['GET', 'OPTIONS'])
def get_approved_not_sent():
    """
    获取已批准但未发送RFQ的PR列表
    用于"发送采购单"界面

    排除条件：
    1. PR的状态必须是 "approved"
    2. PR没有关联的RFQ，或者
    3. PR关联的RFQ状态不是 "po_created"（已创建PO就不再显示）
    """
    if request.method == 'OPTIONS':
        return "", 204

    try:
        approved_prs = PR.query.filter_by(status="approved").order_by(PR.created_at.desc()).all()

        result = []
        for pr in approved_prs:
            # 检查该PR是否有关联的RFQ，且RFQ状态为 'po_created'
            # 如果已经创建了PO，就不再显示在待发送列表中
            has_po_created_rfq = RFQ.query.filter_by(
                pr_id=pr.id,
                status='po_created'
            ).first()

            # 如果已经有PO创建的RFQ，跳过这个PR
            if has_po_created_rfq:
                continue

            owner = get_owner_info(pr.owner_id)
            result.append({
                "id": pr.id,
                "prNumber": pr.pr_number,
                "title": pr.title,
                "urgency": zh_urgency(pr.urgency),
                "urgency_code": pr.urgency,
                "owner_name": owner["full_name"] if owner else None,
                "owner_department": owner["department"] if owner else None,
                "items_count": len(pr.items),
                "created_at": iso(pr.created_at),
            })
        return jsonify(result), 200

    except Exception as e:
        print(f"获取已批准未发送列表错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500