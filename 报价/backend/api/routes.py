# api/routes.py
"""
工艺路线管理API - 整合PM系统的模板化功能
注意：文件名为routes.py，但内容是工艺路线(ProcessRoute)管理，避免与FastAPI的routing模块冲突
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from config.database import get_db
from models.process_route import ProcessRoute, ProcessRouteStep
from models.process import Process
import time

router = APIRouter()


# ==================== Pydantic Schemas ====================

class ProcessRouteStepBase(BaseModel):
    """工序步骤基础Schema"""
    process_id: int = Field(..., description="工艺ID")
    sequence: int = Field(default=0, description="工序顺序")
    department: Optional[str] = Field(None, description="部门")
    machine: Optional[str] = Field(None, description="设备")
    machine_model: Optional[str] = Field(None, description="设备型号")
    estimate_minutes: Optional[int] = Field(None, description="预计工时（分钟）")
    setup_time: Optional[float] = Field(default=0, description="段取时间（小时）")
    labor_cost: Optional[float] = Field(default=0, description="人工成本")
    machine_cost: Optional[float] = Field(default=0, description="机器成本")
    tool_cost: Optional[float] = Field(default=0, description="刀具成本")
    material_cost: Optional[float] = Field(default=0, description="辅料成本")
    other_cost: Optional[float] = Field(default=0, description="其他成本")
    total_cost: Optional[float] = Field(default=0, description="该工序总成本")
    daily_output: Optional[int] = Field(None, description="日产量（件/天）")
    defect_rate: Optional[float] = Field(default=0, description="不良率")
    process_parameters: Optional[str] = Field(None, description="工艺参数JSON")
    remarks: Optional[str] = Field(None, description="备注")
    is_active: bool = Field(default=True, description="是否启用")


class ProcessRouteStepCreate(ProcessRouteStepBase):
    """创建工序步骤Schema"""
    pass


class ProcessRouteStepUpdate(BaseModel):
    """更新工序步骤Schema"""
    process_id: Optional[int] = None
    sequence: Optional[int] = None
    department: Optional[str] = None
    machine: Optional[str] = None
    machine_model: Optional[str] = None
    estimate_minutes: Optional[int] = None
    setup_time: Optional[float] = None
    labor_cost: Optional[float] = None
    machine_cost: Optional[float] = None
    tool_cost: Optional[float] = None
    material_cost: Optional[float] = None
    other_cost: Optional[float] = None
    total_cost: Optional[float] = None
    daily_output: Optional[int] = None
    defect_rate: Optional[float] = None
    process_parameters: Optional[str] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class ProcessInfo(BaseModel):
    """工艺信息（用于嵌套展示）"""
    id: int
    process_code: str
    process_name: str
    category: Optional[str] = None

    class Config:
        from_attributes = True


class ProcessRouteStepResponse(ProcessRouteStepBase):
    """工序步骤响应Schema"""
    id: int
    route_id: int
    process: Optional[ProcessInfo] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcessRouteBase(BaseModel):
    """工艺路线基础Schema"""
    route_code: str = Field(..., description="路线编码")
    name: Optional[str] = Field(None, description="路线名称")
    product_id: Optional[int] = Field(None, description="关联产品ID")
    drawing_id: Optional[int] = Field(None, description="关联图纸ID")
    quote_id: Optional[int] = Field(None, description="关联报价ID")
    is_template: bool = Field(default=False, description="是否为模板")
    template_name: Optional[str] = Field(None, description="模板名称")
    template_category: Optional[str] = Field(None, description="模板分类")
    version: Optional[str] = Field(default="1.0", description="版本号")
    description: Optional[str] = Field(None, description="说明")
    is_active: bool = Field(default=True, description="是否启用")


class ProcessRouteCreate(ProcessRouteBase):
    """创建工艺路线Schema"""
    steps: List[ProcessRouteStepCreate] = Field(default=[], description="工序步骤列表")


class ProcessRouteUpdate(BaseModel):
    """更新工艺路线Schema"""
    route_code: Optional[str] = None
    name: Optional[str] = None
    product_id: Optional[int] = None
    drawing_id: Optional[int] = None
    quote_id: Optional[int] = None
    is_template: Optional[bool] = None
    template_name: Optional[str] = None
    template_category: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    steps: Optional[List[ProcessRouteStepCreate]] = None


class ProcessRouteResponse(ProcessRouteBase):
    """工艺路线响应Schema"""
    id: int
    total_cost: float
    total_time: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    steps: List[ProcessRouteStepResponse] = []

    class Config:
        from_attributes = True


class ProcessRouteSummary(BaseModel):
    """工艺路线摘要（不含步骤详情）"""
    id: int
    route_code: str
    name: Optional[str]
    is_template: bool
    template_name: Optional[str]
    template_category: Optional[str]
    total_cost: float
    total_time: float
    steps_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class CostCalculationResult(BaseModel):
    """成本计算结果"""
    route_id: int
    total_cost: float
    total_time_minutes: float
    total_labor_cost: float
    total_machine_cost: float
    total_tool_cost: float
    total_material_cost: float
    total_other_cost: float
    steps_count: int


# ==================== API Endpoints ====================

@router.get("/routes", response_model=List[ProcessRouteSummary])
def get_routes(
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    product_id: Optional[int] = Query(None, description="按产品ID筛选"),
    drawing_id: Optional[int] = Query(None, description="按图纸ID筛选"),
    quote_id: Optional[int] = Query(None, description="按报价ID筛选"),
    is_template: Optional[bool] = Query(None, description="是否为模板"),
    template_category: Optional[str] = Query(None, description="模板分类"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    search: Optional[str] = Query(None, description="搜索关键词（编码或名称）"),
    db: Session = Depends(get_db)
):
    """获取工艺路线列表"""
    query = db.query(ProcessRoute)

    # 筛选条件
    if product_id:
        query = query.filter(ProcessRoute.product_id == product_id)
    if drawing_id:
        query = query.filter(ProcessRoute.drawing_id == drawing_id)
    if quote_id:
        query = query.filter(ProcessRoute.quote_id == quote_id)
    if is_template is not None:
        query = query.filter(ProcessRoute.is_template == is_template)
    if template_category:
        query = query.filter(ProcessRoute.template_category == template_category)
    if is_active is not None:
        query = query.filter(ProcessRoute.is_active == is_active)
    if search:
        query = query.filter(
            (ProcessRoute.route_code.contains(search)) |
            (ProcessRoute.name.contains(search)) |
            (ProcessRoute.template_name.contains(search))
        )

    # 排序并分页
    routes = query.order_by(ProcessRoute.created_at.desc()).offset(skip).limit(limit).all()

    # 转换为摘要格式
    result = []
    for route in routes:
        result.append(ProcessRouteSummary(
            id=route.id,
            route_code=route.route_code,
            name=route.name,
            is_template=route.is_template,
            template_name=route.template_name,
            template_category=route.template_category,
            total_cost=float(route.total_cost or 0),
            total_time=float(route.total_time or 0),
            steps_count=len(route.steps),
            created_at=route.created_at
        ))

    return result


@router.post("/routes", response_model=ProcessRouteResponse)
def create_route(route: ProcessRouteCreate, db: Session = Depends(get_db)):
    """创建工艺路线"""
    # 检查编码是否已存在
    existing = db.query(ProcessRoute).filter(ProcessRoute.route_code == route.route_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"工艺路线编码 {route.route_code} 已存在")

    # 创建路线
    route_data = route.dict(exclude={'steps'})
    db_route = ProcessRoute(**route_data)
    db.add(db_route)
    db.flush()

    # 创建工序步骤
    for step in route.steps:
        # 验证process_id是否存在
        process = db.query(Process).filter(Process.id == step.process_id).first()
        if not process:
            raise HTTPException(status_code=404, detail=f"工艺ID {step.process_id} 不存在")

        db_step = ProcessRouteStep(**step.dict(), route_id=db_route.id)
        db.add(db_step)

    # 计算总成本和总工时
    db.flush()
    _recalculate_route_totals(db_route, db)

    db.commit()
    db.refresh(db_route)

    # 预加载关联数据
    db_route = db.query(ProcessRoute).options(
        joinedload(ProcessRoute.steps).joinedload(ProcessRouteStep.process)
    ).filter(ProcessRoute.id == db_route.id).first()

    return db_route


@router.get("/routes/{route_id}", response_model=ProcessRouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db)):
    """获取工艺路线详情"""
    route = db.query(ProcessRoute).options(
        joinedload(ProcessRoute.steps).joinedload(ProcessRouteStep.process)
    ).filter(ProcessRoute.id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="工艺路线不存在")

    return route


@router.put("/routes/{route_id}", response_model=ProcessRouteResponse)
def update_route(route_id: int, route: ProcessRouteUpdate, db: Session = Depends(get_db)):
    """更新工艺路线"""
    db_route = db.query(ProcessRoute).filter(ProcessRoute.id == route_id).first()
    if not db_route:
        raise HTTPException(status_code=404, detail="工艺路线不存在")

    # 更新主表
    update_data = route.dict(exclude_unset=True, exclude={'steps'})

    # 检查route_code是否重复
    if 'route_code' in update_data and update_data['route_code'] != db_route.route_code:
        existing = db.query(ProcessRoute).filter(ProcessRoute.route_code == update_data['route_code']).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"工艺路线编码 {update_data['route_code']} 已存在")

    for key, value in update_data.items():
        setattr(db_route, key, value)

    # 如果提供了steps，则更新步骤
    if route.steps is not None:
        # 删除旧步骤
        db.query(ProcessRouteStep).filter(ProcessRouteStep.route_id == route_id).delete()

        # 添加新步骤
        for step in route.steps:
            # 验证process_id是否存在
            process = db.query(Process).filter(Process.id == step.process_id).first()
            if not process:
                raise HTTPException(status_code=404, detail=f"工艺ID {step.process_id} 不存在")

            db_step = ProcessRouteStep(**step.dict(), route_id=route_id)
            db.add(db_step)

        db.flush()
        _recalculate_route_totals(db_route, db)

    db.commit()
    db.refresh(db_route)

    # 预加载关联数据
    db_route = db.query(ProcessRoute).options(
        joinedload(ProcessRoute.steps).joinedload(ProcessRouteStep.process)
    ).filter(ProcessRoute.id == db_route.id).first()

    return db_route


@router.delete("/routes/{route_id}")
def delete_route(route_id: int, db: Session = Depends(get_db)):
    """删除工艺路线"""
    db_route = db.query(ProcessRoute).filter(ProcessRoute.id == route_id).first()
    if not db_route:
        raise HTTPException(status_code=404, detail="工艺路线不存在")

    # 检查是否被引用
    if db_route.product_id or db_route.drawing_id or db_route.quote_id:
        raise HTTPException(
            status_code=400,
            detail="工艺路线已被产品/图纸/报价引用，无法删除。请先解除关联或设置为不启用。"
        )

    db.delete(db_route)
    db.commit()
    return {"message": "工艺路线已删除", "route_id": route_id}


@router.post("/routes/from-template/{template_id}", response_model=ProcessRouteResponse)
def create_route_from_template(
    template_id: int,
    product_id: Optional[int] = Query(None, description="关联产品ID"),
    drawing_id: Optional[int] = Query(None, description="关联图纸ID"),
    quote_id: Optional[int] = Query(None, description="关联报价ID"),
    db: Session = Depends(get_db)
):
    """从模板创建工艺路线"""
    template = db.query(ProcessRoute).options(
        joinedload(ProcessRoute.steps)
    ).filter(
        ProcessRoute.id == template_id,
        ProcessRoute.is_template == True
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 生成新编码（时间戳 + 随机数）
    new_code = f"ROUTE-{int(time.time())}"

    # 复制路线
    new_route = ProcessRoute(
        route_code=new_code,
        name=f"{template.template_name or template.name} - 副本",
        product_id=product_id,
        drawing_id=drawing_id,
        quote_id=quote_id,
        is_template=False,
        version=template.version,
        description=f"从模板 [{template.template_name or template.name}] 创建"
    )
    db.add(new_route)
    db.flush()

    # 复制步骤
    for step in template.steps:
        new_step = ProcessRouteStep(
            route_id=new_route.id,
            process_id=step.process_id,
            sequence=step.sequence,
            department=step.department,
            machine=step.machine,
            machine_model=step.machine_model,
            estimate_minutes=step.estimate_minutes,
            setup_time=step.setup_time,
            labor_cost=step.labor_cost,
            machine_cost=step.machine_cost,
            tool_cost=step.tool_cost,
            material_cost=step.material_cost,
            other_cost=step.other_cost,
            total_cost=step.total_cost,
            daily_output=step.daily_output,
            defect_rate=step.defect_rate,
            process_parameters=step.process_parameters,
            remarks=step.remarks,
            is_active=step.is_active
        )
        db.add(new_step)

    db.flush()
    _recalculate_route_totals(new_route, db)

    db.commit()
    db.refresh(new_route)

    # 预加载关联数据
    new_route = db.query(ProcessRoute).options(
        joinedload(ProcessRoute.steps).joinedload(ProcessRouteStep.process)
    ).filter(ProcessRoute.id == new_route.id).first()

    return new_route


@router.get("/routes/templates/list", response_model=List[ProcessRouteSummary])
def get_templates(
    template_category: Optional[str] = Query(None, description="模板分类"),
    db: Session = Depends(get_db)
):
    """获取工艺路线模板列表"""
    query = db.query(ProcessRoute).filter(ProcessRoute.is_template == True)

    if template_category:
        query = query.filter(ProcessRoute.template_category == template_category)

    templates = query.order_by(ProcessRoute.template_name).all()

    result = []
    for template in templates:
        result.append(ProcessRouteSummary(
            id=template.id,
            route_code=template.route_code,
            name=template.name,
            is_template=template.is_template,
            template_name=template.template_name,
            template_category=template.template_category,
            total_cost=float(template.total_cost or 0),
            total_time=float(template.total_time or 0),
            steps_count=len(template.steps),
            created_at=template.created_at
        ))

    return result


@router.post("/routes/{route_id}/calculate", response_model=CostCalculationResult)
def calculate_route_cost(route_id: int, db: Session = Depends(get_db)):
    """计算工艺路线总成本"""
    route = db.query(ProcessRoute).options(
        joinedload(ProcessRoute.steps)
    ).filter(ProcessRoute.id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="工艺路线不存在")

    # 重新计算
    _recalculate_route_totals(route, db)
    db.commit()
    db.refresh(route)

    # 计算分类成本
    total_labor_cost = sum(float(step.labor_cost or 0) for step in route.steps)
    total_machine_cost = sum(float(step.machine_cost or 0) for step in route.steps)
    total_tool_cost = sum(float(step.tool_cost or 0) for step in route.steps)
    total_material_cost = sum(float(step.material_cost or 0) for step in route.steps)
    total_other_cost = sum(float(step.other_cost or 0) for step in route.steps)

    return CostCalculationResult(
        route_id=route_id,
        total_cost=float(route.total_cost or 0),
        total_time_minutes=float(route.total_time or 0),
        total_labor_cost=total_labor_cost,
        total_machine_cost=total_machine_cost,
        total_tool_cost=total_tool_cost,
        total_material_cost=total_material_cost,
        total_other_cost=total_other_cost,
        steps_count=len(route.steps)
    )


@router.get("/products/{product_id}/routes", response_model=List[ProcessRouteSummary])
def get_product_routes(product_id: int, db: Session = Depends(get_db)):
    """获取产品的所有工艺路线"""
    routes = db.query(ProcessRoute).filter(
        ProcessRoute.product_id == product_id
    ).order_by(ProcessRoute.created_at.desc()).all()

    result = []
    for route in routes:
        result.append(ProcessRouteSummary(
            id=route.id,
            route_code=route.route_code,
            name=route.name,
            is_template=route.is_template,
            template_name=route.template_name,
            template_category=route.template_category,
            total_cost=float(route.total_cost or 0),
            total_time=float(route.total_time or 0),
            steps_count=len(route.steps),
            created_at=route.created_at
        ))

    return result


@router.get("/drawings/{drawing_id}/routes", response_model=List[ProcessRouteSummary])
def get_drawing_routes(drawing_id: int, db: Session = Depends(get_db)):
    """获取图纸的所有工艺路线"""
    routes = db.query(ProcessRoute).filter(
        ProcessRoute.drawing_id == drawing_id
    ).order_by(ProcessRoute.created_at.desc()).all()

    result = []
    for route in routes:
        result.append(ProcessRouteSummary(
            id=route.id,
            route_code=route.route_code,
            name=route.name,
            is_template=route.is_template,
            template_name=route.template_name,
            template_category=route.template_category,
            total_cost=float(route.total_cost or 0),
            total_time=float(route.total_time or 0),
            steps_count=len(route.steps),
            created_at=route.created_at
        ))

    return result


@router.get("/quotes/{quote_id}/routes", response_model=List[ProcessRouteSummary])
def get_quote_routes(quote_id: int, db: Session = Depends(get_db)):
    """获取报价的所有工艺路线"""
    routes = db.query(ProcessRoute).filter(
        ProcessRoute.quote_id == quote_id
    ).order_by(ProcessRoute.created_at.desc()).all()

    result = []
    for route in routes:
        result.append(ProcessRouteSummary(
            id=route.id,
            route_code=route.route_code,
            name=route.name,
            is_template=route.is_template,
            template_name=route.template_name,
            template_category=route.template_category,
            total_cost=float(route.total_cost or 0),
            total_time=float(route.total_time or 0),
            steps_count=len(route.steps),
            created_at=route.created_at
        ))

    return result


# ==================== Helper Functions ====================

def _recalculate_route_totals(route: ProcessRoute, db: Session):
    """重新计算工艺路线的总成本和总工时"""
    total_cost = sum(float(step.total_cost or 0) for step in route.steps)
    total_time = sum(float(step.estimate_minutes or 0) for step in route.steps)

    route.total_cost = total_cost
    route.total_time = total_time
