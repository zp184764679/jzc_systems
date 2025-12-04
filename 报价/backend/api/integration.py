# api/integration.py
"""
跨系统集成API
提供对其他子系统数据的访问
"""
from fastapi import APIRouter, Query, HTTPException
from services.crm_service import crm_service
from services.hr_service import hr_service
from services.pdm_service import pdm_service

router = APIRouter()


# ========== CRM客户数据集成 ==========

@router.get("/customers")
async def get_crm_customers(
    keyword: str = Query("", description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量")
):
    """
    从CRM系统获取客户列表

    用于在报价系统中选择客户，避免重复录入客户信息
    """
    result = crm_service.get_customers(keyword=keyword, page=page, page_size=page_size)
    if not result.get("success", False):
        return {
            "success": False,
            "error": result.get("error", "获取CRM客户数据失败"),
            "data": result.get("data", {"items": [], "total": 0, "page": page, "page_size": page_size})
        }
    return result


@router.get("/customers/{customer_id}")
async def get_crm_customer_detail(customer_id: int):
    """
    从CRM系统获取客户详情
    """
    result = crm_service.get_customer_by_id(customer_id)
    if not result.get("success", False):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "客户不存在")
        )
    return result


@router.post("/customers/search")
async def search_crm_customers(data: dict):
    """
    搜索CRM客户
    """
    keyword = data.get("keyword", "")
    page = data.get("page", 1)
    page_size = data.get("page_size", 20)

    result = crm_service.search_customers(keyword=keyword, page=page, page_size=page_size)
    return result


@router.get("/customers/count")
async def get_crm_customer_count():
    """
    获取CRM客户总数
    """
    count = crm_service.get_customer_count()
    return {"success": True, "data": {"count": count}}


@router.get("/health/crm")
async def check_crm_health():
    """
    检查CRM服务健康状态
    """
    is_healthy = crm_service.health_check()
    return {
        "success": True,
        "data": {
            "service": "CRM",
            "status": "healthy" if is_healthy else "unavailable",
            "url": crm_service.base_url
        }
    }


@router.get("/health")
async def check_all_integrations():
    """
    检查所有跨系统集成的健康状态
    """
    crm_healthy = crm_service.health_check()
    hr_healthy = hr_service.health_check()
    pdm_healthy = pdm_service.health_check()

    return {
        "success": True,
        "data": {
            "integrations": {
                "crm": {
                    "status": "healthy" if crm_healthy else "unavailable",
                    "url": crm_service.base_url
                },
                "hr": {
                    "status": "healthy" if hr_healthy else "unavailable",
                    "url": hr_service.base_url
                },
                "pdm": {
                    "status": "healthy" if pdm_healthy else "unavailable",
                    "url": pdm_service.base_url
                }
            }
        }
    }


# ========== HR员工数据集成 ==========

@router.get("/hr/sales-staff")
async def get_hr_sales_staff(
    search: str = Query("", description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(100, ge=1, le=500, description="每页数量")
):
    """
    从HR系统获取销售人员列表

    用于在报价系统中选择销售负责人
    """
    result = hr_service.get_sales_staff(search=search, page=page, per_page=per_page)
    return result


@router.get("/hr/employees/{employee_id}")
async def get_hr_employee_detail(employee_id: int):
    """
    从HR系统获取员工详情
    """
    result = hr_service.get_employee(employee_id)
    if not result.get("success", False):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "员工不存在")
        )
    return result


@router.get("/health/hr")
async def check_hr_health():
    """
    检查HR服务健康状态
    """
    is_healthy = hr_service.health_check()
    return {
        "success": True,
        "data": {
            "service": "HR",
            "status": "healthy" if is_healthy else "unavailable",
            "url": hr_service.base_url
        }
    }


# ========== PDM产品数据集成 ==========

@router.get("/pdm/products")
async def get_pdm_products(
    keyword: str = Query("", description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量")
):
    """
    从PDM系统获取产品列表

    用于获取产品成本信息进行报价计算
    """
    result = pdm_service.get_products(keyword=keyword, page=page, page_size=page_size)
    return result


@router.get("/pdm/products/{product_id}")
async def get_pdm_product_detail(product_id: int):
    """
    从PDM系统获取产品详情
    """
    result = pdm_service.get_product_by_id(product_id)
    if not result.get("success", False):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "产品不存在")
        )
    return result


@router.get("/pdm/products/by-code/{product_code}")
async def get_pdm_product_by_code(product_code: str):
    """
    根据产品编码从PDM系统获取产品信息
    """
    result = pdm_service.get_product_by_code(product_code)
    if not result.get("success", False):
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "产品不存在")
        )
    return result


@router.get("/pdm/products/{product_id}/cost")
async def get_pdm_product_cost(product_id: int):
    """
    从PDM系统获取产品成本信息

    用于报价计算时获取产品的标准成本
    """
    result = pdm_service.get_product_cost(product_id)
    return result


@router.get("/health/pdm")
async def check_pdm_health():
    """
    检查PDM服务健康状态
    """
    is_healthy = pdm_service.health_check()
    return {
        "success": True,
        "data": {
            "service": "PDM",
            "status": "healthy" if is_healthy else "unavailable",
            "url": pdm_service.base_url
        }
    }
