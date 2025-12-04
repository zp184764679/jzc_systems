# api/products.py
"""
产品管理 API - 工程数据系统的产品模块
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from config.database import get_db
from models.product import Product
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter()


# ===== Pydantic Schemas =====

class ProductBase(BaseModel):
    """产品基础Schema"""
    code: str = Field(..., description="产品编码")
    name: str = Field(..., description="产品名称")
    customer_part_number: Optional[str] = Field(None, description="客户料号")
    material: Optional[str] = Field(None, description="材质")
    material_spec: Optional[str] = Field(None, description="材质规格")
    density: Optional[float] = Field(None, description="密度 g/cm³")
    outer_diameter: Optional[float] = Field(None, description="外径 mm")
    length: Optional[float] = Field(None, description="长度 mm")
    width_or_od: Optional[str] = Field(None, description="宽度/外径")
    weight_kg: Optional[float] = Field(None, description="重量 kg")
    subpart_count: Optional[int] = Field(None, description="子部数量")
    tolerance: Optional[str] = Field(None, description="公差等级")
    surface_roughness: Optional[str] = Field(None, description="表面粗糙度")
    heat_treatment: Optional[str] = Field(None, description="热处理要求")
    surface_treatment: Optional[str] = Field(None, description="表面处理要求")
    customer_drawing_no: Optional[str] = Field(None, description="客户图号")
    drawing_id: Optional[int] = Field(None, description="关联图纸ID")
    version: str = Field(default="A.0", description="版本号")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(default=True, description="是否启用")


class ProductCreate(ProductBase):
    """创建产品Schema"""
    pass


class ProductUpdate(ProductBase):
    """更新产品Schema"""
    code: Optional[str] = Field(None, description="产品编码")
    name: Optional[str] = Field(None, description="产品名称")


class ProductResponse(ProductBase):
    """产品响应Schema"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== API Endpoints =====

@router.get("", response_model=List[ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    material: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取产品列表

    - **skip**: 跳过记录数（分页）
    - **limit**: 返回记录数（分页）
    - **search**: 搜索关键词（产品编码、名称、客户料号）
    - **is_active**: 是否启用（True/False/None）
    - **material**: 按材质筛选
    """
    query = db.query(Product)

    # 搜索过滤
    if search:
        query = query.filter(
            (Product.code.contains(search)) |
            (Product.name.contains(search)) |
            (Product.customer_part_number.contains(search))
        )

    # 状态过滤
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    # 材质过滤
    if material:
        query = query.filter(Product.material.contains(material))

    # 排序：按创建时间倒序
    query = query.order_by(Product.created_at.desc())

    return query.offset(skip).limit(limit).all()


@router.post("", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    创建新产品

    - **code**: 产品编码（必填，唯一）
    - **name**: 产品名称（必填）
    - 其他字段可选
    """
    # 检查产品编码是否已存在
    existing = db.query(Product).filter(Product.code == product.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"产品编码 '{product.code}' 已存在")

    # 创建产品
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    获取单个产品详情

    - **product_id**: 产品ID
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"产品ID {product_id} 不存在")
    return product


@router.get("/code/{product_code}", response_model=ProductResponse)
def get_product_by_code(product_code: str, db: Session = Depends(get_db)):
    """
    根据产品编码获取产品

    - **product_code**: 产品编码
    """
    product = db.query(Product).filter(Product.code == product_code).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"产品编码 '{product_code}' 不存在")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    """
    更新产品信息

    - **product_id**: 产品ID
    - 只更新提供的字段
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail=f"产品ID {product_id} 不存在")

    # 如果更新产品编码，检查新编码是否已被其他产品使用
    if product.code and product.code != db_product.code:
        existing = db.query(Product).filter(Product.code == product.code).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"产品编码 '{product.code}' 已被其他产品使用")

    # 更新字段
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    删除产品

    - **product_id**: 产品ID
    - 注意：如果产品已关联报价单，建议使用停用而非删除
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail=f"产品ID {product_id} 不存在")

    # 检查是否有关联的报价单
    if db_product.quotes:
        raise HTTPException(
            status_code=400,
            detail=f"产品 '{db_product.code}' 已关联 {len(db_product.quotes)} 个报价单，无法删除。建议停用该产品。"
        )

    db.delete(db_product)
    db.commit()
    return {"message": f"产品 '{db_product.code}' 已删除"}


@router.patch("/{product_id}/toggle")
def toggle_product_status(product_id: int, db: Session = Depends(get_db)):
    """
    切换产品启用/停用状态

    - **product_id**: 产品ID
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail=f"产品ID {product_id} 不存在")

    db_product.is_active = not db_product.is_active
    db.commit()
    db.refresh(db_product)

    status_text = "启用" if db_product.is_active else "停用"
    return {
        "message": f"产品 '{db_product.code}' 已{status_text}",
        "is_active": db_product.is_active
    }


@router.post("/from-drawing/{drawing_id}", response_model=ProductResponse)
def create_product_from_drawing(drawing_id: int, db: Session = Depends(get_db)):
    """
    从图纸创建产品

    - **drawing_id**: 图纸ID
    - 自动从图纸信息中提取产品数据
    """
    from models.drawing import Drawing

    drawing = db.query(Drawing).filter(Drawing.id == drawing_id).first()
    if not drawing:
        raise HTTPException(status_code=404, detail=f"图纸ID {drawing_id} 不存在")

    # 检查该图纸是否已创建产品
    existing = db.query(Product).filter(Product.drawing_id == drawing_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"图纸 '{drawing.drawing_number}' 已关联产品 '{existing.code}'"
        )

    # 从图纸创建产品
    product = Product(
        code=drawing.drawing_number,
        name=drawing.product_name or drawing.drawing_number,
        customer_part_number=drawing.customer_part_number,
        material=drawing.material,
        material_spec=drawing.material_spec,
        outer_diameter=float(drawing.outer_diameter) if drawing.outer_diameter and str(drawing.outer_diameter).replace('.', '').isdigit() else None,
        length=float(drawing.length) if drawing.length and str(drawing.length).replace('.', '').isdigit() else None,
        weight_kg=float(drawing.weight) if drawing.weight and str(drawing.weight).replace('.', '').isdigit() else None,
        tolerance=drawing.tolerance,
        surface_roughness=drawing.surface_roughness,
        heat_treatment=drawing.heat_treatment,
        surface_treatment=drawing.surface_treatment,
        customer_drawing_no=drawing.drawing_number,
        drawing_id=drawing.id,
        version=drawing.version or "A.0",
        description=f"从图纸 {drawing.drawing_number} 自动创建"
    )

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/stats/summary")
def get_products_summary(db: Session = Depends(get_db)):
    """
    获取产品统计摘要

    返回：
    - 总产品数
    - 启用产品数
    - 停用产品数
    - 按材质分组统计
    """
    from sqlalchemy import func

    total_count = db.query(func.count(Product.id)).scalar()
    active_count = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
    inactive_count = total_count - active_count

    # 按材质分组统计
    material_stats = db.query(
        Product.material,
        func.count(Product.id).label('count')
    ).filter(
        Product.material.isnot(None)
    ).group_by(
        Product.material
    ).all()

    return {
        "total_count": total_count,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "material_distribution": [
            {"material": mat, "count": cnt}
            for mat, cnt in material_stats
        ]
    }
