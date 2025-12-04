# api/boms.py
"""
BOM管理 API
物料清单的增删改查及版本复制功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from config.database import get_db
from models.bom import BOM, BOMItem
from pydantic import BaseModel, Field

router = APIRouter()


# ==================== Pydantic Schemas ====================

class BOMItemBase(BaseModel):
    """BOM明细基础模型"""
    level: Optional[str] = Field(None, description="层级序号，如：1, 1.1, 1.1.1")
    sequence: Optional[int] = Field(None, description="排序序号")
    part_no: Optional[str] = Field(None, description="零件编号")
    part_name: Optional[str] = Field(None, description="零件名称")
    spec: Optional[str] = Field(None, description="规格型号")
    unit: str = Field(default="PCS", description="单位")
    qty: float = Field(default=1.0, description="用量/配比")
    loss_rate: float = Field(default=0.0, description="损耗率(%)")
    alt_part: Optional[str] = Field(None, description="替代料")
    supplier: Optional[str] = Field(None, description="供应商")
    remark: Optional[str] = Field(None, description="备注")


class BOMItemCreate(BOMItemBase):
    """创建BOM明细"""
    pass


class BOMItemResponse(BOMItemBase):
    """BOM明细响应"""
    id: int
    bom_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BOMBase(BaseModel):
    """BOM基础模型"""
    bom_code: str = Field(..., description="BOM编码")
    product_id: int = Field(..., description="产品ID")
    version: str = Field(default="A.01", description="版本号")
    material_type: str = Field(default="成品", description="物料类型")
    unit: str = Field(default="套", description="单位")
    effective_from: Optional[date] = Field(None, description="生效日期")
    effective_to: Optional[date] = Field(None, description="失效日期")
    maker: Optional[str] = Field(None, description="制表人")
    approver: Optional[str] = Field(None, description="审核人")
    remark: Optional[str] = Field(None, description="备注")
    is_active: bool = Field(default=True, description="是否启用")


class BOMCreate(BOMBase):
    """创建BOM"""
    items: List[BOMItemCreate] = Field(default=[], description="BOM明细列表")


class BOMUpdate(BaseModel):
    """更新BOM"""
    bom_code: Optional[str] = None
    version: Optional[str] = None
    material_type: Optional[str] = None
    unit: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    maker: Optional[str] = None
    approver: Optional[str] = None
    remark: Optional[str] = None
    is_active: Optional[bool] = None
    items: Optional[List[BOMItemCreate]] = None


class BOMResponse(BOMBase):
    """BOM响应"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[BOMItemResponse] = []

    class Config:
        from_attributes = True


# ==================== API Endpoints ====================

@router.get("/boms", response_model=List[BOMResponse])
def get_boms(
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(100, description="返回记录数"),
    product_id: Optional[int] = Query(None, description="产品ID筛选"),
    is_active: Optional[bool] = Query(None, description="启用状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取BOM列表
    支持分页和筛选
    """
    query = db.query(BOM)

    if product_id:
        query = query.filter(BOM.product_id == product_id)
    if is_active is not None:
        query = query.filter(BOM.is_active == is_active)

    boms = query.offset(skip).limit(limit).all()
    return boms


@router.post("/boms", response_model=BOMResponse)
def create_bom(bom: BOMCreate, db: Session = Depends(get_db)):
    """
    创建BOM
    包含表头和明细
    """
    # 检查BOM编码是否已存在
    existing = db.query(BOM).filter(BOM.bom_code == bom.bom_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"BOM编码 {bom.bom_code} 已存在")

    # 检查产品是否存在
    from models.product import Product
    product = db.query(Product).filter(Product.id == bom.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"产品ID {bom.product_id} 不存在")

    # 创建BOM主表
    bom_data = bom.dict(exclude={'items'})
    db_bom = BOM(**bom_data)
    db.add(db_bom)
    db.flush()  # 获取BOM ID

    # 创建BOM明细
    for item in bom.items:
        db_item = BOMItem(**item.dict(), bom_id=db_bom.id)
        db.add(db_item)

    db.commit()
    db.refresh(db_bom)
    return db_bom


@router.get("/boms/{bom_id}", response_model=BOMResponse)
def get_bom(bom_id: int, db: Session = Depends(get_db)):
    """
    获取BOM详情
    包含所有明细行
    """
    bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail=f"BOM ID {bom_id} 不存在")
    return bom


@router.put("/boms/{bom_id}", response_model=BOMResponse)
def update_bom(bom_id: int, bom: BOMUpdate, db: Session = Depends(get_db)):
    """
    更新BOM
    可以更新表头和明细
    """
    db_bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if not db_bom:
        raise HTTPException(status_code=404, detail=f"BOM ID {bom_id} 不存在")

    # 更新主表
    update_data = bom.dict(exclude_unset=True, exclude={'items'})
    for key, value in update_data.items():
        setattr(db_bom, key, value)

    # 如果提供了items，则更新明细（先删除旧的，再添加新的）
    if bom.items is not None:
        # 删除旧明细
        db.query(BOMItem).filter(BOMItem.bom_id == bom_id).delete()

        # 添加新明细
        for item in bom.items:
            db_item = BOMItem(**item.dict(), bom_id=bom_id)
            db.add(db_item)

    db.commit()
    db.refresh(db_bom)
    return db_bom


@router.delete("/boms/{bom_id}")
def delete_bom(bom_id: int, db: Session = Depends(get_db)):
    """
    删除BOM
    级联删除所有明细行
    """
    db_bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if not db_bom:
        raise HTTPException(status_code=404, detail=f"BOM ID {bom_id} 不存在")

    db.delete(db_bom)  # cascade会自动删除items
    db.commit()
    return {"message": f"BOM {db_bom.bom_code} 已删除", "success": True}


@router.post("/boms/{bom_id}/copy", response_model=BOMResponse)
def copy_bom(
    bom_id: int,
    new_version: str = Query(..., description="新版本号"),
    db: Session = Depends(get_db)
):
    """
    复制BOM创建新版本
    保留所有明细数据
    """
    source_bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if not source_bom:
        raise HTTPException(status_code=404, detail=f"源BOM ID {bom_id} 不存在")

    # 生成新BOM编码
    new_code = f"{source_bom.bom_code}-{new_version}"

    # 检查新编码是否存在
    existing = db.query(BOM).filter(BOM.bom_code == new_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"BOM编码 {new_code} 已存在")

    # 复制BOM主表
    new_bom = BOM(
        bom_code=new_code,
        product_id=source_bom.product_id,
        version=new_version,
        material_type=source_bom.material_type,
        unit=source_bom.unit,
        maker=source_bom.maker,
        remark=f"从 {source_bom.bom_code} 复制",
        is_active=True
    )
    db.add(new_bom)
    db.flush()

    # 复制BOM明细
    for item in source_bom.items:
        new_item = BOMItem(
            bom_id=new_bom.id,
            level=item.level,
            sequence=item.sequence,
            part_no=item.part_no,
            part_name=item.part_name,
            spec=item.spec,
            unit=item.unit,
            qty=item.qty,
            loss_rate=item.loss_rate,
            alt_part=item.alt_part,
            supplier=item.supplier,
            remark=item.remark
        )
        db.add(new_item)

    db.commit()
    db.refresh(new_bom)
    return new_bom


@router.get("/products/{product_id}/boms", response_model=List[BOMResponse])
def get_product_boms(product_id: int, db: Session = Depends(get_db)):
    """
    获取指定产品的所有BOM
    按版本排序
    """
    from models.product import Product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"产品ID {product_id} 不存在")

    boms = db.query(BOM).filter(BOM.product_id == product_id).order_by(BOM.version.desc()).all()
    return boms


@router.patch("/boms/{bom_id}/toggle", response_model=BOMResponse)
def toggle_bom_status(bom_id: int, db: Session = Depends(get_db)):
    """
    切换BOM启用状态
    """
    db_bom = db.query(BOM).filter(BOM.id == bom_id).first()
    if not db_bom:
        raise HTTPException(status_code=404, detail=f"BOM ID {bom_id} 不存在")

    db_bom.is_active = not db_bom.is_active
    db.commit()
    db.refresh(db_bom)
    return db_bom


@router.get("/boms/search", response_model=List[BOMResponse])
def search_boms(
    keyword: str = Query(..., description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    搜索BOM
    支持按BOM编码、版本号搜索
    """
    boms = db.query(BOM).filter(
        (BOM.bom_code.like(f"%{keyword}%")) |
        (BOM.version.like(f"%{keyword}%"))
    ).all()
    return boms
