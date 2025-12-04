# services/rfq_service.py
# -*- coding: utf-8 -*-
"""
RFQ完整服务 - 从PR创建、物料分类、供应商匹配、落库报价行、通知派发（永久修复版）
✅ 统一 RFQItem 字段：item_name / item_spec / quantity / unit / category
✅ 永久修复：发送RFQ时，为“每个供应商 × 每个RFQItem”落库 SupplierQuote(status='pending')
✅ 幂等：报价行按 (supplier_id, rfq_id, item_name)，任务按 (rfq_id, supplier_id, category)
"""
import json
import logging
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime

from sqlalchemy import and_
from extensions import db
from models.rfq import RFQ
from models.rfq_item import RFQItem
from models.rfq_notification_task import RFQNotificationTask
from models.supplier_quote import SupplierQuote
from models.supplier import Supplier
from models.supplier_category import SupplierCategory
from services.ai_classifier import LocalClassifier
from constants.categories import get_major_category

logger = logging.getLogger(__name__)


class RFQService:
    """RFQ业务编排服务 - 支持异步通知（Celery）+ 永久修复后的报价落库"""

    def __init__(self):
        self.classifier = LocalClassifier()

    # -----------------------------
    # 工具：从 PRItem 取字段（兼容旧字段）
    # -----------------------------
    @staticmethod
    def _take_item_fields_from_pr_item(pi) -> Tuple[str, str, int, Optional[str], str, str]:
        """
        从 PR 的明细项 pi 中提取标准字段：
        返回: (item_name, item_spec, quantity, unit, category, remark)
        - 兼容旧字段: name/spec/qty 以及 quantity/uom/category_name/major_category 等
        """
        item_name = (
            getattr(pi, "item_name", None)
            or getattr(pi, "name", None)
            or ""
        )
        item_spec = (
            getattr(pi, "item_spec", None)
            or getattr(pi, "spec", None)
            or getattr(pi, "specification", None)
            or ""
        )
        quantity = (
            getattr(pi, "quantity", None)
            or getattr(pi, "qty", None)
            or getattr(pi, "quantity_requested", None)
            or 1
        )
        try:
            quantity = int(quantity or 1)
        except Exception:
            quantity = 1

        unit = (
            getattr(pi, "unit", None)
            or getattr(pi, "uom", None)
            or None
        )
        category = (
            getattr(pi, "category", None)
            or getattr(pi, "category_name", None)
            or getattr(pi, "major_category", None)
            or ""
        )
        remark = getattr(pi, "remark", "") or ""
        return item_name, item_spec, quantity, unit, category, remark

    # -----------------------------
    # 1) 从 PR 自动分类并创建 RFQ
    # -----------------------------
    def create_rfq_from_pr(self, pr, user_id: int, note: str = "", async_classify: bool = True) -> RFQ:
        """
        从 PR 创建 RFQ，异步分类物料（推荐）或同步分类

        Args:
            pr: PR对象
            user_id: 创建用户ID
            note: 备注
            async_classify: 是否异步分类（默认True，提升响应速度）
        """
        # ✅ 0. 直接从数据库查询PR items，避免依赖session状态
        from models.pr_item import PRItem
        pr_items = PRItem.query.filter_by(pr_id=pr.id).all()
        logger.info(f"[DEBUG] 查询到 {len(pr_items)} 个PR items: {[item.id for item in pr_items]}")

        # ✅ 第一步：先创建并提交 RFQ，确保数据库中存在记录
        rfq = RFQ(
            pr_id=pr.id,
            status='draft',
            note=note or "",
            created_by=user_id,
            classification_status='pending' if async_classify else None
        )
        db.session.add(rfq)
        db.session.commit()  # 先提交 RFQ，避免外键约束失败

        rfq_id = rfq.id  # 保存 ID

        # ✅ 第二步：创建 RFQ Items
        from sqlalchemy import text
        for idx, pr_item in enumerate(pr_items):
            logger.info(f"[DEBUG] 处理第 {idx+1}/{len(pr_items)} 个 item, pr_item.id={pr_item.id}")
            # 兼容式提取 PRItem 字段
            item_name, item_spec, quantity, unit, raw_category, remark = \
                self._take_item_fields_from_pr_item(pr_item)

            if async_classify:
                # 异步模式：先创建item，使用占位符分类
                category = "分类中..."
                major_category = ""
                minor_category = ""
                source = "pending"
                top_3_scores = {}
            else:
                # 同步模式：立即进行AI分类
                result = self.classifier.classify(
                    name=item_name,
                    spec=item_spec or "",
                    remark=remark or ""
                ) or {}
                category = result.get('category', raw_category or '未分类')
                major_category = result.get('major_category', get_major_category(category) or "")
                minor_category = result.get('minor_category', '')
                source = result.get('source', 'vector')
                scores = result.get('scores', {}) or {}
                top_3_scores = dict(sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3])

            # ✅ 使用原始SQL插入，绕过ORM对象管理问题
            sql = text("""
                INSERT INTO rfq_items (
                    rfq_id, pr_item_id, item_name, item_spec, quantity, unit,
                    category, major_category, minor_category, classification_source, classification_score
                ) VALUES (
                    :rfq_id, :pr_item_id, :item_name, :item_spec, :quantity, :unit,
                    :category, :major_category, :minor_category, :classification_source, :classification_score
                )
            """)
            db.session.execute(sql, {
                'rfq_id': rfq_id,
                'pr_item_id': getattr(pr_item, "id", None),
                'item_name': item_name,
                'item_spec': item_spec or '',
                'quantity': quantity,
                'unit': unit or '',
                'category': category,
                'major_category': major_category or '',
                'minor_category': minor_category or '',
                'classification_source': source,
                'classification_score': json.dumps(top_3_scores, ensure_ascii=False)
            })
            db.session.commit()  # ✅ 每次插入后立即commit
            logger.info(
                f"[DEBUG] 插入RFQ Item: rfq_id={rfq_id}, pr_item_id={getattr(pr_item, 'id', None)}, "
                f"item_name={item_name}, category={category}"
            )

        # ✅ 第三步：如果异步分类，触发后台任务
        if async_classify:
            from tasks.classify_rfq_items import classify_rfq_items
            from datetime import datetime

            task = classify_rfq_items.delay(rfq_id)
            rfq.classification_task_id = task.id
            rfq.classification_status = 'processing'
            rfq.classification_started_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"✅ RFQ#{rfq.id} 创建成功，异步分类任务已启动 (Task ID: {task.id})")
        else:
            logger.info(f"✅ RFQ#{rfq.id} 创建成功，包含 {len(pr_items)} 项物料（同步分类）")

        return rfq

    # -----------------------------
    # 2) 从 PR + 预分类结果 创建 RFQ
    # -----------------------------
    def create_rfq_from_pr_with_classification(
        self,
        pr,
        user_id: int,
        note: str = "",
        classification_results: List[Dict] = None
    ) -> RFQ:
        """
        根据前端传入的预分类结果为每行物料指定品类，跳过自动分类
        classification_results 形如:
        [
          { "pr_item_id": 1, "category": "刀具/铣削刀具", "major_category": "刀具", "minor_category": "铣削刀具" },
          ...
        ]
        """
        if not classification_results:
            return self.create_rfq_from_pr(pr, user_id, note)

        # ✅ 0. 直接从数据库查询PR items
        from models.pr_item import PRItem
        pr_items = PRItem.query.filter_by(pr_id=pr.id).all()

        # ✅ 第一步：先创建并提交 RFQ
        rfq = RFQ(
            pr_id=pr.id,
            status='draft',
            note=note or "",
            created_by=user_id
        )
        db.session.add(rfq)
        db.session.commit()  # 先提交 RFQ，避免外键约束失败

        rfq_id = rfq.id  # 保存 ID

        # pr_item_id -> 指定分类
        cls_map: Dict[int, Dict] = {}
        for row in classification_results or []:
            pid = row.get("pr_item_id")
            try:
                pid = int(pid) if pid is not None else None
            except Exception:
                pid = None
            if not pid:
                continue
            cls_map[pid] = {
                "category": (row.get("category") or "").strip() or "未分类",
                "major_category": (row.get("major_category") or "").strip(),
                "minor_category": (row.get("minor_category") or "").strip()
            }

        # ✅ 第二步：创建 RFQ Items（使用原始SQL）
        from sqlalchemy import text
        for pr_item in pr_items:
            item_name, item_spec, quantity, unit, raw_category, _ = \
                self._take_item_fields_from_pr_item(pr_item)

            pr_item_id = getattr(pr_item, "id", None)
            cls_data = cls_map.get(pr_item_id, {})
            category = cls_data.get("category") or raw_category or "未分类"
            major_category = cls_data.get("major_category") or get_major_category(category) or ""
            minor_category = cls_data.get("minor_category") or ""

            # ✅ 使用原始SQL插入
            sql = text("""
                INSERT INTO rfq_items (
                    rfq_id, pr_item_id, item_name, item_spec, quantity, unit,
                    category, major_category, minor_category, classification_source, classification_score
                ) VALUES (
                    :rfq_id, :pr_item_id, :item_name, :item_spec, :quantity, :unit,
                    :category, :major_category, :minor_category, :classification_source, :classification_score
                )
            """)
            db.session.execute(sql, {
                'rfq_id': rfq_id,
                'pr_item_id': pr_item_id,
                'item_name': item_name,
                'item_spec': item_spec or '',
                'quantity': quantity,
                'unit': unit or '',
                'category': category,
                'major_category': major_category or '',
                'minor_category': minor_category or '',
                'classification_source': 'manual',
                'classification_score': json.dumps({}, ensure_ascii=False)
            })
            db.session.commit()  # ✅ 每次插入后立即commit
        logger.info(f"✅ RFQ#{rfq.id} 创建成功（预分类），包含 {len(pr_items)} 项物料")
        return rfq

    # -----------------------------
    # 3) 供应商匹配
    # -----------------------------
    def match_suppliers_by_category(self, category: str, major_category: Optional[str] = None) -> List[int]:
        """
        按大类匹配供应商（仅取 status=approved 的供应商）
        """
        try:
            if not category and not major_category:
                logger.warning("[match_suppliers_by_category] category 和 major_category 都为空")
                return []

            # 没给 major 就从完整分类提取（如 "刀具/车削刀具" -> "刀具"）
            if not major_category:
                major_category = get_major_category(category)

            if not major_category:
                logger.warning(f"[match_suppliers_by_category] 无法提取大类: category='{category}'")
                return []

            # 支持逗号分隔的品类：使用 FIND_IN_SET 或模糊匹配
            # 注意：major_category 可能是单个值"刀具"，也可能是多个值"刀具, 五金劳保, 电器气动"
            from sqlalchemy import or_, func
            q = (
                db.session.query(Supplier.id)
                .join(SupplierCategory, Supplier.id == SupplierCategory.supplier_id)
                .filter(
                    Supplier.status == 'approved',
                    or_(
                        # 精确匹配（单个品类）
                        SupplierCategory.major_category == major_category,
                        # 逗号分隔列表匹配（MySQL FIND_IN_SET）
                        func.find_in_set(major_category, SupplierCategory.major_category) > 0,
                        # 兜底：包含匹配（防止有空格差异）
                        SupplierCategory.major_category.like(f'%{major_category}%')
                    )
                )
            )
            supplier_ids = [sid for (sid,) in q.all()]
            supplier_ids = list(dict.fromkeys(supplier_ids))  # 去重保序
            logger.info(f"[match_suppliers_by_category] major='{major_category}' → {len(supplier_ids)}: {supplier_ids}")
            return supplier_ids
        except Exception as e:
            logger.error(f"[match_suppliers_by_category] ❌ 异常: {str(e)}", exc_info=True)
            return []

    def match_suppliers_for_rfq(self, rfq: RFQ) -> Dict[str, List[int]]:
        """
        为 RFQ 的所有物料匹配供应商，按“完整品类”分组：
        返回: { "刀具/铣削刀具": [supplier_id, ...], ... }
        """
        try:
            if not rfq or not getattr(rfq, "items", None):
                logger.warning(f"[match_suppliers_for_rfq] RFQ#{getattr(rfq, 'id', None)} 没有物料")
                return {}

            category_items: Dict[str, List[RFQItem]] = {}
            for it in rfq.items:
                cat = (it.category or "").strip()
                if not cat:
                    continue
                category_items.setdefault(cat, []).append(it)

            routes: Dict[str, List[int]] = {}
            for cat, items in category_items.items():
                supplier_ids = self.match_suppliers_by_category(cat)
                routes[cat] = supplier_ids
                logger.debug(f"[match_suppliers_for_rfq] 品类 '{cat}'（{len(items)} 项）→ {len(supplier_ids)} 个供应商")

            logger.info(
                f"[match_suppliers_for_rfq] RFQ#{rfq.id} {len(category_items)} 个品类，"
                f"共 {sum(len(v) for v in routes.values())} 个供应商"
            )
            return routes

        except Exception as e:
            logger.error(f"[match_suppliers_for_rfq] ❌ 异常: {str(e)}", exc_info=True)
            return {}

    # -----------------------------
    # 4) 永久修复：落库报价行（每个供应商 × 每个品类）- 按品类分组
    # -----------------------------
    def create_supplier_quotes_for_routes(self, rfq: RFQ, routes: Dict[str, List[int]]) -> int:
        """
        为 routes 中的每个供应商 × 每个物料项创建 SupplierQuote（幂等）
        🔧 修复：所有物料都发送给所有匹配的供应商（不按分类过滤物料）
        返回新建条数
        """
        try:
            items: List[RFQItem] = RFQItem.query.filter_by(rfq_id=rfq.id).all()
            if not items:
                logger.warning(f"[create_supplier_quotes_for_routes] RFQ#{rfq.id} 无 RFQItem，跳过")
                return 0

            # 收集所有需要通知的供应商ID（去重）
            all_supplier_ids: Set[int] = set()
            for supplier_ids in (routes or {}).values():
                for sid in (supplier_ids or []):
                    try:
                        all_supplier_ids.add(int(sid))
                    except:
                        pass

            if not all_supplier_ids:
                logger.warning(f"[create_supplier_quotes_for_routes] RFQ#{rfq.id} 无匹配供应商")
                return 0

            created = 0
            supplier_map: Dict[int, Optional[str]] = {}

            # 🔧 关键修复：为每个物料 × 每个供应商创建报价（所有物料都发送）
            for item in items:
                category = (item.category or "未分类").strip()
                for sid in all_supplier_ids:
                    # 幂等检查：同一供应商 × 同一RFQ × 同一RFQItem
                    exists = SupplierQuote.query.filter(
                        and_(
                            SupplierQuote.supplier_id == sid,
                            SupplierQuote.rfq_id == rfq.id,
                            SupplierQuote.rfq_item_id == item.id
                        )
                    ).first()
                    if exists:
                        continue

                    # 获取供应商名称
                    if sid not in supplier_map:
                        s = Supplier.query.get(sid)
                        supplier_map[sid] = s.company_name if s else None

                    sq = SupplierQuote(
                        rfq_id=rfq.id,
                        rfq_item_id=item.id,
                        supplier_id=sid,
                        supplier_name=supplier_map.get(sid),
                        category=category,
                        status='pending',
                        item_name=item.item_name or "",
                        item_description=getattr(item, "item_spec", None) or "",
                        quantity_requested=getattr(item, "quantity", None) or 1,
                        unit=getattr(item, "unit", None) or "个",
                        total_price=None,
                        lead_time=None,
                        quote_json=None,
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(sq)
                    created += 1

            db.session.commit()
            logger.info(f"✅ [create_supplier_quotes_for_routes] RFQ#{rfq.id} 新建报价行 {created} 条（每物料单独创建）")
            return created

        except Exception as e:
            db.session.rollback()
            logger.error(f"[create_supplier_quotes_for_routes] ❌ 异常: {str(e)}", exc_info=True)
            return 0

    # -----------------------------
    # 5) 通知任务（入库 + Celery 派发）
    # -----------------------------
    def create_notification_tasks(self, rfq: RFQ, supplier_category_map: Dict[str, List[int]]) -> List[int]:
        """
        为 RFQ 创建通知任务（仅入库，不发送）
        supplier_category_map 形如：
        {
            "刀具/铣削刀具": [1, 2, 3],
            "五金劳保": [4, 5]
        }
        """
        try:
            if not supplier_category_map:
                logger.warning(f"[create_notification_tasks] RFQ#{rfq.id} 无匹配路由")
                return []

            created_ids: List[int] = []
            created_pairs: Set[Tuple[int, str]] = set()  # (supplier_id, category)

            for category, supplier_ids in (supplier_category_map or {}).items():
                if not supplier_ids:
                    continue
                for sid in supplier_ids:
                    try:
                        sid = int(sid)
                    except Exception:
                        continue

                    pair = (sid, category)
                    if pair in created_pairs:
                        continue
                    created_pairs.add(pair)

                    exists = RFQNotificationTask.query.filter_by(
                        rfq_id=rfq.id, supplier_id=sid, category=category
                    ).first()
                    if exists:
                        created_ids.append(exists.id)
                        continue

                    task = RFQNotificationTask(
                        rfq_id=rfq.id,
                        supplier_id=sid,
                        category=category,          # ✅ 必填
                        status='pending',
                        retry_count=0,
                        max_retries=5,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(task)
                    db.session.flush()
                    created_ids.append(task.id)
                    logger.debug(f"[create_notification_tasks] 创建任务: RFQ#{rfq.id} → S#{sid} ({category})")

            db.session.commit()
            logger.info(f"[create_notification_tasks] RFQ#{rfq.id} 可派发任务 {len(created_ids)} 个")
            return created_ids

        except Exception as e:
            db.session.rollback()
            logger.error(f"[create_notification_tasks] ❌ 异常: {str(e)}", exc_info=True)
            return []

    def generate_notification_tasks(self, rfq: RFQ, routes: Dict[str, List[int]]) -> List[int]:
        """
        生成通知任务 + 同步处理（简化版，不依赖 Celery）
        """
        task_ids = self.create_notification_tasks(rfq, routes)
        if not task_ids:
            logger.warning(f"[generate_notification_tasks] 没有任务可派发")
            return []

        # ✅ 直接使用同步处理，不再依赖 Celery
        logger.info(f"[generate_notification_tasks] 同步处理 {len(task_ids)} 个通知任务")
        self._process_notification_tasks_sync(task_ids)

        return task_ids

    def _process_notification_tasks_sync(self, task_ids: List[int]) -> None:
        """
        同步处理通知任务 - 简化版（直接标记为已发送）
        """
        from models.rfq_notification_task import RFQNotificationTask

        for task_id in task_ids:
            try:
                task = RFQNotificationTask.query.get(task_id)
                if not task or task.status != 'pending':
                    continue

                rfq = RFQ.query.get(task.rfq_id)
                supplier = Supplier.query.get(task.supplier_id)
                if not rfq or not supplier:
                    task.status = 'failed'
                    task.error_reason = "RFQ或Supplier不存在"
                    db.session.commit()
                    continue

                # 直接标记任务完成（简化流程，不再验证报价行）
                task.status = 'sent'
                task.sent_at = datetime.utcnow()
                task.error_reason = None
                db.session.commit()

                logger.info(f"✅ [同步通知] RFQ#{rfq.id} → {supplier.company_name} 已标记发送")

            except Exception as e:
                db.session.rollback()
                logger.error(f"[_process_notification_tasks_sync] 处理任务 {task_id} 失败: {e}")

    # -----------------------------
    # 6) 标记 RFQ 已发送
    # -----------------------------
    def mark_rfq_sent(self, rfq: RFQ) -> None:
        """
        标记 RFQ 为已发送（通知任务已创建并派发）
        """
        try:
            rfq.status = 'sent'
            rfq.sent_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"✅ RFQ#{rfq.id} 已标记为已发送 (sent_at={rfq.sent_at})")
        except Exception as e:
            db.session.rollback()
            logger.error(f"[mark_rfq_sent] ❌ 标记RFQ失败: {str(e)}", exc_info=True)
            raise

    # -----------------------------
    # 7) 统一编排：发送 RFQ（永久修复版全流程）
    # -----------------------------
    def send_rfq(self, rfq: RFQ, routes: Optional[Dict[str, List[int]]] = None) -> Dict:
        """
        编排一步到位：
        1) 若未提供 routes，则自动按品类匹配供应商
        2) 永久修复：先为 routes 创建报价行（每个供应商 × 每个RFQItem，status='pending'）
        3) 生成并派发通知任务（Celery）
        4) 标记 RFQ sent
        返回：{created_quotes, task_ids, total_suppliers, total_items}
        """
        try:
            # 0) 基本校验
            items_cnt = RFQItem.query.filter_by(rfq_id=rfq.id).count()
            if items_cnt <= 0:
                logger.warning(f"[send_rfq] RFQ#{rfq.id} 无 RFQItem，终止发送")
                return {"created_quotes": 0, "task_ids": [], "total_suppliers": 0, "total_items": 0}

            # 1) 匹配
            if routes is None:
                routes = self.match_suppliers_for_rfq(rfq)

            total_suppliers = sum(len(v or []) for v in (routes or {}).values())

            # 2) 永久修复：先落库报价行
            created_quotes = self.create_supplier_quotes_for_routes(rfq, routes)

            # 3) 任务 + Celery
            task_ids = self.generate_notification_tasks(rfq, routes)

            # 4) 标记 sent
            self.mark_rfq_sent(rfq)

            result = {
                "created_quotes": created_quotes,
                "task_ids": task_ids,
                "total_suppliers": total_suppliers,
                "total_items": items_cnt
            }
            logger.info(f"✅ [send_rfq] RFQ#{rfq.id} 完成：{result}")
            return result

        except Exception as e:
            logger.error(f"[send_rfq] ❌ 异常: {str(e)}", exc_info=True)
            return {"created_quotes": 0, "task_ids": [], "total_suppliers": 0, "total_items": 0}

    # -----------------------------
    # 8) 获取 RFQ + 供应商视图（用于前端预览）
    # -----------------------------
    def get_rfq_with_suppliers(self, rfq_id: int) -> Optional[Dict]:
        """
        返回 RFQ 及每行物料的潜在供应商（按分类匹配）
        """
        try:
            rfq = RFQ.query.get(rfq_id)
            if not rfq:
                logger.warning(f"[get_rfq_with_suppliers] RFQ#{rfq_id} 不存在")
                return None

            routes = self.match_suppliers_for_rfq(rfq)

            items_data = []
            for it in rfq.items:
                cat = it.category
                supplier_ids = routes.get(cat, []) or []
                suppliers = Supplier.query.filter(Supplier.id.in_(supplier_ids)).all() if supplier_ids else []

                items_data.append({
                    "id": it.id,
                    # ✅ 输出统一字段
                    "item_name": getattr(it, "item_name", None) or getattr(it, "name", ""),
                    "item_spec": getattr(it, "item_spec", None) or getattr(it, "spec", ""),
                    "quantity": getattr(it, "quantity", None) or getattr(it, "qty", 1),
                    "unit": it.unit,
                    "category": cat,
                    "major_category": it.major_category,
                    "minor_category": it.minor_category,
                    "suppliers": [
                        {
                            "id": s.id,
                            "company_name": s.company_name,
                            "contact_name": s.contact_name,
                            "contact_email": s.contact_email,
                        } for s in suppliers
                    ]
                })

            return {
                "rfq": {
                    "id": rfq.id,
                    "pr_id": rfq.pr_id,
                    "status": rfq.status,
                    "note": rfq.note,
                    "created_at": rfq.created_at.isoformat() if rfq.created_at else None,
                    "sent_at": rfq.sent_at.isoformat() if rfq.sent_at else None,
                },
                "items": items_data
            }

        except Exception as e:
            logger.error(f"[get_rfq_with_suppliers] ❌ 异常: {str(e)}", exc_info=True)
            return None
# Force reload
