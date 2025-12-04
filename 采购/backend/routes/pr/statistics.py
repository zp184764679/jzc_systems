# routes/pr/statistics.py
# 统计相关接口

from flask import Blueprint, request, jsonify
from models.pr import PR
import traceback

bp = Blueprint('pr_statistics', __name__)

@bp.route('/statistics', methods=['GET', 'OPTIONS'])
def get_statistics():
    """
    获取物料申请的统计信息
    可选参数：user_id - 如果提供，则只统计该用户的数据
    
    返回：
    {
        "approved": 5,
        "pending": 3,
        "rejected": 1,
        "total": 9
    }
    """
    if request.method == 'OPTIONS':
        return "", 204
    
    try:
        user_id = request.args.get('user_id')

        query = PR.query
        if user_id:
            query = query.filter_by(owner_id=int(user_id))

        approved_count = query.filter_by(status="approved").count()
        pending_count  = query.filter_by(status="submitted").count()
        rejected_count = query.filter_by(status="rejected").count()

        return jsonify({
            "approved": approved_count,
            "pending": pending_count,
            "rejected": rejected_count,
            "total": approved_count + pending_count + rejected_count
        }), 200

    except Exception as e:
        print(f"获取统计信息错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"查询失败: {str(e)}"}), 500