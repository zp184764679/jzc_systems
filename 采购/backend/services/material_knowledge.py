# -*- coding: utf-8 -*-
"""
物料知识库服务
提供基于知识库的物料分类和匹配功能
"""
from typing import Optional, Dict, List, Tuple
import hashlib
import logging
from sqlalchemy import text, or_, func
from extensions import db

logger = logging.getLogger(__name__)


class MaterialKnowledgeService:
    """物料知识库服务"""

    def __init__(self):
        self.cache_enabled = True
        logger.info("✅ MaterialKnowledgeService 初始化完成")

    def _compute_hash(self, text: str) -> str:
        """计算输入文本的MD5哈希"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get_from_cache(self, input_text: str) -> Optional[Dict]:
        """
        从缓存中查询匹配结果

        Args:
            input_text: 输入文本（物料名称+规格）

        Returns:
            缓存的匹配结果，包含 category, knowledge_id, score, method
            如果未找到返回 None
        """
        if not self.cache_enabled:
            return None

        try:
            input_hash = self._compute_hash(input_text)

            query = text("""
                SELECT matched_category, matched_knowledge_id, match_score, match_method
                FROM material_match_cache
                WHERE input_hash = :hash
                LIMIT 1
            """)

            result = db.session.execute(query, {"hash": input_hash}).fetchone()

            if result:
                # 更新缓存命中统计
                update_query = text("""
                    UPDATE material_match_cache
                    SET hit_count = hit_count + 1,
                        last_hit_at = CURRENT_TIMESTAMP
                    WHERE input_hash = :hash
                """)
                db.session.execute(update_query, {"hash": input_hash})
                db.session.commit()

                logger.debug(f"✅ 缓存命中: {input_text} -> {result[0]}")

                return {
                    "category": result[0],
                    "knowledge_id": result[1],
                    "score": float(result[2]) if result[2] else 0.0,
                    "method": result[3]
                }

            return None

        except Exception as e:
            logger.error(f"缓存查询失败: {e}")
            return None

    def add_to_cache(self, input_text: str, category: str, knowledge_id: Optional[int] = None,
                     score: float = 1.0, method: str = "knowledge") -> None:
        """
        添加匹配结果到缓存

        Args:
            input_text: 输入文本
            category: 匹配的品类
            knowledge_id: 知识库记录ID
            score: 匹配得分
            method: 匹配方法 (exact/fuzzy/llm/vector)
        """
        if not self.cache_enabled:
            return

        try:
            input_hash = self._compute_hash(input_text)

            # 使用 INSERT ... ON DUPLICATE KEY UPDATE
            query = text("""
                INSERT INTO material_match_cache
                (input_text, input_hash, matched_category, matched_knowledge_id, match_score, match_method)
                VALUES (:text, :hash, :category, :kid, :score, :method)
                ON DUPLICATE KEY UPDATE
                    matched_category = :category,
                    matched_knowledge_id = :kid,
                    match_score = :score,
                    match_method = :method,
                    hit_count = hit_count + 1,
                    last_hit_at = CURRENT_TIMESTAMP
            """)

            db.session.execute(query, {
                "text": input_text[:500],  # 截断过长的文本
                "hash": input_hash,
                "category": category,
                "kid": knowledge_id,
                "score": score,
                "method": method
            })
            db.session.commit()

            logger.debug(f"✅ 添加缓存: {input_text} -> {category}")

        except Exception as e:
            logger.error(f"添加缓存失败: {e}")
            db.session.rollback()

    def search_exact(self, name: str, spec: str = "") -> Optional[Tuple[str, int, float]]:
        """
        精确匹配查询

        Args:
            name: 物料名称
            spec: 规格

        Returns:
            (category, knowledge_id, score) 元组，未找到返回 None
        """
        try:
            # 构建查询文本
            query_text = f"{name} {spec}".strip()

            # 精确匹配：标准名称完全匹配
            query = text("""
                SELECT category, id, match_priority
                FROM material_knowledge_base
                WHERE standard_name = :name
                ORDER BY match_priority DESC
                LIMIT 1
            """)

            result = db.session.execute(query, {"name": name.strip()}).fetchone()

            if result:
                logger.info(f"✅ 知识库精确匹配: {name} -> {result[0]}")
                return (result[0], result[1], 1.0)

            return None

        except Exception as e:
            logger.error(f"精确匹配查询失败: {e}")
            return None

    def search_fuzzy(self, name: str, spec: str = "") -> Optional[Tuple[str, int, float]]:
        """
        模糊匹配查询（使用全文搜索）

        Args:
            name: 物料名称
            spec: 规格

        Returns:
            (category, knowledge_id, score) 元组，未找到返回 None
        """
        try:
            # 构建查询文本
            query_text = f"{name} {spec}".strip()

            # 全文搜索：在 keywords, synonyms, description 中搜索
            query = text("""
                SELECT category, id, match_priority,
                    MATCH(keywords, synonyms, description) AGAINST (:query IN NATURAL LANGUAGE MODE) as relevance
                FROM material_knowledge_base
                WHERE MATCH(keywords, synonyms, description) AGAINST (:query IN NATURAL LANGUAGE MODE)
                ORDER BY relevance DESC, match_priority DESC
                LIMIT 1
            """)

            result = db.session.execute(query, {"query": query_text}).fetchone()

            if result and result[3] > 0:  # relevance > 0
                score = min(1.0, result[3] / 10)  # 归一化得分
                logger.info(f"✅ 知识库模糊匹配: {name} -> {result[0]} (相关度: {result[3]:.2f})")
                return (result[0], result[1], score)

            # 如果全文搜索失败，尝试 LIKE 匹配关键词
            fallback_query = text("""
                SELECT category, id, match_priority
                FROM material_knowledge_base
                WHERE keywords LIKE :pattern
                   OR synonyms LIKE :pattern
                   OR standard_name LIKE :pattern
                ORDER BY match_priority DESC
                LIMIT 1
            """)

            result = db.session.execute(fallback_query, {"pattern": f"%{name}%"}).fetchone()

            if result:
                logger.info(f"✅ 知识库关键词匹配: {name} -> {result[0]}")
                return (result[0], result[1], 0.7)

            return None

        except Exception as e:
            logger.error(f"模糊匹配查询失败: {e}")
            return None

    def search(self, name: str, spec: str = "") -> Optional[Dict]:
        """
        综合搜索：先精确后模糊

        Args:
            name: 物料名称
            spec: 规格

        Returns:
            {"category": str, "knowledge_id": int, "score": float, "method": str}
        """
        # 1. 先查缓存
        query_text = f"{name} {spec}".strip()
        cached = self.get_from_cache(query_text)
        if cached:
            return cached

        # 2. 精确匹配
        exact_result = self.search_exact(name, spec)
        if exact_result:
            category, kid, score = exact_result
            result = {
                "category": category,
                "knowledge_id": kid,
                "score": score,
                "method": "exact"
            }
            # 添加到缓存
            self.add_to_cache(query_text, category, kid, score, "exact")
            return result

        # 3. 模糊匹配
        fuzzy_result = self.search_fuzzy(name, spec)
        if fuzzy_result:
            category, kid, score = fuzzy_result
            result = {
                "category": category,
                "knowledge_id": kid,
                "score": score,
                "method": "fuzzy"
            }
            # 添加到缓存
            self.add_to_cache(query_text, category, kid, score, "fuzzy")
            return result

        return None

    def add_material(self, standard_name: str, category: str, major_category: str,
                     minor_category: str = "", spec_pattern: str = "",
                     synonyms: str = "", keywords: str = "", description: str = "",
                     usage_scenario: str = "", match_priority: int = 50) -> int:
        """
        添加物料到知识库

        Args:
            standard_name: 标准物料名称
            category: 品类（大类/子类）
            major_category: 大类
            minor_category: 子类
            spec_pattern: 规格模式
            synonyms: 同义词（逗号分隔）
            keywords: 关键词（逗号分隔）
            description: 描述
            usage_scenario: 使用场景
            match_priority: 匹配优先级（1-100）

        Returns:
            新增记录的ID
        """
        try:
            query = text("""
                INSERT INTO material_knowledge_base
                (standard_name, category, major_category, minor_category, spec_pattern,
                 synonyms, keywords, description, usage_scenario, match_priority, source)
                VALUES (:name, :cat, :major, :minor, :spec, :syn, :kw, :desc, :usage, :priority, 'manual')
            """)

            result = db.session.execute(query, {
                "name": standard_name,
                "cat": category,
                "major": major_category,
                "minor": minor_category,
                "spec": spec_pattern,
                "syn": synonyms,
                "kw": keywords,
                "desc": description,
                "usage": usage_scenario,
                "priority": match_priority
            })
            db.session.commit()

            logger.info(f"✅ 添加知识库记录: {standard_name} -> {category}")
            return result.lastrowid

        except Exception as e:
            logger.error(f"添加知识库记录失败: {e}")
            db.session.rollback()
            raise

    def batch_add_materials(self, materials: List[Dict]) -> int:
        """
        批量添加物料

        Args:
            materials: 物料列表，每个元素是包含字段的字典

        Returns:
            成功添加的数量
        """
        count = 0
        for mat in materials:
            try:
                self.add_material(
                    standard_name=mat.get("standard_name"),
                    category=mat.get("category"),
                    major_category=mat.get("major_category"),
                    minor_category=mat.get("minor_category", ""),
                    spec_pattern=mat.get("spec_pattern", ""),
                    synonyms=mat.get("synonyms", ""),
                    keywords=mat.get("keywords", ""),
                    description=mat.get("description", ""),
                    usage_scenario=mat.get("usage_scenario", ""),
                    match_priority=mat.get("match_priority", 50)
                )
                count += 1
            except Exception as e:
                logger.error(f"批量添加失败（跳过）: {mat.get('standard_name')}: {e}")
                continue

        logger.info(f"✅ 批量添加完成: {count}/{len(materials)} 条记录")
        return count


# 全局单例
_knowledge_service = None

def get_knowledge_service() -> MaterialKnowledgeService:
    """获取知识库服务单例"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = MaterialKnowledgeService()
    return _knowledge_service
