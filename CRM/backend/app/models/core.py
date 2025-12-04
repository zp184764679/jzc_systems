# backend/app/models/core.py
from .. import db
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy import Numeric, event
from datetime import date
from sqlalchemy import func

class Step(db.Model):
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)

class Route(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    name  = db.Column(db.String(200))
    steps = db.Column(JSON, default=list)  # [{'name':..., 'repeat':...}]

class Order(db.Model):
    # 默认表名就是 'order'（与外键一致）
    id         = db.Column(db.Integer, primary_key=True)

    # ——已有字段（原样保留）——
    produce_no = db.Column(db.String(100))                 # 生产指令
    order_no   = db.Column(db.String(100), unique=True, nullable=False)
    product    = db.Column(db.String(200))                 # 内部图号
    qty_total  = db.Column(db.Integer, default=0)          # 订单数量（旧）
    stock_qty  = db.Column(db.Integer, default=0)          # 成品在库数（旧）
    due_date   = db.Column(db.Date, nullable=True)         # 要求纳期（旧）
    route_id   = db.Column(db.Integer, db.ForeignKey('route.id'))
    route      = db.relationship('Route')

    # （上次迁移已加）
    batch_no   = db.Column(db.String(100), index=True)     # 订单批号
    unit_price = db.Column(Numeric(10, 2))                 # 产品单价（两位小数）

    # ——通用字段（与你前端表单对应，本次需要迁移进库）——
    customer_id   = db.Column(db.Integer)
    customer_code = db.Column(db.String(64))
    order_date    = db.Column(db.Date)
    currency      = db.Column(db.String(8), default='CNY')
    remark        = db.Column(db.Text)
    status        = db.Column(db.String(32), default='draft')

    # ——前端新增的 UI 字段（上次已做迁移）——
    process_content   = db.Column(db.String(255))     # 加工内容
    delivered_qty     = db.Column(db.Integer, default=0)  # 已交数量
    delivery_date     = db.Column(db.Date)                # 交货日期
    container_code    = db.Column(db.String(64))          # 货柜编号
    default_small_bag = db.Column(db.Integer, default=0)  # 默认小袋数
    department        = db.Column(db.String(64))          # 所属部门
    poid              = db.Column(db.String(64))          # POID

    order_qty         = db.Column(db.Integer, default=0)  # 订单数量（新）
    deficit_qty       = db.Column(db.Integer, default=0)  # 欠交数量（自动兜底）
    finished_in_stock = db.Column(db.Integer, default=0)  # 成品在库存（新）
    packing_req       = db.Column(db.String(255))         # 包装要求
    default_box_num   = db.Column(db.Integer, default=0)  # 默认分箱数
    biz_dept          = db.Column(db.String(64))          # 业务部门
    cn_name           = db.Column(db.String(255))         # 中文名称

    forecast_qty   = db.Column(Numeric(18, 2), comment="预测数量")
    stock_location = db.Column(db.String(255), comment="库存所在地")

class Plan(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    order_id  = db.Column(db.Integer, db.ForeignKey('order.id'), index=True)
    step_name = db.Column(db.String(200), index=True)
    plan_start= db.Column(db.DateTime)
    plan_end  = db.Column(db.DateTime)

class Record(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    order_id  = db.Column(db.Integer, db.ForeignKey('order.id'), index=True)
    step_name = db.Column(db.String(200), index=True)
    start_time= db.Column(db.DateTime)
    end_time  = db.Column(db.DateTime)
    qty_done  = db.Column(db.Integer, default=0)
    qty_ok    = db.Column(db.Integer, default=0)

class Employee(db.Model):
    __tablename__ = "employees"

    id         = db.Column(db.Integer, primary_key=True)
    empNo      = db.Column(db.String(32), unique=True, nullable=False)
    name       = db.Column(db.String(64), nullable=False)
    department = db.Column(db.String(64), nullable=False)
    title      = db.Column(db.String(64), nullable=False)
    team       = db.Column(db.String(64))
    hireDate   = db.Column(db.Date)
    remark     = db.Column(db.Text)

    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())

# ——自动计算欠交数量：deficit_qty = max((order_qty or qty_total) - delivered_qty, 0)
def _compute_deficit_qty(mapper, connection, target: "Order"):
    # 若未显式赋值则兜底计算
    if target.deficit_qty is None:
        oq = target.order_qty or target.qty_total or 0
        dq = target.delivered_qty or 0
        target.deficit_qty = max(oq - dq, 0)

event.listen(Order, 'before_insert', _compute_deficit_qty)
event.listen(Order, 'before_update', _compute_deficit_qty)

# === 新增：订单明细表模型（与前端 items[] 对应） ===
class OrderLine(db.Model):
    __tablename__ = 'order_line'  # 显式命名，避免与保留字冲突

    id            = db.Column(db.Integer, primary_key=True)
    order_id      = db.Column(db.Integer, db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False, index=True)
    line_no       = db.Column(db.Integer, nullable=False, default=1)

    # —— 与前端明细字段一一对齐（最小改动：仅新增这些列）——
    product_text  = db.Column(db.String(120))   # 内部图号（前端：product_text）
    spec          = db.Column(db.String(200))   # 规格
    material_code = db.Column(db.String(120))   # 物料编码
    material      = db.Column(db.String(120))   # 材质

    # ★ 与数据库 schema 对齐：VARCHAR(255)、DECIMAL(18,2)
    stock_location = db.Column(db.String(255))
    forecast_qty   = db.Column(Numeric(18, 2))

    qty           = db.Column(db.Integer, nullable=False, default=0)
    currency_code = db.Column(db.String(8), nullable=False, default='CNY')  # 前端 unit = 币种
    tax_rate      = db.Column(Numeric(5, 2), nullable=False, default=0)     # 百分比数字，如 13.00
    unit_price    = db.Column(Numeric(12, 4), nullable=False, default=0)
    amount        = db.Column(Numeric(14, 2))  # 行小计；若不传则自动算 qty*unit_price

    created_at    = db.Column(db.DateTime, server_default=db.func.current_timestamp(), nullable=False)
    updated_at    = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        nullable=False
    )

# 自动补全 amount（未传时按 qty*unit_price 计算）
def _compute_line_amount(mapper, connection, target: "OrderLine"):
    if target.amount is None:
        q = int(target.qty or 0)
        up = target.unit_price or 0
        target.amount = q * up

event.listen(OrderLine, 'before_insert', _compute_line_amount)
event.listen(OrderLine, 'before_update', _compute_line_amount)

# === 给 Order 增加关系（只新增属性，不改原字段） ===
try:
    Order.lines
except Exception:
    Order.lines = db.relationship(
        'OrderLine',
        backref='order',
        cascade='all, delete-orphan',
        lazy='selectin'
    )

# === InventoryTx（真实库存流水表）===========================================
from sqlalchemy import func

class InventoryTx(db.Model):
    __tablename__ = "inventory_tx"

    id           = db.Column(db.Integer, primary_key=True)
    # 关键：以"内部图号"作为库存维度主键（你要求：每个内部图号唯一聚合）
    product_text = db.Column(db.String(128), index=True, nullable=False)   # 内部图号
    order_id     = db.Column(db.Integer, index=True, nullable=True)        # 关联订单（可空）
    order_no     = db.Column(db.String(64), index=True, nullable=True)     # 订单编号（冗余，便于聚合展示）

    # 交易类型：IN=入库, OUT=出库(领料/发货/调拨/报废均走负数)，DELIVERY=交货核销，ADJUST=盘点/调整
    tx_type      = db.Column(db.String(16), nullable=False, default="IN")  # IN/OUT/DELIVERY/ADJUST
    qty_delta    = db.Column(Numeric(14, 3), nullable=False, default=0)    # 本次变更数量（正负皆可）
    uom          = db.Column(db.String(16), nullable=True, default="pcs")  # 单位

    location     = db.Column(db.String(32), nullable=True)                 # 地点：深圳/东莞
    bin_code     = db.Column(db.String(64), nullable=True)                 # 仓位/货位

    # 来源与引用（可用于追溯）
    ref_type     = db.Column(db.String(32), nullable=True)                 # 如: "in_form"/"out_form"/"delivery"
    ref_id       = db.Column(db.String(64), nullable=True)
    note         = db.Column(db.Text, nullable=True)

    operator     = db.Column(db.String(64), nullable=True)                 # 经手人
    created_at   = db.Column(db.DateTime, server_default=func.now(), index=True)
    updated_at   = db.Column(db.DateTime, onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "product_text": self.product_text,
            "order_id": self.order_id,
            "order_no": self.order_no,
            "tx_type": self.tx_type,
            "qty_delta": float(self.qty_delta or 0),
            "uom": self.uom,
            "location": self.location,
            "bin_code": self.bin_code,
            "ref_type": self.ref_type,
            "ref_id": self.ref_id,
            "note": self.note,
            "operator": self.operator,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
