# routes/ai_routes.py
# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from services.ai_classifier import LocalClassifier
from constants.categories import get_major_category

URL_PREFIX = '/api/v1/ai'

bp = Blueprint("ai", __name__)
clf = LocalClassifier()

@bp.before_request
def handle_preflight():
    if request.method == 'OPTIONS':
        return '', 200

@bp.post("/classify")
def classify():
    """
    单条物料分类
    Request:
    { "text": "凸轮", "name": "...", "spec": "...", "remark": "..." }
    """
    payload = request.get_json(force=True) or {}
    text = payload.get("text")
    if not text:
        name = payload.get("name", "")
        spec = payload.get("spec", "")
        remark = payload.get("remark", "")
        text = " ".join([name, spec, remark]).strip()
    result = clf.classify(text, "", "")
    return result, 200


@bp.post("/classify-batch")
def classify_batch():
    """
    批量分类物料（按category分组）
    
    Request:
    {
      "items": [
        {"sku": "SKU001", "name": "凸轮", "spec": "φ10x20", "qty": 5, "unit": "个"},
        {"sku": "SKU002", "name": "轴承", "spec": "6205", "qty": 10, "unit": "个"}
      ]
    }
    
    Response:
    {
      "groups": [
        {
          "category": "机械零部件/传动",
          "major_category": "机械零部件",
          "items": [...]
        }
      ]
    }
    """
    try:
        payload = request.get_json() or {}
        items = payload.get("items", [])
        
        if not items:
            return jsonify({"error": "items 不能为空"}), 400
        
        # 分类每一项
        classified_items = []
        for item in items:
            name = item.get("name", "")
            spec = item.get("spec", "")
            remark = item.get("remark", "")
            
            result = clf.classify(name, spec, remark)
            category = result.get("category", "未分类")
            major_category = result.get("major_category", "")
            minor_category = result.get("minor_category", "")
            
            # 保留原始item信息，追加分类结果
            classified_item = {
                **item,
                "category": category,
                "major_category": major_category,
                "minor_category": minor_category
            }
            classified_items.append(classified_item)
        
        # 按category分组
        groups_dict = {}
        for item in classified_items:
            cat = item.get("category")
            major_cat = item.get("major_category")
            
            if cat not in groups_dict:
                groups_dict[cat] = {
                    "category": cat,
                    "major_category": major_cat,
                    "items": []
                }
            groups_dict[cat]["items"].append(item)
        
        # 转换为列表格式
        groups = list(groups_dict.values())
        
        return jsonify({
            "groups": groups
        }), 200
    
    except Exception as e:
        import traceback
        print(f"批量分类错误: {e}")
        traceback.print_exc()
        return jsonify({"error": f"分类失败: {str(e)}"}), 500