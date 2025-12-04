# routes/pr/search.py
# 搜索相关接口

from flask import Blueprint, request, jsonify
from models.pr_item import PRItem
from extensions import db
import traceback

bp = Blueprint('pr_search', __name__)

@bp.route('/materials/search', methods=['GET', 'OPTIONS'])
def search_materials():
    """
    搜索已批准PR中的物料
    参数：q - 搜索关键词
    
    返回格式：
    [
      { "name": "钢板", "spec": "Φ 10mm" },
      { "name": "钢板", "spec": "Φ 15mm" }
    ]
    """
    if request.method == 'OPTIONS':
        resp = jsonify({})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, User-ID, User-Role, Supplier-ID'
        resp.headers['Access-Control-Max-Age'] = '3600'
        return resp, 204
    
    try:
        q = request.args.get('q', '').strip()
        
        if not q:
            return jsonify([]), 200
        
        # 查询已批准PR中的物料，按名称模糊搜索
        items = db.session.query(PRItem).filter(
            PRItem.name.ilike(f'%{q}%'),
            PRItem.status == 'approved'
        ).distinct(PRItem.name, PRItem.spec).all()
        
        result = [
            {"name": item.name, "spec": item.spec}
            for item in items
        ]
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"搜索物料错误: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"搜索失败: {str(e)}"}), 500