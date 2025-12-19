# services/vector_store_service.py
"""
向量存储服务 - 方案C
基于ChromaDB实现OCR修正案例的向量检索增强
"""
import chromadb
from chromadb.config import Settings
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from models.ocr_correction import OCRCorrection
import logging
import os
import json

logger = logging.getLogger(__name__)

# 向量数据库存储路径
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')


class VectorStoreService:
    """向量存储服务 - 用于OCR修正案例的语义检索"""

    def __init__(self, db: Session = None):
        self.db = db
        self._client = None
        self._collection = None
        self._embedding_model = None

    @property
    def client(self):
        """懒加载ChromaDB客户端"""
        if self._client is None:
            # 确保目录存在
            os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

            self._client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"✅ ChromaDB初始化成功: {CHROMA_PERSIST_DIR}")
        return self._client

    @property
    def collection(self):
        """获取OCR修正案例集合"""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name="ocr_corrections",
                metadata={"description": "OCR修正案例向量库"}
            )
            logger.info(f"✅ 集合已加载: ocr_corrections (共{self._collection.count()}条记录)")
        return self._collection

    @property
    def embedding_model(self):
        """懒加载嵌入模型"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # 使用轻量级多语言模型
                self._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("✅ 嵌入模型加载成功: paraphrase-multilingual-MiniLM-L12-v2")
            except Exception as e:
                logger.error(f"❌ 嵌入模型加载失败: {e}")
                raise
        return self._embedding_model

    def _generate_embedding(self, text: str) -> List[float]:
        """生成文本的向量表示"""
        if not text or not text.strip():
            return None
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def _create_correction_text(self, field_name: str, ocr_value: str, corrected_value: str) -> str:
        """创建用于向量化的文本"""
        return f"字段:{field_name} OCR识别:{ocr_value} 修正为:{corrected_value}"

    def add_correction(self, correction: OCRCorrection) -> bool:
        """
        添加修正案例到向量库

        Args:
            correction: OCRCorrection对象

        Returns:
            是否成功
        """
        try:
            # 创建文档文本
            doc_text = self._create_correction_text(
                correction.field_name,
                correction.ocr_value or '',
                correction.corrected_value or ''
            )

            # 生成向量
            embedding = self._generate_embedding(doc_text)
            if embedding is None:
                logger.warning(f"⚠️  无法生成向量: correction_id={correction.id}")
                return False

            # 添加到集合
            self.collection.add(
                ids=[f"correction_{correction.id}"],
                embeddings=[embedding],
                documents=[doc_text],
                metadatas=[{
                    "correction_id": correction.id,
                    "drawing_id": correction.drawing_id,
                    "field_name": correction.field_name,
                    "ocr_value": correction.ocr_value or '',
                    "corrected_value": correction.corrected_value or '',
                    "correction_type": correction.correction_type or '',
                    "similarity_score": correction.similarity_score or 0.0
                }]
            )

            logger.info(f"✅ 修正案例已添加到向量库: correction_id={correction.id}")
            return True

        except Exception as e:
            logger.error(f"❌ 添加修正案例失败: {e}")
            return False

    def search_similar_corrections(
        self,
        field_name: str,
        ocr_value: str,
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        搜索相似的修正案例

        Args:
            field_name: 字段名
            ocr_value: OCR识别值
            top_k: 返回最相似的k条记录
            min_similarity: 最小相似度阈值

        Returns:
            相似修正案例列表
        """
        try:
            # 创建查询文本
            query_text = self._create_correction_text(field_name, ocr_value, '')
            query_embedding = self._generate_embedding(query_text)

            if query_embedding is None:
                return []

            # 执行向量检索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"field_name": field_name},  # 只搜索同一字段
                include=["documents", "metadatas", "distances"]
            )

            if not results or not results['ids'] or not results['ids'][0]:
                return []

            # 处理结果
            similar_corrections = []
            for i, doc_id in enumerate(results['ids'][0]):
                # ChromaDB返回的是距离，转换为相似度
                distance = results['distances'][0][i] if results['distances'] else 1.0
                similarity = 1.0 / (1.0 + distance)  # 距离越小，相似度越高

                if similarity >= min_similarity:
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    similar_corrections.append({
                        'correction_id': metadata.get('correction_id'),
                        'field_name': metadata.get('field_name'),
                        'ocr_value': metadata.get('ocr_value'),
                        'corrected_value': metadata.get('corrected_value'),
                        'similarity': round(similarity, 4),
                        'source': 'vector_search'
                    })

            logger.info(f"🔍 向量检索完成: field={field_name}, ocr_value={ocr_value[:20]}..., 找到{len(similar_corrections)}条相似记录")
            return similar_corrections

        except Exception as e:
            logger.error(f"❌ 向量检索失败: {e}")
            return []

    def sync_from_database(self) -> int:
        """
        从数据库同步修正案例到向量库

        Returns:
            同步的记录数
        """
        if not self.db:
            logger.error("❌ 数据库会话未设置")
            return 0

        try:
            # 获取所有修正记录
            corrections = self.db.query(OCRCorrection).all()

            # 获取已有的ID
            existing_ids = set()
            try:
                existing = self.collection.get()
                if existing and existing['ids']:
                    existing_ids = set(existing['ids'])
            except:
                pass

            synced = 0
            for correction in corrections:
                doc_id = f"correction_{correction.id}"
                if doc_id not in existing_ids:
                    if self.add_correction(correction):
                        synced += 1

            logger.info(f"✅ 向量库同步完成: 新增{synced}条，总计{self.collection.count()}条")
            return synced

        except Exception as e:
            logger.error(f"❌ 向量库同步失败: {e}")
            return 0

    def get_suggested_correction(
        self,
        field_name: str,
        ocr_value: str,
        min_similarity: float = 0.8
    ) -> Optional[str]:
        """
        获取建议的修正值

        Args:
            field_name: 字段名
            ocr_value: OCR识别值
            min_similarity: 最小相似度

        Returns:
            建议的修正值，如果没有找到则返回None
        """
        similar = self.search_similar_corrections(
            field_name=field_name,
            ocr_value=ocr_value,
            top_k=3,
            min_similarity=min_similarity
        )

        if not similar:
            return None

        # 返回最相似的修正值
        best_match = similar[0]
        logger.info(f"🎯 向量检索建议: {field_name}='{ocr_value}' → '{best_match['corrected_value']}' (相似度: {best_match['similarity']})")
        return best_match['corrected_value']


# 全局单例
_vector_store = None


def get_vector_store_service(db: Session = None) -> VectorStoreService:
    """获取向量存储服务实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService(db)
    elif db is not None:
        _vector_store.db = db
    return _vector_store
