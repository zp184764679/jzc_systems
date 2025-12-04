# api/schemas.py
"""
Pydantic数据模型（请求和响应）
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ 图纸相关 ============

class DrawingBase(BaseModel):
    """图纸基础模型"""
    drawing_number: str = Field(..., description="图号")
    customer_name: Optional[str] = Field(None, description="客户名称")
    product_name: Optional[str] = Field(None, description="产品名称")
    customer_part_number: Optional[str] = Field(None, description="客户料号")
    material: Optional[str] = Field(None, description="材质")
    material_spec: Optional[str] = Field(None, description="材质规格")
    outer_diameter: Optional[str] = Field(None, description="外径")
    length: Optional[str] = Field(None, description="长度")
    weight: Optional[str] = Field(None, description="重量")
    tolerance: Optional[str] = Field(None, description="公差等级")
    surface_roughness: Optional[str] = Field(None, description="表面粗糙度")
    heat_treatment: Optional[str] = Field(None, description="热处理要求")
    surface_treatment: Optional[str] = Field(None, description="表面处理要求")
    special_requirements: Optional[str] = Field(None, description="特殊技术要求")
    notes: Optional[str] = Field(None, description="备注")
    version: Optional[str] = Field("A.0", description="版本号")


class DrawingCreate(DrawingBase):
    """创建图纸请求"""
    pass


class DrawingUpdate(BaseModel):
    """更新图纸请求"""
    drawing_number: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    customer_part_number: Optional[str] = None
    material: Optional[str] = None
    material_spec: Optional[str] = None
    outer_diameter: Optional[str] = None
    length: Optional[str] = None
    weight: Optional[str] = None
    tolerance: Optional[str] = None
    surface_roughness: Optional[str] = None
    heat_treatment: Optional[str] = None
    surface_treatment: Optional[str] = None
    special_requirements: Optional[str] = None
    notes: Optional[str] = None
    version: Optional[str] = None


class DrawingResponse(DrawingBase):
    """图纸响应"""
    id: int
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    ocr_data: Optional[Dict[str, Any]] = None
    ocr_confidence: Optional[str] = None
    ocr_status: str = "pending"
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DrawingList(BaseModel):
    """图纸列表响应"""
    total: int
    items: List[DrawingResponse]


class OCRResult(BaseModel):
    """OCR识别结果"""
    success: bool
    drawing_number: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    customer_part_number: Optional[str] = None
    material: Optional[str] = None
    outer_diameter: Optional[str] = None
    length: Optional[str] = None
    tolerance: Optional[str] = None
    surface_roughness: Optional[str] = None
    weight: Optional[str] = None
    dimensions: Optional[Dict[str, str]] = None
    processes: Optional[List[str]] = None
    special_requirements: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None
    # CRM客户匹配结果
    crm_match: Optional[Dict[str, Any]] = None
    ocr_customer_name: Optional[str] = None  # 原始OCR识别的客户名称


# ============ 材料相关 ============

class MaterialBase(BaseModel):
    """材料基础模型"""
    material_code: str
    material_name: str
    category: Optional[str] = None
    density: Optional[float] = None
    hardness: Optional[str] = None
    tensile_strength: Optional[float] = None
    price_per_kg: Optional[float] = None
    price_currency: str = "CNY"
    supplier: Optional[str] = None
    supplier_code: Optional[str] = None
    remark: Optional[str] = None
    is_active: bool = True


class MaterialResponse(MaterialBase):
    """材料响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MaterialList(BaseModel):
    """材料列表响应"""
    total: int
    items: List[MaterialResponse]


# ============ 工艺相关 ============

class ProcessBase(BaseModel):
    """工艺基础模型"""
    process_code: str
    process_name: str
    category: Optional[str] = None
    machine_type: Optional[str] = None
    machine_model: Optional[str] = None
    hourly_rate: Optional[float] = None
    setup_time: Optional[float] = None
    daily_fee: Optional[float] = None
    daily_output: Optional[int] = None
    defect_rate: Optional[float] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class ProcessResponse(ProcessBase):
    """工艺响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProcessList(BaseModel):
    """工艺列表响应"""
    total: int
    items: List[ProcessResponse]


# ============ 报价相关 ============

class QuoteBase(BaseModel):
    """报价基础模型"""
    quote_number: str
    drawing_id: Optional[int] = None
    customer_name: str
    material_cost: float = 0
    process_cost: float = 0
    management_cost: float = 0
    other_cost: float = 0
    profit: float = 0
    total_amount: float
    currency: str = "CNY"
    exchange_rate: float = 1.0
    quantity: int = 1
    lead_time: Optional[int] = None
    notes: Optional[str] = None


class QuoteCreate(QuoteBase):
    """创建报价请求"""
    pass


class QuoteResponse(QuoteBase):
    """报价响应"""
    id: int
    status: str
    details: Optional[Dict[str, Any]] = None
    valid_until: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuoteList(BaseModel):
    """报价列表响应"""
    total: int
    items: List[QuoteResponse]


# ============ 通用响应 ============

class MessageResponse(BaseModel):
    """消息响应"""
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
