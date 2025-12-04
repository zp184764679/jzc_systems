# api/materials.py
"""
材料库管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from config.database import get_db
from models.material import Material
from api.schemas import MaterialResponse, MaterialList, MaterialBase

router = APIRouter()


@router.get("", response_model=MaterialList)
def list_materials(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    search: Optional[str] = Query(None, description="搜索材料代码或名称"),
    db: Session = Depends(get_db)
):
    """
    获取材料列表

    - 支持分页
    - 支持按类别筛选
    - 支持搜索材料代码或名称
    """
    query = db.query(Material).filter(Material.is_active == True)

    # 筛选条件
    if category:
        query = query.filter(Material.category == category)

    if search:
        query = query.filter(
            (Material.material_code.contains(search)) |
            (Material.material_name.contains(search))
        )

    # 获取总数
    total = query.count()

    # 分页查询
    items = query.order_by(Material.material_code).offset(skip).limit(limit).all()

    return MaterialList(total=total, items=items)


@router.get("/categories")
def list_material_categories(db: Session = Depends(get_db)):
    """
    获取所有材料类别

    返回系统中所有不重复的材料类别
    """
    categories = db.query(Material.category).filter(
        Material.is_active == True,
        Material.category.isnot(None)
    ).distinct().all()

    return {
        "categories": [cat[0] for cat in categories if cat[0]]
    }


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(material_id: int, db: Session = Depends(get_db)):
    """
    获取材料详情
    """
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.is_active == True
    ).first()

    if not material:
        raise HTTPException(status_code=404, detail="材料不存在")

    return material


@router.get("/code/{material_code}", response_model=MaterialResponse)
def get_material_by_code(material_code: str, db: Session = Depends(get_db)):
    """
    通过材料代码获取材料详情
    """
    material = db.query(Material).filter(
        Material.material_code == material_code,
        Material.is_active == True
    ).first()

    if not material:
        raise HTTPException(status_code=404, detail=f"材料代码 {material_code} 不存在")

    return material


@router.post("", response_model=MaterialResponse, status_code=201)
def create_material(material: MaterialBase, db: Session = Depends(get_db)):
    """
    添加新材料

    - 需要提供材料代码和名称
    - 材料代码必须唯一
    """
    # 检查材料代码是否已存在
    existing = db.query(Material).filter(
        Material.material_code == material.material_code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"材料代码 {material.material_code} 已存在"
        )

    # 创建材料
    db_material = Material(**material.dict())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)

    return db_material


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_data: MaterialBase,
    db: Session = Depends(get_db)
):
    """
    更新材料信息
    """
    material = db.query(Material).filter(Material.id == material_id).first()

    if not material:
        raise HTTPException(status_code=404, detail="材料不存在")

    # 检查材料代码是否与其他材料冲突
    if material_data.material_code != material.material_code:
        existing = db.query(Material).filter(
            Material.material_code == material_data.material_code,
            Material.id != material_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"材料代码 {material_data.material_code} 已被其他材料使用"
            )

    # 更新字段
    for field, value in material_data.dict(exclude_unset=True).items():
        setattr(material, field, value)

    db.commit()
    db.refresh(material)

    return material


@router.delete("/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    """
    删除材料（软删除）
    """
    material = db.query(Material).filter(Material.id == material_id).first()

    if not material:
        raise HTTPException(status_code=404, detail="材料不存在")

    # 软删除
    material.is_active = False
    db.commit()

    return {"message": f"材料 {material.material_name} 已删除"}
