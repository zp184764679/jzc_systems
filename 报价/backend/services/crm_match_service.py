# services/crm_match_service.py
"""
CRM 客户匹配服务
用于将OCR识别的客户名称与CRM数据库进行匹配
"""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# CRM API 配置
CRM_API_BASE_URL = "http://localhost:8002"


def match_customer_name(customer_name: str, min_score: float = 0.5) -> Optional[Dict[str, Any]]:
    """
    将OCR识别的客户名称与CRM数据库进行匹配

    Args:
        customer_name: OCR识别的客户名称
        min_score: 最低匹配分数阈值 (0.0 - 1.0)

    Returns:
        匹配结果字典，包含:
        - matched: bool - 是否找到匹配
        - customer_name: str - 匹配到的标准客户名称
        - customer_id: int - CRM中的客户ID
        - score: float - 匹配分数
        - matched_field: str - 匹配的字段(code/short_name/name/address)
        - original_name: str - 原始OCR识别的名称
    """
    if not customer_name or not customer_name.strip():
        return {
            "matched": False,
            "original_name": customer_name,
            "error": "空客户名称"
        }

    try:
        response = requests.post(
            f"{CRM_API_BASE_URL}/api/customers/match",
            json={"texts": [customer_name.strip()], "limit": 3},
            timeout=10
        )

        if response.status_code != 200:
            logger.warning(f"CRM匹配API返回错误: {response.status_code}")
            return {
                "matched": False,
                "original_name": customer_name,
                "error": f"API错误: {response.status_code}"
            }

        data = response.json()

        if not data.get("success"):
            return {
                "matched": False,
                "original_name": customer_name,
                "error": data.get("error", "匹配失败")
            }

        best_match = data.get("data", {}).get("best_match")

        if best_match and best_match.get("score", 0) >= min_score:
            customer = best_match.get("customer", {})
            result = {
                "matched": True,
                "customer_name": customer.get("short_name") or customer.get("name"),
                "customer_id": customer.get("id"),
                "customer_code": customer.get("code"),
                "score": best_match.get("score"),
                "matched_field": best_match.get("matched_field"),
                "original_name": customer_name,
                "customer_full_name": customer.get("name"),
                "customer_address": customer.get("address")
            }
            logger.info(f"客户匹配成功: '{customer_name}' -> '{result['customer_name']}' (score: {result['score']})")
            return result
        else:
            return {
                "matched": False,
                "original_name": customer_name,
                "candidates": data.get("data", {}).get("matches", [])
            }

    except requests.exceptions.ConnectionError:
        logger.warning(f"无法连接CRM服务: {CRM_API_BASE_URL}")
        return {
            "matched": False,
            "original_name": customer_name,
            "error": "CRM服务不可用"
        }
    except requests.exceptions.Timeout:
        logger.warning("CRM匹配请求超时")
        return {
            "matched": False,
            "original_name": customer_name,
            "error": "请求超时"
        }
    except Exception as e:
        logger.error(f"CRM匹配异常: {str(e)}")
        return {
            "matched": False,
            "original_name": customer_name,
            "error": str(e)
        }


def enhance_ocr_result_with_crm(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用CRM数据增强OCR结果

    如果OCR识别出客户名称，尝试与CRM匹配并使用标准名称

    Args:
        ocr_result: OCR识别结果字典

    Returns:
        增强后的OCR结果，添加crm_match字段
    """
    if not ocr_result.get("success"):
        return ocr_result

    customer_name = ocr_result.get("customer_name")

    if customer_name:
        match_result = match_customer_name(customer_name)
        ocr_result["crm_match"] = match_result

        # 如果匹配成功，可以选择用标准名称替换OCR识别的名称
        if match_result.get("matched"):
            # 保存原始OCR名称
            ocr_result["ocr_customer_name"] = customer_name
            # 使用CRM标准名称
            ocr_result["customer_name"] = match_result["customer_name"]
            logger.info(f"客户名称已标准化: '{customer_name}' -> '{match_result['customer_name']}'")

    return ocr_result


def get_crm_customers_for_autocomplete(keyword: str, limit: int = 10) -> list:
    """
    获取CRM客户列表用于自动补全

    Args:
        keyword: 搜索关键词
        limit: 返回数量限制

    Returns:
        客户列表
    """
    try:
        response = requests.post(
            f"{CRM_API_BASE_URL}/api/customers/search",
            json={"keyword": keyword, "page": 1, "page_size": limit},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("data", {}).get("items", [])
        return []

    except Exception as e:
        logger.warning(f"获取CRM客户列表失败: {str(e)}")
        return []
