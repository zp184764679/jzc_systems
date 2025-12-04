# routes/pr/create.py
# 创建采购申请（PR）相关接口

from flask import Blueprint, request, jsonify
from datetime import datetime
from models.pr import PR
from models.pr_item import PRItem
from extensions import db
import traceback
from .common import _normalize_urgency_input, zh_status, zh_urgency

bp = Blueprint('pr_create', __name__)

@bp.route('/prs', methods=['POST', 'OPTIONS'])
def create_pr():
    """
    创建采购请求（PR）
    
    请求格式：
    {
        "title": "标题",
        "description": "描述",
        "urgency": "high|medium|low|normal|高|中|低",
        "owner_id": 1,
        "applicant_name": "申请人名称",
        "applicant_dept": "申请人部门",
        "items": [
            {"name":"物料名称","spec":"规格","qty":10,"unit":"个","remark":"备注"}
        ]
    }
    """
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, User-ID, User-Role")
        response.headers.add("Access-Control-Max-Age", "3600")
        return response, 204
    
    try:
        data = request.json or {}

        # 必填校验
        if not data.get("title"):
            return jsonify({"error": "标题不能为空"}), 400
        if not data.get("owner_id"):
            return jsonify({"error": "必须指定申请人"}), 400

        # 生成 PR 编号
        pr_number = PR.generate_pr_number()

        # 归一化紧急程度（入库用英文）
        urgency_norm = _normalize_urgency_input(data.get("urgency"))

        # 创建 PR（状态入库仍用英文）
        pr = PR(
            pr_number=pr_number,
            title=data.get("title"),
            description=data.get("description", ""),
            urgency=urgency_norm,
            owner_id=data.get("owner_id"),
            status="submitted",
            created_at=datetime.utcnow()
        )
        db.session.add(pr)
        db.session.flush()  # 获取 pr.id

        # 处理 PR 项
        items = data.get("items", [])
        if not items:
            return jsonify({"error": "至少需要一个物料项"}), 400

        for it in items:
            if not it.get("name"):
                continue
            pr_item = PRItem(
                name=it["name"],
                spec=it.get("spec", ""),
                qty=it.get("qty", 1),
                unit=it.get("unit", "个"),
                remark=it.get("remark", ""),
                pr_id=pr.id,
                status="pending"
            )
            db.session.add(pr_item)

        db.session.commit()

        # 发送企业微信通知给审批人（所有super_admin，除申请人外）
        try:
            from utils.auth import get_all_approvers
            from services.notification_service import NotificationService

            # 从统一数据源(account.users)查询所有审批人
            approvers = get_all_approvers(exclude_user_id=pr.owner_id)

            # 通知每个审批人
            for approver in approvers:
                try:
                    NotificationService.notify_pr_pending_approval(pr, approver.id)
                    print(f"✅ 已通知审批人 {approver.username} - PR#{pr.id}")
                except Exception as e:
                    print(f"⚠️  通知审批人 {approver.username} 失败: {e}")
        except Exception as e:
            print(f"⚠️  发送PR审批通知失败: {e}")
            # 不影响主流程，继续返回成功

        # 返回时中文化
        return jsonify({
            "id": pr.id,
            "prNumber": pr.pr_number,
            "message": "采购申请创建成功",
            "status": zh_status(pr.status),
            "urgency": zh_urgency(pr.urgency),
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"创建PR错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"创建失败: {str(e)}"}), 500