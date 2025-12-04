# api/processes.py
"""
工艺库管理API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from config.database import get_db
from models.process import Process
from api.schemas import ProcessResponse, ProcessList, ProcessBase

router = APIRouter()


@router.get("", response_model=ProcessList)
def list_processes(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    search: Optional[str] = Query(None, description="搜索工艺代码或名称"),
    db: Session = Depends(get_db)
):
    """
    获取工艺列表

    - 支持分页
    - 支持按类别筛选（车削、铣削、磨削等）
    - 支持搜索工艺代码或名称
    """
    query = db.query(Process).filter(Process.is_active == True)

    # 筛选条件
    if category:
        query = query.filter(Process.category == category)

    if search:
        query = query.filter(
            (Process.process_code.contains(search)) |
            (Process.process_name.contains(search))
        )

    # 获取总数
    total = query.count()

    # 分页查询
    items = query.order_by(Process.process_code).offset(skip).limit(limit).all()

    # 显式转换为ProcessResponse对象
    response_items = [ProcessResponse.model_validate(item) for item in items]

    return ProcessList(total=total, items=response_items)


@router.get("/categories")
def list_process_categories(db: Session = Depends(get_db)):
    """
    获取所有工艺类别

    返回系统中所有不重复的工艺类别
    """
    categories = db.query(Process.category).filter(
        Process.is_active == True,
        Process.category.isnot(None)
    ).distinct().all()

    return {
        "categories": [cat[0] for cat in categories if cat[0]]
    }


@router.get("/{process_id}", response_model=ProcessResponse)
def get_process(process_id: int, db: Session = Depends(get_db)):
    """
    获取工艺详情
    """
    process = db.query(Process).filter(
        Process.id == process_id,
        Process.is_active == True
    ).first()

    if not process:
        raise HTTPException(status_code=404, detail="工艺不存在")

    return process


@router.get("/code/{process_code}", response_model=ProcessResponse)
def get_process_by_code(process_code: str, db: Session = Depends(get_db)):
    """
    通过工艺代码获取工艺详情
    """
    process = db.query(Process).filter(
        Process.process_code == process_code,
        Process.is_active == True
    ).first()

    if not process:
        raise HTTPException(status_code=404, detail=f"工艺代码 {process_code} 不存在")

    return process


@router.post("", response_model=ProcessResponse, status_code=201)
def create_process(process: ProcessBase, db: Session = Depends(get_db)):
    """
    添加新工艺

    - 需要提供工艺代码和名称
    - 工艺代码必须唯一
    """
    # 检查工艺代码是否已存在
    existing = db.query(Process).filter(
        Process.process_code == process.process_code
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"工艺代码 {process.process_code} 已存在"
        )

    # 创建工艺
    db_process = Process(**process.dict())
    db.add(db_process)
    db.commit()
    db.refresh(db_process)

    return db_process


@router.put("/{process_id}", response_model=ProcessResponse)
def update_process(
    process_id: int,
    process_data: ProcessBase,
    db: Session = Depends(get_db)
):
    """
    更新工艺信息
    """
    process = db.query(Process).filter(Process.id == process_id).first()

    if not process:
        raise HTTPException(status_code=404, detail="工艺不存在")

    # 检查工艺代码是否与其他工艺冲突
    if process_data.process_code != process.process_code:
        existing = db.query(Process).filter(
            Process.process_code == process_data.process_code,
            Process.id != process_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"工艺代码 {process_data.process_code} 已被其他工艺使用"
            )

    # 更新字段
    for field, value in process_data.dict(exclude_unset=True).items():
        setattr(process, field, value)

    db.commit()
    db.refresh(process)

    return process


@router.delete("/{process_id}")
def delete_process(process_id: int, db: Session = Depends(get_db)):
    """
    删除工艺（软删除）
    """
    process = db.query(Process).filter(Process.id == process_id).first()

    if not process:
        raise HTTPException(status_code=404, detail="工艺不存在")

    # 软删除
    process.is_active = False
    db.commit()

    return {"message": f"工艺 {process.process_name} 已删除"}


@router.get("/recommend/{material}")
def recommend_processes(
    material: str,
    db: Session = Depends(get_db)
):
    """
    根据材料推荐工艺路线

    - 基于材料特性推荐合适的加工工艺
    - 返回推荐的工艺列表和顺序
    """
    # 简单的推荐逻辑（可以后续优化）
    recommended = []

    # 基础加工工艺
    if "不锈钢" in material or "SUS" in material:
        recommended.extend(["CNC_TURNING", "CNC_MILLING", "GRINDING"])
    elif "铝" in material or "AL" in material:
        recommended.extend(["CNC_TURNING", "CNC_MILLING"])
    else:
        recommended.extend(["CNC_TURNING"])

    # 查询推荐的工艺
    processes = db.query(Process).filter(
        Process.process_code.in_(recommended),
        Process.is_active == True
    ).all()

    return {
        "material": material,
        "recommended_processes": [
            {
                "code": p.process_code,
                "name": p.process_name,
                "category": p.category,
                "hourly_rate": p.hourly_rate
            }
            for p in processes
        ]
    }
